import shutil
import uuid
from pathlib import Path

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.db.models.dataset import Dataset, DatasetSourceType, DatasetStatus


async def create_dataset(
    db: AsyncSession,
    *,
    user_id: uuid.UUID,
    name: str,
    source_type: DatasetSourceType,
    file_path: str,
) -> Dataset:
    dataset = Dataset(
        id=uuid.uuid4(),
        user_id=user_id,
        name=name,
        source_type=source_type,
        status=DatasetStatus.PENDING,
        file_path=str(Path(file_path)),
    )
    db.add(dataset)
    await db.commit()
    await db.refresh(dataset)
    return dataset


async def delete_dataset(
    db: AsyncSession,
    dataset_id: uuid.UUID,
    user_id: uuid.UUID,
) -> Dataset | None:
    dataset = await db.scalar(
        select(Dataset).where(
            Dataset.id == dataset_id,
            Dataset.user_id == user_id,
        )
    )
    if dataset is None:
        return None

    if dataset.file_path:
        file_path = Path(dataset.file_path)
        storage_dir = file_path.parent
        if storage_dir.exists() and storage_dir.is_dir():
            shutil.rmtree(storage_dir, ignore_errors=True)
        elif file_path.exists():
            file_path.unlink(missing_ok=True)

    await db.delete(dataset)
    await db.commit()
    return dataset
