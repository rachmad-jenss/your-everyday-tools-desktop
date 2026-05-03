const { app, BrowserWindow, Menu, shell, dialog, Notification } = require("electron");
const { spawn, execFileSync } = require("child_process");
const { autoUpdater } = require("electron-updater");
const path = require("path");
const fs = require("fs");
const http = require("http");

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

// ── First-run component selection ────────────────────────

function getVendorPath() {
  const isPackaged = !process.defaultApp;
  if (isPackaged) {
    return path.join(process.resourcesPath, "backend", "_internal", "vendor");
  }
  return path.join(__dirname, "..", "dist", "YourEverydayTools", "_internal", "vendor");
}

const COMPONENT_FLAG = path.join(
  app.getPath("userData"),
  "components-configured.json"
);

async function showComponentSelection() {
  // Skip if already configured
  if (fs.existsSync(COMPONENT_FLAG)) return;

  const vendorDir = getVendorPath();
  const ffmpegDir = path.join(vendorDir, "ffmpeg");
  const tesseractDir = path.join(vendorDir, "tesseract");

  const hasFFmpeg = fs.existsSync(ffmpegDir);
  const hasTesseract = fs.existsSync(tesseractDir);

  // Skip if nothing to configure (vendor dirs don't exist)
  if (!hasFFmpeg && !hasTesseract) {
    fs.writeFileSync(COMPONENT_FLAG, JSON.stringify({ ffmpeg: false, tesseract: false }));
    return;
  }

  const choices = [];
  if (hasFFmpeg) choices.push("FFmpeg — Audio/Video tools (~193 MB)");
  if (hasTesseract) choices.push("Tesseract OCR — English + Indonesia (~182 MB)");
  choices.push("Simpan semua komponen");

  const { response } = await dialog.showMessageBox({
    type: "question",
    title: "Pilih Komponen",
    message: "Komponen tambahan mana yang ingin kamu simpan?",
    detail:
      "Kamu bisa menghapus komponen yang tidak diperlukan untuk menghemat disk space.\n\n" +
      (hasFFmpeg ? "• FFmpeg (~193 MB): Dibutuhkan untuk convert audio/video, extract audio, trim, merge\n" : "") +
      (hasTesseract ? "• Tesseract OCR (~182 MB): Dibutuhkan untuk OCR PDF, image to text\n" : "") +
      "\nPilih komponen yang ingin DIHAPUS, atau simpan semua.",
    buttons: [
      ...(hasFFmpeg ? ["Hapus FFmpeg"] : []),
      ...(hasTesseract ? ["Hapus Tesseract"] : []),
      "Simpan Semua",
    ],
    defaultId: choices.length - 1,
    cancelId: choices.length - 1,
    noLink: true,
  });

  const config = { ffmpeg: hasFFmpeg, tesseract: hasTesseract };
  const buttonLabels = [];
  if (hasFFmpeg) buttonLabels.push("ffmpeg");
  if (hasTesseract) buttonLabels.push("tesseract");

  const selected = buttonLabels[response];
  if (selected === "ffmpeg" && hasFFmpeg) {
    fs.rmSync(ffmpegDir, { recursive: true, force: true });
    config.ffmpeg = false;
    console.log("[Setup] Removed FFmpeg");
  } else if (selected === "tesseract" && hasTesseract) {
    fs.rmSync(tesseractDir, { recursive: true, force: true });
    config.tesseract = false;
    console.log("[Setup] Removed Tesseract");
  }

  fs.writeFileSync(COMPONENT_FLAG, JSON.stringify(config));
}

app.whenReady().then(async () => {
  buildMenu();

  // First-run: let user remove optional components
  await showComponentSelection();

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
