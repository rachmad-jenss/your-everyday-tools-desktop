/* ── Theme ────────────────────────────────────── */
const THEME_KEY = "theme";

/* Shared Tailwind class strings for JS-rendered UI */
const TW = {
    badgeSuccess: "inline-flex items-center gap-1 rounded-full border-0 bg-emerald-50 px-2 py-0.5 text-[0.72rem] font-semibold leading-snug text-emerald-700 dark:bg-emerald-950/40 dark:text-emerald-300",
    badgeWarning: "inline-flex items-center gap-1 rounded-full border-0 bg-amber-50 px-2 py-0.5 text-[0.72rem] font-semibold leading-snug text-amber-700 dark:bg-amber-950/40 dark:text-amber-300",
    badgeDefault: "inline-flex items-center gap-1 rounded-full border border-border bg-bg px-2 py-0.5 text-[0.72rem] font-semibold leading-snug text-text-muted",
    toolCard: "tool-card relative flex items-start gap-3 rounded-xl border border-border-light bg-surface p-4 shadow-sm transition hover:-translate-y-px hover:border-border hover:shadow-md",
    toolCardDisabled: "tool-card relative flex items-start gap-3 rounded-xl border border-border-light bg-surface p-4 opacity-40 shadow-sm grayscale pointer-events-none",
    toolCardIcon: "card-icon flex h-10 w-10 shrink-0 items-center justify-center rounded-[10px] bg-primary-soft text-lg text-primary",
    pinBtn: "pin-btn absolute right-2.5 top-2.5 cursor-pointer rounded-md border-0 bg-transparent p-1 text-text-muted transition hover:bg-amber-50 hover:text-amber-600",
    pinBtnPinned: "pin-btn pinned absolute right-2.5 top-2.5 cursor-pointer rounded-md border-0 bg-transparent p-1 text-amber-600 transition hover:bg-amber-50",
    suggestedCard: "suggested-tool-card relative flex items-center gap-3 rounded-xl border border-border-light bg-surface p-4 text-text shadow-sm transition hover:border-border hover:shadow-md no-underline",
    recentFileRow: "recent-file-row flex items-center gap-3 rounded-xl border border-border-light bg-surface px-4 py-3 shadow-sm transition hover:border-border",
    paletteResult: "palette-result flex items-center gap-3 rounded-lg px-3 py-3 text-text no-underline transition hover:bg-primary-soft",
    paletteResultActive: "palette-result active flex items-center gap-3 rounded-lg bg-primary-soft px-3 py-3 text-text no-underline transition",
    paletteResultIcon: "palette-result-icon flex h-9 w-9 shrink-0 items-center justify-center rounded-lg bg-bg text-primary",
    paletteCatBadge: "inline-flex shrink-0 items-center gap-1 rounded-full border border-border bg-bg px-2 py-0.5 text-[0.72rem] font-semibold text-text-muted",
    toastBase: "pointer-events-auto flex min-w-[280px] max-w-[420px] items-center gap-3 rounded-md border border-border bg-surface px-4 py-3 text-sm shadow-lg animate-[toastIn_0.25s_ease]",
    toastSuccess: "border-l-[3px] border-l-success bg-emerald-50 dark:bg-emerald-950/30",
    toastError: "border-l-[3px] border-l-danger bg-red-50 dark:bg-red-950/30",
    toastWarning: "border-l-[3px] border-l-warning bg-amber-50 dark:bg-amber-950/30",
    toastInfo: "border-l-[3px] border-l-primary bg-primary-soft",
    inlineStatus: "inline-status inline-flex items-center gap-2 mt-3 text-sm leading-snug",
    inlineStatusSuccess: "text-emerald-700 dark:text-emerald-300",
    inlineStatusError: "text-danger",
    inlineStatusWarning: "text-amber-600 dark:text-amber-400",
    capabilityBase: "capability-status mb-4 rounded-md border px-4 py-3 text-sm leading-relaxed",
    capabilityHigh: "border-emerald-200 bg-emerald-50 text-emerald-900 dark:border-emerald-500/30 dark:bg-emerald-950/40 dark:text-emerald-200",
    capabilityBasic: "border-amber-200 bg-amber-50 text-amber-900 dark:border-amber-500/30 dark:bg-amber-950/40 dark:text-amber-200",
    capabilityUnavailable: "border-red-200 bg-red-50 text-red-900 dark:border-red-500/30 dark:bg-red-950/40 dark:text-red-200",
    modeBtn: "mode-btn inline-flex items-center justify-center rounded-xl bg-primary/15 px-4 py-2 text-sm font-medium text-primary transition hover:bg-primary/25",
    modeBtnOn: "mode-btn is-active inline-flex items-center justify-center rounded-xl bg-primary px-4 py-2 text-sm font-medium text-white shadow-sm transition",
    workspaceStatusBar: "workspace-status-bar border-t border-border-light px-6 py-3 text-sm font-medium",
};

function setStatusBadge(el, variant, text) {
    const map = { success: TW.badgeSuccess, warning: TW.badgeWarning, default: TW.badgeDefault };
    el.className = map[variant] || TW.badgeDefault;
    el.textContent = text;
}

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

    if (animate) html.classList.add("theme-animate");

    const resolved = resolveTheme(mode);
    html.dataset.theme = resolved;

    if (window.electronAPI && typeof window.electronAPI.setTheme === "function") {
        window.electronAPI.setTheme(mode, resolved);
    }

    document.querySelectorAll(".theme-btn").forEach(btn => {
        btn.classList.toggle("active", btn.dataset.themeMode === mode);
    });

    document.querySelectorAll(".settings-theme-btn").forEach(btn => {
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
            const icon = btn.querySelector("i");
            if (icon) {
                btn.classList.remove("spinning");
                void btn.offsetWidth;
                btn.classList.add("spinning");
                setTimeout(() => btn.classList.remove("spinning"), 380);
            }
            applyTheme(btn.dataset.themeMode, true);
        });
    });
    if (window.matchMedia) {
        window.matchMedia("(prefers-color-scheme: dark)").addEventListener("change", () => {
            if (getStoredTheme() === "system") {
                const resolved = resolveTheme("system");
                document.documentElement.dataset.theme = resolved;
                if (window.electronAPI && typeof window.electronAPI.setTheme === "function") {
                    window.electronAPI.setTheme("system", resolved);
                }
            }
        });
    }
}

function initElectronDesktop() {
    if (!window.electronAPI || !window.electronAPI.isDesktop) return;
    document.body.classList.add("electron-desktop");
    document.documentElement.classList.add("electron-desktop");
    const titleBar = document.getElementById("title-bar");
    const menuBar = document.getElementById("electron-menu-bar");
    const chromeBrand = document.getElementById("chrome-sidebar-brand");
    if (titleBar) titleBar.hidden = false;
    if (chromeBrand) chromeBrand.hidden = false;
    if (menuBar) {
        menuBar.hidden = false;
        menuBar.classList.remove("hidden");
    }
    document.querySelectorAll(".electron-menu-item").forEach((btn) => {
        btn.addEventListener("click", () => {
            if (typeof window.electronAPI.openAppMenu === "function") {
                window.electronAPI.openAppMenu(btn.dataset.menuLabel);
            }
        });
    });
}

/* ── Sidebar ──────────────────────────────────── */
function openSidebar() {
    document.getElementById("sidebar").classList.add("open");
    document.getElementById("overlay").classList.add("open");
}

function closeSidebar() {
    document.getElementById("sidebar").classList.remove("open");
    document.getElementById("overlay").classList.remove("open");
}

const SidebarUI = {
    refreshFavorites() {
        const container = document.getElementById("sidebar-favorites");
        if (!container || typeof Favorites === "undefined") return;
        const all = Favorites.getAll();
        const favs = all.slice(0, 5);
        const path = window.location.pathname;

        if (favs.length === 0) {
            container.innerHTML = `<p class="px-3 py-1.5 text-[0.75rem] text-text-muted">Klik bintang di tool untuk pin di sini.</p>`;
            return;
        }

        let html = favs.map(f => {
            const active = path === f.href;
            const activeCls = active ? " !bg-primary-soft !text-primary font-medium" : "";
            return `
            <a href="${f.href}" class="sidebar-mini-link flex items-center gap-2 rounded-md px-3 py-1.5 text-[0.8rem] text-text-muted no-underline hover:bg-bg-subtle hover:text-text${activeCls}">
                <i class="bi ${f.icon || "bi-tools"} shrink-0 text-primary"></i>
                <span class="min-w-0 truncate">${escapeHtml(f.name)}</span>
                <i class="bi bi-star-fill ml-auto shrink-0 text-[0.65rem] text-amber-600" aria-hidden="true"></i>
            </a>
        `;
        }).join("");

        if (all.length > 5) {
            html += `
            <a href="/favorites" class="sidebar-mini-link flex items-center gap-2 rounded-md px-3 py-1.5 text-[0.75rem] text-primary no-underline hover:bg-bg-subtle">
                Lihat semua (${all.length})
            </a>
        `;
        }

        container.innerHTML = html;
    },
    refreshRecent() {
        const container = document.getElementById("sidebar-recent");
        if (!container || typeof RecentActivity === "undefined") return;
        const recent = RecentActivity.getRecentTools().slice(0, 3);
        container.innerHTML = recent.map(t => `
            <a href="${t.href}" class="sidebar-mini-link flex items-center gap-2 rounded-md px-3 py-1.5 text-[0.8rem] text-text-muted no-underline hover:bg-bg hover:text-text">
                <i class="bi ${t.icon || 'bi-clock'} text-primary"></i>
                <span>${escapeHtml(t.name)}</span>
            </a>
        `).join("");
    },
    init() {
        this.refreshFavorites();
        this.refreshRecent();
        window.addEventListener("everytools:favorites-changed", () => this.refreshFavorites());
        window.addEventListener("everytools:recent-changed", () => this.refreshRecent());
    },
};

/* ── Toast ────────────────────────────────────── */
function showToast(message, type = "info", duration = 3500) {
    const container = document.getElementById("toast-container");
    if (!container) return;
    const toast = document.createElement("div");
    const typeClass = {
        success: TW.toastSuccess,
        error: TW.toastError,
        warning: TW.toastWarning,
        info: TW.toastInfo,
    }[type] || TW.toastInfo;
    toast.className = `${TW.toastBase} ${typeClass}`;
    const icons = { success: "check-circle-fill", error: "x-circle-fill", warning: "exclamation-triangle-fill", info: "info-circle-fill" };
    toast.innerHTML = `<i class="bi bi-${icons[type] || icons.info}"></i><span>${escapeHtml(message)}</span>`;
    container.appendChild(toast);
    setTimeout(() => {
        toast.style.opacity = "0";
        toast.style.transform = "translateY(8px)";
        toast.style.transition = "opacity .2s, transform .2s";
        setTimeout(() => toast.remove(), 200);
    }, duration);
}

/* ── Workspace status ─────────────────────────── */
function updateWorkspaceStatus(text, state = "idle") {
    const bar = document.getElementById("workspace-status-bar");
    const badge = document.getElementById("workspace-ready-badge");
    if (bar) {
        bar.textContent = text;
        bar.className = `${TW.workspaceStatusBar} ${state}`;
    }
    if (badge) {
        const badgeBase = "workspace-ready-badge inline-flex items-center gap-1 rounded-full px-2 py-0.5 text-xs font-medium";
        if (state === "success") {
            badge.className = `${badgeBase} bg-emerald-50 text-emerald-700 dark:bg-emerald-950/40 dark:text-emerald-300`;
            badge.innerHTML = '<i class="bi bi-check-circle-fill text-[0.7rem]"></i> Done';
        } else if (state === "error") {
            badge.className = `${badgeBase} bg-red-50 text-danger dark:bg-red-950/40`;
            badge.innerHTML = '<i class="bi bi-x-circle-fill text-[0.7rem]"></i> Error';
        } else if (state === "processing") {
            badge.className = `${badgeBase} bg-primary-soft text-primary`;
            badge.innerHTML = '<i class="bi bi-arrow-repeat spin text-[0.7rem]"></i> Working';
        } else {
            badge.className = `${badgeBase} bg-bg-subtle text-text-muted`;
            badge.innerHTML = '<i class="bi bi-circle-fill text-[0.45rem]"></i> Ready';
        }
    }
}

function isElementVisible(el) {
    if (!el || el.hidden) return false;
    return getComputedStyle(el).display !== "none";
}

function resetWorkspacePreview() {
    const empty = document.getElementById("workspace-preview-empty");
    const area = document.getElementById("result-area");
    const grid = document.getElementById("workspace-preview-grid");
    const toolbar = document.getElementById("preview-toolbar");
    const previewDl = document.getElementById("preview-download-btn");
    const viewToggle = document.getElementById("preview-view-toggle");
    const zoomWrap = document.getElementById("preview-zoom-wrap");
    outputPreviewMode = null;
    if (empty) {
        empty.hidden = false;
        const icon = empty.querySelector("i");
        const p = empty.querySelector("p");
        if (icon) icon.className = "bi bi-eye text-3xl opacity-50";
        if (p) p.textContent = "Output preview will appear here after you convert.";
    }
    if (area) {
        area.classList.add("hidden");
        area.style.removeProperty("display");
    }
    if (grid) {
        grid.hidden = true;
        grid.innerHTML = "";
        grid.classList.remove("is-list");
    }
    if (toolbar) toolbar.hidden = true;
    if (previewDl) previewDl.classList.add("hidden");
    if (viewToggle) viewToggle.hidden = true;
    if (zoomWrap) zoomWrap.hidden = true;
    revokePreviewUrls();
    updateUploadPreviewUI();
    updateWorkspaceStatus("Ready", "idle");
}

function setWorkspaceProcessing(message = "Processing…") {
    const empty = document.getElementById("workspace-preview-empty");
    const area = document.getElementById("result-area");
    if (area) {
        area.classList.add("hidden");
        area.style.removeProperty("display");
    }
    if (empty) {
        empty.hidden = false;
        const p = empty.querySelector("p");
        if (p) p.textContent = message;
    }
    updateWorkspaceStatus(message, "processing");
}

function getTimeGreeting() {
    const h = new Date().getHours();
    if (h >= 5 && h < 12) return "Good morning";
    if (h >= 12 && h < 17) return "Good afternoon";
    if (h >= 17 && h < 22) return "Good evening";
    return "Good night";
}

function initGreeting() {
    const el = document.getElementById("dashboard-greeting");
    if (el) el.textContent = getTimeGreeting();
}

function showWorkspaceOutput() {
    const empty = document.getElementById("workspace-preview-empty");
    const area = document.getElementById("result-area");
    if (empty) empty.hidden = true;
    if (area) {
        area.classList.remove("hidden");
        area.style.display = "block";
    }
}

function setInlineStatus(el, message, type = "success") {
    if (!el) return;
    const icon = type === "error" ? "bi-x-circle" : type === "warning" ? "bi-exclamation-circle" : "bi-check-circle";
    const tone = {
        success: TW.inlineStatusSuccess,
        error: TW.inlineStatusError,
        warning: TW.inlineStatusWarning,
    }[type] || TW.inlineStatusSuccess;
    el.className = `${TW.inlineStatus} ${tone}`;
    el.innerHTML = `<i class="bi ${icon}"></i> ${escapeHtml(message)}`;
}

/* ── Component status ─────────────────────────── */
const COMPONENT_IDS = ["ffmpeg", "tesseract"];

async function initComponentStatus() {
    const badges = document.querySelectorAll("[data-component]");
    const summary = document.getElementById("components-summary");
    const dot = document.getElementById("components-status-dot");
    if (!badges.length && !summary) return;
    try {
        const resp = await fetch("/capabilities");
        if (!resp.ok) return;
        const data = await resp.json();
        const engines = data.engines || {};
        let missing = 0;
        COMPONENT_IDS.forEach(id => {
            const engine = engines[id];
            const installed = engine && engine.available;
            if (!installed) missing++;
            document.querySelectorAll(`[data-component="${id}"]`).forEach(badge => {
                setStatusBadge(badge, installed ? "success" : "warning", installed ? "Installed" : "Not installed");
            });
            updateComponentActions(id, installed, engine);
        });
        if (summary) {
            if (missing === 0) summary.textContent = "All installed";
            else if (missing === 1) summary.textContent = "1 update available";
            else summary.textContent = `${missing} updates available`;
        }
        if (dot) {
            dot.className = "sidebar-components-dot absolute right-3 top-3 h-2 w-2 rounded-full " + (missing === 0 ? "bg-success" : "bg-warning");
        }
    } catch (_) {
        badges.forEach(badge => setStatusBadge(badge, "default", "Unknown"));
        if (summary) summary.textContent = "Status unavailable";
        if (dot) dot.className = "sidebar-components-dot absolute right-3 top-3 h-2 w-2 rounded-full bg-text-muted/40";
    }
}

function updateComponentActions(id, installed, engine) {
    const isDesktop = !!(window.electronAPI && typeof window.electronAPI.openComponentManager === "function");
    document.querySelectorAll(`[data-component-action][data-component-id="${id}"]`).forEach(btn => {
        const action = btn.dataset.componentAction;
        if (action === "manage") {
            btn.classList.toggle("hidden", !(isDesktop && installed));
        } else if (action === "install") {
            btn.classList.toggle("hidden", installed);
            btn.textContent = isDesktop ? "Install" : "Install guide";
        }
    });
    const hint = document.querySelector(`[data-component-hint="${id}"]`);
    if (hint && engine?.install_hint) {
        hint.classList.remove("hidden");
        const text = hint.querySelector(".component-hint-text");
        if (text) text.textContent = engine.install_hint;
    }
}

/* ── Capability status (per tool) ───────────────── */
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
        const qualityClass = {
            high: TW.capabilityHigh,
            basic: TW.capabilityBasic,
            unavailable: TW.capabilityUnavailable,
        }[status.quality] || TW.capabilityBase;
        box.className = `${TW.capabilityBase} ${qualityClass}`;
        box.classList.remove("hidden");

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
            <strong class="mr-2 inline-flex items-center gap-2 font-semibold"><i class="bi ${status.quality === "high" ? "bi-check-circle-fill" : "bi-exclamation-triangle-fill"}"></i> ${status.status}</strong>
            <span>${status.label}</span>
            <small class="mt-1 block opacity-85">${detail}</small>
        `;
    } catch (_) {}
}

/* ── Upload Zone ──────────────────────────────── */
let selectedFiles = [];
let previewObjectUrls = [];
let previewZoom = 100;
let previewView = "grid";
let outputPreviewMode = null; // null | "pdf" | "images" | "image"

let outputResultUrl = null;

function revokeInputPreviewUrls() {
    previewObjectUrls.forEach(u => URL.revokeObjectURL(u));
    previewObjectUrls = [];
}

function revokePreviewUrls() {
    revokeInputPreviewUrls();
    if (outputResultUrl) {
        URL.revokeObjectURL(outputResultUrl);
        outputResultUrl = null;
    }
}

function toggleStepAccordion(btn) {
    const acc = btn.parentElement;
    acc.classList.toggle("open");
    btn.setAttribute("aria-expanded", acc.classList.contains("open") ? "true" : "false");
}

function clearAllFiles() {
    selectedFiles = [];
    renderFileList();
}

function initUploadZone() {
    const zone = document.getElementById("upload-zone");
    const input = document.getElementById("file-input");
    const addMore = document.getElementById("upload-add-more");
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

    if (addMore) {
        addMore.addEventListener("click", () => input.click());
    }
}

function addFiles(fileList) {
    const input = document.getElementById("file-input");
    const isMultiple = input && input.hasAttribute("multiple");

    if (isMultiple) selectedFiles.push(...Array.from(fileList));
    else selectedFiles = [fileList[0]];

    renderFileList();
}

function removeFile(idx) {
    selectedFiles.splice(idx, 1);
    renderFileList();
}

function countPreviewPages(files) {
    const images = files.filter(f => f.type.startsWith("image/"));
    return images.length || files.length;
}

function formatUploadStatus(files) {
    const n = files.length;
    if (n === 0) return { bar: "Ready", state: "idle", pages: 0 };
    const images = files.filter(f => f.type.startsWith("image/"));
    const pages = countPreviewPages(files);
    const unit = images.length ? "image" : "file";
    const count = images.length || n;
    const bar = `Ready to convert · ${count} ${unit}${count !== 1 ? "s" : ""} · ${pages} page${pages !== 1 ? "s" : ""}`;
    return { bar, state: "idle", pages };
}

function setPreviewToolbarVisible(showDownload, mode) {
    const toolbar = document.getElementById("preview-toolbar");
    const previewDl = document.getElementById("preview-download-btn");
    const viewToggle = document.getElementById("preview-view-toggle");
    const zoomWrap = document.getElementById("preview-zoom-wrap");
    if (toolbar) toolbar.hidden = false;
    if (previewDl) previewDl.classList.toggle("hidden", !showDownload);
    const showImageControls = mode === "images";
    if (viewToggle) viewToggle.hidden = !showImageControls;
    if (zoomWrap) zoomWrap.hidden = !showImageControls;
}

function renderOutputImageGrid(urls) {
    const grid = document.getElementById("workspace-preview-grid");
    if (!grid) return;
    grid.classList.toggle("is-list", previewView === "list");
    grid.style.setProperty("--preview-zoom", previewZoom / 100);
    grid.innerHTML = urls.map((url, i) => `
        <div class="preview-grid-item relative overflow-hidden rounded-md border border-border bg-bg-subtle">
            <div class="preview-grid-thumb overflow-hidden"><img src="${url}" alt="Page ${i + 1}" class="h-full w-full object-contain"></div>
            <span class="preview-grid-label absolute bottom-1 right-1 rounded bg-black/60 px-1.5 py-0.5 text-[0.65rem] font-semibold text-white">${i + 1}</span>
        </div>`).join("");
}

function showOutputPreview(url, contentType, filename, extraUrls) {
    const empty = document.getElementById("workspace-preview-empty");
    const grid = document.getElementById("workspace-preview-grid");
    if (empty) empty.hidden = true;
    if (!grid) return;

    revokeInputPreviewUrls();
    grid.hidden = false;

    if (contentType.includes("pdf")) {
        outputPreviewMode = "pdf";
        grid.classList.remove("is-list");
        grid.innerHTML = `<iframe src="${url}" class="preview-pdf-frame h-[min(70vh,640px)] w-full rounded-lg border border-border bg-white" title="PDF preview of ${escapeHtml(filename)}"></iframe>`;
        setPreviewToolbarVisible(true, "pdf");
        return;
    }

    if (contentType.startsWith("image/") && !extraUrls) {
        outputPreviewMode = "image";
        grid.classList.remove("is-list");
        grid.innerHTML = `<div class="preview-single-image flex min-h-[320px] items-center justify-center rounded-lg border border-border bg-bg-subtle p-4"><img src="${url}" alt="${escapeHtml(filename)}" class="max-h-[min(70vh,640px)] max-w-full object-contain"></div>`;
        setPreviewToolbarVisible(true, "image");
        return;
    }

    const urls = extraUrls && extraUrls.length ? extraUrls : [url];
    outputPreviewMode = "images";
    renderOutputImageGrid(urls);
    setPreviewToolbarVisible(true, "images");
}

function updateUploadPreviewUI() {
    const empty = document.getElementById("workspace-preview-empty");
    const pageCount = document.getElementById("workspace-page-count");
    const resultArea = document.getElementById("result-area");
    const hasResult = isElementVisible(resultArea);

    if (hasResult) return;

    if (pageCount) {
        if (selectedFiles.length === 0) {
            pageCount.hidden = true;
        } else {
            const status = formatUploadStatus(selectedFiles);
            pageCount.textContent = `${status.pages} page${status.pages !== 1 ? "s" : ""}`;
            pageCount.hidden = false;
        }
    }

    if (selectedFiles.length === 0) {
        if (empty) {
            empty.hidden = false;
            const p = empty.querySelector("p");
            if (p) p.textContent = "Output preview will appear here after you convert.";
        }
        updateWorkspaceStatus("Ready", "idle");
        return;
    }

    const status = formatUploadStatus(selectedFiles);
    updateWorkspaceStatus(status.bar, status.state);
    if (empty) {
        empty.hidden = false;
        const icon = empty.querySelector("i");
        const p = empty.querySelector("p");
        if (icon) icon.className = "bi bi-eye text-3xl opacity-50";
        if (p) {
            p.textContent = `${selectedFiles.length} file${selectedFiles.length !== 1 ? "s" : ""} ready — click Convert to preview the output.`;
        }
    }
}

function initWorkspacePreview() {
    document.querySelectorAll("[data-preview-view]").forEach(btn => {
        btn.addEventListener("click", () => {
            previewView = btn.dataset.previewView;
            document.querySelectorAll("[data-preview-view]").forEach(b => b.classList.toggle("active", b === btn));
            if (outputPreviewMode === "images") {
                const grid = document.getElementById("workspace-preview-grid");
                if (grid) {
                    grid.classList.toggle("is-list", previewView === "list");
                }
            }
        });
    });
    document.querySelectorAll("[data-zoom-delta]").forEach(btn => {
        btn.addEventListener("click", () => {
            previewZoom = Math.min(150, Math.max(50, previewZoom + Number(btn.dataset.zoomDelta)));
            const label = document.getElementById("preview-zoom-label");
            if (label) label.textContent = previewZoom + "%";
            const grid = document.getElementById("workspace-preview-grid");
            if (grid && outputPreviewMode === "images") {
                grid.style.setProperty("--preview-zoom", previewZoom / 100);
            }
        });
    });
}

function renderFileList() {
    const list = document.getElementById("file-list");
    const prompt = document.getElementById("upload-prompt");
    const hint = document.getElementById("upload-hint");
    const zone = document.getElementById("upload-zone");
    const addMore = document.getElementById("upload-add-more");
    const input = document.getElementById("file-input");
    const isMultiple = input && input.hasAttribute("multiple");
    if (!list) return;

    if (selectedFiles.length === 0) {
        list.innerHTML = "";
        if (prompt) prompt.style.display = "";
        if (hint) {
            hint.textContent = "Up to 100 MB per file";
            hint.style.display = "";
        }
        if (zone) zone.classList.remove("hidden");
        if (addMore) addMore.classList.add("hidden");
        revokePreviewUrls();
        updateUploadPreviewUI();
        return;
    }
    if (prompt) prompt.style.display = "none";
    if (hint) hint.style.display = "none";
    if (zone) zone.classList.add("hidden");
    if (addMore && isMultiple) addMore.classList.remove("hidden");

    const count = selectedFiles.length;
    const showTip = count > 1 && selectedFiles.every(f => f.type.startsWith("image/"));
    list.innerHTML = `
    <div class="file-list-card mt-3 overflow-hidden rounded-md border border-border bg-surface">
        <div class="file-list-header flex items-center justify-between border-b border-border-light px-4 py-3 text-sm font-semibold">
            <span>${count} file${count !== 1 ? "s" : ""} selected</span>
            <button type="button" class="inline-flex items-center rounded-md px-2.5 py-1 text-xs font-medium text-text-muted transition hover:bg-bg-subtle hover:text-text" onclick="clearAllFiles()">Clear all</button>
        </div>
        <div class="file-list-items p-2">
        ${selectedFiles.map((f, i) => {
        const isImage = f.type.startsWith("image/");
        const thumb = isImage
            ? `<img src="${URL.createObjectURL(f)}" alt="" class="file-thumb-img h-10 w-10 shrink-0 rounded-md object-cover">`
            : `<div class="file-thumb flex h-10 w-10 shrink-0 items-center justify-center rounded-md bg-bg-subtle text-primary"><i class="bi bi-file-earmark"></i></div>`;
        return `
        <div class="file-item flex items-center justify-between gap-2 rounded-md px-2 py-2 hover:bg-bg-subtle">
            <div class="file-item-info flex min-w-0 items-center gap-3">
                ${thumb}
                <span class="file-item-name truncate text-sm font-medium">${escapeHtml(f.name)}</span>
            </div>
            <button type="button" class="remove-file flex h-7 w-7 shrink-0 items-center justify-center rounded border-0 bg-transparent text-lg text-text-muted hover:bg-border hover:text-text" onclick="removeFile(${i})" aria-label="Remove">&times;</button>
        </div>`;
    }).join("")}
        </div>
        ${showTip ? `<div class="file-list-tip mx-3 mb-3 mt-2 flex items-start gap-2 rounded-lg border border-border bg-bg-subtle p-3 text-sm leading-snug text-text-muted"><i class="bi bi-lightbulb text-primary"></i> Tip: images are combined in the order shown above.</div>` : ""}
    </div>`;

    updateUploadPreviewUI();
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

        const textInput = form.querySelector("textarea[name='text']");
        if (!textInput && selectedFiles.length === 0) {
            showError("Please select a file first.");
            showToast("Please select a file first.", "warning");
            return;
        }
        if (textInput && !textInput.value.trim()) {
            showError("Please enter some text.");
            showToast("Please enter some text.", "warning");
            return;
        }

        if (btnText) btnText.style.display = "none";
        if (btnLoad) btnLoad.style.display = "inline-flex";
        submitBtn.disabled = true;
        setWorkspaceProcessing("Processing…");

        const formData = new FormData(form);
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
                showToast(msg, "error");
                return;
            }

            const ct = resp.headers.get("Content-Type") || "";

            if (ct.includes("application/json")) {
                const json = await resp.json();
                if (json.error) {
                    showError(json.error);
                    showToast(json.error, "error");
                } else if (json.text !== undefined) {
                    showTextResult(json.text);
                    showToast("Done!", "success");
                } else if (json.data !== undefined) {
                    showTextResult(typeof json.data === "string" ? json.data : JSON.stringify(json.data, null, 2));
                    showToast("Done!", "success");
                } else {
                    showError("Unexpected response from server.");
                    showToast("Unexpected response from server.", "error");
                }
            } else {
                const blob = await resp.blob();
                const cd = resp.headers.get("Content-Disposition") || "";
                let filename = "download";
                const match = cd.match(/filename="?([^";\n]+)"?/);
                if (match) filename = match[1];

                const url = URL.createObjectURL(blob);
                showFileResult(url, filename, {
                    engine: resp.headers.get("X-Conversion-Engine") || "",
                    quality: resp.headers.get("X-Conversion-Quality") || "",
                    warnings: resp.headers.get("X-Fidelity-Warnings") || "",
                    contentType: ct,
                });
                showToast("File ready for download!", "success");

                if (typeof RecentActivity !== "undefined") {
                    const path = window.location.pathname;
                    const tool = (window.__TOOL_INDEX__ || []).find(t => t.href === path);
                    RecentActivity.trackToolExecuted(tool || { href: path, name: document.title });
                    RecentActivity.trackFileProcessed({
                        name: filename,
                        size: blob.size,
                        toolHref: path,
                        toolName: tool ? tool.name : "",
                    });
                }
            }
        } catch (err) {
            showError("Network error: " + err.message);
            showToast("Network error: " + err.message, "error");
        } finally {
            if (btnText) btnText.style.display = "";
            if (btnLoad) btnLoad.style.display = "none";
            submitBtn.disabled = false;
        }
    });
}

function showError(msg) {
    const grid = document.getElementById("workspace-preview-grid");
    const toolbar = document.getElementById("preview-toolbar");
    const empty = document.getElementById("workspace-preview-empty");
    const area = document.getElementById("result-area");
    const pageCount = document.getElementById("workspace-page-count");

    outputPreviewMode = null;
    if (grid) {
        grid.hidden = true;
        grid.innerHTML = "";
    }
    if (toolbar) toolbar.hidden = true;
    if (pageCount) pageCount.hidden = true;
    if (area) {
        area.classList.add("hidden");
        area.style.removeProperty("display");
        const errEl = document.getElementById("result-error");
        if (errEl) errEl.style.display = "none";
    }
    if (empty) {
        empty.hidden = false;
        const icon = empty.querySelector("i");
        const p = empty.querySelector("p");
        if (icon) {
            icon.className = "bi bi-exclamation-circle text-3xl text-danger";
        }
        if (p) p.textContent = msg;
    }
    updateWorkspaceStatus(msg, "error");
}

function showFileResult(url, filename, meta = {}) {
    if (outputResultUrl && outputResultUrl !== url) {
        URL.revokeObjectURL(outputResultUrl);
    }
    outputResultUrl = url;

    showWorkspaceOutput();
    const area = document.getElementById("result-area");
    area.style.display = "block";
    document.getElementById("result-error").style.display = "none";
    document.getElementById("result-text")?.style.setProperty("display", "none");

    const success = document.getElementById("result-success");
    const contentType = meta.contentType || "";
    const hasMeta = !!(meta.engine || meta.quality || meta.warnings);
    success.style.display = hasMeta ? "flex" : "none";
    document.getElementById("result-message").textContent = "Conversion complete";

    const previewDl = document.getElementById("preview-download-btn");
    if (previewDl) {
        previewDl.href = url;
        previewDl.download = filename;
        previewDl.innerHTML = '<i class="bi bi-download"></i> Download ' + escapeHtml(filename);
        previewDl.classList.remove("hidden");
    }

    showOutputPreview(url, contentType, filename);

    const preview = document.getElementById("result-preview");
    if (preview) {
        preview.style.display = "none";
        preview.innerHTML = "";
    }

    const oldMeta = success.querySelector(".result-meta");
    if (oldMeta) oldMeta.remove();
    if (hasMeta) {
        const div = document.createElement("div");
        div.className = "result-meta mt-3 text-xs text-text-muted";
        const parts = [];
        if (meta.engine) parts.push(`<span>Engine: ${escapeHtml(meta.engine)}</span>`);
        if (meta.quality) parts.push(`<span>Quality: ${escapeHtml(meta.quality)}</span>`);
        if (meta.warnings) parts.push(`<span>Warnings: ${escapeHtml(meta.warnings)}</span>`);
        div.innerHTML = parts.join(" · ");
        success.appendChild(div);
    }
    updateWorkspaceStatus(`Done · ${filename}`, "success");
}

function showTextResult(text) {
    showWorkspaceOutput();
    const area = document.getElementById("result-area");
    area.style.display = "block";
    document.getElementById("result-error").style.display = "none";
    document.getElementById("result-success").style.display = "none";

    const textBox = document.getElementById("result-text");
    if (textBox) {
        textBox.style.display = "block";
        document.getElementById("result-text-content").textContent = text;
    }
    updateWorkspaceStatus("Result ready", "success");
}

function copyResult() {
    const text = document.getElementById("result-text-content")?.textContent;
    if (text) {
        navigator.clipboard.writeText(text);
        showToast("Copied to clipboard", "success");
    }
}

function escapeHtml(text) {
    return String(text).replace(/[&<>"']/g, c => ({
        "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;"
    }[c]));
}

function initDependentOptions() {
    document.querySelectorAll("[data-depends-on]").forEach(el => {
        const parentName = el.dataset.dependsOn;
        const requiredVal = el.dataset.dependsValue;
        const parentInput = document.querySelector(`[name="${parentName}"]`);
        if (!parentInput) return;

        const check = () => {
            const vals = requiredVal.split(",");
            el.style.display = vals.includes(parentInput.value) ? "" : "none";
        };
        parentInput.addEventListener("change", check);
        check();
    });
}

function updateSidebarHighlight() {
    const path = window.location.pathname;
    const category = new URLSearchParams(window.location.search).get("category");
    const tool = (window.__TOOL_INDEX__ || []).find(t => t.href === path);

    document.querySelectorAll(".sidebar-link.active").forEach(el => el.classList.remove("active"));

    let target = null;
    if (tool) {
        target = document.querySelector(`a.sidebar-link[href="/tools?category=${tool.catId}"]`);
    } else if (path === "/tools" && category) {
        target = document.querySelector(`a.sidebar-link[href="/tools?category=${category}"]`);
    } else if (path === "/tools") {
        target = document.querySelector('a.sidebar-link[href="/tools"]');
    } else if (path === "/") {
        target = document.querySelector('a.sidebar-link[href="/"]');
    } else if (path === "/favorites") {
        target = document.querySelector('a.sidebar-link[href="/favorites"]');
    } else if (path === "/recent") {
        target = document.querySelector('a.sidebar-link[href="/recent"]');
    } else if (path === "/settings") {
        target = document.querySelector('a.sidebar-link[href="/settings"]');
    }
    if (target) target.classList.add("active");
}

function initBreadcrumbs() {
    const el = document.getElementById("top-breadcrumbs");
    const title = document.getElementById("top-title");
    if (!el) return;
    const path = window.location.pathname;
    const hideTitlePaths = ["/", "/tools", "/favorites", "/recent", "/settings"];
    const tool = (window.__TOOL_INDEX__ || []).find(t => t.href === path);

    if (tool) {
        el.hidden = false;
        el.className = "top-breadcrumbs flex min-w-0 shrink items-center gap-1.5 text-sm text-text-muted md:gap-2";
        el.innerHTML = `
            <a href="/tools?category=${tool.catId}" class="truncate text-text-muted no-underline hover:text-primary">${escapeHtml(tool.catName)}</a>
            <span class="sep shrink-0 text-xs text-text-muted/50" aria-hidden="true">›</span>
            <span class="current truncate font-semibold text-text">${escapeHtml(tool.name)}</span>
        `;
        if (title) title.classList.add("hidden");
    } else {
        el.hidden = true;
        el.innerHTML = "";
        if (title) {
            title.classList.remove("hidden");
            title.classList.toggle("hidden", hideTitlePaths.includes(path));
        }
    }

    updateSidebarHighlight();
}

/* ── Custom select (replaces native dropdown panel on Windows) ── */
function initCustomSelects() {
    const closeAllSelectMenus = exceptMenu => {
        document.querySelectorAll(".yet-select-menu.open").forEach(menu => {
            if (menu === exceptMenu) return;
            menu.classList.remove("open");
            menu.classList.add("hidden");
            menu.style.cssText = "";
            const wrap = menu._yetWrap;
            if (wrap && menu.parentElement === document.body) wrap.appendChild(menu);
            const trigger = menu._yetTrigger;
            if (trigger) {
                trigger.setAttribute("aria-expanded", "false");
                trigger.classList.remove("is-open");
            }
        });
    };

    document.querySelectorAll("select.yet-select:not([data-yet-enhanced])").forEach(select => {
        if (select.multiple || select.size > 1) return;
        select.dataset.yetEnhanced = "1";
        select.classList.add("sr-only");

        const wrap = document.createElement("div");
        wrap.className = "yet-select-wrap relative w-full";
        select.parentNode.insertBefore(wrap, select);
        wrap.appendChild(select);

        const trigger = document.createElement("button");
        trigger.type = "button";
        trigger.className = "yet-select-trigger flex w-full min-h-11 cursor-pointer items-center justify-between gap-3 rounded-lg border border-border bg-surface px-3.5 py-2.5 text-left text-sm text-text outline-none transition focus:border-primary focus:ring-[3px] focus:ring-primary/10";
        trigger.setAttribute("aria-haspopup", "listbox");
        trigger.setAttribute("aria-expanded", "false");

        const valueEl = document.createElement("span");
        valueEl.className = "yet-select-value min-w-0 flex-1 truncate";
        const chevron = document.createElement("i");
        chevron.className = "bi bi-chevron-down shrink-0 text-xs text-text-muted";
        trigger.append(valueEl, chevron);

        const menu = document.createElement("ul");
        menu.className = "yet-select-menu absolute left-0 right-0 z-[10050] mt-1 hidden max-h-60 list-none overflow-y-auto rounded-lg border border-border bg-surface p-1 shadow-lg";
        menu.setAttribute("role", "listbox");
        menu._yetWrap = wrap;
        menu._yetTrigger = trigger;

        const positionMenu = () => {
            const rect = trigger.getBoundingClientRect();
            menu.style.position = "fixed";
            menu.style.left = `${rect.left}px`;
            menu.style.top = `${rect.bottom + 4}px`;
            menu.style.width = `${rect.width}px`;
            menu.style.minWidth = `${rect.width}px`;
            menu.style.zIndex = "10050";
        };

        const syncValue = () => {
            const opt = select.options[select.selectedIndex];
            valueEl.textContent = opt ? opt.textContent : "";
            menu.querySelectorAll("[role=option]").forEach(li => {
                const selected = li.dataset.value === select.value;
                li.setAttribute("aria-selected", selected ? "true" : "false");
                li.classList.toggle("is-selected", selected);
            });
        };

        Array.from(select.options).forEach(opt => {
            const li = document.createElement("li");
            li.className = "yet-select-option cursor-pointer rounded-md px-3 py-2.5 text-sm text-text transition";
            li.dataset.value = opt.value;
            li.setAttribute("role", "option");
            li.textContent = opt.textContent;
            li.addEventListener("click", () => {
                select.value = opt.value;
                syncValue();
                closeMenu();
                select.dispatchEvent(new Event("change", { bubbles: true }));
            });
            menu.appendChild(li);
        });

        const closeMenu = () => {
            menu.classList.add("hidden");
            menu.classList.remove("open");
            menu.style.cssText = "";
            if (menu.parentElement === document.body) wrap.appendChild(menu);
            trigger.setAttribute("aria-expanded", "false");
            trigger.classList.remove("is-open");
        };

        const openMenu = () => {
            closeAllSelectMenus(menu);
            document.body.appendChild(menu);
            menu.classList.remove("hidden");
            menu.classList.add("open");
            positionMenu();
            trigger.setAttribute("aria-expanded", "true");
            trigger.classList.add("is-open");
        };

        trigger.addEventListener("click", e => {
            e.stopPropagation();
            if (menu.classList.contains("open")) closeMenu();
            else openMenu();
        });

        document.addEventListener("click", e => {
            if (!wrap.contains(e.target) && !menu.contains(e.target)) closeMenu();
        });

        window.addEventListener("resize", () => {
            if (menu.classList.contains("open")) positionMenu();
        });
        window.addEventListener("scroll", () => {
            if (menu.classList.contains("open")) positionMenu();
        }, true);

        select.addEventListener("change", syncValue);
        wrap.append(trigger, menu);
        syncValue();
    });
}

function syncChromeHeight() {
    const chrome = document.getElementById("app-chrome");
    if (!chrome) return;
    const apply = () => {
        const height = Math.ceil(chrome.getBoundingClientRect().height);
        if (height > 0) {
            document.documentElement.style.setProperty("--chrome-h", `${height}px`);
        }
    };
    apply();
    if (typeof ResizeObserver !== "undefined") {
        new ResizeObserver(apply).observe(chrome);
    }
}

/* ── Init ─────────────────────────────────────── */
document.addEventListener("DOMContentLoaded", () => {
    initTheme();
    initElectronDesktop();
    syncChromeHeight();
    initBreadcrumbs();
    initGreeting();
    initUploadZone();
    initToolForm();
    initWorkspacePreview();
    initDependentOptions();
    initCustomSelects();
    initCapabilityStatus();

    if (typeof Favorites !== "undefined") Favorites.init();
    if (typeof RecentActivity !== "undefined") RecentActivity.init();
    if (typeof SearchPalette !== "undefined") SearchPalette.init();
    SidebarUI.init();
});
