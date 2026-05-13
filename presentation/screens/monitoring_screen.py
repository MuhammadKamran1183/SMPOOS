import dash_bootstrap_components as dbc
import plotly.graph_objects as go
from dash import dcc, html

from presentation.components import standard_table
from presentation.theme import CARD_STYLE, SECTION_TITLE_STYLE, card_style


def monitoring_layout():
    from business_logic.service import service
    from presentation.helpers import format_table_rows, safe_float
    from presentation.session import current_user
    from presentation.ui import shell

    user = current_user() or {}
    service.ensure_user_permission(user, "view_monitoring")
    snap = service.get_monitoring_snapshot()
    alerts = snap.get("alerts", [])
    vessels = snap.get("vessel_movements", [])
    occupancy = snap.get("berth_occupancy", [])

    occupied_berths = sum(1 for row in occupancy if safe_float(row.get("occupancy_percent")) > 0)
    average_occupancy = round(sum(safe_float(row.get("occupancy_percent")) for row in occupancy) / len(occupancy), 1) if occupancy else 0
    queued_or_holding = sum(1 for row in vessels if str(row.get("status", "")).strip().lower() in {"queued", "holding"})
    high_alerts = sum(1 for row in alerts if str(row.get("severity", "")).strip().lower() == "high")

    metric_specs = [
        ("Occupied berths", occupied_berths),
        ("Average occupancy %", average_occupancy),
        ("Queued / holding", queued_or_holding),
        ("High severity alerts", high_alerts),
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

    vessel_table = standard_table(
        columns=[{"name": c.replace("_", " ").title(), "id": c} for c in ["path_id", "vessel_name", "status", "estimated_arrival", "estimated_departure"]],
        data=format_table_rows(vessels, ["path_id", "vessel_name", "status", "estimated_arrival", "estimated_departure"]),
        page_size=10,
        style_cell_conditional=[
            {"if": {"column_id": "path_id"}, "minWidth": "120px", "width": "120px"},
            {"if": {"column_id": "vessel_name"}, "minWidth": "170px", "width": "170px"},
            {"if": {"column_id": "status"}, "minWidth": "120px", "width": "120px"},
            {"if": {"column_id": "estimated_arrival"}, "minWidth": "220px", "width": "220px"},
            {"if": {"column_id": "estimated_departure"}, "minWidth": "220px", "width": "220px"},
        ],
    )

    alert_table = standard_table(
        columns=[{"name": c.replace("_", " ").title(), "id": c} for c in ["notification_id", "alert_type", "location_id", "severity", "timestamp"]],
        data=format_table_rows(alerts, ["notification_id", "alert_type", "location_id", "severity", "timestamp"]),
        page_size=10,
        style_cell_conditional=[
            {"if": {"column_id": "notification_id"}, "minWidth": "140px", "width": "140px"},
            {"if": {"column_id": "alert_type"}, "minWidth": "180px", "width": "180px"},
            {"if": {"column_id": "location_id"}, "minWidth": "130px", "width": "130px"},
            {"if": {"column_id": "severity"}, "minWidth": "120px", "width": "120px"},
            {"if": {"column_id": "timestamp"}, "minWidth": "220px", "width": "220px"},
        ],
    )

    fig_occ = go.Figure(
        go.Bar(
            x=[r.get("berth_name") for r in occupancy[:12]],
            y=[r.get("occupancy_percent", 0) for r in occupancy[:12]],
            marker=dict(color="#4f46e5", line=dict(color="#93c5fd", width=1.2)),
            hovertemplate="<b>%{x}</b><br>Occupancy: %{y}%<extra></extra>",
        )
    )
    fig_occ.update_layout(
        template="plotly_dark",
        height=320,
        margin=dict(l=10, r=10, t=30, b=30),
        yaxis_title="Occupancy %",
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(2,6,23,0.35)",
        font=dict(color="#e2e8f0"),
    )

    status_counts = {}
    for row in vessels:
        status = str(row.get("status", "")).strip() or "Unknown"
        status_counts[status] = status_counts.get(status, 0) + 1
    status_labels = list(status_counts.keys()) or ["No Data"]
    status_values = list(status_counts.values()) or [1]
    status_colors = ["#38bdf8", "#22c55e", "#f59e0b", "#8b5cf6", "#f43f5e", "#64748b"]
    fig_status = go.Figure(
        go.Pie(
            labels=status_labels,
            values=status_values,
            hole=0.58,
            marker=dict(colors=status_colors[: len(status_labels)]),
            textinfo="label+percent",
            hovertemplate="<b>%{label}</b><br>Vessels: %{value}<extra></extra>",
        )
    )
    fig_status.update_layout(
        template="plotly_dark",
        height=320,
        margin=dict(l=10, r=10, t=30, b=30),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(2,6,23,0.35)",
        font=dict(color="#e2e8f0"),
        legend=dict(orientation="h", yanchor="bottom", y=-0.15, x=0.5, xanchor="center"),
    )

    content = html.Div(
        [
            html.Div("Live Tracking", style={"color": "#93c5fd", "fontWeight": "700", "letterSpacing": "0.08em", "textTransform": "uppercase", "fontSize": "0.8rem"}),
            html.H2("Monitor Port", className="mb-1", style={"color": "#f8fafc", "fontWeight": "800"}),
            html.Div("Operational monitoring of vessels, berths, and alerts with the same live dashboard experience.", className="mb-3", style={"color": "#cbd5e1"}),
            metric_cards,
            dbc.Row(
                [
                    dbc.Col(
                        dbc.Card(
                            dbc.CardBody(
                                [html.H5("Berth Occupancy", className="mb-3", style=SECTION_TITLE_STYLE), dcc.Graph(figure=fig_occ, config={"displayModeBar": False})],
                                style={"padding": "18px"},
                            ),
                            style=CARD_STYLE,
                        ),
                        md=6,
                    ),
                    dbc.Col(
                        dbc.Card(
                            dbc.CardBody(
                                [html.H5("Vessel Status Breakdown", className="mb-3", style=SECTION_TITLE_STYLE), dcc.Graph(figure=fig_status, config={"displayModeBar": False})],
                                style={"padding": "18px"},
                            ),
                            style=CARD_STYLE,
                        ),
                        md=6,
                    ),
                ],
                className="g-3 mb-3",
            ),
            dbc.Card(dbc.CardBody([html.H5("Latest Alerts", className="mb-3", style=SECTION_TITLE_STYLE), alert_table], style={"padding": "18px"}), style=CARD_STYLE),
            dbc.Card(dbc.CardBody([html.H5("Vessel Movements", className="mb-3", style=SECTION_TITLE_STYLE), vessel_table], style={"padding": "18px"}), style={**CARD_STYLE, "marginTop": "1rem"}),
        ]
    )
    return shell(content, "/monitoring")
