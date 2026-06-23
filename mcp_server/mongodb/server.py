"""MongoDB MCP server — collection introspection and read queries."""

from __future__ import annotations

import json
from typing import Any

from mcp.server.fastmcp import FastMCP

from eai_platform.config import get_settings
from eai_platform.mcp_base import error_result, text_result

mcp = FastMCP(
    "mongodb",
    instructions=(
        "MongoDB integration for collection exploration and read-only document queries. "
        "Write operations are not exposed."
    ),
)

_client: Any = None

BLOCKED_PIPELINE_STAGES = frozenset(
    {"$out", "$merge", "$delete", "$update", "$replaceRoot", "$replaceWith"}
)


def _get_client() -> Any:
    global _client
    if _client is None:
        try:
            from pymongo import MongoClient
        except ImportError as exc:
            raise ImportError("Install MongoDB support: pip install -e '.[mcp]'") from exc
        settings = get_settings()
        _client = MongoClient(settings.mongodb_uri, serverSelectionTimeoutMS=5000)
        _client.admin.command("ping")
    return _client


def _get_db() -> Any:
    settings = get_settings()
    return _get_client()[settings.mongodb_database]


def _validate_read_pipeline(pipeline: list[dict[str, Any]]) -> None:
    for stage in pipeline:
        if not isinstance(stage, dict):
            raise ValueError("Each pipeline stage must be an object")
        for key in stage:
            if key in BLOCKED_PIPELINE_STAGES:
                raise ValueError(f"Write stage not allowed: {key}")


@mcp.tool()
def list_collections() -> str:
    """List all collections in the configured MongoDB database."""
    try:
        collections = _get_db().list_collection_names()
        return text_result({"database": get_settings().mongodb_database, "collections": collections})
    except Exception as exc:
        return error_result(str(exc))


@mcp.tool()
def describe_collection(collection: str, sample_size: int = 5) -> str:
    """Infer schema from sample documents in a collection."""
    try:
        coll = _get_db()[collection]
        docs = list(coll.find({}, limit=sample_size))
        for doc in docs:
            doc.pop("_id", None)
        count = coll.estimated_document_count()
        return text_result(
            {
                "collection": collection,
                "estimated_count": count,
                "sample_documents": docs,
            }
        )
    except Exception as exc:
        return error_result(str(exc))


@mcp.tool()
def find_documents(collection: str, filter_json: str = "{}", limit: int = 25) -> str:
    """Find documents using a MongoDB filter (JSON object)."""
    try:
        query = json.loads(filter_json) if filter_json.strip() else {}
        if not isinstance(query, dict):
            return error_result("filter_json must be a JSON object")
        docs = list(_get_db()[collection].find(query, limit=limit))
        for doc in docs:
            doc["_id"] = str(doc.get("_id", ""))
        return text_result({"collection": collection, "count": len(docs), "documents": docs})
    except Exception as exc:
        return error_result(str(exc))


@mcp.tool()
def count_documents(collection: str, filter_json: str = "{}") -> str:
    """Count documents matching a MongoDB filter."""
    try:
        query = json.loads(filter_json) if filter_json.strip() else {}
        if not isinstance(query, dict):
            return error_result("filter_json must be a JSON object")
        count = _get_db()[collection].count_documents(query)
        return text_result({"collection": collection, "count": count})
    except Exception as exc:
        return error_result(str(exc))


@mcp.tool()
def aggregate(collection: str, pipeline_json: str, limit: int = 100) -> str:
    """Run a read-only aggregation pipeline (JSON array)."""
    try:
        pipeline = json.loads(pipeline_json)
        if not isinstance(pipeline, list):
            return error_result("pipeline_json must be a JSON array")
        _validate_read_pipeline(pipeline)
        if limit > 0 and not any("$limit" in stage for stage in pipeline):
            pipeline = [*pipeline, {"$limit": limit}]
        docs = list(_get_db()[collection].aggregate(pipeline))
        for doc in docs:
            if "_id" in doc:
                doc["_id"] = str(doc["_id"])
        return text_result({"collection": collection, "count": len(docs), "results": docs})
    except Exception as exc:
        return error_result(str(exc))


def main() -> None:
    mcp.run(transport="stdio")


if __name__ == "__main__":
    main()
