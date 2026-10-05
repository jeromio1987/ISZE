"""Slide 20 of the merged I Motors deck (Genuine & BVP) as a one-slide file, with a 2026 full-year projection.

Same content and style as slide 20 in build_merged_deck.py, plus:
  - 2026 projected   : Jan-Aug 2026 x 12/8, Genuine and BVP projected separately (straight line)
  - 2026 at dealer pace (billing chart only): billing if I Motors buys what dealers buy, i.e. the projected sales to dealer
  - seasonality check: Jan-Aug share of the full year in earlier calendar years, per stage
Data: sto_compare.py (ISZE billing, I Motors sales to dealer, IE40 PR00 price list of 10 Aug 2026, Genuine/BVP list).
"""
import pathlib, importlib.util
from pptx import Presentation
from pptx.util import Inches, Pt
from pptx.chart.data import CategoryChartData
from pptx.enum.chart import XL_CHART_TYPE, XL_LABEL_POSITION
from pptx.enum.dml import MSO_PATTERN
from pptx.enum.text import MSO_ANCHOR

HERE = pathlib.Path(__file__).resolve().parent
BPR = HERE.parent.parent
OUT = HERE.parent / "I_Motors_BPR_slide20_Genuine_BVP_projection_2026-09-24.pptx"

prs = Presentation()
ns = {"PRS": prs, "__file__": str(BPR / "charcoal_first7" / "_build" / "build_first7_charcoal.py"), "__name__": "slide20_child"}
exec(compile((BPR / "charcoal_first7" / "_build" / "build_first7_charcoal.py").read_text(encoding="utf-8"), ns["__file__"], "exec"), ns)
# keep only the helpers: drop the slides the helper build created
lst = prs.slides._sldIdLst
for e in list(lst):
    prs.part.drop_rel(e.rId); lst.remove(e)
g = ns
txt, rect, panel, base, chart = g["txt"], g["rect"], g["panel"], g["base"], g["chart"]
style_chart, labels, col_fill, rgb = g["style_chart"], g["labels"], g["col_fill"], g["rgb"]
RED, GREY, WHITE, MUTED, PANEL, ROW2 = g["RED"], g["GREY"], g["WHITE"], g["MUTED"], g["PANEL"], g["ROW2"]
g["PAGE"][0] = 19                      # page number 20, as in the deck

sp = importlib.util.spec_from_file_location("sto_compare", str(HERE / "sto_compare.py"))
STO = importlib.util.module_from_spec(sp); sp.loader.exec_module(STO)
T, COVER = STO.bvp_compare()
assert all(v > 0.97 for v in COVER.values()), COVER

def bv(stage, per, grp=None, lt=None):
    x = T[(T.stage == stage) & (T.period == per)]
    if grp: x = x[x.grp == grp]
    if lt: x = x[x.line_type == lt]
    return float(x.list_eur.sum()) / 1000
def bshare(stage, per, grp=None): t = bv(stage, per, grp); return bv(stage, per, grp, "bvp") / t if t else 0
YTD = "2026 Jan-Aug"
F = 12 / 8
proj = {st: {lt: bv(st, YTD, lt=lt) * F for lt in ("genuine", "bvp")} for st in ("billed", "sold")}
ptot = {st: sum(proj[st].values()) for st in proj}

# seasonality check: Jan-Aug share of the calendar year, per stage, on the same basis (list price, same families)
dim = STO.pd.read_csv(STO.DER / "bvp_pn_dimension.csv", dtype=str)
dim["pn"] = STO.norm(dim.part_number); dim = dim.drop_duplicates("pn")
dim["grp"] = dim.product_family.map({"PMS_Filters": "Filters", "Brakes": "Brakes", "Clutch_Driveline": "Clutch"})
dim = dim[dim.grp.notna()][["pn"]]
price = STO.price_list()
season = {}
for st, df in (("billed", STO.billing()), ("sold", STO.sellout())):
    d = df.merge(dim, on="pn"); d["eur"] = d.qty * d.pn.map(price)
    for y in (2023, 2024, 2025):
        x = d[d.date.dt.year == y]
        if len(x) and x.date.dt.month.nunique() == 12:
            season[(st, y)] = x[x.date.dt.month <= 8].eur.sum() / x.eur.sum()
bs = [v for (st, y), v in season.items() if st == "billed"]
ss = [v for (st, y), v in season.items() if st == "sold"]
b_lo, b_hi = bv("billed", YTD) / max(bs), bv("billed", YTD) / min(bs)
s_seas = bv("sold", YTD) / ss[0]

s = base("Genuine & BVP", "On one price basis, dealers buy a steady Genuine / BVP mix; ISZE billing swings with the 2025 brake stock",
         "Filters, brakes and clutch  |  calendar years  |  EUR K at the ISZE price list of 10 August 2026  |  BVP = Best Value Parts  |  2026 projected at the Jan–Aug pace",
         "Sources: ISZE billing to I Motors; I Motors sales to dealer (month rows); ISZE Genuine / BVP part-number list; units valued at the IE40 PR00 price list of 10 August 2026 (Price_file_PR00_IE40_20260810.xlsx).")

from pptx.enum.dml import MSO_LINE_DASH_STYLE
def hatch(ch, idx):   # projection: darker tint of the series colour with a dashed outline, so the labels stay readable
    for se, c, tint in zip(ch.plots[0].series, [RED, GREY], ["7A0A10", "5E5E5E"]):
        pt = se.points[idx]
        pt.format.fill.solid(); pt.format.fill.fore_color.rgb = rgb(tint)
        pt.format.line.color.rgb = rgb(c); pt.format.line.width = Pt(1.25); pt.format.line.dash_style = MSO_LINE_DASH_STYLE.DASH

def stack_chart(x, w, cats, gen, bvp, hatched):
    cd = CategoryChartData(); cd.categories = cats
    cd.add_series("Genuine", [round(v) for v in gen]); cd.add_series("BVP", [round(v) for v in bvp])
    ch = chart(s, XL_CHART_TYPE.COLUMN_STACKED, cd, x, 2.02, w, 2.7)
    style_chart(ch, '€#,##0"K"'); ch.plots[0].gap_width = 45; ch.value_axis.maximum_scale = 250; ch.value_axis.minimum_scale = 0
    ch.category_axis.tick_labels.font.size = Pt(7)
    for se, c in zip(ch.plots[0].series, [RED, GREY]):
        col_fill(se, c); labels(se, '#,##0', "1A1A1A" if c == GREY else WHITE, XL_LABEL_POSITION.CENTER, 7.5)
    for i in hatched:
        hatch(ch, i)
        for se in ch.plots[0].series:
            dl = se.points[i].data_label; dl.font.color.rgb = rgb(WHITE); dl.font.size = Pt(7.5); dl.font.bold = True
    return ch

BP = ["2023", "2024", "2025", YTD]
txt(s, 0.5, 1.8, 5.3, 0.22, "ISZE BILLING TO I MOTORS", 8, RED, True)
stack_chart(0.4, 5.3,
            ["2023", "2024", "2025", "2026 Jan–Aug", "2026 projected", "2026 at dealer pace"],
            [bv("billed", p, lt="genuine") for p in BP] + [proj["billed"]["genuine"], proj["sold"]["genuine"]],
            [bv("billed", p, lt="bvp") for p in BP] + [proj["billed"]["bvp"], proj["sold"]["bvp"]], [4, 5])
txt(s, 5.95, 1.8, 3.6, 0.22, "I MOTORS SALES TO DEALER", 8, RED, True)
stack_chart(5.85, 3.75, ["2025", "2026 Jan–Aug", "2026 projected"],
            [bv("sold", p, lt="genuine") for p in ("2025", YTD)] + [proj["sold"]["genuine"]],
            [bv("sold", p, lt="bvp") for p in ("2025", YTD)] + [proj["sold"]["bvp"]], [2])
txt(s, 0.4, 4.74, 9.2, 0.3, [
    f"Darker bars with a dashed outline = projection. 2026 projected = Jan–Aug × 12/8, Genuine and BVP separately. Seasonality check: Jan–Aug was {min(bs)*100:.0f}–{max(bs)*100:.0f}% of the year in billing (2023–2025), "
    f"giving €{b_lo:,.0f}K–€{b_hi:,.0f}K; {ss[0]*100:.0f}% in sales to dealer (2025), giving €{s_seas:,.0f}K. "
    "“At dealer pace” = billing if I Motors buys what its dealers buy from September on."], 6.8, MUTED)

hdr = ["Family", "Billed 2025", "To dealer 2025", "Billed 2026 Jan–Aug", "To dealer 2026 Jan–Aug"]
cx = [(0.4, 1.6), (2.0, 1.9), (3.9, 1.9), (5.8, 1.9), (7.7, 1.9)]
y = 5.12
for (x, w), h in zip(cx, hdr):
    rect(s, x, y, w, 0.3, "3A3A3A"); txt(s, x + 0.08, y, w - 0.12, 0.3, h, 7.5, MUTED, True, anchor=MSO_ANCHOR.MIDDLE)
for i, grp in enumerate(["Filters", "Brakes", "Clutch", None]):
    y += 0.32
    vals = [grp or "Total"] + [f"€{bv(st, p, grp):,.1f}K  ·  BVP {bshare(st, p, grp)*100:.0f}%" for st, p in
                               (("billed", "2025"), ("sold", "2025"), ("billed", YTD), ("sold", YTD))]
    for j, ((x, w), v) in enumerate(zip(cx, vals)):
        rect(s, x, y, w, 0.3, ROW2 if i % 2 == 0 else PANEL)
        txt(s, x + 0.08, y, w - 0.12, 0.3, v, 8, WHITE, j == 0 or grp is None, anchor=MSO_ANCHOR.MIDDLE)

b25, s25, b26, s26 = bv("billed", "2025"), bv("sold", "2025"), bv("billed", YTD), bv("sold", YTD)
panel(s, [
    f"At the current pace, ISZE billing in these families lands at about €{ptot['billed']:,.0f}K in 2026, against €{b25:,.0f}K in 2025. Sales to dealer land at about €{ptot['sold']:,.0f}K, above 2025 (€{s25:,.0f}K).",
    f"Where we should land: if I Motors buys at its dealers' pace from September, billing reaches about €{ptot['sold']:,.0f}K, €{ptot['sold']-ptot['billed']:,.0f}K more than at the current pace.",
    f"Brakes carry the stock swing: bought €{bv('billed','2025','Brakes'):,.0f}K against €{bv('sold','2025','Brakes'):,.0f}K sold in 2025, then €{bv('billed',YTD,'Brakes'):,.0f}K against €{bv('sold',YTD,'Brakes'):,.0f}K in 2026 to August.",
    f"Dealers take a steady BVP share ({bshare('sold','2025')*100:.0f}% in 2025, {bshare('sold',YTD)*100:.0f}% in 2026). The billed share moved from {bshare('billed','2025')*100:.0f}% to {bshare('billed',YTD)*100:.0f}% because of the Genuine brake stock bought in 2025.",
    "Euro values are units × the ISZE list price of 10 August 2026, not I Motors' purchase prices or its prices to dealers. Projections are a straight line, not a forecast."])

prs.save(OUT)
print("saved", OUT)
print("projection billed", {k: round(v, 1) for k, v in proj["billed"].items()}, round(ptot["billed"], 1),
      "| sold", {k: round(v, 1) for k, v in proj["sold"].items()}, round(ptot["sold"], 1))
print("season", {k: round(v, 3) for k, v in season.items()}, "billed range", round(b_lo, 1), round(b_hi, 1), "sold seasonal", round(s_seas, 1))
