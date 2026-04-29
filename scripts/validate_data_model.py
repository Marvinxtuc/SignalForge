#!/usr/bin/env python3
from __future__ import annotations

import sys
from datetime import datetime, timezone
from typing import Any

from seed_demo_data import DEMO_PROJECT_NAME, RAW_ITEMS, connect, seed_demo_data, stable_uuid


def scalar(conn: Any, sql: str, params: tuple[Any, ...] = ()) -> Any:
    with conn.cursor() as cur:
        cur.execute(sql, params)
        row = cur.fetchone()
        return row[0] if row else None


def check(condition: bool, label: str, failures: list[str]) -> None:
    if condition:
        print(f"PASS: {label}")
    else:
        print(f"FAIL: {label}")
        failures.append(label)


def project_id(conn: Any) -> Any:
    return scalar(conn, "SELECT id FROM projects WHERE name = %s", (DEMO_PROJECT_NAME,))


def project_count(conn: Any, table: str, project: Any) -> int:
    if table == "cluster_signals":
        return int(
            scalar(
                conn,
                """
                SELECT count(*)
                FROM cluster_signals cs
                JOIN clusters c ON c.id = cs.cluster_id
                WHERE c.project_id = %s
                """,
                (project,),
            )
        )
    return int(scalar(conn, f"SELECT count(*) FROM {table} WHERE project_id = %s", (project,)))


def snapshot_counts() -> dict[str, int]:
    with connect() as conn:
        pid = project_id(conn)
        if pid is None:
            return {}
        return {
            "keywords": project_count(conn, "keywords", pid),
            "raw_items": project_count(conn, "raw_items", pid),
            "signals": project_count(conn, "signals", pid),
            "clusters": project_count(conn, "clusters", pid),
            "cluster_signals": project_count(conn, "cluster_signals", pid),
            "opportunities": project_count(conn, "opportunities", pid),
        }


def validate_seed_counts() -> list[str]:
    failures: list[str] = []
    with connect() as conn:
        pid = project_id(conn)
        check(pid is not None, f"demo project exists: {DEMO_PROJECT_NAME}", failures)
        if pid is None:
            return failures

        keyword_count = project_count(conn, "keywords", pid)
        raw_count = project_count(conn, "raw_items", pid)
        signal_count = project_count(conn, "signals", pid)
        high_value_count = int(
            scalar(
                conn,
                """
                SELECT count(*)
                FROM signals
                WHERE project_id = %s
                  AND is_need_signal = true
                  AND pain_level >= 70
                """,
                (pid,),
            )
        )
        cluster_count = project_count(conn, "clusters", pid)
        opportunity_count = project_count(conn, "opportunities", pid)
        null_source_count = int(scalar(conn, "SELECT count(*) FROM raw_items WHERE project_id = %s AND source_url IS NULL", (pid,)))

        check(keyword_count >= 9, "demo keywords include main, related, and exclude terms", failures)
        check(raw_count >= 5, "demo raw_items >= 5", failures)
        check(null_source_count == 0, "demo raw_items all have source_url", failures)
        check(signal_count >= 5, "demo signals >= 5", failures)
        check(high_value_count >= 2, "demo high value signals >= 2", failures)
        check(cluster_count >= 2, "demo clusters >= 2", failures)
        check(opportunity_count >= 1, "demo opportunities >= 1", failures)
    return failures


def validate_seed_idempotency() -> list[str]:
    failures: list[str] = []
    before = snapshot_counts()
    seed_demo_data()
    after = snapshot_counts()
    check(before == after and bool(before), "seed is idempotent with stable demo counts", failures)
    return failures


def expect_integrity_failure(label: str, operation: Any, failures: list[str]) -> None:
    try:
        with connect() as conn:
            try:
                operation(conn)
            except Exception:
                conn.rollback()
                print(f"PASS: {label}")
                return
            conn.rollback()
    except Exception as exc:  # noqa: BLE001 - validation should expose probe setup failures
        print(f"FAIL: {label} probe error: {exc}")
        failures.append(label)
        return

    print(f"FAIL: {label}")
    failures.append(label)


def duplicate_raw_item_probe(conn: Any) -> None:
    now = datetime.now(timezone.utc)
    pid = project_id(conn)
    with conn.cursor() as cur:
        cur.execute(
            """
            SELECT platform, platform_item_id
            FROM raw_items
            WHERE project_id = %s
            ORDER BY platform_item_id
            LIMIT 1
            """,
            (pid,),
        )
        platform, platform_item_id = cur.fetchone()
        cur.execute(
            """
            INSERT INTO raw_items (
                id, project_id, platform, platform_item_id, source_url, collected_at
            )
            VALUES (%s, %s, %s, %s, %s, %s)
            """,
            (stable_uuid("probe:duplicate"), pid, platform, platform_item_id, "https://example.com/duplicate-probe", now),
        )


def null_source_url_probe(conn: Any) -> None:
    now = datetime.now(timezone.utc)
    pid = project_id(conn)
    with conn.cursor() as cur:
        cur.execute(
            """
            INSERT INTO raw_items (
                id, project_id, platform, platform_item_id, source_url, collected_at
            )
            VALUES (%s, %s, 'reddit', 'null-source-url-probe', NULL, %s)
            """,
            (stable_uuid("probe:null-source"), pid, now),
        )


def invalid_opportunity_status_probe(conn: Any) -> None:
    now = datetime.now(timezone.utc)
    pid = project_id(conn)
    cluster_id = scalar(conn, "SELECT id FROM clusters WHERE project_id = %s LIMIT 1", (pid,))
    with conn.cursor() as cur:
        cur.execute(
            """
            INSERT INTO opportunities (
                id, project_id, cluster_id, title, status, created_at, updated_at
            )
            VALUES (%s, %s, %s, 'Invalid opportunity status probe', 'invalid_status', %s, %s)
            """,
            (stable_uuid("probe:bad-opportunity-status"), pid, cluster_id, now, now),
        )


def invalid_score_range_probe(conn: Any) -> None:
    now = datetime.now(timezone.utc)
    pid = project_id(conn)
    raw_item_id = scalar(conn, "SELECT id FROM raw_items WHERE project_id = %s LIMIT 1", (pid,))
    with conn.cursor() as cur:
        cur.execute(
            """
            INSERT INTO signals (
                id, raw_item_id, project_id, is_need_signal, signal_type, pain_level, status, created_at, updated_at
            )
            VALUES (%s, %s, %s, true, 'feature_request', 999, 'new', %s, %s)
            """,
            (stable_uuid("probe:bad-score"), raw_item_id, pid, now, now),
        )


def validate_constraints() -> list[str]:
    failures: list[str] = []
    expect_integrity_failure("duplicate raw_item is rejected and rolled back", duplicate_raw_item_probe, failures)
    expect_integrity_failure("raw_items.source_url NULL is rejected and rolled back", null_source_url_probe, failures)
    expect_integrity_failure("invalid opportunity status is rejected and rolled back", invalid_opportunity_status_probe, failures)
    expect_integrity_failure("invalid score range is rejected and rolled back", invalid_score_range_probe, failures)
    return failures


def main() -> int:
    try:
        failures = validate_seed_counts()
        failures.extend(validate_seed_idempotency())
        failures.extend(validate_constraints())
        failures.extend(validate_seed_counts())
    except Exception as exc:  # noqa: BLE001 - command-line validation script
        print(f"FAIL: {exc}", file=sys.stderr)
        return 1

    if failures:
        print(f"FAIL: data model validation failed ({len(failures)} issue(s))", file=sys.stderr)
        return 1

    print(f"PASS: data model validation succeeded for {len(RAW_ITEMS)} demo raw_items")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
