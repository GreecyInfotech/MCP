"""Gemini chat client via Vertex AI."""

from __future__ import annotations

import json
from typing import Any

from eai_platform.config import get_settings
from eai_platform.logging import get_logger

logger = get_logger(__name__)


class GeminiClient:
    def __init__(self) -> None:
        self._settings = get_settings()
        self._model_name = self._settings.gemini_model

    async def generate(
        self,
        messages: list[dict[str, Any]],
        tools: list[dict[str, Any]] | None = None,
        temperature: float = 0.2,
    ) -> dict[str, Any]:
        if not self._settings.use_vertex_ai or not self._settings.gcp_project_id:
            return await self._generate_dev(messages, tools)

        import vertexai
        from vertexai.generative_models import Content, FunctionDeclaration, GenerativeModel, Part, Tool

        vertexai.init(project=self._settings.gcp_project_id, location=self._settings.vertex_location)

        gemini_tools = None
        if tools:
            declarations = [
                FunctionDeclaration(
                    name=t["function"]["name"],
                    description=t["function"].get("description", ""),
                    parameters=t["function"].get("parameters", {}),
                )
                for t in tools
            ]
            gemini_tools = [Tool(function_declarations=declarations)]

        model = GenerativeModel(self._model_name, tools=gemini_tools)
        contents = [
            Content(role=m["role"], parts=[Part.from_text(m["content"])])
            for m in messages
            if m.get("content")
        ]
        response = model.generate_content(contents, generation_config={"temperature": temperature})
        return self._parse_response(response)

    async def _generate_dev(
        self, messages: list[dict[str, Any]], tools: list[dict[str, Any]] | None
    ) -> dict[str, Any]:
        user_msg = next((m["content"] for m in reversed(messages) if m["role"] == "user"), "")
        if tools:
            tool_names = [t["function"]["name"] for t in tools]
            return {
                "content": None,
                "tool_calls": [
                    {
                        "id": "dev-call-1",
                        "name": tool_names[0],
                        "arguments": json.dumps({"query": user_msg}),
                    }
                ],
            }
        return {"content": f"[Dev mode] Gemini response for: {user_msg}", "tool_calls": []}

    def _parse_response(self, response: Any) -> dict[str, Any]:
        candidate = response.candidates[0]
        parts = candidate.content.parts
        tool_calls = []
        text_parts = []
        for part in parts:
            if hasattr(part, "function_call") and part.function_call:
                fc = part.function_call
                tool_calls.append(
                    {
                        "id": fc.name,
                        "name": fc.name,
                        "arguments": json.dumps(dict(fc.args)),
                    }
                )
            elif hasattr(part, "text") and part.text:
                text_parts.append(part.text)
        return {
            "content": "\n".join(text_parts) if text_parts else None,
            "tool_calls": tool_calls,
        }
