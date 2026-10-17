"""A ``--standalone`` benchmark report must run Alpine.js without the network.

Adapted from corner123's tests in OpenAdaptAI/openadapt-viewer#23.
"""

from __future__ import annotations

import base64
import shutil

import pytest

from openadapt_viewer.builders import PageBuilder
from openadapt_viewer.viewers.benchmark import generate_benchmark_html

PNG = base64.b64decode(
    "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg=="
)
CDN = "cdn.jsdelivr.net/npm/alpinejs"


def test_standalone_report_inlines_alpine(sample_benchmark_run, tmp_path):
    output = tmp_path / "report.html"
    generate_benchmark_html(run_data=sample_benchmark_run, output_path=output, standalone=True)

    html = output.read_text(encoding="utf-8")
    assert CDN not in html
    assert "<!-- Alpine.js 3.17.4" in html
    assert "Caleb Porzio" in html  # MIT notice travels with the bundled copy


def test_regular_report_keeps_the_cdn(sample_benchmark_run, tmp_path):
    output = tmp_path / "report.html"
    generate_benchmark_html(run_data=sample_benchmark_run, output_path=output, standalone=False)

    html = output.read_text(encoding="utf-8")
    assert CDN in html
    assert "<!-- Alpine.js 3.17.4" not in html


def test_inline_alpine_runs_after_page_handlers():
    html = PageBuilder(title="t", include_alpine=True, inline_alpine=True)
    html.add_script("document.addEventListener('alpine:init', () => {});")
    rendered = html.render()
    assert rendered.index("alpine:init") < rendered.index("<!-- Alpine.js 3.17.4")


@pytest.mark.playwright
def test_standalone_report_works_offline_after_move(sample_benchmark_run, tmp_path):
    sync_api = pytest.importorskip("playwright.sync_api")
    screenshot = tmp_path / "step.png"
    screenshot.write_bytes(PNG)
    sample_benchmark_run.executions[0].steps[0].screenshot_path = str(screenshot)

    original = tmp_path / "original" / "report.html"
    generate_benchmark_html(run_data=sample_benchmark_run, output_path=original, standalone=True)
    moved = tmp_path / "moved" / "report.html"
    moved.parent.mkdir()
    shutil.move(original, moved)
    screenshot.unlink()

    with sync_api.sync_playwright() as p:
        try:
            browser = p.chromium.launch(headless=True)
        except sync_api.Error as e:  # browser binary not installed on this host
            pytest.skip(f"Chromium not available: {e}")
        page = browser.new_page()
        page.route(
            "**/*",
            lambda route: route.abort()
            if route.request.url.startswith(("http:", "https:"))
            else route.continue_(),
        )
        page.goto(moved.as_uri())

        assert page.evaluate("typeof Alpine") == "object"
        sync_api.expect(page.locator(".oa-list-item")).to_have_count(
            len(sample_benchmark_run.executions)
        )
        page.locator(".oa-list-item").first.click()
        image = page.locator(".screenshot-container img").first
        assert image.is_visible()
        assert image.evaluate("el => el.complete && el.naturalWidth > 0")
        browser.close()
