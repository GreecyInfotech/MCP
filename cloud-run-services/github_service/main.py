"""GitHub integration microservice."""

from __future__ import annotations

from typing import Any

from fastapi import HTTPException, Query
from pydantic import BaseModel, Field

from cloud_run_services.shared.app_factory import create_service_app
from eai_platform.config import get_settings

app = create_service_app("GitHub Service", "1.0.0")


def _get_github() -> Any:
    from github import Github

    settings = get_settings()
    if not settings.github_token:
        raise HTTPException(status_code=503, detail="GitHub not configured")
    return Github(settings.github_token)


class CodeSearchRequest(BaseModel):
    query: str
    repo: str = ""
    per_page: int = 20


@app.get("/repos")
async def list_repos(org: str = "", per_page: int = 30) -> dict[str, Any]:
    client = _get_github()
    settings = get_settings()
    target = org or settings.github_org
    repos = (
        client.get_organization(target).get_repos()
        if target
        else client.get_user().get_repos()
    )
    result = [
        {"name": r.name, "full_name": r.full_name, "language": r.language, "stars": r.stargazers_count}
        for i, r in enumerate(repos)
        if i < per_page
    ]
    return {"repos": result}


@app.post("/code/search")
async def search_code(request: CodeSearchRequest) -> dict[str, Any]:
    client = _get_github()
    q = request.query if not request.repo else f"{request.query} repo:{request.repo}"
    results = client.search_code(q)
    items = [
        {"name": r.name, "path": r.path, "repository": r.repository.full_name, "url": r.html_url}
        for i, r in enumerate(results)
        if i < request.per_page
    ]
    return {"results": items}


@app.get("/pulls")
async def list_pull_requests(repo: str = Query(...), state: str = "open", per_page: int = 20) -> dict[str, Any]:
    client = _get_github()
    prs = client.get_repo(repo).get_pulls(state=state)
    result = [
        {"number": pr.number, "title": pr.title, "author": pr.user.login, "state": pr.state, "url": pr.html_url}
        for i, pr in enumerate(prs)
        if i < per_page
    ]
    return {"pull_requests": result}


@app.get("/pulls/{repo}/{pr_number}")
async def get_pull_request(repo: str, pr_number: int) -> dict[str, Any]:
    client = _get_github()
    pr = client.get_repo(repo).get_pull(pr_number)
    return {
        "number": pr.number,
        "title": pr.title,
        "body": pr.body,
        "state": pr.state,
        "author": pr.user.login,
        "url": pr.html_url,
    }


@app.get("/files/{repo}/{path:path}")
async def get_file(repo: str, path: str, ref: str = "main") -> dict[str, Any]:
    import base64

    client = _get_github()
    content = client.get_repo(repo).get_contents(path, ref=ref)
    if isinstance(content, list):
        return {"type": "directory", "entries": [c.path for c in content]}
    decoded = base64.b64decode(content.content).decode("utf-8", errors="replace")
    return {"path": path, "content": decoded}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8085)
