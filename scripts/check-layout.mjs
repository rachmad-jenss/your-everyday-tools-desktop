import { chromium } from "playwright";

const browser = await chromium.launch();
const page = await browser.newPage({ viewport: { width: 1400, height: 900 } });

async function measure(label) {
  const m = await page.evaluate(() => {
    const chrome = document.getElementById("app-chrome").getBoundingClientRect();
    const main = document.querySelector(".main-content");
    const first =
      document.querySelector(".tool-workspace .workspace-panel") ||
      document.querySelector(".dashboard-greeting");
    const r = first?.getBoundingClientRect();
    return {
      chromeBottom: Math.round(chrome.bottom),
      mainPaddingTop: getComputedStyle(main).paddingTop,
      firstTop: r ? Math.round(r.top) : null,
      overlap: r ? Math.round(chrome.bottom - r.top) : null,
      electron: document.body.classList.contains("electron-desktop"),
    };
  });
  console.log(label, JSON.stringify(m));
}

for (const url of ["http://127.0.0.1:5000/", "http://127.0.0.1:5000/text/base64"]) {
  await page.goto(url, { waitUntil: "networkidle" });
  await measure(`web ${url}`);
  await page.evaluate(() => {
    document.body.classList.add("electron-desktop");
    document.documentElement.classList.add("electron-desktop");
    ["title-bar", "chrome-sidebar-brand", "electron-menu-bar"].forEach((id) => {
      const el = document.getElementById(id);
      if (el) el.hidden = false;
    });
  });
  await page.waitForTimeout(250);
  await measure(`electron ${url}`);
}

await browser.close();
