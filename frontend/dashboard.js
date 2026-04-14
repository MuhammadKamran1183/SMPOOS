const dashboardSummaryCards = document.getElementById("dashboardSummaryCards");
const dashboardMapLegend = document.getElementById("dashboardMapLegend");
const dashboardMapCanvas = document.getElementById("dashboardMapCanvas");
const dashboardAlertsList = document.getElementById("dashboardAlertsList");
const dashboardBerthChart = document.getElementById("dashboardBerthChart");
const dashboardQueueChart = document.getElementById("dashboardQueueChart");
const dashboardCongestionGauge = document.getElementById("dashboardCongestionGauge");
const dashboardCongestionText = document.getElementById("dashboardCongestionText");
const dashboardWeatherOverview = document.getElementById("dashboardWeatherOverview");
const dashboardActivityTable = document.getElementById("dashboardActivityTable");
const sessionBadge = document.getElementById("sessionBadge");
const logoutButton = document.getElementById("logoutButton");
const API_TIMEOUT_MS = 10000;
let dashboardData = null;
let activeOverlay = "berth_layout";

function renderTableMarkup(rows, compact = false) {
    if (!rows.length) {
        return "<div class='dashboard-empty'>No data available.</div>";
    }
    const formatHeaderLabel = (header) => header
        .split("_")
        .filter(Boolean)
        .map((word) => word.charAt(0).toUpperCase() + word.slice(1))
        .join(" ");
    const formatCellValue = (header, value) => {
        if (header !== "last_updated") {
            return value ?? "";
        }
        const parsedDate = new Date(value);
        if (Number.isNaN(parsedDate.getTime())) {
            return value ?? "";
        }
        return parsedDate.toLocaleString("en-GB", {
            day: "2-digit",
            month: "short",
            year: "numeric",
            hour: "2-digit",
            minute: "2-digit",
        });
    };
    const headers = Object.keys(rows[0]);
    return `
        <table class="dashboard-table ${compact ? "compact" : ""}">
            <thead><tr>${headers.map((header) => `<th>${formatHeaderLabel(header)}</th>`).join("")}</tr></thead>
            <tbody>
            ${rows
                .map((row) => `<tr>${headers.map((header) => `<td>${formatCellValue(header, row[header])}</td>`).join("")}</tr>`)
                .join("")}
            </tbody>
        </table>
    `;
}

function renderSummary(overview = {}) {
    const berthLayout = dashboardData?.map_overlays?.berth_layout || [];
    const occupied = overview.occupied_berths || 0;
    const totalBerths = berthLayout.length || occupied || 1;
    const alerts = dashboardData?.alerts_panel || [];
    const highSeverityAlerts = alerts.filter((alert) => String(alert.severity).toLowerCase() === "high").length;
    const vesselCount = dashboardData?.vessel_vehicle_activity?.filter(
        (item) => item.activity_type === "Vessel",
    ).length || 0;
    const queuePoints = dashboardData?.congestion_heatmap || [];
    const avgTurnaround = queuePoints.length
        ? (
              queuePoints.reduce((total, point) => total + Number(point.incident_count || 0), 0) /
              queuePoints.length +
              6
          ).toFixed(1)
        : "0.0";
    const cards = [
        {
            label: "Active Berths",
            value: `${occupied} / ${totalBerths}`,
            meta: `${Math.round((occupied / totalBerths) * 100)}% Occupancy`,
            accent: "green",
        },
        {
            label: "Vessels In Port",
            value: vesselCount,
            meta: `Queue ${overview.vessel_queue || 0}`,
            accent: "blue",
        },
        {
            label: "Alerts",
            value: alerts.length,
            meta: `${highSeverityAlerts} high severity`,
            accent: "red",
        },
        {
            label: "Avg. Turnaround",
            value: `${avgTurnaround} hrs`,
            meta: "Live rolling estimate",
            accent: "green",
        },
        {
            label: "Weather",
            value: `${overview.average_wind_knots || 0} kn`,
            meta: `${overview.environmental_alert_zones || 0} alert zones`,
            accent: "amber",
        },
    ];
    dashboardSummaryCards.innerHTML = cards
        .map(
            (card) => `
                <article class="dashboard-kpi-card ${card.accent}">
                    <div class="dashboard-kpi-label">${card.label}</div>
                    <div class="dashboard-kpi-value">${card.value}</div>
                    <div class="dashboard-kpi-meta">${card.meta}</div>
                </article>
            `,
        )
        .join("");
}

function setSessionBadge(user) {
    if (!sessionBadge) {
        return;
    }
    sessionBadge.className = "dashboard-chip admin-topbar-control";
    sessionBadge.textContent = user.name;
}

function getOverlayColumnCount(itemCount, maxColumns) {
    if (itemCount <= 1) {
        return 1;
    }
    return Math.max(1, Math.min(maxColumns, Math.ceil(Math.sqrt(itemCount))));
}

function renderOverlay() {
    const overlayRows = (dashboardData?.map_overlays || {})[activeOverlay] || [];
    const legend = {
        berth_layout: [
            { label: "Berths", color: "cyan" },
            { label: "Occupancy", color: "green" },
        ],
        shipping_lanes: [
            { label: "Routes", color: "blue" },
            { label: "Traffic Flow", color: "cyan" },
        ],
        restricted_zones: [
            { label: "Restricted Zones", color: "red" },
            { label: "Hazards", color: "amber" },
        ],
    };
    dashboardMapLegend.innerHTML = (legend[activeOverlay] || [])
        .map(
            (item) => `
                <span class="dashboard-legend-item">
                    <span class="dashboard-legend-dot ${item.color}"></span>
                    ${item.label}
                </span>
            `,
        )
        .join("");

    if (!overlayRows.length) {
        dashboardMapCanvas.innerHTML = "<div class='dashboard-empty'>No overlay data available.</div>";
        return;
    }

    if (activeOverlay === "berth_layout") {
        const columnCount = getOverlayColumnCount(overlayRows.length, 4);
        dashboardMapCanvas.innerHTML = `
            <div class="dashboard-map-grid dashboard-map-grid-berths" style="--dashboard-grid-columns:${columnCount}">
                ${overlayRows
                    .map(
                        (item) => `
                            <div class="dashboard-map-node-wrap">
                                <div class="dashboard-map-node ${String(item.status).toLowerCase().includes("active") ? "online" : "warning"}">
                                    <span>${item.label}</span>
                                </div>
                            </div>
                        `,
                    )
                    .join("")}
            </div>
        `;
        return;
    }

    if (activeOverlay === "shipping_lanes") {
        dashboardMapCanvas.innerHTML = `
            <div class="dashboard-map-stack">
                ${overlayRows
                    .slice(0, 8)
                    .map(
                        (item) => `
                            <div class="dashboard-map-lane ${String(item.status).toLowerCase().includes("open") ? "open" : "warning"}">
                                <span>${item.label}</span>
                            </div>
                        `,
                    )
                    .join("")}
            </div>
        `;
        return;
    }

    const columnCount = getOverlayColumnCount(overlayRows.length, 3);
    dashboardMapCanvas.innerHTML = `
        <div class="dashboard-map-grid dashboard-map-grid-hazards" style="--dashboard-grid-columns:${columnCount}">
            ${overlayRows
                .map(
                    (item) => `
                        <div class="dashboard-map-hazard ${String(item.severity).toLowerCase() === "high" ? "high" : "medium"}">
                            ${item.label}
                        </div>
                    `,
                )
                .join("")}
        </div>
    `;
}

function renderAlerts(alerts = []) {
    if (!alerts.length) {
        dashboardAlertsList.innerHTML = "<div class='dashboard-empty'>No alerts available.</div>";
        return;
    }
    dashboardAlertsList.innerHTML = alerts
        .slice(0, 5)
        .map(
            (alert) => `
                <article class="dashboard-alert-item ${String(alert.severity).toLowerCase()}">
                    <div class="dashboard-alert-severity">${alert.severity}</div>
                    <div class="dashboard-alert-content">
                        <h3>${alert.alert_type}</h3>
                        <p>${alert.message}</p>
                    </div>
                    <time>${String(alert.timestamp).slice(11, 16)}</time>
                </article>
            `,
        )
        .join("");
}

function renderBerthChart() {
    const berths = dashboardData?.map_overlays?.berth_layout || [];
    if (!berths.length) {
        dashboardBerthChart.innerHTML = "<div class='dashboard-empty'>No berth layout data.</div>";
        return;
    }
    dashboardBerthChart.innerHTML = berths
        .slice(0, 6)
        .map((berth, index) => {
            const base = 45 + (index % 4) * 12;
            const modifier = String(berth.status).toLowerCase().includes("active") ? 18 : -8;
            const value = Math.max(20, Math.min(95, base + modifier));
            return `
                <div class="dashboard-bar-item">
                    <div class="dashboard-bar-track">
                        <div class="dashboard-bar-fill" style="height:${value}%"></div>
                    </div>
                    <div class="dashboard-bar-value">${value}%</div>
                    <div class="dashboard-bar-label">${berth.label.split(" ")[1] || berth.label}</div>
                </div>
            `;
        })
        .join("");
}

function renderQueueChart() {
    const points = dashboardData?.congestion_heatmap || [];
    if (!points.length) {
        dashboardQueueChart.innerHTML = "<div class='dashboard-empty'>No queue data.</div>";
        return;
    }
    const values = points.slice(0, 6).map((point) => Number(point.incident_count || 0));
    const max = Math.max(...values, 1);
    const min = Math.min(...values);
    const range = Math.max(max - min, 1);
    const width = 320;
    const height = 120;
    const centeredPlotHeight = 44;
    const plotTop = (height - centeredPlotHeight) / 2;
    const step = width / Math.max(values.length - 1, 1);
    const polyline = values
        .map((value, index) => {
            const x = index * step;
            const y = range === 0
                ? height / 2
                : plotTop + ((max - value) / range) * centeredPlotHeight;
            return `${x},${y}`;
        })
        .join(" ");
    const labels = points.slice(0, 6).map((point) => point.time_window.slice(0, 5));
    dashboardQueueChart.innerHTML = `
        <svg viewBox="0 0 ${width} ${height}" class="dashboard-line-svg" preserveAspectRatio="none">
            <polyline points="${polyline}" class="dashboard-line-path"></polyline>
        </svg>
        <div class="dashboard-line-labels">
            ${labels.map((label) => `<span>${label}</span>`).join("")}
        </div>
    `;
}

function renderCongestionGauge() {
    const topBand = dashboardData?.congestion_heatmap?.[0];
    const percentage = Math.max(18, Math.min(95, Number(topBand?.incident_count || 0) * 6));
    dashboardCongestionGauge.style.background = `conic-gradient(#ff9f43 0deg, #ff9f43 ${percentage * 3.6}deg, rgba(255,255,255,0.08) ${percentage * 3.6}deg 360deg)`;
    dashboardCongestionText.innerHTML = `${percentage}%<span>${topBand?.severity_band || "Normal"}</span>`;
}

function renderWeatherOverview(overview = {}) {
    const cards = [
        { label: "Wind", value: `${overview.average_wind_knots || 0} kn` },
        { label: "Queue", value: `${overview.vessel_queue || 0}` },
        { label: "Alert Zones", value: `${overview.environmental_alert_zones || 0}` },
    ];
    dashboardWeatherOverview.innerHTML = cards
        .map(
            (card) => `
                <article class="dashboard-weather-card">
                    <div class="dashboard-weather-label">${card.label}</div>
                    <div class="dashboard-weather-value">${card.value}</div>
                </article>
            `,
        )
        .join("");
}

function renderActivityTable(rows = []) {
    dashboardActivityTable.innerHTML = renderTableMarkup(rows.slice(0, 8), true);
}

function renderDashboardError(message) {
    dashboardData = null;
    dashboardSummaryCards.innerHTML = `<div class="dashboard-empty">${message}</div>`;
    dashboardMapLegend.innerHTML = "";
    dashboardMapCanvas.innerHTML = `<div class="dashboard-empty">${message}</div>`;
    dashboardAlertsList.innerHTML = `<div class="dashboard-empty">${message}</div>`;
    dashboardBerthChart.innerHTML = `<div class="dashboard-empty">${message}</div>`;
    dashboardQueueChart.innerHTML = `<div class="dashboard-empty">${message}</div>`;
    dashboardCongestionGauge.style.background = "rgba(255,255,255,0.08)";
    dashboardCongestionText.innerHTML = "0%<span>Unavailable</span>";
    dashboardWeatherOverview.innerHTML = `<div class="dashboard-empty">${message}</div>`;
    dashboardActivityTable.innerHTML = `<div class="dashboard-empty">${message}</div>`;
}

async function apiRequest(path, options = {}) {
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), API_TIMEOUT_MS);
    try {
        const response = await fetch(path, {
            cache: "no-store",
            credentials: "same-origin",
            ...options,
            signal: controller.signal,
            headers: {
                "Content-Type": "application/json",
                ...(options.headers || {}),
            },
        });
        const data = await response.json().catch(() => ({}));
        if (response.status === 401) {
            window.location.href = "/login";
            throw new Error("Login required.");
        }
        if (!response.ok) {
            throw new Error(data.error || "Request failed.");
        }
        return data;
    } finally {
        clearTimeout(timeoutId);
    }
}

async function logout() {
    try {
        await apiRequest("/api/logout", {
            method: "POST",
            body: JSON.stringify({}),
        });
    } finally {
        window.location.href = "/login";
    }
}

async function loadSession() {
    try {
        const data = await apiRequest("/api/session");
        if (!data.user) {
            window.location.href = "/login";
            return;
        }
        setSessionBadge(data.user);
    } catch (error) {
        window.location.href = "/login";
    }
}

function getErrorMessage(error, timeoutMessage) {
    return error.name === "AbortError" ? timeoutMessage : error.message || "Request failed.";
}

async function loadDashboard() {
    try {
        dashboardData = await apiRequest("/api/dashboard-management");
        renderSummary(dashboardData.port_status_overview || {});
        renderOverlay();
        renderAlerts(dashboardData.alerts_panel || []);
        renderBerthChart();
        renderQueueChart();
        renderCongestionGauge();
        renderWeatherOverview(dashboardData.port_status_overview || {});
        renderActivityTable(dashboardData.vessel_vehicle_activity || []);
    } catch (error) {
        renderDashboardError(getErrorMessage(error, "Dashboard request timed out."));
    }
}

document.querySelectorAll(".overlay-toggle").forEach((button) => {
    button.addEventListener("click", () => {
        activeOverlay = button.dataset.overlay;
        document.querySelectorAll(".overlay-toggle").forEach((item) => item.classList.remove("active"));
        button.classList.add("active");
        renderOverlay();
    });
});

if (logoutButton) {
    logoutButton.addEventListener("click", logout);
}
loadSession();
loadDashboard();
