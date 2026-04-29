#!/usr/bin/env python3
from __future__ import annotations

import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
API_ROOT_CANDIDATES = (ROOT, ROOT / "apps" / "api", Path("/app"))
for candidate in API_ROOT_CANDIDATES:
    if (candidate / "app").is_dir() and str(candidate) not in sys.path:
        sys.path.insert(0, str(candidate))


def main() -> int:
    from app.processing.llm_client import run_manual_llm_smoke

    result = run_manual_llm_smoke()
    print(result.status)
    print(result.message)
    for key, value in result.details.items():
        print(f"{key}: {value}")
    return 1 if result.status == "FAIL" else 0


if __name__ == "__main__":
    sys.exit(main())
