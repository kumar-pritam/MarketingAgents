import Link from "next/link";
import type { Route } from "next";
import { apiGet } from "../lib/api";
import { Reveal } from "../components/Reveal";
import { FlowTimeline } from "../components/FlowTimeline";

type Agent = {
  id: string;
  name: string;
  summary: string;
  description?: string;
  category: string;
  tags?: string[];
};

const CATEGORY_STYLE: Record<string, string> = {
  "Channel & Visibility": "tag-channel",
  "Competitive Strategy": "tag-competitive",
  "Content & Campaigns": "tag-content",
  "Content & Creative Generation": "tag-creative",
  "Brand Strategy & Health": "tag-content",
  "Market & Audience Intelligence": "tag-channel",
};

const AGENT_REWRITES: Record<string, string> = {
  "competitive_intelligence_agent": "See exactly what competitors are doing — positioning, campaigns, and strategic moves — and find where you win.",
  "brand_equity_tracker_agent": "Your brand's health in one dashboard — awareness, sentiment, share of voice, and AI visibility, tracked over time.",
  "geo_agent": "Find out if your brand shows up when customers ask AI what to buy — and close the gaps before competitors do.",
  "content_agent": "Brief it once. Get email, ad, push, and social content packs that are on-brand and ready to deploy.",
  "persona_research_agent": "Build evidence-based buyer personas from real consumer signals — reviews, forums, and social conversations.",
  "brand_voice_guardian_agent": "Paste any content. Get it audited against your brand voice and rewritten on the spot.",
  "creative_agent": "From brief to concept in minutes. Get distinct creative territories, headlines, and visual direction — not generic ideas.",
  "social_listening_agent": "Monitor brand sentiment across social platforms and identify emerging narratives before they escalate.",
  "campaign_brief_generator_agent": "Generate comprehensive campaign briefs with insights, strategy, and success metrics — in minutes.",
  "landing_page_optimization_agent": "Audit landing pages for conversion barriers and get actionable recommendations to improve performance.",
  "seo_content_gap_agent": "Identify content gaps vs competitors and discover keyword opportunities to own in search.",
  "pricing_intelligence_agent": "Analyse competitor pricing and positioning to find your optimal price sweet spot.",
  "influencer_evaluation_agent": "Evaluate influencer authenticity, audience quality, and brand fit before you commit.",
  "pr_narrative_agent": "Craft PR narratives and press releases aligned to your communications objective.",
  "marketing_compliance_agent": "Audit marketing content for regulatory and legal compliance risks.",
  "campaign_qa_agent": "Quality-check your entire campaign for consistency, voice, and message alignment.",
  "customer_review_intelligence_agent": "Extract actionable insights from customer reviews to improve products and positioning.",
  "retail_shelf_intelligence_agent": "Analyse your retail presence vs competitors on Amazon, Flipkart, and more.",
  "market_sizing_agent": "Estimate market size (TAM, SAM, SOM) for investor pitches or new market entry.",
  "sales_enablement_agent": "Generate battlecards and talk tracks to help sales position against competitors.",
  "localisation_cultural_fit_agent": "Audit campaign copy for cultural fit when expanding to new markets.",
  "experimentation_agent": "Design rigorous A/B tests with hypotheses, variants, and success metrics.",
  "visual_identity_audit_agent": "Audit brand consistency across logo, color, typography, and imagery.",
  "campaign_planner_agent": "Build comprehensive campaign plans with strategy, channels, and timelines.",
};

const FEATURED_AGENTS = [
  {
    id: "competitive_intelligence_agent",
    name: "Competitive Intelligence Agent",
    summary: "Most teams spend a week pulling together competitor intel. This agent does it in 3 minutes — positioning gaps, campaign themes, and one strategic move to make.",
  },
  {
    id: "content_agent",
    name: "Content Agent",
    summary: "The brief is the bottleneck. Give this agent your objective and audience — get a full content pack across every channel, ready to hand to your team.",
  },
  {
    id: "geo_agent",
    name: "GEO / AI Visibility Agent",
    summary: "Your customers are asking AI what to buy. Is your brand in the answer? This agent tells you exactly where you appear — and where you're invisible.",
  },
];

const FLOW_STEPS = [
  "Build your brand workspace. Add your brand name, positioning, and context once. Every agent run from here starts pre-loaded and aligned.",
  "Pick the agent for the job. Browse 24 specialist agents across 6 marketing disciplines. Each one asks only what it needs.",
  "Get structured, marketer-ready output. No walls of text. Every agent delivers dashboards, recommendations, and actions you can present or act on immediately.",
  "Track, refine, and scale. Full run history, team sharing, and reusable playbooks — so your best thinking compounds over time, not disappears after one sprint.",
];

function HeroHeading() {
  return (
    <h1 className="home-hero-title">
      <span className="hero-word" style={{ animationDelay: "0ms" }}>Your Best Marketing Thinking,</span>
      <br />
      <span className="hero-word" style={{ animationDelay: "100ms" }}>Running Around</span>
      <span className="hero-word" style={{ animationDelay: "170ms" }}> the Clock</span>
    </h1>
  );
}

function PillarIcon({ kind }: { kind: "brain" | "agents" | "speed" }) {
  if (kind === "brain") {
    return (
      <svg viewBox="0 0 24 24" aria-hidden="true">
        <path d="M12 2a8 8 0 0 0-8 8c0 2.8 1.5 5.3 3.8 6.7.2.1.3.3.4.5l.8 1.3c.2.4.6.7 1 .8.5.1 1 .1 1.5 0l1.5-.7 1.5.7c.5.2 1 .1 1.5 0 .4-.1.8-.4 1-.8l.8-1.3c.1-.2.2-.4.4-.5A8 8 0 0 0 12 2Z" />
        <path d="M12 22v-4M8 14c-2 0-4-1-4-3s2-3 4-3M16 14c2 0 4-1 4-3s-2-3-4-3" />
      </svg>
    );
  }
  if (kind === "agents") {
    return (
      <svg viewBox="0 0 24 24" aria-hidden="true">
        <rect x="3" y="3" width="7" height="7" rx="1" />
        <rect x="14" y="3" width="7" height="7" rx="1" />
        <rect x="3" y="14" width="7" height="7" rx="1" />
        <rect x="14" y="14" width="7" height="7" rx="1" />
      </svg>
    );
  }
  return (
    <svg viewBox="0 0 24 24" aria-hidden="true">
      <path d="M13 2L3 14h9l-1 8 10-12h-9l1-8z" />
    </svg>
  );
}

function HomeAgentCard({ agent }: { agent: Agent }) {
  const rewrittenSummary = AGENT_REWRITES[agent.id] || agent.summary;
  return (
    <article className="home-agent-card">
      <div className={`home-agent-tag ${CATEGORY_STYLE[agent.category] || "tag-content"}`}>{agent.category}</div>
      <h3>{agent.name}</h3>
      <p>{rewrittenSummary}</p>
      <div className="home-agent-actions">
        <Link href={`/run/${agent.id}` as Route} className="home-run-btn">
          Run Agent <span aria-hidden="true">→</span>
        </Link>
      </div>
    </article>
  );
}

function FeaturedAgentCard({ agent }: { agent: typeof FEATURED_AGENTS[0] }) {
  return (
    <article className="home-featured-agent-card">
      <h4>{agent.name}</h4>
      <p>"{agent.summary}"</p>
      <Link href={`/run/${agent.id}` as Route} className="home-run-btn featured">
        Run This Agent <span aria-hidden="true">→</span>
      </Link>
    </article>
  );
}

export default async function HomePage() {
  const agents = await apiGet<Agent[]>("/agents");

  return (
    <div className="home-page grid">
      <Reveal>
        <section className="home-hero hero-strip hero-premium">
          <div className="home-hero-bg" aria-hidden="true" />
          <p className="home-eyebrow">The AI Marketing OS for Brand-Led Teams</p>
          <HeroHeading />
          <p className="home-hero-subtext">
            MarketingAgents.ai gives your brand a permanent strategic brain — and 24 specialist AI agents to act on it. From competitive intelligence to campaign execution, get decision-grade output in minutes, not days.
          </p>
          <div className="home-hero-actions hero-actions">
            <Link className="btn" href={"/workspaces" as Route}>
              Build My Brand Workspace
            </Link>
            <Link className="btn ghost-btn" href={"/agents" as Route}>
              Browse the Agent Studio →
            </Link>
          </div>
          <div className="home-stats-row">
            <div className="home-stat-item">
              <span className="home-stat-value">24+</span>
              <span className="home-stat-label">Specialist<br />Agents</span>
            </div>
            <div className="home-stat-divider" />
            <div className="home-stat-item">
              <span className="home-stat-value">42+</span>
              <span className="home-stat-label">Ready-to-Run<br />Playbooks</span>
            </div>
            <div className="home-stat-divider" />
            <div className="home-stat-item">
              <span className="home-stat-value">63%</span>
              <span className="home-stat-label">Faster from brief<br />to marketable output</span>
            </div>
          </div>
        </section>
      </Reveal>

      <Reveal>
        <section className="home-pillars-section">
          <p className="home-section-label">Why marketing teams switch to MarketingAgents.ai</p>
          <div className="grid grid-3 home-pillars">
            <div className="card feature-card home-pillar-card">
              <div className="home-pillar-icon"><PillarIcon kind="brain" /></div>
              <h3>Always-On Brand Intelligence</h3>
              <p>
                Stop briefing from scratch. Build your brand's strategic context once — every agent run starts informed, aligned, and on-brand automatically.
              </p>
            </div>
            <div className="card feature-card home-pillar-card">
              <div className="home-pillar-icon"><PillarIcon kind="agents" /></div>
              <h3>Specialist Agents for Real Marketing Work</h3>
              <p>
                Not a generic AI chatbot. Each agent is purpose-built for a specific marketing job — from GEO visibility audits to campaign QA — with structured, marketer-friendly output.
              </p>
            </div>
            <div className="card feature-card home-pillar-card">
              <div className="home-pillar-icon"><PillarIcon kind="speed" /></div>
              <h3>Built for Teams Who Move Fast</h3>
              <p>
                Persistent workspaces, full run history, and shareable outputs your team and leadership can actually act on.
              </p>
            </div>
          </div>
        </section>
      </Reveal>

      <Reveal>
        <section className="home-top-agents" id="agents">
          <div className="home-top-header">
            <p className="home-section-label">24 Agents. One Studio.</p>
            <h2>A Specialist for Every Marketing Decision</h2>
            <p className="home-top-subtext">
              Stop generalising. Run the exact agent built for the job — and get structured output your team can act on immediately.
            </p>
            <div className="home-stat-pills">
              <span>24 Agents</span>
              <span>6 Specialisations</span>
              <span>Workspace-Linked</span>
            </div>
          </div>
          <div className="home-agents-grid">
            {agents.map((agent) => (
              <HomeAgentCard key={agent.id} agent={agent} />
            ))}
            {!agents.length ? (
              <>
                <div className="home-agent-skeleton" />
                <div className="home-agent-skeleton" />
              </>
            ) : null}
          </div>
        </section>
      </Reveal>

      <Reveal>
        <section className="home-featured-section">
          <p className="home-section-label">High-Impact Starting Points</p>
          <h2>Not Sure Where to Start?<br />These Three Will Change How You Work.</h2>
          <p className="home-featured-subtext">
            Marketers who run these agents first never go back to doing them manually.
          </p>
          <div className="home-featured-grid">
            {FEATURED_AGENTS.map((agent) => (
              <FeaturedAgentCard key={agent.id} agent={agent} />
            ))}
          </div>
          <Link className="home-see-all-link" href={"/agents" as Route}>See all 24 agents in Agent Studio →</Link>
        </section>
      </Reveal>

      <Reveal>
        <section className="home-flow">
          <p className="home-section-label">Simple by Design</p>
          <h2>From Brand Context to Marketing Output<br />in Four Steps</h2>
          <FlowTimeline steps={FLOW_STEPS} />
        </section>
      </Reveal>
    </div>
  );
}
