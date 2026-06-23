"""Shared utilities for MCP server implementations."""

from __future__ import annotations

import json
from typing import Any

from mcp.server.fastmcp import FastMCP


def create_mcp_server(name: str, instructions: str) -> FastMCP:
    return FastMCP(name, instructions=instructions)


def text_result(data: Any) -> str:
    if isinstance(data, str):
        return data
    return json.dumps(data, indent=2, default=str)


def error_result(message: str) -> str:
    return json.dumps({"error": message}, indent=2)
