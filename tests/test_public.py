#!/usr/bin/env python3
"""Test public endpoints against live API (no auth needed)."""

import asyncio
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from laddro_career import Laddro

client = Laddro()
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
    print("\n— Public endpoint tests (no auth, hitting api.laddro.com) —\n")

    async def test_list_templates():
        templates = await client.templates.list()
        assert len(templates) >= 20, f"expected 20+, got {len(templates)}"
        assert templates[0].id
        print(f"    → {len(templates)} templates")

    async def test_get_template():
        detail = await client.templates.get("GRAPHITE")
        assert detail.id == "GRAPHITE"
        assert len(detail.available_colors) > 0
        assert len(detail.available_fonts) > 0
        print(f"    → {len(detail.available_colors)} colors, {len(detail.available_fonts)} fonts")

    async def test_list_fonts():
        fonts = await client.templates.fonts()
        assert len(fonts) >= 20, f"expected 20+, got {len(fonts)}"
        print(f"    → {len(fonts)} fonts")

    async def test_list_languages():
        languages = await client.templates.languages()
        assert len(languages) == 14, f"expected 14, got {len(languages)}"
        print(f"    → {len(languages)} languages")

    async def test_list_models():
        models = await client.templates.models()
        assert len(models) >= 10, f"expected 10+, got {len(models)}"
        names = [m.name for m in models]
        assert "OpenAI" in names
        assert "Anthropic" in names
        print(f"    → {len(models)} providers")

    await test("list templates", test_list_templates)
    await test("get template detail", test_get_template)
    await test("list fonts", test_list_fonts)
    await test("list languages", test_list_languages)
    await test("list models", test_list_models)

    print(f"\n— Results: {passed} passed, {failed} failed —\n")
    sys.exit(1 if failed > 0 else 0)


asyncio.run(main())
