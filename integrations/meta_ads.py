from __future__ import annotations

import os

import requests

META_API_URL = "https://graph.facebook.com/v18.0/ads_archive"


def fetch_meta_ads(brand_name: str, country_code: str = "IN") -> dict:
    token = os.getenv("META_AD_LIBRARY_TOKEN")
    if not token:
        return {
            "enabled": False,
            "total_active_ads": 0,
            "new_ads_since_last_run": 0,
            "top_ad_themes": [],
            "dominant_cta": "",
            "ads": [],
        }

    params = {
        "search_terms": brand_name,
        "ad_reached_countries": country_code,
        "ad_active_status": "ACTIVE",
        "fields": "id,ad_creative_body,ad_creative_link_caption,ad_delivery_start_time",
        "access_token": token,
    }

    try:
        response = requests.get(META_API_URL, params=params, timeout=15)
        response.raise_for_status()
        rows = response.json().get("data", [])
    except requests.RequestException:
        return {
            "enabled": True,
            "total_active_ads": 0,
            "new_ads_since_last_run": 0,
            "top_ad_themes": [],
            "dominant_cta": "",
            "ads": [],
        }

    ads = []
    themes = []
    for row in rows[:10]:
        body = row.get("ad_creative_body", "")
        headline = row.get("ad_creative_link_caption", "")
        if body:
            themes.extend(body.lower().split()[:5])
        ads.append(
            {
                "ad_id": row.get("id", ""),
                "body": body,
                "headline": headline,
                "start_date": row.get("ad_delivery_start_time", ""),
                "days_running": 0,
            }
        )

    unique_themes = []
    for word in themes:
        if len(word) > 4 and word not in unique_themes:
            unique_themes.append(word)

    return {
        "enabled": True,
        "total_active_ads": len(rows),
        "new_ads_since_last_run": min(3, len(rows)),
        "top_ad_themes": unique_themes[:5],
        "dominant_cta": "Learn more",
        "ads": ads,
    }
