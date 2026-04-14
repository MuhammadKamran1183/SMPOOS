function initDemo() {
    const sessionBadge = document.getElementById("sessionBadge");
    if (sessionBadge) {
        sessionBadge.textContent = "Demo";
    }

    const logoutButton = document.getElementById("logoutButton");
    if (logoutButton) {
        logoutButton.addEventListener("click", () => {
            window.location.href = "/index.html";
        });
    }

    document.querySelectorAll("form").forEach((form) => {
        form.addEventListener("submit", (event) => {
            event.preventDefault();
            alert("This Hostinger shared-hosting package is UI-only. Python backend features need VPS or Python hosting.");
        });
    });

    document.querySelectorAll('button[id^="delete"], #deleteRuleButton').forEach((button) => {
        button.addEventListener("click", () => {
            alert("Delete is disabled in the static demo. Upload the full app to VPS for working backend actions.");
        });
    });
}

if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", initDemo);
} else {
    initDemo();
}
