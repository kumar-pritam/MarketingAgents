# PRD: Marketing Agents Platform
**Version:** 2.0  
**Status:** Production Refactor Spec  
**Last Updated:** March 2026

## 1) Product Scope
A production-grade marketing platform serving enterprise practitioners and freelance consultants with:
- marketing website content + product surface
- searchable agent catalog
- brand workspace setup (brand profile, key pages, docs)
- agent-specific run experiences
- per-agent run history

## 2) Core UX Information Architecture
Required pages:
1. Home page: marketing banner, value proposition, key agents
2. Agent Listing page: search/filter all agents
3. Agent Details page: inputs, outputs, use-cases
4. Agent Run page: brand context + agent-specific inputs + run output
5. History page: prior runs grouped by workspace and agent

## 3) Brand Workspace & Data Handling
- Users input brand details once and reuse across agents
- Inputs: brand name, website, positioning, key pages, brand docs (PDF/DOCX/CSV)
- Browser local encrypted persistence as pre-auth storage model
- Server accepts workspace snapshot and stores run artifacts/history

## 4) Integrations
- OAuth-based connectors (multi-connect):
  - GA4
  - Google Ads
  - Google Search Console
- Integration state visible at workspace level
- Connect/disconnect status and scopes logged

## 5) Agents in v1
1. GEO Agent
2. Competitor Intelligence Agent
3. Content Agent
4. Creative Agent
5. Experimentation Agent
6. Landing Page Optimization Agent

Each agent must have:
- dedicated spec
- dedicated executor module
- typed input schema
- output contract
- run logs + history entries

## 6) System Architecture
- Frontend: Next.js app (`frontend/`)
- Backend: FastAPI app (`backend/`)
- Agent runtime: sync and async job modes
- Agent registry and plugin-like executor routing
- In-memory repository now; interface designed to swap for persistent DB

## 7) Security Baseline
- OWASP-aligned validation and sanitization
- URL/file validation and upload size limits (25MB)
- encrypted local workspace persistence
- structured server logging and run audit logs
- RBAC-ready structure for future auth

## 8) Non-Functional
- Extendable agent orchestration without core rewrites
- Explicit API contracts for frontend/backend decoupling
- Observability: run status, execution logs, error capture
- Mobile-responsive frontend baseline

## 9) Rollout
Phase A (this refactor): architecture split + baseline pages + all agents available + run orchestration + history + integrations scaffolding.  
Phase B: auth/signup/login, persistent DB, real OAuth token lifecycle, production hardening tests.
