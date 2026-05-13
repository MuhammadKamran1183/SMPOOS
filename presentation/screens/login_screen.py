import random

import dash_bootstrap_components as dbc
from dash import html

from presentation.theme import INPUT_STYLE, PAGE_STYLE, PANEL_STYLE


LOGIN_PROMPTS = (
    "Enter your admin account details to continue.",
    "Sign in to view live operations, alerts, and analytics.",
    "Use your assigned account to access the SMPOOS dashboard.",
)

TITLE_STYLE = {"color": "#93c5fd", "fontWeight": "700", "letterSpacing": "0.08em", "textTransform": "uppercase", "fontSize": "0.8rem"}
HEADING_STYLE = {"color": "#f8fafc", "fontWeight": "800"}
SUBTITLE_STYLE = {"color": "#cbd5e1"}
ALERT_STYLE = {"borderRadius": "14px", "border": "0"}
HR_STYLE = {"borderColor": "rgba(148,163,184,0.22)"}

BUTTON_PRIMARY_STYLE = {"background": "linear-gradient(135deg, #2563eb, #38bdf8)", "border": "0", "borderRadius": "12px", "fontWeight": "700", "padding": "12px"}
BUTTON_ADMIN_STYLE = {"background": "linear-gradient(135deg, #7c3aed, #8b5cf6)", "border": "0", "borderRadius": "12px", "fontWeight": "600"}
BUTTON_HARBOUR_STYLE = {"background": "linear-gradient(135deg, #0891b2, #06b6d4)", "border": "0", "borderRadius": "12px", "fontWeight": "600"}
BUTTON_SAFETY_STYLE = {"background": "linear-gradient(135deg, #ea580c, #f97316)", "border": "0", "borderRadius": "12px", "fontWeight": "600"}


def login_layout():
    return html.Div(
        dbc.Container(
            [
                dbc.Row(
                    dbc.Col(
                        dbc.Card(
                            dbc.CardBody(
                                [
                                    html.Div("SMPOOS Control Centre", style=TITLE_STYLE),
                                    html.H2("Sign In", className="mb-2", style=HEADING_STYLE),
                                    html.Div("Access live port operations, alerts, analytics, and admin tools from one dashboard.", className="mb-3", style=SUBTITLE_STYLE),
                                    dbc.Alert(id="login-msg", color="info", is_open=True, children=random.choice(LOGIN_PROMPTS), style=ALERT_STYLE),
                                    dbc.Input(id="login-email", type="email", placeholder="Email", className="mb-2", style=INPUT_STYLE),
                                    dbc.Input(id="login-password", type="password", placeholder="Password", className="mb-3", style=INPUT_STYLE),
                                    dbc.Button("Sign In", id="login-submit", className="w-100 mb-3", style=BUTTON_PRIMARY_STYLE),
                                    html.Hr(style=HR_STYLE),
                                    html.Div("Demo Accounts", className="fw-bold", style={"color": "#f8fafc"}),
                                    html.Div("Click any account below to autofill the login form.", className="small mb-2", style={"color": "#cbd5e1"}),
                                    dbc.Button("Admin Demo: user6@portauthority.com / admin123", id="demo-admin", className="w-100 mb-2", style=BUTTON_ADMIN_STYLE),
                                    dbc.Button("Harbourmaster Demo: user19@portauthority.com / harbour123", id="demo-harbour", className="w-100 mb-2", style=BUTTON_HARBOUR_STYLE),
                                    dbc.Button("Safety/Security Demo: user12@portauthority.com / safety123", id="demo-safety", className="w-100", style=BUTTON_SAFETY_STYLE),
                                ]
                            ),
                            style={**PANEL_STYLE, "padding": "8px"},
                            className="shadow-lg",
                        ),
                        width=12,
                    ),
                    justify="center",
                ),
            ],
            style={"maxWidth": "620px"},
            className="py-5",
        ),
        style=PAGE_STYLE,
    )

