from __future__ import annotations

import json
import logging
import re
from typing import Any

from app.services.llm.openrouter_client import call_openrouter

LOGGER = logging.getLogger("app.brand_enrichment")

KNOWN_BRANDS: dict[str, dict[str, Any]] = {
    "maruti suzuki swift": {
        "website": "https://www.marutisuzuki.com/swift",
        "industry": "Automotive",
        "positioning": "A sporty and fuel-efficient hatchback for urban Indian drivers.",
        "key_pages": [
            "https://www.marutisuzuki.com/swift",
            "https://www.marutisuzuki.com/channels/arena/cars/swift",
        ],
    },
    "nike": {
        "website": "https://www.nike.com",
        "industry": "Sportswear",
        "positioning": "Performance-led sportswear brand combining innovation and global cultural relevance.",
        "key_pages": ["https://www.nike.com/", "https://www.nike.com/in/"],
    },
    "mamaearth": {
        "website": "https://mamaearth.in",
        "industry": "Beauty & Personal Care",
        "positioning": "Ingredient-led personal care brand focused on toxin-free and family-safe formulations.",
        "key_pages": ["https://mamaearth.in/", "https://mamaearth.in/product-category/skin-care"],
    },
}


def _slugify(name: str) -> str:
    return re.sub(r"[^a-z0-9]+", "", name.lower()).strip()


def _extract_json(text: str) -> dict[str, Any]:
    start = text.find("{")
    end = text.rfind("}")
    if start == -1 or end == -1 or end <= start:
        return {}
    raw = text[start : end + 1]
    try:
        data = json.loads(raw)
        return data if isinstance(data, dict) else {}
    except json.JSONDecodeError:
        return {}


def enrich_brand_profile(brand_name: str) -> dict[str, Any]:
    cleaned = brand_name.strip()
    if not cleaned:
        return {"brand_name": "", "website": "", "industry": "", "positioning": "", "key_pages": []}

    key = cleaned.lower()
    if key in KNOWN_BRANDS:
        return {"brand_name": cleaned, **KNOWN_BRANDS[key], "source": "rules"}

    heuristic = {
        "brand_name": cleaned,
        "website": f"https://www.{_slugify(cleaned)}.com",
        "industry": "Consumer Brand",
        "positioning": f"{cleaned} is a differentiated brand focused on value, trust, and outcomes for target customers.",
        "key_pages": [f"https://www.{_slugify(cleaned)}.com"],
        "source": "heuristic",
    }

    # Optional LLM enrichment if configured.
    try:
        prompt = (
            "You are a marketing brand profiler. Return ONLY JSON with keys: "
            "website, industry, positioning, key_pages (array of max 3 absolute URLs). "
            f"Brand: {cleaned}."
        )
        text = call_openrouter(
            [
                {"role": "system", "content": "Return strict JSON only."},
                {"role": "user", "content": prompt},
            ],
            temperature=0.2,
            max_tokens=300,
        )
        data = _extract_json(text)
        if data.get("website") and data.get("industry"):
            enriched = {
                "brand_name": cleaned,
                "website": str(data.get("website")),
                "industry": str(data.get("industry")),
                "positioning": str(data.get("positioning") or heuristic["positioning"]),
                "key_pages": [str(x) for x in (data.get("key_pages") or [])][:3],
                "source": "llm",
            }
            LOGGER.info("BRAND_ENRICHMENT_SUCCESS brand=%s source=llm", cleaned)
            return enriched
    except Exception as exc:
        LOGGER.info("BRAND_ENRICHMENT_FALLBACK brand=%s reason=%s", cleaned, exc)

    LOGGER.info("BRAND_ENRICHMENT_SUCCESS brand=%s source=%s", cleaned, heuristic["source"])
    return heuristic


def generate_brand_analysis(brand_name: str, category: str, geography: str) -> dict[str, str]:
    brand = brand_name.strip()
    cat = category.strip() or "General Category"
    geo = geography.strip() or "Global"
    if not brand:
        return {}

    fallback = {
        "brand_overview": f"{brand} operates in {cat} across {geo}. Publicly visible scale indicators should be validated from annual reports/news.",
        "brand_positioning": f"Likely positioned on trust and value within {cat}; perceived positioning may vary by audience segment and channel exposure.",
        "brand_identity_assets": "Core identity likely combines tagline, tone, and visual codes; consistency should be checked across web, social, and campaigns.",
        "brand_personality_archetype": "Probable archetype: Everyman/Creator depending on messaging; functional benefits seem stronger than emotional storytelling.",
        "brand_promise_values": "Promise appears outcome-led, but public evidence should be benchmarked against reviews and campaign claims.",
        "competitive_landscape": f"Top 3 competitors in {geo} should be mapped by pricing, availability, and message sharpness; whitespace often exists in proof-led differentiation.",
        "communication_campaigns": "Messaging themes likely span product utility and aspirational framing; consistency depends on media and agency execution.",
        "mental_availability_ceps": "Brand may own intent-driven CEPs but needs stronger broad-reach memory structures for non-intent discovery.",
        "ai_geo_visibility": "LLM visibility is typically uneven unless the brand has strong structured content, authority mentions, and comparison pages.",
        "brand_health_risks": "Risks include message sameness, promo over-reliance, and disruption from niche challengers with sharper positioning.",
    }

    prompt = (
        f'Analyze "{brand}" in "{cat}", "{geo}" using the framework below. '
        "Base your response on publicly available information, brand communications, and market signals. "
        "Keep each item short (1-2 lines max). Return ONLY JSON with keys: "
        "brand_overview, brand_positioning, brand_identity_assets, brand_personality_archetype, "
        "brand_promise_values, competitive_landscape, communication_campaigns, mental_availability_ceps, "
        "ai_geo_visibility, brand_health_risks."
    )

    try:
        text = call_openrouter(
            [
                {"role": "system", "content": "You are a senior brand strategist. Return strict short JSON only."},
                {"role": "user", "content": prompt},
            ],
            temperature=0.3,
            max_tokens=900,
        )
        parsed = _extract_json(text)
        if parsed:
            normalized = {k: str(parsed.get(k, fallback[k]))[:400] for k in fallback}
            LOGGER.info("BRAND_ANALYSIS_SUCCESS brand=%s category=%s geography=%s", brand, cat, geo)
            return normalized
    except Exception as exc:
        LOGGER.info("BRAND_ANALYSIS_FALLBACK brand=%s reason=%s", brand, exc)

    return fallback
