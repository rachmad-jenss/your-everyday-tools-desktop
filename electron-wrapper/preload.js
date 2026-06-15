const { contextBridge, ipcRenderer } = require("electron");

contextBridge.exposeInMainWorld("electronAPI", {
  setTheme: (resolved) => ipcRenderer.invoke("theme:set", resolved),
});
