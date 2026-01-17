# openadapt-viewer

[![Build Status](https://github.com/OpenAdaptAI/openadapt-viewer/actions/workflows/publish.yml/badge.svg)](https://github.com/OpenAdaptAI/openadapt-viewer/actions/workflows/publish.yml)
[![PyPI version](https://img.shields.io/pypi/v/openadapt-viewer.svg)](https://pypi.org/project/openadapt-viewer/)
[![Downloads](https://img.shields.io/pypi/dm/openadapt-viewer.svg)](https://pypi.org/project/openadapt-viewer/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.10+](https://img.shields.io/badge/python-3.10%2B-blue)](https://www.python.org/downloads/)

Reusable component library for OpenAdapt visualization. Build standalone HTML viewers for training dashboards, benchmark results, capture playback, and demo retrieval.

## Features

- **Component-based**: Reusable building blocks (screenshot, playback, metrics, filters)
- **Composable**: Combine components to build custom viewers
- **Standalone HTML**: Generated files work offline, no server required
- **Consistent styling**: Shared CSS variables and dark mode support
- **Alpine.js integration**: Lightweight interactivity out of the box

## Installation

```bash
pip install openadapt-viewer
```

Or with uv:
```bash
uv add openadapt-viewer
```

## Quick Start

### Using Components

```python
from openadapt_viewer.components import (
    screenshot_display,
    playback_controls,
    metrics_grid,
    filter_bar,
    badge,
)

# Screenshot with click overlays
html = screenshot_display(
    image_path="screenshot.png",
    overlays=[
        {"type": "click", "x": 0.5, "y": 0.3, "label": "H", "variant": "human"},
        {"type": "click", "x": 0.6, "y": 0.4, "label": "AI", "variant": "predicted"},
    ],
)

# Metrics cards
html = metrics_grid([
    {"label": "Total Tasks", "value": 100},
    {"label": "Passed", "value": 75, "color": "success"},
    {"label": "Failed", "value": 25, "color": "error"},
    {"label": "Success Rate", "value": "75%", "color": "accent"},
])
```

### Using PageBuilder

Build complete pages from components:

```python
from openadapt_viewer.builders import PageBuilder
from openadapt_viewer.components import metrics_grid, screenshot_display

builder = PageBuilder(title="My Viewer", include_alpine=True)

builder.add_header(
    title="Benchmark Results",
    subtitle="Model: gpt-5.1",
    nav_tabs=[
        {"href": "dashboard.html", "label": "Training"},
        {"href": "viewer.html", "label": "Viewer", "active": True},
    ],
)

builder.add_section(
    metrics_grid([
        {"label": "Tasks", "value": 100},
        {"label": "Passed", "value": 75, "color": "success"},
    ]),
    title="Summary",
)

# Render to file
builder.render_to_file("output.html")
```

### Ready-to-Use Viewers

```python
from openadapt_viewer.viewers.benchmark import generate_benchmark_html

# From benchmark results directory
generate_benchmark_html(
    data_path="benchmark_results/run_001/",
    output_path="viewer.html",
)
```

## CLI Usage

```bash
# Generate demo benchmark viewer
openadapt-viewer demo --tasks 10 --output viewer.html

# Generate from benchmark results
openadapt-viewer benchmark --data results/run_001/ --output viewer.html
```

## Components

| Component | Description |
|-----------|-------------|
| `screenshot_display` | Screenshot with click/highlight overlays |
| `playback_controls` | Play/pause/speed controls for step playback |
| `timeline` | Progress bar for step navigation |
| `action_display` | Format actions (click, type, scroll, etc.) |
| `metrics_card` | Single statistic card |
| `metrics_grid` | Grid of metric cards |
| `filter_bar` | Filter dropdowns with optional search |
| `selectable_list` | List with selection support |
| `badge` | Status badges (pass/fail, etc.) |

## Project Structure

```
src/openadapt_viewer/
├── components/           # Reusable UI building blocks
│   ├── screenshot.py     # Screenshot with overlays
│   ├── playback.py       # Playback controls
│   ├── timeline.py       # Progress bar
│   ├── action_display.py # Action formatting
│   ├── metrics.py        # Stats cards
│   ├── filters.py        # Filter dropdowns
│   ├── list_view.py      # Selectable lists
│   └── badge.py          # Status badges
├── builders/             # High-level page builders
│   └── page_builder.py   # PageBuilder class
├── styles/               # Shared CSS
│   └── core.css          # CSS variables and base styles
├── core/                 # Core utilities
│   ├── types.py          # Pydantic models
│   └── html_builder.py   # Jinja2 utilities
├── viewers/              # Full viewer implementations
│   └── benchmark/        # Benchmark results viewer
├── examples/             # Reference implementations
│   ├── benchmark_example.py
│   ├── training_example.py
│   ├── capture_example.py
│   └── retrieval_example.py
└── templates/            # Jinja2 templates
```

## Screenshots

### Full Viewer Interface

The viewer provides a complete interface for exploring captured GUI interactions with playback controls, timeline navigation, and event details.

![Turn off Night Shift - Full Viewer](docs/images/turn-off-nightshift_full.png)
*Interactive viewer showing the "Turn off Night Shift" workflow in macOS System Settings*

### Playback Controls

Step through captures with playback controls, timeline scrubbing, and keyboard shortcuts (Space to play/pause, arrow keys to navigate).

![Playback Controls](docs/images/turn-off-nightshift_controls.png)
*Timeline and playback controls with overlay toggle*

### Event List and Details

Browse all captured events with detailed information about each action, including coordinates, timing, and action type.

![Event List](docs/images/turn-off-nightshift_events.png)
*Event list sidebar showing captured actions with timing and type information*

### Demo Workflow

![Demo Workflow](docs/images/demo_new_full.png)
*Example demo workflow viewer*

## Examples

Run the examples to see how different OpenAdapt packages can use the component library:

```bash
# Benchmark results (openadapt-evals)
python -m openadapt_viewer.examples.benchmark_example

# Training dashboard (openadapt-ml)
python -m openadapt_viewer.examples.training_example

# Capture playback (openadapt-capture)
python -m openadapt_viewer.examples.capture_example

# Retrieval results (openadapt-retrieval)
python -m openadapt_viewer.examples.retrieval_example
```

### Generating Screenshots

To regenerate the README screenshots:

```bash
# Install playwright (one-time setup)
uv pip install "openadapt-viewer[screenshots]"
uv run playwright install chromium

# Install openadapt-capture (required)
cd ../openadapt-capture
uv pip install -e .
cd ../openadapt-viewer

# Generate screenshots
uv run python scripts/generate_readme_screenshots.py

# Or with custom options
uv run python scripts/generate_readme_screenshots.py \
  --capture-dir /path/to/openadapt-capture \
  --output-dir docs/images \
  --max-events 50
```

The script will:
1. Load captures from `openadapt-capture` (turn-off-nightshift and demo_new)
2. Generate interactive HTML viewers
3. Take screenshots using Playwright
4. Save screenshots to `docs/images/`

## Development

```bash
# Clone and install
git clone https://github.com/OpenAdaptAI/openadapt-viewer.git
cd openadapt-viewer
uv sync --all-extras

# Run tests
uv run pytest tests/ -v

# Run linter
uv run ruff check .
```

## Integration

Used by other OpenAdapt packages:

- **openadapt-ml**: Training dashboards and model comparison
- **openadapt-evals**: Benchmark result visualization
- **openadapt-capture**: Capture recording playback
- **openadapt-retrieval**: Demo search result display

## License

MIT License - see LICENSE file for details.
