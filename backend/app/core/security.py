from __future__ import annotations

import re


URL_PATTERN = re.compile(r"^https?://[\w.-]+(?:\.[\w\.-]+)+[/\w\.-]*")


def is_valid_http_url(url: str) -> bool:
    return bool(URL_PATTERN.match(url.strip()))


def sanitize_text(value: str, max_len: int = 5000) -> str:
    text = value.strip().replace("\x00", "")
    return text[:max_len]
