from __future__ import annotations

import json
import os
import urllib.error
import urllib.request
from dataclasses import dataclass
from typing import Any, Mapping


LLM_SMOKE_FLAG = "SIGNALFORGE_ALLOW_REAL_LLM_SMOKE"
LLM_PROCESSING_FLAG = "SIGNALFORGE_ALLOW_REAL_LLM_PROCESSING"
REQUIRED_LLM_ENV = ("LLM_BASE_URL", "LLM_API_KEY", "LLM_MODEL")
MAX_CLASSIFICATION_INPUT_CHARS = 4000
MAX_CLASSIFICATION_RESPONSE_BYTES = 65536


@dataclass(frozen=True)
class ManualLLMSmokeResult:
    status: str
    message: str
    details: dict[str, Any]


class LLMProviderError(RuntimeError):
    pass


def real_llm_smoke_enabled(env: Mapping[str, str] | None = None) -> bool:
    source = env or os.environ
    return source.get(LLM_SMOKE_FLAG, "").strip().lower() == "true"


def real_llm_processing_enabled(env: Mapping[str, str] | None = None) -> bool:
    source = env or os.environ
    return source.get(LLM_PROCESSING_FLAG, "").strip().lower() == "true"


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

    def classify_signal(self, text: str) -> str:
        payload = {
            "model": self.model,
            "messages": _classification_messages(text),
            "temperature": 0,
            "max_tokens": 500,
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
            with urllib.request.urlopen(request, timeout=self.timeout_seconds) as response:  # noqa: S310 - gated real LLM path.
                status_code = int(getattr(response, "status", 0) or 0)
                body = response.read(MAX_CLASSIFICATION_RESPONSE_BYTES).decode("utf-8", errors="replace")
        except urllib.error.HTTPError as exc:
            raise LLMProviderError(f"LLM provider HTTP {exc.code}: {_safe_excerpt(exc.read(512))}") from exc
        except Exception as exc:
            raise LLMProviderError(_redact(str(exc))) from exc

        if not 200 <= status_code < 300:
            raise LLMProviderError(f"LLM provider HTTP {status_code}: {_safe_excerpt(body)}")
        return _chat_message_content(body)


def _chat_completions_url(base_url: str) -> str:
    if base_url.endswith("/chat/completions"):
        return base_url
    if base_url.endswith("/v1"):
        return f"{base_url}/chat/completions"
    return f"{base_url}/v1/chat/completions"


def _classification_messages(text: str) -> list[dict[str, str]]:
    safe_text = str(text or "")[:MAX_CLASSIFICATION_INPUT_CHARS]
    schema = {
        "is_need_signal": True,
        "signal_type": "workflow_pain",
        "pain_level": 75,
        "clarity_score": 75,
        "urgency_score": 70,
        "business_relevance": 75,
        "model_confidence": 70,
        "signal_confidence": 72,
        "summary_zh": "一句中文摘要。",
        "recommended_action": "A short actionable recommendation.",
    }
    return [
        {
            "role": "system",
            "content": (
                "You classify user demand signals for a local product opportunity radar. "
                "Return only one JSON object. Do not include markdown. "
                "signal_type must be one of: complaint, feature_request, alternative_search, "
                "pricing_issue, security_concern, workflow_pain, integration_need, "
                "learning_barrier, positive_feedback, noise. "
                "All score fields must be integers from 0 to 100."
            ),
        },
        {
            "role": "user",
            "content": (
                "Classify this source text into the exact JSON schema below.\n"
                f"Schema example: {json.dumps(schema, ensure_ascii=False)}\n"
                f"Source text:\n{safe_text}"
            ),
        },
    ]


def _chat_message_content(body: str) -> str:
    try:
        payload = json.loads(body)
        choices = payload.get("choices")
        if not isinstance(choices, list) or not choices:
            raise LLMProviderError("LLM provider response missing choices")
        first = choices[0]
        if not isinstance(first, Mapping):
            raise LLMProviderError("LLM provider response choice is invalid")
        message = first.get("message")
        if not isinstance(message, Mapping):
            raise LLMProviderError("LLM provider response missing message")
        content = message.get("content")
        if not isinstance(content, str) or not content.strip():
            raise LLMProviderError("LLM provider response missing content")
        return content.strip()
    except json.JSONDecodeError as exc:
        raise LLMProviderError("LLM provider returned invalid JSON response") from exc


def _safe_excerpt(value: bytes | str) -> str:
    text = value.decode("utf-8", errors="replace") if isinstance(value, bytes) else value
    return _redact(text)[:500]


def _redact(text: str) -> str:
    redacted = str(text or "")
    for marker in ("Bearer ", "token", "secret", "api_key", "authorization"):
        redacted = redacted.replace(marker, "[REDACTED]")
        redacted = redacted.replace(marker.upper(), "[REDACTED]")
    return redacted
