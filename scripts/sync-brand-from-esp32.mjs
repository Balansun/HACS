#!/usr/bin/env node
/**
 * Copy canonical brand SVGs from Balansun-ESP32 (sibling repo or BALANSUN_ESP32_ROOT).
 * Edit sources only under ESP32-router/assets/brand/.
 */
import { copyFileSync, existsSync, mkdirSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";

const root = join(dirname(fileURLToPath(import.meta.url)), "..");
const esp32Brand =
  process.env.BALANSUN_ESP32_ROOT?.trim()
    ? join(process.env.BALANSUN_ESP32_ROOT.trim(), "assets", "brand")
    : join(root, "..", "ESP32-router", "assets", "brand");
const outDir = join(root, "assets", "brand");

const files = [
  "balansun-icon-light.svg",
  "balansun-icon-dark.svg",
  "balansun-logo-light.svg",
  "balansun-logo-dark.svg",
];

if (!existsSync(esp32Brand)) {
  console.error(`sync-brand-from-esp32: missing ${esp32Brand}`);
  console.error("Set BALANSUN_ESP32_ROOT to your Balansun-Router clone path.");
  process.exit(1);
}

mkdirSync(outDir, { recursive: true });
for (const name of files) {
  const src = join(esp32Brand, name);
  if (!existsSync(src)) {
    console.error(`sync-brand-from-esp32: missing ${src}`);
    process.exit(1);
  }
  copyFileSync(src, join(outDir, name));
  console.log(`sync-brand-from-esp32: ${name}`);
}
