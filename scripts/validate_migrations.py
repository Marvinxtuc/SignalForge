#!/usr/bin/env python3
from __future__ import annotations

import sys
from typing import Any

from seed_demo_data import connect


TABLES = [
    "projects",
    "keywords",
    "platform_credentials",
    "collection_jobs",
    "collection_logs",
    "raw_items",
    "signals",
    "embeddings",
    "clusters",
    "cluster_signals",
    "opportunities",
]

EXPECTED_FKS = [
    ("keywords", ("project_id",), "projects"),
    ("collection_jobs", ("project_id",), "projects"),
    ("collection_logs", ("job_id",), "collection_jobs"),
    ("raw_items", ("project_id",), "projects"),
    ("signals", ("raw_item_id",), "raw_items"),
    ("signals", ("project_id",), "projects"),
    ("embeddings", ("signal_id",), "signals"),
    ("clusters", ("project_id",), "projects"),
    ("cluster_signals", ("cluster_id",), "clusters"),
    ("cluster_signals", ("signal_id",), "signals"),
    ("opportunities", ("project_id",), "projects"),
    ("opportunities", ("cluster_id",), "clusters"),
]

EXPECTED_CHECK_MARKERS = {
    "keywords": ["keyword_type"],
    "collection_jobs": ["pending", "partial_failed", "rate_limited", "manual", "scheduled"],
    "signals": ["feature_request", "security_concern", "pain_level", "signal_confidence"],
    "clusters": ["watching", "validating", "opportunity_score"],
    "opportunities": ["build_candidate", "content_candidate", "opportunity_score"],
}


def scalar(conn: Any, sql: str, params: tuple[Any, ...] = ()) -> Any:
    with conn.cursor() as cur:
        cur.execute(sql, params)
        row = cur.fetchone()
        return row[0] if row else None


def rows(conn: Any, sql: str, params: tuple[Any, ...] = ()) -> list[tuple[Any, ...]]:
    with conn.cursor() as cur:
        cur.execute(sql, params)
        return cur.fetchall()


def check(condition: bool, label: str, failures: list[str]) -> None:
    if condition:
        print(f"PASS: {label}")
    else:
        print(f"FAIL: {label}")
        failures.append(label)


def table_exists(conn: Any, table: str) -> bool:
    return bool(scalar(conn, "SELECT to_regclass(%s)", (f"public.{table}",)))


def column_not_null(conn: Any, table: str, column: str) -> bool:
    return scalar(
        conn,
        """
        SELECT is_nullable = 'NO'
        FROM information_schema.columns
        WHERE table_schema = 'public'
          AND table_name = %s
          AND column_name = %s
        """,
        (table, column),
    ) is True


def unique_columns(conn: Any, table: str) -> list[list[str]]:
    result = rows(
        conn,
        """
        SELECT array_agg(a.attname ORDER BY x.ord)::text[]
        FROM pg_class t
        JOIN pg_namespace n ON n.oid = t.relnamespace
        JOIN pg_index i ON i.indrelid = t.oid
        JOIN LATERAL unnest(i.indkey) WITH ORDINALITY AS x(attnum, ord) ON true
        JOIN pg_attribute a ON a.attrelid = t.oid AND a.attnum = x.attnum
        WHERE n.nspname = 'public'
          AND t.relname = %s
          AND i.indisunique
        GROUP BY i.indexrelid
        """,
        (table,),
    )
    return [list(row[0]) for row in result]


def pk_columns(conn: Any, table: str) -> list[str] | None:
    row = scalar(
        conn,
        """
        SELECT array_agg(a.attname ORDER BY x.ord)::text[]
        FROM pg_class t
        JOIN pg_namespace n ON n.oid = t.relnamespace
        JOIN pg_index i ON i.indrelid = t.oid
        JOIN LATERAL unnest(i.indkey) WITH ORDINALITY AS x(attnum, ord) ON true
        JOIN pg_attribute a ON a.attrelid = t.oid AND a.attnum = x.attnum
        WHERE n.nspname = 'public'
          AND t.relname = %s
          AND i.indisprimary
        GROUP BY i.indexrelid
        """,
        (table,),
    )
    return list(row) if row else None


def fk_pairs(conn: Any) -> set[tuple[str, tuple[str, ...], str]]:
    result = rows(
        conn,
        """
        SELECT
            src.relname AS source_table,
            array_agg(src_att.attname ORDER BY key_ord.ord)::text[] AS source_columns,
            dst.relname AS target_table
        FROM pg_constraint con
        JOIN pg_class src ON src.oid = con.conrelid
        JOIN pg_namespace src_ns ON src_ns.oid = src.relnamespace
        JOIN pg_class dst ON dst.oid = con.confrelid
        JOIN LATERAL unnest(con.conkey) WITH ORDINALITY AS key_ord(attnum, ord) ON true
        JOIN pg_attribute src_att ON src_att.attrelid = src.oid AND src_att.attnum = key_ord.attnum
        WHERE con.contype = 'f'
          AND src_ns.nspname = 'public'
        GROUP BY con.oid, src.relname, dst.relname
        """,
    )
    return {(row[0], tuple(row[1]), row[2]) for row in result}


def check_constraints(conn: Any) -> dict[str, list[str]]:
    result = rows(
        conn,
        """
        SELECT c.relname, pg_get_constraintdef(con.oid)
        FROM pg_constraint con
        JOIN pg_class c ON c.oid = con.conrelid
        JOIN pg_namespace n ON n.oid = c.relnamespace
        WHERE con.contype = 'c'
          AND n.nspname = 'public'
        """,
    )
    by_table: dict[str, list[str]] = {}
    for table, definition in result:
        by_table.setdefault(table, []).append(definition)
    return by_table


def validate() -> list[str]:
    failures: list[str] = []
    with connect() as conn:
        check(
            scalar(conn, "SELECT EXISTS (SELECT 1 FROM pg_extension WHERE extname = 'vector')"),
            "pgvector extension exists",
            failures,
        )

        for table in TABLES:
            check(table_exists(conn, table), f"table exists: {table}", failures)

        embedding_type = scalar(
            conn,
            """
            SELECT format_type(a.atttypid, a.atttypmod)
            FROM pg_class c
            JOIN pg_namespace n ON n.oid = c.relnamespace
            JOIN pg_attribute a ON a.attrelid = c.oid
            WHERE n.nspname = 'public'
              AND c.relname = 'embeddings'
              AND a.attname = 'embedding'
              AND NOT a.attisdropped
            """,
        )
        check(embedding_type == "vector(1536)", "embeddings.embedding is vector(1536)", failures)

        check(["platform", "platform_item_id"] in unique_columns(conn, "raw_items"), "raw_items unique(platform, platform_item_id)", failures)
        check(column_not_null(conn, "raw_items", "source_url"), "raw_items.source_url NOT NULL", failures)
        check(pk_columns(conn, "cluster_signals") == ["cluster_id", "signal_id"], "cluster_signals composite primary key", failures)

        fks = fk_pairs(conn)
        for table, columns, target in EXPECTED_FKS:
            check((table, columns, target) in fks, f"FK exists: {table}.{','.join(columns)} -> {target}", failures)

        checks = check_constraints(conn)
        for table, markers in EXPECTED_CHECK_MARKERS.items():
            definitions = " ".join(checks.get(table, []))
            for marker in markers:
                check(marker in definitions, f"CHECK marker exists on {table}: {marker}", failures)

    return failures


def main() -> int:
    try:
        failures = validate()
    except Exception as exc:  # noqa: BLE001 - command-line validation script
        print(f"FAIL: {exc}", file=sys.stderr)
        return 1

    if failures:
        print(f"FAIL: migration validation failed ({len(failures)} issue(s))", file=sys.stderr)
        return 1

    print("PASS: migration validation succeeded")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
