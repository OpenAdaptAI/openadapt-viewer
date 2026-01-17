#!/bin/bash
# Example: Generate a standalone benchmark viewer with embedded data

set -e

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
RESULTS_DIR="/Users/abrichr/oa/src/openadapt-ml/benchmark_results"

# Check if benchmark_results exists
if [ ! -d "$RESULTS_DIR" ]; then
    echo "Error: benchmark_results directory not found at $RESULTS_DIR"
    echo "Run a benchmark first:"
    echo "  cd /Users/abrichr/oa/src/openadapt-ml"
    echo "  uv run python -m openadapt_ml.benchmarks.cli test-collection --tasks 5"
    exit 1
fi

# Find first run
RUN_NAME=$(ls -1 "$RESULTS_DIR" | grep -v ".json" | head -1)

if [ -z "$RUN_NAME" ]; then
    echo "Error: No benchmark runs found in $RESULTS_DIR"
    exit 1
fi

echo "Generating viewer for run: $RUN_NAME"

# Generate viewer
python "$SCRIPT_DIR/generator.py" \
    --results-dir "$RESULTS_DIR" \
    --run-name "$RUN_NAME" \
    --output /tmp/benchmark_viewer.html

echo ""
echo "✅ Generated: /tmp/benchmark_viewer.html"
echo ""
echo "Open in browser:"
echo "  open /tmp/benchmark_viewer.html"
