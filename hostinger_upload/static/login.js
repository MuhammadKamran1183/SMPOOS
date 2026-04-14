const loginForm = document.getElementById("loginForm");
const loginEmail = document.getElementById("loginEmail");
const loginPassword = document.getElementById("loginPassword");
const loginMessage = document.getElementById("loginMessage");

function setLoginMessage(text) {
    if (!loginMessage) {
        return;
    }
    loginMessage.textContent = text;
}

document.querySelectorAll(".demo-login-button").forEach((button) => {
    button.addEventListener("click", () => {
        if (loginEmail) {
            loginEmail.value = button.dataset.email || "";
        }
        if (loginPassword) {
            loginPassword.value = button.dataset.password || "";
        }
        setLoginMessage("Demo credentials filled. Click Sign In.");
    });
});

if (loginForm) {
    loginForm.addEventListener("submit", (event) => {
        event.preventDefault();
        window.location.href = "/dashboard.html";
    });
}
