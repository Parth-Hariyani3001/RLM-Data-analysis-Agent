from __future__ import annotations

from pathlib import Path
from typing import Awaitable, Callable

from backend.core.config import settings
from backend.data_runtime.factory import create_file_runtime
from backend.data_runtime.runtime import DataRuntime
from fastapi import HTTPException, status

from backend.db.models.dataset import Dataset, DatasetStatus
from backend.rlm.engine import RLMEngine
from backend.rlm.models import RLMConfig, RLMResult, RLMStep, RunCollector
from backend.rlm.provider import OpenAICompatibleProvider
from backend.rlm.tools import AnalysisTools, ToolRegistry


def create_provider() -> OpenAICompatibleProvider:
    model = settings.llm_model or settings.model_name
    if not model:
        raise ValueError(
            "LLM model is not configured. Set LLM_MODEL in .env"
        )

    return OpenAICompatibleProvider(
        base_url=settings.llm_base_url,
        api_key=settings.llm_api_key,
        model=model,
    )


async def create_runtime_for_dataset(
    dataset: Dataset,
) -> DataRuntime:
    if dataset.status != DatasetStatus.READY:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Dataset is not ready (status: {dataset.status.value})",
        )

    if not dataset.file_path:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Dataset has no associated file",
        )

    file_path = Path(dataset.file_path)
    if not file_path.exists():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Dataset file not found on disk",
        )

    runtime = create_file_runtime(str(file_path))
    await runtime.connect()
    return runtime


def build_dataset_context(dataset: Dataset) -> str | None:
    if not dataset.schema:
        return None

    columns = dataset.schema.get("columns", [])
    if not columns:
        return None

    lines = [
        f"Name: {dataset.name}",
        f"Rows: {dataset.row_count}",
        f"Columns: {dataset.column_count}",
        "",
        "Column schema:",
    ]

    for column in columns:
        if isinstance(column, dict):
            name = column.get("name", "unknown")
            dtype = column.get("dtype", "unknown")
            lines.append(f"  - {name} ({dtype})")
        else:
            lines.append(f"  - {column}")

    return "\n".join(lines)


async def run_agent(
    question: str,
    dataset: Dataset,
    on_step: Callable[[RLMStep], Awaitable[None]] | None = None,
    config: RLMConfig | None = None,
) -> RLMResult:
    runtime = await create_runtime_for_dataset(dataset)

    try:
        tools = AnalysisTools(runtime)
        collector = RunCollector()
        registry = ToolRegistry(tools, collector=collector)
        provider = create_provider()
        
        engine = RLMEngine(
            provider=provider,
            tool_registry=registry,
            config=config or RLMConfig(),
            collector=collector,
        )

        return await engine.run(
            question=question,
            on_step=on_step,
            dataset_context=build_dataset_context(dataset),
        )
    finally:
        await runtime.close()
