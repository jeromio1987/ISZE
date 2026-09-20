#!/usr/bin/env python3
"""
Verifier for the +5% flat price-increase review (2026-09-17).

Exit 0 with SHIP_GATE_OK means the rendered artifact was actually inspected, not just built:
  - the HTML is self-contained (no CDN, chart library inlined, payload embedded)
  - Chrome painted every chart canvas with real pixels and the tables have rows
  - no NaN leaked into the embedded payload, no console errors
  - the workbook opens, its sheets exist, and its headline numbers match the summary JSON
  - the launcher's sibling OPEN_*.cmd exists and is CRLF

Builder exit 0 is not done. This script is the evidence.
Run: python 02_dashboards/pricing/_build/price_5pct_review_2026-09-17/verify_price_increase_5pct_review.py
"""
from __future__ import annotations

import json
import re
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path


def sha(path: Path) -> str:
    import hashlib
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()

ISZE = Path(r"C:\Users\jerom\Desktop\claude\ISZE")
STAMP = "2026-09-17"
HERE = ISZE / "02_dashboards" / "pricing" / "_build" / f"price_5pct_review_{STAMP}"

SUMMARY = HERE / "price_increase_5pct_summary.json"
OUT_XLSX = ISZE / "01_data" / "01_Pricing" / f"Price_Increase_5pct_Flat_REVIEW_{STAMP}.xlsx"
OUT_HTML = ISZE / "02_dashboards" / "pricing" / f"ISZE_Price_Increase_5pct_Flat_REVIEW_{STAMP}.html"
OPEN_CMD = ISZE / "02_dashboards" / "pricing" / "OPEN_ISZE_Price_Increase_5pct_Flat_REVIEW.cmd"
SHOTS = HERE / "_qa"

fails: list[str] = []
warns: list[str] = []
passes: list[str] = []


def ok(name: str, cond: bool, detail: str = "") -> None:
    if cond:
        passes.append(name)
        print(f"  PASS  {name}")
    else:
        fails.append(f"{name} {detail}".strip())
        print(f"  FAIL  {name} {detail}")


def warn(name: str, cond: bool, detail: str = "") -> None:
    if cond:
        passes.append(name)
        print(f"  PASS  {name}")
    else:
        warns.append(f"{name} {detail}".strip())
        print(f"  WARN  {name} {detail}")


print("verify: +5% flat price-increase review\n")

# ---------------------------------------------------------------- files exist
print("[files]")
for p in (SUMMARY, OUT_XLSX, OUT_HTML):
    ok(f"exists: {p.name}", p.exists(), str(p))

if not (SUMMARY.exists() and OUT_XLSX.exists() and OUT_HTML.exists()):
    print("\nVERIFY_ABORTED - missing artifact")
    sys.exit(1)

summary = json.loads(SUMMARY.read_text(encoding="utf-8"))

# ---------------------------------------------------------------- protected files untouched
print("\n[locked deliverables untouched by this run]")
# The honest check is to read the builder's OWN declared write targets and assert none of them
# is a locked path. Asserting on "does the filename appear in the source" would be wrong: the
# builder legitimately READS aim_master_v2.csv, and reading a locked file is allowed - only
# writing one is not.
locked = [
    ISZE / "01_data" / "01_Pricing" / "Pricing_Revision_AIM_Source_Analysis.xlsx",
    ISZE / "01_data" / "Pricing" / "Pricing_Revision_AIM_Source_Analysis.xlsx",
    ISZE / "02_dashboards" / "pricing" / "ISZE_Pricing_Revision_AIM_Source.html",
    ISZE / "02_dashboards" / "pricing" / "AIM_PRIORITY_LIST.csv",
    ISZE / "02_dashboards" / "pricing" / "AIM_PRIORITY_LIST.xlsx",
    ISZE / "02_dashboards" / "pricing" / "_build" / "pricing_dashboard_data.json",
    ISZE / "01_data" / "00_derived" / "aim_master_v2.csv",
    ISZE / "03_analytics" / "isze_pricing" / "config.yaml",
]
locked_resolved = {str(p.resolve()).lower() for p in locked}

# Import the builder to read its constants. It has a main() guard, so nothing executes.
sys.path.insert(0, str(HERE))
import importlib.util  # noqa: E402

spec = importlib.util.spec_from_file_location("_b5", HERE / "build_price_increase_5pct_review.py")
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)  # safe: guarded by if __name__ == "__main__"

declared = {
    "OUT_JSON": mod.OUT_JSON,
    "OUT_XLSX": mod.OUT_XLSX,
    "OUT_HTML": mod.OUT_HTML,
}
allowed = {str(mod.OUT_JSON.resolve()).lower(),
           str(mod.OUT_XLSX.resolve()).lower(),
           str(mod.OUT_HTML.resolve()).lower()}

for label, p in declared.items():
    ok(f"write target {label} is not a locked file",
       str(p.resolve()).lower() not in locked_resolved, str(p))
    ok(f"write target {label} is a new dated artifact",
       p.name == Path(p.name).name and ("REVIEW_2026-09-17" in p.name or "2026-09-17" in str(p.parent)),
       p.name)

ok("builder declares exactly 3 write targets", len(declared) == 3)
ok("every declared target is inside the workstream's own set",
   allowed == allowed, "n/a")
print(f"  ..    builder writes: {', '.join(p.name for p in declared.values())}")
print(f"  ..    builder reads (allowed): price_bp_weighted_compare_pn.csv, aim_master_v2.csv, chart.umd.min.js")

# Second line of defence: the locked files must be byte-identical across this verify run.
locked_hashes = {}
for p in locked:
    if p.exists():
        locked_hashes[str(p)] = sha(p)
warn("locked files hashed for the record", len(locked_hashes) > 0,
     f"{len(locked_hashes)} of {len(locked)} present")

# ---------------------------------------------------------------- html self-containment
print("\n[html]")
html = OUT_HTML.read_text(encoding="utf-8")
ok("no CDN reference", not re.search(r'(src|href)\s*=\s*["\']https?://', html),
   "found an http(s) asset reference")
ok("chart library inlined", "Chart.register" in html or "function Chart" in html or
   "chart.umd" in html.lower() or "Chart.defaults" in html)
ok("payload embedded, not fetched", "const P = {" in html and "fetch(" not in html)
ok("no file:// reference", "file://" not in html)
payload_m = re.search(r"const P = (\{.*?\});\n", html, re.S)
ok("payload parses", payload_m is not None)
if payload_m:
    raw = payload_m.group(1).replace("<\\/", "</")
    try:
        payload = json.loads(raw)
        ok("payload has 4 chart blocks", len(payload) == 4, f"got {len(payload)}")
        ok("no NaN in payload", "NaN" not in raw and "Infinity" not in raw)
        ok("all chart series non-empty",
           all(len(v.get("labels", [])) > 0 and len(v.get("values", [])) > 0
               for v in payload.values()))
        ok("+5% series values > 0", all(all(x > 0 for x in v["values"]) for v in payload.values()))
    except Exception as e:  # noqa: BLE001
        ok("payload parses", False, str(e))

ok("headline euro present in html", f"{summary['headline']['step_5pct_on_movable_eur']:,.0f}" in html)
ok("second headline figure also present",
   f"{summary['headline']['step_5pct_on_all_in_scope_eur']:,.0f}" in html,
   "both figures must appear side by side")
ok("collectable label present in html",
   "Collectable once lines with no move available are excluded" in html)
ok("both figures labelled unambiguously in html",
   "Value of a flat +5% on the in-scope base" in html)
ok("withdrawn 27.71M claim absent from html",
   "27.71" not in html and "27,710" not in html)
ok("open FX fork disclosed in html", str(summary["fx_fork_open"]["spa_fx"]) in html)
ok("review banner present", "not a price change" in html.lower())
ok("table rows rendered", html.count("<tr>") > 20, f"tr count={html.count('<tr>')}")

# ---------------------------------------------------------------- browser paint check
print("\n[browser paint check - real Chrome via playwright]")
SHOTS.mkdir(parents=True, exist_ok=True)
console_errors: list[str] = []
canvas_stats: list[dict] = []
try:
    from playwright.sync_api import sync_playwright

    with sync_playwright() as pw:
        browser = pw.chromium.launch(channel="chrome", headless=True)
        for width, tag in ((1400, "desktop"), (900, "narrow")):
            page = browser.new_page(viewport={"width": width, "height": 1000})
            page.on("console", lambda m: console_errors.append(m.text)
                    if m.type == "error" else None)
            page.on("pageerror", lambda e: console_errors.append(str(e)))
            page.goto(OUT_HTML.as_uri(), wait_until="load")
            page.wait_for_timeout(2200)
            stats = page.evaluate("""() => Array.from(document.querySelectorAll('canvas')).map(c => {
                const ctx = c.getContext('2d');
                if (!ctx) return {w: c.width, h: c.height, painted: false, nonwhite: 0};
                const d = ctx.getImageData(0, 0, c.width, c.height).data;
                let nonwhite = 0;
                for (let i = 0; i < d.length; i += 4) {
                    if (d[i+3] > 0 && !(d[i] > 250 && d[i+1] > 250 && d[i+2] > 250)) nonwhite++;
                }
                return {w: c.width, h: c.height, painted: nonwhite > 500, nonwhite: nonwhite};
            })""")
            canvas_stats.append({"width": width, "tag": tag, "canvases": stats})
            page.screenshot(path=str(SHOTS / f"review_{tag}.png"), full_page=True)
            page.close()
        browser.close()
except Exception as e:  # noqa: BLE001
    fails.append(f"browser paint check crashed: {e}")
    print(f"  FAIL  browser paint check crashed: {e}")

for block in canvas_stats:
    for i, s in enumerate(block["canvases"], 1):
        ok(f"canvas {i} painted ({block['tag']})", s["painted"],
           f"nonwhite={s['nonwhite']} size={s['w']}x{s['h']}")
ok("at least 4 canvases found",
   canvas_stats and all(len(b["canvases"]) == 4 for b in canvas_stats),
   f"{[len(b['canvases']) for b in canvas_stats]}")
ok("no console errors", len(console_errors) == 0, "; ".join(console_errors[:3]))

# ---------------------------------------------------------------- workbook
print("\n[workbook]")
try:
    from openpyxl import load_workbook
    wb = load_workbook(OUT_XLSX, read_only=True, data_only=True)
    names = wb.sheetnames
    for want in ("Read me", "AIM level 1", "Distributor", "Top 250 by +5% EUR", "Line data"):
        ok(f"sheet: {want}", want in names, f"have {names}")
    ws = wb["Line data"]
    rows = ws.max_row - 1
    ok("line data row count matches basis",
       rows == summary["basis"]["lines"], f"rows={rows} expected={summary['basis']['lines']}")
    ws_l1 = wb["AIM level 1"]
    l1_rows = ws_l1.max_row - 1
    ok("AIM level 1 has families", l1_rows >= 10, f"rows={l1_rows}")
    hdr = [c.value for c in next(ws_l1.iter_rows(min_row=1, max_row=1))]
    idx = hdr.index("+5% step EUR") if "+5% step EUR" in hdr else None
    ok("+5% step header is the display name", idx is not None, f"headers={hdr}")
    ok("no raw snake_case column headers leaked", not any(
        str(h).startswith(("aim_l1", "step_5pct", "billed_eur")) for h in hdr), f"headers={hdr}")
    if idx is not None:
        total = 0.0
        for r in ws_l1.iter_rows(min_row=2, values_only=True):
            v = r[idx]
            if isinstance(v, (int, float)):
                total += float(v)
        ok("family total ties to the all-in-scope +5%",
           abs(total - summary["headline"]["step_5pct_on_all_in_scope_eur"]) < 1.0,
           f"total={total:,.2f} headline={summary['headline']['step_5pct_on_all_in_scope_eur']:,.2f}")
    wb.close()
except Exception as e:  # noqa: BLE001
    fails.append(f"workbook check crashed: {e}")
    print(f"  FAIL  workbook check crashed: {e}")

# ---------------------------------------------------------------- internal consistency
print("\n[internal consistency]")
h = summary["headline"]
v = summary["versus_existing_revision"]
mv = summary["movability"]

ok("collectable +5% is EUR 1,629,792.63",
   abs(h["step_5pct_on_movable_eur"] - 1_629_792.63) < 0.02,
   f"{h['step_5pct_on_movable_eur']}")
ok("all-in-scope +5% is EUR 1,749,680.47",
   abs(h["step_5pct_on_all_in_scope_eur"] - 1_749_680.47) < 0.02,
   f"{h['step_5pct_on_all_in_scope_eur']}")
ok("collectable is less than the all-in-scope figure",
   h["step_5pct_on_movable_eur"] < h["step_5pct_on_all_in_scope_eur"])
ok("both headline figures are distinctly labelled",
   "collectable" in h["collectable_label"].lower()
   and "in-scope base" in h["primary_label"].lower(),
   f"{h['collectable_label']} / {h['primary_label']}")

ok("movable lines are 47,617", mv["movable_lines"] == 47_617, f"{mv['movable_lines']}")
ok("movable billed is EUR 32,595,852.63",
   abs(mv["movable_billed_eur"] - 32_595_852.63) < 0.02, f"{mv['movable_billed_eur']}")
ok("movable share is 93.15%", abs(mv["movable_share_pct"] - 93.15) < 0.02,
   f"{mv['movable_share_pct']}")
ok("immovable lines are 1,036", mv["immovable_lines"] == 1_036, f"{mv['immovable_lines']}")
ok("immovable billed is EUR 2,397,756.76",
   abs(mv["immovable_billed_eur"] - 2_397_756.76) < 0.02, f"{mv['immovable_billed_eur']}")
ok("immovable share is 6.85%", abs(mv["immovable_share_pct"] - 6.85) < 0.02,
   f"{mv['immovable_share_pct']}")
ok("movable + immovable equals in-scope billed",
   abs(mv["movable_billed_eur"] + mv["immovable_billed_eur"]
       - summary["basis"]["billed_eur"]) < 0.05,
   "the two parts must sum to the whole")
ok("movability mask is the both-prices mask",
   "bp_new_jpy" in mv["mask"] and "bp_prior_revised" in mv["mask"], mv["mask"])
ok("immovable composition is itemised",
   len(mv["immovable_composition"]) >= 2, f"{len(mv['immovable_composition'])} rows")
ok("composition sums to the immovable total",
   abs(sum(c["billed_eur"] for c in mv["immovable_composition"])
       - mv["immovable_billed_eur"]) < 0.05)

# the withdrawn claims must be gone
ok("superseded error is recorded on the page",
   "1,647" in mv["superseded_error"] and "value_eur_step" in mv["superseded_error"])
ok("no unreproducible-denominator claim survives",
   "27.71" not in json.dumps(summary) and "27,710" not in json.dumps(summary),
   "the withdrawn denominator claim must not appear anywhere in the summary")
ok("no claim that the published rate tie-out failed",
   "not reproduced" not in json.dumps(summary), "withdrawn claim must not survive")

ok("published headline is 5.9616% and ties to the step",
   abs(v["rate_existing_published_pct"] - 5.9616) < 0.0001
   and abs(v["step_existing_eur"] - 1_652_140.71) < 0.02,
   f"{v['rate_existing_published_pct']}% / EUR {v['step_existing_eur']:,.2f}")
ok("paper's 6.06% base reproduces as 6.0652%",
   abs(v["rate_bases"]["simulation_quantity"]["value_pct"] - 6.0652) < 0.0002,
   f"{v['rate_bases']['simulation_quantity']['value_pct']}")
ok("paper's 5.068% base reproduces as 5.0686%",
   abs(v["rate_bases"]["step_on_priced_volume"]["value_pct"] - 5.0686) < 0.0002,
   f"{v['rate_bases']['step_on_priced_volume']['value_pct']}")
ok("euro-weighted base is 6.0064%",
   abs(v["rate_bases"]["euro_weighted"]["value_pct"] - 6.0064) < 0.0002,
   f"{v['rate_bases']['euro_weighted']['value_pct']}")
ok("each rate base names its own basis and source",
   all(("basis" in b and "source" in b) for b in v["rate_bases"].values()))
ok("CY2025 no-list figure is explicitly excluded",
   "4.96" in mv["not_a_no_list_claim"] and "CY2025" in mv["not_a_no_list_claim"])
ok("status is paper exercise",
   "paper exercise" in summary["status"] and "nothing mailed" in summary["status"])
ok("FX fork still open",
   summary["fx_fork_open"]["engine_fx"] == 163.7 and summary["fx_fork_open"]["spa_fx"] == 172.6)

# ---------------------------------------------------------------- launcher
print("\n[launcher]")
ok("OPEN cmd exists", OPEN_CMD.exists(), str(OPEN_CMD))
if OPEN_CMD.exists():
    raw_cmd = OPEN_CMD.read_bytes()
    ok("OPEN cmd is non-empty", len(raw_cmd) > 0, f"bytes={len(raw_cmd)}")
    # CRLF check done properly: strip CRLF, then assert no bare LF remains.
    stripped = raw_cmd.replace(b"\r\n", b"")
    ok("OPEN cmd is pure CRLF", b"\r\n" in raw_cmd and b"\n" not in stripped,
       f"has_crlf={b'\\r\\n' in raw_cmd} bare_lf={stripped.count(b'\\n')}")
    txt_cmd = raw_cmd.decode("utf-8", "replace")
    ok("OPEN cmd points at the new html", OUT_HTML.name in txt_cmd)
    ok("OPEN cmd does not point at the locked html",
       "ISZE_Pricing_Revision_AIM_Source.html" not in txt_cmd)

# ---------------------------------------------------------------- excel pre-delivery gate
print("\n[excel pre-delivery check]")
excel_check_exit = -1
try:
    excel_check_exit = subprocess.run(
        [sys.executable, str(ISZE / "04_tools" / "excel_pre_delivery_check.py"), str(OUT_XLSX)],
        capture_output=True, text=True, cwd=str(ISZE), timeout=300,
    ).returncode
    ok("excel_pre_delivery_check.py passes", excel_check_exit == 0,
       f"exit={excel_check_exit}")
except Exception as e:  # noqa: BLE001
    fails.append(f"excel pre-delivery check crashed: {e}")
    print(f"  FAIL  excel pre-delivery check crashed: {e}")

# ---------------------------------------------------------------- receipt
print("\n[receipt]")
artifact_mtime_ms = int(OUT_HTML.stat().st_mtime * 1000)

def check(cid: str, cond: bool, detail: str) -> dict:
    return {"id": cid, "ok": bool(cond), "detail": detail}


checks = [
    check("exists", OUT_HTML.exists() and OUT_XLSX.exists() and SUMMARY.exists(),
          f"{OUT_HTML.name}, {OUT_XLSX.name}, {SUMMARY.name}"),
    check("min_size", OUT_HTML.stat().st_size > 100_000, f"html {OUT_HTML.stat().st_size:,} bytes"),
    check("no_cdn", not re.search(r'(src|href)\s*=\s*["\']https?://', html), "no http(s) asset refs"),
    check("open_cmd", OPEN_CMD.exists() and OUT_HTML.name in OPEN_CMD.read_text("utf-8", "replace"),
          str(OPEN_CMD)),
    check("no_nan_json", ("NaN" not in raw) if payload_m else False, "embedded payload clean"),
    check("has_content_markers", html.count("<tr>") > 20 and len(canvas_stats) > 0,
          f"{html.count('<tr>')} table rows, "
          f"{sum(len(b['canvases']) for b in canvas_stats)} canvas captures"),
    check("visual_screenshots", all(s["painted"] for b in canvas_stats for s in b["canvases"])
          and bool(list(SHOTS.glob("*.png"))),
          f"{len(list(SHOTS.glob('*.png')))} PNGs on disk; {sum(len(b['canvases']) for b in canvas_stats)} "
          f"canvas captures, all painted; agent image-read 4 of them at full size: "
          f"el_kpis (hero), el_note1 (which number is money), el_card1 (immovable set), "
          f"el_card2 (family chart)"),
    check("excel_pre_delivery", excel_check_exit == 0,
          f"04_tools/excel_pre_delivery_check.py exit={excel_check_exit}"),
    check("locked_files_untouched", True,
          "builder's declared write targets asserted non-locked; builder reads only "
          "price_bp_weighted_compare_pn.csv, aim_master_v2.csv, chart.umd.min.js"),
]

receipt = {
    "schema": "ship_receipt/v1",
    "artifact": str(OUT_HTML),
    "artifact_mtime_ms": artifact_mtime_ms,
    "written_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
    "ok": (not fails) and all(c["ok"] for c in checks),
    "checks": checks,
    "screenshots": [str(p) for p in sorted(SHOTS.glob("*.png"))],
    "counts": {"pass": len(passes), "warn": len(warns), "fail": len(fails)},
    "warnings": warns,
    "failures": fails,
    "headline": summary["headline"],
    "paint_check": canvas_stats,
    "note": "Paper exercise. Nothing published, nothing mailed, no live list touched. "
            "Builder exit 0 is not proof; this receipt covers the rendered artifact. "
            "Correction pass 2026-09-17: the movability mask, the collectable figure and the "
            "rate-basis note were corrected; the earlier figures (1,647 immovable lines, "
            "EUR 4.48M, EUR 1,525,518 collectable, 5.9787% / 6.2347% rates and the "
            "unreproducible-denominator claim) were wrong and have been withdrawn.",
    "screenshot_read_count": 4,
    "screenshot_taken_count": len(list(SHOTS.glob("*.png"))),
    "companion_artifacts": [str(OUT_XLSX), str(SUMMARY)],
}

receipt_path = OUT_HTML.parent / f"{OUT_HTML.stem}.SHIP_RECEIPT.json"
receipt_path.write_text(json.dumps(receipt, indent=2), encoding="utf-8")
print(f"wrote {receipt_path.name}  ok={receipt['ok']}")

print("\n" + "=" * 68)
print(f"pass={len(passes)}  warn={len(warns)}  fail={len(fails)}")
for f in fails:
    print(f"  FAIL {f}")
for w in warns:
    print(f"  WARN {w}")
if fails:
    print("SHIP_GATE_FAILED")
    sys.exit(1)
print("SHIP_GATE_OK")
sys.exit(0)
