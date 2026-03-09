from dash import html
import dash_bootstrap_components as dbc


def build_sidebar(brand, nav_sections):
    nav_items = [dbc.NavLink("Home", href="/", active="exact", className="nav-link")]

    for section in nav_sections:
        nav_items.append(
            dbc.NavItem(
                [
                    dbc.Button(
                        section["label"],
                        id={"type": "nav-toggle", "index": section["id"]},
                        className=f"sidebar-button page-button {'open' if section['initial_open'] else 'closed'}",
                        n_clicks=0,
                    ),
                    dbc.Collapse(
                        dbc.Nav(
                            [
                                dbc.NavLink(
                                    link["label"],
                                    href=link["href"],
                                    active="exact",
                                    className="nav-link",
                                )
                                for link in section["links"]
                            ],
                            vertical=True,
                            pills=True,
                        ),
                        id={"type": "nav-collapse", "index": section["id"]},
                        is_open=section["initial_open"],
                    ),
                ]
            )
        )

    return html.Aside(
        [
            html.Div(style={"height": "24px"}),
            html.Div(
                [
                    html.A(
                        html.Img(
                            src=brand["logo_src"],
                            alt=brand["name"],
                            className="brand-logo",
                        ),
                        href=brand["href"],
                        className="brand-logo-link",
                    ),
                    html.A(brand["name"], href=brand["href"], className="brand-name"),
                ],
                className="brand-lockup",
            ),
            html.Div(style={"height": "24px"}),
            dbc.Nav(nav_items, vertical=True, pills=True, className="sidebar-nav"),
        ],
        className="sidebar d-flex flex-column vh-100",
    )
