# MarketingAgents Platform

Production refactor with separated frontend/backend architecture for a scalable multi-agent marketing product.

## Architecture
- `frontend/`: Next.js website/app (Home, Agents, Agent Details, Run, History)
- `backend/`: FastAPI APIs (workspace, integrations, agents, run orchestration, history)
- `docs/Marketing_Agents_Platform_PRD.md`: platform-level PRD
- Existing Streamlit prototype remains in root for reference/migration continuity.

## Production Flow Implemented
- Brand workspace setup with reusable context:
  - brand name, website, industry, positioning, key pages
  - workspace naming and multiple workspace management (`/workspaces`)
  - LLM-based short brand framework analysis using brand + category + geography
  - brand documents kept in browser local storage and synced as metadata
- Optional martech integrations:
  - GSC, GA4, Google Ads can be enabled/disabled per workspace
  - if not authenticated/enabled, they are excluded from agent input context
- Agent catalog:
  - searchable listing, details page, run page, and run history
- Agent orchestration:
  - sync and async execution paths
  - file-backed repository for workspaces, integrations, and runs (`backend/data/platform_state.json`)
- Content Agent (fully built):
  - LLM-backed campaign content pack generation (OpenRouter)
  - automatic fallback generation if LLM is unavailable
  - marketer-friendly output sections (summary, emails, push, ads, creative brief, next steps)
  - brand-name-based auto-fill for website, industry, positioning, and key pages

## Supported Agents (v1)
- GEO Agent
- Competitor Intelligence Agent
- Content Agent
- Creative Agent
- Experimentation Agent
- Landing Page Optimization Agent
- Pricing Intelligence Agent
- Social Listening Agent
- Campaign Planner Agent

## Run Backend
```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

Optional for full Content Agent generation:
```bash
export OPENROUTER_API_KEY=your_key_here
```

## Run Frontend
```bash
cd frontend
npm install
npm run dev
```

Set API base if needed:
```bash
export NEXT_PUBLIC_API_BASE=http://localhost:8000/api/v1
```

## Key API Endpoints
- `PUT /api/v1/workspaces`
- `GET /api/v1/workspaces`
- `GET /api/v1/workspaces/{workspace_id}`
- `POST /api/v1/workspaces/analyze`
- `POST /api/v1/workspaces/{workspace_id}/assets`
- `POST /api/v1/integrations/connect`
- `GET /api/v1/integrations/{workspace_id}`
- `GET /api/v1/agents`
- `GET /api/v1/agents/{agent_id}`
- `POST /api/v1/agents/run`
- `GET /api/v1/agents/history/{workspace_id}`

## Key Product Capabilities
- Brand workspace setup and reuse across all agents
- Browser-local encrypted workspace persistence (pre-auth mode)
- Agent search, details, runs, and history
- Sync + async agent run orchestration
- Google integration scaffolding (GA4, Google Ads, Search Console)
- Structured server logging (`data/server_logs/`)
- Marketer-friendly dashboards per agent run output

## Notes
- Auth/signup/login is intentionally deferred; architecture is RBAC-ready.
- Repository currently includes both legacy Streamlit prototype and new production scaffold.
- If OpenRouter is unreachable, agent executors gracefully return structured fallback output.
