"""Centralized color palette for EIA Dash application.

All colors used in charts, buttons, and UI elements are defined here.
Import from this module instead of hardcoding hex values.
"""

# === Brand Palette ===
BLACK   = "#000000"
BLUE    = "#00ADEF"
RED     = "#EC002B"
GREEN   = "#4AB04D"
ORANGE  = "#F68E2F"
PURPLE  = "#6A1B9A"

# === Neutrals ===
WHITE      = "#FFFFFF"
GRAY_50    = "#f4f5f9"    # Page background, range bands
GRAY_200   = "#dee2e6"    # Borders, dividers
GRAY_300   = "#bfbec4"    # Sidebar border, table headers, year 1 data
GRAY_500   = "#6c757d"    # Secondary text
GRAY_800   = "#2c3e50"    # Dark headings

# === Chart Color Sequences (ordered) ===
YEAR_COLORS      = [BLACK, BLUE, RED, GREEN, ORANGE]    # Seasonality: Year 3, Year 2, Year 1, Year 4, Year 5
MA_COLORS        = [BLUE, RED, GREEN]                    # 1m MA, 3m MA, 12m MA
EVOLUTION_COLORS = [RED, ORANGE, GRAY_300, BLUE, GREEN]  # DPR forecast releases (1-5)
CHART_SEQUENCE   = [RED, BLUE, ORANGE, GREEN, PURPLE, GRAY_300]  # General multi-series

# === Semantic Aliases ===
POSITIVE = GREEN
NEGATIVE = RED

# === Plotly Colorscales (built-in names) ===
COLORSCALE_DIVERGING  = "RdBu"
COLORSCALE_SEQUENTIAL = "Viridis"
COLORSCALE_HEATMAP    = "RdYlGn"
