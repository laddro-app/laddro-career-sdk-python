from __future__ import annotations

from collections.abc import AsyncIterator
from dataclasses import asdict
from pathlib import Path
from typing import BinaryIO

from .http import HttpClient
from .types import (
    AISettings,
    CoverLetterSummary,
    CreateCoverLetterRequest,
    CreateCoverLetterResponse,
    ExportRequest,
    GenerateCoverLetterRequest,
    Language,
    Model,
    ModelProvider,
    PaginatedList,
    RenderOptions,
    ResumeSummary,
    SettingsResponse,
    SSEEvent,
    TailorRequest,
    Template,
    TemplateColor,
    TemplateDefaults,
    TemplateDetail,
    TemplateFont,
    UpdateAISettingsRequest,
)


def _to_api_body(obj: object) -> dict:
    raw = asdict(obj)  # type: ignore[call-overload]
    result = {}
    for key, value in raw.items():
        if value is None:
            continue
        camel = _snake_to_camel(key)
        result[camel] = value
    return result


def _snake_to_camel(name: str) -> str:
    parts = name.split("_")
    return parts[0] + "".join(p.capitalize() for p in parts[1:])


class Templates:
    def __init__(self, http: HttpClient):
        self._http = http

    async def list(self) -> list[Template]:
        data = await self._http.request("GET", "/v1/templates")
        return [_parse_template(t) for t in data["templates"]]

    async def get(self, template_id: str) -> TemplateDetail:
        data = await self._http.request("GET", f"/v1/templates/{template_id}")
        return _parse_template_detail(data)

    async def fonts(self) -> list[TemplateFont]:
        data = await self._http.request("GET", "/v1/fonts")
        return [TemplateFont(family=f["family"], label=f["label"]) for f in data["fonts"]]

    async def languages(self) -> list[Language]:
        data = await self._http.request("GET", "/v1/languages")
        return [Language(code=l["code"], name=l["name"]) for l in data["languages"]]

    async def models(self) -> list[ModelProvider]:
        data = await self._http.request("GET", "/v1/models")
        return [
            ModelProvider(
                provider=m["provider"],
                name=m["name"],
                base_url=m.get("baseUrl", ""),
                models=[Model(id=mod["id"], name=mod["name"], recommended=mod["recommended"]) for mod in m["models"]],
                key_prefix=m.get("keyPrefix", ""),
                docs_url=m.get("docsUrl", ""),
            )
            for m in data["models"]
        ]


class Resumes:
    def __init__(self, http: HttpClient):
        self._http = http

    async def list(self, *, limit: int = 20, offset: int = 0) -> PaginatedList[ResumeSummary]:
        data = await self._http.request(
            "GET", "/v1/resumes", params={"limit": limit, "offset": offset}
        )
        return PaginatedList(
            items=[_parse_resume(r) for r in data["items"]],
            total=data["total"],
            limit=data["limit"],
            offset=data["offset"],
        )

    async def get(self, resume_id: str) -> ResumeSummary:
        data = await self._http.request("GET", f"/v1/resumes/{resume_id}")
        return _parse_resume(data)

    async def parse(
        self,
        file: BinaryIO | Path | bytes,
        *,
        filename: str = "resume.pdf",
        template_id: str | None = None,
        locale: str | None = None,
        color_id: str | None = None,
        font: str | None = None,
        spacing: float | None = None,
        margin: float | None = None,
        font_size: float | None = None,
    ) -> bytes:
        file_data = _read_file(file)
        files = {"file": (filename, file_data, "application/pdf")}
        data: dict[str, str] = {}
        if template_id:
            data["templateId"] = template_id
        if locale:
            data["locale"] = locale
        if color_id:
            data["colorId"] = color_id
        if font:
            data["font"] = font
        if spacing is not None:
            data["spacing"] = str(spacing)
        if margin is not None:
            data["margin"] = str(margin)
        if font_size is not None:
            data["fontSize"] = str(font_size)

        return await self._http.request_binary("POST", "/v1/resumes/parse", data=data, files=files)

    async def render(self, resume_id: str, options: RenderOptions) -> bytes:
        return await self._http.request_binary(
            "PUT", f"/v1/resumes/{resume_id}/render", json=_to_api_body(options)
        )


class Tailor:
    def __init__(self, http: HttpClient):
        self._http = http

    async def run(self, request: TailorRequest) -> bytes:
        return await self._http.request_binary("POST", "/v1/tailor", json=_to_api_body(request))

    async def upload(
        self,
        file: BinaryIO | Path | bytes,
        *,
        position_name: str,
        filename: str = "resume.pdf",
        job_description: str | None = None,
        job_url: str | None = None,
        mode: str | None = None,
        language: str | None = None,
        include_cover_letter: bool | None = None,
    ) -> bytes:
        file_data = _read_file(file)
        files = {"file": (filename, file_data, "application/pdf")}
        data: dict[str, str] = {"positionName": position_name}
        if job_description:
            data["jobDescription"] = job_description
        if job_url:
            data["jobUrl"] = job_url
        if mode:
            data["mode"] = mode
        if language:
            data["language"] = language
        if include_cover_letter is not None:
            data["includeCoverLetter"] = str(include_cover_letter).lower()

        return await self._http.request_binary("POST", "/v1/tailor", data=data, files=files)

    async def stream(self, request: TailorRequest) -> AsyncIterator[SSEEvent]:
        return self._http.request_sse("POST", "/v1/tailor", json=_to_api_body(request))


class CoverLetters:
    def __init__(self, http: HttpClient):
        self._http = http

    async def list(self, *, limit: int = 20, offset: int = 0) -> PaginatedList[CoverLetterSummary]:
        data = await self._http.request(
            "GET", "/v1/cover-letters", params={"limit": limit, "offset": offset}
        )
        return PaginatedList(
            items=[_parse_cover_letter(c) for c in data["items"]],
            total=data["total"],
            limit=data["limit"],
            offset=data["offset"],
        )

    async def get(self, cover_letter_id: str) -> CoverLetterSummary:
        data = await self._http.request("GET", f"/v1/cover-letters/{cover_letter_id}")
        return _parse_cover_letter(data)

    async def create(self, request: CreateCoverLetterRequest) -> CreateCoverLetterResponse:
        data = await self._http.request("POST", "/v1/cover-letters", json=_to_api_body(request))
        return CreateCoverLetterResponse(
            cover_letter_id=data["coverLetterId"],
            title=data["title"],
            status=data["status"],
        )

    async def generate(self, request: GenerateCoverLetterRequest) -> bytes:
        return await self._http.request_binary(
            "POST", "/v1/cover-letters/generate", json=_to_api_body(request)
        )

    async def upload(
        self,
        file: BinaryIO | Path | bytes,
        *,
        position_name: str,
        filename: str = "resume.pdf",
        job_description: str | None = None,
        job_url: str | None = None,
        language: str | None = None,
    ) -> bytes:
        file_data = _read_file(file)
        files = {"file": (filename, file_data, "application/pdf")}
        data: dict[str, str] = {"positionName": position_name}
        if job_description:
            data["jobDescription"] = job_description
        if job_url:
            data["jobUrl"] = job_url
        if language:
            data["language"] = language

        return await self._http.request_binary(
            "POST", "/v1/cover-letters/generate", data=data, files=files
        )

    async def render(self, cover_letter_id: str, options: RenderOptions) -> bytes:
        return await self._http.request_binary(
            "PUT", f"/v1/cover-letters/{cover_letter_id}/render", json=_to_api_body(options)
        )

    async def generate_stream(self, request: GenerateCoverLetterRequest) -> AsyncIterator[SSEEvent]:
        return self._http.request_sse(
            "POST", "/v1/cover-letters/generate", json=_to_api_body(request)
        )


class Export:
    def __init__(self, http: HttpClient):
        self._http = http

    async def pdf(self, request: ExportRequest) -> bytes:
        return await self._http.request_binary("POST", "/v1/export", json=_to_api_body(request))

    async def stream(self, request: ExportRequest) -> AsyncIterator[SSEEvent]:
        return self._http.request_sse("POST", "/v1/export", json=_to_api_body(request))


class Settings:
    def __init__(self, http: HttpClient):
        self._http = http

    async def get(self) -> SettingsResponse:
        data = await self._http.request("GET", "/v1/settings")
        return _parse_settings(data)

    async def update_model(self, request: UpdateAISettingsRequest) -> SettingsResponse:
        data = await self._http.request("PUT", "/v1/settings/model", json=_to_api_body(request))
        return _parse_settings(data)

    async def delete_model(self) -> SettingsResponse:
        data = await self._http.request("DELETE", "/v1/settings/model")
        return _parse_settings(data)


def _read_file(file: BinaryIO | Path | bytes) -> bytes:
    if isinstance(file, bytes):
        return file
    if isinstance(file, Path):
        return file.read_bytes()
    return file.read()


def _parse_template(data: dict) -> Template:
    defaults = data.get("defaults", {})
    return Template(
        id=data["id"],
        name=data["name"],
        ats_score=data.get("atsScore", 0),
        layout_type=data.get("layoutType", "single-column"),
        supports_profile_image=data.get("supportsProfileImage", False),
        defaults=TemplateDefaults(
            page_size=defaults.get("pageSize", "A4"),
            spacing=defaults.get("spacing", 8),
            font_size=defaults.get("fontSize", 8),
            font=defaults.get("font", "Inter"),
            page_numbering=defaults.get("pageNumbering", "none"),
        ),
    )


def _parse_template_detail(data: dict) -> TemplateDetail:
    base = _parse_template(data)
    return TemplateDetail(
        **{k: v for k, v in base.__dict__.items()},
        available_colors=[
            TemplateColor(
                id=c["id"],
                background_color=c.get("backgroundColor", ""),
                background_part_color=c.get("backgroundPartColor"),
                underline_color=c.get("underlineColor"),
                text=c.get("text"),
                text_muted=c.get("textMuted"),
            )
            for c in data.get("availableColors", [])
        ],
        available_fonts=[
            TemplateFont(family=f["family"], label=f["label"])
            for f in data.get("availableFonts", [])
        ],
    )


def _parse_resume(data: dict) -> ResumeSummary:
    return ResumeSummary(
        id=data["id"],
        resume_id=data["resumeId"],
        title=data["title"],
        is_default=data.get("isDefault", False),
        created_at=data["createdAt"],
        updated_at=data["updatedAt"],
    )


def _parse_cover_letter(data: dict) -> CoverLetterSummary:
    return CoverLetterSummary(
        id=data["id"],
        cover_letter_id=data["coverLetterId"],
        title=data["title"],
        created_at=data["createdAt"],
        updated_at=data["updatedAt"],
    )


def _parse_settings(data: dict) -> SettingsResponse:
    ai = data.get("ai")
    if ai is None:
        return SettingsResponse(ai=None)
    return SettingsResponse(
        ai=AISettings(
            provider=ai["provider"],
            model=ai["model"],
            base_url=ai.get("baseUrl", ""),
            has_api_key=ai.get("hasApiKey", False),
            updated_at=ai.get("updatedAt"),
        )
    )
