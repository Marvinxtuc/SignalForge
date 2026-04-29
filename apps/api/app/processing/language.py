from __future__ import annotations

import re


_CJK_PATTERN = re.compile(r"[\u4e00-\u9fff]")
_LATIN_PATTERN = re.compile(r"[A-Za-z]")


def detect_language(text: str | None) -> str:
    value = "" if text is None else str(text)
    if not value.strip():
        return "unknown"

    cjk_count = len(_CJK_PATTERN.findall(value))
    latin_count = len(_LATIN_PATTERN.findall(value))

    if cjk_count >= 2 and cjk_count >= latin_count * 0.35:
        return "zh"
    if latin_count >= 3:
        return "en"
    return "unknown"
