# -*- coding: utf-8 -*-
"""
Verify the five-sheet pricing workbook, on the MEASURED method.

The method under test:

    weighted increase = SUM(qty x delta_jpy) / SUM(qty x bp_prior) - 1
  on the published recipe: in_scope == TRUE AND unpriced_reason IS NULL -> 47,617 rows.

NO EXCHANGE RATE AND NO DISCOUNT IS MULTIPLIED INTO THE MOVE. Both are already in force:
the rate of 178.5 is what we pay now, and the purchase discount of 67.3% took effect on
5 January 2026. An earlier version of the workbook multiplied both in and produced
figures that were wrong.

There is also NO PASS-THROUGH DIAL. The rate is issued by ISZJ and applied; it is not a
commercial choice. The dial, the five-point grid and the "what each source needs" block
have been removed, and this file asserts their absence.

Run: python 01_data/91_build/verify_pricing_stack_simulation_20260919.py
"""
from __future__ import annotations

import io
import json
import re
import sys
import zipfile
from pathlib import Path
from xml.etree import ElementTree

import pandas as pd
from openpyxl import load_workbook

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

ISZE = Path(r"C:\Users\jerom\Desktop\claude\ISZE")
DERIVED = ISZE / "01_data" / "00_derived"
XLSX = ISZE / "01_data" / "01_Pricing" / "ISZE_Pricing_Stack_Simulation_2026-09-19.xlsx"
CMD = ISZE / "01_data" / "01_Pricing" / "OPEN_Pricing_Stack_Simulation.cmd"
JSON_IN = DERIVED / "pricing_stack_simulation_2026-09-19.json"
NS = "{http://schemas.openxmlformats.org/spreadsheetml/2006/main}"

RECIPE_INDEX = 0.059616
RECIPE_J, RECIPE_T = 0.062081, 0.063088
PR00_REGIONS = ("WEST", "SOUTH", "EAST", "NORDICS", "MIDDLE_EAST")
BANNED = ("pass-through", "pass through", "passthrough", "pass_through",
          "retain the relief", "retains the relief", "retain the rest",
          "hand on", "hand it on", "one dial cannot satisfy")

fails = []


def say(m: str = "") -> None:
    print(m)
    sys.stdout.flush()


def check(label: str, got, exp, tol: float) -> None:
    ok = abs(float(got) - float(exp)) <= tol
    say(f"  {'PASS' if ok else 'FAIL'}  {label:<60} got {float(got):>15,.6f}  "
        f"expected {float(exp):>15,.6f}")
    if not ok:
        fails.append(f"{label}: got {got}, expected {exp}")


def check_bool(label: str, ok: bool) -> None:
    say(f"  {'PASS' if ok else 'FAIL'}  {label}")
    if not ok:
        fails.append(label)


say("=" * 100)
say("1. THE WORKBOOK OPENS, AND THE FIVE SHEETS ARE EXACTLY AS ASKED")
say("=" * 100)
wb = load_workbook(XLSX, data_only=False)
want = ["Legends", "PR00", "UTI", "UMI", "CIS"]
say(f"  sheets found: {wb.sheetnames}")
check_bool(f"exactly five sheets, named {want}", wb.sheetnames == want)
leg = wb["Legends"]

say()
say("=" * 100)
say("2. THE MEASURE IS ON THE SHEET, AND NO FACTOR CHAIN IS")
say("=" * 100)
text = " ".join(str(c.value) for ws in wb.worksheets for row in ws.iter_rows()
                for c in row if isinstance(c.value, str))
low = text.lower()
check_bool("the Legends sheet states the measured formula",
           "sum(qty x delta_jpy) / sum(qty x bp_prior)" in low)
check_bool("the recipe row count of 47,617 is on the sheet", "47,617" in text)
check_bool("the sheet states no exchange rate and no discount is multiplied in",
           "no exchange rate and no discount is multiplied into the move" in low)
check_bool("the sheet states the rate is issued and applied, not a decision",
           "issued by iszj and applied, not a decision" in low)

labels = {}
for rr in range(1, leg.max_row + 1):
    v = leg.cell(rr, 1).value
    if isinstance(v, str):
        labels[v.strip().lower()] = rr


def row_of(frag):
    for k, rr in labels.items():
        if frag.lower() in k:
            return rr
    return None


R_FX = row_of("live rate 01/10/2026")
R_DJ = row_of("purchase discount j (japan), live")
R_DT = row_of("purchase discount t (thailand)")
R_CIS = row_of("cis factor")
check_bool("a live exchange-rate row exists", R_FX is not None)
check_bool("a live Japan discount row exists", R_DJ is not None)
check_bool("a Thailand discount row exists", R_DT is not None)
check_bool("a CIS factor row exists", R_CIS is not None)
if R_FX and R_DJ and R_DT and R_CIS:
    check("the live rate is 178.5", float(leg.cell(R_FX, 2).value), 178.5, 1e-9)
    check("the live Japan discount is 67.3%",
          float(leg.cell(R_DJ, 2).value), 0.673, 1e-9)
    check("the Thailand discount is 61.1%",
          float(leg.cell(R_DT, 2).value), 0.611, 1e-9)
    check("the CIS factor is 0.40", float(leg.cell(R_CIS, 2).value), 0.40, 1e-9)
check_bool("the Japan discount is dated effective 5 January 2026",
           any(isinstance(leg.cell(rr, 1).value, str)
               and "05/01/2026" in str(leg.cell(rr, 1).value).lower()
               for rr in range(1, leg.max_row + 1))
           or "effective 5 january 2026" in low)

say()
say("=" * 100)
say("3. THE PASS-THROUGH FRAMING IS GONE, AND NOTHING REPLACES IT")
say("=" * 100)
say("  The terms below are searched across all five sheets. If any survives it must be")
say("  the Legends disclaimer that names the dial only to say it was invented and")
say("  removed. Nothing may state or imply a choice.")
say(f"  {'term':<34}{'present':>10}")
mkt_text = " ".join(str(c.value) for code in ("PR00", "UTI", "UMI", "CIS")
                    for row in wb[code].iter_rows() for c in row
                    if isinstance(c.value, str)).lower()
for b in BANNED:
    present = (b in low) or (b in mkt_text)
    say(f"  {'NOTE' if present else 'PASS'}  {b!r} present: {present}")
check_bool("no pass-through framing on any market sheet",
           not any(b in mkt_text for b in BANNED))
check_bool("no pass-through dial row on Legends",
           row_of("pass-through of the") is None)
check_bool("no 'what each source needs' block on Legends",
           row_of("what each source needs") is None)
check_bool("no relief row on Legends", row_of("relief") is None)
check_bool("no grid table on Legends", row_of("the pass-through grid") is None)
check_bool("no 'Pass-through dial' block on any market sheet",
           not any("pass-through" in str(wb[c].cell(r, 1).value).lower()
                   for c in ("PR00", "UTI", "UMI", "CIS")
                   for r in range(1, wb[c].max_row + 1)
                   if isinstance(wb[c].cell(r, 1).value, str)))
mentions = [str(c.value) for row in leg.iter_rows() for c in row
            if isinstance(c.value, str) and "pass-through" in str(c.value).lower()]
say(f"  pass-through mentions remaining on Legends: {len(mentions)}")
for mtext in mentions:
    say(f"        {mtext[:120]}")
check_bool("every surviving mention is the disclaimer that it was invented and removed",
           all("invented" in mtext.lower() and "removed" in mtext.lower()
               for mtext in mentions))
check_bool("no pass-through number survives anywhere on Legends",
           not re.search(r"pass-through[^.]{0,40}\d",
                         " ".join(mentions).lower()))
say()
say("  NOTE ON WHAT WAS REMOVED, AND WHAT THAT COSTS THIS FILE")
say("  Checks that asserted the pass-through dial default, its five-point grid and the")
say("  one-dial flag are deleted. They guarded invented numbers, so removing them")
say("  unguards nothing that was true. What replaces them: the dial row, the grid and")
say("  the 'what each source needs' block are now asserted ABSENT, and the two open")
say("  items are asserted present in section 6. Every other check still runs: the sheet")
say("  names and layout, the freeze panes, the no-lookup rule, the source column, the")
say("  container, the per-market figures and the language sweep.")

say()
say("=" * 100)
say("4. THE NUMBERS, RECOMPUTED FROM THE RAW FILES ON THE SAME METHOD")
say("=" * 100)
cmp_ = pd.read_csv(DERIVED / "price_bp_weighted_compare_pn.csv",
                   dtype={"part_number": str, "customer_code": str})
rec = cmp_[(cmp_["in_scope"] == True) & cmp_["unpriced_reason"].isna()].copy()  # noqa: E712
rec["pn"] = rec["part_number"].astype(str).str.strip().str.zfill(10)
rec = rec[rec["billed_qty"].notna() & rec["bp_prior_revised"].notna()
          & rec["delta_jpy"].notna()].copy()
rec["weight"] = rec["billed_qty"] * rec["bp_prior_revised"]
rec["step_yen"] = rec["billed_qty"] * rec["delta_jpy"]
idx = rec["step_yen"].sum() / rec["weight"].sum()
say(f"  the published recipe: {len(rec):,} rows -> {idx:.8f} = {100*idx:.6f}%")
check("the published 5.9616% reproduces on the recipe", idx, RECIPE_INDEX, 1e-6)

pl = pd.read_parquet(DERIVED / "pricing_list_pn.parquet",
                     columns=["part_number", "source", "is_superseded_row"])
pl = pl[pl["is_superseded_row"] != True].drop_duplicates("part_number")       # noqa: E712
pl["pn"] = pl["part_number"].astype(str).str.strip().str.zfill(10)
rec = rec.merge(pl[["pn", "source"]], on="pn", how="left")
rec["srclab"] = rec["source"].where(rec["source"].isin(["J", "T"]), "(none)")
for s, exp in (("J", RECIPE_J), ("T", RECIPE_T)):
    g = rec[rec["srclab"] == s]
    check(f"the per-source weighted increase, {s}",
          g["step_yen"].sum() / g["weight"].sum(), exp, 1e-5)


def mask(code):
    if code == "PR00":
        return rec["region"].isin(PR00_REGIONS)
    if code == "UTI":
        return rec["customer_code"].astype(str).str.strip().eq("1799")
    if code == "UMI":
        return rec["customer_code"].astype(str).str.strip().eq("1797")
    return rec["region"].eq("CIS")


RECOMP = {}
for code in ("PR00", "UTI", "UMI", "CIS"):
    g = rec[mask(code).values]
    RECOMP[code] = {"rows": int(len(g)), "part_numbers": int(g["pn"].nunique()),
                    "billed": float(g["net_sales_value"].sum()),
                    "increase": float(g["step_yen"].sum() / g["weight"].sum()),
                    "japan": float(g[g["srclab"].eq("J")]["step_yen"].sum()
                                   / g[g["srclab"].eq("J")]["weight"].sum()),
                    "thailand": float(g[g["srclab"].eq("T")]["step_yen"].sum()
                                      / g[g["srclab"].eq("T")]["weight"].sum())}
    say(f"  {code:<5}{len(g):>8,} rows  {g['pn'].nunique():>7,} PNs  "
        f"{100*RECOMP[code]['increase']:+9.6f}%   "
        f"Japan {100*RECOMP[code]['japan']:+9.6f}%   "
        f"Thailand {100*RECOMP[code]['thailand']:+9.6f}%")

say()
say("=" * 100)
say("5. THE WRITTEN JSON MUST AGREE WITH THIS RECOMPUTATION")
say("=" * 100)
meta = json.loads(JSON_IN.read_text(encoding="utf-8"))
check_bool("json: the method is the measured weighted increase",
           meta["method"]["formula"].replace(" ", "").startswith(
               "weighted_increase=SUM(qtyxdelta_jpy)/SUM(qtyxbp_prior)-1"))
check_bool("json: no factor chain is declared",
           meta["method"]["no_factor_chain"] is True)
check_bool("json: the exchange rate is declared not to be a decision",
           meta["method"]["exchange_rate_is_a_decision"] is False)
check("json: the computed index", meta["method"]["computed"], RECIPE_INDEX, 1e-6)
check_bool("json: the architecture is recorded as his - no lookups, values carried",
           "no VLOOKUP" in meta["architecture"])
check_bool("json: no what_each_source_needs block",
           "what_each_source_needs" not in json.dumps(meta))
check_bool("json: no pass_through block", "pass_through" not in json.dumps(meta))
check("json: whole book agrees", meta["whole_book"]["weighted_increase"], idx, 1e-9)
for code, dd in RECOMP.items():
    m = meta["markets"].get(code)
    check_bool(f"{code}: present in the json", m is not None)
    if not m or not m.get("rows"):
        continue
    check(f"{code}: rows", m["rows"], dd["rows"], 0)
    check(f"{code}: part numbers", m["part_numbers"], dd["part_numbers"], 0)
    check(f"{code}: weighted increase", m["increase"], dd["increase"], 1e-9)
    check(f"{code}: Japan", m["japan"], dd["japan"], 1e-9)
    check(f"{code}: Thailand", m["thailand"], dd["thailand"], 1e-9)

say()
say("=" * 100)
say("6. THE TWO OPEN ITEMS ARE ON THE SHEET AND IN THE JSON")
say("=" * 100)
ids = {f["id"] for f in meta["open_items"]}
check_bool("the industrial-engine rate is an open item", "IE_RATE" in ids)
check_bool("the revision-size gap is an open item", "REVISION_SIZE" in ids)
check_bool("the IE open item is on the Legends sheet",
           "industrial-engine rate" in low or "only the vehicle-parts rate" in low)
check_bool("the revision gap is on the Legends sheet",
           "different revision size" in low)
check_bool("the 62% vehicle-parts factor is on the sheet",
           "62%" in text and "Export Base Price" in text)
check_bool("the 73.5% industrial-engine factor is on the sheet", "73.5%" in text)
check_bool("the IML 3% statement is on the sheet", "around 3%" in text)
ie = next(f for f in meta["open_items"] if f["id"] == "IE_RATE")
check_bool("the IE item says config.yaml is left alone",
           "config.yaml is left alone" in ie["action"])
rv = next(f for f in meta["open_items"] if f["id"] == "REVISION_SIZE")
check_bool("the revision item carries both figures",
           "3%" in rv["detail"] and "5.9616" in rv["detail"])

say()
say("=" * 100)
say("7. THE ARCHITECTURE - NO LOOKUPS OR ARRAYS, VALUES CARRIED, PROVENANCE PRESENT")
say("=" * 100)
z = zipfile.ZipFile(XLSX)
say(f"  {'sheet part':<26}{'<f> count':>11}")
for n in sorted(x for x in z.namelist()
                if re.match(r"xl/worksheets/sheet\d+\.xml$", x)):
    root = ElementTree.fromstring(z.read(n))
    say(f"  {n:<26}{len(list(root.iter(f'{NS}f'))):>11}")
bad = {}
for n in z.namelist():
    if not re.match(r"xl/worksheets/sheet\d+\.xml$", n):
        continue
    root = ElementTree.fromstring(z.read(n))
    txt = " ".join((f.text or "") for f in root.iter(f"{NS}f"))
    for fn in ("VLOOKUP", "SUMPRODUCT", "SUMIF", "COUNTIF", "INDEX", "MATCH",
               "HLOOKUP", "XLOOKUP"):
        c = txt.count(fn + "(")
        if c:
            bad[fn] = bad.get(fn, 0) + c
check_bool(f"zero lookup/array functions across all <f> elements ({bad})", not bad)
check_bool("no macro part in the package",
           not any("vbaProject" in n for n in z.namelist()))
check_bool("no external link part in the package",
           not any("externalLink" in n for n in z.namelist()))
check_bool("no pivot cache in the package",
           not any("pivotCache" in n or "pivotTable" in n for n in z.namelist()))
cross = 0
for code in ("PR00", "UTI", "UMI", "CIS"):
    for row in wb[code].iter_rows():
        for cc in row:
            v = cc.value
            if isinstance(v, str) and v.startswith("=") and "!" in v:
                cross += 1
check_bool(f"no market-sheet formula references another sheet ({cross} found)",
           cross == 0)
check_bool("no invented provenance code appears anywhere",
           not any(isinstance(c.value, str) and c.value in ("J99", "T99", "X99")
                   for ws in wb.worksheets for row in ws.iter_rows() for c in row))
check_bool("the Source column header is his 'Source'",
           wb["UTI"].cell(1, 4).value == "Source")
check_bool("the Legends sheet carries a Sources block",
           row_of("sources - every input") is not None)
check_bool("the Legends sheet states how many rows carry no source label",
           any(isinstance(leg.cell(rr, 1).value, str)
               and "no source label" in str(leg.cell(rr, 1).value).lower()
               for rr in range(1, leg.max_row + 1)))
check_bool("the Sources block states that changing a value there does not propagate",
           any(isinstance(leg.cell(rr, 1).value, str)
               and "does NOT" in str(leg.cell(rr, 1).value)
               for rr in range(1, leg.max_row + 1)))

say()
say("  THE FREEZE PANE - one frame under the header, never a bottom row. This is the")
say("  defect that cost Jerome two turns: the helper used to set the pane on every")
say("  header row it wrote, so the sheet was pinned at a low row and only a handful of")
say("  rows would scroll.")
for code in ("PR00", "UTI", "UMI", "CIS"):
    ws = wb[code]
    fp = ws.freeze_panes
    check_bool(f"{code}: freeze_panes is A2 (got {fp!r})", fp == "A2")
    ysplit = 1 if fp == "A2" else int(re.sub(r"\D", "", str(fp)) or 0)
    check_bool(f"{code}: ySplit is 1, so {ws.max_row - ysplit:,} rows scroll",
               ysplit == 1 and ws.max_row - ysplit > 1000)
check_bool(f"Legends: no freeze pane (got {leg.freeze_panes!r})",
           leg.freeze_panes is None)

say()
say("  THE LAYOUT - no wrapping and no explicit row height in the data rows, because")
say("  wrapping makes Excel auto-fit every row to its tallest content and the sheet")
say("  cannot be scrolled.")
for code in ("PR00", "UTI", "UMI", "CIS"):
    ws = wb[code]
    wrapped = sum(1 for row in ws.iter_rows(min_row=2)
                  for c in row if c.alignment is not None and c.alignment.wrap_text)
    heights = sum(1 for r in range(2, ws.max_row + 1)
                  if ws.row_dimensions.get(r) is not None
                  and ws.row_dimensions[r].height is not None)
    check_bool(f"{code}: zero wrapped cells in the data ({wrapped})", wrapped == 0)
    check_bool(f"{code}: no explicit row height on a data row ({heights})",
               heights == 0)
    check_bool(f"{code}: row 1 is the real header (PN in A1)",
               ws.cell(1, 1).value == "PN")

say()
say("=" * 100)
say("8. THE LAUNCHER IS CRLF, AND NO BANNED OR STALE LANGUAGE")
say("=" * 100)
raw = CMD.read_bytes()
n_crlf = raw.count(b"\r\n")
n_bare = raw.count(b"\n") - n_crlf
check_bool(f"launcher CRLF ({n_crlf} CRLF, {n_bare} bare LF)",
           n_crlf == 2 and n_bare == 0)
for bad_w in ("sell-out", "sell out", "wallet", "street", "mode a", "mode b"):
    check_bool(f"workbook avoids {bad_w!r}", bad_w not in low)
plain = re.sub(r"\s+", " ", low)
check_bool("workbook avoids 'Book B' (word-boundary)",
           re.search(r"\bbook[\s\-]?b\b", plain) is None)
check_bool("the class factors are shown as margins (=1-factor)",
           any(isinstance(leg.cell(rr, 5).value, str)
               and str(leg.cell(rr, 5).value).startswith("=1-B")
               for rr in range(1, leg.max_row + 1)))
check_bool("CIS is documented as class-independent",
           "class-independent" in low)
check_bool("no internal model nickname in the workbook",
           "iml v7" not in low)

say()
say("=" * 100)
if fails:
    say(f"SIMULATION_VERIFY_FAIL ({len(fails)})")
    for f in fails:
        say(f"  - {f}")
else:
    say("SIMULATION_VERIFY_OK")
say("=" * 100)
