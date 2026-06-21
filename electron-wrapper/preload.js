const { contextBridge, ipcRenderer } = require("electron");

contextBridge.exposeInMainWorld("electronAPI", {
  isDesktop: true,
  setTheme: (mode, resolved) => ipcRenderer.invoke("theme:set", { mode, resolved }),
  openAppMenu: (label) => ipcRenderer.send("menu:popup", label),
  openComponentManager: () => ipcRenderer.invoke("components:open"),
});
