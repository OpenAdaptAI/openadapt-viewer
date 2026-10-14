"""Screenshot display component with overlay support.

This component renders screenshots with optional overlays for:
- Click markers (human vs predicted)
- Bounding box highlights
- Labels and captions
"""

from __future__ import annotations

import base64
import html
from pathlib import Path
from typing import TypedDict


class Overlay(TypedDict, total=False):
    """Overlay marker definition."""

    type: str  # "click", "box", "highlight"
    x: float  # Normalized x coordinate (0-1)
    y: float  # Normalized y coordinate (0-1)
    width: float  # For box overlays, normalized width
    height: float  # For box overlays, normalized height
    label: str  # Label text (e.g., "H" for human, "AI" for predicted)
    color: str  # CSS color
    variant: str  # "human", "predicted", "error"


def screenshot_display(
    image_path: str | Path | None = None,
    width: int | None = 800,
    height: int | None = 450,
    overlays: list[Overlay] | None = None,
    caption: str | None = None,
    embed_image: bool = False,
    placeholder_text: str = "No screenshot available",
    class_name: str = "",
    alt: str = "Screenshot",
) -> str:
    """Render a screenshot with optional overlays.

    Overlay coordinates are fractions of the image, not of the container. The
    image and its overlays share one positioned frame that is exactly the size
    of the rendered image, so a box at ``x=0.25`` starts a quarter of the way
    across the picture even when the image is letterboxed inside a container of
    a different shape.

    A click overlay is centered on ``(x, y)``. A box overlay's ``(x, y)`` is its
    top-left corner, and ``width`` and ``height`` are fractions of the image.

    Args:
        image_path: Path to screenshot image (can be None for placeholder)
        width: Display width in pixels. ``None`` fills the parent's width.
        height: Display height in pixels. ``None`` lets the height follow the
            image's aspect ratio, so the container hugs the image. Pass
            ``width=None, height=None`` for a screenshot that scales with a
            narrow (for example, phone-width) page.
        overlays: List of overlay markers (clicks, boxes, etc.)
        caption: Optional caption text below image
        embed_image: If True, embed image as base64 data URI
        placeholder_text: Text to show when no image
        class_name: Additional CSS classes
        alt: Alternative text for the image

    Returns:
        HTML string for the screenshot display
    """
    overlays = overlays or []
    extra_class = f" {html.escape(class_name)}" if class_name else ""
    fluid = height is None
    if fluid:
        extra_class += " oa-screenshot-fluid"

    safe_alt = html.escape(alt)
    # A fixed-size container letterboxes the image. The cap goes on the image
    # itself, in pixels, because a percentage max-height inside the
    # shrink-wrapped frame would resolve against an auto height and be ignored.
    image_style = "" if fluid else f' style="max-height: {height}px;"'

    # Handle image source
    image_src: str | None = None
    if image_path is None:
        image_html = f'<div class="oa-screenshot-placeholder">{html.escape(placeholder_text)}</div>'
    elif embed_image:
        # Embed as base64 data URI
        path = Path(image_path)
        if path.exists():
            with open(path, "rb") as f:
                data = base64.b64encode(f.read()).decode()
            suffix = path.suffix.lower()
            mime = {
                ".png": "image/png",
                ".jpg": "image/jpeg",
                ".jpeg": "image/jpeg",
                ".gif": "image/gif",
                ".webp": "image/webp",
            }.get(suffix, "image/png")
            image_src = f"data:{mime};base64,{data}"
        else:
            image_html = (
                '<div class="oa-screenshot-placeholder">'
                f"Image not found: {html.escape(str(image_path))}</div>"
            )
    else:
        image_src = html.escape(str(image_path), quote=True)

    # Generate overlay markers
    overlay_html_parts = []
    for overlay in overlays:
        overlay_type = overlay.get("type", "click")
        x = overlay.get("x", 0)
        y = overlay.get("y", 0)
        label = overlay.get("label", "")
        variant = overlay.get("variant", "")
        color = overlay.get("color", "")

        variant_class = f" oa-overlay-{html.escape(variant)}" if variant else ""
        color_style = f" border-color: {html.escape(color)};" if color else ""
        label_html = (
            f'<span class="oa-overlay-label">{html.escape(label)}</span>'
            if label
            else ""
        )

        if overlay_type == "click":
            overlay_html_parts.append(
                f'<div class="oa-overlay oa-overlay-click{variant_class}" '
                f'style="left: {x * 100}%; top: {y * 100}%;{color_style}">'
                f"{label_html}"
                f"</div>"
            )
        elif overlay_type == "box":
            w = overlay.get("width", 0.1)
            h = overlay.get("height", 0.1)
            overlay_html_parts.append(
                f'<div class="oa-overlay oa-overlay-box{variant_class}" '
                f'style="left: {x * 100}%; top: {y * 100}%; '
                f'width: {w * 100}%; height: {h * 100}%;{color_style}">'
                f"{label_html}"
                f"</div>"
            )

    overlays_html = "\n".join(overlay_html_parts)

    if image_src is not None:
        # Overlays are positioned against this frame, which is the image's
        # own box, rather than against the container around it.
        image_html = (
            '<div class="oa-screenshot-frame">'
            f'<img src="{image_src}" alt="{safe_alt}" class="oa-screenshot-image"{image_style}>'
            f"{overlays_html}"
            "</div>"
        )
    elif overlays_html:
        # No picture to pin them to: keep them in the container, as before.
        image_html = f"{image_html}\n{overlays_html}"

    # Caption
    caption_html = (
        f'<div class="oa-screenshot-caption">{html.escape(caption)}</div>'
        if caption
        else ""
    )

    size_style = f"width: {width}px;" if width is not None else "width: 100%;"
    if height is not None:
        size_style += f" height: {height}px;"

    return f'''<div class="oa-screenshot-container{extra_class}" style="{size_style}">
    {image_html}
    {caption_html}
</div>'''
