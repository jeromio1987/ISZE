"""Pricing grid draft on a NEW copy of the +5% proposal (brief 2026-10-11_P1_pricing_grid).

Package A is a faithful copy of build_market_layer_20261004.py: at paper settings it reproduces
EUR 1,629,793 total / given-up 388,914 / ceiling cut 7,654 / recovered 396,568 / extra 3.727 OFF / 4.837 ON.
Packages B-H add, in the new workbook only: hold switches for filters and for intake, exhaust and emission
parts; the stance sheets by price basis (PR00, ZPR1, CIS); the twelve-cell grid of extras by stance and
parts role with one solved base; a reason code on every part x market line; a margin and volume view;
a test design sheet; and the label fixes plus a repair rules note.

Never writes the live workbook, the policy paper, config.yaml, the price ledger or 07_deploy.

Run:  python build_pricing_grid_20261011.py
Then: python recalc_excel.py <staged workbook>
      python verify_pricing_grid_20261011.py <staged workbook>
"""
import json
import os
import re
import shutil
import sys
import tempfile
import time
from pathlib import Path

import numpy as np
import pandas as pd
from openpyxl import load_workbook
from openpyxl.formatting.rule import CellIsRule
from openpyxl.styles import Alignment, Border, Font, PatternFill, Side
from openpyxl.utils import get_column_letter
from openpyxl.workbook.defined_name import DefinedName
from openpyxl.worksheet.datavalidation import DataValidation

HERE = Path(__file__).resolve().parent
ISZE = Path(r"C:\Users\jerom\Desktop\claude\ISZE")
sys.path.insert(0, str(HERE))
from evidence_lib import load_base  # noqa: E402

LIVE = ISZE / "01_data" / "01_Pricing" / "Price_Increase_5pct_Proposal_2026-09-29.xlsx"
STAGE = HERE / "stage_grid_2026-10-11"
OUT = Path(os.environ.get("PROPOSAL_OUT", STAGE / "Price_Increase_5pct_Proposal_GRID_DRAFT_2026-10-11.xlsx"))
RR = HERE / "room_to_raise_2026-10-02"
DERIVED = ISZE / "01_data" / "00_derived"
PRICING = ISZE / "01_data" / "01_Pricing"
DEALER_SALES = ISZE / "01_data" / "12_raw" / "dealer_sales"
AIM_RELEASE = DERIVED / "_releases" / "aim_pn_classification_release_2026-10-07.csv"
ROLE_CSV = PRICING / "aim_category_target_gm_20261007.csv"
CARPARK = DERIVED / "UIO_carpark_for_GPS_recalc_2026-07-30.csv"   # market_facts.py points at a 02_dashboards path that does not exist
GPS_SPU = DERIVED / "gps_spu_by_distributor.csv"
DEC = json.loads((HERE / "market_exercise_decisions_2026-09-30.json").read_text(encoding="utf-8"))
PUB = json.loads((RR / "room_to_raise_variant_B_iuk_exempt_2026-10-02.json").read_text(encoding="utf-8"))
PSUM = json.loads((HERE / "price_5pct_proposal_summary_2026-09-29.json").read_text(encoding="utf-8"))
FACTS = json.loads((HERE / "market_facts_2026-09-30.json").read_text(encoding="utf-8"))

EXPECT = {"parts": 15273, "pm_rows": 45581, "billed": 32595852.63, "lines": 47617, "pad_kits": 29}
CIS = ["ARMENIA", "KAZAKHSTAN"]
EXEMPT = "IUK"
ISR_TRUCKS = "UTI"
CEILING_PTS = 0.05
SEED = 20261011
TEST_MARKETS = [m.strip().upper() for m in os.environ.get("TEST_MARKETS", "ITUK,IRELAND,PORTUGAL").split(",")]
SCRAPPAGE = {"CV": 0.102, "LCV": 0.123}        # the constant-hazard rates behind the 2026 carpark column

REASON = {"service hold (market exercise)": "Service parts held at today's price",
          "UMI body/collision hold": "Body and collision parts held at today's price (Israel D-Max distributor)",
          "UMI lighting hold": "Lighting held at today's price (Israel D-Max distributor)",
          "UTI lighting hold": "Lighting held at today's price (Israel trucks distributor)"}
R_SERVICE = REASON["service hold (market exercise)"]
NAMES = {"ITUK": "UK trucks distributor (ITUK)", "IUK": "Isuzu UK, D-Max (IUK)", "UTI": "Israel trucks distributor (UTI)",
         "UMI": "Israel D-Max distributor (UMI)", "PALESTINE": "Palestine (KIMA, customer 2372)"}

# roles, in the order they sit on the grid
ROLES = ["wear_pms", "captive", "commercial", "body_legal"]
ROLE_LABEL = {"wear_pms": "Wear and service parts", "captive": "Captive parts", "commercial": "Commercial parts",
              "body_legal": "Body and legal parts"}
ROLE_CODE = {"wear_pms": "WEAR_PMS", "captive": "CAPTIVE", "commercial": "COMMERCIAL", "body_legal": "BODY_LEGAL"}
STANCES = ["Keep today's price", "Follow factory increase", "Raise more"]
STANCE_CODE = {1: "KEEP", 2: "FOLLOW", 3: "RAISE"}

# =================================================================== data
t0 = time.time()
ins = load_base()
L = ins[ins.movable].copy()
assert len(L) == EXPECT["lines"], len(L)
dd = pd.read_csv(DERIVED / "distributor_dimension.csv", dtype=str)
L["db"] = L.customer_code.astype(str).map(dict(zip(dd.sold_to_sap, dd.distributor_code)))
assert L.db.notna().all()
pm = L.groupby(["pn", "db"], as_index=False).net_sales_value.sum().rename(columns={"net_sales_value": "billed"})
pm["billed"] = pm.billed.round(2)
csv_pm = pd.read_csv(RR / "room_to_raise_by_part_market_2026-10-02.csv", dtype={"pn": str}, usecols=["pn", "db", "billed_eur", "hold_reason"])
pm = pm.merge(csv_pm, on=["pn", "db"], how="left", validate="1:1")
assert pm.billed_eur.notna().all() and len(pm) == EXPECT["pm_rows"], len(pm)
assert abs(pm.billed.sum() - EXPECT["billed"]) < 0.005, pm.billed.sum()
assert (pm.billed - pm.billed_eur).abs().max() <= 0.5 + 1e-9          # the CSV keeps 6 significant digits only
pm["reason"] = pm.hold_reason.fillna("").map(lambda x: REASON.get(x, x))
assert set(pm.reason.unique()) <= set(REASON.values()) | {""}
pm = pm.sort_values(["pn", "db"], kind="stable").reset_index(drop=True)

live_p = pd.read_excel(LIVE, sheet_name="Proposal", dtype={"Part number": str},
                       usecols=["Part number", "Description", "Billed EUR (Jul 25-Jun 26)", "Proposed move", "Factory move", "Class margin"])
live_p["pn"] = live_p["Part number"].astype(str)
assert len(live_p) == EXPECT["parts"] and live_p.pn.is_unique
bp = pd.read_csv(RR / "room_to_raise_by_part_2026-10-02.csv", dtype={"pn": str},
                 usecols=["pn", "segment", "captive_strict", "lubricant", "padkit"], low_memory=False)
bp = bp.set_index("pn")
parts = pd.DataFrame({"pn": live_p.pn.to_numpy(), "desc": live_p.Description.fillna("").astype(str).to_numpy()})
for c in ["segment", "captive_strict", "lubricant", "padkit"]:
    parts[c] = parts.pn.map(bp[c])
assert parts.segment.notna().all()
assert set(parts.segment.unique()) == {"service", "repair", "body"}
assert int(parts.padkit.sum()) == EXPECT["pad_kits"]
assert set(pm.pn) == set(parts.pn)
parts = parts.sort_values("pn", kind="stable").reset_index(drop=True)

# ---------------------------------------------------------------- parts categories (B + D)
zpad = lambda s: s.astype(str).str.replace(r"\.0$", "", regex=True).str.zfill(10)
aim = pd.read_csv(AIM_RELEASE, dtype=str, usecols=["part_number", "aim_l1_fixed", "aim_l2_fixed", "aim_l3_fixed"])
aim["pn"] = zpad(aim.part_number)
aim = aim.drop_duplicates("pn").set_index("pn")
for c in ["aim_l1_fixed", "aim_l2_fixed", "aim_l3_fixed"]:
    parts[c] = parts.pn.map(aim[c]).fillna("")
n_no_cat = int((parts.aim_l1_fixed == "").sum())

l2, l3 = parts.aim_l2_fixed.str.lower(), parts.aim_l3_fixed.str.lower()
is_filter = l2.str.contains("filter") | l3.str.contains("filter")
is_exhaust = parts.aim_l1_fixed.eq("Intake Exhaust Emission")
DISC_PAT = r"discs? ?& ?drums?|brake disc|brake drum|brake rotor"
is_disc = l2.str.contains(DISC_PAT, regex=True) | l3.str.contains(DISC_PAT, regex=True)
assert not (is_filter & is_exhaust).any() and not (is_filter & is_disc).any() and not (is_exhaust & is_disc).any()
# 0 = nothing special, 1 = filter, 2 = intake/exhaust/emission, 3 = brake disc or drum
parts["hk"] = np.select([is_disc, is_filter, is_exhaust], [3, 1, 2], default=0).astype(int)

roles = pd.read_csv(ROLE_CSV, usecols=["aim_level_1", "pricing_role", "status_note", "use_mode"])
role_of = dict(zip(roles.aim_level_1, roles.pricing_role))
ROLE_STATUS = str(roles.use_mode.iloc[0])
parts["role_raw"] = parts.aim_l1_fixed.map(role_of).fillna("unclassified")
unmatched_cats = sorted(set(parts.aim_l1_fixed[parts.role_raw.eq("unclassified") & ~parts.aim_l1_fixed.isin(roles.aim_level_1)]))
# unclassified follows commercial, and is listed as such
parts["ridx"] = parts.role_raw.map(lambda r: ROLES.index(r) + 1 if r in ROLES else ROLES.index("commercial") + 1)
parts["role_label"] = parts.role_raw.map(lambda r: ROLE_LABEL.get(r, "Not classified (follows commercial parts)"))

pm["hk"] = pm.pn.map(dict(zip(parts.pn, parts.hk)))
pm["base_move"] = pm.pn.map(dict(zip(live_p.pn, live_p["Proposed move"])))
held_now = pm.reason.ne("")
given_by = {}
for key, mask in (("filters", pm.hk.eq(1) & pm.reason.eq(R_SERVICE)),
                  ("exhaust", pm.hk.eq(2) & pm.reason.eq(R_SERVICE)),
                  ("discs", pm.hk.eq(3) & pm.reason.eq(R_SERVICE)),
                  ("other_service", pm.hk.eq(0) & pm.reason.eq(R_SERVICE)),
                  ("israel", held_now & pm.reason.ne(R_SERVICE))):
    given_by[key] = float((pm.billed * pm.base_move)[mask].sum())
print("hold composition at paper settings, EUR given up: " + ", ".join(f"{k} {v:,.0f}" for k, v in given_by.items()))
print(f"  parts with no row in the 7 Oct parts-category release: {n_no_cat}")
if unmatched_cats:
    print(f"  parts categories with no role in {ROLE_CSV.name}: {unmatched_cats}")

# pointers: part rows sit contiguously in the part x market list (both sorted by part number)
PM_FIRST, LP_FIRST = 5, 5
grp = pm.groupby("pn", sort=False).size()
first_idx = pm.reset_index().groupby("pn", sort=False)["index"].min()
assert (parts.pn.to_numpy() == grp.index.to_numpy()).all()
parts["first"] = (first_idx.reindex(parts.pn).to_numpy() + PM_FIRST).astype(int)
parts["nrows"] = grp.reindex(parts.pn).to_numpy().astype(int)
NP, NM = len(parts), len(pm)
LP_LAST, PM_LAST = LP_FIRST + NP - 1, PM_FIRST + NM - 1
markets = pm.groupby("db").billed.sum().sort_values(ascending=False).index.tolist()
assert len(markets) == 22 and set(CIS) <= set(markets) and EXEMPT in markets
MKT_I = {m: i + 1 for i, m in enumerate(markets)}
pm["mkt_i"] = pm.db.map(MKT_I)
print(f"data ready in {time.time() - t0:.0f}s: {NP} parts, {NM} part x market rows, {len(markets)} markets")

# decided treatment, from the decisions file (service) and the 2 Oct paper (Israel body/lighting)
held_service = sorted(k for k, v in DEC["decisions"].items() if v["service"].startswith("hold"))
assert held_service == ["BELGIUM", "CYPRUS", "GERMANY", "HUNGARY", "IUK", "MALTA", "NORWAY", "UMI"], held_service
for mkt in markets:      # the matrix below is data-checked against the hold flags
    rs = set(pm.reason[(pm.db == mkt) & (pm.reason != "")])
    exp_rs = set()
    if mkt in held_service:
        exp_rs.add(R_SERVICE)
    if mkt == "UMI":
        exp_rs |= {REASON["UMI body/collision hold"], REASON["UMI lighting hold"]}
    if mkt == "UTI":
        exp_rs.add(REASON["UTI lighting hold"])
    assert rs == exp_rs, (mkt, rs, exp_rs)

# =================================================================== package C: the facts behind the stance sheets
DB_TO_CODE = {"UTI": "UTI", "UMI": "UMI", "ITUK": "ITUK", "IUK": "IUK", "BL": "ICELAND", "RSA": "NORWAY",
              "Isuzu Sverige": "SWEDEN", "Isuzu Denmark": "DENMARK", "Isuzu Ireland": "IRELAND", "IBX": "BELGIUM",
              "ISD-Lang": "GERMANY", "Imotors": "PORTUGAL", "GasanZammit": "MALTA", "Nordic Auto.": "FINLAND",
              "AutoWallis": "HUNGARY", "Petros Petropoulos": "GREECE", "Isuzu Rom Auto": "ROMANIA",
              "Loutsios & Sons": "CYPRUS"}
cp = pd.read_csv(CARPARK)
cp["code"] = cp.distributor_DB.map(DB_TO_CODE)
cp_unmapped = sorted(set(cp.distributor_DB[cp.code.isna()]))
cpk = cp.dropna(subset=["code"])
f25c = cpk.groupby("code").uio_CY2025_unchanged.sum()
f26c = cpk.groupby("code").uio_CY2026_corrected.sum()
cp_status = cpk[cpk.uio_CY2025_unchanged > 0].groupby("code").status.agg(lambda s: ", ".join(sorted(set(s.dropna()))))
cp_countries = cpk.groupby("code").country.agg(lambda s: ", ".join(sorted(set(s))))
gps = pd.read_csv(GPS_SPU)
fleet_paper = gps.pivot_table(index="distributor_code", columns="year", values="uio_units")
scope_of = dict(zip(dd.distributor_code.dropna(), dd.scope))

# registrations pace read off the 3rd party meeting deck, Jan-May 2026 (indicative, chart labels)
PACE = {"SWEDEN": {"jan_may": 650, "year": 1550, "note": "Swedish market 1,945 Jan-May x 33.3% share"},
        "NORWAY": {"jan_may": 136, "year": 330, "note": "Norwegian market 1,173 Jan-May x 11.6% share"}}
PACE_SOURCE = "Read from the chart labels of the third-party meeting deck of 29 June 2026, pages 14 and 15 (data to May 2026). Indicative."

BASIS = {}
for m in markets:
    if m in ("UMI", "UTI", "PALESTINE"):
        BASIS[m] = "ZPR1"
    elif m in CIS:
        BASIS[m] = "CIS"
    else:
        BASIS[m] = "PR00"

RAISE_MORE_B = ["ITUK", "UTI", "GREECE", "ROMANIA", "DENMARK"]
DIRECTION_BAND = 0.03
stance_facts = {}
for m in markets:
    k = FACTS["markets"].get(m, {})
    ss = k.get("service_share", {})
    f25p = fleet_paper.loc[m, 2025] if m in fleet_paper.index and 2025 in fleet_paper else None
    f23p = fleet_paper.loc[m, 2023] if m in fleet_paper.index and 2023 in fleet_paper else None
    f24p = fleet_paper.loc[m, 2024] if m in fleet_paper.index and 2024 in fleet_paper else None
    c25, c26 = f25c.get(m), f26c.get(m)
    lfl = (c26 / c25 - 1) if (c25 and c25 > 0 and c26) else None
    paper_chg = (c26 / f25p - 1) if (f25p and f25p > 0 and c26) else None
    pace = PACE.get(m)
    scrap = SCRAPPAGE.get(scope_of.get(m, "LCV"), SCRAPPAGE["LCV"])
    f26_pace = (c25 * (1 - scrap) + pace["year"]) if (pace and c25) else None
    pace_chg = (f26_pace / c25 - 1) if (f26_pace and c25) else None
    svc25 = ss.get("2025", {}).get("total")
    svc23 = ss.get("2023", {}).get("total")
    direction = ("growing" if lfl > DIRECTION_BAND else "shrinking" if lfl < -DIRECTION_BAND else "flat") if lfl is not None else ""
    dr = k.get("dealer_response")
    sa = "Keep today's price" if m in held_service else "Follow factory increase"
    adds_b = (lfl is not None and lfl < -DIRECTION_BAND and svc25 is not None and svc25 < 0.28 and m not in held_service)
    sb = "Raise more" if m in RAISE_MORE_B else ("Keep today's price" if (m in held_service or adds_b) else "Follow factory increase")
    stance_facts[m] = {
        "billed25": (k.get("billed") or {}).get("2025"), "f23p": f23p, "f24p": f24p, "f25p": f25p,
        "c25": c25, "c26": c26, "lfl": lfl, "paper_chg": paper_chg, "status": cp_status.get(m),
        "svc25": svc25, "svc_chg": (svc25 - svc23) if (svc25 is not None and svc23 is not None) else None,
        "pays": k.get("pays_pct_list_all"), "beta": dr["beta"] if dr else None, "beta_se": dr["se"] if dr else None,
        "pace": pace["year"] if pace else None, "pace_jm": pace["jan_may"] if pace else None,
        "pace_note": pace["note"] if pace else None, "f26_pace": f26_pace, "pace_chg": pace_chg,
        "direction": direction, "sa": sa, "sb": sb, "adds_b": adds_b, "countries": cp_countries.get(m, ""),
        "scrap": scrap if pace else None}
B_ADDS = [m for m in markets if stance_facts[m]["adds_b"]]
BORDERLINE = [m for m in markets if stance_facts[m]["lfl"] is not None and -0.05 < stance_facts[m]["lfl"] < -DIRECTION_BAND + 0.02
              and m not in held_service]
print(f"carpark distributors with no ISZE market code (left out): {cp_unmapped}")
print("scenario B 'keep' rule (fleet shrinking below -3% like-for-like AND service share under 28%) adds: "
      + (", ".join(B_ADDS) if B_ADDS else "no market beyond the 8 already holding service parts"))
print("  closest markets to that line: " + (", ".join(f"{m} {stance_facts[m]['lfl']:+.1%}" for m in BORDERLINE) if BORDERLINE
                                            else "SWEDEN -1.6% (flat on the estimate, +6% on the registrations pace)"))

# =================================================================== styles (as the 29 Sep builder)
NAVY, CREAM = "15233C", "F7F4EE"
F = "Arial"
HFILL = PatternFill("solid", fgColor=NAVY)
HFILL_HELP = PatternFill("solid", fgColor="6B7280")
HFONT = Font(name=F, bold=True, color=CREAM, size=10)
TITLE = Font(name=F, bold=True, size=14, color=NAVY)
SUB = Font(name=F, italic=True, size=9, color="555555")
SEC = Font(name=F, bold=True, size=11, color=NAVY)
BODY = Font(name=F, size=10)
BOLD = Font(name=F, size=10, bold=True)
INPUT = Font(name=F, size=10, color="0000FF", bold=True)
DATA = Font(name=F, size=10, color="0000FF")          # imported values: blue, as in modelling convention
LINK = Font(name=F, size=10, color="008000")
YELLOW = PatternFill("solid", fgColor="FFFF00")
PALE = PatternFill("solid", fgColor="F3EFE6")
WRAP = Alignment(wrap_text=True, vertical="top")
PCT1, PCT2, PCT3, EUR0, EUR2 = "0.0%;-0.0%;-", "0.00%;-0.00%;-", "0.000%;-0.000%;-", "#,##0;(#,##0);-", "#,##0.00;(#,##0.00);-"
PTS = "+0.00%;-0.00%;-"
NUM0, NUM2, NUM4 = "#,##0;(#,##0);-", "0.00;(0.00);-", "0.0000;(0.0000);-"
RED = Font(name=F, size=10, bold=True, color="C00000")
GREEN = Font(name=F, size=10, bold=True, color="2E7D32")


def header(ws, row, labels, col=1, height=30, fills=None):
    for i, h in enumerate(labels):
        c = ws.cell(row, col + i, h)
        c.fill = (fills or {}).get(i, HFILL)
        c.font = HFONT
        c.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
    ws.row_dimensions[row].height = height


def put(ws, row, col, value, font=BODY, fmt=None, align=None, fill=None):
    c = ws.cell(row, col, value)
    c.font = font
    if fmt:
        c.number_format = fmt
    if align:
        c.alignment = align
    if fill:
        c.fill = fill
    return c


def note_block(ws, row, lines, width=8, height=28):
    for i, t in enumerate(lines):
        put(ws, row + i, 1, t, SUB, align=WRAP)
        ws.merge_cells(start_row=row + i, start_column=1, end_row=row + i, end_column=width)
        ws.row_dimensions[row + i].height = height
    return row + len(lines)


# =================================================================== open a copy of the live workbook
tmpd = Path(tempfile.mkdtemp(prefix="pricing_grid_"))
src_copy = tmpd / LIVE.name
shutil.copy2(LIVE, src_copy)
wb = load_workbook(src_copy)
assert wb.sheetnames == ["Read me", "Summary", "Proposal", "Review lists", "Dealer response", "Not in proposal", "Checks"], wb.sheetnames
assert len(wb["Dealer response"]._charts) == 1
ws_sum, ws_prop, ws_ck, ws_read, ws_rev = wb["Summary"], wb["Proposal"], wb["Checks"], wb["Read me"], wb["Review lists"]
assert ws_prop.max_row == EXPECT["parts"] + 1
PROP_LAST = ws_prop.max_row                                    # 15274
assert ws_sum["B9"].value == 1 and ws_sum["D5"].value is None

ws_ml = wb.create_sheet("Market layer", index=2)
ws_pr00 = wb.create_sheet("Stance PR00", index=3)
ws_zpr1 = wb.create_sheet("Stance ZPR1", index=4)
ws_cis = wb.create_sheet("Stance CIS", index=5)
ws_gr = wb.create_sheet("Pricing grid", index=6)
ws_pm = wb.create_sheet("Layer by part and market")
ws_lp = wb.create_sheet("Layer by part")
ws_sv = wb.create_sheet("Layer solver")
ws_mv = wb.create_sheet("Margin and volume")
ws_td = wb.create_sheet("Test design")
ws_rr = wb.create_sheet("Repair rules")
for w_ in (ws_ml, ws_pr00, ws_zpr1, ws_cis, ws_gr, ws_lp, ws_pm, ws_sv, ws_mv, ws_td, ws_rr):
    w_.sheet_view.showGridLines = False
ML, LPN, PMN, SVN, GRN = "'Market layer'!", "'Layer by part'!", "'Layer by part and market'!", "'Layer solver'!", "'Pricing grid'!"
STN = {"PR00": "'Stance PR00'!", "ZPR1": "'Stance ZPR1'!", "CIS": "'Stance CIS'!"}

# Named ranges keep the 45,581 formulas on the part x market sheet short: without them the file grows past 30 MB.
NAMED = {}


def named(name, ref):
    NAMED[name] = ref
    return name


SW = named("sw_iuk_exempt", "Summary!$D$5")                  # the Isuzu UK exemption switch

# ---- the switches added on 11 October 2026 (package B), all on the Summary sheet
SUM_SW0 = 74
S1 = named("sw_filters_held", f"Summary!$B${SUM_SW0 + 2}")
S2 = named("sw_exhaust_held", f"Summary!$B${SUM_SW0 + 3}")
SBODY_UTI = named("sw_body_israel_trucks", f"Summary!$B${SUM_SW0 + 5}")
SBODY_IUK = named("sw_body_isuzu_uk", f"Summary!$B${SUM_SW0 + 6}")
SBODY_REST = named("sw_body_other_markets", f"Summary!$B${SUM_SW0 + 7}")
SELIG = named("sw_extra_no_alternative_only", f"Summary!$B${SUM_SW0 + 8}")
SSCEN = named("sw_stance_scenario", f"Summary!$B${SUM_SW0 + 9}")

# column registries (letters come from one place, so formulas cannot drift)
LP_COLS = ["pn", "desc", "cat", "noalt", "lub", "role", "ridx", "hk", "pcode", "list_now", "inc_now", "list_new",
           "own_fact", "own_inc", "padheld", "ceil", "floor", "elig", "room", "mone", "mfac", "free_b", "free_ex",
           "w_off", "w_on", "inc_off", "inc_on", "first", "nrows", "ptr", "prow"]
PM_COLS = ["pn", "mkt", "mkt_i", "cat", "billed", "cond", "rcode", "own", "inc", "pts", "eur", "eur_vs", "mchg",
           "state", "lprow", "hk", "ridx", "floor", "room", "mult", "free_b", "free_ex", "inc_off", "inc_on", "reason"]
lc = {n: get_column_letter(i + 1) for i, n in enumerate(LP_COLS)}
pc = {n: get_column_letter(i + 1) for i, n in enumerate(PM_COLS)}


def lp_rng(n, a=LP_FIRST, b=LP_LAST):
    return f"{LPN}${lc[n]}${a}:${lc[n]}${b}"


def pm_rng(n, a=PM_FIRST, b=PM_LAST):
    return f"{PMN}${pc[n]}${a}:${pc[n]}${b}"


LP_IDX_NAME = {}


def lp_idx(n, rowref):                                     # INDEX from the top of the sheet, so the row number is absolute
    if n not in LP_IDX_NAME:
        LP_IDX_NAME[n] = named(f"part_{n}", f"{LPN}${lc[n]}$1:${lc[n]}${LP_LAST}")
    return f"INDEX({LP_IDX_NAME[n]},{rowref})"


def pm_idx_rng(n):
    return f"{PMN}${pc[n]}$1:${pc[n]}${PM_LAST}"


# cells on 'Market layer' that the other sheets read (rows fixed here, the sheet is laid out around them)
R_SET_CEIL, R_SET_EXEMPT, R_SET_CIS, R_SET_ISR, R_SET_SVCTXT = 7, 8, 9, 11, 12
CEIL = f"{ML}$B${R_SET_CEIL}"
EXC = named("code_exempt_market", f"{ML}$B${R_SET_EXEMPT}")
CIS1 = named("code_cis_1", f"{ML}$B${R_SET_CIS}")
CIS2 = named("code_cis_2", f"{ML}$C${R_SET_CIS}")
ISRT = named("code_israel_trucks", f"{ML}$B${R_SET_ISR}")
SVCTXT = named("text_service_hold", f"{ML}$B${R_SET_SVCTXT}")
T_OFF = named("base_points_off", f"{SVN}$B$12")
T_ON = named("base_points_on", f"{SVN}$C$12")

# ---- the pricing grid sheet: cells the other sheets read
GR_ROLE0 = 6                              # first role row (short code in column C)
GR_A0, GR_B0, GR_NOW0 = 14, 21, 26        # first row of the scenario A, scenario B and in-use multiplier tables
GR_ST0 = 34                               # first market row of the resolved stance table
GR_ST_LAST = GR_ST0 + len(markets) - 1
GR_CODE0, GR_CODE_N = GR_ST_LAST + 6, 20  # reason code -> plain sentence lookup
GR_MULT = named("grid_multipliers", f"{GRN}$B${GR_NOW0}:$E${GR_NOW0 + 2}")
GR_BASE = f"{GRN}$B$29"
GR_SI = named("grid_stance_number", f"{GRN}$G${GR_ST0}:$G${GR_ST_LAST}")
GR_SCODE = named("grid_stance_code", f"{GRN}$H${GR_ST0}:$H${GR_ST_LAST}")
GR_RCODE = named("grid_role_code", f"{GRN}$C${GR_ROLE0}:$C${GR_ROLE0 + 3}")

# =================================================================== sheet: Layer by part
ws = ws_lp
put(ws, 1, 1, "Layer by part: one list price per part, and what the market layer does to it", TITLE)
put(ws, 2, 1, ("One row per part number, in part number order. Blue = values copied in (sources on the 'Market layer' sheet); "
               "black = formulas. The list increase shown here is the one for a market that follows the factory increase; "
               "under the grid a market that keeps its price or raises more gets a different extra, as a distributor condition "
               "on the part x market sheet."), SUB)
LP_HEAD = {
    "pn": "Part number", "desc": "Description", "cat": "Parts category (service, repair, body)",
    "noalt": "No aftermarket alternative found (1 = yes)", "lub": "Lubricant (1 = yes): kept at today's price",
    "role": "Parts role on the grid", "ridx": "Role number (1 wear, 2 captive, 3 commercial, 4 body and legal)",
    "hk": "Hold group (0 none, 1 filter, 2 intake/exhaust/emission, 3 brake disc or drum)",
    "pcode": "Part-level reason code (lubricant or brake pad kit)",
    "list_now": "Current list EUR (PR00)", "inc_now": "List increase, market that follows the factory increase",
    "list_new": "New list EUR, market that follows the factory increase",
    "own_fact": "Own factory increase (IML/IMIT)", "own_inc": "Own increase in the +5% proposal",
    "padheld": "Brake pad kit held at today's price (1 = yes)", "ceil": "Ceiling: own factory increase + 5 points",
    "floor": "Own increase limited by the ceiling", "elig": "Can carry the recovery extra (1 = yes)",
    "room": "Room for the extra below the ceiling", "mone": "One minus the class margin",
    "mfac": "One minus the class margin, times one plus the factory increase",
    "free_b": "Billed in markets with no hold, excluding Armenia and Kazakhstan",
    "free_ex": "Of which in the exempt market (Isuzu UK)", "w_off": "Billed that can carry the extra: switch OFF",
    "w_on": "Billed that can carry the extra: switch ON", "inc_off": "List increase: switch OFF",
    "inc_on": "List increase: switch ON", "first": "First row on 'Layer by part and market'", "nrows": "Rows on 'Layer by part and market'",
    "ptr": "Row pointer check (0 = ok)", "prow": "Row on Proposal sheet"}
HELP_LP = {"first", "nrows", "ptr", "prow", "padheld", "free_b", "free_ex", "w_off", "w_on", "floor", "room", "ceil", "elig",
           "ridx", "hk", "pcode", "mone", "mfac"}
header(ws, 4, [LP_HEAD[n] for n in LP_COLS], height=96, fills={i: HFILL_HELP for i, n in enumerate(LP_COLS) if n in HELP_LP})
PM_FREE = pm_idx_rng("free_b")
PM_FREEX = pm_idx_rng("free_ex")
PM_PN_TOP = pm_idx_rng("pn")
for i, r_ in enumerate(parts.itertuples(index=False)):
    r = LP_FIRST + i
    f = {n: f"{lc[n]}{r}" for n in LP_COLS}
    ws[f["pn"]] = r_.pn
    ws[f["desc"]] = r_.desc
    ws[f["cat"]] = r_.segment
    ws[f["noalt"]] = int(r_.captive_strict)
    ws[f["lub"]] = int(r_.lubricant)
    ws[f["role"]] = r_.role_label
    ws[f["ridx"]] = int(r_.ridx)
    ws[f["hk"]] = int(r_.hk)
    ws[f["first"]] = int(r_.first)
    ws[f["nrows"]] = int(r_.nrows)
    ws[f["prow"]] = f"=MATCH({f['pn']},Proposal!$A$2:$A${PROP_LAST},0)+1"
    ws[f["own_fact"]] = f"=INDEX(Proposal!$L$1:$L${PROP_LAST},{f['prow']})"
    ws[f["own_inc"]] = f"=INDEX(Proposal!$P$1:$P${PROP_LAST},{f['prow']})"
    ws[f["padheld"]] = f"=IF(AND(INDEX(Proposal!$AD$1:$AD${PROP_LAST},{f['prow']})=1,Summary!$B$9=1),1,0)"
    ws[f["pcode"]] = f'=IF({f["lub"]}=1,"LUBRICANT_NONE",IF({f["padheld"]}=1,"HOLD_PAD",""))'
    ws[f["ceil"]] = f"=IF(OR({f['padheld']}=1,{f['lub']}=1),0,MAX({f['own_fact']},0)+{CEIL})"
    ws[f["floor"]] = f"=MIN({f['ceil']},{f['own_inc']})"
    ws[f["elig"]] = (f'=IF(OR({f["padheld"]}=1,{f["lub"]}=1),0,IF({SELIG}=1,'
                     f'IF(AND(OR({f["cat"]}="repair",{f["cat"]}="body"),{f["noalt"]}=1),1,0),1))')
    ws[f["room"]] = f"=IF({f['elig']}=1,MAX({f['ceil']}-{f['own_inc']},0),0)"
    ws[f["mone"]] = f'=IFERROR(1-INDEX(Proposal!$D$1:$D${PROP_LAST},{f["prow"]}),"")'
    ws[f["mfac"]] = f'=IFERROR({f["mone"]}*(1+{f["own_fact"]}),"")'
    ws[f["free_b"]] = f"=SUM(INDEX({PM_FREE},{f['first']}):INDEX({PM_FREE},{f['first']}+{f['nrows']}-1))"
    ws[f["free_ex"]] = f"=SUM(INDEX({PM_FREEX},{f['first']}):INDEX({PM_FREEX},{f['first']}+{f['nrows']}-1))"
    ws[f["w_off"]] = f"={f['free_b']}"
    ws[f["w_on"]] = f"={f['free_b']}-{f['free_ex']}"
    # the reference list: a market that follows the factory increase, body parts on the 'all other markets' setting
    mref = f'({f["elig"]}*INDEX({GR_MULT},2,{f["ridx"]})*IF({f["cat"]}="body",{SBODY_REST},1))'
    ws[f["inc_off"]] = f"={f['floor']}+MIN({f['room']},{T_OFF}*{mref})"
    ws[f["inc_on"]] = f"={f['floor']}+MIN({f['room']},{T_ON}*{mref})"
    ws[f["inc_now"]] = f"=IF({SW}=1,{f['inc_on']},{f['inc_off']})"
    ws[f["list_now"]] = f'=IF(INDEX(Proposal!$I$1:$I${PROP_LAST},{f["prow"]})>0,INDEX(Proposal!$I$1:$I${PROP_LAST},{f["prow"]}),"")'
    ws[f["list_new"]] = f'=IF({f["list_now"]}="","",ROUND({f["list_now"]}*(1+{f["inc_now"]}),2))'
    ws[f["ptr"]] = (f"=IF(AND(INDEX({PM_PN_TOP},{f['first']})={f['pn']},"
                    f"INDEX({PM_PN_TOP},{f['first']}+{f['nrows']}-1)={f['pn']}),0,1)")
fmt_lp = {"list_now": EUR2, "inc_now": PCT2, "list_new": EUR2, "own_fact": PCT2, "own_inc": PCT2, "ceil": PCT2, "floor": PCT2,
          "room": PCT2, "free_b": EUR0, "free_ex": EUR0, "w_off": EUR0, "w_on": EUR0, "inc_off": PCT2, "inc_on": PCT2,
          "first": "0", "nrows": "0", "ptr": "0", "prow": "0", "ridx": "0", "hk": "0", "mone": NUM4, "mfac": NUM4}
data_lp = {"pn", "desc", "cat", "noalt", "lub", "role", "ridx", "hk", "first", "nrows"}
for row in ws.iter_rows(min_row=LP_FIRST, max_row=LP_LAST):
    for j, c in enumerate(row):
        n = LP_COLS[j]
        c.font = DATA if n in data_lp else (BOLD if n in ("inc_now", "list_new") else BODY)
        if n in fmt_lp:
            c.number_format = fmt_lp[n]
for n, wd in zip(LP_COLS, [13, 34, 11, 12, 12, 20, 9, 9, 14, 12, 13, 13, 11, 11, 11, 11, 11, 11, 11, 10, 10,
                           14, 12, 14, 14, 11, 11, 11, 10, 10, 10]):
    ws.column_dimensions[lc[n]].width = wd
ws.freeze_panes = f"C{LP_FIRST}"
ws.auto_filter.ref = f"A4:{get_column_letter(len(LP_COLS))}{LP_LAST}"

# =================================================================== sheet: Layer by part and market
ws = ws_pm
put(ws, 1, 1, "Layer by part and market: the condition each distributor gets on each part", TITLE)
put(ws, 2, 1, ("One row per part number and market (45,581 rows). Condition = hold at today's price, own increase, own increase plus "
               "the recovery extra, or own increase only. Every row carries exactly one reason code. Blue = values copied in "
               "(sources on the 'Market layer' sheet); black = formulas. Grey headers are helper columns."), SUB)
PM_HEAD = {
    "pn": "Part number", "mkt": "Market", "mkt_i": "Market number", "cat": "Parts category",
    "billed": "Billed EUR (Jul 25-Jun 26)", "cond": "Condition now (switches as set)", "rcode": "Reason code",
    "own": "Own increase", "inc": "Increase in this market now", "pts": "Hold or extra vs own increase (points)",
    "eur": "EUR at this increase", "eur_vs": "EUR vs own increase", "mchg": "Class margin change (points)",
    "reason": "Hold decided in the paper (text)", "state": "Line type (hold, own only, free)", "lprow": "Row on 'Layer by part'",
    "hk": "Hold group", "ridx": "Role number", "floor": "Own increase limited by the ceiling",
    "room": "Room below the ceiling", "mult": "Multiplier on the base, from the grid",
    "free_b": "Billed in a line with no hold (not Armenia or Kazakhstan)", "free_ex": "Of which exempt market",
    "inc_off": "Increase if switch OFF", "inc_on": "Increase if switch ON"}
HELP_PM = {"reason", "state", "lprow", "free_b", "free_ex", "inc_off", "inc_on", "mkt_i", "hk", "ridx", "floor", "room", "mult"}
header(ws, 4, [PM_HEAD[n] for n in PM_COLS], height=86, fills={i: HFILL_HELP for i, n in enumerate(PM_COLS) if n in HELP_PM})
LPA = named("part_numbers", lp_rng("pn"))
CODE_RNG = named("grid_reason_codes", f"{GRN}$A${GR_CODE0}:$A${GR_CODE0 + GR_CODE_N - 1}")
CODE_TXT = named("grid_reason_text", f"{GRN}$B$1:$B${GR_CODE0 + GR_CODE_N - 1}")
for i, r_ in enumerate(pm.itertuples(index=False)):
    r = PM_FIRST + i
    f = {n: f"{pc[n]}{r}" for n in PM_COLS}
    ws[f["pn"]] = r_.pn
    ws[f["mkt"]] = r_.db
    ws[f["mkt_i"]] = int(r_.mkt_i)
    ws[f["billed"]] = float(r_.billed)
    ws[f["reason"]] = r_.reason if r_.reason else None
    ws[f["lprow"]] = f"=MATCH({f['pn']},{LPA},0)+{LP_FIRST - 1}"
    ws[f["cat"]] = f"={lp_idx('cat', f['lprow'])}"
    ws[f["hk"]] = f"={lp_idx('hk', f['lprow'])}"
    ws[f["ridx"]] = f"={lp_idx('ridx', f['lprow'])}"
    ws[f["floor"]] = f"={lp_idx('floor', f['lprow'])}"
    ws[f["room"]] = f"={lp_idx('room', f['lprow'])}"
    ws[f["state"]] = (f'=IF(OR({f["mkt"]}={CIS1},{f["mkt"]}={CIS2}),"own only",IF({f["reason"]}="","free",'
                      f'IF(AND({f["reason"]}={SVCTXT},OR(AND({f["hk"]}=1,{S1}=0),AND({f["hk"]}=2,{S2}=0))),"free","hold")))')
    ws[f["free_b"]] = f'=IF({f["state"]}="free",{f["billed"]},0)'
    ws[f["free_ex"]] = f"=IF({f['mkt']}={EXC},{f['free_b']},0)"
    ws[f["own"]] = f"={lp_idx('own_inc', f['lprow'])}"
    bodyf = f'IF({f["cat"]}="body",IF({f["mkt"]}={ISRT},{SBODY_UTI},IF({f["mkt"]}={EXC},{SBODY_IUK},{SBODY_REST})),1)'
    ws[f["mult"]] = (f'=IF({f["state"]}<>"free",0,{lp_idx("elig", f["lprow"])}*'
                     f'INDEX({GR_MULT},INDEX({GR_SI},{f["mkt_i"]}),{f["ridx"]})*{bodyf})')
    ws[f["inc_off"]] = (f'=IF({f["state"]}="hold",0,IF({f["state"]}="own only",{f["own"]},'
                        f'{f["floor"]}+MIN({f["room"]},{T_OFF}*{f["mult"]})))')
    ws[f["inc_on"]] = (f'=IF({f["state"]}="hold",0,IF({f["state"]}="own only",{f["own"]},'
                       f'{f["floor"]}+MIN({f["room"]},IF({f["mkt"]}={EXC},0,{T_ON}*{f["mult"]}))))')
    ws[f["inc"]] = f"=IF({SW}=1,{f['inc_on']},{f['inc_off']})"
    ws[f["pts"]] = f"={f['inc']}-{f['own']}"
    ws[f["rcode"]] = (f'=IF({lp_idx("pcode", f["lprow"])}<>"",{lp_idx("pcode", f["lprow"])},'
                      f'IF({f["state"]}="hold",IF({f["hk"]}=3,"HOLD_DISC",'
                      f'IF({f["reason"]}={SVCTXT},"HOLD_SERVICE","HOLD_ISRAEL_BODY_LIGHTING")),'
                      f'IF({f["state"]}="own only","OWN_ONLY_AM_KZ",'
                      f'IF({f["inc"]}>{f["own"]},"EXTRA_"&INDEX({GR_SCODE},{f["mkt_i"]})&"_"'
                      f'&INDEX({GR_RCODE},{f["ridx"]}),IF({f["inc"]}<{f["own"]},"CEILING_CUT","OWN")))))')
    ws[f["cond"]] = f'=IF({f["state"]}="hold",{f["reason"]},INDEX({CODE_TXT},MATCH({f["rcode"]},{CODE_RNG},0)+{GR_CODE0 - 1}))'
    ws[f["eur"]] = f"={f['billed']}*{f['inc']}"
    ws[f["eur_vs"]] = f"={f['billed']}*{f['pts']}"
    ws[f["mchg"]] = f'=IFERROR({lp_idx("mone", f["lprow"])}-{lp_idx("mfac", f["lprow"])}/(1+{f["inc"]}),0)'
fmt_pm = {"billed": EUR2, "own": PCT2, "inc": PCT2, "pts": PTS, "eur": EUR2, "eur_vs": EUR2, "lprow": "0", "free_b": EUR2,
          "free_ex": EUR2, "inc_off": PCT2, "inc_on": PCT2, "mkt_i": "0", "hk": "0", "ridx": "0", "floor": PCT2,
          "room": PCT2, "mult": NUM2, "mchg": PTS}
data_pm = {"pn", "mkt", "mkt_i", "billed", "reason"}
for row in ws.iter_rows(min_row=PM_FIRST, max_row=PM_LAST):
    for j, c in enumerate(row):
        n = PM_COLS[j]
        c.font = DATA if n in data_pm else (BOLD if n in ("inc", "cond", "rcode") else BODY)
        if n in fmt_pm:
            c.number_format = fmt_pm[n]
for n, wd in zip(PM_COLS, [13, 12, 8, 10, 13, 40, 26, 10, 12, 14, 13, 13, 12, 10, 9, 7, 7, 11, 11, 10, 15, 12, 11, 11, 44]):
    ws.column_dimensions[pc[n]].width = wd
ws.freeze_panes = f"C{PM_FIRST}"
ws.auto_filter.ref = f"A4:{get_column_letter(len(PM_COLS))}{PM_LAST}"

# =================================================================== sheet: Layer solver
ws = ws_sv
put(ws, 1, 1, "Layer solver: the base points behind the grid, solved live", TITLE)
put(ws, 2, 1, ("The recovery extra on a line is one base number of points times the multiplier its market stance and its parts role "
               "give it on the 'Pricing grid' sheet, up to the part's ceiling. The base is found by halving the search range 60 times "
               "until the total lands on the target (no macro, no Goal Seek). Change any switch and it re-solves."), SUB)
BFC = pm_rng("billed")
STc = pm_rng("state")
OWNc = pm_rng("own")
FREEB = pm_rng("free_b")
ROOM = pm_rng("room")
MULT = pm_rng("mult")
MKTc = pm_rng("mkt")
put(ws, 4, 1, "Target total increase, EUR (Summary target x billed base)", BODY)
put(ws, 4, 2, f"=Summary!$B$5*SUM({BFC})", BOLD, EUR2)
put(ws, 5, 1, "Own increase on Armenia and Kazakhstan lines (option A, fixed), EUR", BODY)
put(ws, 5, 2, f'=SUMPRODUCT(--({STc}="own only"),{BFC},{OWNc})', BOLD, EUR2)
put(ws, 6, 1, "All other lines with no hold, at their own increase limited by the ceiling, EUR", BODY)
put(ws, 6, 2, f"=SUMPRODUCT({FREEB},{pm_rng('floor')})", BOLD, EUR2)
put(ws, 7, 1, "Recovery the extra has to deliver, EUR (target - fixed lines - lines at their floor)", BOLD)
put(ws, 7, 2, "=B4-B5-B6", BOLD, EUR2)
put(ws, 8, 1, "Upper end of the search range for the base", BODY)
put(ws, 8, 2, f"=MAX({lp_rng('room')})*10+0.01", BODY, PCT2)
header(ws, 10, ["Item", "Switch OFF (paper)", "Switch ON (Isuzu UK exempt)"], height=32)
BIS0 = 20                                                   # first bisection row
BISN = 60
last_b = BIS0 + BISN - 1
NOTEX = f"--({MKTc}<>{EXC})"
put(ws, 11, 1, "Billed that can carry the extra, EUR", BODY)
put(ws, 11, 2, f"=SUMPRODUCT({FREEB},--({ROOM}>0),--({MULT}>0))", BODY, EUR0)
put(ws, 11, 3, f"=SUMPRODUCT({FREEB},{NOTEX},--({ROOM}>0),--({MULT}>0))", BODY, EUR0)
put(ws, 12, 1, "Base points behind the grid (t)", BOLD)
put(ws, 12, 2, f"=C{last_b}", BOLD, "0.000000")
put(ws, 12, 3, f"=G{last_b}", BOLD, "0.000000")
put(ws, 13, 1, "Recovery delivered at the base, EUR", BODY)
put(ws, 13, 2, f"=SUMPRODUCT({FREEB},({ROOM}<B12*{MULT})*{ROOM}+({ROOM}>=B12*{MULT})*B12*{MULT})", BODY, EUR2)
put(ws, 13, 3, f"=SUMPRODUCT({FREEB},{NOTEX},({ROOM}<C12*{MULT})*{ROOM}+({ROOM}>=C12*{MULT})*C12*{MULT})", BODY, EUR2)
put(ws, 14, 1, "Recovery needed, EUR", BODY)
put(ws, 14, 2, "=$B$7", BODY, EUR2)
put(ws, 14, 3, "=$B$7", BODY, EUR2)
put(ws, 15, 1, "Difference, EUR (should be 0.00)", BOLD)
put(ws, 15, 2, "=ROUND(B13-B14,2)", BOLD, EUR2)
put(ws, 15, 3, "=ROUND(C13-C14,2)", BOLD, EUR2)
put(ws, 16, 1, "Can the ceiling deliver it?", BODY)
put(ws, 16, 2, f'=IF(SUMPRODUCT({FREEB},--({MULT}>0),{ROOM})>=B14-0.01,"yes","no: ceiling too tight")', BOLD)
put(ws, 16, 3, f'=IF(SUMPRODUCT({FREEB},{NOTEX},--({MULT}>0),{ROOM})>=C14-0.01,"yes","no: ceiling too tight")', BOLD)
header(ws, BIS0 - 1, ["Step", "Low (OFF)", "High (OFF)", "Middle (OFF)", "Recovery at middle (OFF)",
                       "Low (ON)", "High (ON)", "Middle (ON)", "Recovery at middle (ON)"], height=32)
for k in range(BISN):
    r = BIS0 + k
    put(ws, r, 1, k + 1, BODY, "0")
    for base_col, extra in ((2, ""), (6, f"{NOTEX},")):
        lo, hi, mid, g = (get_column_letter(base_col + j) for j in range(4))
        if k == 0:
            put(ws, r, base_col, 0, BODY, "0.000000")
            put(ws, r, base_col + 1, "=$B$8", BODY, "0.000000")
        else:
            put(ws, r, base_col, f"=IF({g}{r - 1}<$B$7,{mid}{r - 1},{lo}{r - 1})", BODY, "0.000000")
            put(ws, r, base_col + 1, f"=IF({g}{r - 1}<$B$7,{hi}{r - 1},{mid}{r - 1})", BODY, "0.000000")
        put(ws, r, base_col + 2, f"=({lo}{r}+{hi}{r})/2", BODY, "0.000000")
        put(ws, r, base_col + 3,
            f"=SUMPRODUCT({FREEB},{extra}({ROOM}<{mid}{r}*{MULT})*{ROOM}+({ROOM}>={mid}{r}*{MULT})*{mid}{r}*{MULT})", BODY, EUR2)
for col, wd in zip("ABCDEFGHI", [74, 20, 20, 16, 22, 14, 14, 14, 22]):
    ws.column_dimensions[col].width = wd
ws.freeze_panes = "A4"

# =================================================================== sheet: Pricing grid (package D)
ws = ws_gr
put(ws, 1, 1, "Pricing grid: one extra per market stance and parts role", TITLE)
put(ws, 2, 1, ("Three stances a market can take, four roles a part can have: twelve cells. The extra a line gets is one base number of "
               "points, the same for the whole book, times the multiplier of its cell. The base is solved on 'Layer solver' so the total "
               "lands exactly on the target. Yellow cells are inputs."), SUB)
put(ws, 4, 1, "The four parts roles", SEC)
header(ws, GR_ROLE0 - 1, ["Role", "What it means", "Short code", "Parts categories in it"], height=28)
role_cats = {r: ", ".join(sorted(roles.aim_level_1[roles.pricing_role == r])) for r in ROLES}
role_cats["commercial"] += ". Parts with no category of their own keep this role and are counted here."
ROLE_WHAT = {"wear_pms": "Parts that wear out and come back on a service interval.",
             "captive": "Parts a customer can hardly buy anywhere else.",
             "commercial": "Parts an outside shop can match.",
             "body_legal": "Crash, body and legal repair parts."}
for i, rr_ in enumerate(ROLES):
    r = GR_ROLE0 + i
    put(ws, r, 1, ROLE_LABEL[rr_], BODY)
    put(ws, r, 2, ROLE_WHAT[rr_], BODY)
    put(ws, r, 3, ROLE_CODE[rr_], DATA)
    put(ws, r, 4, role_cats[rr_], SUB, align=WRAP)
    ws.row_dimensions[r].height = 26
r = GR_ROLE0 + 4
put(ws, r, 1, (f"The roles come from {ROLE_CSV.name}, column pricing_role, joined on the parts category. That file says "
               f"status {ROLE_STATUS}: the roles are a working view, not a locked decision. "
               f"{int((parts.role_raw == 'unclassified').sum()):,} part numbers have no role of their own and follow the commercial "
               f"parts row; {n_no_cat} of them have no row at all in the parts-category release of 7 October 2026."), SUB, align=WRAP)
ws.merge_cells(start_row=r, start_column=1, end_row=r, end_column=8)
ws.row_dimensions[r].height = 30

MULT_A = {"Keep today's price": [1, 1, 1, 1], "Follow factory increase": [1, 1, 1, 1], "Raise more": [1, 1, 1, 1]}
MULT_B = {"Keep today's price": [0, 0.5, 0, 0.5], "Follow factory increase": [1, 1, 1, 1], "Raise more": [1.0, 1.8, 1.2, 1.5]}
put(ws, GR_A0 - 3, 1, "Scenario A multipliers: the 2 October 2026 paper", SEC)
put(ws, GR_A0 - 2, 1, ("All twelve cells are 1. In scenario A the stance does not change a price by itself: the market treatment is in "
                       "the holds, and the extra reaches only repair and body parts with no aftermarket alternative found. That is what "
                       "reproduces the paper."), SUB)
header(ws, GR_A0 - 1, ["Stance"] + [ROLE_LABEL[r_] for r_ in ROLES], height=32)
for i, s_ in enumerate(STANCES):
    put(ws, GR_A0 + i, 1, s_, BODY)
    put(ws, GR_A0 + i, 9, STANCE_CODE[i + 1], DATA)          # column I: the short stance code, read by the reason code
    for j, r_ in enumerate(ROLES):
        put(ws, GR_A0 + i, 2 + j, MULT_A[s_][j], INPUT, NUM2, fill=YELLOW)
put(ws, GR_B0 - 3, 1, "Scenario B multipliers: illustration, not decided", SEC)
put(ws, GR_B0 - 2, 1, ("An illustration of what a grid could look like, to show the mechanism. Nothing here is proposed. "
                       "Change the numbers and the base re-solves so the total stays on the target."), SUB)
header(ws, GR_B0 - 1, ["Stance"] + [ROLE_LABEL[r_] for r_ in ROLES], height=32)
for i, s_ in enumerate(STANCES):
    put(ws, GR_B0 + i, 1, s_, BODY)
    for j, r_ in enumerate(ROLES):
        put(ws, GR_B0 + i, 2 + j, MULT_B[s_][j], INPUT, NUM2, fill=YELLOW)
put(ws, GR_NOW0 - 2, 1, "Multipliers in use now (scenario chosen on the Summary sheet)", SEC)
header(ws, GR_NOW0 - 1, ["Stance"] + [ROLE_LABEL[r_] for r_ in ROLES], height=32)
for i, s_ in enumerate(STANCES):
    put(ws, GR_NOW0 + i, 1, s_, BOLD)
    for j in range(4):
        cl = get_column_letter(2 + j)
        put(ws, GR_NOW0 + i, 2 + j, f'=IF({SSCEN}="A",{cl}{GR_A0 + i},{cl}{GR_B0 + i})', BOLD, NUM2)
put(ws, 29, 1, "Base points behind the grid, solved on 'Layer solver'", BOLD)
put(ws, 29, 2, f"=IF({SW}=1,{T_ON},{T_OFF})", BOLD, "0.0000%")
put(ws, 30, 1, "The extra a line gets = base points x the multiplier of its cell, never above the part's ceiling.", SUB)

# ---- market stance table
put(ws, GR_ST0 - 2, 1, "Market stance in use", SEC)
header(ws, GR_ST0 - 1, ["Market", "Code", "Scenario A (the paper)", "Scenario B (candidate, not decided)",
                        "Override from the stance sheet", "Stance now", "Stance number", "Stance code", "Price basis"], height=44)
for i, m in enumerate(markets):
    r = GR_ST0 + i
    put(ws, r, 1, NAMES.get(m, m.title()), BODY)
    put(ws, r, 2, m, DATA)
    put(ws, r, 3, stance_facts[m]["sa"], BODY)
    put(ws, r, 4, stance_facts[m]["sb"], BODY)
    put(ws, r, 6, f'=IF(E{r}<>"",E{r},IF({SSCEN}="A",C{r},D{r}))', BOLD)
    put(ws, r, 7, f"=MATCH(F{r},$A${GR_A0}:$A${GR_A0 + 2},0)", BODY, "0")
    put(ws, r, 8, f"=INDEX($I${GR_A0}:$I${GR_A0 + 2},G{r})", BODY)
    put(ws, r, 9, BASIS[m], SUB)
r = GR_ST_LAST + 2
put(ws, r, 1, ("The stance of a market is set here. The facts behind it are on the three stance sheets, one per price basis. "
               "Armenia and Kazakhstan take their own increase only in every scenario, so their stance changes nothing."), SUB, align=WRAP)
ws.merge_cells(start_row=r, start_column=1, end_row=r, end_column=9)
ws.row_dimensions[r].height = 26

# ---- reason code lookup (code -> plain sentence), read by the part x market sheet
put(ws, GR_CODE0 - 2, 1, "Reason codes and what they mean", SEC)
header(ws, GR_CODE0 - 1, ["Reason code", "Condition in plain words", "Lines now", "Billed EUR now"], height=28)
CODES = [("LUBRICANT_NONE", "Lubricant: today's price, no increase and no extra"),
         ("HOLD_PAD", "Brake pad kit kept at today's price"),
         ("HOLD_DISC", "Brake discs and drums kept at today's price (decided 11 October 2026)"),
         ("HOLD_SERVICE", "Service parts held at today's price"),
         ("HOLD_ISRAEL_BODY_LIGHTING", "Body, collision and lighting held at today's price (Israel)"),
         ("OWN_ONLY_AM_KZ", "Own increase only: no hold, no extra (option A)"),
         ("CEILING_CUT", "Own increase, held down by the ceiling"),
         ("OWN", "Own increase")]
for s_i, s_ in enumerate(STANCES):
    for r_ in ROLES:
        CODES.append((f"EXTRA_{STANCE_CODE[s_i + 1]}_{ROLE_CODE[r_]}", "Own increase + recovery extra"))
assert len(CODES) == GR_CODE_N, len(CODES)
RC = pm_rng("rcode")
for i, (code, txt) in enumerate(CODES):
    r = GR_CODE0 + i
    put(ws, r, 1, code, DATA)
    put(ws, r, 2, txt, BODY)
    put(ws, r, 3, f"=COUNTIF({RC},$A{r})", BODY, NUM0)
    put(ws, r, 4, f"=SUMIF({RC},$A{r},{BFC})", BODY, EUR0)
CODE_LAST = GR_CODE0 + GR_CODE_N - 1
r = CODE_LAST + 1
put(ws, r, 1, "All lines", BOLD)
put(ws, r, 3, f"=SUM(C{GR_CODE0}:C{CODE_LAST})", BOLD, NUM0)
put(ws, r, 4, f"=SUM(D{GR_CODE0}:D{CODE_LAST})", BOLD, EUR0)
put(ws, r + 1, 1, "Rows on the part x market sheet", BODY)
put(ws, r + 1, 3, NM, DATA, NUM0)
put(ws, r + 2, 1, "Every line has exactly one reason code", BOLD)
put(ws, r + 2, 3, f'=IF(AND(C{r}=C{r + 1},ABS(D{r}-SUM({BFC}))<0.05),"OK","CHECK")', BOLD)
GR_CODE_CHK = f"{GRN}$C${r + 2}"
ws.conditional_formatting.add(f"C{r + 2}", CellIsRule(operator="equal", formula=['"CHECK"'], font=RED))
ws.conditional_formatting.add(f"C{r + 2}", CellIsRule(operator="equal", formula=['"OK"'], font=GREEN))
r += 4
put(ws, r, 1, ("The codes are read in this order: lubricant, brake pad kit, hold, Armenia and Kazakhstan, extra, cut by the ceiling, "
               "own increase. A lubricant or a pad kit keeps its code in every market, because that decision is on the part, not on "
               "the market."), SUB, align=WRAP)
ws.merge_cells(start_row=r, start_column=1, end_row=r, end_column=8)
ws.row_dimensions[r].height = 26
r += 2

# ---- the twelve cells
GR_CELL0 = r + 1
put(ws, r, 1, "The twelve cells: points and euro", SEC)
header(ws, r + 1, ["Stance", "Parts role", "Extra in points", "Lines", "Billed EUR that carries it", "Recovered EUR"], height=32)
cell_rows = {}
for s_i, s_ in enumerate(STANCES):
    for r_i, r_ in enumerate(ROLES):
        rr = r + 2 + s_i * 4 + r_i
        code = f"EXTRA_{STANCE_CODE[s_i + 1]}_{ROLE_CODE[r_]}"
        cell_rows[(s_i + 1, r_i + 1)] = rr
        put(ws, rr, 1, s_, BODY)
        put(ws, rr, 2, ROLE_LABEL[r_], BODY)
        put(ws, rr, 3, f"=$B$29*{get_column_letter(2 + r_i)}{GR_NOW0 + s_i}", BODY, "0.0000%")
        put(ws, rr, 4, f"=COUNTIF({RC},\"{code}\")", BODY, NUM0)
        put(ws, rr, 5, f'=SUMIF({RC},"{code}",{BFC})', BODY, EUR0)
        put(ws, rr, 6, f'=SUMIF({RC},"{code}",{pm_rng("eur_vs")})', BODY, EUR2)
GR_CELL_LAST = r + 1 + 12
rt = GR_CELL_LAST + 1
put(ws, rt, 1, "All twelve cells", BOLD)
put(ws, rt, 4, f"=SUM(D{GR_CELL0 + 1}:D{GR_CELL_LAST})", BOLD, NUM0)
put(ws, rt, 5, f"=SUM(E{GR_CELL0 + 1}:E{GR_CELL_LAST})", BOLD, EUR0)
put(ws, rt, 6, f"=SUM(F{GR_CELL0 + 1}:F{GR_CELL_LAST})", BOLD, EUR2)
GR_CELL_TOTAL = rt
for col, wd in zip("ABCDEFGHI", [34, 30, 18, 12, 22, 18, 18, 14, 12]):
    ws.column_dimensions[col].width = wd
ws.freeze_panes = "A4"

# =================================================================== sheets: stance by price basis (package C)
ST_COLS = ["Market", "Code", "Billed EUR 2025", "Fleet 2023 (paper source)", "Fleet 2024 (paper source)",
           "Fleet 2025 (paper source)", "Fleet 2025 (carpark file)", "Fleet 2026 (carpark file)",
           "Change 2025 to 2026, same base", "Change as printed in the paper", "Status of the 2026 figure",
           "Service share 2025", "Change in service share since 2023 (points)", "Pays, % of list",
           "Measured dealer reaction", "Registrations outlook (manual)", "Registrations a year at the pace in the decks",
           "Fleet 2026 at that pace", "Change at that pace", "Fleet direction (computed)",
           "Stance: scenario A (the paper)", "Stance: scenario B (candidate, not decided)", "Note",
           "Stance override (leave blank to follow the scenario)"]
ST_OVERRIDE_COL = len(ST_COLS)            # the last column, letter X
ST_FMT = {3: EUR0, 4: NUM0, 5: NUM0, 6: NUM0, 7: NUM0, 8: NUM0, 9: PCT1, 10: PCT1, 12: PCT1, 13: PTS, 14: "0.0",
          15: NUM4, 17: NUM0, 18: NUM0, 19: PCT1}
BASIS_TITLE = {"PR00": "Stance by market: the EU and UK price basis (PR00)",
               "ZPR1": "Stance by market: the Israel price basis (ZPR1)",
               "CIS": "Stance by market: the CIS price basis"}
BASIS_SUB = {
    "PR00": ("One row per distributor that buys on the PR00 price basis, modelled on the tab layout of the price calculator "
             "(ISZE_PriceCalc_AIM_20261007.xlsx). Blue = values read from a file; yellow = an input you can set. The stance itself "
             "is set on the 'Pricing grid' sheet, which reads the override column here."),
    "ZPR1": ("The two Israel distributors buy on their own price basis: the trucks distributor on 1799 and the D-Max distributor on "
             "1797. They are never blended. Customer 2372 (KIMA, Palestine) is in the 2026 base with billing of its own, so it gets "
             "its own block here."),
    "CIS": ("Armenia and Kazakhstan take their own increase only: no hold and no extra, in every scenario and in both switch "
            "positions. Their stance cell is shown for completeness and changes nothing."),
}
BASIS_NOTE = {
    "PR00": ["Ukraine buys on the normal basis and takes the normal treatment (decided). It is not on the own-increase-only list, "
             "so it sits here and not on the CIS sheet. Say so if that is not where you want it.",
             "The fleet 2025 in the paper comes from the GPS file; the fleet 2026 comes from the carpark file. Where the two 2025 "
             "figures differ, the change printed in the paper is measured on two different bases. The 'same base' column fixes that.",
             "Isuzu UK's service share rests on a flat 20,000 km a year; its own measured N35 fleet runs 14,494 km, so its 17% is "
             "probably understated."],
    "ZPR1": ["The Israel trucks distributor and the Israel D-Max distributor are two distributors with two price bases. "
             "Nothing on this sheet blends them.",
             "Palestine (KIMA, customer 2372) billed EUR 42,091 in the base. It falls below the EUR 60,000 cut of the per-market "
             "fact file, so the fleet, service share and dealer reaction columns are empty for it."],
    "CIS": ["Whether the increase reaches Armenia and Kazakhstan depends on the separate decision on their price basis, which is "
            "still open."],
}


def build_stance_sheet(ws, basis):
    mkts = [m for m in markets if BASIS[m] == basis]
    put(ws, 1, 1, BASIS_TITLE[basis], TITLE)
    put(ws, 2, 1, BASIS_SUB[basis], SUB, align=WRAP)
    ws.merge_cells("A2:H2")
    ws.row_dimensions[2].height = 40
    header(ws, 4, ST_COLS, height=110)
    rows = {}
    for i, m in enumerate(mkts):
        r = 5 + i
        rows[m] = r
        k = stance_facts[m]
        put(ws, r, 1, NAMES.get(m, m.title()), BODY)
        put(ws, r, 2, m, DATA)
        vals = [k["billed25"], k["f23p"], k["f24p"], k["f25p"], k["c25"], k["c26"], k["lfl"], k["paper_chg"],
                k["status"], k["svc25"], k["svc_chg"], k["pays"], k["beta"], None, k["pace_jm"] and k["pace"],
                k["f26_pace"], k["pace_chg"], k["direction"], k["sa"], k["sb"]]
        for j, v in enumerate(vals):
            col = 3 + j
            fnt = INPUT if col == 16 else (BOLD if col in (21, 22) else DATA)
            fill = YELLOW if col == 16 else None
            put(ws, r, col, (float(v) if isinstance(v, (int, float, np.floating)) and v is not None else v),
                fnt, ST_FMT.get(col), fill=fill)
        n = []
        if k["countries"]:
            n.append(f"carpark rows: {k['countries']}")
        if k["beta"] is not None:
            n.append(f"dealer reaction measured on the April 2026 change, standard error {k['beta_se']:.2f}")
        if k["pace"]:
            n.append(f"{k['pace_note']}; {PACE_SOURCE}")
        if m in CIS:
            n.append("own increase only")
        if m == "PALESTINE":
            n.append("customer 2372, below the EUR 60,000 cut of the per-market fact file")
        put(ws, r, 23, "; ".join(n), SUB, align=WRAP)
        put(ws, r, ST_OVERRIDE_COL, None, INPUT, fill=YELLOW)
        ws.row_dimensions[r].height = 26
    last = 5 + len(mkts) - 1
    r = last + 2
    put(ws, r, 1, "How to read the columns", SEC)
    reading = [
        "Billed EUR 2025: what the distributor bought from us in calendar 2025, parts only.",
        "Fleet 2023, 2024, 2025 (paper source): vehicles in service as the paper counted them (the GPS file).",
        "Fleet 2025 and 2026 (carpark file): the same two years from one file, so the change is like for like. The 2026 figure is an "
        "interim estimate: the 2025 fleet less a fixed yearly scrappage (10.2% for trucks, 12.3% for light commercials) plus planned "
        "registrations taken one for one. It is neither the forecast marked do-not-use in that file nor the rebuild, which is a "
        "specification only.",
        "Service share 2025: service parts the distributor bought against what its fleet should need at the service intervals, on a "
        "flat 20,000 km a year. Total parts, not genuine only.",
        "Pays, % of list: what the distributor actually paid in 2025 against the list price on the same lines.",
        "Measured dealer reaction: the change in dealer purchases for one point of price, measured on the April 2026 list change. "
        "Empty where it was not measured in that market: a pooled figure is never shown here as if it were local.",
        "Registrations outlook (manual): left empty on purpose. Fill it when a distributor gives a number.",
        "Fleet direction: growing above +3%, flat within plus or minus 3%, shrinking below -3%, on the like-for-like column.",
    ]
    for i, t in enumerate(reading):
        put(ws, r + 1 + i, 1, t, SUB, align=WRAP)
        ws.merge_cells(start_row=r + 1 + i, start_column=1, end_row=r + 1 + i, end_column=10)
        ws.row_dimensions[r + 1 + i].height = 26
    r = r + 1 + len(reading) + 1
    for i, t in enumerate(BASIS_NOTE[basis]):
        put(ws, r + i, 1, t, BODY, align=WRAP)
        ws.merge_cells(start_row=r + i, start_column=1, end_row=r + i, end_column=10)
        ws.row_dimensions[r + i].height = 28
    for j in range(len(ST_COLS)):
        ws.column_dimensions[get_column_letter(1 + j)].width = [30, 12, 14, 12, 12, 13, 13, 13, 13, 13, 16, 11, 13, 11,
                                                                13, 15, 15, 13, 12, 14, 20, 22, 46, 22][j]
    ws.freeze_panes = "C5"
    return rows


stance_rows = {}
for basis, wsx in (("PR00", ws_pr00), ("ZPR1", ws_zpr1), ("CIS", ws_cis)):
    stance_rows.update({m: (basis, r) for m, r in build_stance_sheet(wsx, basis).items()})
# the grid reads the override cell of each market from its own stance sheet (column X)
OVC = get_column_letter(ST_OVERRIDE_COL)
for i, m in enumerate(markets):
    basis, r = stance_rows[m]
    c_ = ws_gr.cell(GR_ST0 + i, 5)
    c_.value = f'=IF({STN[basis]}${OVC}${r}="","",{STN[basis]}${OVC}${r})'
    c_.font = BODY
    c_.fill = PALE

# =================================================================== sheet: Market layer
ws = ws_ml
mk_name = lambda m: NAMES.get(m, m.title())
put(ws, 1, 1, "Market layer: how the market decisions of the 2 October 2026 paper land per part and per market", TITLE)
put(ws, 2, 1, ("A proposal on paper. Nothing published, no price file or price list changed. The list stays one price per part; "
               "the market treatment is a distributor condition per market and parts category. The total stays on the target."), SUB)
put(ws, 4, 1, "Terms used on this sheet", SEC)
legend = ("Own increase = the +5% proposal's increase for that part (its own IML/IMIT factory increase, scaled so the book lands on "
          "+5.00%). Hold = the distributor keeps paying today's price for that parts category. Recovery extra = extra points on "
          "top of own increase, set by the market's stance and the part's role on the 'Pricing grid' sheet, up to the part's own "
          "factory increase + 5 points.")
put(ws, 5, 1, legend, BODY, align=WRAP)
ws.merge_cells("A5:H5")
ws.row_dimensions[5].height = 56
put(ws, 6, 1, "Switch and settings", SEC)
put(ws, R_SET_CEIL, 1, "Ceiling above a part's own factory (IML/IMIT) increase, points (decided 30 September and 2 October, not a switch)", BODY, align=WRAP)
put(ws, R_SET_CEIL, 2, CEILING_PTS, INPUT, PCT1, fill=PALE)
put(ws, R_SET_EXEMPT, 1, "Market code the switch exempts from the recovery extra", BODY, align=WRAP)
put(ws, R_SET_EXEMPT, 2, EXEMPT, INPUT, fill=PALE)
put(ws, R_SET_EXEMPT, 3, "Isuzu UK (D-Max)", SUB)
put(ws, R_SET_CIS, 1, "Markets left on their own increase, no hold, no extra (option A)", BODY, align=WRAP)
put(ws, R_SET_CIS, 2, CIS[0], INPUT, fill=PALE)
put(ws, R_SET_CIS, 3, CIS[1], INPUT, fill=PALE)
put(ws, 10, 1, "Isuzu UK (D-Max) exempt from the recovery extra: switch on the Summary sheet, cell D5 (0 = off, 1 = on)", BOLD, align=WRAP)
put(ws, 10, 2, f'=IF({SW}=1,"ON","OFF")', BOLD)
put(ws, 10, 3, (f'=IF({SW}=1,"ON: Isuzu UK repair and body parts keep their own increase; the extra moves to the other markets '
                f'(suggested, not decided).","OFF (default): Isuzu UK carries the extra, as in the 2 October paper. The exemption is not '
                f'decided: leave open.")'), BODY)
put(ws, R_SET_ISR, 1, "Market code of the Israel trucks distributor (used by the body-parts switch)", BODY, align=WRAP)
put(ws, R_SET_ISR, 2, ISR_TRUCKS, INPUT, fill=PALE)
put(ws, R_SET_SVCTXT, 1, "Text that marks a service hold on the part x market sheet (not a setting)", BODY, align=WRAP)
put(ws, R_SET_SVCTXT, 2, R_SERVICE, DATA)
for r in (R_SET_CEIL, R_SET_EXEMPT, R_SET_CIS, 10, R_SET_ISR, R_SET_SVCTXT):
    ws.row_dimensions[r].height = 28
    for c_ in range(1, 4):
        a_ = ws.cell(r, c_).alignment
        ws.cell(r, c_).alignment = Alignment(wrap_text=a_.wrap_text, vertical="center", horizontal=a_.horizontal)

# ---- reconciliation
RR0 = 14
put(ws, RR0, 1, "Reconciliation: the total stays exactly on the target in both switch positions", SEC)
header(ws, RR0 + 1, ["Item", "Switch OFF (paper)", "Switch ON (Isuzu UK exempt)", "Now (switch as set)", "Published: OFF",
                      "Published: ON", "Matches published", "Where the published figure comes from"], height=44)
cols_state = {"B": "inc_off", "C": "inc_on", "D": "inc"}
Bc, Dc, Gc, Cc, Mc = pm_rng("billed"), pm_rng("own"), pm_rng("state"), pm_rng("cat"), pm_rng("mkt")
rec = {}                                                    # name -> row
PAPER_SETTINGS = (f'AND(Summary!$B$5=0.05,Summary!$B$6=1,Summary!$B$7=1,Summary!$B$8=0,Summary!$B$9=1,'
                  f'{S1}=1,{S2}=1,{SBODY_UTI}=1,{SBODY_IUK}=1,{SBODY_REST}=1,{SELIG}=1,{SSCEN}="A",'
                  f'SUMPRODUCT(--({GRN}$E${GR_ST0}:$E${GR_ST_LAST}<>""))=0,'
                  f'SUM({GRN}$B${GR_A0}:$E${GR_A0 + 2})=12)')


def sp(expr_inc, kind):
    X = pm_rng(expr_inc)
    if kind == "total":
        return f"=SUMPRODUCT({Bc},{X})"
    if kind == "own":
        return f"=SUMPRODUCT({Bc},{Dc})"
    if kind == "given":
        return f'=SUMPRODUCT(--({Gc}="hold"),{Bc},{Dc})'
    if kind == "cut":
        return f'=SUMPRODUCT(--({Gc}="free"),{Bc},--(({Dc}-{X})>0),{Dc}-{X})'
    if kind == "extra":
        return f'=SUMPRODUCT(--({Gc}="free"),{Bc},--(({X}-{Dc})>0),{X}-{Dc})'
    if kind.startswith("extra_cat:"):
        cat = kind.split(":")[1]
        return f'=SUMPRODUCT(--({Gc}="free"),--({Cc}="{cat}"),{Bc},--(({X}-{Dc})>0),{X}-{Dc})'
    if kind == "extra_exempt":
        return (f'=SUMPRODUCT(--({Gc}="free"),--({Mc}={EXC}),--(({Cc}="repair")+({Cc}="body")>0),{Bc},--(({X}-{Dc})>0),{X}-{Dc})')
    raise ValueError(kind)


pubB, pubE = PUB["B_as_published"], PUB["B_iuk_exempt"]
rows = [
    ("own", "Own increase on all parts and markets (the +5% proposal), EUR", "own", EUR0, None, None,
     "Proposal sheet: Summary B13 (EUR 1,629,793)"),
    ("given", "Less: given up by the holds, EUR", "given", EUR0, 388914.0, 388914.0,
     "Paper of 2 Oct 2026 (EUR 388,914); room_to_raise_scenarios_2026-10-02.csv held_step_given_up_eur"),
    ("cut", "Less: cut by the ceiling (own increase above own factory increase + 5 points), EUR", "cut", EUR0,
     7654.0, 7654.0, "room_to_raise_scenarios_2026-10-02.csv cut_below_proposal_by_ceiling_eur (7,654)"),
    ("extra", "Plus: recovery extra from the grid, EUR", "extra", EUR0,
     pubB["uplift_above_proposal_eur"], pubE["uplift_above_proposal_eur"], "room_to_raise_variant_B_iuk_exempt_2026-10-02.json"),
    ("total", "Total increase after market treatment, EUR", "total", EUR0, pubB["total_step_eur"], pubE["total_step_eur"],
     "room_to_raise_variant_B_iuk_exempt_2026-10-02.json total_step_eur"),
]
r = RR0 + 2
for key, label, kind, nf, pOFF, pON, src in rows:
    rec[key] = r
    put(ws, r, 1, label, BOLD if key == "total" else BODY, align=WRAP)
    for col, inc in cols_state.items():
        put(ws, r, "ABCDEFGH".index(col) + 1, sp(inc, kind), BOLD if key == "total" else BODY, nf)
    if pOFF is not None:
        put(ws, r, 5, pOFF, DATA, nf)
        put(ws, r, 6, pON, DATA, nf)
        put(ws, r, 7, f'=IF({PAPER_SETTINGS},IF(AND(ABS(B{r}-E{r})<=1,ABS(C{r}-F{r})<=1),"OK","CHECK"),"n/a: settings changed")', BOLD)
    put(ws, r, 8, src, SUB)
    ws.row_dimensions[r].height = 28 if len(label) > 70 else 16
    r += 1
more = [
    ("target", "Target: Summary target x billed base, EUR", lambda c: f"=Summary!$B$5*SUM({Bc})", EUR0, None, None, "Summary B5 x billed base"),
    ("diff", "Difference to target, EUR (should be 0)", lambda c: f"={c}{rec['total']}-{c}{rec['total'] + 1}", EUR2, None, None, ""),
    ("pct", "Weighted increase after market treatment", lambda c: f"={c}{rec['total']}/SUM({Bc})", PCT3, 0.05, 0.05,
     "Target +5.00% (published total_pct 0.05 in the variant json)"),
    ("base", "Billed base, EUR (Jul 2025 - Jun 2026)", lambda c: f"=SUM({Bc})", EUR2, None, None, "price_bp_weighted_compare_pn.csv, in scope and movable: EUR 32,595,852.63"),
    ("t", "Base points behind the grid (solved on 'Layer solver')", None, "0.0000%", pubB["solver_t_pts"], pubE["solver_t_pts"],
     "room_to_raise_variant_B_iuk_exempt_2026-10-02.json solver_t_pts"),
    ("rep", "Recovery extra on repair parts, EUR", "extra_cat:repair", EUR0, pubB["uplift_repair_eur"], pubE["uplift_repair_eur"],
     "room_to_raise_variant_B_iuk_exempt_2026-10-02.json"),
    ("body", "Recovery extra on body parts, EUR", "extra_cat:body", EUR0, pubB["uplift_body_eur"], pubE["uplift_body_eur"],
     "room_to_raise_variant_B_iuk_exempt_2026-10-02.json"),
    ("svc", "Recovery extra on service parts, EUR (0 at the paper settings)", "extra_cat:service", EUR0, 0.0, 0.0,
     "room_to_raise_variant_B_iuk_exempt_2026-10-02.json uplift_service_eur"),
    ("iuk", "Recovery extra on Isuzu UK (D-Max) repair and body parts, EUR", "extra_exempt", EUR0,
     pubB["uplift_on_iuk_repair_body_eur"], pubE["uplift_on_iuk_repair_body_eur"],
     "room_to_raise_variant_B_iuk_exempt_2026-10-02.json uplift_on_iuk_repair_body_eur"),
    ("nparts", "Part numbers that can carry the extra (billed where it applies)", None, "#,##0",
     pubB["eligible_parts_with_flex_billing"], pubE["eligible_parts_with_flex_billing"],
     "room_to_raise_variant_B_iuk_exempt_2026-10-02.json eligible_parts_with_flex_billing (the paper says 8,447: it also counts one part kept at today's price)"),
]
for key, label, fn, nf, pOFF, pON, src in more:
    rec[key] = r
    put(ws, r, 1, label, BOLD if key in ("diff", "pct") else BODY, align=WRAP)
    for col, inc in cols_state.items():
        ci = "ABCDEFGH".index(col) + 1
        if key == "target":
            put(ws, r, ci, fn(col), BODY, nf)
        elif key in ("diff", "pct", "base"):
            put(ws, r, ci, fn(col), BOLD if key != "base" else BODY, nf)
        elif key == "t":
            put(ws, r, ci, {"B": f"={SVN}$B$12", "C": f"={SVN}$C$12", "D": f"=IF({SW}=1,C{r},B{r})"}[col], BODY, nf)
        elif key == "nparts":
            wcol = {"B": lp_rng("w_off"), "C": lp_rng("w_on"), "D": None}[col]
            put(ws, r, ci, (f"=SUMPRODUCT(--({lp_rng('elig')}=1),--({wcol}>0))" if wcol else f"=IF({SW}=1,C{r},B{r})"), BODY, nf)
        else:
            put(ws, r, ci, sp(inc, fn), BODY, nf)
    if pOFF is not None:
        put(ws, r, 5, pOFF, DATA, nf)
        put(ws, r, 6, pON, DATA, nf)
        tol = "0.0000015" if key == "t" else ("0.0000001" if key == "pct" else ("0" if key == "nparts" else "1"))
        put(ws, r, 7, f'=IF({PAPER_SETTINGS},IF(AND(ABS(B{r}-E{r})<={tol},ABS(C{r}-F{r})<={tol}),"OK","CHECK"),"n/a: settings changed")', BOLD)
    put(ws, r, 8, src, SUB)
    ws.row_dimensions[r].height = 28 if len(label) > 70 else 16
    r += 1
rec["target_row"] = rec["target"]
for col in "BCD":
    ws[f"{col}{rec['diff']}"] = f"=ROUND({col}{rec['total']}-{col}{rec['target']},2)"
rec["ident"] = r
put(ws, r, 1, "Identity: own - given up - cut + extra - total, EUR (should be 0)", BODY)
for col in "BCD":
    put(ws, r, "ABCD".index(col) + 1, f"=ROUND({col}{rec['own']}-{col}{rec['given']}-{col}{rec['cut']}+{col}{rec['extra']}-{col}{rec['total']},2)", BODY, EUR2)
r += 2

# ---- what each hold is worth (package B)
HV0 = r
put(ws, HV0, 1, "What each hold is worth, and which of them is a switch", SEC)
put(ws, HV0 + 1, 1, ("Euro given up = what the distributors would have paid on those lines at their own increase. The figure is shown "
                     "whether the hold is on or off, so you can see what each switch costs before you move it."), SUB)
header(ws, HV0 + 2, ["Hold", "Switch", "Position now", "Lines it covers", "Billed EUR it covers",
                      "Given up if held, EUR", "Given up now, EUR", "Decided?"], height=44)
HKc, RSNc = pm_rng("hk"), pm_rng("reason")
hold_rows = [
    ("Filters (oil, air, fuel, blower, strainers)", f"Summary B{SUM_SW0 + 2}", f"=IF({S1}=1,\"held\",\"follows the factory increase\")",
     f'--({HKc}=1),--({RSNc}={SVCTXT})', "Decided 11 October 2026: they follow"),
    ("Intake, exhaust and emission parts", f"Summary B{SUM_SW0 + 3}", f"=IF({S2}=1,\"held\",\"follows the factory increase\")",
     f'--({HKc}=2),--({RSNc}={SVCTXT})', "Not decided: default is the paper position"),
    ("Brake discs and drums", "not a switch", '="held"', f'--({HKc}=3),--({RSNc}={SVCTXT})',
     "Decided 11 October 2026: they stay held, same logic as the pad kits"),
    ("Other service parts in the 8 markets", "not a switch", '="held"', f'--({HKc}=0),--({RSNc}={SVCTXT})',
     "Decided 30 September 2026"),
    ("Israel body, collision and lighting", "not a switch", '="held"', f'--({RSNc}<>""),--({RSNc}<>{SVCTXT})',
     "Decided 2 October 2026"),
]
hv_rows = {}
for i, (lab, sw, pos, filt, dec) in enumerate(hold_rows):
    rr = HV0 + 3 + i
    hv_rows[lab] = rr
    put(ws, rr, 1, lab, BODY, align=WRAP)
    put(ws, rr, 2, sw, SUB)
    put(ws, rr, 3, pos, BOLD)
    put(ws, rr, 4, f"=SUMPRODUCT({filt})", BODY, NUM0)
    put(ws, rr, 5, f"=SUMPRODUCT({filt},{Bc})", BODY, EUR0)
    put(ws, rr, 6, f"=SUMPRODUCT({filt},{Bc},{Dc})", BODY, EUR0)
    put(ws, rr, 7, f'=SUMPRODUCT({filt},--({Gc}="hold"),{Bc},{Dc})', BOLD, EUR0)
    put(ws, rr, 8, dec, SUB)
hv_last = HV0 + 3 + len(hold_rows) - 1
put(ws, hv_last + 1, 1, "All holds", BOLD)
for col in (4, 5, 6, 7):
    cl = get_column_letter(col)
    put(ws, hv_last + 1, col, f"=SUM({cl}{HV0 + 3}:{cl}{hv_last})", BOLD, NUM0 if col == 4 else EUR0)
HV_TOTAL = hv_last + 1
put(ws, HV_TOTAL + 1, 1, "Base points behind the grid now (switch as set)", BOLD)
put(ws, HV_TOTAL + 1, 2, f"=IF({SW}=1,{T_ON},{T_OFF})", BOLD, "0.0000%")
put(ws, HV_TOTAL + 1, 3, ("Letting a hold go puts euro back in the book, so the base the grid needs falls. "
                          "Hold a group again and it rises."), SUB)
r = HV_TOTAL + 3

# ---- per-market totals
MT0 = r
put(ws, MT0, 1, "Per market: average increase, euro given up, euro recovered", SEC)
put(ws, MT0 + 1, 1, ("Active columns follow the switches; the last four columns show both positions of the Isuzu UK switch side by side. "
                     "Armenia and Kazakhstan: own increase only (see below)."), SUB)
header(ws, MT0 + 2, ["Market", "Code", "Billed EUR", "Own increase (average)", "Given up by holds, EUR", "of which service parts",
                      "of which Israel body, collision, lighting", "Cut by ceiling, EUR", "Recovered by extra, EUR",
                      "Increase after treatment (average)", "Total increase after treatment, EUR", "Switch OFF: increase",
                      "Switch OFF: recovered, EUR", "Switch ON: increase", "Switch ON: recovered, EUR", "Stance now"], height=58)
mt_rows = {}
first_m = MT0 + 3
for i, m in enumerate(markets):
    rr = first_m + i
    mt_rows[m] = rr
    A = f"$B{rr}"
    put(ws, rr, 1, mk_name(m), BODY)
    put(ws, rr, 2, m, DATA)
    put(ws, rr, 3, f"=SUMIF({Mc},{A},{Bc})", BODY, EUR0)
    put(ws, rr, 4, f"=SUMPRODUCT(--({Mc}={A}),{Bc},{Dc})/C{rr}", BODY, PCT2)
    put(ws, rr, 5, f'=SUMPRODUCT(--({Mc}={A}),--({Gc}="hold"),{Bc},{Dc})', BODY, EUR0)
    put(ws, rr, 6, f'=SUMPRODUCT(--({Mc}={A}),--({Gc}="hold"),--({RSNc}={SVCTXT}),{Bc},{Dc})', BODY, EUR0)
    put(ws, rr, 7, f"=E{rr}-F{rr}", BODY, EUR0)
    X = pm_rng("inc")
    put(ws, rr, 8, f'=SUMPRODUCT(--({Mc}={A}),--({Gc}="free"),{Bc},--(({Dc}-{X})>0),{Dc}-{X})', BODY, EUR0)
    put(ws, rr, 9, f'=SUMPRODUCT(--({Mc}={A}),--({Gc}="free"),{Bc},--(({X}-{Dc})>0),{X}-{Dc})', BODY, EUR0)
    put(ws, rr, 10, f"=K{rr}/C{rr}", BOLD, PCT2)
    put(ws, rr, 11, f"=SUMIF({Mc},{A},{pm_rng('eur')})", BODY, EUR0)
    for col, inc in ((12, "inc_off"), (14, "inc_on")):
        XX = pm_rng(inc)
        put(ws, rr, col, f"=SUMPRODUCT(--({Mc}={A}),{Bc},{XX})/C{rr}", BODY, PCT2)
        put(ws, rr, col + 1, f'=SUMPRODUCT(--({Mc}={A}),--({Gc}="free"),{Bc},--(({XX}-{Dc})>0),{XX}-{Dc})', BODY, EUR0)
    put(ws, rr, 16, f"={GRN}$F${GR_ST0 + i}", BODY)
last_m = first_m + len(markets) - 1
rt_ = last_m + 1
mt_total = rt_
put(ws, rt_, 1, "All markets", BOLD)
put(ws, rt_, 3, f"=SUM(C{first_m}:C{last_m})", BOLD, EUR0)
put(ws, rt_, 4, f"=SUMPRODUCT(C{first_m}:C{last_m},D{first_m}:D{last_m})/C{rt_}", BOLD, PCT2)
for col in (5, 6, 7, 8, 9, 11, 13, 15):
    cl = get_column_letter(col)
    put(ws, rt_, col, f"=SUM({cl}{first_m}:{cl}{last_m})", BOLD, EUR0)
put(ws, rt_, 10, f"=K{rt_}/C{rt_}", BOLD, PCT2)
put(ws, rt_, 12, f"=SUMPRODUCT(C{first_m}:C{last_m},L{first_m}:L{last_m})/C{rt_}", BOLD, PCT2)
put(ws, rt_, 14, f"=SUMPRODUCT(C{first_m}:C{last_m},N{first_m}:N{last_m})/C{rt_}", BOLD, PCT2)
for c in range(1, 17):
    ws.cell(rt_, c).border = Border(top=Side(style="thin", color="15233C"))
r = rt_ + 2

# ---- distributor conditions
DC0 = r
put(ws, DC0, 1, "Distributor conditions per market and parts category (decided)", SEC)
put(ws, DC0 + 1, 1, ("Hold = pays today's price. Own + extra = own increase plus the recovery extra of its grid cell. Own = own increase "
                     "only. Where Lighting says Hold, lighting parts are held whatever their category. The list itself stays one price "
                     "per part at the 'follow the factory increase' stance."), SUB)
header(ws, DC0 + 2, ["Market", "Code", "Service parts", "Repair parts", "Body and collision parts", "Lighting", "Note"], height=32)
note_of = {
    "UMI": "Service parts stay at today's price until UMI's share of leasing fleets is known (open, per the paper).",
    "UTI": "Lighting only (EUR 133,712 billed on 87 part numbers). Truck body panels are not held (delivery times, not price).",
    "IUK": "Exemption from the extra is the Summary switch (default OFF: carries the extra).",
    "UKRAINE": "Ukraine takes the normal treatment (decided).",
    "ARMENIA": "Own increase only. Whether it reaches Armenia depends on the open price-basis decision.",
    "KAZAKHSTAN": "Own increase only. Whether it reaches Kazakhstan depends on the open price-basis decision.",
    "PALESTINE": "Customer 2372 (KIMA). In the 2026 base with EUR 42,091 billed; takes the normal treatment.",
}
for i, m in enumerate(markets):
    rr = DC0 + 3 + i
    put(ws, rr, 1, mk_name(m), BODY)
    put(ws, rr, 2, m, DATA)
    if m in CIS:
        vals = ["Own, no extra"] * 4
    else:
        svc = (f'=IF(AND({S1}=0,{S2}=0),"Hold, except filters and exhaust",IF({S1}=0,"Hold, except filters",'
               f'IF({S2}=0,"Hold, except exhaust","Hold")))') if m in held_service else "Own"
        if m == EXEMPT:
            ext = f'=IF({SW}=1,"Own","Own + extra")'
        else:
            ext = "Own + extra"
        rep = ext
        body = "Hold" if m == "UMI" else ext
        light = "Hold" if m in ("UMI", "UTI") else "As its category"
        vals = [svc, rep, body, light]
    for j, v in enumerate(vals):
        put(ws, rr, 3 + j, v, BOLD if v == "Hold" else BODY)
    put(ws, rr, 7, note_of.get(m, ""), SUB)
r = DC0 + 3 + len(markets)
put(ws, r, 1, ("'Own + extra' means the extra of the market's grid cell, which at the paper settings reaches only repair and body parts "
               "with no aftermarket alternative found. The extra is capped by the part's ceiling (own factory increase + 5 points). "
               "Brake discs and drums stay at today's price in the markets that hold service parts."), SUB, align=WRAP)
ws.merge_cells(start_row=r, start_column=1, end_row=r, end_column=8)
ws.row_dimensions[r].height = 30
r += 2

# ---- Armenia and Kazakhstan
AK0 = r
put(ws, AK0, 1, "Armenia and Kazakhstan: own increase only (decided 2 October 2026)", SEC)
c1, c2 = mt_rows[CIS[0]], mt_rows[CIS[1]]
note_ak = [
    ("What the layer does", "Armenia and Kazakhstan keep their own IML/IMIT-based increase. No hold and no recovery extra applies to "
                            "them, in either switch position."),
    ("What is open", "Whether that increase actually reaches them depends on the separate decision on their price basis, which is "
                     "still open. Until it is decided, the layer counts their increase inside the +5.00% total as if it reaches them."),
]
for i, (a, b) in enumerate(note_ak):
    put(ws, AK0 + 1 + i, 1, a, BOLD)
    put(ws, AK0 + 1 + i, 2, b, BODY, align=WRAP)
    ws.merge_cells(start_row=AK0 + 1 + i, start_column=2, end_row=AK0 + 1 + i, end_column=8)
    ws.row_dimensions[AK0 + 1 + i].height = 30
header(ws, AK0 + 4, ["", "Billed EUR", "Own increase", "EUR at own increase"], height=30)
for k, (rr_src, m) in enumerate(((c1, CIS[0]), (c2, CIS[1]))):
    put(ws, AK0 + 5 + k, 1, mk_name(m), BODY)
    put(ws, AK0 + 5 + k, 2, f"=C{rr_src}", BODY, EUR0)
    put(ws, AK0 + 5 + k, 3, f"=J{rr_src}", BODY, PCT2)
    put(ws, AK0 + 5 + k, 4, f"=K{rr_src}", BODY, EUR0)
put(ws, AK0 + 7, 1, "Both", BOLD)
put(ws, AK0 + 7, 2, f"=B{AK0 + 5}+B{AK0 + 6}", BOLD, EUR0)
put(ws, AK0 + 7, 3, f"=D{AK0 + 7}/B{AK0 + 7}", BOLD, PCT2)
put(ws, AK0 + 7, 4, f"=D{AK0 + 5}+D{AK0 + 6}", BOLD, EUR0)
put(ws, AK0 + 8, 1, "If it does not reach them: total increase would be, EUR", BODY)
put(ws, AK0 + 8, 2, f"=D{rec['total']}-D{AK0 + 7}", BOLD, EUR0)
put(ws, AK0 + 8, 3, f"=B{AK0 + 8}/D{rec['base']}", BOLD, PCT3)
put(ws, AK0 + 8, 4, "weighted increase on the whole billed base", SUB)
ak_total_row, ak_nocis_row = AK0 + 7, AK0 + 8
r = AK0 + 10

# ---- labels corrected in this draft (package H)
LB0 = r
put(ws, LB0, 1, "Labels corrected in this draft (11 October 2026)", SEC)
labels = [
    ("'By market' on the Summary sheet",
     "That table shows the proposal before the market decisions. It is now labelled so, and points to this sheet and to the stance "
     "sheets for the picture after them."),
    ("Names on shared sheets",
     "Two lines used to name a person and to put the decision on that person. They now read 'decided 30 September 2026' "
     "(brake pad kits, on the Summary sheet, the Read me and the Review lists) and 'decided 2 October 2026' "
     "(Armenia and Kazakhstan, above). No personal name appears on a sheet that leaves the desk."),
    ("Reference dealer price: 1.785 or 2.19",
     "The workbook of 29 September says our list price times 1.785, built as a 1.40 step to the dealer and a 1.275 step to the "
     "customer, which is the same as a 28.6% margin and then a 21.6% margin. The policy paper of 2 October says our list price "
     "times 2.19 and states in its own words that the September papers used 1.785 and that their ratios are not carried over. "
     "The 2.19 basis is the later and the decided one: it reads the channel as a 37% margin at the distributor step and 25% to "
     "27.5% at the dealer step, which multiplies out to between 2.15 and 2.19. For anything dated 2 October 2026 or later, 2.19 is "
     "the right figure and the paper is correct; the 1.785 in the 29 September workbook is not wrong for its own date, it is "
     "superseded. The paper is not changed by this workbook. The basis itself is still marked provisional in the paper."),
]
for i, (a, b) in enumerate(labels):
    rr = LB0 + 1 + i
    put(ws, rr, 1, a, BOLD, align=WRAP)
    put(ws, rr, 2, b, BODY, align=WRAP)
    ws.merge_cells(start_row=rr, start_column=2, end_row=rr, end_column=8)
    ws.row_dimensions[rr].height = 14 * max(2, -(-len(b) // 95)) + 4
r = LB0 + 1 + len(labels) + 1

# ---- checks
CK0 = r
put(ws, CK0, 1, "Checks: every line should read OK", SEC)
header(ws, CK0 + 1, ["Check", "Value", "Expected", "Result"], height=24)
SVc = SVN
ck = [
    ("Billed base in the layer equals the billed base of the proposal (EUR)", f"=SUM({Bc})", f"=SUM(Proposal!$G$2:$G${PROP_LAST})", EUR2,
     "ABS({v}-{e})<0.05"),
    ("Every part number of the proposal is on 'Layer by part'", f"=COUNTA({lp_rng('pn')})", f"=COUNTA(Proposal!$A$2:$A${PROP_LAST})", "#,##0",
     "{v}={e}"),
    ("Every part x market row finds its part (rows with an error)", f"=SUMPRODUCT(--ISERROR({pm_rng('lprow')}))", 0, "0", "{v}={e}"),
    ("Every part finds its rows on the part x market sheet (pointers off)", f"=SUM({lp_rng('ptr')})", 0, "0", "{v}={e}"),
    ("Own increase in the layer adds up to the proposal's extra euro (Summary B13)", f"=SUMPRODUCT({Bc},{Dc})", "=Summary!$B$13", EUR2,
     "ABS({v}-{e})<0.05"),
    ("Total after market treatment equals the target: switch OFF (EUR)", f"=B{rec['total']}", f"=B{rec['target']}", EUR2, "ABS({v}-{e})<0.5"),
    ("Total after market treatment equals the target: switch ON (EUR)", f"=C{rec['total']}", f"=C{rec['target']}", EUR2, "ABS({v}-{e})<0.5"),
    ("Weighted increase equals the Summary target: switch OFF", f"=B{rec['pct']}", "=Summary!$B$5", PCT3, "ABS({v}-{e})<0.000000001"),
    ("Weighted increase equals the Summary target: switch ON", f"=C{rec['pct']}", "=Summary!$B$5", PCT3, "ABS({v}-{e})<0.000000001"),
    ("Own - given up - cut + extra = total, both positions (largest gap, EUR)", f"=MAX(ABS(B{rec['ident']}),ABS(C{rec['ident']}))", 0, EUR2,
     "{v}<0.01"),
    ("Solver lands on the recovery needed: switch OFF and ON (largest gap, EUR)", f"=MAX(ABS({SVc}$B$15),ABS({SVc}$C$15))", 0, EUR2, "{v}<0.01"),
    ("Solver can reach the target within the ceiling (both positions)", f'=IF(AND({SVc}$B$16="yes",{SVc}$C$16="yes"),1,0)', 1, "0", "{v}={e}"),
    ("Armenia and Kazakhstan: no hold, no extra, own increase, both positions (EUR vs own increase)",
     (f'=SUMPRODUCT(--({Gc}="own only"),{Bc},ABS({pm_rng("inc_off")}-{Dc}))+SUMPRODUCT(--({Gc}="own only"),{Bc},ABS({pm_rng("inc_on")}-{Dc}))'),
     0, EUR2, "ABS({v})<0.005"),
    ("Exempt market gets no extra when the switch is ON (EUR)", f"=C{rec['iuk']}", 0, EUR2, "ABS({v})<0.005"),
    ("Per-market table adds up to the reconciliation (recovered, given up, total; largest gap EUR)",
     f"=ROUND(MAX(ABS(I{mt_total}-D{rec['extra']}),ABS(E{mt_total}-D{rec['given']}),ABS(K{mt_total}-D{rec['total']})),2)", 0, EUR2, "{v}<0.5"),
    ("Published figures reproduced at the paper settings (rows marked in column G above)",
     f'=COUNTIF(G{RR0 + 2}:G{rec["nparts"]},"CHECK")', 0, "0", "{v}={e}"),
    ("Summary switch holds 0 or 1", f"={SW}", "0 or 1", "0", "OR({v}=0,{v}=1)"),
    # ---- new checks (packages B, D, E)
    ("Every part x market line carries exactly one reason code (lines counted by code vs lines on the sheet)",
     f"={GR_CODE_CHK}", '"OK"', None, '{v}="OK"'),
    ("No line carries a reason code the list does not know (rows that find no code)",
     f"=SUMPRODUCT(--ISNA(MATCH({RC},{CODE_RNG},0)))", 0, "0", "{v}={e}"),
    ("The twelve grid cells add up to the recovery extra on the reconciliation (EUR)",
     f"=ROUND(ABS({GRN}$F${GR_CELL_TOTAL}-D{rec['extra']}),2)", 0, EUR2, "{v}<0.5"),
    ("Lubricant part numbers take no increase anywhere (EUR away from today's price)",
     f'=SUMPRODUCT(--({RC}="LUBRICANT_NONE"),{Bc},ABS({pm_rng("inc")}))', 0, EUR2, "ABS({v})<0.005"),
    ("Brake pad kit lines take no increase anywhere (EUR away from today's price)",
     f'=SUMPRODUCT(--({RC}="HOLD_PAD"),{Bc},ABS({pm_rng("inc")}))', 0, EUR2, "ABS({v})<0.005"),
    ("Every held line pays today's price (EUR away from today's price)",
     f'=SUMPRODUCT(--({Gc}="hold"),{Bc},ABS({pm_rng("inc")}))', 0, EUR2, "ABS({v})<0.005"),
    ("Brake discs and drums stay held in the markets that hold service parts (lines released)",
     f'=SUMPRODUCT(--({HKc}=3),--({RSNc}={SVCTXT}),--({Gc}<>"hold"))', 0, "0", "{v}={e}"),
    ("Filters follow the switch (lines held when the switch says follow)",
     f'=IF({S1}=1,0,SUMPRODUCT(--({HKc}=1),--({RSNc}={SVCTXT}),--({Gc}="hold")))', 0, "0", "{v}={e}"),
    ("Intake, exhaust and emission parts follow their switch (lines held when the switch says follow)",
     f'=IF({S2}=1,0,SUMPRODUCT(--({HKc}=2),--({RSNc}={SVCTXT}),--({Gc}="hold")))', 0, "0", "{v}={e}"),
    ("Service parts get no extra while the extra is limited to parts with no alternative found (EUR)",
     f'=IF({SELIG}=1,B{rec["svc"]}+C{rec["svc"]},0)', 0, EUR2, "ABS({v})<0.005"),
    ("Every market has a stance the grid knows (markets with no stance number)",
     f"=SUMPRODUCT(--ISERROR({GR_SI}))", 0, "0", "{v}={e}"),
    ("Scenario is A or B", f"={SSCEN}", '"A or B"', None, 'OR({v}="A",{v}="B")'),
    ("All switches hold a number", f"=COUNT({S1},{S2},{SBODY_UTI},{SBODY_IUK},{SBODY_REST},{SELIG})", 6, "0", "{v}={e}"),
]
ck_first = CK0 + 2
for i, (lab, v, e, nf, cond) in enumerate(ck):
    rr = ck_first + i
    put(ws, rr, 1, lab, BODY, align=WRAP)
    put(ws, rr, 2, v, BODY, nf)
    put(ws, rr, 3, e, BODY, nf)
    put(ws, rr, 4, '=IF(' + cond.format(v=f"B{rr}", e=f"C{rr}") + ',"OK","CHECK")', BOLD)
    ws.row_dimensions[rr].height = 28 if len(lab) > 78 else 16
ck_last = ck_first + len(ck) - 1
put(ws, ck_last + 1, 1, "All market layer checks", BOLD)
put(ws, ck_last + 1, 4, f'=IF(COUNTIF(D{ck_first}:D{ck_last},"OK")={len(ck)},"OK","CHECK")', BOLD)
ALLCK = f"{ML}$D${ck_last + 1}"
ws.conditional_formatting.add(f"D{ck_first}:D{ck_last + 1}", CellIsRule(operator="equal", formula=['"CHECK"'], font=RED))
ws.conditional_formatting.add(f"D{ck_first}:D{ck_last + 1}", CellIsRule(operator="equal", formula=['"OK"'], font=GREEN))
ws.conditional_formatting.add(f"G{RR0 + 2}:G{rec['nparts']}", CellIsRule(operator="equal", formula=['"CHECK"'], font=RED))
ws.conditional_formatting.add(f"G{RR0 + 2}:G{rec['nparts']}", CellIsRule(operator="equal", formula=['"OK"'], font=GREEN))
r = ck_last + 3

# ---- sources and how to read
SR0 = r
put(ws, SR0, 1, "Where each block of values comes from", SEC)
sources = [
    ("Part numbers and descriptions (blue, 'Layer by part')", "Copied as values from the Proposal sheet of this workbook, in part number order. Own increase, own factory increase, "
     "current list, class margin and pad kit flag are read live from the Proposal sheet by part number."),
    ("Parts category, 'no aftermarket alternative found', lubricant flag (blue, 'Layer by part')",
     "Copied as values from 02_dashboards/pricing/_build/price_5pct_proposal_2026-09-29/room_to_raise_2026-10-02/room_to_raise_by_part_2026-10-02.csv "
     "(columns segment, captive_strict, lubricant), built by build_room_to_raise_20261002.py on the approved parts categories of 2 October 2026. "
     "Service = scheduled-service parts (BVP cross-reference service categories and the master service flag); body = family Accident and Body; repair = the rest. "
     "No aftermarket alternative found = no usable competitor part number, no aftermarket price, no BVP alternative, not a competitive family, not measured lost or contested."),
    ("Parts role and hold group (blue, 'Layer by part')",
     f"Role: 01_data/01_Pricing/{ROLE_CSV.name}, column pricing_role, joined on the parts category of the release "
     f"01_data/00_derived/_releases/{AIM_RELEASE.name}. That role file says status {ROLE_STATUS}: a working view, not a locked decision. "
     "Hold group: the same release. Filter = the category or sub-category contains the word Filter; intake, exhaust and emission = that "
     "whole parts category; brake disc or drum = the discs and drums sub-categories (clutch discs are not in it)."),
    ("Billed EUR per part and market (blue, 'Layer by part and market')",
     "Copied as values: 47,617 in-scope lines of 01_data/00_derived/price_bp_weighted_compare_pn.csv (both factory prices present), summed per part number and "
     "distributor code (distributor_dimension.csv): 45,581 rows, EUR 32,595,852.63. Agrees with room_to_raise_by_part_market_2026-10-02.csv within its 6-significant-digit rounding."),
    ("Hold decided in the paper (blue, 'Layer by part and market')",
     "Copied as values from room_to_raise_by_part_market_2026-10-02.csv (column hold_reason): service parts in 8 markets (market_exercise_decisions_2026-09-30.json), "
     "Israel D-Max distributor body, collision and lighting, Israel trucks distributor lighting (2 Oct 2026 paper). 7,833 rows. "
     "Whether a line is still held today also depends on the filter and exhaust switches on the Summary sheet."),
    ("Fleet, service share, what the distributor pays, dealer reaction (blue, stance sheets)",
     "Fleet 2023 to 2025 as the paper counted them: 01_data/00_derived/gps_spu_by_distributor.csv. Fleet 2025 and 2026 like for like: "
     "01_data/00_derived/UIO_carpark_for_GPS_recalc_2026-07-30.csv. Service share, what the distributor pays against list and the measured "
     "dealer reaction: market_facts_2026-09-30.json in the build folder, from the capture and billing files it names."),
    ("Published figures for comparison (blue, columns E and F above)",
     "room_to_raise_variant_B_iuk_exempt_2026-10-02.json (as published and Isuzu UK exempt), the 2 Oct 2026 paper (EUR 388,914) and "
     "room_to_raise_scenarios_2026-10-02.csv (ceiling cut EUR 7,654). They are compared only while every switch sits at its paper position."),
]
for i, (a, b) in enumerate(sources):
    rr = SR0 + 1 + i
    put(ws, rr, 1, a, BOLD, align=WRAP)
    put(ws, rr, 2, b, BODY, align=WRAP)
    ws.merge_cells(start_row=rr, start_column=2, end_row=rr, end_column=8)
    ws.row_dimensions[rr].height = 14 * max(2, -(-len(b) // 95)) + 4
r = SR0 + 1 + len(sources) + 1
put(ws, r, 1, "How it works", SEC)
how = [
    "1. Every line on 'Layer by part and market' is one of: held (pays today's price), Armenia or Kazakhstan (own increase only), or free (own increase, plus the extra of its grid cell).",
    "2. The extra is one base number of points times the multiplier of the market's stance and the part's role, limited by the part's ceiling (own factory increase + 5 points). 'Layer solver' finds the base so the total lands on the target.",
    "3. Switch OFF: Isuzu UK pays the list increase like everyone else. Switch ON: Isuzu UK pays its own increase (limited by the ceiling) on every part and the other free markets carry a higher base.",
    "4. The list price per part (sheet 'Layer by part', column New list EUR) is the price for a market that follows the factory increase; holds, stances and the exemption are distributor conditions on top of it.",
    "5. Pad kits stay at today's price (Summary B9); the two lubricant part numbers carry no increase and no extra. Change any switch on the Summary sheet and everything re-solves.",
]
for i, t in enumerate(how):
    rr = r + 1 + i
    put(ws, rr, 1, t, BODY, align=WRAP)
    ws.merge_cells(start_row=rr, start_column=1, end_row=rr, end_column=8)
    ws.row_dimensions[rr].height = 30
for col, wd in zip("ABCDEFGHIJKLMNOP", [66, 16, 18, 17, 16, 16, 18, 22, 16, 16, 18, 14, 16, 14, 16, 22]):
    ws.column_dimensions[col].width = wd
ws.freeze_panes = "A4"

# =================================================================== sheet: Margin and volume (package F)
ws = ws_mv
put(ws, 1, 1, "Margin and volume: what the increase does per market and per parts role", TITLE)
put(ws, 2, 1, ("Class margin change is measured the same way as on the Proposal sheet: the margin the price class carries, after the "
               "factory price moved and our price moved. Volume effects use the three scenarios on the Summary sheet. Where a market "
               "has its own measured dealer reaction it is shown in its own column; a pooled figure is never printed as if it had been "
               "measured in that market."), SUB)
RIDX, MCHG, INCc, EURVS = pm_rng("ridx"), pm_rng("mchg"), pm_rng("inc"), pm_rng("eur_vs")
MV_HEAD = ["Market", "Code", "Parts role", "Billed EUR", "Average increase", "Increase in EUR",
           "Recovered by the extra, EUR", "Class margin change (points)", "Billed EUR on parts losing more than 1 margin point",
           "No reaction: EUR", "Central reaction (-0.1584): EUR", "Stress reaction (-0.81): EUR",
           "Measured reaction in this market", "At the measured reaction: EUR"]
header(ws, 4, MV_HEAD, height=86)
MV0 = 5
beta_of = {m: stance_facts[m]["beta"] for m in markets}
for i, m in enumerate(markets):
    for j, role in enumerate(ROLES):
        rr = MV0 + i * 4 + j
        A, R = f"$B{rr}", f"$C{rr}"
        sel = f'--({Mc}={A}),--({RIDX}={j + 1})'
        put(ws, rr, 1, mk_name(m) if j == 0 else "", BODY)
        put(ws, rr, 2, m, DATA)
        put(ws, rr, 3, ROLE_LABEL[role], BODY)
        put(ws, rr, 4, f"=SUMPRODUCT({sel},{Bc})", BODY, EUR0)
        put(ws, rr, 5, f"=IF(D{rr}=0,0,F{rr}/D{rr})", BODY, PCT2)
        put(ws, rr, 6, f"=SUMPRODUCT({sel},{Bc},{INCc})", BODY, EUR0)
        put(ws, rr, 7, f'=SUMPRODUCT({sel},--({Gc}="free"),--({EURVS}>0),{EURVS})', BODY, EUR0)
        put(ws, rr, 8, f"=IF(D{rr}=0,0,SUMPRODUCT({sel},{Bc},{MCHG})/D{rr})", BODY, PTS)
        put(ws, rr, 9, f"=SUMPRODUCT({sel},{Bc},--({MCHG}<-0.01))", BODY, EUR0)
        for k, bcell in enumerate(("Summary!$B$32", "Summary!$B$33", "Summary!$B$34")):
            put(ws, rr, 10 + k, f"=SUMPRODUCT({sel},{Bc},(1+{INCc})*(1+{bcell}*{INCc}))-D{rr}", BODY, EUR0)
        b = beta_of[m]
        if b is None:
            put(ws, rr, 13, "not measured here", SUB)
            put(ws, rr, 14, None, BODY, EUR0)
        else:
            put(ws, rr, 13, float(b), DATA, NUM4)
            put(ws, rr, 14, f"=SUMPRODUCT({sel},{Bc},(1+{INCc})*(1+M{rr}*{INCc}))-D{rr}", BODY, EUR0)
    ws.cell(MV0 + i * 4, 1).font = BOLD
MV_LAST = MV0 + len(markets) * 4 - 1
rt = MV_LAST + 1
put(ws, rt, 1, "All markets and roles", BOLD)
for col in (4, 6, 7, 9, 10, 11, 12, 14):
    cl = get_column_letter(col)
    put(ws, rt, col, f"=SUM({cl}{MV0}:{cl}{MV_LAST})", BOLD, EUR0)
put(ws, rt, 5, f"=F{rt}/D{rt}", BOLD, PCT2)
put(ws, rt, 8, f"=SUMPRODUCT(D{MV0}:D{MV_LAST},H{MV0}:H{MV_LAST})/D{rt}", BOLD, PTS)
MV_TOTAL = rt
r = rt + 2
r = note_block(ws, r, [
    "Average increase = increase in euro divided by billed euro, on the same lines.",
    "Class margin change = the margin of the price class after the factory price moved and our price moved, against the margin it "
    "carries today, in points. A part held at today's price while its factory price rose loses margin; that is why the held markets "
    f"show a loss here. {int(live_p['Class margin'].isna().sum()):,} part numbers carry no price class, so they count as no change.",
    "Volume effects: the dealer reaction is the change in dealer purchases for one point of our price. No reaction = 0. The central "
    "and stress figures on the Summary sheet are four markets pooled; they are a network view, not a measurement of any one market. "
    "Only the last two columns show a figure measured in the market itself, and they are empty where it was not measured.",
    "Euro after a volume effect = billed euro at the new price and the new volume, less billed euro today.",
], width=14, height=30)
for col, wd in zip("ABCDEFGHIJKLMN", [30, 12, 26, 14, 13, 14, 16, 15, 20, 15, 18, 16, 16, 16]):
    ws.column_dimensions[col].width = wd
ws.freeze_panes = "D5"

# =================================================================== package G: the test design
rng = np.random.default_rng(SEED)
lp_role = dict(zip(parts.pn, parts.ridx))
lp_rolelab = dict(zip(parts.pn, parts.role_label))
lp_elig = dict(zip(parts.pn, ((parts.segment.isin(["repair", "body"])) & (parts.captive_strict == 1)
                              & (parts.padkit != 1) & (parts.lubricant != 1)).astype(int)))
# at the delivered settings: filters follow (S1 = 0), intake/exhaust/emission stay held (S2 = 1)
released = pm.reason.eq(R_SERVICE) & pm.hk.eq(1)
free_line = (~pm.reason.ne("") | released) & ~pm.db.isin(CIS)
test_rows = []
for m in TEST_MARKETS:
    sel = pm[(pm.db == m) & free_line & pm.pn.map(lp_elig).eq(1)].copy()
    if not len(sel):
        continue
    sel["role"] = sel.pn.map(lp_role)
    sel["band"] = 0
    for rid, gsel in sel.groupby("role"):
        q = gsel.billed.rank(pct=True)
        sel.loc[gsel.index, "band"] = np.searchsorted([0.25, 0.5, 0.75], q.to_numpy(), side="right") + 1
    # deal the parts out largest first: the arm that is behind on billed euro takes the next one, and inside a
    # stratum (role x billed band) the arms stay level on count. Ties are broken by the seeded generator.
    sel["arm"] = -1
    mkt_tot = {0: 0.0, 1: 0.0, 2: 0.0}
    strat = {}
    jitter = rng.permutation(len(sel)) * 1e-9
    order = sel.sort_values("billed", ascending=False).index.to_numpy()
    for n_, idx in enumerate(order):
        key = (int(sel.role[idx]), int(sel.band[idx]))
        cnt = strat.setdefault(key, {0: 0, 1: 0, 2: 0})
        arm = min((0, 1, 2), key=lambda a: (mkt_tot[a] + jitter[n_] * a, cnt[a]))
        cnt[arm] += 1
        mkt_tot[arm] += float(sel.billed[idx])
        sel.loc[idx, "arm"] = arm
    sel["arm"] = sel.arm.astype(int)
    spread = (max(mkt_tot.values()) - min(mkt_tot.values())) / (sum(mkt_tot.values()) / 3)
    print(f"  {m}: {len(sel):,} parts in the test, billed per arm "
          + ", ".join(f"{mkt_tot[a]:,.0f}" for a in (0, 1, 2)) + f" (spread {spread:.2%})")
    for t_ in sel.itertuples(index=False):
        test_rows.append({"pn": t_.pn, "mkt": m, "role": lp_rolelab[t_.pn], "band": int(t_.band),
                          "billed": float(t_.billed), "arm": int(t_.arm)})
test = pd.DataFrame(test_rows)
ARM_LABEL = {0: "A: own increase", 1: "B: own increase + 2 points", 2: "C: own increase + 4 points"}
ARM_PTS = {0: 0.0, 1: 0.02, 2: 0.04}

# pre-registered read-out: monthly sales-to-dealer units per part number
MONTH_SRC = {"IRELAND": ["dealer_sellout_long_IRELAND_CY2025.csv", "dealer_sellout_long_IRELAND_CY2026YTD.csv"],
             "PORTUGAL": ["dealer_sellout_long_PORTUGAL_CY2025.csv", "dealer_sellout_long_PORTUGAL_CY2026YTD.csv"],
             "ITUK": ["dealer_sellout_long_ITUK_CY2025.csv", "dealer_sellout_long_ITUK_CY2026YTD.csv"]}
readout = {}
for m in TEST_MARKETS:
    info = {"market": m, "months": [], "grain": "", "note": "", "mde": None, "n_parts": 0}
    files = MONTH_SRC.get(m, [])
    frames = []
    for fn in files:
        p = DERIVED / fn
        if not p.exists():
            info["note"] = f"no sales-to-dealer file on disk ({fn})"
            continue
        d = pd.read_csv(p, dtype={"part_number": str}, usecols=["part_number", "period", "period_grain", "qty"])
        frames.append(d)
    if not frames:
        info["note"] = info["note"] or "no sales-to-dealer file on disk"
        readout[m] = info
        continue
    d = pd.concat(frames, ignore_index=True)
    grains = sorted(set(d.period_grain.dropna()))
    info["grain"] = ", ".join(grains)
    dm = d[d.period_grain == "month"]
    if not len(dm):
        info["note"] = ("the sales-to-dealer file for this market is a year total per part number, not months. The raw workbook "
                        "01_data/12_raw/dealer_sales/ITUK/ITUK_Dealer_Purchases_by_PN_2023_2026YTD_Aug.xlsx holds a month grid, but "
                        "it is not in the normalised file, so no power figure is computed here." if m == "ITUK"
                        else "no monthly sales-to-dealer rows for this market; no power figure is computed.")
        readout[m] = info
        continue
    dm = dm.assign(pn=zpad(dm.part_number), qty=pd.to_numeric(dm.qty, errors="coerce").fillna(0))
    piv = dm.pivot_table(index="pn", columns="period", values="qty", aggfunc="sum").fillna(0)
    months = sorted(piv.columns)
    info["months"] = [months[0], months[-1], len(months)]
    want = set(test.pn[test.mkt == m]) if len(test) else set()
    piv = piv.loc[piv.index.intersection(want)]
    info["n_parts"] = int(len(piv))
    if len(months) >= 12 and len(piv) >= 30:
        post, pre = months[-6:], months[-12:-6]
        dlog = np.log(piv[post].sum(axis=1) + 0.5) - np.log(piv[pre].sum(axis=1) + 0.5)
        dlog = dlog.replace([np.inf, -np.inf], np.nan).dropna().to_numpy()
        n_each = max(int(len(dlog) // 3), 1)
        diffs = []
        for _ in range(4000):
            perm = rng.permutation(dlog)
            diffs.append(perm[:n_each].mean() - perm[n_each:2 * n_each].mean())
        sd = float(np.std(diffs, ddof=1))
        info["mde"] = {"sd_of_difference_log_units": sd, "mde_log_units": 2.80 * sd,
                       "mde_dealer_reaction": 2.80 * sd / 0.04, "parts_with_months": int(len(dlog)),
                       "pre": [pre[0], pre[-1]], "post": [post[0], post[-1]], "draws": 4000}
    else:
        info["note"] = (f"only {len(months)} months and {len(piv)} of the test parts carry monthly rows: too thin to simulate "
                        f"a detectable effect. No power figure is invented.")
    readout[m] = info

ws = ws_td
put(ws, 1, 1, "Test design: splitting parts inside a market to measure what a price step does", TITLE)
put(ws, 2, 1, ("The split is inside each market, by part number, never across markets: every market keeps its own stance, and the arms "
               "sit inside it. Parts that carry the extra are sorted by their role and by how much the distributor bought of them, and "
               "then dealt into three arms with a fixed random seed so that each arm holds about the same billed euro."), SUB)
r = 4
put(ws, r, 1, "Settings", SEC)
put(ws, r + 1, 1, "Markets in the test", BODY)
put(ws, r + 1, 2, ", ".join(TEST_MARKETS), DATA)
put(ws, r + 1, 4, "Isuzu UK is left out: it keeps its price and it is the one market with a measured dealer reaction already.", SUB)
put(ws, r + 2, 1, "Random seed", BODY)
put(ws, r + 2, 2, SEED, DATA, "0")
put(ws, r + 3, 1, "Arms", BODY)
put(ws, r + 3, 2, "own increase / own increase + 2 points / own increase + 4 points", DATA)
put(ws, r + 4, 1, "Stratified by", BODY)
put(ws, r + 4, 2, "parts role (four) and billed band (four quarters inside the role)", DATA)
put(ws, r + 5, 1, "Built on the settings delivered with this workbook", BODY)
put(ws, r + 5, 2, "filters follow the factory increase, intake and exhaust held, scenario A", DATA)
r += 7
put(ws, r, 1, "What the split looks like", SEC)
header(ws, r + 1, ["Market", "Arm", "Part numbers", "Billed EUR", "Share of the market's test billing",
                   "Extra points this arm adds", "Average increase this arm would carry"], height=44)
td0 = r + 2
rr = td0
mkt_avg = {}
for m in TEST_MARKETS:
    sub = test[test.mkt == m]
    tot = float(sub.billed.sum())
    for a in (0, 1, 2):
        s2 = sub[sub.arm == a]
        put(ws, rr, 1, mk_name(m) if a == 0 else "", BOLD if a == 0 else BODY)
        put(ws, rr, 2, ARM_LABEL[a], BODY)
        put(ws, rr, 3, int(len(s2)), DATA, NUM0)
        put(ws, rr, 4, float(s2.billed.sum()), DATA, EUR0)
        put(ws, rr, 5, (float(s2.billed.sum()) / tot) if tot else None, DATA, PCT1)
        put(ws, rr, 6, ARM_PTS[a], DATA, PCT2)
        rr += 1
    mkt_avg[m] = sum(ARM_PTS[a] * float(sub.billed[sub.arm == a].sum()) for a in (0, 1, 2)) / tot if tot else 0.0
td_last = rr - 1
for i, m in enumerate(TEST_MARKETS):
    base_r = td0 + i * 3
    for a in range(3):
        put(ws, base_r + a, 7, f"={GR_BASE}+F{base_r + a}", BODY, PCT2)
r = td_last + 2
put(ws, r, 1, "What the test does to the market total", SEC)
header(ws, r + 1, ["Market", "Billed EUR in the test", "Average extra the arms add", "The market's extra on the Market layer",
                   "Difference"], height=44)
for i, m in enumerate(TEST_MARKETS):
    rr = r + 2 + i
    put(ws, rr, 1, mk_name(m), BODY)
    put(ws, rr, 2, float(test.billed[test.mkt == m].sum()) if len(test) else 0.0, DATA, EUR0)
    put(ws, rr, 3, mkt_avg.get(m, 0.0), DATA, PCT2)
    put(ws, rr, 4, f"={ML}$I${mt_rows[m]}/{ML}$C${mt_rows[m]}" if m in mt_rows else None, BODY, PCT2)
    put(ws, rr, 5, f"=C{rr}-D{rr}", BOLD, PCT2)
r = r + 2 + len(TEST_MARKETS)
r = note_block(ws, r + 1, [
    "The three arms as written (own increase, own + 2 points, own + 4 points) add 2 points on average. The market's own extra on the "
    "'Market layer' sheet is a different number, so running the arms as written moves that market's total by the difference above. "
    "Either the arms are centred on the market's own extra, or the market total moves: that is a decision, and it is not made here.",
], width=7, height=40)
r += 1
put(ws, r, 1, "The pre-registered read-out", SEC)
header(ws, r + 1, ["Market", "Monthly sales to dealer, units per part number", "Months on file", "Test parts with months",
                   "Spread of the six-month change (standard deviation, log units)",
                   "Smallest change the test could see (log units)", "The same as a dealer reaction", "Note"], height=58)
rd0 = r + 2
for i, m in enumerate(TEST_MARKETS):
    rr = rd0 + i
    info = readout[m]
    put(ws, rr, 1, mk_name(m), BODY)
    put(ws, rr, 2, ("months on file" if info["mde"] else ("year totals only" if info["grain"] else "no file")), DATA)
    put(ws, rr, 3, (f"{info['months'][0]} to {info['months'][1]} ({info['months'][2]})" if info["months"] else ""), DATA)
    put(ws, rr, 4, info["n_parts"], DATA, NUM0)
    if info["mde"]:
        put(ws, rr, 5, info["mde"]["sd_of_difference_log_units"], DATA, NUM4)
        put(ws, rr, 6, info["mde"]["mde_log_units"], DATA, NUM4)
        put(ws, rr, 7, info["mde"]["mde_dealer_reaction"], DATA, NUM2)
        put(ws, rr, 8, (f"Simulated on the real months: the six months {info['mde']['post'][0]} to {info['mde']['post'][1]} against "
                        f"the six before them, with no price change in between, {info['mde']['draws']:,} draws. 80% power, 5% two-sided, "
                        f"arm C against arm A, 4 points of price apart."), SUB, align=WRAP)
    else:
        put(ws, rr, 8, info["note"], SUB, align=WRAP)
    ws.row_dimensions[rr].height = 40
r = rd0 + len(TEST_MARKETS) + 1
r = note_block(ws, r, [
    "Read-out: monthly units per part number that the distributor sold to its dealers, six months before the change and six months "
    "after it, from the sales-to-dealer files in 01_data/12_raw/dealer_sales (through the normalised files in 01_data/00_derived). "
    "The comparison is arm C against arm A inside the same market, so anything that moves the whole market drops out.",
    "The smallest change the test could see is measured by simulation on the real months of each market: the same parts, the same "
    "arm sizes, a period with no price change, re-drawn thousands of times. Where a market has no monthly file, nothing is computed "
    "and nothing is assumed.",
], width=8, height=42)
r += 1
put(ws, r, 1, "Part number, market and arm", SEC)
put(ws, r + 1, 1, "One row per part number and market. Billed euro is the last twelve months, the same base as the rest of the workbook.", SUB)
header(ws, r + 2, ["Part number", "Market", "Parts role", "Billed band (1 smallest to 4 largest)", "Billed EUR", "Arm"], height=44)
tl0 = r + 3
for i, t_ in enumerate(test.itertuples(index=False)):
    rr = tl0 + i
    put(ws, rr, 1, t_.pn, DATA)
    put(ws, rr, 2, t_.mkt, DATA)
    put(ws, rr, 3, t_.role, DATA)
    put(ws, rr, 4, t_.band, DATA, "0")
    put(ws, rr, 5, t_.billed, DATA, EUR2)
    put(ws, rr, 6, ARM_LABEL[t_.arm], DATA)
TL_LAST = tl0 + len(test) - 1
for col, wd in zip("ABCDEFGH", [30, 30, 22, 22, 28, 24, 22, 60]):
    ws.column_dimensions[col].width = wd
ws.auto_filter.ref = f"A{tl0 - 1}:F{TL_LAST}"

# =================================================================== sheet: Repair rules (package H)
ws = ws_rr
put(ws, 1, 1, "Repair rules that decide whether a damaged vehicle is repaired", TITLE)
put(ws, 2, 1, ("Four rules that decide whether an insurer pays for a repair or writes the vehicle off. They matter for body and "
               "collision parts: where a vehicle is written off sooner, fewer body parts are bought. Each line is a public secondary "
               "source. Verify it before quoting it to anyone outside."), SUB)
header(ws, 4, ["Where", "The rule", "What it means for body parts", "Status"], height=32)
rules = [
    ("Israel", "A vehicle is a total loss at 60% of its value. Insurers treat it as a constructive total loss from about 50% to 55%, "
               "on the policy wording. Verified only for vehicles up to 3.5 tonnes.",
     "Damage reaches the write-off line early, so fewer large body repairs on light vehicles.",
     "Public secondary source, verify before quoting. The 3.5 tonne limit means it is not confirmed for trucks."),
    ("Germany", "On a liability claim the owner may have the vehicle repaired up to 130% of its replacement value.",
     "Repairs go ahead that would be written off elsewhere, so more body parts are bought.",
     "Public secondary source, verify before quoting."),
    ("United Kingdom", "No fixed rule. Insurers write a vehicle off somewhere between about 50% and 80% of its value, each on its own "
                       "policy.",
     "The write-off line is not a number we can price against; it moves by insurer.",
     "Public secondary source, verify before quoting."),
    ("European Union", "Directive (EU) 2024/2823 on design protection lets other brands make and sell visible repair parts. Member "
                       "states transpose it by 9 December 2027; design protection already in force runs to 9 December 2032.",
     "From those dates other brands may legally copy visible body panels, lights and glass, so competition on those parts grows.",
     "Public secondary source, verify before quoting."),
]
for i, (a, b, c_, d_) in enumerate(rules):
    r = 5 + i
    put(ws, r, 1, a, BOLD, align=WRAP)
    put(ws, r, 2, b, BODY, align=WRAP)
    put(ws, r, 3, c_, BODY, align=WRAP)
    put(ws, r, 4, d_, SUB, align=WRAP)
    ws.row_dimensions[r].height = 70
r = 10
r = note_block(ws, r, [
    "Not covered here: the Nordic markets, Portugal, Ireland and Belgium. No rule has been read for them, so nothing is assumed "
    "about how soon a vehicle is written off there.",
    "None of these four lines carries a euro figure in this workbook. They are background for the body and collision parts decision, "
    "not an input to the increase.",
], width=4, height=32)
for col, wd in zip("ABCD", [20, 60, 50, 46]):
    ws.column_dimensions[col].width = wd

# =================================================================== Summary: switches and read-outs
ws = ws_sum
put(ws, 4, 4, "Market treatment of the 2 October 2026 paper (sheet 'Market layer')", SEC)
c = put(ws, 5, 4, 0, INPUT, "0", fill=YELLOW)
c.alignment = Alignment(horizontal="center", vertical="center")
dv01 = DataValidation(type="list", formula1='"0,1"', allow_blank=False, showErrorMessage=True,
                      errorTitle="Switch", error="Enter 0 (off) or 1 (on).")
ws.add_data_validation(dv01)
dv01.add("D5")
sum_rows = [
    (5, "Isuzu UK (D-Max) exempt from the recovery extra (1 = on, 0 = off). Default 0 = as in the paper: Isuzu UK carries the extra. Not decided.", None, None),
    (6, "Total increase after market treatment, EUR (equals the target in both positions)", f"={ML}D{rec['total']}", EUR0),
    (7, "Weighted increase after market treatment", f"={ML}D{rec['pct']}", PCT2),
    (8, "Recovery extra from the grid, EUR", f"={ML}D{rec['extra']}", EUR0),
    (9, "Market layer checks (all must read OK)", f"={ALLCK}", None),
    (10, "More switches for the market layer and the grid: see row 74 below.", None, None),
]
for rr, lab, fx, nf in sum_rows:
    put(ws, rr, 5, lab, BODY, align=WRAP)
    ws.merge_cells(start_row=rr, start_column=5, end_row=rr, end_column=8)
    if fx:
        cc = put(ws, rr, 4, fx, BOLD, nf)
        cc.alignment = Alignment(horizontal="center", vertical="center")
ws.conditional_formatting.add("D9", CellIsRule(operator="equal", formula=['"CHECK"'], font=RED))
ws.conditional_formatting.add("D9", CellIsRule(operator="equal", formula=['"OK"'], font=GREEN))

# ---- the switches added 11 October 2026 (package B), rows 74 and below
put(ws, SUM_SW0, 1, "Market treatment switches added 11 October 2026 - change the yellow cells, everything re-solves", SEC)
put(ws, SUM_SW0 + 1, 1, ("Each switch changes what the holds cover or what the grid gives, and the base points behind the grid are "
                         "solved again so the total stays on the target."), SUB)
sw_defs = [
    (SUM_SW0 + 2, "Filters held at today's price (1 = held, as in the paper; 0 = they follow the factory increase). "
                  "Default 0, decided 11 October 2026.", 0, "01"),
    (SUM_SW0 + 3, "Intake, exhaust and emission parts held at today's price (1 = held, as in the paper; 0 = they follow). "
                  "Default 1. Not decided.", 1, "01"),
    (SUM_SW0 + 4, "Brake discs and drums stay at today's price wherever service parts are held. Decided 11 October 2026, not a switch.",
     1, "lock"),
    (SUM_SW0 + 5, "Israel trucks distributor: body parts carry the recovery extra (1 = yes, as in the paper). "
                  "The Israel total-loss limit is verified only up to 3.5 tonnes, so for trucks it is unverified.", 1, "01"),
    (SUM_SW0 + 6, "Isuzu UK (D-Max): body parts carry the recovery extra (1 = yes, as in the paper). Same open point as the "
                  "exemption switch above.", 1, "01"),
    (SUM_SW0 + 7, "Body parts in every other market: multiplier on the extra (1 = as in the paper). Nothing is decided; the grid "
                  "lets you raise it.", 1, "num"),
    (SUM_SW0 + 8, "The extra goes only to parts with no aftermarket alternative found (1 = yes, as in the paper; 0 = every part in "
                  "the role).", 1, "01"),
    (SUM_SW0 + 9, "Stance scenario: A = the 2 October paper, B = candidate stances, not decided. Set the stances on the "
                  "'Pricing grid' sheet.", "A", "AB"),
]
dvAB = DataValidation(type="list", formula1='"A,B"', allow_blank=False, showErrorMessage=True,
                      errorTitle="Scenario", error="Enter A or B.")
ws.add_data_validation(dvAB)
for rr, lab, default, kind in sw_defs:
    put(ws, rr, 1, lab, BODY, align=WRAP)
    cc = put(ws, rr, 2, default, INPUT, None if kind == "AB" else ("0" if kind in ("01", "lock") else NUM2),
             fill=PALE if kind == "lock" else YELLOW)
    cc.alignment = Alignment(horizontal="center", vertical="center")
    if kind == "01":
        dv01.add(cc.coordinate)
    if kind == "AB":
        dvAB.add(cc.coordinate)
    ws.row_dimensions[rr].height = 28
SUM_RO = SUM_SW0 + 11
put(ws, SUM_RO - 1, 1, "What the switches do now", SEC)
HV_FILT = hv_rows["Filters (oil, air, fuel, blower, strainers)"]
HV_EXH = hv_rows["Intake, exhaust and emission parts"]
ro = [
    ("Given up by the holds now, EUR", f"={ML}D{rec['given']}", EUR0),
    ("What the filters switch is worth, EUR (what they give up when held)", f"={ML}F{HV_FILT}", EUR0),
    ("Given up if filters were held as well, EUR", f"={ML}D{rec['given']}+IF({S1}=1,0,{ML}F{HV_FILT})", EUR0),
    ("What the intake, exhaust and emission switch is worth, EUR", f"={ML}F{HV_EXH}", EUR0),
    ("Given up if intake, exhaust and emission parts followed instead, EUR",
     f"={ML}D{rec['given']}-IF({S2}=1,{ML}F{HV_EXH},0)", EUR0),
    ("Base points behind the grid now", f"=IF({SW}=1,{T_ON},{T_OFF})", "0.0000%"),
    ("Recovery extra now, EUR", f"={ML}D{rec['extra']}", EUR0),
    ("Total increase after market treatment, EUR", f"={ML}D{rec['total']}", EUR0),
    ("Weighted increase after market treatment", f"={ML}D{rec['pct']}", PCT3),
    ("Every line has exactly one reason code", f"={GR_CODE_CHK}", None),
]
for i, (lab, fx, nf) in enumerate(ro):
    rr = SUM_RO + i
    put(ws, rr, 1, lab, BODY, align=WRAP)
    cc = put(ws, rr, 2, fx, BOLD, nf)
    cc.alignment = Alignment(horizontal="center", vertical="center")
ws.conditional_formatting.add(f"B{SUM_RO + len(ro) - 1}", CellIsRule(operator="equal", formula=['"CHECK"'], font=RED))
ws.conditional_formatting.add(f"B{SUM_RO + len(ro) - 1}", CellIsRule(operator="equal", formula=['"OK"'], font=GREEN))
SUM_LAST = SUM_RO + len(ro) - 1
ws.column_dimensions["A"].width = max(ws.column_dimensions["A"].width or 60, 60)

# ---- label fixes in the new copy only (package H)
LABEL_FIXES = []
a9 = ws["A9"].value
ws["A9"] = a9.replace("- Jerome, 30 September 2026", "- decided 30 September 2026")
LABEL_FIXES.append(("Summary!A9", a9, ws["A9"].value))
a36 = ws["A36"].value
ws["A36"] = ("By market, before the market decisions (one list price per part; Israel and CIS lists move by the same % on their own "
             "price). For the picture after the market decisions see 'Market layer' and the three stance sheets.")
LABEL_FIXES.append(("Summary!A36", a36, ws["A36"].value))
a38 = ws_rev["A38"].value
ws_rev["A38"] = a38.replace("(Jerome, 30 September 2026)", "(decided 30 September 2026)")
LABEL_FIXES.append(("Review lists!A38", a38, ws_rev["A38"].value))
a11 = ws_read["A11"].value
ws_read["A11"] = a11.replace("(your call, 30 September 2026)", "(decided 30 September 2026)")
LABEL_FIXES.append(("Read me!A11", a11, ws_read["A11"].value))

# Checks sheet: one extra line (row 13 was empty)
assert ws_ck["A13"].value is None and ws_ck["A14"].value is not None
put(ws_ck, 13, 1, "Market layer: all checks on the 'Market layer' sheet", BODY, align=WRAP)
put(ws_ck, 13, 2, f'=COUNTIF({ML}$D${ck_first}:$D${ck_last},"OK")', BODY, "0")
put(ws_ck, 13, 3, len(ck), BODY, "0")
put(ws_ck, 13, 4, '=IF(B13=C13,"OK","CHECK")', BOLD)

# Read me: appended section (the original text is untouched apart from the label fix above)
ws = ws_read
rr0 = ws.max_row + 2
add = [
    ("Market layer, stance sheets and pricing grid (added 11 October 2026)", SEC),
    ("Sheet 'Market layer' shows how the market decisions of the 2 October 2026 paper land per part and per market: holds at today's "
     "price, the recovery extra, and Armenia and Kazakhstan on their own increase. The total stays exactly on the target. "
     "The three stance sheets hold the facts per market, one sheet per price basis (PR00, the Israel basis, CIS). "
     "'Pricing grid' turns a market stance and a parts role into the extra that line gets; 'Layer solver' finds the one base number "
     "of points that makes the whole book land on the target.", BODY),
    ("Summary D5 is the Isuzu UK (D-Max) exemption switch. The switches added on 11 October 2026 sit on the Summary sheet from row 74: "
     "filters held or following, intake and exhaust held or following, the two Israel and Isuzu UK body-part switches, the body "
     "multiplier for the other markets, whether the extra is limited to parts with no aftermarket alternative, and the stance scenario. "
     "Every part x market line carries exactly one reason code.", BODY),
    ("Correction to the paragraph on competitor prices above: that paragraph describes the reference dealer price as our list price "
     "times 1.40 and then 1.275, which is 1.785. The policy paper of 2 October 2026 replaced that basis with our list price times 2.19, "
     "read as a 37% margin at the distributor step and 25% to 27.5% at the dealer step. For anything dated 2 October 2026 or later the "
     "2.19 basis applies, and the paper itself marks it provisional. See 'Labels corrected in this draft' on the 'Market layer' sheet.", BODY),
]
for i, (t, f_) in enumerate(add):
    cc = put(ws, rr0 + i, 1, t, f_, align=WRAP)
    if f_ is BODY:
        ws.row_dimensions[rr0 + i].height = 13.5 * -(-len(t) // 140) + 4

# ---- pre-delivery tidy: freeze the header on the two text sheets, wrap the long cells the checker looks at
ws_td.freeze_panes = "A4"
ws_rr.freeze_panes = "A5"
for w_ in (ws_ml, ws_pr00, ws_zpr1, ws_cis, ws_gr, ws_sv, ws_mv, ws_td, ws_rr):
    for row in w_.iter_rows(min_row=1, max_row=min(w_.max_row, 200), min_col=1, max_col=4):
        for c_ in row:
            if isinstance(c_.value, str) and len(c_.value) > 40 and not (c_.alignment and c_.alignment.wrap_text):
                try:
                    c_.alignment = Alignment(wrap_text=True, vertical=c_.alignment.vertical or "top",
                                             horizontal=c_.alignment.horizontal)
                except AttributeError:
                    pass

# ---- register the named ranges the 45,581 line formulas use
existing = set(wb.defined_names)
for nm, ref in sorted(NAMED.items()):
    assert nm not in existing, nm
    wb.defined_names.add(DefinedName(nm, attr_text=ref.lstrip("=")))
print(f"named ranges registered: {len(NAMED)}")

OUT.parent.mkdir(parents=True, exist_ok=True)
t1 = time.time()
wb.save(OUT)
print(f"saved {OUT} in {time.time() - t1:.0f}s ({OUT.stat().st_size / 1e6:.1f} MB)")

# =================================================================== addresses the verifier needs
addr = {"market_layer": {"rec": rec, "mt_first": first_m, "mt_last": last_m, "mt_total": mt_total, "markets": markets,
                          "dc0": DC0, "ak0": AK0, "ak_total_row": ak_total_row, "ak_nocis_row": ak_nocis_row, "ck_first": ck_first,
                          "ck_last": ck_last, "rr0": RR0, "n_checks": len(ck), "hv_rows": hv_rows, "hv_total": HV_TOTAL,
                          "labels_row": LB0, "settings": {"ceil": R_SET_CEIL, "exempt": R_SET_EXEMPT, "cis": R_SET_CIS,
                                                          "isr": R_SET_ISR, "svctxt": R_SET_SVCTXT}},
        "lp": {"first": LP_FIRST, "last": LP_LAST, "cols": lc, "names": LP_COLS},
        "pm": {"first": PM_FIRST, "last": PM_LAST, "cols": pc, "names": PM_COLS},
        "grid": {"mult_a": [GR_A0, GR_A0 + 2], "mult_b": [GR_B0, GR_B0 + 2], "mult_now": [GR_NOW0, GR_NOW0 + 2], "base_cell": "B29",
                 "stance_first": GR_ST0, "stance_last": GR_ST_LAST, "code_first": GR_CODE0, "code_n": GR_CODE_N,
                 "code_check": f"C{GR_CODE0 + GR_CODE_N + 2}", "cell_first": GR_CELL0 + 1, "cell_last": GR_CELL_LAST,
                 "cell_total": GR_CELL_TOTAL, "codes": [c for c, _ in CODES]},
        "summary": {"sw0": SUM_SW0, "s1": SUM_SW0 + 2, "s2": SUM_SW0 + 3, "disc": SUM_SW0 + 4, "b1": SUM_SW0 + 5,
                    "b2": SUM_SW0 + 6, "b3": SUM_SW0 + 7, "elig": SUM_SW0 + 8, "scen": SUM_SW0 + 9,
                    "readout_first": SUM_RO, "readout_last": SUM_LAST},
        "stance": {m: {"basis": b, "row": r_} for m, (b, r_) in stance_rows.items()},
        "margin_volume": {"first": MV0, "last": MV_LAST, "total": MV_TOTAL},
        "test": {"markets": TEST_MARKETS, "rows": len(test), "list_first": tl0, "list_last": TL_LAST,
                 "readout": {m: {k: v for k, v in readout[m].items()} for m in TEST_MARKETS}},
        "label_fixes": [{"cell": a, "before": b, "after": c_} for a, b, c_ in LABEL_FIXES],
        "facts": {m: {k: (None if (isinstance(v, float) and not np.isfinite(v)) else v) for k, v in stance_facts[m].items()}
                  for m in markets},
        "given_by_hold_paper": given_by, "role_status": ROLE_STATUS,
        "carpark_unmapped": cp_unmapped, "scenario_b_keep_added": B_ADDS,
        "built": time.strftime("%Y-%m-%d %H:%M"), "xlsx": str(OUT)}
(OUT.parent / "grid_addresses_2026-10-11.json").write_text(json.dumps(addr, indent=1, default=float), encoding="utf-8")
(OUT.parent / "OPEN_Price_Increase_5pct_Proposal_GRID_DRAFT_2026-10-11.cmd").write_text(
    '@echo off\r\nstart "" "%~dp0Price_Increase_5pct_Proposal_GRID_DRAFT_2026-10-11.xlsx"\r\n', encoding="ascii")
shutil.rmtree(tmpd, ignore_errors=True)
print("test design rows:", len(test), "| markets:", TEST_MARKETS)
for m in TEST_MARKETS:
    i_ = readout[m]
    print(f"  {m}: months {i_['months']}, test parts with months {i_['n_parts']}, "
          + (f"smallest visible dealer reaction {i_['mde']['mde_dealer_reaction']:.2f}" if i_["mde"] else f"no power figure - {i_['note'][:80]}"))
print("label fixes:", [a for a, _, _ in LABEL_FIXES])
print("done", round(time.time() - t0), "s")
print("NEXT: python recalc_excel.py <xlsx>  then  python verify_pricing_grid_20261011.py <xlsx>")
