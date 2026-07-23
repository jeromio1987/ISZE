"""
Demo deck proving out the rebuilt template + chart methodology.
All numbers below are ILLUSTRATIVE placeholders - not real ISZE sales data -
built purely to demonstrate layout and chart quality.
"""
import os
import isze_chart_theme as ct
import isze_deck_builder as db

HERE = os.path.dirname(os.path.abspath(__file__))
CHART_DIR = os.path.join(HERE, "charts_out")
os.makedirs(CHART_DIR, exist_ok=True)

def cp(name):
    return os.path.join(CHART_DIR, name)

# ---- 1. generate charts (illustrative data only) --------------------------
ct.bar_chart(
    ["Q1", "Q2", "Q3", "Q4"],
    {"FY2026": [8.1, 8.6, 8.3, 9.0], "FY2025": [7.6, 7.9, 7.8, 8.2]},
    cp("vp_sales_by_quarter.png"),
    title="Vehicle Parts Sales by Quarter (illustrative, EUR M)",
    ylabel="EUR M",
)

ct.trend_line(
    ["FY22", "FY23", "FY24", "FY25", "FY26"],
    {"ISZE list price": [100, 104, 109, 118, 124], "Eucon benchmark avg": [100, 102, 105, 109, 113]},
    cp("price_vs_benchmark.png"),
    title="Price Index vs. Competitor Benchmark (illustrative, FY22=100)",
)

ct.waterfall(
    ["FY2025 basket", "FX", "BP (JPY)", "Volume mix", "FY2026 basket"],
    [100, -6, 9, 2, 105],
    cp("basket_bridge.png"),
    total_indices={0, 4},
    title="Basket Impact Bridge FY25 -> FY26 (illustrative, index)",
)

ct.donut_share(
    ["PMS", "Body", "Electrical", "Other"],
    [42, 28, 18, 12],
    cp("category_share.png"),
    center_label="Total (illustrative)", center_value="€8.4M",
    title="FY2026 Parts Revenue by Category",
)

ct.bar_chart(
    ["ITUK", "UMI", "UTI", "GA/CBC"],
    {"Capture rate %": [0.3, 41, 38, 22]},
    cp("capture_rate_by_distributor.png"),
    title="PMS Oil Filter Capture Rate by Distributor (illustrative, %)",
    ylabel="%",
    value_fmt="{:,.1f}",  # 0.3% must not round away to "0" - that's the whole story
)

# ---- 2. assemble deck ------------------------------------------------------
prs = db.new_presentation()

db.build_cover(
    prs,
    title="ISZE Vehicle Parts & Accessories\nQuarterly Review",
    subtitle="Illustrative demo deck  ·  Template v2  ·  " + "FY2026",
)

s = db.build_two_col(
    prs,
    title="Sales tracking ahead of prior year",
    chart_path=cp("vp_sales_by_quarter.png"),
    eyebrow="Vehicle Parts Sales",
    page_no=2,
    takeaways=[
        "FY2026 running ~8% above FY2025 in every quarter shown (illustrative).",
        "Q4 is the strongest quarter — consistent with seasonal pattern.",
        "Gap vs. prior year is widening slightly quarter over quarter.",
    ],
)

s = db.build_two_col(
    prs,
    title="Price index has outpaced the competitor benchmark since FY24",
    chart_path=cp("price_vs_benchmark.png"),
    eyebrow="Pricing",
    page_no=3,
    takeaways=[
        "ISZE list price index at 124 vs. Eucon benchmark at 113 (FY22=100).",
        "Gap opened mainly in FY25-FY26 — worth checking against the basket bridge.",
        "This is the shape of chart James Marsh's team will scrutinize line by line.",
    ],
)

s = db.build_full_chart(
    prs,
    title="Basket impact bridge: FX vs. BP vs. volume mix",
    chart_path=cp("basket_bridge.png"),
    eyebrow="ITUK Pricing Dispute",
    page_no=4,
)

s = db.build_two_col(
    prs,
    title="PMS remains the largest revenue category",
    chart_path=cp("category_share.png"),
    eyebrow="Category Mix",
    page_no=5,
    takeaways=[
        "PMS = 42% of illustrative FY2026 parts revenue.",
        "Body + Electrical combined = 46% — roughly matches PMS alone.",
        "'Other' at 12% is the long tail worth periodic review.",
    ],
)

s = db.build_full_chart(
    prs,
    title="Oil filter capture rate is critically low at ITUK",
    chart_path=cp("capture_rate_by_distributor.png"),
    eyebrow="PMS Coverage",
    page_no=6,
)

db.build_closing(prs)

out_path = os.path.join(HERE, "ISZE_Template_v2_Demo.pptx")
prs.save(out_path)
print("Saved:", out_path)
