"""
ISZE FY2027 Review — Final Draft
================================
Built from ppt_template_v2 (real Isuzu logo, matplotlib chart theme).

Every number below is sourced from a real ISZE file — see inline comments.
Where sources conflict or data is missing, the slide says so explicitly
rather than picking a number silently. No figure here is estimated/invented.

Sources:
  - FY26 by-DB: Downloads\\FY2026_backup.csv (Jerome's confirmed pick over
    sales2022-2026-03.xlsx, which disagreed by EUR 830K network-wide)
  - FY27 target: 01_data\\91_build\\bp_fy27_reviewed.json (BP reviewed 24 Apr 2026)
  - Q1 FY27: 01_data\\04_sales\\(VP) Monthly report 2026-06.pdf
  - Fill rate: 01_data\\11_planning\\ISZE_DB_KPI_Targets_FY2627_v1.xlsx
  - GPS: 01_data\\00_derived\\gps_master.csv (gps_pct_FY2025), cross-checked
    against FACTS.md changelog for the network headline (51.1%, 2026-07-03 entry)
  - PMS/UTI filter capture: existing UTI Performance Review deck (FY2026 chart),
    reconciled against prism\\modules\\pms_engine.py capture-rate formula
  - Clutch interval: prism\\docs\\pms_service_intervals.md (Assumption, pending IML)
    + ISZE_ITUK_PMS_TripReport_Apr2026_revised.docx (clutch excluded phase 1)
  - SOR/urgent: 01_data\\00_derived\\q1fy2027_export_with_saty.csv (recomputed directly)
  - UTI warranty: 01_data\\00_derived\\warranty_by_db_FY_canonical.csv (Jerome's
    confirmed pick — FY canonical basis, not the CY2025-by-DB doc)
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
TEMPLATE_DIR = r"C:\Users\jerom\Desktop\claude\ISZE\04_tools\ppt_template_v2"
sys.path.insert(0, TEMPLATE_DIR)

import isze_chart_theme as ct
import isze_deck_builder as db

# Match the Office body font instead of the sandbox default
ct.FONT_FAMILY = "Calibri"
import matplotlib.pyplot as plt
plt.rcParams["font.family"] = ct.FONT_FAMILY

CHART_DIR = os.path.join(HERE, "charts_out")
os.makedirs(CHART_DIR, exist_ok=True)


def cp(name):
    return os.path.join(CHART_DIR, name)


# ============================================================================
# 1. FY26 network close by distributor (ex-MIDI/Turkey, per policy)
#    Source: Downloads\FY2026_backup.csv, aggregated + name-consolidated
# ============================================================================
ct.bar_chart(
    ["ITUK\n(UK)", "IUK\n(Ireland)", "UMI\n(Israel)", "ISD\n(Germany)",
     "UTI\n(Israel)", "IBX\n(Benelux)", "Imotors\n(Portugal)", "RSA\n(Norway)",
     "Sweden", "Ireland\n(CV)", "Others\n(9 DBs)"],
    {"FY2026 (EUR K)": [6520, 6510, 3020, 2732, 2679, 2282, 1838, 1618, 1453, 1134, 4124]},
    cp("fy26_by_db.png"),
    title="FY2026 Network Close by Distributor (EUR K, ex-MIDI/Turkey)",
    ylabel="EUR K",
    figsize=(10.6, 4.3),
)

# ============================================================================
# 2. FY27 target vs FY26 close — network + top 5 per-DB targets
#    Source: 01_data\91_build\bp_fy27_reviewed.json
# ============================================================================
ct.bar_chart(
    ["FY2026 close\n(ex-MIDI/Turkey)", "FY2027 target"],
    {"Network (EUR M)": [33.91, 35.28]},
    cp("fy27_target_network.png"),
    title="FY2027 Network Target vs FY2026 Close (EUR M)",
    ylabel="EUR M",
    value_fmt="{:,.2f}",
    figsize=(6.4, 4.3),
)

ct.bar_chart(
    ["ITUK", "IUK", "UTI", "UMI", "ISD"],
    {"FY2027 target (EUR M)": [6.97, 6.06, 3.10, 2.97, 2.91]},
    cp("fy27_target_top5.png"),
    title="FY2027 Target — Top 5 Distributors (EUR M)",
    ylabel="EUR M",
    value_fmt="{:,.2f}",
    figsize=(6.4, 4.3),
)

# ============================================================================
# 3. Q1 FY27 review (Apr-Jun 2026)
#    Source: 01_data\04_sales\(VP) Monthly report 2026-06.pdf
# ============================================================================
ct.bar_chart(
    ["Apr'26", "May'26", "Jun'26"],
    {"Sales (EUR K)": [3086, 2305, 3220], "BP (EUR K)": [2855, 2661, 3081]},
    cp("q1_fy27_monthly.png"),
    title="Q1 FY2027 — Sales vs BP by Month (EUR K)",
    ylabel="EUR K",
    figsize=(10.6, 4.3),
)

# ============================================================================
# 4. Fill rate — current vs FY26/27 target, selected distributors
#    Source: 01_data\11_planning\ISZE_DB_KPI_Targets_FY2627_v1.xlsx
# ============================================================================
ct.bar_chart(
    ["ITUK", "IUK", "UTI", "IBX", "Portugal", "Hungary\n(WAE)", "Greece"],
    {"Current fill %": [95, 93, 93, 85, 79.5, 69, 60],
     "FY26/27 target %": [96, 95, 95, 90, 87, 82, 80]},
    cp("fill_rate.png"),
    title="Fill Rate: Current vs FY26/27 Target (%)",
    ylabel="%",
    value_fmt="{:,.1f}",
    figsize=(10.6, 4.3),
)

# ============================================================================
# 5. GPS capture — network headline + selected distributors
#    Source: 01_data\00_derived\gps_master.csv (gps_pct_FY2025)
# ============================================================================
ct.bar_chart(
    ["Ireland", "IBX", "Iceland", "Portugal", "IUK", "UMI",
     "ISD", "AutoWallis", "ITUK", "UTI"],
    {"GPS % CY2025": [151.2, 97.3, 86.2, 74.0, 59.9, 59.9, 52.3, 39.4, 31.8, 31.8]},
    cp("gps_by_db.png"),
    title="GPS Capture by Distributor, CY2025 (%) — selected",
    ylabel="%",
    value_fmt="{:,.1f}",
    figsize=(10.6, 4.3),
)

# ============================================================================
# 6. PMS capture — UTI, filters vs brake vs clutch (FY2026)
#    Source: existing UTI Performance Review deck chart, cross-checked
#    against prism/modules/pms_engine.py capture formula
# ============================================================================
ct.bar_chart(
    ["Oil\nFilter", "Fuel\nFilter", "Air\nFilter", "Brake\nPad",
     "Clutch\nDisc", "Clutch\nPlate", "Clutch\nBooster"],
    {"UTI capture % FY2026": [31.3, 74.8, 58.1, 26.7, 4.3, 4.8, 1.1]},
    cp("pms_uti_capture.png"),
    title="UTI — PMS Capture Rate by Subcategory, FY2026 (%)",
    ylabel="%",
    value_fmt="{:,.1f}",
    figsize=(10.6, 4.3),
)

# ============================================================================
# 7. Urgent orders — SOR vs RUSH/VOR, network + UTI
#    Source: 01_data\00_derived\q1fy2027_export_with_saty.csv (recomputed)
# ============================================================================
ct.donut_share(
    ["SOR (stock order)", "VOR", "RUSH", "Other"],
    [74.2, 15.4, 9.0, 1.4],
    cp("saty_network.png"),
    center_label="of matched Q1 value", center_value="70.4%\nmatched",
    title="Network Order-Type Mix, Q1 FY2027 (% of matched EUR)",
)

ct.bar_chart(
    ["SOR", "RUSH", "VOR"],
    {"UTI % of matched": [88.4, 6.6, 5.1]},
    cp("saty_uti.png"),
    title="UTI Order-Type Mix, Q1 FY2027 (% of matched EUR, 82.2% matched)",
    ylabel="%",
    value_fmt="{:,.1f}",
    figsize=(6.4, 4.3),
)

# ============================================================================
# 8. UTI warranty — 3-year trend
#    Source: 01_data\00_derived\warranty_by_db_FY_canonical.csv
# ============================================================================
ct.trend_line(
    ["FY2024", "FY2025", "FY2026"],
    {"UTI warranty (EUR)": [128875, 292386, 260152]},
    cp("uti_warranty_trend.png"),
    title="UTI Warranty Expense, FY2024-FY2026 (EUR, fiscal basis)",
    value_fmt="{:,.0f}",
    figsize=(8.5, 4.3),
)

# ============================================================================
# 9. Order-type evolution — FY2025 -> FY2026 -> FY2027 Q1
#    Sources: Downloads\CY2024-2025.XLSX (FY2025 = Apr'24-Mar'25 filter, 100%
#    SaTy-matched), Downloads\FY2026_backup.csv (FY2026, footer/grand-total
#    row excluded, 100% matched), 01_data\00_derived\q1fy2027_export_with_saty.csv
#    (FY2027 Q1, only 70.4% matched — flagged, most recent quarter tags slower)
# ============================================================================
ct.trend_line(
    ["FY2025", "FY2026", "FY2027 (Q1)"],
    {
        "SOR": [63.7, 67.3, 74.2],
        "VOR": [12.8, 10.7, 15.4],
        "RUSH": [9.7, 7.4, 9.0],
    },
    cp("saty_evolution.png"),
    title="Order-Type Mix Evolution, FY2025 -> FY2027 Q1 (% of matched EUR)",
    value_fmt="{:,.1f}",
    figsize=(10.2, 4.6),
)
# Note: PRD (9.8% FY25 -> 11.5% FY26 -> 0.0% FY27 Q1) and the small residual
# (DR/CR/SVOR/RE/ZDR) are omitted from this chart — at <2pt gaps from each
# other their end-labels overlapped illegibly. Called out in the takeaways
# text instead, where the PRD swing is the more important fact anyway.

# ============================================================================
# 10. Average across all DBs — value-weighted network vs simple DB average
#    Source: Downloads\FY2026_backup.csv, per-distributor pivot (footer row
#    excluded), 25 distributors ex-MIDI/Turkey, DB name variants consolidated
# ============================================================================
ct.bar_chart(
    ["SOR", "VOR", "RUSH", "Other\n(incl. PRD + adj.)"],
    {
        "Network (value-weighted)": [68.1, 10.8, 6.5, 14.7],
        "Average of DBs (unweighted)": [58.6, 13.0, 17.7, 10.8],
    },
    cp("saty_db_average.png"),
    title="FY2026 Order-Type Mix: Network vs. Simple Average of 25 DBs (%)",
    ylabel="%",
    value_fmt="{:,.1f}",
    figsize=(10.2, 4.6),
)

# ============================================================================
# Assemble deck
# ============================================================================
prs = db.new_presentation()

db.build_cover(
    prs,
    title="ISZE Vehicle Parts & Accessories\nFY2027 Review",
    subtitle="FY26 Close  ·  FY27 Target  ·  Q1 FY27 Review — Draft, 6 July 2026",
)

db.build_two_col(
    prs,
    title="ITUK and IUK anchor the network; two SAP pulls disagree by EUR 830K",
    chart_path=cp("fy26_by_db.png"),
    eyebrow="FY2026 Sales Review",
    page_no=2,
    takeaways=[
        "Network FY2026 close (ex-MIDI/Turkey): EUR 33.91M, from the FY2026_backup.csv extract.",
        "Two independent raw SAP pulls for the same 12 months disagreed by EUR 830K (2.4%) at distributor level — neither is a finance-signed-off actual. This deck uses the extract you selected.",
        "ITUK (EUR 6.52M) and IUK (EUR 6.51M) are the two largest accounts, ~38% of network combined.",
        "UTI EUR 2.68M — third-largest Israel-linked account alongside UMI EUR 3.02M.",
    ],
)

s = db.build_content(prs, title="FY2027 target: +4.1% vs FY2026 close",
                      eyebrow="FY2027 Target", page_no=3)
from pptx.util import Inches
db.add_picture_fit(s, cp("fy27_target_network.png"), Inches(0.32), Inches(1.30), Inches(6.2), Inches(5.35))
db.add_picture_fit(s, cp("fy27_target_top5.png"), Inches(6.75), Inches(1.30), Inches(6.2), Inches(5.35))

db.build_two_col(
    prs,
    title="Q1 FY27 landed flat to BP, +13% vs last year",
    chart_path=cp("q1_fy27_monthly.png"),
    eyebrow="Q1 FY2027 Review (Apr-Jun 2026)",
    page_no=4,
    takeaways=[
        "Q1 total: Sales EUR 8,611K vs BP EUR 8,596K — 0% variance, +13% vs LY.",
        "May missed BP by -13%; April (+8%) and June (+5%) both ahead of plan.",
        "UTI +29% vs LY (first SPA order landed in June, +134% vs BP that month alone).",
        "ITUK -19% vs both LY and BP — the one account pulling the network average down.",
    ],
)

db.build_two_col(
    prs,
    title="Greece and Hungary are the fill-rate gates; UTI and IUK are on-track",
    chart_path=cp("fill_rate.png"),
    eyebrow="Fill Rate",
    page_no=5,
    takeaways=[
        "Network standard is >=95% (floor 92%). Below-floor DBs get an interim half-gap-closed target for FY26/27, full standard by FY27/28.",
        "Greece worst in network at 60% (GATE status, last reported figure); Hungary 69% is flagged as a stock-mix problem, not a shortage.",
        "UTI's more granular BI trend runs 76-86% (Jul'25-May'26, monthly) vs the 93% snapshot shown here — the two sources don't fully reconcile; treat as a range, not a point.",
        "ITUK dealer-level (TVS) first-pick rate: 94.51% in June vs 95% target.",
    ],
)

db.build_two_col(
    prs,
    title="Network GPS 51.1% (ex-MIDI); ITUK and UTI lowest by design",
    chart_path=cp("gps_by_db.png"),
    eyebrow="GPS Capture",
    page_no=6,
    takeaways=[
        "Network headline: 51.1% CY2025 ex-MIDI (FACTS.md re-base, 2026-07-03 entry supersedes an earlier 50.2% cut).",
        "Ireland tops the network at 151% (cross-segment effect, not a normal capture ceiling); IBX #2 at 97%.",
        "ITUK and UTI both sit at 31.8% — lowest in the network, by design (truck-heavy fleets where the GPS wallet definition is a known weak fit).",
    ],
)

db.build_two_col(
    prs,
    title="Filters are captured; clutch has no measured interval to target against",
    chart_path=cp("pms_uti_capture.png"),
    eyebrow="PMS Coverage",
    page_no=7,
    takeaways=[
        "Capture rate = units sold (genuine + BVP combined) / UIO-driven expected demand — not a genuine-only figure.",
        "Of what UTI does capture, filters sell almost entirely as BVP, not genuine (UTI overall mix is 88.9% genuine, but filters specifically run near-100% BVP) — capture volume and genuine mix answer different questions.",
        "Clutch service interval: no verified km/time figure exists in any ISZE source. ITUK's Apr'26 trip report explicitly excluded clutch from the phase-one campaign; the wear-factor weights behind the clutch bars above are labeled 'Assumption - pending IML', not measured data.",
    ],
)

s = db.build_content(prs, title="SOR carries the network; UTI runs tighter than average",
                      eyebrow="Urgent Orders — SOR vs RUSH/VOR", page_no=8)
db.add_picture_fit(s, cp("saty_network.png"), Inches(0.32), Inches(1.30), Inches(6.2), Inches(4.55))
db.add_picture_fit(s, cp("saty_uti.png"), Inches(6.75), Inches(1.30), Inches(6.2), Inches(4.55))
db.bullet_list(
    s,
    ["Network Q1: SOR 74% of matched value, RUSH+VOR 24%. Only 70.4% of total Q1 value (EUR 8.72M) carries a matched order-type tag — treat as directional.",
     "UTI Q1: SOR 88%, RUSH 7%, VOR 5% of matched — tighter SOR discipline than network average, and better tag coverage (82.2%)."],
    Inches(0.32), Inches(5.95), Inches(12.7), Inches(1.0), size=11.5,
)

db.build_two_col(
    prs,
    title="UTI warranty peaked FY2025, down 11% in FY2026",
    chart_path=cp("uti_warranty_trend.png"),
    eyebrow="Warranty",
    page_no=9,
    takeaways=[
        "UTI warranty: EUR 128,875 (FY2024) -> EUR 292,386 (FY2025) -> EUR 260,152 (FY2026), fiscal Apr-Mar basis, canonical file.",
        "A separate calendar-year cut (CY2025, CV-only) shows EUR 255,968 for roughly the same period - ~14% below the fiscal figure. Different year boundary, not a data error - the two should not be averaged.",
    ],
)

db.build_two_col(
    prs,
    title="SOR share is rising, but the newest quarter is also the least-tagged",
    chart_path=cp("saty_evolution.png"),
    eyebrow="Urgent Orders — Evolution by FY",
    page_no=10,
    takeaways=[
        "SOR share of matched value: 63.7% (FY25) -> 67.3% (FY26) -> 74.2% (FY27 Q1) — the network is trending more planned/stock-order-driven, not less.",
        "PRD (~10-11% of value in FY25/FY26) is effectively absent from Q1 FY27's tagged data (0%) — a real gap worth checking with SAP/BI, not yet a confirmed trend.",
        "Tag coverage itself degrades for the newest data: FY2025 and FY2026 are both 100% SaTy-matched; Q1 FY2027 is only 70.4% matched — part of the swing above may be a tagging-lag artifact in the newest quarter, not a behavior shift.",
        "RUSH+VOR (genuinely urgent) combined: 22.5% (FY25) -> 18.1% (FY26) -> 24.4% (FY27 Q1) — no clean downward trend either way.",
    ],
)

db.build_two_col(
    prs,
    title="Small DBs run far more urgent than the network average suggests",
    chart_path=cp("saty_db_average.png"),
    eyebrow="Urgent Orders — Average Across Distributors",
    page_no=11,
    takeaways=[
        "Network value-weighted mix (68% SOR) is driven by the big DBs (ITUK, IUK, UMI). The simple, unweighted average across 25 distributors looks different: 58.6% SOR, 17.7% RUSH.",
        "Worst RUSH-dependency (FY2026, % of DB's own value): Romania 96%, CBC-Trans 99%, Iceland 89% — essentially no planned stock ordering at all.",
        "Two accounts look structurally different, not typical distributor behavior: IMI Ops (100% non-SOR/VOR/RUSH, likely an internal/adjustment account) and Isuzu Motors Germany (91% VOR, tiny volume, a separate legal entity from ISD) — included in the average above but flagged, not verified as normal sell-in.",
    ],
)

db.build_closing(prs)

out_path = os.path.join(HERE, "ISZE_FY27_Review_FINAL_DRAFT.pptx")
prs.save(out_path)
print("Saved:", out_path)
