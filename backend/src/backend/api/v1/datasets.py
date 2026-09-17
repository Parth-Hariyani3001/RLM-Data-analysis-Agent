import uuid
from pathlib import Path

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.core.config import settings
from backend.core.security import get_current_user
from backend.db.models.dataset import Dataset, DatasetSourceType
from backend.db.models.job import Job, JobType
from backend.db.models.user import User
from backend.db.session import get_db
from backend.schemas.dataset import DatasetResponse
from backend.schemas.job import JobResponse
from backend.services.datasets import create_dataset, delete_dataset
from backend.workers.tasks.injestion import inspect_dataset_task

router = APIRouter()


@router.get("", response_model=list[DatasetResponse])
async def list_datasets(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.scalars(
        select(Dataset)
        .where(Dataset.user_id == current_user.id)
        .order_by(Dataset.created_at.desc())
    )
    return result.all()


ALLOWED_EXTENSIONS = {
    ".csv": DatasetSourceType.CSV,
    ".xlsx": DatasetSourceType.XLSX,
}


@router.post("", response_model=dict, status_code=status.HTTP_201_CREATED)
async def upload_dataset(
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    extension = Path(file.filename or "").suffix.lower()
    source_type = ALLOWED_EXTENSIONS.get(extension)

    if source_type is None:
        raise HTTPException(
            status_code=400, detail="Only CSV and XLSX files are supported")

    dataset_id = uuid.uuid4()
    storage_dir = Path(settings.storage_path) / "datasets" / str(dataset_id)
    storage_dir.mkdir(parents=True, exist_ok=True)

    file_path = storage_dir / (file.filename or "dataset")
    max_size = settings.max_upload_size_mb * 1024 * 1024
    total_size = 0

    try:
        with file_path.open("wb") as output:
            while chunk := await file.read(1024 * 1024):
                total_size += len(chunk)
                if total_size > max_size:
                    raise HTTPException(
                        status_code=413,
                        detail=f"File exceeds {settings.max_upload_size_mb} MB",
                    )

                output.write(chunk)

    except Exception:
        if file_path.exists():
            file_path.unlink()
        raise

    dataset = await create_dataset(
        db,
        user_id=current_user.id,
        name=file.filename or "dataset",
        source_type=source_type,
        file_path=str(file_path),
    )

    job = Job(
        id=uuid.uuid4(),
        user_id=current_user.id,
        type=JobType.INGESTION,
    )

    db.add(job)
    await db.commit()
    await db.refresh(job)

    task = inspect_dataset_task.delay(str(dataset.id), str(job.id))
    job.celery_task_id = task.id

    await db.commit()
    await db.refresh(job)

    return {
        "dataset": DatasetResponse.model_validate(dataset),
        "job": JobResponse.model_validate(job),
    }


@router.get("/{dataset_id}", response_model=DatasetResponse)
async def get_dataset(
    dataset_id: uuid.UUID,
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
        raise HTTPException(status_code=404, detail="Dataset not found")

    return dataset


@router.delete("/{dataset_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_dataset(
    dataset_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    dataset = await delete_dataset(db, dataset_id, current_user.id)

    if dataset is None:
        raise HTTPException(status_code=404, detail="Dataset not found")
