const { contextBridge, ipcRenderer } = require("electron");

contextBridge.exposeInMainWorld("electronAPI", {
  setTheme: (mode, resolved) => ipcRenderer.invoke("theme:set", { mode, resolved }),
});
