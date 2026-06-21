import fs from "fs";
import path from "path";
import { fileURLToPath } from "url";
import sharp from "sharp";
import pngToIco from "png-to-ico";

const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");
const svg = fs.readFileSync(path.join(root, "static/favicon.svg"));
const sizes = [16, 24, 32, 48, 64, 128, 256];
const pngBuffers = await Promise.all(
  sizes.map((size) => sharp(svg).resize(size, size).png().toBuffer()),
);
const ico = await pngToIco(pngBuffers);
const out = path.join(root, "images/icon.ico");
fs.writeFileSync(out, ico);
console.log(`Wrote ${out} (${ico.length} bytes, sizes: ${sizes.join(", ")})`);
