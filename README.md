# MCP — Enterprise AI Platform

MCP AI Projects by [GreecyInfotech](https://github.com/GreecyInfotech/MCP).

GCP-native enterprise AI platform built on **Cloud Run**, **Vertex AI**, and Google data services.

## Architecture

```
enterprise-ai-platform/
├── frontend-ui/                 React dashboard
├── cloud-run-services/          Microservices (Python package: cloud_run_services/)
│   ├── ai-gateway/              Unified API entry point
│   ├── rag-service/             Document ingestion + vector search
│   ├── agent-service/           Gemini-powered agents
│   ├── jira-service/            Jira REST API
│   ├── confluence-service/      Confluence REST API
│   ├── github-service/          GitHub REST API
│   └── reporting-service/       Cloud SQL + BigQuery metrics
├── vertex-ai/
│   ├── gemini/                  Gemini chat client
│   ├── embeddings/              Text embedding client
│   ├── vector-search/           Vector Search + ChromaDB fallback
│   └── model-registry/          Model catalog + Vertex sync
└── data-layer/
    ├── BigQuery/                Analytics warehouse
    ├── Cloud SQL/               Operational PostgreSQL
    └── Cloud Storage/           RAG document storage
```

## Quick Start (Local)

```powershell
cd d:\personal\MCP\enterprise-ai-platform

# Install
python -m venv .venv
.\.venv\Scripts\activate
pip install -e .

copy .env.example .env

# Start all services
.\scripts\run-local.ps1

# Frontend (separate terminal)
cd frontend-ui
npm install
npm run dev
```

| Service | URL |
|---------|-----|
| AI Gateway | http://localhost:8080 |
| RAG Service | http://localhost:8081 |
| Agent Service | http://localhost:8082 |
| Frontend UI | http://localhost:3000 |

## Docker Compose

```powershell
cd deployment
copy ..\.env.example ..\.env
docker compose up --build
```

## GCP Deployment

```bash
# 1. Provision infrastructure
cd deployment/terraform
terraform init
terraform apply -var="project_id=YOUR_PROJECT"

# 2. Build and deploy via Cloud Build
gcloud builds submit --config=deployment/cloudbuild.yaml .
```

Set `USE_VERTEX_AI=true` and `GCP_PROJECT_ID` in Cloud Run environment for production.

## API Flow

```
frontend-ui → ai-gateway → agent-service → vertex-ai/gemini
                        ↘ jira / confluence / github / reporting / rag services
                                              ↘ data-layer (Cloud SQL, BigQuery, GCS)
```

## Vertex AI

| Component | Model | Purpose |
|-----------|-------|---------|
| Gemini | `gemini-2.0-flash` | Agent reasoning + tool selection |
| Embeddings | `text-embedding-005` | RAG document vectors |
| Vector Search | Matching Engine | Production vector retrieval |
| Model Registry | Vertex Model Registry | Model catalog sync |

Local dev uses ChromaDB + hash embeddings when `USE_VERTEX_AI=false`.

## MCP Servers

Nine MCP servers are available for Cursor / Claude Desktop integration (stdio transport):

| Server | Command | Tools |
|--------|---------|-------|
| GitHub | `mcp-github` | repos, PRs, issues, code search, file contents |
| Jira | `mcp-jira` | JQL search, create/update issues, sprints |
| Confluence | `mcp-confluence` | page search, create/update, spaces |
| PostgreSQL | `mcp-postgresql` | schema introspection, read-only SQL |
| MongoDB | `mcp-mongodb` | collections, find, aggregate |
| Kubernetes | `mcp-kubernetes` | pods, deployments, logs, events |
| AWS | `mcp-aws` | S3, EC2, Lambda, CloudWatch logs |
| Slack | `mcp-slack` | channels, post message, search, history |
| Browser | `mcp-browser` | navigate, click, fill, screenshot |

```powershell
pip install -e ".[mcp]"
.\scripts\install-mcp.ps1
playwright install chromium   # for browser MCP only
```

Cursor config template: `deployment/mcp-config.json`

## Migration from enterprise-mcp

The original MCP monolith lives in the sibling project [`../enterprise-mcp/`](../enterprise-mcp/README.md). This platform replaces:

| Legacy | New |
|--------|-----|
| `agents/orchestrator.py` | `cloud_run_services/agent-service` + `ai-gateway` |
| `rag/` | `cloud_run_services/rag-service` + `vertex-ai/` |
| `mcp_server/jira/` | `cloud_run_services/jira-service` |
| OpenAI direct calls | `vertex-ai/gemini` |
| ChromaDB only | `vertex-ai/vector-search` + ChromaDB fallback |
| PostgreSQL local | `data-layer/cloud_sql` + Cloud SQL connector |
| `frontend/` | `frontend-ui/` |

## License

MIT
