from __future__ import annotations

from fastapi import APIRouter

from app.api.errors import not_found
from app.api.deps import DbSession
from app.schemas.settings import CredentialStatusResponse, PlatformEnvTestResponse, PlatformsResponse
from app.services import settings as settings_service


router = APIRouter(prefix="/api/settings", tags=["settings"])


@router.get("/platforms", response_model=PlatformsResponse)
def list_platforms(db: DbSession) -> PlatformsResponse:
    return PlatformsResponse(platforms=settings_service.list_platform_statuses(db))


@router.get("/credentials/status", response_model=CredentialStatusResponse)
def list_credential_statuses(db: DbSession) -> CredentialStatusResponse:
    return CredentialStatusResponse(credentials=settings_service.list_credential_statuses(db))


@router.post("/platforms/{platform}/test", response_model=PlatformEnvTestResponse)
def test_platform_env_status(platform: str) -> PlatformEnvTestResponse:
    try:
        return settings_service.test_platform_env_status(platform)
    except ValueError as exc:
        raise not_found("Unsupported platform", {"platform": platform}) from exc
