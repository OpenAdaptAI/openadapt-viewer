"""Tests for HTML generation functionality."""

import pytest
import re
from pathlib import Path
import tempfile

from openadapt_viewer.viewers.benchmark import generate_benchmark_html, create_sample_data
from openadapt_viewer.core.html_builder import HTMLBuilder
from openadapt_viewer.core.types import BenchmarkRun, BenchmarkTask, TaskExecution, ExecutionStep


class TestGenerateBenchmarkHtml:
    """Tests for the generate_benchmark_html function."""

    def test_generate_html_with_run_data(self, sample_benchmark_run, temp_dir):
        """Test generating HTML with provided BenchmarkRun data."""
        output_path = temp_dir / "output.html"
        result = generate_benchmark_html(
            run_data=sample_benchmark_run,
            output_path=output_path,
        )

        assert result == str(output_path)
        assert output_path.exists()

        html_content = output_path.read_text()
        assert len(html_content) > 0

    def test_generate_html_creates_valid_html(self, sample_benchmark_run, temp_dir):
        """Test that generated HTML is valid."""
        output_path = temp_dir / "output.html"
        generate_benchmark_html(
            run_data=sample_benchmark_run,
            output_path=output_path,
        )

        html_content = output_path.read_text()

        # Check for essential HTML structure
        assert "<!DOCTYPE html>" in html_content
        assert "<html" in html_content
        assert "</html>" in html_content
        assert "<head>" in html_content
        assert "</head>" in html_content
        assert "<body" in html_content
        assert "</body>" in html_content
        assert "<title>" in html_content
        assert "</title>" in html_content

    def test_generate_html_contains_benchmark_name(self, sample_benchmark_run, temp_dir):
        """Test that HTML contains the benchmark name."""
        output_path = temp_dir / "output.html"
        generate_benchmark_html(
            run_data=sample_benchmark_run,
            output_path=output_path,
        )

        html_content = output_path.read_text()
        assert "Test Benchmark" in html_content

    def test_generate_html_contains_model_id(self, sample_benchmark_run, temp_dir):
        """Test that HTML contains the model ID."""
        output_path = temp_dir / "output.html"
        generate_benchmark_html(
            run_data=sample_benchmark_run,
            output_path=output_path,
        )

        html_content = output_path.read_text()
        assert "test-model-v1" in html_content

    def test_generate_html_contains_statistics(self, sample_benchmark_run, temp_dir):
        """Test that HTML contains task statistics."""
        output_path = temp_dir / "output.html"
        generate_benchmark_html(
            run_data=sample_benchmark_run,
            output_path=output_path,
        )

        html_content = output_path.read_text()

        # Should contain total tasks
        assert "Total Tasks" in html_content
        # Should contain pass/fail labels
        assert "Passed" in html_content or "Pass" in html_content
        assert "Failed" in html_content or "Fail" in html_content
        # Should contain success rate
        assert "Success Rate" in html_content

    def test_generate_html_contains_tasks_data(self, sample_benchmark_run, temp_dir):
        """Test that HTML contains task data in JSON format."""
        output_path = temp_dir / "output.html"
        generate_benchmark_html(
            run_data=sample_benchmark_run,
            output_path=output_path,
        )

        html_content = output_path.read_text()

        # Task IDs should be in the HTML (as part of JS data)
        assert "task_001" in html_content
        assert "task_002" in html_content
        assert "task_003" in html_content

    def test_generate_html_contains_domain_breakdown(self, sample_benchmark_run, temp_dir):
        """Test that HTML contains domain breakdown section."""
        output_path = temp_dir / "output.html"
        generate_benchmark_html(
            run_data=sample_benchmark_run,
            output_path=output_path,
        )

        html_content = output_path.read_text()

        # Domain breakdown should be present
        assert "Results by Domain" in html_content
        # Domains from fixture
        assert "office" in html_content.lower()
        assert "browser" in html_content.lower()

    def test_generate_html_includes_alpine_js(self, sample_benchmark_run, temp_dir):
        """Test that HTML includes Alpine.js for interactivity."""
        output_path = temp_dir / "output.html"
        generate_benchmark_html(
            run_data=sample_benchmark_run,
            output_path=output_path,
        )

        html_content = output_path.read_text()

        # Alpine.js should be loaded
        assert "alpinejs" in html_content.lower() or "alpine" in html_content.lower()

    def test_generate_html_includes_tailwind(self, sample_benchmark_run, temp_dir):
        """Test that HTML includes Tailwind CSS."""
        output_path = temp_dir / "output.html"
        generate_benchmark_html(
            run_data=sample_benchmark_run,
            output_path=output_path,
        )

        html_content = output_path.read_text()

        # Tailwind should be loaded
        assert "tailwindcss" in html_content.lower() or "tailwind" in html_content.lower()

    def test_generate_html_with_sample_data(self, temp_dir):
        """Test generating HTML with automatically created sample data."""
        output_path = temp_dir / "sample_output.html"
        result = generate_benchmark_html(
            output_path=output_path,
        )

        assert result == str(output_path)
        assert output_path.exists()

        html_content = output_path.read_text()
        assert "Sample Benchmark" in html_content
        assert "sample-agent-v1" in html_content

    def test_generate_html_creates_parent_directories(self, temp_dir):
        """Test that output directory is created if it doesn't exist."""
        output_path = temp_dir / "nested" / "deep" / "output.html"
        run = create_sample_data(num_tasks=1)

        generate_benchmark_html(
            run_data=run,
            output_path=output_path,
        )

        assert output_path.exists()

    def test_generate_html_returns_path_as_string(self, sample_benchmark_run, temp_dir):
        """Test that the function returns the output path as a string."""
        output_path = temp_dir / "output.html"
        result = generate_benchmark_html(
            run_data=sample_benchmark_run,
            output_path=output_path,
        )

        assert isinstance(result, str)
        assert result == str(output_path)

    def test_generate_html_with_path_string(self, sample_benchmark_run, temp_dir):
        """Test generating HTML with output path as string."""
        output_path = str(temp_dir / "string_path_output.html")
        result = generate_benchmark_html(
            run_data=sample_benchmark_run,
            output_path=output_path,
        )

        assert result == output_path
        assert Path(output_path).exists()

    def test_generate_html_contains_playback_controls(self, sample_benchmark_run, temp_dir):
        """Test that HTML contains step playback controls."""
        output_path = temp_dir / "output.html"
        generate_benchmark_html(
            run_data=sample_benchmark_run,
            output_path=output_path,
        )

        html_content = output_path.read_text()

        # Playback controls
        assert "Prev" in html_content
        assert "Next" in html_content
        assert "Play" in html_content

    def test_generate_html_contains_filter_controls(self, sample_benchmark_run, temp_dir):
        """Test that HTML contains filter controls."""
        output_path = temp_dir / "output.html"
        generate_benchmark_html(
            run_data=sample_benchmark_run,
            output_path=output_path,
        )

        html_content = output_path.read_text()

        # Filter controls
        assert "All Domains" in html_content
        assert "filterDomain" in html_content
        assert "filterStatus" in html_content

    def test_generate_html_empty_run(self, temp_dir):
        """Test generating HTML with an empty benchmark run."""
        empty_run = BenchmarkRun(
            run_id="empty",
            benchmark_name="Empty Run",
            model_id="none",
        )

        output_path = temp_dir / "empty_output.html"
        generate_benchmark_html(
            run_data=empty_run,
            output_path=output_path,
        )

        assert output_path.exists()
        html_content = output_path.read_text()
        assert "Empty Run" in html_content


class TestHtmlBuilder:
    """Tests for the HTMLBuilder class."""

    def test_html_builder_creation(self):
        """Test creating an HTMLBuilder instance."""
        builder = HTMLBuilder()
        assert builder is not None
        assert builder.env is not None

    def test_html_builder_custom_filters(self):
        """Test that custom filters are registered."""
        builder = HTMLBuilder()
        filters = builder.env.filters

        assert "tojson_safe" in filters
        assert "format_duration" in filters
        assert "format_percent" in filters

    def test_tojson_safe_filter(self):
        """Test the tojson_safe filter escapes script tags."""
        result = HTMLBuilder._tojson_safe("</script>")
        assert "<\\/script>" in result
        assert "</script>" not in result

    def test_tojson_safe_filter_with_dict(self):
        """Test the tojson_safe filter with a dictionary."""
        data = {"key": "value", "nested": {"inner": "data"}}
        result = HTMLBuilder._tojson_safe(data)
        assert '"key"' in result
        assert '"value"' in result
        assert '"nested"' in result

    def test_format_duration_seconds(self):
        """Test format_duration with seconds only."""
        assert HTMLBuilder._format_duration(30) == "30s"
        assert HTMLBuilder._format_duration(59) == "59s"

    def test_format_duration_minutes(self):
        """Test format_duration with minutes."""
        assert HTMLBuilder._format_duration(60) == "1m 0s"
        assert HTMLBuilder._format_duration(90) == "1m 30s"
        assert HTMLBuilder._format_duration(3599) == "59m 59s"

    def test_format_duration_hours(self):
        """Test format_duration with hours."""
        assert HTMLBuilder._format_duration(3600) == "1h 0m"
        assert HTMLBuilder._format_duration(3661) == "1h 1m"
        assert HTMLBuilder._format_duration(7200) == "2h 0m"

    def test_format_duration_none(self):
        """Test format_duration with None."""
        assert HTMLBuilder._format_duration(None) == "N/A"

    def test_format_percent(self):
        """Test format_percent filter."""
        assert HTMLBuilder._format_percent(0.5) == "50.0%"
        assert HTMLBuilder._format_percent(0.333) == "33.3%"
        assert HTMLBuilder._format_percent(1.0) == "100.0%"
        assert HTMLBuilder._format_percent(0.0) == "0.0%"

    def test_format_percent_decimals(self):
        """Test format_percent with custom decimal places."""
        assert HTMLBuilder._format_percent(0.333, decimals=2) == "33.30%"
        assert HTMLBuilder._format_percent(0.333, decimals=0) == "33%"

    def test_format_percent_none(self):
        """Test format_percent with None."""
        assert HTMLBuilder._format_percent(None) == "N/A"

    def test_render_inline(self):
        """Test rendering an inline template."""
        builder = HTMLBuilder()
        template = "<h1>{{ title }}</h1>"
        result = builder.render_inline(template, title="Test Title")

        assert "<h1>Test Title</h1>" in result

    def test_render_inline_with_filters(self):
        """Test rendering an inline template with custom filters."""
        builder = HTMLBuilder()
        template = "<span>{{ rate | format_percent }}</span>"
        result = builder.render_inline(template, rate=0.75)

        assert "75.0%" in result

    def test_render_to_file(self, temp_dir):
        """Test rendering a template to a file."""
        builder = HTMLBuilder()
        output_path = temp_dir / "rendered.html"

        # We can't use render_template without actual template files,
        # but we can test render_inline and manual file writing
        template = "<!DOCTYPE html><html><body>{{ content }}</body></html>"
        html = builder.render_inline(template, content="Hello World")

        # Write manually since we don't have actual template files
        output_path.write_text(html)

        assert output_path.exists()
        assert "Hello World" in output_path.read_text()


class TestHtmlValidation:
    """Tests for HTML output validation."""

    def test_html_has_proper_encoding(self, sample_benchmark_run, temp_dir):
        """Test that HTML has proper UTF-8 encoding declaration."""
        output_path = temp_dir / "output.html"
        generate_benchmark_html(
            run_data=sample_benchmark_run,
            output_path=output_path,
        )

        html_content = output_path.read_text()
        assert 'charset="UTF-8"' in html_content or "charset=UTF-8" in html_content

    def test_html_has_viewport_meta(self, sample_benchmark_run, temp_dir):
        """Test that HTML has viewport meta tag for responsiveness."""
        output_path = temp_dir / "output.html"
        generate_benchmark_html(
            run_data=sample_benchmark_run,
            output_path=output_path,
        )

        html_content = output_path.read_text()
        assert "viewport" in html_content

    def test_html_has_dark_mode_support(self, sample_benchmark_run, temp_dir):
        """Test that HTML has dark mode support."""
        output_path = temp_dir / "output.html"
        generate_benchmark_html(
            run_data=sample_benchmark_run,
            output_path=output_path,
        )

        html_content = output_path.read_text()
        # Check for dark mode class references
        assert "dark:" in html_content
        assert "darkMode" in html_content

    def test_html_has_footer_attribution(self, sample_benchmark_run, temp_dir):
        """Test that HTML has footer with openadapt-viewer attribution."""
        output_path = temp_dir / "output.html"
        generate_benchmark_html(
            run_data=sample_benchmark_run,
            output_path=output_path,
        )

        html_content = output_path.read_text()
        assert "openadapt-viewer" in html_content

    def test_html_json_data_properly_embedded(self, sample_benchmark_run, temp_dir):
        """Test that task data is properly embedded as JSON in the HTML."""
        output_path = temp_dir / "output.html"
        generate_benchmark_html(
            run_data=sample_benchmark_run,
            output_path=output_path,
        )

        html_content = output_path.read_text()

        # Check that the tasks array is properly formatted
        assert "tasks:" in html_content

        # Ensure no raw Python objects leaked through
        assert "<class '" not in html_content
        assert "datetime.datetime" not in html_content

    def test_html_script_tags_balanced(self, sample_benchmark_run, temp_dir):
        """Test that HTML has balanced script tags."""
        output_path = temp_dir / "output.html"
        generate_benchmark_html(
            run_data=sample_benchmark_run,
            output_path=output_path,
        )

        html_content = output_path.read_text()

        # Count opening and closing script tags
        open_count = html_content.count("<script")
        close_count = html_content.count("</script>")

        assert open_count == close_count

    def test_html_no_xss_vulnerability(self, temp_dir):
        """Test that HTML properly escapes potentially dangerous content."""
        # Create a run with potentially dangerous content
        dangerous_run = BenchmarkRun(
            run_id="test",
            benchmark_name="<script>alert('xss')</script>",
            model_id="</script><script>evil()</script>",
        )

        output_path = temp_dir / "output.html"
        generate_benchmark_html(
            run_data=dangerous_run,
            output_path=output_path,
        )

        html_content = output_path.read_text()

        # The dangerous strings should be escaped
        # Either HTML-escaped or JSON-escaped
        assert "alert('xss')" not in html_content or "&lt;script&gt;" in html_content or "<\\/script>" in html_content
