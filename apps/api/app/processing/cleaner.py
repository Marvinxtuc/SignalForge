from __future__ import annotations

import html
import re
import unicodedata


_CONTROL_CHARS = re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]")
_ZERO_WIDTH = re.compile(r"[\u200b-\u200f\ufeff]")
_WHITESPACE = re.compile(r"\s+")
_URL_TRACKING_PARAMS = re.compile(r"([?&])(?:utm_[^=&\s]+|fbclid|gclid)=[^&\s]+&?")


def clean_text(text: str | None) -> str:
    if text is None:
        return ""

    value = unicodedata.normalize("NFKC", str(text))
    value = html.unescape(value)
    value = value.replace("\r\n", "\n").replace("\r", "\n")
    value = _CONTROL_CHARS.sub(" ", value)
    value = _ZERO_WIDTH.sub("", value)
    value = _strip_tracking_params(value)
    value = _WHITESPACE.sub(" ", value)
    return value.strip()


def build_excerpt(text: str | None, *, max_length: int = 280) -> str:
    cleaned = clean_text(text)
    if len(cleaned) <= max_length:
        return cleaned
    return cleaned[: max_length - 1].rstrip() + "..."


def normalize_for_matching(text: str | None) -> str:
    cleaned = clean_text(text).lower()
    cleaned = re.sub(r"https?://\S+", " ", cleaned)
    cleaned = re.sub(r"[^a-z0-9\u4e00-\u9fff]+", " ", cleaned)
    return _WHITESPACE.sub(" ", cleaned).strip()


def _strip_tracking_params(text: str) -> str:
    value = text
    previous = None
    while previous != value:
        previous = value
        value = _URL_TRACKING_PARAMS.sub(r"\1", value)
    return value.replace("? ", " ").replace("& ", " ")
