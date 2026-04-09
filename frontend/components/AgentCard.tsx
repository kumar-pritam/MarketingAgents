import Link from "next/link";
import type { Route } from "next";

type Props = {
  id: string;
  name: string;
  summary: string;
  category: string;
};

const AGENT_ICON: Record<string, string> = {
  geo_agent: "🌐",
  competitive_intelligence_agent: "🧭",
  content_agent: "✍️",
  creative_agent: "🎨",
  experimentation_agent: "🧪",
  landing_page_optimization_agent: "🚀",
  pricing_intelligence_agent: "💰",
  social_listening_agent: "👂",
  campaign_planner_agent: "📋",
  campaign_qa_agent: "🎯",
  brand_equity_tracker_agent: "🧬",
  brand_voice_guardian_agent: "🎙️",
  campaign_brief_generator_agent: "📝",
  persona_research_agent: "👤",
  seo_content_gap_agent: "🔎",
  localisation_cultural_fit_agent: "🌍",
  customer_review_intelligence_agent: "⭐",
  retail_shelf_intelligence_agent: "📦",
  market_sizing_agent: "📊",
  sales_enablement_agent: "⚔️",
  influencer_evaluation_agent: "📣",
  pr_narrative_agent: "📰",
  marketing_compliance_agent: "⚖️",
  visual_identity_audit_agent: "🖼️",
  competitor_intelligence_legacy_agent: "🧭",
};

export function AgentCard({ id, name, summary, category }: Props) {
  return (
    <div className="card agent-card agent-card-clickable">
      <Link className="agent-card-main" href={`/agents/${id}` as Route}>
        <div className="badge">{category}</div>
        <h3>{AGENT_ICON[id] || "🤖"} {name}</h3>
        <p>{summary}</p>
      </Link>
      <div className="agent-card-actions">
        <Link className="btn btn-subtle" href={`/run/${id}` as Route}>Run Agent</Link>
      </div>
    </div>
  );
}
