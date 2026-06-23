"""Vertex AI text embeddings with local fallback."""

from __future__ import annotations

import hashlib

from eai_platform.config import get_settings
from eai_platform.logging import get_logger

logger = get_logger(__name__)

DIMENSION = 768


class EmbeddingClient:
    def __init__(self) -> None:
        self._settings = get_settings()

    async def embed(self, texts: list[str]) -> list[list[float]]:
        if not texts:
            return []
        if self._settings.use_vertex_ai and self._settings.gcp_project_id:
            return await self._embed_vertex(texts)
        return self._embed_local(texts)

    async def _embed_vertex(self, texts: list[str]) -> list[list[float]]:
        import vertexai
        from vertexai.language_models import TextEmbeddingModel

        vertexai.init(project=self._settings.gcp_project_id, location=self._settings.vertex_location)
        model = TextEmbeddingModel.from_pretrained(self._settings.embedding_model)
        embeddings = model.get_embeddings(texts)
        return [e.values for e in embeddings]

    def _embed_local(self, texts: list[str]) -> list[list[float]]:
        logger.warning("Using local embedding fallback — enable USE_VERTEX_AI for production")
        vectors: list[list[float]] = []
        for text in texts:
            digest = hashlib.sha256(text.encode()).digest()
            vec = [((digest[i % len(digest)] / 255.0) * 2 - 1) for i in range(DIMENSION)]
            vectors.append(vec)
        return vectors
