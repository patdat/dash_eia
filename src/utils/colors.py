"""Centralized color palette for EIA Dash application.

All colors used in charts, buttons, and UI elements are defined here.
Import from this module instead of hardcoding hex values.
"""

# === Brand Palette (muted accent scheme) ===
BLACK      = "#000000"
BRAND_BLUE = "#00ADEF"   # logo/brand only
BLUE       = "#0072ab"   # primary accent
RED        = "#c8102e"   # muted semantic negative
GREEN      = "#1a7f42"   # muted semantic positive
ORANGE     = "#b45d0e"   # muted amber
PURPLE     = "#5c6b7f"   # de-emphasized -> slate

# === Neutrals ===
WHITE    = "#FFFFFF"
GRAY_50  = "#fafbfc"
GRAY_200 = "#e5e8ec"
GRAY_300 = "#d3d8de"
GRAY_400 = "#b8c0cb"
GRAY_500 = "#8b97a6"
GRAY_600 = "#5c6b7f"
GRAY_800 = "#1a2332"

# === Chart Color Sequences (accent + grays) ===
YEAR_COLORS      = [BLUE, GRAY_600, GRAY_500, GRAY_400, GRAY_300]
MA_COLORS        = [BLUE, GRAY_500, GRAY_400]
EVOLUTION_COLORS = [BLUE, GRAY_600, GRAY_500, GRAY_400, GRAY_300]
CHART_SEQUENCE   = [BLUE, GRAY_600, GRAY_500, RED, GREEN, GRAY_400]

# === Semantic Aliases ===
POSITIVE = GREEN
NEGATIVE = RED

# === Plotly Colorscales (built-in names) ===
COLORSCALE_DIVERGING  = "RdBu"
COLORSCALE_SEQUENTIAL = "Viridis"
COLORSCALE_HEATMAP    = "RdYlGn"
COLORSCALE_EFFICIENCY = [
    [0.0, "#ef5350"],    # Red (worst) — light enough for dark text
    [0.2, "#ff9800"],    # Orange
    [0.4, "#ffee58"],    # Yellow
    [0.5, "#fffde7"],    # Very light yellow (neutral)
    [0.6, "#81d4fa"],    # Light blue
    [0.8, "#42a5f5"],    # Medium blue
    [1.0, "#1e88e5"],    # Blue (best) — not too dark for readability
]
