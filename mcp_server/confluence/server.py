"""Confluence MCP server — page search, read, and create."""

from __future__ import annotations

from atlassian import Confluence
from mcp.server.fastmcp import FastMCP

from eai_platform.config import get_settings
from eai_platform.mcp_base import error_result, text_result

mcp = FastMCP(
    "confluence",
    instructions=(
        "Confluence integration for knowledge base operations. "
        "Search, read, and create documentation pages."
    ),
)


def _get_client() -> Confluence:
    settings = get_settings()
    if not settings.confluence_url or not settings.confluence_api_token:
        raise ValueError("CONFLUENCE_URL and CONFLUENCE_API_TOKEN must be configured")
    return Confluence(
        url=settings.confluence_url,
        username=settings.confluence_email,
        password=settings.confluence_api_token,
        cloud=True,
    )


@mcp.tool()
def search_pages(query: str, space_key: str = "", limit: int = 20) -> str:
    """Search Confluence pages by text query, optionally filtered by space."""
    try:
        client = _get_client()
        cql = f'type=page AND text ~ "{query}"'
        if space_key:
            cql += f' AND space="{space_key}"'
        result = client.cql(cql, limit=limit)
        pages = [
            {
                "id": r["content"]["id"],
                "title": r["content"]["title"],
                "space": r["content"].get("_expandable", {}).get("space", ""),
            }
            for r in result.get("results", [])
        ]
        return text_result({"pages": pages, "total": len(pages)})
    except Exception as exc:
        return error_result(str(exc))


@mcp.tool()
def get_page(page_id: str) -> str:
    """Get a Confluence page by ID including body content."""
    try:
        client = _get_client()
        page = client.get_page_by_id(page_id, expand="body.storage,version,space")
        return text_result(
            {
                "id": page["id"],
                "title": page["title"],
                "space": page.get("space", {}).get("key"),
                "version": page.get("version", {}).get("number"),
                "body": page.get("body", {}).get("storage", {}).get("value", ""),
            }
        )
    except Exception as exc:
        return error_result(str(exc))


@mcp.tool()
def create_page(space_key: str, title: str, body: str, parent_id: str = "") -> str:
    """Create a new Confluence page in the given space."""
    try:
        client = _get_client()
        kwargs: dict = {"space": space_key, "title": title, "body": body, "type": "page"}
        if parent_id:
            kwargs["parent_id"] = parent_id
        result = client.create_page(**kwargs)
        return text_result({"created": True, "id": result.get("id"), "title": title})
    except Exception as exc:
        return error_result(str(exc))


@mcp.tool()
def update_page(page_id: str, title: str, body: str, version: int) -> str:
    """Update an existing Confluence page (requires current version number)."""
    try:
        client = _get_client()
        result = client.update_page(page_id=page_id, title=title, body=body, version=version)
        return text_result({"updated": True, "id": result.get("id"), "version": version + 1})
    except Exception as exc:
        return error_result(str(exc))


@mcp.tool()
def list_spaces(limit: int = 50) -> str:
    """List available Confluence spaces."""
    try:
        client = _get_client()
        spaces = client.get_all_spaces(start=0, limit=limit)
        simplified = [
            {"key": s["key"], "name": s["name"], "type": s.get("type")}
            for s in spaces.get("results", [])
        ]
        return text_result({"spaces": simplified})
    except Exception as exc:
        return error_result(str(exc))


def main() -> None:
    mcp.run(transport="stdio")


if __name__ == "__main__":
    main()
