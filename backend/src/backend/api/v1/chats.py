import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from backend.core.security import get_current_user
from backend.db.models.user import User
from backend.db.session import get_db
from backend.schemas.chat import (
    ChatSessionDetailResponse,
    ChatSessionResponse,
)
from backend.services import chats as chat_service

router = APIRouter()


@router.get(
    "/{dataset_id}/sessions",
    response_model=list[ChatSessionResponse],
)
async def list_chat_sessions(
    dataset_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    dataset = await chat_service.get_owned_dataset(
        db, dataset_id, current_user.id
    )
    if dataset is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Dataset not found",
        )

    return await chat_service.list_sessions(
        db,
        dataset_id=dataset_id,
        user_id=current_user.id,
    )


@router.post(
    "/{dataset_id}/sessions",
    response_model=ChatSessionResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_chat_session(
    dataset_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    dataset = await chat_service.get_owned_dataset(
        db, dataset_id, current_user.id
    )
    if dataset is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Dataset not found",
        )

    return await chat_service.create_session(
        db,
        dataset_id=dataset_id,
        user_id=current_user.id,
    )


@router.get(
    "/{dataset_id}/sessions/{session_id}",
    response_model=ChatSessionDetailResponse,
)
async def get_chat_session(
    dataset_id: uuid.UUID,
    session_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    dataset = await chat_service.get_owned_dataset(
        db, dataset_id, current_user.id
    )
    if dataset is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Dataset not found",
        )

    session = await chat_service.get_session(
        db,
        session_id=session_id,
        dataset_id=dataset_id,
        user_id=current_user.id,
    )
    if session is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Chat session not found",
        )

    return session


@router.delete(
    "/{dataset_id}/sessions/{session_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def delete_chat_session(
    dataset_id: uuid.UUID,
    session_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    dataset = await chat_service.get_owned_dataset(
        db, dataset_id, current_user.id
    )
    if dataset is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Dataset not found",
        )

    deleted = await chat_service.delete_session(
        db,
        session_id=session_id,
        dataset_id=dataset_id,
        user_id=current_user.id,
    )
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Chat session not found",
        )
