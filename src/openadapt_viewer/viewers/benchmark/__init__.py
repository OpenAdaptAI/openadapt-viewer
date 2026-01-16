"""Benchmark viewer for displaying evaluation results.

This module generates standalone HTML files for visualizing
benchmark evaluation results (WAA, WebArena, OSWorld, etc.).
"""

from openadapt_viewer.viewers.benchmark.generator import generate_benchmark_html
from openadapt_viewer.viewers.benchmark.data import (
    load_benchmark_data,
    create_sample_data,
)

__all__ = [
    "generate_benchmark_html",
    "load_benchmark_data",
    "create_sample_data",
]
