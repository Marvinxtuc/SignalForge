from __future__ import annotations

import json

import pytest

from app.connectors.credential_resolver import resolve_connector_credentials
from app.connectors.http_client import ConnectorHTTPClient
from app.connectors.types import CredentialResolutionStatus


def test_reddit_missing_env_returns_missing_disabled_state() -> None:
    credentials = resolve_connector_credentials("reddit", env={})

    assert credentials.platform == "reddit"
    assert credentials.status == CredentialResolutionStatus.MISSING
    assert credentials.is_disabled is True
    assert credentials.get_authorization_header() is None
    assert credentials.safe_metadata() == {
        "credential_status": "missing",
        "missing_required_env_count": 3,
    }


def test_product_hunt_missing_env_returns_missing_disabled_state() -> None:
    credentials = resolve_connector_credentials("product_hunt", env={})

    assert credentials.platform == "product_hunt"
    assert credentials.status == CredentialResolutionStatus.MISSING
    assert credentials.is_disabled is True
    assert credentials.get_authorization_header() is None
    assert credentials.safe_metadata() == {
        "credential_status": "missing",
        "missing_required_env_count": 1,
    }


def test_product_hunt_env_token_is_excluded_from_serialized_model() -> None:
    secret = "ph-test-token"

    credentials = resolve_connector_credentials(
        "product_hunt",
        env={"PRODUCT_HUNT_TOKEN": secret},
    )

    assert credentials.status == CredentialResolutionStatus.AVAILABLE
    assert credentials.get_authorization_header() == f"Bearer {secret}"
    serialized = json.dumps(credentials.model_dump()).lower()
    assert secret not in serialized
    assert "bearer" not in serialized
    assert "product_hunt_token" not in serialized


def test_reddit_env_secrets_are_excluded_from_serialized_model() -> None:
    credentials = resolve_connector_credentials(
        "reddit",
        env={
            "REDDIT_CLIENT_ID": "reddit-client-id",
            "REDDIT_CLIENT_SECRET": "reddit-secret-value",
            "REDDIT_USER_AGENT": "SignalForge test",
        },
    )

    assert credentials.status == CredentialResolutionStatus.AVAILABLE
    assert credentials.get_client_id() == "reddit-client-id"
    assert credentials.get_client_secret() == "reddit-secret-value"
    assert credentials.get_user_agent() == "SignalForge test"
    serialized = json.dumps(credentials.model_dump()).lower()
    assert "reddit-secret-value" not in serialized
    assert "reddit_client_secret" not in serialized


def test_http_client_requires_timeout_and_rejects_authorization_header_input() -> None:
    with pytest.raises(ValueError, match="timeout is required"):
        ConnectorHTTPClient(timeout=None)  # type: ignore[arg-type]

    with ConnectorHTTPClient(timeout=5.0) as client:
        with pytest.raises(ValueError, match="authorization argument"):
            client.request(
                "GET",
                "https://example.test/no-call",
                headers={"Authorization": "Bearer secret-value"},
            )
