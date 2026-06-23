"""Jira MCP server — issue search, creation, and sprint management."""

from __future__ import annotations

from typing import Any

from atlassian import Jira
from mcp.server.fastmcp import FastMCP

from eai_platform.config import get_settings
from eai_platform.mcp_base import error_result, text_result

mcp = FastMCP(
    "jira",
    instructions=(
        "Jira integration for enterprise workflows. Search issues, create tickets, "
        "update status, and manage sprints."
    ),
)


def _get_client() -> Jira:
    settings = get_settings()
    if not settings.jira_url or not settings.jira_api_token:
        raise ValueError("JIRA_URL and JIRA_API_TOKEN must be configured")
    return Jira(
        url=settings.jira_url,
        username=settings.jira_email,
        password=settings.jira_api_token,
        cloud=True,
    )


@mcp.tool()
def search_issues(jql: str, max_results: int = 25) -> str:
    """Search Jira issues using JQL."""
    try:
        client = _get_client()
        result = client.jql(jql, limit=max_results)
        issues = result.get("issues", [])
        simplified = [
            {
                "key": i["key"],
                "summary": i["fields"]["summary"],
                "status": i["fields"]["status"]["name"],
                "assignee": (i["fields"].get("assignee") or {}).get("displayName"),
                "priority": (i["fields"].get("priority") or {}).get("name"),
            }
            for i in issues
        ]
        return text_result({"total": result.get("total", len(simplified)), "issues": simplified})
    except Exception as exc:
        return error_result(str(exc))


@mcp.tool()
def get_issue(issue_key: str) -> str:
    """Get full details for a Jira issue by key (e.g. PROJ-123)."""
    try:
        client = _get_client()
        issue = client.issue(issue_key)
        return text_result(issue)
    except Exception as exc:
        return error_result(str(exc))


@mcp.tool()
def create_issue(
    project_key: str,
    summary: str,
    description: str,
    issue_type: str = "Task",
    priority: str = "Medium",
) -> str:
    """Create a new Jira issue."""
    try:
        client = _get_client()
        fields: dict[str, Any] = {
            "project": {"key": project_key},
            "summary": summary,
            "description": description,
            "issuetype": {"name": issue_type},
            "priority": {"name": priority},
        }
        result = client.create_issue(fields=fields)
        return text_result({"created": True, "key": result.get("key"), "id": result.get("id")})
    except Exception as exc:
        return error_result(str(exc))


@mcp.tool()
def update_issue_status(issue_key: str, transition_name: str) -> str:
    """Transition a Jira issue to a new status (e.g. 'In Progress', 'Done')."""
    try:
        client = _get_client()
        transitions = client.get_issue_transitions(issue_key)
        match = next((t for t in transitions if t["name"].lower() == transition_name.lower()), None)
        if not match:
            available = [t["name"] for t in transitions]
            return error_result(f"Transition '{transition_name}' not found. Available: {available}")
        client.set_issue_status(issue_key, match["id"])
        return text_result({"updated": True, "key": issue_key, "status": transition_name})
    except Exception as exc:
        return error_result(str(exc))


@mcp.tool()
def add_comment(issue_key: str, comment: str) -> str:
    """Add a comment to a Jira issue."""
    try:
        client = _get_client()
        client.issue_add_comment(issue_key, comment)
        return text_result({"commented": True, "key": issue_key})
    except Exception as exc:
        return error_result(str(exc))


@mcp.tool()
def list_sprints(board_id: int, state: str = "active") -> str:
    """List sprints for a Jira board (state: active, future, closed)."""
    try:
        client = _get_client()
        sprints = client.get_all_sprints_from_board(board_id, state=state)
        return text_result(sprints)
    except Exception as exc:
        return error_result(str(exc))


def main() -> None:
    mcp.run(transport="stdio")


if __name__ == "__main__":
    main()
