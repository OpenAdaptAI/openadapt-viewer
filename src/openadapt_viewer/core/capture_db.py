"""Reading openadapt-capture recording databases, in either schema.

openadapt-capture changed its storage on 2026-07-17 (PR #28). The recorder now
writes ``recording.db``, a SQLAlchemy schema whose ``recording`` table stores a
start timestamp, ``monitor_width`` and ``monitor_height``. Recordings made
before that have ``capture.db``, a bespoke schema whose ``capture`` table stores
``started_at``, ``ended_at``, ``screen_width`` and ``screen_height``.

Both are normalised into :class:`CaptureMetadata` here, so callers work with one
shape and no caller has to know which format it was handed. This module is the
single place that knows the difference; the benchmark loader and the recording
scanner both read through it.

Columns are introspected rather than assumed. ``recording.pixel_ratio`` is
declared in the openadapt-capture model but absent from recordings written
before it was added, because that migration is additive.
"""

from __future__ import annotations

import sqlite3
from dataclasses import dataclass
from pathlib import Path

#: Database written by the current recorder, one row per recording.
RECORDING_DB = "recording.db"

#: Database written before openadapt-capture PR #28 (2026-07-17).
LEGACY_CAPTURE_DB = "capture.db"

#: Tables whose newest timestamp bounds a recording. The recording table has no
#: end time of its own, so the last thing that happened during it is the end.
_END_TIME_TABLES = ("action_event", "screenshot", "window_event")

#: Where each schema keeps its events, for counting.
_EVENT_TABLES = {RECORDING_DB: "action_event", LEGACY_CAPTURE_DB: "events"}


@dataclass(frozen=True)
class CaptureMetadata:
    """Recording-level facts the viewer needs, independent of database schema."""

    recording_id: str
    started_at: float
    ended_at: float
    platform: str
    screen_width: int
    screen_height: int
    task_description: str | None
    pixel_ratio: float | None
    source_format: str

    @property
    def duration_seconds(self) -> float:
        """Length of the recording in seconds."""
        return self.ended_at - self.started_at


def find_recording_db(capture_path: Path) -> tuple[Path, str] | None:
    """Locate a recording database inside a capture directory.

    Prefers the current format when a directory somehow holds both.

    Args:
        capture_path: A recording directory.

    Returns:
        A ``(path, format)`` pair, or None if neither database is present.
    """
    for filename in (RECORDING_DB, LEGACY_CAPTURE_DB):
        candidate = capture_path / filename
        if candidate.exists():
            return candidate, filename
    return None


def _table_exists(conn: sqlite3.Connection, table: str) -> bool:
    """Report whether a table is present in the database."""
    row = conn.execute(
        "SELECT 1 FROM sqlite_master WHERE type = 'table' AND name = ?", (table,)
    ).fetchone()
    return row is not None


def _column_names(conn: sqlite3.Connection, table: str) -> set[str]:
    """Return the column names of a table."""
    return {row[1] for row in conn.execute(f"PRAGMA table_info({table})")}


def _optional(row: sqlite3.Row, column: str):
    """Return a column's value, or None when the schema predates the column."""
    return row[column] if column in row.keys() else None


def _derive_end_time(conn: sqlite3.Connection, started_at: float) -> float:
    """Return the timestamp of the last event in a recording.

    The ``recording`` table stores a start time and no end time, so the end is
    the newest timestamp across the event tables. Falls back to the start time
    for a recording that captured no events.

    Args:
        conn: An open connection to a recording database.
        started_at: The recording's start timestamp.

    Returns:
        The end timestamp, never earlier than ``started_at``.
    """
    latest = started_at
    for table in _END_TIME_TABLES:
        if not _table_exists(conn, table):
            continue
        if "timestamp" not in _column_names(conn, table):
            continue
        row = conn.execute(f"SELECT MAX(timestamp) FROM {table}").fetchone()
        if row and row[0] is not None:
            latest = max(latest, float(row[0]))
    return latest


def _read_recording_db(conn: sqlite3.Connection, db_path: Path) -> CaptureMetadata:
    """Read metadata from the current ``recording.db`` schema."""
    if not _table_exists(conn, "recording"):
        raise ValueError(
            f"{db_path} has no 'recording' table. It may be an unrelated SQLite "
            "file rather than an openadapt-capture recording."
        )

    row = conn.execute("SELECT * FROM recording ORDER BY id LIMIT 1").fetchone()
    if row is None:
        raise ValueError(f"No recording row found in {db_path}")

    started_at = float(row["timestamp"])
    return CaptureMetadata(
        recording_id=str(row["id"]),
        started_at=started_at,
        ended_at=_derive_end_time(conn, started_at),
        platform=row["platform"] or "unknown",
        screen_width=int(row["monitor_width"] or 0),
        screen_height=int(row["monitor_height"] or 0),
        task_description=_optional(row, "task_description"),
        pixel_ratio=_optional(row, "pixel_ratio"),
        source_format=RECORDING_DB,
    )


def _read_legacy_capture_db(conn: sqlite3.Connection, db_path: Path) -> CaptureMetadata:
    """Read metadata from the pre-PR-#28 ``capture.db`` schema."""
    if not _table_exists(conn, "capture"):
        raise ValueError(
            f"{db_path} has no 'capture' table. It may be an unrelated SQLite "
            "file rather than an openadapt-capture recording."
        )

    row = conn.execute("SELECT * FROM capture LIMIT 1").fetchone()
    if row is None:
        raise ValueError(f"No capture metadata found in {db_path}")

    started_at = float(row["started_at"])
    ended_at = _optional(row, "ended_at")
    return CaptureMetadata(
        recording_id=str(row["id"]),
        started_at=started_at,
        ended_at=float(ended_at) if ended_at is not None else started_at,
        platform=row["platform"] or "unknown",
        screen_width=int(row["screen_width"] or 0),
        screen_height=int(row["screen_height"] or 0),
        task_description=_optional(row, "task_description"),
        pixel_ratio=_optional(row, "pixel_ratio"),
        source_format=LEGACY_CAPTURE_DB,
    )


def read_capture_metadata(capture_path: Path) -> CaptureMetadata:
    """Read recording metadata from whichever database format is present.

    Args:
        capture_path: A recording directory.

    Returns:
        Normalised capture metadata.

    Raises:
        FileNotFoundError: If neither database is present.
        ValueError: If the database holds no usable recording row.
    """
    found = find_recording_db(capture_path)
    if found is None:
        raise FileNotFoundError(
            f"No recording database in {capture_path}. Expected {RECORDING_DB} "
            f"(current) or {LEGACY_CAPTURE_DB} (written before openadapt-capture "
            "PR #28)."
        )

    db_path, source_format = found
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    try:
        if source_format == RECORDING_DB:
            return _read_recording_db(conn, db_path)
        return _read_legacy_capture_db(conn, db_path)
    finally:
        conn.close()


def count_events(capture_path: Path) -> int | None:
    """Count the recorded events in a capture directory.

    The two schemas keep events in differently named tables: ``action_event``
    in the current one, ``events`` in the legacy one.

    Args:
        capture_path: A recording directory.

    Returns:
        The event count, or None if it cannot be determined.
    """
    found = find_recording_db(capture_path)
    if found is None:
        return None

    db_path, source_format = found
    table = _EVENT_TABLES[source_format]
    conn = sqlite3.connect(db_path)
    try:
        if not _table_exists(conn, table):
            return None
        row = conn.execute(f"SELECT COUNT(*) FROM {table}").fetchone()
        return int(row[0]) if row else None
    except sqlite3.Error:
        return None
    finally:
        conn.close()
