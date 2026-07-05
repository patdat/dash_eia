import re
from src.utils import colors

HEX = re.compile(r"^#[0-9A-Fa-f]{6}$")

def test_accent_is_muted_blue():
    assert colors.BLUE == "#0072ab"
    assert colors.BRAND_BLUE == "#00ADEF"

def test_year_colors_full_brand_palette():
    # Seasonality year lines use the distinct brand palette.
    assert colors.YEAR_COLORS == [
        colors.BLACK, colors.BRAND_BLUE, colors.BRAND_RED,
        colors.BRAND_GREEN, colors.BRAND_ORANGE, colors.BRAND_PURPLE,
    ]
    for c in colors.YEAR_COLORS:
        assert HEX.match(c)

def test_public_names_present():
    for name in ["MA_COLORS", "EVOLUTION_COLORS", "CHART_SEQUENCE",
                 "POSITIVE", "NEGATIVE", "COLORSCALE_DIVERGING"]:
        assert hasattr(colors, name)
    assert len(colors.MA_COLORS) == 3
    assert len(colors.EVOLUTION_COLORS) == 5
