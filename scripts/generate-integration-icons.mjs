#!/usr/bin/env node
/**
 * PNG brand assets for Home Assistant / HACS (HA 2026.3+ inline brand/ folder).
 * Outputs:
 *   custom_components/balansun/brand/icon.png, icon@2x.png, logo.png, logo@2x.png
 *   custom_components/balansun/brand/dark_icon.png, dark_icon@2x.png, dark_logo.png, dark_logo@2x.png
 */
import { mkdirSync, readFileSync, writeFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";
import sharp from "sharp";

const root = join(dirname(fileURLToPath(import.meta.url)), "..");
const brandDir = join(root, "assets", "brand");
const iconLightSvg = join(brandDir, "balansun-icon-light.svg");
const iconDarkSvg = join(brandDir, "balansun-icon-dark.svg");
const logoLightSvg = join(brandDir, "balansun-logo-light.svg");
const logoDarkSvg = join(brandDir, "balansun-logo-dark.svg");

const OUT_DIR = join(root, "custom_components", "balansun", "brand");

function writePng(path, buffer) {
  writeFileSync(path, buffer);
}

async function squareIcon(svg, size) {
  return sharp(svg)
    .resize(size, size, { fit: "contain", background: { r: 0, g: 0, b: 0, alpha: 0 } })
    .png({ compressionLevel: 9, progressive: true })
    .toBuffer();
}

/** Logo: shortest side in [minSide, maxSide], preserve aspect ratio. */
async function landscapeLogo(svg, minSide, maxSide) {
  const meta = await sharp(svg).metadata();
  const w = meta.width ?? 1;
  const h = meta.height ?? 1;
  const short = Math.min(w, h);
  const targetShort = Math.min(maxSide, Math.max(minSide, short));
  const scale = targetShort / short;
  const width = Math.round(w * scale);
  const height = Math.round(h * scale);
  return sharp(svg)
    .resize(width, height, { fit: "inside", background: { r: 0, g: 0, b: 0, alpha: 0 } })
    .png({ compressionLevel: 9, progressive: true })
    .toBuffer();
}

async function emitSet(outDir) {
  mkdirSync(outDir, { recursive: true });
  const iconLight = readFileSync(iconLightSvg);
  const iconDark = readFileSync(iconDarkSvg);
  const logoLight = readFileSync(logoLightSvg);
  const logoDark = readFileSync(logoDarkSvg);

  const files = [
    ["icon.png", await squareIcon(iconLight, 256)],
    ["icon@2x.png", await squareIcon(iconLight, 512)],
    ["dark_icon.png", await squareIcon(iconDark, 256)],
    ["dark_icon@2x.png", await squareIcon(iconDark, 512)],
    ["logo.png", await landscapeLogo(logoLight, 128, 256)],
    ["logo@2x.png", await landscapeLogo(logoLight, 256, 512)],
    ["dark_logo.png", await landscapeLogo(logoDark, 128, 256)],
    ["dark_logo@2x.png", await landscapeLogo(logoDark, 256, 512)],
  ];

  for (const [name, buf] of files) {
    writePng(join(outDir, name), buf);
  }
}

await emitSet(OUT_DIR);
console.log(`generate-integration-icons: wrote ${OUT_DIR}`);
