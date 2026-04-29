from __future__ import annotations

from app.connectors.base import BaseConnector
from app.connectors.types import (
    ConnectorResult,
    ConnectorStatus,
    ProjectCollectionConfig,
)


class DisabledConnector(BaseConnector):
    platform = "disabled"

    def collect(self, config: ProjectCollectionConfig) -> ConnectorResult:
        return ConnectorResult(
            platform=self.platform,
            status=ConnectorStatus.DISABLED,
            items=[],
            items_collected=0,
            items_inserted=0,
            items_skipped=0,
            error_message=(
                f"Connector '{self.platform}' is disabled or not implemented."
            ),
        )
