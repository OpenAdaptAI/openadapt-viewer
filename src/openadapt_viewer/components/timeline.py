"""Timeline component for step progress visualization.

This component provides:
- Progress bar showing current position
- Click-to-seek functionality
- Optional step markers
- Episode segmentation visualization (Phase 1)
"""

from __future__ import annotations


def timeline(
    step_count: int = 1,
    current_step: int = 0,
    step_labels: list[str] | None = None,
    clickable: bool = True,
    show_markers: bool = False,
    alpine_data_name: str = "playback",
    class_name: str = "",
    episodes: list[dict] | None = None,
) -> str:
    """Render a timeline progress bar with optional episode segmentation.

    Args:
        step_count: Total number of steps
        current_step: Current step index (0-based)
        step_labels: Optional labels for start/end markers
        clickable: Whether clicking seeks to that position
        show_markers: Whether to show start/end markers
        alpine_data_name: Alpine.js x-data variable name for binding
        class_name: Additional CSS classes
        episodes: Optional list of episode segments [{task_id, steps}]

    Returns:
        HTML string for the timeline
    """
    extra_class = f" {class_name}" if class_name else ""

    # Calculate progress percentage
    progress = ((current_step + 1) / step_count * 100) if step_count > 0 else 0

    # Click handler for seeking
    click_handler = ""
    if clickable:
        click_handler = f'''@click="(e) => {{
            const rect = $el.getBoundingClientRect();
            const clickX = e.clientX - rect.left;
            const percent = clickX / rect.width;
            {alpine_data_name}.currentStep = Math.floor(percent * {alpine_data_name}.totalSteps);
            if ({alpine_data_name}.currentStep >= {alpine_data_name}.totalSteps) {{
                {alpine_data_name}.currentStep = {alpine_data_name}.totalSteps - 1;
            }}
        }}"'''

    # Episode segments (Phase 1: Visual segments only)
    episode_segments_html = ""
    episode_labels_html = ""
    if episodes:
        # Build episode segments
        segments = []
        labels = []
        episode_colors = [
            "linear-gradient(135deg, #3b82f6 0%, #2563eb 100%)",  # Blue
            "linear-gradient(135deg, #8b5cf6 0%, #7c3aed 100%)",  # Purple
            "linear-gradient(135deg, #ec4899 0%, #db2777 100%)",  # Pink
            "linear-gradient(135deg, #f59e0b 0%, #d97706 100%)",  # Orange
            "linear-gradient(135deg, #10b981 0%, #059669 100%)",  # Green
        ]

        for idx, episode in enumerate(episodes):
            task_id = episode.get("task_id", f"Task {idx + 1}")
            step_start = episode.get("step_start", 0)
            step_end = episode.get("step_end", step_count - 1)

            # Calculate position and width as percentages
            left_percent = (step_start / step_count * 100) if step_count > 0 else 0
            width_percent = ((step_end - step_start + 1) / step_count * 100) if step_count > 0 else 0

            # Rotate through colors
            color = episode_colors[idx % len(episode_colors)]

            # Episode segment
            segments.append(f'''
                <div class="oa-episode-segment"
                     style="left: {left_percent}%; width: {width_percent}%; background: {color};"
                     title="{task_id}">
                </div>
            ''')

            # Episode label
            labels.append(f'''
                <div class="oa-episode-label"
                     style="left: {left_percent}%; width: {width_percent}%;"
                     title="{task_id}">
                    <span>{task_id}</span>
                </div>
            ''')

        episode_segments_html = "".join(segments)
        episode_labels_html = f'''
        <div class="oa-episode-labels">
            {"".join(labels)}
        </div>
        '''

    # Markers
    markers_html = ""
    if show_markers:
        start_label = step_labels[0] if step_labels and len(step_labels) > 0 else "1"
        end_label = step_labels[-1] if step_labels and len(step_labels) > 1 else str(step_count)
        markers_html = f'''
        <div class="oa-timeline-markers">
            <span>{start_label}</span>
            <span>{end_label}</span>
        </div>
        '''

    return f'''<div class="oa-timeline{extra_class}">
    {episode_labels_html}
    <div class="oa-timeline-track" {click_handler}
         style="cursor: {'pointer' if clickable else 'default'}; position: relative;">
        {episode_segments_html}
        <div class="oa-timeline-progress"
             :style="'width: ' + (({alpine_data_name}.currentStep + 1) / {alpine_data_name}.totalSteps * 100) + '%'"
             style="width: {progress}%; position: relative; z-index: 10;"></div>
    </div>
    {markers_html}
</div>'''


def timeline_css() -> str:
    """Return CSS for episode timeline visualization.

    This CSS should be added to PageBuilder custom CSS.

    Returns:
        CSS string for episode timeline styling
    """
    return """
/* Episode Timeline Styles (Phase 1: Basic Segmentation) */
.oa-episode-labels {
    position: relative;
    height: 24px;
    margin-bottom: 8px;
}

.oa-episode-label {
    position: absolute;
    top: 0;
    height: 100%;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 11px;
    font-weight: 600;
    color: var(--oa-text-muted);
    border-radius: 4px;
    background: rgba(255, 255, 255, 0.03);
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
}

.oa-episode-label span {
    padding: 0 8px;
    overflow: hidden;
    text-overflow: ellipsis;
}

.oa-episode-label:hover {
    background: rgba(255, 255, 255, 0.08);
    color: var(--oa-text-primary);
    z-index: 5;
}

.oa-episode-segment {
    position: absolute;
    top: 0;
    height: 100%;
    border-right: 1px solid rgba(255, 255, 255, 0.1);
    transition: all 0.2s ease;
    opacity: 0.6;
}

.oa-episode-segment:hover {
    opacity: 0.8;
}

.oa-timeline-track {
    position: relative;
}

.oa-timeline-progress {
    position: relative;
    z-index: 10;
}
"""
