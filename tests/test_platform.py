"""Platform tests."""

import pytest
from httpx import ASGITransport, AsyncClient

from cloud_run_services.ai_gateway.main import app as gateway_app
from cloud_run_services.agent_service.main import app as agent_app
from vertex_ai.embeddings.client import EmbeddingClient


@pytest.mark.asyncio
async def test_gateway_health():
    transport = ASGITransport(app=gateway_app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"


@pytest.mark.asyncio
async def test_agent_list():
    transport = ASGITransport(app=agent_app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/agents")
    assert response.status_code == 200
    assert len(response.json()) == 5


@pytest.mark.asyncio
async def test_embeddings_local():
    client = EmbeddingClient()
    vectors = await client.embed(["hello", "world"])
    assert len(vectors) == 2
    assert len(vectors[0]) == 768
