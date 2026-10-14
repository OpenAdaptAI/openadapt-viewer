"""Tests for filter components."""

from openadapt_viewer.components import filter_dropdown


class TestFilterDropdownAllOption:
    """The catch-all option names the plural of the label."""

    def test_regular_plural(self):
        html = filter_dropdown("domain", "Domain", ["office"])

        assert '<option value="">All Domains</option>' in html

    def test_label_ending_in_s(self):
        html = filter_dropdown("status", "Status", ["passed", "failed"])

        assert '<option value="">All Statuses</option>' in html
        assert "Statuss" not in html
