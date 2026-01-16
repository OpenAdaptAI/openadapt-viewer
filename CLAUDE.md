# Claude Code Instructions for openadapt-viewer

## Overview

**Reusable component library** for OpenAdapt visualization. Provides building blocks (components) and high-level builders for creating standalone HTML viewers.

Used by:
- **openadapt-ml**: Training dashboards
- **openadapt-evals**: Benchmark result viewers
- **openadapt-capture**: Capture playback viewers
- **openadapt-retrieval**: Demo search result viewers

## Quick Start

```bash
# Install
cd /Users/abrichr/oa/src/openadapt-viewer
uv sync

# Run tests
uv run pytest tests/ -v

# Generate demo benchmark viewer
uv run openadapt-viewer demo --tasks 5 --output viewer.html

# Run examples
uv run python -m openadapt_viewer.examples.benchmark_example
uv run python -m openadapt_viewer.examples.training_example
uv run python -m openadapt_viewer.examples.capture_example
uv run python -m openadapt_viewer.examples.retrieval_example
```

## Architecture

```
openadapt_viewer/
├── components/               # Reusable UI building blocks
│   ├── screenshot.py         # Screenshot with overlays
│   ├── playback.py           # Play/pause/speed controls
│   ├── timeline.py           # Step progress bar
│   ├── action_display.py     # Format actions (click, type, etc.)
│   ├── metrics.py            # Stats cards and grids
│   ├── filters.py            # Filter dropdowns
│   ├── list_view.py          # Selectable list component
│   └── badge.py              # Status badges
│
├── builders/                 # High-level page builders
│   └── page_builder.py       # PageBuilder class
│
├── styles/                   # Shared CSS
│   └── core.css              # CSS variables and base styles
│
├── core/                     # Core utilities
│   ├── types.py              # Pydantic data models
│   ├── data_loader.py        # Data loading utilities
│   └── html_builder.py       # Jinja2 HTMLBuilder
│
├── viewers/                  # Full viewer implementations
│   └── benchmark/            # Benchmark results viewer
│       ├── generator.py      # generate_benchmark_html()
│       └── data.py           # Data loading
│
├── examples/                 # Reference implementations
│   ├── benchmark_example.py  # openadapt-evals usage
│   ├── training_example.py   # openadapt-ml usage
│   ├── capture_example.py    # openadapt-capture usage
│   └── retrieval_example.py  # openadapt-retrieval usage
│
├── templates/                # Jinja2 templates
│   └── base.html             # Base HTML template
│
└── __init__.py               # Package exports
```

## Component Usage

### Individual Components

Each component returns an HTML string:

```python
from openadapt_viewer.components import (
    screenshot_display,
    playback_controls,
    metrics_grid,
    filter_bar,
    selectable_list,
    badge,
)

# Screenshot with overlays
html = screenshot_display(
    image_path="screenshot.png",
    overlays=[
        {"type": "click", "x": 0.5, "y": 0.3, "label": "H", "variant": "human"},
        {"type": "click", "x": 0.6, "y": 0.4, "label": "AI", "variant": "predicted"},
    ],
    caption="Step 5",
)

# Metrics cards
html = metrics_grid([
    {"label": "Total", "value": 100},
    {"label": "Passed", "value": 75, "color": "success"},
    {"label": "Failed", "value": 25, "color": "error"},
])

# Playback controls (requires Alpine.js)
html = playback_controls(step_count=20, initial_step=0)

# Filter bar
html = filter_bar(
    filters=[
        {"id": "domain", "label": "Domain", "options": ["office", "browser"]},
        {"id": "status", "label": "Status", "options": ["passed", "failed"]},
    ],
    search_placeholder="Search tasks...",
)
```

### Page Builder

Build complete pages from components:

```python
from openadapt_viewer.builders import PageBuilder
from openadapt_viewer.components import metrics_grid, screenshot_display

builder = PageBuilder(title="My Viewer", include_alpine=True)

builder.add_header(
    title="Results",
    subtitle="Model: gpt-5.1",
    nav_tabs=[
        {"href": "dashboard.html", "label": "Training"},
        {"href": "viewer.html", "label": "Viewer", "active": True},
    ],
)

builder.add_section(
    metrics_grid([...]),
    title="Summary",
)

builder.add_section(
    screenshot_display("screenshot.png"),
)

# Render to string
html = builder.render()

# Or write to file
path = builder.render_to_file("output.html")
```

### Ready-to-Use Viewers

```python
# Benchmark viewer
from openadapt_viewer.viewers.benchmark import generate_benchmark_html
generate_benchmark_html(data_path="results/", output_path="viewer.html")

# Or with data
from openadapt_viewer import BenchmarkRun, generate_benchmark_html
run = BenchmarkRun(...)
generate_benchmark_html(run_data=run, output_path="viewer.html")
```

## CSS Classes

All component classes use the `oa-` prefix:

| Component | Classes |
|-----------|---------|
| Screenshot | `oa-screenshot-container`, `oa-overlay`, `oa-overlay-click` |
| Playback | `oa-playback-controls`, `oa-playback-btn`, `oa-playback-speed` |
| Timeline | `oa-timeline`, `oa-timeline-track`, `oa-timeline-progress` |
| Metrics | `oa-metrics-card`, `oa-metrics-grid`, `oa-metrics-value` |
| Filters | `oa-filter-bar`, `oa-filter-dropdown` |
| List | `oa-list`, `oa-list-item`, `oa-list-item-selected` |
| Badge | `oa-badge`, `oa-badge-success`, `oa-badge-error` |

## CSS Variables

Core CSS variables in `styles/core.css`:

```css
:root {
    --oa-bg-primary: #0a0a0f;
    --oa-bg-secondary: #12121a;
    --oa-text-primary: #f0f0f0;
    --oa-accent: #00d4aa;
    --oa-success: #34d399;
    --oa-error: #ff5f5f;
    /* ... */
}
```

## Testing

```bash
# Run all tests
uv run pytest tests/ -v

# Run component tests
uv run pytest tests/test_components/ -v

# Check imports work
uv run python -c "from openadapt_viewer import screenshot_display, PageBuilder; print('OK')"
```

## Integration Examples

### openadapt-ml (Training Dashboard)

```python
from openadapt_viewer.builders import PageBuilder
from openadapt_viewer.components import metrics_grid, screenshot_display

def generate_training_dashboard(state, config):
    builder = PageBuilder(title="Training", include_chartjs=True)
    builder.add_header(title="Training Dashboard", subtitle=f"Model: {state.model_name}")
    builder.add_section(metrics_grid([
        {"label": "Epoch", "value": state.epoch},
        {"label": "Loss", "value": f"{state.loss:.4f}"},
    ]))
    return builder.render()
```

### openadapt-evals (Benchmark Viewer)

```python
from openadapt_viewer import generate_benchmark_html, BenchmarkRun

run = BenchmarkRun.from_directory("results/run_001/")
generate_benchmark_html(run_data=run, output_path="benchmark.html")
```

### openadapt-retrieval (Search Results)

```python
from openadapt_viewer.builders import PageBuilder
from openadapt_viewer.components import screenshot_display, selectable_list

def generate_retrieval_viewer(results):
    builder = PageBuilder(title="Search Results")
    for result in results:
        builder.add_section(f'''
            {screenshot_display(result.screenshot)}
            <div>Similarity: {result.score:.3f}</div>
        ''')
    return builder.render()
```

## Related Projects

- [openadapt-ml](../openadapt-ml/) - ML engine, uses this for dashboards
- [openadapt-evals](../openadapt-evals/) - Benchmark evaluation, uses this for viewers
- [openadapt-capture](../openadapt-capture/) - Recording capture
- [openadapt-retrieval](../openadapt-retrieval/) - Demo retrieval
