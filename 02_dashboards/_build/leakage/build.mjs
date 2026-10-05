#!/usr/bin/env node
/* Distributor leakage cockpit + sales performance review packs.
 *
 * One payload, two audiences:
 *   node build.mjs                             -> internal cockpit, all markets, partner league
 *   node build.mjs --audience=customer --focus=ITUK
 *                                              -> one self-contained pack for one distributor
 *
 * The customer switch does three things, in this order:
 *   1. Only the focus market's rows are written into the file.
 *   2. Peer benchmarks are reduced to a number and a member COUNT. The codes of the
 *      other markets never enter the payload, so they cannot leak from it.
 *   3. Any module declaring `audience: ["internal"]` is skipped entirely. Its render
 *      source is not compiled, so even internal field names are absent from the file.
 *
 * That is the difference between hiding something and not shipping it.
 */
import fs from "node:fs";
import path from "node:path";
import { fileURLToPath, pathToFileURL } from "node:url";

import { assertLabelsClean, L } from "./labels.mjs";
import { CSS } from "./theme.mjs";
import * as charts from "./charts.mjs";

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const ROOT = process.env.ISZE_ROOT || path.resolve(__dirname, "..", "..", "..");
const PAYLOAD_PATH = path.join(__dirname, "payload.json");
const MODULE_DIR = path.join(__dirname, "modules");
const OUT_DIR = path.join(ROOT, "02_dashboards", "sales");
const PACK_DIR = path.join(OUT_DIR, "leakage_packs");
const MIN_PEER = 3;

const args = Object.fromEntries(process.argv.slice(2).map((a) => {
  const [k, v] = a.replace(/^--/, "").split("=");
  return [k, v ?? true];
}));
const audience = args.audience === "customer" ? "customer" : "internal";
const focus = args.focus ? String(args.focus).toUpperCase() : null;
if (audience === "customer" && !focus) {
  console.error("  ! --audience=customer requires --focus=<DISTRIBUTOR_CODE>");
  process.exit(1);
}

/* Serialise a function for inlining. Object shorthand methods stringify to something
 * that is not a valid expression, so they are promoted to named function expressions. */
function fnSource(fn) {
  const s = fn.toString().trim();
  if (/^(function\b|async\s+function\b|\()/.test(s)) return s;
  if (/^[A-Za-z_$][\w$]*\s*=>/.test(s)) return s;
  return "function " + s;
}

/* Emit an object as a JS literal, keeping functions as callable source. Used for the
 * label dictionary, which carries a couple of dynamic strings. */
function withFns(value, indent = 0) {
  const pad = "  ".repeat(indent);
  const pad2 = "  ".repeat(indent + 1);
  if (typeof value === "function") return fnSource(value);
  if (value === undefined) return "undefined";
  if (typeof value === "string") return JSON.stringify(value);
  if (value === null || typeof value !== "object") return JSON.stringify(value);
  if (Array.isArray(value)) {
    if (!value.length) return "[]";
    return "[\n" + value.map((v) => pad2 + withFns(v, indent + 1)).join(",\n") + "\n" + pad + "]";
  }
  // Drop undefined, null, empty-string, empty-array and empty-object members: an empty key
  // still puts the word in the file, which is precisely what a customer strip must prevent.
  const drop = (v) => v === undefined || v === null || v === ""
    || (Array.isArray(v) && v.length === 0)
    || (typeof v === "object" && !Array.isArray(v) && Object.keys(v).length === 0);
  const keys = Object.keys(value).filter((k) => !drop(value[k]));
  if (!keys.length) return "{}";
  return "{\n" + keys.map((k) =>
    `${pad2}${JSON.stringify(k)}: ${withFns(value[k], indent + 1)}`).join(",\n") + "\n" + pad + "}";
}

/* ---------------------------------------------------------------- payload */
if (!fs.existsSync(PAYLOAD_PATH)) {
  console.error(`  ! payload missing -> ${PAYLOAD_PATH}`);
  console.error("    run: python 02_dashboards\\_build\\leakage\\extract.py");
  process.exit(1);
}
const payload = JSON.parse(fs.readFileSync(PAYLOAD_PATH, "utf8"));
const { meta, dbs, network_dbs: networkDbs, peer_groups: peerGroups, modules } = payload;

if (!meta.verification?.ok) {
  console.error("  ! verification report is not green - refusing to build");
  process.exit(1);
}

const dbName = (code) => dbs[code]?.name || code;

/* ------------------------------------------------------- peer benchmark maths */
const median = (xs) => {
  const a = [...xs].filter((x) => typeof x === "number" && Number.isFinite(x)).sort((x, y) => x - y);
  if (!a.length) return null;
  const m = Math.floor(a.length / 2);
  return a.length % 2 ? a[m] : (a[m - 1] + a[m]) / 2;
};

/* For every peer group and every module, precompute the median of each metric field.
 * Precomputed so the customer file needs a number, not the other markets' rows. */
const peerMedians = {};
for (const [key, g] of Object.entries(peerGroups)) {
  const med = {};
  for (const [mid, mod] of Object.entries(modules)) {
    if (!mod.rows?.length) continue;
    const rows = mod.rows.filter((r) => g.members.includes(r.db));
    const per = {};
    for (const field of (mod.peer_metrics || [])) {
      per[field] = median(rows.map((r) => r[field]));
    }
    // mix needs a family-level median so each family bar has its own reference
    if (mid === "mix") {
      const fams = {};
      const allFams = new Set(rows.flatMap((r) => (r.families || []).map((f) => f.family)));
      for (const fam of allFams) {
        fams[fam] = median(rows.flatMap((r) =>
          (r.families || []).filter((f) => f.family === fam).map((f) => f.bvp_share_pct)));
      }
      per.familyBvp = fams;
    }
    med[mid] = per;
  }
  peerMedians[key] = med;
}

/* Which peer groups a given distributor can legitimately be compared against.
 * Customer-type first, per Jerome: an LCV market against LCV markets. Exact type, then the
 * customer-type pool, then region, then everything - the first that is not too thin. */
function groupsFor(code) {
  const info = dbs[code];
  if (!info) return ["all"];
  const u = info.uio_2025;
  const fleet = (u === null || u === undefined) ? null
    : (u < 2000 ? "fleet:xs" : u < 10000 ? "fleet:s" : u < 25000 ? "fleet:m" : "fleet:l");
  const order = [`scope:${info.scope}`, `pool:${info.scope}`, `region:${info.region}`];
  if (fleet) order.push(fleet);
  order.push("all");
  return order.filter((k) => peerGroups[k]);
}

/* The best defensible benchmark for one market: the first group in preference order that is
 * neither too thin nor absent, preferring a group this market belongs to. */
function defaultPeerFor(code) {
  const info = dbs[code];
  if (!info) return "all";
  const prefer = [`scope:${info.scope}`, `pool:${info.scope}`, `region:${info.region}`, "all"];
  for (const key of prefer) {
    const g = peerGroups[key];
    if (g && !g.thin && g.members.includes(code)) return key;
  }
  for (const key of prefer) {
    const g = peerGroups[key];
    if (g && !g.thin) return key;
  }
  return "all";
}

/* ------------------------------------------------------------- module loading */
const moduleFiles = fs.readdirSync(MODULE_DIR).filter((f) => f.endsWith(".mjs")).sort();
const mods = [];
const PANEL_ORDER = ["evolution", "dynamics", "gps", "pms", "mix", "aim", "subgroup",
                     "unbilled", "actions", "league", "honesty"];
for (const file of moduleFiles) {
  const ns = await import(pathToFileURL(path.join(MODULE_DIR, file)).href);
  // A file may export one module as default or several as named exports. Collect every
  // export that looks like a panel, so a file can hold a related pair.
  const candidates = [...Object.values(ns)].filter(
    (v) => v && typeof v === "object" && typeof v.render === "function" && typeof v.id === "string");
  if (!candidates.length) {
    console.warn(`  ! ${file}: no panel export found (needs id + render)`);
    continue;
  }
  for (const mod of candidates) {
    if (mods.some((m) => m.id === mod.id)) continue;
    const aud = mod.audience || ["internal", "customer"];
    if (!aud.includes(audience)) {
      console.log(`  - ${mod.id}: excluded for '${audience}' (render source not compiled)`);
      continue;
    }
    mods.push(mod);
  }
}
mods.sort((a, b) => {
  const ia = PANEL_ORDER.indexOf(a.id), ib = PANEL_ORDER.indexOf(b.id);
  return (ia < 0 ? 99 : ia) - (ib < 0 ? 99 : ib);
});
if (!mods.length) {
  console.error("  ! no panels compiled - refusing to write an empty page");
  process.exit(1);
}

/* --------------------------------------------------------------- runtime mode */
const RUNTIME = String.raw`
const SEL = { dbs: [], peer: null, state: {} };

function ctxFor(m) {
  const C = window.__LEAK__;
  const key = SEL.peer && C.peerGroups[SEL.peer] ? SEL.peer : C.meta.defaultPeer;
  const group = C.peerGroups[key] || null;
  const med = (C.peerMedians[key] && C.peerMedians[key][m.id]) || {};
  const members = group ? group.members : 0;
  const peer = (group && !group.thin && members >= C.meta.peerMin)
    ? {
        key: key, label: group.label, members: members, median: med,
        // Plain words for what this market is being compared with. The group's own label is
        // used rather than a hardcoded "same type", because the default falls back to a
        // wider pool when the exact customer type is too thin to benchmark against.
        basis: (function () {
          const k = key || "";
          if (k.indexOf("scope:") === 0) return C.L.peer.scope.toLowerCase();
          if (k.indexOf("pool:") === 0) return "comparable markets";
          if (k.indexOf("region:") === 0) return "markets in the region";
          if (k.indexOf("fleet:") === 0) return "markets of similar fleet size";
          return "comparable markets";
        })(),
        group_label: group.label,
        note: group.label + " median, " + members + " markets",
        tip: "The median across " + members + " comparable markets (" + group.label.toLowerCase() +
             "). No other distributor is named, and this market is excluded from its own benchmark.",
      }
    : null;
  const inSel = (code) => !SEL.dbs.length || SEL.dbs.includes(code);
  const visible = {};
  for (const mm of C.modules) {
    const bag = C.modulesById[mm.id];
    visible[mm.id] = (bag && bag.rows ? bag.rows : []).filter((r) => inSel(r.db));
  }
  return {
    audience: C.meta.audience, focus: C.meta.focus, L: C.L,
    payload: { meta: C.meta, modules: C.modulesById },
    networkDbs: C.networkDbs, dbName: C.dbName, dbInfo: (c) => C.dbs[c] || null,
    inSelection: inSel, peer: peer, peerGroups: C.peerGroups,
    peerReady: !!(peer && members >= C.meta.peerMin),
    mod: (id) => C.modulesById[id] || { rows: [] },
    rowsOf: (id) => visible[id] || [],
    // Panel-local control state, so a selector survives a redraw and is remembered per panel.
    state: (id, key) => (SEL.state[id] || {})[key],
    networkSum: (id, field) => {
      let s = 0;
      for (const r of (C.modulesById[id] || { rows: [] }).rows) {
        if (inSel(r.db) && typeof r[field] === "number") s += r[field];
      }
      return s;
    },
    networkUio: () => C.meta.networkUio,
  };
}

/* Called by an in-panel selector. Redraws only that panel, so the rest of the page does not
   jump under the reader. */
window.__LEAK_SET = function (moduleId, key, value) {
  SEL.state[moduleId] = SEL.state[moduleId] || {};
  SEL.state[moduleId][key] = value;
  const m = (window.__LEAK__.modules || []).find((x) => x.id === moduleId);
  if (m) draw(m);
};

function draw(m) {
  const el = document.getElementById("mod-" + m.id);
  if (!el) return;
  try { el.innerHTML = m.render(ctxFor(m)); }
  catch (err) {
    el.innerHTML = '<p class="banner rose">This panel failed to draw: ' + err.message + '</p>';
    if (window.console) console.error(m.id, err);
  }
}
function mount() { for (const m of window.__LEAK__.modules) draw(m); }

function renderPickers() {
  const C = window.__LEAK__;
  const D = document.getElementById("picker");
  if (!D) return;
  const chips = C.networkDbs.map((code) => {
    const on = SEL.dbs.includes(code);
    const d = C.dbs[code] || {};
    return '<label class="chip' + (on ? " on" : "") + '">' +
      '<input type="checkbox" data-pick="db" data-db="' + code + '"' + (on ? " checked" : "") + '>' +
      code + '<span class="sc">' + (d.scope || "") + '</span></label>';
  }).join("");
  const groups = C.peerOrder.map((k) => {
    const g = C.peerGroups[k];
    const dis = !!g.thin;
    const on = SEL.peer === k;
    return '<button class="gbtn' + (dis ? " dis" : "") + (on ? " on" : "") +
      '" data-pick="group" data-group="' + k + '"' + (dis ? " disabled" : "") +
      ' title="' + (dis ? "Fewer than " + C.meta.peerMin + " comparable markets, so no median is shown"
                        : "Compare against " + g.members + " markets") + '">' +
      g.label + ' <span class="n">' + g.members + '</span></button>';
  }).join("");
  const quick = '<button class="gbtn" data-pick="clear">Show all ' + C.networkDbs.length + ' markets</button>';
  D.innerHTML =
    '<div class="pickbar"><div class="pick-lbl">Markets</div><div class="gbtns">' + quick + '</div>' +
      '<span class="sel-note">' + (SEL.dbs.length ? SEL.dbs.length + " selected" : "all " + C.networkDbs.length + " shown") + '</span></div>' +
    '<div class="chips">' + chips + '</div>' +
    '<div class="pickbar"><div class="pick-lbl">' + C.L.peer.label + '</div>' +
      '<div class="gbtns">' + groups + '</div></div>' +
    '<p class="note">' + C.L.peer.anonymous + '</p>';
}

document.addEventListener("DOMContentLoaded", () => {
  const C = window.__LEAK__;
  const q = new URLSearchParams(location.search);
  const wantDb = (q.get("db") || "").split(",").map((s) => s.trim().toUpperCase())
    .filter((c) => C.networkDbs.includes(c));
  if (wantDb.length && C.meta.audience !== "customer") SEL.dbs = wantDb;
  const wantPeer = q.get("peer");
  if (wantPeer && C.peerGroups[wantPeer] && !C.peerGroups[wantPeer].thin) SEL.peer = wantPeer;
  if (!SEL.peer) SEL.peer = C.meta.defaultPeer;

  const picker = document.getElementById("picker");
  if (picker) {
    picker.addEventListener("click", (e) => {
      const t = e.target.closest("[data-pick]");
      if (!t) return;
      if (t.dataset.pick === "clear") { SEL.dbs = []; }
      else if (t.dataset.pick === "group") {
        const k = t.dataset.group;
        if (C.peerGroups[k] && C.peerGroups[k].thin) return;
        SEL.peer = k;
      } else return;
      renderPickers(); mount();
    });
    picker.addEventListener("change", (e) => {
      const t = e.target.closest("[data-pick]");
      if (!t || t.dataset.pick !== "db") return;
      const db = t.dataset.db;
      SEL.dbs = SEL.dbs.includes(db) ? SEL.dbs.filter((x) => x !== db) : [...SEL.dbs, db];
      renderPickers(); mount();
    });
    renderPickers();
  }

  const links = [...document.querySelectorAll("nav.mods a")];
  const secs = links.map((a) => document.querySelector(a.getAttribute("href"))).filter(Boolean);
  if ("IntersectionObserver" in window && secs.length) {
    const io = new IntersectionObserver((entries) => {
      for (const en of entries) {
        if (!en.isIntersecting) continue;
        links.forEach((a) => a.classList.toggle("on", a.getAttribute("href") === "#" + en.target.id));
      }
    }, { rootMargin: "-72px 0px -70% 0px" });
    secs.forEach((s) => io.observe(s));
  }
  mount();
});
`;

/* ------------------------------------------------------------------ helpers */
let labelCount;
try {
  const extra = [];
  for (const m of mods) if (m.title) extra.push(m.title);
  labelCount = assertLabelsClean(extra);
} catch (err) {
  console.error(`  ! ${err.message}`);
  process.exit(1);
}
console.log(`  labels: ${labelCount} strings checked against the banned-vocabulary list`);

/* ------------------------------------------------------------------- payload */
const focusInfo = focus ? dbs[focus] : null;
const groupOptions = audience === "customer"
  ? groupsFor(focus).map((k) => ({ ...peerGroups[k], members: peerGroups[k].members.length }))
  : Object.entries(peerGroups).map(([k, g]) => ({
      key: k, label: g.label, kind: g.kind, members: g.members.length,
      thin: g.members.length < MIN_PEER,
    }));

/* Customer peer medians must exclude the focus market itself: benchmarking a market
 * against a median that contains it is quietly self-referential. */
let peerMediansOut = peerMedians;
if (audience === "customer") {
  peerMediansOut = {};
  for (const [key, g] of Object.entries(peerGroups)) {
    const med = {};
    for (const [mid, mod] of Object.entries(modules)) {
      if (mid === "league" || !mod.rows) continue;
      const others = mod.rows.filter((r) => g.members.includes(r.db) && r.db !== focus);
      const per = {};
      for (const field of (mod.peer_metrics || [])) per[field] = median(others.map((r) => r[field]));
      if (mid === "mix") {
        const fams = {};
        const allFams = new Set(others.flatMap((r) => (r.families || []).map((f) => f.family)));
        for (const fam of allFams) {
          fams[fam] = median(others.flatMap((r) =>
            (r.families || []).filter((f) => f.family === fam).map((f) => f.bvp_share_pct)));
        }
        per.familyBvp = fams;
      }
      med[mid] = per;
    }
    peerMediansOut[key] = med;
  }
}

const defaultPeer = audience === "customer"
  ? defaultPeerFor(focus)
  : "all";

/* Per-module rows. In a customer build only the focus market's rows exist here, which is
 * what makes the strip real rather than cosmetic. */
const modRows = {};
for (const [mid, mod] of Object.entries(modules)) {
  if (!mod.rows) continue;
  modRows[mid] = audience === "customer"
    ? mod.rows.filter((r) => r.db === focus)
    : mod.rows;
}

/* Facts each panel needs about the module it is drawing. Kept even when there are no
 * rows, because a panel still has to explain why it is empty. `checks` become the spec
 * the verifier asserts against, so the panel list and the verifier cannot drift apart. */
const MODULE_CHECKS = [
  { module: "evolution", tag: "parts_same_six_months", type: "eur" },
  { module: "evolution", tag: "growth_like_for_like", type: "pct" },
  { module: "dynamics", tag: "average_month_current_year", type: "eur" },
  { module: "gps", tag: "ceiling_share_of_ceiling", type: "pct" },
  { module: "gps", tag: "ceiling_addressable_gap", type: "eur" },
  { module: "pms", tag: "capture_cy2025", type: "pct" },
  { module: "mix", tag: "other_brand_share", type: "pct" },
  { module: "aim", tag: "value_in_at_risk_groups", type: "eur" },
  { module: "subgroup", tag: "largest_typed_gap", type: "eur" },
  { module: "unbilled", tag: "unbought_service_part_value", type: "eur" },
  { module: "actions", tag: "value_in_raised_actions", type: "eur" },
];
function buildChecks() {
  const out = [];
  const codes = audience === "customer" ? [focus] : networkDbs;
  const cur = meta.current_year;
  for (const code of codes) {
    for (const c of MODULE_CHECKS) {
      const row = (modules[c.module]?.rows || []).find((r) => r.db === code);
      if (!row) continue;
      let v;
      if (c.module === "evolution") {
        const w = (row.ytd || []).find((x) => x.year === cur);
        v = c.tag === "growth_like_for_like" ? row.metric_growth_pct : (w && w.eur);
      } else if (c.module === "dynamics") {
        v = row.metric_avg_month_eur;
      } else if (c.module === "gps") {
        const y = (row.years || []).find((x) => x.year === 2025);
        v = c.tag === "ceiling_share_of_ceiling" ? (y && y.gps_pct) : (y && y.addressable_gap_eur);
      } else if (c.module === "pms") {
        v = row.metric_capture_pct;
      } else if (c.module === "mix") {
        v = row.metric_bvp_pct;
      } else if (c.module === "aim") {
        v = row.metric_high_risk_eur;
      } else if (c.module === "subgroup") {
        // The panel renders each gap type in a donut, not the sum, so the largest type is
        // the value that must be present.
        v = (row.gap_types || []).reduce((a, g) => Math.max(a, g.eur || 0), 0);
      } else if (c.module === "unbilled") {
        v = row.metric_gap_eur;
      } else if (c.module === "actions") {
        v = row.metric_eur_at_stake;
      }
      if (typeof v === "number" && Number.isFinite(v) && v !== 0) {
        out.push({ module: c.module, db: code, tag: c.tag, type: c.type, value: v });
      }
    }
  }
  return out;
}

// Module-level keys that must never reach a customer file, whatever a module declares. The
// spread below would otherwise carry them, because a module's own metadata is copied wholesale.
const INTERNAL_ONLY_KEYS = ["threshold_note", "defection_note", "unscored_categories",
                            "customer_ok_signals"];

function moduleMeta(mod, audience) {
  // A panel may carry its own facts beyond the shared list below, and the honesty panel does:
  // verification, scope, mileage. Spreading first means a new module-level key cannot silently
  // fail to reach the page, which is what happened once: the honesty panel rendered "undefined"
  // for every figure because its own keys were filtered out here.
  const base = { ...mod };
  if (audience === "customer") {
    for (const k of INTERNAL_ONLY_KEYS) delete base[k];
  }
  return {
    ...base,
    peer_metrics: mod.peer_metrics || [],
    peer_metric_label: mod.peer_metric_label || null,
    group_vintage: mod.group_vintage || null,
    trajectory_vintage: mod.trajectory_vintage || null,
    gap_vintage: mod.gap_vintage || null,
    threshold_note: audience === "customer" ? null : (mod.threshold_note || null),
    defection_note: audience === "customer" ? null : (mod.defection_note || null),
    ceiling: mod.ceiling || null,
    rows: [],
  };
}
const moduleMetaOut = {};
for (const [mid, mod] of Object.entries(modules)) {
  // A customer build carries only the panels it ships. Dropping the rest here removes both
  // the rows and the module's own metadata keys, so no internal panel name survives.
  if (audience === "customer" && mid === "league") continue;
  moduleMetaOut[mid] = { ...moduleMeta(mod, audience), rows: modRows[mid] || [] };
}

/* The honesty panel discloses the network. In a customer pack it must disclose only what
 * is true of that market, and must not describe the network's composition or name any
 * other market. The stripping test below enforces this rather than trusting it. */
if (audience === "customer") {
  const h = modules.honesty;
  const hasDetail = (h.dealer_markets || []).includes(focus);
  // Service-family scope for this market comes from the service-family panel, which holds
  // one row per market with every category. Reading it from the honesty module would give
  // zero, because that module deliberately carries no per-market rows.
  const own = (modRows.pms || [])[0];
  const ownCats = (own && own.categories) ? own.categories : [];
  const sampled = ownCats.filter((c) => c.capture_2025_pct !== null && c.capture_2025_pct !== undefined);
  const over100 = sampled.filter((c) => c.capture_2025_pct > 100).length;
  const ceil = modules.gps.ceiling || {};
  moduleMetaOut.honesty = {
    ...moduleMetaOut.honesty,
    verification: h.verification,
    as_of: h.as_of,
    current_year: h.current_year,
    expected_demand_note: h.expected_demand_note,
    settings_note: h.settings_note,
    // Scope counts restated for this market alone: no network size, no market list.
    scope: {
      network_markets_n: 1,
      scored_markets_n: sampled.length ? 1 : 0,
      dealer_detail_n: hasDetail ? 1 : 0,
      captured_cells: sampled.length,
      over_100: over100,
      over_100_share_pct: sampled.length ? (over100 / sampled.length) * 100 : null,
      modelled_gap_eur: own ? own.metric_gap_eur : null,
      fleet_uio: own ? own.uio : null,
      scored_markets: [],
    },
    // The measured-distance sample names other markets, so it is reduced to the finding.
    mileage: {
      model_default_km: h.mileage.model_default_km,
      measured: [],
      spread_note: h.mileage.spread_note,
    },
    gap_vintage: h.gap_vintage,
    mix_decomposition_gap: h.mix_decomposition_gap,
    mix_note: h.mix_note,
    uio_note: own && own.uio
      ? `Fleet denominator is vehicles in service for this market: ${own.uio.toLocaleString("en-GB")} vehicles. A unit count without that base cannot be judged.`
      : null,
    gps_denominator_note: h.gps_denominator_note,
    peer_rule: h.peer_rule,
    peer_min_members: h.peer_min_members,
    sources_note: h.sources_note,
    // The claim spec lets the verifier assert every figure on the page is actually present.
    // It is added below for both audiences; declared here so the key always exists.
    checks: [],
    dealer_coverage: {
      [focus]: h.dealer_coverage[focus]
        || { has_dealer_detail: false, named_years: [], max_dealers: 0, sources: [] },
    },
    dealer_markets: hasDetail ? [focus] : [],
  };
  // The ceiling keeps its own-market placeholder reading and drops the other seven names.
  if (ceil) {
    moduleMetaOut.gps.ceiling = {
      ...ceil,
      flat_markets: [],
      per_market: ceil.per_market ? { [focus]: ceil.per_market[focus] } : null,
    };
  }
}

/* The spec the verifier asserts against: every number this page claims, in machine-readable
 * form. Written next to the artefacts so the gate can find it without guessing selectors. */
const checks = buildChecks();
moduleMetaOut.honesty.checks = checks;
fs.writeFileSync(
  path.join(__dirname, audience === "customer" ? `_checks_${focus}.json` : "_checks_internal.json"),
  JSON.stringify(checks, null, 1), "utf8");
console.log(`  checks: ${checks.length} tagged figures written for the verifier`);

/* The label dictionary is embedded whole so panels can find their copy. In a customer
 * build the labels belonging to internal-only panels are removed, so even the nav wording
 * for a panel that is not shipped is absent from the file. */
const labelsOut = audience === "customer"
  ? { ...L, nav: { ...L.nav, league: undefined }, q: { ...L.q, league: undefined } }
  : L;

/* The footer lists what the page is built from in plain language. Raw pipeline file names
 * are internal artefacts and are not shown, even internally, because they carry label words
 * that are not approved wording. The machine-readable list travels in payload.json. */
const SOURCE_METHODS = [
  "the approved billing extract",
  "the distributor dimension",
  "the target-spend and fleet model",
  "the service-demand model and its trajectory",
  "the opportunity and recovery model",
  "the brand-mix classification",
  "our own part-group classification",
  "the cross-reference substitution layer",
  "the revenue bridge and forward ceiling model",
  "the network percentile surface",
  "the aftersales risk, early-warning and account-health registers",
];

const pagePayload = {
  meta: {
    audience,
    focus,
    focus_name: focusInfo ? dbName(focus) : null,
    generated: meta.generated,
    as_of: meta.as_of,
    years: meta.years,
    current_year: meta.current_year,
    ytd_note: meta.ytd_note,
    peerMin: MIN_PEER,
    defaultPeer,
    network: meta.network || {},
    verification: meta.verification,
    sources: [],
    source_methods: SOURCE_METHODS,
    source_count: (meta.sources || []).length,
    layer_labels: meta.layer_labels,
  },
  L: labelsOut,
  dbs: audience === "customer" ? { [focus]: dbs[focus] } : dbs,
  networkDbs: audience === "customer" ? [focus] : networkDbs,
  peerGroups: Object.fromEntries(groupOptions.map((g) => [g.key, g])),
  peerOrder: groupOptions.map((g) => g.key),
  peerMedians: peerMediansOut,
  modules: moduleMetaOut,
};

/* Network fleet base, shown beside any quantity so it can be read as a rate. */
const networkUioTotal = audience === "customer"
  ? (dbs[focus]?.uio_2025 ?? null)
  : networkDbs.reduce((a, c) => a + (dbs[c]?.uio_2025 || 0), 0);

/* -------------------------------------------------------------------- labels */
const title = audience === "customer"
  ? `${L.tool.packTitle} — ${dbName(focus)}`
  : L.tool.cockpitTitle;
const subtitle = audience === "customer"
  ? `${L.tool.packSub} · ${dbName(focus)}`
  : `${L.tool.cockpitSub} · ${networkDbs.length} markets`;

const navHtml = mods.map((m) =>
  `<a href="#sec-${m.id}">${escHtml(m.title)}</a>`).join("");
function escHtml(s) {
  return String(s ?? "").replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;");
}

/* The picker exists only where a selection is meaningful. A customer pack is about one
 * market, so it shows its fixed benchmark instead of a picker. */
const pickerBlock = audience === "customer"
  ? `<section class="panel"><h3>${escHtml(L.peer.label)}</h3>
      <p class="sub">${escHtml(L.peer.anonymous)}</p>
      <div id="picker"></div></section>`
  : `<section class="panel"><h3>Markets and benchmark</h3>
      <p class="sub">Select one or more markets. The benchmark is always the same customer type,
        and is shown as an unlabelled median.</p><div id="picker"></div></section>`;

/* Helper source bundle: the page needs the same formatting and chart primitives the
 * modules use, so they are serialised once into the runtime. */
const helperNames = Object.keys(charts).filter((k) => k !== "default");
const helperSrc = helperNames.map((n) => `const ${n} = ${fnSource(charts[n])};`).join("\n");

const moduleSrc = mods.map((m) => `
{ id: ${JSON.stringify(m.id)}, title: ${JSON.stringify(m.title)},
  render: ${fnSource(m.render)} }`).join(",");

const html = `<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>${escHtml(title)}</title>
<style>${CSS}</style>
</head>
<body>
<header class="top">
  <div class="wm">IS<b>U</b>ZU EUROPE<small>${escHtml(subtitle)}</small></div>
  <div class="tools">
    <span class="badge ${audience === "customer" ? "cust" : "int"}">${
      escHtml(audience === "customer" ? L.tool.customerBadge : L.tool.internalBadge)}</span>
    ${audience === "customer"
      ? `<span style="font:600 11px 'Inter',sans-serif;color:#9fb0c9">${escHtml(dbName(focus))}</span>`
      : `<label for="period">Reporting basis</label>
         <select id="period" disabled title="All figures are calendar year, with CY2026 shown to 30 June.">
           <option>Calendar year</option>
         </select>`}
  </div>
</header>
<nav class="mods">${navHtml}</nav>
<main>
${pickerBlock}
${mods.map((m) => `  <section id="sec-${m.id}" class="panel">
    <h2>${escHtml(m.title)}</h2>
    <div id="mod-${m.id}"></div>
  </section>`).join("\n")}
</main>
<div class="foot">
  <p><b>${escHtml(title)}</b> · built ${escHtml(meta.as_of)}
     · figures re-derived from the approved derived layer · verification report
     ${meta.verification.pass} passed / ${meta.verification.fail} failed
     · ${escHtml(meta.ytd_note)}</p>
  <p>Self-contained file: no server, no external request, opens by double-click.
     ${audience === "customer"
       ? "Prepared for distribution. Benchmarks are unlabelled medians of comparable markets."
       : `Internal. Built from ${SOURCE_METHODS.length} approved layers, listed in <code>_build/leakage/payload.json</code>.`}</p>
</div>
<script>
${helperSrc}
const __LEAK__ = ${withFns(pagePayload)};
__LEAK__.networkUio = ${JSON.stringify(networkUioTotal)};
__LEAK__.modulesById = __LEAK__.modules;
__LEAK__.modules = [${moduleSrc}];
__LEAK__.dbName = function (c) { return (__LEAK__.dbs[c] && __LEAK__.dbs[c].name) || c; };
window.__LEAK__ = __LEAK__;
${RUNTIME}
</script>
</body>
</html>
`;

/* --------------------------------------------------------------------- write */
fs.mkdirSync(OUT_DIR, { recursive: true });
if (audience === "customer") fs.mkdirSync(PACK_DIR, { recursive: true });

const stamp = new Date().toISOString().slice(0, 10).replace(/-/g, "");
const targets = audience === "customer"
  ? [{ file: path.join(PACK_DIR, `ISZE_Sales_Performance_Review_${focus}.html`),
       cmd: path.join(PACK_DIR, `OPEN_Sales_Performance_Review_${focus}.cmd`),
       label: `${L.tool.packTitle} · ${dbName(focus)}` }]
  : [{ file: path.join(OUT_DIR, "ISZE_Leakage_Cockpit.html"),
       cmd: path.join(OUT_DIR, "OPEN_ISZE_Leakage_Cockpit.cmd"),
       label: L.tool.cockpitTitle }];

for (const t of targets) {
  fs.writeFileSync(t.file, html, "utf8");
  // Launcher must be CRLF: Jerome double-clicks it in Explorer.
  const cmd = `@echo off\r\nrem ${t.label}\r\nstart "" "%~dp0${path.basename(t.file)}"\r\n`;
  fs.writeFileSync(t.cmd, cmd, "utf8");
  const kb = (fs.statSync(t.file).size / 1024).toFixed(1);
  console.log(`  -> ${t.file} (${kb} KB)`);
  console.log(`     launcher ${t.cmd} (CRLF)`);
}

/* Non-zero exit if a customer file somehow carries another market's code. This is the
 * check that actually protects the relationship, so it runs on every build. */
if (audience === "customer") {
  const text = fs.readFileSync(targets[0].file, "utf8");
  const leaks = networkDbs.filter((c) => c !== focus && new RegExp(`\\b${c}\\b`).test(text));
  if (leaks.length) {
    console.error(`  ! STRIPPING TEST FAILED - other markets found in the customer file: ${leaks.join(", ")}`);
    process.exit(1);
  }
  if (/"(league)"/.test(text)) {
    console.error("  ! STRIPPING TEST FAILED - internal league data present in a customer file");
    process.exit(1);
  }
  console.log(`  stripping test: no other market code present (checked ${networkDbs.length - 1} codes)`);
}
console.log(`\n  ${audience} build complete · ${mods.length} panels · audit stamp ${stamp}`);
