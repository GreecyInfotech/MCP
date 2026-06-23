"""Vector search — Vertex AI Vector Search with ChromaDB local fallback."""

from __future__ import annotations

import uuid
from dataclasses import dataclass
from typing import Any

import chromadb
from chromadb.config import Settings as ChromaSettings

from eai_platform.config import get_settings
from eai_platform.logging import get_logger
from vertex_ai.embeddings.client import EmbeddingClient

logger = get_logger(__name__)


@dataclass
class VectorDocument:
    id: str
    content: str
    metadata: dict[str, Any]


@dataclass
class VectorMatch:
    id: str
    content: str
    score: float
    metadata: dict[str, Any]


class VectorSearchClient:
    def __init__(self) -> None:
        self._settings = get_settings()
        self._embeddings = EmbeddingClient()
        self._chroma = chromadb.PersistentClient(
            path=self._settings.chroma_persist_dir,
            settings=ChromaSettings(anonymized_telemetry=False),
        )
        self._collection = self._chroma.get_or_create_collection(
            name=self._settings.chroma_collection,
            metadata={"hnsw:space": "cosine"},
        )

    async def upsert(self, documents: list[VectorDocument]) -> list[str]:
        if not documents:
            return []
        embeddings = await self._embeddings.embed([d.content for d in documents])

        if self._settings.use_vertex_ai and self._settings.vector_search_index_id:
            await self._upsert_vertex(documents, embeddings)

        self._collection.upsert(
            ids=[d.id for d in documents],
            documents=[d.content for d in documents],
            metadatas=[d.metadata for d in documents],
            embeddings=embeddings,
        )
        return [d.id for d in documents]

    async def search(self, query: str, top_k: int = 5) -> list[VectorMatch]:
        query_embedding = (await self._embeddings.embed([query]))[0]

        if self._settings.use_vertex_ai and self._settings.vector_search_endpoint_id:
            vertex_results = await self._search_vertex(query_embedding, top_k)
            if vertex_results:
                return vertex_results

        results = self._collection.query(
            query_embeddings=[query_embedding],
            n_results=top_k,
            include=["documents", "metadatas", "distances"],
        )
        matches: list[VectorMatch] = []
        if results["ids"] and results["ids"][0]:
            for i, doc_id in enumerate(results["ids"][0]):
                distance = results["distances"][0][i] if results["distances"] else 0.0
                matches.append(
                    VectorMatch(
                        id=doc_id,
                        content=results["documents"][0][i] if results["documents"] else "",
                        score=1.0 - distance,
                        metadata=results["metadatas"][0][i] if results["metadatas"] else {},
                    )
                )
        return matches

    async def _upsert_vertex(
        self, documents: list[VectorDocument], embeddings: list[list[float]]
    ) -> None:
        logger.info("Vertex Vector Search upsert", count=len(documents))
        # Production: use MatchingEngineIndexEndpoint.upsert_datapoints()
        # Requires pre-provisioned index in GCP console / Terraform

    async def _search_vertex(
        self, query_embedding: list[float], top_k: int
    ) -> list[VectorMatch]:
        logger.info("Vertex Vector Search query", top_k=top_k)
        return []

    @staticmethod
    def new_id() -> str:
        return str(uuid.uuid4())
