"""BigQuery analytics client."""

from __future__ import annotations

from typing import Any

from eai_platform.config import get_settings
from eai_platform.logging import get_logger

logger = get_logger(__name__)


class BigQueryClient:
    def __init__(self) -> None:
        self._settings = get_settings()

    def _client(self) -> Any:
        from google.cloud import bigquery

        return bigquery.Client(project=self._settings.gcp_project_id)

    async def query(self, sql: str, params: dict[str, Any] | None = None) -> list[dict[str, Any]]:
        if not self._settings.gcp_project_id:
            logger.warning("BigQuery not configured — returning empty result")
            return []

        from google.cloud import bigquery

        client = self._client()
        job_config = bigquery.QueryJobConfig()
        if params:
            job_config.query_parameters = [
                bigquery.ScalarQueryParameter(k, "STRING", str(v)) for k, v in params.items()
            ]
        result = client.query(sql, job_config=job_config).result()
        return [dict(row) for row in result]

    async def incident_analytics(self, days: int = 30) -> list[dict[str, Any]]:
        sql = f"""
            SELECT severity, status, COUNT(*) AS count
            FROM `{self._settings.gcp_project_id}.{self._settings.bigquery_dataset}.incidents`
            WHERE created_at >= TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL {days} DAY)
            GROUP BY severity, status
            ORDER BY severity, status
        """
        return await self.query(sql)

    async def insert_rows(self, table: str, rows: list[dict[str, Any]]) -> int:
        if not self._settings.gcp_project_id:
            return 0
        client = self._client()
        table_ref = f"{self._settings.gcp_project_id}.{self._settings.bigquery_dataset}.{table}"
        errors = client.insert_rows_json(table_ref, rows)
        if errors:
            logger.error("BigQuery insert errors", errors=errors)
        return len(rows) - len(errors)
