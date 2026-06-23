"""Confluence integration microservice."""

from __future__ import annotations

from typing import Any

from fastapi import HTTPException
from pydantic import BaseModel, Field

from cloud_run_services.shared.app_factory import create_service_app
from eai_platform.config import get_settings

app = create_service_app("Confluence Service", "1.0.0")


def _get_confluence() -> Any:
    from atlassian import Confluence

    settings = get_settings()
    if not settings.confluence_url or not settings.confluence_api_token:
        raise HTTPException(status_code=503, detail="Confluence not configured")
    return Confluence(
        url=settings.confluence_url,
        username=settings.confluence_email,
        password=settings.confluence_api_token,
        cloud=True,
    )


class SearchRequest(BaseModel):
    query: str
    space_key: str = ""
    limit: int = 20


class CreatePageRequest(BaseModel):
    space_key: str
    title: str
    body: str
    parent_id: str = ""


@app.post("/pages/search")
async def search_pages(request: SearchRequest) -> dict[str, Any]:
    client = _get_confluence()
    cql = f'type=page AND text ~ "{request.query}"'
    if request.space_key:
        cql += f' AND space="{request.space_key}"'
    result = client.cql(cql, limit=request.limit)
    pages = [
        {"id": r["content"]["id"], "title": r["content"]["title"]}
        for r in result.get("results", [])
    ]
    return {"pages": pages, "total": len(pages)}


@app.get("/pages/{page_id}")
async def get_page(page_id: str) -> dict[str, Any]:
    client = _get_confluence()
    page = client.get_page_by_id(page_id, expand="body.storage,version,space")
    return {
        "id": page["id"],
        "title": page["title"],
        "body": page.get("body", {}).get("storage", {}).get("value", ""),
    }


@app.post("/pages")
async def create_page(request: CreatePageRequest) -> dict[str, Any]:
    client = _get_confluence()
    kwargs: dict[str, Any] = {
        "space": request.space_key,
        "title": request.title,
        "body": request.body,
        "type": "page",
    }
    if request.parent_id:
        kwargs["parent_id"] = request.parent_id
    result = client.create_page(**kwargs)
    return {"created": True, "id": result.get("id")}


@app.get("/spaces")
async def list_spaces(limit: int = 50) -> dict[str, Any]:
    client = _get_confluence()
    spaces = client.get_all_spaces(start=0, limit=limit)
    return {
        "spaces": [
            {"key": s["key"], "name": s["name"]} for s in spaces.get("results", [])
        ]
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8084)
