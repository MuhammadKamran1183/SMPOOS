const statusMessage = document.getElementById("statusMessage");
const refreshButton = document.getElementById("refreshButton");
const loginForm = document.getElementById("loginForm");
const logoutButton = document.getElementById("logoutButton");
const authMessage = document.getElementById("authMessage");
const sessionBadge = document.getElementById("sessionBadge");
const adminPanel = document.getElementById("adminPanel");
const changeResults = document.getElementById("changeResults");

const API_TIMEOUT_MS = 10000;

function setAuthMessage(message, type = "secondary") {
    authMessage.className = `alert alert-${type}`;
    authMessage.textContent = message;
}

function setSessionState(user) {
    if (user) {
        sessionBadge.className = "badge text-bg-success";
        sessionBadge.textContent = `${user.role}: ${user.name}`;
        adminPanel.classList.remove("d-none");
        setAuthMessage("Admin session active. Protected actions are enabled.", "success");
        return;
    }

    sessionBadge.className = "badge text-bg-secondary";
    sessionBadge.textContent = "Signed out";
    adminPanel.classList.add("d-none");
    setAuthMessage("Sign in to unlock admin actions.", "secondary");
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

        if (!response.ok) {
            throw new Error(data.error || "Request failed.");
        }

        return data;
    } finally {
        clearTimeout(timeoutId);
    }
}

function getValue(id) {
    return document.getElementById(id).value.trim();
}

function resetForm(formId) {
    document.getElementById(formId).reset();
}

function setPortalStatus(message, type = "info") {
    statusMessage.className = `alert alert-${type}`;
    statusMessage.textContent = message;
}

async function refreshPortalStatus() {
    setPortalStatus("Checking admin portal connection...", "info");

    statusMessage.className = "alert alert-info";

    try {
        await apiRequest("/api/session", {
            method: "GET",
        });
        setPortalStatus("Admin portal is ready.", "success");
    } catch (error) {
        setPortalStatus(
            error.name === "AbortError"
                ? "Admin portal request timed out. Open the app through http://127.0.0.1:8000/ and refresh."
                : error.message,
            "danger",
        );
    }
}

async function loadSession() {
    try {
        const data = await apiRequest("/api/session", {
            method: "GET",
        });
        setSessionState(data.user);
    } catch (error) {
        setSessionState(null);
        setAuthMessage(error.message, "danger");
    }
}

async function login(event) {
    event.preventDefault();

    try {
        const data = await apiRequest("/api/login", {
            method: "POST",
            body: JSON.stringify({
                email: getValue("loginEmail"),
                password: document.getElementById("loginPassword").value,
            }),
        });
        setSessionState(data.user);
    } catch (error) {
        setSessionState(null);
        setAuthMessage(error.message, "danger");
    }
}

async function logout() {
    try {
        await apiRequest("/api/logout", {
            method: "POST",
            body: JSON.stringify({}),
        });
    } finally {
        setSessionState(null);
    }
}

async function saveLocation(event) {
    event.preventDefault();

    const locationId = getValue("locationId");
    const payload = {
        location_id: locationId,
        name: getValue("locationName"),
        type: getValue("locationType"),
        status: getValue("locationStatus"),
        capacity_tonnes: getValue("locationCapacity"),
    };

    const path = locationId ? `/api/admin/locations/${locationId}` : "/api/admin/locations";
    const method = locationId ? "PUT" : "POST";

    await apiRequest(path, {
        method,
        body: JSON.stringify(payload),
    });

    setAuthMessage("Location saved successfully.", "success");
    resetForm("locationForm");
}

async function deleteLocation() {
    const locationId = getValue("locationId");

    if (!locationId) {
        setAuthMessage("Enter a location ID to delete.", "warning");
        return;
    }

    await apiRequest(`/api/admin/locations/${locationId}`, {
        method: "DELETE",
    });

    setAuthMessage(`Location ${locationId} deleted successfully.`, "success");
    resetForm("locationForm");
}

async function saveRoute(event) {
    event.preventDefault();

    const routeId = getValue("routeId");
    const payload = {
        route_id: routeId,
        start_location: getValue("routeStart"),
        end_location: getValue("routeEnd"),
        route_type: getValue("routeType"),
        distance_km: getValue("routeDistance"),
        status: getValue("routeStatus"),
    };

    const path = routeId ? `/api/admin/routes/${routeId}` : "/api/admin/routes";
    const method = routeId ? "PUT" : "POST";

    await apiRequest(path, {
        method,
        body: JSON.stringify(payload),
    });

    setAuthMessage("Route saved successfully.", "success");
    resetForm("routeForm");
}

async function deleteRoute() {
    const routeId = getValue("routeId");

    if (!routeId) {
        setAuthMessage("Enter a route ID to delete.", "warning");
        return;
    }

    await apiRequest(`/api/admin/routes/${routeId}`, {
        method: "DELETE",
    });

    setAuthMessage(`Route ${routeId} deleted successfully.`, "success");
    resetForm("routeForm");
}

async function saveNotification(event) {
    event.preventDefault();

    const notificationId = getValue("notificationId");
    const payload = {
        notification_id: notificationId,
        alert_type: getValue("notificationType"),
        location_id: getValue("notificationLocationId"),
        severity: getValue("notificationSeverity"),
        message: getValue("notificationMessageText"),
    };

    const path = notificationId
        ? `/api/admin/notifications/${notificationId}`
        : "/api/admin/notifications";
    const method = notificationId ? "PUT" : "POST";

    await apiRequest(path, {
        method,
        body: JSON.stringify(payload),
    });

    setAuthMessage("Notification saved successfully.", "success");
    resetForm("notificationForm");
}

async function deleteNotification() {
    const notificationId = getValue("notificationId");

    if (!notificationId) {
        setAuthMessage("Enter a notification ID to delete.", "warning");
        return;
    }

    await apiRequest(`/api/admin/notifications/${notificationId}`, {
        method: "DELETE",
    });

    setAuthMessage(`Notification ${notificationId} deleted successfully.`, "success");
    resetForm("notificationForm");
}

async function applyOperationalChange(event) {
    event.preventDefault();

    const result = await apiRequest("/api/admin/operational-change", {
        method: "POST",
        body: JSON.stringify({
            target_type: getValue("changeTargetType"),
            target_id: getValue("changeTargetId"),
            new_status: getValue("changeStatus"),
            alert_type: getValue("changeAlertType"),
            severity: getValue("changeSeverity"),
            message: getValue("changeMessage"),
        }),
    });

    changeResults.textContent = JSON.stringify(result, null, 2);
    setAuthMessage("Operational change applied successfully.", "success");
}

function bindAdminForms() {
    loginForm.addEventListener("submit", login);
    logoutButton.addEventListener("click", logout);
    document.getElementById("locationForm").addEventListener("submit", saveLocation);
    document.getElementById("deleteLocationButton").addEventListener("click", deleteLocation);
    document.getElementById("routeForm").addEventListener("submit", saveRoute);
    document.getElementById("deleteRouteButton").addEventListener("click", deleteRoute);
    document.getElementById("notificationForm").addEventListener("submit", saveNotification);
    document
        .getElementById("deleteNotificationButton")
        .addEventListener("click", deleteNotification);
    document.getElementById("changeForm").addEventListener("submit", applyOperationalChange);
}

refreshButton.addEventListener("click", refreshPortalStatus);
bindAdminForms();
loadSession();
refreshPortalStatus();
