from __future__ import annotations

import difflib
from dataclasses import dataclass


@dataclass(slots=True)
class DiffResult:
    change_pct: float
    change_magnitude: str
    change_types: list[str]
    diff_summary: str


def _change_magnitude(change_pct: float) -> str:
    if change_pct < 5:
        return "none"
    if change_pct < 15:
        return "minor"
    if change_pct < 30:
        return "moderate"
    return "major"


def classify_change(previous_text: str, current_text: str) -> DiffResult:
    prev = previous_text or ""
    curr = current_text or ""

    if not prev and curr:
        return DiffResult(
            change_pct=100.0,
            change_magnitude="major",
            change_types=["new_page", "copy"],
            diff_summary="New page content detected for the first time.",
        )

    ratio = difflib.SequenceMatcher(None, prev, curr).ratio()
    change_pct = round((1 - ratio) * 100, 2)

    change_types: list[str] = []
    lower_curr = curr.lower()
    if any(term in lower_curr for term in ["price", "pricing", "plan", "annual", "monthly", "free trial"]):
        change_types.append("pricing")
    if any(term in lower_curr for term in ["cta", "book demo", "start free", "get started", "talk to sales"]):
        change_types.append("copy")
    if any(term in lower_curr for term in ["section", "feature", "module", "platform", "solution"]):
        change_types.append("structure")
    if not change_types and change_pct >= 5:
        change_types.append("copy")

    magnitude = _change_magnitude(change_pct)
    summary = f"Content delta is {change_pct}% ({magnitude})."

    return DiffResult(
        change_pct=change_pct,
        change_magnitude=magnitude,
        change_types=change_types,
        diff_summary=summary,
    )
