import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict

from backend.db.models.job import JobStatus, JobType


class JobResponse(BaseModel):
    model_config = ConfigDict(
        from_attributes=True
    )

    id: uuid.UUID
    user_id: uuid.UUID
    type: JobType
    status: JobStatus

    celery_task_id: str | None

    progress: float

    error_message: str | None

    created_at: datetime
    started_at: datetime | None
    completed_at: datetime | None
