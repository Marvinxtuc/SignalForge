from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models import PlatformCredential
from app.schemas.settings import CredentialStatusItem, PlatformStatus


PLATFORM_PHASES = {
    "reddit": ("P0", True),
    "product_hunt": ("P0", True),
    "x": ("P1", False),
    "discord": ("P2", False),
}

ALLOWED_STATUSES = {"missing", "configured", "invalid", "permission_limited", "disabled"}
ACTIVE_STATUSES = {"active", "configured"}


def normalize_credential_status(status: str | None) -> str:
    if status in ACTIVE_STATUSES:
        return "configured"
    if status in ALLOWED_STATUSES:
        return status
    return "invalid" if status else "missing"


def credential_status_by_platform(db: Session) -> dict[str, PlatformCredential]:
    credentials: dict[str, PlatformCredential] = {}
    stmt = select(PlatformCredential).order_by(PlatformCredential.updated_at.desc(), PlatformCredential.created_at.desc())
    for credential in db.scalars(stmt).all():
        if credential.platform in PLATFORM_PHASES and credential.platform not in credentials:
            credentials[credential.platform] = credential
    return credentials


def list_platform_statuses(db: Session) -> list[PlatformStatus]:
    credentials = credential_status_by_platform(db)
    statuses: list[PlatformStatus] = []
    for platform, (phase, enabled_for_mvp) in PLATFORM_PHASES.items():
        credential = credentials.get(platform)
        statuses.append(
            PlatformStatus(
                platform=platform,  # type: ignore[arg-type]
                phase=phase,  # type: ignore[arg-type]
                enabled_for_mvp=enabled_for_mvp,
                status=normalize_credential_status(credential.status if credential else None),  # type: ignore[arg-type]
            )
        )
    return statuses


def list_credential_statuses(db: Session) -> list[CredentialStatusItem]:
    credentials = credential_status_by_platform(db)
    items: list[CredentialStatusItem] = []
    for platform in PLATFORM_PHASES:
        credential = credentials.get(platform)
        items.append(
            CredentialStatusItem(
                platform=platform,  # type: ignore[arg-type]
                status=normalize_credential_status(credential.status if credential else None),  # type: ignore[arg-type]
                credential_name=credential.credential_name if credential else None,
                last_checked_at=credential.last_checked_at if credential else None,
            )
        )
    return items
