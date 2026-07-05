// SPDX-License-Identifier: AGPL-3.0-or-later
// Copyright (c) 2026 CommonHuman-Lab
//
// screenshot-demo.mjs — drive the NyxStrike dashboard in demo mode and
// capture a full set of page screenshots, for README/marketing/PR screenshots.
//
// Usage:
//   1. Start the dashboard dev server: cd ui && npm run dev
//   2. Install dependencies once:
//        npm install && npx playwright install chromium
//   3. Run:
//        node scripts/screenshot-demo.mjs
//
// Env vars (all optional):
//   BASE_URL             default http://localhost:5173
//   NYXSTRIKE_API_TOKEN  if set, seeds the session with this token instead of
//                        using demo mode, so real backend data is captured
//   OUT_DIR              default ./screenshots (next to this script)
//
// What it does: loads the dashboard with demo mode enabled (?demo=1, see
// ui/src/app/demoUtils.ts), then visits and screenshots each page in nav order.

import { chromium } from "playwright";
import fs from "fs";
import path from "path";
import { fileURLToPath } from "url";

const SCRIPT_DIR = path.dirname(fileURLToPath(import.meta.url));

const BASE_URL = process.env.BASE_URL ?? "http://localhost:5173";
const API_TOKEN = process.env.NYXSTRIKE_API_TOKEN ?? null;
const OUT = process.env.OUT_DIR ?? path.join(SCRIPT_DIR, "screenshots");

fs.mkdirSync(OUT, { recursive: true });

// Matches ui/src/app/navRegistry.ts NAV_ENTRIES order.
const pages = [
  ["01-dashboard", ""],
  ["02-run", "run"],
  ["03-logs", "logs"],
  ["04-settings", "settings"],
  ["05-help", "help"],
  ["06-tasks", "tasks"],
  ["07-tools", "tools"],
  ["08-plugins", "plugins"],
  ["09-reports", "reports"],
  ["10-sessions", "sessions"],
  ["11-loot", "loot"],
];

const browser = await chromium.launch();
const page = await browser.newPage({ viewport: { width: 1920, height: 1080 }, deviceScaleFactor: 1 });
const consoleErrors = [];
page.on("console", (msg) => {
  if (msg.type() === "error") consoleErrors.push(msg.text());
});
page.on("pageerror", (err) => consoleErrors.push("pageerror: " + err.message));

if (API_TOKEN) {
  await page.addInitScript((token) => {
    sessionStorage.setItem("nyxstrike_token", token);
  }, API_TOKEN);
}

async function shot(name) {
  await page.waitForTimeout(600);
  await page.screenshot({ path: `${OUT}/${name}.png`, fullPage: true });
  console.log("shot:", name);
}

async function open(hash) {
  const demoFlag = API_TOKEN ? "" : "?demo=1";
  await page.goto(`${BASE_URL}/${demoFlag}#/${hash}`, { waitUntil: "networkidle" }).catch(() => {});
}

for (const [name, hash] of pages) {
  await open(hash);
  await shot(name);
}

// First session's detail page. SessionCard is a clickable div (not an <a>),
// so click it and wait for the app to route to #/sessions/<id> rather than
// guessing a session id. SessionDetailPage always fetches from the live
// backend (it has no demo-mode branch), so this only produces a real page
// when a live backend + token is used instead of demo mode.
if (API_TOKEN) {
  await open("sessions");
  const sessionCard = page.locator(".session-card").first();
  if (await sessionCard.count() > 0) {
    await sessionCard.click();
    await page.waitForFunction(() => window.location.hash.startsWith("#/sessions/"), { timeout: 5000 }).catch(() => {});
    await shot("10b-session-detail");
  }
}

await browser.close();

fs.writeFileSync(`${OUT}/console-errors.json`, JSON.stringify(consoleErrors, null, 2));
console.log(`\nScreenshots written to ${OUT}`);
console.log("console/page errors:", consoleErrors.length);
if (consoleErrors.length > 0) {
  console.log(consoleErrors.join("\n"));
  process.exit(1);
}
