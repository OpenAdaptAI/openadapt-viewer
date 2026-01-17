"""Real data loader for benchmark viewer from nightshift recording.

This module loads REAL data from openadapt-capture recordings
instead of fake/sample data.

POLICY: ALWAYS use real data from actual recordings by default.
Sample data should ONLY be used for unit tests, clearly marked.
"""

import json
import sqlite3
import base64
from pathlib import Path
from datetime import datetime
from typing import Optional

from openadapt_viewer.core.types import (
    BenchmarkRun,
    BenchmarkTask,
    TaskExecution,
    ExecutionStep,
)


# Default to nightshift recording if no path specified
DEFAULT_CAPTURE_PATH = Path("/Users/abrichr/oa/src/openadapt-capture/turn-off-nightshift")


def load_real_capture_data(
    capture_path: Optional[Path | str] = None,
    run_id: Optional[str] = None,
) -> BenchmarkRun:
    """Load REAL data from a capture recording.

    Args:
        capture_path: Path to capture directory (defaults to nightshift recording)
        run_id: Optional run ID (defaults to recording name)

    Returns:
        BenchmarkRun with real data from the recording

    Raises:
        FileNotFoundError: If capture directory or required files don't exist
    """
    # Use default nightshift recording if no path specified
    if capture_path is None:
        capture_path = DEFAULT_CAPTURE_PATH

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
                    # Handle paths that start with ../openadapt-capture/
                    if frame_path.startswith("../openadapt-capture/"):
                        screenshot_path = str(Path("/Users/abrichr/oa/src") / frame_path.lstrip("../"))
                    else:
                        screenshot_path = str(capture_path / frame_path)

            # Calculate timestamp within episode
            step_timestamp = episode["start_time"] + (i * episode["duration"] / max(len(episode_steps), 1))

            step = ExecutionStep(
                step_number=i,
                timestamp=datetime.fromtimestamp(started_at + step_timestamp),
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
            start_time=datetime.fromtimestamp(started_at + episode["start_time"]),
            end_time=datetime.fromtimestamp(started_at + episode["end_time"]),
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
        start_time=datetime.fromtimestamp(started_at),
        end_time=datetime.fromtimestamp(ended_at),
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
    """Load the nightshift recording (convenience function).

    Returns:
        BenchmarkRun with nightshift recording data
    """
    return load_real_capture_data(DEFAULT_CAPTURE_PATH)
