const chatWindow = document.getElementById("chatWindow");
const messageInput = document.getElementById("messageInput");
const sendBtn = document.getElementById("sendBtn");
const sendBtnText = document.getElementById("sendBtnText");
const sendSpinner = document.getElementById("sendSpinner");
const loadingDot = document.getElementById("loadingDot");

const imageDropZone = document.getElementById("imageDropZone");
const imageInput = document.getElementById("imageInput");
const imageStatus = document.getElementById("imageStatus");

const docDropZone = document.getElementById("docDropZone");
const docInput = document.getElementById("docInput");
const docStatus = document.getElementById("docStatus");

const selectedFilesEl = document.getElementById("selectedFiles");
const fileManager = document.getElementById("fileManager");
const refreshFilesBtn = document.getElementById("refreshFilesBtn");
const themeToggleBtn = document.getElementById("themeToggleBtn");
const themeLabel = document.getElementById("themeLabel");
const themeIcon = themeToggleBtn.querySelector("i");
const logoutBtn = document.getElementById("logoutBtn");
const userBadge = document.getElementById("userBadge");

const MAX_FILE_SIZE = 15 * 1024 * 1024;
const IMAGE_EXT = ["jpg", "jpeg", "png"];
const DOC_EXT = ["pdf", "docx", "csv", "xlsx", "pptx"];

const state = {
    files: [],
    selectedIds: new Set(),
};

async function apiFetch(url, options = {}) {
    const response = await fetch(url, options);
    if (response.status === 401) {
        window.location.href = "/login";
        throw new Error("Session expired.");
    }
    return response;
}

function escapeHtml(text) {
    const div = document.createElement("div");
    div.textContent = text;
    return div.innerHTML;
}

function applyInlineMarkdown(text) {
    return text
        .replace(/\*\*(.+?)\*\*/g, "<strong>$1</strong>")
        .replace(/\*(.+?)\*/g, "<em>$1</em>")
        .replace(/`([^`]+)`/g, "<code>$1</code>");
}

function markdownToHtml(raw) {
    const lines = escapeHtml(raw || "").replace(/\r\n/g, "\n").split("\n");
    let html = "";
    let inUl = false;
    let inOl = false;

    const closeLists = () => {
        if (inUl) {
            html += "</ul>";
            inUl = false;
        }
        if (inOl) {
            html += "</ol>";
            inOl = false;
        }
    };

    lines.forEach((line) => {
        const trimmed = line.trim();

        if (!trimmed) {
            closeLists();
            return;
        }

        if (/^###\s+/.test(trimmed)) {
            closeLists();
            html += `<h3>${applyInlineMarkdown(trimmed.replace(/^###\s+/, ""))}</h3>`;
            return;
        }

        if (/^##\s+/.test(trimmed)) {
            closeLists();
            html += `<h3>${applyInlineMarkdown(trimmed.replace(/^##\s+/, ""))}</h3>`;
            return;
        }

        if (/^#\s+/.test(trimmed)) {
            closeLists();
            html += `<h3>${applyInlineMarkdown(trimmed.replace(/^#\s+/, ""))}</h3>`;
            return;
        }

        if (/^[-*]\s+/.test(trimmed)) {
            if (inOl) {
                html += "</ol>";
                inOl = false;
            }
            if (!inUl) {
                html += "<ul>";
                inUl = true;
            }
            html += `<li>${applyInlineMarkdown(trimmed.replace(/^[-*]\s+/, ""))}</li>`;
            return;
        }

        if (/^\d+\.\s+/.test(trimmed)) {
            if (inUl) {
                html += "</ul>";
                inUl = false;
            }
            if (!inOl) {
                html += "<ol>";
                inOl = true;
            }
            html += `<li>${applyInlineMarkdown(trimmed.replace(/^\d+\.\s+/, ""))}</li>`;
            return;
        }

        closeLists();
        html += `<p>${applyInlineMarkdown(trimmed)}</p>`;
    });

    closeLists();
    return html || `<p>${escapeHtml(raw || "")}</p>`;
}

function addMessage(content, role = "ai", formatted = false) {
    const row = document.createElement("div");
    row.className = `message-row ${role}`;

    const bubble = document.createElement("div");
    bubble.className = `message-bubble ${role}`;

    if (formatted) {
        bubble.innerHTML = markdownToHtml(content);
    } else {
        bubble.textContent = content;
    }

    row.appendChild(bubble);
    chatWindow.appendChild(row);
    chatWindow.scrollTop = chatWindow.scrollHeight;
    return row;
}

function showTyping() {
    const row = document.createElement("div");
    row.className = "message-row ai";

    const bubble = document.createElement("div");
    bubble.className = "message-bubble ai";
    bubble.innerHTML = '<span class="typing-dot"></span><span class="typing-dot"></span><span class="typing-dot"></span>';

    row.appendChild(bubble);
    chatWindow.appendChild(row);
    chatWindow.scrollTop = chatWindow.scrollHeight;
    return row;
}

function setLoading(loading) {
    sendBtn.disabled = loading;
    sendBtnText.classList.toggle("d-none", loading);
    sendSpinner.classList.toggle("d-none", !loading);
    loadingDot.classList.toggle("d-none", !loading);
}

function getExt(filename) {
    const idx = filename.lastIndexOf(".");
    return idx >= 0 ? filename.slice(idx + 1).toLowerCase() : "";
}

function formatSize(bytes) {
    if (bytes < 1024) return `${bytes} B`;
    if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
    return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
}

function formatDate(dateStr) {
    return new Date(dateStr).toLocaleString();
}

function iconForType(type) {
    if (IMAGE_EXT.includes(type)) return "bi-file-image";
    if (type === "pdf") return "bi-file-earmark-pdf";
    if (type === "docx") return "bi-file-earmark-word";
    if (type === "pptx") return "bi-file-earmark-slides";
    if (["csv", "xlsx"].includes(type)) return "bi-file-earmark-spreadsheet";
    return "bi-file-earmark";
}

function basename(path) {
    return String(path).replace(/\\/g, "/").split("/").pop();
}

function syncSelectedIds() {
    const fileIds = new Set(state.files.map((f) => f.id));
    [...state.selectedIds].forEach((id) => {
        if (!fileIds.has(id)) state.selectedIds.delete(id);
    });
}

function renderSelectedFiles() {
    selectedFilesEl.innerHTML = "";
    const selected = state.files.filter((f) => state.selectedIds.has(f.id));

    selected.forEach((file) => {
        const chip = document.createElement("div");
        chip.className = "file-chip";
        chip.innerHTML = `
            <i class="bi ${iconForType(file.filetype)}"></i>
            <span>${escapeHtml(file.filename)} (${formatSize(file.size)})</span>
            <button type="button" aria-label="Remove file"><i class="bi bi-x"></i></button>
        `;

        chip.querySelector("button").addEventListener("click", () => {
            state.selectedIds.delete(file.id);
            renderSelectedFiles();
            renderFileManager();
        });

        selectedFilesEl.appendChild(chip);
    });
}

function renderFileManager() {
    fileManager.innerHTML = "";

    if (state.files.length === 0) {
        fileManager.innerHTML = '<div class="text-muted small p-1">No uploaded files yet.</div>';
        return;
    }

    state.files.forEach((file) => {
        const selected = state.selectedIds.has(file.id);
        const row = document.createElement("div");
        row.className = "file-row";
        row.innerHTML = `
            <div class="file-row-head">
                <div class="file-row-name"><i class="bi ${iconForType(file.filetype)} me-1"></i>${escapeHtml(file.filename)}</div>
                <button class="btn btn-sm ${selected ? "btn-success" : "btn-outline-success"}" data-action="toggle-use">${selected ? "Using" : "Use"}</button>
            </div>
            <div class="file-row-meta">${formatDate(file.created_at)} • ${formatSize(file.size)}</div>
            <div class="file-row-actions">
                <button class="btn btn-sm btn-outline-secondary" data-action="open">Open</button>
                <button class="btn btn-sm btn-outline-primary" data-action="rename">Rename</button>
                <button class="btn btn-sm btn-outline-danger" data-action="delete">Delete</button>
            </div>
        `;

        row.querySelector('[data-action="toggle-use"]').addEventListener("click", () => {
            if (state.selectedIds.has(file.id)) {
                state.selectedIds.delete(file.id);
            } else {
                state.selectedIds.add(file.id);
            }
            renderSelectedFiles();
            renderFileManager();
        });

        row.querySelector('[data-action="open"]').addEventListener("click", () => {
            window.open(`/uploads/${basename(file.filepath)}`, "_blank");
        });

        row.querySelector('[data-action="rename"]').addEventListener("click", async () => {
            const next = prompt("Enter new filename", file.filename);
            if (!next || !next.trim()) return;

            const response = await apiFetch(`/files/${file.id}`, {
                method: "PUT",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ filename: next.trim() }),
            });

            const data = await response.json();
            if (!response.ok) {
                addMessage(`Rename failed: ${data.detail || "Unknown error"}`, "ai");
                return;
            }

            await loadFiles();
        });

        row.querySelector('[data-action="delete"]').addEventListener("click", async () => {
            if (!confirm(`Delete ${file.filename}?`)) return;

            const response = await apiFetch(`/files/${file.id}`, { method: "DELETE" });
            const data = await response.json();
            if (!response.ok) {
                addMessage(`Delete failed: ${data.detail || "Unknown error"}`, "ai");
                return;
            }

            state.selectedIds.delete(file.id);
            await loadFiles();
        });

        fileManager.appendChild(row);
    });
}

async function loadFiles() {
    const response = await apiFetch("/files");
    const data = await response.json();
    if (!response.ok) {
        addMessage(`Failed to load files: ${data.detail || "Unknown error"}`, "ai");
        return;
    }

    state.files = data;
    syncSelectedIds();
    renderSelectedFiles();
    renderFileManager();
}

function validateFile(file, allowedExt, label) {
    if (!file) return false;

    const ext = getExt(file.name);
    if (!allowedExt.includes(ext)) {
        addMessage(`${label} upload error: Unsupported .${ext || "unknown"} file`, "ai");
        return false;
    }

    if (file.size > MAX_FILE_SIZE) {
        addMessage(`${label} upload error: File too large (max 15MB)`, "ai");
        return false;
    }

    return true;
}

async function uploadFile(file, statusEl) {
    const formData = new FormData();
    formData.append("file", file);

    statusEl.textContent = "Uploading...";

    const response = await apiFetch("/upload", {
        method: "POST",
        body: formData,
    });

    const data = await response.json();
    if (!response.ok) {
        throw new Error(data.detail || "Upload failed");
    }

    state.selectedIds.add(data.file.id);
    statusEl.textContent = `Uploaded: ${data.file.filename}`;

    await loadFiles();
    addMessage(`Uploaded: ${data.file.filename} and selected for context.`, "ai");
}

async function handleImage(file) {
    if (!validateFile(file, IMAGE_EXT, "Image")) return;
    try {
        await uploadFile(file, imageStatus);
    } catch (error) {
        imageStatus.textContent = "Drag & drop JPG/PNG or click";
        addMessage(`Image upload error: ${error.message}`, "ai");
    }
}

async function handleDoc(file) {
    if (!validateFile(file, DOC_EXT, "Document")) return;
    try {
        await uploadFile(file, docStatus);
    } catch (error) {
        docStatus.textContent = "Drag & drop PDF/DOCX/CSV/XLSX/PPTX or click";
        addMessage(`Document upload error: ${error.message}`, "ai");
    }
}

async function sendMessage() {
    const question = messageInput.value.trim();
    if (!question) return;

    addMessage(question, "user");
    messageInput.value = "";
    setLoading(true);
    const typing = showTyping();

    try {
        const response = await apiFetch("/chat", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
                question,
                file_ids: [...state.selectedIds],
            }),
        });

        const data = await response.json();
        if (!response.ok) {
            throw new Error(data.detail || "Failed to get answer");
        }

        typing.remove();

        if (data.auto_selected && Array.isArray(data.used_files)) {
            data.used_files.forEach((id) => state.selectedIds.add(id));
            await loadFiles();
            addMessage("I auto-selected recent uploaded files for this request.", "ai");
        }

        addMessage(data.answer, "ai", true);
    } catch (error) {
        typing.remove();
        addMessage(`Error: ${error.message}`, "ai");
    } finally {
        setLoading(false);
    }
}

function wireDropZone(zoneEl, inputEl, onFile) {
    zoneEl.addEventListener("click", () => inputEl.click());

    zoneEl.addEventListener("keydown", (e) => {
        if (e.key === "Enter" || e.key === " ") {
            e.preventDefault();
            inputEl.click();
        }
    });

    inputEl.addEventListener("change", (e) => {
        const file = e.target.files?.[0];
        onFile(file);
        inputEl.value = "";
    });

    ["dragenter", "dragover"].forEach((evt) => {
        zoneEl.addEventListener(evt, (e) => {
            e.preventDefault();
            zoneEl.classList.add("active");
        });
    });

    ["dragleave", "drop"].forEach((evt) => {
        zoneEl.addEventListener(evt, (e) => {
            e.preventDefault();
            zoneEl.classList.remove("active");
        });
    });

    zoneEl.addEventListener("drop", (e) => {
        const file = e.dataTransfer?.files?.[0];
        onFile(file);
    });
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

async function ensureAuthenticated() {
    const response = await fetch("/auth/me");
    if (response.status === 401) {
        window.location.href = "/login";
        return;
    }

    const data = await response.json();
    if (!response.ok) {
        window.location.href = "/login";
        return;
    }

    userBadge.textContent = `@${data.username}`;
    userBadge.classList.remove("d-none");
}

async function logout() {
    await fetch("/auth/logout", { method: "POST" });
    window.location.href = "/login";
}

sendBtn.addEventListener("click", sendMessage);
messageInput.addEventListener("keydown", (e) => {
    if (e.key === "Enter" && !e.shiftKey) {
        e.preventDefault();
        sendMessage();
    }
});

refreshFilesBtn.addEventListener("click", loadFiles);
themeToggleBtn.addEventListener("click", toggleTheme);
logoutBtn.addEventListener("click", logout);

wireDropZone(imageDropZone, imageInput, handleImage);
wireDropZone(docDropZone, docInput, handleDoc);

(async () => {
    initTheme();
    await ensureAuthenticated();
    await loadFiles();
    addMessage("Hi, upload your image or document and ask anything. I can summarize and reason across multiple files.", "ai");
})();
