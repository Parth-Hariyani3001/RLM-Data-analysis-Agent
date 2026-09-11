# app/api/routes/runtime.py

from fastapi import APIRouter, Depends, HTTPException

from backend.core.security import get_current_user
from backend.data_runtime.factory import create_file_runtime
from backend.data_runtime.profiling.profiler import DatasetProfiler
from backend.db.models.user import User


router = APIRouter()


@router.get("/test")
async def test_runtime(
    _current_user: User = Depends(get_current_user),
):
    runtime = create_file_runtime(
        "src/data/example.csv"
    )

    await runtime.connect()

    try:
        schema = await runtime.schema()
        sample = await runtime.sample(
            limit=5
        )

        profiler = DatasetProfiler(
            runtime
        )

        profile = await profiler.profile()
        return {
            "schema": schema,
            "sample": sample,
            "profile": profile,
        }

    finally:
        await runtime.close()
