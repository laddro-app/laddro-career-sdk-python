from __future__ import annotations

from collections.abc import AsyncIterator
from typing import Any

import httpx

from .errors import LaddroAPIError, LaddroAuthError, LaddroNotFoundError, LaddroUsageLimitError
from .types import SSEEvent


class HttpClient:
    def __init__(self, base_url: str, api_key: str | None = None):
        self._base_url = base_url.rstrip("/")
        self._api_key = api_key

    def _headers(self) -> dict[str, str]:
        headers: dict[str, str] = {}
        if self._api_key:
            headers["x-api-key"] = self._api_key
        return headers

    async def request(
        self,
        method: str,
        path: str,
        *,
        json: Any | None = None,
        params: dict[str, Any] | None = None,
        data: dict[str, Any] | None = None,
        files: dict[str, Any] | None = None,
    ) -> Any:
        url = f"{self._base_url}{path}"
        clean_params = {k: v for k, v in (params or {}).items() if v is not None}

        async with httpx.AsyncClient() as client:
            response = await client.request(
                method,
                url,
                headers=self._headers(),
                json=json,
                params=clean_params or None,
                data=data,
                files=files,
                timeout=120,
            )

        if not response.is_success:
            self._handle_error(response)

        return response.json()

    async def request_binary(
        self,
        method: str,
        path: str,
        *,
        json: Any | None = None,
        data: dict[str, Any] | None = None,
        files: dict[str, Any] | None = None,
    ) -> bytes:
        url = f"{self._base_url}{path}"

        async with httpx.AsyncClient() as client:
            response = await client.request(
                method,
                url,
                headers=self._headers(),
                json=json,
                data=data,
                files=files,
                timeout=120,
            )

        if not response.is_success:
            self._handle_error(response)

        return response.content

    async def request_sse(
        self,
        method: str,
        path: str,
        *,
        json: Any | None = None,
        data: dict[str, Any] | None = None,
        files: dict[str, Any] | None = None,
    ) -> AsyncIterator[SSEEvent]:
        url = f"{self._base_url}{path}"
        headers = {**self._headers(), "accept": "text/event-stream"}

        async with httpx.AsyncClient() as client:
            async with client.stream(
                method,
                url,
                headers=headers,
                json=json,
                data=data,
                files=files,
                timeout=120,
            ) as response:
                if not response.is_success:
                    await response.aread()
                    self._handle_error(response)

                current_event = ""
                async for line in response.aiter_lines():
                    if line.startswith("event: "):
                        current_event = line[7:].strip()
                    elif line.startswith("data: "):
                        data_str = line[6:]
                        if current_event:
                            yield SSEEvent(event=current_event, data=data_str)  # type: ignore[arg-type]
                            current_event = ""

    def _handle_error(self, response: httpx.Response) -> None:
        try:
            body = response.json()
        except Exception:
            body = {"error": response.text}

        message = body.get("error", response.text)
        code = body.get("code")

        match response.status_code:
            case 401:
                raise LaddroAuthError(message)
            case 402:
                raise LaddroUsageLimitError(message)
            case 404:
                raise LaddroNotFoundError(message)
            case _:
                raise LaddroAPIError(message, response.status_code, code)
