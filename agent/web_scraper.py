from __future__ import annotations

import hashlib
import json
import time
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup

from agent.diff_engine import DiffResult, classify_change

SNAPSHOT_DIR = Path("data/snapshots")
SNAPSHOT_DIR.mkdir(parents=True, exist_ok=True)

PAGE_PATHS = {
    "homepage": "",
    "pricing": "pricing",
    "features": "features",
    "about": "about",
}

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 13_0) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0 Safari/537.36"
}


def _slug(text: str) -> str:
    return "".join(ch.lower() if ch.isalnum() else "_" for ch in text).strip("_")


def _snapshot_file(competitor_name: str, page_type: str) -> Path:
    return SNAPSHOT_DIR / f"{_slug(competitor_name)}_{page_type}.json"


def _load_previous_snapshot(competitor_name: str, page_type: str) -> dict | None:
    target = _snapshot_file(competitor_name, page_type)
    if not target.exists():
        return None
    with target.open("r", encoding="utf-8") as file:
        payload = json.load(file)
    return payload[-1] if payload else None


def _append_snapshot(competitor_name: str, page_type: str, snapshot: dict) -> None:
    target = _snapshot_file(competitor_name, page_type)
    history = []
    if target.exists():
        with target.open("r", encoding="utf-8") as file:
            history = json.load(file)
    history.append(snapshot)
    with target.open("w", encoding="utf-8") as file:
        json.dump(history[-12:], file, indent=2)


def _fetch_page_text(url: str, retries: int = 3, debug_callback=None) -> str:
    for attempt in range(retries):
        try:
            if debug_callback:
                debug_callback(f"CI_SCRAPE_REQUEST url={url} attempt={attempt + 1}")
            response = requests.get(url, headers=HEADERS, timeout=12)
            if response.status_code >= 400:
                if debug_callback:
                    debug_callback(f"CI_SCRAPE_HTTP_ERROR url={url} status={response.status_code}")
                continue
            soup = BeautifulSoup(response.text, "html.parser")
            text = soup.get_text(" ", strip=True)
            if debug_callback:
                debug_callback(f"CI_SCRAPE_SUCCESS url={url} chars={len(text)}")
            return " ".join(text.split())
        except requests.RequestException as exc:
            if debug_callback:
                debug_callback(f"CI_SCRAPE_EXCEPTION url={url} error={exc}")
            if attempt == retries - 1:
                return ""
            time.sleep(2**attempt)
    return ""


def monitor_competitor_website(competitor_name: str, website: str, debug_callback=None) -> list[dict]:
    output: list[dict] = []
    if debug_callback:
        debug_callback(f"CI_SCRAPE_START competitor={competitor_name} website={website}")
    for page_type, page_path in PAGE_PATHS.items():
        url = urljoin(website.rstrip("/") + "/", page_path)
        page_text = _fetch_page_text(url, debug_callback=debug_callback)
        if not page_text:
            if debug_callback:
                debug_callback(f"CI_SCRAPE_SKIPPED competitor={competitor_name} page_type={page_type} reason=empty")
            continue

        previous = _load_previous_snapshot(competitor_name, page_type)
        previous_text = previous.get("content_text", "") if previous else ""
        diff: DiffResult = classify_change(previous_text, page_text)

        snapshot = {
            "competitor_name": competitor_name,
            "page_type": page_type,
            "url": url,
            "content_text": page_text,
            "content_hash": hashlib.sha256(page_text.encode("utf-8")).hexdigest(),
            "fetched_at": datetime.now(timezone.utc).isoformat(),
        }
        _append_snapshot(competitor_name, page_type, snapshot)

        output.append(
            {
                "competitor_name": competitor_name,
                "page_type": page_type,
                "url": url,
                "diff_summary": diff.diff_summary,
                "change_pct": diff.change_pct,
                "change_magnitude": diff.change_magnitude,
                "change_types": diff.change_types,
            }
        )
        if debug_callback:
            debug_callback(
                f"CI_DIFF competitor={competitor_name} page_type={page_type} change_pct={diff.change_pct} "
                f"magnitude={diff.change_magnitude} types={diff.change_types}"
            )

        time.sleep(2)

    if debug_callback:
        debug_callback(f"CI_SCRAPE_DONE competitor={competitor_name} pages_processed={len(output)}")
    return output
