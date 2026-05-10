from __future__ import annotations

from .http import HttpClient
from .resources import CoverLetters, Export, Resumes, Settings, Tailor, Templates
from .types import LaddroConfig


class Laddro:
    templates: Templates
    resumes: Resumes
    tailor: Tailor
    cover_letters: CoverLetters
    export: Export
    settings: Settings

    def __init__(self, api_key: str | None = None, *, base_url: str = "https://api.laddro.com"):
        http = HttpClient(base_url, api_key)
        self.templates = Templates(http)
        self.resumes = Resumes(http)
        self.tailor = Tailor(http)
        self.cover_letters = CoverLetters(http)
        self.export = Export(http)
        self.settings = Settings(http)

    @classmethod
    def from_config(cls, config: LaddroConfig) -> Laddro:
        return cls(api_key=config.api_key, base_url=config.base_url)
