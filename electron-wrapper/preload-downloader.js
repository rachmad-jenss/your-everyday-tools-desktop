// Preload for downloader/component-manager window.
// Exposes a minimal IPC bridge — no Node.js internals leak to the renderer.
const { contextBridge, ipcRenderer } = require("electron");

contextBridge.exposeInMainWorld("downloaderAPI", {
  startDownload:    (components) => ipcRenderer.send("download:start", components),
  skip:             ()           => ipcRenderer.send("download:skip"),
  finish:           ()           => ipcRenderer.send("download:finish"),
  onProgress:       (cb) => ipcRenderer.on("download:progress",        (_, d) => cb(d)),
  onComponentDone:  (cb) => ipcRenderer.on("download:component-done",  (_, d) => cb(d)),
  onAllDone:        (cb) => ipcRenderer.once("download:all-done",       (_, d) => cb(d)),
});
