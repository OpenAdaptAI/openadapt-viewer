"""Tests for segmentation viewer screenshot generation.

This test suite verifies that:
1. Screenshot generation script runs successfully
2. All expected screenshots are generated
3. Screenshots have valid content (not empty)
4. Metadata is generated correctly
5. CLI integration works properly
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).parent.parent
SCRIPT_PATH = REPO_ROOT / "scripts" / "generate_segmentation_screenshots.py"
VIEWER_PATH = REPO_ROOT / "segmentation_viewer.html"
TEST_DATA_PATH = REPO_ROOT / "test_episodes.json"


@pytest.fixture
def script_exists():
    """Verify the screenshot generation script exists."""
    assert SCRIPT_PATH.exists(), f"Script not found: {SCRIPT_PATH}"
    return SCRIPT_PATH


@pytest.fixture
def viewer_exists():
    """Verify the segmentation viewer HTML exists."""
    assert VIEWER_PATH.exists(), f"Viewer not found: {VIEWER_PATH}"
    return VIEWER_PATH


@pytest.fixture
def test_data_exists():
    """Verify test data exists."""
    assert TEST_DATA_PATH.exists(), f"Test data not found: {TEST_DATA_PATH}"
    return TEST_DATA_PATH


def test_script_exists(script_exists):
    """Test that the screenshot generation script exists."""
    assert script_exists.is_file()
    assert script_exists.suffix == ".py"


def test_script_has_shebang(script_exists):
    """Test that the script has a proper shebang."""
    content = script_exists.read_text()
    assert content.startswith("#!/usr/bin/env python3")


def test_script_imports():
    """Test that the script can be imported without errors."""
    try:
        # Add scripts directory to path
        sys.path.insert(0, str(REPO_ROOT / "scripts"))

        # Try importing the module (this checks syntax and import errors)
        import generate_segmentation_screenshots  # noqa: F401

        # Import successful
        assert True
    except ImportError as e:
        pytest.fail(f"Failed to import script: {e}")
    finally:
        # Clean up path
        if str(REPO_ROOT / "scripts") in sys.path:
            sys.path.remove(str(REPO_ROOT / "scripts"))


def test_dependency_check():
    """Test that dependency checking works."""
    result = subprocess.run(
        [sys.executable, str(SCRIPT_PATH), "--check-deps"],
        capture_output=True,
        text=True,
        timeout=10,
    )

    # Script should exit with 0 if playwright available, 1 if missing
    assert result.returncode in (0, 1), f"Unexpected exit code: {result.returncode}"


def test_help_message(script_exists):
    """Test that the script shows help message."""
    result = subprocess.run(
        [sys.executable, str(script_exists), "--help"],
        capture_output=True,
        text=True,
        timeout=10,
    )

    assert result.returncode == 0
    assert "Generate screenshots of segmentation viewer" in result.stdout
    assert "--output" in result.stdout
    assert "--viewer" in result.stdout
    assert "--test-data" in result.stdout
    assert "--skip-responsive" in result.stdout
    assert "--save-metadata" in result.stdout


def test_required_files_exist(viewer_exists, test_data_exists):
    """Test that required files exist."""
    assert viewer_exists.exists()
    assert test_data_exists.exists()


def test_test_data_valid_json(test_data_exists):
    """Test that test data is valid JSON."""
    with open(test_data_exists) as f:
        data = json.load(f)

    assert "episodes" in data
    assert len(data["episodes"]) > 0
    assert "recording_id" in data


@pytest.mark.slow
@pytest.mark.playwright
def test_screenshot_generation_desktop_only(tmp_path, viewer_exists, test_data_exists):
    """Test screenshot generation with desktop viewport only (fast test).

    This test verifies that:
    1. The script can run successfully
    2. Desktop screenshots are generated
    3. Screenshots are not empty

    Note: Requires playwright to be installed.
    Run: uv pip install playwright && uv run playwright install chromium
    """
    # Check if playwright is available
    try:
        from playwright.sync_api import sync_playwright  # noqa: F401
    except ImportError:
        pytest.skip("Playwright not installed")

    output_dir = tmp_path / "screenshots"
    output_dir.mkdir()

    result = subprocess.run(
        [
            sys.executable,
            str(SCRIPT_PATH),
            "--output",
            str(output_dir),
            "--viewer",
            str(viewer_exists),
            "--test-data",
            str(test_data_exists),
            "--skip-responsive",  # Skip responsive for faster test
        ],
        capture_output=True,
        text=True,
        timeout=60,
    )

    # Check output
    print("STDOUT:", result.stdout)
    print("STDERR:", result.stderr)

    # Script should succeed
    if result.returncode != 0:
        pytest.fail(
            f"Script failed with exit code {result.returncode}\n"
            f"STDOUT: {result.stdout}\n"
            f"STDERR: {result.stderr}"
        )

    # Verify screenshots were generated
    screenshots = list(output_dir.glob("*.png"))
    assert len(screenshots) > 0, "No screenshot files generated"

    # Check that we have expected desktop screenshots
    expected_prefixes = ["01_", "02_", "03_", "04_", "05_", "06_", "07_", "08_", "09_"]
    for prefix in expected_prefixes:
        matching = [s for s in screenshots if s.name.startswith(prefix)]
        assert len(matching) > 0, f"No screenshot with prefix '{prefix}' found"

    # Verify screenshots are not empty
    for screenshot in screenshots:
        size = screenshot.stat().st_size
        assert size > 10000, f"Screenshot {screenshot.name} is too small ({size} bytes)"


@pytest.mark.slow
@pytest.mark.playwright
def test_screenshot_generation_with_metadata(tmp_path, viewer_exists, test_data_exists):
    """Test screenshot generation with metadata output.

    This test verifies that:
    1. Metadata is generated when requested
    2. Metadata contains expected fields
    3. Screenshot paths in metadata are correct
    """
    # Check if playwright is available
    try:
        from playwright.sync_api import sync_playwright  # noqa: F401
    except ImportError:
        pytest.skip("Playwright not installed")

    output_dir = tmp_path / "screenshots"
    output_dir.mkdir()

    result = subprocess.run(
        [
            sys.executable,
            str(SCRIPT_PATH),
            "--output",
            str(output_dir),
            "--viewer",
            str(viewer_exists),
            "--test-data",
            str(test_data_exists),
            "--skip-responsive",
            "--save-metadata",
        ],
        capture_output=True,
        text=True,
        timeout=60,
    )

    # Check that script succeeded
    assert result.returncode == 0, f"Script failed: {result.stderr}"

    # Verify metadata file exists
    metadata_path = output_dir / "metadata.json"
    assert metadata_path.exists(), "Metadata file not generated"

    # Load and validate metadata
    with open(metadata_path) as f:
        metadata = json.load(f)

    # Check expected fields
    assert "generated_at" in metadata
    assert "viewer_path" in metadata
    assert "test_data_path" in metadata
    assert "output_dir" in metadata
    assert "screenshot_count" in metadata
    assert "screenshots" in metadata

    # Check screenshot count matches actual files
    screenshots = list(output_dir.glob("*.png"))
    assert metadata["screenshot_count"] == len(screenshots)

    # Check screenshots list in metadata
    assert len(metadata["screenshots"]) == len(screenshots)
    for screenshot_info in metadata["screenshots"]:
        assert "path" in screenshot_info
        assert "filename" in screenshot_info
        assert "size_bytes" in screenshot_info
        assert screenshot_info["size_bytes"] > 0


@pytest.mark.slow
@pytest.mark.playwright
def test_screenshot_generation_full(tmp_path, viewer_exists, test_data_exists):
    """Test full screenshot generation including responsive viewports.

    This is the comprehensive integration test that:
    1. Generates all screenshots (desktop + responsive)
    2. Verifies all expected screenshots exist
    3. Checks screenshot quality

    Note: This test is slower as it generates 13+ screenshots.
    """
    # Check if playwright is available
    try:
        from playwright.sync_api import sync_playwright  # noqa: F401
    except ImportError:
        pytest.skip("Playwright not installed")

    output_dir = tmp_path / "screenshots"
    output_dir.mkdir()

    result = subprocess.run(
        [
            sys.executable,
            str(SCRIPT_PATH),
            "--output",
            str(output_dir),
            "--viewer",
            str(viewer_exists),
            "--test-data",
            str(test_data_exists),
            # Don't skip responsive - test everything
        ],
        capture_output=True,
        text=True,
        timeout=120,  # Longer timeout for all screenshots
    )

    # Check output
    print("STDOUT:", result.stdout)
    print("STDERR:", result.stderr)

    # Script should succeed
    assert result.returncode == 0, f"Script failed: {result.stderr}"

    # Verify screenshots were generated
    screenshots = list(output_dir.glob("*.png"))
    assert len(screenshots) >= 13, f"Expected at least 13 screenshots, got {len(screenshots)}"

    # Check that we have expected screenshots
    expected_prefixes = [
        "01_",  # initial empty
        "02_",  # episodes loaded
        "03_",  # thumbnails
        "04_",  # details expanded
        "05_",  # key frames
        "06_",  # search empty
        "07_",  # search filtered
        "08_",  # recording filter
        "09_",  # full page
        "10_",  # tablet list
        "11_",  # tablet details
        "12_",  # mobile list
        "13_",  # mobile details
    ]

    for prefix in expected_prefixes:
        matching = [s for s in screenshots if s.name.startswith(prefix)]
        assert len(matching) > 0, f"No screenshot with prefix '{prefix}' found"


def test_error_handling_missing_viewer(tmp_path):
    """Test that the script handles missing viewer gracefully."""
    output_dir = tmp_path / "screenshots"
    output_dir.mkdir()

    result = subprocess.run(
        [
            sys.executable,
            str(SCRIPT_PATH),
            "--output",
            str(output_dir),
            "--viewer",
            "/nonexistent/viewer.html",
            "--test-data",
            str(TEST_DATA_PATH),
        ],
        capture_output=True,
        text=True,
        timeout=10,
    )

    # Script should fail gracefully
    assert result.returncode != 0
    # Check for error in either stdout or stderr
    output = result.stdout + result.stderr
    assert "Error" in output or "not found" in output.lower()


def test_error_handling_missing_test_data(tmp_path):
    """Test that the script handles missing test data gracefully."""
    output_dir = tmp_path / "screenshots"
    output_dir.mkdir()

    result = subprocess.run(
        [
            sys.executable,
            str(SCRIPT_PATH),
            "--output",
            str(output_dir),
            "--viewer",
            str(VIEWER_PATH),
            "--test-data",
            "/nonexistent/test_data.json",
        ],
        capture_output=True,
        text=True,
        timeout=10,
    )

    # Script should fail gracefully
    assert result.returncode != 0
    # Check for error in either stdout or stderr
    output = result.stdout + result.stderr
    assert "Error" in output or "not found" in output.lower()


def test_cli_integration():
    """Test that CLI integration works."""
    result = subprocess.run(
        [sys.executable, "-m", "openadapt_viewer.cli", "screenshots", "--help"],
        capture_output=True,
        text=True,
        timeout=10,
        cwd=str(REPO_ROOT / "src"),
    )

    # Check that screenshots command is available
    assert result.returncode == 0
    assert "screenshots" in result.stdout.lower()


def test_cli_segmentation_help():
    """Test that CLI segmentation screenshots help works."""
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "openadapt_viewer.cli",
            "screenshots",
            "segmentation",
            "--help",
        ],
        capture_output=True,
        text=True,
        timeout=10,
        cwd=str(REPO_ROOT / "src"),
    )

    # Check that segmentation command is available
    assert result.returncode == 0
    assert "segmentation" in result.stdout.lower()
    assert "--output" in result.stdout
    assert "--viewer" in result.stdout


@pytest.mark.slow
@pytest.mark.playwright
@pytest.mark.parametrize(
    "args",
    [
        ["--skip-responsive"],
        ["--save-metadata"],
    ],
)
def test_command_line_options(args, tmp_path):
    """Test that command-line options are accepted.

    Note: This test requires Playwright and will generate actual screenshots.
    """
    # Check if playwright is available
    try:
        from playwright.sync_api import sync_playwright  # noqa: F401
    except ImportError:
        pytest.skip("Playwright not installed")

    output_dir = tmp_path / "screenshots"
    output_dir.mkdir()

    result = subprocess.run(
        [
            sys.executable,
            str(SCRIPT_PATH),
            "--output",
            str(output_dir),
            "--viewer",
            str(VIEWER_PATH),
            "--test-data",
            str(TEST_DATA_PATH),
        ]
        + args,
        capture_output=True,
        text=True,
        timeout=120,  # Increased timeout for screenshot generation
    )

    # Should succeed with these options
    assert result.returncode == 0, f"Script failed: {result.stderr}"
