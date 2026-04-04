const statusMessage = document.getElementById("statusMessage");
const authMessage = document.getElementById("authMessage");
const sessionBadge = document.getElementById("sessionBadge");
const logoutButton = document.getElementById("logoutButton");
const changeResults = document.getElementById("changeResults");
const API_TIMEOUT_MS = 10000;

function setStatusMessage(message, type = "info") {
    statusMessage.className = `alert alert-${type}`;
    statusMessage.textContent = message;
}

function setAuthMessage(message, type = "secondary") {
    authMessage.className = `alert alert-${type}`;
    authMessage.textContent = message;
}

function setSessionBadge(user) {
    sessionBadge.className = "badge text-bg-success";
    sessionBadge.textContent = `${user.role}: ${user.name}`;
}

function getErrorMessage(error, timeoutMessage) {
    if (error.name === "AbortError") {
        return timeoutMessage;
    }
    return error.message || "Request failed.";
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

function getValue(id) {
    return document.getElementById(id).value.trim();
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

function resetForm(formId) {
    document.getElementById(formId).reset();
}

async function loadSession() {
    setStatusMessage("Loading admin tools...", "info");

    try {
        const data = await apiRequest("/api/session", { method: "GET" });

        if (!data.user) {
            window.location.href = "/login";
            return;
        }

        setSessionBadge(data.user);
        setStatusMessage("Admin portal is ready.", "success");
        setAuthMessage("You can now manage operational data.", "success");
    } catch (error) {
        setStatusMessage(
            error.name === "AbortError"
                ? "Session check timed out. Please reload."
                : error.message,
            "danger",
        );
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

async function saveLocation(event) {
    event.preventDefault();

    const locationId = normalisePrefixedId(getValue("locationId"), "L");
    const payload = {
        location_id: locationId,
        name: getValue("locationName"),
        type: getValue("locationType"),
        status: getValue("locationStatus"),
        capacity_tonnes: getValue("locationCapacity"),
    };

    try {
        if (locationId) {
            try {
                await apiRequest(`/api/admin/locations/${locationId}`, {
                    method: "PUT",
                    body: JSON.stringify(payload),
                });
                setAuthMessage(`Location ${locationId} updated successfully.`, "success");
            } catch (error) {
                if (!error.message.includes("was not found")) {
                    throw error;
                }
                await apiRequest("/api/admin/locations", {
                    method: "POST",
                    body: JSON.stringify(payload),
                });
                setAuthMessage(`Location ${locationId} created successfully.`, "success");
            }
        } else {
            await apiRequest("/api/admin/locations", {
                method: "POST",
                body: JSON.stringify(payload),
            });
            setAuthMessage("Location created successfully.", "success");
        }

        resetForm("locationForm");
    } catch (error) {
        setAuthMessage(
            getErrorMessage(error, "Saving location timed out. Please try again."),
            "danger",
        );
    }
}

async function deleteLocation() {
    const locationId = normalisePrefixedId(getValue("locationId"), "L");

    if (!locationId) {
        setAuthMessage("Enter a location ID to delete.", "warning");
        return;
    }

    try {
        await apiRequest(`/api/admin/locations/${locationId}`, { method: "DELETE" });
        setAuthMessage(`Location ${locationId} deleted successfully.`, "success");
        resetForm("locationForm");
    } catch (error) {
        setAuthMessage(
            getErrorMessage(error, "Deleting location timed out. Please try again."),
            "danger",
        );
    }
}

async function saveRoute(event) {
    event.preventDefault();

    const routeId = normalisePrefixedId(getValue("routeId"), "R");
    const payload = {
        route_id: routeId,
        start_location: normalisePrefixedId(getValue("routeStart"), "L"),
        end_location: normalisePrefixedId(getValue("routeEnd"), "L"),
        route_type: getValue("routeType"),
        distance_km: getValue("routeDistance"),
        status: getValue("routeStatus"),
    };

    try {
        if (routeId) {
            try {
                await apiRequest(`/api/admin/routes/${routeId}`, {
                    method: "PUT",
                    body: JSON.stringify(payload),
                });
                setAuthMessage(`Route ${routeId} updated successfully.`, "success");
            } catch (error) {
                if (!error.message.includes("was not found")) {
                    throw error;
                }
                await apiRequest("/api/admin/routes", {
                    method: "POST",
                    body: JSON.stringify(payload),
                });
                setAuthMessage(`Route ${routeId} created successfully.`, "success");
            }
        } else {
            await apiRequest("/api/admin/routes", {
                method: "POST",
                body: JSON.stringify(payload),
            });
            setAuthMessage("Route created successfully.", "success");
        }

        resetForm("routeForm");
    } catch (error) {
        setAuthMessage(
            getErrorMessage(error, "Saving route timed out. Please try again."),
            "danger",
        );
    }
}

async function deleteRoute() {
    const routeId = normalisePrefixedId(getValue("routeId"), "R");

    if (!routeId) {
        setAuthMessage("Enter a route ID to delete.", "warning");
        return;
    }

    try {
        await apiRequest(`/api/admin/routes/${routeId}`, { method: "DELETE" });
        setAuthMessage(`Route ${routeId} deleted successfully.`, "success");
        resetForm("routeForm");
    } catch (error) {
        setAuthMessage(
            getErrorMessage(error, "Deleting route timed out. Please try again."),
            "danger",
        );
    }
}

async function saveNotification(event) {
    event.preventDefault();

    const notificationId = normalisePrefixedId(getValue("notificationId"), "N");
    const payload = {
        notification_id: notificationId,
        alert_type: getValue("notificationType"),
        location_id: normalisePrefixedId(getValue("notificationLocationId"), "L"),
        severity: getValue("notificationSeverity"),
        message: getValue("notificationMessageText"),
    };

    try {
        if (notificationId) {
            try {
                await apiRequest(`/api/admin/notifications/${notificationId}`, {
                    method: "PUT",
                    body: JSON.stringify(payload),
                });
                setAuthMessage(
                    `Notification ${notificationId} updated successfully.`,
                    "success",
                );
            } catch (error) {
                if (!error.message.includes("was not found")) {
                    throw error;
                }
                await apiRequest("/api/admin/notifications", {
                    method: "POST",
                    body: JSON.stringify(payload),
                });
                setAuthMessage(
                    `Notification ${notificationId} created successfully.`,
                    "success",
                );
            }
        } else {
            await apiRequest("/api/admin/notifications", {
                method: "POST",
                body: JSON.stringify(payload),
            });
            setAuthMessage("Notification created successfully.", "success");
        }

        resetForm("notificationForm");
    } catch (error) {
        setAuthMessage(
            getErrorMessage(error, "Saving notification timed out. Please try again."),
            "danger",
        );
    }
}

async function deleteNotification() {
    const notificationId = normalisePrefixedId(getValue("notificationId"), "N");

    if (!notificationId) {
        setAuthMessage("Enter a notification ID to delete.", "warning");
        return;
    }

    try {
        await apiRequest(`/api/admin/notifications/${notificationId}`, { method: "DELETE" });
        setAuthMessage(`Notification ${notificationId} deleted successfully.`, "success");
        resetForm("notificationForm");
    } catch (error) {
        setAuthMessage(
            getErrorMessage(error, "Deleting notification timed out. Please try again."),
            "danger",
        );
    }
}

async function applyOperationalChange(event) {
    event.preventDefault();

    try {
        const result = await apiRequest("/api/admin/operational-change", {
            method: "POST",
            body: JSON.stringify({
                target_type: getValue("changeTargetType"),
                target_id: normalisePrefixedId(
                    getValue("changeTargetId"),
                    getValue("changeTargetType") === "route" ? "R" : "L",
                ),
                new_status: getValue("changeStatus"),
                alert_type: getValue("changeAlertType"),
                severity: getValue("changeSeverity"),
                message: getValue("changeMessage"),
            }),
        });

        changeResults.textContent = JSON.stringify(result, null, 2);
        setAuthMessage("Operational change applied successfully.", "success");
    } catch (error) {
        setAuthMessage(
            getErrorMessage(error, "Applying change timed out. Please try again."),
            "danger",
        );
    }
}

function bindForms() {
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

bindForms();
loadSession();
