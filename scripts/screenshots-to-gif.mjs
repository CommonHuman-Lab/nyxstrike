// SPDX-License-Identifier: AGPL-3.0-or-later
// Copyright (c) 2026 CommonHuman-Lab
//
// screenshots-to-gif.mjs — stitch a directory of PNG screenshots into a
// crossfade GIF, for README/marketing content.
//
// Usage:
//   node scripts/screenshots-to-gif.mjs
//
// Env vars (all optional):
//   IN_DIR          default ./screenshots (next to this script)
//   OUT_FILE        default ./demo.gif (next to this script)
//   SKIP            comma-separated substrings; filenames containing any are excluded
//   ONLY            comma-separated substrings; only filenames containing one are included
//   WIDTH           output width in px, default 1280
//   HEIGHT          output height in px, default round(WIDTH * 9/16); source
//                   screenshots are full-page (variable height), so each frame
//                   is scaled to cover WIDTHxHEIGHT and top-cropped to fit —
//                   xfade requires every input frame to share exact dimensions
//   FPS             palette/output fps, default 12
//   HOLD_MS         time each frame is held before crossfading out, default 1000
//   FIRST_HOLD_MS   hold time for the first frame (overrides HOLD_MS), optional
//   LAST_HOLD_MS    hold time for the last frame (overrides HOLD_MS), optional
//   FADE_MS         crossfade duration between frames, default 400
//   LOOP_FADE       "1" to crossfade from the last frame back to the first, default "0"
//
// Requires ffmpeg/ffprobe on PATH.

import fs from "fs";
import path from "path";
import { spawnSync } from "child_process";
import { fileURLToPath } from "url";

const SCRIPT_DIR = path.dirname(fileURLToPath(import.meta.url));

const IN_DIR = process.env.IN_DIR ?? path.join(SCRIPT_DIR, "screenshots");
const OUT_FILE = process.env.OUT_FILE ?? path.join(SCRIPT_DIR, "demo.gif");
const SKIP = (process.env.SKIP ?? "").split(",").map((s) => s.trim()).filter(Boolean);
const ONLY = (process.env.ONLY ?? "").split(",").map((s) => s.trim()).filter(Boolean);
const WIDTH = Number(process.env.WIDTH ?? 1280);
const HEIGHT = Number(process.env.HEIGHT ?? Math.round((WIDTH * 9) / 16));
const FPS = Number(process.env.FPS ?? 12);
const HOLD_MS = Number(process.env.HOLD_MS ?? 1000);
const FIRST_HOLD_MS = Number(process.env.FIRST_HOLD_MS ?? HOLD_MS);
const LAST_HOLD_MS = Number(process.env.LAST_HOLD_MS ?? HOLD_MS);
const FADE_MS = Number(process.env.FADE_MS ?? 400);
const LOOP_FADE = process.env.LOOP_FADE === "1";

function run(cmd, args) {
  const res = spawnSync(cmd, args, { stdio: "inherit" });
  if (res.status !== 0) {
    console.error(`${cmd} exited with code ${res.status}`);
    process.exit(res.status ?? 1);
  }
}

function checkTool(name) {
  const res = spawnSync(name, ["-version"], { stdio: "ignore" });
  if (res.error) {
    console.error(`Required tool "${name}" not found on PATH.`);
    process.exit(1);
  }
}

checkTool("ffmpeg");
checkTool("ffprobe");

let files = fs
  .readdirSync(IN_DIR)
  .filter((f) => f.toLowerCase().endsWith(".png"))
  .sort();

if (ONLY.length > 0) {
  files = files.filter((f) => ONLY.some((s) => f.includes(s)));
}
if (SKIP.length > 0) {
  files = files.filter((f) => !SKIP.some((s) => f.includes(s)));
}

if (files.length === 0) {
  console.error(`No PNG files found in ${IN_DIR} after applying ONLY/SKIP filters.`);
  process.exit(1);
}

console.log(`Building GIF from ${files.length} frame(s):`, files.join(", "));

const frames = LOOP_FADE ? [...files, files[0]] : files;
const holdSeconds = (i) => {
  const ms = i === 0 ? FIRST_HOLD_MS : i === frames.length - 1 ? LAST_HOLD_MS : HOLD_MS;
  return (ms + FADE_MS) / 1000;
};

const inputs = [];
const filterParts = [];
frames.forEach((file, i) => {
  inputs.push("-loop", "1", "-t", String(holdSeconds(i)), "-i", path.join(IN_DIR, file));
  filterParts.push(
    `[${i}:v]scale=${WIDTH}:${HEIGHT}:force_original_aspect_ratio=increase,crop=${WIDTH}:${HEIGHT}:0:0,fps=${FPS},format=yuva420p,setsar=1[v${i}]`
  );
});

let last = "v0";
let chainParts = [];
for (let i = 1; i < frames.length; i++) {
  const out = `x${i}`;
  const offset = holdSeconds(i - 1) - FADE_MS / 1000;
  chainParts.push(`[${last}][v${i}]xfade=transition=fade:duration=${FADE_MS / 1000}:offset=${offset.toFixed(3)}[${out}]`);
  last = out;
}

const filterComplex =
  filterParts.join(";") + (chainParts.length ? ";" + chainParts.join(";") : "") +
  `;[${last}]split[gp][gv];[gp]palettegen=stats_mode=diff[pal];[gv][pal]paletteuse=dither=sierra2_4a[final]`;

fs.mkdirSync(path.dirname(OUT_FILE), { recursive: true });

run("ffmpeg", [
  "-y",
  ...inputs,
  "-filter_complex", filterComplex,
  "-map", "[final]",
  OUT_FILE,
]);

console.log("Saved GIF to", OUT_FILE);
