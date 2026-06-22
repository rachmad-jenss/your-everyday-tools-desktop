import { chromium } from "playwright";
import fs from "fs";
import path from "path";
import os from "os";

const TINY_PNG = Buffer.from(
    "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8z8BQDwAEhQGAhKmMIQAAAABJRU5ErkJggg==",
    "base64",
);

const tmpPng = path.join(os.tmpdir(), "yet-test-upload.png");
fs.writeFileSync(tmpPng, TINY_PNG);

const browser = await chromium.launch();
const page = await browser.newPage({ viewport: { width: 1400, height: 900 } });

let failed = false;
function fail(msg) {
    console.error("FAIL", msg);
    failed = true;
}

await page.goto("http://127.0.0.1:5000/convert/to-pdf", { waitUntil: "networkidle" });

if (!(await page.locator("#upload-add-more").count())) {
    fail("missing #upload-add-more");
}

await page.locator("#file-input").setInputFiles(tmpPng);
await page.waitForTimeout(300);

const addMoreVisible = await page.locator("#upload-add-more").isVisible();
if (!addMoreVisible) fail("add-more button should be visible after file select");

const emptyText = await page.locator("#workspace-preview-empty p").textContent();
if (!emptyText?.includes("ready")) fail(`unexpected empty state: ${emptyText}`);

if (await page.locator("#workspace-preview-grid img").count()) {
    fail("output grid should not show input thumbnails before convert");
}

await page.locator("#submit-btn").click();

try {
    await page.waitForFunction(
        () => {
            const grid = document.querySelector("#workspace-preview-grid");
            return grid && !grid.hidden && (grid.querySelector("iframe") || grid.querySelector("img"));
        },
        { timeout: 30000 },
    );
} catch {
    const err = await page.locator("#workspace-preview-empty p").textContent();
    fail(`conversion did not show preview: ${err}`);
}

const iframe = page.locator("#workspace-preview-grid iframe");
const dl = page.locator("#preview-download-btn");
if (!(await iframe.count()) && !(await page.locator("#workspace-preview-grid img").count())) {
    fail("no pdf iframe or image preview after convert");
}
if (!(await dl.isVisible())) fail("download button not visible");
if (await page.locator("#download-btn").count()) fail("legacy green download button should be removed");

const dlCount = await page.locator("a[download], button:has-text('Download')").count();
if (dlCount > 2) fail(`too many download controls: ${dlCount}`);

await browser.close();
fs.unlinkSync(tmpPng);

if (failed) process.exit(1);
console.log("Browser upload workspace test passed.");
