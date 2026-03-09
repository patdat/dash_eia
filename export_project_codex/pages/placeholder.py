from dash import html
import dash_bootstrap_components as dbc


def build_placeholder_page(page):
    return html.Div(
        [
            html.Section(
                [
                    html.Div(page["eyebrow"], className="page-eyebrow"),
                    html.H1(page["title"], className="page-title"),
                    html.P(page["summary"], className="page-summary"),
                ],
                className="page-hero",
            ),
            dbc.Row(
                [
                    dbc.Col(
                        dbc.Card(
                            dbc.CardBody(
                                [
                                    html.H3("Suggested Modules", className="surface-title"),
                                    html.Ul(
                                        [html.Li(item, className="surface-list-item") for item in page["highlights"]],
                                        className="surface-list",
                                    ),
                                ]
                            ),
                            className="surface-card",
                        ),
                        lg=6,
                    ),
                    dbc.Col(
                        dbc.Card(
                            dbc.CardBody(
                                [
                                    html.H3("Implementation Notes", className="surface-title"),
                                    html.P(
                                        "Swap this placeholder body for your page-specific Dash components while keeping the shell classes intact.",
                                        className="surface-copy",
                                    ),
                                    html.P(
                                        "The sidebar, routing, spacing, and active-link behavior are already wired up.",
                                        className="surface-copy",
                                    ),
                                ]
                            ),
                            className="surface-card",
                        ),
                        lg=6,
                    ),
                ],
                className="g-4 section-block",
            ),
        ],
        className="page-shell",
    )
