const summaryCards = document.getElementById("summaryCards");
const statusMessage = document.getElementById("statusMessage");
const refreshButton = document.getElementById("refreshButton");

function renderSummary(summary) {
    const items = [
        ["Locations", summary.locations],
        ["Routes", summary.routes],
        ["Notifications", summary.notifications],
        ["Users", summary.users],
    ];

    summaryCards.innerHTML = items
        .map(
            ([label, count]) => `
                <div class="col-md-6 col-xl-3">
                    <div class="card summary-card shadow-sm">
                        <div class="card-body">
                            <div class="text-uppercase small">${label}</div>
                            <div class="count">${count}</div>
                        </div>
                    </div>
                </div>
            `
        )
        .join("");
}

function renderTable(tableId, rows) {
    const table = document.getElementById(tableId);

    if (!rows.length) {
        table.innerHTML = "<tbody><tr><td>No data found.</td></tr></tbody>";
        return;
    }

    const headers = Object.keys(rows[0]);
    const headerHtml = headers.map((header) => `<th>${header}</th>`).join("");
    const bodyHtml = rows
        .slice(0, 20)
        .map((row) => {
            const cells = headers
                .map((header) => `<td>${row[header]}</td>`)
                .join("");
            return `<tr>${cells}</tr>`;
        })
        .join("");

    table.innerHTML = `
        <thead>
            <tr>${headerHtml}</tr>
        </thead>
        <tbody>${bodyHtml}</tbody>
    `;
}

async function loadDashboard() {
    statusMessage.className = "alert alert-info";
    statusMessage.textContent = "Loading dashboard data...";

    try {
        const response = await fetch("/api/dashboard");

        if (!response.ok) {
            throw new Error("Failed to load dashboard data.");
        }

        const data = await response.json();
        renderSummary(data.summary);
        renderTable("locationsTable", data.locations);
        renderTable("routesTable", data.routes);
        renderTable("notificationsTable", data.notifications);
        renderTable("usersTable", data.users);

        statusMessage.className = "alert alert-success";
        statusMessage.textContent = "Dashboard data loaded successfully.";
    } catch (error) {
        statusMessage.className = "alert alert-danger";
        statusMessage.textContent = error.message;
    }
}

refreshButton.addEventListener("click", loadDashboard);
loadDashboard();
