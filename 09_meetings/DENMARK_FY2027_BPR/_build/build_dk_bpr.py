"""Isuzu Danmark | FY2027 Business Performance Review (charcoal layout of the I Motors review, 24 Sep 2026).

Every figure is computed here from a named source; nothing is typed in except the Power BI fill-rate points
(read off the report on 1 Oct 2026, labels as shown) and the network urgent-share basis (computed below).

Sources
  ISZE billing          : 01_data/00_derived/sales_fact.parquet, sold-to 2027 + 2751 (Isuzu Danmark), through 31 Aug 2026
  FY2027 BP (4+8)       : 01_data/90_INBOX/_bp_fy27_4plus8_2026-10-01/Full Package Plan VP+ACC FY2027-28 BP 4+8 V3.xlsx,
                          sheet 'VP FY27-28', row '2027 - ISUZU DANMARK' (block 'BP 2027 (FY revised 4+8)' and 'BP 2028 (FY)')
  Sales to dealer, BO   : 01_data/11_planning/KPI Master File august 2026.xlsx, sheet 'Parts Handling'
  Registrations         : same file, sheet 'Vehicle Registration, RM, WE', 'No. of Vehicles Registered LCV'
  Fill rate             : Power BI 'SALES DATA VP NEW' > INDIVIDUAL FILL RATE, customer ISZ DENMARK, Sep 2025-Sep 2026
  Genuine parts share   : 01_data/00_derived/gps_spu_by_distributor.csv (CY2025, all markets) and gps_master.csv (FY billing)
  Fleet (UIO)           : 01_data/00_derived/uio_by_market_type_year.csv (ISUZU_UIO_Overview_2026 '1.UIO Overview')
  Part classification   : 01_data/00_derived/aim_pn_classification_20260920.csv (catalog_l1), bvp_pn_dimension.csv
"""
import pathlib
import numpy as np
import openpyxl
import pandas as pd
from pptx import Presentation
from pptx.chart.data import CategoryChartData
from pptx.dml.color import RGBColor
from pptx.enum.chart import XL_CHART_TYPE, XL_LEGEND_POSITION, XL_LABEL_POSITION, XL_MARKER_STYLE
from pptx.enum.dml import MSO_LINE_DASH_STYLE
from pptx.enum.shapes import MSO_SHAPE, MSO_CONNECTOR
from pptx.enum.text import PP_ALIGN, MSO_ANCHOR
from pptx.util import Inches, Pt

NAMED = False   # other markets in the ranking slides: False = anonymous (distributor-facing), True = country names

R = pathlib.Path(r"C:\Users\jerom\Desktop\claude\ISZE")
DER = R / "01_data" / "00_derived"
HERE = pathlib.Path(__file__).resolve().parent
OUT = HERE.parent / "Isuzu_Danmark_FY2027_Business_Performance_Review_2026-10-01.pptx"
LOGO = R / "09_meetings" / "IMotors_FY2027_BPR" / "charcoal_first7" / "_build" / "isuzu_logo.png"
BP_FILE = R / "01_data" / "90_INBOX" / "_bp_fy27_4plus8_2026-10-01" / "Full Package Plan VP+ACC FY2027-28 BP 4+8 V3.xlsx"
KPI_FILE = R / "01_data" / "11_planning" / "KPI Master File august 2026.xlsx"

# ======================================================================= data
sf = pd.read_parquet(DER / "sales_fact.parquet")
sf["fy"] = np.where(sf.billing_date.dt.month >= 4, sf.billing_date.dt.year + 1, sf.billing_date.dt.year)
sf["ym"] = sf.billing_date.dt.to_period("M")
dk = sf[sf.sold_to_sap.isin([2027.0, 2751.0])].copy()
LAST = dk.billing_date.max()                                   # 2026-08-31
AA = [4, 5, 6, 7, 8]                                            # comparable Apr-Aug
FR = dk.part_number.eq("TRANSPORT")                             # freight line, billed with the parts

bill_m = dk.groupby("ym").net_sales_value.sum()
def ym(y, m): return pd.Period(f"{y}-{m:02d}", "M")
FY_MONTHS = ["Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec", "Jan", "Feb", "Mar"]
def fy_series(fy):
    out = []
    for i in range(12):
        m = (i + 3) % 12 + 1; y = fy - 1 if m >= 4 else fy
        out.append(float(bill_m.get(ym(y, m), np.nan)))
    return out
b26, b27 = fy_series(2026), fy_series(2027)
ytd27 = sum(b27[:5]); ytd26 = sum(b26[:5]); fy26_tot = sum(b26)

# BP
ws = openpyxl.load_workbook(BP_FILE, read_only=True, data_only=True)["VP FY27-28"]
rows = list(ws.iter_rows(values_only=True))
def bp_row(start):
    for r in rows[start:start + 40]:
        if r[1] and "DANMARK" in str(r[1]).upper():
            return [float(v) for v in r[3:15]], float(r[17])
bp48, bp48_tot = bp_row(40)          # BP 2027 (FY revised 4+8): Apr-Jul actual, Aug-Mar plan
bp28, bp28_tot = bp_row(80)          # BP 2028 (FY)
bp_ytd = sum(bp48[:5]); bp_rest = sum(bp48[5:]); need_rest = bp48_tot - ytd27

# KPI master file
wb = openpyxl.load_workbook(KPI_FILE, read_only=True, data_only=True)
ph = list(wb["Parts Handling"].iter_rows(values_only=True))
HDR = ph[2]
def kpi_row(section_title):
    sec = None
    for r in ph:
        if r[0] and isinstance(r[0], str) and r[1] is None and r[2] is None: sec = r[0]
        if sec == section_title and r[0] == "Isuzu Danmark": return dict(zip(HDR[1:], r[1:]))
    raise KeyError(section_title)
SD = kpi_row("Parts Sales DB to DLR in €"); BO = kpi_row("Back Order Lines"); DAYS = ph[10]
assert ph[10][0] == "Isuzu Danmark"
sd_fy26_keys = ["Apr 25", "Mai 25", "Jun 25", "Jul 25", "Aug 25", "Sep 25", "Oct 25", "Nov 25", "Dec 25", "Jan 26", "Feb 26", "Mar 26"]
sd_fy27_keys = ["Apr 26", "May 26", "Jun 26", "Jul 26"]
sd26 = [float(SD[k]) for k in sd_fy26_keys]; sd27 = [float(SD[k]) for k in sd_fy27_keys]
sd_fy26 = sum(sd26); sd_aj26 = sum(sd26[:4]); sd_aj27 = sum(sd27)
sd_r12 = sd_fy26 - sd_aj26 + sd_aj27
bo_keys = ["Aug 25", "Sep 25", "Oct 25", "Nov 25", "Dec 25", "Jan 26", "Feb 26", "Mar 26", "Apr 26", "May 26", "Jun 26", "Jul 26"]
bo = [BO[k] for k in bo_keys]
days_status = sorted(set(str(v) for v in DAYS[13:29] if v is not None))  # FY26-FY27 cells for days in stock
reg_rows = list(wb["Vehicle Registration, RM, WE"].iter_rows(values_only=True))
REG = dict(zip(reg_rows[2][1:], next(r for r in reg_rows if r[0] == "Isuzu Danmark")[1:]))
reg25 = sum(int(REG[k]) for k in ["Jan 25", "Feb 25", "Mrz 25", "Apr 25", "Mai 25", "Jun 25", "Jul 25", "Aug 25", "Sep 25", "Oct 25", "Nov 25", "Dec 25"])
reg26 = sum(int(REG[k]) for k in ["Jan 26", "Feb 26", "Mar 26", "Apr 26", "May 26", "Jun 26", "Jul 26"] if isinstance(REG[k], (int, float)))

# Fill rate, Power BI (labels as shown on the report, rounded to whole %)
FR_M = ["Sep 25", "Oct 25", "Nov 25", "Dec 25", "Jan 26", "Feb 26", "Mar 26", "Apr 26", "May 26", "Jun 26", "Jul 26", "Aug 26", "Sep 26"]
FR_V = [0.97, 0.94, 0.86, 0.91, 0.94, 0.92, 0.87, 0.83, 0.84, 0.97, 0.96, 0.94, 0.88]
FR_TARGET = 0.93

# Order pattern (parts only: freight and uncoded lines excluded)
def urgent_share(df):
    c = df[df.saty.notna() & ~df.part_number.eq("TRANSPORT") & ~df.saty.eq("DR")]
    return c[c.saty.isin(["VOR", "RUSH", "SVOR"])].net_sales_value.sum() / c.net_sales_value.sum(), c.net_sales_value.sum()
u25, _ = urgent_share(dk[dk.fy == 2025]); u26, c26 = urgent_share(dk[dk.fy == 2026])
u_ja26, _ = urgent_share(dk[(dk.billing_date >= "2026-07-01") & (dk.billing_date <= "2026-08-31")])
u_ja25, _ = urgent_share(dk[(dk.billing_date >= "2025-07-01") & (dk.billing_date <= "2025-08-31")])
net26 = sf[(sf.fy == 2026) & sf.sold_to_sap.notna()]
u_net, _ = urgent_share(net26)
saty_cov27 = dk[(dk.fy == 2027) & ~FR & dk.saty.notna()].net_sales_value.sum() / dk[(dk.fy == 2027) & ~FR].net_sales_value.sum()

# Part-number pattern (FY2026, parts only)
p = dk[~FR]
p26 = p[p.fy == 2026]; p25 = p[p.fy == 2025]; p27 = p[p.fy == 2027]
g26 = p26.groupby("part_number").net_sales_value.sum().sort_values(ascending=False)
n_pn26 = len(g26); top20 = g26.head(20).sum() / g26.sum()
n80 = int((g26.cumsum() / g26.sum() < 0.8).sum() + 1)
months_per_pn = p26.groupby("part_number").ym.nunique()
once = int((months_per_pn == 1).sum()); six = int((months_per_pn >= 6).sum())
new27 = set(p27.part_number) - set(p[p.fy <= 2026].part_number)
new27_eur = p27[p27.part_number.isin(new27)].net_sales_value.sum()
lost = set(p25.part_number) - set(p26.part_number)
lost_eur = p25[p25.part_number.isin(lost)].net_sales_value.sum()
pn_aa = {fy: p[(p.fy == fy) & p.billing_date.dt.month.isin(AA)].part_number.nunique() for fy in (2025, 2026, 2027)}
top_pn = (p26.groupby(["part_number", "description"]).net_sales_value.sum().sort_values(ascending=False).head(8))

# Categories, comparable Apr-Aug
cls = pd.read_csv(DER / "aim_pn_classification_20260920.csv", dtype=str, usecols=["part_number", "catalog_l1"])
pc = p[p.billing_date.dt.month.isin(AA) & p.fy.isin([2026, 2027])].merge(cls, on="part_number", how="left")
pc["catalog_l1"] = pc.catalog_l1.fillna("Unclassified").replace({"Other / review": "Other"})
cat = pc.pivot_table(index="catalog_l1", columns="fy", values="net_sales_value", aggfunc="sum").fillna(0)
cat = cat[cat.max(axis=1) > 1000].sort_values(2027, ascending=False)
bvp = pd.read_csv(DER / "bvp_pn_dimension.csv", dtype=str, usecols=["part_number", "line_type"]).drop_duplicates("part_number")
pb = p26.merge(bvp, on="part_number", how="left")
bvp26 = pb[pb.line_type == "bvp"].net_sales_value.sum(); bvp_pns = pb[pb.line_type == "bvp"].part_number.nunique()

# Genuine parts share
gm = pd.read_csv(DER / "gps_master.csv", index_col=0)
spu = pd.read_csv(DER / "gps_spu_by_distributor.csv")
r25 = spu[(spu.year == 2025) & spu.gps_capture_vs_max.notna()].sort_values("gps_capture_vs_max", ascending=False).reset_index(drop=True)
dk25 = r25[r25.distributor_code == "DENMARK"].iloc[0]
WALLET = float(dk25.max_spend_eur); UIO25 = float(dk25.uio_units); RATE = WALLET / UIO25
dk_rank = int(r25.index[r25.distributor_code == "DENMARK"][0]) + 1; n_mkts = len(r25)
med = float(r25.gps_capture_vs_max.median())
net_w = float(r25.total_sales_eur.sum() / r25.max_spend_eur.sum())
nord = r25[r25.region == "Nordics"].reset_index(drop=True)
dk_nrank = int(nord.index[nord.distributor_code == "DENMARK"][0]) + 1
gfy = {fy: float(gm.loc["Danmark", f"net_FY{fy}"]) / WALLET for fy in (2024, 2025, 2026)}
gps25 = float(dk25.gps_capture_vs_max); gps25_xw = float(dk25.gps_capture_ex_warranty_vs_max)

# Fleet
u = pd.read_csv(DER / "uio_by_market_type_year.csv")
ud = u[u.distributor_code == "DENMARK"].groupby("year").agg(n=("uio_units", "sum"), basis=("basis", "first"))
uio = {y: float(ud.loc[y, "n"]) for y in range(2019, 2027)}
SCRAP = (0.01, 0.02)
chk = [uio[2024] + reg25 - uio[2024] * s for s in SCRAP]          # 2024 fleet + 2025 registrations - scrapping
CHK = round(sum(chk) / 2 / 5) * 5
gps25_chk = float(dk25.total_sales_eur) / (CHK * RATE); gfy26_chk = float(gm.loc["Danmark", "net_FY2026"]) / (CHK * RATE)

m16 = [pd.Period(f"2025-{m:02d}", "M") for m in range(4, 13)] + [pd.Period(f"2026-{m:02d}", "M") for m in range(1, 8)]
sd16 = sd26 + sd27
bp16 = [float(dk[(dk.ym == p_) & ~FR].net_sales_value.sum()) for p_ in m16]
ratio = sum(sd16) / sum(bp16)
r_above = r25.gps_capture_vs_max.iloc[dk_rank - 2]; r_below = r25.gps_capture_vs_max.iloc[dk_rank]

# ======================================================================= style (I Motors charcoal layout)
BG, PANEL, BORDER, ROW2 = "262626", "303030", "6E6E6E", "2B2B2B"
WHITE, MUTED, GRID = "F2F2F2", "BDBDBD", "4D4D4D"
RED, AMBER, GREY, GREEN, LGREEN = "E30613", "F5A000", "B7B7B7", "31A354", "55C271"
FONT = "Aptos"
def rgb(h): return RGBColor.from_string(h)
prs = Presentation(); prs.slide_width, prs.slide_height = Inches(13.333), Inches(7.5)
BLANK = prs.slide_layouts[6]

def txt(slide, x, y, w, h, text, size=10, color=WHITE, bold=False, align=PP_ALIGN.LEFT, anchor=MSO_ANCHOR.TOP):
    tb = slide.shapes.add_textbox(Inches(x), Inches(y), Inches(w), Inches(h))
    tf = tb.text_frame; tf.word_wrap = True; tf.vertical_anchor = anchor
    tf.margin_left = tf.margin_right = tf.margin_top = tf.margin_bottom = 0
    for i, line in enumerate(text if isinstance(text, list) else [text]):
        p_ = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
        p_.alignment = align
        r = p_.add_run(); r.text = line
        r.font.size = Pt(size); r.font.bold = bold; r.font.name = FONT; r.font.color.rgb = rgb(color)
    return tb

def rect(slide, x, y, w, h, fill, line=None, shape=MSO_SHAPE.RECTANGLE):
    s = slide.shapes.add_shape(shape, Inches(x), Inches(y), Inches(w), Inches(h))
    if fill: s.fill.solid(); s.fill.fore_color.rgb = rgb(fill)
    else: s.fill.background()
    if line: s.line.color.rgb = rgb(line); s.line.width = Pt(0.75)
    else: s.line.fill.background()
    s.shadow.inherit = False
    return s

def hline(slide, x, y, w, color, width=0.75):
    c = slide.shapes.add_connector(MSO_CONNECTOR.STRAIGHT, Inches(x), Inches(y), Inches(x + w), Inches(y))
    c.line.color.rgb = rgb(color); c.line.width = Pt(width)

PAGE = [1]
def base(section, title, sub, source):
    PAGE[0] += 1
    s = prs.slides.add_slide(BLANK)
    s.background.fill.solid(); s.background.fill.fore_color.rgb = rgb(BG)
    txt(s, 0.25, 0.10, 3.8, 0.18, "ISZE  ·  VEHICLE PARTS & ACCESSORIES", 6.6, WHITE, True)
    txt(s, 0.25, 0.43, 6.0, 0.22, section.upper(), 7.5, RED, True)
    txt(s, 0.25, 0.68, 9.45, 0.66, title, 20 if len(title) <= 60 else 16.5, WHITE, True)
    txt(s, 0.25, 1.42, 9.45, 0.24, sub, 8.5, MUTED)
    hline(s, 0.25, 7.18, 12.85, "575757")
    txt(s, 0.25, 7.24, 11.5, 0.16, source, 6.5, "8C8C8C")
    txt(s, 12.55, 7.24, 0.55, 0.16, str(PAGE[0]), 7, MUTED, align=PP_ALIGN.RIGHT)
    return s

def panel(slide, points, x=9.86, y=1.46, w=3.25, h=5.58):
    rect(slide, x, y, w, h, PANEL, BORDER)
    txt(slide, x + 0.28, y + 0.26, w - 0.5, 0.2, "OBSERVATIONS / QUESTIONS", 7.5, RED, True)
    yy = y + 0.72; step = (h - 0.95) / max(len(points), 1)
    for i, pnt in enumerate(points):
        rect(slide, x + 0.28, yy + 0.07, 0.09, 0.09, RED if i == 0 else AMBER, shape=MSO_SHAPE.OVAL)
        txt(slide, x + 0.52, yy, w - 0.8, step - 0.08, pnt, 8.6, WHITE)
        yy += step

def tile(slide, x, y, w, h, label, big, sub, color=WHITE, big_size=24):
    rect(slide, x, y, w, h, PANEL, BORDER)
    txt(slide, x + 0.18, y + 0.16, w - 0.3, 0.2, label, 7, RED, True)
    txt(slide, x + 0.18, y + 0.42, w - 0.3, 0.5, big, big_size, color, True)
    txt(slide, x + 0.18, y + 0.98, w - 0.3, h - 1.05, sub, 7.8, MUTED)

def style_chart(ch, num_fmt='#,##0', legend=True):
    ch.font.name = FONT; ch.font.size = Pt(8); ch.font.color.rgb = rgb(MUTED); ch.has_title = False
    if legend:
        ch.has_legend = True; ch.legend.position = XL_LEGEND_POSITION.BOTTOM; ch.legend.include_in_layout = False
        ch.legend.font.color.rgb = rgb(MUTED); ch.legend.font.size = Pt(8)
    else: ch.has_legend = False
    va = ch.value_axis; va.has_major_gridlines = True
    va.major_gridlines.format.line.color.rgb = rgb(GRID); va.major_gridlines.format.line.width = Pt(0.5)
    va.format.line.fill.background()
    va.tick_labels.font.color.rgb = rgb(MUTED); va.tick_labels.font.size = Pt(7.5)
    va.tick_labels.number_format = num_fmt; va.tick_labels.number_format_is_linked = False
    ca = ch.category_axis
    ca.format.line.color.rgb = rgb(GRID); ca.tick_labels.font.color.rgb = rgb(MUTED); ca.tick_labels.font.size = Pt(7.5)

def labels(series, fmt, color=WHITE, pos=XL_LABEL_POSITION.OUTSIDE_END, size=7.5):
    dl = series.data_labels; dl.show_value = True
    dl.number_format = fmt; dl.number_format_is_linked = False
    dl.font.size = Pt(size); dl.font.color.rgb = rgb(color); dl.font.bold = True; dl.position = pos

def col_fill(series, c):
    series.format.fill.solid(); series.format.fill.fore_color.rgb = rgb(c); series.format.line.fill.background()

def line_fmt(series, c, width=2.25, marker=True, dash=False):
    series.smooth = False
    series.format.line.color.rgb = rgb(c); series.format.line.width = Pt(width)
    if dash: series.format.line.dash_style = MSO_LINE_DASH_STYLE.DASH
    if marker:
        series.marker.style = XL_MARKER_STYLE.CIRCLE; series.marker.size = 6
        series.marker.format.fill.solid(); series.marker.format.fill.fore_color.rgb = rgb(c)
        series.marker.format.line.color.rgb = rgb(c)
    else: series.marker.style = XL_MARKER_STYLE.NONE

def chart(slide, kind, cd, x, y, w, h):
    return slide.shapes.add_chart(kind, Inches(x), Inches(y), Inches(w), Inches(h), cd).chart

def k(v): return f"€{v/1000:,.1f}K"
def pct(v, d=1): return f"{v*100:.{d}f}%"
def sgn(v, d=1): return f"{'+' if v >= 0 else ''}{v*100:.{d}f}%"

# ======================================================================= 1 cover
s = prs.slides.add_slide(BLANK)
s.background.fill.solid(); s.background.fill.fore_color.rgb = rgb(BG)
rect(s, 0, 0, 0.10, 7.5, RED)
txt(s, 0.45, 0.32, 5, 0.2, "ISZE  ·  VEHICLE PARTS & ACCESSORIES", 7, WHITE, True)
txt(s, 0.45, 2.05, 10.5, 1.3, ["Isuzu Danmark", "FY2027 Business Performance Review"], 30, WHITE, True)
txt(s, 0.45, 3.55, 10.5, 0.3, "FY27 plan  ·  Sales to dealer  ·  Fill rate  ·  Order pattern  ·  Fleet  ·  Genuine parts share ranking", 11, MUTED)
txt(s, 0.45, 4.05, 10.5, 0.3, "ISZE billing through August 2026, fill rate through September 2026  |  Review draft, 1 October 2026", 9, MUTED)
s.shapes.add_picture(str(LOGO), Inches(0.45), Inches(6.6), height=Inches(0.36))

# ======================================================================= 2 agenda (with the data rule from the network review)
s = base("Agenda", "Review structure", "Isuzu Danmark FY2027 business performance review", "Fiscal year = April to March (FY2027 = April 2026 to March 2027).")
items = [("01", "Where we stand", "FY2027 plan and pace, sales to dealer"),
         ("02", "Service", "Fill rate from ISZE, back orders and stock"),
         ("03", "What your purchases tell us", "Order pattern, part-number pattern, category movers"),
         ("04", "Fleet and genuine parts share", "Fleet size check, share trend, network and Nordic ranking"),
         ("05", "Next steps", "Part-level sales to dealer, priorities, action points")]
for i, (n, h, d) in enumerate(items):
    y = 1.95 + i * 0.92
    rect(s, 0.4, y, 0.62, 0.62, RED); txt(s, 0.4, y, 0.62, 0.62, n, 16, WHITE, True, PP_ALIGN.CENTER, MSO_ANCHOR.MIDDLE)
    txt(s, 1.2, y + 0.02, 6.5, 0.3, h, 14, WHITE, True); txt(s, 1.2, y + 0.36, 6.5, 0.25, d, 9.5, MUTED)
rect(s, 9.86, 1.95, 3.25, 4.4, PANEL, BORDER)
txt(s, 10.14, 2.2, 2.8, 0.2, "DATA RULE FOR THIS REVIEW", 7.5, RED, True)
txt(s, 10.14, 2.6, 2.8, 3.6, ["Every figure is read from a named ISZE file or report on its build date, listed in the footer of each page and in the method page.",
                               "", "Where a measure is modelled, the page says so. Where Isuzu Danmark does not report a KPI, it is shown as not reported, never as zero.",
                               "", "Fiscal and calendar years are labelled on every page and never mixed in one chart."], 8.6, WHITE)

# ======================================================================= 3 executive view
s = base("Executive view", "Billing is ahead of plan and dealer sales are growing faster; fill rate is the gap to close",
         "Periods differ by KPI: ISZE billing Apr–Aug 2026; sales to dealer Apr–Jul 2026; fill rate Sep 2026; genuine parts share calendar 2025.",
         "Sources: ISZE billing (sales_fact); FY2027 BP 4+8; KPI Master File Aug 2026; Power BI individual fill rate; ISZE genuine parts share and fleet files.")
tiles = [
    ("ISZE BILLING VS BP", k(ytd27), [f"Apr–Aug 2026 vs {k(bp_ytd)} BP", f"= {sgn(ytd27 / bp_ytd - 1)} vs plan"], LGREEN),
    ("YEAR ON YEAR", sgn(ytd27 / ytd26 - 1), [f"Apr–Aug 2026 vs {k(ytd26)}", "same months FY2026"], LGREEN),
    ("SALES TO DEALER", k(sd_aj27), [f"Apr–Jul 2026 vs {k(sd_aj26)}", f"= {sgn(sd_aj27 / sd_aj26 - 1)} year on year"], LGREEN),
    ("FILL RATE ISZE → DANMARK", pct(FR_V[-1], 0), [f"Sep 2026 vs {pct(FR_TARGET, 0)} target", f"range {pct(min(FR_V), 0)}–{pct(max(FR_V), 0)} over 13 months"], RED),
    ("URGENT ORDER SHARE", pct(u26, 0), [f"of parts billing FY2026", f"network: {pct(u_net, 0)}"], AMBER),
    ("BACK-ORDER LINES", f"{bo[-1]}", ["Jul 2026; days in stock", "not reported in the KPI file"], WHITE),
    ("GENUINE PARTS SHARE", pct(gps25), [f"calendar 2025, #{dk_rank} of {n_mkts} markets", f"#{dk_nrank} of {len(nord)} in the Nordics"], AMBER),
    ("FLEET (UIO)", f"{UIO25:,.0f}", ["2025 estimate in the ISZE fleet file", f"our check: about {CHK:,.0f}"], AMBER),
]
tw, th, gx, gy = 2.2, 1.6, 0.13, 0.15
for i, (lab, big, sub, c) in enumerate(tiles):
    tile(s, 0.4 + (i % 4) * (tw + gx), 1.8 + (i // 4) * (th + gy), tw, th, lab, big, sub, c)
rect(s, 0.4, 5.4, 4 * tw + 3 * gx, 1.1, PANEL, BORDER)
txt(s, 0.6, 5.58, 1.6, 0.25, "Management read", 9, RED, True)
txt(s, 2.25, 5.58, 7.0, 0.9, f"Isuzu Danmark is on plan: {k(ytd27)} billed against {k(bp_ytd)} in the BP, and dealer sales grow faster still. "
    f"What holds the business back is availability: about {pct(u26, 0)} of parts are bought as urgent orders, and ISZE fill rate dipped to {pct(min(FR_V), 0)} in April. "
    "Part-level sales-to-dealer data is the next step to plan stock instead of chasing orders.", 9.2, WHITE)
panel(s, [
    f"FY2027 BP is {k(bp48_tot)}; after five months {k(need_rest)} remains for September to March, against {k(bp_rest)} planned. The plan is reachable at the current pace.",
    f"Dealer sales are {k(sd_r12)} over the last 12 months. Since April 2025 Isuzu Danmark sold €{ratio:.1f} to dealers for every €1 of parts bought from ISZE; we would like to understand that difference.",
    f"Genuine parts share is {pct(gps25)} (calendar 2025), above the network median of {pct(med)}. On our fleet check it would be about {pct(gps25_chk)}.",
    "Question: can Isuzu Danmark share sales to dealer by part number and month, so stock can follow dealer demand?"])

# ======================================================================= 4 FY27 plan monthly
s = base("FY2027 plan", "April to August billing is on the BP; the plan for the rest of the year is flat",
         "ISZE billing to Isuzu Danmark, € per month  |  FY2027 actual to 31 August 2026 against the BP 4+8",
         "Sources: ISZE billing, sold-to 2027 and 2751, freight lines included as in the BP; Full Package Plan VP+ACC FY2027-28 BP 4+8 V3 (1 Oct 2026), row 2027 - ISUZU DANMARK.")
cd = CategoryChartData(); cd.categories = FY_MONTHS
cd.add_series("Actual FY2027", [round(v / 1000, 1) if not np.isnan(v) else None for v in b27[:5]] + [None] * 7)
cd.add_series("BP 4+8", [round(v / 1000, 1) for v in bp48])
ch = chart(s, XL_CHART_TYPE.COLUMN_CLUSTERED, cd, 0.4, 1.8, 9.2, 4.2)
style_chart(ch, '€#,##0"K"'); ch.plots[0].gap_width = 70; ch.plots[0].overlap = -5
ch.value_axis.minimum_scale = 0; ch.value_axis.maximum_scale = 25
for se, c in zip(ch.plots[0].series, [RED, GREY]): col_fill(se, c); labels(se, '#,##0.0', MUTED, size=7)
rect(s, 0.4, 6.15, 9.2, 0.8, PANEL, BORDER)
txt(s, 0.65, 6.4, 4.3, 0.3, f"Apr–Aug: {k(ytd27)} vs {k(bp_ytd)} BP ({sgn(ytd27 / bp_ytd - 1)})", 10, LGREEN, True)
txt(s, 5.05, 6.4, 4.4, 0.3, f"FY2027 BP {k(bp48_tot)}  ·  FY2028 BP {k(bp28_tot)}", 10, WHITE, True)
panel(s, [
    f"Billing is {k(ytd27)} after five months against {k(bp_ytd)} in the BP: {sgn(ytd27 / bp_ytd - 1)}. July was the strongest month at {k(b27[3])}.",
    f"The BP for September to March is {k(bp_rest)}, about {k(bp_rest / 7)} a month. Isuzu Danmark has billed {k(ytd27 / 5)} a month so far.",
    f"The BP adds {sgn(bp48_tot / fy26_tot - 1)} on FY2026 ({k(fy26_tot)}); FY2028 adds a further {sgn(bp28_tot / bp48_tot - 1)}.",
    "Question: is there anything in the second half (fleet deals, campaigns, stock decisions) that changes the monthly pace?"])

# ======================================================================= 5 FY27 pace
cum26 = np.cumsum(b26); cum27 = np.cumsum(b27[:5]); cumbp = np.cumsum(bp48)
s = base("FY2027 pace", f"April–August billing is {sgn(ytd27 / ytd26 - 1)} on last year; a straight-line full year gives {pct(ytd27 / 5 * 12 / bp48_tot, 0)} of the BP",
         "Cumulative ISZE billing to Isuzu Danmark, € K  |  FY2026 against FY2027 to 31 August 2026 and the BP 4+8",
         "Sources: ISZE billing, sold-to 2027 and 2751, freight included; FY2027 BP 4+8. Straight line = Apr–Aug billing ÷ 5 × 12.")
cd = CategoryChartData(); cd.categories = FY_MONTHS
cd.add_series("FY2026", [round(v / 1000, 1) for v in cum26])
cd.add_series("FY2027", [round(v / 1000, 1) for v in cum27] + [None] * 7)
cd.add_series("BP 4+8", [round(v / 1000, 1) for v in cumbp])
ch = chart(s, XL_CHART_TYPE.LINE_MARKERS, cd, 0.4, 1.8, 9.2, 3.75)
style_chart(ch, '€#,##0"K"'); ch.value_axis.minimum_scale = 0
a, b_, c_ = ch.plots[0].series
line_fmt(a, GREY, 2); line_fmt(b_, RED, 2.75); line_fmt(c_, AMBER, 1.75, marker=False, dash=True)
labels(b_, '#,##0.0', WHITE, XL_LABEL_POSITION.ABOVE, 7.5)
t3w = (9.2 - 2 * 0.2) / 3
for i, (lab, big, sub, c) in enumerate([
        ("APR–AUG FY2026", k(ytd26), ["Same five months last year"], WHITE),
        ("APR–AUG FY2027", k(ytd27), [f"{sgn(ytd27 / ytd26 - 1)} year on year"], LGREEN),
        ("STRAIGHT-LINE FY2027", k(ytd27 / 5 * 12), [f"{pct(ytd27 / 5 * 12 / bp48_tot, 1)} of the {k(bp48_tot)} BP"], LGREEN)]):
    tile(s, 0.4 + i * (t3w + 0.2), 5.62, t3w, 1.42, lab, big, sub, c, 22)
panel(s, [
    f"FY2027 runs above FY2026 in every cumulative month so far; the gap is {k(ytd27 - ytd26)} after August.",
    f"FY2026 ended at {k(fy26_tot)}. To reach the BP, Isuzu Danmark needs {k(need_rest)} in the last seven months, {k(need_rest / 7)} a month.",
    f"The straight line is a check, not a forecast: FY2026 had its strongest months in October and February ({k(b26[6])} and {k(b26[10])}).",
    "Question: which months does Isuzu Danmark expect to be strong this year, so ISZE can plan supply around them?"])

# ======================================================================= 6 sales to dealer
s = base("Sales to dealer", f"Dealer sales are up {sgn(sd_aj27 / sd_aj26 - 1, 0)} on April–July last year; the last 12 months reached {k(sd_r12)}",
         "Isuzu Danmark reported sales to dealer, € K per month  |  FY2026 (April 2025 to March 2026) and FY2027 to July 2026",
         "Source: KPI Master File august 2026.xlsx, Parts Handling – Parts Sales DB to DLR in €. August 2026 not yet reported.")
cd = CategoryChartData(); cd.categories = FY_MONTHS
cd.add_series("FY2026", [round(v / 1000, 1) for v in sd26])
cd.add_series("FY2027", [round(v / 1000, 1) for v in sd27] + [None] * 8)
ch = chart(s, XL_CHART_TYPE.COLUMN_CLUSTERED, cd, 0.4, 1.8, 9.2, 3.75)
style_chart(ch, '€#,##0"K"'); ch.plots[0].gap_width = 70; ch.value_axis.minimum_scale = 0
for se, c in zip(ch.plots[0].series, [GREY, RED]): col_fill(se, c); labels(se, '#,##0', MUTED, size=7)
for i, (lab, big, sub, c) in enumerate([
        ("APR–JUL FY2026", k(sd_aj26), ["Reported sales to dealer"], WHITE),
        ("APR–JUL FY2027", k(sd_aj27), [f"{sgn(sd_aj27 / sd_aj26 - 1)} vs comparable period"], LGREEN),
        ("FY2026 TOTAL", k(sd_fy26), [f"Largest month: {k(max(sd26))} (December 2025)"], WHITE)]):
    tile(s, 0.4 + i * (t3w + 0.2), 5.62, t3w, 1.42, lab, big, sub, c, 22)
panel(s, [
    f"Every FY2027 month so far is above the same month last year; July 2026 was {k(sd27[3])} against {k(sd26[3])}.",
    f"FY2026 had a strong winter: November and December 2025 were {k(sd26[7])} and {k(sd26[8])}, more than double the spring months.",
    "These are Isuzu Danmark's sales to its dealers, at its own prices. They are not comparable in level with ISZE billing (next page).",
    "Question: what drove the November–December 2025 peak: fleet orders, a campaign, accessories, or tyres and lubricants?"])

# ======================================================================= 7 sales to dealer vs ISZE billing
lab16 = [p_.strftime("%b %y") for p_ in m16]
s = base("Sales to dealer  ·  ISZE billing", "Dealer sales and ISZE billing do not move together; the winter peak did not reach our billing",
         "€ K per month  |  Isuzu Danmark sales to dealer against ISZE parts billing to Isuzu Danmark (freight excluded)  |  April 2025 to July 2026",
         "Sources: KPI Master File Aug 2026 (sales to dealer); ISZE billing, sold-to 2027 and 2751, freight line excluded. Different price levels: compare movements, not levels.")
cd = CategoryChartData(); cd.categories = lab16
cd.add_series("Sales to dealer", [round(v / 1000, 1) for v in sd16])
cd.add_series("ISZE parts billing", [round(v / 1000, 1) for v in bp16])
ch = chart(s, XL_CHART_TYPE.LINE_MARKERS, cd, 0.4, 1.8, 9.2, 4.25)
style_chart(ch, '€#,##0"K"'); ch.value_axis.minimum_scale = 0
line_fmt(ch.plots[0].series[0], RED, 2.5); line_fmt(ch.plots[0].series[1], GREY, 2.25)
labels(ch.plots[0].series[0], '#,##0', WHITE, XL_LABEL_POSITION.ABOVE, 7)
rect(s, 0.4, 6.2, 9.2, 0.8, PANEL, BORDER)
txt(s, 0.65, 6.2, 8.8, 0.8, f"April 2025 – July 2026:  sales to dealer {k(sum(sd16))}   |   ISZE parts billing {k(sum(bp16))}   |   €{ratio:.1f} of dealer sales per €1 bought from ISZE", 10.5, WHITE, True, anchor=MSO_ANCHOR.MIDDLE)
panel(s, [
    f"In November–December 2025 dealer sales rose to {k(sd16[7])} and {k(sd16[8])} while ISZE parts billing stayed near {k((bp16[7] + bp16[8]) / 2)} a month.",
    f"Over 16 months Isuzu Danmark sold €{ratio:.1f} to dealers for every €1 of parts it bought from ISZE. Distributor margin alone does not explain a gap of that size.",
    "Possible reasons: the dealer figure includes accessories, lubricants, tyres or parts from other suppliers, or stock built before April 2025 was sold.",
    "Question: what does the sales-to-dealer figure include? Part-level data would answer this directly."])

# ======================================================================= 8 fill rate
s = base("Fill rate  ·  ISZE → Isuzu Danmark", f"ISZE fill rate to Isuzu Danmark recovered to 94–97% in summer, but fell back to {pct(FR_V[-1], 0)} in September",
         f"ISZE supplying Isuzu Danmark  |  individual fill rate  |  Sep 2025 – Sep 2026  |  latest point {pct(FR_V[-1], 0)}",
         f"Source: Power BI, SALES DATA VP NEW – INDIVIDUAL FILL RATE, customer ISZ DENMARK, engines excluded (data updated 1 Oct 2026). Target {pct(FR_TARGET, 0)}, the current ISZE internal fill-rate target.")
cd = CategoryChartData(); cd.categories = FR_M
cd.add_series("Fill rate ISZE → Isuzu Danmark", FR_V); cd.add_series(f"Target {pct(FR_TARGET, 0)}", [FR_TARGET] * len(FR_V))
ch = chart(s, XL_CHART_TYPE.LINE_MARKERS, cd, 0.4, 1.8, 9.2, 4.3)
style_chart(ch, '0%'); ch.value_axis.minimum_scale = 0.80; ch.value_axis.maximum_scale = 1.0; ch.value_axis.major_unit = 0.05
a, t = ch.plots[0].series
line_fmt(a, RED, 2.5); line_fmt(t, AMBER, 1.75, marker=False, dash=True)
labels(a, '0%', WHITE, XL_LABEL_POSITION.ABOVE, 8)
below = sum(v < FR_TARGET for v in FR_V)
rect(s, 0.4, 6.25, 9.2, 0.75, PANEL, BORDER)
txt(s, 0.65, 6.25, 8.8, 0.75, f"ISZE → Isuzu Danmark   |   Latest: {pct(FR_V[-1], 0)}   |   High: {pct(max(FR_V), 0)}   |   Low: {pct(min(FR_V), 0)}   |   {below} of {len(FR_V)} months below {pct(FR_TARGET, 0)}", 11, RED, True, anchor=MSO_ANCHOR.MIDDLE)
panel(s, [
    f"This is our own supply to Isuzu Danmark. {len(FR_V) - below} of the {len(FR_V)} months are at or above the {pct(FR_TARGET, 0)} target; the low point is {pct(min(FR_V), 0)} in April 2026.",
    "March to May 2026 sat at 83–87%, four months in a row below target. That is the period to analyse first, part number by part number.",
    f"June to August recovered to 94–97%; September dropped to {pct(FR_V[-1], 0)}. ISZE will check which part numbers caused the drop.",
    "Question for both sides: which part numbers does Isuzu Danmark miss most often, so ISZE can stock them for Denmark?"])

# ======================================================================= 9 stock & availability
s = base("Stock & availability  ·  Isuzu Danmark", "Back orders stay low; stock cover is not reported yet",
         "Isuzu Danmark back-order lines  |  KPI Master File  |  Aug 2025 – Jul 2026", "Source: KPI Master File august 2026.xlsx, Parts Handling – Back Order Lines and Days of Parts in Stock. August 2026 not yet reported.")
txt(s, 0.5, 1.85, 4.3, 0.22, "BACK-ORDER LINES", 8, RED, True)
cd = CategoryChartData(); cd.categories = bo_keys; cd.add_series("Back-order lines", [int(v) for v in bo])
ch = chart(s, XL_CHART_TYPE.COLUMN_CLUSTERED, cd, 0.4, 2.1, 5.6, 3.8)
style_chart(ch, '#,##0', legend=False); ch.value_axis.minimum_scale = 0; ch.value_axis.maximum_scale = 15; ch.plots[0].gap_width = 50
ch.category_axis.tick_labels.font.size = Pt(6.5)
col_fill(ch.plots[0].series[0], GREY); labels(ch.plots[0].series[0], '#,##0', WHITE, size=7)
rect(s, 6.25, 2.1, 3.35, 3.8, PANEL, BORDER)
txt(s, 6.45, 2.3, 3.0, 0.22, "MONTHS OF STOCK (MOS)", 8, RED, True)
txt(s, 6.45, 2.7, 3.0, 0.6, "Not reported", 22, AMBER, True)
txt(s, 6.45, 3.45, 3.0, 2.3, ["'Days of Parts in Stock' is marked N/A (not tracked) for Isuzu Danmark in every month of the KPI file.",
                               "", "With MOS reported, we can see whether urgent orders come from low stock or from parts never stocked."], 8.5, WHITE)
rect(s, 0.4, 6.1, 9.2, 0.85, PANEL, BORDER)
txt(s, 0.65, 6.1, 8.8, 0.85, f"Back-order lines:  {min(bo)}–{max(bo)} per month over 12 months   |   latest {bo[-1]} (July 2026)   |   MOS: not reported", 10.5, WHITE, True, anchor=MSO_ANCHOR.MIDDLE)
panel(s, [
    f"Back orders are small: between {min(bo)} and {max(bo)} lines a month, with peaks of 10 in October and November 2025.",
    "Low back orders and a high urgent-order share can go together: urgent orders are often placed exactly to avoid a back order.",
    "Without days in stock, we cannot tell how much buffer Isuzu Danmark holds on its fast movers.",
    "Request: report days of parts in stock monthly in the KPI file from October 2026."])

# ======================================================================= 10 order pattern
s = base("What your purchases tell us  ·  Order pattern", f"About {pct(u26, 0)} of parts are bought as urgent orders, against {pct(u_net, 0)} across the network",
         "Share of ISZE parts billing by order type  |  fiscal years  |  freight lines and lines without order type excluded",
         f"Source: ISZE billing, order type (SaTy) per line. Urgent = VOR, RUSH and SVOR. Apr–Jun 2026 billing has no order type in the SAP export, so FY2027 uses Jul–Aug only. Network = all ISZE customers, FY2026.")
cats = ["FY2025", "FY2026", "Jul–Aug 2025", "Jul–Aug 2026", "Network FY2026"]
vals = [u25, u26, u_ja25, u_ja26, u_net]
cd = CategoryChartData(); cd.categories = cats
cd.add_series("Urgent orders", [round(v, 3) for v in vals]); cd.add_series("Stock and other orders", [round(1 - v, 3) for v in vals])
ch = chart(s, XL_CHART_TYPE.COLUMN_STACKED_100, cd, 0.4, 1.8, 9.2, 4.3)
style_chart(ch, '0%'); ch.plots[0].gap_width = 60
col_fill(ch.plots[0].series[0], RED); col_fill(ch.plots[0].series[1], "4A4A4A")
labels(ch.plots[0].series[0], '0%', WHITE, XL_LABEL_POSITION.CENTER, 10); labels(ch.plots[0].series[1], '0%', MUTED, XL_LABEL_POSITION.CENTER, 9)
pt = ch.plots[0].series[0].points[4]; pt.format.fill.solid(); pt.format.fill.fore_color.rgb = rgb(GREY)
rect(s, 0.4, 6.25, 9.2, 0.75, PANEL, BORDER)
txt(s, 0.65, 6.25, 8.8, 0.75, f"Urgent share:  FY2025 {pct(u25, 0)}   |   FY2026 {pct(u26, 0)}   |   Jul–Aug 2026 {pct(u_ja26, 0)}   |   network {pct(u_net, 0)}", 11, WHITE, True, anchor=MSO_ANCHOR.MIDDLE)
panel(s, [
    f"Roughly two in every five euros of parts reach Isuzu Danmark as urgent orders, about {u26 / u_net:.1f} times the network share.",
    "An urgent order usually means a vehicle is waiting in a workshop. It costs more freight on both sides and is harder for ISZE to fill first time.",
    "A higher stock-order share on fast movers would lift fill rate and lower freight cost per part.",
    "Question: which parts does Isuzu Danmark keep on its own shelf today, and is there a list we could stock against together?"])

# ======================================================================= 11 part-number pattern
s = base("What your purchases tell us  ·  Part numbers", f"Two in three part numbers were bought in one month only; {n80} make 80% of the value",
         "ISZE parts billing to Isuzu Danmark  |  FY2026 (April 2025 to March 2026), freight excluded  |  new part numbers in FY2027 to August",
         "Source: ISZE billing, sold-to 2027 and 2751, by part number and billing month.")
t4w = (9.2 - 3 * 0.17) / 4
for i, (lab, big, sub, c) in enumerate([
        ("PART NUMBERS FY2026", f"{n_pn26}", [f"Top 20 = {pct(top20, 0)} of value", f"{n80} part numbers = 80%"], WHITE),
        ("BOUGHT IN ONE MONTH ONLY", f"{once}", [f"{pct(once / n_pn26, 0)} of all part numbers", f"only {six} bought in 6+ months"], AMBER),
        ("NEW IN FY2027", f"{len(new27)}", ["never bought before April 2026", f"{k(new27_eur)} so far"], WHITE),
        ("NOT REPEATED", f"{len(lost)}", ["bought in FY2025, not in FY2026", f"{k(lost_eur)} in FY2025"], AMBER)]):
    tile(s, 0.4 + i * (t4w + 0.17), 1.8, t4w, 1.6, lab, big, sub, c, 24)
txt(s, 0.4, 3.62, 9.2, 0.22, "LARGEST PART NUMBERS, FY2026", 8, RED, True)
y = 3.92
for i, ((pn, desc), v) in enumerate(top_pn.items()):
    fillc = ROW2 if i % 2 == 0 else PANEL
    rect(s, 0.4, y, 9.2, 0.33, fillc)
    txt(s, 0.55, y, 1.6, 0.33, pn, 8.5, MUTED, anchor=MSO_ANCHOR.MIDDLE)
    txt(s, 2.2, y, 5.2, 0.33, str(desc).title(), 8.5, WHITE, anchor=MSO_ANCHOR.MIDDLE)
    txt(s, 7.6, y, 1.8, 0.33, f"€{v:,.0f}", 8.5, WHITE, True, PP_ALIGN.RIGHT, MSO_ANCHOR.MIDDLE)
    y += 0.36
panel(s, [
    f"Isuzu Danmark buys a long tail: {pct(once / n_pn26, 0)} of part numbers appear in one month only. That is the pattern of ordering per job, not of restocking.",
    f"Only {six} part numbers were bought in six or more months. These are the natural candidates for a stock list.",
    f"The range is widening: {pn_aa[2027]} part numbers in April–August 2026 against {pn_aa[2026]} a year earlier, {len(new27)} of them never bought before.",
    f"Best Value Parts are {k(bvp26)} of FY2026 billing, almost all one front brake-pad kit. Question: is there interest in BVP for older D-Max vehicles?"])

# ======================================================================= 12 category movers
s = base("What your purchases tell us  ·  Categories", "Repair parts doubled on last year; accident parts are lower",
         "ISZE parts billing to Isuzu Danmark by part group, € K  |  comparable April–August, FY2026 against FY2027",
         "Sources: ISZE billing, freight excluded; ISZE part classification (catalogue level 1). Competitive parts = parts also sold by the independent aftermarket.")
cd = CategoryChartData(); cd.categories = list(cat.index)
cd.add_series("Apr–Aug FY2026", [round(v / 1000, 1) for v in cat[2026]]); cd.add_series("Apr–Aug FY2027", [round(v / 1000, 1) for v in cat[2027]])
ch = chart(s, XL_CHART_TYPE.COLUMN_CLUSTERED, cd, 0.4, 1.8, 9.2, 4.3)
style_chart(ch, '€#,##0"K"'); ch.plots[0].gap_width = 70; ch.value_axis.minimum_scale = 0
for se, c in zip(ch.plots[0].series, [GREY, RED]): col_fill(se, c); labels(se, '#,##0.0', MUTED, size=7)
def cv(name, fy): return float(cat.loc[name, fy]) if name in cat.index else 0.0
rect(s, 0.4, 6.25, 9.2, 0.75, PANEL, BORDER)
txt(s, 0.65, 6.25, 8.8, 0.75, f"Repair parts {k(cv('Repair parts', 2026))} → {k(cv('Repair parts', 2027))}   |   Accident parts {k(cv('Accident parts', 2026))} → {k(cv('Accident parts', 2027))}   |   Competitive parts {k(cv('Competitive parts', 2026))} → {k(cv('Competitive parts', 2027))}", 10, WHITE, True, anchor=MSO_ANCHOR.MIDDLE)
panel(s, [
    f"Repair parts grew from {k(cv('Repair parts', 2026))} to {k(cv('Repair parts', 2027))}, consistent with a fleet that is getting older.",
    f"Competitive parts (filters, brakes and other parts the aftermarket also sells) are the largest group at {k(cv('Competitive parts', 2027))}, about flat on last year.",
    f"Accident parts fell from {k(cv('Accident parts', 2026))} to {k(cv('Accident parts', 2027))}; that group follows claims and is hard to plan.",
    "Question: as the fleet ages, does Isuzu Danmark see more independent workshops servicing D-Max, and where do they buy?"])

# ======================================================================= 13 fleet (UIO)
s = base("Fleet", f"We count {UIO25:,.0f} vehicles in 2025; your registrations suggest it is closer to {CHK:,.0f}",
         "Isuzu vehicles in operation in Denmark, calendar years  |  2025 estimate and 2026 forecast as held in the ISZE fleet file",
         "Sources: ISUZU_UIO_Overview_2026 (uio_by_market_type_year); registrations: KPI Master File, Vehicle Registration – No. of Vehicles Registered LCV, Jan–Dec 2025.")
yrs = list(range(2019, 2027))
cd = CategoryChartData(); cd.categories = [str(y) + (" est." if y == 2025 else " fcst." if y == 2026 else "") for y in yrs]
cd.add_series("Vehicles in operation (ISZE fleet file)", [uio[y] for y in yrs])
ch = chart(s, XL_CHART_TYPE.COLUMN_CLUSTERED, cd, 0.4, 1.8, 5.4, 4.25)
style_chart(ch, '#,##0', legend=False); ch.plots[0].gap_width = 55; ch.value_axis.minimum_scale = 0; ch.value_axis.maximum_scale = 1100
col_fill(ch.plots[0].series[0], GREY); labels(ch.plots[0].series[0], '#,##0', WHITE, size=7.5)
for i in (6, 7):
    pt = ch.plots[0].series[0].points[i]; pt.format.fill.solid(); pt.format.fill.fore_color.rgb = rgb(AMBER)
rect(s, 6.0, 1.8, 3.6, 4.25, PANEL, BORDER)
txt(s, 6.2, 1.98, 3.2, 0.22, "OUR CHECK FOR END 2025", 8, RED, True)
rows_ = [("Fleet end 2024 (ISZE file)", f"{uio[2024]:,.0f}"), ("+ registrations 2025 (your KPI return)", f"+{reg25}"),
         ("– scrapping at 1–2% a year", f"–{uio[2024] * SCRAP[0]:.0f} to –{uio[2024] * SCRAP[1]:.0f}"), ("= our check", f"≈ {CHK:,.0f}"),
         ("ISZE fleet file, 2025 estimate", f"{UIO25:,.0f}")]
yy = 2.38
for i, (a_, b2) in enumerate(rows_):
    bold = i == 3
    txt(s, 6.2, yy, 2.35, 0.42, a_, 8.5, WHITE if bold else MUTED, bold, anchor=MSO_ANCHOR.MIDDLE)
    txt(s, 8.5, yy, 0.95, 0.42, b2, 10 if bold else 9, AMBER if bold else WHITE, True, PP_ALIGN.RIGHT, MSO_ANCHOR.MIDDLE)
    if i == 2: hline(s, 6.2, yy + 0.46, 3.2, BORDER)
    yy += 0.5
txt(s, 6.2, yy + 0.08, 3.25, 0.9, f"The fleet is young: almost every vehicle was registered from 2014 onwards, so scrapping should stay low. 2026 so far: {reg26} registrations (January–July).", 7.8, MUTED)
rect(s, 0.4, 6.2, 9.2, 0.8, PANEL, BORDER)
txt(s, 0.65, 6.2, 8.8, 0.8, f"Effect on genuine parts share (calendar 2025):  {pct(gps25)} on {UIO25:,.0f} vehicles   →   about {pct(gps25_chk)} on {CHK:,.0f} vehicles", 10.5, WHITE, True, anchor=MSO_ANCHOR.MIDDLE)
panel(s, [
    f"The ISZE fleet file grows by only {uio[2025] - uio[2024]:.0f} vehicles from 2024 to 2025, while Isuzu Danmark registered {reg25} new vehicles in 2025. That would mean about {reg25 - (uio[2025] - uio[2024]):.0f} vehicles scrapped in one year, which a fleet this young does not do.",
    f"Our check gives about {CHK:,.0f} vehicles at the end of 2025, close to the {uio[2026]:,.0f} the file forecasts for 2026. The 2025 estimate looks one year behind.",
    "A larger fleet lowers the genuine parts share: the same purchases spread over more vehicles. We prefer an honest base to a flattering one.",
    "Request: Isuzu Danmark's own count of Isuzu vehicles on the road (registrations by year since 2014), so both sides use one fleet base."])

# ======================================================================= 14 genuine parts share trend
s = base("Genuine parts share", f"Genuine parts share rose to {pct(gfy[2026])} in FY2026, up from {pct(gfy[2025])} in FY2025",
         f"ISZE billing to Isuzu Danmark (parts, warranty included) ÷ fleet potential  |  fiscal years on a fixed 2025 fleet potential of {k(WALLET)} ({UIO25:,.0f} vehicles × €{RATE:,.0f})",
         "Sources: ISZE genuine parts share files (gps_master FY billing; gps_spu_by_distributor 2025 fleet potential). Fleet potential = modelled annual parts spend of the fleet, not measured competitor spend.")
cats = ["FY2024", "FY2025", "FY2026", "FY2026 on our fleet check"]
vals = [gfy[2024], gfy[2025], gfy[2026], gfy26_chk]
cd = CategoryChartData(); cd.categories = cats; cd.add_series("Genuine parts share", [round(v, 3) for v in vals])
ch = chart(s, XL_CHART_TYPE.COLUMN_CLUSTERED, cd, 0.4, 1.8, 9.2, 4.3)
style_chart(ch, '0%', legend=False); ch.value_axis.minimum_scale = 0; ch.value_axis.maximum_scale = 1.0; ch.plots[0].gap_width = 70
col_fill(ch.plots[0].series[0], RED); labels(ch.plots[0].series[0], '0.0%', WHITE, size=10)
pt = ch.plots[0].series[0].points[3]; pt.format.fill.solid(); pt.format.fill.fore_color.rgb = rgb(AMBER)
rect(s, 0.4, 6.25, 9.2, 0.75, PANEL, BORDER)
txt(s, 0.65, 6.25, 8.8, 0.75, f"Calendar 2025, used for the ranking on the next pages:  {pct(gps25)}   |   warranty parts excluded: {pct(gps25_xw)}", 10.5, WHITE, True, anchor=MSO_ANCHOR.MIDDLE)
panel(s, [
    f"FY2026 is the best year of the three: {pct(gfy[2026])} of the fleet's modelled parts spend was bought from ISZE.",
    f"The FY2025 dip to {pct(gfy[2025])} followed a strong FY2024; FY2027 billing to August is {sgn(ytd27 / ytd26 - 1)} on last year, so the share is still rising.",
    f"On our fleet check of {CHK:,.0f} vehicles the FY2026 share would be about {pct(gfy26_chk)}. The trend stays the same.",
    "Question: which families does Isuzu Danmark think it loses most to the aftermarket: filters, brakes or body parts?"])

# ======================================================================= 15 ranking, all markets
def mlabel(row, i):
    if row.distributor_code == "DENMARK": return "Denmark"
    if NAMED: return str(row.country) if row.distributor_code not in ("IUK", "ITUK", "UMI", "UTI") else f"{row.country} ({row.distributor_code})"
    return f"Market {i + 1}"
rk = r25.iloc[::-1].reset_index(drop=True)          # bar charts draw bottom-up
names = [mlabel(r_, n_mkts - 1 - i) for i, r_ in rk.iterrows()]
s = base("Genuine parts share  ·  Network ranking", f"Denmark ranks #{dk_rank} of {n_mkts} markets with {pct(gps25)}, above the network median",
         f"Genuine parts share by market  |  calendar 2025  |  ISZE billing ÷ fleet potential, same method for every market  |  {'markets named' if NAMED else 'other markets not named'}",
         "Source: gps_spu_by_distributor.csv (2025, full year): ISZE billing to each distributor, warranty included, ÷ fleet × modelled parts spend per vehicle. Markets without a fleet base are not ranked.")
cd = CategoryChartData(); cd.categories = names; cd.add_series("Genuine parts share 2025", [round(float(v), 3) for v in rk.gps_capture_vs_max])
ch = chart(s, XL_CHART_TYPE.BAR_CLUSTERED, cd, 0.4, 1.75, 9.2, 5.3)
style_chart(ch, '0%', legend=False); ch.value_axis.minimum_scale = 0; ch.value_axis.maximum_scale = 1.0; ch.plots[0].gap_width = 35
ch.category_axis.tick_labels.font.size = Pt(7.5)
col_fill(ch.plots[0].series[0], "5A5A5A"); labels(ch.plots[0].series[0], '0%', MUTED, size=7.5)
for i, r_ in rk.iterrows():
    if r_.distributor_code == "DENMARK":
        pt = ch.plots[0].series[0].points[i]; pt.format.fill.solid(); pt.format.fill.fore_color.rgb = rgb(RED)
panel(s, [
    f"Denmark is #{dk_rank} of {n_mkts}: {pct(gps25)} against a network median of {pct(med)}. Nobody is above 100%; the highest market is at {pct(float(r25.gps_capture_vs_max.iloc[0]))}.",
    f"Across all ranked markets together, ISZE billing covers {pct(net_w)} of the fleet potential, so Denmark is well above the network as a whole.",
    f"Denmark is {(r_above - gps25) * 100:.1f} points behind the market in place {dk_rank - 1} and {(gps25 - r_below) * 100:.1f} points ahead of place {dk_rank + 1}: the middle of the table is tight.",
    f"On our fleet check ({CHK:,.0f} vehicles) Denmark would read about {pct(gps25_chk)}, around #{int((r25.gps_capture_vs_max > gps25_chk).sum()) + 1}. Agreeing the fleet base matters for the ranking."])

# ======================================================================= 16 Nordic ranking
nk = nord.iloc[::-1].reset_index(drop=True)
nn = [("Denmark" if r_.distributor_code == "DENMARK" else (str(r_.country) if NAMED else f"Nordic market {chr(65 + len(nk) - 1 - i)}")) for i, r_ in nk.iterrows()]
s = base("Genuine parts share  ·  Nordic ranking", f"In the Nordics Denmark is #{dk_nrank} of {len(nord)}; the leaders sit above 84%",
         f"Genuine parts share, Nordic markets  |  calendar 2025  |  same method as the network ranking  |  {'markets named' if NAMED else 'other markets not named'}",
         "Source: gps_spu_by_distributor.csv (2025, full year), region Nordics. Fleet = vehicles in operation per market; fleet potential = fleet × modelled parts spend per vehicle.")
cd = CategoryChartData(); cd.categories = nn; cd.add_series("Genuine parts share 2025", [round(float(v), 3) for v in nk.gps_capture_vs_max])
ch = chart(s, XL_CHART_TYPE.BAR_CLUSTERED, cd, 0.4, 1.8, 5.6, 4.3)
style_chart(ch, '0%', legend=False); ch.value_axis.minimum_scale = 0; ch.value_axis.maximum_scale = 1.0; ch.plots[0].gap_width = 45
col_fill(ch.plots[0].series[0], "5A5A5A"); labels(ch.plots[0].series[0], '0.0%', WHITE, size=9)
for i, r_ in nk.iterrows():
    if r_.distributor_code == "DENMARK":
        pt = ch.plots[0].series[0].points[i]; pt.format.fill.solid(); pt.format.fill.fore_color.rgb = rgb(RED)
cols = [(6.2, 1.5), (7.7, 0.95), (8.65, 0.95)]
y = 1.85
for (x, w), h in zip(cols, ["Market", "Fleet 2025", "Share"]):
    rect(s, x, y, w, 0.38, RED); txt(s, x + 0.08, y, w - 0.14, 0.38, h, 8, WHITE, True, PP_ALIGN.LEFT if x == 6.2 else PP_ALIGN.CENTER, MSO_ANCHOR.MIDDLE)
y += 0.42
for i, r_ in nord.iterrows():
    nm = "Denmark" if r_.distributor_code == "DENMARK" else (str(r_.country) if NAMED else f"Nordic market {chr(65 + i)}")
    fillc = ROW2 if i % 2 == 0 else PANEL; hl = r_.distributor_code == "DENMARK"
    for (x, w), v in zip(cols, [nm, f"{r_.uio_units:,.0f}", pct(float(r_.gps_capture_vs_max))]):
        rect(s, x, y, w, 0.44, fillc)
        txt(s, x + 0.08, y, w - 0.14, 0.44, v, 9, RED if hl else WHITE, hl, PP_ALIGN.LEFT if x == 6.2 else PP_ALIGN.CENTER, MSO_ANCHOR.MIDDLE)
    y += 0.47
txt(s, 6.2, y + 0.1, 3.4, 1.2, f"Denmark has the second-smallest Nordic fleet. With few vehicles, one large fleet customer or one bulk order moves the share by several points.", 8, MUTED)
rect(s, 0.4, 6.25, 9.2, 0.75, PANEL, BORDER)
gap_next = float(nord.gps_capture_vs_max.iloc[dk_nrank - 2]) - gps25 if dk_nrank > 1 else 0
txt(s, 0.65, 6.25, 8.8, 0.75, f"Denmark {pct(gps25)}   |   next place up: {pct(float(nord.gps_capture_vs_max.iloc[dk_nrank - 2]))} (+{gap_next * 100:.1f} points ≈ {k(gap_next * WALLET)} a year of extra billing)", 10.5, WHITE, True, anchor=MSO_ANCHOR.MIDDLE)
panel(s, [
    f"Denmark is #{dk_nrank} of {len(nord)} Nordic markets, close behind the market in third place and well ahead of the last.",
    f"Moving up one place takes {gap_next * 100:.1f} points of share, about {k(gap_next * WALLET)} of additional parts a year on today's fleet base.",
    f"The two leaders have fleets of {nord.uio_units.iloc[0]:,.0f} and {nord.uio_units.iloc[1]:,.0f} vehicles, the same size class as Denmark, so they are a fair benchmark.",
    "Question: what would Isuzu Danmark need from ISZE (stock list, pricing on competitive parts, fill rate) to close that gap?"])

# ======================================================================= 17 the ask: part-level sales to dealer
s = base("Next steps  ·  Data request", "Part-level sales to dealer: the same report you send today, by part number",
         "What we ask, and what it gives Isuzu Danmark", "Request: sales to dealer by part number and month, quantities only, from 1 January 2025 onwards; monthly after that. No prices or margins needed.")
cards = [("1", "Already halfway there", ["Isuzu Danmark reports sales to dealer every month in the KPI file.", "The ask is the same figure split by part number: quantity per part per month. No prices, no margins, no dealer names."]),
         ("2", "Stock that follows your dealers", ["Your fast movers become visible, so ISZE can stock them for Denmark.", f"Fewer urgent orders (today {pct(u26, 0)} of parts value) and a higher fill rate on the first order."]),
         ("3", "A clear view of where demand goes", ["Part-level data separates a stock movement from a lost job.", f"It answers the €{ratio:.1f}-per-€1 question on page 7 and makes service-part cover measurable, which today swings on bulk orders."]),
         ("4", "A fair target and a fair ranking", ["Targets and the genuine parts share can be built on what dealers actually sell.", "Together with your own fleet count, both sides work from one set of numbers."])]
cw = (9.2 - 0.3) / 2
for i, (n, h, body) in enumerate(cards):
    x = 0.4 + (i % 2) * (cw + 0.3); y = 1.85 + (i // 2) * 2.2
    rect(s, x, y, cw, 2.0, PANEL, BORDER)
    rect(s, x + 0.2, y + 0.2, 0.45, 0.45, RED); txt(s, x + 0.2, y + 0.2, 0.45, 0.45, n, 14, WHITE, True, PP_ALIGN.CENTER, MSO_ANCHOR.MIDDLE)
    txt(s, x + 0.8, y + 0.24, cw - 1.0, 0.35, h, 12, WHITE, True)
    txt(s, x + 0.8, y + 0.7, cw - 1.0, 1.2, body, 8.8, MUTED)
rect(s, 0.4, 6.3, 9.2, 0.7, RED)
txt(s, 0.65, 6.3, 8.8, 0.7, "What we use it for: stock planning, fill rate and joint category actions. It is not used to review Isuzu Danmark's pricing to dealers.", 10, WHITE, True, anchor=MSO_ANCHOR.MIDDLE)
panel(s, [
    "Other distributors already share part-level sales to dealer with ISZE. It is what made stock-build and campaign effects visible in their reviews.",
    "The file can be a simple export: invoice month, part number, quantity. ISZE does the mapping to families and Genuine / BVP.",
    "We share the results back: a monthly view of your dealer demand by family, next to what you buy from ISZE.",
    "Question: who at Isuzu Danmark can provide the first file, and can it start with January 2025 to July 2026?"])

# ======================================================================= 18 discussion priorities
s = base("Discussion priorities", "Three topics should drive the Isuzu Danmark review",
         "Built on ISZE billing, the KPI file, Power BI fill rate and the fleet check", "Sources: as on the individual pages.")
pri = [("Availability", f"Bring fill rate back above {pct(FR_TARGET, 0)} and move the {six} regularly bought part numbers, plus the dealer fast movers, onto stock orders. Target: urgent share from {pct(u26, 0)} towards the network {pct(u_net, 0)}."),
       ("One set of numbers", f"Agree the fleet base ({UIO25:,.0f} in our file, about {CHK:,.0f} on the registrations) and what the sales-to-dealer figure includes. Then the share, the ranking and the targets all rest on the same base."),
       ("Growth on plan", f"Hold the pace for the second half: {k(need_rest)} to reach the {k(bp48_tot)} BP. Repair parts are growing with the ageing fleet; competitive parts are where share can be won.")]
for i, (h, body) in enumerate(pri):
    y = 1.9 + i * 1.62
    rect(s, 0.4, y, 9.2, 1.45, PANEL, BORDER)
    rect(s, 0.4, y, 0.12, 1.45, RED)
    txt(s, 0.75, y + 0.18, 8.6, 0.32, f"{i + 1}.  {h}", 13, WHITE, True)
    txt(s, 0.75, y + 0.62, 8.6, 0.8, body, 9.5, MUTED)
panel(s, [
    "Isuzu Danmark is on plan and growing. The review should spend its time on availability, not on the target.",
    "Fill rate and urgent orders are two sides of one problem: ISZE stocks what it sees, and today it only sees urgent demand.",
    "The fleet check is in Isuzu Danmark's interest as much as ours: a correct base makes the targets fair.",
    "Question: which of the three does Isuzu Danmark want to start with?"])

# ======================================================================= 19 action points (with the 'one decision' box from the network review)
s = base("Action points", "Proposed output of the review for Isuzu Danmark and ISZE", "To agree in the meeting; owners per side", "Owners and dates to be confirmed in the meeting.")
acts = [("Part-level sales to dealer", "First file Jan 2025 – Jul 2026 (month, part number, quantity), then monthly.", "Isuzu Danmark"),
        ("Fleet base", f"Share own vehicle count by registration year; ISZE updates the fleet file ({UIO25:,.0f} → agreed figure).", "Joint"),
        ("Days in stock", "Report days of parts in stock monthly in the KPI file.", "Isuzu Danmark"),
        ("Fill rate", "List the part numbers behind the March–May and September 2026 dips; agree a Denmark stock list.", "ISZE"),
        ("Order pattern", f"Move regularly bought parts from urgent to stock orders; review the urgent share quarterly (today {pct(u26, 0)}).", "Joint"),
        ("Sales to dealer scope", "Confirm what the reported sales-to-dealer figure includes (accessories, lubricants, other suppliers).", "Isuzu Danmark")]
cols = [(0.4, 2.2), (2.6, 5.4), (8.0, 1.6)]
y = 1.85
for (x, w), h in zip(cols, ["Topic", "Action", "Owner"]):
    rect(s, x, y, w, 0.4, RED); txt(s, x + 0.1, y, w - 0.15, 0.4, h, 8.5, WHITE, True, anchor=MSO_ANCHOR.MIDDLE)
y += 0.44
for i, row in enumerate(acts):
    fillc = ROW2 if i % 2 == 0 else PANEL
    for j, ((x, w), v) in enumerate(zip(cols, row)):
        rect(s, x, y, w, 0.56, fillc)
        txt(s, x + 0.1, y, w - 0.18, 0.56, v, 8.8 if j else 9, WHITE, j == 0, anchor=MSO_ANCHOR.MIDDLE)
    y += 0.59
rect(s, 0.4, y + 0.12, 9.2, 0.85, PANEL, BORDER)
txt(s, 0.6, y + 0.22, 2.2, 0.25, "THE ONE DECISION WE NEED", 7.5, RED, True)
txt(s, 0.6, y + 0.48, 8.8, 0.45, "Whether part-level sales to dealer becomes a standing part of the Isuzu Danmark review. With it, stock, fill rate and targets follow dealer demand.", 9.5, WHITE, True)
panel(s, [
    "Suggested rhythm: a short monthly check on fill rate, urgent share and sales to dealer, and this full review twice a year.",
    "The first part-level file lets ISZE draft a Denmark stock list within a month.",
    "The fleet count and the sales-to-dealer scope are one-off questions; once answered, every later number gets easier to read.",
    "Next review: after the first part-level data, with FY2027 half-year billing."])

# ======================================================================= 20 appendix: method
s = base("Appendix  ·  Method", "How these figures were built", "Data used, what was assumed, and what was not shown",
         "All files are ISZE internal; build date 1 October 2026.")
blocks = [
    ("ISZE billing", f"SAP billing to sold-to 2027 and 2751 (both Isuzu Danmark), to {LAST:%d %B %Y}. Plan pages include the freight line, as the BP does; all other analysis excludes it. Fiscal year April–March."),
    ("FY2027 BP", f"Full Package Plan VP+ACC FY2027-28 BP 4+8 (received 1 October 2026): April–July actual, August–March plan; FY2027 {k(bp48_tot)}, FY2028 {k(bp28_tot)}."),
    ("KPI file", "KPI Master File August 2026: sales to dealer (€), back-order lines, days in stock (not tracked for Denmark), new LCV registrations."),
    ("Fill rate", "Power BI SALES DATA VP NEW, INDIVIDUAL FILL RATE, ISZ DENMARK, engines excluded, monthly labels as shown in the report."),
    ("Order type", f"SAP order type per billing line. Urgent = VOR, RUSH, SVOR. April–June 2026 has no order type in the export ({pct(1 - saty_cov27, 0)} of FY2027 parts value uncoded), so FY2027 uses July–August."),
    ("Genuine parts share", f"ISZE billing incl. warranty ÷ (fleet × modelled parts spend per vehicle). Ranking: calendar 2025, {n_mkts} markets with a fleet base. Trend: fiscal billing on the fixed 2025 fleet potential of {k(WALLET)}."),
    ("Fleet check", f"Fleet end 2024 ({uio[2024]:,.0f}) + 2025 registrations ({reg25}) – 1 to 2% scrapping = about {CHK:,.0f}. An assumption, to be replaced by Isuzu Danmark's own count."),
    ("Not shown", "Service-part (PMS) cover: on a fleet of this size single bulk orders push several families above 100% in one year, so the measure is not reliable without sales-to-dealer data. No dealer prices or margins were used.")]
cw = (12.7 - 0.3) / 2
for i, (h, body) in enumerate(blocks):
    x = 0.4 + (i % 2) * (cw + 0.3); y = 1.85 + (i // 2) * 1.3
    rect(s, x, y, cw, 1.18, PANEL, BORDER)
    txt(s, x + 0.2, y + 0.14, cw - 0.4, 0.25, h.upper(), 7.5, RED, True)
    txt(s, x + 0.2, y + 0.42, cw - 0.4, 0.75, body, 8.4, WHITE)

prs.save(OUT)
print("saved", OUT)
print({"ytd27": ytd27, "bp_ytd": bp_ytd, "bp_tot": bp48_tot, "fy26": fy26_tot, "ytd26": ytd26, "sd_aj26": sd_aj26, "sd_aj27": sd_aj27, "sd_fy26": sd_fy26,
       "u25": u25, "u26": u26, "u_ja26": u_ja26, "u_net": u_net, "saty_cov27": saty_cov27, "n_pn26": n_pn26, "once": once, "six": six, "n80": n80,
       "gps25": gps25, "rank": dk_rank, "n": n_mkts, "nrank": dk_nrank, "med": med, "net_w": net_w, "gfy": gfy, "CHK": CHK, "reg25": reg25,
       "gps25_chk": gps25_chk, "gfy26_chk": gfy26_chk, "ratio": ratio, "bo": bo, "days_status": days_status})
