from __future__ import annotations

import os
from collections.abc import Mapping
from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.connectors.credential_resolver import PRODUCT_HUNT_ENV_VARS, REDDIT_ENV_VARS
from app.db.models import PlatformCredential
from app.schemas.settings import CredentialStatusItem, PlatformEnvTestResponse, PlatformStatus


PLATFORM_PHASES = {
    "reddit": ("P0", True),
    "product_hunt": ("P0", True),
    "x": ("P1", False),
    "discord": ("P2", False),
}

ALLOWED_STATUSES = {"missing", "configured", "invalid", "permission_limited", "disabled"}
ACTIVE_STATUSES = {"active", "configured"}
REQUIRED_ENV_BY_PLATFORM = {
    "reddit": REDDIT_ENV_VARS,
    "product_hunt": PRODUCT_HUNT_ENV_VARS,
}
PLATFORM_ALIASES = {
    "product-hunt": "product_hunt",
    "producthunt": "product_hunt",
    "twitter": "x",
}


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


def test_platform_env_status(platform: str, env: Mapping[str, str] | None = None) -> PlatformEnvTestResponse:
    normalized_platform = normalize_platform_name(platform)
    if normalized_platform == "mock":
        return PlatformEnvTestResponse(
            platform=normalized_platform,
            status="available",
            message="Mock connector is always available for Personal Production v1.",
            checked_at=datetime.now(UTC),
        )
    if normalized_platform not in PLATFORM_PHASES:
        raise ValueError(f"unsupported platform: {platform}")

    checked_at = datetime.now(UTC)
    _phase, enabled_for_mvp = PLATFORM_PHASES[normalized_platform]
    if not enabled_for_mvp:
        return PlatformEnvTestResponse(
            platform=normalized_platform,  # type: ignore[arg-type]
            status="coming_soon",
            message=f"{normalized_platform} environment test is not available in the current phase.",
            checked_at=checked_at,
        )

    required_env = REQUIRED_ENV_BY_PLATFORM.get(normalized_platform, ())
    source_env = os.environ if env is None else env
    missing_env = [name for name in required_env if not source_env.get(name, "").strip()]
    if missing_env:
        return PlatformEnvTestResponse(
            platform=normalized_platform,  # type: ignore[arg-type]
            status="missing_env",
            message=f"{normalized_platform} is missing required environment variables.",
            checked_at=checked_at,
            required_env_missing=missing_env,
        )

    return PlatformEnvTestResponse(
        platform=normalized_platform,  # type: ignore[arg-type]
        status="configured_unverified",
        message=(
            f"{normalized_platform} required environment variables are configured; "
            "live platform verification is not performed by this endpoint."
        ),
        checked_at=checked_at,
    )


def normalize_platform_name(platform: str) -> str:
    normalized = platform.strip().lower().replace(" ", "_")
    normalized = PLATFORM_ALIASES.get(normalized, normalized)
    return normalized
