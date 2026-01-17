"""
Automatic discovery and scanning of OpenAdapt recordings and results.

This module scans directories to find:
- Recordings from openadapt-capture (directories with capture.db)
- Segmentation results from openadapt-ml (JSON files with episodes)
- Episode data for indexing
"""

import json
import os
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

from .catalog import Episode, Recording, RecordingCatalog, SegmentationResult


class RecordingScanner:
    """Scanner for discovering and indexing OpenAdapt data."""

    def __init__(self, catalog: RecordingCatalog):
        """
        Initialize the scanner.

        Args:
            catalog: The RecordingCatalog instance to populate
        """
        self.catalog = catalog

    def scan_recording_directory(
        self,
        base_path: str,
        recursive: bool = False
    ) -> List[Recording]:
        """
        Scan a directory for recordings (directories containing capture.db).

        Args:
            base_path: Path to scan for recordings
            recursive: If True, scan subdirectories recursively

        Returns:
            List of newly registered Recording objects
        """
        base_path = Path(base_path).resolve()
        recordings = []

        if not base_path.exists():
            raise FileNotFoundError(f"Directory not found: {base_path}")

        # Find all directories with capture.db
        if recursive:
            pattern = "**/capture.db"
        else:
            pattern = "*/capture.db"

        for capture_db in base_path.glob(pattern):
            recording_dir = capture_db.parent
            recording_id = recording_dir.name

            try:
                recording = self._extract_recording_info(recording_dir, recording_id)
                # register_recording needs positional args, then kwargs
                registered = self.catalog.register_recording(
                    recording_id=recording.id,
                    name=recording.name,
                    path=recording.path,
                    created_at=recording.created_at,
                    duration_seconds=recording.duration_seconds,
                    frame_count=recording.frame_count,
                    event_count=recording.event_count,
                    task_description=recording.task_description,
                    tags=recording.tags,
                    metadata=recording.metadata,
                )
                recordings.append(registered)
            except Exception as e:
                print(f"Warning: Failed to index {recording_dir}: {e}")
                continue

        return recordings

    def _extract_recording_info(
        self,
        recording_dir: Path,
        recording_id: str
    ) -> Recording:
        """
        Extract recording metadata from a recording directory.

        Args:
            recording_dir: Path to the recording directory
            recording_id: Identifier for the recording (usually directory name)

        Returns:
            Recording object with extracted metadata
        """
        capture_db = recording_dir / "capture.db"
        screenshots_dir = recording_dir / "screenshots"

        # Extract from capture.db
        metadata = {}
        created_at = None
        duration_seconds = None
        task_description = None

        try:
            with sqlite3.connect(str(capture_db)) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.execute("SELECT * FROM capture LIMIT 1")
                row = cursor.fetchone()

                if row:
                    created_at = row["started_at"]
                    if row["ended_at"]:
                        duration_seconds = row["ended_at"] - row["started_at"]
                    task_description = row["task_description"]

                    # Store additional metadata
                    metadata.update({
                        "platform": row["platform"],
                        "screen_width": row["screen_width"],
                        "screen_height": row["screen_height"],
                        "pixel_ratio": row["pixel_ratio"],
                    })

                # Count events
                cursor = conn.execute("SELECT COUNT(*) FROM events")
                event_count = cursor.fetchone()[0]
        except Exception as e:
            print(f"Warning: Could not read capture.db: {e}")
            event_count = None

        # Count screenshots
        frame_count = None
        if screenshots_dir.exists():
            frame_count = len(list(screenshots_dir.glob("*.png")))

        # Use directory modification time if no capture date found
        if created_at is None:
            created_at = recording_dir.stat().st_mtime

        return Recording(
            id=recording_id,
            name=recording_id.replace("_", " ").replace("-", " ").title(),
            path=str(recording_dir),
            created_at=created_at,
            duration_seconds=duration_seconds,
            frame_count=frame_count,
            event_count=event_count,
            task_description=task_description,
            metadata=metadata,
        )

    def scan_segmentation_results(
        self,
        segmentation_dir: str
    ) -> List[SegmentationResult]:
        """
        Scan directory for segmentation result JSON files.

        Looks for files matching pattern: {recording_id}_episodes.json

        Args:
            segmentation_dir: Path to segmentation output directory

        Returns:
            List of newly registered SegmentationResult objects
        """
        segmentation_dir = Path(segmentation_dir).resolve()
        results = []

        if not segmentation_dir.exists():
            raise FileNotFoundError(f"Directory not found: {segmentation_dir}")

        # Find all *_episodes.json files
        for episodes_file in segmentation_dir.glob("*_episodes.json"):
            try:
                result = self._extract_segmentation_info(episodes_file)
                registered = self.catalog.register_segmentation(
                    segmentation_id=result.id,
                    recording_id=result.recording_id,
                    path=result.path,
                    created_at=result.created_at,
                    episode_count=result.episode_count,
                    boundary_count=result.boundary_count,
                    status=result.status,
                    llm_model=result.llm_model,
                    metadata=result.metadata,
                )

                # Also index episodes
                self._index_episodes_from_file(episodes_file, registered.id, registered.recording_id)

                results.append(registered)
            except Exception as e:
                print(f"Warning: Failed to index {episodes_file}: {e}")
                continue

        return results

    def _extract_segmentation_info(
        self,
        episodes_file: Path
    ) -> SegmentationResult:
        """
        Extract segmentation result metadata from JSON file.

        Args:
            episodes_file: Path to {recording_id}_episodes.json

        Returns:
            SegmentationResult object
        """
        with open(episodes_file) as f:
            data = json.load(f)

        # Extract recording ID from filename
        recording_id = episodes_file.stem.replace("_episodes", "")
        segmentation_id = f"{recording_id}_segmentation_{int(datetime.now().timestamp())}"

        created_at = episodes_file.stat().st_mtime

        # Parse processing timestamp if present
        if "processing_timestamp" in data:
            try:
                dt = datetime.fromisoformat(data["processing_timestamp"])
                created_at = dt.timestamp()
            except:
                pass

        episode_count = len(data.get("episodes", []))
        boundary_count = len(data.get("boundaries", []))

        return SegmentationResult(
            id=segmentation_id,
            recording_id=recording_id,
            path=str(episodes_file),
            created_at=created_at,
            episode_count=episode_count,
            boundary_count=boundary_count,
            status="complete" if episode_count > 0 else "partial",
            llm_model=data.get("llm_model"),
            metadata={
                "coverage": data.get("coverage"),
                "avg_confidence": data.get("avg_confidence"),
            },
        )

    def _index_episodes_from_file(
        self,
        episodes_file: Path,
        segmentation_result_id: str,
        recording_id: str
    ):
        """
        Index all episodes from a segmentation result file.

        Args:
            episodes_file: Path to episodes JSON file
            segmentation_result_id: ID of the parent segmentation result
            recording_id: ID of the source recording
        """
        with open(episodes_file) as f:
            data = json.load(f)

        episodes = data.get("episodes", [])

        for idx, episode_data in enumerate(episodes):
            episode_id = f"{recording_id}_episode_{idx}"

            self.catalog.register_episode(
                episode_id=episode_id,
                segmentation_result_id=segmentation_result_id,
                recording_id=recording_id,
                name=episode_data.get("name"),
                description=episode_data.get("description"),
                start_time=episode_data.get("start_time"),
                end_time=episode_data.get("end_time"),
                start_frame=episode_data.get("start_frame"),
                end_frame=episode_data.get("end_frame"),
                confidence=episode_data.get("confidence"),
                metadata=episode_data,
            )

    def scan_all(
        self,
        capture_dirs: Optional[List[str]] = None,
        segmentation_dirs: Optional[List[str]] = None
    ) -> Dict[str, int]:
        """
        Scan multiple directories for recordings and segmentation results.

        Args:
            capture_dirs: List of directories to scan for recordings
            segmentation_dirs: List of directories to scan for segmentation results

        Returns:
            Dict with counts of newly indexed items
        """
        counts = {
            "recordings": 0,
            "segmentations": 0,
        }

        # Default paths if not specified
        if capture_dirs is None:
            # Try common locations
            capture_dirs = []
            possible_paths = [
                Path.home() / "oa" / "src" / "openadapt-capture",
                Path.cwd() / "recordings",
                Path.home() / ".openadapt" / "recordings",
            ]
            for path in possible_paths:
                if path.exists():
                    capture_dirs.append(str(path))

        if segmentation_dirs is None:
            segmentation_dirs = []
            possible_paths = [
                Path.home() / "oa" / "src" / "openadapt-ml" / "segmentation_output",
                Path.cwd() / "segmentation_output",
                Path.home() / ".openadapt" / "segmentation_output",
            ]
            for path in possible_paths:
                if path.exists():
                    segmentation_dirs.append(str(path))

        # Scan recordings
        for capture_dir in capture_dirs:
            try:
                recordings = self.scan_recording_directory(capture_dir, recursive=False)
                counts["recordings"] += len(recordings)
                print(f"Found {len(recordings)} recordings in {capture_dir}")
            except Exception as e:
                print(f"Warning: Failed to scan {capture_dir}: {e}")

        # Scan segmentation results
        for seg_dir in segmentation_dirs:
            try:
                results = self.scan_segmentation_results(seg_dir)
                counts["segmentations"] += len(results)
                print(f"Found {len(results)} segmentation results in {seg_dir}")
            except Exception as e:
                print(f"Warning: Failed to scan {seg_dir}: {e}")

        return counts


def scan_and_update_catalog(
    catalog: Optional[RecordingCatalog] = None,
    capture_dirs: Optional[List[str]] = None,
    segmentation_dirs: Optional[List[str]] = None
) -> Dict[str, int]:
    """
    Convenience function to scan and update the catalog.

    Args:
        catalog: RecordingCatalog instance (uses default if None)
        capture_dirs: List of directories to scan for recordings
        segmentation_dirs: List of directories to scan for segmentation results

    Returns:
        Dict with counts of newly indexed items
    """
    from .catalog import get_catalog

    if catalog is None:
        catalog = get_catalog()

    scanner = RecordingScanner(catalog)
    return scanner.scan_all(capture_dirs, segmentation_dirs)
