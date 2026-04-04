const loginForm = document.getElementById("loginForm");
const loginMessage = document.getElementById("loginMessage");
const demoLoginButtons = document.querySelectorAll(".demo-login-button");
const API_TIMEOUT_MS = 10000;

function setLoginMessage(message, type = "secondary") {
    loginMessage.className = `alert alert-${type}`;
    loginMessage.textContent = message;
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

async function redirectIfLoggedIn() {
    try {
        const data = await apiRequest("/api/session", { method: "GET" });
        if (data.user) {
            window.location.href = "/admin";
        }
    } catch (error) {
        setLoginMessage("Enter your admin account details to continue.", "secondary");
    }
}

async function handleLogin(event) {
    event.preventDefault();
    setLoginMessage("Signing in...", "info");

    try {
        await apiRequest("/api/login", {
            method: "POST",
            body: JSON.stringify({
                email: document.getElementById("loginEmail").value.trim(),
                password: document.getElementById("loginPassword").value,
            }),
        });
        window.location.href = "/admin";
    } catch (error) {
        setLoginMessage(
            error.name === "AbortError" ? "Login timed out. Please try again." : error.message,
            "danger",
        );
    }
}

function fillDemoCredentials(event) {
    const button = event.currentTarget;
    document.getElementById("loginEmail").value = button.dataset.email || "";
    document.getElementById("loginPassword").value = button.dataset.password || "";
    setLoginMessage("Demo credentials loaded. Click Sign In to continue.", "info");
}

loginForm.addEventListener("submit", handleLogin);
demoLoginButtons.forEach((button) => {
    button.addEventListener("click", fillDemoCredentials);
});
redirectIfLoggedIn();
