import plotly.graph_objs as go

from src.utils import colors
from src.utils.plotly_theme import FONT_FAMILY, apply_minimal_chrome


def test_chrome_sets_white_bg_and_inter_font():
    layout = go.Layout(xaxis=dict(), yaxis=dict())
    out = apply_minimal_chrome(layout)
    assert out.paper_bgcolor == colors.WHITE
    assert out.plot_bgcolor == colors.WHITE
    assert "Inter" in out.font.family
    assert FONT_FAMILY.startswith("Inter")


def test_chrome_sets_light_gridlines():
    layout = go.Layout(xaxis=dict(), yaxis=dict())
    out = apply_minimal_chrome(layout)
    assert out.xaxis.gridcolor == colors.GRAY_200
    assert out.yaxis.gridcolor == colors.GRAY_200
