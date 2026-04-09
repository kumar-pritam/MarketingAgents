from __future__ import annotations

from app.services.agents.executors.brand_equity_agent import (
    run as run_brand_equity_tracker,
)
from app.services.agents.executors.competitor_intelligence_agent import (
    run as run_competitor_intelligence,
)
from app.services.agents.executors.campaign_planner_agent import (
    run as run_campaign_planner,
)
from app.services.agents.executors.content_agent import run as run_content
from app.services.agents.executors.creative_agent import run as run_creative
from app.services.agents.executors.experimentation_agent import (
    run as run_experimentation,
)
from app.services.agents.executors.geo_agent import run as run_geo
from app.services.agents.executors.landing_page_optimization_agent import run as run_lpo
from app.services.agents.executors.pricing_intelligence_agent import run as run_pricing
from app.services.agents.executors.prd_agents import run_prd_agent
from app.services.agents.executors.social_listening_agent import (
    run as run_social_listening,
)

EXECUTORS = {
    # Custom executors
    "geo_agent": run_geo,
    "competitor_intelligence_agent": run_competitor_intelligence,
    "content_agent": run_content,
    "creative_agent": run_creative,
    "experimentation_agent": run_experimentation,
    "landing_page_optimization_agent": run_lpo,
    "pricing_intelligence_agent": run_pricing,
    "social_listening_agent": run_social_listening,
    "campaign_planner_agent": run_campaign_planner,
    "brand_equity_tracker_agent": run_brand_equity_tracker,
    # PRD agents using generic executor
    "competitive_intelligence_agent": lambda payload: run_prd_agent(
        "competitive_intelligence_agent", payload
    ),
    "content_agent_v2": lambda payload: run_prd_agent("content_agent", payload),
    "brand_voice_guardian_agent": lambda payload: run_prd_agent(
        "brand_voice_guardian_agent", payload
    ),
    "campaign_brief_generator_agent": lambda payload: run_prd_agent(
        "campaign_brief_generator_agent", payload
    ),
    "landing_page_optimization_agent_v2": lambda payload: run_prd_agent(
        "landing_page_optimization_agent", payload
    ),
    "persona_research_agent": lambda payload: run_prd_agent(
        "persona_research_agent", payload
    ),
    "social_listening_agent_v2": lambda payload: run_prd_agent(
        "social_listening_agent", payload
    ),
    "seo_content_gap_agent": lambda payload: run_prd_agent(
        "seo_content_gap_agent", payload
    ),
    "localisation_cultural_fit_agent": lambda payload: run_prd_agent(
        "localisation_cultural_fit_agent", payload
    ),
    "customer_review_intelligence_agent": lambda payload: run_prd_agent(
        "customer_review_intelligence_agent", payload
    ),
    "experimentation_agent_v2": lambda payload: run_prd_agent(
        "experimentation_agent", payload
    ),
    "retail_shelf_intelligence_agent": lambda payload: run_prd_agent(
        "retail_shelf_intelligence_agent", payload
    ),
    "market_sizing_agent": lambda payload: run_prd_agent(
        "market_sizing_agent", payload
    ),
    "sales_enablement_agent": lambda payload: run_prd_agent(
        "sales_enablement_agent", payload
    ),
    "influencer_evaluation_agent": lambda payload: run_prd_agent(
        "influencer_evaluation_agent", payload
    ),
    "pr_narrative_agent": lambda payload: run_prd_agent("pr_narrative_agent", payload),
    "marketing_compliance_agent": lambda payload: run_prd_agent(
        "marketing_compliance_agent", payload
    ),
    "campaign_qa_agent": lambda payload: run_prd_agent("campaign_qa_agent", payload),
    "visual_identity_audit_agent": lambda payload: run_prd_agent(
        "visual_identity_audit_agent", payload
    ),
    "pricing_intelligence_agent_v2": lambda payload: run_prd_agent(
        "pricing_intelligence_agent", payload
    ),
    "competitor_intelligence_legacy_agent": lambda payload: run_prd_agent(
        "competitor_intelligence_agent", payload
    ),
}
