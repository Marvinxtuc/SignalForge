from __future__ import annotations

from uuid import uuid4

import pytest

from app.connectors.disabled import DisabledConnector
from app.connectors.types import ConnectorStatus, ProjectCollectionConfig


@pytest.mark.parametrize("platform", ["reddit", "product_hunt"])
def test_disabled_connector_returns_disabled_without_crashing(platform: str) -> None:
    connector = DisabledConnector(platform)
    config = ProjectCollectionConfig(project_id=uuid4(), platform=platform)

    result = connector.collect(config)

    assert result.platform == platform
    assert result.status == ConnectorStatus.DISABLED
    assert result.items == []
    assert result.items_collected == 0
    assert result.items_inserted == 0
    assert result.items_skipped == 0
    assert result.error_message
