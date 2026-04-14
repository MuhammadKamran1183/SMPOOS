const monitoringSummaryCards = document.getElementById("monitoringSummaryCards");
const monitoringLegend = document.getElementById("monitoringLegend");
const monitoringMapCanvas = document.getElementById("monitoringMapCanvas");
const monitoringAlertsList = document.getElementById("monitoringAlertsList");
const monitoringBerthChart = document.getElementById("monitoringBerthChart");
const monitoringVesselChart = document.getElementById("monitoringVesselChart");
const monitoringHealthGauge = document.getElementById("monitoringHealthGauge");
const monitoringHealthText = document.getElementById("monitoringHealthText");
const monitoringWeatherCards = document.getElementById("monitoringWeatherCards");
const monitoringVesselsTable = document.getElementById("monitoringVesselsTable");
const monitoringCargoTable = document.getElementById("monitoringCargoTable");
const monitoringSystemHealthTable = document.getElementById("monitoringSystemHealthTable");
const monitoringEventLogsTable = document.getElementById("monitoringEventLogsTable");
const sessionBadge = document.getElementById("sessionBadge");
const logoutButton = document.getElementById("logoutButton");
const API_TIMEOUT_MS = 10000;
let monitoringData = null;

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

function setSessionBadge(user) {
    if (!sessionBadge) {
        return;
    }
    sessionBadge.className = "dashboard-chip admin-topbar-control";
    sessionBadge.textContent = user.name;
}

async function loadSession() {
    try {
        const data = await apiRequest("/api/session", { method: "GET" });
        if (!data.user) {
            window.location.href = "/login";
            return;
        }
        setSessionBadge(data.user);
    } catch (error) {
        window.location.href = "/login";
    }
}

function renderTableMarkup(rows, compact = false) {
    if (!rows.length) {
        return "<div class='dashboard-empty'>No data available.</div>";
    }

    const formatHeaderLabel = (header) => header
        .split("_")
        .filter(Boolean)
        .map((word) => word.charAt(0).toUpperCase() + word.slice(1))
        .join(" ");
    const isDateLikeHeader = (header) => [
        "last_updated",
        "estimated_arrival",
        "estimated_departure",
        "created_at",
        "requested_at",
        "resolved_at",
        "scanned_at",
        "applied_at",
        "eta",
        "etd",
    ].includes(header);
    const formatCellValue = (header, value) => {
        if (!isDateLikeHeader(header)) {
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
            <thead>
                <tr>${headers.map((header) => `<th>${formatHeaderLabel(header)}</th>`).join("")}</tr>
            </thead>
            <tbody>
                ${rows
                    .map((row) => {
                        const cells = headers
                            .map((header) => `<td>${formatCellValue(header, row[header])}</td>`)
                            .join("");
                        return `<tr>${cells}</tr>`;
                    })
                    .join("")}
            </tbody>
        </table>
    `;
}

function renderSummary(data) {
    const vesselCount = (data.vessel_movements || []).length;
    const occupiedBerths = (data.berth_occupancy || []).filter(
        (row) => Number(row.occupancy_percent || 0) > 0,
    ).length;
    const activeAlerts = (data.alerts || []).length;
    const unhealthySystems = (data.system_health || []).filter(
        (row) => !String(row.status || "").toLowerCase().includes("healthy"),
    ).length;
    const cards = [
        {
            label: "Live Vessels",
            value: vesselCount,
            meta: "Tracked movements",
            accent: "blue",
        },
        {
            label: "Occupied Berths",
            value: occupiedBerths,
            meta: `${(data.berth_occupancy || []).length} total monitored`,
            accent: "green",
        },
        {
            label: "Alerts",
            value: activeAlerts,
            meta: "Current notifications",
            accent: "red",
        },
        {
            label: "System Health",
            value: unhealthySystems ? "Watch" : "Healthy",
            meta: unhealthySystems ? `${unhealthySystems} issue(s)` : "All core checks healthy",
            accent: unhealthySystems ? "amber" : "green",
        },
    ];
    monitoringSummaryCards.innerHTML = cards
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

function renderLegend() {
    monitoringLegend.innerHTML = [
        { label: "Vessels", color: "cyan" },
        { label: "Occupied Berths", color: "green" },
        { label: "Alerts", color: "red" },
    ]
        .map(
            (item) => `
                <span class="dashboard-legend-item">
                    <span class="dashboard-legend-dot ${item.color}"></span>
                    ${item.label}
                </span>
            `,
        )
        .join("");
}

function renderMap(data) {
    const vessels = data.vessel_movements || [];
    const berths = data.berth_occupancy || [];
    monitoringMapCanvas.innerHTML = `
        <div class="monitoring-map-layout">
            <div class="monitoring-map-vessel-grid">
                ${vessels.slice(0, 6).map(
                    (item) => `
                        <div class="dashboard-map-node online monitoring-map-vessel-node">
                            <span>${item.vessel_name || item.asset_name || "Vessel"}</span>
                        </div>
                    `,
                ).join("")}
            </div>
            <div class="monitoring-map-berth-stack">
                ${berths.slice(0, 6).map(
                    (item) => `
                        <div class="dashboard-map-hazard medium monitoring-map-berth-pill">
                            ${item.berth_name || item.berth_id}
                        </div>
                    `,
                ).join("")}
            </div>
        </div>
    `;
}

function renderAlerts(alerts) {
    if (!alerts.length) {
        monitoringAlertsList.innerHTML = "<div class='dashboard-empty'>No alerts available.</div>";
        return;
    }
    monitoringAlertsList.innerHTML = alerts
        .slice(0, 4)
        .map(
            (alert) => `
                <article class="dashboard-alert-item ${String(alert.severity).toLowerCase()}">
                    <div class="dashboard-alert-severity">${alert.severity}</div>
                    <div class="dashboard-alert-content">
                        <h3>${alert.alert_type || "Alert"}</h3>
                        <p>${alert.message || ""}</p>
                    </div>
                    <time>${String(alert.timestamp || "").slice(11, 16)}</time>
                </article>
            `,
        )
        .join("");
}

function renderBerthChart(rows) {
    if (!rows.length) {
        monitoringBerthChart.innerHTML = "<div class='dashboard-empty'>No berth occupancy data.</div>";
        return;
    }
    monitoringBerthChart.innerHTML = rows
        .slice(0, 6)
        .map(
            (row) => `
                <div class="dashboard-bar-item">
                    <div class="dashboard-bar-track">
                        <div class="dashboard-bar-fill" style="height:${Math.max(10, Number(row.occupancy_percent || 0))}%"></div>
                    </div>
                    <div class="dashboard-bar-value">${row.occupancy_percent || 0}%</div>
                    <div class="dashboard-bar-label">${row.berth_name || row.berth_id}</div>
                </div>
            `,
        )
        .join("");
}

function renderVesselChart(rows) {
    if (!rows.length) {
        monitoringVesselChart.innerHTML = "<div class='dashboard-empty'>No vessel movement data.</div>";
        return;
    }
    const values = rows.slice(0, 6).map((_, index) => 18 + index * 8 + (index % 2 ? 6 : 0));
    const max = Math.max(...values, 1);
    const width = 320;
    const height = 120;
    const step = width / Math.max(values.length - 1, 1);
    const polyline = values
        .map((value, index) => {
            const x = index * step;
            const y = height - (value / max) * (height - 18) - 6;
            return `${x},${y}`;
        })
        .join(" ");
    monitoringVesselChart.innerHTML = `
        <svg viewBox="0 0 ${width} ${height}" class="dashboard-line-svg" preserveAspectRatio="none">
            <polyline points="${polyline}" class="dashboard-line-path"></polyline>
        </svg>
        <div class="dashboard-line-labels">
            ${rows.slice(0, 6).map((row) => `<span>${(row.vessel_name || "Vessel").split(" ")[0]}</span>`).join("")}
        </div>
    `;
}

function renderHealthGauge(rows) {
    const healthyCount = rows.filter((row) => String(row.status || "").toLowerCase().includes("healthy")).length;
    const percentage = rows.length ? Math.round((healthyCount / rows.length) * 100) : 0;
    monitoringHealthGauge.style.background = `conic-gradient(#22c55e 0deg, #22c55e ${percentage * 3.6}deg, rgba(255,255,255,0.08) ${percentage * 3.6}deg 360deg)`;
    monitoringHealthText.innerHTML = `${percentage}%<span>${healthyCount === rows.length ? "Healthy" : "Watch"}</span>`;
}

function renderWeather(rows) {
    if (!rows.length) {
        monitoringWeatherCards.innerHTML = "<div class='dashboard-empty'>No environmental data.</div>";
        return;
    }
    const latest = rows[0];
    const cards = [
        { label: "Wind", value: `${latest.wind_speed_knots || 0} kn` },
        { label: "Tide", value: `${latest.tide_level_m || 0} m` },
        { label: "Visibility", value: `${latest.visibility_km || 0} km` },
    ];
    monitoringWeatherCards.innerHTML = cards
        .map(
            (card) => `
                <article class="dashboard-weather-card">
                    <div class="dashboard-weather-value">${card.value}</div>
                    <div class="dashboard-weather-label">${card.label}</div>
                </article>
            `,
        )
        .join("");
}

async function loadMonitoring() {
    try {
        const data = await apiRequest("/api/monitoring", { method: "GET" });
        monitoringData = data;
        renderSummary(data);
        renderLegend();
        renderMap(data);
        renderAlerts(data.alerts || []);
        renderBerthChart(data.berth_occupancy || []);
        renderVesselChart(data.vessel_movements || []);
        renderHealthGauge(data.system_health || []);
        renderWeather(data.environmental_updates || []);
        monitoringVesselsTable.innerHTML = renderTableMarkup(data.vessel_movements || [], true);
        monitoringCargoTable.innerHTML = renderTableMarkup(data.cargo_activity || [], true);
        monitoringSystemHealthTable.innerHTML = renderTableMarkup(data.system_health || [], true);
        monitoringEventLogsTable.innerHTML = renderTableMarkup(data.event_logs || [], true);
    } catch (error) {
        const message = error.name === "AbortError"
            ? "Monitoring request timed out. Please refresh."
            : error.message;
        monitoringSummaryCards.innerHTML = `<div class="dashboard-empty">${message}</div>`;
    }
}
loadSession();
loadMonitoring();

if (logoutButton) {
    logoutButton.addEventListener("click", logout);
}
