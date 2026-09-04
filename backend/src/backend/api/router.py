"""Агрегатор API router-ов."""

from fastapi import APIRouter

from backend.api.v1.auth import router as auth_router
from backend.api.v1.dev_auth import router as dev_auth_router
from backend.api.v1.task_statuses import router as task_statuses_router
from backend.api.v1.tasks import router as tasks_router

api_router = APIRouter()
api_router.include_router(auth_router)
api_router.include_router(dev_auth_router)
api_router.include_router(task_statuses_router)
api_router.include_router(tasks_router)
