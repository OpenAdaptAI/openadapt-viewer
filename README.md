# openadapt-viewer

[![Test](https://github.com/OpenAdaptAI/openadapt-viewer/actions/workflows/test.yml/badge.svg)](https://github.com/OpenAdaptAI/openadapt-viewer/actions/workflows/test.yml)
[![PyPI](https://img.shields.io/pypi/v/openadapt-viewer.svg)](https://pypi.org/project/openadapt-viewer/)
[![Python](https://img.shields.io/pypi/pyversions/openadapt-viewer)](https://pypi.org/project/openadapt-viewer/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://github.com/OpenAdaptAI/openadapt-viewer/blob/main/LICENSE)

openadapt-viewer turns the results of a GUI agent run into one HTML file. Open
it in a browser to see pass and fail counts, filter the task list, and step
through each task's screenshots, with the action and the agent's reasoning
under each one. There is no server to run. Keep the file with the run, or
embed the screenshots in it and send it to a colleague.

It is for developers who run agents against desktop or web tasks, or who build
on [OpenAdapt](https://github.com/OpenAdaptAI/OpenAdapt), and want to see what
happened in a run without writing a dashboard.

## Quick start

```bash
pip install openadapt-viewer
openadapt-viewer demo --output viewer.html
```

```
Generating demo viewer with 10 sample tasks...
Generated: viewer.html
```

Open `viewer.html` in a browser and select a task:

![The demo viewer: summary cards, results by domain, filters, the task list, and the detail panel for a failed task with playback controls](https://raw.githubusercontent.com/OpenAdaptAI/openadapt-viewer/main/docs/images/demo_viewer.png)

The demo generates 10 sample tasks with random results, so your numbers will
differ.
Add `--open` to open the page in your default browser.

## View your own run

`openadapt-viewer benchmark` reads a run from a directory laid out like this:

```
my-run/
├── metadata.json          {"benchmark_name": "Notepad smoke test", "model_id": "my-agent-v2"}
└── tasks/
    └── task_001/
        ├── task.json      {"task_id": "task_001", "instruction": "Open Notepad and type hello", "domain": "office"}
        ├── execution.json {"success": true, "steps": [...]}
        └── screenshots/
            ├── step_000.png
            └── step_001.png
```

Each entry in `steps` is one action. The viewer shows `description` under the
screenshot, and `reasoning` below it when present:

```json
{"action_type": "click", "action_details": {"description": "Click the Start button"}, "reasoning": "Notepad is not open yet"}
```

`step_000.png` is the screenshot for the first step, `step_001.png` for the
second, and so on. A failed task can carry an `error` string in
`execution.json`, which the viewer shows above its steps. Then build the page:

```bash
openadapt-viewer benchmark --data my-run --output my-run.html --standalone
```

```
Generating benchmark viewer from: my-run
Generated: my-run.html
```

`--standalone` embeds the screenshots and a pinned copy of Alpine.js (3.17.4,
MIT) in the HTML, so the file keeps its images and works offline after you move
it or attach it to an email. Without it, the page links to the PNG files and
loads Alpine.js from a CDN.

To view a recording made with
[openadapt-capture](https://github.com/OpenAdaptAI/openadapt-capture), pass the
recording directory as `--data` instead. It needs the `recording.db` that
openadapt-capture writes and an `episodes.json` from the segmentation step in
[openadapt-ml](https://github.com/OpenAdaptAI/openadapt-ml), which splits the
recording into tasks.

## Build your own page

Each component is a Python function that returns an HTML string, so you can
use one inside a template you already have. `PageBuilder` puts components
together into a complete page with the stylesheet inlined:

```python
from openadapt_viewer.builders import PageBuilder
from openadapt_viewer.components import badge, metrics_grid

page = PageBuilder(title="Nightly eval", dark_mode=False)
page.add_header(title="Nightly eval", subtitle="run 2026-10-14")
page.add_section(
    metrics_grid([
        {"label": "Tasks", "value": 42},
        {"label": "Passed", "value": 39, "color": "success"},
        {"label": "Failed", "value": 3, "color": "error"},
    ]),
    title="Summary",
)
page.add_section(badge("Pass", color="success"))
print(page.render_to_file("eval.html"))
```

`dark_mode=False` opens the page in the light theme. The button in the header
switches themes either way. The
[component reference](https://github.com/OpenAdaptAI/openadapt-viewer/blob/main/docs/COMPONENTS.md)
lists all 22 components with their signatures, including screenshot overlays,
action timelines, filter bars, side-by-side comparisons, and failure-analysis
panels.

## Play back recorded steps

`generate_capture_html` writes a player for a list of steps, with play, pause,
and step controls:

```python
from openadapt_viewer.viewers.capture.generator import generate_capture_html

steps = [
    {"timestamp": 0.0, "duration": 1.2, "action": {"type": "click", "x": 0.42, "y": 0.31}},
    {"timestamp": 1.2, "duration": 2.4, "action": {"type": "type", "text": "Jane Doe"}},
    {"timestamp": 3.6, "duration": 0.9, "action": {"type": "click", "x": 0.78, "y": 0.64}},
]

print(generate_capture_html(
    capture_id="turn-off-nightshift",
    goal="Turn off Night Shift in Display settings",
    steps=steps,
    output_path="capture_viewer.html",
))
```

Give a step a `"screenshot"` key, holding a path relative to the HTML file or a
data URI, and the player shows that frame with a marker where the click landed.
`x` and `y` are fractions of the frame, so `0.42` means 42% of the way across.

## Limits

- As of October 2026, PyPI has version 0.2.0. It ignores `--standalone`, marks
  a task failed when its `execution.json` has no `task_id`, does not read
  `recording.db`, and its capture player does not render. Until a newer
  release is on PyPI, install from GitHub with
  `pip install git+https://github.com/OpenAdaptAI/openadapt-viewer`.
- Without `--standalone`, the page loads [Alpine.js](https://alpinejs.dev)
  from `cdn.jsdelivr.net`. Offline, the summary cards still render, but the
  task list and the playback controls do not work.
- The `benchmark` command reads the run layout above or an openadapt-capture
  recording. Results from other harnesses need converting to that layout first.
- Recordings made before 2026-07-17 store a `capture.db`, which this version
  does not read. The `benchmark` command stops with an error that names the
  openadapt-capture script that converts it.

## Other commands

`openadapt-viewer --help` lists every command.
`openadapt-viewer catalog scan --capture-dir DIR` indexes recordings into
`~/.openadapt/catalog.db` so that `openadapt-viewer segmentation` can find
them, and `openadapt-viewer catalog stats` prints the counts.

## Development

```bash
git clone https://github.com/OpenAdaptAI/openadapt-viewer && cd openadapt-viewer
uv sync --all-extras
uv run ruff check .
uv run pytest tests/ -v
```

Three test modules read recordings that openadapt-capture wrote, rather than
fixtures written to match this repository's idea of the schema. They skip
when no openadapt-capture checkout is found. Clone it alongside and point the
tests at it:

```bash
export OPENADAPT_CAPTURE_DIR=/path/to/openadapt-capture
export OPENADAPT_CAPTURE_EXAMPLES=$OPENADAPT_CAPTURE_DIR/examples/captures
```

CI runs Python 3.10 and 3.11 on Ubuntu and macOS. `ruff check .` is a blocking
check over the whole repository. To regenerate the screenshot above, run
`uv run python scripts/generate_demo_screenshot.py`.

## License

MIT. See [LICENSE](https://github.com/OpenAdaptAI/openadapt-viewer/blob/main/LICENSE).
