import json
import os
import traceback
from enum import Enum

import dash
import dash_bootstrap_components as dbc
import matplotlib
matplotlib.use("Agg")
from dash import Input, Output, State, dcc, html
from dash.exceptions import PreventUpdate
from flask import Flask, session

from presentation.theme import (
    ADMIN_ACTIVE_TAB_LABEL_STYLE,
    ADMIN_ACTIVE_TAB_STYLE,
    ADMIN_FORM_CARD_STYLE,
    ADMIN_PANEL_STYLE,
    ADMIN_TAB_LABEL_STYLE,
    ADMIN_TAB_STYLE,
    ADMIN_TABLE_CARD_STYLE,
    CARD_STYLE,
    DATE_INPUT_STYLE,
    DATE_TIME_LABEL_STYLE,
    INPUT_STYLE,
    PAGE_STYLE,
    PANEL_STYLE,
    PRIMARY_BUTTON_STYLE,
    SECTION_TITLE_STYLE,
    SECONDARY_BUTTON_STYLE,
    TABLE_CELL_STYLE,
    TABLE_CSS,
    TABLE_DATA_STYLE_CONDITIONAL,
    TABLE_HEADER_STYLE,
    TABLE_STYLE,
    TIME_INPUT_STYLE,
    card_style,
)

from business_logic.service import service
from presentation.audit import audit, create_record
from presentation.helpers import combine_date_time, format_table_rows, now_iso, safe_float
from presentation.session import current_user, first_allowed_path, guard_requires_login, user_permissions
from presentation.charts import (
    fig_congestion_heatmap,
    fig_map_overlay,
    normalise_management_snapshot,
)
from presentation.ui import admin_datetime_row, admin_form_card, admin_tab, admin_table_card, shell, sidebar, topbar

class LocationStatus(str, Enum):
    ACTIVE = "Active"
    INACTIVE = "Inactive"
    UNDER_MAINTENANCE = "Under Maintenance"


class RouteStatus(str, Enum):
    OPEN = "Open"
    RESTRICTED = "Restricted"


class Severity(str, Enum):
    HIGH = "High"
    MEDIUM = "Medium"
    LOW = "Low"


class VesselPathStatus(str, Enum):
    APPROACHING = "Approaching"
    QUEUED = "Queued"
    HOLDING = "Holding"
    IN_TRANSIT = "In Transit"


class RestrictedAreaStatus(str, Enum):
    ACTIVE = "Active"
    INACTIVE = "Inactive"
    RESTRICTED = "Restricted"


class CraneOutageStatus(str, Enum):
    ACTIVE = "Active"
    UNAVAILABLE = "Unavailable"
    RESOLVED = "Resolved"


class BerthAllocationStatus(str, Enum):
    SCHEDULED = "Scheduled"
    CANCELLED = "Cancelled"
    DELAYED = "Delayed"


class Priority(str, Enum):
    HIGH = "High"
    MEDIUM = "Medium"
    LOW = "Low"

server = Flask(__name__)
server.secret_key = os.getenv("SMPOOS_SECRET_KEY", "smpoos-dev-secret")

app = dash.Dash(
    __name__,
    server=server,
    external_stylesheets=[dbc.themes.DARKLY],
    suppress_callback_exceptions=True,
    title="SMPOOS",
)


def login_layout():
    from presentation.screens.login_screen import login_layout as render_login_layout

    return render_login_layout()


def no_access_layout():
    content = html.Div(
        [
            html.H2("No Access", className="mb-0"),
            html.Div("Your account is authenticated but has no permissions assigned.", className="text-muted mb-3"),
            dbc.Alert("Contact an administrator to assign a role or permissions.", color="warning"),
        ]
    )
    return shell(content, "/no-access")


def dashboard_layout():
    from presentation.screens.dashboard_screen import dashboard_layout as render_dashboard_layout

    return render_dashboard_layout()


def monitoring_layout():
    from presentation.screens.monitoring_screen import monitoring_layout as render_monitoring_layout

    return render_monitoring_layout()


def analytics_layout():
    from presentation.screens.analytics_screen import analytics_layout as render_analytics_layout

    return render_analytics_layout()


def notification_engine_layout():
    from presentation.screens.notification_screen import notification_engine_layout as render_notification_layout

    return render_notification_layout()


def admin_layout():
    user = current_user() or {}
    service.ensure_user_permission(user, "view_admin_portal")
    perms = user_permissions(user)
    locations = service._serialize_records(service.repository.get_locations())[-50:]
    routes = service._serialize_records(service.repository.get_routes())[-50:]
    vessel_paths = service._serialize_records(service.repository.get_vessel_paths())[-50:]
    restricted_areas = service._serialize_records(service.repository.get_restricted_areas())[-50:]
    crane_outages = service._serialize_records(service.repository.get_crane_outages())[-50:]
    berth_allocations = service._serialize_records(service.repository.get_berth_allocations())[-50:]

    metric_specs = [
        ("Locations", len(locations)),
        ("Routes", len(routes)),
        ("Active notifications", len(service.repository.get_notifications())),
        ("Vessel paths", len(vessel_paths)),
    ]
    metric_cards = dbc.Row(
        [
            dbc.Col(
                dbc.Card(
                    dbc.CardBody(
                        [
                            html.Div(label, className="small", style={"color": "rgba(255,255,255,0.8)", "fontWeight": "600"}),
                            html.H2(value, className="mb-0 mt-2", style={"color": "#ffffff", "fontWeight": "800"}),
                        ]
                    ),
                    style=card_style(index),
                ),
                md=3,
            )
            for index, (label, value) in enumerate(metric_specs)
        ],
        className="g-3 mb-3",
    )

    content = html.Div(
        [
            html.Div("Operations Control", style={"color": "#93c5fd", "fontWeight": "700", "letterSpacing": "0.08em", "textTransform": "uppercase", "fontSize": "0.8rem"}),
            html.H2("Admin", className="mb-1", style={"color": "#f8fafc", "fontWeight": "800"}),
            html.Div("Manage zones, routes, allocations, and operational changes from a single control panel.", className="mb-3", style={"color": "#cbd5e1"}),
            metric_cards,
            dbc.Tabs(
                [
                    admin_tab(
                        html.Div(
                            [
                                dbc.Row(
                                    [
                                        dbc.Col(
                                            admin_form_card(
                                                "Locations",
                                                [
                                                    dbc.Input(id="loc-id", placeholder="Optional custom ID. Leave blank to auto-generate.", className="mb-2", style=INPUT_STYLE),
                                                    dbc.Input(id="loc-name", placeholder="Name", className="mb-2", style=INPUT_STYLE),
                                                    dbc.Input(id="loc-type", placeholder="Type e.g. Berth", className="mb-2", style=INPUT_STYLE),
                                                    dbc.Select(id="loc-status", options=[{"label": s.value, "value": s.value} for s in LocationStatus], value=LocationStatus.ACTIVE.value, className="mb-2", style=INPUT_STYLE),
                                                    dbc.Input(id="loc-capacity", placeholder="Capacity tonnes", className="mb-2", style=INPUT_STYLE),
                                                    dbc.ButtonGroup([dbc.Button("Save", id="loc-save", style=PRIMARY_BUTTON_STYLE), dbc.Button("Delete By ID", id="loc-delete", style=SECONDARY_BUTTON_STYLE)]),
                                                    dbc.Alert(id="loc-alert", is_open=False, duration=None, dismissable=True, color="success", className="mt-3", style={"borderRadius": "14px", "border": "0"}),
                                                ],
                                            ),
                                            xs=12,
                                            md=12,
                                        ),
                                    ],
                                    className="g-3 mb-3",
                                ),
                                dbc.Row(
                                    [
                                        dbc.Col(
                                            admin_table_card("Location Records", locations, ["location_id", "name", "type", "status", "capacity_tonnes"], page_size=10, table_id="admin-locations-table"),
                                            xs=12,
                                        ),
                                    ],
                                    className="g-3",
                                ),
                            ]
                        ),
                        "Locations",
                        disabled="manage_locations" not in perms,
                    ),
                    admin_tab(
                        html.Div(
                            [
                                dbc.Row(
                                    [
                                        dbc.Col(
                                            admin_form_card(
                                                "Routes",
                                                [
                                                    dbc.Input(id="route-id", placeholder="Optional custom ID. Leave blank to auto-generate.", className="mb-2", style=INPUT_STYLE),
                                                    dbc.Input(id="route-type", placeholder="Route type", className="mb-2", style=INPUT_STYLE),
                                                    dbc.Input(id="route-start", placeholder="Start Location e.g. L0001", className="mb-2", style=INPUT_STYLE),
                                                    dbc.Input(id="route-end", placeholder="End Location e.g. L0002", className="mb-2", style=INPUT_STYLE),
                                                    dbc.Input(id="route-distance", placeholder="Distance KM", className="mb-2", style=INPUT_STYLE),
                                                    dbc.Select(id="route-status", options=[{"label": s.value, "value": s.value} for s in RouteStatus], value=RouteStatus.OPEN.value, className="mb-2", style=INPUT_STYLE),
                                                    dbc.ButtonGroup([dbc.Button("Save", id="route-save", style=PRIMARY_BUTTON_STYLE), dbc.Button("Delete By ID", id="route-delete", style=SECONDARY_BUTTON_STYLE)]),
                                                    dbc.Alert(id="route-alert", is_open=False, duration=None, dismissable=True, color="success", className="mt-3", style={"borderRadius": "14px", "border": "0"}),
                                                ],
                                            ),
                                            xs=12,
                                            md=12,
                                        ),
                                    ],
                                    className="g-3 mb-3",
                                ),
                                dbc.Row(
                                    [
                                        dbc.Col(
                                            admin_table_card("Route Records", routes, ["route_id", "start_location", "end_location", "route_type", "distance_km", "status"], page_size=10, table_id="admin-routes-table"),
                                            xs=12,
                                        ),
                                    ],
                                    className="g-3",
                                ),
                            ]
                        ),
                        "Routes",
                        disabled="manage_routes" not in perms,
                    ),
                    admin_tab(
                        html.Div(
                            [
                                dbc.Row(
                                    [
                                        dbc.Col(
                                            admin_form_card(
                                                "Vessel Paths",
                                                [
                                                    dbc.Input(id="vp-id", placeholder="Optional custom ID. Leave blank to auto-generate.", className="mb-2", style=INPUT_STYLE),
                                                    dbc.Input(id="vp-name", placeholder="Vessel Name", className="mb-2", style=INPUT_STYLE),
                                                    dbc.Input(id="vp-type", placeholder="Vessel Type", className="mb-2", style=INPUT_STYLE),
                                                    dbc.Input(id="vp-cargo", placeholder="Cargo Tonnes", className="mb-2", style=INPUT_STYLE),
                                                    dbc.Select(id="vp-status", options=[{"label": s.value, "value": s.value} for s in VesselPathStatus], value=VesselPathStatus.APPROACHING.value, className="mb-2", style=INPUT_STYLE),
                                                    dbc.Input(id="vp-current", placeholder="Current Location ID e.g. L0001", className="mb-2", style=INPUT_STYLE),
                                                    dbc.Input(id="vp-destination", placeholder="Destination Location ID e.g. L0002", className="mb-2", style=INPUT_STYLE),
                                                    dbc.Input(id="vp-route", placeholder="Assigned Route ID e.g. R0001", className="mb-2", style=INPUT_STYLE),
                                                    dbc.Input(id="vp-berth", placeholder="Assigned Berth ID e.g. L0004", className="mb-2", style=INPUT_STYLE),
                                                    dbc.ButtonGroup([dbc.Button("Save", id="vp-save", style=PRIMARY_BUTTON_STYLE), dbc.Button("Delete By ID", id="vp-delete", style=SECONDARY_BUTTON_STYLE)]),
                                                    dbc.Alert(id="vp-alert", is_open=False, duration=None, dismissable=True, color="success", className="mt-3", style={"borderRadius": "14px", "border": "0"}),
                                                ],
                                            ),
                                            xs=12,
                                            md=12,
                                        ),
                                    ],
                                    className="g-3 mb-3",
                                ),
                                dbc.Row(
                                    [
                                        dbc.Col(
                                            admin_table_card("Vessel Path Records", vessel_paths, ["path_id", "vessel_name", "vessel_type", "cargo_tonnes", "status", "current_location_id", "destination_location_id", "assigned_route_id", "assigned_berth_id", "last_updated"], page_size=10, table_id="admin-vessel-paths-table"),
                                            xs=12,
                                        ),
                                    ],
                                    className="g-3",
                                ),
                            ]
                        ),
                        "Vessel Paths",
                        disabled="manage_vessel_paths" not in perms,
                    ),
                    admin_tab(
                        html.Div(
                            [
                                dbc.Row(
                                    [
                                        dbc.Col(
                                            admin_form_card(
                                                "Restricted Areas",
                                                [
                                                    dbc.Input(id="ra-id", placeholder="Optional custom ID. Leave blank to auto-generate.", className="mb-2", style=INPUT_STYLE),
                                                    dbc.Input(id="ra-name", placeholder="Area Name", className="mb-2", style=INPUT_STYLE),
                                                    dbc.Input(id="ra-location", placeholder="Location ID e.g. L0001", className="mb-2", style=INPUT_STYLE),
                                                    dbc.Input(id="ra-type", placeholder="Area Type e.g. Hazardous Area", className="mb-2", style=INPUT_STYLE),
                                                    dbc.Select(id="ra-status", options=[{"label": s.value, "value": s.value} for s in RestrictedAreaStatus], value=RestrictedAreaStatus.ACTIVE.value, className="mb-2", style=INPUT_STYLE),
                                                    dbc.Select(id="ra-severity", options=[{"label": s.value, "value": s.value} for s in Severity], value=Severity.MEDIUM.value, className="mb-2", style=INPUT_STYLE),
                                                    admin_datetime_row("ra-start-date", "ra-start-time", "Start Date", "Start Time"),
                                                    admin_datetime_row("ra-end-date", "ra-end-time", "End Date", "End Time"),
                                                    dbc.Textarea(id="ra-reason", placeholder="Reason", className="mb-2", style=INPUT_STYLE),
                                                    dbc.ButtonGroup([dbc.Button("Save", id="ra-save", style=PRIMARY_BUTTON_STYLE), dbc.Button("Delete By ID", id="ra-delete", style=SECONDARY_BUTTON_STYLE)]),
                                                    dbc.Alert(id="ra-alert", is_open=False, duration=None, dismissable=True, color="success", className="mt-3", style={"borderRadius": "14px", "border": "0"}),
                                                ],
                                            ),
                                            xs=12,
                                            md=12,
                                        ),
                                    ],
                                    className="g-3 mb-3",
                                ),
                                dbc.Row(
                                    [
                                        dbc.Col(
                                            admin_table_card("Restricted Area Records", restricted_areas, ["area_id", "name", "location_id", "area_type", "status", "severity", "start_time", "end_time", "reason"], page_size=10, table_id="admin-restricted-areas-table"),
                                            xs=12,
                                        ),
                                    ],
                                    className="g-3",
                                ),
                            ]
                        ),
                        "Restricted Areas",
                        disabled="manage_restricted_areas" not in perms,
                    ),
                    admin_tab(
                        html.Div(
                            [
                                dbc.Row(
                                    [
                                        dbc.Col(
                                            admin_form_card(
                                                "Crane Outages",
                                                [
                                                    dbc.Input(id="co-id", placeholder="Optional custom ID. Leave blank to auto-generate.", className="mb-2", style=INPUT_STYLE),
                                                    dbc.Input(id="co-crane", placeholder="Crane ID", className="mb-2", style=INPUT_STYLE),
                                                    dbc.Input(id="co-location", placeholder="Location ID e.g. L0001", className="mb-2", style=INPUT_STYLE),
                                                    dbc.Select(id="co-status", options=[{"label": s.value, "value": s.value} for s in CraneOutageStatus], value=CraneOutageStatus.ACTIVE.value, className="mb-2", style=INPUT_STYLE),
                                                    dbc.Select(id="co-severity", options=[{"label": s.value, "value": s.value} for s in Severity], value=Severity.MEDIUM.value, className="mb-2", style=INPUT_STYLE),
                                                    admin_datetime_row("co-start-date", "co-start-time", "Start Date", "Start Time"),
                                                    admin_datetime_row("co-end-date", "co-end-time", "End Date", "End Time"),
                                                    dbc.Textarea(id="co-reason", placeholder="Reason", className="mb-2", style=INPUT_STYLE),
                                                    dbc.ButtonGroup([dbc.Button("Save", id="co-save", style=PRIMARY_BUTTON_STYLE), dbc.Button("Delete By ID", id="co-delete", style=SECONDARY_BUTTON_STYLE)]),
                                                    dbc.Alert(id="co-alert", is_open=False, duration=None, dismissable=True, color="success", className="mt-3", style={"borderRadius": "14px", "border": "0"}),
                                                ],
                                            ),
                                            xs=12,
                                            md=12,
                                        ),
                                    ],
                                    className="g-3 mb-3",
                                ),
                                dbc.Row(
                                    [
                                        dbc.Col(
                                            admin_table_card("Crane Outage Records", crane_outages, ["outage_id", "crane_id", "location_id", "status", "severity", "start_time", "end_time", "reason"], page_size=10, table_id="admin-crane-outages-table"),
                                            xs=12,
                                        ),
                                    ],
                                    className="g-3",
                                ),
                            ]
                        ),
                        "Crane Outages",
                        disabled="manage_crane_outages" not in perms,
                    ),
                    admin_tab(
                        html.Div(
                            [
                                dbc.Row(
                                    [
                                        dbc.Col(
                                            admin_form_card(
                                                "Berth Allocations",
                                                [
                                                    dbc.Input(id="ba-id", placeholder="Optional custom ID. Leave blank to auto-generate.", className="mb-2", style=INPUT_STYLE),
                                                    dbc.Input(id="ba-vessel", placeholder="Vessel Name", className="mb-2", style=INPUT_STYLE),
                                                    dbc.Input(id="ba-cargo", placeholder="Cargo Tonnes", className="mb-2", style=INPUT_STYLE),
                                                    dbc.Input(id="ba-berth", placeholder="Berth ID e.g. L0004", className="mb-2", style=INPUT_STYLE),
                                                    admin_datetime_row("ba-eta-date", "ba-eta-time", "Eta Date", "Eta Time"),
                                                    dbc.Select(id="ba-status", options=[{"label": s.value, "value": s.value} for s in BerthAllocationStatus], value=BerthAllocationStatus.SCHEDULED.value, className="mb-2", style=INPUT_STYLE),
                                                    dbc.Select(id="ba-priority", options=[{"label": s.value, "value": s.value} for s in Priority], value=Priority.MEDIUM.value, className="mb-2", style=INPUT_STYLE),
                                                    dbc.Textarea(id="ba-notes", placeholder="Notes", className="mb-2", style=INPUT_STYLE),
                                                    dbc.ButtonGroup([dbc.Button("Save", id="ba-save", style=PRIMARY_BUTTON_STYLE), dbc.Button("Delete By ID", id="ba-delete", style=SECONDARY_BUTTON_STYLE)]),
                                                    dbc.Alert(id="ba-alert", is_open=False, duration=None, dismissable=True, color="success", className="mt-3", style={"borderRadius": "14px", "border": "0"}),
                                                ],
                                            ),
                                            xs=12,
                                            md=12,
                                        ),
                                    ],
                                    className="g-3 mb-3",
                                ),
                                dbc.Row(
                                    [
                                        dbc.Col(
                                            admin_table_card("Berth Allocation Records", berth_allocations, ["allocation_id", "vessel_name", "cargo_tonnes", "berth_id", "eta", "status", "priority", "notes"], page_size=10, table_id="admin-berth-allocations-table"),
                                            xs=12,
                                        ),
                                    ],
                                    className="g-3",
                                ),
                            ]
                        ),
                        "Berth Allocations",
                        disabled="manage_berth_allocations" not in perms,
                    ),
                    admin_tab(
                        admin_form_card(
                            "Operational Change",
                            [
                                dbc.Select(
                                    id="op-target-type",
                                    options=[
                                        {"label": "Location", "value": "location"},
                                        {"label": "Route", "value": "route"},
                                        {"label": "Restricted Area", "value": "restricted_area"},
                                        {"label": "Crane Outage", "value": "crane_outage"},
                                        {"label": "Vessel Path", "value": "vessel_path"},
                                        {"label": "Berth Allocation", "value": "berth_allocation"},
                                    ],
                                    value="location",
                                    className="mb-2",
                                    style=INPUT_STYLE,
                                ),
                                dbc.Input(id="op-target-id", placeholder="Target ID e.g. L0001", className="mb-2", style=INPUT_STYLE),
                                dbc.Input(id="op-new-status", placeholder="New Status e.g. Restricted", className="mb-2", style=INPUT_STYLE),
                                dbc.Select(id="op-severity", options=[{"label": s.value, "value": s.value} for s in Severity], value=Severity.HIGH.value, className="mb-2", style=INPUT_STYLE),
                                dbc.Input(id="op-alert-type", placeholder="Alert Type (optional)", className="mb-2", style=INPUT_STYLE),
                                dbc.Input(id="op-location-id", placeholder="Location ID (optional)", className="mb-2", style=INPUT_STYLE),
                                dbc.Textarea(id="op-message", placeholder="Message", className="mb-2", style=INPUT_STYLE),
                                dbc.ButtonGroup([dbc.Button("Apply Change", id="op-apply", style=PRIMARY_BUTTON_STYLE), dbc.Button("Recalculate Now", id="op-recalc", style=SECONDARY_BUTTON_STYLE)]),
                                dbc.Alert(id="op-alert", is_open=False, duration=None, dismissable=True, color="success", className="mt-3", style={"borderRadius": "14px", "border": "0"}),
                                html.Pre(id="op-result", className="mt-3", style={"color": "#cbd5e1", "background": "rgba(2,6,23,0.45)", "border": "1px solid rgba(148,163,184,0.16)", "borderRadius": "12px", "padding": "12px"}),
                            ],
                        ),
                        "Operational Change",
                        disabled="manage_operational_changes" not in perms,
                    ),
                ],
                className="mb-2",
                style=ADMIN_PANEL_STYLE,
            ),
        ]
    )
    return shell(content, "/admin")


app.layout = html.Div([dcc.Location(id="url"), html.Div(id="page-content")])


@app.callback(Output("login-email", "value"), Output("login-password", "value"), Input("demo-admin", "n_clicks"), Input("demo-harbour", "n_clicks"), Input("demo-safety", "n_clicks"), prevent_initial_call=True)
def fill_demo(_demo_admin_clicks, _demo_harbour_clicks, _demo_safety_clicks):
    trigger = dash.callback_context.triggered[0]["prop_id"].split(".")[0]
    if trigger == "demo-admin":
        return "user6@portauthority.com", "admin123"
    if trigger == "demo-harbour":
        return "user19@portauthority.com", "harbour123"
    return "user12@portauthority.com", "safety123"


@app.callback(Output("login-msg", "children"), Output("login-msg", "color"), Output("url", "pathname"), Input("login-submit", "n_clicks"), State("login-email", "value"), State("login-password", "value"), prevent_initial_call=True)
def handle_login(_, email, password):
    try:
        user = service.authenticate_user(email or "", password or "")
        session["user"] = user
        audit("system_access", "session", user.get("user_id", ""), "User signed in to the SMPOOS admin platform.")
        return f"Welcome {user.get('name','')}. Login successful.", "success", first_allowed_path(user)
    except Exception as exc:
        return str(exc) or "Login failed.", "danger", "/login"


@app.callback(Output("url", "pathname"), Input("logout-btn", "n_clicks"), prevent_initial_call=True)
def handle_logout(n_clicks):
    if not n_clicks:
        raise PreventUpdate
    session.pop("user", None)
    return "/login"


@app.callback(Output("page-content", "children"), Input("url", "pathname"))
def route(pathname):
    try:
        guard = guard_requires_login(pathname)
        if guard is not None:
            return guard
        if pathname in {"/", "/login"}:
            return login_layout()
        if pathname == "/no-access":
            return no_access_layout()
        if pathname == "/dashboard":
            return dashboard_layout()
        if pathname == "/monitoring":
            return monitoring_layout()
        if pathname == "/analytics":
            return analytics_layout()
        if pathname == "/notification-engine":
            return notification_engine_layout()
        if pathname == "/admin":
            return admin_layout()
        return dcc.Location(pathname=first_allowed_path(), id="redirect-default")
    except PermissionError:
        landing = first_allowed_path()
        if landing != pathname:
            return dcc.Location(pathname=landing, id="redirect-permission")
        return shell(dbc.Alert("Access denied.", color="danger"), pathname or "/")
    except Exception as exc:
        print(f"Error while rendering {pathname}: {exc}")
        traceback.print_exc()
        return shell(dbc.Alert("Something went wrong while rendering this page. Check the server logs.", color="danger"), pathname or "/")


@app.callback(Output("mgmt-map", "figure"), Input("map-overlay", "value"), State("mgmt-snapshot", "data"), prevent_initial_call=True)
def update_map(overlay_key, snapshot):
    snapshot = normalise_management_snapshot(snapshot)
    return fig_map_overlay(snapshot.get("map_overlays", {}), overlay_key or "berths")


@app.callback(Output("mgmt-snapshot", "data"), Input("dashboard-refresh", "n_intervals"), prevent_initial_call=True)
def refresh_dashboard_snapshot(_n_intervals):
    user = current_user() or {}
    service.ensure_user_permission(user, "view_management_dashboard")
    runtime_context = {"https_enabled": True, "session_count": 1}
    return normalise_management_snapshot(
        service.get_management_dashboard_snapshot(user=user, filters={}, runtime_context=runtime_context)
    )


@app.callback(Output("mgmt-heatmap", "figure"), Input("mgmt-snapshot", "data"), prevent_initial_call=True)
def update_heatmap(snapshot):
    snapshot = normalise_management_snapshot(snapshot)
    return fig_congestion_heatmap(snapshot.get("congestion_heatmap", []))


@app.callback(Output("dashboard-alert-table", "data"), Input("mgmt-snapshot", "data"), prevent_initial_call=True)
def update_dashboard_alerts(snapshot):
    snapshot = normalise_management_snapshot(snapshot)
    alerts = snapshot.get("alerts_panel", []) or []
    return format_table_rows(alerts, ["notification_id", "alert_type", "location_id", "severity", "message", "timestamp"])


@app.callback(
    Output("toast", "children", allow_duplicate=True),
    Output("toast", "color", allow_duplicate=True),
    Output("toast", "is_open", allow_duplicate=True),
    Output("notification-engine-refresh-signal", "data", allow_duplicate=True),
    Output("rule-id", "value", allow_duplicate=True),
    Input("save-rule", "n_clicks"),
    State("rule-id", "value"),
    State("rule-name", "value"),
    State("rule-location", "value"),
    State("rule-role", "value"),
    State("rule-context", "value"),
    State("rule-metric", "value"),
    State("rule-operator", "value"),
    State("rule-threshold", "value"),
    State("rule-severity", "value"),
    State("rule-channels", "value"),
    State("rule-active", "value"),
    State("rule-message", "value"),
    prevent_initial_call=True,
)
def save_rule(_, rule_id, name, location_id, target_role, context_type, metric_name, operator, threshold, severity, channels, active, message_template):
    user = current_user() or {}
    try:
        service.ensure_user_permission(user, "manage_notification_rules")
        payload = {
            "rule_id": (rule_id or "").strip(),
            "name": name or "",
            "location_id": (location_id or "").strip(),
            "target_role": target_role or "",
            "context_type": context_type or "",
            "metric_name": metric_name or "",
            "operator": operator or "",
            "threshold_value": threshold or "",
            "severity": severity or "",
            "channels": channels or "",
            "active": active or "Yes",
            "message_template": message_template or "",
        }
        record_id = payload.get("rule_id")
        if record_id and any(rule.rule_id == record_id for rule in service.repository.get_notification_rules()):
            raise ValueError(f"Rule {record_id} already exists. Use a unique rule ID.")

        created = service.create_notification_rule(payload)
        created_id = created.get("rule_id", "")
        audit("create", "notification_rule", created_id, "Created notification rule.")
        return f"Rule {created_id} created.", "success", True, now_iso(), ""
    except Exception as exc:
        return str(exc) or "Save failed.", "danger", True, dash.no_update, dash.no_update


@app.callback(
    Output("toast", "children", allow_duplicate=True),
    Output("toast", "color", allow_duplicate=True),
    Output("toast", "is_open", allow_duplicate=True),
    Output("notification-engine-refresh-signal", "data", allow_duplicate=True),
    Output("rule-id", "value", allow_duplicate=True),
    Input("delete-rule", "n_clicks"),
    State("rule-id", "value"),
    prevent_initial_call=True,
)
def delete_rule(_, rule_id):
    user = current_user() or {}
    try:
        service.ensure_user_permission(user, "manage_notification_rules")
        record_id = (rule_id or "").strip()
        if not record_id:
            raise ValueError("Enter a rule ID to delete.")
        service.delete_notification_rule(record_id)
        audit("delete", "notification_rule", record_id, "Deleted notification rule.")
        return f"Rule {record_id} deleted.", "success", True, now_iso(), ""
    except Exception as exc:
        return str(exc) or "Delete failed.", "danger", True, dash.no_update, dash.no_update


@app.callback(
    Output("notification-engine-snapshot", "data"),
    Input("notification-engine-refresh", "n_intervals"),
    Input("notification-engine-refresh-signal", "data"),
    prevent_initial_call=True,
)
def refresh_notification_engine_snapshot(_n_intervals, _refresh_signal):
    user = current_user() or {}
    service.ensure_user_permission(user, "view_notification_engine")
    return service.get_notification_engine_snapshot()


@app.callback(
    Output("notification-engine-metric-rules", "children"),
    Output("notification-engine-metric-deliveries", "children"),
    Output("notification-engine-metric-notifications", "children"),
    Output("notification-engine-metric-events", "children"),
    Output("notification-rules-table", "data"),
    Output("notification-deliveries-table", "data"),
    Output("notification-records-table", "data"),
    Output("notification-event-log-table", "data"),
    Input("notification-engine-snapshot", "data"),
    prevent_initial_call=True,
)
def update_notification_engine_live(snapshot):
    snapshot = snapshot or {}
    rules = snapshot.get("rules", []) or []
    deliveries = snapshot.get("deliveries", []) or []
    notifications = snapshot.get("notifications", []) or []
    event_logs = snapshot.get("event_logs", []) or []
    return (
        len(rules),
        len(deliveries),
        len(notifications),
        len(event_logs),
        format_table_rows(rules, ["rule_id", "name", "target_role", "context_type", "metric_name", "operator", "threshold_value", "severity", "channels", "active"]),
        format_table_rows(deliveries, ["delivery_id", "notification_id", "rule_id", "target_role", "channel", "status", "delivered_at"]),
        format_table_rows(notifications, ["notification_id", "alert_type", "location_id", "severity", "message", "timestamp"]),
        format_table_rows(event_logs, ["event_id", "event_type", "entity_type", "entity_id", "severity", "created_at"]),
    )


@app.callback(
    Output("analytics-report-store", "data"),
    Output("analytics-report-alert", "children"),
    Output("analytics-report-alert", "color"),
    Output("analytics-report-alert", "is_open"),
    Output("analytics-start-date", "value"),
    Output("analytics-end-date", "value"),
    Output("analytics-vessel-type", "value"),
    Output("analytics-cargo-type", "value"),
    Input("analytics-generate", "n_clicks"),
    Input("analytics-reset", "n_clicks"),
    State("analytics-start-date", "value"),
    State("analytics-end-date", "value"),
    State("analytics-vessel-type", "value"),
    State("analytics-cargo-type", "value"),
    prevent_initial_call=True,
)
def manage_analytics_report(_generate_clicks, _reset_clicks, start_date, end_date, vessel_type, cargo_type):
    user = current_user() or {}
    try:
        trigger = dash.callback_context.triggered[0]["prop_id"].split(".")[0]
    except dash.exceptions.MissingCallbackContextException:
        trigger = "analytics-reset" if _reset_clicks and not _generate_clicks else "analytics-generate"
    try:
        if trigger == "analytics-reset":
            service.ensure_user_permission(user, "view_analytics")
            report = service.generate_custom_report({})
            return report, "Filters reset.", "success", True, None, None, "", ""

        service.ensure_user_permission(user, "generate_reports")
        filters = {
            "start_date": start_date or "",
            "end_date": end_date or "",
            "vessel_type": vessel_type or "",
            "cargo_type": cargo_type or "",
        }
        report = service.generate_custom_report(filters)
        audit("generate", "analytics_report", "custom", "Generated filtered analytics report.")
        return report, "Report generated.", "success", True, start_date, end_date, vessel_type, cargo_type
    except Exception as exc:
        return dash.no_update, str(exc) or "Report generation failed.", "danger", True, start_date, end_date, vessel_type, cargo_type


@app.callback(
    Output("analytics-report-matched", "children"),
    Output("analytics-report-vessel-count", "children"),
    Output("analytics-report-cargo-count", "children"),
    Output("analytics-report-generated-at", "children"),
    Output("analytics-report-vessel-types", "children"),
    Output("analytics-report-cargo-types", "children"),
    Output("analytics-report-table", "data"),
    Output("analytics-report-recommendations", "children"),
    Output("analytics-vessel-type-graph", "figure"),
    Output("analytics-destination-graph", "figure"),
    Output("analytics-status-graph", "figure"),
    Input("analytics-report-store", "data"),
    prevent_initial_call=True,
)
def render_analytics_report(report):
    from presentation.screens.analytics_screen import build_report_graphs

    report = report or {}
    summary = report.get("summary", {}) or {}
    rows = report.get("rows", []) or []
    recommendations = report.get("recommendations", []) or []
    vessel_fig, destination_fig, status_fig = build_report_graphs(report)
    recommendation_items = [
        dbc.ListGroupItem(
            [
                html.Div(item.get("category", "Recommendation"), style={"color": "#f8fafc", "fontWeight": "700"}),
                html.Div(item.get("insight", ""), style={"color": "#cbd5e1"}),
            ],
            style={"background": "rgba(2,6,23,0.28)", "border": "1px solid rgba(96,165,250,0.14)", "color": "#e2e8f0"},
        )
        for item in recommendations
    ] or [
        dbc.ListGroupItem(
            "No recommendations available for the current filters.",
            style={"background": "rgba(2,6,23,0.28)", "border": "1px solid rgba(96,165,250,0.14)", "color": "#cbd5e1"},
        )
    ]
    return (
        summary.get("matched_records", 0),
        len(summary.get("vessel_types", []) or []),
        len(summary.get("cargo_types", []) or []),
        report.get("generated_at", "-"),
        ", ".join(summary.get("vessel_types", []) or []) or "All",
        ", ".join(summary.get("cargo_types", []) or []) or "All",
        format_table_rows(
            rows,
            [
                "vessel_name",
                "vessel_type",
                "cargo_type",
                "current_location_id",
                "destination",
                "assigned_route_id",
                "assigned_berth_id",
                "eta",
                "status",
            ],
        ),
        recommendation_items,
        vessel_fig,
        destination_fig,
        status_fig,
    )


@app.callback(
    Output("admin-locations-table", "data"),
    Output("loc-alert", "children"),
    Output("loc-alert", "color"),
    Output("loc-alert", "is_open"),
    Output("loc-id", "value"),
    Input("loc-save", "n_clicks"),
    Input("loc-delete", "n_clicks"),
    State("loc-id", "value"),
    State("loc-name", "value"),
    State("loc-type", "value"),
    State("loc-status", "value"),
    State("loc-capacity", "value"),
    prevent_initial_call=True,
)
def handle_locations(_save, _delete, loc_id, name, loc_type, status, capacity_tonnes):
    trigger = dash.callback_context.triggered[0]["prop_id"].split(".")[0]
    user = current_user() or {}
    try:
        service.ensure_user_permission(user, "manage_locations")
        if trigger == "loc-save":
            payload = {
                "name": name or "",
                "type": loc_type or "",
                "status": status or "",
                "capacity_tonnes": capacity_tonnes or "",
            }
            created, action = create_record(
                loc_id,
                payload,
                service.create_location,
                "Location",
            )
            record_id = created.get("location_id", "")
            audit(action, "location", record_id, f"{action.title()}d location record.")
            msg = f"Location {record_id} saved."
            new_loc_id = ""
        else:
            record_id = (loc_id or "").strip()
            if not record_id:
                raise ValueError("Enter a location ID to delete.")
            service.delete_location(record_id)
            audit("delete", "location", record_id, "Deleted location record.")
            msg = f"Location {record_id} deleted."
            new_loc_id = ""

        rows = service._serialize_records(service.repository.get_locations())[-50:]
        data = format_table_rows(rows, ["location_id", "name", "type", "status", "capacity_tonnes"])
        return data, msg, "success", True, new_loc_id
    except Exception as exc:
        return dash.no_update, str(exc) or "Action failed.", "danger", True, dash.no_update


@app.callback(
    Output("admin-routes-table", "data"),
    Output("route-alert", "children"),
    Output("route-alert", "color"),
    Output("route-alert", "is_open"),
    Output("route-id", "value"),
    Input("route-save", "n_clicks"),
    Input("route-delete", "n_clicks"),
    State("route-id", "value"),
    State("route-type", "value"),
    State("route-start", "value"),
    State("route-end", "value"),
    State("route-distance", "value"),
    State("route-status", "value"),
    prevent_initial_call=True,
)
def handle_routes(_save, _delete, route_id, route_type, start_location, end_location, distance_km, status):
    trigger = dash.callback_context.triggered[0]["prop_id"].split(".")[0]
    user = current_user() or {}
    try:
        service.ensure_user_permission(user, "manage_routes")
        if trigger == "route-save":
            payload = {
                "route_type": route_type or "",
                "start_location": start_location or "",
                "end_location": end_location or "",
                "distance_km": distance_km or "",
                "status": status or "",
            }
            created, action = create_record(
                route_id,
                payload,
                service.create_route,
                "Route",
            )
            record_id = created.get("route_id", "")
            audit(action, "route", record_id, f"{action.title()}d route record.")
            msg = f"Route {record_id} saved."
            new_route_id = ""
        else:
            record_id = (route_id or "").strip()
            if not record_id:
                raise ValueError("Enter a route ID to delete.")
            service.delete_route(record_id)
            audit("delete", "route", record_id, "Deleted route record.")
            msg = f"Route {record_id} deleted."
            new_route_id = ""

        rows = service._serialize_records(service.repository.get_routes())[-50:]
        data = format_table_rows(rows, ["route_id", "start_location", "end_location", "route_type", "distance_km", "status"])
        return data, msg, "success", True, new_route_id
    except Exception as exc:
        return dash.no_update, str(exc) or "Action failed.", "danger", True, dash.no_update


@app.callback(
    Output("admin-vessel-paths-table", "data"),
    Output("vp-alert", "children"),
    Output("vp-alert", "color"),
    Output("vp-alert", "is_open"),
    Output("vp-id", "value"),
    Input("vp-save", "n_clicks"),
    Input("vp-delete", "n_clicks"),
    State("vp-id", "value"),
    State("vp-name", "value"),
    State("vp-type", "value"),
    State("vp-cargo", "value"),
    State("vp-status", "value"),
    State("vp-current", "value"),
    State("vp-destination", "value"),
    State("vp-route", "value"),
    State("vp-berth", "value"),
    prevent_initial_call=True,
)
def handle_vessel_paths(
    _save,
    _delete,
    path_id,
    vessel_name,
    vessel_type,
    cargo_tonnes,
    status,
    current_location_id,
    destination_location_id,
    assigned_route_id,
    assigned_berth_id,
):
    trigger = dash.callback_context.triggered[0]["prop_id"].split(".")[0]
    user = current_user() or {}
    try:
        service.ensure_user_permission(user, "manage_vessel_paths")
        if trigger == "vp-save":
            create_payload = {
                "vessel_name": vessel_name or "",
                "vessel_type": vessel_type or "",
                "cargo_tonnes": cargo_tonnes or "",
                "status": status or "",
                "current_location_id": current_location_id or "",
                "destination_location_id": destination_location_id or "",
                "assigned_route_id": assigned_route_id or "",
                "assigned_berth_id": assigned_berth_id or "",
            }
            created, action = create_record(
                path_id,
                create_payload,
                service.create_vessel_path,
                "Vessel path",
            )
            record_id = created.get("path_id", "")
            audit(action, "vessel_path", record_id, f"{action.title()}d vessel path record.")
            msg = f"Vessel path {record_id} saved."
            new_path_id = ""
        else:
            record_id = (path_id or "").strip()
            if not record_id:
                raise ValueError("Enter a vessel path ID to delete.")
            service.delete_vessel_path(record_id)
            audit("delete", "vessel_path", record_id, "Deleted vessel path record.")
            msg = f"Vessel path {record_id} deleted."
            new_path_id = ""

        rows = service._serialize_records(service.repository.get_vessel_paths())[-50:]
        data = format_table_rows(
            rows,
            [
                "path_id",
                "vessel_name",
                "vessel_type",
                "cargo_tonnes",
                "status",
                "current_location_id",
                "destination_location_id",
                "assigned_route_id",
                "assigned_berth_id",
                "last_updated",
            ],
        )
        return data, msg, "success", True, new_path_id
    except Exception as exc:
        return dash.no_update, str(exc) or "Action failed.", "danger", True, dash.no_update


@app.callback(
    Output("admin-restricted-areas-table", "data"),
    Output("ra-alert", "children"),
    Output("ra-alert", "color"),
    Output("ra-alert", "is_open"),
    Output("ra-id", "value"),
    Input("ra-save", "n_clicks"),
    Input("ra-delete", "n_clicks"),
    State("ra-id", "value"),
    State("ra-name", "value"),
    State("ra-location", "value"),
    State("ra-type", "value"),
    State("ra-status", "value"),
    State("ra-severity", "value"),
    State("ra-start-date", "value"),
    State("ra-start-time", "value"),
    State("ra-end-date", "value"),
    State("ra-end-time", "value"),
    State("ra-reason", "value"),
    prevent_initial_call=True,
)
def handle_restricted_areas(
    _save,
    _delete,
    area_id,
    name,
    location_id,
    area_type,
    status,
    severity,
    start_date,
    start_time,
    end_date,
    end_time,
    reason,
):
    trigger = dash.callback_context.triggered[0]["prop_id"].split(".")[0]
    user = current_user() or {}
    try:
        service.ensure_user_permission(user, "manage_restricted_areas")
        if trigger == "ra-save":
            payload = {
                "name": name or "",
                "location_id": location_id or "",
                "area_type": area_type or "",
                "status": status or "",
                "severity": severity or "",
                "start_time": combine_date_time(start_date, start_time),
                "end_time": combine_date_time(end_date, end_time),
                "reason": reason or "",
            }
            created, action = create_record(
                area_id,
                payload,
                service.create_restricted_area,
                "Restricted area",
            )
            record_id = created.get("area_id", "")
            audit(action, "restricted_area", record_id, f"{action.title()}d restricted area record.")
            msg = f"Restricted area {record_id} saved."
            new_area_id = ""
        else:
            record_id = (area_id or "").strip()
            if not record_id:
                raise ValueError("Enter a restricted area ID to delete.")
            service.delete_restricted_area(record_id)
            audit("delete", "restricted_area", record_id, "Deleted restricted area record.")
            msg = f"Restricted area {record_id} deleted."
            new_area_id = ""

        rows = service._serialize_records(service.repository.get_restricted_areas())[-50:]
        data = format_table_rows(rows, ["area_id", "name", "location_id", "area_type", "status", "severity", "start_time", "end_time", "reason"])
        return data, msg, "success", True, new_area_id
    except Exception as exc:
        return dash.no_update, str(exc) or "Action failed.", "danger", True, dash.no_update


@app.callback(
    Output("admin-crane-outages-table", "data"),
    Output("co-alert", "children"),
    Output("co-alert", "color"),
    Output("co-alert", "is_open"),
    Output("co-id", "value"),
    Input("co-save", "n_clicks"),
    Input("co-delete", "n_clicks"),
    State("co-id", "value"),
    State("co-crane", "value"),
    State("co-location", "value"),
    State("co-status", "value"),
    State("co-severity", "value"),
    State("co-start-date", "value"),
    State("co-start-time", "value"),
    State("co-end-date", "value"),
    State("co-end-time", "value"),
    State("co-reason", "value"),
    prevent_initial_call=True,
)
def handle_crane_outages(
    _save,
    _delete,
    outage_id,
    crane_id,
    location_id,
    status,
    severity,
    start_date,
    start_time,
    end_date,
    end_time,
    reason,
):
    trigger = dash.callback_context.triggered[0]["prop_id"].split(".")[0]
    user = current_user() or {}
    try:
        service.ensure_user_permission(user, "manage_crane_outages")
        if trigger == "co-save":
            payload = {
                "crane_id": crane_id or "",
                "location_id": location_id or "",
                "status": status or "",
                "severity": severity or "",
                "start_time": combine_date_time(start_date, start_time),
                "end_time": combine_date_time(end_date, end_time),
                "reason": reason or "",
            }
            created, action = create_record(
                outage_id,
                payload,
                service.create_crane_outage,
                "Crane outage",
            )
            record_id = created.get("outage_id", "")
            audit(action, "crane_outage", record_id, f"{action.title()}d crane outage record.")
            msg = f"Crane outage {record_id} saved."
            new_outage_id = ""
        else:
            record_id = (outage_id or "").strip()
            if not record_id:
                raise ValueError("Enter a crane outage ID to delete.")
            service.delete_crane_outage(record_id)
            audit("delete", "crane_outage", record_id, "Deleted crane outage record.")
            msg = f"Crane outage {record_id} deleted."
            new_outage_id = ""

        rows = service._serialize_records(service.repository.get_crane_outages())[-50:]
        data = format_table_rows(rows, ["outage_id", "crane_id", "location_id", "status", "severity", "start_time", "end_time", "reason"])
        return data, msg, "success", True, new_outage_id
    except Exception as exc:
        return dash.no_update, str(exc) or "Action failed.", "danger", True, dash.no_update


@app.callback(
    Output("admin-berth-allocations-table", "data"),
    Output("ba-alert", "children"),
    Output("ba-alert", "color"),
    Output("ba-alert", "is_open"),
    Output("ba-id", "value"),
    Input("ba-save", "n_clicks"),
    Input("ba-delete", "n_clicks"),
    State("ba-id", "value"),
    State("ba-vessel", "value"),
    State("ba-cargo", "value"),
    State("ba-berth", "value"),
    State("ba-eta-date", "value"),
    State("ba-eta-time", "value"),
    State("ba-status", "value"),
    State("ba-priority", "value"),
    State("ba-notes", "value"),
    prevent_initial_call=True,
)
def handle_berth_allocations(
    _save,
    _delete,
    allocation_id,
    vessel_name,
    cargo_tonnes,
    berth_id,
    eta_date,
    eta_time,
    status,
    priority,
    notes,
):
    trigger = dash.callback_context.triggered[0]["prop_id"].split(".")[0]
    user = current_user() or {}
    try:
        service.ensure_user_permission(user, "manage_berth_allocations")
        if trigger == "ba-save":
            payload = {
                "vessel_name": vessel_name or "",
                "cargo_tonnes": cargo_tonnes or "",
                "berth_id": berth_id or "",
                "eta": combine_date_time(eta_date, eta_time),
                "status": status or "",
                "priority": priority or "",
                "notes": notes or "",
            }
            created, action = create_record(
                allocation_id,
                payload,
                service.create_berth_allocation,
                "Berth allocation",
            )
            record_id = created.get("allocation_id", "")
            audit(action, "berth_allocation", record_id, f"{action.title()}d berth allocation record.")
            msg = f"Berth allocation {record_id} saved."
            new_allocation_id = ""
        else:
            record_id = (allocation_id or "").strip()
            if not record_id:
                raise ValueError("Enter a berth allocation ID to delete.")
            service.delete_berth_allocation(record_id)
            audit("delete", "berth_allocation", record_id, "Deleted berth allocation record.")
            msg = f"Berth allocation {record_id} deleted."
            new_allocation_id = ""

        rows = service._serialize_records(service.repository.get_berth_allocations())[-50:]
        data = format_table_rows(rows, ["allocation_id", "vessel_name", "cargo_tonnes", "berth_id", "eta", "status", "priority", "notes"])
        return data, msg, "success", True, new_allocation_id
    except Exception as exc:
        return dash.no_update, str(exc) or "Action failed.", "danger", True, dash.no_update


@app.callback(
    Output("op-result", "children"),
    Output("op-alert", "children"),
    Output("op-alert", "color"),
    Output("op-alert", "is_open"),
    Input("op-apply", "n_clicks"),
    Input("op-recalc", "n_clicks"),
    State("op-target-type", "value"),
    State("op-target-id", "value"),
    State("op-new-status", "value"),
    State("op-severity", "value"),
    State("op-alert-type", "value"),
    State("op-location-id", "value"),
    State("op-message", "value"),
    prevent_initial_call=True,
)
def handle_operational_actions(
    _apply,
    _recalc,
    target_type,
    target_id,
    new_status,
    severity,
    alert_type,
    location_id,
    message,
):
    trigger = dash.callback_context.triggered[0]["prop_id"].split(".")[0]
    user = current_user() or {}
    try:
        if trigger == "op-apply":
            service.ensure_user_permission(user, "manage_operational_changes")
            payload = {
                "target_type": target_type or "",
                "target_id": target_id or "",
                "new_status": new_status or "",
                "severity": severity or "",
                "alert_type": alert_type or "Operational Change",
                "location_id": location_id or "",
                "message": message or "",
            }
            result = service.apply_operational_change(payload)
            audit("update", "operations", payload.get("target_id", ""), "Applied operational change.")
            return json.dumps(result, indent=2, default=str), "Operational change applied.", "success", True

        service.ensure_user_permission(user, "run_recalculation")
        result = service.recalculate_operations()
        audit("execute", "operations_engine", "recalculate", "Ran operations recalculation.")
        return json.dumps(result, indent=2, default=str), "Recalculation complete.", "success", True
    except Exception as exc:
        return dash.no_update, str(exc) or "Operational action failed.", "danger", True


if __name__ == "__main__":
    host = os.getenv("HOST", "127.0.0.1")
    port = int(os.getenv("PORT", "8050"))
    app.run(host=host, port=port, debug=False)
