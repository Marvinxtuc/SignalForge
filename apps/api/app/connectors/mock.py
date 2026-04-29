from __future__ import annotations

from datetime import UTC, datetime

from app.connectors.base import BaseConnector
from app.connectors.types import (
    ConnectorResult,
    ConnectorStatus,
    NormalizedRawItem,
    ProjectCollectionConfig,
)


class MockConnector(BaseConnector):
    platform = "mock"

    def __init__(self) -> None:
        super().__init__(self.platform)

    def collect(self, config: ProjectCollectionConfig) -> ConnectorResult:
        items = [
            NormalizedRawItem(
                platform=self.platform,
                platform_item_id="mock-001",
                source_url="https://example.local/mock/mock-001",
                author_hash="mock-author-alpha",
                content_text="SignalForge mock item for wallet onboarding feedback.",
                content_excerpt="Wallet onboarding feedback",
                normalized_text="signalforge mock item for wallet onboarding feedback",
                language="en",
                engagement={"score": 12, "comments": 3},
                keyword_hits=["wallet", "onboarding"],
                raw_payload={"source": "static_mock", "sequence": 1},
                created_at_source=datetime(2026, 1, 1, 9, 0, tzinfo=UTC),
            ),
            NormalizedRawItem(
                platform=self.platform,
                platform_item_id="mock-002",
                source_url="https://example.local/mock/mock-002",
                author_hash="mock-author-beta",
                content_text="Mock complaint about pricing clarity during checkout.",
                content_excerpt="Pricing clarity during checkout",
                normalized_text="mock complaint about pricing clarity during checkout",
                language="en",
                engagement={"score": 8, "comments": 1},
                keyword_hits=["pricing", "checkout"],
                raw_payload={"source": "static_mock", "sequence": 2},
                created_at_source=datetime(2026, 1, 2, 10, 30, tzinfo=UTC),
            ),
            NormalizedRawItem(
                platform=self.platform,
                platform_item_id="mock-003",
                source_url="https://example.local/mock/mock-003",
                author_hash="mock-author-gamma",
                content_text="Static request for better integration docs.",
                content_excerpt="Better integration documentation",
                normalized_text="static request for better integration docs",
                language="en",
                engagement={"score": 15, "comments": 5},
                keyword_hits=["integration", "documentation"],
                raw_payload={"source": "static_mock", "sequence": 3},
                created_at_source=datetime(2026, 1, 3, 14, 15, tzinfo=UTC),
            ),
        ]

        return ConnectorResult(
            platform=self.platform,
            status=ConnectorStatus.SUCCESS,
            items=items,
            items_collected=len(items),
        )
