from __future__ import annotations

from dataclasses import dataclass, field
from typing import Literal


@dataclass
class LaddroConfig:
    api_key: str | None = None
    base_url: str = "https://api.laddro.com"


@dataclass
class ResumeSummary:
    id: str
    resume_id: str
    title: str
    is_default: bool
    created_at: str
    updated_at: str


@dataclass
class PaginatedList[T]:
    items: list[T]
    total: int
    limit: int
    offset: int


@dataclass
class TemplateDefaults:
    page_size: str
    spacing: int
    font_size: int
    font: str
    page_numbering: str


@dataclass
class Template:
    id: str
    name: str
    ats_score: int
    layout_type: str
    supports_profile_image: bool
    defaults: TemplateDefaults


@dataclass
class TemplateColor:
    id: str
    background_color: str
    background_part_color: str | None = None
    underline_color: str | None = None
    text: str | None = None
    text_muted: str | None = None


@dataclass
class TemplateFont:
    family: str
    label: str


@dataclass
class TemplateDetail(Template):
    available_colors: list[TemplateColor] = field(default_factory=list)
    available_fonts: list[TemplateFont] = field(default_factory=list)


@dataclass
class Model:
    id: str
    name: str
    recommended: bool


@dataclass
class ModelProvider:
    provider: str
    name: str
    base_url: str
    models: list[Model]
    key_prefix: str
    docs_url: str


@dataclass
class Language:
    code: str
    name: str


PageNumbering = Literal["none", "simple", "fraction", "page"]


@dataclass
class RenderOptions:
    template_id: str
    locale: str | None = None
    color_id: str | None = None
    font: str | None = None
    spacing: float | None = None
    margin: float | None = None
    font_size: float | None = None
    show_profile_image: bool | None = None
    profile_image_url: str | None = None
    page_numbering: PageNumbering | None = None


@dataclass
class TailorRequest:
    position_name: str
    resume_id: str | None = None
    job_description: str | None = None
    job_url: str | None = None
    mode: Literal["standard", "new"] | None = None
    language: str | None = None
    include_cover_letter: bool | None = None
    template_id: str | None = None
    color_id: str | None = None
    font: str | None = None
    spacing: float | None = None
    margin: float | None = None
    font_size: float | None = None
    page_numbering: PageNumbering | None = None


@dataclass
class CoverLetterSummary:
    id: str
    cover_letter_id: str
    title: str
    created_at: str
    updated_at: str


@dataclass
class CreateCoverLetterRequest:
    full_name: str
    letter_content: str
    title: str | None = None
    job_title: str | None = None
    address: str | None = None
    email: str | None = None
    phone: str | None = None
    company_name: str | None = None
    hiring_manager: str | None = None


@dataclass
class CreateCoverLetterResponse:
    cover_letter_id: str
    title: str
    status: str


@dataclass
class GenerateCoverLetterRequest:
    position_name: str
    resume_id: str | None = None
    job_description: str | None = None
    job_url: str | None = None
    language: str | None = None
    template_id: str | None = None
    color_id: str | None = None
    font: str | None = None
    spacing: float | None = None
    margin: float | None = None
    font_size: float | None = None
    page_numbering: PageNumbering | None = None


@dataclass
class ExportRequest:
    resume_id: str
    template_id: str | None = None
    locale: str | None = None
    color_id: str | None = None
    font: str | None = None
    spacing: float | None = None
    margin: float | None = None
    font_size: float | None = None
    show_profile_image: bool | None = None
    profile_image_url: str | None = None
    page_numbering: PageNumbering | None = None


@dataclass
class AISettings:
    provider: str
    model: str
    base_url: str
    has_api_key: bool
    updated_at: str | None = None


@dataclass
class SettingsResponse:
    ai: AISettings | None


@dataclass
class UpdateAISettingsRequest:
    provider: str
    api_key: str
    model: str | None = None


@dataclass
class SSEEvent:
    event: Literal["progress", "complete", "error"]
    data: str
