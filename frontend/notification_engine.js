const rulesTableShell = document.getElementById("rulesTableShell");
const deliveriesTableShell = document.getElementById("deliveriesTableShell");
const notificationRecordsTableShell = document.getElementById("notificationRecordsTableShell");
const notificationEventLogsTableShell = document.getElementById("notificationEventLogsTableShell");
const sessionBadge = document.getElementById("sessionBadge");
const logoutButton = document.getElementById("logoutButton");
const API_TIMEOUT_MS = 10000;

function setMessage(message, type = "secondary") {
    void message;
    void type;
}

function setSessionBadge(user) {
    if (!sessionBadge) {
        return;
    }
    sessionBadge.className = "dashboard-chip admin-topbar-control";
    sessionBadge.textContent = user.name;
}

function normalisePrefixedId(value, prefix) {
    const trimmedValue = String(value || "").trim();
    if (!trimmedValue) {
        return "";
    }
    if (/^\d+$/.test(trimmedValue)) {
        return `${prefix}${trimmedValue.padStart(4, "0")}`;
    }
    return trimmedValue.toUpperCase();
}

function getValue(id) {
    return document.getElementById(id).value.trim();
}

function resetForm(formId) {
    document.getElementById(formId).reset();
}

function renderTableMarkup(rows) {
    if (!rows.length) {
        return "<div class='dashboard-empty'>No data available.</div>";
    }

    const formatHeaderLabel = (header) => header
        .split("_")
        .filter(Boolean)
        .map((word) => word.charAt(0).toUpperCase() + word.slice(1))
        .join(" ");
    const isDateLikeHeader = (header) => [
        "delivered_at",
        "created_at",
        "updated_at",
        "last_updated",
        "timestamp",
        "evaluated_at",
        "sent_at",
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
    const headers = Object.keys(rows[0]).filter((header) => header !== "message_template");
    return `
        <table class="dashboard-table compact">
            <thead><tr>${headers.map((header) => `<th>${formatHeaderLabel(header)}</th>`).join("")}</tr></thead>
            <tbody>
                ${rows
                    .map((row) => {
                        const cells = headers.map((header) => `<td>${formatCellValue(header, row[header])}</td>`).join("");
                        return `<tr>${cells}</tr>`;
                    })
                    .join("")}
            </tbody>
        </table>
    `;
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
    if (error.name === "AbortError") {
        return timeoutMessage;
    }
    return error.message || "Request failed.";
}

async function loadNotificationEngine() {
    try {
        const data = await apiRequest("/api/notification-engine", { method: "GET" });
        rulesTableShell.innerHTML = renderTableMarkup(data.rules || []);
        deliveriesTableShell.innerHTML = renderTableMarkup(data.deliveries || []);
        notificationRecordsTableShell.innerHTML = renderTableMarkup(data.notifications || []);
        notificationEventLogsTableShell.innerHTML = renderTableMarkup(data.event_logs || []);
    } catch (error) {
        rulesTableShell.innerHTML = `<div class="dashboard-empty">${getErrorMessage(error, "Notification engine request timed out.")}</div>`;
    }
}

async function saveRule(event) {
    event.preventDefault();
    const ruleId = normalisePrefixedId(getValue("ruleId"), "NR");
    const payload = {
        rule_id: ruleId,
        name: getValue("ruleName"),
        location_id: normalisePrefixedId(getValue("ruleLocationId"), "L"),
        target_role: getValue("ruleTargetRole"),
        context_type: getValue("ruleContextType"),
        metric_name: getValue("ruleMetricName"),
        operator: getValue("ruleOperator"),
        threshold_value: getValue("ruleThresholdValue"),
        severity: getValue("ruleSeverity"),
        channels: getValue("ruleChannels"),
        message_template: getValue("ruleMessageTemplate"),
        active: getValue("ruleActive"),
    };

    try {
        if (ruleId) {
            try {
                await apiRequest(`/api/admin/notification-rules/${ruleId}`, {
                    method: "PUT",
                    body: JSON.stringify(payload),
                });
                setMessage(`Notification rule ${ruleId} updated successfully.`, "success");
            } catch (error) {
                if (!error.message.includes("was not found")) {
                    throw error;
                }
                await apiRequest("/api/admin/notification-rules", {
                    method: "POST",
                    body: JSON.stringify(payload),
                });
                setMessage(`Notification rule ${ruleId} created successfully.`, "success");
            }
        } else {
            await apiRequest("/api/admin/notification-rules", {
                method: "POST",
                body: JSON.stringify(payload),
            });
            setMessage("Notification rule created successfully.", "success");
        }
        resetForm("notificationRuleForm");
        await loadNotificationEngine();
    } catch (error) {
        setMessage(getErrorMessage(error, "Saving rule timed out."), "danger");
    }
}

async function deleteRule() {
    const ruleId = normalisePrefixedId(getValue("ruleId"), "NR");
    if (!ruleId) {
        setMessage("Enter a notification rule ID to delete.", "warning");
        return;
    }
    try {
        await apiRequest(`/api/admin/notification-rules/${ruleId}`, { method: "DELETE" });
        setMessage(`Notification rule ${ruleId} deleted successfully.`, "success");
        resetForm("notificationRuleForm");
        await loadNotificationEngine();
    } catch (error) {
        setMessage(getErrorMessage(error, "Deleting rule timed out."), "danger");
    }
}

document.getElementById("notificationRuleForm").addEventListener("submit", saveRule);
document.getElementById("deleteRuleButton").addEventListener("click", deleteRule);
if (logoutButton) {
    logoutButton.addEventListener("click", logout);
}
loadSession();
loadNotificationEngine();
