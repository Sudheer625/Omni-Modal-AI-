const mode = document.body.dataset.mode;

const form = document.getElementById("authForm");
const errorBox = document.getElementById("errorBox");
const submitText = document.getElementById("submitText");
const submitSpinner = document.getElementById("submitSpinner");
const themeToggleBtn = document.getElementById("themeToggleBtn");
const themeLabel = document.getElementById("themeLabel");
const themeIcon = themeToggleBtn.querySelector("i");

const usernameInput = document.getElementById("usernameInput");
const emailInput = document.getElementById("emailInput");
const identifierInput = document.getElementById("identifierInput");
const passwordInput = document.getElementById("passwordInput");
const confirmPasswordInput = document.getElementById("confirmPasswordInput");

function setSubmitting(isSubmitting) {
    submitText.classList.toggle("d-none", isSubmitting);
    submitSpinner.classList.toggle("d-none", !isSubmitting);
}

function showError(message) {
    errorBox.textContent = message;
    errorBox.classList.remove("d-none");
}

function clearError() {
    errorBox.textContent = "";
    errorBox.classList.add("d-none");
}

function applyTheme(theme) {
    document.documentElement.setAttribute("data-theme", theme);
    localStorage.setItem("omni_theme", theme);
    const isLight = theme === "light";
    themeLabel.textContent = isLight ? "Dark" : "Light";
    themeIcon.className = isLight ? "bi bi-moon-stars me-1" : "bi bi-sun me-1";
}

function toggleTheme() {
    const current = document.documentElement.getAttribute("data-theme") || "light";
    applyTheme(current === "light" ? "dark" : "light");
}

function initTheme() {
    const saved = localStorage.getItem("omni_theme") || "light";
    applyTheme(saved);
}

function buildPayload() {
    if (mode === "register") {
        const username = usernameInput.value.trim();
        const email = emailInput.value.trim();
        const password = passwordInput.value;
        const confirm = confirmPasswordInput.value;

        if (!username || !email || !password || !confirm) {
            throw new Error("All fields are required.");
        }

        if (password !== confirm) {
            throw new Error("Passwords do not match.");
        }

        return { username, email, password };
    }

    const identifier = identifierInput.value.trim();
    const password = passwordInput.value;

    if (!identifier || !password) {
        throw new Error("Identifier and password are required.");
    }

    return { identifier, password };
}

async function submitForm(event) {
    event.preventDefault();
    clearError();

    let payload;
    try {
        payload = buildPayload();
    } catch (err) {
        showError(err.message || "Invalid input.");
        return;
    }

    setSubmitting(true);

    try {
        if (mode === "register") {
            const registerRes = await fetch("/auth/register", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify(payload),
            });
            const registerData = await registerRes.json();
            if (!registerRes.ok) {
                throw new Error(registerData.detail || "Registration failed.");
            }

            const loginRes = await fetch("/auth/login", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ identifier: payload.email, password: payload.password }),
            });
            const loginData = await loginRes.json();
            if (!loginRes.ok) {
                throw new Error(loginData.detail || "Auto-login failed after registration.");
            }
        } else {
            const loginRes = await fetch("/auth/login", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify(payload),
            });
            const loginData = await loginRes.json();
            if (!loginRes.ok) {
                throw new Error(loginData.detail || "Login failed.");
            }
        }

        window.location.href = "/";
    } catch (err) {
        showError(err.message || "Request failed.");
    } finally {
        setSubmitting(false);
    }
}

form.addEventListener("submit", submitForm);
themeToggleBtn.addEventListener("click", toggleTheme);

initTheme();
