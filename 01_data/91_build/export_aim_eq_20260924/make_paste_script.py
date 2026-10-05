"""Generate the paste-into-console EQ lookup script for the EXPORT parts.

The automatic driver (CDP Runtime.evaluate) is failing in this Cursor session, so the
lookup script is generated as a single self-contained file with the worklist embedded.
It is pasted once into the Snap-on EQ tab's own console and runs there by itself.

Reads  : 01_data/91_build/export_aim_eq_20260924/open_worklist_20260924.json
Writes : 01_data/91_build/export_aim_eq_20260924/PASTE_INTO_EQ_CONSOLE_20260924.js

Run: python 01_data/91_build/export_aim_eq_20260924/make_paste_script.py

The worklist, the output file, the download name and the gap between lookups can be
overridden, so the same generator can build the narrowed EPC-only run without editing it:

  python 01_data/91_build/export_aim_eq_20260924/make_paste_script.py \
      --worklist open_worklist_epc_only_20260924.json \
      --target   PASTE_INTO_EQ_CONSOLE_EPC_ONLY_20260924.js \
      --download eq_hits_export_epc_only_20260924.json

With no arguments it reproduces exactly the file it built before.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

OUT = Path(__file__).resolve().parent
WORKLIST = OUT / "open_worklist_20260924.json"
TARGET = OUT / "PASTE_INTO_EQ_CONSOLE_20260924.js"
DOWNLOAD = "eq_hits_export_20260924.json"

JS = """// EQ-Hit lookup for the IE40 price extract — 2026-09-24
// HOW TO USE
//   1. Open https://isuzu.snaponepc.com/epc/#/ and sign in.
//   2. Press F12, click the Console tab.
//   3. If Chrome says "Warning: Don't paste code...", type:  allow pasting
//   4. Paste this whole file, press Enter. It starts by itself.
//   5. It runs about %N% parts. Watch the progress line.
//   6. At the end it downloads  %DOWNLOAD%
//      and also leaves the data in this tab under localStorage key "%KEY%".
//   Nothing is sent anywhere. Close the tab only after it says DONE.

window.__eqh = window.__eqh || {};
window.__eqh.pns = %PNS%;
window.__eqh.results = window.__eqh.results || [];
window.__eqh.gapMs = %GAP%;

window.__eqh.lookup = async function (pn) {
  const sleep = (ms) => new Promise((r) => setTimeout(r, ms));
  const pnInput = () => {
    const byPh = document.querySelector('input[placeholder="Part Number"]');
    if (byPh) return byPh;
    const btn = [...document.querySelectorAll('button')].find(
      (b) => (b.title || '') === 'Perform search'
    );
    if (!btn) return null;
    const grp = btn.closest('.p-toolbar-group-right') || btn.parentElement;
    const texts = [...(grp ? grp.querySelectorAll('input[type="text"]') : [])];
    return texts.find((i) => !/inputMask/.test(i.className || '')) || texts[texts.length - 1] || null;
  };
  const searchBtn = () =>
    [...document.querySelectorAll('button')].find((b) => (b.title || '') === 'Perform search');
  const getTotal = () => {
    let t = null;
    document.querySelectorAll('div.right').forEach((e) => {
      const m = (e.textContent || '').trim().match(/^Total Results:?\\s*(\\d+)/);
      if (m) t = +m[1];
    });
    return t;
  };

  const inp = pnInput();
  const btn = searchBtn();
  if (!inp || !btn) return { pn, eq_status: 'ERROR', error: 'no controls' };

  const nativeSet = Object.getOwnPropertyDescriptor(window.HTMLInputElement.prototype, 'value').set;
  inp.focus();
  nativeSet.call(inp, pn);
  inp.dispatchEvent(new InputEvent('input', { bubbles: true, data: pn, inputType: 'insertText' }));
  inp.dispatchEvent(new Event('change', { bubbles: true }));
  await sleep(90);
  btn.click();

  const t0 = Date.now();
  let total = null, headerOk = false;
  while (Date.now() - t0 < 15000) {
    const h = (document.querySelector('.part-search-header') || {}).textContent || '';
    if (h.includes(pn)) {
      headerOk = true;
      total = getTotal();
      if (total !== null) break;
    }
    await sleep(180);
  }
  if (!headerOk) return { pn, eq_status: 'ERROR', error: 'header timeout' };
  if (total === 0) return { pn, eq_status: 'NOT_FOUND', eq_total: 0, found: false };

  await sleep(320);
  const rows = [...document.querySelectorAll('.ag-row')].filter((rr) =>
    /\\d{3,6}\\s*-\\s*[A-Z0-9]{2,4}/.test(rr.textContent || '')
  );

  const out = {
    pn,
    eq_status: 'FOUND',
    eq_total: total,
    found: true,
    row_count: rows.length,
    eq_catalog: '',
    eq_fig_key: '',
    eq_fig_name: '',
    eq_part_name: '',
  };

  if (rows.length) {
    const cells = [...rows[0].querySelectorAll('.ag-cell')].map((c) => (c.textContent || '').trim());
    out.eq_catalog = cells.join(' | ').slice(0, 300);
    const fk = cells.find((c) => /^\\d{3,6}\\s*-\\s*[A-Z0-9]{2,4}$/.test(c));
    if (fk) out.eq_fig_key = fk.replace(/\\s+/g, '');
    rows[0].click();
    await sleep(900);
  }

  for (let i = 0; i < 25; i++) {
    const txt = document.body.innerText || '';
    const m = txt.match(/FIG Name\\s*[\\r\\n]+Part Name\\s*[\\r\\n]+([^\\r\\n]+)[\\r\\n]+([^\\r\\n]+)/);
    if (m && m[1].trim() && !/^FIG Name/i.test(m[1])) {
      out.eq_fig_name = m[1].trim();
      out.eq_part_name = m[2].trim();
      break;
    }
    await sleep(180);
  }
  return out;
};

window.__eqh.run = async function () {
  if (window.__eqh.running) return 'already running';
  window.__eqh.running = true;
  const sleep = (ms) => new Promise((r) => setTimeout(r, ms));
  const start = window.__eqh.results.length;
  const total = window.__eqh.pns.length;
  for (let i = 0; i < total; i++) {
    if (window.__eqh.cancel) break;
    let hit;
    try {
      hit = await window.__eqh.lookup(window.__eqh.pns[i]);
    } catch (e) {
      hit = { pn: window.__eqh.pns[i], eq_status: 'ERROR', error: String((e && e.message) || e) };
    }
    window.__eqh.results.push(hit);
    try {
      if (window.__eqh.results.length % 25 === 0) {
        localStorage.setItem('%KEY%', JSON.stringify(window.__eqh.results));
      }
    } catch (e) {}
    const n = window.__eqh.results.length;
    console.log('EQ ' + n + '/' + total + '  ' + hit.pn + '  ' + (hit.eq_status || '') + '  ' + (hit.eq_fig_name || ''));
    if (i < total - 1) await sleep(window.__eqh.gapMs);
  }
  window.__eqh.running = false;
  try {
    localStorage.setItem('%KEY%', JSON.stringify(window.__eqh.results));
  } catch (e) {}
  const blob = new Blob([JSON.stringify(window.__eqh.results, null, 2)], { type: 'application/json' });
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = '%DOWNLOAD%';
  document.body.appendChild(a);
  a.click();
  document.body.removeChild(a);
  URL.revokeObjectURL(url);
  console.log('DONE  ' + window.__eqh.results.length + ' results downloaded as %DOWNLOAD%');
  return window.__eqh.results.length;
};

window.__eqh.cancel = false;
console.log('EQ-Hit ready: ' + window.__eqh.pns.length + ' part numbers. Starting in 3 seconds. To stop it, run:  __eqh.cancel = true');
setTimeout(() => window.__eqh.run(), 3000);
"""


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--worklist", default=str(WORKLIST),
                    help="worklist JSON to embed (default: the 1,097-part open_worklist_20260924.json)")
    ap.add_argument("--target", default=str(TARGET),
                    help="JS file to write (default: PASTE_INTO_EQ_CONSOLE_20260924.js)")
    ap.add_argument("--download", default=DOWNLOAD,
                    help="name of the file the browser downloads at the end")
    ap.add_argument("--gap-ms", type=int, default=1800,
                    help="pause between lookups in milliseconds (default 1800)")
    ap.add_argument("--key", default="eqhits_export",
                    help="localStorage key the run saves under (default eqhits_export, as before)")
    args = ap.parse_args()

    worklist = Path(args.worklist)
    if not worklist.is_absolute():
        worklist = OUT / worklist
    target = Path(args.target)
    if not target.is_absolute():
        target = OUT / target
    if not worklist.exists():
        raise SystemExit(f"worklist not found: {worklist}")

    # one localStorage key per run, so a narrowed run does not overwrite the full one
    key = args.key or ("eqhits_" + target.stem.lower())

    pns = json.loads(worklist.read_text(encoding="utf-8"))
    js = JS.replace("%PNS%", json.dumps(pns, separators=(",", ":")))
    js = js.replace("%N%", str(len(pns)))
    js = js.replace("%GAP%", str(args.gap_ms))
    js = js.replace("%DOWNLOAD%", args.download)
    js = js.replace("%KEY%", key)
    target.write_text(js, encoding="utf-8")
    print(f"worklist : {worklist}")
    print(f"wrote    : {target} ({target.stat().st_size:,} bytes) with {len(pns)} part numbers")
    print(f"download : {args.download}")
    print("estimated run time:", round(len(pns) * args.gap_ms / 1000 / 60, 1), "minutes")


if __name__ == "__main__":
    main()
