// SPDX-License-Identifier: AGPL-3.0-or-later
// Copyright (c) 2026 CommonHuman-Lab
//
// screenshot-themes.mjs — capture the dashboard once per available UI theme,
// for README/marketing screenshots.
//
// Usage:
//   1. Start the dashboard dev server: cd ui && npm run dev
//   2. Install dependencies once:
//        npm install && npx playwright install chromium
//   3. Run:
//        node scripts/screenshot-themes.mjs
//
// Env vars (all optional):
//   BASE_URL  default http://localhost:5173
//   OUT_DIR   default ./themes (next to this script)

import { chromium } from "playwright";
import fs from "fs";
import path from "path";
import { fileURLToPath } from "url";

const SCRIPT_DIR = path.dirname(fileURLToPath(import.meta.url));

const BASE_URL = process.env.BASE_URL ?? "http://localhost:5173";
const OUT = process.env.OUT_DIR ?? path.join(SCRIPT_DIR, "themes");

// Keep in sync with ui/src/app/themes.ts THEME_OPTIONS.
const THEME_IDS = [
  "dark", "unicorn", "forest", "solarized", "ocean-glass",
  "crimson-night", "retro-crt", "nord",
  "dracula", "gruvbox", "folio", "tokyo", "catppuccin", "synthwave", "rose", "frost",
];

const THEME_STORAGE_KEY = "nyxstrike_theme";

fs.mkdirSync(OUT, { recursive: true });

const browser = await chromium.launch();
const page = await browser.newPage({ viewport: { width: 1920, height: 1080 }, deviceScaleFactor: 1 });
const consoleErrors = [];
page.on("console", (msg) => {
  if (msg.type() === "error") consoleErrors.push(msg.text());
});
page.on("pageerror", (err) => consoleErrors.push("pageerror: " + err.message));

async function shot(name) {
  await page.waitForTimeout(600);
  await page.screenshot({ path: `${OUT}/${name}.png`, fullPage: true });
  console.log("shot:", name);
}

// Initial load to get a document context to run localStorage writes against.
await page.goto(`${BASE_URL}/?demo=1#/dashboard`, { waitUntil: "networkidle" }).catch(() => {});

for (const themeId of THEME_IDS) {
  // Theme is applied via an effect that only runs on mount, so a plain
  // re-navigation to the same URL is a no-op in Chromium (no URL change ->
  // no reload). Force a real reload after writing the new theme id.
  await page.evaluate(([key, id]) => {
    localStorage.setItem(key, id);
  }, [THEME_STORAGE_KEY, themeId]);
  await page.reload({ waitUntil: "networkidle" }).catch(() => {});
  await shot(themeId);
}

await browser.close();

fs.writeFileSync(`${OUT}/console-errors.json`, JSON.stringify(consoleErrors, null, 2));
console.log(`\nScreenshots written to ${OUT}`);
console.log("console/page errors:", consoleErrors.length);
if (consoleErrors.length > 0) {
  console.log(consoleErrors.join("\n"));
  process.exit(1);
}
