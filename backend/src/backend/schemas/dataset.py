import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict

from backend.db.models.dataset import (
    DatasetSourceType,
    DatasetStatus,
)


class DatasetResponse(BaseModel):
    model_config = ConfigDict(
        from_attributes=True
    )

    id: uuid.UUID
    user_id: uuid.UUID
    name: str
    source_type: DatasetSourceType
    status: DatasetStatus

    row_count: int | None
    column_count: int | None

    schema: dict | None

    error_message: str | None

    created_at: datetime
    updated_at: datetime
