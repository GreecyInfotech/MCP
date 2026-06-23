"""Jira integration microservice."""

from __future__ import annotations

from typing import Any

from fastapi import HTTPException
from pydantic import BaseModel, Field

from cloud_run_services.shared.app_factory import create_service_app
from eai_platform.config import get_settings
from eai_platform.logging import get_logger

logger = get_logger(__name__)
app = create_service_app("Jira Service", "1.0.0")


def _get_jira() -> Any:
    from atlassian import Jira

    settings = get_settings()
    if not settings.jira_url or not settings.jira_api_token:
        raise HTTPException(status_code=503, detail="Jira not configured")
    return Jira(
        url=settings.jira_url,
        username=settings.jira_email,
        password=settings.jira_api_token,
        cloud=True,
    )


class SearchRequest(BaseModel):
    jql: str
    max_results: int = 25


class CreateIssueRequest(BaseModel):
    project_key: str
    summary: str
    description: str
    issue_type: str = "Task"
    priority: str = "Medium"


@app.post("/issues/search")
async def search_issues(request: SearchRequest) -> dict[str, Any]:
    try:
        client = _get_jira()
        result = client.jql(request.jql, limit=request.max_results)
        issues = [
            {
                "key": i["key"],
                "summary": i["fields"]["summary"],
                "status": i["fields"]["status"]["name"],
                "assignee": (i["fields"].get("assignee") or {}).get("displayName"),
            }
            for i in result.get("issues", [])
        ]
        return {"total": result.get("total", len(issues)), "issues": issues}
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@app.get("/issues/{issue_key}")
async def get_issue(issue_key: str) -> dict[str, Any]:
    client = _get_jira()
    return client.issue(issue_key)


@app.post("/issues")
async def create_issue(request: CreateIssueRequest) -> dict[str, Any]:
    client = _get_jira()
    fields = {
        "project": {"key": request.project_key},
        "summary": request.summary,
        "description": request.description,
        "issuetype": {"name": request.issue_type},
        "priority": {"name": request.priority},
    }
    result = client.create_issue(fields=fields)
    return {"created": True, "key": result.get("key")}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8083)
