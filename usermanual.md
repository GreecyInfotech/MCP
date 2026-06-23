# Enterprise AI Platform — User Manual

Version 1.0.0

---

## Table of Contents

1. [Introduction](#1-introduction)
2. [Getting Started](#2-getting-started)
3. [Dashboard Guide](#3-dashboard-guide)
4. [Working with Agents](#4-working-with-agents)
5. [Integrations](#5-integrations)
6. [Knowledge Base (RAG)](#6-knowledge-base-rag)
7. [Reporting & Metrics](#7-reporting--metrics)
8. [API Reference](#8-api-reference)
9. [Configuration Reference](#9-configuration-reference)
10. [Production Deployment](#10-production-deployment)
11. [Troubleshooting](#11-troubleshooting)
12. [Frequently Asked Questions](#12-frequently-asked-questions)

---

## 1. Introduction

The **Enterprise AI Platform** is a GCP-native system that brings together AI agents, document search, and enterprise tool integrations (Jira, Confluence, GitHub) behind a single dashboard.

### What You Can Do

| Capability | Description |
|------------|-------------|
| **Run AI agents** | Ask natural-language questions and get answers backed by live data |
| **Manage backlog** | Search Jira issues, check sprint velocity, create stories |
| **Triage support** | Search knowledge base and Confluence, draft responses, create tickets |
| **Respond to incidents** | Review incident metrics and create incident tickets |
| **Generate reports** | Pull executive summaries, velocity, and incident trends |
| **Assist development** | Search code on GitHub, review pull requests, find internal docs |

### Architecture Overview

```
┌─────────────────┐
│  Frontend UI    │  React dashboard (port 3000)
│  (Dashboard)    │
└────────┬────────┘
         │
┌────────▼────────┐
│   AI Gateway    │  Unified API entry (port 8080)
└────────┬────────┘
         │
    ┌────┴────┬──────────┬──────────┬──────────┬──────────┐
    ▼         ▼          ▼          ▼          ▼          ▼
 Agent     RAG       Jira    Confluence  GitHub   Reporting
 Service   Service   Service  Service    Service  Service
 (8082)    (8081)    (8083)   (8084)     (8085)   (8086)
```

All agent requests flow through the **AI Gateway**, which routes calls to the appropriate microservice.

---

## 2. Getting Started

### Prerequisites

| Requirement | Version / Notes |
|-------------|-----------------|
| Python | 3.10+ |
| Node.js | 18+ (for frontend) |
| npm | Latest LTS recommended |
| PostgreSQL | Optional locally; included in Docker Compose |
| Docker | Optional; for full-stack container deployment |

### Quick Start (Local Development)

Open PowerShell in the project root:

```powershell
cd d:\personal\MCP\enterprise-ai-platform

# 1. Create and activate virtual environment
python -m venv .venv
.\.venv\Scripts\activate

# 2. Install the platform package
pip install -e .

# 3. Create environment file
copy .env.example .env

# 4. Start all backend services
.\scripts\run-local.ps1
```

In a **second terminal**, start the frontend:

```powershell
cd d:\personal\MCP\enterprise-ai-platform\frontend-ui
npm install
npm run dev
```

### Access URLs

| Component | URL |
|-----------|-----|
| **Dashboard** | http://localhost:3000 |
| AI Gateway | http://localhost:8080 |
| RAG Service | http://localhost:8081 |
| Agent Service | http://localhost:8082 |
| Jira Service | http://localhost:8083 |
| Confluence Service | http://localhost:8084 |
| GitHub Service | http://localhost:8085 |
| Reporting Service | http://localhost:8086 |

> **Note:** If port 3000 is already in use, Vite will automatically use the next available port (e.g. 3001). Check the terminal output for the actual URL.

### Docker Compose (Full Stack)

Runs PostgreSQL, all seven backend services, and the frontend in containers:

```powershell
cd deployment
copy ..\.env.example ..\.env
docker compose up --build
```

Access the dashboard at http://localhost:3000.

### Verify Installation

1. Open http://localhost:3000 in your browser.
2. Confirm the header badge shows **Gateway Online** (green).
3. The sidebar should list five agents, seven Cloud Run services, and two Vertex AI models.

You can also check health directly:

```powershell
Invoke-RestMethod http://localhost:8080/health
```

Expected response:

```json
{
  "status": "healthy",
  "service": "AI Gateway",
  "version": "1.0.0"
}
```

---

## 3. Dashboard Guide

The dashboard is a single-page application with three main areas.

### Header

| Element | Meaning |
|---------|---------|
| **Enterprise AI Platform** | Application title |
| *Vertex AI · Cloud Run · BigQuery* | Platform subtitle |
| **Gateway Online** | AI Gateway is reachable and healthy |
| **Gateway Offline** | Backend is not running or unreachable |
| **Checking...** | Initial health check in progress |

### Sidebar — Agents

Lists all available AI agents. Click an agent to select it. The selected agent is highlighted.

Each agent entry shows:
- **Name** (e.g. `backlog-agent`)
- **Short description** (first 50 characters)

### Sidebar — Cloud Run Services

Shows the registered backend services and their local ports. This is informational — you do not need to interact with these directly when using the dashboard.

### Sidebar — Vertex AI Models

Lists registered AI models and their status:

| Model | Purpose |
|-------|---------|
| `gemini-chat` | Agent reasoning and chat (Gemini 2.0 Flash) |
| `text-embeddings` | Document embeddings for knowledge search |

### Main Panel — Agent Workspace

When an agent is selected, the main panel displays:

1. **Agent header** — full name and description
2. **Suggestion chips** — click to pre-fill common questions
3. **Query textarea** — type your question
4. **Run Agent** button — submit the query
5. **Response** — the agent's answer
6. **Actions taken** — expandable list of tools the agent called (e.g. Jira search, RAG lookup)

---

## 4. Working with Agents

### Available Agents

#### backlog-agent

**Purpose:** Sprint planning, backlog prioritization, and Jira management.

**Tools used:** Jira issue search, sprint velocity metrics

**Example questions:**
- "Show me all open stories in the current sprint"
- "What's our average sprint velocity?"
- "Create a story for user authentication improvements"

---

#### support-agent

**Purpose:** Support ticket triage with knowledge base and Confluence lookup.

**Tools used:** RAG knowledge search, Confluence page search, Jira ticket creation

**Example questions:**
- "A customer can't reset their password. Help me triage."
- "Search the knowledge base for SSO configuration issues"
- "Draft a response for a dashboard loading issue"

---

#### incident-agent

**Purpose:** Incident detection, triage, and response.

**Tools used:** Incident metrics, Jira incident creation

**Example questions:**
- "Query errors in the last hour with severity >= 3"
- "Create a P1 incident for API latency spike"
- "What's the blast radius of a database connection pool exhaustion?"

---

#### reporting-agent

**Purpose:** Metrics, dashboards, and executive reports.

**Tools used:** Dashboard snapshot, report generation

**Example questions:**
- "Generate an executive summary report"
- "Show incident trends for the last 30 days"
- "What's our support SLA compliance this week?"

---

#### code-agent

**Purpose:** Pull request review, code search, and development assistance.

**Tools used:** GitHub code search, pull request listing, internal doc search

**Example questions:**
- "Review open PRs in our main repository"
- "Search for authentication middleware implementations"
- "Find documentation about our API design patterns"

---

### How to Run an Agent

**Step 1:** Select an agent in the sidebar.

**Step 2:** Enter a question using one of these methods:
- Click a **suggestion chip** to auto-fill a prompt
- Type your own question in the textarea

**Step 3:** Click **Run Agent**.

**Step 4:** Review the results:
- Read the **Response** section for the agent's answer
- Expand **Actions taken** to see which backend tools were invoked

### Understanding Agent Responses

A successful response includes:

```json
{
  "agent": "support",
  "answer": "Based on the knowledge base...",
  "actions_taken": [
    "search_knowledge({\"query\": \"SSO configuration\"})"
  ],
  "metadata": {
    "tool_results": [...]
  }
}
```

| Field | Description |
|-------|-------------|
| `answer` | Natural-language response from the agent |
| `actions_taken` | List of tool calls made during processing |
| `metadata.tool_results` | Raw data returned by each tool |

### Local vs Production Behavior

| Mode | Setting | Behavior |
|------|---------|----------|
| **Local dev** | `USE_VERTEX_AI=false` | Uses stub AI responses; automatically invokes the first available tool for the agent |
| **Production** | `USE_VERTEX_AI=true` | Uses real Gemini function-calling with up to 3 tool iterations |

---

## 5. Integrations

Integrations are configured via environment variables — there is no settings screen in the dashboard. An administrator must set credentials in the `.env` file and restart the affected services.

### Jira

**Required variables:**

```env
JIRA_URL=https://your-org.atlassian.net
JIRA_EMAIL=you@company.com
JIRA_API_TOKEN=your-atlassian-api-token
```

**How to get an API token:**
1. Go to https://id.atlassian.com/manage-profile/security/api-tokens
2. Click **Create API token**
3. Copy the token into `.env`

**Used by:** backlog-agent, support-agent, incident-agent

**Direct API examples:**

```powershell
# Search issues
Invoke-RestMethod -Uri "http://localhost:8083/issues/search" `
  -Method POST -ContentType "application/json" `
  -Body '{"jql": "status != Done", "max_results": 10}'

# Get a specific issue
Invoke-RestMethod "http://localhost:8083/issues/PROJ-123"
```

> If credentials are missing, the Jira service returns HTTP 503.

---

### Confluence

**Required variables:**

```env
CONFLUENCE_URL=https://your-org.atlassian.net/wiki
CONFLUENCE_EMAIL=you@company.com
CONFLUENCE_API_TOKEN=your-atlassian-api-token
```

**Used by:** support-agent

**Direct API example:**

```powershell
Invoke-RestMethod -Uri "http://localhost:8084/pages/search" `
  -Method POST -ContentType "application/json" `
  -Body '{"query": "SSO configuration", "limit": 10}'
```

---

### GitHub

**Required variables:**

```env
GITHUB_TOKEN=ghp_your_personal_access_token
GITHUB_ORG=your-org
```

**How to get a token:**
1. Go to GitHub → Settings → Developer settings → Personal access tokens
2. Create a token with `repo` and `read:org` scopes
3. Add to `.env`

**Used by:** code-agent (searches `{GITHUB_ORG}/main-app` for pull requests)

**Direct API examples:**

```powershell
# List repositories
Invoke-RestMethod "http://localhost:8085/repos"

# Search code
Invoke-RestMethod -Uri "http://localhost:8085/code/search" `
  -Method POST -ContentType "application/json" `
  -Body '{"query": "authentication middleware"}'
```

---

### Integration Defaults (Operator Notes)

Some agent tool calls use hardcoded defaults that you may want to customize in a future release:

| Default | Used For |
|---------|----------|
| `PROJ` | Jira project key when creating tickets/incidents |
| `{GITHUB_ORG}/main-app` | Repository for pull request listing |

---

## 6. Knowledge Base (RAG)

The RAG (Retrieval-Augmented Generation) service stores and searches internal documents. Agents use it to answer questions from your organization's knowledge base.

### How It Works

```
Document → Embedding → Vector Index (ChromaDB locally / Vertex AI in production)
                              ↓
User query → Semantic search → Ranked results → Agent answer
```

### Ingesting Documents

There is **no upload UI** in the dashboard. Documents are ingested via the API.

#### Option 1: Ingest text directly

```powershell
Invoke-RestMethod -Uri "http://localhost:8081/ingest" `
  -Method POST -ContentType "application/json" `
  -Body '{
    "texts": ["Our SSO uses SAML 2.0 with Okta."],
    "metadatas": [{"source": "kb/sso.md", "category": "auth"}]
  }'
```

Via the AI Gateway:

```powershell
Invoke-RestMethod -Uri "http://localhost:8080/rag/ingest" `
  -Method POST -ContentType "application/json" `
  -Body '{"texts": ["Company VPN uses WireGuard."], "metadatas": [{"topic": "network"}]}'
```

#### Option 2: Ingest a local file

```powershell
Invoke-RestMethod -Uri "http://localhost:8081/ingest/file" `
  -Method POST -ContentType "application/json" `
  -Body '{"path": "C:/docs/runbook.txt"}'
```

#### Option 3: Ingest from Google Cloud Storage

```powershell
Invoke-RestMethod -Uri "http://localhost:8081/ingest" `
  -Method POST -ContentType "application/json" `
  -Body '{"gcs_uri": "gs://your-bucket/rag-documents/runbook.txt"}'
```

### Searching the Knowledge Base

```powershell
Invoke-RestMethod -Uri "http://localhost:8081/search" `
  -Method POST -ContentType "application/json" `
  -Body '{"query": "How do we configure SSO?", "top_k": 5}'
```

Response:

```json
{
  "results": [
    {
      "id": "abc-123",
      "content": "Our SSO uses SAML 2.0 with Okta.",
      "score": 0.87,
      "metadata": {"source": "kb/sso.md"}
    }
  ]
}
```

### List Stored Documents

```powershell
Invoke-RestMethod "http://localhost:8081/documents"
```

### Local Storage

In development mode (`USE_VERTEX_AI=false`):
- Vectors are stored in `./data/chroma`
- Files fall back to `./data/gcs-fallback/` when GCS is not configured

---

## 7. Reporting & Metrics

The reporting service provides operational metrics from PostgreSQL (Cloud SQL in production) and analytics from BigQuery.

### Available Metrics

| Endpoint | Description |
|----------|-------------|
| `GET /metrics/velocity` | Sprint velocity by sprint name and average |
| `GET /metrics/incidents` | Incident counts by severity and status |
| `GET /metrics/support` | Support ticket volume and resolution time |
| `GET /dashboard` | Combined snapshot of all metrics |

### Example: Dashboard Snapshot

```powershell
Invoke-RestMethod "http://localhost:8086/dashboard"
```

Via AI Gateway:

```powershell
Invoke-RestMethod "http://localhost:8080/reporting/dashboard"
```

### Generate a Report

```powershell
Invoke-RestMethod -Uri "http://localhost:8086/reports" `
  -Method POST -ContentType "application/json" `
  -Body '{
    "report_type": "executive",
    "parameters": {},
    "format": "json"
  }'
```

**Report types:**

| Type | Description |
|------|-------------|
| `sprint_velocity` | Velocity metrics for a project |
| `incident_summary` | Incident trends over a time period |
| `executive` | Full dashboard snapshot |

### Sample Data (Docker)

When using Docker Compose, sample data is loaded automatically:

- 2 sample incidents (API latency spike, DB pool exhausted)
- 2 sprint metric records (Sprint 23 and Sprint 24)

---

## 8. API Reference

All services expose `GET /health`. The AI Gateway proxies most user-facing endpoints.

### AI Gateway (port 8080)

| Method | Path | Description |
|--------|------|-------------|
| GET | `/` | Platform identity |
| GET | `/health` | Health check |
| GET | `/services` | Service registry |
| GET | `/models` | List registered models |
| POST | `/models/sync` | Sync models from Vertex AI Model Registry |
| POST | `/chat` | Direct Gemini chat (no agent) |
| GET | `/agents` | List agents |
| POST | `/agents/{agent_id}/run` | Run an agent |
| POST | `/rag/ingest` | Ingest documents |
| POST | `/rag/search` | Search knowledge base |
| GET | `/reporting/dashboard` | Reporting dashboard snapshot |

### Run an Agent via API

```http
POST http://localhost:8080/agents/support/run
Content-Type: application/json

{
  "query": "Search the knowledge base for password reset procedures",
  "context": {}
}
```

### Direct Chat with Gemini

```http
POST http://localhost:8080/chat
Content-Type: application/json

{
  "messages": [
    {"role": "system", "content": "You are a helpful assistant."},
    {"role": "user", "content": "Summarize our sprint status."}
  ],
  "temperature": 0.2
}
```

### Service Ports Quick Reference

| Service | Port |
|---------|------|
| AI Gateway | 8080 |
| RAG Service | 8081 |
| Agent Service | 8082 |
| Jira Service | 8083 |
| Confluence Service | 8084 |
| GitHub Service | 8085 |
| Reporting Service | 8086 |
| Frontend UI | 3000 |

---

## 9. Configuration Reference

Copy `.env.example` to `.env` and adjust values as needed.

### Platform

| Variable | Default | Description |
|----------|---------|-------------|
| `GCP_PROJECT_ID` | — | GCP project ID (required for production) |
| `GCP_REGION` | `us-central1` | GCP region |
| `USE_VERTEX_AI` | `false` | `true` = real Vertex AI; `false` = local stubs |
| `APP_ENV` | `development` | Environment label |

### Service URLs

| Variable | Default |
|----------|---------|
| `AI_GATEWAY_URL` | `http://localhost:8080` |
| `RAG_SERVICE_URL` | `http://localhost:8081` |
| `AGENT_SERVICE_URL` | `http://localhost:8082` |
| `JIRA_SERVICE_URL` | `http://localhost:8083` |
| `CONFLUENCE_SERVICE_URL` | `http://localhost:8084` |
| `GITHUB_SERVICE_URL` | `http://localhost:8085` |
| `REPORTING_SERVICE_URL` | `http://localhost:8086` |

### Vertex AI

| Variable | Default | Description |
|----------|---------|-------------|
| `VERTEX_LOCATION` | `us-central1` | Vertex AI region |
| `GEMINI_MODEL` | `gemini-2.0-flash` | Chat model |
| `EMBEDDING_MODEL` | `text-embedding-005` | Embedding model |
| `VECTOR_SEARCH_INDEX_ID` | — | Matching Engine index (production) |
| `VECTOR_SEARCH_ENDPOINT_ID` | — | Matching Engine endpoint (production) |

### Data Layer

| Variable | Description |
|----------|-------------|
| `DATABASE_URL` | PostgreSQL connection string (local) |
| `CLOUD_SQL_INSTANCE` | Cloud SQL instance (`project:region:instance`) |
| `CLOUD_SQL_DATABASE` | Database name (`enterprise_ai`) |
| `BIGQUERY_DATASET` | Analytics dataset (`enterprise_analytics`) |
| `GCS_BUCKET` | GCS bucket for RAG documents |
| `GCS_RAG_PREFIX` | Object prefix (`rag-documents`) |

### Local Development

| Variable | Default | Description |
|----------|---------|-------------|
| `CHROMA_PERSIST_DIR` | `./data/chroma` | ChromaDB storage path |
| `CHROMA_COLLECTION` | `enterprise_knowledge` | Vector collection name |
| `VITE_API_URL` | `http://localhost:8080` | Frontend API base URL |

---

## 10. Production Deployment

### GCP Infrastructure

```bash
cd deployment/terraform
terraform init
terraform apply -var="project_id=YOUR_PROJECT"
```

### Build and Deploy

```bash
gcloud builds submit --config=deployment/cloudbuild.yaml .
```

### Production Checklist

- [ ] Set `USE_VERTEX_AI=true`
- [ ] Set `GCP_PROJECT_ID` and `GCP_REGION`
- [ ] Configure Cloud SQL (`CLOUD_SQL_INSTANCE`, credentials)
- [ ] Configure GCS bucket for RAG documents
- [ ] Set up BigQuery dataset for analytics
- [ ] Add Jira, Confluence, and GitHub API tokens
- [ ] Provision Vertex AI Vector Search index (if using Matching Engine)
- [ ] Update service URLs to Cloud Run endpoints

### Local vs Production

| Aspect | Local Dev | Production |
|--------|-----------|------------|
| AI model | Stub responses | Vertex AI Gemini |
| Embeddings | Hash-based fallback | `text-embedding-005` |
| Vector search | ChromaDB | Vertex Matching Engine |
| Database | Local PostgreSQL | Cloud SQL |
| Document storage | Local filesystem | Google Cloud Storage |
| Analytics | Cloud SQL only | BigQuery + Cloud SQL |
| Authentication | None (open) | Configure as needed |

---

## 11. Troubleshooting

### Gateway Offline / Proxy Errors

**Symptom:** Dashboard shows **Gateway Offline** or Vite logs `ECONNREFUSED` for `/health`, `/agents`, `/services`.

**Cause:** Backend services are not running.

**Fix:**

```powershell
cd d:\personal\MCP\enterprise-ai-platform
.\scripts\run-local.ps1
```

Wait until all seven services report `Uvicorn running on http://0.0.0.0:808X`, then refresh the dashboard.

---

### `.env` File Missing

**Symptom:** Services start but integrations fail or behave unexpectedly.

**Cause:** `.env` was not created (a common mistake is copying to `.en` instead of `.env`).

**Fix:**

```powershell
copy .env.example .env
```

Restart services after editing `.env`.

---

### Jira / Confluence / GitHub Returns 503

**Symptom:** Agent actions fail with integration errors.

**Cause:** API credentials are not set in `.env`.

**Fix:** Add the required tokens (see [Section 5](#5-integrations)) and restart the integration services.

---

### Agent Returns Empty or Stub Response

**Symptom:** Agent answers are generic or only show tool metadata.

**Cause:** Running in local dev mode with `USE_VERTEX_AI=false`.

**Fix:** This is expected in local development. For real AI responses, set `USE_VERTEX_AI=true` and configure GCP credentials.

---

### Port Already in Use

**Symptom:** `Port 3000 is in use, trying another one...` or service fails to bind.

**Fix:**
- Frontend: Vite auto-selects the next port — check terminal output
- Backend: Stop processes on ports 8080–8086, then re-run `.\scripts\run-local.ps1`

```powershell
Get-NetTCPConnection -LocalPort 8080 -ErrorAction SilentlyContinue |
  Select-Object OwningProcess
```

---

### Reporting Metrics Are Empty

**Symptom:** reporting-agent returns no velocity or incident data.

**Cause:** PostgreSQL is not running or `DATABASE_URL` is incorrect.

**Fix:**
- Use Docker Compose (includes PostgreSQL with sample data), or
- Start a local PostgreSQL instance and set `DATABASE_URL` in `.env`

---

### Health Check All Services

```powershell
8080..8086 | ForEach-Object {
  try {
    $r = Invoke-RestMethod "http://localhost:$_/health" -TimeoutSec 3
    Write-Host "Port $_`: $($r.service) - $($r.status)"
  } catch {
    Write-Host "Port $_`: FAILED"
  }
}
```

---

## 12. Frequently Asked Questions

### Can I upload documents through the dashboard?

Not currently. Document ingestion is API-only. Use the RAG service endpoints described in [Section 6](#6-knowledge-base-rag), or ask the **support-agent** or **code-agent** to search already-ingested content.

### Do I need a GCP account for local development?

No. Local development works without GCP when `USE_VERTEX_AI=false`. You get stub AI responses and ChromaDB-based search.

### How do I add a new agent?

Agents are defined in `cloud_run_services/agent_service/main.py` in the `AGENT_DEFS` dictionary. Add a new entry with `name`, `description`, `system` prompt, and `tools` list, then restart the agent service.

### Is authentication enabled?

No. The platform runs without authentication in both local and default Terraform configurations. Add authentication at the gateway or load balancer level for production use.

### How do I stop all services?

Close the terminal windows running the services, or stop the Python/Node processes bound to ports 8080–8086 and 3000.

For Docker Compose:

```powershell
docker compose down
```

### Where is data stored locally?

| Data | Location |
|------|----------|
| Vector embeddings | `./data/chroma` |
| Document fallback | `./data/gcs-fallback/` |
| PostgreSQL (Docker) | Docker volume |

---

## Support & Further Reading

| Resource | Location |
|----------|----------|
| Project README | `README.md` |
| Environment template | `.env.example` |
| Database schema | `deployment/init-db.sql` |
| Terraform infrastructure | `deployment/terraform/` |
| Legacy MCP migration notes | `README.md` → Migration from enterprise-mcp |

---

*Enterprise AI Platform — MIT License*
