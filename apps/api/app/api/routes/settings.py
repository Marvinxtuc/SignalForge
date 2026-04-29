from __future__ import annotations

from fastapi import APIRouter

from app.api.deps import DbSession
from app.schemas.settings import CredentialStatusResponse, PlatformsResponse
from app.services import settings as settings_service


router = APIRouter(prefix="/api/settings", tags=["settings"])


@router.get("/platforms", response_model=PlatformsResponse)
def list_platforms(db: DbSession) -> PlatformsResponse:
    return PlatformsResponse(platforms=settings_service.list_platform_statuses(db))


@router.get("/credentials/status", response_model=CredentialStatusResponse)
def list_credential_statuses(db: DbSession) -> CredentialStatusResponse:
    return CredentialStatusResponse(credentials=settings_service.list_credential_statuses(db))
