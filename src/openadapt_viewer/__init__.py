"""OpenAdapt Viewer - Reusable component library for OpenAdapt visualization.

This package provides:
1. Components - Reusable UI building blocks (screenshot, playback, metrics, etc.)
2. Builders - High-level page builders for complete viewers
3. Viewers - Ready-to-use viewer generators (benchmark, training, capture)

Quick Start:
    # Use individual components
    from openadapt_viewer.components import screenshot_display, playback_controls
    html = screenshot_display("screenshot.png", overlays=[...])

    # Build complete pages
    from openadapt_viewer.builders import PageBuilder
    builder = PageBuilder(title="My Viewer")
    builder.add_section(screenshot_display(...))
    html = builder.render()

    # Generate ready-to-use viewers
    from openadapt_viewer.viewers.benchmark import generate_benchmark_html
    generate_benchmark_html(data_path="results/", output_path="viewer.html")
"""

__version__ = "0.1.0"

# Core types and utilities
from openadapt_viewer.core.html_builder import HTMLBuilder
from openadapt_viewer.core.types import (
    BenchmarkRun,
    BenchmarkTask,
    TaskExecution,
    ExecutionStep,
)

# Components - reusable UI building blocks
from openadapt_viewer.components import (
    screenshot_display,
    playback_controls,
    timeline,
    action_display,
    metrics_card,
    metrics_grid,
    filter_bar,
    filter_dropdown,
    selectable_list,
    list_item,
    badge,
)

# Builders - high-level page construction
from openadapt_viewer.builders import PageBuilder

# Viewer generators (re-exported for convenience)
from openadapt_viewer.viewers.benchmark import generate_benchmark_html

__all__ = [
    # Core
    "HTMLBuilder",
    "BenchmarkRun",
    "BenchmarkTask",
    "TaskExecution",
    "ExecutionStep",
    # Components
    "screenshot_display",
    "playback_controls",
    "timeline",
    "action_display",
    "metrics_card",
    "metrics_grid",
    "filter_bar",
    "filter_dropdown",
    "selectable_list",
    "list_item",
    "badge",
    # Builders
    "PageBuilder",
    # Viewers
    "generate_benchmark_html",
]
