#!/usr/bin/env python3
from __future__ import annotations

import os
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
API_ROOT_CANDIDATES = (ROOT, ROOT / "apps" / "api", Path("/app"))
for candidate in API_ROOT_CANDIDATES:
    if (candidate / "app").is_dir() and str(candidate) not in sys.path:
        sys.path.insert(0, str(candidate))


SMOKE_FLAG = "SIGNALFORGE_ALLOW_REAL_PLATFORM_SMOKE"
WRITE_FLAG = "SIGNALFORGE_ALLOW_REAL_PLATFORM_WRITE"
PRODUCT_HUNT_REQUIRED_ENV = ("PRODUCT_HUNT_TOKEN",)


def _status_line(status: str, message: str, *, details: dict[str, Any] | None = None) -> int:
    print(status)
    print(message)
    if details:
        for key, value in details.items():
            print(f"{key}: {value}")
    return 1 if status == "FAIL" else 0


def _env_enabled(name: str) -> bool:
    return os.environ.get(name, "").strip().lower() == "true"


def _missing_env() -> list[str]:
    return [name for name in PRODUCT_HUNT_REQUIRED_ENV if not os.environ.get(name, "").strip()]


def _result_status_category(status: str) -> str:
    if status == "success":
        return "PASS_REAL"
    if status == "disabled":
        return "DISABLED_MISSING_TOKEN"
    if status == "permission_limited":
        return "PERMISSION_LIMITED"
    if status == "rate_limited":
        return "RATE_LIMITED"
    return "FAIL"


def _preview_connectivity() -> tuple[str, dict[str, Any]]:
    from app.connectors.product_hunt import ProductHuntConnector
    from app.connectors.types import ProjectCollectionConfig

    config = ProjectCollectionConfig(
        project_id="00000000-0000-0000-0000-000000000001",
        platform="product_hunt",
        keywords=["wallet", "onboarding"],
        max_items=3,
    )
    result = ProductHuntConnector(env=os.environ).collect(config)
    details = {
        "connector_status": result.status.value,
        "items_collected": result.items_collected,
        "items_previewed": min(len(result.items), 3),
        "first_source_url": result.items[0].source_url if result.items else "n/a",
        "write_enabled": _env_enabled(WRITE_FLAG),
    }
    return _result_status_category(result.status.value), details


def _write_demo_project() -> dict[str, Any]:
    from sqlalchemy import select

    from app.db.models import CollectionLog, Project
    from app.db.session import SessionLocal
    from app.services.collection_executor import execute_collection

    if SessionLocal is None:
        return {"write_status": "skipped", "reason": "DATABASE_URL is not configured"}

    with SessionLocal() as db:
        project = db.scalar(select(Project).where(Project.name == "Polymarket Opportunity Radar").limit(1))
        if project is None:
            return {"write_status": "skipped", "reason": "demo project not found"}
        job = execute_collection(db, project_id=project.id, execution_mode="product_hunt")
        log = db.scalar(
            select(CollectionLog)
            .where(CollectionLog.job_id == job.id)
            .where(CollectionLog.platform == "product_hunt")
            .limit(1)
        )
        return {
            "write_status": job.status,
            "demo_project_id": str(project.id),
            "items_inserted": log.items_inserted if log is not None else 0,
            "items_skipped": log.items_skipped if log is not None else 0,
        }


def main() -> int:
    if not _env_enabled(SMOKE_FLAG):
        return _status_line(
            "DISABLED_MISSING_TOKEN",
            "Product Hunt real-platform smoke is disabled. Set SIGNALFORGE_ALLOW_REAL_PLATFORM_SMOKE=true to allow official API calls.",
            details={"write_enabled": False},
        )

    missing = _missing_env()
    if missing:
        return _status_line(
            "DISABLED_MISSING_TOKEN",
            "Product Hunt smoke requires PRODUCT_HUNT_TOKEN.",
            details={"missing_required_env_count": len(missing)},
        )

    try:
        status, details = _preview_connectivity()
        if status == "PASS_REAL" and _env_enabled(WRITE_FLAG):
            details.update(_write_demo_project())
        elif status == "PASS_REAL":
            details["write_status"] = "skipped; set SIGNALFORGE_ALLOW_REAL_PLATFORM_WRITE=true to write raw_items"
        return _status_line(status, "Product Hunt manual smoke completed without printing tokens.", details=details)
    except Exception as exc:
        return _status_line("FAIL", "Product Hunt manual smoke failed.", details={"error": str(exc)})


if __name__ == "__main__":
    sys.exit(main())
