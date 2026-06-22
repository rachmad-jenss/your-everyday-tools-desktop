/**
 * Desktop auto-update UI — progress banner + Settings sync (Electron only).
 */
const DesktopUpdater = {
  state: { phase: "idle" },

  init() {
    const api = window.electronAPI;
    if (!api || typeof api.onUpdateStatus !== "function") {
      document.getElementById("settings-update-panel")?.classList.add("hidden");
      return;
    }

    this.banner = document.getElementById("app-update-banner");
    this.bindBannerActions();
    this.bindSettingsActions();

    api.onUpdateStatus((status) => this.apply(status));
  },

  bindBannerActions() {
    if (!this.banner) return;
    this.banner.addEventListener("click", (event) => {
      const btn = event.target.closest("[data-update-action]");
      if (!btn) return;
      this.handleAction(btn.dataset.updateAction);
    });
  },

  bindSettingsActions() {
    const panel = document.getElementById("settings-update-panel");
    if (!panel) return;
    panel.addEventListener("click", (event) => {
      const btn = event.target.closest("[data-update-action]");
      if (!btn) return;
      this.handleAction(btn.dataset.updateAction);
    });
  },

  async handleAction(action) {
    const api = window.electronAPI;
    if (!api) return;

    try {
      if (action === "check") {
        await api.checkForUpdates();
      } else if (action === "download") {
        await api.downloadUpdate({ background: false });
      } else if (action === "download-bg") {
        await api.downloadUpdate({ background: true });
      } else if (action === "install") {
        await api.installUpdate();
      } else if (action === "dismiss") {
        await api.dismissUpdateUi();
      } else if (action === "settings") {
        window.location.href = "/settings#updates";
      }
    } catch (err) {
      const message = err && err.message ? err.message : String(err);
      if (typeof showToast === "function") {
        showToast(message, "error", 5000);
      }
    }
  },

  apply(status) {
    this.state = status || { phase: "idle" };
    this.renderBanner();
    this.renderSettings();

    if (status?.phase === "up-to-date" && status.manual && typeof showToast === "function") {
      showToast(`Sudah versi terbaru (v${status.currentVersion || "?"}).`, "success");
    }
    if (status?.phase === "checking" && status.manual && typeof showToast === "function") {
      showToast("Mengecek update…", "info", 2000);
    }
    if (status?.phase === "downloaded" && (status.dismissed || status.background) && typeof showToast === "function") {
      showToast(`Update v${status.version || ""} siap diinstall. Buka Settings untuk restart.`, "success", 6000);
    }
    if (status?.phase === "error" && typeof showToast === "function") {
      showToast(status.message || "Update gagal.", "error", 6000);
    }
  },

  renderBanner() {
    const el = this.banner;
    if (!el) return;

    const s = this.state;
    const phase = s.phase || "idle";

    if (phase === "idle" || phase === "checking" || phase === "up-to-date") {
      el.classList.add("hidden");
      el.innerHTML = "";
      return;
    }

    if (phase === "downloading" && s.dismissed) {
      el.classList.add("hidden");
      el.innerHTML = "";
      return;
    }

    el.classList.remove("hidden");
    const compact = phase === "downloading" && s.background;
    const version = s.version ? `v${s.version}` : "";
    const pct = Math.max(0, Math.min(100, Math.round(s.percent || 0)));
    const progressText = this.formatProgress(s);

    if (compact) {
      el.innerHTML = `
        <div class="pointer-events-auto border-t border-border bg-surface/95 px-4 py-2 shadow-lg backdrop-blur-sm md:ml-[280px]">
          <div class="mx-auto flex max-w-[1200px] items-center gap-3">
            <div class="min-w-0 flex-1">
              <div class="mb-1 flex items-center justify-between gap-2 text-xs text-text-muted">
                <span>Download update ${version} di background</span>
                <span>${pct}% · ${progressText}</span>
              </div>
              <div class="h-1.5 overflow-hidden rounded-full bg-bg-subtle">
                <div class="h-full rounded-full bg-primary transition-all duration-200" style="width:${pct}%"></div>
              </div>
            </div>
            <button type="button" class="shrink-0 rounded-md px-2 py-1 text-xs text-text-muted hover:bg-bg-subtle hover:text-text" data-update-action="dismiss" title="Sembunyikan">Sembunyikan</button>
          </div>
        </div>`;
      return;
    }

    let title = "";
    let body = "";
    let actions = "";

    if (phase === "available") {
      title = `Update tersedia: ${version}`;
      body = `<p class="mt-1 text-sm text-text-muted">Versi saat ini: v${s.currentVersion || "?"}</p>`;
      if (s.releaseNotes) {
        body += `<pre class="mt-3 max-h-28 overflow-auto whitespace-pre-wrap rounded-lg border border-border bg-bg-subtle p-3 text-xs leading-relaxed text-text-muted">${this.escapeHtml(s.releaseNotes)}</pre>`;
      }
      actions = `
        <button type="button" class="rounded-lg bg-primary px-3 py-2 text-sm font-medium text-white hover:bg-primary-dark" data-update-action="download">Download</button>
        <button type="button" class="rounded-lg border border-border bg-surface px-3 py-2 text-sm font-medium text-text hover:bg-bg-subtle" data-update-action="download-bg">Download di background</button>
        <button type="button" class="rounded-lg px-3 py-2 text-sm text-text-muted hover:bg-bg-subtle hover:text-text" data-update-action="dismiss">Nanti</button>`;
    } else if (phase === "downloading") {
      title = `Mengunduh update ${version}…`;
      body = `
        <div class="mt-3">
          <div class="mb-1 flex items-center justify-between text-xs text-text-muted">
            <span>${pct}%</span>
            <span>${progressText}</span>
          </div>
          <div class="h-2 overflow-hidden rounded-full bg-bg-subtle">
            <div class="h-full rounded-full bg-primary transition-all duration-200" style="width:${pct}%"></div>
          </div>
        </div>`;
      actions = `<button type="button" class="rounded-lg border border-border bg-surface px-3 py-2 text-sm font-medium text-text hover:bg-bg-subtle" data-update-action="download-bg">Jalankan di background</button>`;
    } else if (phase === "downloaded") {
      title = `Update ${version} siap diinstall`;
      body = `<p class="mt-1 text-sm text-text-muted">Restart aplikasi untuk menerapkan update. Pekerjaan yang belum disimpan bisa hilang.</p>`;
      actions = `
        <button type="button" class="rounded-lg bg-primary px-3 py-2 text-sm font-medium text-white hover:bg-primary-dark" data-update-action="install">Restart sekarang</button>
        <button type="button" class="rounded-lg border border-border bg-surface px-3 py-2 text-sm font-medium text-text hover:bg-bg-subtle" data-update-action="dismiss">Nanti (install saat tutup)</button>`;
    } else if (phase === "error") {
      title = "Update gagal";
      body = `<p class="mt-1 text-sm text-text-muted">${this.escapeHtml(s.message || "Terjadi kesalahan.")}</p>`;
      actions = `
        <button type="button" class="rounded-lg bg-primary px-3 py-2 text-sm font-medium text-white hover:bg-primary-dark" data-update-action="check">Coba lagi</button>
        <a href="https://github.com/rachmad-jenss/your-everyday-tools-desktop/releases" target="_blank" rel="noopener noreferrer" class="rounded-lg border border-border bg-surface px-3 py-2 text-sm font-medium text-text no-underline hover:bg-bg-subtle">Download manual</a>`;
    } else {
      el.classList.add("hidden");
      return;
    }

    el.innerHTML = `
      <div class="pointer-events-auto border-t border-border bg-surface/95 px-4 py-4 shadow-lg backdrop-blur-sm md:ml-[280px]">
        <div class="mx-auto max-w-[1200px]">
          <div class="font-semibold text-text">${this.escapeHtml(title)}</div>
          ${body}
          <div class="mt-3 flex flex-wrap gap-2">${actions}</div>
        </div>
      </div>`;
  },

  renderSettings() {
    const panel = document.getElementById("settings-update-panel");
    if (!panel) return;

    const s = this.state;
    const phase = s.phase || "idle";
    const versionEl = document.getElementById("settings-update-version");
    const statusEl = document.getElementById("settings-update-status");
    const notesEl = document.getElementById("settings-update-notes");
    const progressEl = document.getElementById("settings-update-progress");
    const progressBar = document.getElementById("settings-update-progress-bar");
    const progressLabel = document.getElementById("settings-update-progress-label");
    const actionsEl = document.getElementById("settings-update-actions");

    if (versionEl) {
      versionEl.textContent = s.currentVersion ? `v${s.currentVersion}` : "—";
    }

    const statusText = {
      idle: "Siap mengecek update.",
      checking: "Mengecek update…",
      available: `Update tersedia: v${s.version || "?"}`,
      downloading: `Mengunduh v${s.version || "?"}…`,
      downloaded: `Update v${s.version || "?"} siap diinstall.`,
      "up-to-date": "Sudah versi terbaru.",
      error: s.message || "Gagal mengecek atau mengunduh update.",
    };
    if (statusEl) statusEl.textContent = statusText[phase] || statusText.idle;

    if (notesEl) {
      if (phase === "available" && s.releaseNotes) {
        notesEl.textContent = s.releaseNotes;
        notesEl.classList.remove("hidden");
      } else {
        notesEl.classList.add("hidden");
        notesEl.textContent = "";
      }
    }

    if (progressEl && progressBar && progressLabel) {
      if (phase === "downloading") {
        const pct = Math.max(0, Math.min(100, Math.round(s.percent || 0)));
        progressEl.classList.remove("hidden");
        progressBar.style.width = `${pct}%`;
        progressLabel.textContent = `${pct}% · ${this.formatProgress(s)}`;
      } else {
        progressEl.classList.add("hidden");
        progressBar.style.width = "0%";
        progressLabel.textContent = "";
      }
    }

    if (!actionsEl) return;
    let html = `<button type="button" class="rounded-lg border border-border bg-surface px-3 py-2 text-sm font-medium text-text hover:bg-bg-subtle disabled:opacity-50" data-update-action="check" ${phase === "checking" || phase === "downloading" ? "disabled" : ""}>Cek update</button>`;

    if (phase === "available") {
      html += `<button type="button" class="rounded-lg bg-primary px-3 py-2 text-sm font-medium text-white hover:bg-primary-dark" data-update-action="download">Download</button>`;
      html += `<button type="button" class="rounded-lg border border-border bg-surface px-3 py-2 text-sm font-medium text-text hover:bg-bg-subtle" data-update-action="download-bg">Download di background</button>`;
    } else if (phase === "downloading") {
      html += `<button type="button" class="rounded-lg border border-border bg-surface px-3 py-2 text-sm font-medium text-text hover:bg-bg-subtle" data-update-action="download-bg">Jalankan di background</button>`;
    } else if (phase === "downloaded") {
      html += `<button type="button" class="rounded-lg bg-primary px-3 py-2 text-sm font-medium text-white hover:bg-primary-dark" data-update-action="install">Restart sekarang</button>`;
    } else if (phase === "error") {
      html += `<a href="https://github.com/rachmad-jenss/your-everyday-tools-desktop/releases" target="_blank" rel="noopener noreferrer" class="rounded-lg border border-border bg-surface px-3 py-2 text-sm font-medium text-text no-underline hover:bg-bg-subtle">Download manual</a>`;
    }

    actionsEl.innerHTML = html;
  },

  formatProgress(s) {
    const transferred = s.transferred || 0;
    const total = s.total || 0;
    if (!total) return "Menghitung…";
    return `${this.formatBytes(transferred)} / ${this.formatBytes(total)}`;
  },

  formatBytes(bytes) {
    if (!bytes) return "0 B";
    const units = ["B", "KB", "MB", "GB"];
    let value = bytes;
    let unit = 0;
    while (value >= 1024 && unit < units.length - 1) {
      value /= 1024;
      unit += 1;
    }
    return `${value.toFixed(unit === 0 ? 0 : 1)} ${units[unit]}`;
  },

  escapeHtml(text) {
    return String(text)
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;");
  },
};

document.addEventListener("DOMContentLoaded", () => DesktopUpdater.init());
