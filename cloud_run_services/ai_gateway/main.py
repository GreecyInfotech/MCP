"""AI Gateway — unified API entry point for the enterprise AI platform."""

from __future__ import annotations

from typing import Any

from fastapi import HTTPException
from pydantic import BaseModel, Field

from cloud_run_services.shared.app_factory import create_service_app
from eai_platform.config import get_settings
from eai_platform.http_client import ServiceClient
from eai_platform.logging import get_logger
from vertex_ai.gemini.client import GeminiClient
from vertex_ai.model_registry.registry import ModelRegistry

logger = get_logger(__name__)
app = create_service_app("AI Gateway", "1.0.0")
registry = ModelRegistry()


class ChatRequest(BaseModel):
    messages: list[dict[str, str]]
    tools: list[dict[str, Any]] = Field(default_factory=list)
    temperature: float = 0.2


class AgentRunRequest(BaseModel):
    query: str = Field(..., min_length=1)
    context: dict[str, Any] = Field(default_factory=dict)


@app.get("/")
async def root() -> dict[str, str]:
    return {"platform": "enterprise-ai-platform", "gateway": "ai-gateway"}


@app.get("/services")
async def list_services() -> dict[str, str]:
    return get_settings().service_registry


@app.get("/models")
async def list_models() -> list[dict[str, Any]]:
    return registry.list_models()


@app.post("/models/sync")
async def sync_models() -> dict[str, int]:
    count = await registry.sync_from_vertex()
    return {"synced": count}


@app.post("/chat")
async def chat(request: ChatRequest) -> dict[str, Any]:
    client = GeminiClient()
    return await client.generate(request.messages, request.tools or None, request.temperature)


@app.get("/agents")
async def list_agents() -> Any:
    settings = get_settings()
    client = ServiceClient(settings.agent_service_url)
    return await client.get("/agents")


@app.post("/agents/{agent_id}/run")
async def run_agent(agent_id: str, request: AgentRunRequest) -> Any:
    settings = get_settings()
    client = ServiceClient(settings.agent_service_url)
    try:
        return await client.post(f"/agents/{agent_id}/run", request.model_dump())
    except Exception as exc:
        logger.error("Agent service error", error=str(exc))
        raise HTTPException(status_code=502, detail=f"Agent service unavailable: {exc}") from exc


@app.post("/rag/ingest")
async def rag_ingest(body: dict[str, Any]) -> Any:
    settings = get_settings()
    client = ServiceClient(settings.rag_service_url)
    return await client.post("/ingest", body)


@app.post("/rag/search")
async def rag_search(body: dict[str, Any]) -> Any:
    settings = get_settings()
    client = ServiceClient(settings.rag_service_url)
    return await client.post("/search", body)


@app.get("/reporting/dashboard")
async def dashboard() -> Any:
    settings = get_settings()
    client = ServiceClient(settings.reporting_service_url)
    return await client.get("/dashboard")


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8080)
