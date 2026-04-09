from __future__ import annotations


def _bucket(score: float) -> str:
    if score <= 20:
        return "dormant"
    if score <= 40:
        return "steady"
    if score <= 60:
        return "active"
    if score <= 80:
        return "aggressive"
    return "sprint"


def compute_cvs(website_change_score: float, ad_volume_score: float, ad_theme_score: float, hn_score: float, new_page_score: float) -> tuple[float, str]:
    score = (
        website_change_score * 0.30
        + ad_volume_score * 0.25
        + ad_theme_score * 0.20
        + hn_score * 0.15
        + new_page_score * 0.10
    )
    score = round(max(0.0, min(100.0, score)), 2)
    return score, _bucket(score)
