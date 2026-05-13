COLOR_TEXT = "#e2e8f0"
COLOR_TEXT_MUTED = "#cbd5e1"
COLOR_TEXT_STRONG = "#f8fafc"
COLOR_ACCENT = "#93c5fd"

GRADIENT_PAGE = "radial-gradient(circle at top left, #1d4ed8 0%, #0f172a 32%, #020617 100%)"
GRADIENT_PANEL = "linear-gradient(180deg, rgba(15,23,42,0.92), rgba(17,24,39,0.88))"
GRADIENT_CARD = "linear-gradient(180deg, rgba(30,41,59,0.96), rgba(15,23,42,0.96))"

PAGE_STYLE = {
    "minHeight": "100vh",
    "background": GRADIENT_PAGE,
    "color": COLOR_TEXT,
}

PANEL_STYLE = {
    "background": GRADIENT_PANEL,
    "border": "1px solid rgba(96,165,250,0.18)",
    "borderRadius": "20px",
    "boxShadow": "0 24px 60px rgba(2,6,23,0.45)",
    "backdropFilter": "blur(8px)",
}

CARD_STYLE = {
    "background": GRADIENT_CARD,
    "border": "1px solid rgba(148,163,184,0.18)",
    "borderRadius": "18px",
    "boxShadow": "0 16px 38px rgba(15,23,42,0.35)",
}

ACCENT_CARD_STYLES = [
    {
        "background": "linear-gradient(135deg, rgba(37,99,235,0.98), rgba(59,130,246,0.82))",
        "border": "1px solid rgba(191,219,254,0.22)",
        "borderRadius": "18px",
        "boxShadow": "0 20px 45px rgba(37,99,235,0.28)",
    },
    {
        "background": "linear-gradient(135deg, rgba(8,145,178,0.98), rgba(34,211,238,0.8))",
        "border": "1px solid rgba(165,243,252,0.22)",
        "borderRadius": "18px",
        "boxShadow": "0 20px 45px rgba(8,145,178,0.24)",
    },
    {
        "background": "linear-gradient(135deg, rgba(234,88,12,0.96), rgba(249,115,22,0.78))",
        "border": "1px solid rgba(254,215,170,0.24)",
        "borderRadius": "18px",
        "boxShadow": "0 20px 45px rgba(234,88,12,0.24)",
    },
    {
        "background": "linear-gradient(135deg, rgba(139,92,246,0.96), rgba(168,85,247,0.78))",
        "border": "1px solid rgba(221,214,254,0.24)",
        "borderRadius": "18px",
        "boxShadow": "0 20px 45px rgba(139,92,246,0.24)",
    },
]

INPUT_STYLE = {
    "backgroundColor": "rgba(15,23,42,0.85)",
    "border": "1px solid rgba(96,165,250,0.28)",
    "color": COLOR_TEXT,
    "borderRadius": "12px",
}

DATE_TIME_LABEL_STYLE = {
    "color": COLOR_ACCENT,
    "fontSize": "0.74rem",
    "fontWeight": "700",
    "letterSpacing": "0.08em",
    "marginBottom": "0.35rem",
    "textTransform": "uppercase",
}

DATE_INPUT_STYLE = {
    **INPUT_STYLE,
    "height": "52px",
    "padding": "10px 14px",
    "fontSize": "1rem",
    "WebkitTextFillColor": "#e2e8f0",
    "colorScheme": "dark",
}

TIME_INPUT_STYLE = {
    **DATE_INPUT_STYLE,
    "fontWeight": "600",
}

TABLE_CELL_STYLE = {
    "backgroundColor": "rgba(2,6,23,0.08)",
    "color": COLOR_TEXT,
    "border": "0",
    "padding": "10px 12px",
    "fontSize": "0.95rem",
    "textAlign": "left",
    "minWidth": "120px",
    "whiteSpace": "normal",
    "height": "auto",
}

TABLE_HEADER_STYLE = {
    "backgroundColor": "rgba(30,41,59,0.92)",
    "color": COLOR_TEXT_STRONG,
    "fontWeight": "700",
    "border": "0",
    "padding": "12px",
}

TABLE_STYLE = {
    "overflowX": "auto",
    "maxWidth": "100%",
    "width": "100%",
    "borderRadius": "14px",
    "overflowY": "hidden",
}

TABLE_DATA_STYLE_CONDITIONAL = [
    {
        "if": {"state": "active"},
        "backgroundColor": "rgba(37, 99, 235, 0.18)",
        "border": "1px solid rgba(96, 165, 250, 0.45)",
        "color": "#f8fafc",
    },
    {
        "if": {"state": "selected"},
        "backgroundColor": "rgba(30, 41, 59, 0.96)",
        "border": "1px solid rgba(96, 165, 250, 0.35)",
        "color": "#f8fafc",
    },
]

TABLE_CSS = [
    {
        "selector": ".dash-spreadsheet-inner tr:hover td",
        "rule": "background-color: rgba(15, 23, 42, 0.94) !important; color: #f8fafc !important;",
    },
    {
        "selector": ".dash-spreadsheet-container .dash-spreadsheet-inner td.focused, .dash-spreadsheet-container .dash-spreadsheet-inner td.cell--selected",
        "rule": "background-color: rgba(30, 41, 59, 0.96) !important; color: #f8fafc !important; border: 1px solid rgba(96, 165, 250, 0.35) !important;",
    },
]

SECTION_TITLE_STYLE = {"color": COLOR_TEXT_STRONG, "fontWeight": "700"}

ADMIN_TAB_STYLE = {
    "background": "rgba(15,23,42,0.6)",
    "border": "1px solid rgba(96,165,250,0.14)",
    "borderRadius": "14px",
    "marginRight": "10px",
    "marginBottom": "10px",
    "padding": "2px",
}

ADMIN_ACTIVE_TAB_STYLE = {
    "background": "linear-gradient(135deg, rgba(37,99,235,0.96), rgba(59,130,246,0.82))",
    "border": "1px solid rgba(191,219,254,0.24)",
    "borderRadius": "14px",
    "marginRight": "10px",
    "marginBottom": "10px",
    "padding": "2px",
    "boxShadow": "0 12px 24px rgba(37,99,235,0.24)",
}

ADMIN_TAB_LABEL_STYLE = {
    "color": "#cbd5e1",
    "fontWeight": "600",
    "padding": "10px 14px",
}

ADMIN_ACTIVE_TAB_LABEL_STYLE = {
    "color": "#ffffff",
    "fontWeight": "700",
    "padding": "10px 14px",
}

ADMIN_PANEL_STYLE = {
    "background": "linear-gradient(180deg, rgba(10,18,38,0.92), rgba(8,15,30,0.88))",
    "border": "1px solid rgba(96,165,250,0.16)",
    "borderRadius": "20px",
    "padding": "18px",
    "boxShadow": "0 20px 50px rgba(2,6,23,0.32)",
}

ADMIN_FORM_CARD_STYLE = {
    "background": "linear-gradient(180deg, rgba(30,41,59,0.98), rgba(15,23,42,0.98))",
    "border": "1px solid rgba(96,165,250,0.18)",
    "borderRadius": "18px",
    "boxShadow": "0 20px 40px rgba(2,6,23,0.24)",
    "height": "100%",
}

ADMIN_TABLE_CARD_STYLE = {
    "background": "linear-gradient(180deg, rgba(12,20,38,0.98), rgba(6,13,30,0.98))",
    "border": "1px solid rgba(59,130,246,0.16)",
    "borderRadius": "18px",
    "boxShadow": "0 20px 40px rgba(2,6,23,0.22)",
}

PRIMARY_BUTTON_STYLE = {
    "background": "linear-gradient(135deg, #2563eb, #38bdf8)",
    "border": "0",
    "fontWeight": "700",
    "padding": "10px 16px",
}

SECONDARY_BUTTON_STYLE = {
    "background": "rgba(30,41,59,0.96)",
    "border": "1px solid rgba(148,163,184,0.22)",
    "color": "#f8fafc",
    "fontWeight": "700",
    "padding": "10px 16px",
}


def card_style(accent_index=None):
    if accent_index is None:
        return dict(CARD_STYLE)
    return dict(ACCENT_CARD_STYLES[accent_index % len(ACCENT_CARD_STYLES)])
