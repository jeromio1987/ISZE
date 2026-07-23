"""
Demo deck proving out the rebuilt template + chart methodology.

IMPORTANT: every label, number, and category name below is GENERIC / MADE UP
("Category A", "Region 1", etc.) - deliberately NOT tied to any real ISZE
distributor, project, or figure. A v1 of this demo used real codes (ITUK,
GA/CBC) alongside made-up numbers, which read as if it were quoting real
(and in one case stale/wrong) internal figures. Keeping the demo fully
generic avoids that failure mode - this file exists to prove the chart/
layout methodology, not to say anything about actual ISZE data.
"""
import os
import isze_chart_theme as ct
import isze_deck_builder as db

HERE = os.path.dirname(os.path.abspath(__file__))
CHART_DIR = os.path.join(HERE, "charts_out")
os.makedirs(CHART_DIR, exist_ok=True)

def cp(name):
    return os.path.join(CHART_DIR, name)

# ---- 1. generate charts (fully generic placeholder data) ------------------
ct.bar_chart(
    ["Q1", "Q2", "Q3", "Q4"],
    {"Current year": [8.1, 8.6, 8.3, 9.0], "Prior year": [7.6, 7.9, 7.8, 8.2]},
    cp("sample_bar.png"),
    title="Sample bar chart — current vs. prior year (placeholder units)",
    ylabel="Units (placeholder)",
)

ct.trend_line(
    ["Yr1", "Yr2", "Yr3", "Yr4", "Yr5"],
    {"Series A": [100, 104, 109, 118, 124], "Series B": [100, 102, 105, 109, 113]},
    cp("sample_trend.png"),
    title="Sample trend chart — index vs. reference (Yr1=100)",
)

ct.waterfall(
    ["Start", "Driver 1", "Driver 2", "Driver 3", "End"],
    [100, -6, 9, 2, 105],
    cp("sample_waterfall.png"),
    total_indices={0, 4},
    title="Sample bridge chart — decomposing a variance (placeholder index)",
)

ct.donut_share(
    ["Category A", "Category B", "Category C", "Category D"],
    [42, 28, 18, 12],
    cp("sample_donut.png"),
    center_label="Total (placeholder)", center_value="X.XM",
    title="Sample share-of-total chart",
)

ct.bar_chart(
    ["Region 1", "Region 2", "Region 3"],
    {"Metric %": [35.1, 41.0, 38.0]},
    cp("sample_bar2.png"),
    title="Sample single-series bar (only regions with a valid denominator shown)",
    ylabel="%",
    value_fmt="{:,.1f}",
)

# ---- 2. assemble deck ------------------------------------------------------
prs = db.new_presentation()

db.build_cover(
    prs,
    title="ISZE Template v2\nChart & Layout Demo",
    subtitle="Fully generic placeholder data  ·  proves methodology only, not a real analysis",
)

s = db.build_two_col(
    prs,
    title="Grouped bar: current vs. prior period",
    chart_path=cp("sample_bar.png"),
    eyebrow="Layout: chart + takeaways",
    page_no=2,
    takeaways=[
        "Direct value labels on every bar instead of relying on the axis.",
        "Headline series in brand red, comparison series in charcoal.",
        "Legend only appears because there are 2 series here.",
    ],
)

s = db.build_two_col(
    prs,
    title="Trend line with end-of-line labels instead of a legend box",
    chart_path=cp("sample_trend.png"),
    eyebrow="Layout: chart + takeaways",
    page_no=3,
    takeaways=[
        "Labels sit at the end of each line - no legend needed.",
        "Headline series thicker + red; reference series thin + gray.",
        "Works well for any 'us vs. benchmark' comparison.",
    ],
)

s = db.build_full_chart(
    prs,
    title="Waterfall / bridge for decomposing a variance",
    chart_path=cp("sample_waterfall.png"),
    eyebrow="Layout: full-width chart",
    page_no=4,
)

s = db.build_two_col(
    prs,
    title="Share-of-total donut with direct labels",
    chart_path=cp("sample_donut.png"),
    eyebrow="Layout: chart + takeaways",
    page_no=5,
    takeaways=[
        "No legend - labels sit directly on each wedge.",
        "Center annotation carries the total.",
        "Ramp always starts red (largest / headline slice).",
    ],
)

s = db.build_full_chart(
    prs,
    title="Single-series bar - only use this metric where the denominator exists",
    chart_path=cp("sample_bar2.png"),
    eyebrow="Layout: full-width chart",
    page_no=6,
)

db.build_closing(prs)

out_path = os.path.join(HERE, "ISZE_Template_v2_Demo_GENERIC.pptx")
prs.save(out_path)
print("Saved:", out_path)
