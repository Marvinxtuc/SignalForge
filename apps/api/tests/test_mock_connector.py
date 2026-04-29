from __future__ import annotations

from uuid import uuid4

from app.connectors.mock import MockConnector
from app.connectors.types import ConnectorStatus, ProjectCollectionConfig


def test_mock_connector_returns_normalized_static_items() -> None:
    connector = MockConnector()
    config = ProjectCollectionConfig(project_id=uuid4(), platform="mock")

    result = connector.collect(config)

    assert result.platform == "mock"
    assert result.status == ConnectorStatus.SUCCESS
    assert len(result.items) >= 3
    assert result.items_collected == len(result.items)

    for item in result.items:
        assert item.platform == "mock"
        assert item.platform_item_id
        assert item.source_url
