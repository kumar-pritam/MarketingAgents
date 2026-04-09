from __future__ import annotations

import re
from collections.abc import Iterable


def normalize_text(text: str) -> str:
    return re.sub(r"\s+", " ", text.lower()).strip()


def dedupe_keep_order(items: Iterable[str]) -> list[str]:
    seen: set[str] = set()
    output: list[str] = []
    for item in items:
        value = item.strip()
        key = value.lower()
        if value and key not in seen:
            seen.add(key)
            output.append(value)
    return output
