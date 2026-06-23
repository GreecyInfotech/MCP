"""Reporting microservice — Cloud SQL + BigQuery analytics."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from fastapi import Query
from pydantic import BaseModel, Field

from cloud_run_services.shared.app_factory import create_service_app
from data_layer.bigquery.client import BigQueryClient
from data_layer.cloud_sql.client import CloudSQLClient
from eai_platform.logging import get_logger

logger = get_logger(__name__)
app = create_service_app("Reporting Service", "1.0.0")
sql_client = CloudSQLClient()
bq_client = BigQueryClient()


class ReportRequest(BaseModel):
    report_type: str
    parameters: dict[str, Any] = Field(default_factory=dict)
    format: str = "json"


@app.get("/metrics/velocity")
async def sprint_velocity(project_key: str = "", sprints: int = 5) -> dict[str, Any]:
    return await sql_client.sprint_velocity(project_key, sprints)


@app.get("/metrics/incidents")
async def incident_summary(days: int = 30) -> dict[str, Any]:
    try:
        bq_result = await bq_client.incident_analytics(days)
        if bq_result:
            return {"period_days": days, "summary": bq_result, "source": "bigquery"}
    except Exception as exc:
        logger.warning("BigQuery fallback to Cloud SQL", error=str(exc))
    return await sql_client.incident_summary(days)


@app.get("/metrics/support")
async def support_metrics(days: int = 7) -> dict[str, Any]:
    sql = """
        SELECT COUNT(*) AS total_tickets,
               AVG(EXTRACT(EPOCH FROM (resolved_at - created_at))/3600) AS avg_resolution_hours
        FROM support_tickets
        WHERE created_at >= NOW() - (:days || ' days')::interval
    """
    result = await sql_client.execute_read(sql, {"days": days})
    return {"period_days": days, "metrics": result["rows"][0] if result["rows"] else {}}


@app.get("/dashboard")
async def dashboard_snapshot() -> dict[str, Any]:
    velocity = await sql_client.sprint_velocity("", 3)
    incidents = await sql_client.incident_summary(7)
    return {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "velocity": velocity,
        "incidents": incidents,
    }


@app.post("/reports")
async def generate_report(request: ReportRequest) -> dict[str, Any]:
    params = request.parameters
    data: dict[str, Any] = {"type": request.report_type}

    if request.report_type == "sprint_velocity":
        data["data"] = await sprint_velocity(params.get("project_key", ""), params.get("sprints", 5))
    elif request.report_type == "incident_summary":
        data["data"] = await incident_summary(params.get("days", 30))
    elif request.report_type == "executive":
        data["data"] = await dashboard_snapshot()
    else:
        data["error"] = f"Unknown report type: {request.report_type}"

    data["generated_at"] = datetime.now(timezone.utc).isoformat()
    data["format"] = request.format
    return data


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8086)
