"""Slack MCP server — channels, messaging, and search."""

from __future__ import annotations

from typing import Any

from mcp.server.fastmcp import FastMCP

from eai_platform.config import get_settings
from eai_platform.mcp_base import error_result, text_result

mcp = FastMCP(
    "slack",
    instructions=(
        "Slack integration for channel discovery, posting messages, "
        "searching messages, and reading channel history."
    ),
)

_client: Any = None


def _get_client() -> Any:
    global _client
    if _client is None:
        try:
            from slack_sdk import WebClient
        except ImportError as exc:
            raise ImportError("Install Slack support: pip install -e '.[mcp]'") from exc
        settings = get_settings()
        if not settings.slack_bot_token:
            raise ValueError("SLACK_BOT_TOKEN must be configured")
        _client = WebClient(token=settings.slack_bot_token)
    return _client


@mcp.tool()
def list_channels(types: str = "public_channel,private_channel", limit: int = 100) -> str:
    """List Slack channels. types: comma-separated channel types."""
    try:
        type_list = [t.strip() for t in types.split(",") if t.strip()]
        response = _get_client().conversations_list(types=",".join(type_list), limit=limit)
        channels = [
            {
                "id": ch["id"],
                "name": ch["name"],
                "is_private": ch.get("is_private", False),
                "num_members": ch.get("num_members"),
                "topic": (ch.get("topic") or {}).get("value", ""),
            }
            for ch in response.get("channels", [])
        ]
        return text_result({"channels": channels})
    except Exception as exc:
        return error_result(str(exc))


@mcp.tool()
def post_message(channel: str, text: str, thread_ts: str = "") -> str:
    """Post a message to a Slack channel (channel ID or name)."""
    try:
        client = _get_client()
        channel_id = channel
        if not channel.startswith("C") and not channel.startswith("D"):
            response = client.conversations_list(types="public_channel,private_channel", limit=200)
            match = next(
                (ch["id"] for ch in response.get("channels", []) if ch["name"] == channel.lstrip("#")),
                None,
            )
            if not match:
                return error_result(f"Channel '{channel}' not found")
            channel_id = match

        kwargs: dict[str, Any] = {"channel": channel_id, "text": text}
        if thread_ts:
            kwargs["thread_ts"] = thread_ts
        response = client.chat_postMessage(**kwargs)
        return text_result(
            {
                "posted": True,
                "channel": channel_id,
                "ts": response.get("ts"),
                "permalink": response.get("message", {}).get("permalink"),
            }
        )
    except Exception as exc:
        return error_result(str(exc))


@mcp.tool()
def search_messages(query: str, count: int = 20) -> str:
    """Search Slack messages using Slack search syntax."""
    try:
        response = _get_client().search_messages(query=query, count=count)
        matches = response.get("messages", {}).get("matches", [])
        results = [
            {
                "channel": m.get("channel", {}).get("name"),
                "user": m.get("username"),
                "text": m.get("text"),
                "timestamp": m.get("ts"),
                "permalink": m.get("permalink"),
            }
            for m in matches
        ]
        return text_result({"query": query, "total": len(results), "messages": results})
    except Exception as exc:
        return error_result(str(exc))


@mcp.tool()
def get_channel_history(channel: str, limit: int = 50) -> str:
    """Get recent messages from a Slack channel."""
    try:
        client = _get_client()
        channel_id = channel
        if not channel.startswith("C") and not channel.startswith("D"):
            response = client.conversations_list(types="public_channel,private_channel", limit=200)
            match = next(
                (ch["id"] for ch in response.get("channels", []) if ch["name"] == channel.lstrip("#")),
                None,
            )
            if not match:
                return error_result(f"Channel '{channel}' not found")
            channel_id = match

        response = client.conversations_history(channel=channel_id, limit=limit)
        messages = [
            {
                "user": msg.get("user"),
                "text": msg.get("text"),
                "timestamp": msg.get("ts"),
                "thread_ts": msg.get("thread_ts"),
            }
            for msg in response.get("messages", [])
        ]
        return text_result({"channel": channel_id, "messages": messages})
    except Exception as exc:
        return error_result(str(exc))


@mcp.tool()
def list_users(limit: int = 50) -> str:
    """List workspace users."""
    try:
        response = _get_client().users_list(limit=limit)
        users = [
            {
                "id": u["id"],
                "name": u.get("name"),
                "real_name": u.get("real_name"),
                "email": (u.get("profile") or {}).get("email"),
                "is_bot": u.get("is_bot", False),
            }
            for u in response.get("members", [])
            if not u.get("deleted")
        ]
        return text_result({"users": users})
    except Exception as exc:
        return error_result(str(exc))


def main() -> None:
    mcp.run(transport="stdio")


if __name__ == "__main__":
    main()
