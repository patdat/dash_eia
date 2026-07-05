from src.components.shell import build_sidebar, compute_collapse_state
from src.config.navigation import BRAND, HOME, NAV_SECTIONS


def test_build_sidebar_returns_aside_with_toggle_ids():
    side = build_sidebar(BRAND, HOME, NAV_SECTIONS)
    assert "sidebar" in side.className
    text = str(side)
    for s in NAV_SECTIONS:
        assert f"'index': '{s['id']}'" in text or f'"index": "{s["id"]}"' in text


def test_compute_collapse_state_toggles_only_triggered():
    sections = [{"id": "a"}, {"id": "b"}]
    open_list = [True, True]
    new_open, classes = compute_collapse_state(sections, open_list, "a")
    assert new_open == [False, True]
    assert classes[0].endswith("closed")
    assert classes[1].endswith("open")


def test_compute_collapse_state_reopens():
    sections = [{"id": "a"}]
    new_open, classes = compute_collapse_state(sections, [False], "a")
    assert new_open == [True]
    assert classes[0].endswith("open")
