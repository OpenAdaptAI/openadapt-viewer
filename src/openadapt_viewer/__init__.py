"""OpenAdapt Viewer - Standalone HTML viewer generation for ML dashboards and benchmarks."""

__version__ = "0.1.0"

from openadapt_viewer.core.html_builder import HTMLBuilder
from openadapt_viewer.core.types import (
    BenchmarkRun,
    BenchmarkTask,
    TaskExecution,
    ExecutionStep,
)

__all__ = [
    "HTMLBuilder",
    "BenchmarkRun",
    "BenchmarkTask",
    "TaskExecution",
    "ExecutionStep",
]
