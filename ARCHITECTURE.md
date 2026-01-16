# OpenAdapt Viewer Architecture

This document describes the architecture of the openadapt-viewer package for LLM assistants and developers.

## Overview

openadapt-viewer generates standalone HTML files for visualizing ML training results, benchmark evaluations, and capture recordings. The architecture prioritizes:

1. **Maintainability** - Small, focused files that fit in LLM context windows
2. **Separation of concerns** - Data loading, processing, and presentation are separate
3. **Standalone capability** - Generated HTML files work offline without a server
4. **No build step** - CDN-loaded libraries, no webpack/vite required

## Technology Stack

| Layer | Technology | Rationale |
|-------|------------|-----------|
| Data Processing | Pure Python + Pydantic | Type-safe, testable |
| HTML Structure | Jinja2 templates | Industry standard, well-understood |
| Visualization | Plotly | Best standalone export support |
| Styling | Tailwind CSS (CDN) | Utility-first, no build step |
| Interactivity | Alpine.js (CDN) | Lightweight (~15KB), declarative |

## Directory Structure

```
openadapt-viewer/
├── pyproject.toml
├── README.md
├── ARCHITECTURE.md              # This file
├── src/
│   └── openadapt_viewer/
│       ├── __init__.py          # Package exports
│       ├── cli.py               # CLI entry point
│       │
│       ├── core/                # Shared utilities
│       │   ├── __init__.py
│       │   ├── types.py         # Pydantic models, type definitions
│       │   ├── data_loader.py   # Common data loading utilities
│       │   └── html_builder.py  # Jinja2 environment setup
│       │
│       ├── templates/           # Jinja2 templates
│       │   ├── base.html        # Base template with CDN imports
│       │   └── components/      # Reusable HTML components
│       │       ├── header.html
│       │       └── navigation.html
│       │
│       └── viewers/             # Vertical slices by viewer type
│           ├── __init__.py
│           └── benchmark/       # Benchmark viewer
│               ├── __init__.py
│               ├── data.py      # Data models and loading
│               └── generator.py # HTML generation logic
```

## Key Design Patterns

### 1. Vertical Slice Architecture

Each viewer type (benchmark, training, recording) is a self-contained module with:
- **data.py** - Pydantic models and data loading functions
- **generator.py** - HTML generation logic
- **templates/** (optional) - Viewer-specific templates

This allows LLMs to understand and modify one viewer without loading the entire codebase.

### 2. Template Inheritance

All templates inherit from `base.html`, which provides:
- CDN imports for Tailwind CSS, Alpine.js, and Plotly
- Common header and navigation components
- Dark mode support
- Responsive layout

```html
{% extends "base.html" %}
{% block title %}My Page{% endblock %}
{% block content %}
  <h1>Page content here</h1>
{% endblock %}
```

### 3. Data/Presentation Separation

Data loading and HTML generation are strictly separated:

```python
# data.py - Pure data operations
from pydantic import BaseModel

class BenchmarkTask(BaseModel):
    task_id: str
    status: str
    metrics: dict

def load_benchmark_data(path: str) -> list[BenchmarkTask]:
    # Load and validate data, no HTML concerns
    ...
```

```python
# generator.py - HTML generation only
from .data import load_benchmark_data

def generate_benchmark_html(data_path: str, output_path: str) -> None:
    tasks = load_benchmark_data(data_path)
    # Render templates with data
    ...
```

### 4. Standalone HTML Generation

Generated HTML files are fully self-contained:
- Plotly.js can be embedded or loaded from CDN
- Data is embedded as inline JSON
- No external dependencies required for viewing

```python
# CDN mode (smaller file, requires internet)
fig.to_html(include_plotlyjs='cdn')

# Standalone mode (larger file, works offline)
fig.to_html(include_plotlyjs=True)
```

## File Size Guidelines

To maintain LLM-friendliness:
- Keep files under **500 lines**
- One responsibility per file
- Use type hints throughout
- Add docstrings explaining intent, not mechanics

## Adding a New Viewer

1. Create a new directory under `viewers/`:
   ```
   viewers/myviewer/
   ├── __init__.py
   ├── data.py
   └── generator.py
   ```

2. Define Pydantic models in `data.py`

3. Implement generation logic in `generator.py`

4. Add CLI command in `cli.py`

5. Update this document

## CDN Resources

The following CDN resources are loaded in `base.html`:

| Library | CDN URL | Version | Size |
|---------|---------|---------|------|
| Tailwind CSS | cdn.tailwindcss.com | 3.x | ~100KB (JIT) |
| Alpine.js | cdn.jsdelivr.net/npm/alpinejs | 3.x | ~15KB |
| Plotly.js | cdn.plot.ly/plotly-2.32.0.min.js | 2.32.0 | ~3.5MB |

For offline/standalone mode, Plotly.js is embedded directly in the HTML.

## Testing

Run tests with:
```bash
uv run pytest
```

Test files should mirror the source structure:
```
tests/
├── test_core/
│   ├── test_types.py
│   ├── test_data_loader.py
│   └── test_html_builder.py
└── test_viewers/
    └── test_benchmark/
        ├── test_data.py
        └── test_generator.py
```

## Related Projects

- **openadapt-ml** - ML training pipeline (source of training data)
- **openadapt-evals** - Benchmark evaluation infrastructure
- **openadapt-capture** - Recording capture tool
