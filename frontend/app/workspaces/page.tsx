"use client";

import { useEffect, useMemo, useState } from "react";
import Link from "next/link";
import type { Route } from "next";
import { apiGet, apiPost, apiPut } from "../../lib/api";
import {
  WorkspaceDraft,
  getActiveWorkspaceId,
  loadWorkspaceLocal,
  saveWorkspaceLocal,
  setActiveWorkspaceId,
} from "../../lib/workspace";
import { showToast } from "../../components/Toast";
import { Tooltip } from "../../components/Tooltip";

type BackendWorkspace = {
  workspace_id: string;
  workspace_name: string;
  brand_name: string;
  website: string;
  industry: string;
  category?: string | null;
  geography?: string | null;
  positioning?: string | null;
  additional_details?: string | null;
  brand_summary?: string | null;
  brand_analysis?: Record<string, string> | null;
  key_pages: string[];
  assets: Array<{ name: string; kind: string; size_bytes: number; content_type: string }>;
  updated_at: string;
};

type BrandAnalysisResponse = {
  brand_name: string;
  website: string;
  industry: string;
  positioning: string;
  key_pages: string[];
  category: string;
  geography: string;
  brand_summary?: string;
  brand_analysis: Record<string, string>;
};

type BrandCardItem = {
  key: string;
  label: string;
  dot: string;
  defaultText: string;
  risk?: boolean;
};

type EventType = "save" | "agent" | "edit";
type WorkspaceEvent = { ts: string; type: EventType; message: string };
type NewWorkspaceForm = { brandName: string; company: string; industry: string; country: string };
const DELETED_WORKSPACES_KEY = "marketing_agents_deleted_workspaces_v1";
const MY_BRAND_WORKSPACE_KEY = "marketing_agents_my_brand_workspace_v1";

const BRAND_GRID_ITEMS: BrandCardItem[] = [
  {
    key: "brand_overview",
    label: "BRAND OVERVIEW",
    dot: "#4F6EF7",
    defaultText:
      "India's best-selling hatchback — known for sporty design, stellar fuel efficiency, and one of the strongest resale values in its class.",
  },
  {
    key: "brand_positioning",
    label: "POSITIONING",
    dot: "#00B894",
    defaultText:
      "The youthful, fun-to-drive hatchback that delivers premium features at an accessible price — for buyers who refuse to compromise.",
  },
  {
    key: "brand_identity_assets",
    label: "IDENTITY & ASSETS",
    dot: "#8B5CF6",
    defaultText:
      "Swept-back headlamps, bold grille, dual-tone roof, and the iconic Swift badge — a design language that's aged into a recognisable signature.",
  },
  {
    key: "brand_personality_archetype",
    label: "PERSONALITY & ARCHETYPE",
    dot: "#F59E0B",
    defaultText:
      "The Explorer. Adventurous, energetic, and unapologetically youthful. Built for those who see every drive as a story worth telling.",
  },
  {
    key: "brand_promise_values",
    label: "BRAND PROMISE",
    dot: "#EC4899",
    defaultText:
      "Reliable performance, low running costs, and a driving experience that puts a smile on your face — every single day.",
  },
  {
    key: "competitive_landscape",
    label: "COMPETITIVE LANDSCAPE",
    dot: "#FF4D6D",
    defaultText:
      "Primary rivals: Hyundai i20, Tata Altroz, Honda Jazz, Volkswagen Polo. Swift leads on brand trust and resale — trails on interior premium feel.",
  },
  {
    key: "communication_campaigns",
    label: "CAMPAIGNS & COMMS",
    dot: "#4F6EF7",
    defaultText:
      "'Feel the Rush' (TV + digital) and '#DriveYourStory' social series. Consistent energy-led storytelling across channels.",
  },
  {
    key: "mental_availability_ceps",
    label: "MENTAL AVAILABILITY",
    dot: "#00B894",
    defaultText:
      "Owns: city commuting, weekend getaways, first-car purchase, sporty styling. Strong CEP coverage for its core segment.",
  },
  {
    key: "ai_geo_visibility",
    label: "AI & GEO VISIBILITY",
    dot: "#8B5CF6",
    defaultText:
      "High presence for 'best hatchback India' and 'Maruti Swift price' across Google and voice. Emerging visibility in AI-generated comparisons.",
  },
  {
    key: "brand_health_risks",
    label: "BRAND HEALTH RISKS",
    dot: "#FF4D6D",
    risk: true,
    defaultText:
      "SUV segment cannibalising hatchback demand. EV readiness gap vs. newer rivals. Supply chain exposure needs monitoring.",
  },
];

const DEFAULT_SUMMARY =
  "Swift is positioned as India's go-to youthful hatchback — sporty, affordable, and built for first-time buyers who want premium feel without the premium price tag. Key risk to watch: SUV preference shift and EV readiness.";

const SAMPLE_WORKSPACES: BackendWorkspace[] = [
  { workspace_id: "final-ui-ws", workspace_name: "Final UI WS", brand_name: "GlowNest", website: "", industry: "Beauty", category: "Skincare", geography: "India", positioning: "", additional_details: "", brand_summary: "", brand_analysis: {}, key_pages: [], assets: [], updated_at: new Date(Date.now() - 2 * 60 * 60 * 1000).toISOString() },
  { workspace_id: "maruti-suzuki-swift", workspace_name: "Maruti Suzuki Swift", brand_name: "Maruti Suzuki Swift", website: "", industry: "Automotive", category: "Automotive", geography: "India", positioning: "", additional_details: "", brand_summary: "", brand_analysis: {}, key_pages: [], assets: [], updated_at: new Date(Date.now() - 3 * 60 * 60 * 1000).toISOString() },
  { workspace_id: "all-agents-validation-1", workspace_name: "All Agents Validation", brand_name: "Maruti Suzuki Swift", website: "", industry: "Automotive", category: "Automotive", geography: "India", positioning: "", additional_details: "", brand_summary: "", brand_analysis: {}, key_pages: [], assets: [], updated_at: new Date(Date.now() - 4 * 60 * 60 * 1000).toISOString() },
  { workspace_id: "all-agents-validation-2", workspace_name: "All Agents Validation", brand_name: "Maruti Suzuki Swift", website: "", industry: "Automotive", category: "Automotive", geography: "India", positioning: "", additional_details: "", brand_summary: "", brand_analysis: {}, key_pages: [], assets: [], updated_at: new Date(Date.now() - 5 * 60 * 60 * 1000).toISOString() },
  { workspace_id: "test-save", workspace_name: "Test Save", brand_name: "Tanishq", website: "", industry: "Jewelry", category: "Jewelry", geography: "India", positioning: "", additional_details: "", brand_summary: "", brand_analysis: {}, key_pages: [], assets: [], updated_at: new Date(Date.now() - 7 * 60 * 60 * 1000).toISOString() },
  { workspace_id: "nike-india-core", workspace_name: "Nike India Core", brand_name: "Nike", website: "", industry: "Sportswear", category: "Sportswear", geography: "India", positioning: "", additional_details: "", brand_summary: "", brand_analysis: {}, key_pages: [], assets: [], updated_at: new Date(Date.now() - 12 * 60 * 60 * 1000).toISOString() },
  { workspace_id: "swift-q2-core", workspace_name: "Swift Q2 Core", brand_name: "Maruti Suzuki Swift", website: "", industry: "Automotive", category: "Automotive", geography: "India", positioning: "", additional_details: "", brand_summary: "", brand_analysis: {}, key_pages: [], assets: [], updated_at: new Date(Date.now() - 21 * 60 * 60 * 1000).toISOString() },
  { workspace_id: "maruit-suzuki-swift", workspace_name: "Maruit Suzuki Swift", brand_name: "Maruti Suzuki Swift", website: "", industry: "Automotive", category: "Automotive", geography: "India", positioning: "", additional_details: "", brand_summary: "", brand_analysis: {}, key_pages: [], assets: [], updated_at: new Date(Date.now() - 25 * 60 * 60 * 1000).toISOString() },
  { workspace_id: "maruti-suzuki-swift-2", workspace_name: "Maruti Suzuki Swift", brand_name: "Maruti Suzuki Swift", website: "", industry: "Automotive", category: "Automotive", geography: "India", positioning: "", additional_details: "", brand_summary: "", brand_analysis: {}, key_pages: [], assets: [], updated_at: new Date(Date.now() - 40 * 60 * 60 * 1000).toISOString() },
];

const BRAND_SUGGESTIONS = ["Maruti Suzuki Swift", "Nike", "Tanishq", "GlowNest", "Mamaearth", "Minimalist"];
const COMPANY_SUGGESTIONS = ["Maruti Suzuki", "Nike Inc.", "Titan Company", "GlowNest Labs", "Hindustan Unilever"];
const INDUSTRY_SUGGESTIONS = ["Automotive", "FMCG", "Skincare", "Sportswear", "Jewelry", "D2C"];
const COUNTRY_SUGGESTIONS = ["India", "United States", "United Kingdom", "UAE", "Singapore", "Global"];

const EMPTY: WorkspaceDraft = {
  workspaceId: "",
  workspaceName: "",
  brandName: "",
  website: "",
  industry: "",
  category: "",
  geography: "",
  positioning: "",
  additionalDetails: "",
  brandSummary: "",
  brandAnalysis: {},
  keyPages: [],
  docs: [],
};

function toDraft(row: BackendWorkspace): WorkspaceDraft {
  return {
    workspaceId: row.workspace_id,
    workspaceName: row.workspace_name,
    brandName: row.brand_name,
    website: row.website,
    industry: row.industry,
    category: row.category || "",
    geography: row.geography || "",
    positioning: row.positioning || "",
    additionalDetails: row.additional_details || "",
    brandSummary: row.brand_summary || "",
    brandAnalysis: row.brand_analysis || {},
    keyPages: row.key_pages || [],
    docs: [],
  };
}

function slugify(value: string): string {
  return value.trim().toLowerCase().replace(/[^a-z0-9]+/g, "-").replace(/(^-|-$)/g, "");
}

function cleanWorkspaceName(name: string): string {
  const trimmed = name.trim();
  if (trimmed.toLowerCase() === "final ui ws") return "Final UI Workspace";
  if (trimmed.toLowerCase() === "test save") return "Quick Test";
  if (trimmed.toLowerCase() === "maruit suzuki swift") return "Maruti Suzuki Swift";
  return trimmed;
}

function relativeTime(iso: string): string {
  const ts = new Date(iso).getTime();
  if (Number.isNaN(ts)) return "just now";
  const diff = Date.now() - ts;
  const mins = Math.floor(diff / 60000);
  if (mins < 1) return "just now";
  if (mins < 60) return `${mins} min ago`;
  const hrs = Math.floor(mins / 60);
  if (hrs < 24) return `${hrs} hour${hrs > 1 ? "s" : ""} ago`;
  const days = Math.floor(hrs / 24);
  if (days === 1) return "yesterday";
  return `${days} days ago`;
}

function avatarColor(brandName: string): string {
  const b = brandName.toLowerCase();
  if (b.includes("maruti")) return "#4F6EF7";
  if (b.includes("nike")) return "#FF4D6D";
  if (b.includes("tanishq")) return "#F59E0B";
  if (b.includes("glownest")) return "#00B894";
  const palette = ["#4F6EF7", "#00B894", "#8B5CF6", "#F59E0B", "#EC4899"];
  const hash = [...brandName].reduce((acc, ch) => acc + ch.charCodeAt(0), 0);
  return palette[hash % palette.length];
}

function eventDot(type: EventType): string {
  if (type === "save") return "#00B894";
  if (type === "edit") return "#F59E0B";
  return "#4F6EF7";
}

export default function WorkspacesPage() {
  const [nextPath, setNextPath] = useState<string | null>(null);
  const [items, setItems] = useState<BackendWorkspace[]>([]);
  const [draft, setDraft] = useState<WorkspaceDraft>(EMPTY);
  const [keyPagesInput, setKeyPagesInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [info, setInfo] = useState("");
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [quickEdit, setQuickEdit] = useState(false);
  const [events, setEvents] = useState<WorkspaceEvent[]>([]);
  const [query, setQuery] = useState("");
  const [activityFilter, setActivityFilter] = useState<"all" | EventType>("all");
  const [draftItems, setDraftItems] = useState<BackendWorkspace[]>([]);
  const [showNewWorkspaceForm, setShowNewWorkspaceForm] = useState(false);
  const [newWs, setNewWs] = useState<NewWorkspaceForm>({
    brandName: "",
    company: "",
    industry: "",
    country: "India",
  });
  const [deletedWorkspaceIds, setDeletedWorkspaceIds] = useState<string[]>([]);
  const [myBrandWorkspaceId, setMyBrandWorkspaceId] = useState<string>("");

  const isEdit = useMemo(() => Boolean(draft.workspaceId), [draft.workspaceId]);
  const allItems = useMemo(() => {
    const base = items.length ? items : SAMPLE_WORKSPACES;
    const seen = new Set(draftItems.map((w) => w.workspace_id));
    return [...draftItems, ...base.filter((w) => !seen.has(w.workspace_id))].filter(
      (w) => !deletedWorkspaceIds.includes(w.workspace_id),
    );
  }, [items, draftItems, deletedWorkspaceIds]);
  const filteredItems = useMemo(() => {
    const term = query.trim().toLowerCase();
    if (!term) return allItems;
    return allItems.filter((item) => `${cleanWorkspaceName(item.workspace_name)} ${item.brand_name}`.toLowerCase().includes(term));
  }, [allItems, query]);
  const activeWorkspaceId = draft.workspaceId || getActiveWorkspaceId();
  const filteredEvents = useMemo(
    () => (activityFilter === "all" ? events : events.filter((event) => event.type === activityFilter)),
    [events, activityFilter],
  );

  function pushEvent(type: EventType, message: string) {
    setEvents((prev) => [{ ts: new Date().toISOString(), type, message }, ...prev].slice(0, 30));
  }

  function upsertDraftItem(item: BackendWorkspace) {
    setDraftItems((prev) => {
      const rest = prev.filter((row) => row.workspace_id !== item.workspace_id);
      return [item, ...rest];
    });
  }

  async function reload() {
    const rows = await apiGet<BackendWorkspace[]>("/workspaces");
    setItems(rows);
  }

  useEffect(() => {
    const queryParams = new URLSearchParams(window.location.search);
    setNextPath(queryParams.get("next"));
  }, []);

  useEffect(() => {
    reload().catch(() => setItems([]));
    const activeId = getActiveWorkspaceId();
    if (activeId) {
      const local = loadWorkspaceLocal(activeId);
      if (local) {
        setDraft(local);
        setKeyPagesInput(local.keyPages.join(", "));
      }
    }
    try {
      const deletedRaw = localStorage.getItem(DELETED_WORKSPACES_KEY);
      const parsedDeleted = deletedRaw ? (JSON.parse(deletedRaw) as string[]) : [];
      setDeletedWorkspaceIds(Array.isArray(parsedDeleted) ? parsedDeleted : []);
      const myBrandId = localStorage.getItem(MY_BRAND_WORKSPACE_KEY) || "";
      setMyBrandWorkspaceId(myBrandId);
    } catch {
      setDeletedWorkspaceIds([]);
      setMyBrandWorkspaceId("");
    }
  }, []);

  useEffect(() => {
    localStorage.setItem(DELETED_WORKSPACES_KEY, JSON.stringify(deletedWorkspaceIds));
  }, [deletedWorkspaceIds]);

  useEffect(() => {
    if (myBrandWorkspaceId) localStorage.setItem(MY_BRAND_WORKSPACE_KEY, myBrandWorkspaceId);
    else localStorage.removeItem(MY_BRAND_WORKSPACE_KEY);
  }, [myBrandWorkspaceId]);

  async function analyzeBrand() {
    const brand = draft.brandName.trim();
    const category = (draft.category || "").trim();
    const geography = (draft.geography || "").trim();
    if (!brand || !category || !geography) {
      setError("Brand name, category, and geography are required for analysis.");
      return;
    }
    setIsAnalyzing(true);
    setError("");
    setInfo("");
    try {
      const enriched = await apiPost<BrandAnalysisResponse>("/workspaces/analyze", {
        brand_name: brand,
        category,
        geography,
      });
      setDraft((prev) => ({
        ...prev,
        website: enriched.website || prev.website,
        industry: enriched.industry || prev.industry,
        positioning: enriched.positioning || prev.positioning,
        brandSummary: enriched.brand_summary || prev.brandSummary || "",
        keyPages: enriched.key_pages?.length ? enriched.key_pages : prev.keyPages,
        brandAnalysis: enriched.brand_analysis || prev.brandAnalysis || {},
      }));
      if (enriched.key_pages?.length) setKeyPagesInput(enriched.key_pages.join(", "));
      setInfo("Fresh strategic analysis is ready. Review and save to keep every agent run context-aware.");
      pushEvent("agent", `AI analysis completed for ${brand}`);
      showToast("success", `Analysis complete for ${brand}!`);
    } catch (err) {
      setError(String(err));
      showToast("error", "Analysis failed. Please try again.");
    } finally {
      setIsAnalyzing(false);
    }
  }

  async function save() {
    setLoading(true);
    setError("");
    setInfo("");
    try {
      const workspaceName = (draft.workspaceName || draft.brandName).trim();
      const workspaceId =
        draft.workspaceId && !draft.workspaceId.startsWith("draft-")
          ? draft.workspaceId
          : `${slugify(workspaceName || draft.brandName)}-ws`;
      const payload = {
        workspace_id: workspaceId,
        workspace_name: workspaceName || workspaceId,
        brand_name: draft.brandName,
        website: draft.website,
        industry: draft.industry,
        category: draft.category || "",
        geography: draft.geography || "",
        positioning: draft.positioning,
        additional_details: draft.additionalDetails || "",
        brand_summary: draft.brandSummary || "",
        brand_analysis: draft.brandAnalysis || {},
        key_pages: draft.keyPages,
        assets: draft.docs.map((doc) => ({
          name: doc.name,
          kind: doc.kind,
          size_bytes: doc.sizeBytes,
          content_type: doc.contentType,
        })),
      };
      const saved = await apiPut<BackendWorkspace>("/workspaces", payload);
      setDraftItems((prev) => prev.filter((row) => row.workspace_id !== draft.workspaceId));
      const localDraft = toDraft(saved);
      saveWorkspaceLocal(localDraft);
      setActiveWorkspaceId(localDraft.workspaceId);
      setDraft(localDraft);
      setKeyPagesInput(localDraft.keyPages.join(", "));
      setInfo(`Workspace saved: ${cleanWorkspaceName(saved.workspace_name)}.`);
      pushEvent("save", `Workspace saved: ${cleanWorkspaceName(saved.workspace_name)}`);
      setShowNewWorkspaceForm(false);
      await reload();
      if (nextPath) window.location.href = nextPath;
      showToast("success", `Workspace saved: ${cleanWorkspaceName(saved.workspace_name)}`);
    } catch (err) {
      setError(String(err));
      showToast("error", "Failed to save workspace. Please try again.");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="workspace-page workspace-redesign grid">
      <section className="workspace-page-head">
        <div>
          <p className="workspace-eyebrow">Brand Intelligence Hub</p>
          <h1>Your Brand Workspaces</h1>
          <p>
            Each workspace holds your brand&apos;s full strategic context — so every agent run starts informed, not from scratch.
          </p>
        </div>
        <button
          type="button"
          className="btn workspace-new-btn"
          onClick={() => {
            const draftId = `draft-${Date.now()}`;
            const draftRow: BackendWorkspace = {
              workspace_id: draftId,
              workspace_name: "New Workspace Draft",
              brand_name: "New Brand",
              website: "",
              industry: "",
              category: "",
              geography: "India",
              positioning: "",
              additional_details: "",
              brand_summary: "",
              brand_analysis: {},
              key_pages: [],
              assets: [],
              updated_at: new Date().toISOString(),
            };
            upsertDraftItem(draftRow);
            setDraft({
              ...EMPTY,
              workspaceId: draftId,
              workspaceName: "New Workspace Draft",
              brandName: "",
              geography: "India",
            });
            setNewWs({ brandName: "", company: "", industry: "", country: "India" });
            setShowNewWorkspaceForm(true);
            setKeyPagesInput("");
            setInfo("");
            setError("");
            pushEvent("edit", "Draft workspace created");
          }}
        >
          <span>+</span> New Workspace
        </button>
      </section>

      {allItems.length === 0 && !showNewWorkspaceForm && (
        <div className="onboarding-tip">
          <span className="onboarding-tip-icon">💡</span>
          <div className="onboarding-tip-content">
            <p className="onboarding-tip-title">Welcome to Brand Workspaces!</p>
            <p className="onboarding-tip-text">
              Create your first workspace to start building brand context. Each workspace stores your brand&apos;s strategic information so agents can run with full context.
            </p>
          </div>
        </div>
      )}

      {allItems.length > 0 && !showNewWorkspaceForm && (
        <div className="onboarding-tip">
          <span className="onboarding-tip-icon">🎯</span>
          <div className="onboarding-tip-content">
            <p className="onboarding-tip-title">Tip: Use &quot;My Brand&quot; to set your primary workspace</p>
            <p className="onboarding-tip-text">
              Mark any workspace as &quot;My Brand&quot; to prioritize it. You can switch between workspaces anytime — each agent run uses the currently active workspace.
            </p>
          </div>
        </div>
      )}

      {showNewWorkspaceForm ? (
        <section className="card workspace-new-intake">
          <h3>Set up your draft workspace</h3>
          <div className="workspace-new-grid">
            <div>
              <label>Brand name</label>
              <input
                className="input"
                list="brand-options"
                value={newWs.brandName}
                onChange={(e) => {
                  const brandName = e.target.value;
                  setNewWs((prev) => ({ ...prev, brandName }));
                  setDraft((prev) => ({ ...prev, brandName, workspaceName: brandName ? `${brandName} Workspace` : prev.workspaceName }));
                  if (draft.workspaceId.startsWith("draft-")) {
                    upsertDraftItem({
                      workspace_id: draft.workspaceId,
                      workspace_name: brandName ? `${brandName} Workspace` : "New Workspace Draft",
                      brand_name: brandName || "New Brand",
                      website: "",
                      industry: newWs.industry,
                      category: draft.category || "",
                      geography: newWs.country || "India",
                      positioning: "",
                      additional_details: "",
                      brand_summary: "",
                      brand_analysis: {},
                      key_pages: [],
                      assets: [],
                      updated_at: new Date().toISOString(),
                    });
                  }
                }}
                placeholder="Search or type brand"
              />
            </div>
            <div>
              <label>Company</label>
              <input
                className="input"
                list="company-options"
                value={newWs.company}
                onChange={(e) => {
                  const company = e.target.value;
                  setNewWs((prev) => ({ ...prev, company }));
                  setDraft((prev) => ({ ...prev, additionalDetails: company ? `Company: ${company}` : prev.additionalDetails }));
                }}
                placeholder="Search or type company"
              />
            </div>
            <div>
              <label>Industry</label>
              <input
                className="input"
                list="industry-options"
                value={newWs.industry}
                onChange={(e) => {
                  const industry = e.target.value;
                  setNewWs((prev) => ({ ...prev, industry }));
                  setDraft((prev) => ({ ...prev, industry, category: prev.category || industry }));
                }}
                placeholder="Search or choose industry"
              />
            </div>
            <div>
              <label>Country</label>
              <input
                className="input"
                list="country-options"
                value={newWs.country}
                onChange={(e) => {
                  const country = e.target.value;
                  setNewWs((prev) => ({ ...prev, country }));
                  setDraft((prev) => ({ ...prev, geography: country }));
                }}
                placeholder="Search or choose country"
              />
            </div>
          </div>
          <datalist id="brand-options">{BRAND_SUGGESTIONS.map((s) => <option value={s} key={s} />)}</datalist>
          <datalist id="company-options">{COMPANY_SUGGESTIONS.map((s) => <option value={s} key={s} />)}</datalist>
          <datalist id="industry-options">{INDUSTRY_SUGGESTIONS.map((s) => <option value={s} key={s} />)}</datalist>
          <datalist id="country-options">{COUNTRY_SUGGESTIONS.map((s) => <option value={s} key={s} />)}</datalist>
        </section>
      ) : null}

      <section className="workspace-layout">
        <aside className="workspace-left">
          <div className="workspace-left-head">
            <h3>Saved Workspaces</h3>
            <span className="workspace-count-pill">{allItems.length} workspaces</span>
          </div>
          <div className="workspace-search-wrap">
            <svg viewBox="0 0 24 24" aria-hidden="true">
              <circle cx="11" cy="11" r="7" />
              <path d="m20 20-3.2-3.2" />
            </svg>
            <input className="workspace-search" placeholder="Search workspaces..." value={query} onChange={(e) => setQuery(e.target.value)} />
            {query ? (
              <button type="button" className="workspace-clear-search" onClick={() => setQuery("")} aria-label="Clear search">
                ×
              </button>
            ) : null}
          </div>

          <select
            className="workspace-select-mobile"
            value={activeWorkspaceId}
            onChange={(e) => {
              const selected = allItems.find((item) => item.workspace_id === e.target.value);
              if (!selected) return;
              const nextDraft = toDraft(selected);
              setDraft(nextDraft);
              setKeyPagesInput(nextDraft.keyPages.join(", "));
              setActiveWorkspaceId(nextDraft.workspaceId);
              saveWorkspaceLocal(nextDraft);
              setShowNewWorkspaceForm(nextDraft.workspaceId.startsWith("draft-"));
              pushEvent("edit", `Workspace selected: ${cleanWorkspaceName(nextDraft.workspaceName || nextDraft.workspaceId)}`);
            }}
          >
            {allItems.map((item) => (
              <option key={item.workspace_id} value={item.workspace_id}>
                {cleanWorkspaceName(item.workspace_name)} | {item.brand_name}
              </option>
            ))}
          </select>

          <div className="workspace-list-cards">
            {filteredItems.map((item) => {
              const selected = item.workspace_id === activeWorkspaceId;
              return (
                <article key={item.workspace_id} className={`workspace-list-item ${selected ? "active" : ""}`}>
                  <div className="workspace-avatar" style={{ background: avatarColor(item.brand_name) }}>
                    {(item.brand_name || "B").charAt(0).toUpperCase()}
                  </div>
                  <div className="workspace-list-meta">
                    <p className="workspace-list-name">{cleanWorkspaceName(item.workspace_name)}</p>
                    <p className="workspace-list-brand">{item.brand_name}</p>
                    <p className="workspace-list-time">Updated {relativeTime(item.updated_at)}</p>
                    {item.workspace_id === myBrandWorkspaceId ? <span className="workspace-my-brand-pill">★ My Brand</span> : null}
                  </div>
                  <div className="workspace-row-actions">
                    <button
                      type="button"
                      className={`workspace-my-brand-link ${item.workspace_id === myBrandWorkspaceId ? "active" : ""}`}
                      onClick={() => {
                        if (item.workspace_id === myBrandWorkspaceId) {
                          setMyBrandWorkspaceId("");
                          pushEvent("edit", `Unmarked My Brand: ${cleanWorkspaceName(item.workspace_name)}`);
                        } else {
                          setMyBrandWorkspaceId(item.workspace_id);
                          pushEvent("edit", `Marked as My Brand: ${cleanWorkspaceName(item.workspace_name)}`);
                        }
                      }}
                    >
                      {item.workspace_id === myBrandWorkspaceId ? "★ My Brand" : "My Brand"}
                    </button>
                    <button
                      type="button"
                      className="workspace-use-link"
                      onClick={() => {
                        const nextDraft = toDraft(item);
                        setDraft(nextDraft);
                        setKeyPagesInput(nextDraft.keyPages.join(", "));
                        setActiveWorkspaceId(nextDraft.workspaceId);
                        saveWorkspaceLocal(nextDraft);
                        setShowNewWorkspaceForm(nextDraft.workspaceId.startsWith("draft-"));
                        pushEvent("edit", `Workspace selected: ${cleanWorkspaceName(nextDraft.workspaceName || nextDraft.workspaceId)}`);
                      }}
                    >
                      Use <span aria-hidden="true">→</span>
                    </button>
                    <button
                      type="button"
                      className="workspace-delete-link"
                      onClick={() => {
                        setDeletedWorkspaceIds((prev) => (prev.includes(item.workspace_id) ? prev : [item.workspace_id, ...prev]));
                        if (item.workspace_id === myBrandWorkspaceId) setMyBrandWorkspaceId("");
                        if (item.workspace_id === draft.workspaceId) {
                          setDraft(EMPTY);
                          setShowNewWorkspaceForm(false);
                        }
                        pushEvent("edit", `Deleted workspace: ${cleanWorkspaceName(item.workspace_name)}`);
                      }}
                    >
                      Delete
                    </button>
                  </div>
                </article>
              );
            })}
          </div>
        </aside>

        <div className="workspace-right">
          <div className="workspace-action-row">
            <button
              type="button"
              className="btn btn-subtle"
              onClick={() => {
                setQuickEdit((v) => !v);
                pushEvent("edit", "Quick edit toggled");
              }}
            >
              <svg viewBox="0 0 24 24" aria-hidden="true"><path d="m4 20 4.5-1 9.6-9.6a1.5 1.5 0 0 0 0-2.1l-1.4-1.4a1.5 1.5 0 0 0-2.1 0L5 15.5 4 20Z" /><path d="M13 7l4 4" /></svg>
              Quick Edit
            </button>
            <Tooltip content="AI analyzes your brand and fills in strategic context automatically">
              <button type="button" className="btn btn-subtle" onClick={analyzeBrand} disabled={isAnalyzing}>
                <svg viewBox="0 0 24 24" aria-hidden="true"><path d="m12 3 1.8 4.2L18 9l-4.2 1.8L12 15l-1.8-4.2L6 9l4.2-1.8L12 3Z" /><path d="M19 16.5 20 19l2.5 1-2.5 1-1 2.5-1-2.5-2.5-1 2.5-1 1-2.5Z" /></svg>
                {isAnalyzing ? "Analyzing..." : "Analyze with AI"}
              </button>
            </Tooltip>
            <Tooltip content="Save your workspace to keep it for future agent runs">
              <button type="button" className="btn" onClick={save} disabled={loading}>
                <svg viewBox="0 0 24 24" aria-hidden="true"><path d="M5 5h12l2 2v12H5V5Z" /><path d="M8 5v5h8V5M8 19v-5h8v5" /></svg>
                {loading ? "Saving..." : isEdit ? "Save Workspace" : "Create Workspace"}
              </button>
            </Tooltip>
          </div>

          <section className="workspace-snapshot-head">
            <p>Brand Intelligence Snapshot</p>
            <h2>{draft.brandName || "Maruti Suzuki Swift"}</h2>
            <span>{draft.category || "Automotive"} · {draft.geography || "India"}</span>
          </section>

          <section className="workspace-summary-card-pro">
            <div className="workspace-summary-top">
              <p className="workspace-summary-label">Strategic Summary</p>
              <button
                type="button"
                className="workspace-icon-btn"
                onClick={() => {
                  setQuickEdit((v) => !v);
                  pushEvent("edit", "Strategic summary opened for edit");
                }}
                aria-label="Edit summary"
              >
                ✎
              </button>
            </div>
            {quickEdit ? (
              <textarea className="textarea" value={draft.brandSummary || DEFAULT_SUMMARY} onChange={(e) => setDraft((prev) => ({ ...prev, brandSummary: e.target.value }))} />
            ) : (
              <p>{draft.brandSummary || DEFAULT_SUMMARY}</p>
            )}
          </section>

          <section className="workspace-brand-grid">
            {BRAND_GRID_ITEMS.map((item) => (
              <article key={item.key} className={`workspace-brand-card ${item.risk ? "risk" : ""}`}>
                <div className="workspace-brand-card-head">
                  <div className="workspace-brand-label-wrap">
                    <span className="workspace-brand-dot" style={{ background: item.dot }} />
                    <span className="workspace-brand-label">{item.label}</span>
                  </div>
                  <button
                    type="button"
                    className="workspace-card-edit"
                    onClick={() => {
                      setQuickEdit((v) => !v);
                      pushEvent("edit", `${item.label} opened for edit`);
                    }}
                    aria-label={`Edit ${item.label}`}
                  >
                    ✎
                  </button>
                </div>
                {quickEdit ? (
                  <textarea
                    className="textarea"
                    value={(draft.brandAnalysis || {})[item.key] || item.defaultText}
                    onChange={(e) =>
                      setDraft((prev) => ({
                        ...prev,
                        brandAnalysis: { ...(prev.brandAnalysis || {}), [item.key]: e.target.value },
                      }))
                    }
                  />
                ) : (
                  <p>{(draft.brandAnalysis || {})[item.key] || item.defaultText}</p>
                )}
              </article>
            ))}
          </section>

          <section className="workspace-details-card">
            <div className="workspace-details-head">
              <h3>Brand Details</h3>
            </div>
            <div className="workspace-details-grid">
              <div className="workspace-detail-row">
                <span className="workspace-detail-label">Brand</span>
                <span className="workspace-detail-value">{draft.brandName || "—"}</span>
              </div>
              <div className="workspace-detail-row">
                <span className="workspace-detail-label">Website</span>
                <span className="workspace-detail-value">
                  {draft.website ? (
                    <a href={draft.website} target="_blank" rel="noopener noreferrer">{draft.website}</a>
                  ) : "—"}
                </span>
              </div>
              <div className="workspace-detail-row">
                <span className="workspace-detail-label">Category</span>
                <span className="workspace-detail-value">{draft.category || "—"}</span>
              </div>
              <div className="workspace-detail-row">
                <span className="workspace-detail-label">Geography</span>
                <span className="workspace-detail-value">{draft.geography || "—"}</span>
              </div>
              <div className="workspace-detail-row">
                <span className="workspace-detail-label">Industry</span>
                <span className="workspace-detail-value">{draft.industry || "—"}</span>
              </div>
            </div>
            {draft.positioning && (
              <div className="workspace-positioning">
                <span className="workspace-detail-label">Positioning</span>
                <p>{draft.positioning}</p>
              </div>
            )}
            {draft.keyPages.length > 0 && (
              <div className="workspace-key-pages">
                <span className="workspace-detail-label">Key Pages</span>
                <div className="workspace-pages-list">
                  {draft.keyPages.map((page, idx) => (
                    <a key={idx} href={page} target="_blank" rel="noopener noreferrer" className="workspace-page-tag">
                      {page.replace(/^https?:\/\//, "").split("/")[0]}
                    </a>
                  ))}
                </div>
              </div>
            )}
          </section>

          <section className="workspace-events-pro">
            <div className="workspace-events-head">
              <h3>Activity Log</h3>
              <select className="workspace-activity-filter" value={activityFilter} onChange={(e) => setActivityFilter(e.target.value as "all" | EventType)}>
                <option value="all">All activity</option>
                <option value="save">Save</option>
                <option value="agent">Agent run</option>
                <option value="edit">Edit</option>
              </select>
            </div>
            {filteredEvents.length === 0 ? (
              <div className="workspace-events-empty">
                <svg viewBox="0 0 220 120" aria-hidden="true">
                  <path d="M30 20v80M30 30h45M30 60h65M30 90h40" />
                  <circle cx="30" cy="30" r="5" />
                  <circle cx="30" cy="60" r="5" />
                  <circle cx="30" cy="90" r="5" />
                  <path d="M80 30h100M100 60h80M75 90h105" />
                </svg>
                <h4>No activity yet</h4>
                <p>Run an agent or save changes to start building your workspace history.</p>
                <Link href={"/agents" as Route}>Run your first agent →</Link>
              </div>
            ) : (
              <div className="workspace-events-timeline">
                {filteredEvents.map((event, idx) => (
                  <div className="workspace-event-row" key={`${event.ts}-${idx}`}>
                    <p>{relativeTime(event.ts)}</p>
                    <div className="workspace-event-track">
                      <span style={{ background: eventDot(event.type) }} />
                    </div>
                    <div>{event.message}</div>
                  </div>
                ))}
              </div>
            )}
          </section>

          {error ? <p className="workspace-msg workspace-error">{error}</p> : null}
          {info ? <p className="workspace-msg workspace-info">{info}</p> : null}
        </div>
      </section>
    </div>
  );
}
