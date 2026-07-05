"""Sidebar shell built from the declarative navigation config."""

from dash import html
import dash_bootstrap_components as dbc


def _nav_link(label, href, icon=None):
    children = []
    if icon:
        children.append(html.I(className=f"fa-solid {icon} nav-icon"))
    children.append(html.Span(label, className="nav-label"))
    extra = "" if icon else " nav-link-child"
    return dbc.NavLink(children, href=href, active="exact", className=f"nav-link{extra}")


def build_sidebar(brand, home, nav_sections):
    nav_items = [_nav_link(home["label"], home["href"], home["icon"])]

    for section in nav_sections:
        state = "open" if section["initial_open"] else "closed"
        nav_items.append(
            dbc.NavItem([
                dbc.Button(
                    [
                        html.Span([
                            html.I(className=f"fa-solid {section['icon']} nav-section-icon"),
                            html.Span(section["label"], className="nav-section-label"),
                        ], className="nav-section-left"),
                        html.I(className="fa-solid fa-chevron-down nav-section-chevron"),
                    ],
                    id={"type": "nav-toggle", "index": section["id"]},
                    className=f"sidebar-button page-button {state}",
                    n_clicks=0,
                ),
                dbc.Collapse(
                    dbc.Nav(
                        [_nav_link(l["label"], l["href"]) for l in section["links"]],
                        vertical=True, pills=True,
                    ),
                    id={"type": "nav-collapse", "index": section["id"]},
                    is_open=section["initial_open"],
                ),
            ])
        )

    return html.Aside(
        [
            html.Div([
                html.A(
                    html.Img(src=brand["logo_src"], alt=brand["name"], className="brand-logo"),
                    href=brand["href"], target="_blank", rel="noopener noreferrer",
                    className="brand-logo-link",
                ),
                html.A(
                    brand["name"], href=brand["href"], target="_blank",
                    rel="noopener noreferrer", className="brand-name",
                ),
            ], className="brand-lockup"),
            dbc.Nav(nav_items, vertical=True, pills=True, className="sidebar-nav"),
        ],
        className="sidebar d-flex flex-column vh-100",
    )


def compute_collapse_state(nav_sections, is_open_list, triggered_index):
    """Flip the triggered section; return (new_open_list, new_classnames)."""
    new_open = list(is_open_list)
    classes = []
    for i, section in enumerate(nav_sections):
        if section["id"] == triggered_index:
            new_open[i] = not new_open[i]
        classes.append(f"sidebar-button page-button {'open' if new_open[i] else 'closed'}")
    return new_open, classes
