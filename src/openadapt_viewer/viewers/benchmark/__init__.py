"""Benchmark viewer for displaying evaluation results.

This module generates standalone HTML files for visualizing
benchmark evaluation results (WAA, WebArena, OSWorld, etc.).

Components:
- Single-run viewer: generate_benchmark_html
- Multi-run viewer: generate_multi_run_viewer (compare multiple runs)
- Data loading: load_benchmark_data, load_multi_run_data
"""

from openadapt_viewer.viewers.benchmark.generator import generate_benchmark_html
from openadapt_viewer.viewers.benchmark.data import (
    load_benchmark_data,
    create_sample_data,
)
from openadapt_viewer.viewers.benchmark.multi_run import (
    # Data models
    RunMetadata,
    RunSummary,
    TaskResult,
    MultiRunData,
    # Data loading
    load_multi_run_data,
    # HTML generation
    generate_multi_run_viewer,
    run_selector,
    run_comparison_panel,
    execution_logs_panel,
    summary_cards_section,
    filter_bar_section,
    task_list_section,
    mock_banner_section,
    # CSS/JS
    multi_run_css,
    multi_run_js,
)

__all__ = [
    # Single-run viewer
    "generate_benchmark_html",
    "load_benchmark_data",
    "create_sample_data",
    # Multi-run viewer - Data models
    "RunMetadata",
    "RunSummary",
    "TaskResult",
    "MultiRunData",
    # Multi-run viewer - Data loading
    "load_multi_run_data",
    # Multi-run viewer - HTML generation
    "generate_multi_run_viewer",
    "run_selector",
    "run_comparison_panel",
    "execution_logs_panel",
    "summary_cards_section",
    "filter_bar_section",
    "task_list_section",
    "mock_banner_section",
    # Multi-run viewer - CSS/JS
    "multi_run_css",
    "multi_run_js",
]
