from dash import html
import dash_bootstrap_components as dbc


def build_stat_card(title, value, change, accent_class):
    return dbc.Card(
        dbc.CardBody(
            [
                html.Div(title, className="metric-label"),
                html.Div(value, className="metric-value"),
                html.Div(change, className=f"metric-delta {accent_class}"),
            ]
        ),
        className="metric-card",
    )


def build_feature_card(title, description, href, accent_class):
    return dbc.Card(
        dbc.CardBody(
            [
                html.Div(className=f"feature-accent {accent_class}"),
                html.H4(title, className="feature-title"),
                html.P(description, className="feature-copy"),
                dbc.Button("Open", href=href, className="feature-button", color="light"),
            ]
        ),
        className="feature-card",
    )
