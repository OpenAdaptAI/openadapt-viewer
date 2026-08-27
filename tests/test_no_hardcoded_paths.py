"""Guard against absolute developer paths in tracked code.

This is a public repository. A path like ``/Users/<someone>/oa/src/...`` baked
into shipped code breaks that code for every other user, and it leaks the
directory layout of the machine it was written on.

The failure this catches is real: ``real_data_loader.py`` shipped a default
capture path under one developer's home directory, so ``openadapt-viewer
benchmark`` raised FileNotFoundError for everyone else.

Markdown is deliberately out of scope here. Roughly 50 status documents at the
repository root still carry these paths; they are prose, not code, and cleaning
them up is a separate change.
"""

from __future__ import annotations

import subprocess
from pathlib import Path

REPO_ROOT = Path(__file__).parent.parent

# Extensions that hold code or code-adjacent configuration.
CODE_SUFFIXES = {".py", ".sh", ".html", ".js", ".css", ".json", ".yml", ".yaml", ".toml"}

# Absolute home-directory prefixes that must never appear in tracked code.
FORBIDDEN_PREFIXES = ("/Users/", "/home/")

# Known offenders fixed in PR #13 (fix/screenshot-workflow-honesty), which was
# open when this guard landed. Delete these two entries once #13 merges; the
# test then covers the whole tree with no exceptions.
ALLOWLIST = {
    "scripts/generate_for_web.sh",
    "scripts/generate_readme_screenshots.py",
}

# This file necessarily spells out the prefixes it bans, so it always matches
# itself. Skipping it by path keeps the check honest for every other file.
SELF = "tests/test_no_hardcoded_paths.py"


def _tracked_code_files() -> list[str]:
    """List tracked files whose extension marks them as code."""
    result = subprocess.run(
        ["git", "ls-files"],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        check=True,
    )
    return [
        name
        for name in result.stdout.splitlines()
        if Path(name).suffix in CODE_SUFFIXES
    ]


def test_tracked_code_has_no_absolute_home_paths():
    """No tracked code file may hardcode an absolute home-directory path."""
    offenders: list[str] = []

    for name in _tracked_code_files():
        if name in ALLOWLIST or name == SELF:
            continue
        path = REPO_ROOT / name
        try:
            content = path.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError):
            continue
        for line_number, line in enumerate(content.splitlines(), start=1):
            if any(prefix in line for prefix in FORBIDDEN_PREFIXES):
                offenders.append(f"{name}:{line_number}: {line.strip()[:120]}")

    assert not offenders, (
        "Tracked code hardcodes absolute home-directory paths. Resolve the "
        "location from an environment variable with a repository-relative "
        "fallback instead.\n" + "\n".join(offenders)
    )


def test_allowlist_entries_still_exist():
    """The allowlist must not outlive the files it exempts.

    Without this, a renamed or deleted file leaves a stale exemption that
    silently widens the hole in the guard above.
    """
    missing = [
        name for name in ALLOWLIST | {SELF} if not (REPO_ROOT / name).exists()
    ]
    assert not missing, (
        f"ALLOWLIST names files that no longer exist: {missing}. "
        "Remove the stale entries."
    )
