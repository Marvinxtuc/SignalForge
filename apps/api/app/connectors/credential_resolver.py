from __future__ import annotations

import os
from collections.abc import Mapping

from pydantic import SecretStr

from app.connectors.types import (
    CredentialResolutionStatus,
    ResolvedConnectorCredentials,
)


REDDIT_ENV_VARS = (
    "REDDIT_CLIENT_ID",
    "REDDIT_CLIENT_SECRET",
    "REDDIT_USER_AGENT",
)
PRODUCT_HUNT_ENV_VARS = ("PRODUCT_HUNT_TOKEN",)
REAL_PLATFORM_SMOKE_ENV = "SIGNALFORGE_ALLOW_REAL_PLATFORM_SMOKE"


def resolve_connector_credentials(
    platform: str,
    env: Mapping[str, str] | None = None,
) -> ResolvedConnectorCredentials:
    source_env = os.environ if env is None else env
    normalized_platform = platform.strip().lower().replace("-", "_")

    if normalized_platform == "reddit":
        return _resolve_reddit_credentials(source_env)
    if normalized_platform == "product_hunt":
        return _resolve_product_hunt_credentials(source_env)

    return ResolvedConnectorCredentials(
        platform=normalized_platform or "unknown",
        status=CredentialResolutionStatus.DISABLED,
        reason="unsupported_platform",
    )


def _resolve_reddit_credentials(env: Mapping[str, str]) -> ResolvedConnectorCredentials:
    missing_env = _missing_env(REDDIT_ENV_VARS, env)
    if missing_env:
        return ResolvedConnectorCredentials(
            platform="reddit",
            status=CredentialResolutionStatus.MISSING,
            missing_env=missing_env,
            reason="missing_required_env",
        )

    return ResolvedConnectorCredentials(
        platform="reddit",
        status=CredentialResolutionStatus.AVAILABLE,
        client_id=SecretStr(env["REDDIT_CLIENT_ID"].strip()),
        client_secret=SecretStr(env["REDDIT_CLIENT_SECRET"].strip()),
        user_agent=SecretStr(env["REDDIT_USER_AGENT"].strip()),
    )


def _resolve_product_hunt_credentials(env: Mapping[str, str]) -> ResolvedConnectorCredentials:
    missing_env = _missing_env(PRODUCT_HUNT_ENV_VARS, env)
    if missing_env:
        return ResolvedConnectorCredentials(
            platform="product_hunt",
            status=CredentialResolutionStatus.MISSING,
            missing_env=missing_env,
            reason="missing_required_env",
        )

    token = env["PRODUCT_HUNT_TOKEN"].strip()
    return ResolvedConnectorCredentials(
        platform="product_hunt",
        status=CredentialResolutionStatus.AVAILABLE,
        authorization_header=SecretStr(f"Bearer {token}"),
    )


def _missing_env(names: tuple[str, ...], env: Mapping[str, str]) -> tuple[str, ...]:
    return tuple(name for name in names if not env.get(name, "").strip())


def real_platform_smoke_enabled(env: Mapping[str, str] | None = None) -> bool:
    source_env = os.environ if env is None else env
    return source_env.get(REAL_PLATFORM_SMOKE_ENV, "").strip().lower() == "true"
