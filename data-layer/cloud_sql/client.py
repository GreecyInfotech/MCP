"""Cloud SQL (PostgreSQL) client."""

from __future__ import annotations

from typing import Any

from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine

from eai_platform.config import get_settings
from eai_platform.logging import get_logger

logger = get_logger(__name__)

BLOCKED = frozenset({"INSERT", "UPDATE", "DELETE", "DROP", "ALTER", "TRUNCATE", "CREATE"})


class CloudSQLClient:
    def __init__(self) -> None:
        self._settings = get_settings()
        self._engine: Engine | None = None

    def _get_engine(self) -> Engine:
        if self._engine is None:
            if self._settings.cloud_sql_instance and self._settings.gcp_project_id:
                self._engine = self._create_cloud_sql_engine()
            else:
                self._engine = create_engine(
                    self._settings.database_url, pool_pre_ping=True
                )
        return self._engine

    def _create_cloud_sql_engine(self) -> Engine:
        from google.cloud.sql.connector import Connector

        connector = Connector()

        def getconn() -> Any:
            return connector.connect(
                self._settings.cloud_sql_instance,
                "pg8000",
                user=self._settings.cloud_sql_user,
                password=self._settings.cloud_sql_password,
                db=self._settings.cloud_sql_database,
            )

        return create_engine("postgresql+pg8000://", creator=getconn, pool_pre_ping=True)

    async def execute_read(self, sql: str, params: dict[str, Any] | None = None, limit: int = 100) -> dict[str, Any]:
        first = sql.strip().split()[0].upper() if sql.strip() else ""
        if first in BLOCKED:
            raise ValueError(f"Write operations blocked: {first}")

        with self._get_engine().connect() as conn:
            result = conn.execute(text(sql), params or {})
            rows = [dict(r._mapping) for r in result.fetchmany(limit)]
            columns = list(result.keys()) if result.returns_rows else []
        return {"columns": columns, "rows": rows, "count": len(rows)}

    async def sprint_velocity(self, project_key: str = "", sprints: int = 5) -> dict[str, Any]:
        sql = """
            SELECT sprint_name, SUM(story_points) AS completed_points
            FROM sprint_metrics
            WHERE (:project_key = '' OR project_key = :project_key) AND status = 'done'
            GROUP BY sprint_name ORDER BY sprint_name DESC LIMIT :sprints
        """
        result = await self.execute_read(sql, {"project_key": project_key, "sprints": sprints}, limit=sprints)
        rows = result["rows"]
        avg = sum(r.get("completed_points", 0) or 0 for r in rows) / max(len(rows), 1)
        return {"velocity_by_sprint": rows, "average_velocity": round(avg, 1)}

    async def incident_summary(self, days: int = 30) -> dict[str, Any]:
        sql = """
            SELECT severity, status, COUNT(*) AS count FROM incidents
            WHERE created_at >= NOW() - (:days || ' days')::interval
            GROUP BY severity, status ORDER BY severity, status
        """
        result = await self.execute_read(sql, {"days": days}, limit=100)
        return {"period_days": days, "summary": result["rows"]}
