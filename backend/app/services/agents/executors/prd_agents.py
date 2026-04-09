from __future__ import annotations

import json
import logging
from typing import Any

from app.services.agents.executors.common import base_output
from app.services.agents.executors.llm_helper import run_llm_json
from app.storage.repository import repo

LOGGER = logging.getLogger("app.agent.prd")

SYSTEM_PROMPT = """You are a senior marketing strategist. Provide practical, evidence-based analysis.
Return ONLY valid JSON with no markdown or explanation.
The JSON must match the structure defined in the user's request.
If you cannot find specific data, provide reasonable estimates and flag them with [Estimated].
Do not leave arrays empty or strings blank unless explicitly told to do so."""

AGENT_PROMPTS = {
    "competitive_intelligence_agent": {
        "title": "Competitive Intelligence",
        "user_prompt": """You are a competitive intelligence analyst for {{brand_name}}.
Brand context: {{brand_context}}
Competitors: {{competitors}}
Focus: {{analysis_focus}}
Period: {{time_window}}
{{#if strategic_question}}Answer this: {{strategic_question}}{{/if}}

Search competitor websites, news, LinkedIn, job postings, ad libraries, reviews.

Return JSON with this exact structure:
{
  "executive_summary": "One sentence overview",
  "positioning_map": {"x_axis": "X axis label", "y_axis": "Y axis label", "brands": [{"name": "brand", "x": 5, "y": 7, "quadrant": "label"}]},
  "messaging_themes": [{"brand": "name", "theme": "theme", "evidence": "source"}],
  "recent_moves": [{"brand": "name", "move": "description", "signal": "what this means"}],
  "where_you_win": ["advantage 1", "advantage 2"],
  "where_vulnerable": ["vulnerability 1", "vulnerability 2"],
  "one_strategic_move": {"action": "description", "rationale": "why now"}
}
Max 350 words total.""",
    },
    "content_agent": {
        "title": "Content Generation",
        "user_prompt": """You are a senior brand copywriter for {{brand_name}}.
Brand context: {{brand_context}}
Content needed: {{content_type}}
Audience: {{target_audience}}
Objective: {{campaign_objective}}
Tone: {{tone}}
{{#if mandatories}}Mandatories: {{mandatories}}{{/if}}

For each content type requested, produce 2 variants.

Return JSON:
{
  "executive_summary": "Content overview",
  "content_variants": [{"type": "email", "variant_a": {"headlines": [], "body": "", "cta": ""}, "variant_b": {}}]
}
On-brand, benefit-led, no jargon. Each variant must feel distinct.""",
    },
    "brand_equity_tracker_agent": {
        "title": "Brand Health Pulse",
        "user_prompt": """You are a brand strategist auditing {{brand_name}}.
Brand context: {{brand_context}}
Competitors: {{competitors}}
Keywords: {{category_keywords}}
Period: {{time_window}}
Focus: {{primary_concern}}

Search news, media, social signals, reviews, analyst commentary.

Return JSON (max 400 words total):
{
  "executive_summary": "CMO-ready verdict",
  "health_score": {"overall": 65, "rating": "Moderate", "verdict": "one sentence"},
  "dimensions": [{"label": "Awareness", "score": 13}, {"label": "Sentiment", "score": 12}, {"label": "SOV", "score": 11}, {"label": "AI Visibility", "score": 10}, {"label": "Competitive Position", "score": 14}],
  "pulse": ["signal → implication 1", "signal → implication 2", "signal → implication 3", "signal → implication 4"],
  "top_risk": {"what": "description", "evidence": "source", "severity": "High", "action": "one action"},
  "top_opportunity": {"what": "description", "why_now": "reason", "action": "one action"},
  "ai_visibility": {"status": "Partial", "context": "where it appears", "vs_competitors": "who leads"},
  "associations": {"owned": ["word1", "word2", "word3", "word4", "word5"], "intended": ["word1", "word2"], "gap": "one line"},
  "top_actions": ["action → outcome 1", "action → outcome 2", "action → outcome 3"]
}
Lead with sharpest finding. No filler.""",
    },
    "geo_agent": {
        "title": "GEO / AI Visibility",
        "user_prompt": """You are a GEO analyst for {{brand_name}}.
Brand context: {{brand_context}}
Competitors: {{competitors}}
Queries: {{category_queries}}
Platforms: {{ai_platforms}}
Goal: {{visibility_goal}}

Search how {{brand_name}} and competitors appear in AI-generated content.

Return JSON:
{
  "executive_summary": "GEO overview",
  "ai_sov": [{"platform": "ChatGPT", "status": "Prominent", "your_brand": true, "competitors": ["CompA"]}],
  "query_visibility": [{"query_type": "category", "surfaces_brand": true, "competitors": ["CompA"]}],
  "representation_accuracy": {"correct": ["point1"], "wrong": ["point2"], "missing": ["point3"]},
  "sentiment_in_ai": {"brand": "Positive", "competitors": "vs competitor"},
  "top_actions": ["action 1", "action 2", "action 3"],
  "geo_health_score": {"score": 65, "rating": "Developing", "lever": "one key action"}
}
Max 350 words.""",
    },
    "creative_agent": {
        "title": "Creative Direction",
        "user_prompt": """You are a creative director for {{brand_name}}.
Brand context: {{brand_context}}
Brief: {{campaign_brief}}
Formats: {{format}}
{{#if reference_brands}}Reference: {{reference_brands}}{{/if}}
Territories: {{creative_territories}}

Generate {{creative_territories}} distinct creative territories.

Return JSON:
{
  "executive_summary": "Creative direction overview",
  "territories": [
    {
      "name": "Territory Name",
      "core_idea": "one sentence",
      "insight": "human truth",
      "execution": "how it comes to life",
      "sample_headline": "ready-to-present headline",
      "visual_direction": "describe in 2 sentences",
      "why_it_works": "strategic rationale"
    }
  ]
}
Territories must be genuinely distinct. No safe ideas.""",
    },
    "brand_voice_guardian_agent": {
        "title": "Brand Voice Audit",
        "user_prompt": """You are a brand copy editor for {{brand_name}}.
Brand context: {{brand_context}}
Voice guidelines: {{voice_guidelines}}
Content type: {{content_type}}
Strictness: {{strictness}}

Audit this content:
---
{{content_to_audit}}
---

Return JSON:
{
  "executive_summary": "Compliance overview",
  "compliance_rating": {"rating": "Partial", "summary": "one sentence"},
  "flagged_lines": [{"quote": "exact text", "violation": "reason", "rewrite": "corrected version"}],
  "what_works": ["strong line 1", "strong line 2"],
  "recommendation": "single most important fix"
}
Only flag genuine violations. Do not rewrite what doesn't need fixing.""",
    },
    "campaign_brief_generator_agent": {
        "title": "Campaign Brief",
        "user_prompt": """You are a strategic creative director writing a brief for {{brand_name}}.
Brand context: {{brand_context}}
Objective: {{business_objective}}
Audience: {{target_audience}}
Budget: {{budget_range}}
Duration: {{campaign_duration}}
Channels: {{channels}}
{{#if mandatories}}Mandatories: {{mandatories}}{{/if}}

Return JSON:
{
  "executive_summary": "Campaign overview",
  "campaign_objective": "one measurable sentence",
  "target_audience": "demographic + psychographic",
  "consumer_insight": "human truth that makes this land",
  "single_minded_proposition": "one sentence",
  "reasons_to_believe": ["proof 1", "proof 2", "proof 3"],
  "desired_response": "feel/think/do after campaign",
  "channel_roles": [{"channel": "TV", "role": "one line"}, {"channel": "Digital", "role": "one line"}],
  "success_metrics": {"leading": ["metric 1", "metric 2"], "lagging": ["metric 1", "metric 2"]},
  "creative_territories": [{"name": "Direction A", "idea": "one line"}, {"name": "Direction B", "idea": "one line"}]
}
Challenge any brief without real insight.""",
    },
    "landing_page_optimization_agent": {
        "title": "Landing Page Audit",
        "user_prompt": """You are a CRO specialist auditing a landing page for {{brand_name}}.
Brand context: {{brand_context}}
Page: {{page_url}}
Goal: {{conversion_goal}}
Audience: {{target_audience}}
{{#if current_conversion_issue}}Known issue: {{current_conversion_issue}}{{/if}}

Fetch and analyse the page. Audit against conversion best practices.

Return JSON:
{
  "executive_summary": "Audit overview",
  "conversion_audit": {"score": 65, "rating": "Needs Work", "verdict": "one sentence"},
  "above_fold": {"headline": "current", "assessment": "review", "suggested": "rewrite if needed"},
  "friction_points": [{"issue": "description", "impact": "how it kills conversions", "fix": "recommendation"}],
  "copy_improvements": [{"current": "text", "improved": "rewrite"}],
  "structural_recommendations": ["recommendation 1", "recommendation 2"],
  "quick_win": {"change": "one specific action", "impact": "expected improvement"}
}
Be specific. Quote exact lines. No generic CRO advice.""",
    },
    "persona_research_agent": {
        "title": "Buyer Persona",
        "user_prompt": """You are a consumer researcher building a persona for {{brand_name}}.
Brand context: {{brand_context}}
Category: {{product_category}}
Segment: {{target_segment}}
Geography: {{geography}}
{{#if pain_point}}Pain point: {{pain_point}}{{/if}}

Search Reddit, Amazon reviews, Quora, forums. Every insight from real sources.

Return JSON:
{
  "executive_summary": "Persona overview",
  "persona_snapshot": {"name": "Persona Name", "age": "28-35", "occupation": "description", "income": "range"},
  "motivations": ["motivation 1", "motivation 2"],
  "frustrations": [{"pain": "description", "source": "Reddit/news/review"}],
  "current_behaviour": {"how_they_solve": "current solution", "brands_used": ["brand1", "brand2"]},
  "switching_triggers": {"triggers_leave": ["reason1"], "triggers_stay": ["reason1"]},
  "voice_of_consumer": [{"quote": "verbatim style", "source": "source type"}],
  "channels": {"where": ["Instagram", "LinkedIn"], "trust": ["content type"]},
  "buying_journey": {"triggers": [], "blockers": [], "influencers": []}
}
Cite source type for all claims.""",
    },
    "social_listening_agent": {
        "title": "Social Sentiment",
        "user_prompt": """You are a social listening analyst for {{brand_name}}.
Brand context: {{brand_context}}
Track: {{keywords_to_track}}
Competitors: {{competitors}}
Period: {{time_window}}
Platforms: {{platforms}}

Search for brand mentions, conversations, sentiment signals.

Return JSON:
{
  "executive_summary": "Sentiment overview",
  "sentiment_score": {"overall": "Mixed", "positive_pct": 45, "neutral_pct": 35, "negative_pct": 20},
  "trending_themes": [{"theme": "name", "sentiment": "Positive", "description": "detail"}],
  "emerging_narratives": ["narrative 1", "narrative 2"],
  "competitor_sentiment": "brief comparison",
  "crisis_signals": ["flag 1", "flag 2"] or [],
  "engagement_opportunities": ["opportunity 1", "opportunity 2", "opportunity 3"]
}
Max 300 words. Flag [Estimated] where exact figures unavailable.""",
    },
    "seo_content_gap_agent": {
        "title": "SEO Content Gap",
        "user_prompt": """You are an SEO content strategist for {{brand_name}}.
Brand context: {{brand_context}}
Site: {{brand_url}}
Competitors: {{competitor_urls}}
Keywords: {{category_keywords}}
Funnel: {{funnel_focus}}
Formats: {{content_formats}}

Search top-ranking content, competitor topics, Reddit/forum queries.

Return JSON:
{
  "executive_summary": "Gap analysis overview",
  "content_gaps": [{"topic": "name", "intent": "informational", "priority": "High", "format": "Blog", "search_volume": "medium"}],
  "quick_wins": ["topic 1", "topic 2", "topic 3"],
  "content_briefs": [{"keyword": "target", "title": "suggested title", "h2s": ["H2 1", "H2 2"], "word_count": 1200, "cta": "recommendation"}],
  "competitor_strengths": [{"competitor": "name", "what_works": "reason", "why": "explanation"}],
  "calendar": ["Week 1: topic A", "Week 2: topic B", "etc"]
}
No generic content suggestions.""",
    },
    "localisation_cultural_fit_agent": {
        "title": "Cultural Fit Audit",
        "user_prompt": """You are a cultural strategist for {{brand_name}}.
Brand context: {{brand_context}}
Source: {{source_market}}
Target: {{target_market}}
Format: {{campaign_format}}
{{#if sensitivity_areas}}Check: {{sensitivity_areas}}{{/if}}

Campaign to audit:
---
{{campaign_copy}}
---

Search cultural norms, sensitivities, idioms, current events.

Return JSON:
{
  "executive_summary": "Cultural fit overview",
  "fit_rating": {"rating": "Needs Adaptation", "why": "one sentence"},
  "doesnt_translate": [{"element": "quote", "risk": "High", "reason": "explanation"}],
  "cultural_strengths": ["strength 1", "strength 2"],
  "local_language": ["idiom 1", "idiom 2"],
  "regulatory_flags": ["flag 1"] or [],
  "adapted_creative": {"headline": "rewritten", "cta": "rewritten"}
}
Specific to {{target_market}} only.""",
    },
    "customer_review_intelligence_agent": {
        "title": "Review Intelligence",
        "user_prompt": """You are a consumer insights analyst for {{brand_name}}.
Brand context: {{brand_context}}
Product: {{product_name}}
Platforms: {{platforms}}
Focus: {{focus_area}}
{{#if competitor_product}}Compare: {{competitor_product}}{{/if}}

Search reviews. Extract strategic signal - not summaries.

Return JSON:
{
  "executive_summary": "Review analysis overview",
  "praise_themes": [{"theme": "name", "frequency": "very common", "quote": "example"}],
  "complaint_themes": [{"theme": "name", "frequency": "common", "quote": "example", "systemic": true}],
  "unmet_needs": ["need 1", "need 2"],
  "voice_of_consumer": [{"quote": "verbatim", "source": "platform"}],
  "sentiment_trend": {"trend": "Improving", "evidence": "description"},
  "churn_signals": ["signal 1", "signal 2"],
  "vs_competitor": {"wins": ["area 1"], "loses": ["area 2"]} or null,
  "recommendation": "sharpest strategic action"
}
Distinguish systemic from isolated.""",
    },
    "experimentation_agent": {
        "title": "A/B Test Design",
        "user_prompt": """You are a growth experimentation strategist for {{brand_name}}.
Brand context: {{brand_context}}
Asset: {{page_or_asset}}
Goal: {{conversion_goal}}
Hypothesis: {{hypothesis}}
{{#if audience_segment}}Audience: {{audience_segment}}{{/if}}

Return JSON:
{
  "executive_summary": "Test design overview",
  "hypothesis_quality": {"rating": "Specific", "comment": "assessment", "sharpened": "improved version if needed"},
  "test_design": {"control": "description", "variant": "description"},
  "test_ideas": [
    {"what": "test element", "control": "control version", "variant": "variant version", "why_win": "rationale", "metric": "primary metric", "effort": "Low", "impact": "High"}
  ],
  "prioritization_matrix": [{"idea": 1, "effort": "Low", "impact": "High"}, {"idea": 2, "effort": "Medium", "impact": "Medium"}],
  "sample_size_note": "rough guidance",
  "what_not_to_test": ["idea 1", "idea 2"],
  "winner_recommendation": "which test to run first"
}
One clear winner recommendation.""",
    },
    "retail_shelf_intelligence_agent": {
        "title": "Retail Intelligence",
        "user_prompt": """You are a retail intelligence analyst for {{brand_name}}.
Brand context: {{brand_context}}
Product: {{product_sku}}
Platform: {{platform}}
Competitors: {{competitor_products}}
Search term: {{category_search_term}}

Search {{platform}} listings, reviews, pricing.

Return JSON:
{
  "executive_summary": "Retail overview",
  "listing_audit": [{"element": "title", "rating": "Strong", "fix": "recommendation"}],
  "review_comparison": [{"product": "name", "rating": 4.2, "count": 1200, "trend": "up"}],
  "customer_complaints": [{"complaint": "description", "count": "frequency", "both_products": false}],
  "pricing_position": {"position": "Mid", "vs_category": "aligned", "perception": "value-for-money"},
  "share_of_shelf": {"sku_count": 5, "vs_competitors": "parity", "page1_visibility": true},
  "recommendations": [{"action": "quick win", "priority": "High"}, {"action": "longer play", "priority": "Medium"}]
}
Specific to {{platform}}.""",
    },
    "market_sizing_agent": {
        "title": "Market Sizing",
        "user_prompt": """You are a market sizing analyst for {{brand_name}}.
Brand context: {{brand_context}}
Category: {{product_category}}
Geography: {{geography}}
Stage: {{market_stage}}
Purpose: {{sizing_purpose}}

Search industry reports, news, earnings calls, analyst estimates.

Return JSON:
{
  "executive_summary": "Market size overview",
  "tam": {"size": "$XXB", "methodology": "how calculated", "assumptions": ["assumption 1"]},
  "sam": {"size": "$XXB", "rationale": "scoping explanation"},
  "som": {"size": "$XXB", "year1": "$XX", "year2": "$XX", "year3": "$XX"},
  "growth_drivers": ["driver 1", "driver 2", "driver 3"],
  "constraints": ["constraint 1", "constraint 2", "constraint 3"],
  "sources": [{"source": "name", "credibility": "High", "year": 2024}],
  "confidence": {"level": "Medium", "why": "reason"}
}
Show your working. Flag estimated vs cited.""",
    },
    "sales_enablement_agent": {
        "title": "Sales Battle Card",
        "user_prompt": """You are a B2B product marketer building sales enablement for {{brand_name}}.
Brand context: {{brand_context}}
Competitor: {{competitor}}
Feature: {{product_feature}}
Buyer: {{buyer_persona}}
{{#if top_objection}}Top objection: {{top_objection}}{{/if}}

Search competitor website, G2, reviews, news, pricing pages.

Return JSON as a battle card:
{
  "executive_summary": "Battle card overview",
  "know_your_enemy": {"strengths": ["strength 1"], "weaknesses": ["weakness 1"]},
  "winning_narrative": "one sentence a sales rep can say on a call",
  "discovery_questions": ["question 1", "question 2", "question 3"],
  "objection_handlers": [
    {"objection": "{{competitor}} is cheaper", "response": "handler"},
    {"objection": "{{competitor}} is market leader", "response": "handler"},
    {"objection": "Switching cost too high", "response": "handler"}
  ],
  "proof_points": ["evidence 1", "evidence 2", "evidence 3"],
  "when_to_walk_away": "customer profile description"
}
Plain language only.""",
    },
    "influencer_evaluation_agent": {
        "title": "Influencer Evaluation",
        "user_prompt": """You are an influencer marketing strategist for {{brand_name}}.
Brand context: {{brand_context}}
Handles: {{influencer_handles}}
Platform: {{platform}}
Objective: {{campaign_objective}}
Tier: {{budget_tier}}
{{#if conflict_check}}Conflict check: {{conflict_check}}{{/if}}

Search public profiles, recent content, past collabs, engagement.

Return JSON for each influencer:
{
  "executive_summary": "Evaluation overview",
  "evaluations": [{
    "handle": "@influencer",
    "audience_profile": {"demographics": "description", "geography": "primary regions"},
    "content_quality": {"rating": "Strong", "strengths": ["strength"], "weaknesses": ["weakness"]},
    "brand_alignment": {"rating": "High", "reason": "explanation"},
    "engagement_quality": {"rating": "High", "signals": "genuine vs inflated"},
    "past_collabs": {"categories": ["category1"], "conflict_result": "Clear"},
    "red_flags": ["flag 1"] or [],
    "collab_format": {"best_for": "format", "concept": "one idea"},
    "verdict": {"status": "Pursue", "rationale": "one line"}
  }]
}
Be direct. Flag risks clearly.""",
    },
    "pr_narrative_agent": {
        "title": "PR & Narrative",
        "user_prompt": """You are a PR strategist for {{brand_name}}.
Brand context: {{brand_context}}
Objective: {{comms_objective}}
Story type: {{story_type}}
{{#if target_media}}Target media: {{target_media}}{{/if}}
{{#if news_hook}}Hook: {{news_hook}}{{/if}}

Search current news cycles, cultural moments, trending conversations.

Return JSON:
{
  "executive_summary": "PR opportunities overview",
  "newsjacking_opportunities": [{"story": "current event", "angle": "why brand has right to play", "proposed": "angle", "urgency": "Act now"}],
  "proactive_pitches": [{"headline": "pitch headline", "hook": "reason", "publication": "type"}],
  "thought_leadership": {"angle": "long-form topic", "format": "recommendation"},
  "narrative_risks": ["risk 1", "risk 2"],
  "media_targets": [{"publication": "name", "angle": "what to pitch"}] or []
}
Be timely. Generic PR advice has zero value.""",
    },
    "marketing_compliance_agent": {
        "title": "Compliance Audit",
        "user_prompt": """You are a marketing compliance specialist for {{brand_name}}.
Brand context: {{brand_context}}
Market: {{target_market}}
Sector: {{sector}}
Format: {{content_format}}
{{#if specific_concern}}Concern: {{specific_concern}}{{/if}}

Content to audit:
---
{{content_to_audit}}
---

Apply ASCI/FTC/ASA/EU Directive/NMC as relevant.

Return JSON:
{
  "executive_summary": "Compliance overview",
  "risk_rating": {"rating": "Review Required", "summary": "one sentence"},
  "flagged_claims": [{"quote": "exact text", "regulation": "which rule", "risk": "High", "rewrite": "safe version"}],
  "required_disclosures": ["disclosure 1"],
  "sector_flags": ["flag 1"] or [],
  "whats_clean": ["clean claim 1", "clean claim 2"],
  "specific_answer": "answer to {{specific_concern}}" or null
}
Flag genuine risks only. Advisory only.""",
    },
    "campaign_qa_agent": {
        "title": "Campaign QA",
        "user_prompt": """You are a campaign quality analyst for {{brand_name}}.
Brand context: {{brand_context}}
Objective: {{campaign_objective}}
Audience: {{target_audience}}
Channels: {{channels}}

Campaign assets to QA:
---
{{campaign_assets}}
---

Return JSON:
{
  "executive_summary": "QA overview",
  "qa_score": {"score": 75, "rating": "Needs Work", "verdict": "one sentence"},
  "message_consistency": {"consistent": true, "flags": ["contradiction 1"] or []},
  "brand_fit": {"rating": "On-brand", "off_lines": ["line 1"] or []},
  "audience_alignment": {"rating": "Aligned", "gaps": ["gap 1"] or []},
  "cta_audit": {"clear": true, "consistent": true, "optimization": "suggestion"},
  "channel_adaptation": [{"channel": "Instagram", "adapted": true, "issues": []}],
  "top_fixes": [{"fix": "description", "impact": "High", "channel": "affected"}]
}
No generic feedback. Quote exact lines.""",
    },
    "visual_identity_audit_agent": {
        "title": "Visual Identity Audit",
        "user_prompt": """You are a brand design strategist auditing {{brand_name}}.
Brand context: {{brand_context}}
Website: {{brand_url}}
Social: {{social_handles}}
Focus: {{audit_focus}}
{{#if visual_guidelines}}Standards: {{visual_guidelines}}{{/if}}

Search and fetch brand digital touchpoints. Assess visual consistency.

Return JSON:
{
  "executive_summary": "Visual audit overview",
  "consistency_scores": [{"touchpoint": "Website", "score": 75, "average": 70}],
  "whats_working": ["element 1", "element 2", "element 3"],
  "inconsistencies": [{"where": "page/post", "issue": "problem", "severity": "High"}],
  "distinctive_assets": ["ownable element 1", "ownable element 2"],
  "vs_competitors": "differentiation assessment",
  "top_fixes": [{"fix": "description", "touchpoint": "affected", "impact": "High"}]
}
Be specific. Name exact pages.""",
    },
    "pricing_intelligence_agent": {
        "title": "Pricing Intelligence",
        "user_prompt": """You are a pricing strategist for {{brand_name}}.
Brand context: {{brand_context}}
Product: {{product_name}}
Competitors: {{competitors}}
Market: {{market}}
Question: {{pricing_question}}

Search pricing pages, e-commerce, news, reviews, analyst commentary.

Return JSON:
{
  "executive_summary": "Pricing overview",
  "price_benchmarks": [{"product": "name", "price": "$XX", "features": ["feature1"]}],
  "positioning": {"tier": "Mid", "vs_category": "aligned", "intentional": true},
  "value_gap": {"perception": "good value", "evidence": "review pattern"},
  "pricing_power": {"signals": ["evidence 1"], "ability": "hold prices"},
  "competitor_moves": [{"competitor": "name", "change": "description", "when": "date"}] or [],
  "recommendation": {"action": "description", "rationale": "reason"},
  "question_answered": "direct answer to {{pricing_question}}"
}
Flag all prices as [Verified] or [Estimated].""",
    },
}


def _extract_json(text: str) -> dict | None:
    """Extract JSON from LLM response."""
    import re

    if not text:
        return None
    try:
        import json

        return json.loads(text)
    except json.JSONDecodeError:
        pass
    json_match = re.search(r"```(?:json)?\s*([\s\S]*?)\s*```", text)
    if json_match:
        try:
            return json.loads(json_match.group(1))
        except json.JSONDecodeError:
            pass
    brace_start = text.find("{")
    brace_end = text.rfind("}")
    if brace_start != -1 and brace_end != -1 and brace_end > brace_start:
        try:
            return json.loads(text[brace_start : brace_end + 1])
        except json.JSONDecodeError:
            pass
    return None


def _build_payload(payload: dict, workspace_id: str) -> dict:
    """Build common payload with workspace context."""
    workspace = repo.get_workspace(workspace_id) or {}
    result = {
        **payload,
        "brand_name": payload.get("brand_name") or workspace.get("brand_name") or "",
        "brand_context": payload.get("brand_context")
        or workspace.get("brand_summary")
        or workspace.get("positioning")
        or "",
    }
    # Convert lists to comma-separated strings for template
    for key, value in result.items():
        if isinstance(value, list):
            result[key] = ", ".join(str(v) for v in value if v)
    return result


def _apply_template(text: str, payload: dict) -> str:
    """Replace template variables with payload values."""
    import re

    for key, value in payload.items():
        if value is not None:
            text = text.replace(f"{{{{{key}}}}}", str(value))
    # Remove any remaining {{variable}} patterns
    text = re.sub(r"\{\{[^}]+\}\}", "", text)
    return text


def run_prd_agent(agent_id: str, payload: dict) -> tuple[dict, list[str]]:
    """Run a PRD agent with the appropriate prompt."""
    config = AGENT_PROMPTS.get(agent_id)
    if not config:
        # Fallback for agents not in our config
        return _run_generic_agent(agent_id, payload)

    logs: list[str] = []
    workspace_id = payload.get("workspace_id", "")
    built_payload = _build_payload(payload, workspace_id)

    brand_name = built_payload.get("brand_name", "your brand")
    logs.append(f"Starting {config['title']} for {brand_name}")

    user_prompt = _apply_template(config["user_prompt"], built_payload)

    try:
        from app.services.llm.openrouter_client import call_openrouter

        response = call_openrouter(
            [
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_prompt},
            ],
            temperature=0.4,
            max_tokens=2000,
        )
        parsed = _extract_json(response)

        if parsed:
            logs.append(f"LLM returned {len(parsed)} fields")
            debug_source = "llm"
        else:
            logs.append("LLM returned no valid JSON - using fallback")
            parsed = {}
            debug_source = "fallback"
    except Exception as exc:
        LOGGER.warning("LLM call failed for %s: %s", agent_id, exc)
        logs.append(f"LLM error: {exc}")
        parsed = {}
        debug_source = "error"

    output = {
        **base_output(agent_id, payload),
        "agent_title": config["title"],
        "result": parsed,
        "_debug": {"source": debug_source, "agent_id": agent_id},
    }
    logs.append(f"{agent_id} completed")
    return output, logs


def _run_generic_agent(agent_id: str, payload: dict) -> tuple[dict, list[str]]:
    """Fallback for agents without specific prompts."""
    logs: list[str] = []
    workspace_id = payload.get("workspace_id", "")
    workspace = repo.get_workspace(workspace_id) or {}

    brand_name = (
        payload.get("brand_name") or workspace.get("brand_name") or "your brand"
    )
    logs.append(f"Running generic agent {agent_id} for {brand_name}")

    output = {
        **base_output(agent_id, payload),
        "agent_title": agent_id.replace("_", " ").title(),
        "result": {
            "executive_summary": f"Analysis for {brand_name} completed.",
            "note": "This agent needs a specific prompt configuration.",
        },
        "_debug": {"source": "generic", "agent_id": agent_id},
    }
    logs.append(f"{agent_id} completed (generic)")
    return output, logs
