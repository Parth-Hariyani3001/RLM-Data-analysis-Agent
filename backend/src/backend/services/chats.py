import uuid
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from backend.db.models.chat import (
    ChatMessage,
    ChatMessageRole,
    ChatRunLog,
    ChatSession,
)
from backend.db.models.dataset import Dataset
from backend.rlm.models import RLMResult

TITLE_MAX_LEN = 80


def _title_from_question(question: str) -> str:
    trimmed = " ".join(question.strip().split())
    if len(trimmed) <= TITLE_MAX_LEN:
        return trimmed
    return f"{trimmed[: TITLE_MAX_LEN - 1].rstrip()}…"


async def get_owned_dataset(
    db: AsyncSession,
    dataset_id: uuid.UUID,
    user_id: uuid.UUID,
) -> Dataset | None:
    return await db.scalar(
        select(Dataset).where(
            Dataset.id == dataset_id,
            Dataset.user_id == user_id,
        )
    )


async def list_sessions(
    db: AsyncSession,
    *,
    dataset_id: uuid.UUID,
    user_id: uuid.UUID,
) -> list[ChatSession]:
    result = await db.scalars(
        select(ChatSession)
        .where(
            ChatSession.dataset_id == dataset_id,
            ChatSession.user_id == user_id,
        )
        .order_by(ChatSession.updated_at.desc())
    )
    return list(result.all())


async def create_session(
    db: AsyncSession,
    *,
    dataset_id: uuid.UUID,
    user_id: uuid.UUID,
    title: str | None = None,
) -> ChatSession:
    session = ChatSession(
        id=uuid.uuid4(),
        user_id=user_id,
        dataset_id=dataset_id,
        title=title,
    )
    db.add(session)
    await db.commit()
    await db.refresh(session)
    return session


async def get_session(
    db: AsyncSession,
    *,
    session_id: uuid.UUID,
    dataset_id: uuid.UUID,
    user_id: uuid.UUID,
) -> ChatSession | None:
    return await db.scalar(
        select(ChatSession)
        .where(
            ChatSession.id == session_id,
            ChatSession.dataset_id == dataset_id,
            ChatSession.user_id == user_id,
        )
        .options(
            selectinload(ChatSession.messages),
            selectinload(ChatSession.run_logs),
        )
    )


async def delete_session(
    db: AsyncSession,
    *,
    session_id: uuid.UUID,
    dataset_id: uuid.UUID,
    user_id: uuid.UUID,
) -> bool:
    session = await db.scalar(
        select(ChatSession).where(
            ChatSession.id == session_id,
            ChatSession.dataset_id == dataset_id,
            ChatSession.user_id == user_id,
        )
    )
    if session is None:
        return False

    await db.delete(session)
    await db.commit()
    return True


async def persist_turn(
    db: AsyncSession,
    *,
    session_id: uuid.UUID,
    question: str,
    result: RLMResult,
) -> ChatSession | None:
    session = await db.scalar(
        select(ChatSession).where(ChatSession.id == session_id)
    )
    if session is None:
        return None

    if not session.title:
        session.title = _title_from_question(question)

    session.updated_at = datetime.now(timezone.utc)

    db.add(
        ChatMessage(
            id=uuid.uuid4(),
            session_id=session.id,
            role=ChatMessageRole.USER,
            content=question,
        )
    )

    assistant_id = uuid.uuid4()
    db.add(
        ChatMessage(
            id=assistant_id,
            session_id=session.id,
            role=ChatMessageRole.ASSISTANT,
            content=result.answer,
            steps=[
                {
                    "type": step.type.value,
                    "content": step.content,
                    "iteration": step.iteration,
                }
                for step in result.steps
                if step.type.value != "final"
            ],
            iterations=result.iterations,
        )
    )

    usage = result.usage
    db.add(
        ChatRunLog(
            id=uuid.uuid4(),
            session_id=session.id,
            message_id=assistant_id,
            model=usage.model,
            iterations=usage.iterations or result.iterations,
            llm_calls=usage.llm_calls,
            tool_calls=usage.tool_calls,
            prompt_tokens=usage.prompt_tokens,
            completion_tokens=usage.completion_tokens,
            total_tokens=usage.total_tokens,
            events=usage.events,
        )
    )

    await db.commit()
    await db.refresh(session)
    return session
