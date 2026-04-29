from __future__ import annotations

from uuid import UUID, uuid4

from fastapi.testclient import TestClient
from sqlalchemy import func, select

from app.db.models import ClusterSignal, Embedding, Opportunity, Project, RawItem, Signal
from app.db.session import SessionLocal
from app.main import app


def client() -> TestClient:
    return TestClient(app)


def create_raw_only_project() -> str:
    assert SessionLocal is not None
    with SessionLocal() as db:
        project = Project(
            name=f"Phase 5 Processing Test {uuid4()}",
            description="Raw-only project for processing pipeline tests",
            platforms_enabled={"mock": True},
            collection_frequency="manual",
        )
        db.add(project)
        db.flush()
        rows = [
            ("mock-alerts", "I wish Polymarket had better alerts when odds change.", False),
            ("mock-portfolio", "Is there any tool to track my positions across prediction markets?", False),
            ("mock-noise", "Airdrop giveaway referral campaign hiring now", False),
            ("mock-security", "This wallet integration feels unsafe and confusing. email me at user@example.com", False),
            ("mock-alternative", "Looking for an alternative to expensive crypto analytics tools.", False),
            ("mock-deleted", "[deleted]", True),
        ]
        for index, (platform_item_id, text, deleted) in enumerate(rows):
            db.add(
                RawItem(
                    project_id=project.id,
                    platform="mock",
                    platform_item_id=f"{platform_item_id}-{uuid4()}",
                    source_url=f"https://example.com/phase5/{index}",
                    author_hash=f"author-{index}",
                    content_text=text,
                    content_excerpt=text[:140],
                    normalized_text=text.lower(),
                    language="en",
                    engagement={"score": 20 + index, "comments": index},
                    keyword_hits=["polymarket"] if index < 2 else ["crypto"],
                    raw_payload={"test": True},
                    deleted_at_source=deleted,
                )
            )
        db.commit()
        return str(project.id)


def delete_project(project_id: str) -> None:
    assert SessionLocal is not None
    with SessionLocal() as db:
        project = db.get(Project, UUID(project_id))
        if project is not None:
            db.delete(project)
            db.commit()


def counts(project_id: str) -> dict[str, int]:
    assert SessionLocal is not None
    project_uuid = UUID(project_id)
    with SessionLocal() as db:
        return {
            "signals": int(db.scalar(select(func.count()).select_from(Signal).where(Signal.project_id == project_uuid)) or 0),
            "embeddings": int(
                db.scalar(
                    select(func.count())
                    .select_from(Embedding)
                    .join(Signal, Signal.id == Embedding.signal_id)
                    .where(Signal.project_id == project_uuid)
                )
                or 0
            ),
            "cluster_signals": int(
                db.scalar(
                    select(func.count())
                    .select_from(ClusterSignal)
                    .join(Signal, Signal.id == ClusterSignal.signal_id)
                    .where(Signal.project_id == project_uuid)
                )
                or 0
            ),
            "opportunities": int(db.scalar(select(func.count()).select_from(Opportunity).where(Opportunity.project_id == project_uuid)) or 0),
            "high_value": int(
                db.scalar(
                    select(func.count())
                    .select_from(Signal)
                    .join(RawItem, RawItem.id == Signal.raw_item_id)
                    .where(Signal.project_id == project_uuid)
                    .where(Signal.pain_level >= 70)
                    .where(Signal.signal_confidence >= 60)
                    .where(RawItem.deleted_at_source.is_(False))
                )
                or 0
            ),
        }


def test_processing_pipeline_creates_signals_embeddings_clusters_and_opportunities() -> None:
    project_id = create_raw_only_project()
    try:
        response = client().post(f"/api/projects/{project_id}/process", json={"mode": "mock", "reprocess": False})
        payload = response.json()

        assert response.status_code == 200
        assert payload["status"] == "success"
        assert payload["total_raw_items"] == 6
        assert payload["processed_raw_items"] == 6
        assert payload["total_signals"] == 6
        assert payload["high_value_signals"] >= 2
        assert payload["embedding_count"] == 5
        assert payload["cluster_count"] >= 1
        assert payload["opportunity_count"] >= 1
        assert payload["top_5_high_value_signals"]
        assert all(item["source_url"].startswith("https://example.com/phase5/") for item in payload["top_5_high_value_signals"])
        assert all(item["summary_zh"] and "user@example.com" not in item["summary_zh"] for item in payload["top_5_high_value_signals"])
    finally:
        delete_project(project_id)


def test_processing_pipeline_is_idempotent() -> None:
    project_id = create_raw_only_project()
    try:
        first = client().post(f"/api/projects/{project_id}/process", json={"mode": "mock", "reprocess": False})
        assert first.status_code == 200
        first_counts = counts(project_id)

        second = client().post(f"/api/projects/{project_id}/process", json={"mode": "mock", "reprocess": False})
        assert second.status_code == 200
        second_counts = counts(project_id)

        assert second.json()["processed_in_run"] == 0
        assert first_counts == second_counts
    finally:
        delete_project(project_id)


def test_processing_summary_preserves_source_url_and_excludes_deleted_high_value() -> None:
    project_id = create_raw_only_project()
    try:
        processed = client().post(f"/api/projects/{project_id}/process", json={"mode": "fallback_only", "reprocess": False})
        assert processed.status_code == 200

        response = client().get(f"/api/projects/{project_id}/processing-summary")
        payload = response.json()

        assert response.status_code == 200
        assert payload["high_value_signals"] >= 2
        assert all(item["source_url"] != "https://example.com/phase5/5" for item in payload["top_5_high_value_signals"])
    finally:
        delete_project(project_id)


def test_processing_rejects_real_provider_modes() -> None:
    project_id = create_raw_only_project()
    try:
        for mode in ("real_llm", "real_embedding"):
            response = client().post(f"/api/projects/{project_id}/process", json={"mode": mode, "reprocess": False})
            payload = response.json()
            assert response.status_code == 409
            assert payload["error"]["code"] == "phase_not_available"
            assert payload["error"]["message"] == "Real LLM and embedding providers are manual-only in Phase 5."
    finally:
        delete_project(project_id)
