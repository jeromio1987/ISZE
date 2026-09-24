"""Append exactly ONE change-log row to DELEGATOR_BOARD.md, byte level, then check it.

- ASCII only in the appended bytes, so no character can be mangled by an encoding.
- exactly 5 cells: 6 pipes, no pipe inside any cell.
- never uses PowerShell ReadAllText/WriteAllText on this file (that is what broke it at 18:19).
- after the append, re-measure the whole file and print the checks.
"""
from __future__ import annotations

import sys
from collections import Counter
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
P = Path(r"C:\Users\jerom\Desktop\claude\ISZE\00_docs\agent\DELEGATOR_BOARD.md")

ROW = (
    "| 2026-09-24 19:55 | cursor (AIM refresh, second pass) | "
    "**The four outstanding refresh items are done: 17 pages rebuilt on the settled master, 17 signed.** "
    "The master settled at 19:17:03 after another agent added the Cab Assembly class "
    "(20 part numbers, EUR 119,407 of the last twelve months of billing, 111,125 of it one service cab). "
    "It was watched until stable for two minutes before building and re-checked before the commit. This pass did not write it. "
    "The three pages that read stale files now read current ones. Their intermediates were stale, not the pages. "
    "Rebuilt in order: build_pms_tonnage_model.py, build_bvp_p4_p5.py, enrich_gps_spu_v9.py, build_aim_gps_matrix.py, build_nseries_tonnage_bands.py, "
    "then ISZE_PMS_Tonnage_Evolution, ISZE_PMS_Family_Compare and ISZE_DB_DLR_Replenishment_CY2025. "
    "Extra pages those builders touch, all rebuilt and signed: ISZE_KPI_Dashboard, ISZE_Risk_Cockpit, isze_data.json with its preload, viz/risk_cockpit.json, dealer_sellout_aim_gps.json. "
    "The band model is unchanged row for row and the aim evolution file grew 18,865 to 19,534 rows on the same total euro. "
    "AIM_Dashboard_CY2026 is now signed: the CDN fallback line is gone and the local plotly file next to the page stays. "
    "Inlining the library was tried first and renders correctly, but the receipt writer refuses any page carrying the CDN string or a NaN literal, and the library source contains both. "
    "Chapter and verse: verify_aftermarket_bi_command_center.py exit 0; verify_tier_a_html_json.py exit 1 on the pre-existing Aftermarket BI Command Center hero, untouched today; "
    "ship_gate_check.ps1 exit 1 inheriting that same failure with HUB_GUARD_OK printed; verify_derived_pipeline.py exit 0 on 163 pass, 2 warn, 0 fail. "
    "Every other reader of the master was found and refreshed: the classification paper, the pricing cube and its nine pages, the lost sales model and its page, the KPI dashboard, the risk cockpit, the dashboard JSONs. "
    "27 screenshots taken and 27 read one at a time; no blank panel, no empty table, no NaN in visible text. "
    "Four deep dive and comparison pages still read the restored 2026-09-21 export pair by name and were deliberately left, because repointing them changes what they mean. | "
    "`01_data/00_derived/aim_evolution_model.csv`, `pms_tonnage_model.csv`, `gps_spu_by_distributor.csv`, `aim_bvp_family_risk.csv`, `aim_exposure_by_db_year.csv`, `aim_gps_matrix.csv`, "
    "`lost_sales_model.csv`, `nseries_tonnage_evolution.csv`, `01_data/14_dashboards/isze_data.json` + `isze_data.preload.js` + `viz/risk_cockpit.json` + `dealer_sellout_aim_gps.json`, "
    "`02_dashboards/sales/` (8 pages + receipts), `02_dashboards/pricing/` (9 pages + receipts), `02_dashboards/_build/_aim_refresh2/` (probes, before-copies, 27 screenshots, paint report) | "
    "Jerome to decide two things that are not mine to decide: whether the OS Hub and OS Console AIM cells should point at aim_master_v2.csv instead of aim_pn_classification.csv, "
    "and whether the deep dive and comparison pages should move off the restored 2026-09-21 export pair onto today's. "
    "Also open and named: the pre-existing tier-A failure on ISZE_Aftermarket_BI_Command_Center.html, and the fact that a spine rebuild would drop every appended row because build_aim_master.py does not read the master as an input. |\n"
)

raw = P.read_bytes()
if b"AIM refresh, second pass" in raw:
    raise SystemExit("this row is already on the board - refusing to append twice")
assert raw.count(b"\r\n") == 0, "unexpected CRLF"
assert raw.endswith(b"\n"), "file does not end with a newline"
for ch in ROW:
    if ord(ch) > 127:
        raise SystemExit("non-ascii char: " + repr(ch))
assert ROW.count("|") == 6, f"expected 6 pipes, got {ROW.count('|')}"

before_text = raw.decode("utf-8")
before = dict(
    fffd=before_text.count("\ufffd"),
    emdash=before_text.count("\u2014"),
    euro=before_text.count("\u20ac"),
    rows=sum(1 for l in before_text.split("\n") if l.startswith("|")),
)

P.open("ab").write(ROW.encode("ascii"))

after_raw = P.read_bytes()
after_text = after_raw.decode("utf-8")
lines = after_text.split("\n")
table_lines = [l for l in lines if l.startswith("|")]
cells = Counter(l.count("|") - 1 for l in table_lines)

print("appended 1 row, pipes in row:", ROW.count("|"))
print("U+FFFD", before["fffd"], "->", after_text.count("\ufffd"))
print("em-dash", before["emdash"], "->", after_text.count("\u2014"))
print("euro   ", before["euro"], "->", after_text.count("\u20ac"))
print("table lines", before["rows"], "->", len(table_lines))
print("cells per table line:", dict(cells))

problems = []
if after_text.count("\ufffd") != 0:
    problems.append("replacement characters present")
if after_text.count("\u2014") != before["emdash"] or after_text.count("\u20ac") != before["euro"]:
    problems.append("accented-character counts moved")
bad_rows = [i for i, l in enumerate(table_lines, 1) if l.count("|") - 1 not in (2, 5)]
if bad_rows:
    problems.append(f"rows that are neither 2 nor 5 cells: {bad_rows}")
print("\nproblems:", problems or "none")
