from __future__ import annotations

from abc import ABC, abstractmethod

from app.connectors.types import ConnectorResult, ProjectCollectionConfig


class BaseConnector(ABC):
    platform: str

    def __init__(self, platform: str | None = None) -> None:
        if platform is not None:
            self.platform = platform

    @abstractmethod
    def collect(self, config: ProjectCollectionConfig) -> ConnectorResult:
        raise NotImplementedError
