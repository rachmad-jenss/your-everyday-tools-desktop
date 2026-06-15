"use strict";

const os = require("os");

const DWMWA_USE_IMMERSIVE_DARK_MODE_BEFORE_20H1 = 19;
const DWMWA_USE_IMMERSIVE_DARK_MODE = 20;

let DwmSetWindowAttribute = null;
let SetWindowPos = null;
let koffi = null;
let ready = false;

function isSupported() {
  if (process.platform !== "win32") return false;
  const build = Number.parseInt(String(os.release()).split(".").pop(), 10);
  return !Number.isNaN(build) && build >= 17763;
}

function init() {
  if (!isSupported()) return false;
  try {
    koffi = require("koffi");
    const dwmapi = koffi.load("dwmapi.dll");
    const user32 = koffi.load("user32.dll");
    DwmSetWindowAttribute = dwmapi.func(
      "int DwmSetWindowAttribute(void *hwnd, uint32_t dwAttribute, void *pvAttribute, uint32_t cbAttribute)"
    );
    SetWindowPos = user32.func(
      "int SetWindowPos(void *hWnd, void *hWndInsertAfter, int X, int Y, int cx, int cy, uint32_t uFlags)"
    );
    ready = true;
    return true;
  } catch (err) {
    console.warn("[win-dark-titlebar] init failed:", err.message);
    return false;
  }
}

init();

function isReady() {
  return ready;
}

function hwndFromWindow(win) {
  const handle = win.getNativeWindowHandle();
  return koffi.decode(handle, "void *");
}

function setWindowDarkMode(win, dark) {
  if (!ready || !win || win.isDestroyed()) return;
  try {
    const hwnd = hwndFromWindow(win);
    const value = koffi.alloc("int32", dark ? 1 : 0);
    DwmSetWindowAttribute(hwnd, DWMWA_USE_IMMERSIVE_DARK_MODE_BEFORE_20H1, value, 4);
    DwmSetWindowAttribute(hwnd, DWMWA_USE_IMMERSIVE_DARK_MODE, value, 4);
    // Redraw frame so the title bar picks up the new mode immediately.
    const SWP_NOMOVE = 0x0002;
    const SWP_NOSIZE = 0x0001;
    const SWP_NOZORDER = 0x0004;
    const SWP_FRAMECHANGED = 0x0020;
    const SWP_NOACTIVATE = 0x0010;
    SetWindowPos(
      hwnd,
      null,
      0,
      0,
      0,
      0,
      SWP_NOMOVE | SWP_NOSIZE | SWP_NOZORDER | SWP_FRAMECHANGED | SWP_NOACTIVATE
    );
  } catch (err) {
    console.warn("[win-dark-titlebar] setWindowDarkMode:", err.message);
  }
}

module.exports = { setWindowDarkMode, isSupported, isReady };
