"""The standalone benchmark report must work after its source files are removed."""

import base64
import shutil
import sys

import pytest
from playwright.sync_api import Error as PlaywrightError
from playwright.sync_api import expect, sync_playwright

from openadapt_viewer.cli import main
from openadapt_viewer.viewers.benchmark import generate_benchmark_html

PNG = base64.b64decode(
    "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg=="
)


@pytest.mark.playwright
def test_standalone_report_works_offline_after_move(sample_benchmark_run, tmp_path):
    screenshot = tmp_path / "step.png"
    screenshot.write_bytes(PNG)
    sample_benchmark_run.executions[0].steps[0].screenshot_path = str(screenshot)

    original = tmp_path / "original" / "report.html"
    generate_benchmark_html(
        run_data=sample_benchmark_run,
        output_path=original,
        standalone=True,
    )
    moved = tmp_path / "moved" / "report.html"
    moved.parent.mkdir()
    shutil.move(original, moved)
    screenshot.unlink()

    with sync_playwright() as playwright:
        try:
            browser = playwright.chromium.launch(headless=True)
        except PlaywrightError as exc:
            if "Executable doesn't exist" in str(exc):
                pytest.skip("Playwright Chromium is not installed")
            raise
        page = browser.new_page()
        page.route(
            "**/*",
            lambda route: route.abort()
            if route.request.url.startswith(("http:", "https:"))
            else route.continue_(),
        )
        page.goto(moved.as_uri())

        assert page.evaluate("typeof Alpine") == "object"
        expect(page.locator(".oa-list-item")).to_have_count(3)
        page.locator(".oa-list-item").first.click()
        image = page.locator(".screenshot-container img")
        assert image.is_visible()
        assert image.evaluate("element => element.complete && element.naturalWidth > 0")
        browser.close()


def test_standalone_report_rejects_missing_screenshot(sample_benchmark_run, tmp_path):
    sample_benchmark_run.executions[0].steps[0].screenshot_path = str(tmp_path / "missing.png")

    with pytest.raises(FileNotFoundError, match="missing.png"):
        generate_benchmark_html(
            run_data=sample_benchmark_run,
            output_path=tmp_path / "report.html",
            standalone=True,
        )


def test_standalone_resolves_screenshots_relative_to_data_dir(sample_benchmark_run, tmp_path):
    data_dir = tmp_path / "capture"
    screenshot = data_dir / "screenshots" / "step.png"
    screenshot.parent.mkdir(parents=True)
    screenshot.write_bytes(PNG)
    sample_benchmark_run.executions[0].steps[0].screenshot_path = "screenshots/step.png"

    output = tmp_path / "exports" / "report.html"
    generate_benchmark_html(
        data_path=data_dir,
        run_data=sample_benchmark_run,
        output_path=output,
        standalone=True,
    )

    html = output.read_text(encoding="utf-8")
    assert "data:image/png;base64," in html
    assert "screenshots/step.png" not in html


def test_standalone_cli_embeds_benchmark_screenshots(benchmark_data_dir, tmp_path, monkeypatch):
    screenshot = benchmark_data_dir / "tasks" / "task_001" / "screenshots" / "step_000.png"
    screenshot.write_bytes(PNG)
    output = tmp_path / "report.html"
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "openadapt-viewer",
            "benchmark",
            "--data",
            str(benchmark_data_dir),
            "--output",
            str(output),
            "--standalone",
        ],
    )

    main()

    html = output.read_text(encoding="utf-8")
    assert "data:image/png;base64," in html
    assert "cdn.jsdelivr.net" not in html
