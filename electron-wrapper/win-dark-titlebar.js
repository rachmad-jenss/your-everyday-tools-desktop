"use strict";

const os = require("os");
const { execFileSync } = require("child_process");

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

function initKoffi() {
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
    console.warn("[win-dark-titlebar] koffi init failed:", err.message);
    return false;
  }
}

initKoffi();

function isReady() {
  return ready;
}

function hwndFromWindow(win) {
  return win.getNativeWindowHandle().readBigUInt64LE(0);
}

function redrawFrame(hwnd) {
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
}

function setWindowDarkModeKoffi(win, dark) {
  const hwnd = hwndFromWindow(win);
  const value = koffi.alloc("int32", dark ? 1 : 0);
  const r1 = DwmSetWindowAttribute(hwnd, DWMWA_USE_IMMERSIVE_DARK_MODE_BEFORE_20H1, value, 4);
  const r2 = DwmSetWindowAttribute(hwnd, DWMWA_USE_IMMERSIVE_DARK_MODE, value, 4);
  redrawFrame(hwnd);
  return r1 === 0 || r2 === 0;
}

const PS_APPLY_DWM = String.raw`
Add-Type @"
using System;
using System.Runtime.InteropServices;
public class YetDwm {
  const int DWMWA_USE_IMMERSIVE_DARK_MODE = 20;
  const int DWMWA_USE_IMMERSIVE_DARK_MODE_BEFORE_20H1 = 19;
  [DllImport("dwmapi.dll")] static extern int DwmSetWindowAttribute(IntPtr h, int a, ref int v, int s);
  [DllImport("user32.dll")] static extern bool SetWindowPos(IntPtr h, IntPtr i, int x, int y, int cx, int cy, uint f);
  public static void Apply(long hwnd, bool dark) {
    IntPtr h = new IntPtr(hwnd);
    int v = dark ? 1 : 0;
    DwmSetWindowAttribute(h, DWMWA_USE_IMMERSIVE_DARK_MODE_BEFORE_20H1, ref v, 4);
    DwmSetWindowAttribute(h, DWMWA_USE_IMMERSIVE_DARK_MODE, ref v, 4);
    SetWindowPos(h, IntPtr.Zero, 0, 0, 0, 0, 0x0020 | 0x0002 | 0x0001 | 0x0004 | 0x0010);
  }
}
"@
[YetDwm]::Apply({{HWND}}, {{DARK}})
`;

function setWindowDarkModePowerShell(win, dark) {
  const hwnd = hwndFromWindow(win);
  const script = PS_APPLY_DWM.replace("{{HWND}}", hwnd.toString()).replace(
    "{{DARK}}",
    dark ? "$true" : "$false"
  );
  execFileSync(
    "powershell.exe",
    ["-NoProfile", "-NonInteractive", "-ExecutionPolicy", "Bypass", "-Command", script],
    { windowsHide: true, timeout: 8000 }
  );
  return true;
}

function setWindowDarkMode(win, dark) {
  if (!isSupported() || !win || win.isDestroyed()) return false;
  try {
    if (ready) {
      return setWindowDarkModeKoffi(win, dark);
    }
    return setWindowDarkModePowerShell(win, dark);
  } catch (err) {
    console.warn("[win-dark-titlebar] setWindowDarkMode:", err.message);
    return false;
  }
}

module.exports = { setWindowDarkMode, isSupported, isReady };
