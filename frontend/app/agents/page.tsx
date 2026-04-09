"use client";

import Link from "next/link";
import type { Route } from "next";
import { useEffect, useMemo, useState } from "react";
import { getActiveWorkspaceId } from "../../lib/workspace";

type AgentCategory =
  | "Brand Strategy & Health"
  | "Channel & Visibility"
  | "Competitive Strategy"
  | "Content & Campaigns"
  | "Content & Creative Generation"
  | "Market & Audience Intelligence";

type AgentBadge = "NEW" | "UPDATED" | "LEGACY";

type AgentStudioItem = {
  id: string;
  name: string;
  category: AgentCategory;
  tags: string[];
  description: string;
  icon: string;
  badge?: AgentBadge;
  mostUsed: number;
  createdRank: number;
};

const CATEGORY_COLORS: Record<AgentCategory, string> = {
  "Brand Strategy & Health": "#8B5CF6",
  "Channel & Visibility": "#00B894",
  "Competitive Strategy": "#FF4D6D",
  "Content & Campaigns": "#4F6EF7",
  "Content & Creative Generation": "#EC4899",
  "Market & Audience Intelligence": "#F59E0B",
};

const AGENTS: AgentStudioItem[] = [
  {
    id: "brand_equity_tracker_agent",
    name: "Brand Equity Tracker Agent",
    category: "Brand Strategy & Health",
    tags: ["brand health", "awareness", "sov"],
    description: "Monitor brand strength across awareness, sentiment, and share of voice with AI scoring.",
    icon: "🧬",
    mostUsed: 96,
    createdRank: 9,
  },
  {
    id: "brand_voice_guardian_agent",
    name: "Brand Voice Guardian Agent",
    category: "Brand Strategy & Health",
    tags: ["brand voice", "tone", "copy audit"],
    description: "Audit content against brand guidelines and get instant on-brand rewrites.",
    icon: "🎙️",
    mostUsed: 92,
    createdRank: 10,
  },
  {
    id: "localisation_cultural_fit_agent",
    name: "Localisation & Cultural Fit Agent",
    category: "Brand Strategy & Health",
    tags: ["cultural fit", "localization", "campaign QA"],
    description: "Check campaign content for cultural fit before you launch in any new market.",
    icon: "🌍",
    mostUsed: 84,
    createdRank: 11,
  },
  {
    id: "geo_agent",
    name: "GEO / AI Visibility Agent",
    category: "Channel & Visibility",
    tags: ["geo", "ai visibility", "llm visibility", "sov"],
    description: "Track how your brand surfaces in AI recommendations and close visibility gaps.",
    icon: "🌐",
    badge: "UPDATED",
    mostUsed: 94,
    createdRank: 6,
  },
  {
    id: "retail_shelf_intelligence_agent",
    name: "Retail & Shelf Intelligence Agent",
    category: "Channel & Visibility",
    tags: ["retail", "ecommerce", "digital shelf"],
    description: "Audit your digital shelf presence and outperform competitors on Amazon and Flipkart.",
    icon: "📦",
    mostUsed: 80,
    createdRank: 14,
  },
  {
    id: "influencer_evaluation_agent",
    name: "Influencer Evaluation Agent",
    category: "Channel & Visibility",
    tags: ["influencer", "creator", "fit scoring"],
    description: "Score influencer fit against your brief using public signals before budget is committed.",
    icon: "🤝",
    mostUsed: 73,
    createdRank: 15,
  },
  {
    id: "marketing_compliance_agent",
    name: "Marketing Compliance Agent",
    category: "Channel & Visibility",
    tags: ["compliance", "claims", "regulation"],
    description: "Flag risky claims and get safe rewrites before your campaign goes live.",
    icon: "✅",
    mostUsed: 70,
    createdRank: 16,
  },
  {
    id: "sales_enablement_agent",
    name: "Sales Enablement Agent",
    category: "Competitive Strategy",
    tags: ["battle card", "objections", "competitor"],
    description: "Generate battle cards and objection handlers from live competitive intelligence.",
    icon: "⚔️",
    mostUsed: 76,
    createdRank: 12,
  },
  {
    id: "pricing_intelligence_agent",
    name: "Pricing Intelligence Agent",
    category: "Competitive Strategy",
    tags: ["pricing", "benchmarks", "competitive intelligence"],
    description: "Benchmark pricing against competitors and surface value perception gaps.",
    icon: "💰",
    badge: "NEW",
    mostUsed: 68,
    createdRank: 2,
  },
  {
    id: "competitive_intelligence_agent",
    name: "Competitive Intelligence Agent",
    category: "Competitive Strategy",
    tags: ["competitive intelligence", "positioning", "market moves"],
    description: "Map competitor positioning, messaging, and strategic moves with job signal intelligence.",
    icon: "🧭",
    badge: "UPDATED",
    mostUsed: 88,
    createdRank: 1,
  },
  {
    id: "campaign_brief_generator_agent",
    name: "Campaign Brief Generator Agent",
    category: "Content & Campaigns",
    tags: ["brief", "campaign", "planning"],
    description: "Turn a business objective into a full, strategically sharp creative brief.",
    icon: "📋",
    mostUsed: 91,
    createdRank: 8,
  },
  {
    id: "pr_narrative_agent",
    name: "PR & Narrative Agent",
    category: "Content & Campaigns",
    tags: ["pr", "narrative", "newsjacking"],
    description: "Find newsjacking opportunities and pitch angles aligned to your brand story right now.",
    icon: "📣",
    mostUsed: 71,
    createdRank: 13,
  },
  {
    id: "seo_content_gap_agent",
    name: "SEO Content Gap Agent",
    category: "Content & Campaigns",
    tags: ["content gap", "seo", "organic growth"],
    description: "Identify keyword gaps vs competitors and get ready-to-brief content plans.",
    icon: "🔍",
    mostUsed: 86,
    createdRank: 7,
  },
  {
    id: "content_agent",
    name: "Content Agent",
    category: "Content & Campaigns",
    tags: ["copy", "email", "ads", "social"],
    description: "Generate email, ad, and push content packs on-brand and ready to deploy.",
    icon: "✍️",
    mostUsed: 97,
    createdRank: 4,
  },
  {
    id: "campaign_qa_agent",
    name: "Campaign QA Agent",
    category: "Content & Campaigns",
    tags: ["campaign QA", "copy audit", "compliance"],
    description: "Audit campaigns for consistency, brand fit, and message clarity before launch.",
    icon: "🎯",
    mostUsed: 64,
    createdRank: 1,
  },
  {
    id: "creative_agent",
    name: "Creative Agent",
    category: "Content & Creative Generation",
    tags: ["creative", "creative strategy", "ads"],
    description: "Generate creative direction and concept variants from your brief in minutes.",
    icon: "🎨",
    mostUsed: 93,
    createdRank: 3,
  },
  {
    id: "experimentation_agent",
    name: "Experimentation Agent",
    category: "Content & Creative Generation",
    tags: ["ab test", "experimentation", "cro"],
    description: "Create A/B test ideas and prioritisation plans grounded in your audience data.",
    icon: "🧪",
    mostUsed: 81,
    createdRank: 17,
  },
  {
    id: "landing_page_optimization_agent",
    name: "Landing Page Optimisation Agent",
    category: "Content & Creative Generation",
    tags: ["landing page", "cro", "copy"],
    description: "Audit and improve landing page copy and structure for higher conversion outcomes.",
    icon: "🚀",
    mostUsed: 89,
    createdRank: 18,
  },
  {
    id: "visual_identity_audit_agent",
    name: "Visual Identity Audit Agent",
    category: "Content & Creative Generation",
    tags: ["brand voice", "design", "tone"],
    description: "Assess visual consistency across your brand's digital touchpoints and assets.",
    icon: "🖼️",
    mostUsed: 52,
    createdRank: 19,
  },
  {
    id: "persona_research_agent",
    name: "Persona Research Agent",
    category: "Market & Audience Intelligence",
    tags: ["persona", "audience", "consumer research"],
    description: "Build evidence-based buyer personas from real signals across reviews and forums.",
    icon: "👤",
    mostUsed: 88,
    createdRank: 20,
  },
  {
    id: "market_sizing_agent",
    name: "Market Sizing Agent",
    category: "Market & Audience Intelligence",
    tags: ["sizing", "tam", "sam", "som", "benchmarks"],
    description: "Estimate TAM, SAM, and SOM from public data for planning or investor decks.",
    icon: "📊",
    mostUsed: 78,
    createdRank: 21,
  },
  {
    id: "customer_review_intelligence_agent",
    name: "Customer Review Intelligence Agent",
    category: "Market & Audience Intelligence",
    tags: ["reviews", "sentiment", "churn", "voc"],
    description: "Extract strategic signal from reviews across G2, Amazon, Trustpilot, and more.",
    icon: "⭐",
    mostUsed: 83,
    createdRank: 22,
  },
  {
    id: "social_listening_agent",
    name: "Social Listening & Sentiment Agent",
    category: "Market & Audience Intelligence",
    tags: ["listening", "sentiment", "awareness", "sov"],
    description: "Monitor brand sentiment and surface emerging narratives before they spike.",
    icon: "👂",
    mostUsed: 87,
    createdRank: 23,
  },
  {
    id: "competitor_intelligence_legacy_agent",
    name: "Competitor Intelligence Agent (Legacy)",
    category: "Competitive Strategy",
    tags: ["competitor", "legacy"],
    description: "Legacy single-competitor scorecard. Upgrade to Competitive Intelligence Agent for multi-competitor analysis.",
    icon: "🧭",
    badge: "LEGACY",
    mostUsed: 15,
    createdRank: 24,
  },
];

const ANNOUNCEMENTS = [
  {
    type: "NEW",
    color: "#00B894",
    text: "Pricing Intelligence Agent now live in Competitive Strategy",
  },
  {
    type: "UPDATED",
    color: "#4F6EF7",
    text: "GEO Visibility Agent upgraded with AI share-of-voice scoring",
  },
  {
    type: "LIVE",
    color: "#F59E0B",
    text: "Agent runs now sync automatically to your Brand Workspace history",
  },
] as const;

const CATEGORY_ORDER: Array<"all" | AgentCategory> = [
  "all",
  "Brand Strategy & Health",
  "Channel & Visibility",
  "Competitive Strategy",
  "Content & Campaigns",
  "Content & Creative Generation",
  "Market & Audience Intelligence",
];

const TAG_ORDER = [
  "persona", "audience", "consumer research", "market moves", "sizing", "tam", "sam", "som", "benchmarks",
  "brand health", "brand voice", "positioning", "tone", "voc",
  "copy", "brief", "campaign", "content gap", "social", "email", "ads", "creative", "creative strategy",
  "geo", "ai search", "ai visibility", "llm visibility", "sov", "share of voice", "awareness",
  "competitive intelligence", "competitor", "battle card", "objections", "pricing",
  "ab test", "experimentation", "cro", "landing page", "organic growth", "seo",
  "claims", "compliance", "regulation", "cultural fit", "localization",
  "influencer", "creator", "fit scoring", "listening", "sentiment", "reviews",
  "retail", "ecommerce", "digital shelf", "churn", "narrative", "newsjacking", "pr", "planning", "campaign qa",
];

type SortOption = "Most Used" | "Newest" | "A–Z" | "By Category";

export default function AgentsPage() {
  const [search, setSearch] = useState("");
  const [draftCategory, setDraftCategory] = useState<"all" | AgentCategory>("all");
  const [draftTags, setDraftTags] = useState<string[]>([]);
  const [appliedCategory, setAppliedCategory] = useState<"all" | AgentCategory>("all");
  const [appliedTags, setAppliedTags] = useState<string[]>([]);
  const [sortBy, setSortBy] = useState<SortOption>("Most Used");
  const [showAllTags, setShowAllTags] = useState(false);
  const [drawerOpen, setDrawerOpen] = useState(false);
  const [workspaceReady, setWorkspaceReady] = useState(false);
  const [countAnimate, setCountAnimate] = useState(false);

  useEffect(() => {
    const params = new URLSearchParams(window.location.search);
    const qsCategory = params.get("category");
    if (!qsCategory) return;
    const valid = CATEGORY_ORDER.find((c) => c === qsCategory);
    if (valid) {
      setDraftCategory(valid as "all" | AgentCategory);
      setAppliedCategory(valid as "all" | AgentCategory);
    }
  }, []);

  useEffect(() => {
    const id = getActiveWorkspaceId();
    setWorkspaceReady(Boolean(id && id !== "ws_local_demo"));
  }, []);

  const categoryCounts = useMemo(() => {
    const counts: Record<string, number> = { all: AGENTS.length };
    CATEGORY_ORDER.forEach((category) => {
      if (category !== "all") counts[category] = AGENTS.filter((agent) => agent.category === category).length;
    });
    return counts;
  }, []);

  const visibleTags = useMemo(() => {
    const source = TAG_ORDER;
    return showAllTags ? source : source.slice(0, 16);
  }, [showAllTags]);

  const filtered = useMemo(() => {
    const q = search.trim().toLowerCase();
    let rows = AGENTS.filter((agent) => {
      const matchesSearch =
        !q ||
        agent.name.toLowerCase().includes(q) ||
        agent.description.toLowerCase().includes(q) ||
        agent.tags.some((tag) => tag.toLowerCase().includes(q));
      const matchesCategory = appliedCategory === "all" || agent.category === appliedCategory;
      const matchesTags = appliedTags.every((tag) => agent.tags.includes(tag));
      return matchesSearch && matchesCategory && matchesTags;
    });

    if (sortBy === "Most Used") rows = [...rows].sort((a, b) => b.mostUsed - a.mostUsed);
    if (sortBy === "Newest") rows = [...rows].sort((a, b) => a.createdRank - b.createdRank);
    if (sortBy === "A–Z") rows = [...rows].sort((a, b) => a.name.localeCompare(b.name));
    if (sortBy === "By Category") rows = [...rows].sort((a, b) => a.category.localeCompare(b.category) || a.name.localeCompare(b.name));

    return rows;
  }, [search, appliedCategory, appliedTags, sortBy]);

  useEffect(() => {
    setCountAnimate(true);
    const t = window.setTimeout(() => setCountAnimate(false), 220);
    return () => window.clearTimeout(t);
  }, [filtered.length]);

  function toggleDraftTag(tag: string) {
    setDraftTags((prev) => {
      if (prev.includes(tag)) return prev.filter((t) => t !== tag);
      if (prev.length >= 3) return prev;
      return [...prev, tag];
    });
  }

  function applyFilters() {
    setAppliedCategory(draftCategory);
    setAppliedTags(draftTags);
    setDrawerOpen(false);
  }

  function clearAll() {
    setDraftCategory("all");
    setDraftTags([]);
    setAppliedCategory("all");
    setAppliedTags([]);
  }

  return (
    <div className="agent-studio-page grid">
      <section className="agent-studio-head">
        <p className="agent-studio-eyebrow">Agent Studio</p>
        <h1>Your Marketing Team, Running 24/7 on AI</h1>
        <p>
          Choose from 24 specialist agents built for real marketing decisions — from brand strategy to campaign execution. Each agent runs in minutes, not meetings.
        </p>
        <div className="agent-studio-stats-inline">
          <span><b>24</b> Agents Available</span>
          <i>·</i>
          <span><b>6</b> Specialisations</span>
          <i>·</i>
          <span><b>1-Click</b> Workspace Integration</span>
        </div>
      </section>

      <section className="agent-announcement-bar">
        {ANNOUNCEMENTS.map((item) => (
          <article key={item.text} className="agent-announcement-pill">
            <span className="pulse-dot" style={{ background: item.color }} />
            <strong style={{ color: item.color }}>{item.type}</strong>
            <p>{item.text}</p>
            <a href="#" aria-label={item.text}>→</a>
          </article>
        ))}
      </section>

      <div className="agent-mobile-filter-row">
        <div className="agent-mobile-category-strip">
          {CATEGORY_ORDER.map((category) => (
            <button key={category} className={`agent-mobile-cat ${draftCategory === category ? "active" : ""}`} onClick={() => setDraftCategory(category)}>
              {category === "all" ? "All Categories" : category}
            </button>
          ))}
        </div>
        <button className="btn btn-subtle" onClick={() => setDrawerOpen(true)}>Filter</button>
      </div>

      <section className="agent-studio-layout">
        <aside className="agent-filter-sidebar">
          <div className="agent-search-wrap">
            <svg viewBox="0 0 24 24" aria-hidden="true"><circle cx="11" cy="11" r="7" /><path d="m20 20-3.2-3.2" /></svg>
            <input className="input" placeholder="Search agents..." value={search} onChange={(e) => setSearch(e.target.value)} />
          </div>

          <p className="agent-filter-label">CATEGORY</p>
          <div className="agent-category-list">
            {CATEGORY_ORDER.map((category) => {
              const color = category === "all" ? "#4F6EF7" : CATEGORY_COLORS[category as AgentCategory];
              const active = draftCategory === category;
              return (
                <button
                  key={category}
                  className={`agent-category-row ${active ? "active" : ""}`}
                  style={{ borderLeftColor: active ? color : "transparent" }}
                  onClick={() => setDraftCategory(category)}
                >
                  <span className="agent-category-left"><i style={{ background: color }} />{category === "all" ? "All Categories" : category}</span>
                  <em>{categoryCounts[category]}</em>
                </button>
              );
            })}
          </div>

          <div className="agent-filter-divider" />

          <p className="agent-filter-label">FILTER BY TAG</p>
          <div className="agent-tag-cloud">
            {visibleTags.map((tag) => (
              <button
                key={tag}
                className={`agent-tag ${draftTags.includes(tag) ? "active" : ""}`}
                onClick={() => toggleDraftTag(tag)}
                disabled={!draftTags.includes(tag) && draftTags.length >= 3}
              >
                {tag}
              </button>
            ))}
            <button className="agent-tag-more" onClick={() => setShowAllTags((v) => !v)}>{showAllTags ? "Show less" : "+ more"}</button>
          </div>

          <div className="agent-filter-actions">
            <button className="btn" onClick={applyFilters}>Apply Filters</button>
            <button className="agent-clear" onClick={clearAll}>Clear All</button>
          </div>
        </aside>

        <div className="agent-grid-wrap">
          {(appliedCategory !== "all" || appliedTags.length > 0) ? (
            <div className="agent-active-summary">
              <span>
                Showing {filtered.length} agents in {appliedCategory === "all" ? "All Categories" : appliedCategory}
                {appliedTags.length ? ` · ${appliedTags.map((tag) => `#${tag}`).join(" ")}` : ""}
              </span>
              {appliedCategory !== "all" ? <button onClick={() => { setAppliedCategory("all"); setDraftCategory("all"); }}>× category</button> : null}
              {appliedTags.map((tag) => (
                <button key={tag} onClick={() => {
                  setAppliedTags((prev) => prev.filter((t) => t !== tag));
                  setDraftTags((prev) => prev.filter((t) => t !== tag));
                }}>× #{tag}</button>
              ))}
            </div>
          ) : null}

          <div className="agent-grid-head">
            <div>
              <h2 className={countAnimate ? "count-animate" : ""}>{filtered.length} Agents</h2>
              <p>{appliedCategory === "all" ? "Showing all categories" : `Showing ${appliedCategory}`}</p>
            </div>
            <label className="agent-sort">
              Sort:
              <select className="select" value={sortBy} onChange={(e) => setSortBy(e.target.value as SortOption)}>
                <option>Most Used</option>
                <option>Newest</option>
                <option>A–Z</option>
                <option>By Category</option>
              </select>
            </label>
          </div>

          {filtered.length === 0 ? (
            <div className="agent-empty-state">
              <svg viewBox="0 0 120 120" aria-hidden="true"><circle cx="50" cy="50" r="28" /><path d="m72 72 22 22" /><path d="M50 38v20" /><circle cx="50" cy="66" r="2" /></svg>
              <h3>No agents match these filters</h3>
              <p>Try clearing a tag or browsing by category instead.</p>
              <button className="btn" onClick={clearAll}>Clear Filters</button>
            </div>
          ) : (
            <div className="agent-card-grid">
              {filtered.map((agent) => {
                const color = CATEGORY_COLORS[agent.category];
                return (
                  <article key={agent.id} className="agent-market-card" style={{ ["--cat-color" as string]: color }}>
                    {agent.badge ? <span className={`agent-status-badge ${agent.badge.toLowerCase()}`}>{agent.badge}</span> : null}
                    <div className="agent-card-top">
                      <span className="agent-category-pill" style={{ color, background: `${color}1f` }}>{agent.category}</span>
                      <div className="agent-top-tags">
                        {agent.tags.slice(0, 2).map((tag) => <span key={tag}>{tag}</span>)}
                        {agent.tags.length > 2 ? <span>+ {agent.tags.length - 2} more</span> : null}
                      </div>
                    </div>
                    <div className="agent-name-row">
                      <div className="agent-icon-box">{agent.icon}</div>
                      <h3><Link href={`/agents/${agent.id}` as Route}>{agent.name}</Link></h3>
                    </div>
                    <p className="agent-desc" title={agent.description}>{agent.description}</p>
                    <div className="agent-card-divider" />
                    <div className="agent-card-bottom">
                      <span className={`agent-workspace-indicator ${workspaceReady ? "ready" : "off"}`}>
                        {workspaceReady ? "Workspace ready" : "No workspace"}
                      </span>
                      <Link className="agent-run-btn" href={`/run/${agent.id}` as Route}>Run Agent <span>→</span></Link>
                    </div>
                  </article>
                );
              })}
            </div>
          )}
        </div>
      </section>

      <div className={`agent-filter-drawer ${drawerOpen ? "open" : ""}`}>
        <div className="agent-drawer-surface">
          <div className="agent-drawer-head">
            <h3>Filters</h3>
            <button onClick={() => setDrawerOpen(false)}>×</button>
          </div>
          <p className="agent-filter-label">CATEGORY</p>
          <div className="agent-drawer-cats">
            {CATEGORY_ORDER.map((category) => (
              <button key={category} className={`agent-drawer-cat ${draftCategory === category ? "active" : ""}`} onClick={() => setDraftCategory(category)}>
                {category === "all" ? "All Categories" : category}
              </button>
            ))}
          </div>
          <p className="agent-filter-label">FILTER BY TAG</p>
          <div className="agent-tag-cloud">
            {TAG_ORDER.map((tag) => (
              <button key={tag} className={`agent-tag ${draftTags.includes(tag) ? "active" : ""}`} onClick={() => toggleDraftTag(tag)}>
                {tag}
              </button>
            ))}
          </div>
          <div className="agent-filter-actions">
            <button className="btn" onClick={applyFilters}>Apply Filters</button>
            <button className="agent-clear" onClick={clearAll}>Clear All</button>
          </div>
        </div>
      </div>
    </div>
  );
}
