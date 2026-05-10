#!/usr/bin/env python3
"""Integration tests against the live Laddro Career API."""

import asyncio
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from laddro_career import Laddro, LaddroAuthError

api_key = os.environ.get("LADDRO_API_KEY")
if not api_key:
    print("Set LADDRO_API_KEY to run integration tests")
    sys.exit(1)

client = Laddro(api_key)
public_client = Laddro()

passed = 0
failed = 0


async def test(name, fn):
    global passed, failed
    try:
        await fn()
        print(f"  ✓ {name}")
        passed += 1
    except Exception as e:
        print(f"  ✗ {name}: {e}")
        failed += 1


async def main():
    global passed, failed

    print("\n— Public endpoints (no auth) —\n")

    async def test_list_templates():
        templates = await public_client.templates.list()
        assert len(templates) >= 20, f"expected 20+ templates, got {len(templates)}"
        assert templates[0].id, "template missing id"

    async def test_get_template():
        detail = await public_client.templates.get("GRAPHITE")
        assert detail.id == "GRAPHITE"
        assert len(detail.available_colors) > 0
        assert len(detail.available_fonts) > 0

    async def test_list_fonts():
        fonts = await public_client.templates.fonts()
        assert len(fonts) >= 20, f"expected 20+ fonts, got {len(fonts)}"

    async def test_list_languages():
        languages = await public_client.templates.languages()
        assert len(languages) == 14, f"expected 14 languages, got {len(languages)}"

    async def test_list_models():
        models = await public_client.templates.models()
        assert len(models) >= 10, f"expected 10+ providers, got {len(models)}"
        names = [m.name for m in models]
        assert "OpenAI" in names
        assert "Anthropic" in names

    await test("list templates", test_list_templates)
    await test("get template detail", test_get_template)
    await test("list fonts", test_list_fonts)
    await test("list languages", test_list_languages)
    await test("list models", test_list_models)

    print("\n— Protected endpoints (with auth) —\n")

    async def test_list_resumes():
        result = await client.resumes.list(limit=5)
        assert result.items is not None
        assert isinstance(result.total, int)
        assert result.limit == 5

    async def test_get_settings():
        result = await client.settings.get()
        assert hasattr(result, "ai")

    async def test_list_cover_letters():
        result = await client.cover_letters.list(limit=5)
        assert result.items is not None
        assert isinstance(result.total, int)

    await test("list resumes", test_list_resumes)
    await test("get settings", test_get_settings)
    await test("list cover letters", test_list_cover_letters)

    resume_id = None

    async def test_get_first_resume():
        nonlocal resume_id
        result = await client.resumes.list(limit=1)
        if result.items:
            resume_id = result.items[0].resume_id
            resume = await client.resumes.get(resume_id)
            assert resume.resume_id == resume_id

    await test("get first resume", test_get_first_resume)

    if resume_id:
        async def test_export_pdf():
            from laddro_career import ExportRequest
            pdf = await client.export.pdf(ExportRequest(resume_id=resume_id))
            assert len(pdf) > 1000, f"PDF too small: {len(pdf)} bytes"

        async def test_render_resume():
            from laddro_career import RenderOptions
            pdf = await client.resumes.render(resume_id, RenderOptions(template_id="GRAPHITE"))
            assert len(pdf) > 1000, f"PDF too small: {len(pdf)} bytes"

        await test("export resume as PDF", test_export_pdf)
        await test("render resume with template", test_render_resume)

    async def test_auth_error():
        bad = Laddro("laddro_live_invalid")
        try:
            await bad.resumes.list()
            raise AssertionError("should have raised")
        except LaddroAuthError:
            pass

    await test("auth error on bad key", test_auth_error)

    print(f"\n— Results: {passed} passed, {failed} failed —\n")
    sys.exit(1 if failed > 0 else 0)


asyncio.run(main())
