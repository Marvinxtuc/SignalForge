from __future__ import annotations

from app.connectors.disabled import DisabledConnector
from app.connectors.product_hunt import ProductHuntConnector
from app.connectors.reddit import RedditConnector
from app.connectors.registry import registry
from app.connectors.types import ConnectorStatus, ProjectCollectionConfig


def test_registry_returns_p0_connector_classes() -> None:
    assert isinstance(registry.get("reddit"), RedditConnector)
    assert isinstance(registry.get("product_hunt"), ProductHuntConnector)


def test_registry_normalizes_platform_names() -> None:
    assert isinstance(registry.get(" Reddit "), RedditConnector)
    assert isinstance(registry.get(" PRODUCT_HUNT "), ProductHuntConnector)


def test_registry_keeps_future_platforms_disabled() -> None:
    for platform in ("x", "discord", "unknown_future_platform"):
        connector = registry.get(platform)
        result = connector.collect(
            ProjectCollectionConfig(
                project_id="00000000-0000-0000-0000-000000000000",
                platform=platform,
            )
        )

        assert isinstance(connector, DisabledConnector)
        assert result.platform == platform
        assert result.status == ConnectorStatus.DISABLED
        assert result.items == []
