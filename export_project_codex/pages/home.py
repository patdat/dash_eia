from dash import html
import dash_bootstrap_components as dbc

from components.cards import build_feature_card, build_stat_card


def build_home_page():
    stats = [
        ("Coverage", "24 Modules", "+3 this quarter", "metric-blue"),
        ("Latency", "180 ms", "-24 ms week over week", "metric-green"),
        ("Availability", "99.94%", "+0.11%", "metric-orange"),
        ("Open Work", "7 Items", "-5 resolved", "metric-red"),
    ]
    features = [
        (
            "Config-Driven Navigation",
            "Sidebar groups and routes live in one file, so the shell is easy to port and reshape.",
            "/market/overview",
            "accent-blue",
        ),
        (
            "Reusable Page Framing",
            "Each page already has a consistent title band, surface cards, and spacing rules.",
            "/operations/performance",
            "accent-green",
        ),
        (
            "Brand-Ready Styling",
            "Logo, colors, typography, and sidebar behavior are separated from business logic.",
            "/research/scenario-lab",
            "accent-red",
        ),
    ]

    return html.Div(
        [
            html.Section(
                [
                    html.Div("Dashboard Shell", className="page-eyebrow"),
                    html.H1("Portable Layout Export", className="page-title"),
                    html.P(
                        "This is the essential visual structure extracted for reuse in a different Dash project.",
                        className="page-summary",
                    ),
                ],
                className="page-hero",
            ),
            dbc.Row(
                [dbc.Col(build_stat_card(*stat), lg=3, md=6) for stat in stats],
                className="g-4 section-block",
            ),
            dbc.Row(
                [dbc.Col(build_feature_card(*feature), lg=4) for feature in features],
                className="g-4 section-block",
            ),
        ],
        className="page-shell",
    )
