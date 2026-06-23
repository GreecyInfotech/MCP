"""Cloud Storage client for RAG documents and artifacts."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from eai_platform.config import get_settings
from eai_platform.logging import get_logger

logger = get_logger(__name__)


class CloudStorageClient:
    def __init__(self) -> None:
        self._settings = get_settings()

    def _bucket(self) -> Any:
        from google.cloud import storage

        client = storage.Client(project=self._settings.gcp_project_id)
        return client.bucket(self._settings.gcs_bucket)

    async def upload_file(self, local_path: str, destination: str = "") -> str:
        path = Path(local_path)
        dest = destination or f"{self._settings.gcs_rag_prefix}/{path.name}"

        if not self._settings.gcs_bucket or not self._settings.gcp_project_id:
            logger.warning("GCS not configured — storing locally", path=local_path)
            local_dest = Path("./data/gcs-fallback") / dest
            local_dest.parent.mkdir(parents=True, exist_ok=True)
            local_dest.write_bytes(path.read_bytes())
            return str(local_dest)

        blob = self._bucket().blob(dest)
        blob.upload_from_filename(str(path))
        return f"gs://{self._settings.gcs_bucket}/{dest}"

    async def download_text(self, gcs_uri: str) -> str:
        if gcs_uri.startswith("gs://"):
            if not self._settings.gcs_bucket:
                raise ValueError("GCS not configured")
            parts = gcs_uri.replace("gs://", "").split("/", 1)
            blob = self._bucket().blob(parts[1] if len(parts) > 1 else parts[0])
            return blob.download_as_text()
        return Path(gcs_uri).read_text(encoding="utf-8", errors="replace")

    async def list_documents(self, prefix: str = "") -> list[dict[str, str]]:
        prefix = prefix or self._settings.gcs_rag_prefix
        if not self._settings.gcs_bucket or not self._settings.gcp_project_id:
            local_dir = Path("./data/gcs-fallback") / prefix
            if not local_dir.exists():
                return []
            return [{"name": f.name, "uri": str(f)} for f in local_dir.rglob("*") if f.is_file()]

        blobs = self._bucket().list_blobs(prefix=prefix)
        return [{"name": b.name, "uri": f"gs://{self._settings.gcs_bucket}/{b.name}"} for b in blobs]
