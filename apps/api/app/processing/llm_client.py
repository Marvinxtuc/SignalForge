from __future__ import annotations

import json
import os
import urllib.error
import urllib.request
from dataclasses import dataclass
from typing import Any, Mapping


LLM_SMOKE_FLAG = "SIGNALFORGE_ALLOW_REAL_LLM_SMOKE"
REQUIRED_LLM_ENV = ("LLM_BASE_URL", "LLM_API_KEY", "LLM_MODEL")


@dataclass(frozen=True)
class ManualLLMSmokeResult:
    status: str
    message: str
    details: dict[str, Any]


def real_llm_smoke_enabled(env: Mapping[str, str] | None = None) -> bool:
    source = env or os.environ
    return source.get(LLM_SMOKE_FLAG, "").strip().lower() == "true"


def missing_llm_env(env: Mapping[str, str] | None = None) -> list[str]:
    source = env or os.environ
    return [name for name in REQUIRED_LLM_ENV if not source.get(name, "").strip()]


def run_manual_llm_smoke(env: Mapping[str, str] | None = None, *, timeout_seconds: float = 15.0) -> ManualLLMSmokeResult:
    source = env or os.environ
    if not real_llm_smoke_enabled(source):
        return ManualLLMSmokeResult(
            status="DISABLED_MISSING_TOKEN",
            message="Real LLM smoke is disabled. Set SIGNALFORGE_ALLOW_REAL_LLM_SMOKE=true to allow a manual provider call.",
            details={"real_provider_called": False},
        )

    missing = missing_llm_env(source)
    if missing:
        return ManualLLMSmokeResult(
            status="DISABLED_MISSING_TOKEN",
            message="Real LLM smoke requires LLM_BASE_URL, LLM_API_KEY, and LLM_MODEL.",
            details={"missing_required_env_count": len(missing), "real_provider_called": False},
        )

    client = OpenAICompatibleLLMClient(
        base_url=source["LLM_BASE_URL"],
        api_key=source["LLM_API_KEY"],
        model=source["LLM_MODEL"],
        timeout_seconds=timeout_seconds,
    )
    return client.smoke()


class OpenAICompatibleLLMClient:
    def __init__(self, *, base_url: str, api_key: str, model: str, timeout_seconds: float = 15.0) -> None:
        self.base_url = base_url.strip().rstrip("/")
        self.api_key = api_key
        self.model = model.strip()
        self.timeout_seconds = timeout_seconds

    def smoke(self) -> ManualLLMSmokeResult:
        payload = {
            "model": self.model,
            "messages": [
                {
                    "role": "user",
                    "content": "Return a short JSON object with status set to ok.",
                }
            ],
            "temperature": 0,
            "max_tokens": 32,
        }
        request = urllib.request.Request(
            _chat_completions_url(self.base_url),
            data=json.dumps(payload).encode("utf-8"),
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
                "Accept": "application/json",
            },
            method="POST",
        )
        try:
            with urllib.request.urlopen(request, timeout=self.timeout_seconds) as response:  # noqa: S310 - manual smoke only.
                status_code = int(getattr(response, "status", 0) or 0)
                body = response.read(2048).decode("utf-8", errors="replace")
        except urllib.error.HTTPError as exc:
            status = "PERMISSION_LIMITED" if exc.code in {401, 403} else "RATE_LIMITED" if exc.code == 429 else "FAIL"
            return ManualLLMSmokeResult(
                status=status,
                message="Manual LLM smoke completed with provider error. Token was not printed.",
                details={"http_status": exc.code, "safe_body_excerpt": _safe_excerpt(exc.read(512))},
            )
        except Exception as exc:
            return ManualLLMSmokeResult(
                status="FAIL",
                message="Manual LLM smoke failed before a valid provider response.",
                details={"error": _redact(str(exc))},
            )

        return ManualLLMSmokeResult(
            status="PASS_REAL" if 200 <= status_code < 300 else "FAIL",
            message="Manual LLM smoke completed without printing tokens.",
            details={"http_status": status_code, "safe_body_excerpt": _safe_excerpt(body)},
        )


def _chat_completions_url(base_url: str) -> str:
    if base_url.endswith("/chat/completions"):
        return base_url
    if base_url.endswith("/v1"):
        return f"{base_url}/chat/completions"
    return f"{base_url}/v1/chat/completions"


def _safe_excerpt(value: bytes | str) -> str:
    text = value.decode("utf-8", errors="replace") if isinstance(value, bytes) else value
    return _redact(text)[:500]


def _redact(text: str) -> str:
    redacted = str(text or "")
    for marker in ("Bearer ", "token", "secret", "api_key", "authorization"):
        redacted = redacted.replace(marker, "[REDACTED]")
        redacted = redacted.replace(marker.upper(), "[REDACTED]")
    return redacted
