import asyncio
import json
import uuid
from collections.abc import AsyncIterator

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.core.security import get_current_user
from backend.db.models.dataset import Dataset, DatasetStatus
from backend.db.models.user import User
from backend.db.session import AsyncSessionLocal, get_db
from backend.rlm.models import RLMResult, RLMStep
from backend.schemas.agent import AgentAskRequest, AgentStepEvent, AgentUsageSummary
from backend.services import chats as chat_service
from backend.services.agent import create_provider, run_agent

router = APIRouter()


def _step_payload(step: RLMStep) -> dict:
    return {
        "event": "step",
        "type": step.type.value,
        "content": step.content,
        "iteration": step.iteration,
    }


def _final_payload(result: RLMResult, session_id: uuid.UUID) -> dict:
    usage = AgentUsageSummary(**result.usage.to_dict())
    return {
        "event": "final",
        "answer": result.answer,
        "iterations": result.iterations,
        "session_id": str(session_id),
        "usage": usage.model_dump(),
        "steps": [
            AgentStepEvent(
                type=step.type.value,
                content=step.content,
                iteration=step.iteration,
            ).model_dump()
            for step in result.steps
            if step.type.value != "final"
        ],
    }


@router.post("/{dataset_id}/ask")
async def ask_dataset(
    dataset_id: uuid.UUID,
    body: AgentAskRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    dataset = await db.scalar(
        select(Dataset).where(
            Dataset.id == dataset_id,
            Dataset.user_id == current_user.id,
        )
    )

    if dataset is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Dataset not found",
        )

    if dataset.status != DatasetStatus.READY:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Dataset is not ready (status: {dataset.status.value})",
        )

    try:
        create_provider()
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(exc),
        ) from exc

    if body.session_id is not None:
        session = await chat_service.get_session(
            db,
            session_id=body.session_id,
            dataset_id=dataset_id,
            user_id=current_user.id,
        )
        if session is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Chat session not found",
            )
        session_id = session.id
    else:
        session = await chat_service.create_session(
            db,
            dataset_id=dataset_id,
            user_id=current_user.id,
        )
        session_id = session.id

    # Detach ORM objects needed after the request session may close.
    question = body.question
    dataset_snapshot = dataset

    async def event_stream() -> AsyncIterator[str]:
        queue: asyncio.Queue[dict | None] = asyncio.Queue()

        async def on_step(step: RLMStep) -> None:
            if step.type.value == "final":
                return
            await queue.put(_step_payload(step))

        async def execute() -> None:
            try:
                result = await run_agent(
                    question=question,
                    dataset=dataset_snapshot,
                    on_step=on_step,
                )

                async with AsyncSessionLocal() as persist_db:
                    await chat_service.persist_turn(
                        persist_db,
                        session_id=session_id,
                        question=question,
                        result=result,
                    )

                await queue.put(_final_payload(result, session_id))
            except HTTPException as exc:
                await queue.put({
                    "event": "error",
                    "message": exc.detail,
                    "status_code": exc.status_code,
                })
            except Exception as exc:
                await queue.put({
                    "event": "error",
                    "message": str(exc),
                })
            finally:
                await queue.put(None)

        task = asyncio.create_task(execute())

        try:
            while True:
                item = await queue.get()
                if item is None:
                    break

                yield f"data: {json.dumps(item)}\n\n"
        finally:
            if not task.done():
                await task

    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )
