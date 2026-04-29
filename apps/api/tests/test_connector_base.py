from __future__ import annotations

from uuid import uuid4

import pytest
from pydantic import ValidationError

from app.connectors import ConnectorResult, ConnectorStatus, NormalizedRawItem, ProjectCollectionConfig, RateLimitState


def test_normalized_raw_item_requires_source_url() -> None:
    with pytest.raises(ValidationError):
        NormalizedRawItem(platform="reddit", platform_item_id="abc")


def test_normalized_raw_item_rejects_null_source_url() -> None:
    with pytest.raises(ValidationError):
        NormalizedRawItem(platform="reddit", platform_item_id="abc", source_url=None)  # type: ignore[arg-type]


def test_normalized_raw_item_rejects_empty_source_url() -> None:
    with pytest.raises(ValidationError):
        NormalizedRawItem(platform="reddit", platform_item_id="abc", source_url="")


def test_connector_status_supports_required_values() -> None:
    assert {status.value for status in ConnectorStatus} == {
        "success",
        "disabled",
        "failed",
        "rate_limited",
        "permission_limited",
    }


def test_connector_result_requires_non_empty_platform() -> None:
    with pytest.raises(ValidationError):
        ConnectorResult(platform="", status=ConnectorStatus.SUCCESS)


def test_connector_result_has_required_default_counters() -> None:
    result = ConnectorResult(platform="reddit", status=ConnectorStatus.SUCCESS)

    assert result.items == []
    assert result.items_collected == 0
    assert result.items_inserted == 0
    assert result.items_skipped == 0
    assert result.error_message is None
    assert result.rate_limit_state is None


def test_connector_result_rejects_negative_counters() -> None:
    with pytest.raises(ValidationError):
        ConnectorResult(platform="reddit", status=ConnectorStatus.SUCCESS, items_collected=-1)

    with pytest.raises(ValidationError):
        ConnectorResult(platform="reddit", status=ConnectorStatus.SUCCESS, items_inserted=-1)

    with pytest.raises(ValidationError):
        ConnectorResult(platform="reddit", status=ConnectorStatus.SUCCESS, items_skipped=-1)


def test_connector_result_uses_rate_limit_state_field() -> None:
    rate_limit_state = RateLimitState(remaining=0, retry_after_seconds=60)
    result = ConnectorResult(
        platform="reddit",
        status=ConnectorStatus.RATE_LIMITED,
        rate_limit_state=rate_limit_state,
    )

    assert result.rate_limit_state == rate_limit_state

    with pytest.raises(ValidationError):
        ConnectorResult(platform="reddit", status=ConnectorStatus.RATE_LIMITED, rate_limit=rate_limit_state)  # type: ignore[call-arg]


def test_project_collection_config_contains_collection_filters_without_tokens() -> None:
    config = ProjectCollectionConfig(
        project_id=uuid4(),
        platform="reddit",
        keywords=["wallet"],
        exclude_keywords=["hiring"],
        languages=["en"],
        max_items=10,
    )

    assert config.keywords == ["wallet"]
    assert config.exclude_keywords == ["hiring"]
    assert config.languages == ["en"]
    assert "token" not in ProjectCollectionConfig.model_fields
