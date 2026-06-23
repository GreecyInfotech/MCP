"""RAG Service — document ingestion and semantic search."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from pydantic import BaseModel, Field

from cloud_run_services.shared.app_factory import create_service_app
from data_layer.cloud_storage.client import CloudStorageClient
from eai_platform.logging import get_logger
from vertex_ai.vector_search.client import VectorDocument, VectorSearchClient

logger = get_logger(__name__)
app = create_service_app("RAG Service", "1.0.0")
vector_client = VectorSearchClient()
storage_client = CloudStorageClient()


class IngestRequest(BaseModel):
    texts: list[str] = Field(default_factory=list)
    metadatas: list[dict[str, Any]] = Field(default_factory=list)
    gcs_uri: str = ""


class SearchRequest(BaseModel):
    query: str = Field(..., min_length=1)
    top_k: int = 5


@app.post("/ingest")
async def ingest(request: IngestRequest) -> dict[str, Any]:
    texts = list(request.texts)
    metadatas = list(request.metadatas) or [{} for _ in texts]

    if request.gcs_uri:
        content = await storage_client.download_text(request.gcs_uri)
        texts.append(content)
        metadatas.append({"source": request.gcs_uri})

    if not texts:
        return {"ingested": 0, "ids": []}

    docs = [
        VectorDocument(id=VectorSearchClient.new_id(), content=t, metadata=m)
        for t, m in zip(texts, metadatas)
    ]
    ids = await vector_client.upsert(docs)
    return {"ingested": len(ids), "ids": ids}


@app.post("/search")
async def search(request: SearchRequest) -> dict[str, Any]:
    matches = await vector_client.search(request.query, top_k=request.top_k)
    return {
        "results": [
            {"id": m.id, "content": m.content, "score": m.score, "metadata": m.metadata}
            for m in matches
        ]
    }


@app.post("/ingest/file")
async def ingest_file(body: dict[str, str]) -> dict[str, Any]:
    path = body.get("path", "")
    if not path or not Path(path).exists():
        return {"error": f"File not found: {path}"}
    gcs_uri = await storage_client.upload_file(path)
    content = Path(path).read_text(encoding="utf-8", errors="replace")
    doc = VectorDocument(
        id=VectorSearchClient.new_id(),
        content=content,
        metadata={"source": gcs_uri, "filename": Path(path).name},
    )
    ids = await vector_client.upsert([doc])
    return {"ingested": 1, "ids": ids, "gcs_uri": gcs_uri}


@app.get("/documents")
async def list_documents() -> dict[str, Any]:
    docs = await storage_client.list_documents()
    return {"documents": docs}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8081)
