from fastapi import APIRouter

from backend.api.v1 import agent, auth, chats, datasets, health, jobs, runtime

api_router = APIRouter()

api_router.include_router(health.router, prefix="/health", tags=["health"])
api_router.include_router(auth.router, prefix="/auth", tags=["auth"])
api_router.include_router(
    datasets.router, prefix="/datasets", tags=["datasets"])
api_router.include_router(
    chats.router, prefix="/datasets", tags=["chats"])
api_router.include_router(
    agent.router, prefix="/datasets", tags=["agent"])
api_router.include_router(jobs.router, prefix="/jobs", tags=["jobs"])
api_router.include_router(
    runtime.router, prefix='/test-runtime', tags=["runtime"],)
