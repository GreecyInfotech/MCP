"""Agent Service — Gemini-powered agents orchestrating microservices."""

from __future__ import annotations

import json
from typing import Any

from fastapi import HTTPException
from pydantic import BaseModel, Field

from cloud_run_services.shared.app_factory import create_service_app
from eai_platform.config import get_settings
from eai_platform.http_client import ServiceClient
from eai_platform.logging import get_logger
from vertex_ai.gemini.client import GeminiClient

logger = get_logger(__name__)
app = create_service_app("Agent Service", "1.0.0")


class AgentRequest(BaseModel):
    query: str = Field(..., min_length=1)
    context: dict[str, Any] = Field(default_factory=dict)


class AgentResponse(BaseModel):
    agent: str
    answer: str
    actions_taken: list[str]
    metadata: dict[str, Any]


AGENT_DEFS: dict[str, dict[str, Any]] = {
    "backlog": {
        "name": "backlog-agent",
        "description": "Sprint planning, backlog prioritization, and Jira management.",
        "system": "You are a product backlog agent. Use Jira and reporting tools.",
        "tools": [
            {"name": "search_issues", "service": "jira", "path": "/issues/search"},
            {"name": "sprint_velocity", "service": "reporting", "path": "/metrics/velocity"},
        ],
    },
    "support": {
        "name": "support-agent",
        "description": "Support ticket triage with knowledge base and Confluence lookup.",
        "system": "You are a support agent. Search knowledge base and Confluence.",
        "tools": [
            {"name": "search_knowledge", "service": "rag", "path": "/search"},
            {"name": "search_confluence", "service": "confluence", "path": "/pages/search"},
            {"name": "create_ticket", "service": "jira", "path": "/issues"},
        ],
    },
    "incident": {
        "name": "incident-agent",
        "description": "Incident detection, triage, and response.",
        "system": "You are an incident response agent. Query reporting and create incidents.",
        "tools": [
            {"name": "incident_summary", "service": "reporting", "path": "/metrics/incidents"},
            {"name": "create_incident", "service": "jira", "path": "/issues"},
        ],
    },
    "reporting": {
        "name": "reporting-agent",
        "description": "Metrics, dashboards, and executive reports.",
        "system": "You are a reporting agent. Generate metrics and dashboards.",
        "tools": [
            {"name": "dashboard_snapshot", "service": "reporting", "path": "/dashboard"},
            {"name": "generate_report", "service": "reporting", "path": "/reports"},
        ],
    },
    "code": {
        "name": "code-agent",
        "description": "PR review, code search, and development assistance.",
        "system": "You are a code agent. Search GitHub and internal docs.",
        "tools": [
            {"name": "search_code", "service": "github", "path": "/code/search"},
            {"name": "list_pull_requests", "service": "github", "path": "/pulls"},
            {"name": "search_docs", "service": "rag", "path": "/search"},
        ],
    },
}


def _service_client(service_key: str) -> ServiceClient:
    settings = get_settings()
    mapping = {
        "jira": settings.jira_service_url,
        "confluence": settings.confluence_service_url,
        "github": settings.github_service_url,
        "reporting": settings.reporting_service_url,
        "rag": settings.rag_service_url,
    }
    return ServiceClient(mapping[service_key])


async def _execute_tool(tool_def: dict[str, Any], query: str) -> str:
    client = _service_client(tool_def["service"])
    path = tool_def["path"]
    name = tool_def["name"]

    try:
        if tool_def["service"] == "rag":
            return json.dumps(await client.post(path, {"query": query, "top_k": 5}))
        if name == "search_issues":
            return json.dumps(
                await client.post(path, {"jql": "status != Done ORDER BY created DESC", "max_results": 10})
            )
        if name == "create_incident" or name == "create_ticket":
            return json.dumps(
                await client.post(path, {"project_key": "PROJ", "summary": query[:100], "description": query})
            )
        if name == "search_confluence":
            return json.dumps(await client.post(path, {"query": query}))
        if name == "search_code":
            return json.dumps(await client.post(path, {"query": query}))
        if name == "list_pull_requests":
            return json.dumps(await client.get(f"{path}?repo={get_settings().github_org}/main-app"))
        return json.dumps(await client.get(path))
    except Exception as exc:
        return json.dumps({"error": str(exc)})


@app.get("/agents")
async def list_agents() -> list[dict[str, str]]:
    return [
        {"id": k, "name": v["name"], "description": v["description"]}
        for k, v in AGENT_DEFS.items()
    ]


@app.post("/agents/{agent_id}/run", response_model=AgentResponse)
async def run_agent(agent_id: str, request: AgentRequest) -> AgentResponse:
    if agent_id not in AGENT_DEFS:
        raise HTTPException(status_code=404, detail=f"Agent '{agent_id}' not found")

    agent_def = AGENT_DEFS[agent_id]
    gemini = GeminiClient()
    tools = [
        {
            "type": "function",
            "function": {
                "name": t["name"],
                "description": f"Call {t['name']} on {t['service']}",
                "parameters": {"type": "object", "properties": {"query": {"type": "string"}}},
            },
        }
        for t in agent_def["tools"]
    ]

    messages = [
        {"role": "system", "content": agent_def["system"]},
        {"role": "user", "content": request.query},
    ]

    actions: list[str] = []
    tool_results: list[dict[str, Any]] = []

    for _ in range(3):
        response = await gemini.generate(messages, tools)
        if response.get("tool_calls"):
            for tc in response["tool_calls"]:
                tool_def = next(t for t in agent_def["tools"] if t["name"] == tc["name"])
                result = await _execute_tool(tool_def, request.query)
                actions.append(f"{tc['name']}({tc['arguments']})")
                tool_results.append({"tool": tc["name"], "result": result})
            messages.append({"role": "assistant", "content": f"Tool results: {tool_results}"})
        else:
            return AgentResponse(
                agent=agent_id,
                answer=response.get("content") or "No response generated.",
                actions_taken=actions,
                metadata={"tool_results": tool_results},
            )

    return AgentResponse(
        agent=agent_id,
        answer="Completed tool execution.",
        actions_taken=actions,
        metadata={"tool_results": tool_results},
    )


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8082)
