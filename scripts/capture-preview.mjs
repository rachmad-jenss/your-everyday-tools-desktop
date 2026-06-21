import { chromium } from "playwright";
import fs from "fs";
import path from "path";

const outDir = path.join("static", "preview");
fs.mkdirSync(outDir, { recursive: true });

const browser = await chromium.launch();
const page = await browser.newPage({ viewport: { width: 1400, height: 900 } });
await page.goto("http://127.0.0.1:5000", { waitUntil: "networkidle" });
await page.screenshot({ path: path.join(outDir, "preview-browser.png") });

await page.evaluate(() => {
  document.body.classList.add("electron-desktop");
  const titleBar = document.getElementById("title-bar");
  const menuBar = document.getElementById("electron-menu-bar");
  const chromeBrand = document.getElementById("chrome-sidebar-brand");
  if (titleBar) titleBar.hidden = false;
  if (chromeBrand) chromeBrand.hidden = false;
  if (menuBar) {
    menuBar.hidden = false;
    menuBar.classList.remove("hidden");
  }
});
await page.waitForTimeout(400);
await page.screenshot({ path: path.join(outDir, "preview-electron.png") });
await page.locator("#app-chrome").screenshot({
  path: path.join(outDir, "preview-electron-header.png"),
});
await page.locator("#sidebar").screenshot({
  path: path.join(outDir, "preview-sidebar.png"),
});
await page.locator(".sidebar-cat-fold").first().click();
await page.waitForTimeout(200);
await page.locator("#sidebar").screenshot({
  path: path.join(outDir, "preview-sidebar-categories-open.png"),
});
await browser.close();
console.log("Screenshots saved to static/preview/");
