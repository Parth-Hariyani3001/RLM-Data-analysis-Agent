import asyncio
import uuid
from datetime import datetime, timezone

import structlog
from sqlalchemy import select

from backend.db.models.dataset import Dataset, DatasetStatus
from backend.db.models.job import Job, JobStatus
from backend.db.session import AsyncSessionLocal, dispose_engine
from backend.services.injestion.service import inspect_dataset
from backend.workers.celery_app import celery_app

logger = structlog.get_logger()


async def _run_ingestion(dataset_id: str, job_id: str) -> None:
    try:
        async with AsyncSessionLocal() as db:
            dataset = await db.scalar(select(Dataset).where(Dataset.id == uuid.UUID(dataset_id)))
            job = await db.scalar(select(Job).where(Job.id == uuid.UUID(job_id)))

            if dataset is None:
                raise ValueError(f"Dataset not found: {dataset_id}")
            if job is None:
                raise ValueError(f"Job not found: {job_id}")

            job.status = JobStatus.RUNNING
            job.progress = 10
            job.started_at = datetime.now(timezone.utc)
            dataset.status = DatasetStatus.PROCESSING
            await db.commit()

            try:
                logger.info("dataset_ingestion_started", dataset_id=dataset_id, job_id=job_id)

                if dataset.file_path is None:
                    raise ValueError("Dataset has no file path")

                result = inspect_dataset(dataset.source_type, dataset.file_path)

                dataset.row_count = result["row_count"]
                dataset.column_count = result["column_count"]
                dataset.schema = result["schema"]
                dataset.status = DatasetStatus.READY

                job.status = JobStatus.COMPLETED
                job.progress = 100
                job.completed_at = datetime.now(timezone.utc)
                await db.commit()

                logger.info("dataset_ingestion_completed", dataset_id=dataset_id, job_id=job_id)

            except Exception as exc:
                logger.exception("dataset_ingestion_failed", dataset_id=dataset_id, job_id=job_id)

                dataset.status = DatasetStatus.FAILED
                dataset.error_message = str(exc)
                job.status = JobStatus.FAILED
                job.error_message = str(exc)
                job.completed_at = datetime.now(timezone.utc)
                await db.commit()

                raise
    finally:
        # Prevent pooled asyncpg connections from outliving this asyncio.run() loop.
        await dispose_engine()


@celery_app.task(bind=True, name="ingestion.inspect_dataset")
def inspect_dataset_task(self, dataset_id: str, job_id: str) -> None:
    asyncio.run(_run_ingestion(dataset_id, job_id))
