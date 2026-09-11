from pathlib import Path

from backend.db.models.dataset import DatasetSourceType
from backend.services.injestion.csv import inspect_csv
from backend.services.injestion.excel import inspect_excel


def inspect_dataset(
    source_type: DatasetSourceType,
    file_path: str,
) -> dict:

    path = Path(file_path)

    if not path.exists():
        raise FileNotFoundError(
            f"Dataset file does not exist: {file_path}"
        )

    if source_type == DatasetSourceType.CSV:
        return inspect_csv(file_path)

    if source_type == DatasetSourceType.XLSX:
        return inspect_excel(file_path)

    raise ValueError(
        f"Unsupported source type: {source_type}"
    )
