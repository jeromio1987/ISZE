"""Batch-2 collector: drives the EPC tab over CDP, writes every result to disk as it arrives.

The page itself cannot reach a local sink — Chrome blocks a public HTTPS origin from fetching
loopback, confirmed by probe (fetch, no-cors fetch and XHR all return "Failed to fetch"). So the
transport is the CDP session instead: one long-lived Runtime.evaluate runs a staged decoder inside
the EPC tab, exposing the results on window; the driver here polls that array and appends each new
record to a JSONL file immediately.

Files
-----
_epc_batch2_js_part1.js .. part5.js   the decoder, split so each Runtime.evaluate is small
epc_decode_batch2_20260919.jsonl      one JSON record per part number, appended as collected
epc_decode_batch2_20260919.json       consolidated output, same shape as batch 1
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
import time
from pathlib import Path

BUILD = Path(__file__).resolve().parent
ROOT = Path(r"C:\Users\jerom\Desktop\claude\ISZE")
OUT_DIR = ROOT / "01_data" / "00_derived"
JSONL = OUT_DIR / "epc_decode_batch2_20260919.jsonl"
FINAL = OUT_DIR / "epc_decode_batch2_20260919.json"
PNS_FILE = BUILD / "_pns_csv.txt"
STATE = BUILD / "_state.json"
LOG = BUILD / "_batch2.log"

VIEW_ID = "glass-browser-072b3f76-03d2-4f17-a486-bad24637b146"
STAGGER_MS = 5000
RATE_MS = 6000

GAP_JS = r"""
window.__BR = window.__BR || [];
window.__one = function (pn, timeoutMs) {
  timeoutMs = timeoutMs || 12000;
  return new Promise(function (resolve) {
    var sleep = function (ms) { return new Promise(function (r) { setTimeout(r, ms); }); };
    var out = function (o) { window.__BR.push(o); resolve(o); };
    var btn = Array.from(document.querySelectorAll('button')).find(function (b) {
      return (b.title || '') === 'Perform search';
    });
    if (!btn) return out({ pn: pn, error: 'no button' });
    var grp = btn.closest('.p-toolbar-group-right') || btn.parentElement;
    var texts = Array.from(grp.querySelectorAll('input[type=text]'));
    var inp = texts.find(function (i) { return !/inputMask/.test(i.className); }) ||
              texts[texts.length - 1];
    if (!inp) return out({ pn: pn, error: 'no input' });
    var setter = Object.getOwnPropertyDescriptor(window.HTMLInputElement.prototype, 'value').set;
    setter.call(inp, pn);
    inp.dispatchEvent(new InputEvent('input', { bubbles: true, data: pn, inputType: 'insertText' }));
    inp.dispatchEvent(new Event('change', { bubbles: true }));
    setTimeout(function () {
      btn.click();
      (function wait() {
        var total = null;
        var landed = false;
        var h = document.querySelector('.part-search-header');
        var ht = h ? h.textContent.trim() : '';
        var m = ht.match(/For:\s*(\d{4,15})/);
        if (m && m[1] === pn) {
          document.querySelectorAll('div.right').forEach(function (e) {
            var t = (e.textContent || '').trim().match(/^Total Results::?\s*(\d+)$/);
            if (t) total = parseInt(t[1]);
          });
          if (total !== null) landed = true;
        }
        if (!landed) {
          if (Date.now() - t0 >= timeoutMs) {
            return out({ pn: pn, error: 'did not land', header: ht });
          }
          return setTimeout(wait, 150);
        }
        if (total === 0) return out({ pn: pn, total: 0, found: false, families: [], editions: 0 });
        try {
          var vps = Array.from(document.querySelectorAll('.ag-body-viewport'))
            .filter(function (v) { return v.getBoundingClientRect().height > 0; })
            .sort(function (a, b) {
              return a.getBoundingClientRect().left - b.getBoundingClientRect().left;
            });
          var lv = vps[0];
          if (!lv) return out({ pn: pn, total: total, error: 'no viewport' });
          var seen = {};
          var fams = {};
          var scan = function () {
            lv.querySelectorAll('.ag-row').forEach(function (row) {
              var text = row.textContent.trim();
              if (/^(TRUCKS|BUSES|PASSENGER VEHICLE|INDUSTRIAL|MARINE|COMPONENT)/.test(text)) {
                fams[text.split(/\s{2,}/)[0].trim()] = 1;
                return;
              }
              var mm = text.match(/^(\d{4,6})\s*-\s*(.+)/);
              if (mm) seen[mm[1]] = mm[2].trim();
            });
          };
          lv.scrollTop = 0;
          setTimeout(function () {
            scan();
            var step = Math.max(250, lv.clientHeight - 50);
            var pos = 0;
            (function next() {
              if (pos > lv.scrollHeight) {
                lv.scrollTop = 0;
                return out({
                  pn: pn,
                  total: total,
                  found: true,
                  editions: Object.keys(seen).length,
                  families: Object.keys(fams),
                  models: Object.keys(seen).map(function (k) { return seen[k]; }).slice(0, 40)
                });
              }
              lv.scrollTop = pos;
              pos += step;
              setTimeout(function () { scan(); next(); }, 45);
            })();
          }, 90);
        } catch (e) {
          return out({ pn: pn, total: total, error: 'read failed: ' + String(e).slice(0, 120) });
        }
      })();
      var t0 = Date.now();
    }, 120);
  });
};
window.__push = function (pn) { try { window.__one(pn); } catch (e) {} };
window.__status = function () { return { rows: window.__BR.length, tail: window.__BR.slice(-3) }; };
'staged decoder ready';
"""


def log(msg: str) -> None:
    line = f"{time.strftime('%H:%M:%S')}  {msg}"
    print(line, flush=True)
    with open(LOG, "a", encoding="utf-8") as fh:
        fh.write(line + "\n")


def cdp(js: str, await_promise: bool = False, timeout: int = 180):
    expr = "JSON.stringify((" + js + "))"
    cmd = [
        "node", str(BUILD / "cdp_eval.js"), VIEW_ID, expr,
        "1" if await_promise else "0", str(timeout),
    ]
    r = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="replace")
    if r.returncode != 0:
        raise RuntimeError((r.stderr or r.stdout)[:400])
    raw = (r.stdout or "").strip().splitlines()[-1]
    return json.loads(json.loads(raw))


def main() -> int:
    pns = [p.strip() for p in PNS_FILE.read_text().split(",") if p.strip()]
    log(f"batch 2: {len(pns)} part numbers, stagger {STAGGER_MS} ms, gap {RATE_MS} ms")

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    JSONL.write_text("", encoding="utf-8")

    log("injecting decoder: " + str(cdp(GAP_JS)))

    launched = 0
    for i, pn in enumerate(pns):
        try:
            cdp(f"window.__push('{pn}'); 'queued'")
            launched += 1
        except Exception as exc:  # noqa: BLE001
            log(f"  LAUNCH FAIL {pn}: {exc}")
        if i < len(pns) - 1:
            time.sleep(STAGGER_MS / 1000.0)

    log(f"all {launched} part numbers queued; draining")

    written = 0
    empty_polls = 0
    started = time.time()
    while True:
        try:
            st = cdp("window.__status()")
        except Exception as exc:  # noqa: BLE001
            log(f"  status error: {exc}")
            time.sleep(10)
            continue
        rows = st["rows"]
        if rows > written:
            all_rows = cdp("window.__BR")
            with open(JSONL, "a", encoding="utf-8") as fh:
                for rec in all_rows[written:]:
                    fh.write(json.dumps(rec, ensure_ascii=False) + "\n")
                fh.flush()
                os.fsync(fh.fileno())
            written = rows
            errs = sum(1 for r in all_rows[:written] if r.get("error"))
            log(f"  saved {written}/{len(pns)}  (errors {errs})  last={st['tail'][-1].get('pn')}")
            empty_polls = 0
        else:
            empty_polls += 1

        if written >= len(pns):
            break
        if empty_polls > 60 and time.time() - started > 600:
            log("  no progress for 60 polls; stopping")
            break
        time.sleep(RATE_MS / 1000.0)

    elapsed = time.time() - started
    rows = [json.loads(l) for l in JSONL.read_text(encoding="utf-8").splitlines() if l.strip()]
    payload = {
        "batch": 2,
        "collected_at": time.strftime("%Y-%m-%dT%H:%M:%S"),
        "records": len(rows),
        "meta": {"pns_requested": len(pns), "elapsed_s": round(elapsed, 1),
                 "stagger_ms": STAGGER_MS, "gap_ms": RATE_MS},
        "results": rows,
    }
    FINAL.write_text(json.dumps(payload, ensure_ascii=False, indent=1), encoding="utf-8")
    errors = sum(1 for r in rows if r.get("error"))
    found = sum(1 for r in rows if r.get("found"))
    log(f"DONE  {len(rows)} records, found={found}, errors={errors}, "
        f"{elapsed/60:.1f} min -> {FINAL}")
    STATE.write_text(json.dumps({"records": len(rows), "found": found, "errors": errors,
                                 "elapsed_s": round(elapsed, 1), "final": str(FINAL)},
                                indent=1), encoding="utf-8")
    return 0


if __name__ == "__main__":
    sys.exit(main())
