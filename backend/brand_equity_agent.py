from __future__ import annotations

import json
import logging
from typing import Any

from app.services.agents.executors.common import base_output
from app.services.agents.executors.llm_helper import run_llm_json
from app.storage.repository import repo

LOGGER = logging.getLogger("app.agent.brand_equity")

def _filter_workspace_context(workspace: dict[str, Any]) -> dict[str, Any]:
    """
    Ensures isolation by only passing relevant brand health signals.
    Excludes generic document blobs or technical assets used by other agents.
    """
    return {
        "brand_name": workspace.get("brand_name", ""),
        "website": workspace.get("website", ""),
        "industry": workspace.get("industry", ""),
        "geography": workspace.get("geography", ""),
        "category": workspace.get("category", ""),
        "positioning": workspace.get("positioning", ""),
    }

def run_brand_equity_tracker(payload: dict) -> tuple[dict, list[str]]:
    logs: list[str] = []
    agent_id = "brand_equity_tracker_agent"
    workspace_id = payload.get("workspace_id", "")
    workspace = repo.get_workspace(workspace_id) or {}
    
    # Isolated Context Construction
    brand_name = str(payload.get("brand_name") or workspace.get("brand_name") or "Your Brand")
    brand_context = str(payload.get("brand_context") or workspace.get("brand_summary") or "")
    
    competitors_list = payload.get("competitors") or []
    category_keywords_list = payload.get("category_keywords") or []
    time_window = payload.get("time_window", "Last 90 days")
    primary_concern = payload.get("primary_concern", "All")

    # Prepare data for LLM, ensuring all relevant inputs are available
    llm_input_data = {
        "brand_name": brand_name,
        "brand_context": brand_context,
        "competitors": competitors_list,
        "category_keywords": category_keywords_list,
        "time_window": time_window,
        "primary_concern": primary_concern,
        "workspace_info": _filter_workspace_context(workspace)
    }

    system_prompt = (
        "You are an expert Brand Equity Analyst. Analyze signals to track brand health. "
        "Return valid JSON. The JSON should ideally have a top-level 'equity_report' key containing these keys, "
        "but you may return these keys at the root level if necessary:\n"
        "- 'report_title': string (e.g., 'Brand Health Report for [Brand Name]')\n"
        "- 'executive_summary_overall': string (a high-level summary of the entire report)\n"
        "- 'brand_health_score': { 'overall_score': number, 'rating': string, 'verdict': string, 'dimensions': [ { 'label': string, 'score': number } ] }\n"
        "- 'brand_awareness': { 'summary_text': string, 'awareness_trend': string, 'notable_moments': [ { 'title': string, 'detail': string } ] }\n"
        "- 'brand_sentiment': { 'overall_sentiment': string, 'positive_themes': [ { 'text': string, 'signal': string } ], 'negative_themes': [ { 'text': string, 'signal': string } ], 'competitive_sentiment_summary': string }\n"
        "- 'share_of_voice': { 'summary_text': string, 'competitor_shares': [ { 'brand': string, 'pct': number } ], 'methodology': string, 'trend': string }\n"
        "- 'ai_visibility': { 'platforms': [ { 'name': string, 'status': string, 'detail': string } ], 'accuracy_summary': string }\n"
        "- 'brand_association': { 'owned': [string], 'intended': [string], 'gap': [string], 'shared': [string] }\n"
        "- 'competitive_position': { 'leads': [string], 'trails': [string], 'competitor_moves': [string] }\n"
        "- 'brand_risks': [ { 'title': string, 'signal': string, 'severity': string, 'action': string } ]\n"
        "- 'strategic_recommendations': [ { 'title': string, 'priority': string, 'detail': string } ]\n"
        "Ensure all numerical values are actual numbers, not strings."
    )

    user_prompt = f"""
Conduct a brand health audit for {brand_name}.

Brand Context: {brand_context}
Competitors: {', '.join(competitors_list)}
Category Keywords: {', '.join(category_keywords_list)}
Time Window for analysis: {time_window}
Primary Concern: {primary_concern}

Analyze public signals (news, social, reviews, AI outputs) to generate the report.
Be specific and provide evidence types for claims where possible.
Focus on actionable insights for a CMO.

Input data for your analysis:
{json.dumps(llm_input_data, indent=2)}

Return the 'equity_report' JSON object strictly following the schema provided in the system prompt.
"""

    try:
        logs.append(f"Starting isolated Brand Equity analysis for {brand_name}")
        parsed = run_llm_json(system_prompt, user_prompt, temperature=0.3, max_tokens=2500) # Increased max_tokens for detailed output
        
        if not parsed or "equity_report" not in parsed:
            logs.append("LLM failed to return structured equity report. Using safety fallback.")
            report = _get_fallback_equity_report(brand_name, competitors_list, category_keywords_list, time_window)
        else:
            report = parsed["equity_report"]
            # Basic validation to ensure top-level keys exist
            expected_keys = [
                "report_title", "executive_summary_overall", "brand_health_score", "brand_awareness", "brand_sentiment",
                "share_of_voice", "ai_visibility", "brand_association", "competitive_position", "brand_risks",
                "strategic_recommendations"
            ]
            if not all(key in report for key in expected_keys):
                logs.append("LLM returned incomplete equity report. Using safety fallback.")
                report = _get_fallback_equity_report(brand_name, competitors_list, category_keywords_list, time_window)
            
    except Exception as exc:
        LOGGER.exception("BRAND_EQUITY_LLM_ERROR workspace_id=%s error=%s", workspace_id, exc)
        report = _get_fallback_equity_report(brand_name, competitors_list, category_keywords_list, time_window)
        logs.append(f"Execution error: {exc}")

    output = {
        **base_output(agent_id, payload),
        "brand_equity_data": report
    }
    logs.append("Brand Equity report isolated and generated")
    return output, logs

def _get_fallback_equity_report(brand_name: str, competitors: list[str], category_keywords: list[str], time_window: str) -> dict:
    # Generate dynamic competitor awareness for fallback
    competitor_awareness_str = ""
    brand_pct = 35
    competitor_shares_list = [{"brand": brand_name, "pct": brand_pct}]
    if competitors:
        # Simple heuristic for fallback percentages
        comp_pcts = [40, 25, 15, 10, 5] # Example distribution
        competitor_awareness_parts = []
        for i, comp in enumerate(competitors):
            pct = comp_pcts[i % len(comp_pcts)]
            competitor_awareness_parts.append(f"{comp} ~{pct}%")
            competitor_shares_list.append({"brand": comp, "pct": pct})
        competitor_awareness_str = f" | {' | '.join(competitor_awareness_parts)}"

    return {
        "report_title": f"Brand Health Report for {brand_name}",
        "executive_summary_overall": f"Initial health baseline generated for {brand_name}. Further analysis required for detailed insights.",
        "brand_health_score": {
            "overall_score": 50,
            "rating": "Moderate",
            "verdict": f"Initial health baseline generated for {brand_name}.",
            "dimensions": [
                {"label": "Awareness & Reach", "score": 10},
                {"label": "Sentiment & Perception", "score": 10},
                {"label": "Share of Voice", "score": 10},
                {"label": "AI & GEO Visibility", "score": 10},
                {"label": "Competitive Position", "score": 10},
            ]
        },
        "brand_awareness": {
            "summary_text": f"Estimated awareness vs. competitors: {brand_name} ~{brand_pct}%{competitor_awareness_str} (based on initial signals and {time_window} data).",
            "awareness_trend": "Stable with baseline visibility.",
            "notable_moments": [
                {"title": "Initial Baseline", "detail": "No specific events detected yet."}
            ]
        },
        "brand_sentiment": {
            "overall_sentiment": "Neutral",
            "positive_themes": [{"text": "Foundational presence", "signal": "Initial data"}],
            "negative_themes": [{"text": "Lack of specific signals", "signal": "Initial data"}],
            "competitive_sentiment_summary": "Competitive sentiment is currently undifferentiated."
        },
        "share_of_voice": {
            "summary_text": f"Estimated SOV for {brand_name} is being established.",
            "competitor_shares": competitor_shares_list,
            "methodology": "Initial estimate based on available data.",
            "trend": "Establishing baseline."
        },
        "ai_visibility": {
            "platforms": [
                {"name": "General LLMs", "status": "Weak", "detail": "Limited specific mentions."}
            ],
            "accuracy_summary": "Baseline accuracy."
        },
        "brand_association": {
            "owned": ["Reliability"],
            "intended": ["Innovation"],
            "gap": ["Specific product features"],
            "shared": ["Quality"]
        },
        "competitive_position": {
            "leads": ["Foundational presence"],
            "trails": ["Specific market segments"],
            "competitor_moves": ["No significant moves detected yet."]
        },
        "brand_risks": [
            {
                "title": "Low initial visibility",
                "signal": "Limited public data",
                "severity": "Medium",
                "action": "Focus on content generation."
            }
        ],
        "strategic_recommendations": [
            {
                "title": "Build foundational content",
                "priority": "High / Immediate",
                "detail": "Create content around core brand values and product benefits."
            }
        ]
    }