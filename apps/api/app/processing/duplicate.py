from __future__ import annotations

import hashlib
from collections.abc import Callable, Iterable
from typing import TypeVar

from app.processing.cleaner import normalize_for_matching


T = TypeVar("T")


def duplicate_key(text: str | None) -> str:
    normalized = normalize_for_matching(text)
    return hashlib.sha256(normalized.encode("utf-8")).hexdigest()


def collapse_duplicate_texts(
    items: Iterable[T],
    *,
    text_getter: Callable[[T], str | None] | None = None,
) -> list[T]:
    getter = text_getter or _identity_text_getter
    seen: set[str] = set()
    unique_items: list[T] = []

    for item in items:
        key = duplicate_key(getter(item))
        if key in seen:
            continue
        seen.add(key)
        unique_items.append(item)

    return unique_items


def _identity_text_getter(value: T) -> str | None:
    if value is None:
        return None
    return str(value)
