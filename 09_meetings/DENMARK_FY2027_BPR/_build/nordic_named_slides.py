"""Denmark FY2027 review: the four slides redone from Jerome's to-do (named DBs, five Nordic markets together).

Reuses the style helpers of build_dk_bpr.py (same charcoal layout). Everything is computed from
sales_fact.parquet, aim_pn_classification_20260920.csv and gps_spu_by_distributor.csv.

Not built: fill rate by order type and individual fill rate per country (Power BI, only Denmark is on disk).
"""
import pathlib, re
import numpy as np, pandas as pd
from pptx import Presentation
from pptx.chart.data import CategoryChartData
from pptx.dml.color import RGBColor
from pptx.enum.chart import XL_CHART_TYPE, XL_LEGEND_POSITION, XL_LABEL_POSITION, XL_MARKER_STYLE
from pptx.enum.dml import MSO_LINE_DASH_STYLE
from pptx.enum.shapes import MSO_SHAPE, MSO_CONNECTOR
from pptx.enum.text import PP_ALIGN, MSO_ANCHOR
from pptx.util import Inches, Pt

HERE = pathlib.Path(__file__).resolve().parent
R = HERE.parents[2]
DER = R / "01_data" / "00_derived"
OUT = HERE.parent / "Isuzu_Danmark_FY2027_BPR_named_DBs_slides_2026-10-26.pptx"
LOGO = R / "09_meetings" / "IMotors_FY2027_BPR" / "charcoal_first7" / "_build" / "isuzu_logo.png"

# style helpers, taken verbatim from the main build so the slides match the deck
src = (HERE / "build_dk_bpr.py").read_text(encoding="utf-8")
a = src.index("BG, PANEL, BORDER, ROW2"); b = src.index("# ======================================================================= 1 cover")
exec(src[a:b])
PAGE[0] = 0

NORD = {"DENMARK": [2027.0, 2751.0], "FINLAND": [2679.0], "ICELAND": [1576.0], "NORWAY": [86.0], "SWEDEN": [2181.0]}
LABEL = {"DENMARK": "Denmark", "FINLAND": "Finland", "ICELAND": "Iceland", "NORWAY": "Norway", "SWEDEN": "Sweden"}
AA = [4, 5, 6, 7, 8]

sf = pd.read_parquet(DER / "sales_fact.parquet")
sf["fy"] = np.where(sf.billing_date.dt.month >= 4, sf.billing_date.dt.year + 1, sf.billing_date.dt.year)
parts = sf[~sf.part_number.eq("TRANSPORT")]

def urgent(df):
    c = df[df.saty.notna() & ~df.saty.eq("DR")]
    tot = c.net_sales_value.sum()
    return (c[c.saty.isin(["VOR", "RUSH", "SVOR"])].net_sales_value.sum() / tot) if tot else np.nan

spu = pd.read_csv(DER / "gps_spu_by_distributor.csv")
r25 = spu[(spu.year == 2025) & spu.gps_capture_vs_max.notna()].sort_values("gps_capture_vs_max", ascending=False).reset_index(drop=True)
nord = r25[r25.region == "Nordics"].reset_index(drop=True)
assert set(nord.distributor_code) == set(NORD), nord.distributor_code.tolist()
dk_rank = int(r25.index[r25.distributor_code == "DENMARK"][0]) + 1; n_mkts = len(r25)
dk_nrank = int(nord.index[nord.distributor_code == "DENMARK"][0]) + 1
gps25 = float(nord[nord.distributor_code == "DENMARK"].gps_capture_vs_max.iloc[0])

# ---------------------------------------------------------------- 1 Nordic ranking, named, no fleet numbers
nk = nord.iloc[::-1].reset_index(drop=True)
s = base("Genuine parts share  ·  Nordic ranking", f"In the Nordics Denmark is #{dk_nrank} of {len(nord)}; Finland and Iceland lead above 84%",
         "Genuine parts share, Nordic markets  |  calendar 2025  |  same method as the network ranking",
         "Source: gps_spu_by_distributor.csv (2025, full year), region Nordics. Share = ISZE billing ÷ (fleet × modelled parts spend per vehicle).")
cd = CategoryChartData(); cd.categories = [LABEL[c] for c in nk.distributor_code]
cd.add_series("Genuine parts share 2025", [round(float(v), 3) for v in nk.gps_capture_vs_max])
ch = chart(s, XL_CHART_TYPE.BAR_CLUSTERED, cd, 0.4, 1.8, 5.6, 4.3)
style_chart(ch, '0%', legend=False); ch.value_axis.minimum_scale = 0; ch.value_axis.maximum_scale = 1.0; ch.plots[0].gap_width = 45
col_fill(ch.plots[0].series[0], "5A5A5A"); labels(ch.plots[0].series[0], '0.0%', WHITE, size=9)
for i, c in enumerate(nk.distributor_code):
    if c == "DENMARK":
        pt = ch.plots[0].series[0].points[i]; pt.format.fill.solid(); pt.format.fill.fore_color.rgb = rgb(RED)
cols = [(6.2, 2.0), (8.3, 1.3)]
y = 1.85
for (x, w), h in zip(cols, ["Market", "Genuine parts share"]):
    rect(s, x, y, w, 0.38, RED); txt(s, x + 0.08, y, w - 0.14, 0.38, h, 8, WHITE, True, PP_ALIGN.LEFT if x == 6.2 else PP_ALIGN.CENTER, MSO_ANCHOR.MIDDLE)
y += 0.42
for i, r_ in nord.iterrows():
    fillc = ROW2 if i % 2 == 0 else PANEL; hl = r_.distributor_code == "DENMARK"
    for (x, w), v in zip(cols, [LABEL[r_.distributor_code], pct(float(r_.gps_capture_vs_max))]):
        rect(s, x, y, w, 0.44, fillc)
        txt(s, x + 0.08, y, w - 0.14, 0.44, v, 9, RED if hl else WHITE, hl, PP_ALIGN.LEFT if x == 6.2 else PP_ALIGN.CENTER, MSO_ANCHOR.MIDDLE)
    y += 0.47
gap_next = float(nord.gps_capture_vs_max.iloc[dk_nrank - 2]) - gps25
rect(s, 0.4, 6.25, 9.2, 0.75, PANEL, BORDER)
txt(s, 0.65, 6.25, 8.8, 0.75, f"Denmark {pct(gps25)}   |   next place up: {LABEL[nord.distributor_code.iloc[dk_nrank - 2]]} {pct(float(nord.gps_capture_vs_max.iloc[dk_nrank - 2]))} (+{gap_next * 100:.1f} points)", 10.5, WHITE, True, anchor=MSO_ANCHOR.MIDDLE)
panel(s, [
    f"Denmark is #{dk_nrank} of {len(nord)} Nordic markets, close behind {LABEL[nord.distributor_code.iloc[dk_nrank - 2]]} and well ahead of {LABEL[nord.distributor_code.iloc[-1]]}.",
    f"Moving up one place takes {gap_next * 100:.1f} points of share.",
    "Question: what would Isuzu Danmark need from ISZE (stock list, pricing on competitive parts, fill rate) to close that gap?"])

# ---------------------------------------------------------------- 2 order pattern, five Nordic markets
rows = []
for code, st in NORD.items():
    d = parts[parts.sold_to_sap.isin(st)]
    rows.append((LABEL[code], urgent(d[d.fy == 2025]), urgent(d[d.fy == 2026]),
                 urgent(d[(d.billing_date >= "2026-07-01") & (d.billing_date <= "2026-08-31")])))
net = parts[(parts.fy == 2026) & parts.sold_to_sap.notna()]
u_net = urgent(net)
nordic = parts[parts.sold_to_sap.isin(sum(NORD.values(), [])) & (parts.fy == 2026)]
u_nordic = urgent(nordic)
order = sorted(rows, key=lambda r: -r[2])
cats = [r[0] for r in order] + ["Nordic 5 together", "Network (all ISZE)"]
vals = [r[2] for r in order] + [u_nordic, u_net]
s = base("What your purchases tell us  ·  Order pattern", f"Urgent orders are {pct(order[0][2], 0)} of parts in {order[0][0]} and {pct(order[-1][2], 0)} in {order[-1][0]}; Denmark is at {pct(dict((r[0], r[2]) for r in rows)['Denmark'], 0)}",
         "Share of ISZE parts billing by order type  |  FY2026 (April 2025 to March 2026)  |  freight lines and lines without order type excluded",
         "Source: ISZE billing, order type (SaTy) per line. Urgent = VOR, RUSH and SVOR. Network = all ISZE customers, FY2026.")
cd = CategoryChartData(); cd.categories = cats
cd.add_series("Urgent orders", [round(v, 3) for v in vals]); cd.add_series("Stock and other orders", [round(1 - v, 3) for v in vals])
ch = chart(s, XL_CHART_TYPE.COLUMN_STACKED_100, cd, 0.4, 1.8, 9.2, 4.3)
style_chart(ch, '0%'); ch.plots[0].gap_width = 60
col_fill(ch.plots[0].series[0], RED); col_fill(ch.plots[0].series[1], "4A4A4A")
labels(ch.plots[0].series[0], '0%', WHITE, XL_LABEL_POSITION.CENTER, 10); labels(ch.plots[0].series[1], '0%', MUTED, XL_LABEL_POSITION.CENTER, 9)
for i in (len(order), len(order) + 1):
    pt = ch.plots[0].series[0].points[i]; pt.format.fill.solid(); pt.format.fill.fore_color.rgb = rgb(GREY)
for i, r_ in enumerate(order):
    if r_[0] == "Denmark":
        pt = ch.plots[0].series[0].points[i]; pt.format.fill.solid(); pt.format.fill.fore_color.rgb = rgb(AMBER)
rect(s, 0.4, 6.25, 9.2, 0.75, PANEL, BORDER)
txt(s, 0.65, 6.25, 8.8, 0.75, "Urgent share FY2025 → FY2026 → Jul–Aug 2026:   " + "   |   ".join(
    f"{r[0]} {pct(r[1], 0)} → {pct(r[2], 0)} → {pct(r[3], 0)}" for r in order), 8.5, WHITE, True, anchor=MSO_ANCHOR.MIDDLE)
panel(s, [
    f"Across the five Nordic markets together {pct(u_nordic, 0)} of parts value is bought as urgent orders, against {pct(u_net, 0)} across the network.",
    "An urgent order usually means a vehicle is waiting in a workshop. It costs more freight on both sides and is harder for ISZE to fill first time.",
    "Question: which parts does each Nordic distributor keep on its own shelf, and is there a list ISZE could stock against?"])

# ---------------------------------------------------------------- 3 categories, five Nordic markets together
cls = pd.read_csv(DER / "aim_pn_classification_20260920.csv", dtype=str, usecols=["part_number", "catalog_l1"])
pc = parts[parts.sold_to_sap.isin(sum(NORD.values(), [])) & parts.billing_date.dt.month.isin(AA) & parts.fy.isin([2026, 2027])].merge(cls, on="part_number", how="left")
pc["catalog_l1"] = pc.catalog_l1.fillna("Unclassified").replace({"Other / review": "Other"})
cat = pc.pivot_table(index="catalog_l1", columns="fy", values="net_sales_value", aggfunc="sum").fillna(0)
cat = cat[cat.max(axis=1) > 1000].sort_values(2027, ascending=False)
def cv(n, fy): return float(cat.loc[n, fy]) if n in cat.index else 0.0
def chg(n): return cv(n, 2027) / cv(n, 2026) - 1 if cv(n, 2026) else np.nan
tot26, tot27 = cat[2026].sum(), cat[2027].sum()
mover = max((c for c in cat.index if cat.loc[c, 2026] > 20000), key=lambda c: abs(chg(c)))
s = base("What your purchases tell us  ·  Categories", f"The five Nordic markets together: parts billing {sgn(tot27 / tot26 - 1, 0)} on last year; biggest move in {mover.lower()}",
         "ISZE parts billing to Denmark, Finland, Iceland, Norway and Sweden together by part group, € K  |  comparable April–August, FY2026 against FY2027",
         "Sources: ISZE billing, freight excluded; ISZE part classification (catalogue level 1). Competitive parts = parts also sold by the independent aftermarket.")
cd = CategoryChartData(); cd.categories = list(cat.index)
cd.add_series("Apr–Aug FY2026", [round(v / 1000, 1) for v in cat[2026]]); cd.add_series("Apr–Aug FY2027", [round(v / 1000, 1) for v in cat[2027]])
ch = chart(s, XL_CHART_TYPE.COLUMN_CLUSTERED, cd, 0.4, 1.8, 9.2, 4.3)
style_chart(ch, '€#,##0"K"'); ch.plots[0].gap_width = 70; ch.value_axis.minimum_scale = 0
for se, c in zip(ch.plots[0].series, [GREY, RED]): col_fill(se, c); labels(se, '#,##0.0', MUTED, size=7)
rect(s, 0.4, 6.25, 9.2, 0.75, PANEL, BORDER)
big = list(cat.index[:3])
txt(s, 0.65, 6.25, 8.8, 0.75, "   |   ".join(f"{c} {k(cv(c, 2026))} → {k(cv(c, 2027))}" for c in big) + f"   |   Total {k(tot26)} → {k(tot27)}", 10, WHITE, True, anchor=MSO_ANCHOR.MIDDLE)
panel(s, [
    f"Together the five markets bought {k(tot27)} of parts in April–August FY2027, against {k(tot26)} a year earlier ({sgn(tot27 / tot26 - 1, 1)}).",
    "The mix is dominated by the two large fleets (Norway, Sweden); Denmark, Finland and Iceland add the smaller part.",
    "Question: do the Nordic distributors see the same category pattern in their own workshops?"])

# ---------------------------------------------------------------- 4 network ranking, all markets named
rk = r25.iloc[::-1].reset_index(drop=True)
def mlabel(row):
    return row.country if row.distributor_code not in ("IUK", "ITUK", "UMI", "UTI") else f"{row.country} ({row.distributor_code})"
s = base("Genuine parts share  ·  Network ranking", f"Denmark ranks #{dk_rank} of {n_mkts} markets with {pct(gps25)}",
         "Genuine parts share by market  |  calendar 2025  |  ISZE billing ÷ fleet potential, same method for every market",
         "Source: gps_spu_by_distributor.csv (2025, full year): ISZE billing to each distributor, warranty included, ÷ fleet × modelled parts spend per vehicle. Markets without a fleet base are not ranked.")
cd = CategoryChartData(); cd.categories = [mlabel(r_) for _, r_ in rk.iterrows()]
cd.add_series("Genuine parts share 2025", [round(float(v), 3) for v in rk.gps_capture_vs_max])
ch = chart(s, XL_CHART_TYPE.BAR_CLUSTERED, cd, 0.4, 1.75, 9.2, 5.3)
style_chart(ch, '0%', legend=False); ch.value_axis.minimum_scale = 0; ch.value_axis.maximum_scale = 1.0; ch.plots[0].gap_width = 35
ch.category_axis.tick_labels.font.size = Pt(7.5)
col_fill(ch.plots[0].series[0], "5A5A5A"); labels(ch.plots[0].series[0], '0%', MUTED, size=7.5)
for i, r_ in rk.iterrows():
    if r_.distributor_code == "DENMARK":
        pt = ch.plots[0].series[0].points[i]; pt.format.fill.solid(); pt.format.fill.fore_color.rgb = rgb(RED)
med = float(r25.gps_capture_vs_max.median())
panel(s, [
    f"Denmark is #{dk_rank} of {n_mkts}: {pct(gps25)} against a network median of {pct(med)}.",
    f"The highest market is {mlabel(r25.iloc[0])} at {pct(float(r25.gps_capture_vs_max.iloc[0]))}.",
    "Agreeing the fleet base matters for the ranking: the share moves with the fleet count used."])

prs.save(OUT)
print("saved", OUT)
print({"order": order, "u_nordic": u_nordic, "u_net": u_net, "tot26": tot26, "tot27": tot27, "mover": mover})
print(cat.round(0))
