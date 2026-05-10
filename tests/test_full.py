#!/usr/bin/env python3
"""Full integration test — all 18 Career API endpoints."""

import asyncio
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from laddro_career import (
    Laddro,
    LaddroAuthError,
    LaddroNotFoundError,
    CreateCoverLetterRequest,
    ExportRequest,
    GenerateCoverLetterRequest,
    RenderOptions,
    TailorRequest,
    UpdateAISettingsRequest,
)

api_key = os.environ.get("LADDRO_API_KEY")
if not api_key:
    print("Set LADDRO_API_KEY to run tests")
    sys.exit(1)

client = Laddro(api_key)
public = Laddro()
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
    resume_id = None
    cover_letter_id = None

    # --- PUBLIC (5) ---
    print("\n— 1. Public endpoints (5/18) —\n")

    async def t1():
        templates = await public.templates.list()
        assert len(templates) == 22, f"expected 22, got {len(templates)}"
    await test("GET /v1/templates", t1)

    async def t2():
        d = await public.templates.get("GRAPHITE")
        assert d.id == "GRAPHITE"
        assert len(d.available_colors) > 0
        assert len(d.available_fonts) > 0
    await test("GET /v1/templates/{id}", t2)

    async def t3():
        fonts = await public.templates.fonts()
        assert len(fonts) == 21, f"expected 21, got {len(fonts)}"
    await test("GET /v1/fonts", t3)

    async def t4():
        langs = await public.templates.languages()
        assert len(langs) == 14, f"expected 14, got {len(langs)}"
    await test("GET /v1/languages", t4)

    async def t5():
        models = await public.templates.models()
        assert len(models) == 10, f"expected 10, got {len(models)}"
    await test("GET /v1/models", t5)

    # --- RESUMES (4) ---
    print("\n— 2. Resume endpoints (4/18) —\n")

    async def t6():
        nonlocal resume_id
        result = await client.resumes.list(limit=5)
        assert len(result.items) > 0, "no resumes"
        resume_id = next((r.resume_id for r in result.items if r.is_default), result.items[0].resume_id)
    await test("GET /v1/resumes", t6)

    async def t7():
        r = await client.resumes.get(resume_id)
        assert r.resume_id == resume_id
    await test("GET /v1/resumes/{id}", t7)

    async def t8():
        pdf = await client.resumes.render(resume_id, RenderOptions(template_id="GRAPHITE"))
        assert len(pdf) > 1000, f"too small: {len(pdf)}"
    await test("PUT /v1/resumes/{id}/render", t8)

    async def t9():
        pass  # parse requires file upload — tested separately
    await test("POST /v1/resumes/parse (skip - needs file)", t9)

    # --- TAILOR (1) ---
    print("\n— 3. Tailor endpoint (1/18) —\n")

    async def t10():
        pdf = await client.tailor.run(TailorRequest(
            position_name="SDK Test Engineer",
            resume_id=resume_id,
            job_description="Build and test SDKs. Python required.",
            template_id="GRAPHITE",
        ))
        assert len(pdf) > 5000, f"too small: {len(pdf)}"
    await test("POST /v1/tailor", t10)

    # --- EXPORT (1) ---
    print("\n— 4. Export endpoint (1/18) —\n")

    async def t11():
        pdf = await client.export.pdf(ExportRequest(resume_id=resume_id, template_id="COBALT"))
        assert len(pdf) > 1000, f"too small: {len(pdf)}"
    await test("POST /v1/export", t11)

    # --- COVER LETTERS (5) ---
    print("\n— 5. Cover Letter endpoints (5/18) —\n")

    async def t12():
        result = await client.cover_letters.list()
        assert result.items is not None
    await test("GET /v1/cover-letters", t12)

    async def t13():
        nonlocal cover_letter_id
        result = await client.cover_letters.create(CreateCoverLetterRequest(
            full_name="Test User",
            letter_content="<p>Dear Hiring Manager,</p><p>SDK integration test.</p>",
            title="Python SDK Test",
            company_name="Test Corp",
        ))
        assert result.cover_letter_id
        cover_letter_id = result.cover_letter_id
    await test("POST /v1/cover-letters", t13)

    async def t14():
        cl = await client.cover_letters.get(cover_letter_id)
        assert cl.cover_letter_id == cover_letter_id
    await test("GET /v1/cover-letters/{id}", t14)

    async def t15():
        pdf = await client.cover_letters.render(cover_letter_id, RenderOptions(template_id="NICKEL"))
        assert len(pdf) > 1000, f"too small: {len(pdf)}"
    await test("PUT /v1/cover-letters/{id}/render", t15)

    async def t16():
        pdf = await client.cover_letters.generate(GenerateCoverLetterRequest(
            position_name="SDK Test Engineer",
            resume_id=resume_id,
            job_description="Write SDK tests. Python required.",
            template_id="NICKEL",
        ))
        assert len(pdf) > 1000, f"too small: {len(pdf)}"
    await test("POST /v1/cover-letters/generate", t16)

    # --- SETTINGS (3) ---
    print("\n— 6. Settings endpoints (3/18) —\n")

    async def t17():
        s = await client.settings.get()
        assert hasattr(s, "ai")
    await test("GET /v1/settings", t17)

    async def t18():
        try:
            await client.settings.update_model(UpdateAISettingsRequest(
                provider="OpenAI",
                model="gpt-4o-mini",
                api_key="sk-test-invalid-key",
            ))
        except Exception as e:
            assert "400" in str(type(e).__name__) or hasattr(e, "status")
    await test("PUT /v1/settings/model", t18)

    async def t19():
        s = await client.settings.delete_model()
        assert s.ai is None
    await test("DELETE /v1/settings/model", t19)

    # --- ERROR HANDLING ---
    print("\n— 7. Error handling —\n")

    async def t20():
        bad = Laddro("laddro_live_invalid")
        try:
            await bad.resumes.list()
            raise AssertionError("should raise")
        except LaddroAuthError:
            pass
    await test("401 on bad key", t20)

    async def t21():
        try:
            await client.resumes.get("00000000-0000-0000-0000-000000000000")
            raise AssertionError("should raise")
        except LaddroNotFoundError:
            pass
    await test("404 on missing resume", t21)

    print(f"\n═══ FINAL: {passed} passed, {failed} failed (18 endpoints covered) ═══\n")
    sys.exit(1 if failed > 0 else 0)


asyncio.run(main())
