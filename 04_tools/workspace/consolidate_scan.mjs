#!/usr/bin/env node
/**
 * Workspace duplicate scanner / quarantiner.
 *
 * Walks C:\\Users\\jerom\\Desktop\\claude (or --root), SHA-256s every file,
 * writes consolidate_plan.csv, default dry-run. --execute moves only
 * action=quarantine rows to _quarantine/<YYYY-MM-DD>/… — never deletes.
 *
 *   node consolidate_scan.mjs
 *   node consolidate_scan.mjs --execute
 *
 * Skip (hard rules): 07_deploy, .claude/worktrees, 90_archive, 91_legacy,
 * any _archive, .git, node_modules, .next, .netlify, .vercel, _quarantine,
 * directory junctions / symlinks (Prive, mypens, …).
 */

import fs from "node:fs";
import fsp from "node:fs/promises";
import path from "node:path";
import crypto from "node:crypto";
import { fileURLToPath } from "node:url";

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const ISZE_ROOT = path.resolve(__dirname, "..", "..");
const DEFAULT_WORKSPACE = path.resolve(ISZE_ROOT, "..");
const TODAY = "2026-08-13";

const SKIP_DIR_EXACT = new Set([
  ".git",
  "node_modules",
  ".next",
  ".netlify",
  ".vercel",
  "_quarantine",
]);

const argv = process.argv.slice(2);
const EXECUTE = argv.includes("--execute");
const rootArg = argv.find((a) => a.startsWith("--root="));
const WORKSPACE = path.resolve(rootArg ? rootArg.slice("--root=".length) : DEFAULT_WORKSPACE);
const PLAN_CSV = path.join(__dirname, "consolidate_plan.csv");
const QUARANTINE_ROOT = path.join(WORKSPACE, "_quarantine", TODAY);
const HASH_CONCURRENCY = 12;

function toPosix(p) {
  return p.split(path.sep).join("/");
}

function relOf(abs) {
  return toPosix(path.relative(WORKSPACE, abs));
}

function isReparse(abs) {
  try {
    return fs.lstatSync(abs).isSymbolicLink();
  } catch {
    return true;
  }
}

function shouldSkipDir(rel, name) {
  const lower = name.toLowerCase();
  if (SKIP_DIR_EXACT.has(name) || SKIP_DIR_EXACT.has(lower)) return true;
  if (lower === "_archive") return true;
  if (rel === "ISZE/07_deploy" || rel.startsWith("ISZE/07_deploy/")) return true;
  if (rel === "ISZE/.claude/worktrees" || rel.startsWith("ISZE/.claude/worktrees/")) return true;
  if (rel === "ISZE/90_archive" || rel.startsWith("ISZE/90_archive/")) return true;
  if (rel === "ISZE/91_legacy" || rel.startsWith("ISZE/91_legacy/")) return true;
  const parts = rel.split("/");
  if (parts.some((p) => p.toLowerCase() === "_archive")) return true;
  return false;
}

function is01(rel) {
  return rel === "ISZE/01_data" || rel.startsWith("ISZE/01_data/");
}

function isDashData(rel) {
  return rel === "ISZE/02_dashboards/Data" || rel.startsWith("ISZE/02_dashboards/Data/");
}

function strip01(rel) {
  return rel.startsWith("ISZE/01_data/") ? rel.slice("ISZE/01_data/".length) : null;
}

function stripData(rel) {
  return rel.startsWith("ISZE/02_dashboards/Data/")
    ? rel.slice("ISZE/02_dashboards/Data/".length)
    : null;
}

function csvEscape(s) {
  const t = String(s ?? "");
  if (/[",\r\n]/.test(t)) return `"${t.replaceAll('"', '""')}"`;
  return t;
}

function fmtBytes(n) {
  if (n < 1024) return `${n} B`;
  if (n < 1024 ** 2) return `${(n / 1024).toFixed(1)} KB`;
  if (n < 1024 ** 3) return `${(n / 1024 ** 2).toFixed(1)} MB`;
  return `${(n / 1024 ** 3).toFixed(2)} GB`;
}

function parseBackup(name) {
  const m = name.match(/^(.*)\.backup_(\d{8})(?:_(\d+))?(.*)$/i);
  if (!m) return null;
  return {
    stem: m[1],
    ymd: m[2],
    hhmm: m[3] || "",
    rest: m[4] || "",
    stamp: m[2] + (m[3] || ""),
  };
}

async function walkFiles(root) {
  const files = [];
  const stack = [root];
  while (stack.length) {
    const dir = stack.pop();
    let entries;
    try {
      entries = await fsp.readdir(dir, { withFileTypes: true });
    } catch {
      continue;
    }
    for (const ent of entries) {
      const abs = path.join(dir, ent.name);
      const rel = relOf(abs);
      if (ent.isSymbolicLink() || isReparse(abs)) continue;
      if (ent.isDirectory()) {
        if (shouldSkipDir(rel, ent.name)) continue;
        stack.push(abs);
        continue;
      }
      if (ent.isFile()) files.push(abs);
    }
  }
  return files;
}

function hashFile(abs) {
  return new Promise((resolve, reject) => {
    const h = crypto.createHash("sha256");
    const s = fs.createReadStream(abs, { highWaterMark: 1024 * 1024 });
    s.on("data", (c) => h.update(c));
    s.on("error", reject);
    s.on("end", () => resolve(h.digest("hex")));
  });
}

async function mapPool(items, n, fn) {
  const out = new Array(items.length);
  let i = 0;
  async function worker() {
    for (;;) {
      const idx = i++;
      if (idx >= items.length) return;
      out[idx] = await fn(items[idx], idx);
    }
  }
  await Promise.all(Array.from({ length: Math.min(n, items.length) }, worker));
  return out;
}

function bucketRank(rel) {
  if (
    rel.startsWith("ISZE/") ||
    rel.startsWith("Projects/") ||
    rel.startsWith("Private/")
  ) {
    return 0;
  }
  if (rel.startsWith("my-pens-app/")) return 2;
  return 1;
}

function pickKeeper(files) {
  return files.slice().sort((a, b) => {
    const br = bucketRank(a.rel) - bucketRank(b.rel);
    if (br !== 0) return br;
    const a01 = is01(a.rel);
    const b01 = is01(b.rel);
    const aD = isDashData(a.rel);
    const bD = isDashData(b.rel);
    if (a01 && bD) return -1;
    if (b01 && aD) return 1;
    if (a.rel.length !== b.rel.length) return a.rel.length - b.rel.length;
    if (b.mtimeMs !== a.mtimeMs) return b.mtimeMs - a.mtimeMs;
    return a.rel.localeCompare(b.rel);
  })[0];
}

function resolveKeeperChains(rows) {
  const qMap = new Map();
  for (const r of rows) {
    if (r.action === "quarantine") qMap.set(r.candidate_path, r.keeper_path);
  }
  function finalKeeper(start) {
    const seen = new Set();
    let p = start;
    while (qMap.has(p)) {
      if (seen.has(p)) {
        throw new Error(`keeper cycle at ${p}`);
      }
      seen.add(p);
      p = qMap.get(p);
    }
    return p;
  }
  const out = [];
  let chained = 0;
  for (const r of rows) {
    if (r.action !== "quarantine") {
      out.push(r);
      continue;
    }
    const k = finalKeeper(r.keeper_path);
    if (k !== r.keeper_path) chained++;
    if (k === r.candidate_path) continue;
    out.push({ ...r, keeper_path: k });
  }
  const stillCandidate = new Set(
    out.filter((r) => r.action === "quarantine").map((r) => r.candidate_path),
  );
  for (const r of out) {
    if (r.action === "quarantine" && stillCandidate.has(r.keeper_path)) {
      throw new Error(`keeper still a candidate after chain resolve: ${r.keeper_path}`);
    }
  }
  if (chained) {
    process.stderr.write(`resolved ${chained} keeper chains\n`);
  }
  return out;
}

function basenameOf(rel) {
  return rel.split("/").pop();
}

function extOf(name) {
  const i = name.lastIndexOf(".");
  return i >= 0 ? name.slice(i).toLowerCase() : "";
}

async function ensureDir(p) {
  await fsp.mkdir(p, { recursive: true });
}

async function main() {
  console.log(`workspace: ${WORKSPACE}`);
  console.log(`mode:      ${EXECUTE ? "EXECUTE (quarantine moves)" : "dry-run"}`);
  console.log(`plan:      ${PLAN_CSV}`);
  console.log(`skip:      07_deploy, worktrees, 90/91 archive, _archive, .git, node_modules, .next, .netlify, .vercel, junctions`);
  console.log("");

  const t0 = Date.now();
  process.stderr.write("walking…\n");
  const absFiles = await walkFiles(WORKSPACE);
  process.stderr.write(`walked ${absFiles.length} files in ${((Date.now() - t0) / 1000).toFixed(1)}s\n`);

  const records = [];
  let hashed = 0;
  let hashErrors = 0;
  const tHash = Date.now();
  await mapPool(absFiles, HASH_CONCURRENCY, async (abs) => {
    let st;
    try {
      st = await fsp.stat(abs);
    } catch {
      hashErrors++;
      return;
    }
    let hash;
    try {
      hash = await hashFile(abs);
    } catch (err) {
      hashErrors++;
      process.stderr.write(`hash fail: ${relOf(abs)} (${err.message})\n`);
      return;
    }
    records.push({
      abs,
      rel: relOf(abs),
      hash,
      bytes: st.size,
      mtimeMs: st.mtimeMs,
    });
    hashed++;
    if (hashed % 1000 === 0) {
      const dt = (Date.now() - tHash) / 1000;
      process.stderr.write(`hashed ${hashed}/${absFiles.length} (${(hashed / dt).toFixed(0)}/s)\n`);
    }
  });
  process.stderr.write(
    `hashed ${hashed} files, ${hashErrors} errors, ${((Date.now() - tHash) / 1000).toFixed(1)}s\n\n`,
  );

  const byRel = new Map(records.map((r) => [r.rel, r]));
  const byHash = new Map();
  for (const r of records) {
    if (!byHash.has(r.hash)) byHash.set(r.hash, []);
    byHash.get(r.hash).push(r);
  }

  const planned = new Set(); // candidate rel already in plan
  const rows = [];

  function addRow({ action, hash, keeper, candidate, reason }) {
    if (planned.has(candidate.rel)) return;
    planned.add(candidate.rel);
    rows.push({
      action,
      hash,
      keeper_path: keeper.rel,
      candidate_path: candidate.rel,
      bytes: candidate.bytes,
      reason,
    });
  }

  // --- 02_dashboards/Data vs 01_data counterparts ---
  let dataFiles = 0;
  let identical01 = 0;
  let divergent01 = 0;
  let uniqueData = 0;
  let salesFactFlag = null;
  const divergentList = [];

  for (const r of records) {
    const rest = stripData(r.rel);
    if (rest == null) continue;
    dataFiles++;
    const counterpartRel = `ISZE/01_data/${rest}`;
    const counterpart = byRel.get(counterpartRel);
    if (!counterpart) {
      uniqueData++;
      continue;
    }
    if (counterpart.hash === r.hash) {
      identical01++;
      addRow({
        action: "quarantine",
        hash: r.hash,
        keeper: counterpart,
        candidate: r,
        reason: "identical_to_01_data",
      });
    } else {
      divergent01++;
      divergentList.push({
        data: r,
        src: counterpart,
      });
    }
    if (rest === "00_derived/sales_fact.csv") {
      salesFactFlag = { data: r, src: counterpart, same: counterpart.hash === r.hash };
    }
  }

  // --- dated backups first (so they are not stuck as report:identical_other) ---
  const backupGroups = new Map();
  for (const r of records) {
    const name = basenameOf(r.rel);
    const info = parseBackup(name);
    if (!info) continue;
    const dir = r.rel.slice(0, r.rel.length - name.length);
    const key = `${dir}|${info.stem}|${info.rest}`;
    if (!backupGroups.has(key)) backupGroups.set(key, []);
    backupGroups.get(key).push({ rec: r, info });
  }
  for (const [, group] of backupGroups) {
    if (group.length < 2) continue;
    group.sort((a, b) => {
      if (b.info.stamp !== a.info.stamp) return b.info.stamp.localeCompare(a.info.stamp);
      return b.rec.mtimeMs - a.rec.mtimeMs;
    });
    const keeper = group[0].rec;
    for (const { rec } of group.slice(1)) {
      if (planned.has(rec.rel)) continue;
      addRow({
        action: "quarantine",
        hash: rec.hash,
        keeper,
        candidate: rec,
        reason: "dated_backup",
      });
    }
  }

  // --- hash groups: remaining extras ---
  for (const [hash, group] of byHash) {
    if (group.length < 2) continue;
    const survivors = group.filter((f) => !planned.has(f.rel));
    if (!survivors.length) continue;
    const keeper = pickKeeper(survivors);
    const keeperBase = basenameOf(keeper.rel);
    for (const f of group) {
      if (f.rel === keeper.rel) continue;
      if (planned.has(f.rel)) continue;
      if (f.bytes === 0) {
        addRow({
          action: "report",
          hash,
          keeper,
          candidate: f,
          reason: "empty_duplicate",
        });
        continue;
      }
      const base = basenameOf(f.rel);
      if (base !== keeperBase) {
        addRow({
          action: "report",
          hash,
          keeper,
          candidate: f,
          reason: "misleading_name",
        });
        continue;
      }
      if (extOf(base) === ".html") {
        addRow({
          action: "quarantine",
          hash,
          keeper,
          candidate: f,
          reason: "duplicate_same_basename",
        });
        continue;
      }
      addRow({
        action: "report",
        hash,
        keeper,
        candidate: f,
        reason: "identical_other",
      });
    }
  }

  const chainedRows = resolveKeeperChains(rows);
  rows.length = 0;
  rows.push(...chainedRows);
  rows.sort((a, b) => b.bytes - a.bytes || a.candidate_path.localeCompare(b.candidate_path));

  const header = "action,hash,keeper_path,candidate_path,bytes,reason";
  const csv = [
    header,
    ...rows.map((r) =>
      [r.action, r.hash, r.keeper_path, r.candidate_path, r.bytes, r.reason]
        .map(csvEscape)
        .join(","),
    ),
  ].join("\n");
  await fsp.writeFile(PLAN_CSV, csv, "utf8");

  const byReason = new Map();
  for (const r of rows) {
    const key = `${r.action}:${r.reason}`;
    if (!byReason.has(key)) byReason.set(key, { n: 0, bytes: 0 });
    const s = byReason.get(key);
    s.n++;
    s.bytes += r.bytes;
  }
  const qRows = rows.filter((r) => r.action === "quarantine");
  const qBytes = qRows.reduce((s, r) => s + r.bytes, 0);

  console.log("=== 02_dashboards/Data vs 01_data ===");
  console.log(`  files in Data/           ${dataFiles}`);
  console.log(`  identical counterpart    ${identical01}   (${fmtBytes(qRows.filter((r) => r.reason === "identical_to_01_data").reduce((s, r) => s + r.bytes, 0))})`);
  console.log(`  divergent same-path      ${divergent01}`);
  console.log(`  unique to Data/          ${uniqueData}`);
  if (salesFactFlag) {
    const smaller = salesFactFlag.data.bytes < salesFactFlag.src.bytes;
    const tag = smaller ? "STALE COPY — Data is SMALLER than 01_data (line-level billing)" : "sizes ok or Data larger";
    console.log(
      `  sales_fact.csv            Data ${fmtBytes(salesFactFlag.data.bytes)} vs 01_data ${fmtBytes(salesFactFlag.src.bytes)}  same_hash=${salesFactFlag.same}  ${tag}`,
    );
  } else {
    console.log("  sales_fact.csv            not present as a same-path pair");
  }
  console.log("");

  console.log("=== plan totals ===");
  const keys = [...byReason.keys()].sort();
  for (const k of keys) {
    const s = byReason.get(k);
    console.log(`  ${k.padEnd(40)} ${String(s.n).padStart(5)} files   ${fmtBytes(s.bytes)}`);
  }
  console.log("");
  console.log(`  QUARANTINE (reclaimable)               ${String(qRows.length).padStart(5)} files   ${fmtBytes(qBytes)}`);
  console.log(`  plan written: ${PLAN_CSV}`);
  console.log("");

  console.log("=== 20 largest quarantine candidates ===");
  const top = qRows.slice(0, 20);
  for (const r of top) {
    console.log(
      `  ${fmtBytes(r.bytes).padStart(10)}  ${r.reason.padEnd(26)}  ${r.candidate_path}`,
    );
    console.log(`             keeper: ${r.keeper_path}`);
  }
  if (!top.length) console.log("  (none)");
  console.log("");

  const misleading = rows.filter((r) => r.reason === "misleading_name");
  if (misleading.length) {
    console.log("=== misleading names (report only — not quarantined) ===");
    for (const r of misleading.slice(0, 30)) {
      console.log(`  ${fmtBytes(r.bytes).padStart(10)}  ${r.candidate_path}`);
      console.log(`             identical to: ${r.keeper_path}`);
    }
    if (misleading.length > 30) console.log(`  … +${misleading.length - 30} more`);
    console.log("");
  }

  if (divergentList.length) {
    console.log(`=== divergent same-path (Data vs 01_data) — first 15 of ${divergentList.length} ===`);
    const shown = divergentList
      .slice()
      .sort((a, b) => b.data.bytes - a.data.bytes)
      .slice(0, 15);
    for (const d of shown) {
      console.log(
        `  Data ${fmtBytes(d.data.bytes).padStart(8)} | 01_data ${fmtBytes(d.src.bytes).padStart(8)}  ${stripData(d.data.rel)}`,
      );
    }
    console.log("");
  }

  if (!EXECUTE) {
    console.log("Dry-run only. Re-run with --execute to move quarantine rows to:");
    console.log(`  ${QUARANTINE_ROOT}`);
    return;
  }

  console.log(`EXECUTE: moving ${qRows.length} files → ${QUARANTINE_ROOT}`);
  const moved = [];
  for (const r of qRows) {
    const src = path.join(WORKSPACE, ...r.candidate_path.split("/"));
    const dest = path.join(QUARANTINE_ROOT, ...r.candidate_path.split("/"));
    const keeperAbs = path.join(WORKSPACE, ...r.keeper_path.split("/"));
    if (!fs.existsSync(src)) {
      console.error(`ABORT: candidate missing before move: ${r.candidate_path}`);
      await restoreAll(moved);
      process.exit(1);
    }
    if (!fs.existsSync(keeperAbs)) {
      console.error(`ABORT: keeper missing before move: ${r.keeper_path}`);
      await restoreAll(moved);
      process.exit(1);
    }
    if (fs.existsSync(dest)) {
      console.error(`ABORT: quarantine dest already exists: ${dest}`);
      await restoreAll(moved);
      process.exit(1);
    }
    await ensureDir(path.dirname(dest));
    await fsp.rename(src, dest);
    moved.push({ src, dest, keeperAbs, hash: r.hash, keeperPath: r.keeper_path });
  }

  console.log(`moved ${moved.length}; verifying keepers still present and hash-unchanged…`);
  for (const r of qRows) {
    const keeperAbs = path.join(WORKSPACE, ...r.keeper_path.split("/"));
    if (!fs.existsSync(keeperAbs)) {
      console.error(`VERIFY FAIL: keeper missing after moves: ${r.keeper_path}`);
      await restoreAll(moved);
      process.exit(1);
    }
    const keeperRec = byRel.get(r.keeper_path);
    if (!keeperRec) {
      console.error(`VERIFY FAIL: keeper was not in scan index: ${r.keeper_path}`);
      await restoreAll(moved);
      process.exit(1);
    }
    const live = await hashFile(keeperAbs);
    if (live !== keeperRec.hash) {
      console.error(`VERIFY FAIL: keeper hash changed: ${r.keeper_path}`);
      await restoreAll(moved);
      process.exit(1);
    }
  }

  console.log(`OK: ${moved.length} files quarantined; all keepers present and hash-unchanged.`);
}

async function restoreAll(moved) {
  console.error(`Restoring ${moved.length} files from quarantine…`);
  for (const m of [...moved].reverse()) {
    try {
      if (fs.existsSync(m.dest) && !fs.existsSync(m.src)) {
        await ensureDir(path.dirname(m.src));
        await fsp.rename(m.dest, m.src);
      }
    } catch (err) {
      console.error(`restore failed ${m.dest} → ${m.src}: ${err.message}`);
    }
  }
}

main().catch((err) => {
  console.error(err);
  process.exit(1);
});
