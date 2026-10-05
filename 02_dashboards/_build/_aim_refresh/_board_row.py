import sys
sys.stdout.reconfigure(encoding="utf-8")

ROW = (
    "| 2026-09-24 18:13 | cursor (AIM dashboard refresh) | "
    "**19 AIM pages rebuilt on today's classification. 20 receipts written. One page could not be signed, and three were left alone.** "
    "Found 109 pages carrying AIM material across 02_dashboards and 09_meetings; 19 are a real AIM subject with a builder of their own. "
    "Every one was rebuilt by running its existing builder with its existing arguments, re-reading aim_master_v2.csv at build time. No figure, formula or definition was changed. "
    "The master was measured, not trusted: 165,257 rows to 165,289, rows carrying a real family 20,662 to 21,548, the Unknown marker 4,271 to 3,603, 1,229 rows stamped export_aim_eq_20260924. "
    "It moved again at 17:01 under me and I did not write it. "
    "Headline moves: classification paper classified part numbers 165,213 to 165,289 and parts with AIM labels 19,791 to 21,015. "
    "FX overlay lines not on the AIM spine 2,245 to 1,217 and their euro 318,420 to 118,048. "
    "+5% review part numbers not on the AIM spine 1,967 to 1,321 and their euro 1,071,113 to 647,861. "
    "Pricing revision drill groups 5,756 to 5,973 and brake part numbers 1,544 to 1,772. "
    "AIM CY2026 coverage 97.6 to 97.7 per cent and open or review euro 209,610 to 203,727, but that page's YoY moved 10.4 to 8.3 per cent on live billing and I cannot attribute that to the classification. "
    "Rendered every page from file:// in headless Chrome, 34 screenshots taken and 34 read by me, no blank panel and no empty Top-N shell. "
    "No embedded payload carries a literal NaN. "
    "One page left unsigned: AIM_Dashboard_CY2026.html fails the receipt writer on a Plotly CDN fallback line, which is a page edit rather than a data refresh, and it is not fully self-contained - it loads ../_ui/plotly.min.js and its data file, which are present. "
    "Three left alone: ISZE_PMS_Family_Compare, ISZE_PMS_Tonnage_Evolution and ISZE_DB_DLR_Replenishment_CY2025 read the master through stale intermediates built at 07:30 and 07:53 whose generator also refreshes pages outside this brief. "
    "Two build notes and build stamps stripped at the builder from the Pricing Policy Paper and the Dealer Sellout AIM GPS page. "
    "Four launchers fixed, all currently cannot sign off. "
    "**Current sign-off: 20 of 21 pages signed; AIM_Dashboard_CY2026 left unsigned and named.** | "
    "`02_dashboards/sales/` (7 pages + data file + 4 launchers), `02_dashboards/pricing/` (9 pages), `02_dashboards/hub/ISZE_OS_Hub.html`, "
    "`02_dashboards/ops/ISZE_OS_Console.html`, `02_dashboards/_build/AIM_DASHBOARD_REFRESH_20260924.md`, "
    "four builders under `04_tools/aim_db_dlr_deep_dive/` and `03_analytics/Isuzu/prism/scripts/`, "
    "`02_dashboards/_build/_aim_refresh/` (probes, paint reports, 34 screenshots, before-images) | "
    "Jerome to decide two things that need his word, not mine: "
    "(1) the OS Hub and OS Console AIM cells still read aim_pn_classification.csv by name and still print 98 per cent and 1.8 per cent - point them at aim_master_v2.csv or leave them; "
    "(2) whether to run sync_evidence_derived.py to bring the three stale-intermediate pages into line, knowing it moves pages beyond AIM. "
    "Also unresolved: the AIM_Dashboard_CY2026 Plotly CDN line, and the pre-existing tier-A failure on ISZE_Aftermarket_BI_Command_Center.html which I did not touch. |\n"
)

p = "00_docs/agent/DELEGATOR_BOARD.md"
raw = open(p, "rb").read()
if b"cursor (AIM dashboard refresh)" in raw:
    raise SystemExit("my row is already on the board - refusing to append twice")
assert raw.count(b"\r\n") == 0, "unexpected CRLF"
assert raw.endswith(b"\n"), "file does not end with a newline"
for ch in ROW:
    if ord(ch) > 127:
        raise SystemExit("non-ascii char: " + repr(ch))
# exactly 5 cells => exactly 6 pipes, and no pipe inside the cell text
assert ROW.count("|") == 6, f"expected 6 pipes, got {ROW.count('|')}"
assert "\u2192" not in ROW and "—" not in ROW and "·" not in ROW
open(p, "ab").write(ROW.encode("ascii"))
print("appended 1 row")
print("pipes in row:", ROW.count("|"))
print("new bytes:", len(open(p, "rb").read()))
