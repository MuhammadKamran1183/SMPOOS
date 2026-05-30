import base64
import io
import math

import matplotlib.pyplot as plt
import plotly.graph_objects as go
import seaborn as sns

from presentation.helpers import safe_float


def _mean(values: list[float]) -> float:
    return sum(values) / len(values) if values else 0.0


def _stdev(values: list[float], mean: float) -> float:
    if not values:
        return 0.0
    return math.sqrt(sum((value - mean) ** 2 for value in values) / max(1, (len(values) - 1)))


def _covariance(left: list[float], right: list[float], left_mean: float, right_mean: float) -> float:
    if not left:
        return 0.0
    return sum((a - left_mean) * (b - right_mean) for a, b in zip(left, right)) / max(1, (len(left) - 1))


def corr_matrix(rows, keys):
    key_list = list(keys)
    values = [[safe_float(row.get(key)) for key in key_list] for row in (rows or [])]
    columns = [list(col) for col in zip(*values)] if values else [[] for _ in key_list]

    means = [_mean(col) for col in columns]
    stdevs = [_stdev(col, mean) for col, mean in zip(columns, means)]

    matrix = []
    for i in range(len(columns)):
        row_values = []
        for j in range(len(columns)):
            if i == j:
                row_values.append(1.0)
                continue
            denom = (stdevs[i] * stdevs[j]) or 1.0
            row_values.append(_covariance(columns[i], columns[j], means[i], means[j]) / denom)
        matrix.append(row_values)
    return matrix


def seaborn_heatmap_png(occupancy_rows):
    keys = ["occupied_tonnes", "capacity_tonnes", "occupancy_percent"]
    labels = ["Occupied", "Capacity", "Occupancy%"]
    matrix = corr_matrix(occupancy_rows, keys)

    sns.set_theme(style="dark")
    fig = plt.figure(figsize=(5.4, 4.2), dpi=140)
    ax = fig.add_subplot(111)
    sns.heatmap(
        matrix,
        annot=True,
        fmt=".2f",
        cmap="viridis",
        xticklabels=labels,
        yticklabels=labels,
        ax=ax,
    )
    ax.set_title("Berth Occupancy Correlation", pad=12)
    buf = io.BytesIO()
    fig.tight_layout()
    fig.savefig(buf, format="png", bbox_inches="tight", facecolor=fig.get_facecolor())
    plt.close(fig)
    return "data:image/png;base64," + base64.b64encode(buf.getvalue()).decode("utf-8")


def fig_congestion_heatmap(rows):
    if not rows:
        fig = go.Figure()
        fig.add_annotation(text="No congestion data available.", x=0.5, y=0.5, xref="paper", yref="paper", showarrow=False)
        fig.update_layout(template="plotly_dark", height=360, margin=dict(l=10, r=10, t=30, b=30))
        return fig

    zones = sorted({row.get("zone") for row in rows if row.get("zone")})
    windows = sorted({row.get("hour_window") for row in rows if row.get("hour_window")})
    grid = [[0 for _ in zones] for _ in windows]
    lookup = {(row.get("hour_window"), row.get("zone")): safe_float(row.get("congestion_score", 0)) for row in rows}
    for window_index, window in enumerate(windows):
        for zone_index, zone in enumerate(zones):
            grid[window_index][zone_index] = lookup.get((window, zone), 0)
    fig = go.Figure(go.Heatmap(z=grid, x=zones, y=windows, colorscale="Viridis"))
    fig.update_layout(
        template="plotly_dark",
        height=360,
        margin=dict(l=10, r=10, t=45, b=30),
        title="Congestion Score by Zone & Time Window",
        xaxis_title="Zone",
        yaxis_title="Time Window",
    )
    return fig



def normalise_congestion_heatmap(rows):
    normalised = []
    for row in rows or []:
        hour_window = row.get("hour_window") or row.get("time_window") or ""
        zone = row.get("zone") or row.get("severity_band") or row.get("severity") or "Activity"
        congestion_score = row.get("congestion_score")
        if congestion_score is None:
            congestion_score = row.get("incident_count", 0)
        normalised.append(
            {
                "hour_window": hour_window,
                "zone": zone,
                "congestion_score": safe_float(congestion_score),
            }
        )
    return normalised


def normalise_map_overlays(map_overlays):
    map_overlays = map_overlays or {}
    raw_berths = map_overlays.get("berths") or map_overlays.get("berth_layout") or []
    berth_positions = {}
    berths = []
    for index, row in enumerate(raw_berths):
        x = row.get("x", index)
        y = row.get("y", 0)
        normalised = {**row, "x": x, "y": y}
        berths.append(normalised)
        if row.get("id"):
            berth_positions[row["id"]] = (x, y)

    def fill_positions(rows, overlay_key):
        normalised_rows = []
        for index, row in enumerate(rows or []):
            row_x = row.get("x")
            row_y = row.get("y")
            if row_x is None or row_y is None:
                location_id = row.get("location_id")
                if location_id in berth_positions:
                    row_x, row_y = berth_positions[location_id]
                else:
                    row_x = index
                    row_y = 0 if overlay_key == "shipping_lanes" else index % 3
            normalised_rows.append({**row, "x": row_x, "y": row_y})
        return normalised_rows

    return {
        "berths": berths,
        "shipping_lanes": fill_positions(map_overlays.get("shipping_lanes"), "shipping_lanes"),
        "restricted_zones": fill_positions(map_overlays.get("restricted_zones"), "restricted_zones"),
    }


def fig_map_overlay(map_overlays, overlay_key):
    overlay = (map_overlays or {}).get(overlay_key) or []
    if not overlay:
        fig = go.Figure()
        fig.add_annotation(text="No overlay data available.", x=0.5, y=0.5, xref="paper", yref="paper", showarrow=False)
        fig.update_layout(template="plotly_dark", height=360, margin=dict(l=10, r=10, t=30, b=10), xaxis=dict(visible=False), yaxis=dict(visible=False))
        return fig

    if overlay_key == "shipping_lanes":
        fig = go.Figure()
        lane_rows = max(3, min(6, math.ceil(len(overlay) / 4)))
        lane_spacing = 1.2
        for index, row in enumerate(overlay):
            status = str(row.get("status", "")).strip().title()
            if status in {"Active", "Open"}:
                color = "#22c55e"
            elif status in {"Under Maintenance", "Unavailable", "Delayed"}:
                color = "#f59e0b"
            else:
                color = "#ef4444"

            lane_y = (index % lane_rows) * lane_spacing
            lane_group = index // lane_rows
            start_x = lane_group * 3.8
            end_x = start_x + 2.8
            label = row.get("label", row.get("id", "Shipping Lane"))

            fig.add_trace(
                go.Scatter(
                    x=[start_x, end_x],
                    y=[lane_y, lane_y],
                    mode="lines+markers",
                    line=dict(color=color, width=6),
                    marker=dict(size=8, color=color),
                    text=[label, label],
                    customdata=[status, status],
                    hovertemplate="<b>%{text}</b><br>Status: %{customdata}<extra></extra>",
                    showlegend=False,
                )
            )

        max_y = (lane_rows - 1) * lane_spacing
        max_x = max(3.8, ((len(overlay) - 1) // lane_rows) * 3.8 + 2.8)
        fig.update_layout(
            template="plotly_dark",
            height=360,
            margin=dict(l=30, r=30, t=30, b=20),
            xaxis=dict(visible=False, range=[-0.8, max_x + 0.8]),
            yaxis=dict(visible=False, range=[-0.8, max_y + 0.8]),
        )
        return fig

    xs = [row.get("x", 0) for row in overlay]
    ys = [row.get("y", 0) for row in overlay]
    labels = [row.get("label", row.get("name", row.get("id", ""))) for row in overlay]
    colors = []
    for row in overlay:
        status = str(row.get("status", "")).strip().title()
        if status in {"Active", "Open"}:
            colors.append("#22c55e")
        elif status in {"Under Maintenance", "Unavailable", "Delayed"}:
            colors.append("#f59e0b")
        else:
            colors.append("#ef4444")

    min_x, max_x = min(xs), max(xs)
    min_y, max_y = min(ys), max(ys)
    padding_x = max(1.2, (max_x - min_x) * 0.3 if max_x != min_x else 1.4)
    padding_y = max(1.0, (max_y - min_y) * 0.3 if max_y != min_y else 1.2)

    fig = go.Figure(
        go.Scatter(
            x=xs,
            y=ys,
            mode="markers",
            marker=dict(size=14, color=colors, line=dict(color="rgba(255,255,255,0.3)", width=1.5)),
            text=labels,
            customdata=[str(row.get("status", "")).strip().title() for row in overlay],
            hovertemplate="<b>%{text}</b><br>Status: %{customdata}<extra></extra>",
            cliponaxis=False,
        )
    )
    fig.update_layout(
        template="plotly_dark",
        height=360,
        margin=dict(l=30, r=30, t=30, b=20),
        xaxis=dict(visible=False, range=[min_x - padding_x, max_x + padding_x]),
        yaxis=dict(visible=False, range=[min_y - padding_y, max_y + padding_y]),
    )
    return fig


def normalise_management_snapshot(snapshot):
    snapshot = dict(snapshot or {})
    snapshot["congestion_heatmap"] = normalise_congestion_heatmap(snapshot.get("congestion_heatmap", []))
    snapshot["map_overlays"] = normalise_map_overlays(snapshot.get("map_overlays", {}))
    return snapshot
