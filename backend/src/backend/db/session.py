from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from backend.core.config import settings


engine = create_async_engine(
    settings.database_url,
    pool_pre_ping=True,
)

AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


async def get_db():
    async with AsyncSessionLocal() as session:
        yield session


async def dispose_engine() -> None:
    """Drop pooled connections so they are not reused across closed event loops.

    Required for Celery tasks that call ``asyncio.run()``: each run creates and
    closes a loop, and asyncpg connections bound to a closed loop fail on reuse.
    """
    await engine.dispose()
