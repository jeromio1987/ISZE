"""
UTI PMS Sales Leakage — 3-slide deck (ISZE Template v2).
Source: UTI_PMS_Sales_Leakage_Deep_Dive.xlsx (PMS_PN_Detail + category tabs).
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

import isze_chart_theme as ct
import isze_deck_builder as db

ct.FONT_FAMILY = "Calibri"

CHART_DIR = os.path.join(HERE, "charts_out", "uti_pms_leakage")
os.makedirs(CHART_DIR, exist_ok=True)


def cp(name):
    return os.path.join(CHART_DIR, name)


# Slide 1 — waterfall: net decline vs gross churn
ct.waterfall(
    ["FY2025\nPMS", "Gross PN\nleaks", "Offsetting\ngains", "FY2026\nPMS"],
    [426, -144, 83, 365],
    cp("waterfall_churn.png"),
    total_indices={0, 3},
    title="FY2025→FY2026: €61K net decline masks €144K gross leakage",
    value_fmt="{:+,.0f}",
)

# Slide 2 — top leaking PNs (kEUR)
ct.bar_chart(
    ["5876102320\nClutch Kit BVP", "5876101170\nOil Filter BVP",
     "1876100934\nFuel Filter BVP", "1876101132\nAir Filter BVP",
     "8982447940\nBrake Pad Gen."],
    {"Leak (k€)": [46.6, 42.7, 22.0, 12.4, 4.9]},
    cp("top_pn_leaks.png"),
    title="Top 5 leaking part numbers — top 4 = 86% of gross leakage",
    ylabel="Revenue leak (k€)",
    value_fmt="{:,.1f}",
    figsize=(10.2, 4.6),
)

# Slide 3 — category movers (kEUR FY25→FY26 change)
ct.bar_chart(
    ["Clutch Kit", "Oil Filter", "Brake Pad", "Filters total\n(net)", "Air Filter\n(net up)"],
    {"FY25→FY26 Δ (k€)": [-55.3, -18.2, -7.6, 1.6, 14.9]},
    cp("category_moves.png"),
    title="Category view: clutch & oil filter leak; filters net looks flat",
    ylabel="Revenue change (k€)",
    value_fmt="{:+,.1f}",
    figsize=(10.2, 4.6),
)

prs = db.new_presentation()

db.build_cover(
    prs,
    title="UTI PMS Sales Leakage\nFY2025 → FY2026",
    subtitle="PN-level deep dive  ·  PMS_PN_Detail tab  ·  July 2026",
    eyebrow="ISZE  ·  UTI  ·  PREVENTIVE MAINTENANCE SALES",
)

db.build_two_col(
    prs,
    title="€61K net decline hides €144K gross PN leakage",
    chart_path=cp("waterfall_churn.png"),
    eyebrow="Executive summary",
    page_no=2,
    takeaways=[
        "PMS revenue fell €426K → €365K (−€61K) in the latest tab.",
        "19 declining PNs leaked €144K before offsets; new/growing PNs recovered €83K.",
        "FY2026 modeled open gap: €428K — largest upside sits in brake pad & filters.",
    ],
)

db.build_two_col(
    prs,
    title="Clutch kit PN 5876102320 is the single largest true leak",
    chart_path=cp("top_pn_leaks.png"),
    eyebrow="Where sales are leaking",
    page_no=3,
    takeaways=[
        "5876102320 (Clutch Kit BVP): €90K → €44K; qty 670 → 325 — volume leak, ASP flat ~€135.",
        "5876101170 (Oil Filter BVP) dropped to €0 — validate supersession to 1876102890 (+€25K).",
        "8982447940 (Brake Pad Genuine): capture 33% → 27%; no BVP offset — straight leakage.",
    ],
)

db.build_two_col(
    prs,
    title="Filters look stable at category level — PN churn masks real losses",
    chart_path=cp("category_moves.png"),
    eyebrow="Priority focus",
    page_no=4,
    takeaways=[
        "P1 — Recover clutch kit 5876102320: largest true leak, volume-driven.",
        "P2 — Validate oil filter PN migration (5876101170 → 1876102890); capture fell 56% → 31%.",
        "P3 — Attack brake pad gap (€116K modeled); genuine down with no BVP substitute.",
    ],
)

db.build_closing(prs)

out_path = os.path.join(
    os.path.expanduser("~"),
    "Downloads",
    "UTI_PMS_Sales_Leakage_Deck.pptx",
)
prs.save(out_path)
print("Saved:", out_path)
