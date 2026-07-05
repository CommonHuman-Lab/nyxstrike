// SPDX-License-Identifier: AGPL-3.0-or-later
// Copyright (c) 2026 CommonHuman-Lab
//
// screenshot-themes-slices.mjs — combine the per-theme dashboard screenshots
// produced by screenshot-themes.mjs into one composite JPG, cropping each
// theme's screenshot into an equal-width vertical band with a name label.
//
// Usage:
//   node scripts/screenshot-themes-slices.mjs
//
// Env vars (all optional):
//   IN_DIR    default ./themes (next to this script)
//   OUT_FILE  default ./themes-slices.jpg (next to this script)
//   LABEL     "1" to overlay the theme id on each band, default "1"
//   QUALITY   JPG quality (2-31, lower is better), default 3
//
// Requires ffmpeg/ffprobe on PATH.

import fs from "fs";
import path from "path";
import { spawnSync } from "child_process";
import { fileURLToPath } from "url";

const SCRIPT_DIR = path.dirname(fileURLToPath(import.meta.url));

const IN_DIR = process.env.IN_DIR ?? path.join(SCRIPT_DIR, "themes");
const OUT_FILE = process.env.OUT_FILE ?? path.join(SCRIPT_DIR, "themes-slices.jpg");
const LABEL = process.env.LABEL !== "0";
const QUALITY = process.env.QUALITY ?? "3";

function checkTool(name) {
  const res = spawnSync(name, ["-version"], { stdio: "ignore" });
  if (res.error) {
    console.error(`Required tool "${name}" not found on PATH.`);
    process.exit(1);
  }
}

checkTool("ffmpeg");
checkTool("ffprobe");

const files = fs
  .readdirSync(IN_DIR)
  .filter((f) => f.toLowerCase().endsWith(".png"))
  .sort();

if (files.length === 0) {
  console.error(`No PNG files found in ${IN_DIR}.`);
  process.exit(1);
}

const probe = spawnSync("ffprobe", [
  "-v", "error",
  "-select_streams", "v:0",
  "-show_entries", "stream=width,height",
  "-of", "csv=s=x:p=0",
  path.join(IN_DIR, files[0]),
]);
const [srcWidth, srcHeight] = probe.stdout.toString().trim().split("x").map(Number);
if (!srcWidth || !srcHeight) {
  console.error("Could not determine source image dimensions via ffprobe.");
  process.exit(1);
}

const bandWidth = Math.floor(srcWidth / files.length);

console.log(`Building slices JPG from ${files.length} theme(s), band width ${bandWidth}px`);

// Bands are narrow (source width / theme count), so scale the font down to
// fit and split hyphenated ids ("solarized-terminal") onto two lines rather
// than letting long labels overlap neighboring bands.
const fontSize = Math.max(12, Math.min(28, Math.floor(bandWidth / 6)));

const inputs = [];
const filterParts = [];
files.forEach((file, i) => {
  const themeId = path.basename(file, ".png");
  inputs.push("-i", path.join(IN_DIR, file));
  const cropX = i * bandWidth;
  let chain = `[${i}:v]crop=${bandWidth}:${srcHeight}:${cropX}:0`;
  if (LABEL) {
    const label = themeId
      .toUpperCase()
      .split("-")
      .join("\n")
      .replace(/'/g, "\\'")
      .replace(/:/g, "\\:");
    chain += `,drawtext=text='${label}':x=(w-text_w)/2:y=h-70:fontsize=${fontSize}:fontcolor=white:line_spacing=4:box=1:boxcolor=black@0.55:boxborderw=8`;
  }
  chain += `[b${i}]`;
  filterParts.push(chain);
});

const stackInputs = files.map((_, i) => `[b${i}]`).join("");
const filterComplex = filterParts.join(";") + `;${stackInputs}hstack=inputs=${files.length}[out]`;

fs.mkdirSync(path.dirname(OUT_FILE), { recursive: true });

const res = spawnSync("ffmpeg", [
  "-y",
  ...inputs,
  "-filter_complex", filterComplex,
  "-map", "[out]",
  "-q:v", QUALITY,
  "-update", "1",
  OUT_FILE,
], { stdio: "inherit" });

if (res.status !== 0) {
  console.error(`ffmpeg exited with code ${res.status}`);
  process.exit(res.status ?? 1);
}

console.log("Saved slices JPG to", OUT_FILE);
