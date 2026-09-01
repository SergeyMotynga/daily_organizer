"""Агрегатор API router-ов."""

from fastapi import APIRouter

from backend.api.v1.auth import router as auth_router
from backend.api.v1.dev_auth import router as dev_auth_router

api_router = APIRouter()
api_router.include_router(auth_router)
api_router.include_router(dev_auth_router)
