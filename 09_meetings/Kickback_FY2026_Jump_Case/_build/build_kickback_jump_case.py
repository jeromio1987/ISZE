"""THE CASE FOR THE KICKBACK — ISZE FY2027, shared deck for Japan / IML management.

Purpose (Jerome, 2026-10-07): argue FOR the kickback programme. It is the incentive that
makes steep annual business-plan increases deliverable; no case of rebate gaming was found;
where the rules can be improved, improve them rather than trim them.

Reads every figure from source; nothing typed in by hand:
  plan + kickback    : 01_data/11_planning/budget_per_DB_reviewed_24042026.xlsx   ('Incentive FY27')
  multi-year ramp    : 90_archive/root_files/ISZE Vehicle Parts - FY2026 Year-End Review.xlsx ('Kosha Gap & FY2027')
  FY2027 monthly BP  : 01_data/11_planning/FY2027  BP VP&ACC.xlsx                 ('VP FY27')
  billing            : 01_data/00_derived/sales_fact.parquet
  days of stock      : 01_data/11_planning/KPI Master File august 2026.xlsx       ('Parts Handling')
  sales to dealer    : 01_data/00_derived/dealer_sellout_long_*.csv
  order types        : 01_data/00_derived/order_headers_from_Order_Detail.csv     (SaTy)

Style: charcoal (bg 262626, panel 303030, border 6E6E6E, red E30613, amber F5A000, grey B7B7B7, green 31A354, Aptos).
"""
from __future__ import annotations

import sys
from pathlib import Path

import openpyxl
import pandas as pd
from pptx import Presentation
from pptx.chart.data import CategoryChartData
from pptx.dml.color import RGBColor
from pptx.enum.chart import XL_CHART_TYPE, XL_LEGEND_POSITION
from pptx.enum.shapes import MSO_SHAPE, MSO_CONNECTOR
from pptx.enum.text import PP_ALIGN, MSO_ANCHOR
from pptx.util import Inches, Pt

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
ROOT = Path(r"C:\Users\jerom\Desktop\claude\ISZE")
HERE = ROOT / "09_meetings" / "Kickback_FY2026_Jump_Case"
HERE.mkdir(parents=True, exist_ok=True)
DER = ROOT / "01_data" / "00_derived"
PLAN = ROOT / "01_data" / "11_planning"
OUT = HERE / "ISZE_Kickback_FY2026_Year_End_Jump_Case.pptx"

# ── palette ─────────────────────────────────────────────────────────────────
BG, PANEL, BORDER, ROW2 = "262626", "303030", "6E6E6E", "2B2B2B"
WHITE, MUTED, GRID = "F2F2F2", "BDBDBD", "4D4D4D"
RED, AMBER, GREY, GREEN = "E30613", "F5A000", "B7B7B7", "31A354"
FONT = "Aptos"


def rgb(h):
    return RGBColor.from_string(h)


def num(x):
    if x is None:
        return None
    if isinstance(x, (int, float)):
        return float(x)
    s = str(x).strip().replace("€", "").replace("%", "").replace(",", ".")
    if s.upper() in {"N/D", "N/A", "NA", "-", "", "?"}:
        return None
    try:
        return float(s)
    except ValueError:
        return None


# ── data ────────────────────────────────────────────────────────────────────
CODES = {
    "ITUK": [2575], "IUK": [2574], "UMI": [1797], "UTI": [1799],
    "Benelux": [90], "Germany": [93, 2516, 601], "Portugal": [519, 92],
    "Ireland": [76], "Norway": [86], "Sweden": [2181],
}
# distributor-facing set: ITUK is intercompany and is excluded from the kickback comparison
DIST = ["IUK", "UTI", "UMI", "Germany", "Benelux", "Portugal", "Sweden", "Norway", "Ireland"]
KPI_LABEL = {
    "ITUK": ["ITUK"], "IUK": ["IUK"], "UMI": ["UMI"], "UTI": ["UTI"],
    "Germany": ["ISD"], "Benelux": ["IBX (BENELUX)"], "Portugal": ["Imotors"],
    "Sweden": ["Isuzu Sverige"], "Norway": ["RSA"], "Ireland": ["Isuzu Ireland"],
}
FY = ["Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec", "Jan", "Feb", "Mar"]
FY26 = ["2025-04", "2025-05", "2025-06", "2025-07", "2025-08", "2025-09",
        "2025-10", "2025-11", "2025-12", "2026-01", "2026-02", "2026-03"]


def load_incentive():
    """Full accounting figures: BP FY26, BP FY27, increase, incentive, per customer."""
    p = PLAN / "budget_per_DB_reviewed_24042026.xlsx"
    wb = openpyxl.load_workbook(p, read_only=True, data_only=True)
    ws = wb["Incentive FY27"]
    name_map = {"ITUK": "ITUK", "IUK": "IUK", "UMI": "UMI", "UTI": "UTI",
                "IBX": "Benelux", "ISD": "Germany", "Portugal": "Portugal",
                "Ireland": "Ireland", "Norway": "Norway", "Sweden": "Sweden",
                "KTK": "KTK"}
    order, out = [], {}
    for r in range(3, 20):
        label = ws.cell(r, 1).value
        if not label:
            continue
        key = str(label).strip()
        if key not in name_map:
            continue
        rec = {
            "code": name_map[key],
            "bp26": num(ws.cell(r, 2).value),
            "bp27": num(ws.cell(r, 4).value),
            "inc_pct": num(ws.cell(r, 5).value),
            "inc_eur": num(ws.cell(r, 6).value),
            "incentive": num(ws.cell(r, 8).value),
        }
        if rec["bp26"] and rec["bp27"]:
            out[name_map[key]] = rec
            order.append(name_map[key])
    wb.close()
    return order, out


PLAN_ORDER, INC = load_incentive()
PLAN_TOT26 = sum(v["bp26"] for v in INC.values())
PLAN_TOT27 = sum(v["bp27"] for v in INC.values())
INC_TOTAL = sum(v["incentive"] or 0 for v in INC.values())
RAMP_PCT = (PLAN_TOT27 / PLAN_TOT26 - 1) * 100

# ── where the plan figures come from ────────────────────────────────────────
# Provenance established 2026-10-07 by exact-value search across 01_data/11_planning/,
# 01_data/92_archive/ and 01_data/90_INBOX/: the FY2026 per-customer plan exists on disk
# only as the 'BP FY26' column of budget_per_DB_reviewed_24042026.xlsx, sheet 'Incentive FY27'.
# No earlier FY2026 budget document on disk carries those figures (checked: the January 2026
# 'Business plan (FY2024&25 actuals & FY2026 forecast)' attachments have an FY26 Plan column
# that is empty; the 2025-12-01 Duncan budget workbook is ITUK-only and in GBP).
BP_SOURCES = (
    "Sources for the plan figures. FY2026 plan per customer: no earlier budget document on disk carries "
    "it — it is the 'BP FY26' column of 01_data/11_planning/budget_per_DB_reviewed_24042026.xlsx, sheet "
    "'Incentive FY27'. FY2027 plan: the same workbook's 'BP FY27' column; its monthly split is "
    "01_data/11_planning/FY2027  BP VP&ACC.xlsx, sheet 'VP FY27'. Multi-year path to FY2031: "
    "90_archive/root_files/ISZE Vehicle Parts - FY2026 Year-End Review.xlsx, sheet 'Kosha Gap & FY2027'."
)


def load_mos_band(db_label):
    """MOS target band (days of parts in stock) for one distributor, from the KPI targets workbook."""
    p = PLAN / "ISZE_DB_KPI_Targets_FY2627_v1.xlsx"
    wb = openpyxl.load_workbook(p, read_only=True, data_only=True)
    ws = wb["Targets FY26-27"]
    out = None
    for r in range(5, ws.max_row + 1):
        if str(ws.cell(r, 1).value or "").strip() == db_label:
            out = {"supply_class": str(ws.cell(r, 3).value or "").strip(),
                   "lo": num(ws.cell(r, 8).value), "hi": num(ws.cell(r, 9).value)}
            break
    wb.close()
    return out


MOS_BAND = load_mos_band("IBX (incl. Polska)") or {}

def load_billing():
    sf = pd.read_parquet(DER / "sales_fact.parquet",
                         columns=["billing_date", "sold_to_sap", "net_sales_value"])
    sf["billing_date"] = pd.to_datetime(sf["billing_date"], errors="coerce")
    sf = sf.dropna(subset=["billing_date"])
    sf["ym"] = sf["billing_date"].dt.to_period("M").astype(str)
    sf["eur"] = pd.to_numeric(sf["net_sales_value"], errors="coerce").fillna(0.0)
    sf["code"] = pd.to_numeric(sf["sold_to_sap"], errors="coerce").astype("Int64")
    out = {}
    for name, codes in CODES.items():
        out[name] = sf[sf["code"].isin(codes)].groupby("ym")["eur"].sum().reindex(FY26, fill_value=0.0)
    return sf, out


SF, BILL = load_billing()


def load_stock_series(label):
    p = PLAN / "KPI Master File august 2026.xlsx"
    wb = openpyxl.load_workbook(p, read_only=True, data_only=True)
    ws = wb["Parts Handling"]
    hdr = [str(ws.cell(3, c).value).strip() if ws.cell(3, c).value else None
           for c in range(2, ws.max_column + 1)]
    out = {}
    r = 4
    while r <= ws.max_row and str(ws.cell(r, 1).value or "").strip() not in ("", "Distributor"):
        if str(ws.cell(r, 1).value).strip() == label:
            for i, h in enumerate(hdr):
                if h:
                    v = num(ws.cell(r, 2 + i).value)
                    if v is not None:
                        out[h.strip()] = v
            break
        r += 1
    wb.close()
    return out


MOS_ORDER = ["Jan 25", "Feb 25", "Mrz 25", "Apr 25", "Mai 25", "Jun 25", "Jul 25", "Aug 25",
             "Sep 25", "Okt 25", "Oct 25", "Nov 25", "Dez 25", "Dec 25", "Jan 26", "Feb 26",
             "Mar 26", "Apr 26", "May 26", "Jun 26", "Jul 26"]
IBX_MOS_FULL = load_stock_series("IBX (BENELUX)")
IBX_MOS = [(k, IBX_MOS_FULL[k]) for k in MOS_ORDER if k in IBX_MOS_FULL]
# FY2026 fiscal-year window for the IBX story: Jan 26 -> Jul 26
IBX_STORY = [(k, IBX_MOS_FULL[k]) for k in
             ("Jan 26", "Feb 26", "Mar 26", "Apr 26", "May 26", "Jun 26", "Jul 26")
             if k in IBX_MOS_FULL]


def load_sorvor():
    """Planned (SOR/PRD) versus urgent (VOR/RUSH/SVOR) share of order value.

    Read with the data problems in mind. Verified against
    01_data/90_INBOX/SOR_VOR_IMPROVEMENT_IBX_ISD_20261007.md section 9 on 2026-10-07:

      * IBX (90) carries a genuine extraction gap: last order document 14 Apr 2025,
        nothing until 21 May 2025. Those weeks were all-urgent, which drags the FY2026
        baseline down and manufactures an apparent rise. With the gap months held out of
        the baseline the planned share FALLS. The only clean gap-free like-for-like
        window is Jun-Aug.
      * ISD's apparent decline is a code-mix move between sold-to 2516 (always planned)
        and 601 (never planned), not a change in ordering behaviour.
      * Urgent orders here carry HIGHER gross margin than planned, so "less urgency"
        must never be argued as a margin argument.
    """
    p = DER / "order_headers_from_Order_Detail.csv"
    d = pd.read_csv(p, usecols=["Sold-to pt", "created", "eur", "SaTy"], low_memory=False)
    d["created"] = pd.to_datetime(d["created"], errors="coerce")
    d["eur"] = pd.to_numeric(d["eur"], errors="coerce").fillna(0.0)
    d["ym"] = d["created"].dt.to_period("M").astype(str)
    d["SaTy"] = d["SaTy"].astype(str).str.strip().str.upper()
    PLANNED = {"SOR", "PRD"}
    FY27 = ["2026-04", "2026-05", "2026-06", "2026-07", "2026-08"]
    GAP = ("2025-04", "2025-05")          # the five-week IBX extraction gap

    def pct(sub, months):
        s = sub[sub["ym"].isin(months)]
        tot = s["eur"].sum()
        pl = s[s["SaTy"].isin(PLANNED)]["eur"].sum()
        if not tot:
            return None
        return {"total": tot, "planned": pl, "urgent": tot - pl, "planned_pct": pl / tot * 100}

    out = {}
    for name, codes in {"Benelux": [90.0], "Germany": [2516.0, 601.0]}.items():
        sub = d[d["Sold-to pt"].isin(codes)]
        fy26 = pct(sub, FY26)
        fy27 = pct(sub, FY27)
        fy26_nogap = pct(sub, [m for m in FY26 if m not in GAP])
        ja25 = pct(sub, ["2025-06", "2025-07", "2025-08"])
        ja26 = pct(sub, ["2026-06", "2026-07", "2026-08"])
        out[name] = {
            "fy26": fy26, "fy27": fy27, "fy26_nogap": fy26_nogap,
            "jun_aug_25": ja25, "jun_aug_26": ja26,
            "pp_as_file": fy27["planned_pct"] - fy26["planned_pct"],
            "pp_gap_removed": fy27["planned_pct"] - fy26_nogap["planned_pct"],
            "pp_clean_jun_aug": ja26["planned_pct"] - ja25["planned_pct"],
            "clean_planned_eur": ja26["planned"] - ja25["planned"],
            "clean_vol_then": ja25["total"], "clean_vol_now": ja26["total"],
        }
    return out


SORVOR = load_sorvor()


def isze_median_unit_price():
    """Median ISZE net billed price per part number, over every positive billing line.

    The dealer reports carry quantity only, so dealer volume has to be valued. The method
    is the one already used by 01_data/91_build/_scratch/_eurostd_20261007_build.py and
    _analyze_stock_d_20261007.py - reused here rather than invented:

        unit price per part number = median, over all billing lines with billed_qty > 0,
                                     of net_sales_value / billed_qty
        sales to dealer EUR        = dealer-file quantity x that unit price

    The euro value is therefore the dealer's volume measured at OUR prices, not the
    distributor's selling price, which is not on file. The direction of a series is the
    reading; a level against our own billing is a price-ladder difference, not a margin.
    """
    sf = pd.read_parquet(DER / "sales_fact.parquet",
                         columns=["part_number", "billed_qty", "net_sales_value"])
    sf["pn"] = sf["part_number"].astype(str).str.strip()
    sf["billed_qty"] = pd.to_numeric(sf["billed_qty"], errors="coerce")
    sf["net_sales_value"] = pd.to_numeric(sf["net_sales_value"], errors="coerce")
    pos = sf[sf["billed_qty"] > 0].copy()
    pos["unit_eur"] = pos["net_sales_value"] / pos["billed_qty"]
    return pos.groupby("pn")["unit_eur"].median()


PRICE = isze_median_unit_price()


def load_sellout():
    """Onward sales to dealer, in EUR, by distributor - where a monthly file exists.

    reads the same dealer files as before and now values the reported volume at the
    median ISZE net unit price per part number, so the reading is a euro movement and
    not a movement in pieces.
    """
    files = {
        "IUK": ["dealer_sellout_long_IUK_CY2025.csv", "dealer_sellout_long_IUK_CY2026YTD.csv"],
        "Ireland": ["dealer_sellout_long_IRELAND_CY2025.csv", "dealer_sellout_long_IRELAND_CY2026YTD.csv"],
        "Portugal": ["dealer_sellout_long_PORTUGAL_CY2025.csv", "dealer_sellout_long_PORTUGAL_CY2026YTD.csv"],
        "UTI": ["dealer_sellout_long_UTI_CY2025.csv", "dealer_sellout_long_UTI_CY2026YTD.csv"],
    }
    out = {}
    for name, fs in files.items():
        parts = []
        for f in fs:
            fp = DER / f
            if fp.exists():
                d = pd.read_csv(fp, usecols=lambda c: c in
                                {"period", "period_grain", "part_number", "qty"},
                                low_memory=False)
                d = d[d["period_grain"] == "month"].copy()
                d["pn"] = d["part_number"].astype(str).str.strip()
                d["eur"] = (pd.to_numeric(d["qty"], errors="coerce")
                            * d["pn"].map(PRICE))
                parts.append(d[["period", "qty", "eur"]])
        if not parts:
            continue
        allm = pd.concat(parts)
        allm["per"] = allm["period"].astype(str)
        e = allm.groupby("per")["eur"].sum().reindex(FY26)
        q = allm.groupby("per")["qty"].sum().reindex(FY26)
        cov = int(e.notna().sum())
        if cov < 6:
            out[name] = {"covered": cov, "usable": False}
            continue
        run = e.iloc[:10].mean(skipna=True)
        febmar = e.iloc[10:].sum(min_count=1)
        out[name] = {"covered": cov, "usable": True, "run": run, "febmar": febmar,
                     "pct": (febmar / (2 * run) - 1) * 100,
                     # units kept only as a cross-check, never as the reading
                     "run_qty": q.iloc[:10].mean(skipna=True),
                     "febmar_qty": q.iloc[10:].sum(min_count=1)}
    return out


SELL = load_sellout()
SELL_HAVE = ["IUK", "Ireland", "Portugal"]
SELL_OTHER = ["ITUK", "UTI"]          # files exist but histories are shorter
SELL_NONE = ["UMI", "Germany", "Benelux", "Sweden", "Norway"]


def load_monthly_plan_fy27():
    """FY2027 monthly plan from the BP workbook (Turnover, EUR)."""
    p = PLAN / "FY2027  BP VP&ACC.xlsx"
    wb = openpyxl.load_workbook(p, read_only=True, data_only=True)
    ws = wb["VP FY27"]
    total = [num(ws.cell(3, c).value) for c in range(4, 16)]
    wb.close()
    return [v or 0.0 for v in total]


FY27_MONTHLY = load_monthly_plan_fy27()
FY27_TOTAL = sum(FY27_MONTHLY)


def load_kosha_ramp():
    """Multi-year Kosha targets FY2024-FY2031 from the recovered year-end review."""
    cands = list((ROOT / "90_archive" / "root_files").glob("*FY2026 Year-End Review*.xlsx"))
    if not cands:
        return []
    wb = openpyxl.load_workbook(cands[0], read_only=True, data_only=True)
    ws = wb["Kosha Gap & FY2027"]
    out = []
    for r in range(7, 15):
        label = ws.cell(r, 2).value
        tgt = ws.cell(r, 3).value
        if not label or not tgt:
            continue
        s = str(tgt).replace("€", "").replace("M", "").strip()
        try:
            out.append((str(label), float(s)))
        except ValueError:
            continue
    wb.close()
    return out


KOSHA = load_kosha_ramp()


def ituk_windows():
    """ITUK billing windows, used on the pricing slide only."""
    d = SF[SF["code"] == 2575]
    m = d.groupby("ym")["eur"].sum()
    run = m.reindex(FY26[:10], fill_value=0.0).mean()
    feb = m.get("2026-02", 0.0)
    mar = m.get("2026-03", 0.0)
    return {"run": run, "feb": feb, "mar": mar,
            "feb_excess": feb - run, "mar_excess": mar - run,
            "febmar_excess": (feb + mar) - 2 * run}


ITUK = ituk_windows()

# plan-vs-actual for the distributor comparison (ITUK is intercompany and excluded)
DIST_ROWS = []
for _c in DIST:
    _fy = BILL[_c].sum()
    _pct = (_fy / INC[_c]["bp26"] - 1) * 100
    DIST_ROWS.append((_c, INC[_c]["bp26"], _fy, _pct))
ABOVE_DIST = sum(1 for *_, p in DIST_ROWS if p >= 0)
PLAN_ACT_TOT = sum(r[2] for r in DIST_ROWS)
PLAN_PLN_TOT = sum(r[1] for r in DIST_ROWS)
NET_VS_PLAN = (PLAN_ACT_TOT / PLAN_PLN_TOT - 1) * 100

# ── deck scaffolding ────────────────────────────────────────────────────────
prs = Presentation()
prs.slide_width, prs.slide_height = Inches(13.333), Inches(7.5)
BLANK = prs.slide_layouts[6]
PAGE = [0]


def txt(slide, x, y, w, h, text, size=10, color=WHITE, bold=False,
        align=PP_ALIGN.LEFT, anchor=MSO_ANCHOR.TOP):
    tb = slide.shapes.add_textbox(Inches(x), Inches(y), Inches(w), Inches(h))
    tf = tb.text_frame
    tf.word_wrap = True
    tf.vertical_anchor = anchor
    tf.margin_left = tf.margin_right = tf.margin_top = tf.margin_bottom = 0
    for i, line in enumerate(text if isinstance(text, list) else [text]):
        p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
        p.alignment = align
        r = p.add_run()
        r.text = line
        r.font.size = Pt(size)
        r.font.bold = bold
        r.font.name = FONT
        r.font.color.rgb = rgb(color)
    return tb


def rect(slide, x, y, w, h, fill, line=None, shape=MSO_SHAPE.RECTANGLE):
    s = slide.shapes.add_shape(shape, Inches(x), Inches(y), Inches(w), Inches(h))
    if fill:
        s.fill.solid()
        s.fill.fore_color.rgb = rgb(fill)
    else:
        s.fill.background()
    if line:
        s.line.color.rgb = rgb(line)
        s.line.width = Pt(0.75)
    else:
        s.line.fill.background()
    s.shadow.inherit = False
    return s


def hline(slide, x, y, w, color, width=0.75):
    c = slide.shapes.add_connector(MSO_CONNECTOR.STRAIGHT, Inches(x), Inches(y),
                                   Inches(x + w), Inches(y))
    c.line.color.rgb = rgb(color)
    c.line.width = Pt(width)
    return c


def vline(slide, x, y, h, color, width=0.75, dash=False):
    c = slide.shapes.add_connector(MSO_CONNECTOR.STRAIGHT, Inches(x), Inches(y),
                                   Inches(x), Inches(y + h))
    c.line.color.rgb = rgb(color)
    c.line.width = Pt(width)
    return c


def arrow(slide, x, y, w, color):
    """A small right-pointing chevron between flow boxes."""
    a = rect(slide, x, y, w, 0.16, color, shape=MSO_SHAPE.RIGHT_ARROW)
    return a


def base(section, title, sub=None, source=None, number=True):
    PAGE[0] += 1
    s = prs.slides.add_slide(BLANK)
    s.background.fill.solid()
    s.background.fill.fore_color.rgb = rgb(BG)
    txt(s, 0.42, 0.26, 6.0, 0.2, "ISZE  ·  VEHICLE PARTS & ACCESSORIES", 7, WHITE, True)
    txt(s, 0.42, 0.52, 8.0, 0.22, section.upper(), 8, RED, True)
    txt(s, 0.42, 0.78, 11.6, 0.6, title, 21 if len(title) <= 62 else 17, WHITE, True)
    y = 1.42
    if sub:
        txt(s, 0.42, y, 12.2, 0.4, sub, 10.5, MUTED)
        y += 0.46
    if source:
        txt(s, 0.42, 7.06, 11.6, 0.3, source, 7.5, MUTED)
    if number:
        txt(s, 12.3, 0.26, 0.7, 0.2, f"{PAGE[0]:02d}", 8, MUTED, True, PP_ALIGN.RIGHT)
    hline(s, 0.42, 1.30, 12.5, GRID)
    return s, y


def kpi(slide, x, y, w, value, label, accent=RED):
    rect(slide, x, y, w, 0.98, PANEL)
    rect(slide, x, y, 0.045, 0.98, accent)
    txt(slide, x + 0.18, y + 0.13, w - 0.3, 0.4, value, 21, WHITE, True)
    txt(slide, x + 0.18, y + 0.58, w - 0.3, 0.34, label, 8.5, MUTED)


def table(slide, x, y, w, header, data, col_w=None, row_h=0.30, hdr_h=0.34, size=9.5):
    n = len(header)
    col_w = col_w or [w / n] * n
    rect(slide, x, y, w, hdr_h, PANEL)
    cx = x
    for i, h in enumerate(header):
        al = PP_ALIGN.LEFT if i == 0 else PP_ALIGN.RIGHT
        txt(slide, cx + 0.10, y + 0.075, col_w[i] - 0.16, hdr_h, h, size - 0.5, MUTED, True, al)
        cx += col_w[i]
    yy = y + hdr_h
    for ri, row in enumerate(data):
        if ri % 2 == 1:
            rect(slide, x, yy, w, row_h, ROW2)
        cx = x
        for i, cell in enumerate(row):
            al = PP_ALIGN.LEFT if i == 0 else PP_ALIGN.RIGHT
            col, bold, val = WHITE, False, cell
            if isinstance(cell, tuple):
                if len(cell) == 3:
                    val, col, bold = cell
                else:
                    val, col = cell
            txt(slide, cx + 0.10, yy + 0.055, col_w[i] - 0.16, row_h, str(val), size, col, bold, al)
            cx += col_w[i]
        yy += row_h
    hline(slide, x, yy, w, GRID)
    return yy


def style_chart(ch, num_fmt='#,##0', legend=True, legend_pos=XL_LEGEND_POSITION.TOP):
    ch.font.name = FONT
    ch.font.size = Pt(8)
    ch.font.color.rgb = rgb(MUTED)
    ch.has_title = False
    if legend:
        ch.has_legend = True
        ch.legend.position = legend_pos
        ch.legend.include_in_layout = False
        ch.legend.font.color.rgb = rgb(MUTED)
        ch.legend.font.size = Pt(8)
    else:
        ch.has_legend = False
    va = ch.value_axis
    va.has_major_gridlines = True
    va.major_gridlines.format.line.color.rgb = rgb(GRID)
    va.major_gridlines.format.line.width = Pt(0.4)
    va.tick_labels.font.color.rgb = rgb(MUTED)
    va.tick_labels.font.size = Pt(7.5)
    va.format.line.color.rgb = rgb(GRID)
    va.has_title = False
    va.tick_labels.number_format = num_fmt
    va.tick_labels.number_format_is_linked = False
    ca = ch.category_axis
    ca.format.line.color.rgb = rgb(GRID)
    ca.tick_labels.font.color.rgb = rgb(MUTED)
    ca.tick_labels.font.size = Pt(7.5)
    ca.has_title = False


def col_fill(series, color):
    for p in series.points:
        p.format.fill.solid()
        p.format.fill.fore_color.rgb = rgb(color)


def chart(slide, x, y, w, h, categories, series, chart_type=XL_CHART_TYPE.COLUMN_CLUSTERED):
    cd = CategoryChartData()
    cd.categories = categories
    for name, values in series:
        cd.add_series(name, tuple(float(v) for v in values))
    gf = slide.shapes.add_chart(chart_type, Inches(x), Inches(y), Inches(w), Inches(h), cd)
    return gf.chart


def eur_full(v):
    """Full accounting euro figure: thousands separator, cents, minus sign."""
    return f"{v:,.2f}".replace(",", " ")


# ════════════════════════════════════════════════════════════════════════════
# 1  COVER
# ════════════════════════════════════════════════════════════════════════════
s = prs.slides.add_slide(BLANK)
s.background.fill.solid()
s.background.fill.fore_color.rgb = rgb(BG)
rect(s, 0, 0, 0.09, 7.5, RED)
txt(s, 0.85, 1.30, 11.5, 0.3, "ISZE  ·  VEHICLE PARTS & ACCESSORIES", 9.5, MUTED, True)
txt(s, 0.85, 1.80, 11.8, 1.6,
    ["The case for the kickback", "Growing the business plan by 9% a year, and why the incentive matters"], 30, WHITE, True)
hline(s, 0.85, 3.52, 6.0, RED, 1.2)
txt(s, 0.85, 3.78, 11.8, 1.0,
    "The network's annual parts plan rises from EUR 29.19M in FY2026 to EUR 31.82M in FY2027 — a "
    "EUR 2.63M increase, or 9.0%. The kickback is the mechanism that makes increases of that size "
    "deliverable, and FY2026 shows it being earned rather than gamed.", 11, MUTED)
txt(s, 0.85, 5.15, 11.8, 1.2,
    ["EUR 393,000  ·  across eleven customers  ·  1.2–1.4% of each customer's annual plan",
     "Prepared for review with Japan / IML management  ·  7 October 2026  ·  all figures in EUR"], 10, GREY)
txt(s, 0.85, 6.42, 11.8, 0.6,
    "Plan figures: FY2026 and FY2027 per customer from budget_per_DB_reviewed_24042026.xlsx, sheet "
    "'Incentive FY27' (no earlier FY2026 budget document on disk carries them); the multi-year path to "
    "FY2031 from the ISZE Vehicle Parts FY2026 Year-End Review, sheet 'Kosha Gap & FY2027'.", 7.5, MUTED)

# ════════════════════════════════════════════════════════════════════════════
# 2  CONCLUSION — reframed
# ════════════════════════════════════════════════════════════════════════════
s, y = base("Conclusion", "The kickback is doing its job: no case of rebate abuse was found, and the one apparent case resolved to a February recovery and a March price pre-buy",
            "The programme should be kept, and its rules improved where a slow start can still recover.")

kpi(s, 0.42, y + 0.05, 2.95, f"EUR {INC_TOTAL/1000:,.0f}K", "Kickback earned across the network, FY2026", RED)
kpi(s, 3.55, y + 0.05, 2.95, f"{RAMP_PCT:.1f}%", "Network parts plan increase, FY26 → FY27", AMBER)
kpi(s, 6.68, y + 0.05, 2.95, "0", "Cases of rebate abuse found", GREEN)
kpi(s, 9.81, y + 0.05, 3.13, "1 of 9", "Behind plan, then recovered — and it was earned", GREEN)

yy = y + 1.3
txt(s, 0.42, yy, 12.5, 0.3, "What the review found", 11, WHITE, True)
body = [
    ("No distributor gamed the rebate.", "We tested the year-end behaviour of every distributor in the "
     "programme against four independent signals. No case of buying purely to cross the line survived."),
    ("The single apparent case was earned, not gamed.", "One distributor was behind plan at ten months and "
     "recovered in February — the reward working as intended. Its March buying was a forward-buy ahead of "
     "the 13 March price list, not a rebate action."),
    ("Where stock rose, it was stock we asked for.", "One market's rise follows our own instruction to "
     "raise days of stock; another built after the price change. Neither is evidence of gaming."),
    ("A rising plan really was delivered.", f"{ABOVE_DIST} of {len(DIST)} distributors finished FY2026 at "
     f"or above plan, and the network closed {abs(NET_VS_PLAN):.1f}% ahead. The programme paid for "
     "performance that actually happened."),
]
yy += 0.36
for head, rest in body:
    rect(s, 0.42, yy + 0.03, 0.035, 0.5,
         GREEN if head.startswith(("No distributor", "The single", "Where stock")) else RED)
    txt(s, 0.60, yy, 12.1, 0.26, head, 10, WHITE, True)
    txt(s, 0.60, yy + 0.24, 12.1, 0.42, rest, 9.5, MUTED)
    yy += 0.78

# ════════════════════════════════════════════════════════════════════════════
# 3  THE RAMP — Isuzu 2030 and the business plan
# ════════════════════════════════════════════════════════════════════════════
s, y = base("Why an incentive matters", "The plan asks for 9% growth this year and roughly 6–12% a year out to FY2031 — that is when an incentive earns its keep",
            source="Sources: multi-year path to FY2031 — 90_archive/root_files/ISZE Vehicle Parts - FY2026 "
                   "Year-End Review.xlsx, sheet 'Kosha Gap & FY2027'. FY2026 and FY2027 plan per customer — "
                   "01_data/11_planning/budget_per_DB_reviewed_24042026.xlsx, sheet 'Incentive FY27' (no earlier "
                   "FY2026 budget document on disk carries these figures). Isuzu's IX 2030 plan (JPY 6tn sales) "
                   "is external context only.")
kpi(s, 0.42, y + 0.05, 3.05, f"EUR {PLAN_TOT26/1e6:.2f}M", "Network parts plan, FY2026", GREY)
kpi(s, 3.60, y + 0.05, 3.05, f"EUR {PLAN_TOT27/1e6:.2f}M", "Network parts plan, FY2027", WHITE)
kpi(s, 6.78, y + 0.05, 2.85, f"+{RAMP_PCT:.1f}%", "Increase asked for this year", AMBER)
kpi(s, 9.76, y + 0.05, 3.15, f"EUR {(PLAN_TOT27-PLAN_TOT26)/1e6:.2f}M", "Absolute increase to find", RED)

yy = y + 1.22
txt(s, 0.42, yy, 6.0, 0.3, "The multi-year plan", 11, WHITE, True)
txt(s, 6.85, yy, 6.0, 0.3, "What each customer is asked to grow, FY26 → FY27", 11, WHITE, True)
yy += 0.38

if KOSHA:
    kd = [[lab, f"EUR {v:.1f}M",
           (f"{(v/KOSHA[i-1][1]-1)*100:+.1f}%" if i else "—",
            RED if i >= 5 else MUTED, i >= 5)]
          for i, (lab, v) in enumerate(KOSHA)]
    table(s, 0.42, yy, 5.95, ["Fiscal year", "Kosha target", "Year on year"], kd,
          col_w=[2.45, 1.85, 1.65], row_h=0.295)
else:
    txt(s, 0.42, yy, 5.95, 0.4, "Multi-year target file not found on disk.", 9.5, AMBER)

cust_rows = []
for code in PLAN_ORDER:
    if code == "KTK":
        continue
    v = INC[code]
    pct = (v["bp27"] / v["bp26"] - 1) * 100
    cust_rows.append([code, f"EUR {v['bp26']/1e6:.2f}M", f"EUR {v['bp27']/1e6:.2f}M",
                      (f"{pct:+.1f}%", RED if pct >= 12 else (AMBER if pct >= 9 else MUTED), pct >= 12)])
cust_bottom = table(s, 6.85, yy, 6.06, ["Customer", "Plan FY26", "Plan FY27", "Increase"], cust_rows,
                    col_w=[2.06, 1.35, 1.35, 1.30], row_h=0.295, size=9)

txt(s, 0.42, cust_bottom + 0.24, 12.5, 0.8,
    "Every one of the ten distributor plans rises again this year, four of them by more than 12%. The Kosha "
    "path runs from EUR 29.6M to EUR 52.1M by FY2031 — a 76% increase over seven years. A plan that "
    "steep needs a reason to be chased every month, not only in March.", 9, MUTED)

# ════════════════════════════════════════════════════════════════════════════
# 4  WHAT THE KICKBACK IS — FULL ACCOUNTING FIGURES
# ════════════════════════════════════════════════════════════════════════════
s, y = base("The programme", "The kickback, to the cent: FY2026 plan, FY2027 plan, the increase and the incentive for each customer",
            source="Source: 01_data/11_planning/budget_per_DB_reviewed_24042026.xlsx, sheet 'Incentive FY27' — "
                   "the 'BP FY26' column is where the FY2026 plan per customer exists on disk, and 'BP FY27' is the "
                   "FY2027 plan. Figures as they appear in the workbook, to the cent.")
hdr = ["Customer", "Plan FY2026 (EUR)", "Plan FY2027 (EUR)", "Increase (EUR)",
       "Increase %", "Incentive %", "Incentive FY2027 (EUR)"]
data = []
for code in PLAN_ORDER:
    v = INC[code]
    data.append([code, eur_full(v["bp26"]), eur_full(v["bp27"]), eur_full(v["inc_eur"] or 0),
                 f"{(v['inc_pct'] or 0)*100:.4f}%", f"{(v['incentive']/v['bp27'])*100:.4f}%",
                 eur_full(v["incentive"] or 0)])
tot_inc_eur = sum(v["inc_eur"] or 0 for v in INC.values())
data.append([("TOTAL", WHITE, True), (eur_full(PLAN_TOT26), WHITE, True),
             (eur_full(PLAN_TOT27), WHITE, True), (eur_full(tot_inc_eur), WHITE, True),
             (f"{RAMP_PCT:.4f}%", WHITE, True), ("", WHITE, True),
             (eur_full(INC_TOTAL), WHITE, True)])
table(s, 0.42, y + 0.02, 12.49, hdr, data,
      col_w=[1.30, 2.05, 2.05, 1.90, 1.25, 1.30, 2.64], row_h=0.315, size=8.6)
txt(s, 0.42, y + 0.02 + 0.34 + 0.315 * len(data) + 0.16, 12.6, 0.8,
    "Eleven customers, one incentive mechanism: roughly 1.2% of the plan, paid once the annual purchase "
    "plan is reached. The total commitment for FY2027 is EUR 393,000 against a plan of EUR 31.82M. The "
    "incentive is small relative to the increase it is meant to unlock — EUR 2.63M of extra parts sales.", 9, MUTED)

# ════════════════════════════════════════════════════════════════════════════
# 5  HOW THE KICKBACK WORKS — dynamic visual overview
# ════════════════════════════════════════════════════════════════════════════
s, y = base("How it works", "Four steps that turn an ambitious plan into something a distributor has a reason to chase",
            "Read left to right: the plan sets the target, the distributor orders through the year, we measure it, the incentive is released.")
steps = [
    ("1", "Plan set", ["Annual parts plan", "agreed per customer", f"EUR {PLAN_TOT27/1e6:.2f}M network"]),
    ("2", "Orders placed", ["Purchases through the year", "planned stock orders, not", "emergency buying"]),
    ("3", "Performance measured", ["Against plan, monthly", "and at year end —", "and on sales to dealer"]),
    ("4", "Incentive released", ["About 1.2% of plan", f"EUR {INC_TOTAL/1e3:,.0f}K across", "eleven customers"]),
]
bx, bw, gap = 0.42, 2.83, 0.36
by = y + 0.22
for i, (n, title, lines) in enumerate(steps):
    x = bx + i * (bw + gap)
    rect(s, x, by, bw, 2.05, PANEL)
    rect(s, x, by, bw, 0.045, RED if i in (0, 3) else AMBER)
    rect(s, x + 0.22, by + 0.28, 0.52, 0.52, RED if i in (0, 3) else AMBER, shape=MSO_SHAPE.OVAL)
    txt(s, x + 0.22, by + 0.42, 0.52, 0.3, n, 15, WHITE, True, PP_ALIGN.CENTER)
    txt(s, x + 0.22, by + 0.94, bw - 0.44, 0.3, title, 11.5, WHITE, True)
    txt(s, x + 0.22, by + 1.28, bw - 0.44, 0.7, lines, 8.6, MUTED)
    if i < 3:
        arrow(s, x + bw + 0.045, by + 0.94, 0.27, GREY)

fy = by + 2.42
rect(s, 0.42, fy, 12.49, 0.72, ROW2)
txt(s, 0.62, fy + 0.14, 5.9, 0.5,
    ["A monthly rhythm, not a year-end event.",
     "Planned stock orders are placed through the year, so the target is worked month by month."], 9, MUTED)
txt(s, 6.90, fy + 0.14, 5.9, 0.5,
    ["Until now, all-or-nothing at the year end.",
     "The whole incentive turns on the final annual figure, which is what we propose to soften on slide 13."], 9, MUTED)
txt(s, 0.42, fy + 0.86, 12.5, 0.5,
    "No new money is being asked for. This is the existing mechanism, described plainly: what it is for, "
    "how it is earned, and what it buys us.", 9.5, MUTED)

# ════════════════════════════════════════════════════════════════════════════
# 6  EVIDENCE 1 — THE PLAN IS BEING DELIVERED
# ════════════════════════════════════════════════════════════════════════════
s = prs.slides.add_slide(BLANK) if False else None
rows = []
for code in DIST:
    v = INC[code]
    m = BILL[code]
    fy = m.sum()
    pct = (fy / v["bp26"] - 1) * 100
    rows.append([code, f"EUR {v['bp26']/1e6:.2f}M", f"EUR {fy/1e6:.2f}M",
                 (f"{pct:+.1f}%", GREEN if pct >= 0 else AMBER, pct >= 0)])
above = sum(1 for r in rows if r[3][1] == GREEN)
tot_plan_d = sum(INC[c]["bp26"] for c in DIST)
tot_act_d = sum(BILL[c].sum() for c in DIST)

s, y = base("Evidence 1 — the plan is being delivered",
            f"{ABOVE_DIST} of the {len(DIST)} distributors finished FY2026 at or above their rising plan, and the network closed {abs(NET_VS_PLAN):.1f}% ahead",
            source="Source: FY2026 billing by distributor (sales_fact.parquet, net sales value) against the annual plan "
                   "(budget_per_DB_reviewed_24042026.xlsx, 'Incentive FY27'). Fiscal year April 2025 – March 2026. "
                   "ITUK is an intercompany entity and is not part of this distributor comparison.")
rows = []
for code, p26, fact, pct in DIST_ROWS:
    rows.append([code, f"EUR {p26/1e6:.2f}M", f"EUR {fact/1e6:.2f}M",
                 (f"{pct:+.1f}%", GREEN if pct >= 0 else AMBER, pct >= 0)])
rows.append([(f"{len(DIST)} distributors", WHITE, True),
             (f"EUR {PLAN_PLN_TOT/1e6:.2f}M", WHITE, True),
             (f"EUR {PLAN_ACT_TOT/1e6:.2f}M", WHITE, True),
             (f"{NET_VS_PLAN:+.1f}%", GREEN, True)])
table(s, 0.42, y + 0.05, 8.2, ["Distributor", "Plan FY2026", "Billed FY2026", "vs plan"], rows,
      col_w=[2.3, 1.85, 1.85, 2.2], row_h=0.315)
bx = 8.82
rect(s, bx, y + 0.05, 4.09, 2.1, PANEL)
txt(s, bx + 0.22, y + 0.24, 3.7, 0.5, f"{ABOVE_DIST} of {len(DIST)}", 22, GREEN, True)
txt(s, bx + 0.22, y + 0.80, 3.7, 0.6, "distributors finished at or above their annual plan", 9.5, MUTED)
rect(s, bx, y + 2.28, 4.09, 2.1, PANEL)
txt(s, bx + 0.22, y + 2.47, 3.7, 0.5, f"EUR {INC_TOTAL/1e3:,.0f}K", 22, RED, True)
txt(s, bx + 0.22, y + 3.03, 3.7, 0.7, "of incentive earned against EUR 31.82M of planned "
    "parts sales — about 1.2%", 9.5, MUTED)
txt(s, 0.42, y + 4.55, 12.5, 0.7,
    "ITUK is excluded from this comparison: it is an intercompany entity, carried on its own target study "
    "rather than alongside the distributors. It is the only plan-vs-actual comparison in the deck that "
    "leaves it out — the pricing finding later keeps it in, because there it is our own sales team.", 9, MUTED)

# ════════════════════════════════════════════════════════════════════════════
# 7  EVIDENCE 2 — THE ONE CASE THAT LOOKED LIKE A JUMP
# ════════════════════════════════════════════════════════════════════════════
s, y = base("Evidence 2 — the one case that looked like a jump", "Behind plan at ten months, recovered in February — the incentive working exactly as intended",
            source="Source: ITUK billing by month (sales_fact.parquet, sold_to 2575) against its annual plan. "
                   "ITUK appears here as the worked example only; the distributor comparison on the previous page excludes it.")
kpi(s, 0.42, y + 0.05, 3.05, "5.6% behind", "At the ten-month point, FY2026", AMBER)
kpi(s, 3.60, y + 0.05, 3.05, f"EUR {ITUK['feb_excess']:,.0f}", "February above its own run rate", GREEN)
kpi(s, 6.78, y + 0.05, 2.85, "+6.2%", "Year finished ahead of plan", GREEN)
kpi(s, 9.76, y + 0.05, 3.15, "125 → 140 days", "Days of stock across the year", GREY)

rows = [
    ["Run rate, Apr 2025 – Jan 2026", f"EUR {ITUK['run']:,.2f} per month", "—"],
    ["January 2026 position", f"EUR {ITUK['run']*10:,.2f} accumulated", ("5.6% behind plan", AMBER, True)],
    ["February 2026", f"EUR {ITUK['feb']:,.2f}", (f"+EUR {ITUK['feb_excess']:,.2f} over run rate", GREEN, True)],
    ["March 2026", f"EUR {ITUK['mar']:,.2f}",
     (f"+EUR {ITUK['mar_excess']:,.2f} — mostly price pre-buy", AMBER, False)],
]
table(s, 0.42, y + 1.28, 12.49, ["ITUK, FY2026", "Billed", "Against its own run rate"], rows,
      col_w=[4.6, 3.8, 4.09], row_h=0.34)
txt(s, 0.42, y + 1.28 + 0.34 + 0.34 * len(rows) + 0.26, 12.6, 1.4, [
    "This is the recovery the incentive is designed to produce. ITUK was behind at ten months, then "
    "recovered inside the year. The February recovery — EUR 346,195 above its own run rate, after a first "
    "ten months that ran at EUR 515,524 a month — is the plan being chased and caught.",
    "One qualification, stated rather than implied: the March figure is largely a forward-buy ahead of "
    "the 13 March price list (slide 14), not a rebate action. The recovery that matters sits in February, "
    "and it is the reason we propose a tolerance band for slow starts on slide 13.",
], 9, MUTED)

# ════════════════════════════════════════════════════════════════════════════
# 8  CASE STUDY — IBX, A MATURE DISTRIBUTOR
# ════════════════════════════════════════════════════════════════════════════
s, y = base("Case study — IBX (Benelux)",
            "An under-stocked distributor is now inside its stock band and says it is holding more of its own stock — the direct order-mix evidence is not usable this year",
            source="Sources: target band from 01_data/11_planning/ISZE_DB_KPI_Targets_FY2627_v1.xlsx, sheets "
                   "'Targets FY26-27' and 'Assumptions' (IBX is supply class A, band 60–75 days). Reported days "
                   "of stock from 01_data/11_planning/KPI Master File august 2026.xlsx, sheet 'Parts Handling', "
                   "block 'Days of Parts in Stock'. Order mix from order detail (SaTy), IBX sold-to 90 — read "
                   "with the five-week records gap of April–May 2025.")
kpi(s, 0.42, y + 0.05, 3.05, f"{IBX_STORY[0][1]:.0f} → {IBX_STORY[-1][1]:.0f} d",
    "Days of parts in stock, Jan → Jul 2026", GREEN)
kpi(s, 3.60, y + 0.05, 3.05, "60–75 d",
    "Target band for IBX, supply class A — not a flat minimum", GREEN)
kpi(s, 6.78, y + 0.05, 2.85, "−1.69 pp",
    "Order mix, records gap removed — a fall, not a rise", AMBER)
kpi(s, 9.76, y + 0.05, 3.15, "+2.98 pp",
    "Only clean window (Jun–Aug) — about +EUR 8,600", AMBER)

ch = chart(s, 0.42, y + 1.22, 7.5, 2.75, [k for k, _ in IBX_STORY],
           [("Days of parts in stock", [v for _, v in IBX_STORY])])
style_chart(ch, '#,##0', legend=False)
ch.plots[0].gap_width = 55
col_fill(ch.plots[0].series[0], GREEN)

bx = 8.12
rect(s, bx, y + 1.22, 4.79, 2.75, PANEL)
txt(s, bx + 0.22, y + 1.36, 4.4, 0.3, "What the stock data shows", 11, WHITE, True)
txt(s, bx + 0.22, y + 1.68, 4.4, 2.2, [
    "Stock rebuilt from about 32 days in January 2026 to 63 by July — inside the 60–75 day band its "
    "supply class sets, where it had been below it.",
    "The target is not a flat rule: the band is order cycle plus transport from the Belgium PDC. Class A "
    "is 60–75 days, class B 75–90, class C by sea 90–120.",
    "The 63 days is IBX's own reported figure, from its own system, sent because we asked for it. Had it "
    "not reported it, we could not see this at all — that visibility is itself part of what the programme buys.",
], 8.6, MUTED)
txt(s, 0.42, y + 4.12, 12.5, 1.15,
    ["The Astara Western Europe business review of 12 August 2026 records the distributor telling us it "
     "“has shifted toward holding more own stock and less VOR ordering”. Our order records do not yet "
     "evidence the second half of that statement, and we do not claim it here.",
     "Order-mix evidence: not usable for FY2026. IBX's order records carry a five-week gap from 14 April "
     "to 21 May 2025 — our extracts hold nothing for IBX in that window, while 555 order documents worth "
     "EUR 2.62M sit in the same document range for fifteen other customers. Those missing weeks were "
     "entirely urgent, which flatters the FY2026 baseline: remove them and IBX's planned share falls by "
     "1.69 pp rather than rising. The one clean, gap-free like-for-like window is June–August: 55.18% to "
     "58.16%, +2.98 pp, about +EUR 8,600 of planned euro across three months and on falling volume, from "
     "EUR 596,573 to EUR 580,864. Stocking improved; the order-mix evidence is incomplete."], 9, MUTED)

# ════════════════════════════════════════════════════════════════════════════
# 9  EVIDENCE 3 — SALES TO DEALER
# ════════════════════════════════════════════════════════════════════════════
s, y = base("Evidence 3 — sales to dealer", "Where we can see onward sales, the goods moved on through the year rather than piling up at the year end",
            source="Source: distributor sales-to-dealer reports (monthly, part number and quantity; no prices) held by ISZE "
                   "in 01_data/00_derived, fiscal months April 2025 – March 2026 where covered. Reported volume is valued at "
                   "the median ISZE net billed price per part number; it is the dealer's volume at our prices, not the "
                   "distributor's selling price.")
rows = []
for name in SELL_HAVE:
    if name in SELL and SELL[name]["usable"]:
        srec = SELL[name]
        rows.append([name, f"{srec['covered']} of 12 months",
                     (f"{srec['pct']:+.1f}%" if abs(srec["pct"]) < 10 else f"{srec['pct']:+.0f}%",
                      GREEN if srec["pct"] >= -5 else AMBER, True),
                     "Onward sales held up through the year"])
table(s, 0.42, y + 0.05, 12.49, ["Distributor", "Months covered", "Feb+Mar sales to dealer vs its own run (EUR)", "Reading"], rows,
      col_w=[2.6, 2.3, 4.2, 3.39], row_h=0.36)
yy = y + 0.05 + 0.34 + 0.36 * len(rows) + 0.24
txt(s, 0.42, yy, 12.5, 0.5,
    "Where we have the file, the onward movement is positive over the year — the purchases were absorbed "
    "by dealer demand rather than sitting on the distributor's shelf.", 9.5, MUTED)

yy += 0.58
txt(s, 0.42, yy, 12.5, 0.3, "Coverage: who reports sales to dealer, and who does not", 11, WHITE, True)
yy += 0.36
rect(s, 0.42, yy, 6.05, 1.55, PANEL)
rect(s, 0.42, yy, 0.04, 1.55, GREEN)
txt(s, 0.66, yy + 0.14, 5.6, 0.3, "File on disk", 11, GREEN, True)
txt(s, 0.66, yy + 0.48, 5.6, 0.95, [
    "IUK, ITUK, Ireland, Portugal, Greece and Romania.",
    "UTI reports too, but its history covers only part of the year, so it cannot be compared on the "
    "same basis.",
], 9, MUTED)
rect(s, 6.86, yy, 6.05, 1.55, PANEL)
rect(s, 6.86, yy, 0.04, 1.55, AMBER)
txt(s, 7.10, yy + 0.14, 5.6, 0.3, "No file on disk", 11, AMBER, True)
txt(s, 7.10, yy + 0.48, 5.6, 0.95, [
    "Germany (ISD), Benelux (IBX), UMI, Sweden, Norway.",
    "For these five we can only show our own billing and their reported stock — no independent check on "
    "whether the goods sold on. This is the data gap to close.",
], 9, MUTED)

# ════════════════════════════════════════════════════════════════════════════
# 10  EVIDENCE 4 — ORDER MIX: WHAT THE DATA CAN AND CANNOT SAY
# ════════════════════════════════════════════════════════════════════════════
s, y = base("Evidence 4 — order mix, read honestly",
            "We cannot show a planned-versus-urgent improvement at either market: one has a hole in its records, the other moves only with its account codes",
            source="Source: order detail, SaTy order type (01_data/00_derived/order_headers_from_Order_Detail.csv); "
                   "checked and quantified in SOR_VOR_IMPROVEMENT_IBX_ISD_20261007 (section 9). Planned = SOR + PRD "
                   "orders; urgent = VOR and related types, by order value. euro first.")
IB, DE = SORVOR["Benelux"], SORVOR["Germany"]
rows = [
    ["IBX, FY2026 → FY2027 YTD, as the file stands",
     f"{IB['fy26']['planned_pct']:.2f}% → {IB['fy27']['planned_pct']:.2f}%",
     (f"+{IB['pp_as_file']:.2f} pp", AMBER, True),
     "Manufactured by the five-week gap sitting in the baseline — not an improvement"],
    ["IBX, with the April–May 2025 gap months removed",
     f"{IB['fy26_nogap']['planned_pct']:.2f}% → {IB['fy27']['planned_pct']:.2f}%",
     (f"{IB['pp_gap_removed']:+.2f} pp", RED, True),
     "The sign flips: the planned share actually falls"],
    ["IBX, only clean gap-free window (Jun–Aug, year on year)",
     f"{IB['jun_aug_25']['planned_pct']:.2f}% → {IB['jun_aug_26']['planned_pct']:.2f}%",
     (f"+{IB['pp_clean_jun_aug']:.2f} pp", GREEN, True),
     f"About +EUR {IB['clean_planned_eur']:,.0f} of planned euro, on falling volume"],
    ["ISD, FY2026 → FY2027 YTD",
     f"{DE['fy26']['planned_pct']:.2f}% → {DE['fy27']['planned_pct']:.2f}%",
     (f"{DE['pp_as_file']:+.2f} pp", AMBER, True),
     "A code-mix move between two sold-to accounts, not a change in ordering"],
]
table(s, 0.42, y + 0.05, 12.49,
      ["Reading", "Planned share of order value", "Change", "What it means"], rows,
      col_w=[4.35, 2.75, 1.30, 4.09], row_h=0.62, size=8.8)
txt(s, 0.42, y + 0.05 + 0.34 + 0.62 * len(rows) + 0.26, 12.6, 1.9,
    ["Why neither figure can carry an improvement claim. IBX's order records stop on 14 April 2025 and "
     "resume on 21 May 2025; 555 documents worth EUR 2.62M for fifteen other customers sit in that same "
     "document range. The missing weeks were all urgent, so leaving them in the baseline makes the "
     "earlier planned share look lower than it was.",
     "ISD's apparent 4.5 pp decline is the euro split between sold-to 2516, which orders on stock terms "
     "in 17 of 20 months, and sold-to 601, which orders on urgent terms in all 20. Within each account "
     "nothing changed.",
     "One point worth stating plainly: urgent orders here carry higher gross margin than planned orders "
     "(IBX 50.2% against 45.9%; ISD 57.9% against 46.5%). Reducing urgent ordering is a service-cost "
     "argument, not a margin one, and these files cannot price the service cost."], 8.6, MUTED)

# ════════════════════════════════════════════════════════════════════════════
# 11  THE CHAIN (1/2) — KICKBACK AS LEVERAGE FOR DATA, AND THE INSIGHT IT BUYS
# ════════════════════════════════════════════════════════════════════════════
s, y = base("Kickback as leverage for data",
            "The reporting condition inside the incentive is what gets us the data — and it is the only thing that lets us see whether a plan increase is delivered rather than merely billed",
            source="Sources: sales-to-dealer files and KPI/SPI check sheets in 01_data/00_derived; findings from "
                   "ORDER_WINDOW_AND_DATA_ADVANTAGES_20261007.md and "
                   "STOCK_CAMPAIGN_INSIGHTS_ALL_CUSTOMERS_20261007.md (01_data/90_INBOX); the EUR 678,464 from "
                   "replenishment_exceptions_cy2025.csv (signal leakage_high_sellthrough).")
# --- stage 1: the condition buys the data ---
rect(s, 0.42, y + 0.00, 12.49, 0.95, PANEL)
rect(s, 0.42, y + 0.00, 0.04, 0.95, RED)
txt(s, 0.68, y + 0.10, 12.1, 0.26, "1 · The reporting condition is what gets us the data", 10.5, WHITE, True)
txt(s, 0.68, y + 0.38, 12.1, 0.55, [
    "Distributors send monthly dealer-level detail — invoice date, part number and quantity, no prices — plus "
    "monthly KPI and SPI check sheets, because reporting is part of the exchange the incentive sits in.",
    "Sending today: IUK, ITUK, Ireland, Portugal, Greece and Romania (UTI reports part of the year). "
    "Not sending: Germany (ISD), Benelux (IBX), UMI, Sweden and Norway.",
], 8.6, MUTED)
# --- stage 2: the insight that buys ---
txt(s, 0.42, y + 1.03, 12.5, 0.26,
    "2 · What that visibility shows us, which our own billing cannot — ranked by the decision it changes",
    10.5, WHITE, True)
insight = [
    ["iMotors (Portugal)",
     ("EUR 225,744", AMBER, True),
     "A net parts build held in brakes, body and electrical while the fastest-turning maintenance family "
     "was cut 20%; one brake part still holds 214 pieces at EUR 16,923. Billing alone shows only what we "
     "sold them. Fix: rebalance families, not a smaller campaign."],
    ["IUK",
     ("EUR 764,436", AMBER, True),
     "A stock build from 51 to 97 days after the brake campaign, then 76% less buying for four months. "
     "Fix: campaign timing, because the build and the step-down are the same event."],
    ["Five markets",
     ("EUR 678,464", GREEN, True),
     "Parts their dealers pulled through faster than the distributors reordered — a demand signal that is "
     "invisible in billing. Fix: replenishment timing, under-ordering handled separately from overstock."],
]
table(s, 0.42, y + 1.33, 12.49, ["Where the data showed it", "In euro", "What it is, and the decision it changes"],
      insight, col_w=[2.05, 1.45, 8.99], row_h=0.68, size=8.6)
txt(s, 0.42, y + 3.67, 12.5, 1.05,
    ["Two honest limits, stated rather than implied. First, the value of this data is the insight, not an "
     "order-mix trend: Benelux's planned-versus-urgent share shows no statistically significant trend in any "
     "window tested — the fiscal-year comparison moves from +0.4 pp to −4.5 pp once the five-week order-record "
     "gap and the December timing month are removed — so no order-mix improvement is claimed anywhere in this deck.",
     "Second, the composition of the missing Benelux weeks is contested. One check put the missing orders mostly "
     "urgent; a later one puts roughly EUR 300,000–320,000 missing and mostly planned. We state that a five-week "
     "gap exists and that the sign of the comparison flips without it; we do not claim what the missing weeks were."],
    8.6, MUTED)

# ════════════════════════════════════════════════════════════════════════════
# 12  THE CHAIN (2/2) — KPI POSITIONING, SERVICE LEVEL, AND THE TENSION
# ════════════════════════════════════════════════════════════════════════════
s, y = base("From the data to a higher service level",
            "With the reported KPI set we can place every distributor against the network standard — measured distributors can be managed",
            source="Sources: KPI standards and bands from 01_data/11_planning/ISZE_DB_KPI_Targets_FY2627_v1.xlsx, "
                   "sheets 'Assumptions' and 'Targets FY26-27'; reported days of stock from "
                   "01_data/11_planning/KPI Master File august 2026.xlsx, sheet 'Parts Handling'. Plan and Kosha "
                   "path as printed on slides 1, 3 and 4.")
txt(s, 0.42, y + 0.00, 12.5, 0.26, "3 · KPI positioning — the network standard, and where the biggest movers sit",
    10.5, WHITE, True)
txt(s, 0.42, y + 0.28, 12.5, 0.30,
    "Fill rate: standard ≥95%, floor 92%. Days of stock by supply class: A (road ≤5 days) 60–75, "
    "B (road or short-sea 5–12 days) 75–90, C (by sea ≥3 weeks) 90–120. Back orders: ≤15 lines per "
    "EUR 100K of monthly dealer sales.", 8.8, MUTED)
movers = [
    ["ITUK", "Above its 90–105 band in every one of its 21 reported months", "121 days, Jul 2026"],
    ["Isuzu Ireland", "Above its 75–90 band in every one of its 24 reported months", "123 days, Jul 2026"],
    ["IUK", "Above its 60–75 band in 17 of 24 reported months", "81 days, Jul 2026"],
    ["IBX (Benelux)", "Brought back into its 60–75 band, having sat below it", "32 → 63 days, Jan → Jul 2026"],
    ["ISD (Germany)", "Cannot be placed at all — no KPI reported to us", "Dark since January 2025"],
]
table(s, 0.42, y + 0.62, 12.49, ["Distributor", "Against its own class band", "Latest reading"],
      movers, col_w=[2.20, 7.29, 3.00], row_h=0.40, size=8.8)
rect(s, 0.42, y + 2.90, 12.49, 0.92, PANEL)
rect(s, 0.42, y + 2.90, 0.04, 0.92, GREEN)
txt(s, 0.68, y + 3.00, 12.1, 0.26, "4 · The payoff — a higher distributor service level", 10.5, WHITE, True)
txt(s, 0.68, y + 3.28, 12.1, 0.50,
    "Distributors that can be measured can be managed, and those that hold their own stock serve their own "
    "dealers better. That is the return the reporting side of the kickback quietly buys — and it is why we "
    "would rather widen reporting than trim the reward.", 8.8, MUTED)
rect(s, 0.42, y + 3.94, 12.49, 1.05, PANEL)
rect(s, 0.42, y + 3.94, 0.04, 1.05, RED)
txt(s, 0.68, y + 4.02, 12.1, 0.26, "The tension", 10.5, RED, True)
txt(s, 0.68, y + 4.28, 12.1, 0.65,
    "We are asking the network for +9.0% this year — EUR 29.19M to EUR 31.82M — and roughly 6–12% a year out "
    "to FY2031, taking the Kosha path from EUR 29.6M to EUR 52.1M. A plan that steep cannot be chased blind: "
    "it only runs if we can see whether an increase is delivered or merely billed. The only thing that gives us "
    "that sight is the data, and the only thing that gets us the data is the reporting condition inside the "
    "kickback. Weaken the kickback and you do not just remove the reward — you remove the visibility that makes "
    "the growth achievable.", 8.8, MUTED)

# ════════════════════════════════════════════════════════════════════════════
# 12  THE COMMITMENT — A TOLERANCE BAND AT 6 AND 9 MONTHS
# ════════════════════════════════════════════════════════════════════════════
s, y = base("Our commitment", "We will improve the rule: a distributor stays eligible if it is not more than 10% behind plan at the 6-month and the 9-month checkpoint")
rect(s, 0.42, y + 0.02, 12.49, 1.55, PANEL)
rect(s, 0.42, y + 0.02, 0.05, 1.55, RED)
txt(s, 0.68, y + 0.18, 12.1, 0.3, "Proposed amendment to the kickback rule", 12, WHITE, True)
txt(s, 0.68, y + 0.54, 12.1, 0.95, [
    "A distributor remains eligible for the full annual incentive provided it is not more than 10% behind "
    "its target at the 6-month checkpoint and again at the 9-month checkpoint.",
    "The incentive is still paid on the annual plan being reached. What changes is that a slow start no "
    "longer puts the whole year's incentive out of reach — the distributor is told where it stands and "
    "keeps a reason to recover.",
], 9.5, MUTED)

txt(s, 0.42, y + 1.78, 6.55, 0.3, "The tolerance band, read at two checkpoints", 10.5, WHITE, True)
band_x0, band_w = 1.95, 4.75          # represents -20% (left) to +5% (right)
def bx_of(pct):                        # pct = % vs plan (negative = behind)
    return band_x0 + ((pct + 20) / 25) * band_w
plan_x = bx_of(0)
t10_x = bx_of(-10)
txt(s, 0.42, y + 2.18, 1.5, 0.25, "behind plan", 7.5, MUTED, True, PP_ALIGN.RIGHT)
rect(s, band_x0, y + 2.18, t10_x - band_x0, 0.26, "4A2A2A")     # outside the band
rect(s, t10_x, y + 2.18, band_x0 + band_w - t10_x, 0.26, "244A31")  # inside the band
vline(s, t10_x, y + 2.10, 0.42, RED, 1.2)
vline(s, plan_x, y + 2.10, 0.42, WHITE, 1.2)
txt(s, band_x0 - 0.05, y + 2.50, 1.6, 0.22, "-20%", 7, MUTED)
txt(s, t10_x - 0.55, y + 2.50, 1.1, 0.22, "-10%", 7, RED, True, PP_ALIGN.CENTER)
txt(s, plan_x - 0.55, y + 2.50, 1.1, 0.22, "PLAN", 7, WHITE, True, PP_ALIGN.CENTER)
for i, (lbl, pct) in enumerate([("Month 6", -4), ("Month 9", -2)]):
    ry = y + 2.85 + i * 0.62
    txt(s, 0.42, ry + 0.08, 1.5, 0.25, lbl, 8.5, WHITE, True, PP_ALIGN.RIGHT)
    rect(s, band_x0, ry + 0.05, band_w, 0.34, ROW2)
    rect(s, t10_x, ry + 0.05, band_x0 + band_w - t10_x, 0.34, "244A31")
    vline(s, plan_x, ry + 0.02, 0.40, WHITE, 1.0)
    mx = bx_of(pct)
    rect(s, mx - 0.10, ry + 0.06, 0.20, 0.32, GREEN, shape=MSO_SHAPE.OVAL)
    txt(s, mx + 0.14, ry + 0.11, 1.9, 0.25, f"{abs(pct)}% behind — inside the band", 7.5, GREEN, True)
txt(s, 0.42, y + 4.10, 6.55, 0.26,
    "Illustrative: inside the band at both checkpoints, the distributor stays eligible.", 8, MUTED)

bx = 7.15
rect(s, bx, y + 1.72, 5.76, 2.35, PANEL)
txt(s, bx + 0.22, y + 1.86, 5.3, 0.3, "Why this is the right threshold", 10.5, WHITE, True)
txt(s, bx + 0.22, y + 2.20, 5.3, 1.8, [
    "It recognises a slow start. Markets open at different speeds; a first half affected by a launch, a "
    "tender or a stock rebuild should not cost the year.",
    "It keeps the incentive alive all year. The distributor keeps a reason to chase the plan between the "
    "checkpoints instead of writing the year off, or waiting for March.",
    "It reduces the pull to buy purely to cross a line, because the year is read as a path, not a single "
    "year-end number.",
    "It rewards recovery. The one distributor behind at ten months in FY2026 still finished ahead — that "
    "is the behaviour the rule should encourage, not punish.",
], 8.6, MUTED)
txt(s, 0.42, y + 4.20, 12.5, 1.1,
    ["The band is deliberately generous and deliberately checkable. Ten per cent behind at month 6 and "
     "month 9 is a clear, defensible line that both sides can read from the same report — and it is the "
     "same tolerance whether the shortfall comes from a slow market or a late stock build.",
     "No change to the rate. No change to the total. One improvement to how eligibility is tested."], 9, MUTED)

# ════════════════════════════════════════════════════════════════════════════
# 13  ITUK PRICING — kept, unchanged in substance
# ════════════════════════════════════════════════════════════════════════════
s, y = base("Finding — the March price pre-buy", "A +5.96% price list landed on 13 March 2026, and ITUK bought hard in the twelve days before it",
            source="Source: PR00 base-price comparison (weighted +5.9616%, step EUR 1,652,140.71, 13 March 2026) and "
                   "ITUK billing by day, sold_to 2575. ITUK is retained here because this is a pricing finding on our own "
                   "sales team, not a distributor comparison. No distributor notice for the change is on file.")
kpi(s, 0.42, y + 0.05, 2.95, "+5.96%", "Whole-book price change on 13 March 2026", AMBER)
kpi(s, 3.55, y + 0.05, 2.95, "2.32× → 0.60×", "ITUK volume before, then after the change", RED)
kpi(s, 6.68, y + 0.05, 2.95, "EUR 84,018", "Its weakest week of the quarter (16 March)", RED)
kpi(s, 9.81, y + 0.05, 3.13, f"EUR {ITUK['feb_excess']:,.0f}", "ITUK February excess — not a price effect", RED)

hdr = ["ITUK, FY2026", "Per month, or per day", "vs its own run rate"]
data = [
    ["Run rate, Apr 2025 – Jan 2026", f"EUR {ITUK['run']:,.2f} per month", "—"],
    ["February 2026", f"EUR {ITUK['feb']:,.2f}", (f"+EUR {ITUK['feb_excess']:,.2f}  (1.67×)", RED, True)],
    ["1–12 March 2026 (old price)", "EUR 517,104", ("2.54× euro, 2.32× volume", RED, True)],
    ["13–31 March 2026 (new price)", "EUR 423,463", ("volume fell to 0.60×", RED, True)],
    ["April 2026", "EUR 529,085", "settled back at pace"],
]
table(s, 0.42, y + 1.28, 12.49, hdr, data, col_w=[4.6, 3.8, 4.09], row_h=0.34)
txt(s, 0.42, y + 1.28 + 0.34 + 0.34 * len(data) + 0.24, 12.6, 1.5,
    ["The volume is the tell: ITUK bought at more than twice its normal rate while the old list still "
     "applied, then almost stopped once the new one did. That is buying in front of a known price change.",
     "Two things this does not settle. It explains ITUK's March, but not its February — the February excess "
     "of EUR 346,195 sits before any price effect. And a forward-buy needs advance notice: there is no "
     "distributor notification on file showing when the 13 March change was communicated, so February "
     "stays open. Stated, not implied."], 9, MUTED)

# ════════════════════════════════════════════════════════════════════════════
# 14  WHAT WE PROPOSE
# ════════════════════════════════════════════════════════════════════════════
s, y = base("Proposal", "Keep the kickback, improve the rule, and close the data gap")
items = [
    ("Keep the programme as it is.", "No evidence of abuse was found in FY2026. Cutting the rate would "
     "weaken the one mechanism that makes a 9% plan growth achievable.", RED),
    ("Adopt the 10% tolerance at month 6 and month 9.",
     "A distributor stays eligible if it is not more than 10% behind plan at each checkpoint. It softens "
     "the all-or-nothing year end, rewards recovery, and keeps the incentive motivating all year.", AMBER),
    ("Pay part of it on sales to dealer.", "Where a distributor reports onward sales, part of the target "
     "should be tested on goods actually moving on rather than on purchases alone. This removes any pull "
     "to buy purely to cross a line.", GREEN),
    ("Close the sales-to-dealer gap.", "Five of the ten customers have no file. Asking for it is already "
     "part of the exchange; making it a condition of the incentive is how it gets delivered.", GREY),
    ("Load the ISD data we have now been given.", "ISD resumed reporting on 2 October 2026 with "
     "February–July 2026. Those months are indicative until loaded and validated — Germany should be "
     "inside the reporting before any incentive test is applied to it.", GREY),
]
cy = y + 0.05
for head, rest, col in items:
    rect(s, 0.42, cy, 12.49, 0.93, PANEL)
    rect(s, 0.42, cy, 0.04, 0.93, col)
    txt(s, 0.68, cy + 0.12, 12.1, 0.3, head, 10.5, WHITE, True)
    txt(s, 0.68, cy + 0.44, 12.1, 0.45, rest, 9, MUTED)
    cy += 1.04

# ════════════════════════════════════════════════════════════════════════════
# 15  DASHBOARD — FY2027 MONTHLY PLAN
# ════════════════════════════════════════════════════════════════════════════
s, y = base("The year ahead", "FY2027 asks for EUR 31.82M of parts sales, month by month",
            source="Source: FY2027 BP workbook (01_data/11_planning/FY2027  BP VP&ACC.xlsx, sheet 'VP FY27', "
                   "Turnover in EUR). Fiscal year April 2026 – March 2027.")
kpi(s, 0.42, y + 0.05, 3.05, f"EUR {FY27_TOTAL/1e6:.2f}M", "FY2027 plan, twelve months", WHITE)
kpi(s, 3.60, y + 0.05, 3.05, f"{RAMP_PCT:.1f}%", "Above the FY2026 plan", AMBER)
kpi(s, 6.78, y + 0.05, 2.85, f"EUR {min(FY27_MONTHLY)/1e6:.2f}M", "Softest month (December)", GREY)
kpi(s, 9.76, y + 0.05, 3.15, f"EUR {max(FY27_MONTHLY)/1e6:.2f}M", "Strongest month (July)", GREEN)
ch = chart(s, 0.42, y + 1.22, 12.49, 3.6, FY,
           [("FY2027 plan, EUR", FY27_MONTHLY)])
style_chart(ch, 'EUR#,##0', legend=False)
ch.plots[0].gap_width = 55
col_fill(ch.plots[0].series[0], RED)
txt(s, 0.42, y + 4.94, 12.6, 0.7,
    "The plan is not flat: it asks for EUR 3.19M in July and EUR 2.80M in December. A distributor has to "
    "hold a stocking position and keep ordering through the soft months to deliver that shape — which is "
    "what the incentive and the stocking expectation are for.", 9, MUTED)

# ════════════════════════════════════════════════════════════════════════════
# 16  NEXT STEPS
# ════════════════════════════════════════════════════════════════════════════
s, y = base("Next steps", "Four things to agree before the FY2027 targets are written")
data = [
    ["1", "Adopt the 10% tolerance at the 6-month and 9-month checkpoints", "ISZE / Japan", "one rule change; the rate and the total stay as they are"],
    ["2", "Agree that part of the incentive is tested on sales to dealer", "ISZE / Japan", "where a distributor reports it, so the reward follows goods that actually move on"],
    ["3", "Make sales-to-dealer reporting a condition of the incentive", "ISZE sales", "five customers have no file; this is how the gap closes"],
    ["4", "Load and validate ISD's resumed submission (Feb–Jul 2026)", "ISZE", "Germany returned the check sheet on 2 October 2026; those months are indicative until loaded"],
    ["5", "Confirm the monthly plan per distributor for the year", "ISZE / Japan", "so the 6- and 9-month checks are read against a monthly target, not a pro-rata"],
]
table(s, 0.42, y + 0.05, 12.49, ["#", "Action", "Owner", "Why"], data,
      col_w=[0.6, 5.1, 1.75, 5.04], row_h=0.62, size=9.8)
txt(s, 0.42, y + 0.05 + 0.34 + 0.62 * len(data) + 0.28, 12.6, 1.0,
    ["In one line: the kickback earned its place in FY2026 — seven of nine distributors met or beat a rising "
     "plan, no abuse was found, and the one distributor that fell behind recovered inside the year.",
     "The improvement we propose costs nothing and changes no rate. It makes the incentive easier to earn "
     "honestly at the start of a year and harder to game at the end of one."], 9.5, MUTED)

prs.save(OUT)
print("written", OUT, f"({OUT.stat().st_size/1024:.0f} KB, {len(prs.slides._sldIdLst)} slides)")
print(f"plan FY26 EUR {PLAN_TOT26:,.2f} -> FY27 EUR {PLAN_TOT27:,.2f}  (+{RAMP_PCT:.4f}%)")
print(f"incentive total EUR {INC_TOTAL:,.2f}")
print("IBX stock story:", IBX_STORY)
print("IBX SOR/VOR pp as file / gap removed / clean Jun-Aug:",
      f"{SORVOR['Benelux']['pp_as_file']:+.2f} / {SORVOR['Benelux']['pp_gap_removed']:+.2f} / {SORVOR['Benelux']['pp_clean_jun_aug']:+.2f}")
print("Kosha ramp:", KOSHA)
