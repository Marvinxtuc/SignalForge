#!/usr/bin/env python3
from __future__ import annotations

import json
import os
import sys
from pathlib import Path
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


ROOT = Path(__file__).resolve().parents[1]
API_ROOT_CANDIDATES = (ROOT, ROOT / "apps" / "api", Path("/app"))
for candidate in API_ROOT_CANDIDATES:
    if (candidate / "app").is_dir() and str(candidate) not in sys.path:
        sys.path.insert(0, str(candidate))


SMOKE_FLAG = "SIGNALFORGE_ALLOW_REAL_EMBEDDING_SMOKE"
REQUIRED_ENV = ("LLM_BASE_URL", "LLM_API_KEY", "EMBEDDING_MODEL")


def _enabled(name: str) -> bool:
    return os.environ.get(name, "").strip().lower() == "true"


def _missing_env() -> list[str]:
    return [name for name in REQUIRED_ENV if not os.environ.get(name, "").strip()]


def _status(status: str, message: str, details: dict[str, Any] | None = None) -> int:
    print(status)
    print(message)
    if details:
        for key, value in details.items():
            print(f"{key}: {value}")
    return 1 if status == "FAIL" else 0


def _base_url() -> str:
    return os.environ["LLM_BASE_URL"].rstrip("/")


def _request_embedding() -> tuple[int, dict[str, Any]]:
    payload = {
        "model": os.environ["EMBEDDING_MODEL"],
        "input": "SignalForge manual embedding smoke test.",
    }
    request = Request(
        f"{_base_url()}/embeddings",
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Accept": "application/json",
            "Content-Type": "application/json",
            "Authorization": "Bearer " + os.environ["LLM_API_KEY"],
        },
        method="POST",
    )
    with urlopen(request, timeout=20) as response:
        body = json.loads(response.read().decode("utf-8"))
        return response.status, body


def main() -> int:
    if not _enabled(SMOKE_FLAG):
        return _status(
            "DISABLED_MISSING_TOKEN",
            f"{SMOKE_FLAG}=true is required for real embedding smoke. No provider call was made.",
        )

    missing = _missing_env()
    if missing:
        return _status(
            "DISABLED_MISSING_TOKEN",
            "Embedding smoke is enabled but required env vars are missing.",
            {"missing_env": ", ".join(missing)},
        )

    try:
        status, body = _request_embedding()
    except HTTPError as exc:
        if exc.code in {401, 403}:
            return _status("PERMISSION_LIMITED", f"Embedding provider returned HTTP {exc.code}.")
        if exc.code == 429:
            return _status("RATE_LIMITED", "Embedding provider returned HTTP 429.")
        return _status("FAIL", f"Embedding provider returned HTTP {exc.code}.")
    except (OSError, URLError, TimeoutError) as exc:
        return _status("FAIL", f"Embedding provider smoke failed without exposing token: {type(exc).__name__}")

    data = body.get("data") if isinstance(body, dict) else None
    first = data[0] if isinstance(data, list) and data else {}
    embedding = first.get("embedding") if isinstance(first, dict) else None
    if status != 200 or not isinstance(embedding, list):
        return _status("FAIL", "Embedding provider response did not contain an embedding.")

    return _status(
        "PASS_REAL",
        "Embedding provider returned an embedding. Token was not printed.",
        {"dimension": len(embedding), "model": os.environ["EMBEDDING_MODEL"]},
    )


if __name__ == "__main__":
    raise SystemExit(main())
