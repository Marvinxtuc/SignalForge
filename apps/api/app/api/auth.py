from __future__ import annotations

import hmac
import os

from fastapi import Request, status
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse, Response

from app.api.errors import error_body


OWNER_TOKEN_HEADER = "X-SignalForge-Owner-Token"


def env_flag_enabled(name: str) -> bool:
    return os.getenv(name, "").strip().lower() in {"1", "true", "yes", "on"}


class OwnerAuthMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next) -> Response:
        if not _requires_owner_auth(request):
            return await call_next(request)

        expected_token = os.getenv("SIGNALFORGE_OWNER_API_TOKEN", "").strip()
        if not expected_token:
            return JSONResponse(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                content=error_body(
                    "owner_auth_not_configured",
                    "Owner API authentication is required but not configured.",
                ),
            )

        provided_token = request.headers.get(OWNER_TOKEN_HEADER, "")
        if not hmac.compare_digest(provided_token, expected_token):
            return JSONResponse(
                status_code=status.HTTP_401_UNAUTHORIZED,
                content=error_body(
                    "owner_auth_required",
                    "Owner API authentication is required.",
                ),
            )

        return await call_next(request)


def _requires_owner_auth(request: Request) -> bool:
    if not env_flag_enabled("SIGNALFORGE_REQUIRE_OWNER_AUTH"):
        return False
    if request.url.path == "/health":
        return False
    return request.url.path.startswith("/api/")
