from fastapi import APIRouter
from sqlalchemy import text

from backend.db.session import AsyncSessionLocal

router = APIRouter()


@router.get("")
async def health():
    return {"status": "ok"}


@router.get("/ready")
async def readiness():
    async with AsyncSessionLocal() as db:
        await db.execute(text("SELECT 1"))
    return {"status": "ready"}
