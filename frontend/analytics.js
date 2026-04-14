const analyticsSummaryCards = document.getElementById("analyticsSummaryCards");
const analyticsBerthChart = document.getElementById("analyticsBerthChart");
const analyticsRouteChart = document.getElementById("analyticsRouteChart");
const analyticsCongestionGauge = document.getElementById("analyticsCongestionGauge");
const analyticsCongestionText = document.getElementById("analyticsCongestionText");
const analyticsEnvironmentCards = document.getElementById("analyticsEnvironmentCards");
const analyticsBerthTable = document.getElementById("analyticsBerthTable");
const analyticsRouteTable = document.getElementById("analyticsRouteTable");
const analyticsCongestionTable = document.getElementById("analyticsCongestionTable");
const analyticsEquipmentTable = document.getElementById("analyticsEquipmentTable");
const sessionBadge = document.getElementById("sessionBadge");
const logoutButton = document.getElementById("logoutButton");
const API_TIMEOUT_MS = 10000;
let analyticsData = null;

function setSessionBadge(user) {
    if (!sessionBadge) {
        return;
    }
    sessionBadge.className = "dashboard-chip admin-topbar-control";
    sessionBadge.textContent = user.name;
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
    const headers = Object.keys(rows[0]);
    return `
        <table class="dashboard-table ${compact ? "compact" : ""}">
            <thead><tr>${headers.map((header) => `<th>${formatHeaderLabel(header)}</th>`).join("")}</tr></thead>
            <tbody>
            ${rows
                .map(
                    (row) =>
                        `<tr>${headers.map((header) => `<td>${row[header]}</td>`).join("")}</tr>`,
                )
                .join("")}
            </tbody>
        </table>
    `;
}

function renderSummary(summary = {}) {
    const cards = [
        { label: "Most Used Berth", value: summary.most_used_berth || "No data", meta: "Top allocation target", accent: "green" },
        { label: "Busiest Route", value: summary.busiest_route || "No data", meta: "Highest route demand", accent: "blue" },
        { label: "Peak Congestion", value: summary.peak_congestion_hour || "No data", meta: "Current hotspot window", accent: "red" },
        { label: "Highest Wind Zone", value: summary.highest_wind_zone || "No data", meta: "Most exposed environmental area", accent: "amber" },
    ];
    analyticsSummaryCards.innerHTML = cards
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

function renderBerthChart(rows) {
    analyticsBerthChart.innerHTML = rows.length
        ? rows.slice(0, 6).map((row) => `
            <div class="dashboard-bar-item">
                <div class="dashboard-bar-track">
                    <div class="dashboard-bar-fill" style="height:${Math.max(15, Number(row.allocation_count || 0) * 18)}%"></div>
                </div>
                <div class="dashboard-bar-value">${row.allocation_count}</div>
                <div class="dashboard-bar-label">${row.berth_name || row.berth_id}</div>
            </div>
        `).join("")
        : "<div class='dashboard-empty'>No berth usage data.</div>";
}

function renderRouteChart(rows) {
    if (!rows.length) {
        analyticsRouteChart.innerHTML = "<div class='dashboard-empty'>No route usage data.</div>";
        return;
    }
    const values = rows.slice(0, 6).map((row) => Number(row.usage_count || 0));
    const max = Math.max(...values, 1);
    const width = 320;
    const height = 120;
    const step = width / Math.max(values.length - 1, 1);
    const polyline = values.map((value, index) => {
        const x = index * step;
        const y = height - (value / max) * (height - 18) - 6;
        return `${x},${y}`;
    }).join(" ");
    analyticsRouteChart.innerHTML = `
        <svg viewBox="0 0 ${width} ${height}" class="dashboard-line-svg" preserveAspectRatio="none">
            <polyline points="${polyline}" class="dashboard-line-path"></polyline>
        </svg>
        <div class="dashboard-line-labels">
            ${rows.slice(0, 6).map((row) => `<span>${row.route_id}</span>`).join("")}
        </div>
    `;
}

function renderCongestionGauge(rows) {
    const topRow = rows[0];
    const percentage = Math.max(12, Math.min(95, Number(topRow?.incident_count || 0) * 7));
    analyticsCongestionGauge.style.background = `conic-gradient(#ff9f43 0deg, #ff9f43 ${percentage * 3.6}deg, rgba(255,255,255,0.08) ${percentage * 3.6}deg 360deg)`;
    analyticsCongestionText.innerHTML = `${percentage}%<span>${topRow?.hour_window || "Normal"}</span>`;
}

function renderEnvironmentCards(rows) {
    if (!rows.length) {
        analyticsEnvironmentCards.innerHTML = "<div class='dashboard-empty'>No environmental trend data.</div>";
        return;
    }
    const top = rows[0];
    const cards = [
        { label: "Wind", value: `${top.average_wind_knots || 0} kn` },
        { label: "Tide", value: `${top.average_tide_m || 0} m` },
        { label: "Visibility", value: `${top.average_visibility_km || 0} km` },
    ];
    analyticsEnvironmentCards.innerHTML = cards.map((card) => `
        <article class="dashboard-weather-card">
            <div class="dashboard-weather-value">${card.value}</div>
            <div class="dashboard-weather-label">${card.label}</div>
        </article>
    `).join("");
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

function getErrorMessage(error, timeoutMessage) {
    return error.name === "AbortError" ? timeoutMessage : error.message || "Request failed.";
}

async function loadAnalytics() {
    try {
        const data = await apiRequest("/api/analytics", { method: "GET" });
        analyticsData = data;
        renderSummary(data.summary || {});
        renderBerthChart(data.most_used_berths || []);
        renderRouteChart(data.common_routes || []);
        renderCongestionGauge(data.peak_congestion_times || []);
        renderEnvironmentCards(data.environmental_trends || []);
        analyticsBerthTable.innerHTML = renderTableMarkup(data.most_used_berths || [], true);
        analyticsRouteTable.innerHTML = renderTableMarkup(data.common_routes || [], true);
        analyticsCongestionTable.innerHTML = renderTableMarkup(data.peak_congestion_times || [], true);
        analyticsEquipmentTable.innerHTML = renderTableMarkup(data.equipment_utilisation || [], true);
    } catch (error) {
        analyticsSummaryCards.innerHTML = `<div class="dashboard-empty">${getErrorMessage(error, "Analytics request timed out.")}</div>`;
    }
}
if (logoutButton) {
    logoutButton.addEventListener("click", logout);
}
loadSession();
loadAnalytics();
