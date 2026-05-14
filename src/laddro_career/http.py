from __future__ import annotations

from collections.abc import AsyncIterator
from typing import Any
from urllib.parse import unquote

import httpx

from .errors import LaddroAPIError, LaddroAuthError, LaddroNotFoundError, LaddroUsageLimitError
from .types import ArtifactMetadata, BinaryResponse, SSEEvent


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
        response = await self.request_binary_detailed(method, path, json=json, data=data, files=files)
        return response.data

    async def request_binary_detailed(
        self,
        method: str,
        path: str,
        *,
        json: Any | None = None,
        data: dict[str, Any] | None = None,
        files: dict[str, Any] | None = None,
    ) -> BinaryResponse:
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

        return BinaryResponse(data=response.content, metadata=_artifact_metadata(response.headers))

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


def _artifact_metadata(headers: httpx.Headers) -> ArtifactMetadata:
    content_type = headers.get("content-type")
    return ArtifactMetadata(
        resume_id=headers.get("x-resume-id"),
        cover_letter_id=headers.get("x-cover-letter-id"),
        filename=_content_disposition_filename(headers.get("content-disposition")),
        mime_type=content_type.split(";", 1)[0] if content_type else None,
    )


def _content_disposition_filename(value: str | None) -> str | None:
    if not value:
        return None
    for part in value.split(";"):
        part = part.strip()
        if part.lower().startswith("filename*="):
            filename = part.split("=", 1)[1].removeprefix("UTF-8''").strip('"')
            return unquote(filename)
        if part.lower().startswith("filename="):
            return part.split("=", 1)[1].strip('"')
    return None
