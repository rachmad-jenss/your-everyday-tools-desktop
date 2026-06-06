/* ── Theme ────────────────────────────────────── */
const THEME_KEY = "theme";

function getStoredTheme() {
    return localStorage.getItem(THEME_KEY) || "system";
}

function resolveTheme(mode) {
    if (mode === "dark") return "dark";
    if (mode === "light") return "light";
    return (window.matchMedia && window.matchMedia("(prefers-color-scheme: dark)").matches) ? "dark" : "light";
}

function applyTheme(mode, animate) {
    localStorage.setItem(THEME_KEY, mode);
    const html = document.documentElement;

    if (animate) {
        html.classList.add("theme-animate");
    }

    html.dataset.theme = resolveTheme(mode);

    document.querySelectorAll(".theme-btn").forEach(btn => {
        btn.classList.toggle("active", btn.dataset.themeMode === mode);
    });

    if (animate) {
        clearTimeout(applyTheme._timer);
        applyTheme._timer = setTimeout(() => html.classList.remove("theme-animate"), 400);
    }
}

function initTheme() {
    const mode = getStoredTheme();
    applyTheme(mode, false);
    document.querySelectorAll(".theme-btn").forEach(btn => {
        btn.addEventListener("click", () => {
            // Spin the icon
            const icon = btn.querySelector("i");
            if (icon) {
                btn.classList.remove("spinning");
                void btn.offsetWidth; // force reflow to restart animation
                btn.classList.add("spinning");
                setTimeout(() => btn.classList.remove("spinning"), 380);
            }
            applyTheme(btn.dataset.themeMode, true);
        });
    });
    if (window.matchMedia) {
        window.matchMedia("(prefers-color-scheme: dark)").addEventListener("change", () => {
            if (getStoredTheme() === "system") {
                document.documentElement.dataset.theme = resolveTheme("system");
            }
        });
    }
}

/* ── Sidebar ──────────────────────────────────── */
function toggleCategory(btn) {
    btn.classList.toggle("open");
    const items = btn.nextElementSibling;
    items.classList.toggle("open");
}

function openSidebar() {
    document.getElementById("sidebar").classList.add("open");
    document.getElementById("overlay").classList.add("open");
}

function closeSidebar() {
    document.getElementById("sidebar").classList.remove("open");
    document.getElementById("overlay").classList.remove("open");
}

// Highlight active nav item & auto-open its category
document.addEventListener("DOMContentLoaded", () => {
    const path = window.location.pathname;
    document.querySelectorAll(".nav-item").forEach(a => {
        if (a.getAttribute("href") === path) {
            a.classList.add("active");
            const items = a.closest(".nav-items");
            if (items) {
                items.classList.add("open");
                const btn = items.previousElementSibling;
                if (btn) btn.classList.add("open");
            }
        }
    });

    initTheme();
    initUploadZone();
    initToolForm();
    initDependentOptions();
    initCapabilityStatus();
});

async function initCapabilityStatus() {
    const box = document.getElementById("capability-status");
    if (!box) return;
    const endpoint = box.dataset.endpoint;
    if (!endpoint) return;
    try {
        const resp = await fetch("/capabilities");
        if (!resp.ok) return;
        const data = await resp.json();
        const status = data.routes && data.routes[endpoint];
        if (!status) return;
        box.className = "capability-status " + status.quality;
        box.style.display = "block";

        const missing = (status.missing_engines || [])
            .map(id => data.engines[id]?.label || id)
            .join(", ");
        const engines = (status.required_engines || [])
            .map(id => data.engines[id]?.label || id)
            .join(", ");
        const detail = status.quality === "high"
            ? `Using local high-fidelity engine${engines ? ": " + engines : ""}.`
            : status.quality === "basic"
                ? `High-fidelity engine missing${missing ? ": " + missing : ""}. ${status.fallback || ""}`
                : `Required local engine missing${missing ? ": " + missing : ""}.`;

        box.innerHTML = `
            <strong><i class="bi ${status.quality === "high" ? "bi-check-circle-fill" : "bi-exclamation-triangle-fill"}"></i> ${status.status}</strong>
            <span>${status.label}</span>
            <small>${detail}</small>
        `;
    } catch (_) {}
}


/* ── Upload Zone ──────────────────────────────── */
let selectedFiles = [];

function initUploadZone() {
    const zone = document.getElementById("upload-zone");
    const input = document.getElementById("file-input");
    if (!zone || !input) return;

    zone.addEventListener("dragover", e => { e.preventDefault(); zone.classList.add("dragover"); });
    zone.addEventListener("dragleave", () => zone.classList.remove("dragover"));
    zone.addEventListener("drop", e => {
        e.preventDefault();
        zone.classList.remove("dragover");
        addFiles(e.dataTransfer.files);
    });

    input.addEventListener("change", () => {
        addFiles(input.files);
        input.value = "";
    });
}

function addFiles(fileList) {
    const input = document.getElementById("file-input");
    const isMultiple = input && input.hasAttribute("multiple");

    if (isMultiple) {
        selectedFiles.push(...Array.from(fileList));
    } else {
        selectedFiles = [fileList[0]];
    }
    renderFileList();
}

function removeFile(idx) {
    selectedFiles.splice(idx, 1);
    renderFileList();
}

function renderFileList() {
    const list = document.getElementById("file-list");
    const prompt = document.getElementById("upload-prompt");
    if (!list) return;

    if (selectedFiles.length === 0) {
        list.innerHTML = "";
        if (prompt) prompt.style.display = "";
        return;
    }
    if (prompt) prompt.style.display = "none";

    list.innerHTML = selectedFiles.map((f, i) => `
        <div class="file-item">
            <span><i class="bi bi-file-earmark"></i> ${f.name}
            <small>(${formatSize(f.size)})</small></span>
            <button type="button" class="remove-file" onclick="removeFile(${i})">&times;</button>
        </div>
    `).join("");
}

function formatSize(bytes) {
    if (bytes < 1024) return bytes + " B";
    if (bytes < 1048576) return (bytes / 1024).toFixed(1) + " KB";
    return (bytes / 1048576).toFixed(1) + " MB";
}


/* ── Form Submission ──────────────────────────── */
function initToolForm() {
    const form = document.getElementById("tool-form");
    if (!form) return;

    form.addEventListener("submit", async (e) => {
        e.preventDefault();
        const endpoint = form.dataset.endpoint;
        if (!endpoint) return;

        const btnText = document.querySelector(".btn-text");
        const btnLoad = document.querySelector(".btn-loading");
        const submitBtn = document.getElementById("submit-btn");
        const resultArea = document.getElementById("result-area");

        // Validate: either files or text input required
        const textInput = form.querySelector("textarea[name='text']");
        if (!textInput && selectedFiles.length === 0) {
            showError("Please select a file first.");
            return;
        }
        if (textInput && !textInput.value.trim()) {
            showError("Please enter some text.");
            return;
        }

        // Show loading
        if (btnText) btnText.style.display = "none";
        if (btnLoad) btnLoad.style.display = "inline-flex";
        submitBtn.disabled = true;
        resultArea.style.display = "none";

        const formData = new FormData(form);

        // Remove the empty file input and add our tracked files
        formData.delete("files");
        selectedFiles.forEach(f => formData.append("files", f));

        try {
            const resp = await fetch(endpoint, { method: "POST", body: formData });

            if (!resp.ok) {
                let msg = "Processing failed.";
                try {
                    const json = await resp.json();
                    msg = json.error || msg;
                } catch (_) {}
                showError(msg);
                return;
            }

            const ct = resp.headers.get("Content-Type") || "";

            if (ct.includes("application/json")) {
                const json = await resp.json();
                if (json.error) {
                    showError(json.error);
                } else if (json.text !== undefined) {
                    showTextResult(json.text);
                } else if (json.data !== undefined) {
                    showTextResult(typeof json.data === "string" ? json.data : JSON.stringify(json.data, null, 2));
                }
            } else {
                // Binary file download
                const blob = await resp.blob();
                const cd = resp.headers.get("Content-Disposition") || "";
                let filename = "download";
                const match = cd.match(/filename="?([^";\n]+)"?/);
                if (match) filename = match[1];

                const url = URL.createObjectURL(blob);

                // If image, show preview
                const meta = {
                    engine: resp.headers.get("X-Conversion-Engine") || "",
                    quality: resp.headers.get("X-Conversion-Quality") || "",
                    warnings: resp.headers.get("X-Fidelity-Warnings") || ""
                };

                if (ct.startsWith("image/")) {
                    showFileResult(url, filename, true, meta);
                } else {
                    showFileResult(url, filename, false, meta);
                }
            }
        } catch (err) {
            showError("Network error: " + err.message);
        } finally {
            if (btnText) btnText.style.display = "";
            if (btnLoad) btnLoad.style.display = "none";
            submitBtn.disabled = false;
        }
    });
}

function showError(msg) {
    const area = document.getElementById("result-area");
    area.style.display = "block";
    document.getElementById("result-success").style.display = "none";
    document.getElementById("result-text")?.style.setProperty("display", "none");
    const errEl = document.getElementById("result-error");
    errEl.style.display = "flex";
    document.getElementById("error-message").textContent = msg;
}

function showFileResult(url, filename, isImage, meta = {}) {
    const area = document.getElementById("result-area");
    area.style.display = "block";
    document.getElementById("result-error").style.display = "none";
    document.getElementById("result-text")?.style.setProperty("display", "none");

    const success = document.getElementById("result-success");
    success.style.display = "flex";
    document.getElementById("result-message").textContent = "File ready!";

    const btn = document.getElementById("download-btn");
    btn.href = url;
    btn.download = filename;
    btn.textContent = "";
    btn.innerHTML = '<i class="bi bi-download"></i> Download ' + filename;

    const preview = document.getElementById("result-preview");
    if (isImage) {
        preview.style.display = "block";
        preview.innerHTML = `<img src="${url}" alt="Preview">`;
    } else {
        preview.style.display = "none";
    }

    const oldMeta = success.querySelector(".result-meta");
    if (oldMeta) oldMeta.remove();
    if (meta.engine || meta.quality || meta.warnings) {
        const div = document.createElement("div");
        div.className = "result-meta";
        const parts = [];
        if (meta.engine) parts.push(`<span>Engine: ${escapeHtml(meta.engine)}</span>`);
        if (meta.quality) parts.push(`<span>Quality: ${escapeHtml(meta.quality)}</span>`);
        if (meta.warnings) parts.push(`<span>Warnings: ${escapeHtml(meta.warnings)}</span>`);
        div.innerHTML = parts.join("");
        success.appendChild(div);
    }
}

function showTextResult(text) {
    const area = document.getElementById("result-area");
    area.style.display = "block";
    document.getElementById("result-error").style.display = "none";
    document.getElementById("result-success").style.display = "none";

    const textBox = document.getElementById("result-text");
    if (textBox) {
        textBox.style.display = "block";
        document.getElementById("result-text-content").textContent = text;
    }
}

function copyResult() {
    const text = document.getElementById("result-text-content")?.textContent;
    if (text) navigator.clipboard.writeText(text);
}

function escapeHtml(text) {
    return String(text).replace(/[&<>"']/g, c => ({
        "&": "&amp;",
        "<": "&lt;",
        ">": "&gt;",
        '"': "&quot;",
        "'": "&#39;"
    }[c]));
}


/* ── Dependent Options ────────────────────────── */
function initDependentOptions() {
    document.querySelectorAll("[data-depends-on]").forEach(el => {
        const parentName = el.dataset.dependsOn;
        const requiredVal = el.dataset.dependsValue;
        const parentInput = document.querySelector(`[name="${parentName}"]`);
        if (!parentInput) return;

        const check = () => {
            // Support comma-separated values
            const vals = requiredVal.split(",");
            el.style.display = vals.includes(parentInput.value) ? "" : "none";
        };
        parentInput.addEventListener("change", check);
        check();
    });
}
