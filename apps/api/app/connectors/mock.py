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
        item_prefix = str(config.project_id)
        items = [
            NormalizedRawItem(
                platform=self.platform,
                platform_item_id=f"{item_prefix}-mock-001",
                source_url="https://example.local/mock/mock-001",
                author_hash="mock-author-alpha",
                content_text="I need a less confusing onboarding flow for wallet setup and position tracking.",
                content_excerpt="Wallet onboarding feedback",
                normalized_text="i need a less confusing onboarding flow for wallet setup and position tracking",
                language="en",
                engagement={"score": 12, "comments": 3},
                keyword_hits=["wallet", "onboarding"],
                raw_payload={"source": "static_mock", "sequence": 1},
                created_at_source=datetime(2026, 1, 1, 9, 0, tzinfo=UTC),
            ),
            NormalizedRawItem(
                platform=self.platform,
                platform_item_id=f"{item_prefix}-mock-002",
                source_url="https://example.local/mock/mock-002",
                author_hash="mock-author-beta",
                content_text="Looking for an alternative to expensive market research tools with clearer pricing.",
                content_excerpt="Pricing clarity during checkout",
                normalized_text="looking for an alternative to expensive market research tools with clearer pricing",
                language="en",
                engagement={"score": 8, "comments": 1},
                keyword_hits=["pricing", "checkout"],
                raw_payload={"source": "static_mock", "sequence": 2},
                created_at_source=datetime(2026, 1, 2, 10, 30, tzinfo=UTC),
            ),
            NormalizedRawItem(
                platform=self.platform,
                platform_item_id=f"{item_prefix}-mock-003",
                source_url="https://example.local/mock/mock-003",
                author_hash="mock-author-gamma",
                content_text="We need better integration docs before we can adopt this workflow.",
                content_excerpt="Better integration documentation",
                normalized_text="we need better integration docs before we can adopt this workflow",
                language="en",
                engagement={"score": 15, "comments": 5},
                keyword_hits=["integration", "documentation"],
                raw_payload={"source": "static_mock", "sequence": 3},
                created_at_source=datetime(2026, 1, 3, 14, 15, tzinfo=UTC),
            ),
            NormalizedRawItem(
                platform=self.platform,
                platform_item_id=f"{item_prefix}-mock-004",
                source_url="https://example.local/mock/mock-004",
                author_hash="mock-author-delta",
                content_text="The current signal workflow is too noisy and hard to turn into next actions.",
                content_excerpt="Signal workflow is too noisy",
                normalized_text="the current signal workflow is too noisy and hard to turn into next actions",
                language="en",
                engagement={"score": 22, "comments": 7},
                keyword_hits=["workflow", "actions"],
                raw_payload={"source": "static_mock", "sequence": 4},
                created_at_source=datetime(2026, 1, 4, 16, 0, tzinfo=UTC),
            ),
            NormalizedRawItem(
                platform=self.platform,
                platform_item_id=f"{item_prefix}-mock-005",
                source_url="https://example.local/mock/mock-005",
                author_hash="mock-author-epsilon",
                content_text="I wish there was a simple report that tells me what to build next.",
                content_excerpt="Report should tell what to build next",
                normalized_text="i wish there was a simple report that tells me what to build next",
                language="en",
                engagement={"score": 18, "comments": 4},
                keyword_hits=["report", "next action"],
                raw_payload={"source": "static_mock", "sequence": 5},
                created_at_source=datetime(2026, 1, 5, 11, 45, tzinfo=UTC),
            ),
        ]

        return ConnectorResult(
            platform=self.platform,
            status=ConnectorStatus.SUCCESS,
            items=items,
            items_collected=len(items),
        )
