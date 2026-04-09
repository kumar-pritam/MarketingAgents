# PRD: Competitor Intelligence Agent — Automated Brand & Messaging Monitor
**Version:** 1.0
**Author:** Kumar Pritam
**Status:** Draft — WTP Validation Build
**Last Updated:** March 2026

---

## Table of Contents

1. [Overview](#overview)
2. [Problem Statement](#problem-statement)
3. [Target Users](#target-users)
4. [Goals & Success Metrics](#goals--success-metrics)
5. [Functional Requirements](#functional-requirements)
6. [Agent Architecture](#agent-architecture)
7. [Integrations](#integrations)
8. [Data Models](#data-models)
9. [UI / UX Specification](#ui--ux-specification)
10. [Non-Functional Requirements](#non-functional-requirements)
11. [Build Phases](#build-phases)
12. [Cost Model](#cost-model)
13. [Open Questions](#open-questions)

---

## Overview

Competitor Intelligence Agent is an AI-powered monitoring system that continuously tracks competitor websites, ad creatives, landing pages, messaging, and product positioning — and synthesizes everything into a structured weekly digest. It tells brand and marketing teams not just *what* changed, but *why it matters* and *how fast* competitors are moving.

Unlike generic web monitoring tools (Google Alerts, Mention), this agent adds an LLM reasoning layer that interprets signals: detecting messaging pivots, pricing strategy shifts, new market entries, and campaign angle changes — then surfaces the so-what for the user's own brand strategy.

---

## Problem Statement

### What's Happening
Marketing and brand strategy teams spend 4–8 hours per week manually checking competitor websites, social profiles, and ad libraries. The output is usually a fragmented spreadsheet that nobody reads, updated irregularly, and missing the strategic interpretation layer.

### The Gap
- **Google Alerts** — catches keyword mentions in news but misses website copy changes, ad strategy, and landing page pivots
- **Semrush / Ahrefs** — strong on SEO rankings but blind to messaging, creative direction, and product positioning changes
- **Manual monitoring** — slow, inconsistent, and does not scale across 5+ competitors
- **No tool today** combines website change detection + ad creative tracking + LLM-powered strategic interpretation in one automated weekly flow

### The Consequence
Teams react late to competitor moves. A pricing change, a new audience segment being targeted, or a new value proposition goes unnoticed for weeks. By the time the brand responds, the competitor has already captured mindshare.

---

## Target Users

### Primary Persona — The Brand Strategist / Head of Marketing
- Works at a mid-to-large enterprise or growing startup
- Responsible for brand positioning, messaging architecture, and campaign strategy
- Spends hours manually reviewing competitor activity every week
- Pain: No single source of truth on competitor moves; always playing catch-up
- Willingness to pay: ₹12,000–₹30,000/month

### Secondary Persona — The Product Marketing Manager (PMM)
- Owns competitive positioning, battle cards, and win/loss narrative
- Needs up-to-date competitor messaging for sales enablement
- Pain: Battle cards go stale within weeks of being written; no automated refresh mechanism
- Willingness to pay: ₹8,000–₹20,000/month

### Tertiary Persona — The Strategy Consultant / Agency Account Lead
- Manages competitive landscape for multiple client accounts
- Needs a scalable, repeatable intel process across brands and industries
- Pain: Manual competitive analysis is not billable at scale; needs productized intel delivery
- Willingness to pay: ₹40,000–₹80,000/month (multi-client agency pricing)

---

## Goals & Success Metrics

### Product Goals
| Goal | Metric | Target |
|---|---|---|
| Demonstrate WTP | Paid pilots secured | 2 of first 5 demos convert |
| Core value delivery | Weekly digest generated per schedule | 100% on-time, < 5 min runtime |
| Signal quality | User acts on ≥ 1 insight per digest | Tracked via feedback button |
| Stickiness | Digest opened next week | ≥ 80% return read rate |
| Time saved | Hours saved vs manual monitoring | ≥ 4 hours/week reported |

### Business Goals (Post-Validation)
- Month 3: 5 paying clients, ₹1,00,000 MRR
- Month 6: 15 clients, ₹3,00,000 MRR
- Month 12: SaaS dashboard live with multi-user support, ₹12L+ MRR

---

## Functional Requirements

### FR-01: Competitor & Brand Setup
- User inputs their own brand name and website URL
- User inputs up to 8 competitor names with website URLs
- User inputs monitoring focus areas (optional tags): Pricing / Messaging / Product / Ads / Hiring / PR
- User sets monitoring cadence: Weekly (default) / Daily (Phase 2)
- User can add custom "watch phrases" — specific terms to flag if they appear in competitor content (e.g., "enterprise plan", "ISO certified", "new partnership")
- System validates all URLs before saving configuration

### FR-02: Website Change Detector
- On each scheduled run, agent fetches HTML of key competitor pages:
  - Homepage
  - Pricing page (if detectable via URL pattern)
  - Product / Features page
  - About / Mission page
- Compares current fetch against previous stored snapshot (diff-based)
- Detects and classifies changes:
  - **Copy changes** — headline, subheadline, CTA text, value proposition statements
  - **Structural changes** — new sections added, sections removed, page reorganized
  - **Pricing changes** — new tiers, price points, feature inclusions/exclusions
  - **New pages** — new URLs detected on sitemap or navigation that did not exist before
- Stores snapshots as plain text (stripped HTML) to minimize storage
- Change threshold: Only flag changes above 5% content delta to suppress minor edits

### FR-03: Ad Creative Monitor (Meta Ad Library)
- Pulls active ads for each competitor brand via Meta Ad Library API
- Tracks per competitor:
  - Number of active ads (volume signal — high volume = active push)
  - New ads launched since last check
  - Ad copy themes and headlines
  - Audience targeting signals (age, region if available)
  - Estimated ad run duration (long-running = proven creative)
- Detects messaging pivots: if a competitor's dominant ad theme shifts between weeks, flag as "Messaging Pivot Detected"
- Stores raw ad data per competitor per week for trend analysis

### FR-04: Hacker News & Public Signal Monitor
- Searches Hacker News API for competitor brand mentions (last 7 days)
- Classifies mentions by sentiment: Praise / Criticism / Neutral / Technical Discussion
- Detects patterns: sudden spike in mentions may signal product launch, outage, controversy, or press coverage
- Also monitors public job postings via Google for hiring signals (e.g., competitor hiring 5 ML engineers = product investment signal)
- Graceful fallback: If no HN mentions found, section is omitted from digest

### FR-05: LLM Analysis & Signal Interpretation
- After data collection, all raw signals are passed to the LLM (via OpenRouter)
- LLM performs structured analysis per competitor:
  - **What changed** — factual summary of detected changes
  - **What it signals** — strategic interpretation (e.g., "Shift from SME to Enterprise messaging suggests upmarket move")
  - **Speed of movement** — Slow / Moderate / Fast / Aggressive (based on change frequency and volume)
  - **Threat level to your brand** — Low / Medium / High with one-line rationale
  - **Recommended response** — one concrete action the user's brand should consider
- LLM is provided brand context of the user's own brand to make interpretations relative, not generic

### FR-06: Competitive Velocity Scoring
Compute a weekly Competitive Velocity Score (CVS) per competitor:

```
CVS = weighted sum of:
  Website changes detected:     30%  (0 = none, 10 = major rewrite)
  Ad volume change (week/week): 25%  (increase = higher score)
  New ad themes launched:       20%
  Public signal volume (HN):    15%
  New pages / product signals:  10%

CVS Range: 0–100
  0–20  = Dormant
  21–40 = Steady
  41–60 = Active
  61–80 = Aggressive
  81–100 = Sprint Mode
```

CVS shown as a trend sparkline over 4 weeks once history exists.

### FR-07: Weekly Digest Generator
- Final output is a structured digest document with the following sections:
  1. **Executive Summary** — 3–5 bullets, biggest moves this week across all competitors
  2. **Competitor Scorecards** — one card per competitor with CVS, changes detected, threat level
  3. **Deep Dives** — detailed section for competitors with CVS > 40 (Active or above)
  4. **Ad Intelligence** — top 3 new ad creatives per active competitor with copy analysis
  5. **Your Brand's Blind Spots** — topics competitors are actively messaging that your brand isn't
  6. **Recommended Actions** — 3–5 prioritized actions ranked by urgency
- Digest must be readable as a standalone document with no tool access required
- Written at executive communication level — crisp, opinionated, not just descriptive

### FR-08: Digest Delivery
- Phase 1: Digest displayed in Streamlit UI + copy-to-clipboard button
- Phase 2: Digest exported as PDF and emailed via SendGrid free tier
- Phase 2: Slack webhook delivery (send digest summary as a formatted Slack message)
- Digest stored locally as JSON + markdown for audit trail

### FR-09: Historical Timeline & Velocity Trend
- Phase 2: Each week's digest archived locally
- Timeline view: scroll through past digests by date
- CVS trend chart: 8-week sparkline per competitor showing acceleration/deceleration
- "First detected" timestamp for each messaging theme — shows who moved first

---

## Agent Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                         STREAMLIT UI                            │
│   Setup → Monitor Config → Run Now → Digest → History          │
└──────────────────────────┬──────────────────────────────────────┘
                           │
┌──────────────────────────▼──────────────────────────────────────┐
│                    ORCHESTRATOR (main.py)                        │
│    Manages agent pipeline, shared state, error handling         │
└──┬──────────────┬──────────────┬──────────────┬────────────────┘
   │              │              │              │
   ▼              ▼              ▼              ▼
┌─────────┐ ┌──────────┐ ┌───────────┐ ┌──────────────────┐
│  Web    │ │   Ad     │ │  Public   │ │     Analyst      │
│ Scraper │ │ Monitor  │ │  Signal   │ │     Agent        │
│  Agent  │ │  Agent   │ │  Agent    │ │                  │
│         │ │          │ │           │ │ LLM interprets   │
│Fetches  │ │Meta Ad   │ │HN API +   │ │ all signals →   │
│pages,   │ │Library   │ │Google job │ │ CVS scoring +   │
│diffs vs │ │API pulls │ │ search    │ │ digest output   │
│snapshot │ │ad data   │ │ signals   │ │                  │
└─────────┘ └──────────┘ └───────────┘ └──────────────────┘
     │              │              │              │
     └──────────────┴──────────────┴──────────────┘
                           │
              ┌────────────┼──────────────┐
              ▼            ▼              ▼
       Meta Ad        Hacker News    Local JSON
       Library API    API (free)     Snapshots
       (free)                        /data/snapshots/
              │
       OpenRouter API
       (LLM Analysis)
       Free Model
```

### Agent Personas

**Web Scraper Agent** — Operates as a technical content analyst. Fetches competitor pages, strips HTML to readable text, performs semantic diff against previous snapshot, and classifies the nature and magnitude of changes.

**Ad Monitor Agent** — Operates as a media buyer analyst. Pulls active ad data from Meta Ad Library, identifies new creatives, clusters ad copy by theme using keyword grouping, and flags volume anomalies.

**Public Signal Agent** — Operates as a market intelligence analyst. Monitors Hacker News for brand sentiment, searches for hiring signals, and identifies any PR or community activity worth flagging.

**Analyst Agent** — Operates as a senior competitive strategist. Receives all collected signals, applies the user's brand context, and generates the full strategic interpretation. This is the highest-value LLM call in the pipeline — it must produce opinionated, specific insights, not generic summaries.

---

## Integrations

All integrations beyond OpenRouter are **optional**. The core agent can run with web scraping + OpenRouter alone, delivering meaningful output on day one.

### Integration 1: OpenRouter API *(Required)*
- **Purpose:** LLM analysis, signal interpretation, digest generation (Analyst Agent)
- **Auth:** API key via `.env` file (`OPENROUTER_API_KEY`)
- **Base URL:** `https://openrouter.ai/api/v1` (OpenAI-SDK compatible)
- **Primary Model:** `meta-llama/llama-3.3-70b-instruct:free`
- **Fallback Model:** `openrouter/free` — auto-selects best available free model
- **Free tier:** 20 req/min, 200 req/day — no credit card required
- **Capacity:** ~1 LLM call per competitor (analysis) + 1 digest call = ~9 calls/run for 8 competitors. Well within 200/day limit
- **Setup:**
  1. Create account at openrouter.ai
  2. Keys → Create API Key
  3. Store as `OPENROUTER_API_KEY` in `.env`
- **API call pattern:**
```python
from openai import OpenAI

client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=os.getenv("OPENROUTER_API_KEY")
)

response = client.chat.completions.create(
    model="meta-llama/llama-3.3-70b-instruct:free",
    messages=[
        {"role": "system", "content": "You are a senior competitive intelligence analyst..."},
        {"role": "user", "content": competitor_signals_json}
    ]
)
```

### Integration 2: Meta Ad Library API *(Optional — High Value)*
- **Purpose:** Pull active ad creatives, copy, and volume data per competitor
- **Auth:** Facebook Developer App Token (free, no ad account needed)
- **Free tier:** Fully free, read-only access
- **Rate limits:** 200 calls/hour per token — sufficient for weekly runs
- **Setup flow:**
  1. Create account at developers.facebook.com
  2. Create a new App → Business type
  3. Add Marketing API product
  4. Generate App Access Token (Settings → Basic → App Token)
  5. Store as `META_AD_LIBRARY_TOKEN` in `.env`
- **Key API endpoint:**
```
GET https://graph.facebook.com/v18.0/ads_archive
  ?search_terms={competitor_name}
  &ad_reached_countries=IN
  &ad_active_status=ACTIVE
  &fields=id,ad_creative_body,ad_creative_link_caption,ad_delivery_start_time
  &access_token={token}
```
- **Graceful fallback:** Ad Intelligence section excluded from digest if token absent. UI shows "Connect Meta Ad Library for ad creative tracking" prompt.

### Integration 3: Hacker News API *(Optional — Free, No Auth)*
- **Purpose:** Monitor competitor brand mentions in tech community discussions
- **Auth:** None required — fully public API
- **Free tier:** Completely free, no rate limits for reasonable use
- **Base URL:** `https://hacker-news.firebaseio.com/v0/`
- **Search endpoint:** `https://hn.algolia.com/api/v1/search?query={brand}&tags=story`
- **Setup:** No setup needed — works out of the box
- **Graceful fallback:** If no mentions found in last 7 days, section omitted cleanly

### Integration 4: Google Sheets API *(Optional)*
- **Purpose:** Store weekly digests in a shared sheet for team access and trend tracking
- **Auth:** OAuth 2.0 via Google account
- **Free tier:** Fully free
- **Scopes required:** `https://www.googleapis.com/auth/spreadsheets`
- **Setup flow:**
  1. Create project at console.cloud.google.com
  2. Enable Sheets API
  3. Create OAuth 2.0 credentials (Desktop App)
  4. Download `credentials.json` → place in `/integrations/`
  5. On first run, browser opens for Google login → token saved as `token.json`
- **Graceful fallback:** Digest saved to local markdown only

### Integration 5: Slack Webhook *(Optional — Phase 2)*
- **Purpose:** Deliver weekly digest summary as a Slack message to a team channel
- **Auth:** Slack Incoming Webhook URL (free, no Slack paid plan needed)
- **Free tier:** Fully free for incoming webhooks
- **Setup flow:**
  1. Go to api.slack.com/apps → Create New App
  2. Enable Incoming Webhooks
  3. Add to a workspace → choose channel → copy Webhook URL
  4. Store as `SLACK_WEBHOOK_URL` in `.env`
- **Graceful fallback:** Delivery skipped; digest available in UI only

### Integration Summary Table

| Integration | Required? | Auth Type | Cost | Phase |
|---|---|---|---|---|
| OpenRouter API | ✅ Yes | API Key | Free (200 req/day) | 1 |
| Web Scraping (BeautifulSoup) | ✅ Yes | None | Free | 1 |
| Hacker News API | Optional | None | Free | 1 |
| Meta Ad Library API | Optional | App Token | Free | 1 |
| Google Sheets | Optional | OAuth 2.0 | Free | 1 |
| Slack Webhook | Optional | Webhook URL | Free | 2 |

---

## Data Models

### MonitorConfig
```json
{
  "config_id": "uuid",
  "own_brand": {
    "name": "string",
    "website": "string",
    "positioning": "string"
  },
  "competitors": [
    {
      "name": "string",
      "website": "string",
      "pages_to_monitor": ["homepage", "pricing", "features", "about"]
    }
  ],
  "watch_phrases": ["string"],
  "focus_areas": ["Pricing", "Messaging", "Product", "Ads", "Hiring"],
  "cadence": "weekly | daily",
  "created_at": "ISO8601"
}
```

### PageSnapshot
```json
{
  "competitor_name": "string",
  "page_type": "homepage | pricing | features | about | other",
  "url": "string",
  "content_text": "string",
  "content_hash": "string",
  "fetched_at": "ISO8601",
  "run_id": "uuid"
}
```

### PageDiff
```json
{
  "competitor_name": "string",
  "page_type": "string",
  "url": "string",
  "diff_summary": "string",
  "change_magnitude": "none | minor | moderate | major",
  "change_types": ["copy", "pricing", "structure", "new_page"],
  "previous_snapshot_date": "ISO8601",
  "current_snapshot_date": "ISO8601"
}
```

### AdData
```json
{
  "competitor_name": "string",
  "run_id": "uuid",
  "total_active_ads": "integer",
  "new_ads_since_last_run": "integer",
  "top_ad_themes": ["string"],
  "dominant_cta": "string",
  "ads": [
    {
      "ad_id": "string",
      "body": "string",
      "headline": "string",
      "start_date": "ISO8601",
      "days_running": "integer"
    }
  ]
}
```

### PublicSignal
```json
{
  "competitor_name": "string",
  "source": "hacker_news | google_news",
  "mentions_count": "integer",
  "sentiment_distribution": {
    "positive": "integer",
    "negative": "integer",
    "neutral": "integer"
  },
  "top_discussions": [
    {
      "title": "string",
      "url": "string",
      "points": "integer",
      "date": "ISO8601"
    }
  ]
}
```

### CompetitorAnalysis
```json
{
  "competitor_name": "string",
  "run_id": "uuid",
  "cvs_score": "float",
  "cvs_category": "dormant | steady | active | aggressive | sprint",
  "threat_level": "low | medium | high",
  "what_changed": "string",
  "strategic_interpretation": "string",
  "speed_of_movement": "slow | moderate | fast | aggressive",
  "recommended_response": "string",
  "key_signals": ["string"]
}
```

### WeeklyDigest
```json
{
  "digest_id": "uuid",
  "run_id": "uuid",
  "generated_at": "ISO8601",
  "own_brand": "string",
  "period": "string",
  "executive_summary": ["string"],
  "competitor_analyses": ["CompetitorAnalysis"],
  "ad_intelligence": ["AdData"],
  "brand_blind_spots": ["string"],
  "recommended_actions": [
    {
      "action": "string",
      "urgency": "immediate | this_week | this_month",
      "rationale": "string"
    }
  ],
  "total_run_time_seconds": "float",
  "llm_calls_made": "integer"
}
```

---

## UI / UX Specification

### Screen 1: Setup & Configuration
- **Your Brand** section: Name + Website + 1-line positioning statement
- **Competitors** section: Up to 8 rows of Name + Website inputs; add/remove rows dynamically
- **Watch Phrases** section: Tag input field — phrases to flag anywhere they appear
- **Focus Areas** section: Multi-select toggle: Pricing / Messaging / Ads / Product / Hiring / PR
- **Integrations panel** (collapsible): Meta Ad Library token input, GSC OAuth button, Slack webhook input
- **Cadence selector**: Weekly (Monday 9am) / Run Manually
- CTA: `→ Save & Run First Monitor`

### Screen 2: Running (Progress)
- Step-by-step progress log:
  ```
  ✅ Fetching Competitor 1 homepage... done
  ✅ Fetching Competitor 2 homepage... done
  ⏳ Pulling Meta Ad Library for Competitor 3...
  ⏳ Analysing signals with AI...
  ```
- Live CVS preview as scores are computed
- Cancel button available
- Estimated time remaining

### Screen 3: Weekly Digest View
**Header bar:**
```
Week of [Date] | 6 competitors monitored | Run time: 3m 42s
[Export PDF]  [Copy Summary]  [Send to Slack]
```

**Section A — Executive Summary**
- 3–5 bold bullet points, largest moves of the week
- Color-coded urgency tags: 🔴 Act Now / 🟡 Watch / 🟢 Steady

**Section B — Competitor Scorecards (grid view)**
```
┌─────────────────┬─────────────────┬─────────────────┐
│  Competitor A   │  Competitor B   │  Competitor C   │
│  CVS: 74 🔴     │  CVS: 32 🟢     │  CVS: 58 🟡     │
│  AGGRESSIVE     │  STEADY         │  ACTIVE         │
│  Threat: HIGH   │  Threat: LOW    │  Threat: MED    │
│  [View Details] │  [View Details] │  [View Details] │
└─────────────────┴─────────────────┴─────────────────┘
```

**Section C — Deep Dive Cards (expanded for CVS > 40)**
Each card contains:
- What changed (bullet summary)
- Strategic interpretation (1 paragraph)
- Ad Intelligence (top 2 new creatives with copy)
- Recommended response

**Section D — Your Brand's Blind Spots**
- Topics competitors are actively messaging that the user's brand isn't
- Shown as a simple gap table: Topic | Who's Messaging It | Intensity

**Section E — Action Plan**
- Numbered list, 3–5 actions, each with urgency badge and rationale
- "Mark as Done" checkbox per action (local state only)

### Screen 4: History Timeline (Phase 2)
- Calendar strip showing past digest dates
- Click any date to view that week's digest
- CVS trend chart: 8-week line chart per competitor
- "First seen" timestamps for messaging themes

---

## Non-Functional Requirements

| Requirement | Specification |
|---|---|
| Runtime | Full run for 8 competitors completes in < 6 minutes |
| LLM calls | ≤ 10 LLM calls per full run (well within 200/day free limit) |
| Cost per run | $0.00 on OpenRouter free tier |
| Scraping reliability | Retry failed page fetches up to 3 times; skip and log if still failing |
| Snapshot storage | Store as plain text (HTML stripped); max ~50KB per page per week |
| Data privacy | All snapshots and digests stored locally; no data sent to third parties except OpenRouter and Meta Ad Library API |
| Anti-blocking | Requests include realistic User-Agent headers; 2–3 second delay between fetches per domain |
| Portability | Runs on Mac, Windows, Linux via `streamlit run app.py` |
| Graceful degradation | If any integration fails (Meta, HN), run continues and digest notes the data gap |

---

## Build Phases

### Phase 1 — WTP Validation Build (Target: 2 weeks)
**Goal:** Working prototype that generates a demo-able weekly digest for 3–5 competitors.

| Task | File | Priority |
|---|---|---|
| Setup & config form | `app.py` | P0 |
| Web scraper + HTML stripper | `agent/web_scraper.py` | P0 |
| Diff engine (compare snapshots) | `agent/diff_engine.py` | P0 |
| Hacker News signal puller | `agent/hn_monitor.py` | P0 |
| Analyst Agent (LLM interpretation) | `agent/analyst.py` | P0 |
| CVS scorer | `agent/scorer.py` | P0 |
| Digest generator | `agent/digest.py` | P0 |
| Results display in UI | `app.py` (digest section) | P0 |
| Local JSON snapshot store | `data/snapshots/` | P0 |
| Meta Ad Library integration | `integrations/meta_ads.py` | P1 |
| Google Sheets export | `integrations/sheets_client.py` | P1 |

### Phase 2 — Paid Pilot Build (Target: Month 2)
- PDF export of weekly digest
- Slack webhook delivery
- 8-week CVS trend chart
- Email digest via SendGrid free tier
- Hiring signal detection (Google job search scraping)
- Scheduled automated weekly runs (APScheduler)
- Multi-brand workspace (monitor different brand sets)

### Phase 3 — SaaS Launch (Target: Month 4–6)
- Deploy on Render or Railway
- User authentication (Supabase free tier)
- Stripe payment integration
- White-label digest branding for agency clients
- API endpoint: `GET /digest/latest`, `GET /competitor/{name}/history`
- Browser extension (Phase 3+): Real-time flag when visiting competitor site

---

## Cost Model

### Per Run Cost (Phase 1 — Local, Free Tier)
| Item | Calls | Cost |
|---|---|---|
| Web scraping (BeautifulSoup) | 8 competitors × 4 pages = 32 fetches | $0.00 |
| Hacker News API | 8 searches | $0.00 |
| Meta Ad Library API | 8 brand queries | $0.00 |
| OpenRouter LLM (analyst per competitor) | 8 calls | $0.00 |
| OpenRouter LLM (digest generator) | 1 call | $0.00 |
| **Total LLM calls per run** | **9 calls** | **$0.00** |
| **Total per run** | | **$0.00** |

> ✅ 9 LLM calls per run × 7 runs/week = 63 calls/week — well within the 200/day free limit.

### Monthly Operating Cost (Production — Post Validation)
| Item | Free Tier | Paid (Scale) |
|---|---|---|
| OpenRouter API | $0 | ~$10–15/month |
| Hosting (Render free → paid) | $0 | $7/month |
| Google / Meta APIs | $0 | $0 |
| Domain | ~$1/month | ~$1/month |
| **Total** | **~$1/month** | **~$18–23/month** |

### Suggested Pricing (Post-Validation)
| Tier | Competitors | Cadence | Price | Margin |
|---|---|---|---|---|
| Starter | Up to 3 | Weekly | ₹10,000/month | ~99% |
| Growth | Up to 8 | Weekly + on-demand | ₹25,000/month | ~99% |
| Agency | Up to 25, 5 brands | Daily | ₹75,000/month | ~99% |

---

## WTP Validation Strategy

### The 2-Week Sprint

**Week 1 — Run free intel reports for 5 brands**
Pick brands where you know the marketing lead — ex-clients, JAGSOM alumni companies, or direct LinkedIn connections. Run a full competitive audit for their category and share the digest cold:

> *"I ran a competitive intelligence report for [their category] — here's how [Competitor X] changed their messaging this week, what their ad volume signals, and 3 actions [their brand] should consider. Took 4 minutes to generate. Happy to walk you through it."*

**What you're testing:** Do they forward it internally? Do they ask "how often can I get this?"

**Week 2 — The pricing conversation**
With the 3 who responded warmly:

> *"I'm turning this into a weekly monitoring service. Early access pilot is ₹15,000/month — includes automated weekly digest, ad creative tracking, and competitor velocity scoring. Interested in a 4-week pilot?"*

**Signal that means YES to build:** 2 of 5 say yes, or 1 pays upfront.

---

## Open Questions

| # | Question | Owner | Due |
|---|---|---|---|
| 1 | Should the MVP include LinkedIn company page monitoring (public posts only) as an additional signal source? | Kumar | Phase 1 review |
| 2 | Is BeautifulSoup sufficient for JS-rendered competitor sites, or do we need Playwright for dynamic pages? | Kumar | Before coding FR-02 |
| 3 | Should CVS be shown to clients numerically or abstracted as category labels only (Dormant / Sprint)? | Validate with first 3 users | Week 1 |
| 4 | Is 8 competitors the right cap for Phase 1 or should we start with 5 to keep run time under 3 minutes? | Kumar | Before coding FR-01 |
| 5 | For the Analyst Agent, is one LLM call per competitor better, or batch all competitors in one large prompt? | Kumar | Before coding agent/analyst.py |
| 6 | For agency white-label in Phase 3, does the digest need custom branding (logo, colors) per client? | Kumar | Phase 3 planning |

---

*This PRD is a living document. Update version number and Last Updated date with each significant change.*
