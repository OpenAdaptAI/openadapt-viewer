"""Locating the recordings openadapt-capture commits, for tests to read.

openadapt-capture commits two recordings under ``examples/captures``,
regenerated and byte-compared by its own CI. Tests that exercise a reader of
the recording format read those, rather than a database written here to match
this repository's idea of the schema. A test that builds its own input can only
prove the reader agrees with the test author, which is how the format drifted
unnoticed for six weeks.

Two readers depend on this now -- the catalog scanner and the benchmark
loader -- so the lookup lives here rather than in either test module.
"""

from __future__ import annotations

import os
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).parent.parent

#: Set by CI to the checked-out openadapt-capture's examples/captures.
EXAMPLES_ENV = "OPENADAPT_CAPTURE_EXAMPLES"

#: The recordings openadapt-capture commits, with what its specs declare.
REAL_RECORDINGS = ("demo_new", "turn-off-nightshift")


def examples_dir() -> Path | None:
    """Return the directory holding the committed example recordings, or None.

    Honours ``$OPENADAPT_CAPTURE_EXAMPLES`` first, then looks for an
    openadapt-capture checkout beside this one. No absolute path is written
    here: this repository is public and one developer's home directory is not
    a location any other user has.

    Returns:
        The directory, or None when neither source is present.
    """
    named = os.environ.get(EXAMPLES_ENV)
    if named:
        return Path(named).expanduser()

    sibling = REPO_ROOT.parent / "openadapt-capture" / "examples" / "captures"
    return sibling if sibling.is_dir() else None


def require_examples() -> Path:
    """Return the examples directory, skipping or failing with a reason.

    Returns:
        The directory holding the committed example recordings.
    """
    directory = examples_dir()
    if directory is None:
        pytest.skip(
            "No openadapt-capture checkout found. Clone it beside this "
            f"repository, or set ${EXAMPLES_ENV} to its examples/captures."
        )
    if not directory.is_dir():
        # The variable was set on purpose, so an absent directory is an error
        # in the caller's setup, not a reason to quietly pass.
        pytest.fail(f"${EXAMPLES_ENV} names {directory}, which is not a directory")
    missing = [
        name
        for name in REAL_RECORDINGS
        if not (directory / name / "recording.db").is_file()
    ]
    if missing:
        pytest.fail(f"{directory} is missing recording.db for: {', '.join(missing)}")
    return directory
