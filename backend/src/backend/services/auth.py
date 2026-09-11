from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.core.security import hash_password, verify_password
from backend.db.models.user import User


async def register_user(
    db: AsyncSession,
    username: str,
    password: str,
    full_name: str,
) -> User:
    existing = await db.scalar(select(User).where(User.username == username))
    if existing is not None:
        raise ValueError("Username already exists")

    user = User(
        username=username,
        hashed_password=hash_password(password),
        full_name=full_name,
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user


async def authenticate_user(
    db: AsyncSession,
    username: str,
    password: str,
) -> User | None:
    user = await db.scalar(select(User).where(User.username == username))
    if user is None or not verify_password(password, user.hashed_password):
        return None
    return user
