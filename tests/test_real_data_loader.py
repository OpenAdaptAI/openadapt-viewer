"""Tests for loading openadapt-capture recordings in both database formats.

The recorder writes ``recording.db``. Recordings made before openadapt-capture
PR #28 (2026-07-17) have ``capture.db`` instead, with a different table,
different column names, and an explicit end time the new schema does not store.
The loader has to read both.

Every fixture here is synthetic. Real recordings are local data that never ships
with this repository, so tests that depend on one cannot run in CI.
"""

from __future__ import annotations

import json
import sqlite3
from pathlib import Path

import pytest

from openadapt_viewer.viewers.benchmark.real_data_loader import (
    LEGACY_CAPTURE_DB,
    RECORDING_DB,
    load_real_capture_data,
    read_capture_metadata,
)

STARTED_AT = 1765672628.0
LAST_EVENT_AT = 1765672688.0
PLATFORM = "darwin"
WIDTH, HEIGHT = 1920, 1080


def _write_episodes(capture_dir: Path, *, frame_prefix: str) -> None:
    """Write an episodes.json with two key frames.

    Args:
        capture_dir: The recording directory to write into.
        frame_prefix: Prefix for each key frame path, so a test can exercise
            both the checkout-relative and the directory-relative forms.
    """
    (capture_dir / "screenshots").mkdir(exist_ok=True)
    episodes = {
        "recording_id": "test-recording",
        "recording_name": "Test Recording",
        "llm_model": "test-model",
        "processing_timestamp": "2026-01-01T00:00:00Z",
        "coverage": 1.0,
        "avg_confidence": 0.9,
        "episodes": [
            {
                "episode_id": "episode_001",
                "name": "Do the thing",
                "description": "A synthetic episode",
                "application": "system",
                "start_time": 0.0,
                "end_time": 30.0,
                "duration": 30.0,
                "steps": ["First step", "Second step"],
                "boundary_confidence": 0.8,
                "coherence_score": 0.7,
                "screenshots": {
                    "key_frames": [
                        {"frame_index": 0, "path": f"{frame_prefix}step_0.png"},
                        {"frame_index": 2, "path": f"{frame_prefix}step_2.png"},
                    ]
                },
            }
        ],
    }
    (capture_dir / "episodes.json").write_text(json.dumps(episodes))


def _make_recording_db(capture_dir: Path, *, with_events: bool = True) -> Path:
    """Create a recording.db in the current schema.

    Deliberately omits ``pixel_ratio``. That column exists in the
    openadapt-capture model but not in recordings written before it was added,
    because that migration is additive, so the loader must not require it.
    """
    db_path = capture_dir / RECORDING_DB
    conn = sqlite3.connect(db_path)
    conn.execute(
        """
        CREATE TABLE recording (
            id INTEGER NOT NULL PRIMARY KEY,
            timestamp NUMERIC(10, 2),
            monitor_width INTEGER,
            monitor_height INTEGER,
            double_click_interval_seconds NUMERIC,
            double_click_distance_pixels NUMERIC,
            platform VARCHAR,
            task_description VARCHAR,
            video_start_time NUMERIC(10, 2),
            config JSON,
            original_recording_id INTEGER
        )
        """
    )
    conn.execute(
        "INSERT INTO recording (id, timestamp, monitor_width, monitor_height, "
        "platform, task_description) VALUES (?, ?, ?, ?, ?, ?)",
        (1, STARTED_AT, WIDTH, HEIGHT, PLATFORM, "Turn off night shift"),
    )
    conn.execute("CREATE TABLE action_event (id INTEGER PRIMARY KEY, timestamp NUMERIC)")
    conn.execute("CREATE TABLE screenshot (id INTEGER PRIMARY KEY, timestamp NUMERIC)")
    if with_events:
        conn.execute("INSERT INTO action_event (timestamp) VALUES (?)", (STARTED_AT + 10,))
        conn.execute("INSERT INTO action_event (timestamp) VALUES (?)", (LAST_EVENT_AT,))
        conn.execute("INSERT INTO screenshot (timestamp) VALUES (?)", (LAST_EVENT_AT - 5,))
    conn.commit()
    conn.close()
    return db_path


def _make_legacy_capture_db(capture_dir: Path) -> Path:
    """Create a capture.db in the pre-PR-#28 schema."""
    db_path = capture_dir / LEGACY_CAPTURE_DB
    conn = sqlite3.connect(db_path)
    conn.execute(
        """
        CREATE TABLE capture (
            id TEXT PRIMARY KEY,
            started_at REAL NOT NULL,
            ended_at REAL,
            platform TEXT NOT NULL,
            screen_width INTEGER NOT NULL,
            screen_height INTEGER NOT NULL,
            pixel_ratio REAL DEFAULT 1.0,
            task_description TEXT,
            metadata JSON
        )
        """
    )
    conn.execute(
        "INSERT INTO capture (id, started_at, ended_at, platform, screen_width, "
        "screen_height) VALUES (?, ?, ?, ?, ?, ?)",
        ("31807990", STARTED_AT, LAST_EVENT_AT, PLATFORM, WIDTH, HEIGHT),
    )
    conn.commit()
    conn.close()
    return db_path


@pytest.fixture
def recording_dir(tmp_path):
    """A recording directory in the current recording.db format."""
    capture_dir = tmp_path / "openadapt-capture" / "my-recording"
    capture_dir.mkdir(parents=True)
    _make_recording_db(capture_dir)
    _write_episodes(capture_dir, frame_prefix="screenshots/")
    return capture_dir


@pytest.fixture
def legacy_dir(tmp_path):
    """A recording directory in the legacy capture.db format."""
    capture_dir = tmp_path / "openadapt-capture" / "legacy-recording"
    capture_dir.mkdir(parents=True)
    _make_legacy_capture_db(capture_dir)
    _write_episodes(capture_dir, frame_prefix="screenshots/")
    return capture_dir


class TestReadCaptureMetadata:
    """Reading recording-level metadata out of each schema."""

    def test_reads_current_recording_db(self, recording_dir):
        meta = read_capture_metadata(recording_dir)
        assert meta.source_format == RECORDING_DB
        assert meta.started_at == STARTED_AT
        assert meta.platform == PLATFORM
        assert (meta.screen_width, meta.screen_height) == (WIDTH, HEIGHT)
        assert meta.task_description == "Turn off night shift"

    def test_reads_legacy_capture_db(self, legacy_dir):
        meta = read_capture_metadata(legacy_dir)
        assert meta.source_format == LEGACY_CAPTURE_DB
        assert meta.started_at == STARTED_AT
        assert meta.ended_at == LAST_EVENT_AT
        assert meta.platform == PLATFORM
        assert (meta.screen_width, meta.screen_height) == (WIDTH, HEIGHT)

    def test_both_schemas_agree(self, recording_dir, legacy_dir):
        """The two formats describe the same recording identically."""
        current = read_capture_metadata(recording_dir)
        legacy = read_capture_metadata(legacy_dir)
        assert current.started_at == legacy.started_at
        assert current.ended_at == legacy.ended_at
        assert current.platform == legacy.platform
        assert current.screen_width == legacy.screen_width
        assert current.screen_height == legacy.screen_height

    def test_end_time_derived_from_last_event(self, recording_dir):
        """recording.db has no end time, so the last event supplies it."""
        assert read_capture_metadata(recording_dir).ended_at == LAST_EVENT_AT

    def test_end_time_falls_back_to_start_without_events(self, tmp_path):
        """A recording that captured nothing has zero duration, not a crash."""
        capture_dir = tmp_path / "empty-recording"
        capture_dir.mkdir()
        _make_recording_db(capture_dir, with_events=False)
        meta = read_capture_metadata(capture_dir)
        assert meta.started_at == STARTED_AT
        assert meta.ended_at == STARTED_AT

    def test_recording_db_wins_when_both_present(self, tmp_path):
        """A directory holding both formats reads the current one."""
        capture_dir = tmp_path / "both"
        capture_dir.mkdir()
        _make_recording_db(capture_dir)
        _make_legacy_capture_db(capture_dir)
        assert read_capture_metadata(capture_dir).source_format == RECORDING_DB

    def test_missing_database_names_both_formats(self, tmp_path):
        """The error has to tell you what the loader looked for."""
        capture_dir = tmp_path / "nothing-here"
        capture_dir.mkdir()
        with pytest.raises(FileNotFoundError) as excinfo:
            read_capture_metadata(capture_dir)
        message = str(excinfo.value)
        assert RECORDING_DB in message
        assert LEGACY_CAPTURE_DB in message

    def test_empty_recording_table_is_reported(self, tmp_path):
        capture_dir = tmp_path / "no-rows"
        capture_dir.mkdir()
        db_path = capture_dir / RECORDING_DB
        conn = sqlite3.connect(db_path)
        conn.execute("CREATE TABLE recording (id INTEGER PRIMARY KEY, timestamp NUMERIC)")
        conn.commit()
        conn.close()
        with pytest.raises(ValueError, match="No recording row"):
            read_capture_metadata(capture_dir)

    def test_unrelated_sqlite_file_is_reported(self, tmp_path):
        """A SQLite file that is not a recording gets a clear message."""
        capture_dir = tmp_path / "wrong-db"
        capture_dir.mkdir()
        conn = sqlite3.connect(capture_dir / RECORDING_DB)
        conn.execute("CREATE TABLE something_else (id INTEGER)")
        conn.commit()
        conn.close()
        with pytest.raises(ValueError, match="no 'recording' table"):
            read_capture_metadata(capture_dir)


class TestLoadRealCaptureData:
    """End-to-end loading into a BenchmarkRun."""

    def test_loads_from_recording_db(self, recording_dir):
        run = load_real_capture_data(recording_dir)
        assert run.run_id == "real_capture_test-recording"
        assert len(run.tasks) == 1
        assert len(run.executions) == 1
        assert run.config["platform"] == PLATFORM
        assert run.config["screen_size"] == f"{WIDTH}x{HEIGHT}"
        assert run.config["capture_format"] == RECORDING_DB

    def test_loads_from_legacy_capture_db(self, legacy_dir):
        run = load_real_capture_data(legacy_dir)
        assert len(run.tasks) == 1
        assert run.config["capture_format"] == LEGACY_CAPTURE_DB

    def test_both_formats_produce_the_same_run(self, recording_dir, legacy_dir):
        """Schema is an implementation detail; the viewer sees one shape."""
        current = load_real_capture_data(recording_dir)
        legacy = load_real_capture_data(legacy_dir)
        assert current.start_time == legacy.start_time
        assert current.end_time == legacy.end_time
        assert current.config["duration"] == legacy.config["duration"]
        assert len(current.executions[0].steps) == len(legacy.executions[0].steps)

    def test_frame_paths_resolve_under_the_capture_directory(self, recording_dir):
        run = load_real_capture_data(recording_dir)
        paths = [step.screenshot_path for step in run.executions[0].steps]
        assert paths, "expected key frames to produce screenshot paths"
        for path in paths:
            assert Path(path).is_absolute()
            assert str(recording_dir) in path

    def test_checkout_relative_frame_paths_are_reanchored(self, tmp_path):
        """"../openadapt-capture/<rec>/..." resolves under the given directory.

        These paths were written relative to whichever checkout produced the
        recording. They must not send the reader back to that machine.
        """
        capture_dir = tmp_path / "openadapt-capture" / "reanchor-me"
        capture_dir.mkdir(parents=True)
        _make_recording_db(capture_dir)
        _write_episodes(
            capture_dir,
            frame_prefix="../openadapt-capture/reanchor-me/screenshots/",
        )
        run = load_real_capture_data(capture_dir)
        for step in run.executions[0].steps:
            assert step.screenshot_path.startswith(str(capture_dir))
            assert "/../" not in step.screenshot_path

    def test_missing_episodes_file_is_reported(self, tmp_path):
        capture_dir = tmp_path / "db-but-no-episodes"
        capture_dir.mkdir()
        _make_recording_db(capture_dir)
        with pytest.raises(FileNotFoundError, match="Episodes file not found"):
            load_real_capture_data(capture_dir)

    def test_missing_directory_is_reported(self, tmp_path):
        with pytest.raises(FileNotFoundError, match="Capture directory not found"):
            load_real_capture_data(tmp_path / "does-not-exist")

    def test_no_path_and_no_env_var(self, monkeypatch):
        monkeypatch.delenv("OPENADAPT_CAPTURE_RECORDING", raising=False)
        with pytest.raises(FileNotFoundError, match="No capture directory given"):
            load_real_capture_data()

    def test_env_var_supplies_the_default(self, monkeypatch, recording_dir):
        monkeypatch.setenv("OPENADAPT_CAPTURE_RECORDING", str(recording_dir))
        run = load_real_capture_data()
        assert run.config["capture_path"] == str(recording_dir)
