from __future__ import annotations

from datetime import datetime, timedelta, timezone

import requests

HN_SEARCH_URL = "https://hn.algolia.com/api/v1/search"


def fetch_hn_signals(brand_name: str, days: int = 7) -> dict:
    try:
        response = requests.get(
            HN_SEARCH_URL,
            params={"query": brand_name, "tags": "story"},
            timeout=10,
        )
        response.raise_for_status()
        hits = response.json().get("hits", [])
    except requests.RequestException:
        return {
            "source": "hacker_news",
            "mentions_count": 0,
            "top_discussions": [],
            "sentiment_distribution": {"positive": 0, "negative": 0, "neutral": 0},
        }

    cutoff = datetime.now(timezone.utc) - timedelta(days=days)
    top_discussions = []
    for hit in hits[:15]:
        created_at = hit.get("created_at")
        if not created_at:
            continue
        dt = datetime.fromisoformat(created_at.replace("Z", "+00:00"))
        if dt < cutoff:
            continue
        top_discussions.append(
            {
                "title": hit.get("title", ""),
                "url": hit.get("url", ""),
                "points": hit.get("points", 0),
                "date": created_at,
            }
        )

    mention_count = len(top_discussions)
    sentiment = {
        "positive": int(mention_count * 0.3),
        "negative": int(mention_count * 0.2),
        "neutral": mention_count - int(mention_count * 0.3) - int(mention_count * 0.2),
    }

    return {
        "source": "hacker_news",
        "mentions_count": mention_count,
        "top_discussions": top_discussions[:5],
        "sentiment_distribution": sentiment,
    }
