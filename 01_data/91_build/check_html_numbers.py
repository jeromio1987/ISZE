# -*- coding: utf-8 -*-
"""
Fact-check a built HTML deliverable against the source files it claims to summarise.

Two passes, both mandatory:
  1. Every number written into the page is re-derived from its source file and
     compared. A mismatch is a hard fail.
  2. The rendered page is opened in a real browser: the app script must parse, no
     console errors, and every canvas must actually have pixels drawn on it.

Run: python 01_data/91_build/check_html_numbers.py --html <path> --kind pricing
Exit 0 only when both passes are clean.
"""
from __future__ import annotations

import argparse
import io
import json
import os
import re
import subprocess
import sys
import tempfile
from collections import Counter

import pandas as pd

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

D = r"C:\Users\jerom\Desktop\claude\ISZE\01_data\00_derived"
ISZE = r"C:\Users\jerom\Desktop\claude\ISZE"


def say(m=""):
    print(m)
    sys.stdout.flush()


def truth_pricing() -> dict:
    """Re-derive every headline the pricing page states, from source."""
    spec = json.load(open(os.path.join(ISZE, "02_dashboards", "pricing", "_build",
                                       "_spec_basis_meta.json"), encoding="utf-8"))
    cost = json.load(open(os.path.join(D, "pricing_cost_floor_meta.json"), encoding="utf-8"))
    wl = json.load(open(os.path.join(D, "price_collection_worklist_meta.json"), encoding="utf-8"))
    rec = json.load(open(os.path.join(D, "aim_pricing_recalc_2026-09-17.json"), encoding="utf-8"))

    top = pd.read_csv(os.path.join(D, "margin_opportunity_top200.csv"), dtype={"pn": str})
    fam = pd.DataFrame(rec["aim_l1"])

    return {
        "weighted_pct": round(spec["weighted_pct"] * 100, 4),
        "step_eur_m": round(spec["step_eur"] / 1e6, 2),
        "billed_priced_eur": round(spec["billed_eur_priced"]),
        "gross_profit_eur_m": round(cost["headline"]["gross_profit_eur"] / 1e6, 2),
        "gm_pct": round(cost["headline"]["weighted_gm_pct"], 2),
        "book_lines": int(spec["lines_priced"]),
        "top200_billed_eur": round(top["billed_eur"].sum()),
        "top200_with_price_pns": int((top["competition"] == 2).sum()),
        "top200_rival_pns": int((top["competition"] == 1).sum()),
        "top200_rival_eur": round(top.loc[top["competition"] == 1, "billed_eur"].sum()),
        "worklist_pns": int(wl["counts"]["part_numbers"]),
        "worklist_eur": round(wl["counts"]["billed_eur"]),
        "worklist_brand_named": int(wl["counts"]["brand_named"]),
        "worklist_brand_named_eur": round(wl["counts"]["brand_named_billed_eur"]),
        "worklist_crit_a": int(wl["counts"]["criticality_A"]),
        "spine_billed_eur": round(fam["billed_eur"].sum()),
        "spine_step_eur": round(fam["step_eur"].sum()),
    }


def panel_truth() -> dict:
    """Re-derive the competitor-panel headlines."""
    ks = pd.read_csv(os.path.join(D, "iam_ks_price_gap.csv"), dtype={"pn": str})
    ks["idx"] = ks["proj_retail_eur"] / ks["ks_am_min_eur"]
    uniq = ks.groupby("pn")["idx"].nunique()
    return {
        "ks_pns": int(ks["pn"].nunique()),
        "ks_markets": int(ks["db"].nunique()),
        "ks_same_index_everywhere": int((uniq == 1).sum()),
        "ks_median_index": round(float(ks.groupby("pn")["idx"].median().median()), 2),
        "ks_one_price_rows": int((ks["competitor_count"] == 1).sum()),
        "ks_rows": int(len(ks)),
        "ks_median_brands": float(ks["competitor_count"].median()),
    }


def check_numbers(html: str, truth: dict) -> list:
    """Every claim below must appear in the page, formatted as stated."""
    fails = []

    def want(label, needle):
        ok = needle in html
        print(f"  {'PASS' if ok else 'FAIL'}  {label:<46} {needle}")
        if not ok:
            fails.append(label)

    print("NUMBERS WRITTEN INTO THE PAGE")
    want("weighted base price move", f"{truth['weighted_pct']:.4f}%")
    want("step euro, millions", f"\u20ac{truth['step_eur_m']:.2f}M")
    want("gross profit, millions", f"\u20ac{truth['gross_profit_eur_m']:.2f}M")
    want("book weighted margin", f"{truth['gm_pct']:.2f}%")
    want("priced book euro", f"{truth['billed_priced_eur']:,d}")
    want("top-200 rival count", str(truth["top200_rival_pns"]))
    want("worklist part numbers", str(truth["worklist_pns"]))
    want("worklist brand-named count", str(truth["worklist_brand_named"]))
    want("worklist criticality A", str(truth["worklist_crit_a"]))
    want("spine step euro, millions", f"{truth['spine_step_eur']/1e6:.2f}M")
    want("spine billed euro, full", f"{truth['spine_billed_eur']:,d}")
    return fails


def check_render(path: str) -> list:
    """Open in a real browser: script parses, no console errors, canvases painted."""
    fails = []
    print()
    print("BROWSER RENDER")

    scripts = re.findall(r"<script>(.*?)</script>", open(path, encoding="utf-8").read(), re.S)
    app = scripts[-1] if scripts else ""
    with tempfile.NamedTemporaryFile("w", suffix=".js", delete=False, encoding="utf-8") as fh:
        fh.write(app)
        tmp = fh.name
    r = subprocess.run(["node", "--check", tmp], capture_output=True, text=True)
    os.unlink(tmp)
    print(f"  {'PASS' if r.returncode == 0 else 'FAIL'}  app script parses")
    if r.returncode:
        print("        " + r.stderr.strip().split("\n")[0])
        fails.append("script parses")

    ids = re.findall(r'<canvas id="([^"]+)"', open(path, encoding="utf-8").read())
    dupes = {k: v for k, v in Counter(ids).items() if v > 1}
    print(f"  {'PASS' if not dupes else 'FAIL'}  canvas ids unique ({len(ids)} canvases)")
    if dupes:
        fails.append(f"duplicate canvases {dupes}")

    if not os.path.isabs(path):
        path = os.path.join(ISZE, path)
    path = os.path.abspath(path)
    if not os.path.exists(path):
        say(f"  SKIP  file not found for render: {path}")
        return ["html not found"]

    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        print("  SKIP  playwright not available - canvas paint NOT VERIFIED")
        fails.append("playwright missing, canvas paint unverified")
        return fails

    errors = []
    with sync_playwright() as pw:
        b = pw.chromium.launch(channel="chrome")
        pg = b.new_page(viewport={"width": 794, "height": 1123})
        pg.on("console", lambda m: errors.append(f"[{m.type}] {m.text}")
              if m.type == "error" else None)
        pg.on("pageerror", lambda e: errors.append(f"[pageerror] {e}"))
        pg.goto("file:///" + path.replace("\\", "/"))
        pg.wait_for_timeout(3000)
        probe = pg.evaluate("""() => {
          const out = [];
          document.querySelectorAll('canvas').forEach(c => {
            const ctx = c.getContext('2d');
            const d = ctx.getImageData(0,0,c.width,c.height).data;
            let drawn = 0;
            for (let i=0;i<d.length;i+=4) {
              if (d[i+3] > 8 && (d[i]+d[i+1]+d[i+2])/3 < 244) drawn++;
            }
            out.push({id:c.id, drawn:drawn});
          });
          return JSON.stringify(out);
        }""")
        charts = json.loads(probe)
        b.close()

    print(f"  {'PASS' if not errors else 'FAIL'}  console clean ({len(errors)} errors)")
    for e in errors[:6]:
        print("        " + e)
    if errors:
        fails.append("console errors")

    blank = [c["id"] for c in charts if c["drawn"] < 400]
    for c in charts:
        mark = "PASS" if c["drawn"] >= 400 else "FAIL"
        print(f"  {mark}  canvas {c['id']:<10} {c['drawn']:>8,} px drawn")
    if blank:
        fails.append(f"blank canvases {blank}")
    return fails


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--html", required=True)
    ap.add_argument("--kind", default="pricing")
    a = ap.parse_args()

    if not os.path.exists(a.html):
        say(f"HTML not found: {a.html}")
        sys.exit(2)

    html = open(a.html, encoding="utf-8").read()
    say("=" * 78)
    say(f"FACT CHECK  {os.path.basename(a.html)}")
    say("=" * 78)

    truth = truth_pricing()
    truth.update(panel_truth())
    fails = check_numbers(html, truth)
    fails += check_render(a.html)

    say()
    say("=" * 78)
    if fails:
        say(f"FACT_CHECK_FAIL  ({len(fails)})")
        for f in fails:
            say(f"  - {f}")
        sys.exit(1)
    say("FACT_CHECK_OK")
    sys.exit(0)


if __name__ == "__main__":
    main()
