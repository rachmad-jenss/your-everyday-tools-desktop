const { contextBridge, ipcRenderer } = require("electron");

contextBridge.exposeInMainWorld("electronAPI", {
  isDesktop: true,
  setTheme: (mode, resolved) => ipcRenderer.invoke("theme:set", { mode, resolved }),
  openAppMenu: (label) => ipcRenderer.send("menu:popup", label),
  openComponentManager: () => ipcRenderer.invoke("components:open"),
  getAppVersion: () => ipcRenderer.invoke("app:getVersion"),
  checkForUpdates: () => ipcRenderer.invoke("update:check"),
  downloadUpdate: (opts) => ipcRenderer.invoke("update:download", opts || {}),
  installUpdate: () => ipcRenderer.invoke("update:install"),
  dismissUpdateUi: () => ipcRenderer.invoke("update:dismiss"),
  onUpdateStatus: (callback) => {
    if (typeof callback !== "function") return () => {};
    const handler = (_event, payload) => callback(payload);
    ipcRenderer.on("update:status", handler);
    return () => ipcRenderer.removeListener("update:status", handler);
  },
});
