# Claude Code Instructions for openadapt-viewer

## Overview

HTML visualization generators for training dashboards, benchmark results, and capture playback. Generates standalone HTML files that can be opened in any browser.

## Quick Start

```bash
# Install
uv sync

# Generate demo benchmark viewer
uv run openadapt-viewer demo --tasks 5 --output viewer.html

# Open in browser
open viewer.html
```

## CLI Commands

| Command | Description |
|---------|-------------|
| `demo` | Generate demo viewer with sample data |
| `benchmark` | Generate viewer from benchmark results |

## Key Files

- `viewers/benchmark/generator.py` - Main HTML generator
- `viewers/benchmark/data.py` - Data models (BenchmarkRun, TaskExecution)
- `viewers/benchmark/templates/` - Jinja2 templates
- `__main__.py` - CLI entry point

## Architecture

```
openadapt_viewer/
├── viewers/
│   └── benchmark/
│       ├── generator.py      # generate_benchmark_html()
│       ├── data.py           # BenchmarkRun, TaskExecution, ExecutionStep
│       └── templates/
│           └── benchmark.html.j2
├── __init__.py
└── __main__.py               # CLI
```

## HTML Features

The generated viewer includes:
- Summary statistics (pass/fail, success rate)
- Domain breakdown charts
- Task list with filtering
- Step-by-step screenshot playback
- Playback controls (prev/next, play/pause, speed)
- Keyboard shortcuts

## Integration

Used by openadapt-ml and openadapt-evals to visualize results:

```python
from openadapt_viewer import generate_benchmark_html, BenchmarkRun

run = BenchmarkRun.from_results(results)
html = generate_benchmark_html(run, embed_screenshots=True)
Path("results.html").write_text(html)
```

## Development

```bash
# Run tests (when added)
uv run pytest tests/ -v

# Check imports
uv run python -c "from openadapt_viewer import generate_benchmark_html; print('OK')"
```
