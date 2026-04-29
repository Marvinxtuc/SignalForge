#!/usr/bin/env python3
from __future__ import annotations

import os
import sys
import uuid
from datetime import datetime, timezone
from typing import Any


DEFAULT_DATABASE_URL = "postgresql+psycopg://signalforge:signalforge_dev_password@postgres:5432/signalforge"
DEMO_PROJECT_NAME = "Polymarket Opportunity Radar"


RAW_ITEMS = [
    (
        "reddit",
        "demo-polymarket-alerts",
        "I wish Polymarket had better alerts when odds change.",
        ["polymarket", "odds alert"],
        {"score": 42, "comments": 8},
    ),
    (
        "reddit",
        "demo-position-tracker",
        "Is there any tool to track my positions across prediction markets?",
        ["prediction market", "polymarket"],
        {"score": 31, "comments": 12},
    ),
    (
        "reddit",
        "demo-discord-alpha-noise",
        "Discord alpha groups are too noisy. I need summaries.",
        ["discord alpha"],
        {"score": 28, "comments": 5},
    ),
    (
        "product_hunt",
        "demo-wallet-safety",
        "This wallet integration feels unsafe and confusing.",
        ["polymarket"],
        {"votes": 18, "comments": 4},
    ),
    (
        "product_hunt",
        "demo-expensive-analytics",
        "Looking for an alternative to expensive crypto analytics tools.",
        ["kalshi", "prediction market"],
        {"votes": 25, "comments": 7},
    ),
]

SIGNAL_ROWS = [
    ("feature_request", 82, 86, 78, 80, "用户希望 Polymarket 在赔率变化时提供更好的提醒。", "Validate alerting workflow demand."),
    ("integration_need", 74, 82, 66, 78, "用户想跨预测市场跟踪自己的仓位。", "Explore portfolio tracking opportunity."),
    ("workflow_pain", 72, 75, 62, 70, "用户认为 Discord alpha 群噪声过高，需要摘要。", "Test summarized signal digest workflow."),
    ("security_concern", 68, 72, 61, 74, "用户觉得钱包集成不安全且难理解。", "Collect more wallet trust evidence."),
    ("alternative_search", 71, 80, 64, 76, "用户在寻找昂贵加密分析工具的替代品。", "Compare competitor pricing complaints."),
]

CLUSTERS = [
    ("Prediction market alerting", "Users need odds-change alerts and cross-market position tracking.", 81, {"reddit": 2}),
    ("Noisy crypto research workflows", "Users need safer, clearer, and less noisy research workflows.", 73, {"reddit": 1, "product_hunt": 2}),
]


def normalize_database_url(url: str) -> str:
    return (
        url.replace("postgresql+psycopg://", "postgresql://", 1)
        .replace("postgresql+psycopg2://", "postgresql://", 1)
        .replace("postgres+psycopg://", "postgresql://", 1)
    )


def database_url() -> str:
    return normalize_database_url(os.getenv("DATABASE_URL", DEFAULT_DATABASE_URL))


def load_psycopg() -> Any:
    try:
        import psycopg
    except ModuleNotFoundError as exc:
        raise RuntimeError("psycopg is required in the API container or host environment") from exc
    return psycopg


def connect() -> Any:
    return load_psycopg().connect(database_url())


def stable_uuid(name: str) -> str:
    return str(uuid.uuid5(uuid.NAMESPACE_URL, f"signalforge-demo:{name}"))


def delete_demo_data(conn: Any) -> None:
    with conn.cursor() as cur:
        cur.execute("SELECT id FROM projects WHERE name = %s", (DEMO_PROJECT_NAME,))
        project_ids = [row[0] for row in cur.fetchall()]

        for project_id in project_ids:
            cur.execute(
                """
                DELETE FROM cluster_signals
                WHERE cluster_id IN (SELECT id FROM clusters WHERE project_id = %s)
                   OR signal_id IN (SELECT id FROM signals WHERE project_id = %s)
                """,
                (project_id, project_id),
            )
            cur.execute(
                """
                DELETE FROM embeddings
                WHERE signal_id IN (SELECT id FROM signals WHERE project_id = %s)
                """,
                (project_id,),
            )
            cur.execute("DELETE FROM opportunities WHERE project_id = %s", (project_id,))
            cur.execute("DELETE FROM clusters WHERE project_id = %s", (project_id,))
            cur.execute("DELETE FROM signals WHERE project_id = %s", (project_id,))
            cur.execute("DELETE FROM raw_items WHERE project_id = %s", (project_id,))
            cur.execute(
                """
                DELETE FROM collection_logs
                WHERE job_id IN (SELECT id FROM collection_jobs WHERE project_id = %s)
                """,
                (project_id,),
            )
            cur.execute("DELETE FROM collection_jobs WHERE project_id = %s", (project_id,))
            cur.execute("DELETE FROM keywords WHERE project_id = %s", (project_id,))
            cur.execute("DELETE FROM projects WHERE id = %s", (project_id,))


def seed_demo_data() -> None:
    from psycopg.types.json import Jsonb

    now = datetime.now(timezone.utc)
    project_id = stable_uuid("project")

    with connect() as conn:
        delete_demo_data(conn)
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO projects (
                    id, name, description, platforms_enabled, collection_frequency, created_at, updated_at
                )
                VALUES (%s, %s, %s, %s, %s, %s, %s)
                """,
                (
                    project_id,
                    DEMO_PROJECT_NAME,
                    "Demo project for SignalForge Phase 1 data model validation.",
                    Jsonb({"reddit": True, "product_hunt": True}),
                    "manual",
                    now,
                    now,
                ),
            )

            keywords = [
                ("polymarket", "main"),
                ("prediction market", "main"),
                ("odds alert", "main"),
                ("kalshi", "related"),
                ("discord alpha", "related"),
                ("giveaway", "exclude"),
                ("airdrop", "exclude"),
                ("referral", "exclude"),
                ("hiring", "exclude"),
            ]
            for keyword, keyword_type in keywords:
                cur.execute(
                    """
                    INSERT INTO keywords (
                        id, project_id, keyword, keyword_type, language, enabled, created_at, updated_at
                    )
                    VALUES (%s, %s, %s, %s, 'all', true, %s, %s)
                    """,
                    (stable_uuid(f"keyword:{keyword}"), project_id, keyword, keyword_type, now, now),
                )

            job_id = stable_uuid("collection-job")
            cur.execute(
                """
                INSERT INTO collection_jobs (id, project_id, status, trigger_type, started_at, finished_at, created_at)
                VALUES (%s, %s, 'success', 'manual', %s, %s, %s)
                """,
                (job_id, project_id, now, now, now),
            )
            cur.execute(
                """
                INSERT INTO collection_logs (
                    id, job_id, platform, status, items_collected, items_inserted, items_skipped, created_at
                )
                VALUES (%s, %s, 'demo', 'success', 5, 5, 0, %s)
                """,
                (stable_uuid("collection-log"), job_id, now),
            )

            raw_ids: list[str] = []
            for index, (platform, platform_item_id, text, keyword_hits, engagement) in enumerate(RAW_ITEMS):
                raw_id = stable_uuid(f"raw:{platform_item_id}")
                raw_ids.append(raw_id)
                cur.execute(
                    """
                    INSERT INTO raw_items (
                        id, project_id, platform, platform_item_id, source_url, author_hash,
                        content_text, content_excerpt, normalized_text, language, engagement, keyword_hits,
                        raw_payload, deleted_at_source, created_at_source, collected_at
                    )
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, 'en', %s, %s, %s, false, %s, %s)
                    """,
                    (
                        raw_id,
                        project_id,
                        platform,
                        platform_item_id,
                        f"https://example.com/signalforge/demo/{index + 1}",
                        f"demo-author-{index + 1}",
                        text,
                        text[:140],
                        text.lower(),
                        Jsonb(engagement),
                        keyword_hits,
                        Jsonb({"demo": True}),
                        now,
                        now,
                    ),
                )

            signal_ids: list[str] = []
            for index, raw_id in enumerate(raw_ids):
                signal_type, pain, clarity, urgency, relevance, summary, action = SIGNAL_ROWS[index]
                signal_id = stable_uuid(f"signal:{index}")
                signal_ids.append(signal_id)
                cur.execute(
                    """
                    INSERT INTO signals (
                        id, raw_item_id, project_id, is_need_signal, signal_type, pain_level,
                        clarity_score, urgency_score, business_relevance, model_confidence,
                        signal_confidence, summary_zh, recommended_action, status, created_at, updated_at
                    )
                    VALUES (%s, %s, %s, true, %s, %s, %s, %s, %s, 82, 84, %s, %s, 'new', %s, %s)
                    """,
                    (
                        signal_id,
                        raw_id,
                        project_id,
                        signal_type,
                        pain,
                        clarity,
                        urgency,
                        relevance,
                        summary,
                        action,
                        now,
                        now,
                    ),
                )

            cluster_ids: list[str] = []
            for index, (title, description, score, diversity) in enumerate(CLUSTERS):
                cluster_id = stable_uuid(f"cluster:{index}")
                cluster_ids.append(cluster_id)
                evidence_count = 2 if index == 0 else 3
                cur.execute(
                    """
                    INSERT INTO clusters (
                        id, project_id, title, description, opportunity_score, status,
                        source_diversity, evidence_count, last_seen_at, created_at, updated_at
                    )
                    VALUES (%s, %s, %s, %s, %s, 'new', %s, %s, %s, %s, %s)
                    """,
                    (cluster_id, project_id, title, description, score, Jsonb(diversity), evidence_count, now, now, now),
                )

            for signal_index, signal_id in enumerate(signal_ids):
                cluster_id = cluster_ids[0] if signal_index < 2 else cluster_ids[1]
                cur.execute(
                    """
                    INSERT INTO cluster_signals (cluster_id, signal_id, similarity_score, created_at)
                    VALUES (%s, %s, %s, %s)
                    """,
                    (cluster_id, signal_id, 0.86 if signal_index < 2 else 0.83, now),
                )

            cur.execute(
                """
                INSERT INTO opportunities (
                    id, project_id, cluster_id, title, description, status, opportunity_score,
                    evidence_count, platform_distribution, last_seen_at, created_at, updated_at
                )
                VALUES (%s, %s, %s, %s, %s, 'new', 81, 2, %s, %s, %s, %s)
                """,
                (
                    stable_uuid("opportunity:alerts"),
                    project_id,
                    cluster_ids[0],
                    "Prediction market odds-change alerting",
                    "Build or validate a lightweight alert workflow for Polymarket odds changes.",
                    Jsonb({"reddit": 2}),
                    now,
                    now,
                    now,
                ),
            )
        conn.commit()


def main() -> int:
    try:
        seed_demo_data()
    except Exception as exc:  # noqa: BLE001 - command-line seed script
        print(f"FAIL: {exc}", file=sys.stderr)
        return 1

    print("PASS: demo data seeded")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
