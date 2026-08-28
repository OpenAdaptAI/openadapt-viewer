"""
Automatic discovery and scanning of OpenAdapt recordings and results.

This module scans directories to find:
- Recordings from openadapt-capture (directories with recording.db)
- Segmentation results from openadapt-ml (JSON files with episodes)
- Episode data for indexing

The recorder writes one SQLAlchemy database per capture, at
``<recording>/recording.db``. Its tables are ``recording``, ``action_event``,
``screenshot``, ``window_event``, ``browser_event``, ``audio_info``,
``performance_stat`` and ``memory_stat``. The columns this module reads are
listed beside each query below.

Two notes on what this module deliberately does not do.

It reads the database with ``sqlite3`` rather than through
``openadapt_capture.CaptureSession.load``. Indexing needs two row counts and a
handful of scalars, and installing ``openadapt-capture`` to get them would
pull mss, sounddevice, soundfile, matplotlib, sqlalchemy, alembic, numpy and
the platform accessibility stack into an HTML generator. It is therefore not
a dependency of this package. Anything that needs decoded frames or replayable
actions should import ``CaptureSession`` rather than extend this module.

It does not read the pre-2026-07-17 ``capture.db``. That format held a single
``capture`` row and a generic ``events`` table; openadapt-capture PR #28
replaced it, and current code cannot load it at all. A legacy directory is
reported with the command that converts it rather than skipped in silence.
"""

import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path

from .catalog import Recording, RecordingCatalog, SegmentationResult

#: Filename the current recorder writes, one per capture directory.
RECORDING_DB_NAME = "recording.db"

#: Filename the pre-2026-07-17 recorder wrote. Detected, never read.
LEGACY_DB_NAME = "capture.db"

#: Printed when a directory holds only a legacy capture.
LEGACY_HINT = (
    "holds the legacy {legacy} format, which the current viewer cannot read. "
    "Convert it with openadapt-capture: "
    "python scripts/migrate_legacy_capture.py <src> <dest>"
)

#: Event tables whose timestamps bound the recording's duration.
_TIMESTAMPED_TABLES = ("screenshot", "action_event", "window_event", "browser_event")


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
    ) -> list[Recording]:
        """
        Scan a directory for recordings (directories containing recording.db).

        A directory holding only the legacy ``capture.db`` is named in a
        warning and skipped. Reporting it is the point: the two formats share
        no table, so registering one would produce a catalog entry with no
        date, no duration and no counts.

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

        prefix = "**/" if recursive else "*/"

        for legacy_db in base_path.glob(f"{prefix}{LEGACY_DB_NAME}"):
            if (legacy_db.parent / RECORDING_DB_NAME).exists():
                # Already converted in place; the current database wins.
                continue
            print(f"Warning: {legacy_db.parent} " + LEGACY_HINT.format(legacy=LEGACY_DB_NAME))

        for recording_db in base_path.glob(f"{prefix}{RECORDING_DB_NAME}"):
            recording_dir = recording_db.parent
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
            except (OSError, sqlite3.Error, ValueError) as e:
                # Narrow on purpose: an unreadable directory, a corrupt
                # recording.db or a row that fails Recording validation should
                # skip that recording, not the whole scan. Anything else is a
                # bug in this module and must surface.
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

        Raises:
            FileNotFoundError: If the directory holds no recording.db. A legacy
                capture.db is named as such, with the conversion command.
        """
        recording_dir = Path(recording_dir)
        recording_db = recording_dir / RECORDING_DB_NAME
        screenshots_dir = recording_dir / "screenshots"

        if not recording_db.is_file():
            # Returning a hollow Recording here is what made a legacy directory
            # look indexable: no date, no duration, no counts, no complaint.
            if (recording_dir / LEGACY_DB_NAME).is_file():
                raise FileNotFoundError(
                    f"{recording_dir} " + LEGACY_HINT.format(legacy=LEGACY_DB_NAME)
                )
            raise FileNotFoundError(f"No {RECORDING_DB_NAME} in {recording_dir}")

        metadata = {}
        created_at = None
        duration_seconds = None
        task_description = None
        event_count = None
        frame_count = None

        try:
            with sqlite3.connect(str(recording_db)) as conn:
                conn.row_factory = sqlite3.Row

                # One row per capture directory, matching CaptureSession.load's
                # `session.query(Recording).first()`. Columns: timestamp (epoch
                # seconds at record start), monitor_width, monitor_height,
                # pixel_ratio, platform, task_description.
                row = conn.execute(
                    "SELECT * FROM recording ORDER BY id LIMIT 1"
                ).fetchone()

                if row is None:
                    raise sqlite3.DatabaseError("recording table is empty")

                created_at = row["timestamp"]
                task_description = row["task_description"]
                metadata.update({
                    "platform": row["platform"],
                    # Catalog vocabulary, not the recorder's: these keys are
                    # what the catalog has always stored. The recorder calls
                    # them monitor_width and monitor_height.
                    "screen_width": row["monitor_width"],
                    "screen_height": row["monitor_height"],
                    "pixel_ratio": row["pixel_ratio"],
                })

                # An action_event row is one mouse or key event, which is what
                # the legacy `events` table counted.
                event_count = conn.execute(
                    "SELECT COUNT(*) FROM action_event"
                ).fetchone()[0]

                # Frames are rows now, not files: the recorder stores each PNG
                # as a blob in `screenshot` rather than under screenshots/.
                frame_count = conn.execute(
                    "SELECT COUNT(*) FROM screenshot"
                ).fetchone()[0]

                # There is no ended_at column. The recording ends at its last
                # observation, so take the newest timestamp across the event
                # tables that carry one.
                if created_at is not None:
                    duration_seconds = self._duration_from_events(conn, created_at)
        except (sqlite3.Error, IndexError, TypeError) as e:
            # sqlite3.Error covers a corrupt database and a missing table;
            # IndexError is sqlite3.Row's "no such column"; TypeError is a NULL
            # in an arithmetic column. Each means "no event metadata", not
            # "abort", so the directory is still indexed by name and mtime.
            print(f"Warning: Could not read {recording_db}: {e}")

        # Some capture directories still carry PNGs under screenshots/. Read
        # them only when the database could not answer, so a readable database
        # reporting zero retained frames is reported as zero, not overwritten.
        if frame_count is None and screenshots_dir.is_dir():
            frame_count = len(list(screenshots_dir.glob("*.png")))

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

    @staticmethod
    def _duration_from_events(conn: sqlite3.Connection, started_at: float) -> float | None:
        """
        Return seconds from the recording start to its newest observation.

        Args:
            conn: Open connection to a recording.db
            started_at: The recording row's `timestamp`, in epoch seconds

        Returns:
            Duration in seconds, or None if the database holds no timestamped
            event at or after the start.
        """
        latest = None

        for table in _TIMESTAMPED_TABLES:
            try:
                value = conn.execute(f"SELECT MAX(timestamp) FROM {table}").fetchone()[0]
            except sqlite3.Error:
                # An optional table this build does not have. Other tables can
                # still bound the duration.
                continue
            if value is not None and (latest is None or value > latest):
                latest = value

        if latest is None or latest < started_at:
            return None
        return float(latest) - float(started_at)

    def scan_segmentation_results(
        self,
        segmentation_dir: str
    ) -> list[SegmentationResult]:
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
            except (OSError, ValueError, KeyError, TypeError) as e:
                # ValueError covers json.JSONDecodeError and SegmentationResult
                # validation; KeyError/TypeError cover an episodes file whose
                # shape is not what this scanner expects.
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
        segmentation_id = (
            f"{recording_id}_segmentation_"
            f"{int(datetime.now(timezone.utc).timestamp())}"
        )

        created_at = episodes_file.stat().st_mtime

        # Parse processing timestamp if present
        if "processing_timestamp" in data:
            try:
                dt = datetime.fromisoformat(data["processing_timestamp"])
                created_at = dt.timestamp()
            except (ValueError, TypeError) as e:
                # Falling back to the file mtime is deliberate, but say so. A
                # bare `except: pass` here also swallowed KeyboardInterrupt and
                # made an unparseable timestamp indistinguishable from an
                # absent one -- the catalog then showed the file's mtime as the
                # segmentation date with no indication it was a guess.
                print(
                    f"Warning: Could not parse processing_timestamp "
                    f"{data['processing_timestamp']!r} in {episodes_file}; "
                    f"using file mtime instead ({e})"
                )

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
        capture_dirs: list[str] | None = None,
        segmentation_dirs: list[str] | None = None
    ) -> dict[str, int]:
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
            except (OSError, sqlite3.Error, ValueError) as e:
                print(f"Warning: Failed to scan {capture_dir}: {e}")

        # Scan segmentation results
        for seg_dir in segmentation_dirs:
            try:
                results = self.scan_segmentation_results(seg_dir)
                counts["segmentations"] += len(results)
                print(f"Found {len(results)} segmentation results in {seg_dir}")
            except (OSError, ValueError, KeyError, TypeError) as e:
                print(f"Warning: Failed to scan {seg_dir}: {e}")

        return counts


def scan_and_update_catalog(
    catalog: RecordingCatalog | None = None,
    capture_dirs: list[str] | None = None,
    segmentation_dirs: list[str] | None = None
) -> dict[str, int]:
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
