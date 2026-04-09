from __future__ import annotations

from dataclasses import dataclass
import logging
from pathlib import Path
from time import perf_counter
from typing import Callable
from uuid import uuid4

from agent.analyst import CompetitorAnalyst
from agent.ci_scorer import compute_cvs
from agent.digest import build_weekly_digest
from agent.hn_monitor import fetch_hn_signals
from agent.llm_runner import LLMRunner
from agent.parser import ResponseParser
from agent.query_builder import build_queries
from agent.report import ReportGenerator
from agent.scorer import score_audit
from agent.web_scraper import monitor_competitor_website
from integrations.meta_ads import fetch_meta_ads
from utils.models import AuditScore, BrandContext, ParsedResult, QueryItem
from utils.server_logger import get_logger, setup_server_logging

setup_server_logging(logging.DEBUG)
LOGGER = get_logger("main")


@dataclass(slots=True)
class AuditExecution:
    context: BrandContext
    queries: list[QueryItem]
    parsed_results: list[ParsedResult]
    score: AuditScore
    recommendations: list[dict[str, str]]
    runner_stats: dict
    gsc_insights: list[dict[str, str | int | float]]

    def to_dict(self) -> dict:
        return {
            "context": self.context.to_dict(),
            "queries": [query.to_dict() for query in self.queries],
            "parsed_results": [item.to_dict() for item in self.parsed_results],
            "score": self.score.to_dict(),
            "recommendations": self.recommendations,
            "runner_stats": self.runner_stats,
            "gsc_insights": self.gsc_insights,
        }


@dataclass(slots=True)
class CompetitorRunExecution:
    run_id: str
    own_brand: dict
    competitors: list[dict]
    digest: dict
    runtime_seconds: float

    def to_dict(self) -> dict:
        return {
            "run_id": self.run_id,
            "own_brand": self.own_brand,
            "competitors": self.competitors,
            "digest": self.digest,
            "runtime_seconds": self.runtime_seconds,
        }


def generate_query_set(context: BrandContext, total_queries: int = 10) -> list[QueryItem]:
    return build_queries(context=context, total_queries=total_queries)


def run_full_audit(
    context: BrandContext,
    queries: list[QueryItem],
    progress_callback: Callable[[int, int, str], None] | None = None,
    gsc_insights: list[dict[str, str | int | float]] | None = None,
    debug_callback: Callable[[str], None] | None = None,
) -> AuditExecution:
    started = perf_counter()
    LOGGER.info(
        "GEO_RUN_START brand=%s queries=%s competitors=%s",
        context.brand_name,
        len(queries),
        len(context.competitors),
    )
    if debug_callback:
        debug_callback(
            f"GEO_RUN_START brand={context.brand_name} queries={len(queries)} "
            f"competitors={context.competitors} category={context.category}"
        )

    runner = LLMRunner(usage_store=Path("data/openrouter_usage.log"))
    responses, runner_stats = runner.run_queries(
        queries,
        progress_callback=progress_callback,
        debug_callback=debug_callback,
    )
    LOGGER.info(
        "GEO_RUN_LLM_COMPLETE completed=%s failed=%s tokens=%s",
        runner_stats.completed,
        runner_stats.failed,
        runner_stats.total_tokens,
    )
    if debug_callback:
        debug_callback(
            f"GEO_RUN_LLM_COMPLETE completed={runner_stats.completed} failed={runner_stats.failed} "
            f"tokens={runner_stats.total_tokens}"
        )

    parser = ResponseParser(context)
    parsed_results = parser.batch_parse(responses)
    if debug_callback:
        debug_callback(f"GEO_PARSE_COMPLETE parsed_results={len(parsed_results)}")

    runtime_seconds = perf_counter() - started
    score = score_audit(
        context=context,
        queries=queries,
        parsed_results=parsed_results,
        total_tokens=runner_stats.total_tokens,
        runtime_seconds=runtime_seconds,
    )

    gsc_data = gsc_insights or []
    report_generator = ReportGenerator()
    recommendations = report_generator.generate(
        context,
        score,
        gsc_insights=gsc_data,
        debug_callback=debug_callback,
    )
    LOGGER.info(
        "GEO_RUN_END brand=%s visibility=%s ai_sov=%s runtime=%.2fs",
        context.brand_name,
        score.visibility_score,
        score.ai_sov_pct,
        runtime_seconds,
    )
    if debug_callback:
        debug_callback(
            f"GEO_RUN_END visibility_score={score.visibility_score} ai_sov={score.ai_sov_pct} "
            f"recommendations={len(recommendations)} runtime={round(runtime_seconds, 2)}"
        )

    return AuditExecution(
        context=context,
        queries=queries,
        parsed_results=parsed_results,
        score=score,
        recommendations=recommendations,
        runner_stats={
            "total_tokens": runner_stats.total_tokens,
            "completed": runner_stats.completed,
            "failed": runner_stats.failed,
            "requests_used_today": runner_stats.requests_used_today,
            "warnings": runner_stats.warnings,
        },
        gsc_insights=gsc_data,
    )


def _threat_level(cvs_score: float) -> str:
    if cvs_score >= 70:
        return "high"
    if cvs_score >= 40:
        return "medium"
    return "low"


def _build_ci_actions(sorted_by_threat: list[dict]) -> list[dict]:
    action_templates = [
        "Publish a competitor comparison page focused on {competitor} vs your brand with proof-backed differentiators.",
        "Launch a high-intent FAQ and objection-handling content cluster to counter {competitor} messaging.",
        "Refresh pricing and value communication to neutralize {competitor} offer framing.",
        "Ship an ad-response campaign with sharper USP hooks against {competitor} themes.",
        "Create a trust-proof landing page (reviews, outcomes, guarantees) to reduce {competitor} narrative advantage.",
    ]

    actions: list[dict] = []
    seen_action_keys: set[str] = set()
    seen_rationales: set[str] = set()

    for idx, item in enumerate(sorted_by_threat[:8]):
        competitor = item["competitor_name"]
        recommended = (item.get("recommended_response") or "").strip()
        strategic_text = (item.get("strategic_interpretation") or "").strip()

        if recommended:
            action_text = recommended
        else:
            template = action_templates[idx % len(action_templates)]
            action_text = template.format(competitor=competitor)

        # Ensure per-action competitor specificity even when LLM fallback is generic.
        if competitor.lower() not in action_text.lower():
            action_text = f"{action_text.rstrip('.')} for {competitor}."

        rationale = strategic_text or f"{competitor} is increasing visibility and strategic pressure in tracked channels."

        # Avoid repeated generic rationales.
        if rationale in seen_rationales:
            rationale = f"{rationale} Priority tied to {competitor}'s current movement velocity."
        seen_rationales.add(rationale)

        action_key = action_text.lower().strip()
        if action_key in seen_action_keys:
            continue
        seen_action_keys.add(action_key)

        actions.append(
            {
                "action": action_text,
                "urgency": "immediate" if item["cvs_score"] >= 60 else "this_week",
                "rationale": rationale,
            }
        )

        if len(actions) == 5:
            break

    if not actions:
        actions.append(
            {
                "action": "Run a focused competitor response sprint on messaging, pricing, and landing page differentiation.",
                "urgency": "this_week",
                "rationale": "No strong signal differentiation was detected, so a baseline response plan is recommended.",
            }
        )
    return actions


def run_competitor_intelligence(
    own_brand: dict,
    competitors: list[dict],
    use_hn_signals: bool,
    use_meta_ads: bool,
    progress_callback: Callable[[int, int, str], None] | None = None,
    debug_callback: Callable[[str], None] | None = None,
) -> CompetitorRunExecution:
    run_id = str(uuid4())
    started = perf_counter()
    analyst = CompetitorAnalyst()
    if debug_callback:
        debug_callback(
            f"CI_RUN_START run_id={run_id} brand={own_brand.get('name')} competitors={len(competitors)} "
            f"use_hn={use_hn_signals} use_meta={use_meta_ads}"
        )
    LOGGER.info(
        "CI_RUN_START run_id=%s brand=%s competitors=%s use_hn=%s use_meta=%s",
        run_id,
        own_brand.get("name"),
        len(competitors),
        use_hn_signals,
        use_meta_ads,
    )

    analyzed_competitors: list[dict] = []
    total = len(competitors)

    for idx, competitor in enumerate(competitors, start=1):
        name = competitor["name"]
        website = competitor["website"]
        if progress_callback:
            progress_callback(idx, total, f"Scanning {name} website")

        web_diffs = monitor_competitor_website(name, website, debug_callback=debug_callback)
        website_change_score = min(100.0, sum(item.get("change_pct", 0) for item in web_diffs) / 2)
        new_page_score = min(100.0, len([item for item in web_diffs if "new_page" in item.get("change_types", [])]) * 25)
        if debug_callback:
            debug_callback(
                f"CI_WEBSITE_SCORES competitor={name} website_change_score={website_change_score} "
                f"new_page_score={new_page_score}"
            )

        hn_signals = fetch_hn_signals(name) if use_hn_signals else {
            "source": "hacker_news",
            "mentions_count": 0,
            "top_discussions": [],
            "sentiment_distribution": {"positive": 0, "negative": 0, "neutral": 0},
        }
        hn_score = min(100.0, hn_signals.get("mentions_count", 0) * 12.5)
        if debug_callback:
            debug_callback(
                f"CI_HN_SIGNALS competitor={name} mentions={hn_signals.get('mentions_count', 0)} hn_score={hn_score}"
            )

        meta_data = fetch_meta_ads(name) if use_meta_ads else {
            "enabled": False,
            "total_active_ads": 0,
            "new_ads_since_last_run": 0,
            "top_ad_themes": [],
            "dominant_cta": "",
            "ads": [],
        }
        ad_volume_score = min(100.0, meta_data.get("total_active_ads", 0) * 5)
        ad_theme_score = min(100.0, len(meta_data.get("top_ad_themes", [])) * 20)
        if debug_callback:
            debug_callback(
                f"CI_AD_SIGNALS competitor={name} ads={meta_data.get('total_active_ads', 0)} "
                f"ad_volume_score={ad_volume_score} ad_theme_score={ad_theme_score}"
            )

        cvs_score, cvs_category = compute_cvs(
            website_change_score=website_change_score,
            ad_volume_score=ad_volume_score,
            ad_theme_score=ad_theme_score,
            hn_score=hn_score,
            new_page_score=new_page_score,
        )

        payload = {
            "competitor_name": name,
            "web_diffs": web_diffs,
            "hn_signals": hn_signals,
            "meta_ads": meta_data,
            "cvs_score": cvs_score,
            "cvs_category": cvs_category,
        }
        insight = analyst.analyze(
            own_brand=own_brand,
            competitor_payload=payload,
            debug_callback=debug_callback,
        )
        LOGGER.info(
            "CI_COMPETITOR_DONE run_id=%s competitor=%s cvs=%s category=%s",
            run_id,
            name,
            cvs_score,
            cvs_category,
        )
        if debug_callback:
            debug_callback(
                f"CI_ANALYSIS_RESULT competitor={name} cvs_score={cvs_score} cvs_category={cvs_category} "
                f"threat={_threat_level(cvs_score)}"
            )

        analyzed_competitors.append(
            {
                "competitor_name": name,
                "website": website,
                "cvs_score": cvs_score,
                "cvs_category": cvs_category,
                "threat_level": _threat_level(cvs_score),
                "what_changed": insight.get("what_changed", ""),
                "strategic_interpretation": insight.get("strategic_interpretation", ""),
                "speed_of_movement": insight.get("speed_of_movement", "moderate"),
                "recommended_response": insight.get("recommended_response", ""),
                "key_signals": insight.get("key_signals", []),
                "web_diffs": web_diffs,
                "hn_signals": hn_signals,
                "meta_ads": meta_data,
            }
        )

    sorted_by_threat = sorted(analyzed_competitors, key=lambda item: item["cvs_score"], reverse=True)
    actions = _build_ci_actions(sorted_by_threat)

    digest = build_weekly_digest(
        own_brand_name=own_brand.get("name", "Your Brand"),
        competitor_analyses=sorted_by_threat,
        actions=actions,
    )

    runtime = perf_counter() - started
    if debug_callback:
        debug_callback(
            f"CI_RUN_END run_id={run_id} competitors={len(sorted_by_threat)} "
            f"actions={len(actions)} runtime={round(runtime, 2)}"
        )
    LOGGER.info(
        "CI_RUN_END run_id=%s competitors=%s actions=%s runtime=%.2fs",
        run_id,
        len(sorted_by_threat),
        len(actions),
        runtime,
    )

    return CompetitorRunExecution(
        run_id=run_id,
        own_brand=own_brand,
        competitors=sorted_by_threat,
        digest=digest,
        runtime_seconds=round(runtime, 2),
    )
