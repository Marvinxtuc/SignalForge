from __future__ import annotations

from collections.abc import Callable
from importlib import import_module
from typing import cast

from app.connectors.base import BaseConnector


ConnectorFactory = Callable[[], BaseConnector]


class ConnectorRegistry:
    def __init__(self) -> None:
        self._factories: dict[str, ConnectorFactory] = {}

    def register(self, platform: str, factory: ConnectorFactory | type[BaseConnector] | BaseConnector) -> None:
        normalized_platform = self._normalize_platform(platform)

        if isinstance(factory, BaseConnector):
            self._factories[normalized_platform] = lambda factory=factory: factory
            return

        self._factories[normalized_platform] = factory

    def get(self, platform: str) -> BaseConnector:
        normalized_platform = self._normalize_platform(platform)
        factory = self._factories.get(normalized_platform)
        if factory is None:
            return self._disabled_connector(normalized_platform)
        return factory()

    @staticmethod
    def _disabled_connector(platform: str) -> BaseConnector:
        disabled_module = import_module("app.connectors.disabled")
        disabled_connector = getattr(disabled_module, "DisabledConnector")
        return cast(BaseConnector, disabled_connector(platform))

    @staticmethod
    def _normalize_platform(platform: str) -> str:
        normalized = platform.strip()
        if not normalized:
            raise ValueError("platform must be a non-empty string")
        return normalized


registry = ConnectorRegistry()
