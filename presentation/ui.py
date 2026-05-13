import dash_bootstrap_components as dbc
from dash import html
from dash.dash_table import DataTable

from presentation.helpers import format_table_rows
from presentation.session import current_user, user_permissions
from presentation.theme import (
    ADMIN_ACTIVE_TAB_LABEL_STYLE,
    ADMIN_ACTIVE_TAB_STYLE,
    ADMIN_FORM_CARD_STYLE,
    ADMIN_PANEL_STYLE,
    ADMIN_TAB_LABEL_STYLE,
    ADMIN_TAB_STYLE,
    ADMIN_TABLE_CARD_STYLE,
    DATE_INPUT_STYLE,
    DATE_TIME_LABEL_STYLE,
    PAGE_STYLE,
    PANEL_STYLE,
    SECTION_TITLE_STYLE,
    TABLE_CELL_STYLE,
    TABLE_CSS,
    TABLE_DATA_STYLE_CONDITIONAL,
    TABLE_HEADER_STYLE,
    TABLE_STYLE,
    TIME_INPUT_STYLE,
)


def admin_datetime_row(date_id, time_id, date_label, time_label):
    return dbc.Row(
        [
            dbc.Col(
                [
                    html.Div(date_label, style=DATE_TIME_LABEL_STYLE),
                    dbc.Input(id=date_id, type="date", style=DATE_INPUT_STYLE),
                ],
                md=6,
            ),
            dbc.Col(
                [
                    html.Div(time_label, style=DATE_TIME_LABEL_STYLE),
                    dbc.Input(id=time_id, type="time", style=TIME_INPUT_STYLE),
                ],
                md=6,
            ),
        ],
        className="g-2 mb-2",
    )


def nav_link(label, href, active_path, accent):
    is_active = active_path == href
    return dbc.NavLink(
        label,
        href=href,
        active=is_active,
        style={
            "color": "#e2e8f0" if not is_active else "#ffffff",
            "background": accent if is_active else "rgba(15,23,42,0.42)",
            "border": "1px solid rgba(255,255,255,0.05)" if not is_active else "1px solid rgba(255,255,255,0.16)",
            "borderRadius": "14px",
            "padding": "12px 14px",
            "marginBottom": "10px",
            "fontWeight": "600",
            "boxShadow": "0 12px 24px rgba(15,23,42,0.24)" if is_active else "none",
        },
    )


def admin_form_card(title, children):
    return dbc.Card(
        dbc.CardBody(
            [
                html.Div("Admin Editor", style={"color": "#93c5fd", "fontWeight": "700", "letterSpacing": "0.08em", "textTransform": "uppercase", "fontSize": "0.74rem"}),
                html.H5(title, className="mb-3 mt-1", style=SECTION_TITLE_STYLE),
                *children,
            ],
            style={"padding": "18px"},
        ),
        style=ADMIN_FORM_CARD_STYLE,
    )


def admin_tab(content, label, disabled=False):
    return dbc.Tab(
        content,
        label=label,
        disabled=disabled,
        tab_style=ADMIN_TAB_STYLE,
        active_tab_style=ADMIN_ACTIVE_TAB_STYLE,
        label_style=ADMIN_TAB_LABEL_STYLE,
        active_label_style=ADMIN_ACTIVE_TAB_LABEL_STYLE,
    )


def admin_table_card(title, rows, columns, page_size=10, table_id=None):
    table_props = {
        "columns": [{"name": c.replace("_", " ").title(), "id": c} for c in columns],
        "data": format_table_rows(rows, columns),
        "page_size": page_size,
        "css": TABLE_CSS,
        "style_table": TABLE_STYLE,
        "style_cell": TABLE_CELL_STYLE,
        "style_header": TABLE_HEADER_STYLE,
        "style_data_conditional": TABLE_DATA_STYLE_CONDITIONAL,
    }
    if table_id is not None:
        table_props["id"] = table_id

    return dbc.Card(
        dbc.CardBody(
            [
                html.Div("Live Records", style={"color": "#60a5fa", "fontWeight": "700", "letterSpacing": "0.08em", "textTransform": "uppercase", "fontSize": "0.74rem"}),
                html.H5(title, className="mb-3 mt-1", style=SECTION_TITLE_STYLE),
                DataTable(**table_props),
            ],
            style={"padding": "18px"},
        ),
        style=ADMIN_TABLE_CARD_STYLE,
    )


def sidebar(active_path):
    perms = user_permissions()
    links = []
    if "view_management_dashboard" in perms:
        links.append(nav_link("Dashboard", "/dashboard", active_path, "linear-gradient(135deg, #2563eb, #3b82f6)"))
    if "view_monitoring" in perms:
        links.append(nav_link("Monitor Port", "/monitoring", active_path, "linear-gradient(135deg, #0f766e, #14b8a6)"))
    if "view_admin_portal" in perms:
        links.append(nav_link("Admin", "/admin", active_path, "linear-gradient(135deg, #7c3aed, #8b5cf6)"))
    if "view_notification_engine" in perms:
        links.append(nav_link("Notification Engine", "/notification-engine", active_path, "linear-gradient(135deg, #ea580c, #f97316)"))
    if "view_analytics" in perms:
        links.append(nav_link("Analytics", "/analytics", active_path, "linear-gradient(135deg, #0891b2, #06b6d4)"))
    return dbc.Nav(links, vertical=True, pills=True, className="p-2")


def topbar():
    user = current_user() or {}
    name = user.get("name", "Guest")
    return dbc.Row(
        [
            dbc.Col(
                [
                    html.Div("Port Control Centre", style={"color": "#93c5fd", "fontWeight": "700", "letterSpacing": "0.08em", "textTransform": "uppercase", "fontSize": "0.8rem"}),
                    html.H3("Live Operations Dashboard", className="mb-0", style={"color": "#f8fafc"}),
                ],
                width=True,
            ),
            dbc.Col(
                dbc.ButtonGroup(
                    [
                        dbc.Badge(name, className="p-2 px-3", style={"background": "linear-gradient(135deg, #334155, #1e293b)", "border": "1px solid rgba(148,163,184,0.24)", "fontSize": "0.9rem"}),
                        dbc.Button("Sign Out", id="logout-btn", style={"background": "linear-gradient(135deg, #2563eb, #38bdf8)", "border": "0", "fontWeight": "700"}),
                    ],
                    size="sm",
                ),
                width="auto",
            ),
        ],
        className="align-items-center mb-3",
    )


def shell(content, active_path):
    return html.Div(
        dbc.Container(
            [
                dbc.Row(
                    [
                        dbc.Col(
                            html.Div(
                                [
                                    html.H3("SMPOOS", className="mb-1", style={"color": "#f8fafc", "fontWeight": "800"}),
                                    html.Div("Smart Maritime Port Operations", className="small mb-4", style={"color": "#93c5fd"}),
                                    sidebar(active_path),
                                ],
                                style={**PANEL_STYLE, "padding": "20px 16px", "position": "sticky", "top": "16px"},
                            ),
                            xs=12,
                            lg=2,
                        ),
                        dbc.Col(
                            html.Div(
                                [
                                    topbar(),
                                    dbc.Alert(id="toast", is_open=False, duration=3000, color="success", style={"borderRadius": "14px", "border": "0"}),
                                    content,
                                ],
                                style={**PANEL_STYLE, "padding": "20px"},
                            ),
                            xs=12,
                            lg=10,
                        ),
                    ],
                    className="g-3",
                ),
            ],
            fluid=True,
            className="py-3 px-3",
        ),
        style=PAGE_STYLE,
    )
