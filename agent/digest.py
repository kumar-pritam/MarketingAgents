from __future__ import annotations

from datetime import datetime


def build_weekly_digest(own_brand_name: str, competitor_analyses: list[dict], actions: list[dict]) -> dict:
    executive_summary = []
    high_threat = [item for item in competitor_analyses if item.get("threat_level") == "high"]
    if high_threat:
        executive_summary.append(f"{len(high_threat)} competitor(s) are at high threat level this cycle.")
    active = [item for item in competitor_analyses if item.get("cvs_score", 0) > 40]
    executive_summary.append(f"{len(active)} competitor(s) are in Active+ velocity mode.")
    executive_summary.append("Top actions prioritize messaging gaps and fast-response landing pages.")

    return {
        "generated_at": datetime.utcnow().isoformat(),
        "own_brand": own_brand_name,
        "executive_summary": executive_summary,
        "competitor_analyses": competitor_analyses,
        "recommended_actions": actions,
    }
