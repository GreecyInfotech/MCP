"""HTTP client for inter-service communication."""

from __future__ import annotations

from typing import Any

import httpx

from eai_platform.config import get_settings
from eai_platform.logging import get_logger

logger = get_logger(__name__)


class ServiceClient:
    def __init__(self, base_url: str, timeout: float = 60.0) -> None:
        self._base_url = base_url.rstrip("/")
        self._timeout = timeout

    async def get(self, path: str, params: dict[str, Any] | None = None) -> Any:
        async with httpx.AsyncClient(timeout=self._timeout) as client:
            response = await client.get(f"{self._base_url}{path}", params=params)
            response.raise_for_status()
            return response.json()

    async def post(self, path: str, body: dict[str, Any]) -> Any:
        async with httpx.AsyncClient(timeout=self._timeout) as client:
            response = await client.post(f"{self._base_url}{path}", json=body)
            response.raise_for_status()
            return response.json()


def get_service_client(service_name: str) -> ServiceClient:
    settings = get_settings()
    url = settings.service_registry.get(service_name, "")
    if not url:
        raise ValueError(f"Unknown service: {service_name}")
    return ServiceClient(url)
