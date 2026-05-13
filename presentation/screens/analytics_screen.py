from collections import Counter

import dash_bootstrap_components as dbc
import plotly.graph_objects as go
from dash import dcc, html

from presentation.components import standard_table
from presentation.theme import (
    ADMIN_FORM_CARD_STYLE,
    ADMIN_TABLE_CARD_STYLE,
    INPUT_STYLE,
    PRIMARY_BUTTON_STYLE,
    SECTION_TITLE_STYLE,
    SECONDARY_BUTTON_STYLE,
    card_style,
)


REPORT_COLUMNS = [
    "vessel_name",
    "vessel_type",
    "cargo_type",
    "current_location_id",
    "destination",
    "assigned_route_id",
    "assigned_berth_id",
    "eta",
    "status",
]


def _base_figure():
    fig = go.Figure()
    fig.update_layout(
        template="plotly_dark",
        height=320,
        margin=dict(l=40, r=24, t=36, b=40),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(2,6,23,0.35)",
        font=dict(color="#e2e8f0"),
    )
    return fig


def _empty_figure(title):
    fig = _base_figure()
    fig.update_layout(title=title)
    fig.add_annotation(
        text="No data available",
        x=0.5,
        y=0.5,
        xref="paper",
        yref="paper",
        showarrow=False,
        font=dict(size=14, color="#cbd5e1"),
    )
    fig.update_xaxes(visible=False)
    fig.update_yaxes(visible=False)
    return fig


def build_report_graphs(report):
    rows = (report or {}).get("rows", []) or []
    if not rows:
        return (
            _empty_figure("Vessel Types"),
            _empty_figure("Top Destinations"),
            _empty_figure("Status Mix"),
        )

    vessel_counts = Counter(row.get("vessel_type") or "Unknown" for row in rows)
    destination_counts = Counter(row.get("destination") or "Unknown" for row in rows)
    status_counts = Counter(row.get("status") or "Unknown" for row in rows)

    top_vessels = vessel_counts.most_common(6)
    fig_vessels = _base_figure()
    fig_vessels.add_trace(
        go.Bar(
            x=[label for label, _ in top_vessels],
            y=[value for _, value in top_vessels],
            marker=dict(color="#38bdf8", line=dict(color="#bfdbfe", width=1.2)),
            hovertemplate="<b>%{x}</b><br>Records: %{y}<extra></extra>",
        )
    )
    fig_vessels.update_layout(title="Vessel Types", xaxis_title="Type", yaxis_title="Records")

    top_destinations = destination_counts.most_common(6)
    fig_destinations = _base_figure()
    fig_destinations.add_trace(
        go.Bar(
            x=[value for _, value in top_destinations],
            y=[label for label, _ in top_destinations],
            orientation="h",
            marker=dict(color="#22c55e", line=dict(color="#bbf7d0", width=1.2)),
            hovertemplate="<b>%{y}</b><br>Records: %{x}<extra></extra>",
        )
    )
    fig_destinations.update_layout(title="Top Destinations", xaxis_title="Records", yaxis_title="")

    fig_status = _base_figure()
    fig_status.add_trace(
        go.Pie(
            labels=list(status_counts.keys()),
            values=list(status_counts.values()),
            hole=0.45,
            marker=dict(colors=["#f59e0b", "#8b5cf6", "#fb7185", "#67e8f9", "#a3e635", "#f97316"]),
        )
    )
    fig_status.update_layout(title="Status Mix", margin=dict(l=24, r=24, t=36, b=24))

    return fig_vessels, fig_destinations, fig_status


def analytics_layout():
    from business_logic.service import service
    from presentation.helpers import format_table_rows
    from presentation.session import current_user
    from presentation.ui import shell

    user = current_user() or {}
    service.ensure_user_permission(user, "view_analytics")
    snap = service.get_analytics_snapshot()
    report = service.generate_custom_report({})
    summary = snap.get("summary", {})
    report_summary = report.get("summary", {})
    recommendations = report.get("recommendations", [])
    vessel_fig, destination_fig, status_fig = build_report_graphs(report)

    metric_specs = [
        ("Most used berth", summary.get("most_used_berth", "No data")),
        ("Busiest route", summary.get("busiest_route", "No data")),
        ("Peak congestion", summary.get("peak_congestion_hour", "No data")),
        ("Highest wind zone", summary.get("highest_wind_zone", "No data")),
    ]
    metric_cards = dbc.Row(
        [
            dbc.Col(
                dbc.Card(
                    dbc.CardBody(
                        [
                            html.Div(label, className="small", style={"color": "rgba(255,255,255,0.8)", "fontWeight": "600"}),
                            html.H4(value, className="mb-0 mt-2", style={"color": "#ffffff", "fontWeight": "800"}),
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

    content = html.Div(
        [
            dcc.Store(id="analytics-report-store", data=report),
            html.Div("Operational Insight", style={"color": "#67e8f9", "fontWeight": "700", "letterSpacing": "0.08em", "textTransform": "uppercase", "fontSize": "0.8rem"}),
            html.H2("Analytics", className="mb-1", style={"color": "#f8fafc", "fontWeight": "800"}),
            html.Div("Generate filtered analytics reports with the earlier report builder layout.", className="mb-3", style={"color": "#cbd5e1"}),
            metric_cards,
            dbc.Row(
                [
                    dbc.Col(
                        dbc.Card(
                            dbc.CardBody(
                                [
                                    html.Div("Report Builder", style={"color": "#67e8f9", "fontWeight": "700", "letterSpacing": "0.08em", "textTransform": "uppercase", "fontSize": "0.74rem"}),
                                    html.H5("Analytics Filters", className="mb-3 mt-1", style=SECTION_TITLE_STYLE),
                                    dbc.Row(
                                        [
                                            dbc.Col(dbc.Input(id="analytics-start-date", type="date", style=INPUT_STYLE), md=6),
                                            dbc.Col(dbc.Input(id="analytics-end-date", type="date", style=INPUT_STYLE), md=6),
                                        ],
                                        className="g-2 mb-2",
                                    ),
                                    dbc.Row(
                                        [
                                            dbc.Col(dbc.Input(id="analytics-vessel-type", placeholder="Vessel Type", style=INPUT_STYLE), md=4),
                                            dbc.Col(dbc.Input(id="analytics-cargo-type", placeholder="Cargo Type", style=INPUT_STYLE), md=4),
                                            dbc.Col(dbc.Input(id="analytics-port-area", placeholder="Port Area", style=INPUT_STYLE), md=4),
                                        ],
                                        className="g-2 mb-2",
                                    ),
                                    dbc.ButtonGroup(
                                        [
                                            dbc.Button("Generate Report", id="analytics-generate", style=PRIMARY_BUTTON_STYLE),
                                            dbc.Button("Reset Filters", id="analytics-reset", style=SECONDARY_BUTTON_STYLE),
                                        ]
                                    ),
                                    dbc.Alert(id="analytics-report-alert", is_open=False, duration=3000, color="success", className="mt-3", style={"borderRadius": "14px", "border": "0"}),
                                ],
                                style={"padding": "18px"},
                            ),
                            style={**ADMIN_FORM_CARD_STYLE, "height": "100%"},
                        ),
                        md=5,
                    ),
                    dbc.Col(
                        dbc.Card(
                            dbc.CardBody(
                                [
                                    html.Div("Report Summary", style={"color": "#67e8f9", "fontWeight": "700", "letterSpacing": "0.08em", "textTransform": "uppercase", "fontSize": "0.74rem"}),
                                    html.H5("Generated Report", className="mb-3 mt-1", style=SECTION_TITLE_STYLE),
                                    dbc.Row(
                                        [
                                            dbc.Col(dbc.Card(dbc.CardBody([html.Div("Matched Records", className="small", style={"color": "#93c5fd"}), html.H3(report_summary.get("matched_records", 0), id="analytics-report-matched", className="mb-0", style={"color": "#ffffff"})]), style=card_style(0)), md=4),
                                            dbc.Col(dbc.Card(dbc.CardBody([html.Div("Vessel Types", className="small", style={"color": "#a7f3d0"}), html.H3(len(report_summary.get("vessel_types", [])), id="analytics-report-vessel-count", className="mb-0", style={"color": "#ffffff"})]), style=card_style(1)), md=4),
                                            dbc.Col(dbc.Card(dbc.CardBody([html.Div("Cargo Types", className="small", style={"color": "#fde68a"}), html.H3(len(report_summary.get("cargo_types", [])), id="analytics-report-cargo-count", className="mb-0", style={"color": "#ffffff"})]), style=card_style(2)), md=4),
                                        ],
                                        className="g-3 mb-3",
                                    ),
                                    html.Div(["Generated at: ", html.Span(report.get("generated_at", "-"), id="analytics-report-generated-at", style={"color": "#f8fafc"})], style={"color": "#cbd5e1", "marginBottom": "0.75rem"}),
                                    html.Div(["Vessel types: ", html.Span(", ".join(report_summary.get("vessel_types", [])) or "All", id="analytics-report-vessel-types", style={"color": "#f8fafc"})], style={"color": "#cbd5e1", "marginBottom": "0.5rem"}),
                                    html.Div(["Cargo types: ", html.Span(", ".join(report_summary.get("cargo_types", [])) or "All", id="analytics-report-cargo-types", style={"color": "#f8fafc"})], style={"color": "#cbd5e1"}),
                                ],
                                style={"padding": "18px"},
                            ),
                            style={**ADMIN_TABLE_CARD_STYLE, "height": "100%"},
                        ),
                        md=7,
                    ),
                ],
                className="g-3 mb-3",
            ),
            dbc.Card(
                dbc.CardBody(
                    [
                        html.Div("Visual Summary", style={"color": "#67e8f9", "fontWeight": "700", "letterSpacing": "0.08em", "textTransform": "uppercase", "fontSize": "0.74rem"}),
                        html.H5("Report Graphs", className="mb-2 mt-1", style=SECTION_TITLE_STYLE),
                        html.Div("Charts update from the current filters and appear before the table for quick scanning.", className="mb-3", style={"color": "#cbd5e1"}),
                        dbc.Row(
                            [
                                dbc.Col(
                                    dbc.Card(
                                        dbc.CardBody(
                                            [
                                                html.Div("Visual Summary", style={"color": "#67e8f9", "fontWeight": "700", "letterSpacing": "0.08em", "textTransform": "uppercase", "fontSize": "0.74rem"}),
                                                html.H5("Vessel Types", className="mb-3 mt-1", style=SECTION_TITLE_STYLE),
                                                dcc.Graph(id="analytics-vessel-type-graph", figure=vessel_fig, config={"displayModeBar": False}),
                                            ],
                                            style={"padding": "18px"},
                                        ),
                                        style=ADMIN_TABLE_CARD_STYLE,
                                    ),
                                    md=4,
                                ),
                                dbc.Col(
                                    dbc.Card(
                                        dbc.CardBody(
                                            [
                                                html.Div("Visual Summary", style={"color": "#67e8f9", "fontWeight": "700", "letterSpacing": "0.08em", "textTransform": "uppercase", "fontSize": "0.74rem"}),
                                                html.H5("Top Destinations", className="mb-3 mt-1", style=SECTION_TITLE_STYLE),
                                                dcc.Graph(id="analytics-destination-graph", figure=destination_fig, config={"displayModeBar": False}),
                                            ],
                                            style={"padding": "18px"},
                                        ),
                                        style=ADMIN_TABLE_CARD_STYLE,
                                    ),
                                    md=4,
                                ),
                                dbc.Col(
                                    dbc.Card(
                                        dbc.CardBody(
                                            [
                                                html.Div("Visual Summary", style={"color": "#67e8f9", "fontWeight": "700", "letterSpacing": "0.08em", "textTransform": "uppercase", "fontSize": "0.74rem"}),
                                                html.H5("Status Mix", className="mb-3 mt-1", style=SECTION_TITLE_STYLE),
                                                dcc.Graph(id="analytics-status-graph", figure=status_fig, config={"displayModeBar": False}),
                                            ],
                                            style={"padding": "18px"},
                                        ),
                                        style=ADMIN_TABLE_CARD_STYLE,
                                    ),
                                    md=4,
                                ),
                            ],
                            className="g-3",
                        ),
                    ],
                    style={"padding": "18px"},
                ),
                style={**ADMIN_TABLE_CARD_STYLE, "marginBottom": "1rem"},
            ),
            dbc.Row(
                [
                    dbc.Col(
                        dbc.Card(
                            dbc.CardBody(
                                [
                                    html.Div("Report Results", style={"color": "#67e8f9", "fontWeight": "700", "letterSpacing": "0.08em", "textTransform": "uppercase", "fontSize": "0.74rem"}),
                                    html.H5("Filtered Vessel Movements", className="mb-3 mt-1", style=SECTION_TITLE_STYLE),
                                    standard_table(
                                        table_id="analytics-report-table",
                                        columns=[{"name": c.replace("_", " ").title(), "id": c} for c in REPORT_COLUMNS],
                                        data=format_table_rows(report.get("rows", []), REPORT_COLUMNS),
                                        page_size=10,
                                    ),
                                ],
                                style={"padding": "18px"},
                            ),
                            style=ADMIN_TABLE_CARD_STYLE,
                        )
                    ),
                ],
                className="g-3 mb-3",
            ),
            dbc.Card(
                dbc.CardBody(
                    [
                        html.Div("Recommended Actions", style={"color": "#67e8f9", "fontWeight": "700", "letterSpacing": "0.08em", "textTransform": "uppercase", "fontSize": "0.74rem"}),
                        html.H5("Recommendations", className="mb-3 mt-1", style=SECTION_TITLE_STYLE),
                        dbc.ListGroup(recommendation_items, id="analytics-report-recommendations", flush=True),
                    ],
                    style={"padding": "18px"},
                ),
                style=ADMIN_TABLE_CARD_STYLE,
            ),
        ]
    )
    return shell(content, "/analytics")
