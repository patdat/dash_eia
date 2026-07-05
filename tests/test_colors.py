import re
from src.utils import colors

HEX = re.compile(r"^#[0-9A-Fa-f]{6}$")

def test_accent_is_muted_blue():
    assert colors.BLUE == "#0072ab"
    assert colors.BRAND_BLUE == "#00ADEF"

def test_year_colors_accent_then_grays():
    assert len(colors.YEAR_COLORS) == 5
    assert colors.YEAR_COLORS[0] == colors.BLUE
    for c in colors.YEAR_COLORS:
        assert HEX.match(c)

def test_public_names_present():
    for name in ["MA_COLORS", "EVOLUTION_COLORS", "CHART_SEQUENCE",
                 "POSITIVE", "NEGATIVE", "COLORSCALE_DIVERGING"]:
        assert hasattr(colors, name)
    assert len(colors.MA_COLORS) == 3
    assert len(colors.EVOLUTION_COLORS) == 5
