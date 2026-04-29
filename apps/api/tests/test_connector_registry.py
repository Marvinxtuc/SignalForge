from __future__ import annotations

import sys
from types import ModuleType
from uuid import uuid4

import pytest

from app.connectors import BaseConnector, ConnectorRegistry, ConnectorResult, ConnectorStatus, ProjectCollectionConfig


class DummyConnector(BaseConnector):
    platform = "dummy"

    def collect(self, config: ProjectCollectionConfig) -> ConnectorResult:
        return ConnectorResult(platform=self.platform, status=ConnectorStatus.SUCCESS)


def test_registry_can_register_connector() -> None:
    registry = ConnectorRegistry()
    registry.register("dummy", DummyConnector)

    connector = registry.get("dummy")

    assert isinstance(connector, DummyConnector)
    config = ProjectCollectionConfig(project_id=uuid4(), platform="dummy")
    assert connector.collect(config).status == ConnectorStatus.SUCCESS


def test_registry_falls_back_to_lazy_disabled_connector(monkeypatch: pytest.MonkeyPatch) -> None:
    disabled_module = ModuleType("app.connectors.disabled")

    class FakeDisabledConnector(BaseConnector):
        def collect(self, config: ProjectCollectionConfig) -> ConnectorResult:
            return ConnectorResult(platform=self.platform, status=ConnectorStatus.DISABLED)

    disabled_module.DisabledConnector = FakeDisabledConnector  # type: ignore[attr-defined]
    monkeypatch.setitem(sys.modules, "app.connectors.disabled", disabled_module)
    registry = ConnectorRegistry()

    connector = registry.get("reddit")
    result = connector.collect(ProjectCollectionConfig(project_id=uuid4(), platform="reddit"))

    assert isinstance(connector, FakeDisabledConnector)
    assert connector.platform == "reddit"
    assert result.status == ConnectorStatus.DISABLED


def test_registry_fallback_supports_product_hunt(monkeypatch: pytest.MonkeyPatch) -> None:
    disabled_module = ModuleType("app.connectors.disabled")

    class FakeDisabledConnector(BaseConnector):
        def collect(self, config: ProjectCollectionConfig) -> ConnectorResult:
            return ConnectorResult(platform=self.platform, status=ConnectorStatus.DISABLED)

    disabled_module.DisabledConnector = FakeDisabledConnector  # type: ignore[attr-defined]
    monkeypatch.setitem(sys.modules, "app.connectors.disabled", disabled_module)
    registry = ConnectorRegistry()

    connector = registry.get("product_hunt")
    result = connector.collect(ProjectCollectionConfig(project_id=uuid4(), platform="product_hunt"))

    assert isinstance(connector, FakeDisabledConnector)
    assert connector.platform == "product_hunt"
    assert result.status == ConnectorStatus.DISABLED
