# openadapt-viewer

Standalone HTML viewer generation for OpenAdapt ML dashboards and benchmarks.

## Overview

openadapt-viewer generates self-contained HTML files for visualizing:
- Benchmark evaluation results (WAA, WebArena, OSWorld)
- ML training metrics and loss curves
- Capture recordings with action predictions

Generated files work offline without requiring a server.

## Installation

```bash
pip install openadapt-viewer
```

Or with uv:
```bash
uv add openadapt-viewer
```

## Quick Start

### Generate a Benchmark Viewer

```python
from openadapt_viewer.viewers.benchmark import generate_benchmark_html

# From a benchmark results directory
generate_benchmark_html(
    data_path="benchmark_results/run_001/",
    output_path="benchmark_viewer.html",
    standalone=True  # Embed all resources for offline viewing
)
```

### CLI Usage

```bash
# Generate benchmark viewer
openadapt-viewer benchmark --data benchmark_results/run_001/ --output viewer.html

# Generate with embedded resources (standalone)
openadapt-viewer benchmark --data benchmark_results/run_001/ --output viewer.html --standalone
```

## Architecture

The package uses:
- **Jinja2** for HTML templating with inheritance
- **Plotly** for interactive visualizations
- **Tailwind CSS** (CDN) for styling
- **Alpine.js** (CDN) for lightweight interactivity

See [ARCHITECTURE.md](ARCHITECTURE.md) for detailed design documentation.

## Development

```bash
# Clone the repo
git clone https://github.com/OpenAdaptAI/openadapt-viewer.git
cd openadapt-viewer

# Install with dev dependencies
uv sync --all-extras

# Run tests
uv run pytest

# Run linter
uv run ruff check .
```

## Project Structure

```
src/openadapt_viewer/
├── cli.py               # CLI entry point
├── core/                # Shared utilities
│   ├── types.py         # Pydantic models
│   ├── data_loader.py   # Data loading utilities
│   └── html_builder.py  # Jinja2 environment setup
├── templates/           # Jinja2 templates
│   ├── base.html        # Base template with CDN imports
│   └── components/      # Reusable components
└── viewers/             # Viewer implementations
    └── benchmark/       # Benchmark viewer
```

## License

MIT License - see LICENSE file for details.
