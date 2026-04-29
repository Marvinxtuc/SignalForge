from typing import Any

from fastapi import HTTPException, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse


class ApiError(HTTPException):
    def __init__(
        self,
        code: str,
        message: str,
        status_code: int = status.HTTP_400_BAD_REQUEST,
        details: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(
            status_code=status_code,
            detail={"code": code, "message": message, "details": details or {}},
        )


def error_body(code: str, message: str, details: dict[str, Any] | None = None) -> dict[str, Any]:
    return {"error": {"code": code, "message": message, "details": details or {}}}


def error_response(
    code: str,
    message: str,
    status_code: int = status.HTTP_400_BAD_REQUEST,
    details: dict[str, Any] | None = None,
) -> JSONResponse:
    return JSONResponse(status_code=status_code, content=error_body(code, message, details))


async def api_error_handler(_request: Request, exc: ApiError) -> JSONResponse:
    detail = exc.detail if isinstance(exc.detail, dict) else {}
    return error_response(
        code=str(detail.get("code", "internal_error")),
        message=str(detail.get("message", "Unexpected API error")),
        status_code=exc.status_code,
        details=detail.get("details") if isinstance(detail.get("details"), dict) else {},
    )


async def validation_error_handler(_request: Request, exc: RequestValidationError) -> JSONResponse:
    return error_response(
        code="validation_error",
        message="Request validation failed",
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        details={"errors": exc.errors()},
    )


async def http_exception_handler(_request: Request, exc: HTTPException) -> JSONResponse:
    if isinstance(exc.detail, dict) and {"code", "message", "details"} <= set(exc.detail):
        return error_response(
            code=str(exc.detail["code"]),
            message=str(exc.detail["message"]),
            status_code=exc.status_code,
            details=exc.detail["details"] if isinstance(exc.detail["details"], dict) else {},
        )
    return error_response(
        code="not_found" if exc.status_code == status.HTTP_404_NOT_FOUND else "http_error",
        message=str(exc.detail),
        status_code=exc.status_code,
        details={},
    )


def not_found(message: str = "Resource not found", details: dict[str, Any] | None = None) -> ApiError:
    return ApiError("not_found", message, status.HTTP_404_NOT_FOUND, details)


def conflict(message: str = "Resource conflict", details: dict[str, Any] | None = None) -> ApiError:
    return ApiError("conflict", message, status.HTTP_409_CONFLICT, details)


def phase_not_available(message: str, details: dict[str, Any] | None = None) -> ApiError:
    return ApiError("phase_not_available", message, status.HTTP_409_CONFLICT, details)
