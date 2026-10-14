"""Tests for PageBuilder's theme handling."""

import re

from openadapt_viewer.builders import PageBuilder


def _body_tag(html: str) -> str:
    match = re.search(r"<body[^>]*>", html)
    assert match, "rendered page has no <body> tag"
    return match.group(0)


class TestDarkMode:
    """``dark_mode`` picks the theme the page opens in.

    The argument used to be stored and never read, so ``dark_mode=False``
    rendered the same dark page as the default.
    """

    def test_default_renders_dark(self):
        html = PageBuilder(title="t").render()

        assert "oa-light" not in _body_tag(html)

    def test_dark_mode_false_renders_light(self):
        html = PageBuilder(title="t", dark_mode=False).render()

        assert 'class="oa-light"' in _body_tag(html)

    def test_the_light_class_is_defined_in_the_page(self):
        """The class on <body> must have CSS behind it, or light mode is a no-op."""
        html = PageBuilder(title="t", dark_mode=False).render()

        assert ".oa-light" in html

    def test_the_header_toggle_flips_the_same_class(self):
        """The toggle must work from either starting theme."""
        for dark_mode in (True, False):
            builder = PageBuilder(title="t", dark_mode=dark_mode)
            builder.add_header(title="t")

            assert "document.body.classList.toggle('oa-light')" in builder.render()
