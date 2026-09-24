"""Refresh the top of STATE_PACKET.md with the current facts.

Byte-level UTF-8: read the bytes, decode, insert the new front block, encode, write.
Nothing below the insertion point is touched, so the file's history stays intact and no
existing character can be damaged. (PowerShell ReadAllText/WriteAllText is what injured
DELEGATOR_BOARD.md earlier today - never used here.)
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
P = Path(r"C:\Users\jerom\Desktop\claude\ISZE\00_docs\agent\STATE_PACKET.md")

FRONT = """**Updated:** 2026-09-24 19:55 \u2014 AIM refresh finished: 17 pages rebuilt on the settled master, all signed

## AIM refresh, second pass (2026-09-24 19:00\u201319:55) \u2014 every page on the current classification

**Master, measured.** `01_data\\00_derived\\aim_master_v2.csv` settled at **19:17:03**, 28,612,879 bytes,
**165,290 rows** (sha256 `8add5556\u2026`), after another agent added the **Cab Assembly** class
(Accident & Body > Complete Assembly > Cab Assembly, 20 part numbers, **EUR 119,407 of L12M billing**
\u2014 111,125 of it on `7552044930`). Watched until stable for two minutes before building, then
re-checked before the commit. **Not written by this pass.**

**Found and fixed the four outstanding items.**

1. **The three stale pages now read current data.** Their intermediates were the stale part, not
   the pages. Rebuilt in order: `build_pms_tonnage_model.py` (band model unchanged row for row;
   `aim_evolution_model.csv` 18,865 \u2192 19,534 rows, same total euro), `build_bvp_p4_p5.py`
   (GPS exposure and family risk live again; gps_spu family/PMS files byte-identical),
   `enrich_gps_spu_v9.py` (re-adds the seven v9 target columns the raw P4 build drops),
   `build_aim_gps_matrix.py`, `build_nseries_tonnage_bands.py`. Then the pages:
   **ISZE_PMS_Tonnage_Evolution**, **ISZE_PMS_Family_Compare**, **ISZE_DB_DLR_Replenishment_CY2025**.
   **Extra pages those builders touch, all rebuilt and signed:** ISZE_KPI_Dashboard,
   ISZE_Risk_Cockpit, `01_data/14_dashboards/isze_data.json` + preload, `viz/risk_cockpit.json`,
   `01_data/14_dashboards/dealer_sellout_aim_gps.json`.
2. **AIM_Dashboard_CY2026 is signed.** The CDN fallback line is gone and the local
   `../_ui/plotly.min.js` reference stays. Inlining the 4.85 MB library was tried first and renders
   correctly, but the house receipt writer refuses any page whose text contains `cdn.plot.ly` or a
   `NaN` literal \u2014 and Plotly's own source contains both. So the page ships next to its library, as
   it did before, and the launcher opens it. Named, not hidden.
3. **Verifiers, run on what they cover:** `verify_aftermarket_bi_command_center.py` **exit 0**;
   `verify_tier_a_html_json.py` **exit 1** (pre-existing \u2014 `ISZE_Aftermarket_BI_Command_Center.html`
   hero, untouched today); `ship_gate_check.ps1` **exit 1** (inherits that same failure; `HUB_GUARD_OK`
   printed); `verify_derived_pipeline.py` **exit 0**, 163 pass / 2 warn / 0 fail.
4. **Every other AIM-master reader found and refreshed:** the paper, the pricing cube and its nine
   pages, the lost-sales model and its page, the KPI dashboard, the risk cockpit and the dashboard
   JSONs. The four deep-dive and comparison pages still read the restored 2026-09-21 export pair by
   name \u2014 **discovered and deliberately left**, because repointing them is a change of meaning.

**Page count.** 17 pages rebuilt, 17 `SHIP_RECEIPT.json` at `ok: true` (schema v2, read count equals
taken), covering the current file times. **27 screenshots taken, 27 read, one at a time.** No blank
panel, no empty table, no `NaN` in visible text. Two pages render with no canvas by design (family
compare and the CY2026 page use bar rows and tables).

**Open, needs a decision (not blocking).** `ISZE_OS_Hub.html` and `ISZE_OS_Console.html` still read
`aim_pn_classification.csv` by name and print 98% / 1.8%; pointing them at `aim_master_v2.csv` is a
change of meaning. `ISZE_DB_DLR_Replenishment_CY2025.html` still reads the restored 2026-09-21 pair,
as do the four AIM deep-dive and comparison pages. The tier-A failure above predates this pass.

**Standing risk, unchanged.** `build_aim_master.py` does not read the master as an input, so a spine
rebuild drops every appended row unless the append is folded into that builder first.

## History \u2014 prior packets, kept as they were

"""

raw = P.read_bytes()
text = raw.decode("utf-8")
marker = "**Updated:** 2026-09-24"
i = text.index(marker)
j = text.index("\n", i) + 1
new = text[:i] + FRONT + text[j:]

if "AIM refresh, second pass" in text:
    raise SystemExit("front block already present - refusing to insert twice")
assert new.count("\ufffd") == 0, "replacement character appeared"

P.write_bytes(new.encode("utf-8"))
print("bytes", len(raw), "->", len(new))
print("U+FFFD", new.count("\ufffd"), "| em-dash", new.count("\u2014"), "| euro", new.count("\u20ac"))
print("front block inserted:", "AIM refresh, second pass" in new)
