"""Real data loader for the benchmark viewer, reading openadapt-capture recordings.

This module loads REAL data from openadapt-capture recordings
instead of fake/sample data.

POLICY: ALWAYS use real data from actual recordings by default.
Sample data should ONLY be used for unit tests, clearly marked.

There is no built-in default recording. A recording is local data that lives
outside this repository, so the caller names one -- either by passing
``capture_path`` or by setting ``$OPENADAPT_CAPTURE_RECORDING``.

Note the two variables are different. ``$OPENADAPT_CAPTURE_DIR`` names the
openadapt-capture checkout, which holds many recordings; the screenshot scripts
use it. ``$OPENADAPT_CAPTURE_RECORDING`` names one recording directory inside it.
"""

import json
import os
import sqlite3
from datetime import datetime
from pathlib import Path, PurePosixPath

from openadapt_viewer.core.types import (
    BenchmarkRun,
    BenchmarkTask,
    ExecutionStep,
    TaskExecution,
)

#: Environment variable naming one recording directory to load by default.
CAPTURE_RECORDING_ENV = "OPENADAPT_CAPTURE_RECORDING"


def default_capture_path() -> Path | None:
    """Return the recording directory from the environment, or None if unset.

    Returns:
        The directory named by ``$OPENADAPT_CAPTURE_RECORDING``, or None.
    """
    value = os.environ.get(CAPTURE_RECORDING_ENV)
    return Path(value).expanduser() if value else None


def _resolve_frame_path(capture_path: Path, frame_path: str) -> str:
    """Resolve a key frame path from episodes.json against a capture directory.

    episodes.json stores frame paths relative to the checkout root that holds
    the capture repository, for example
    ``../openadapt-capture/<recording>/screenshots/step_0.png``. Re-anchor those
    on the capture directory the caller actually passed, so a recording loads
    from any checkout rather than only from the one that wrote the file.

    Args:
        capture_path: The capture directory being loaded.
        frame_path: The path recorded in episodes.json.

    Returns:
        An absolute path to the frame, as a string.
    """
    if not frame_path.startswith("../"):
        return str(capture_path / frame_path)

    parts = PurePosixPath(frame_path.removeprefix("../")).parts
    # "<capture-repo>/<recording>/..." -> strip the two leading segments and
    # re-anchor the tail on the capture directory we were given.
    if parts[:2] == (capture_path.parent.name, capture_path.name):
        return str(capture_path.joinpath(*parts[2:]))

    # Unknown layout: fall back to reading "../" literally.
    return str((capture_path / frame_path).resolve())


def load_real_capture_data(
    capture_path: Path | str | None = None,
    run_id: str | None = None,
) -> BenchmarkRun:
    """Load REAL data from a capture recording.

    Args:
        capture_path: Path to a capture directory. If omitted, falls back to
            ``$OPENADAPT_CAPTURE_RECORDING``.
        run_id: Optional run ID (defaults to recording name)

    Returns:
        BenchmarkRun with real data from the recording

    Raises:
        FileNotFoundError: If no capture directory was named, or if the named
            directory or its required files don't exist.
    """
    if capture_path is None:
        capture_path = default_capture_path()

    if capture_path is None:
        raise FileNotFoundError(
            "No capture directory given. Pass capture_path, or set "
            f"${CAPTURE_RECORDING_ENV} to a directory holding a recording "
            "(episodes.json plus capture.db)."
        )

    capture_path = Path(capture_path)

    if not capture_path.exists():
        raise FileNotFoundError(f"Capture directory not found: {capture_path}")

    # Load episodes.json
    episodes_path = capture_path / "episodes.json"
    if not episodes_path.exists():
        raise FileNotFoundError(f"Episodes file not found: {episodes_path}")

    with open(episodes_path) as f:
        episodes_data = json.load(f)

    # Load capture.db metadata
    db_path = capture_path / "capture.db"
    if not db_path.exists():
        raise FileNotFoundError(f"Capture database not found: {db_path}")

    # Connect to database
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    # Get capture metadata
    cursor.execute("SELECT * FROM capture LIMIT 1")
    capture_meta = cursor.fetchone()

    if capture_meta is None:
        raise ValueError(f"No capture metadata found in {db_path}")

    # Calculate timing
    started_at = capture_meta["started_at"]
    ended_at = capture_meta["ended_at"] or started_at
    duration = ended_at - started_at

    # Get recording name
    recording_id = episodes_data.get("recording_id", capture_path.name)
    recording_name = episodes_data.get("recording_name", recording_id.replace("-", " ").title())

    # Create tasks and executions from episodes
    tasks = []
    executions = []

    episodes = episodes_data.get("episodes", [])

    for episode in episodes:
        task_id = episode["episode_id"]

        # Create task
        task = BenchmarkTask(
            task_id=task_id,
            instruction=episode["name"],
            domain=episode.get("application", "system"),
            difficulty="real",  # Mark as real data
            time_limit=int(episode["duration"]) + 60,  # Episode duration + buffer
            metadata={
                "source": "real_capture",
                "recording_id": recording_id,
                "recording_name": recording_name,
                "episode_description": episode.get("description", ""),
                "boundary_confidence": episode.get("boundary_confidence", 0.0),
                "coherence_score": episode.get("coherence_score", 0.0),
            },
        )
        tasks.append(task)

        # Create execution steps from episode steps
        steps = []
        episode_steps = episode.get("steps", [])
        key_frames = episode.get("screenshots", {}).get("key_frames", [])

        for i, step_text in enumerate(episode_steps):
            # Find corresponding key frame
            screenshot_path = None
            if i < len(key_frames):
                frame = key_frames[i]
                # Convert relative path to absolute
                frame_path = frame.get("path", "")
                if frame_path:
                    screenshot_path = _resolve_frame_path(capture_path, frame_path)

            # Calculate timestamp within episode
            step_timestamp = episode["start_time"] + (i * episode["duration"] / max(len(episode_steps), 1))

            step = ExecutionStep(
                step_number=i,
                timestamp=datetime.fromtimestamp(started_at + step_timestamp).astimezone(),
                screenshot_path=screenshot_path,
                action_type="ml_inferred",  # Mark as ML-inferred (not raw hardware event)
                action_details={
                    "description": step_text,
                    "episode": episode["name"],
                    "frame_index": key_frames[i]["frame_index"] if i < len(key_frames) else None,
                    # Data provenance metadata
                    "provenance": "ml_inferred",
                    "source": "episodes.json",
                    "model": episodes_data.get("llm_model", "unknown"),
                    "confidence": episode.get("boundary_confidence", 0.0),
                    "processing_timestamp": episodes_data.get("processing_timestamp", "unknown"),
                },
                reasoning=f"ML interpretation ({episodes_data.get('llm_model', 'unknown')}): {step_text}",
                raw_output=f"Episode: {episode['name']}, Step {i+1}: {step_text}",
            )
            steps.append(step)

        # Create execution
        execution = TaskExecution(
            task_id=task_id,
            start_time=datetime.fromtimestamp(
                started_at + episode["start_time"]
            ).astimezone(),
            end_time=datetime.fromtimestamp(
                started_at + episode["end_time"]
            ).astimezone(),
            steps=steps,
            success=True,  # Real recordings are successful completions
            error=None,
        )
        executions.append(execution)

    conn.close()

    # Create benchmark run
    if run_id is None:
        run_id = f"real_capture_{recording_id}"

    return BenchmarkRun(
        run_id=run_id,
        benchmark_name=f"Real Capture: {recording_name}",
        model_id="human_demonstration",
        start_time=datetime.fromtimestamp(started_at).astimezone(),
        end_time=datetime.fromtimestamp(ended_at).astimezone(),
        tasks=tasks,
        executions=executions,
        config={
            "source": "real_capture",
            "recording_id": recording_id,
            "recording_name": recording_name,
            "capture_path": str(capture_path),
            "duration": duration,
            "platform": capture_meta["platform"],
            "screen_size": f"{capture_meta['screen_width']}x{capture_meta['screen_height']}",
            "episode_count": len(episodes),
            "llm_model": episodes_data.get("llm_model", "unknown"),
            "processing_timestamp": episodes_data.get("processing_timestamp", "unknown"),
            "coverage": episodes_data.get("coverage", 0.0),
            "avg_confidence": episodes_data.get("avg_confidence", 0.0),
        },
    )


def load_nightshift_data() -> BenchmarkRun:
    """Load the recording named by ``$OPENADAPT_CAPTURE_RECORDING``.

    Deprecated: this used to point at one specific local recording. It is now a
    thin alias for ``load_real_capture_data()``. Call that instead.

    Returns:
        BenchmarkRun with data from the configured recording
    """
    return load_real_capture_data()
