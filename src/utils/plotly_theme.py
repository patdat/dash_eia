"""Shared neutral Plotly chrome (white background, Inter font, light grid)."""

from src.utils.colors import WHITE, GRAY_200, GRAY_500, GRAY_800

FONT_FAMILY = "Inter, -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif"


def apply_minimal_chrome(layout):
    """Merge neutral chrome onto a go.Layout without dropping existing keys."""
    layout.update(
        paper_bgcolor=WHITE,
        plot_bgcolor=WHITE,
        font=dict(family=FONT_FAMILY, color=GRAY_800),
    )
    layout.xaxis.update(gridcolor=GRAY_200, linecolor=GRAY_200, spikecolor=GRAY_500)
    layout.yaxis.update(gridcolor=GRAY_200, linecolor=GRAY_200, spikecolor=GRAY_500)
    return layout
