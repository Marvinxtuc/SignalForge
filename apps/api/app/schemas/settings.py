from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import Field

from app.schemas.common import ApiSchema


PlatformName = Literal["reddit", "product_hunt", "x", "discord"]
PlatformPhase = Literal["P0", "P1", "P2"]
CredentialStatus = Literal["missing", "configured", "invalid", "permission_limited", "disabled"]
PlatformTestStatus = Literal[
    "available",
    "missing_env",
    "configured_unverified",
    "valid",
    "invalid",
    "rate_limited",
    "permission_limited",
    "coming_soon",
]


class PlatformStatus(ApiSchema):
    platform: PlatformName
    phase: PlatformPhase
    enabled_for_mvp: bool
    status: CredentialStatus


class PlatformsResponse(ApiSchema):
    platforms: list[PlatformStatus]


class CredentialStatusItem(ApiSchema):
    platform: PlatformName
    status: CredentialStatus
    credential_name: str | None = None
    last_checked_at: datetime | None = None


class CredentialStatusResponse(ApiSchema):
    credentials: list[CredentialStatusItem]


class PlatformEnvTestResponse(ApiSchema):
    platform: str
    status: PlatformTestStatus
    message: str
    checked_at: datetime
    required_env_missing: list[str] = Field(default_factory=list)
