"""Measure, in a real browser, where screenshot_display draws its overlays.

The string tests in ``tests/test_components/test_screenshot.py`` check the
markup. This checks the geometry: a box given as fractions of the image must
cover exactly that part of the rendered image, both when the image is
letterboxed in a fixed container and when it scales down to a phone-width
page. Before the fix, a box at x=0.25 on a letterboxed 1280x800 frame landed
at x=0.083 with no border at all.
"""

from __future__ import annotations

import pytest
from PIL import Image

from openadapt_viewer.builders import PageBuilder
from openadapt_viewer.components import screenshot_display

BOX = {"type": "box", "x": 0.25, "y": 0.5, "width": 0.25, "height": 0.125}
CLICK = {"type": "click", "x": 0.75, "y": 0.25}

MEASURE = """() => {
  const img = document.querySelector('.oa-screenshot-image').getBoundingClientRect();
  const rel = (el) => {
    const r = el.getBoundingClientRect();
    return {
      x: (r.left - img.left) / img.width,
      y: (r.top - img.top) / img.height,
      w: r.width / img.width,
      h: r.height / img.height,
      cx: (r.left + r.width / 2 - img.left) / img.width,
      cy: (r.top + r.height / 2 - img.top) / img.height,
    };
  };
  const box = document.querySelector('.oa-overlay-box');
  return {
    box: rel(box),
    click: rel(document.querySelector('.oa-overlay-click')),
    border: getComputedStyle(box).borderTopWidth,
    imgWidth: img.width,
    pageWidth: document.documentElement.scrollWidth,
  };
}"""


@pytest.fixture(scope="module")
def browser():
    sync_api = pytest.importorskip("playwright.sync_api")
    with sync_api.sync_playwright() as p:
        try:
            b = p.chromium.launch()
        except sync_api.Error as e:  # browser binary not installed on this host
            pytest.skip(f"Chromium not available: {e}")
        yield b
        b.close()


def _render(tmp_path, **kwargs):
    image = tmp_path / "frame.png"
    Image.new("RGB", (1280, 800), "white").save(image)
    page = PageBuilder(title="overlay geometry", include_alpine=False)
    page.add_section(
        screenshot_display(str(image), overlays=[BOX, CLICK], embed_image=True, **kwargs)
    )
    return page.render_to_file(tmp_path / "page.html")


def _assert_on_target(m):
    tol = 0.005
    assert m["box"]["x"] == pytest.approx(0.25, abs=tol)
    assert m["box"]["y"] == pytest.approx(0.5, abs=tol)
    assert m["box"]["w"] == pytest.approx(0.25, abs=tol)
    assert m["box"]["h"] == pytest.approx(0.125, abs=tol)
    assert m["click"]["cx"] == pytest.approx(0.75, abs=tol)
    assert m["click"]["cy"] == pytest.approx(0.25, abs=tol)
    assert m["border"] != "0px"


def test_box_lands_on_a_letterboxed_image(browser, tmp_path):
    """800x450 container, 16:10 image: the image is pillarboxed to 720x450."""
    html = _render(tmp_path, width=800, height=450)
    page = browser.new_page(viewport={"width": 1200, "height": 900})
    page.goto(html.as_uri())
    m = page.evaluate(MEASURE)
    page.close()
    assert m["imgWidth"] == pytest.approx(720, abs=1)
    _assert_on_target(m)


def test_fluid_box_lands_on_a_phone_width_page(browser, tmp_path):
    """width=None, height=None at 390 px: scales down, no sideways scroll."""
    html = _render(tmp_path, width=None, height=None)
    page = browser.new_page(viewport={"width": 390, "height": 844})
    page.goto(html.as_uri())
    m = page.evaluate(MEASURE)
    page.close()
    assert m["pageWidth"] <= 390
    assert m["imgWidth"] < 390
    _assert_on_target(m)
