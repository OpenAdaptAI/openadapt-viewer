"""Reusable UI components for OpenAdapt viewers.

This module provides building blocks for creating viewer HTML:
- screenshot_display: Screenshot with click/highlight overlays
- playback_controls: Play/pause/speed controls for step playback
- timeline: Progress bar for step navigation
- action_display: Format actions (click, type, scroll, etc.)
- metrics_card/metrics_grid: Statistics display cards
- filter_bar: Filter dropdowns and search
- selectable_list: List with selection support
- badge: Status badges (pass/fail, etc.)

All components return HTML strings that can be composed together.
"""

from openadapt_viewer.components.screenshot import screenshot_display
from openadapt_viewer.components.playback import playback_controls
from openadapt_viewer.components.timeline import timeline
from openadapt_viewer.components.action_display import action_display
from openadapt_viewer.components.metrics import metrics_card, metrics_grid
from openadapt_viewer.components.filters import filter_bar, filter_dropdown
from openadapt_viewer.components.list_view import selectable_list, list_item
from openadapt_viewer.components.badge import badge

__all__ = [
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
]
