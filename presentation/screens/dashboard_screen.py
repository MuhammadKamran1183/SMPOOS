import dash_bootstrap_components as dbc
from dash import dcc, html

from presentation.components import standard_table
from presentation.theme import CARD_STYLE, INPUT_STYLE, SECTION_TITLE_STYLE, card_style


def dashboard_layout():
    from business_logic.service import service
    from presentation.helpers import format_table_rows
    from presentation.session import current_user
    from presentation.charts import fig_congestion_heatmap, fig_map_overlay, normalise_management_snapshot, seaborn_heatmap_png
    from presentation.ui import shell

    user = current_user() or {}
    service.ensure_user_permission(user, "view_management_dashboard")
    runtime_context = {"https_enabled": True, "session_count": 1}
    snap = normalise_management_snapshot(service.get_management_dashboard_snapshot(user=user, filters={}, runtime_context=runtime_context))
    status_overview = snap.get("port_status_overview", {}) or {}
    activity_rows = snap.get("vessel_vehicle_activity", []) or []
    vessel_rows = [row for row in activity_rows if str(row.get("activity_type", "")).strip().lower() == "vessel"]
    vehicle_rows = [row for row in activity_rows if str(row.get("activity_type", "")).strip().lower() != "vessel"]
    alerts = snap.get("alerts_panel", []) or []
    analytics_summary = snap.get("analytics_summary", {}) or {}
    heatmap_rows = snap.get("congestion_heatmap", []) or []
    map_overlays = snap.get("map_overlays", {}) or {}
    occupancy_rows = service.get_monitoring_snapshot().get("berth_occupancy", [])

    metric_specs = [
        ("Occupied berths", status_overview.get("occupied_berths", 0)),
        ("Vessel queue", status_overview.get("vessel_queue", 0)),
        ("Average wind (knots)", status_overview.get("average_wind_knots", 0)),
        ("Environmental alert zones", status_overview.get("environmental_alert_zones", 0)),
    ]
    cards = dbc.Row(
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

    analytics_specs = [
        ("Most used berth", analytics_summary.get("most_used_berth", "")),
        ("Busiest route", analytics_summary.get("busiest_route", "")),
        ("Peak congestion", analytics_summary.get("peak_congestion_hour", "")),
        ("Highest wind zone", analytics_summary.get("highest_wind_zone", "")),
    ]
    analytics_cards = dbc.Row(
        [
            dbc.Col(
                dbc.Card(
                    dbc.CardBody(
                        [
                            html.Div(label, className="small", style={"color": "#93c5fd", "fontWeight": "600"}),
                            html.H4(value, className="mb-0 mt-2", style={"color": "#f8fafc", "fontWeight": "700"}),
                        ]
                    ),
                    style=CARD_STYLE,
                ),
                md=3,
            )
            for label, value in analytics_specs
        ],
        className="g-3 mb-3",
    )

    vessel_table = standard_table(
        columns=[
            {"name": "Asset Name", "id": "asset_name"},
            {"name": "Status", "id": "status"},
            {"name": "Current Location", "id": "current_location"},
            {"name": "Target Location", "id": "target_location"},
            {"name": "Assigned Route", "id": "assigned_route"},
            {"name": "Last Updated", "id": "last_updated"},
        ],
        data=format_table_rows(vessel_rows, ["asset_name", "status", "current_location", "target_location", "assigned_route", "last_updated"]),
        page_size=8,
        style_cell_conditional=[
            {"if": {"column_id": "asset_name"}, "minWidth": "150px", "width": "150px"},
            {"if": {"column_id": "status"}, "minWidth": "120px", "width": "120px"},
            {"if": {"column_id": "current_location"}, "minWidth": "140px", "width": "140px"},
            {"if": {"column_id": "target_location"}, "minWidth": "140px", "width": "140px"},
            {"if": {"column_id": "assigned_route"}, "minWidth": "120px", "width": "120px"},
            {"if": {"column_id": "last_updated"}, "minWidth": "220px", "width": "220px"},
        ],
    )

    vehicle_table = standard_table(
        columns=[
            {"name": "Asset Name", "id": "asset_name"},
            {"name": "Status", "id": "status"},
            {"name": "Current Location", "id": "current_location"},
            {"name": "Target Activity", "id": "target_location"},
            {"name": "Assigned Route", "id": "assigned_route"},
            {"name": "Last Updated", "id": "last_updated"},
        ],
        data=format_table_rows(vehicle_rows, ["asset_name", "status", "current_location", "target_location", "assigned_route", "last_updated"]),
        page_size=8,
        style_cell_conditional=[
            {"if": {"column_id": "asset_name"}, "minWidth": "150px", "width": "150px"},
            {"if": {"column_id": "status"}, "minWidth": "120px", "width": "120px"},
            {"if": {"column_id": "current_location"}, "minWidth": "140px", "width": "140px"},
            {"if": {"column_id": "target_location"}, "minWidth": "150px", "width": "150px"},
            {"if": {"column_id": "assigned_route"}, "minWidth": "130px", "width": "130px"},
            {"if": {"column_id": "last_updated"}, "minWidth": "220px", "width": "220px"},
        ],
    )

    alert_table = standard_table(
        table_id="dashboard-alert-table",
        columns=[
            {"name": "Notification ID", "id": "notification_id"},
            {"name": "Alert Type", "id": "alert_type"},
            {"name": "Location ID", "id": "location_id"},
            {"name": "Severity", "id": "severity"},
            {"name": "Message", "id": "message"},
            {"name": "Timestamp", "id": "timestamp"},
        ],
        data=format_table_rows(alerts, ["notification_id", "alert_type", "location_id", "severity", "message", "timestamp"]),
        page_size=8,
        style_cell_conditional=[
            {"if": {"column_id": "notification_id"}, "minWidth": "140px", "width": "140px"},
            {"if": {"column_id": "alert_type"}, "minWidth": "150px", "width": "150px"},
            {"if": {"column_id": "location_id"}, "minWidth": "120px", "width": "120px"},
            {"if": {"column_id": "severity"}, "minWidth": "110px", "width": "110px"},
            {"if": {"column_id": "message"}, "minWidth": "420px", "width": "420px"},
            {"if": {"column_id": "timestamp"}, "minWidth": "220px", "width": "220px"},
        ],
    )

    overlay_options = [
        {"label": "Berths", "value": "berths"},
        {"label": "Shipping Lanes", "value": "shipping_lanes"},
        {"label": "Restricted Zones", "value": "restricted_zones"},
    ]
    try:
        occupancy_png = seaborn_heatmap_png(occupancy_rows)
        occupancy_panel = html.Img(src=occupancy_png, style={"width": "100%", "borderRadius": "8px"})
    except Exception:
        occupancy_panel = dbc.Alert("Heatmap unavailable (Matplotlib/Seaborn rendering failed).", color="warning")

    content = html.Div(
        [
            dcc.Store(id="mgmt-snapshot", data=snap),
            dcc.Interval(id="dashboard-refresh", interval=5000, n_intervals=0),
            html.Div("Maritime Overview", style={"color": "#93c5fd", "fontWeight": "700", "letterSpacing": "0.08em", "textTransform": "uppercase", "fontSize": "0.8rem"}),
            html.H2("Dashboard", className="mb-1", style={"color": "#f8fafc", "fontWeight": "800"}),
            html.Div("Port status overview, activity, alerts, analytics summaries, and overlays.", className="mb-3", style={"color": "#cbd5e1"}),
            cards,
            analytics_cards,
            dbc.Row(
                [
                    dbc.Col(
                        dbc.Card(
                            dbc.CardBody(
                                [
                                    html.H5("Congestion Score by Zone & Time Window", className="mb-3", style=SECTION_TITLE_STYLE),
                                    dcc.Graph(id="mgmt-heatmap", figure=fig_congestion_heatmap(heatmap_rows), config={"displayModeBar": False}),
                                ]
                            ),
                            style=CARD_STYLE,
                        ),
                        md=6,
                    ),
                    dbc.Col(dbc.Card(dbc.CardBody([html.H5("Berth Occupancy Correlation (Seaborn)", className="mb-3", style=SECTION_TITLE_STYLE), occupancy_panel]), style=CARD_STYLE), md=6),
                ],
                className="g-3 mb-3",
            ),
            dbc.Card(
                dbc.CardBody(
                    [
                        html.H5("Interactive Map Overlays", className="mb-3", style=SECTION_TITLE_STYLE),
                        dbc.Row(
                            [
                                dbc.Col(dbc.Select(id="map-overlay", options=overlay_options, value="berths", style=INPUT_STYLE), xs=12, md=5, lg=4),
                            ],
                            className="g-2 mb-2 justify-content-end",
                        ),
                        dcc.Graph(id="mgmt-map", figure=fig_map_overlay(map_overlays, "berths"), config={"displayModeBar": False}),
                    ]
                ),
                style={**CARD_STYLE, "marginBottom": "1rem"},
            ),
            dbc.Row(
                [
                    dbc.Col(dbc.Card(dbc.CardBody([html.H5("Vessel Activity", className="mb-3", style=SECTION_TITLE_STYLE), vessel_table], style={"padding": "18px"}), style=CARD_STYLE), xs=12),
                    dbc.Col(dbc.Card(dbc.CardBody([html.H5("Vehicle / Cargo Activity", className="mb-3", style=SECTION_TITLE_STYLE), vehicle_table], style={"padding": "18px"}), style=CARD_STYLE), xs=12),
                    dbc.Col(dbc.Card(dbc.CardBody([html.H5("Notifications & Alerts", className="mb-3", style=SECTION_TITLE_STYLE), alert_table], style={"padding": "18px"}), style=CARD_STYLE), xs=12),
                ],
                className="g-3 mb-2",
            ),
        ]
    )
    return shell(content, "/dashboard")
