"""The reported version must be the installed one.

``openadapt_viewer.__version__`` was a hardcoded "0.1.0" that the release
workflow never touched, so 0.2.0 shipped reporting the wrong version.
"""

import subprocess
import sys
from importlib.metadata import version

import openadapt_viewer


def test_dunder_version_matches_package_metadata():
    assert openadapt_viewer.__version__ == version("openadapt-viewer")


def test_cli_version_flag_prints_the_package_version():
    result = subprocess.run(
        [sys.executable, "-m", "openadapt_viewer.cli", "--version"],
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0
    assert result.stdout.strip().endswith(version("openadapt-viewer"))
