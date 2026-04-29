from __future__ import annotations

import re
from datetime import datetime
from enum import StrEnum
from typing import Annotated, Any
from uuid import UUID

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    SecretStr,
    StringConstraints,
    field_validator,
)


NonEmptyStr = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1)]
REDACTED = "[REDACTED]"
_SENSITIVE_KEY_PARTS = (
    "authorization",
    "bearer",
    "token",
    "secret",
    "access_token",
    "refresh_token",
    "client_secret",
    "reddit_client_secret",
    "product_hunt_token",
)
_SENSITIVE_REQUEST_KEYS = {"request", "request_headers", "request_object"}
_SENSITIVE_WORD_PATTERN = re.compile(
    r"(?i)\b("
    r"authorization|bearer_token|bearer|access_token|refresh_token|client_secret|"
    r"reddit_client_secret|product_hunt_token|token|secret"
    r")\b"
)
_BEARER_VALUE_PATTERN = re.compile(r"(?i)\bbearer\s+[A-Za-z0-9._~+/=-]+")
_ASSIGNMENT_SECRET_PATTERN = re.compile(
    r"(?i)\b(?:authorization|access_token|refresh_token|client_secret|token|secret)"
    r"\s*[:=]\s*['\"]?[^,'\"\s)}\]]+"
)
_TOKEN_LIKE_PATTERN = re.compile(
    r"(?<![/:])(?=.*[A-Za-z])(?=.*\d)[A-Za-z0-9._~+=-]{32,}(?![/:])"
)


class ConnectorStatus(StrEnum):
    SUCCESS = "success"
    DISABLED = "disabled"
    FAILED = "failed"
    RATE_LIMITED = "rate_limited"
    PERMISSION_LIMITED = "permission_limited"


class CredentialResolutionStatus(StrEnum):
    AVAILABLE = "available"
    MISSING = "missing"
    DISABLED = "disabled"


class ResolvedConnectorCredentials(BaseModel):
    model_config = ConfigDict(extra="forbid")

    platform: NonEmptyStr
    status: CredentialResolutionStatus
    authorization_header: SecretStr | None = Field(default=None, exclude=True, repr=False)
    client_id: SecretStr | None = Field(default=None, exclude=True, repr=False)
    client_secret: SecretStr | None = Field(default=None, exclude=True, repr=False)
    user_agent: SecretStr | None = Field(default=None, exclude=True, repr=False)
    missing_env: tuple[str, ...] = Field(default_factory=tuple, exclude=True, repr=False)
    reason: str | None = None

    @property
    def is_available(self) -> bool:
        return self.status == CredentialResolutionStatus.AVAILABLE

    @property
    def is_disabled(self) -> bool:
        return self.status in {
            CredentialResolutionStatus.DISABLED,
            CredentialResolutionStatus.MISSING,
        }

    def get_authorization_header(self) -> str | None:
        if self.authorization_header is None:
            return None
        return self.authorization_header.get_secret_value()

    def get_client_id(self) -> str | None:
        if self.client_id is None:
            return None
        return self.client_id.get_secret_value()

    def get_client_secret(self) -> str | None:
        if self.client_secret is None:
            return None
        return self.client_secret.get_secret_value()

    def get_user_agent(self) -> str | None:
        if self.user_agent is None:
            return None
        return self.user_agent.get_secret_value()

    def safe_metadata(self) -> dict[str, Any]:
        return {
            "credential_status": self.status.value,
            "missing_required_env_count": len(self.missing_env),
        }


class HTTPResponseSnapshot(BaseModel):
    model_config = ConfigDict(extra="forbid")

    status_code: int = Field(ge=100, le=599)
    headers: dict[str, str] = Field(default_factory=dict)
    body_excerpt: str | None = None


class RateLimitState(BaseModel):
    model_config = ConfigDict(extra="forbid")

    remaining: int | None = Field(default=None, ge=0)
    reset_at: datetime | None = None
    retry_after_seconds: int | None = Field(default=None, ge=0)


class NormalizedRawItem(BaseModel):
    model_config = ConfigDict(extra="forbid")

    platform: NonEmptyStr
    platform_item_id: NonEmptyStr
    source_url: NonEmptyStr
    author_hash: str | None = None
    content_text: str | None = None
    content_excerpt: str | None = None
    normalized_text: str | None = None
    language: str | None = None
    engagement: dict[str, Any] | None = None
    keyword_hits: list[str] = Field(default_factory=list)
    raw_payload: dict[str, Any] = Field(default_factory=dict)
    deleted_at_source: bool = False
    created_at_source: datetime | None = None
    collected_at: datetime | None = None

    @field_validator("raw_payload", mode="before")
    @classmethod
    def sanitize_raw_payload(cls, value: Any) -> Any:
        return _sanitize_connector_log_value(value)


class ConnectorResult(BaseModel):
    model_config = ConfigDict(extra="forbid")

    platform: NonEmptyStr
    status: ConnectorStatus
    items: list[NormalizedRawItem] = Field(default_factory=list)
    items_collected: int = Field(default=0, ge=0)
    items_inserted: int = Field(default=0, ge=0)
    items_skipped: int = Field(default=0, ge=0)
    error_message: str | None = None
    rate_limit_state: RateLimitState | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)

    @field_validator("error_message", mode="before")
    @classmethod
    def sanitize_error_message(cls, value: Any) -> Any:
        if isinstance(value, str):
            return _redact_connector_log_text(value)
        return value

    @field_validator("metadata", mode="before")
    @classmethod
    def sanitize_metadata(cls, value: Any) -> Any:
        return _sanitize_connector_log_value(value)


class ProjectCollectionConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")

    project_id: UUID
    platform: NonEmptyStr
    keywords: list[str] = Field(default_factory=list)
    exclude_keywords: list[str] = Field(default_factory=list)
    languages: list[str] = Field(default_factory=list)
    max_items: int | None = Field(default=None, ge=1)


def _sanitize_connector_log_value(value: Any) -> Any:
    if isinstance(value, dict):
        sanitized: dict[str, Any] = {}
        for key, child in value.items():
            key_text = str(key)
            if _is_sensitive_connector_log_key(key_text):
                continue
            sanitized[_redact_connector_log_text(key_text)] = _sanitize_connector_log_value(
                child
            )
        return sanitized
    if isinstance(value, list | tuple | set):
        return [_sanitize_connector_log_value(item) for item in value]
    if isinstance(value, bytes):
        return _redact_connector_log_text(value.decode("utf-8", errors="replace"))
    if isinstance(value, str):
        return _redact_connector_log_text(value)
    return value


def _redact_connector_log_text(value: str) -> str:
    redacted = _BEARER_VALUE_PATTERN.sub(REDACTED, value)
    redacted = _ASSIGNMENT_SECRET_PATTERN.sub(REDACTED, redacted)
    redacted = _TOKEN_LIKE_PATTERN.sub(REDACTED, redacted)
    redacted = _SENSITIVE_WORD_PATTERN.sub(REDACTED, redacted)
    return redacted


def _is_sensitive_connector_log_key(key: str) -> bool:
    normalized = key.strip().lower().replace("-", "_")
    if normalized in _SENSITIVE_REQUEST_KEYS:
        return True
    return any(part in normalized for part in _SENSITIVE_KEY_PARTS)
