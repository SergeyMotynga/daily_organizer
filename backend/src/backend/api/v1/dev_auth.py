"""Dev-only auth endpoint-ы API v1."""

from typing import Annotated

from fastapi import APIRouter, Depends, Response, status

from backend.api.deps import get_auth_service
from backend.schemas.auth import DevResetPasswordRequest
from backend.services.auth import AuthService

router = APIRouter(prefix="/api/v1/dev/auth", tags=["dev-auth"])


@router.post("/reset-password", status_code=status.HTTP_204_NO_CONTENT)
async def reset_password(
    payload: DevResetPasswordRequest,
    auth_service: Annotated[AuthService, Depends(get_auth_service)],
) -> Response:
    """Сбрасывает пароль пользователя в dev-режиме."""
    await auth_service.dev_reset_password(login=payload.login, new_password=payload.new_password)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
