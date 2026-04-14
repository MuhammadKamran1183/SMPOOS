const statusMessage = document.getElementById("statusMessage");
const authMessage = document.getElementById("authMessage");
const sessionBadge = document.getElementById("sessionBadge");
const logoutButton = document.getElementById("logoutButton");
const dashboardLink = document.getElementById("dashboardLink");
const monitoringLink = document.getElementById("monitoringLink");
const notificationEngineLink = document.getElementById("notificationEngineLink");
const analyticsLink = document.getElementById("analyticsLink");
const API_TIMEOUT_MS = 10000;
const PERMISSION_LABELS = {
    view_management_dashboard: "the management dashboard",
    view_analytics: "analytics dashboards",
    manage_locations: "port zones and berths",
    manage_routes: "internal routes",
    manage_notifications: "notifications",
    manage_vessel_paths: "vessel paths",
    manage_restricted_areas: "restricted areas",
    manage_crane_outages: "crane outages",
    manage_berth_allocations: "berth allocations",
    manage_operational_changes: "operational changes",
    run_recalculation: "operations recalculation",
};
const ROLE_PERMISSION_FALLBACKS = {
    administrator: [
        "view_monitoring",
        "view_notification_engine",
        "view_management_dashboard",
        "view_analytics",
        "generate_reports",
        "view_sensitive_data",
        "manage_sensitive_data",
        "manage_locations",
        "manage_routes",
        "manage_notifications",
        "manage_vessel_paths",
        "manage_restricted_areas",
        "manage_crane_outages",
        "manage_berth_allocations",
        "manage_operational_changes",
        "run_recalculation",
        "manage_notification_rules",
    ],
    harbourmaster: [
        "view_monitoring",
        "view_management_dashboard",
        "view_analytics",
        "view_sensitive_data",
        "generate_reports",
        "manage_locations",
        "manage_routes",
        "manage_notifications",
        "manage_vessel_paths",
        "manage_berth_allocations",
        "manage_operational_changes",
        "run_recalculation",
    ],
    "operations supervisor": [
        "view_monitoring",
        "view_management_dashboard",
        "view_analytics",
        "generate_reports",
        "manage_routes",
        "manage_notifications",
        "manage_vessel_paths",
        "manage_berth_allocations",
        "manage_operational_changes",
        "run_recalculation",
    ],
    "safety officer": [
        "view_monitoring",
        "view_management_dashboard",
        "view_analytics",
        "manage_notifications",
        "manage_restricted_areas",
        "manage_crane_outages",
        "manage_operational_changes",
    ],
    "security officer": [
        "view_monitoring",
        "view_analytics",
        "manage_notifications",
        "manage_restricted_areas",
        "manage_crane_outages",
        "manage_operational_changes",
    ],
};

function setStatusMessage(message, type = "info") {
    // Disabled to match user request: only show save/delete messages
    return;
}

function setAuthMessage(message, type = "secondary") {
    if (!authMessage) {
        return;
    }
    authMessage.style.display = message ? "block" : "none";
    authMessage.className = `dashboard-banner ${type === "success" ? "success" : type === "danger" ? "danger" : type === "warning" ? "info" : "subtle"}`;
    authMessage.textContent = message;
    
    // Auto-hide success messages after 3 seconds
    if (type === "success") {
        setTimeout(() => {
            authMessage.style.display = "none";
        }, 3000);
    }
}

function setSessionBadge(user) {
    if (!sessionBadge) {
        return;
    }
    sessionBadge.className = "dashboard-chip admin-topbar-control";
    sessionBadge.textContent = user.name;
}

function applyPermissions(user) {
    const roleKey = String(user.canonical_role || user.role || "").trim().toLowerCase();
    const permissions = new Set(
        (user.permissions && user.permissions.length ? user.permissions : ROLE_PERMISSION_FALLBACKS[roleKey]) || [],
    );
    document.querySelectorAll("[data-permission]").forEach((section) => {
        const permission = section.dataset.permission;
        if (permissions.has(permission)) {
            return;
        }

        section.classList.add("opacity-50");
        section.querySelectorAll("input, textarea, select, button").forEach((element) => {
            element.disabled = true;
        });

        const cardBody = section.querySelector(".dashboard-panel-body");
        if (cardBody && !cardBody.querySelector(".permission-note")) {
            const note = document.createElement("p");
            note.className = "permission-note";
            note.textContent = `Your role cannot manage ${PERMISSION_LABELS[permission] || permission}.`;
            cardBody.appendChild(note);
        }
    });

    if (!permissions.has("view_notification_engine")) {
        notificationEngineLink.classList.add("disabled");
        notificationEngineLink.setAttribute("aria-disabled", "true");
        notificationEngineLink.href = "#";
    }

    if (!permissions.has("view_management_dashboard")) {
        dashboardLink.classList.add("disabled");
        dashboardLink.setAttribute("aria-disabled", "true");
        dashboardLink.href = "#";
    }

    if (!permissions.has("view_monitoring")) {
        monitoringLink.classList.add("disabled");
        monitoringLink.setAttribute("aria-disabled", "true");
        monitoringLink.href = "#";
    }

    if (!permissions.has("view_analytics")) {
        analyticsLink.classList.add("disabled");
        analyticsLink.setAttribute("aria-disabled", "true");
        analyticsLink.href = "#";
    }

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

function targetPrefix(targetType) {
    const prefixes = {
        location: "L",
        route: "R",
        restricted_area: "RA",
        crane_outage: "CO",
        vessel_path: "VP",
        berth_allocation: "BA",
        notification: "N",
    };
    return prefixes[targetType] || "";
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
        applyPermissions(data.user);
        setStatusMessage("Admin portal is ready.", "success");
        setAuthMessage(
            `Role permissions loaded for ${data.user.role}. Unavailable sections are disabled.`,
            "success",
        );
    } catch (error) {
        setStatusMessage(
            getErrorMessage(error, "Session check timed out. Please reload."),
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

async function saveRecord({
    recordId,
    collectionPath,
    payload,
    formId,
    singularLabel,
    timeoutMessage,
}) {
    try {
        if (recordId) {
            try {
                await apiRequest(`${collectionPath}/${recordId}`, {
                    method: "PUT",
                    body: JSON.stringify(payload),
                });
                setAuthMessage(`${singularLabel} ${recordId} updated successfully.`, "success");
            } catch (error) {
                if (!error.message.includes("was not found")) {
                    throw error;
                }
                await apiRequest(collectionPath, {
                    method: "POST",
                    body: JSON.stringify(payload),
                });
                setAuthMessage(`${singularLabel} ${recordId} created successfully.`, "success");
            }
        } else {
            await apiRequest(collectionPath, {
                method: "POST",
                body: JSON.stringify(payload),
            });
            setAuthMessage(`${singularLabel} created successfully.`, "success");
        }
        resetForm(formId);
    } catch (error) {
        setAuthMessage(getErrorMessage(error, timeoutMessage), "danger");
    }
}

async function deleteRecord({
    recordId,
    collectionPath,
    formId,
    singularLabel,
    timeoutMessage,
}) {
    if (!recordId) {
        setAuthMessage(`Enter a ${singularLabel.toLowerCase()} ID to delete.`, "warning");
        return;
    }

    try {
        await apiRequest(`${collectionPath}/${recordId}`, { method: "DELETE" });
        setAuthMessage(`${singularLabel} ${recordId} deleted successfully.`, "success");
        resetForm(formId);
    } catch (error) {
        setAuthMessage(getErrorMessage(error, timeoutMessage), "danger");
    }
}

async function saveLocation(event) {
    event.preventDefault();
    const recordId = normalisePrefixedId(getValue("locationId"), "L");
    await saveRecord({
        recordId,
        collectionPath: "/api/admin/locations",
        formId: "locationForm",
        singularLabel: "Location",
        timeoutMessage: "Saving location timed out. Please try again.",
        payload: {
            location_id: recordId,
            name: getValue("locationName"),
            type: getValue("locationType"),
            status: getValue("locationStatus"),
            capacity_tonnes: getValue("locationCapacity"),
        },
    });
}

async function deleteLocation() {
    await deleteRecord({
        recordId: normalisePrefixedId(getValue("locationId"), "L"),
        collectionPath: "/api/admin/locations",
        formId: "locationForm",
        singularLabel: "Location",
        timeoutMessage: "Deleting location timed out. Please try again.",
    });
}

async function saveRoute(event) {
    event.preventDefault();
    const recordId = normalisePrefixedId(getValue("routeId"), "R");
    await saveRecord({
        recordId,
        collectionPath: "/api/admin/routes",
        formId: "routeForm",
        singularLabel: "Route",
        timeoutMessage: "Saving route timed out. Please try again.",
        payload: {
            route_id: recordId,
            start_location: normalisePrefixedId(getValue("routeStart"), "L"),
            end_location: normalisePrefixedId(getValue("routeEnd"), "L"),
            route_type: getValue("routeType"),
            distance_km: getValue("routeDistance"),
            status: getValue("routeStatus"),
        },
    });
}

async function deleteRoute() {
    await deleteRecord({
        recordId: normalisePrefixedId(getValue("routeId"), "R"),
        collectionPath: "/api/admin/routes",
        formId: "routeForm",
        singularLabel: "Route",
        timeoutMessage: "Deleting route timed out. Please try again.",
    });
}

async function saveVesselPath(event) {
    event.preventDefault();
    const recordId = normalisePrefixedId(getValue("pathId"), "VP");
    await saveRecord({
        recordId,
        collectionPath: "/api/admin/vessel-paths",
        formId: "vesselPathForm",
        singularLabel: "Vessel path",
        timeoutMessage: "Saving vessel path timed out. Please try again.",
        payload: {
            path_id: recordId,
            vessel_name: getValue("vesselName"),
            vessel_type: getValue("vesselType"),
            cargo_tonnes: getValue("vesselCargoTonnes"),
            current_location_id: normalisePrefixedId(getValue("currentLocationId"), "L"),
            destination_location_id: normalisePrefixedId(getValue("destinationLocationId"), "L"),
            assigned_route_id: normalisePrefixedId(getValue("assignedRouteId"), "R"),
            assigned_berth_id: normalisePrefixedId(getValue("assignedBerthId"), "L"),
            status: getValue("pathStatus"),
        },
    });
}

async function deleteVesselPath() {
    await deleteRecord({
        recordId: normalisePrefixedId(getValue("pathId"), "VP"),
        collectionPath: "/api/admin/vessel-paths",
        formId: "vesselPathForm",
        singularLabel: "Vessel path",
        timeoutMessage: "Deleting vessel path timed out. Please try again.",
    });
}

async function saveRestrictedArea(event) {
    event.preventDefault();
    const recordId = normalisePrefixedId(getValue("areaId"), "RA");
    await saveRecord({
        recordId,
        collectionPath: "/api/admin/restricted-areas",
        formId: "restrictedAreaForm",
        singularLabel: "Restricted area",
        timeoutMessage: "Saving restricted area timed out. Please try again.",
        payload: {
            area_id: recordId,
            name: getValue("areaName"),
            location_id: normalisePrefixedId(getValue("areaLocationId"), "L"),
            area_type: getValue("areaType"),
            status: getValue("areaStatus"),
            severity: getValue("areaSeverity"),
            reason: getValue("areaReason"),
            start_time: getValue("areaStartTime"),
            end_time: getValue("areaEndTime"),
        },
    });
}

async function deleteRestrictedArea() {
    await deleteRecord({
        recordId: normalisePrefixedId(getValue("areaId"), "RA"),
        collectionPath: "/api/admin/restricted-areas",
        formId: "restrictedAreaForm",
        singularLabel: "Restricted area",
        timeoutMessage: "Deleting restricted area timed out. Please try again.",
    });
}

async function saveCraneOutage(event) {
    event.preventDefault();
    const recordId = normalisePrefixedId(getValue("outageId"), "CO");
    await saveRecord({
        recordId,
        collectionPath: "/api/admin/crane-outages",
        formId: "craneOutageForm",
        singularLabel: "Crane outage",
        timeoutMessage: "Saving crane outage timed out. Please try again.",
        payload: {
            outage_id: recordId,
            crane_id: getValue("craneId"),
            location_id: normalisePrefixedId(getValue("outageLocationId"), "L"),
            status: getValue("outageStatus"),
            severity: getValue("outageSeverity"),
            reason: getValue("outageReason"),
            start_time: getValue("outageStartTime"),
            end_time: getValue("outageEndTime"),
        },
    });
}

async function deleteCraneOutage() {
    await deleteRecord({
        recordId: normalisePrefixedId(getValue("outageId"), "CO"),
        collectionPath: "/api/admin/crane-outages",
        formId: "craneOutageForm",
        singularLabel: "Crane outage",
        timeoutMessage: "Deleting crane outage timed out. Please try again.",
    });
}

async function saveBerthAllocation(event) {
    event.preventDefault();
    const recordId = normalisePrefixedId(getValue("allocationId"), "BA");
    await saveRecord({
        recordId,
        collectionPath: "/api/admin/berth-allocations",
        formId: "berthAllocationForm",
        singularLabel: "Berth allocation",
        timeoutMessage: "Saving berth allocation timed out. Please try again.",
        payload: {
            allocation_id: recordId,
            vessel_name: getValue("allocationVesselName"),
            cargo_tonnes: getValue("allocationCargoTonnes"),
            berth_id: normalisePrefixedId(getValue("allocationBerthId"), "L"),
            eta: getValue("allocationEta"),
            status: getValue("allocationStatus"),
            priority: getValue("allocationPriority"),
            notes: getValue("allocationNotes"),
        },
    });
}

async function deleteBerthAllocation() {
    await deleteRecord({
        recordId: normalisePrefixedId(getValue("allocationId"), "BA"),
        collectionPath: "/api/admin/berth-allocations",
        formId: "berthAllocationForm",
        singularLabel: "Berth allocation",
        timeoutMessage: "Deleting berth allocation timed out. Please try again.",
    });
}

function bindDateTimePickers() {
    ["areaStartTime", "areaEndTime", "outageStartTime", "outageEndTime"].forEach(id => {
        const el = document.getElementById(id);
        if (el) {
            // Revert type to text when blurred/empty to show placeholder
            el.addEventListener("blur", () => {
                if (!el.value) el.type = "text";
            });
            // Switch type to datetime-local on focus/click to show picker
            const openPicker = () => {
                el.type = "datetime-local";
                if (el.showPicker) el.showPicker();
            };
            el.addEventListener("focus", openPicker);
            el.addEventListener("click", openPicker);
            // Initial state: text if empty
            if (!el.value) el.type = "text";
        }
    });
}

function bindForms() {
    if (logoutButton) {
        logoutButton.addEventListener("click", logout);
    }
    bindDateTimePickers();

    document.getElementById("locationForm").addEventListener("submit", saveLocation);
    document.getElementById("deleteLocationButton").addEventListener("click", deleteLocation);
    document.getElementById("routeForm").addEventListener("submit", saveRoute);
    document.getElementById("deleteRouteButton").addEventListener("click", deleteRoute);
    document.getElementById("vesselPathForm").addEventListener("submit", saveVesselPath);
    document.getElementById("deleteVesselPathButton").addEventListener("click", deleteVesselPath);
    document.getElementById("restrictedAreaForm").addEventListener("submit", saveRestrictedArea);
    document.getElementById("deleteRestrictedAreaButton").addEventListener("click", deleteRestrictedArea);
    document.getElementById("craneOutageForm").addEventListener("submit", saveCraneOutage);
    document.getElementById("deleteCraneOutageButton").addEventListener("click", deleteCraneOutage);
    document.getElementById("berthAllocationForm").addEventListener("submit", saveBerthAllocation);
    document.getElementById("deleteBerthAllocationButton").addEventListener("click", deleteBerthAllocation);
}

bindForms();
loadSession();
