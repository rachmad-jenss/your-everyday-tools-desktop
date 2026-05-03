const { app, BrowserWindow, Menu, shell, dialog, ipcMain } = require("electron");
const { spawn, execFileSync } = require("child_process");
const { autoUpdater } = require("electron-updater");
const path = require("path");
const fs = require("fs");
const http = require("http");
const https = require("https");
const os = require("os");

let mainWindow = null;
let flaskProcess = null;
let chosenPort = 5000;

const PORT_FILE = path.join(
  process.env.TEMP || process.env.TMPDIR || "/tmp",
  "yet-desktop-port.txt"
);

function getBackendPath() {
  const isPackaged = !process.defaultApp;
  const exeName =
    process.platform === "win32" ? "YourEverydayTools.exe" : "YourEverydayTools";

  if (isPackaged) {
    return path.join(process.resourcesPath, "backend", exeName);
  }
  return path.join(__dirname, "..", "dist", "YourEverydayTools", exeName);
}

function cleanPortFile() {
  try {
    fs.unlinkSync(PORT_FILE);
  } catch (_) {}
}

function readPortFromFile() {
  try {
    const content = fs.readFileSync(PORT_FILE, "utf-8").trim();
    const port = parseInt(content, 10);
    if (port >= 5000 && port <= 5010) return port;
  } catch (_) {}
  return 5000;
}

function waitForServer(port, retries, delay) {
  return new Promise((resolve, reject) => {
    let attempts = 0;
    function tryConnect() {
      attempts++;
      const req = http.get(`http://127.0.0.1:${port}/`, (res) => {
        resolve(port);
      });
      req.on("error", () => {
        if (attempts >= retries) {
          reject(new Error(`Flask did not start after ${retries} attempts`));
        } else {
          setTimeout(tryConnect, delay);
        }
      });
      req.setTimeout(2000, () => {
        req.destroy();
        if (attempts >= retries) {
          reject(new Error(`Flask did not start after ${retries} attempts`));
        } else {
          setTimeout(tryConnect, delay);
        }
      });
    }
    tryConnect();
  });
}

function startFlask() {
  const backendPath = getBackendPath();

  if (!fs.existsSync(backendPath)) {
    dialog.showErrorBox(
      "Backend Not Found",
      `Could not find the backend executable at:\n${backendPath}\n\nPlease reinstall the application.`
    );
    app.quit();
    return;
  }

  cleanPortFile();

  flaskProcess = spawn(backendPath, [], {
    env: { ...process.env, ELECTRON_WRAPPER: "1" },
    stdio: ["ignore", "pipe", "pipe"],
    detached: false,
    windowsHide: true,
  });

  flaskProcess.stdout.on("data", (data) => {
    console.log(`[Flask] ${data.toString().trim()}`);
  });

  flaskProcess.stderr.on("data", (data) => {
    console.error(`[Flask] ${data.toString().trim()}`);
  });

  flaskProcess.on("error", (err) => {
    dialog.showErrorBox("Backend Error", `Failed to start backend:\n${err.message}`);
    app.quit();
  });

  flaskProcess.on("exit", (code, signal) => {
    console.log(`Flask exited with code ${code}, signal ${signal}`);
    if (mainWindow && !mainWindow.isDestroyed()) {
      dialog.showErrorBox(
        "Backend Crashed",
        `The backend process exited unexpectedly (code: ${code}).\nThe application will now close.`
      );
      app.quit();
    }
  });
}

function killFlask() {
  if (!flaskProcess) return;
  try {
    if (process.platform === "win32") {
      // Safe: PID is an integer from our own child process, not user input
      execFileSync("taskkill", ["/PID", String(flaskProcess.pid), "/T", "/F"], {
        stdio: "ignore",
      });
    } else {
      process.kill(-flaskProcess.pid, "SIGTERM");
    }
  } catch (_) {
    try {
      flaskProcess.kill("SIGKILL");
    } catch (__) {}
  }
  flaskProcess = null;
  cleanPortFile();
}

// ── Auto-update via GitHub Releases ──────────────────────

function setupAutoUpdater() {
  autoUpdater.autoDownload = false;
  autoUpdater.autoInstallOnAppQuit = true;

  autoUpdater.on("update-available", (info) => {
    const newVersion = info.version || "unknown";
    const notes = info.releaseNotes || "";
    dialog
      .showMessageBox(mainWindow, {
        type: "info",
        title: "Update Tersedia",
        message: `Versi baru tersedia: v${newVersion}`,
        detail:
          `Versi kamu: v${app.getVersion()}\n\n` +
          (notes ? `${typeof notes === "string" ? notes : ""}\n\n` : "") +
          "Mau download dan install sekarang?",
        buttons: ["Download Sekarang", "Nanti Saja"],
        defaultId: 0,
        cancelId: 1,
      })
      .then(({ response }) => {
        if (response === 0) {
          autoUpdater.downloadUpdate();
        }
      });
  });

  autoUpdater.on("update-not-available", () => {
    console.log("[Updater] No update available.");
  });

  autoUpdater.on("download-progress", (progress) => {
    const pct = Math.round(progress.percent);
    if (mainWindow && !mainWindow.isDestroyed()) {
      mainWindow.setProgressBar(pct / 100);
      mainWindow.setTitle(`Your Everyday Tools — Downloading update ${pct}%`);
    }
  });

  autoUpdater.on("update-downloaded", () => {
    if (mainWindow && !mainWindow.isDestroyed()) {
      mainWindow.setProgressBar(-1);
      mainWindow.setTitle("Your Everyday Tools");
    }
    dialog
      .showMessageBox(mainWindow, {
        type: "info",
        title: "Update Siap",
        message: "Update sudah didownload.",
        detail:
          "Aplikasi akan restart untuk menginstall update.\nPastikan semua pekerjaan sudah disimpan.",
        buttons: ["Restart Sekarang", "Nanti (install saat tutup app)"],
        defaultId: 0,
        cancelId: 1,
      })
      .then(({ response }) => {
        if (response === 0) {
          autoUpdater.quitAndInstall(false, true);
        }
      });
  });

  autoUpdater.on("error", (err) => {
    console.error("[Updater] Error:", err.message);
  });

  // Auto-check 30 detik setelah app siap
  setTimeout(() => {
    autoUpdater.checkForUpdates().catch((err) => {
      console.error("[Updater] Silent check failed:", err.message);
    });
  }, 30000);
}

function checkForUpdatesManual() {
  autoUpdater.checkForUpdates()
    .then((result) => {
      if (!result || !result.updateInfo) {
        dialog.showMessageBox(mainWindow, {
          type: "info",
          title: "Update",
          message: "Tidak ada update",
          detail: `Kamu sudah menggunakan versi terbaru (v${app.getVersion()}).`,
        });
      }
    })
    .catch(() => {
      dialog.showMessageBox(mainWindow, {
        type: "info",
        title: "Update",
        message: "Tidak bisa cek update",
        detail:
          "Gagal menghubungi server update. Periksa koneksi internet.\n\n" +
          "Cek update manual di:\nhttps://github.com/rachmad-jenss/your-everyday-tools-desktop/releases",
      });
    });
}

function buildMenu() {
  const template = [
    {
      label: "File",
      submenu: [{ role: "quit", label: "Quit Your Everyday Tools" }],
    },
    {
      label: "Edit",
      submenu: [
        { role: "undo" },
        { role: "redo" },
        { type: "separator" },
        { role: "cut" },
        { role: "copy" },
        { role: "paste" },
        { role: "selectAll" },
      ],
    },
    {
      label: "View",
      submenu: [
        { role: "reload" },
        { role: "forceReload" },
        { role: "toggleDevTools" },
        { type: "separator" },
        { role: "resetZoom" },
        { role: "zoomIn" },
        { role: "zoomOut" },
        { type: "separator" },
        { role: "togglefullscreen" },
      ],
    },
    {
      label: "Help",
      submenu: [
        {
          label: "Cek Update...",
          click: () => checkForUpdatesManual(),
        },
        {
          label: "Kelola Komponen...",
          click: async () => {
            if (downloaderWindow) { downloaderWindow.focus(); return; }
            await showDownloaderWindow(true);
          },
        },
        { type: "separator" },
        {
          label: "About Your Everyday Tools",
          click: () => {
            dialog.showMessageBox(mainWindow, {
              type: "info",
              title: "About",
              message: "Your Everyday Tools",
              detail: `Version ${app.getVersion()}\n89+ offline utilities.\nBuilt with Flask + Electron.`,
            });
          },
        },
      ],
    },
  ];

  if (process.platform === "darwin") {
    template.unshift({
      label: app.name,
      submenu: [
        { role: "about" },
        { type: "separator" },
        { role: "hide" },
        { role: "hideOthers" },
        { role: "unhide" },
        { type: "separator" },
        { role: "quit" },
      ],
    });
  }

  Menu.setApplicationMenu(Menu.buildFromTemplate(template));
}

function createWindow(port) {
  mainWindow = new BrowserWindow({
    width: 1280,
    height: 800,
    title: "Your Everyday Tools",
    webPreferences: {
      preload: path.join(__dirname, "preload.js"),
      contextIsolation: true,
      nodeIntegration: false,
      sandbox: true,
    },
    show: false,
  });

  mainWindow.loadURL(`http://127.0.0.1:${port}`);
  mainWindow.once("ready-to-show", () => mainWindow.show());

  mainWindow.webContents.setWindowOpenHandler(({ url }) => {
    if (!url.startsWith(`http://127.0.0.1:${port}`)) {
      shell.openExternal(url);
      return { action: "deny" };
    }
    return { action: "allow" };
  });

  mainWindow.webContents.on("will-navigate", (event, url) => {
    if (!url.startsWith(`http://127.0.0.1:${port}`)) {
      event.preventDefault();
      shell.openExternal(url);
    }
  });

  mainWindow.on("closed", () => {
    mainWindow = null;
  });
}

// ── Component download system ─────────────────────────────

function getVendorPath() {
  const isPackaged = !process.defaultApp;
  if (isPackaged) {
    return path.join(process.resourcesPath, "backend", "_internal", "vendor");
  }
  return path.join(__dirname, "..", "dist", "YourEverydayTools", "_internal", "vendor");
}

const COMPONENT_FLAG = path.join(app.getPath("userData"), "components-configured.json");

// ─── Update these URLs after uploading zips to GitHub Releases ───────────────
// Tag: components-v1  (create once, never changes)
// Upload: ffmpeg-windows.zip, tesseract-windows.zip
const COMPONENT_DOWNLOADS = {
  ffmpeg: {
    name: "FFmpeg",
    url: "https://github.com/rachmad-jenss/your-everyday-tools-desktop/releases/download/components-v1/ffmpeg-windows.zip",
    dest: "ffmpeg",
  },
  tesseract: {
    name: "Tesseract OCR",
    url: "https://github.com/rachmad-jenss/your-everyday-tools-desktop/releases/download/components-v1/tesseract-windows.zip",
    dest: "tesseract",
  },
};
// ─────────────────────────────────────────────────────────────────────────────

/** Stream-download a URL to destPath, calling onProgress(0-100). Follows redirects. */
function downloadFile(url, destPath, onProgress) {
  return new Promise((resolve, reject) => {
    const file = fs.createWriteStream(destPath);
    let downloaded = 0;

    const doGet = (reqUrl, hops) => {
      if (hops > 10) { reject(new Error("Too many redirects")); return; }
      const client = reqUrl.startsWith("https") ? https : http;
      client.get(reqUrl, { headers: { "User-Agent": "YETDesktop" } }, (res) => {
        if (res.statusCode >= 300 && res.statusCode < 400 && res.headers.location) {
          res.resume();
          doGet(res.headers.location, hops + 1);
          return;
        }
        if (res.statusCode !== 200) {
          file.destroy();
          reject(new Error(`HTTP ${res.statusCode} — ${reqUrl}`));
          return;
        }
        const total = parseInt(res.headers["content-length"] || "0", 10);
        res.on("data", (chunk) => {
          downloaded += chunk.length;
          file.write(chunk);
          if (total > 0) onProgress(Math.round((downloaded / total) * 100));
        });
        res.on("end", () => { file.end(); resolve(); });
        res.on("error", (err) => { file.destroy(); reject(err); });
      }).on("error", (err) => { file.destroy(); reject(err); });
    };
    doGet(url, 0);
  });
}

/** Extract a zip file to destDir using PowerShell (Windows) or unzip (macOS/Linux). */
function extractZip(zipPath, destDir) {
  return new Promise((resolve, reject) => {
    fs.mkdirSync(destDir, { recursive: true });
    let cmd, args;
    if (process.platform === "win32") {
      cmd = "powershell";
      args = [
        "-NonInteractive", "-NoProfile", "-ExecutionPolicy", "Bypass", "-Command",
        `Expand-Archive -LiteralPath '${zipPath.replace(/'/g, "''")}' -DestinationPath '${destDir.replace(/'/g, "''")}' -Force`,
      ];
    } else {
      cmd = "unzip";
      args = ["-o", zipPath, "-d", destDir];
    }
    const proc = spawn(cmd, args, { windowsHide: true, stdio: "pipe" });
    let stderr = "";
    proc.stderr.on("data", (d) => (stderr += d.toString()));
    proc.on("close", (code) => {
      if (code === 0) resolve();
      else reject(new Error(`Extraction failed (exit ${code}): ${stderr.slice(0, 300)}`));
    });
    proc.on("error", reject);
  });
}

/** Download + extract one component, sending IPC progress to the downloader window. */
async function downloadComponent(id, win) {
  const comp = COMPONENT_DOWNLOADS[id];
  const vendorDir = getVendorPath();
  const destDir = path.join(vendorDir, comp.dest);
  const tmpPath = path.join(os.tmpdir(), `yet-${id}-${Date.now()}.zip`);

  const send = (data) => {
    if (win && !win.isDestroyed()) win.webContents.send("download:progress", data);
  };

  try {
    send({ id, percent: 0, statusText: "Menghubungi server...", noteText: "", mode: "download" });
    await downloadFile(comp.url, tmpPath, (pct) => {
      send({ id, percent: pct, statusText: `${pct}%`, noteText: "", mode: "download" });
    });

    send({ id, percent: 100, statusText: "Mengekstrak...", noteText: "Mohon tunggu...", mode: "extract" });
    await extractZip(tmpPath, destDir);
    try { fs.unlinkSync(tmpPath); } catch (_) {}

    console.log(`[Downloader] ${id} installed to ${destDir}`);
    if (win && !win.isDestroyed()) win.webContents.send("download:component-done", { id, success: true });
    return true;
  } catch (err) {
    console.error(`[Downloader] ${id} failed:`, err.message);
    try { fs.unlinkSync(tmpPath); } catch (_) {}
    try { fs.rmSync(destDir, { recursive: true, force: true }); } catch (_) {}
    if (win && !win.isDestroyed()) {
      win.webContents.send("download:component-done", { id, success: false, error: err.message });
    }
    return false;
  }
}

let downloaderWindow = null;

/** Open the component downloader window. Resolves when the window closes. */
function showDownloaderWindow(forceShow = false) {
  // Skip if already configured (unless forced from menu)
  if (!forceShow && fs.existsSync(COMPONENT_FLAG)) return Promise.resolve();

  return new Promise((resolve) => {
    downloaderWindow = new BrowserWindow({
      width: 460,
      height: 490,
      resizable: false,
      maximizable: false,
      title: "Komponen Opsional — Your Everyday Tools",
      webPreferences: {
        preload: path.join(__dirname, "preload-downloader.js"),
        contextIsolation: true,
        nodeIntegration: false,
        sandbox: true,
      },
    });

    downloaderWindow.setMenuBarVisibility(false);
    downloaderWindow.loadFile(path.join(__dirname, "downloader.html"));

    downloaderWindow.on("closed", () => {
      downloaderWindow = null;
      resolve();
    });
  });
}

// ── IPC handlers for downloader window ───────────────────

ipcMain.on("download:start", async (event, components) => {
  const win = downloaderWindow;
  let anySuccess = false;
  let anyError = false;

  for (const id of components) {
    if (!COMPONENT_DOWNLOADS[id]) continue;
    const ok = await downloadComponent(id, win);
    if (ok) anySuccess = true; else anyError = true;
  }

  // Save flag so first-run dialog doesn't repeat
  try {
    const vendorDir = getVendorPath();
    const config = {};
    for (const id of Object.keys(COMPONENT_DOWNLOADS)) {
      config[id] = fs.existsSync(path.join(vendorDir, COMPONENT_DOWNLOADS[id].dest));
    }
    fs.writeFileSync(COMPONENT_FLAG, JSON.stringify(config));
  } catch (_) {}

  if (win && !win.isDestroyed()) {
    win.webContents.send("download:all-done", { anySuccess, anyError });
  }
});

ipcMain.on("download:skip", () => {
  try { fs.writeFileSync(COMPONENT_FLAG, JSON.stringify({ skipped: true })); } catch (_) {}
  if (downloaderWindow && !downloaderWindow.isDestroyed()) downloaderWindow.close();
});

ipcMain.on("download:finish", () => {
  if (downloaderWindow && !downloaderWindow.isDestroyed()) downloaderWindow.close();
});

app.whenReady().then(async () => {
  buildMenu();

  // First-run: let user download optional components
  await showDownloaderWindow();

  startFlask();

  await new Promise((r) => setTimeout(r, 1500));
  chosenPort = readPortFromFile();

  try {
    await waitForServer(chosenPort, 30, 500);
  } catch (err) {
    dialog.showErrorBox("Startup Failed", err.message);
    killFlask();
    app.quit();
    return;
  }

  createWindow(chosenPort);

  // Auto-update: setup handlers (no auto-check — owner must configure release server first)
  setupAutoUpdater();

  app.on("activate", () => {
    if (BrowserWindow.getAllWindows().length === 0) {
      createWindow(chosenPort);
    }
  });
});

app.on("window-all-closed", () => {
  if (process.platform !== "darwin") {
    killFlask();
    app.quit();
  }
});

app.on("will-quit", () => {
  killFlask();
});

app.on("before-quit", () => {
  killFlask();
});
