# Production Readiness Checklist

This document outlines all tasks required to deploy the MarketingAgents platform to production, organized by category, sequence, and dependencies.

---

## NEXT 5 TO-DOS (Priority Order)

> These are the immediate next steps based on current development progress.

| # | Task | Section | Status |
|---|------|---------|--------|
| 1 | **Test admin portal tracking** - Verify signup/run tracking works end-to-end | 13.1 | ✅ |
| 2 | **Implement real payment flow** - UPI screenshot verification (manual approval) | 6.1 | ✅ |
| 3 | **Set up PostgreSQL** - Move from JSON files to database | 5.1 | ✅ |
| 4 | **Implement JWT auth** - Replace localStorage with backend authentication | 4.1 | ✅ |
| 5 | **Deploy to staging** - Set up Vercel (frontend) and Railway (backend) | 9.3 | ⬜ |
| 6 | **Set up email integration** - Resend for payment confirmations | 3.2 | ⬜ |
| 7 | **Add error handling and loading states** - Error boundaries, toasts, skeleton loaders | 7.1 | ✅ |
| 8 | **SEO setup** - sitemap.xml, meta tags, robots.txt, structured data | 7.5 | ✅ |
| 9 | **Add global exception handler** - Backend error handling | 8.3 | ✅ |
| 10 | **Set up Google Analytics 4** - Track sign-ups, payments, page views | 7.4 | ✅ |
| 11 | **Set up CI/CD pipeline** - GitHub Actions for automated builds/deploys | 9.1 | ⬜ |
| 12 | **Set up Sentry error tracking** - Frontend and backend error monitoring | 13.1 | ⬜ |
| 13 | **Create Privacy Policy & Terms of Service** - Legal pages required for launch | 12.1 | ⬜ |
| 14 | **Add cookie consent banner** - GDPR compliance for analytics | 12.1 | ⬜ |
| 15 | **Add onboarding tooltips** - Help users understand features | 7.3 | ✅ |
| 16 | **Implement empty states** - Better UX when no data/workspace | 7.3 | ✅ |
| 17 | **Add success confirmations** - Toast notifications for completed actions | 7.3 | ✅ |
| 18 | **Add mobile responsiveness** - Optimize for tablet and phone | 7.3 | ⬜ |
| 19 | **Set up database backups** - Automated daily backups to cloud storage | 5.1 | ⬜ |
| 20 | **Add keyboard shortcuts** - Power user productivity features | 7.3 | ⬜ |

---

---

## Table of Contents

1. [Tech Stack](#1-tech-stack)
2. [Additional Installation](#2-additional-installation)
3. [Environment & Configuration](#3-environment--configuration)
4. [Security](#4-security)
5. [Database](#5-database)
6. [Payment Integration](#6-payment-integration)
7. [Frontend](#7-frontend)
8. [Backend](#8-backend)
9. [Infrastructure & DevOps](#9-infrastructure--devops)
10. [Testing](#10-testing)
11. [Performance](#11-performance)
12. [Compliance & Legal](#12-compliance--legal)
13. [Monitoring & Observability](#13-monitoring--observability)
14. [Launch Checklist](#14-launch-checklist)

---

## 1. Tech Stack

### Current Stack

| Layer | Technology | Version | Purpose |
|-------|------------|---------|---------|
| **Frontend** | Next.js (Pages Router) | 14.x | React framework |
| | React | 18.x | UI library |
| | TypeScript | 5.x | Type safety |
| | CSS | - | Styling |
| **Backend** | Python | 3.12 | API server |
| | FastAPI | 0.109.x | API framework |
| | Pydantic | 2.x | Data validation |
| | Uvicorn | 0.27.x | ASGI server |
| **AI/ML** | OpenRouter | - | LLM API gateway |
| | Claude/HuggingFace | - | AI models |
| **Utilities** | python-dotenv | - | Env loading |
| | httpx | - | HTTP client |

### Production Stack (Free Software)

| Layer | Technology | Cost | Purpose |
|-------|------------|------|---------|
| **Database** | PostgreSQL (Neon) | Free tier | User data, payments |
| | OR PostgreSQL (Supabase) | Free tier | Alt option |
| | OR PostgreSQL (Railway) | Free tier ($5 credit) | Alt option |
| **Payments** | Manual (UPI) | Free | No integration needed |
| **Hosting** | Vercel | Free tier | Frontend |
| | Railway | Free tier | Backend API |
| | OR Render | Free tier | Alt backend option |
| | OR Fly.io | Free tier | Alt backend option |
| **Monitoring** | Sentry | Free tier | Error tracking |
| | UptimeRobot | Free tier | Uptime monitoring |
| **Domain** | Namecheap/Cloudflare | ~$10/year | Domain registration |
| **Email** | Resend | Free tier | Transactional emails |
| | OR Mailgun | Free tier | Alt email option |
| **Analytics** | Google Analytics 4 | Free | User analytics |
| **CDN** | Cloudflare | Free tier | CDN & security |
| **Error Tracking** | Sentry | Free tier | Application errors |

### Optional Enhancements (Later)

| Layer | Technology | Cost | Purpose |
|-------|------------|------|---------|
| **Cache** | Redis (Upstash) | Free tier | Session cache |
| **Search** | Meilisearch | Free (self-hosted) | Full-text search |
| **CI/CD** | GitHub Actions | Free | Automation |
| **SSL** | Let's Encrypt | Free | SSL certificates |

### File Storage

| Service | Cost | Purpose |
|---------|------|---------|
| Cloudflare R2 | Free tier | Store UPI payment screenshots |
| OR AWS S3 | Free tier | Alt option |
| OR Supabase Storage | Free tier | Alt option |

### Architecture Overview

```
┌─────────────────────────────────────────────────────────────┐
│                        USERS                                │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                    CLOUDFLARE (CDN + SSL)                  │
│                   *.marketingagents.ai                       │
└─────────────────────────────────────────────────────────────┘
                              │
            ┌─────────────────┴─────────────────┐
            ▼                                   ▼
┌───────────────────────────┐       ┌───────────────────────────┐
│      VERCEL (Frontend)   │       │    RAILWAY (Backend)     │
│   Next.js App (Port 3000)│       │  FastAPI (Port 8000)    │
└───────────────────────────┘       └───────────────────────────┘
                                          │
                     ┌─────────────────────┼─────────────────────┼─────────────────────┐
                     ▼                     ▼                     ▼                     ▼
           ┌─────────────────┐   ┌─────────────────┐   ┌─────────────────┐   ┌─────────────────┐
           │  NEON (Postgres)│   │   OPENROUTER    │   │    RESEND       │   │   CLOUDFLARE R2 │
           │  Database       │   │   AI Models     │   │    Emails       │   │   File Storage  │
           └─────────────────┘   └─────────────────┘   └─────────────────┘   └─────────────────┘
```

---

## 2. Additional Installation

### 2.1 Local Development Setup

**Prerequisites:**
- Python 3.12+
- Node.js 20+
- npm or yarn
- Git

**Backend Dependencies:**

```bash
# Navigate to backend
cd backend

# Create virtual environment
python3 -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Install additional production dependencies
pip install:
  - psycopg2-binary       # PostgreSQL adapter
  - asyncpg               # Async PostgreSQL
  - python-jose[cryptography]  # JWT handling
  - passlib[bcrypt]      # Password hashing
  - slowapi              # Rate limiting
  - redis               # Redis client (for caching)
  - httpx               # Async HTTP client
  - email-validator     # Email validation
  - celery[redis]       # Background tasks
```

**Frontend Dependencies:**

```bash
# Navigate to frontend
cd frontend

# Install dependencies
npm install

# Install additional production dependencies
npm install:
  @sentry/nextjs      # Error tracking
  @analytics/google    # Google Analytics
  zod                 # Schema validation
  @tanstack/react-query  # Data fetching
```

**Database Setup (Local):**

```bash
# Install PostgreSQL (macOS)
brew install postgresql@15
brew services start postgresql@15

# Install PostgreSQL (Ubuntu/Debian)
sudo apt update
sudo apt install postgresql postgresql-contrib

# Create database
psql -U postgres
CREATE DATABASE marketingagents;
CREATE USER admin WITH ENCRYPTED PASSWORD 'your_password';
GRANT ALL PRIVILEGES ON DATABASE marketingagents TO admin;
\q
```

**Redis Setup (Optional):**

```bash
# macOS
brew install redis
brew services start redis

# Ubuntu/Debian
sudo apt install redis-server
sudo systemctl start redis
```

### 2.2 Environment Variables Setup

Create `.env` files for development:

**Backend `.env`:**
```env
# AI Services
OPENROUTER_API_KEY=sk-or-v1-xxx
OPENROUTER_BASE_URL=https://openrouter.ai/api/v1
OPENROUTER_MODEL=nvidia/nemotron-3-super-120b-a12b:free

# Security
ADMIN_PASSWORD=your-secure-admin-password
SECRET_KEY=generate-a-random-secret-key

# Database
DATABASE_URL=postgresql://admin:password@localhost:5432/marketingagents

# Redis (optional)
REDIS_URL=redis://localhost:6379

# Email (Resend)
RESEND_API_KEY=re_xxx

# Frontend URL
FRONTEND_URL=http://localhost:3000

# CORS
CORS_ORIGINS=http://localhost:3000
```

**Frontend `.env.local`:**
```env
NEXT_PUBLIC_API_URL=http://localhost:8000/api/v1
NEXT_PUBLIC_APP_URL=http://localhost:3000
```

### 2.3 Database Migrations

```bash
cd backend

# Using Alembic for migrations
pip install alembic

# Initialize Alembic
alembic init alembic

# Create migration
alembic revision --autogenerate -m "Initial migration"

# Apply migrations
alembic upgrade head
```

### 2.4 Git Hooks Setup

```bash
# Install pre-commit
pip install pre-commit
npm install --save-dev husky lint-staged

# Create .pre-commit-config.yaml
cat > .pre-commit-config.yaml << EOF
repos:
  - repo: https://github.com/pre-commit/pre-commit-hooks
    rev: v4.5.0
    hooks:
      - id: trailing-whitespace
      - id: end-of-file-fixer
      - id: check-yaml
      - id: check-added-large-files
  - repo: https://github.com/psf/black
    rev: 24.1.1
    hooks:
      - id: black
        language_version: python3.12
  - repo: https://github.com/pycqa/isort
    rev: 5.13.2
    hooks:
      - id: isort
EOF

# Install hooks
pre-commit install
```

### 2.5 Required Accounts (Free Tier)

| Service | Signup URL | Purpose |
|---------|------------|---------|
| Neon PostgreSQL | https://neon.tech | Database |
| Railway | https://railway.app | Backend hosting |
| Vercel | https://vercel.com | Frontend hosting |
| Resend | https://resend.com | Transactional emails |
| Sentry | https://sentry.io | Error tracking |
| UptimeRobot | https://uptimerobot.com | Uptime monitoring |
| Cloudflare | https://cloudflare.com | CDN, DNS & File Storage |
| OpenRouter | https://openrouter.ai | AI API |

### 2.6 Quick Start Commands

```bash
# 1. Clone and setup
git clone <repo>
cd MarketingAgents

# 2. Backend setup
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env  # Edit with your values

# 3. Frontend setup
cd ../frontend
npm install
cp .env.example .env.local  # Edit with your values

# 4. Run locally
# Terminal 1: Backend
cd backend && source .venv/bin/activate && uvicorn app.main:app --reload

# Terminal 2: Frontend
cd frontend && npm run dev

# 5. Access
# Frontend: http://localhost:3000
# Backend API: http://localhost:8000
# API Docs: http://localhost:8000/docs
```

---

## 3. Environment & Configuration

**Owner:** DevOps / Backend

| Task | Sequence | Dependencies | Status |
|------|----------|--------------|--------|
| Create production `.env` file with all API keys | 1 | None | ⬜ |
| Set up environment variable management (Vercel/Railway) | 2 | Task 1 | ⬜ |
| Move all hardcoded URLs to environment variables | 3 | Task 1 | ⬜ |
| Configure `API_BASE` for production (no localhost) | 4 | Task 1 | ⬜ |
| Set up `ADMIN_PASSWORD` for production admin portal | 5 | None | ⬜ |
| Configure CORS origins for production domain | 6 | Production domain known | ⬜ |
| Create `.env.example` with all required variables | 7 | None | ⬜ |

**Required Environment Variables:**

```env
# Backend (.env)
OPENROUTER_API_KEY=sk-or-v1-xxx
ADMIN_PASSWORD=<secure-password>
SECRET_KEY=<generate-random-key>
DATABASE_URL=postgresql://...
REDIS_URL=redis://...
RESEND_API_KEY=re_xxx
UPI_ID=marketing@upi
FRONTEND_URL=https://marketingagents.ai
CORS_ORIGINS=https://marketingagents.ai

# Frontend (.env.local)
NEXT_PUBLIC_API_URL=https://api.marketingagents.ai
NEXT_PUBLIC_APP_URL=https://marketingagents.ai
```

---

## 4. Security

**Owner:** Backend / DevOps

### 4.1 Authentication & Authorization

| Task | Sequence | Dependencies | Status |
|------|----------|--------------|--------|
| Replace localStorage auth with backend JWT | 1 | Database setup | ✅ |
| Implement secure session management | 2 | Task 1 | ⬜ |
| Add password hashing (bcrypt) | 3 | Task 1 | ✅ |
| Implement CSRF protection | 4 | Task 1 | ⬜ |
| Add rate limiting to auth endpoints | 5 | None | ⬜ |
| Implement token refresh mechanism | 6 | Task 1 | ✅ |

### 4.2 API Security

| Task | Sequence | Dependencies | Status |
|------|----------|--------------|--------|
| Add global rate limiting middleware | 1 | None | ⬜ |
| Implement request validation (Pydantic) | 2 | None | ⬜ |
| Add CORS restrictions (specific origins only) | 3 | Production domain | ⬜ |
| Sanitize all user inputs | 4 | None | ⬜ |
| Implement API key authentication for integrations | 5 | None | ⬜ |
| Add security headers (CSP, HSTS, etc.) | 6 | None | ⬜ |

### 4.3 Admin Portal Security

| Task | Sequence | Dependencies | Status |
|------|----------|--------------|--------|
| Add 2FA support for admin login | 1 | None | ⬜ |
| Implement admin IP whitelist (optional) | 2 | None | ⬜ |
| Add admin activity logging | 3 | Database | ⬜ |
| Set up admin session timeout | 4 | Task 1 | ⬜ |

---

## 5. Database

**Owner:** Backend / DevOps

### 5.1 PostgreSQL Setup

| Task | Sequence | Dependencies | Status |
|------|----------|--------------|--------|
| Set up PostgreSQL database (Neon/Supabase/Railway) | 1 | None | ✅ |
| Create database schema/migrations | 2 | Task 1 | ⬜ |
| Set up connection pooling | 3 | Task 1 | ⬜ |
| Configure database backups | 4 | Task 1 | ⬜ |

### 5.2 Data Models

| Task | Sequence | Dependencies | Status |
|------|----------|--------------|--------|
| Users table (email, password_hash, name, tier, timestamps) | 1 | Task 5.1 | ⬜ |
| Subscriptions table (user_id, plan, status, expires_at) | 2 | Task 1 | ⬜ |
| Payments table (user_id, amount, method, status, receipt) | 3 | Task 1 | ⬜ |
| Workspaces table (user_id, name, config, metadata) | 4 | Task 1 | ⬜ |
| Agent runs table (workspace_id, agent_id, inputs, outputs, timestamp) | 5 | Task 1 | ⬜ |
| Refunds table (payment_id, amount, status, reason) | 6 | Task 3 | ⬜ |
| OAuth tokens table (user_id, provider, encrypted_token) | 7 | Task 1 | ⬜ |

### 5.3 Redis (Optional)

| Task | Sequence | Dependencies | Status |
|------|----------|--------------|--------|
| Set up Redis for session management (Upstash) | 1 | None | ⬜ |
| Configure caching for agent configs | 2 | Task 1 | ⬜ |
| Set up rate limit counters | 3 | Task 1 | ⬜ |

---

## 6. Payment Integration

**Owner:** Backend / Frontend

> **Note:** Payments are processed manually (no Razorpay/Stripe integration). UPI screenshot verification happens via admin approval.

### 6.1 Manual Payment Flow

| Task | Sequence | Dependencies | Status |
|------|----------|--------------|--------|
| Set up file storage for screenshots (Cloudflare R2/S3) | 1 | None | ⬜ |
| Create payment request endpoint | 2 | Database | ⬜ |
| Implement screenshot upload to storage | 3 | Task 1, 2 | ⬜ |
| Add admin payment approval workflow | 4 | Admin portal | ✅ |
| Send payment confirmation email | 5 | Task 4, Email setup | ⬜ |
| Update user tier on approval | 6 | Task 4 | ⬜ |

> **Note:** Current implementation stores screenshots locally. File storage (Cloudflare R2) for production can be added later.

### 6.2 Refund Processing

| Task | Sequence | Dependencies | Status |
|------|----------|--------------|--------|
| Implement refund eligibility check | 1 | Database | ⬜ |
| Create refund request endpoint | 2 | Task 1 | ⬜ |
| Add manual refund approval workflow | 3 | Admin portal | ⬜ |
| Process refund via UPI/bank transfer | 4 | Task 3 | ⬜ |
| Mark refund as completed | 5 | Task 4 | ⬜ |

### 6.3 Frontend Payment Flow

| Task | Sequence | Dependencies | Status |
|------|----------|--------------|--------|
| Current: UPI screenshot upload working | 1 | Backend API ready | ⬜ |
| Add payment pending status indicator | 2 | Task 1 | ⬜ |
| Implement subscription management UI | 3 | Task 1 | ⬜ |
| Add payment receipt/download | 4 | Task 1 | ⬜ |
| Show refund eligibility on payment page | 5 | Task 2.1 | ⬜ |

---

## 7. Frontend

**Owner:** Frontend

### 7.1 Error Handling

| Task | Sequence | Dependencies | Status |
|------|----------|--------------|--------|
| Set up error boundaries | 1 | None | ⬜ |
| Add global error toast notifications | 2 | Task 1 | ⬜ |
| Implement API error handling | 3 | None | ⬜ |
| Add network offline detection | 4 | None | ⬜ |

### 7.2 Loading States

| Task | Sequence | Dependencies | Status |
|------|----------|--------------|--------|
| Add skeleton loaders for all pages | 1 | None | ⬜ |
| Implement loading spinners | 2 | Task 1 | ⬜ |
| Add optimistic UI updates where applicable | 3 | None | ⬜ |

### 7.3 User Experience

| Task | Sequence | Dependencies | Status |
|------|----------|--------------|--------|
| Add onboarding tooltips | 1 | None | ✅ |
| Implement empty states | 2 | None | ✅ |
| Add success confirmations | 3 | None | ✅ |
| Improve mobile responsiveness | 4 | None | ⬜ |
| Add keyboard shortcuts | 5 | None | ⬜ |

### 7.4 Analytics

| Task | Sequence | Dependencies | Status |
|------|----------|--------------|--------|
| Set up Google Analytics 4 | 1 | None | ✅ |
| Add conversion tracking for sign-ups | 2 | Task 1 | ✅ |
| Add conversion tracking for payments | 3 | Task 1 | ✅ |
| Implement funnel analytics | 4 | Task 2, 3 | ⬜ |
| Add page view tracking | 5 | Task 1 | ✅ |

### 7.5 SEO

| Task | Sequence | Dependencies | Status |
|------|----------|--------------|--------|
| Set up sitemap.xml | 1 | Production URL | ⬜ |
| Add meta tags (title, description, OG) | 2 | Task 1 | ⬜ |
| Implement robots.txt | 3 | Task 1 | ⬜ |
| Add structured data (JSON-LD) | 4 | None | ⬜ |

---

## 8. Backend

**Owner:** Backend

### 8.1 API Documentation

| Task | Sequence | Dependencies | Status |
|------|----------|--------------|--------|
| Document all API endpoints (Swagger/OpenAPI) | 1 | None | ⬜ |
| Add request/response examples | 2 | Task 1 | ⬜ |
| Document error codes | 3 | Task 1 | ⬜ |
| Create API versioning strategy | 4 | None | ⬜ |

### 8.2 Logging & Monitoring

| Task | Sequence | Dependencies | Status |
|------|----------|--------------|--------|
| Set up structured logging | 1 | None | ⬜ |
| Add request ID tracking | 2 | Task 1 | ⬜ |
| Log all payment events | 3 | None | ⬜ |
| Log admin actions | 4 | None | ⬜ |

### 8.3 Error Handling

| Task | Sequence | Dependencies | Status |
|------|----------|--------------|--------|
| Implement global exception handler | 1 | None | ⬜ |
| Add custom error classes | 2 | Task 1 | ⬜ |
| Set up error email alerts | 3 | None | ⬜ |

### 8.4 Health Checks

| Task | Sequence | Dependencies | Status |
|------|----------|--------------|--------|
| Add database connection check | 1 | Database | ⬜ |
| Add Redis connection check (if used) | 2 | Redis | ⬜ |
| Add external API health checks | 3 | None | ⬜ |
| Implement /health endpoint | 4 | Task 1-3 | ⬜ |

---

## 9. Infrastructure & DevOps

**Owner:** DevOps / Backend

### 9.1 CI/CD Pipeline

| Task | Sequence | Dependencies | Status |
|------|----------|--------------|--------|
| Set up GitHub Actions workflow | 1 | None | ⬜ |
| Add linting check | 2 | Task 1 | ⬜ |
| Add TypeScript type check | 3 | Task 1 | ⬜ |
| Add unit tests to pipeline | 4 | Tests written | ⬜ |
| Set up staging environment | 5 | Task 1 | ⬜ |
| Configure auto-deploy to staging | 6 | Task 5 | ⬜ |
| Configure manual deploy to production | 7 | Task 6 | ⬜ |

### 9.2 Docker

| Task | Sequence | Dependencies | Status |
|------|----------|--------------|--------|
| Create Dockerfile for backend | 1 | None | ⬜ |
| Create Dockerfile for frontend | 2 | None | ⬜ |
| Create docker-compose.yml for local dev | 3 | Task 1, 2 | ⬜ |
| Add multi-stage builds for optimization | 4 | Task 1, 2 | ⬜ |

### 9.3 Hosting

| Task | Sequence | Dependencies | Status |
|------|----------|--------------|--------|
| Deploy frontend to Vercel | 1 | None | ⬜ |
| Deploy backend to Railway/Render/Fly.io | 2 | None | ⬜ |
| Set up custom domain (marketingagents.ai) | 3 | Domain registered | ⬜ |
| Configure SSL certificates | 4 | Task 3 | ⬜ |
| Set up API subdomain (api.marketingagents.ai) | 5 | Task 2, 3 | ⬜ |

### 9.4 Database Hosting

| Task | Sequence | Dependencies | Status |
|------|----------|--------------|--------|
| Set up Neon/Supabase PostgreSQL | 1 | None | ⬜ |
| Configure connection limits | 2 | Task 1 | ⬜ |
| Set up read replicas (if needed) | 3 | None | ⬜ |
| Configure automatic backups | 4 | Task 1 | ⬜ |

---

## 10. Testing

**Owner:** QA / All

### 10.1 Unit Tests

| Task | Sequence | Dependencies | Status |
|------|----------|--------------|--------|
| Set up Jest/Vitest | 1 | None | ⬜ |
| Write tests for auth functions | 2 | None | ⬜ |
| Write tests for usage tracking | 3 | None | ⬜ |
| Write tests for payment logic | 4 | None | ⬜ |
| Write tests for refund eligibility | 5 | None | ⬜ |
| Write tests for API endpoints | 6 | None | ⬜ |

### 10.2 Integration Tests

| Task | Sequence | Dependencies | Status |
|------|----------|--------------|--------|
| Set up Playwright | 1 | None | ⬜ |
| Write sign-up flow test | 2 | Task 1 | ⬜ |
| Write payment flow test | 3 | Task 1 | ⬜ |
| Write agent run test | 4 | Task 1 | ⬜ |
| Write workspace save test | 5 | Task 1 | ⬜ |

### 10.3 E2E Tests

| Task | Sequence | Dependencies | Status |
|------|----------|--------------|--------|
| Write happy path test | 1 | None | ⬜ |
| Write error handling test | 2 | None | ⬜ |
| Add to CI/CD pipeline | 3 | CI/CD setup | ⬜ |

---

## 11. Performance

**Owner:** Frontend / Backend

### 11.1 Frontend Performance

| Task | Sequence | Dependencies | Status |
|------|----------|--------------|--------|
| Run Lighthouse audit | 1 | None | ⬜ |
| Optimize bundle size | 2 | Task 1 | ⬜ |
| Add code splitting | 3 | Task 1 | ⬜ |
| Implement lazy loading for pages | 4 | Task 3 | ⬜ |
| Optimize images | 5 | None | ⬜ |
| Add service worker for caching | 6 | None | ⬜ |
| Set up CDN for static assets | 7 | Hosting setup | ⬜ |

### 11.2 Backend Performance

| Task | Sequence | Dependencies | Status |
|------|----------|--------------|--------|
| Add database indexes | 1 | Database | ⬜ |
| Implement query optimization | 2 | Task 1 | ⬜ |
| Add response caching | 3 | Redis | ⬜ |
| Optimize agent config lookups | 4 | None | ⬜ |

---

## 12. Compliance & Legal

**Owner:** Product / Legal

### 12.1 Privacy & Data

| Task | Sequence | Dependencies | Status |
|------|----------|--------------|--------|
| Create Privacy Policy page | 1 | None | ⬜ |
| Create Terms of Service page | 2 | None | ⬜ |
| Add cookie consent banner | 3 | None | ⬜ |
| Implement data export feature (GDPR) | 4 | Database | ⬜ |
| Implement data deletion feature (GDPR) | 5 | Task 4 | ⬜ |
| Add cookie policy | 6 | Task 3 | ⬜ |

### 12.2 Business

| Task | Sequence | Dependencies | Status |
|------|----------|--------------|--------|
| Create refund policy page | 1 | None | ⬜ |
| Add pricing page | 2 | Payment ready | ⬜ |
| Set up billing address/company info | 3 | None | ⬜ |
| Add contact page | 4 | None | ⬜ |

---

## 13. Monitoring & Observability

**Owner:** DevOps / Backend

### 13.1 Error Tracking

| Task | Sequence | Dependencies | Status |
|------|----------|--------------|--------|
| Set up Sentry for backend | 1 | None | ⬜ |
| Set up Sentry for frontend | 2 | None | ⬜ |
| Add source maps | 3 | Task 1, 2 | ⬜ |
| Set up error alerts | 4 | Task 1, 2 | ⬜ |

### 13.2 Performance Monitoring

| Task | Sequence | Dependencies | Status |
|------|----------|--------------|--------|
| Set up Vercel Analytics | 1 | None | ⬜ |
| Add Core Web Vitals tracking | 2 | Task 1 | ⬜ |
| Set up API response time monitoring | 3 | None | ⬜ |

### 13.3 Uptime Monitoring

| Task | Sequence | Dependencies | Status |
|------|----------|--------------|--------|
| Set up uptime monitoring (UptimeRobot) | 1 | Production URL | ⬜ |
| Configure alert notifications | 2 | Task 1 | ⬜ |
| Set up status page | 3 | None | ⬜ |

---

## 14. Launch Checklist

**Owner:** Product / All

### 14.1 Pre-Launch

| Task | Sequence | Dependencies | Status |
|------|----------|--------------|--------|
| All items in sections 1-13 completed | - | All above | ⬜ |
| Remove all test/debug logs | - | None | ⬜ |
| Remove sample/demo data | - | None | ⬜ |
| Test on multiple browsers | - | None | ⬜ |
| Test on mobile devices | - | None | ⬜ |
| Performance audit passed | - | Performance section | ⬜ |
| Security audit passed | - | Security section | ⬜ |
| Backup strategy verified | - | Database section | ⬜ |

### 14.2 Launch Day

| Task | Sequence | Dependencies | Status |
|------|----------|--------------|--------|
| DNS propagation confirmed | 1 | Domain configured | ⬜ |
| SSL certificates active | 2 | Hosting setup | ⬜ |
| Email notifications working | 3 | None | ⬜ |
| Payment processing verified | 4 | Payment section | ⬜ |
| Admin portal accessible | 5 | Admin section | ⬜ |
| Monitoring dashboards active | 6 | Monitoring section | ⬜ |
| Team briefed on launch tasks | 7 | None | ⬜ |

### 14.3 Post-Launch

| Task | Sequence | Dependencies | Status |
|------|----------|--------------|--------|
| Monitor error rates | 1 | Launch complete | ⬜ |
| Monitor payment success rate | 2 | Launch complete | ⬜ |
| Collect user feedback | 3 | Launch complete | ⬜ |
| Address critical bugs | 4 | Task 1 | ⬜ |
| Schedule post-mortem | 5 | Task 1 | ⬜ |

---

## Recommended Launch Order

Based on dependencies, here's the recommended sequence:

```
Week 1: Environment & Security Basics
├── Environment variables setup
├── Security headers
├── Rate limiting
└── Input validation

Week 2: Database & Auth
├── PostgreSQL setup (Neon)
├── User auth system
├── JWT implementation
└── Admin auth

Week 3: Payments & Compliance
├── Manual UPI payment flow
├── Screenshot verification admin workflow
├── Refund processing
├── Privacy/Terms pages
└── Cookie consent

Week 4: Infrastructure & Testing
├── CI/CD pipeline
├── Docker setup
├── Unit/Integration tests
└── Staging deployment

Week 5: Frontend Polish & SEO
├── Error handling
├── Loading states
├── Analytics
├── SEO optimization
└── Mobile polish

Week 6: Monitoring & Launch
├── Error tracking (Sentry)
├── Performance monitoring
├── Uptime monitoring
├── Final testing
└── Production launch
```

---

## Quick Wins (Do First)

These tasks provide high value with minimal effort:

1. **Add rate limiting** - Prevents abuse immediately
2. **Set up Sentry** - Catch errors before users report them
3. **Add error boundaries** - Better UX on errors
4. **Environment variables** - Avoid hardcoded secrets
5. **Basic logging** - Debug issues quickly
6. **Health check endpoint** - Monitor service status
7. **Privacy/Terms pages** - Legal requirement

---

## Free Tier Service Limits

| Service | Free Tier Limits | Notes |
|---------|-----------------|-------|
| Neon PostgreSQL | 0.5GB storage, 1 project | Sufficient for startup |
| Railway | $5 credit/month, 500 hours | Use wisely |
| Vercel | 100GB bandwidth, 100 deployments | Very generous |
| Supabase | 500MB database, 1GB file storage | Alt option |
| Resend | 100 emails/day | Transactional only |
| Sentry | 5K events/month | Sufficient for startup |
| Upstash Redis | 10K commands/day | Caching only |
| Cloudflare | Unlimited requests | CDN + DNS |

---

*Last updated: April 2026*
