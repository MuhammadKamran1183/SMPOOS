import dash_bootstrap_components as dbc
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


def notification_engine_layout():
    from business_logic.service import service
    from dash_app import Severity
    from presentation.session import current_user
    from presentation.ui import admin_table_card, shell

    user = current_user() or {}
    service.ensure_user_permission(user, "view_notification_engine")
    snap = service.get_notification_engine_snapshot()
    rules = snap.get("rules", [])
    deliveries = snap.get("deliveries", [])
    notifications = snap.get("notifications", [])
    event_logs = snap.get("event_logs", [])

    def metric_card(label, value, accent_index, value_id):
        return dbc.Col(
            dbc.Card(
                dbc.CardBody(
                    [
                        html.Div(label, className="small", style={"color": "rgba(255,255,255,0.8)", "fontWeight": "600"}),
                        html.H2(value, id=value_id, className="mb-0 mt-2", style={"color": "#ffffff", "fontWeight": "800"}),
                    ]
                ),
                style=card_style(accent_index),
            ),
            md=3,
        )

    metric_cards = dbc.Row(
        [
            metric_card("Configured rules", len(rules), 0, "notification-engine-metric-rules"),
            metric_card("Deliveries", len(deliveries), 1, "notification-engine-metric-deliveries"),
            metric_card("Notifications", len(notifications), 2, "notification-engine-metric-notifications"),
            metric_card("Event logs", len(event_logs), 3, "notification-engine-metric-events"),
        ],
        className="g-3 mb-3",
    )

    content = html.Div(
        [
            dcc.Store(id="notification-engine-snapshot", data=snap),
            dcc.Store(id="notification-engine-refresh-signal"),
            dcc.Interval(id="notification-engine-refresh", interval=3000, n_intervals=0),
            html.Div("Alert Automation", style={"color": "#fb923c", "fontWeight": "700", "letterSpacing": "0.08em", "textTransform": "uppercase", "fontSize": "0.8rem"}),
            html.H2("Notification Engine", className="mb-1", style={"color": "#f8fafc", "fontWeight": "800"}),
            html.Div("Configure notification rules, track deliveries, and review live event activity in one place.", className="mb-3", style={"color": "#cbd5e1"}),
            metric_cards,
            dbc.Card(
                dbc.CardBody(
                    [
                        html.Div("Admin Editor", style={"color": "#fb923c", "fontWeight": "700", "letterSpacing": "0.08em", "textTransform": "uppercase", "fontSize": "0.74rem"}),
                        html.H5("Notification Rules", className="mb-3 mt-1", style=SECTION_TITLE_STYLE),
                        dbc.Row(
                            [
                                dbc.Col(dbc.Input(id="rule-id", placeholder="Rule ID e.g. NR0001 (optional)", className="mb-2", style=INPUT_STYLE), md=6),
                                dbc.Col(dbc.Input(id="rule-name", placeholder="Rule Name", className="mb-2", style=INPUT_STYLE), md=6),
                            ],
                            className="g-2",
                        ),
                        dbc.Row(
                            [
                                dbc.Col(dbc.Input(id="rule-location", placeholder="Location ID e.g. L0012", className="mb-2", style=INPUT_STYLE), md=6),
                                dbc.Col(dbc.Input(id="rule-role", placeholder="Target Role e.g. Harbourmaster", className="mb-2", style=INPUT_STYLE), md=6),
                            ],
                            className="g-2",
                        ),
                        dbc.Row(
                            [
                                dbc.Col(dbc.Input(id="rule-context", placeholder="Context Type e.g. weather", className="mb-2", style=INPUT_STYLE), md=6),
                                dbc.Col(dbc.Input(id="rule-metric", placeholder="Metric Name e.g. wind_speed_knots", className="mb-2", style=INPUT_STYLE), md=6),
                            ],
                            className="g-2",
                        ),
                        dbc.Row(
                            [
                                dbc.Col(dbc.Input(id="rule-operator", placeholder="Operator e.g. >=", className="mb-2", style=INPUT_STYLE), md=4),
                                dbc.Col(dbc.Input(id="rule-threshold", placeholder="Threshold", className="mb-2", style=INPUT_STYLE), md=4),
                                dbc.Col(dbc.Select(id="rule-severity", options=[{"label": s.value, "value": s.value} for s in Severity], value=Severity.MEDIUM.value, className="mb-2", style=INPUT_STYLE), md=4),
                            ],
                            className="g-2",
                        ),
                        dbc.Row(
                            [
                                dbc.Col(dbc.Select(id="rule-channels", options=[{"label": "In System", "value": "in_system"}, {"label": "Email", "value": "email"}, {"label": "In System + Email", "value": "in_system,email"}], value="in_system", className="mb-2", style=INPUT_STYLE), md=6),
                                dbc.Col(dbc.Select(id="rule-active", options=[{"label": "Yes", "value": "Yes"}, {"label": "No", "value": "No"}], value="Yes", className="mb-2", style=INPUT_STYLE), md=6),
                            ],
                            className="g-2",
                        ),
                        dbc.Textarea(id="rule-message", placeholder="Message template", className="mb-2", style=INPUT_STYLE),
                        dbc.ButtonGroup(
                            [
                                dbc.Button("Save Rule", id="save-rule", style=PRIMARY_BUTTON_STYLE),
                                dbc.Button("Delete Rule", id="delete-rule", style=SECONDARY_BUTTON_STYLE),
                            ]
                        ),
                    ],
                    style={"padding": "18px"},
                ),
                style={**ADMIN_FORM_CARD_STYLE, "marginBottom": "1rem"},
            ),
            dbc.Card(
                dbc.CardBody(
                    [
                        html.Div("Live Records", style={"color": "#60a5fa", "fontWeight": "700", "letterSpacing": "0.08em", "textTransform": "uppercase", "fontSize": "0.74rem"}),
                        html.H5("Configured Rules", className="mb-3 mt-1", style=SECTION_TITLE_STYLE),
                        standard_table(
                            table_id="notification-rules-table",
                            columns=[{"name": c.replace("_", " ").title(), "id": c} for c in ["rule_id", "name", "target_role", "context_type", "metric_name", "operator", "threshold_value", "severity", "channels", "active"]],
                            data=rules,
                            page_size=8,
                        ),
                    ],
                    style={"padding": "18px"},
                ),
                style={**ADMIN_TABLE_CARD_STYLE, "marginBottom": "1rem"},
            ),
            dbc.Card(
                dbc.CardBody(
                    [
                        html.Div("Live Records", style={"color": "#60a5fa", "fontWeight": "700", "letterSpacing": "0.08em", "textTransform": "uppercase", "fontSize": "0.74rem"}),
                        html.H5("Delivery Audit Trail", className="mb-3 mt-1", style=SECTION_TITLE_STYLE),
                        standard_table(
                            table_id="notification-deliveries-table",
                            columns=[{"name": c.replace("_", " ").title(), "id": c} for c in ["delivery_id", "notification_id", "rule_id", "target_role", "channel", "status", "delivered_at"]],
                            data=deliveries,
                            page_size=8,
                        ),
                    ],
                    style={"padding": "18px"},
                ),
                style={**ADMIN_TABLE_CARD_STYLE, "marginBottom": "1rem"},
            ),
            dbc.Card(
                dbc.CardBody(
                    [
                        html.Div("Live Records", style={"color": "#60a5fa", "fontWeight": "700", "letterSpacing": "0.08em", "textTransform": "uppercase", "fontSize": "0.74rem"}),
                        html.H5("Recent Notification Records", className="mb-3 mt-1", style=SECTION_TITLE_STYLE),
                        standard_table(
                            table_id="notification-records-table",
                            columns=[{"name": c.replace("_", " ").title(), "id": c} for c in ["notification_id", "alert_type", "location_id", "severity", "message", "timestamp"]],
                            data=notifications,
                            page_size=8,
                        ),
                    ],
                    style={"padding": "18px"},
                ),
                style={**ADMIN_TABLE_CARD_STYLE, "marginBottom": "1rem"},
            ),
            admin_table_card("Notification Event Log", event_logs, ["event_id", "event_type", "entity_type", "entity_id", "severity", "created_at"], page_size=12, table_id="notification-event-log-table"),
        ]
    )
    return shell(content, "/notification-engine")
