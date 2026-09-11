import asyncio
import uuid

from sqlalchemy import select

from backend.db.models.job import Job
from backend.db.session import AsyncSessionLocal, dispose_engine


async def get_job(
    job_id: str,
) -> Job | None:
    try:
        async with AsyncSessionLocal() as db:
            return await db.scalar(
                select(Job).where(
                    Job.id == uuid.UUID(job_id)
                )
            )
    finally:
        await dispose_engine()


def get_job_sync(
    job_id: str,
) -> Job | None:

    return asyncio.run(
        get_job(job_id)
    )
