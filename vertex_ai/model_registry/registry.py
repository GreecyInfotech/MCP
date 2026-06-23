"""Model registry — tracks deployed Vertex AI models."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any

from eai_platform.config import get_settings
from eai_platform.logging import get_logger

logger = get_logger(__name__)


@dataclass
class ModelEntry:
    name: str
    version: str
    provider: str
    endpoint: str
    status: str
    metadata: dict[str, Any]


class ModelRegistry:
    """In-memory registry with Vertex AI Model Registry sync."""

    def __init__(self) -> None:
        self._settings = get_settings()
        self._models: dict[str, ModelEntry] = {}
        self._register_defaults()

    def _register_defaults(self) -> None:
        defaults = [
            ModelEntry(
                name="gemini-chat",
                version="2.0-flash",
                provider="vertex-ai",
                endpoint=self._settings.gemini_model,
                status="active",
                metadata={"type": "generative"},
            ),
            ModelEntry(
                name="text-embeddings",
                version="005",
                provider="vertex-ai",
                endpoint=self._settings.embedding_model,
                status="active",
                metadata={"type": "embedding", "dimensions": 768},
            ),
        ]
        for m in defaults:
            self._models[m.name] = m

    def list_models(self) -> list[dict[str, Any]]:
        return [
            {
                "name": m.name,
                "version": m.version,
                "provider": m.provider,
                "endpoint": m.endpoint,
                "status": m.status,
                "metadata": m.metadata,
            }
            for m in self._models.values()
        ]

    def get_model(self, name: str) -> ModelEntry | None:
        return self._models.get(name)

    async def sync_from_vertex(self) -> int:
        if not self._settings.use_vertex_ai or not self._settings.gcp_project_id:
            return 0
        try:
            from google.cloud import aiplatform

            aiplatform.init(
                project=self._settings.gcp_project_id,
                location=self._settings.vertex_location,
            )
            models = aiplatform.Model.list()
            for model in models:
                self._models[model.display_name] = ModelEntry(
                    name=model.display_name,
                    version=model.version_id or "latest",
                    provider="vertex-ai",
                    endpoint=model.resource_name,
                    status="deployed",
                    metadata={"synced_at": datetime.now(timezone.utc).isoformat()},
                )
            return len(models)
        except Exception as exc:
            logger.warning("Vertex model sync failed", error=str(exc))
            return 0
