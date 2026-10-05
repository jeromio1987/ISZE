# -*- coding: utf-8 -*-
"""
ISZE pricing simulation - specification-basis workbook.

Builds a live-formula Excel model in the same shape as the existing
'pricing simulation 2026' workbook, with the reporting axis switched from the
raw price class code to the segmentation set out in the pricing specification.

This is a reporting model. It does not change a published number, does not
propose a price change, and does not run an allocation.

Run: python 02_dashboards/pricing/_build/build_pricing_simulation_spec_basis.py
"""
from __future__ import annotations

import io
import json
import os
import sys

import numpy as np
import pandas as pd
from openpyxl import Workbook
from openpyxl.styles import Alignment, Font, PatternFill
from openpyxl.utils import get_column_letter

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

ISZE = r"C:\Users\jerom\Desktop\claude\ISZE"
DERIVED = os.path.join(ISZE, "01_data", "00_derived")
PRISM = os.path.join(ISZE, "03_analytics", "Isuzu", "prism")
SNAP = os.path.join(ISZE, "04_tools", "autodoc_scraper", "_snapshots", "2026-09-15")
OUT_DIR = os.path.join(ISZE, "02_dashboards", "pricing")
XLSX = os.path.join(OUT_DIR, "ISZE_Pricing_Simulation_Spec_Basis.xlsx")
META = os.path.join(OUT_DIR, "_build", "_spec_basis_meta.json")

FXP = 163.7
EXPECT_PCT = 0.059616
EXPECT_STEP_EUR = 1652140.71
EXPECT_SIM_PCT = 0.06064
EXPECT_QTY = 1225500
EXPECT_BILLED_EUR = 32595852.63
EXPECT_LINES = 47617

CATEGORY_LABELS = {
    "air_filter": "Air Filter",
    "blower_filter": "Blower Unit Filter",
    "brake_pad": "Brake Pad",
    "brake_rotor": "Brake Rotor",
    "brake_shoe": "Brake Shoe",
    "clutch_booster": "Clutch Booster",
    "clutch_disc": "Clutch Disc",
    "clutch_kit": "Clutch Kit",
    "clutch_pressure_plate": "Clutch Pressure Plate",
    "fuel_filter": "Fuel Filter",
    "oil_filter": "Oil Filter",
    "pilot_bearing": "Pilot Bearing",
    "release_bearing": "Release Bearing",
    "urea_filter": "Urea (AdBlue) Filter",
}
ISRAEL = {1797, 1799}
CIS = {2733, 2734}
log = []


def say(msg):
    print(msg)
    sys.stdout.flush()
    log.append(msg)


# ---------------------------------------------------------------- 1. basis
say("Loading the last-12-month base-price comparison ...")
df = pd.read_csv(os.path.join(DERIVED, "price_bp_weighted_compare_pn.csv"),
                 dtype={"part_number": str})
ins = df[df["in_scope"] == True].copy()                                  # noqa: E712
priced = ins[ins["bp_new_jpy"].notna() & ins["bp_prior_revised"].notna()].copy()
unpriced = ins[~(ins["bp_new_jpy"].notna() & ins["bp_prior_revised"].notna())].copy()
say(f"  in scope : {len(ins):,} lines, qty {ins['billed_qty'].sum():,.0f}, "
    f"billed EUR {ins['net_sales_value'].sum():,.2f}")
say(f"  priced   : {len(priced):,} lines, qty {priced['billed_qty'].sum():,.0f}, "
    f"billed EUR {priced['net_sales_value'].sum():,.2f}")
say(f"  excluded : {len(unpriced):,} lines, billed EUR {unpriced['net_sales_value'].sum():,.2f}")

priced["pn"] = priced["part_number"].str.strip()
priced["lane"] = np.where(
    priced["customer_code"].isin(ISRAEL), "Israel",
    np.where(priced["customer_code"].isin(CIS), "CIS", "PR00"))
ins["pn"] = ins["part_number"].str.strip()
ins["lane"] = np.where(
    ins["customer_code"].isin(ISRAEL), "Israel",
    np.where(ins["customer_code"].isin(CIS), "CIS", "PR00"))

# ---------------------------------------------------------------- 2. list + source
say("Joining source of supply and the official list price ...")
enq = pd.read_parquet(os.path.join(DERIVED, "pricing_pn_enquiry.parquet"),
                      columns=["part_number", "source", "sp_eur_pr00_ie40"])
enq["pn"] = enq["part_number"].astype(str).str.strip()
enq = enq.drop(columns=["part_number"]).drop_duplicates("pn")
priced = priced.merge(enq.rename(columns={"source": "supply_source"}),
                      on="pn", how="left")
say(f"  source of supply : {priced['supply_source'].notna().sum():,} of {len(priced):,}")
say(f"  official list    : {priced['sp_eur_pr00_ie40'].notna().sum():,} of {len(priced):,}")

# ---------------------------------------------------------------- 3. classification
say("Attaching the parts classification ...")
sys.path.insert(0, PRISM)
from modules.pms_engine import PMS_PN_REGISTRY, _MULTI_MODEL   # noqa: E402

registry = {}
for k, v in PMS_PN_REGISTRY.items():
    registry[str(int(k))] = v.get("category")
for k, v in _MULTI_MODEL.items():
    registry.setdefault(str(int(k)), v[0].get("category"))

bvp = pd.read_csv(os.path.join(DERIVED, "bvp_pn_dimension.csv"), dtype={"part_number": str})
bvp["pn"] = bvp["part_number"].str.strip()
bvp = bvp.drop_duplicates("pn")
bvp_map = dict(zip(bvp["pn"], bvp["pms_category"]))
bvp_family = dict(zip(bvp["pn"], bvp["product_family"]))

FILTER_WORDS = [("OIL", "oil_filter"), ("FUEL", "fuel_filter"),
                ("UREA", "urea_filter"), ("ADBLUE", "urea_filter"),
                ("BLOWER", "blower_filter"), ("AIR", "air_filter")]


def service_category(row):
    """The service category for a line, and where it came from. Never guessed."""
    pn = row["pn"].lstrip("0")
    if pn in registry:
        return registry[pn], "registry"
    if bvp_family.get(row["pn"]) == "PMS_Filters":
        desc = str(row["billed_description"] or "").upper()
        for word, cat in FILTER_WORDS:
            if word in desc:
                return cat, "bvp_catalog_filter_family"
        return bvp_map.get(row["pn"]), "bvp_catalog_filter_family"
    return None, ""


sc = priced.apply(service_category, axis=1, result_type="expand")
priced["service_category"] = sc[0]
priced["service_category_source"] = sc[1]
say(f"  service category present : {priced['service_category'].notna().sum():,} "
    f"of {len(priced):,}")

cap = pd.read_csv(os.path.join(DERIVED, "pms_capture_by_db_year.csv"))
cap25 = cap[(cap["year"] == 2025) & (cap["line_type"] == "total")][
    ["distributor_code", "pms_category", "capture_rate"]].copy()

CATS14 = sorted(CATEGORY_LABELS)
bvp_alt = (bvp[bvp["in_bvp_catalog"] == True]                          # noqa: E712
           .groupby("pms_category").size().to_dict())
family_contested = {c: (bvp_alt.get(c, 0) > 0) for c in CATS14}

# ---------------------------------------------------------------- 4. ladder
say("Walking the fallback classification ladder ...")
auto = pd.read_csv(os.path.join(DERIVED, "competitiveness_autodoc_risk.csv"),
                   dtype={"part_number": str})
auto["pn"] = auto["part_number"].str.strip()
auto_pns = set(auto["pn"])

aim = pd.read_csv(os.path.join(DERIVED, "aim_pn_classification.csv"),
                  usecols=["part_number", "aim_l1"], dtype={"part_number": str})
aim_v2 = pd.read_csv(os.path.join(DERIVED, "aim_pn_classification_20260920.csv"),
                     usecols=["part_number", "catalog_node_present",
                              "catalog_l1", "catalog_residual"],
                     dtype=str)
aim_v2["pn"] = aim_v2["part_number"].str.strip()
# A part number being present in a catalogue does NOT mean no competitor exists.
# Only these signals may ever justify "Captive": a real governed node.
aim_catalogue_pn = dict(zip(aim_v2["pn"], aim_v2["catalog_node_present"]))
aim_residual_pn = dict(zip(aim_v2["pn"], aim_v2["catalog_residual"]))
aim["pn"] = aim["part_number"].str.strip()
aim_map = dict(zip(aim["pn"], aim["aim_l1"]))

RATE_SRC = ("billed demand against the demand the fleet should generate, "
            "by distributor and service category")


def classify(row):
    """Return the rolled-up captured-demand zone, the rung of the ladder it came
    from, the measured rate where one exists, and the plain-English source.

    The measured rungs come from the capture rate. The fallback rungs are the
    specification's own binary proxy, not a measurement, and are labelled so."""
    cat = row["service_category"]
    code = row["distributor_code"]
    if pd.notna(cat) and cat in CATEGORY_LABELS and pd.notna(code):
        hit = cap25[(cap25["distributor_code"] == code) & (cap25["pms_category"] == cat)]
        if len(hit):
            rate = float(hit.iloc[0]["capture_rate"])
            if np.isfinite(rate):
                zone = ("Captive" if rate >= 0.80
                        else "Contested" if rate >= 0.45 else "Lost")
                return zone, "Captured-demand measure", rate, RATE_SRC, "Measured"
        return (np.nan, "UNCLASSIFIED", np.nan,
                "service category known, but no captured-demand measure "
                "for this distributor", "Not classified")
    if row["pn"] in auto_pns:
        return ("Contested", "Competitor file", np.nan,
                "an independent alternative for this part exists in the "
                "competitor file", "Proxy")
    if bvp_family.get(row["pn"]) == "PMS_Filters":
        contested = family_contested.get(cat or "", False)
        return ("Contested" if contested else "Captive", "Filter family", np.nan,
                "parts catalogue filter family; an alternative exists"
                if contested else
                "parts catalogue filter family; no alternative catalogued", "Proxy")
    if aim_residual_pn.get(row["pn"]) == "1":
        # Documented residual (Other / review). A residual is not evidence of a
        # moat, so it may not be rolled up as "Captive".
        return (np.nan, "UNCLASSIFIED", np.nan,
                "catalogue residual (Other / review) - not evidence either way",
                "Not classified")
    if aim_catalogue_pn.get(row["pn"]) == "1":
        # A governed catalogue node is a proxy for "no alternative catalogued".
        # It is NOT a measured competitive position and must be read as such.
        return ("Captive (proxy)", "Parts catalogue", np.nan,
                "governed catalogue node; no competitive alternative on file "
                "(proxy, not measured)", "Proxy")
    return (np.nan, "UNCLASSIFIED", np.nan,
            "no source on disk classifies this line", "Not classified")


cl = priced.apply(classify, axis=1, result_type="expand")
priced["ladder_position"] = cl[0]
priced["classification_basis"] = cl[1]
priced["capture_rate"] = cl[2]
priced["classification_source"] = cl[3]
priced["position_kind"] = cl[4]
priced["unclassified"] = priced["classification_basis"] == "UNCLASSIFIED"

# Where the ladder was used, the position is fixed by the catalogue and is not a
# measured rate. The zone is written as a formula against the Legend thresholds
# on every row, so moving the threshold dial reclassifies the measured lines.
priced["zone_from_ladder"] = np.where(
    priced["position_kind"] == "Proxy", priced["ladder_position"], "")

# ---------------------------------------------------------------- 5. benchmark
say("Building the independent-market benchmark and its evidence tiers ...")
ks = pd.read_csv(os.path.join(DERIVED, "iam_ks_price_gap.csv"), dtype={"pn": str})
ks["db"] = ks["db"].astype(str).str.strip().str.upper()
ks["pn"] = ks["pn"].str.strip()
ks_db = {(r["db"], r["pn"]): float(r["ks_am_min_eur"]) for _, r in ks.iterrows()}
ks_pn = ks.groupby("pn")["ks_am_min_eur"].min().to_dict()

eu = pd.read_csv(os.path.join(DERIVED, "eucon_price_gap.csv"), dtype={"pn": str})
eu["pn"] = eu["pn"].str.strip()
eucon_map = {r["pn"]: float(r["Min_Competitor_EUR"]) for _, r in eu.iterrows()}

t4 = {}
frames = []
for f in ["auto365_results.csv", "tmc_results.csv", "tranzparts_results.csv"]:
    p = os.path.join(SNAP, f)
    if os.path.exists(p):
        frames.append(pd.read_csv(p))
if frames:
    scrub = pd.concat(frames, ignore_index=True).dropna(subset=["PMS_Category"])
    med = scrub.groupby("PMS_Category")["Price_EUR"].median().to_dict()
    t4 = {"brake_pad": med.get("brake"), "brake_shoe": med.get("brake"),
          "clutch_disc": med.get("clutch"), "clutch_kit": med.get("clutch"),
          "air_filter": med.get("air_filter"), "fuel_filter": med.get("fuel_filter"),
          "oil_filter": med.get("oil_filter")}
    t4 = {k: (None if v is None or not np.isfinite(v) else float(v)) for k, v in t4.items()}

say(f"  same-shop listings  : {len(ks_db):,} distributor/part pairs, {ks['pn'].nunique()} parts")
say(f"  Eucon benchmark     : {len(eucon_map):,} parts")
say(f"  category medians    : {sum(1 for v in t4.values() if v)}")


def benchmark(row):
    pn = row["pn"]
    db = str(row["distributor_code"] or "").strip().upper()
    v = ks_db.get((db, pn))
    if v and np.isfinite(v) and v > 0:
        return float(v), "T1"
    v = ks_pn.get(pn)
    if v and np.isfinite(v) and v > 0:
        return float(v), "T2"
    v = eucon_map.get(pn)
    if v and np.isfinite(v) and v > 0:
        return float(v), "T3"
    v = t4.get(row["service_category"] or "")
    if v:
        return float(v), "T4"
    return None, "T5"


bm = priced.apply(benchmark, axis=1, result_type="expand")
priced["independent_price_eur"] = bm[0]
priced["evidence_tier"] = bm[1]
say(f"  tiers: {priced['evidence_tier'].value_counts().to_dict()}")

# honest gap accounting
step_eur = float((priced["billed_qty"] *
                  (priced["bp_new_jpy"] - priced["bp_prior_revised"])).sum() / FXP)
weighted = float((priced["billed_qty"] *
                  (priced["bp_new_jpy"] - priced["bp_prior_revised"])).sum() /
                 (priced["billed_qty"] * priced["bp_prior_revised"]).sum())
n_unclass = int((priced["classification_basis"] == "UNCLASSIFIED").sum())
eur_unclass = float(priced.loc[priced["classification_basis"] == "UNCLASSIFIED",
                               "net_sales_value"].sum())
n_t5 = int((priced["evidence_tier"] == "T5").sum())
eur_t5 = float(priced.loc[priced["evidence_tier"] == "T5", "net_sales_value"].sum())
n_nocat = int(priced["service_category"].isna().sum())

say("")
say(f"Reconcile: weighted {weighted:.6f} ({weighted*100:.4f}%) vs published "
    f"{EXPECT_PCT*100:.4f}%")
say(f"Reconcile: step EUR {step_eur:,.2f} vs published EUR {EXPECT_STEP_EUR:,.2f}")
say("")
say("Gaps reported instead of filled:")
say(f"  no service category                   : {n_nocat:,} lines")
say(f"  captured-demand position unclassified : {n_unclass:,} lines, "
    f"EUR {eur_unclass:,.2f}")
say(f"  no independent benchmark (T5)         : {n_t5:,} lines, EUR {eur_t5:,.2f}")
say("  momentum term not used by design; no allocation is run")
say("")

# ---------------------------------------------------------------- 6. write
say("Writing the workbook ...")
HDR_FILL = PatternFill("solid", fgColor="15233C")
HDR_FONT = Font(bold=True, color="F7F4EE", size=10)
TITLE_FONT = Font(bold=True, size=13, color="15233C")
SUB_FONT = Font(italic=True, size=9, color="555555")
DIAL_FILL = PatternFill("solid", fgColor="FDE9D9")
SEC_FONT = Font(bold=True, size=10, color="15233C")
TOT_FONT = Font(bold=True)

wb = Workbook()
ws_read = wb.active
ws_read.title = "Read me"
ws_ov = wb.create_sheet("Overview")
ws_lg = wb.create_sheet("Legend")
ws_pn = wb.create_sheet("PN data")
ws_seg = wb.create_sheet("Increase by segment")
ws_cls = wb.create_sheet("Increase by class")
ws_il = wb.create_sheet("Israel")
ws_cis = wb.create_sheet("CIS")
ws_ex = wb.create_sheet("Excluded")
ws_ck = wb.create_sheet("Checks")
for ws in wb.worksheets:
    ws.sheet_view.showGridLines = False

# ============================================================ Legend
ws_lg["A1"] = "Legend - the dials and the definitions this model reads"
ws_lg["A1"].font = TITLE_FONT
ws_lg["A2"] = ("Every euro figure in this workbook reads a cell on this sheet. Change a "
               "shaded cell and the roll-ups move.")
ws_lg["A2"].font = SUB_FONT

def legend(rr, label, value=None, extra=None, note=None, section=False, dial=False):
    c = ws_lg.cell(rr, 1, label)
    if section:
        c.font = SEC_FONT
    if value is not None:
        ws_lg.cell(rr, 2, value)
    if extra is not None:
        ws_lg.cell(rr, 3, extra)
    if note is not None:
        ws_lg.cell(rr, 4, note)
    if dial:
        ws_lg.cell(rr, 2).fill = DIAL_FILL


# Every dial sits at a fixed row. These are the anchors every formula reads.
ROW_FX = 7
ROW_REF = 12
ROW_CAP = 15
ROW_CON = 16
ROW_LOW = 20
ROW_HIGH = 21
ROW_TIER1 = 25

legend(4, "A. Foreign exchange (JPY per EUR)", section=True)
legend(5, "Rate as of 01/10/2023", 146.6)
legend(6, "Rate as of 01/10/2024", 159.4, "=B6/B5-1", "Year on year")
legend(7, "Rate used in this model", 163.7, "=B7/B6-1",
       "Change this cell: every euro column recalculates", dial=True)
legend(9, "B. Channel margins (the reference dealer price)", section=True)
legend(10, "Distributor margin", 1.40, dial=True)
legend(11, "Dealer margin", 1.275, dial=True)
legend(12, "Reference dealer price factor", "=B10*B11", None,
       "Official list price x this factor = the price a dealer would show a customer")
legend(14, "C. Captured-demand position (capture rate on total parts billed)",
       section=True)
legend(15, "Captive at or above", 0.80, dial=True)
legend(16, "Contested from", 0.45, dial=True)
legend(17, "Lost below", "=B16", None, "Below the contested floor is Lost")
legend(19, "D. Price index bands (reference dealer price / independent market price)",
       section=True)
legend(20, "Below reference, at or under", 0.95, dial=True)
legend(21, "Above reference, at or over", 1.15, dial=True)
legend(23, "E. Evidence tiers, and how far each tier may move a line", section=True)
legend(24, "Tier", "Permitted movement", "Meaning")
for i, (tier, move, meaning) in enumerate([
    ("T1", 0.10, "Observed at the same shop, same part number"),
    ("T2", 0.06, "Derived from a published listing"),
    ("T3", 0.06, "Eucon benchmark, network level"),
    ("T4", 0.03, "Category median"),
    ("T5", 0.00, "No benchmark - never move blind"),
]):
    legend(ROW_TIER1 + i, tier, move, None, meaning)
legend(31, "F. Service categories the captured-demand measure covers", section=True)
r = 32
for cat in CATS14:
    ws_lg.cell(r, 1, CATEGORY_LABELS[cat])
    ws_lg.cell(r, 2, cat)
    r += 1
r += 1
ws_lg.cell(r, 1, "Sections A to D are the dials. Section E is carried from the pricing "
                 "specification: it shows how far the evidence would let a line move. It "
                 "is shown, not applied. No price change is proposed anywhere in this "
                 "workbook and no volume response is assumed.")
ws_lg.cell(r, 1).font = SUB_FONT
for col, w in zip("ABCD", (56, 20, 34, 66)):
    ws_lg.column_dimensions[col].width = w
for rr in range(ROW_TIER1, ROW_TIER1 + 5):
    ws_lg.cell(rr, 2).number_format = "0.00%"

FX_CELL = f"Legend!$B${ROW_FX}"
REFF = f"Legend!$B${ROW_REF}"
CAPV = f"Legend!$B${ROW_CAP}"
CONV = f"Legend!$B${ROW_CON}"
LOWC = f"Legend!$B${ROW_LOW}"
HIGHC = f"Legend!$B${ROW_HIGH}"
TIERS = f"Legend!$B${ROW_TIER1}:$C${ROW_TIER1 + 4}"

# ============================================================ PN data
# Column B is the description, as in the earlier workbook, so the sheet reads the
# same way and the description column carries the width.
PN_HEAD = [
    ("lane", 10), ("description", 42), ("distributor", 13), ("customer_code", 12),
    ("part_number", 13), ("class_retained", 8), ("supply_origin", 14),
    ("service_category", 18), ("l12m_qty", 10), ("l12m_billed_eur", 14),
    ("bp_prior_jpy", 12), ("bp_fy27_jpy", 12), ("delta_jpy", 10), ("delta_pct", 10),
    ("step_eur", 12), ("list_price_eur", 12), ("reference_dealer_price_eur", 15),
    ("independent_price_eur", 15), ("price_index", 11), ("evidence_tier", 9),
    ("permitted_move_pp", 11), ("capture_rate", 11), ("classification_basis", 20),
    ("classification_source", 50), ("captured_demand_zone", 14),
    ("position_kind", 11), ("price_zone", 15), ("two_gate_action", 26),
]
for i, (h, w) in enumerate(PN_HEAD, start=1):
    c = ws_pn.cell(1, i, h)
    c.fill = HDR_FILL
    c.font = HDR_FONT
    c.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
    ws_pn.column_dimensions[get_column_letter(i)].width = w
ws_pn.freeze_panes = "F2"

# Named column letters. Every cross-sheet formula reads these, so a column can
# never drift out of step with the sheet it points at.
PCOL = {name: get_column_letter(i) for i, (name, _w) in enumerate(PN_HEAD, start=1)}
C_LANE = PCOL["lane"]
C_QTY = PCOL["l12m_qty"]
C_BILLED = PCOL["l12m_billed_eur"]
C_BP_PRIOR = PCOL["bp_prior_jpy"]
C_BP_NEW = PCOL["bp_fy27_jpy"]
C_DELTA = PCOL["delta_jpy"]
C_STEP = PCOL["step_eur"]
C_TIER = PCOL["evidence_tier"]
C_CUST = PCOL["customer_code"]
C_PN = PCOL["part_number"]
C_CLASS = PCOL["class_retained"]
C_RATE = PCOL["capture_rate"]
C_ZONE = PCOL["captured_demand_zone"]
C_INDEX = PCOL["price_index"]
C_PRICE_ZONE = PCOL["price_zone"]
C_ACTION = PCOL["two_gate_action"]
C_POSKIND = PCOL["position_kind"]

priced = priced.sort_values(["lane", "distributor_code", "part_number"],
                            kind="stable").reset_index(drop=True)
last = len(priced) + 1

for idx, row in priced.iterrows():
    rr = idx + 2
    src = row["supply_source"]
    ws_pn.cell(rr, 1, row["lane"])
    ws_pn.cell(rr, 2, str(row["billed_description"] or "")[:120])
    ws_pn.cell(rr, 3, row["distributor_code"] if pd.notna(row["distributor_code"])
               else row["gps_db_label"])
    ws_pn.cell(rr, 4, int(row["customer_code"]))
    ws_pn.cell(rr, 5, row["part_number"])
    ws_pn.cell(rr, 6, row["bp_new_class"] if pd.notna(row["bp_new_class"]) else None)
    ws_pn.cell(rr, 7, {"J": "Japan", "T": "Thailand"}.get(str(src),
               "UNKNOWN source on disk"))
    ws_pn.cell(rr, 8, CATEGORY_LABELS.get(row["service_category"]) or "UNKNOWN")
    ws_pn.cell(rr, 9, float(row["billed_qty"]))
    ws_pn.cell(rr, 10, float(row["net_sales_value"]))
    ws_pn.cell(rr, 11, float(row["bp_prior_revised"]))
    ws_pn.cell(rr, 12, float(row["bp_new_jpy"]))
    ws_pn.cell(rr, 13, f"=L{rr}-K{rr}")
    ws_pn.cell(rr, 14, f'=IF(K{rr}=0,"",L{rr}/K{rr}-1)')
    ws_pn.cell(rr, 15, f"=I{rr}*M{rr}/{FX_CELL}")
    ws_pn.cell(rr, 16, float(row["sp_eur_pr00_ie40"])
               if pd.notna(row["sp_eur_pr00_ie40"]) else None)
    ws_pn.cell(rr, 17, f'=IF(ISNUMBER(P{rr}),P{rr}*{REFF},"")')
    ws_pn.cell(rr, 18, float(row["independent_price_eur"])
               if pd.notna(row["independent_price_eur"]) else None)
    ws_pn.cell(rr, 19, f'=IF(AND(ISNUMBER(Q{rr}),ISNUMBER(R{rr}),R{rr}>0),Q{rr}/R{rr},"")')
    ws_pn.cell(rr, 20, row["evidence_tier"])
    ws_pn.cell(rr, 21, f'=IFERROR(VLOOKUP(T{rr},{TIERS},2,FALSE),"")')
    ws_pn.cell(rr, 22, float(row["capture_rate"])
               if pd.notna(row["capture_rate"]) else None)
    ws_pn.cell(rr, 23, row["classification_basis"])
    ws_pn.cell(rr, 24, row["classification_source"])
    ws_pn.cell(rr, 25,
               f'=IF(NOT(ISNUMBER(V{rr})),"{row["zone_from_ladder"] or "Not classified"}",'
               f'IF(V{rr}>={CAPV},"Captive",'
               f'IF(V{rr}>={CONV},"Contested","Lost")))')
    ws_pn.cell(rr, 26, row["position_kind"] if row["position_kind"] else "")
    ws_pn.cell(rr, 27,
               f'=IF(NOT(ISNUMBER(S{rr})),"Not computable",'
               f'IF(S{rr}<={LOWC},"Below reference",'
               f'IF(S{rr}>={HIGHC},"Above reference","In band")))')
    ws_pn.cell(rr, 28,
               f'=IF(Y{rr}="Not classified","UNCLASSIFIED - no position",'
               f'IF(AA{rr}="Not computable","0 - hold (no price index)",'
               f'IF(Y{rr}="Captive","+",'
               f'IF(Y{rr}="Contested",IF(S{rr}<{LOWC},"+",'
               f'IF(S{rr}>{HIGHC},"-","0 - hold")),'
               f'IF(Y{rr}="Lost",IF(S{rr}>{HIGHC},"- -",'
               f'IF(S{rr}<{LOWC},"0 - investigate","0 - hold")),'
               f'"UNCLASSIFIED - no position")))))')

for rr in range(2, last + 1):
    for col, fmt in [(9, "#,##0"), (10, "#,##0.00"), (13, "#,##0"),
                     (14, "0.00%"), (15, "#,##0.00"), (16, "#,##0.00"),
                     (17, "#,##0.00"), (18, "#,##0.00"), (19, "0.000"),
                     (21, "0.00%"), (22, "0.0000")]:
        ws_pn.cell(rr, col).number_format = fmt

PN = "'PN data'"
say(f"  {len(priced):,} rows written")

# ============================================================ Overview
ws_ov["A1"] = "What the specification segmentation says about the same step"
ws_ov["A1"].font = TITLE_FONT
ws_ov["A2"] = ("The base-price step is unchanged. What changes is how it is read: by "
               "captured-demand position and by position against the independent "
               "aftermarket, instead of by price class code.")
ws_ov["A2"].font = SUB_FONT

OV_HEAD = ["Lane", "Lines priced", "Quantity priced", "In-scope quantity",
           "Quantity coverage", "Base price prior (JPY)", "Base price new (JPY)",
           "Base price increase", "Value of the step (EUR)",
           "L12M billed to dealer (EUR)", "Step as % of L12M billed"]
for i, h in enumerate(OV_HEAD, start=1):
    c = ws_ov.cell(5, i, h)
    c.fill = HDR_FILL
    c.font = HDR_FONT
    c.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)

in_qty = ins.groupby("lane")["billed_qty"].sum().to_dict()
LANES = [("PR00 (all other distributors)", "PR00"),
         ("Israel (UMI 1797 + UTI 1799)", "Israel"),
         ("CIS (Armenia + Kazakhstan)", "CIS")]
r = 6
lane_rows = []
for label, key in LANES:
    ws_ov.cell(r, 1, label)
    ws_ov.cell(r, 2, f'=COUNTIF({PN}!${C_LANE}:${C_LANE},"="&"{key}")')
    ws_ov.cell(r, 3, f'=SUMIF({PN}!${C_LANE}:${C_LANE},"="&"{key}",{PN}!${C_QTY}:${C_QTY})')
    ws_ov.cell(r, 4, float(in_qty.get(key, 0)))
    ws_ov.cell(r, 5, f"=C{r}/D{r}")
    ws_ov.cell(r, 6, f'=SUMPRODUCT(({PN}!${C_LANE}$2:${C_LANE}${last}="{key}")'
                     f'*{PN}!${C_QTY}$2:${C_QTY}${last}'
                     f'*{PN}!${C_BP_PRIOR}$2:${C_BP_PRIOR}${last})')
    ws_ov.cell(r, 7, f'=SUMPRODUCT(({PN}!${C_LANE}$2:${C_LANE}${last}="{key}")'
                     f'*{PN}!${C_QTY}$2:${C_QTY}${last}'
                     f'*{PN}!${C_BP_NEW}$2:${C_BP_NEW}${last})')
    ws_ov.cell(r, 8, f"=G{r}/F{r}-1")
    ws_ov.cell(r, 9, f'=SUMIF({PN}!${C_LANE}:${C_LANE},"="&"{key}",{PN}!${C_STEP}:${C_STEP})')
    ws_ov.cell(r, 10, f'=SUMIF({PN}!${C_LANE}:${C_LANE},"="&"{key}",{PN}!${C_BILLED}:${C_BILLED})')
    ws_ov.cell(r, 11, f"=I{r}/J{r}")
    lane_rows.append(r)
    r += 1
ov_total = r
ws_ov.cell(ov_total, 1, "Total")
for col in "BCDEFGHIJ":
    ws_ov[f"{col}{ov_total}"] = f"=SUM({col}{lane_rows[0]}:{col}{lane_rows[-1]})"
ws_ov.cell(ov_total, 5, f"=C{ov_total}/D{ov_total}")
ws_ov.cell(ov_total, 8, f"=G{ov_total}/F{ov_total}-1")
ws_ov.cell(ov_total, 11, f"=I{ov_total}/J{ov_total}")

r = ov_total + 2
ws_ov.cell(r, 1, "Israel is always two rows, never one blended figure").font = SEC_FONT
r += 1
for i, h in enumerate(OV_HEAD, start=1):
    c = ws_ov.cell(r, i, h)
    c.fill = HDR_FILL
    c.font = HDR_FONT
r += 1
il_rows = []
for label, code in [("UMI (1797)", 1797), ("UTI (1799)", 1799)]:
    ws_ov.cell(r, 1, label)
    ws_ov.cell(r, 2, f'=COUNTIF({PN}!${C_CUST}:${C_CUST},"="&{code})')
    ws_ov.cell(r, 3, f'=SUMIF({PN}!${C_CUST}:${C_CUST},"="&{code},{PN}!${C_QTY}:${C_QTY})')
    ws_ov.cell(r, 4, float(ins[ins["customer_code"] == code]["billed_qty"].sum()))
    ws_ov.cell(r, 5, f"=C{r}/D{r}")
    ws_ov.cell(r, 6, f'=SUMPRODUCT(({PN}!${C_CUST}$2:${C_CUST}${last}={code})'
                     f'*{PN}!${C_QTY}$2:${C_QTY}${last}'
                     f'*{PN}!${C_BP_PRIOR}$2:${C_BP_PRIOR}${last})')
    ws_ov.cell(r, 7, f'=SUMPRODUCT(({PN}!${C_CUST}$2:${C_CUST}${last}={code})'
                     f'*{PN}!${C_QTY}$2:${C_QTY}${last}'
                     f'*{PN}!${C_BP_NEW}$2:${C_BP_NEW}${last})')
    ws_ov.cell(r, 8, f"=G{r}/F{r}-1")
    ws_ov.cell(r, 9, f'=SUMIF({PN}!${C_CUST}:${C_CUST},"="&{code},{PN}!${C_STEP}:${C_STEP})')
    ws_ov.cell(r, 10, f'=SUMIF({PN}!${C_CUST}:${C_CUST},"="&{code},{PN}!${C_BILLED}:${C_BILLED})')
    ws_ov.cell(r, 11, f"=I{r}/J{r}")
    il_rows.append(r)
    r += 1

for rr in lane_rows + [ov_total] + il_rows:
    for col in "BCDEFGHIJ":
        ws_ov[f"{col}{rr}"].font = TOT_FONT if rr == ov_total else Font()
    for col, fmt in [(2, "#,##0"), (3, "#,##0"), (4, "#,##0"), (5, "0.00%"),
                     (6, "#,##0"), (7, "#,##0"), (8, "0.000%"),
                     (9, "#,##0.00"), (10, "#,##0.00"), (11, "0.000%")]:
        ws_ov.cell(rr, col).number_format = fmt
ws_ov.cell(5, 6).comment = None
for col, w in zip("ABCDEFGHIJK", (32, 10, 13, 14, 12, 17, 17, 14, 17, 19, 16)):
    ws_ov.column_dimensions[col].width = w
r = ov_total + 3 + 2 + 3
ws_ov.cell(r, 1, "In-scope quantity is the published quantity in the window. Quantity "
                 "coverage is the share of it the step could be measured on.")
ws_ov.cell(r, 1).font = SUB_FONT

# ============================================================ segment pivots
ws_seg["A1"] = "The same step, read on the specification axes and the two-gate rule"
ws_seg["A1"].font = TITLE_FONT
ws_seg["A2"] = ("Every figure is a live sum over the PN data sheet. Change a dial on the "
                "Legend sheet and these rows move.")
ws_seg["A2"].font = SUB_FONT

SEG_HEAD = ["Segment", "Lines", "L12M quantity", "Base price prior (JPY)",
            "Base price new (JPY)", "Base price increase", "Value of the step (EUR)",
            "L12M billed (EUR)", "Step as % of billed"]
BLOCKS = [
    ("Captured-demand position", C_ZONE,
     ["Captive", "Contested", "Lost", "Not classified"]),
    ("How that position was arrived at", C_POSKIND,
     ["Measured", "Proxy", "Not classified"]),
    ("Position against the independent aftermarket (price index)", C_PRICE_ZONE,
     ["Below reference", "In band", "Above reference", "Not computable"]),
    ("Evidence behind the benchmark", C_TIER, ["T1", "T2", "T3", "T4", "T5"]),
    ("The action the two gates point to (sign only - no change is made)", C_ACTION,
     ["+", "0 - hold", "0 - hold (no price index)", "0 - investigate", "-", "- -",
      "UNCLASSIFIED - no position"]),
]
r = 4
seg_total_rows = []
seg_block_totals = []
seg_block_names = []
for title, col, values in BLOCKS:
    ws_seg.cell(r, 1, title).font = SEC_FONT
    r += 1
    for i, h in enumerate(SEG_HEAD, start=1):
        c = ws_seg.cell(r, i, h)
        c.fill = HDR_FILL
        c.font = HDR_FONT
        c.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
    r += 1
    first = r
    for v in values:
        esc = v.replace('"', '""')
        ws_seg.cell(r, 1, v)
        ws_seg.cell(r, 2, f'=COUNTIF({PN}!${col}:${col},"="&"{esc}")')
        ws_seg.cell(r, 3, f'=SUMIF({PN}!${col}:${col},"="&"{esc}",{PN}!${C_QTY}:${C_QTY})')
        ws_seg.cell(r, 4, f'=SUMPRODUCT(({PN}!${col}$2:${col}${last}="{esc}")'
                          f'*{PN}!${C_QTY}$2:${C_QTY}${last}'
                          f'*{PN}!${C_BP_PRIOR}$2:${C_BP_PRIOR}${last})')
        ws_seg.cell(r, 5, f'=SUMPRODUCT(({PN}!${col}$2:${col}${last}="{esc}")'
                          f'*{PN}!${C_QTY}$2:${C_QTY}${last}'
                          f'*{PN}!${C_BP_NEW}$2:${C_BP_NEW}${last})')
        ws_seg.cell(r, 6, f"=E{r}/D{r}-1")
        ws_seg.cell(r, 7, f'=SUMIF({PN}!${col}:${col},"="&"{esc}",{PN}!${C_STEP}:${C_STEP})')
        ws_seg.cell(r, 8, f'=SUMIF({PN}!${col}:${col},"="&"{esc}",{PN}!${C_BILLED}:${C_BILLED})')
        ws_seg.cell(r, 9, f"=G{r}/H{r}")
        r += 1
    ws_seg.cell(r, 1, "Total")
    for colx in "BCDEFGH":
        ws_seg[f"{colx}{r}"] = f"=SUM({colx}{first}:{colx}{r-1})"
    ws_seg.cell(r, 6, f"=E{r}/D{r}-1")
    ws_seg.cell(r, 9, f"=G{r}/H{r}")
    for colx in "ABCDEFGHI":
        ws_seg[f"{colx}{r}"].font = TOT_FONT
    seg_total_rows.append(r)
    seg_block_totals.append(r)
    seg_block_names.append(title)
    r += 2

for rr in range(4, r):
    for col, fmt in [(2, "#,##0"), (3, "#,##0"), (4, "#,##0"), (5, "#,##0"),
                     (6, "0.000%"), (7, "#,##0.00"), (8, "#,##0.00"), (9, "0.000%")]:
        ws_seg.cell(rr, col).number_format = fmt
for col, w in zip("ABCDEFGHI", (52, 9, 13, 18, 18, 14, 17, 17, 15)):
    ws_seg.column_dimensions[col].width = w


def segment_sheet(ws, title, subtitle, lane, values, label_head):
    """A lane-filtered view on the captured-demand axis."""
    ws["A1"] = title
    ws["A1"].font = TITLE_FONT
    ws["A2"] = subtitle
    ws["A2"].font = SUB_FONT
    head = [label_head, "Lines", "L12M quantity", "Base price prior (JPY)",
            "Base price new (JPY)", "Base price increase", "Value of the step (EUR)",
            "L12M billed (EUR)", "Step as % of billed"]
    for i, h in enumerate(head, start=1):
        c = ws.cell(4, i, h)
        c.fill = HDR_FILL
        c.font = HDR_FONT
        c.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
    rr = 5
    first = rr
    for v in values:
        esc = v.replace('"', '""')
        ws.cell(rr, 1, v)
        ws.cell(rr, 2, f'=COUNTIFS({PN}!${C_LANE}:${C_LANE},"{lane}",'
                       f'{PN}!${C_ZONE}:${C_ZONE},"="&"{esc}")')
        ws.cell(rr, 3, f'=SUMIFS({PN}!${C_QTY}:${C_QTY},{PN}!${C_LANE}:${C_LANE},"{lane}",'
                       f'{PN}!${C_ZONE}:${C_ZONE},"="&"{esc}")')
        ws.cell(rr, 4, f'=SUMPRODUCT(({PN}!${C_LANE}$2:${C_LANE}${last}="{lane}")'
                       f'*({PN}!${C_ZONE}$2:${C_ZONE}${last}="{esc}")'
                       f'*{PN}!${C_QTY}$2:${C_QTY}${last}'
                       f'*{PN}!${C_BP_PRIOR}$2:${C_BP_PRIOR}${last})')
        ws.cell(rr, 5, f'=SUMPRODUCT(({PN}!${C_LANE}$2:${C_LANE}${last}="{lane}")'
                       f'*({PN}!${C_ZONE}$2:${C_ZONE}${last}="{esc}")'
                       f'*{PN}!${C_QTY}$2:${C_QTY}${last}'
                       f'*{PN}!${C_BP_NEW}$2:${C_BP_NEW}${last})')
        ws.cell(rr, 6, f"=E{rr}/D{rr}-1")
        ws.cell(rr, 7, f'=SUMIFS({PN}!${C_STEP}:${C_STEP},{PN}!${C_LANE}:${C_LANE},"{lane}",'
                       f'{PN}!${C_ZONE}:${C_ZONE},"="&"{esc}")')
        ws.cell(rr, 8, f'=SUMIFS({PN}!${C_BILLED}:${C_BILLED},{PN}!${C_LANE}:${C_LANE},"{lane}",'
                       f'{PN}!${C_ZONE}:${C_ZONE},"="&"{esc}")')
        ws.cell(rr, 9, f"=G{rr}/H{rr}")
        rr += 1
    ws.cell(rr, 1, "Total")
    for colx in "BCDEFGH":
        ws[f"{colx}{rr}"] = f"=SUM({colx}{first}:{colx}{rr-1})"
    ws.cell(rr, 6, f"=E{rr}/D{rr}-1")
    ws.cell(rr, 9, f"=G{rr}/H{rr}")
    for colx in "ABCDEFGHI":
        ws[f"{colx}{rr}"].font = TOT_FONT
    for r2 in range(first, rr + 1):
        for col, fmt in [(2, "#,##0"), (3, "#,##0"), (4, "#,##0"), (5, "#,##0"),
                         (6, "0.000%"), (7, "#,##0.00"), (8, "#,##0.00"), (9, "0.000%")]:
            ws.cell(r2, col).number_format = fmt
    for colx, w in zip("ABCDEFGHI", (34, 10, 13, 18, 18, 14, 17, 17, 15)):
        ws.column_dimensions[colx].width = w
    return rr


segment_sheet(
    ws_il, "Israel - read on the specification axes",
    "Israel sits on its own lists. UMI and UTI are always separate rows, never one "
    "blended figure. These are the network zone definitions, not a separate calculation.",
    "Israel", ["Captive", "Contested", "Lost", "Not classified"],
    "Captured-demand position")

r0 = 15
ws_il.cell(r0, 1, "By distributor").font = SEC_FONT
head = ["Distributor", "Lines", "L12M quantity", "Value of the step (EUR)",
        "L12M billed (EUR)", "Increase in yen", "Step as % of billed"]
for i, h in enumerate(head, start=1):
    c = ws_il.cell(r0 + 1, i, h)
    c.fill = HDR_FILL
    c.font = HDR_FONT
for rr, (lab, code) in enumerate([("UMI (1797)", 1797), ("UTI (1799)", 1799)], start=r0 + 2):
    ws_il.cell(rr, 1, lab)
    ws_il.cell(rr, 2, f'=COUNTIF({PN}!${C_CUST}:${C_CUST},"="&{code})')
    ws_il.cell(rr, 3, f'=SUMIF({PN}!${C_CUST}:${C_CUST},"="&{code},{PN}!${C_QTY}:${C_QTY})')
    ws_il.cell(rr, 4, f'=SUMIF({PN}!${C_CUST}:${C_CUST},"="&{code},{PN}!${C_STEP}:${C_STEP})')
    ws_il.cell(rr, 5, f'=SUMIF({PN}!${C_CUST}:${C_CUST},"="&{code},{PN}!${C_BILLED}:${C_BILLED})')
    ws_il.cell(rr, 6, f'=SUMPRODUCT(({PN}!${C_CUST}$2:${C_CUST}${last}={code})'
                      f'*{PN}!${C_QTY}$2:${C_QTY}${last}'
                      f'*{PN}!${C_DELTA}$2:${C_DELTA}${last})')
    ws_il.cell(rr, 7, f"=D{rr}/E{rr}")
    ws_il.cell(rr, 6).number_format = "#,##0"
    ws_il.cell(rr, 7).number_format = "0.000%"
    ws_il.cell(rr, 2).number_format = "#,##0"
    ws_il.cell(rr, 3).number_format = "#,##0"
    ws_il.cell(rr, 4).number_format = "#,##0.00"
    ws_il.cell(rr, 5).number_format = "#,##0.00"

segment_sheet(
    ws_cis, "CIS - read on the specification axes",
    "Armenia and Kazakhstan together. Their lists are not class-dependent today; that is "
    "a question about the shape of the list, not about how this step reads.",
    "CIS", ["Captive", "Contested", "Lost", "Not classified"],
    "Captured-demand position")

# ============================================================ by class
ws_cls["A1"] = "The retained price class code, kept for traceability"
ws_cls["A1"].font = TITLE_FONT
ws_cls["A2"] = ("Class is no longer the grouping axis, but it stays visible so any line "
                "can still be found the old way.")
ws_cls["A2"].font = SUB_FONT
CLS_HEAD = ["Price class", "Lines", "L12M quantity", "Value of the step (EUR)",
            "L12M billed (EUR)", "Base price increase", "Step as % of billed"]
for i, h in enumerate(CLS_HEAD, start=1):
    c = ws_cls.cell(4, i, h)
    c.fill = HDR_FILL
    c.font = HDR_FONT
    c.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
classes = sorted(priced["bp_new_class"].dropna().unique())
r = 5
cls_first = r
for cl in classes:
    ws_cls.cell(r, 1, cl)
    ws_cls.cell(r, 2, f'=COUNTIF({PN}!${C_CLASS}:${C_CLASS},"="&"{cl}")')
    ws_cls.cell(r, 3, f'=SUMIF({PN}!${C_CLASS}:${C_CLASS},"="&"{cl}",{PN}!${C_QTY}:${C_QTY})')
    ws_cls.cell(r, 4, f'=SUMIF({PN}!${C_CLASS}:${C_CLASS},"="&"{cl}",{PN}!${C_STEP}:${C_STEP})')
    ws_cls.cell(r, 5, f'=SUMIF({PN}!${C_CLASS}:${C_CLASS},"="&"{cl}",{PN}!${C_BILLED}:${C_BILLED})')
    ws_cls.cell(r, 6, f'=SUMPRODUCT(({PN}!${C_CLASS}$2:${C_CLASS}${last}="{cl}")'
                      f'*{PN}!${C_QTY}$2:${C_QTY}${last}'
                      f'*{PN}!${C_BP_NEW}$2:${C_BP_NEW}${last})'
                      f'/SUMPRODUCT(({PN}!${C_CLASS}$2:${C_CLASS}${last}="{cl}")'
                      f'*{PN}!${C_QTY}$2:${C_QTY}${last}'
                      f'*{PN}!${C_BP_PRIOR}$2:${C_BP_PRIOR}${last})-1')
    ws_cls.cell(r, 7, f"=D{r}/E{r}")
    r += 1
# Lines the price list carries no class for. Without this row the class view is
# short, and the shortfall would be invisible.
ws_cls.cell(r, 1, "(no class)")
ws_cls.cell(r, 2, f'=COUNTIF({PN}!${C_CLASS}:${C_CLASS},"")')
ws_cls.cell(r, 3, f'=SUMIF({PN}!${C_CLASS}:${C_CLASS},"",{PN}!${C_QTY}:${C_QTY})')
ws_cls.cell(r, 4, f'=SUMIF({PN}!${C_CLASS}:${C_CLASS},"",{PN}!${C_STEP}:${C_STEP})')
ws_cls.cell(r, 5, f'=SUMIF({PN}!${C_CLASS}:${C_CLASS},"",{PN}!${C_BILLED}:${C_BILLED})')
ws_cls.cell(r, 6, f'=SUMPRODUCT(({PN}!${C_CLASS}$2:${C_CLASS}${last}="")'
                  f'*{PN}!${C_QTY}$2:${C_QTY}${last}'
                  f'*{PN}!${C_BP_NEW}$2:${C_BP_NEW}${last})'
                  f'/SUMPRODUCT(({PN}!${C_CLASS}$2:${C_CLASS}${last}="")'
                  f'*{PN}!${C_QTY}$2:${C_QTY}${last}'
                  f'*{PN}!${C_BP_PRIOR}$2:${C_BP_PRIOR}${last})-1')
ws_cls.cell(r, 7, "n/a")
r += 1
cls_total = r
ws_cls.cell(r, 1, "Total")
for col in "BCDEFG":
    ws_cls[f"{col}{r}"] = f"=SUM({col}{cls_first}:{col}{r-1})"
ws_cls.cell(r, 6, f"=SUMPRODUCT({PN}!${C_QTY}$2:${C_QTY}${last},"
                  f"{PN}!${C_BP_NEW}$2:${C_BP_NEW}${last})"
                  f"/SUMPRODUCT({PN}!${C_QTY}$2:${C_QTY}${last},"
                  f"{PN}!${C_BP_PRIOR}$2:${C_BP_PRIOR}${last})-1")
ws_cls.cell(r, 7, f"=D{r}/E{r}")
for col in "ABCDEFG":
    ws_cls[f"{col}{cls_total}"].font = TOT_FONT
ws_cls.cell(cls_total, 6).value = (f"=SUMPRODUCT({PN}!${C_QTY}$2:${C_QTY}${last},"
                                   f"{PN}!${C_BP_NEW}$2:${C_BP_NEW}${last})"
                                   f"/SUMPRODUCT({PN}!${C_QTY}$2:${C_QTY}${last},"
                                   f"{PN}!${C_BP_PRIOR}$2:${C_BP_PRIOR}${last})-1")
ws_cls.cell(cls_total, 6).number_format = "0.000%"
ws_cls.cell(cls_total, 7).value = f"=D{cls_total}/E{cls_total}"
ws_cls.cell(cls_total, 7).number_format = "0.000%"
for rr in range(cls_first, cls_total + 1):
    for col, fmt in [(2, "#,##0"), (3, "#,##0"), (4, "#,##0.00"), (5, "#,##0.00"),
                     (6, "0.000%"), (7, "0.000%")]:
        ws_cls.cell(rr, col).number_format = fmt
for col, w in zip("ABCDEFG", (28, 10, 13, 17, 17, 15, 15)):
    ws_cls.column_dimensions[col].width = w

# ============================================================ Excluded
ws_ex["A1"] = "What the model deliberately leaves out"
ws_ex["A1"].font = TITLE_FONT
ws_ex["A2"] = ("Nothing is quietly dropped. Each group is named with its line count and "
               "what it is worth on last-twelve-month billing.")
ws_ex["A2"].font = SUB_FONT
EX_HEAD = ["Group", "Lines", "L12M quantity", "L12M billed (EUR)", "Why it is out"]


def ex_header(row):
    for i, h in enumerate(EX_HEAD, start=1):
        c = ws_ex.cell(row, i, h)
        c.fill = HDR_FILL
        c.font = HDR_FONT
        c.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)


reasons = {
    "no_price_on_one_side": "No base price on one side, so no step can be measured",
    "rebate_or_non_part_admin": "A rebate or an administrative charge, not a priced part",
    "lubricant_no_pr00_in_sap": "Lubricant with no official list price in the system",
}
ex_header(4)
r = 5
ex_rows = []
for key, grp in unpriced.groupby("unpriced_reason"):
    ws_ex.cell(r, 1, key)
    ws_ex.cell(r, 2, int(len(grp)))
    ws_ex.cell(r, 3, float(grp["billed_qty"].sum()))
    ws_ex.cell(r, 4, float(grp["net_sales_value"].sum()))
    ws_ex.cell(r, 5, reasons.get(key, ""))
    ex_rows.append(r)
    r += 1
ws_ex.cell(r, 1, "Excluded total")
ws_ex.cell(r, 2, f"=SUM(B{ex_rows[0]}:B{ex_rows[-1]})")
ws_ex.cell(r, 3, f"=SUM(C{ex_rows[0]}:C{ex_rows[-1]})")
ws_ex.cell(r, 4, f"=SUM(D{ex_rows[0]}:D{ex_rows[-1]})")
for col in "ABCD":
    ws_ex[f"{col}{r}"].font = TOT_FONT
r += 2

ws_ex.cell(r, 1, "Lines with no captured-demand position").font = SEC_FONT
r += 1
ex_header(r)
r += 1
ex_unclass_row = r
ws_ex.cell(r, 1, "No source on disk classifies the line")
ws_ex.cell(r, 2, f'=COUNTIF({PN}!${C_ZONE}:${C_ZONE},"Not classified")')
ws_ex.cell(r, 3, f'=SUMIF({PN}!${C_ZONE}:${C_ZONE},"Not classified",{PN}!${C_QTY}:${C_QTY})')
ws_ex.cell(r, 4, f'=SUMIF({PN}!${C_ZONE}:${C_ZONE},"Not classified",'
                 f'{PN}!${C_BILLED}:${C_BILLED})')
ws_ex.cell(r, 5, "Reported as unclassified. No bucket is invented for it.")
r += 2

ws_ex.cell(r, 1, "Lines with no independent market benchmark").font = SEC_FONT
r += 1
ex_header(r)
r += 1
ex_t5_row = r
ws_ex.cell(r, 1, "T5 - no benchmark on disk")
ws_ex.cell(r, 2, f'=COUNTIF({PN}!${C_TIER}:${C_TIER},"T5")')
ws_ex.cell(r, 3, f'=SUMIF({PN}!${C_TIER}:${C_TIER},"T5",{PN}!${C_QTY}:${C_QTY})')
ws_ex.cell(r, 4, f'=SUMIF({PN}!${C_TIER}:${C_TIER},"T5",{PN}!${C_BILLED}:${C_BILLED})')
ws_ex.cell(r, 5, "No price index can be computed. The two-gate rule forces a hold.")
r += 2

cmp_meta = json.loads(open(os.path.join(DERIVED, "price_bp_weighted_compare_meta.json"),
                           encoding="utf-8").read())
ws_ex.cell(r, 1, "Outside the distributor network").font = SEC_FONT
r += 1
ex_header(r)
r += 1
for lab, n, eur, why in [
    ("Service fees and administrative charges",
     cmp_meta["non_parts_excluded"]["rows"],
     cmp_meta["non_parts_excluded"]["l12m_billed_eur"], "Not a priceable part"),
    ("Direct account: trades, but is not a network distributor",
     cmp_meta["direct_account_excluded"]["rows"],
     cmp_meta["direct_account_excluded"]["l12m_billed_eur"],
     "Outside the network definition"),
]:
    ws_ex.cell(r, 1, lab)
    ws_ex.cell(r, 2, n)
    ws_ex.cell(r, 4, eur)
    ws_ex.cell(r, 5, why)
    r += 1
r += 1
ws_ex.cell(r, 1, "The specification's momentum term is not used here by design. This "
                 "workbook makes no allocation and proposes no price change.")
ws_ex.cell(r, 1).font = SUB_FONT

for rr in range(5, r):
    for col in (2, 3, 4):
        ws_ex.cell(rr, col).number_format = "#,##0.00" if col == 4 else "#,##0"
for col, w in zip("ABCDE", (50, 10, 13, 17, 56)):
    ws_ex.column_dimensions[col].width = w

# ============================================================ Checks
ws_ck["A1"] = "Reconciliation the reader can see"
ws_ck["A1"].font = TITLE_FONT
ws_ck["A2"] = ("Each line is a live formula against the PN data sheet, so a change that "
               "breaks the arithmetic shows up here rather than in a footnote.")
ws_ck["A2"].font = SUB_FONT
for i, h in enumerate(["Check", "Value", "Expected", "Result", "Note"], start=1):
    c = ws_ck.cell(4, i, h)
    c.fill = HDR_FILL
    c.font = HDR_FONT

SEG_SHEET = "'Increase by segment'!"


step_sum = f'SUM({PN}!${C_STEP}:${C_STEP})'
pct_sum = (f'SUMPRODUCT({PN}!${C_QTY}$2:${C_QTY}${last},'
           f'{PN}!${C_BP_NEW}$2:${C_BP_NEW}${last})'
           f'/SUMPRODUCT({PN}!${C_QTY}$2:${C_QTY}${last},'
           f'{PN}!${C_BP_PRIOR}$2:${C_BP_PRIOR}${last})-1')
checks = [
    ("Value of the step, summed from the PN data sheet", f"={step_sum}",
     EXPECT_STEP_EUR, "0.00", "The published figure for the network step."),
    ("Base price move, recomputed from the PN data sheet", f"={pct_sum}",
     EXPECT_PCT, "0.0000%", "Independent of the Overview formulas."),
    ("Base price move, weighted on the simulation quantity", f"={pct_sum}",
     EXPECT_SIM_PCT, "0.0000%",
     "A sensitivity reported alongside the headline; the gap is the weight basis."),
    ("Quantity the step is measured on", f'=SUM({PN}!${C_QTY}:${C_QTY})',
     EXPECT_QTY, "#,##0", "Priced quantity in the window."),
    ("L12M billed to dealer, priced lines", f'=SUM({PN}!${C_BILLED}:${C_BILLED})',
     EXPECT_BILLED_EUR, "#,##0.00", "Billed value of the priced lines."),
    ("Priced lines", f'=COUNTA({PN}!${C_PN}$2:${C_PN}${last})', EXPECT_LINES, "#,##0",
     "One row per distributor and part number."),
    ("Overview total ties to the PN data sheet",
     f'=Overview!$I${ov_total}-{step_sum}', 0, "#,##0.00",
     "The Overview total must equal the summed step."),
    ("Captured-demand segments sum to the network step",
     f'={SEG_SHEET}$G${seg_block_totals[0]}', EXPECT_STEP_EUR, "#,##0.00",
     "The position totals must add back to the network step."),
    ("Measured and proxy positions sum to the network step",
     f'={SEG_SHEET}$G${seg_block_totals[1]}', EXPECT_STEP_EUR, "#,##0.00",
     "Every line is either measured, a proxy, or named as not classified."),
    ("Price-index segments sum to the network step",
     f'={SEG_SHEET}$G${seg_block_totals[2]}', EXPECT_STEP_EUR, "#,##0.00",
     "Includes the lines with no computable index."),
    ("Evidence-tier segments sum to the network step",
     f'={SEG_SHEET}$G${seg_block_totals[3]}', EXPECT_STEP_EUR, "#,##0.00",
     "Every line carries exactly one tier."),
    ("Two-gate sign segments sum to the network step",
     f'={SEG_SHEET}$G${seg_block_totals[4]}', EXPECT_STEP_EUR, "#,##0.00",
     "Every line receives exactly one sign."),
]
checks = [c for c in checks if c[2] is not None]
checks.append(
    ("Price classes sum to the network step",
     f"='Increase by class'!$D${cls_total}", EXPECT_STEP_EUR, "#,##0.00",
     "The retained class view must add back to the same total."))
checks.append(
    ("Israel rows sum to the Israel lane",
     f"=Overview!$I${il_rows[0]}+Overview!$I${il_rows[1]}-Overview!$I${lane_rows[1]}",
     0, "#,##0.00", "UMI and UTI are reported separately and must tie to the lane."))
checks.append(
    ("Unclassified lines carry no sign",
     f'=COUNTIFS({PN}!${C_ZONE}:${C_ZONE},"Not classified",'
     f'{PN}!${C_ACTION}:${C_ACTION},"<>"&"UNCLASSIFIED - no position")',
     0, "#,##0", "A line with no position cannot be given an action."))
checks.append(
    ("Unclassified lines are named on the Excluded sheet",
     f"='Excluded'!$B${ex_unclass_row}", n_unclass, "#,##0",
     "The count written to the workbook matches the build."))

r = 5
check_rows = []
for lab, formula, exp, fmt, note in checks:
    ws_ck.cell(r, 1, lab)
    ws_ck.cell(r, 2, formula)
    ws_ck.cell(r, 3, exp)
    ws_ck.cell(r, 2).number_format = fmt
    ws_ck.cell(r, 3).number_format = fmt
    ws_ck.cell(r, 4, f'=IF(ABS(B{r}-C{r})<=MAX(ABS(C{r})*0.00005,0.02),"OK","CHECK")')
    ws_ck.cell(r, 5, note)
    check_rows.append(r)
    r += 1

r += 1
ws_ck.cell(r, 1, "Formula errors anywhere a reader looks").font = SEC_FONT
r += 1
ws_ck.cell(r, 1, "Count of error values in the computed columns")
ws_ck.cell(r, 2, f'=SUMPRODUCT(--ISERROR({PN}!${C_DELTA}$2:${C_DELTA}${last}))'
                 f'+SUMPRODUCT(--ISERROR({PN}!${C_STEP}$2:${C_STEP}${last}))'
                 f'+SUMPRODUCT(--ISERROR({PN}!${C_INDEX}$2:${C_INDEX}${last}))'
                 f'+SUMPRODUCT(--ISERROR({PN}!${C_PRICE_ZONE}$2:${C_PRICE_ZONE}${last}))'
                 f'+SUMPRODUCT(--ISERROR({PN}!${C_ACTION}$2:${C_ACTION}${last}))')
ws_ck.cell(r, 3, 0)
ws_ck.cell(r, 4, f'=IF(B{r}=0,"OK","CHECK")')
ws_ck.cell(r, 5, "A formula error in any computed column is a failure.")
err_row = r

r += 2
ws_ck.cell(r, 1, "Weighted base-price move, published").font = SEC_FONT
r += 1
ws_ck.cell(r, 1, "Network")
ws_ck.cell(r, 2, EXPECT_PCT)
ws_ck.cell(r, 2).number_format = "0.0000%"
r += 1
ws_ck.cell(r, 1, "Value of the step, published")
ws_ck.cell(r, 2, EXPECT_STEP_EUR)
ws_ck.cell(r, 2).number_format = "#,##0.00"
r += 1
ws_ck.cell(r, 1, "Priced coverage, quantity")
ws_ck.cell(r, 2, 0.9857)
ws_ck.cell(r, 2).number_format = "0.00%"
r += 1
ws_ck.cell(r, 1, "Priced coverage, billed euro")
ws_ck.cell(r, 2, 0.9315)
ws_ck.cell(r, 2).number_format = "0.00%"

for rr in check_rows + [err_row]:
    ws_ck.cell(rr, 2).alignment = Alignment(horizontal="right")
    ws_ck.cell(rr, 3).alignment = Alignment(horizontal="right")
    ws_ck.cell(rr, 4).font = Font(bold=True)
    ws_ck.cell(rr, 4).alignment = Alignment(horizontal="center")
for col, w in zip("ABCDE", (54, 16, 16, 10, 56)):
    ws_ck.column_dimensions[col].width = w

# ============================================================ Read me
read = [
    ("ISZE pricing simulation - specification basis", "title"),
    ("", ""),
    ("What this workbook is", "head"),
    ("A working model of the base-price step that is already published, with the "
     "reporting axis changed from the raw price class code to the segmentation set out "
     "in the pricing specification. It is laid out in the same shape as the existing "
     "pricing simulation workbook: the line detail on one data sheet, small summary "
     "sheets in front, one Legend sheet holding every dial, and an overview that rolls "
     "the lanes up. The prices, quantities and euro values are the published ones, "
     "unchanged.", ""),
    ("", ""),
    ("The basis and the window", "head"),
    ("The window is the last twelve months of available billing, 1 July 2025 to 30 June "
     "2026. The comparison is the CY2026 revision, which is the base price in force "
     "through that window, against the FY2027 base price filed on 10 September 2026. The "
     "weight is the quantity actually billed in the window.", ""),
    ("The headline is a base-price move weighted on last-twelve-month quantity: "
     "5.9616% on the network, worth EUR 1,652,141 on that volume. Priced coverage is "
     "98.57% of quantity and 93.15% of billed euro. Those figures are not restated here; "
     "the Checks sheet recomputes them from this workbook's own rows.", ""),
    ("Israel is reported as two distributors, UMI (1797) and UTI (1799), never as one "
     "blended figure. Armenia and Kazakhstan sit in the CIS lane.", ""),
    ("", ""),
    ("The reporting axis, and what replaced what", "head"),
    ("Captured-demand position. This replaces the price class code as the grouping axis. "
     "It comes from the capture rate on total parts billed: what dealers actually bought "
     "as a share of the demand the vehicles in service should generate. Total sales are "
     "used, not genuine only, so an alternative-brand sale still counts as a sale. The "
     "bands are:", ""),
    ("    Captive    - capture rate 0.80 and above", ""),
    ("    Contested  - capture rate 0.45 up to 0.80", ""),
    ("    Lost       - capture rate below 0.45", ""),
    ("A line the fallback ladder places carries the same three words, with the kind of "
     "position shown beside it so a proxy is never read as a measurement.", ""),
    ("The capture rate is defined for fourteen service categories. Where a line falls "
     "outside them, the specification's own fallback ladder is followed: the competitor "
     "file, then the parts-catalogue filter family, then the parts catalogue. Those "
     "fallback rungs give a contested or captive position only, never a measured one, and "
     "the position_kind column says which of the two a row is. The column "
     "classification_basis says which rung a line landed on and classification_source "
     "says where that came from. A line that no source on disk classifies is reported as "
     "not classified. No bucket is invented for it.", ""),
    ("Position against the independent aftermarket. The price index is the reference "
     "dealer price divided by the independent market price, where the reference dealer "
     "price is the official list price multiplied by the distributor margin of 1.40 and "
     "the dealer margin of 1.275. The bands are below reference (0.95 or under), in band, "
     "and above reference (1.15 or over). Every benchmark carries an evidence tier, and "
     "the tier is what limits how far a line could ever move:", ""),
    ("    T1  observed at the same shop, same part number         10pp", ""),
    ("    T2  derived from a published listing                    6pp", ""),
    ("    T3  Eucon benchmark, network level                       6pp", ""),
    ("    T4  category median                                      3pp", ""),
    ("    T5  no benchmark                                         0pp", ""),
    ("That limit is shown as a column on every line. It is not applied: this workbook "
     "proposes no price change.", ""),
    ("The two gates together. The two axes are read together and the combination gives "
     "the direction the specification points to, as a sign only:", ""),
    ("    Captive, any index                       +", ""),
    ("    Contested below 0.95                     +", ""),
    ("    Contested above 1.15                     -", ""),
    ("    Lost above 1.15                          - -", ""),
    ("    Lost below 0.95                          0 - investigate", ""),
    ("    Any line with no benchmark               0 - hold", ""),
    ("The cheap-and-still-losing case is deliberately held at investigate rather than "
     "cut. If the price already sits below the reference and the business is still being "
     "lost, price is not the problem, and cutting further would give up margin for "
     "nothing.", ""),
    ("", ""),
    ("What is measured and what is read across", "head"),
    ("Measured: the quantity and billed euro for every line, both base prices, the "
     "official list price, the source of supply, and the same-shop and Eucon competitor "
     "listings where they exist.", ""),
    ("Read across, not measured for the individual line: the capture rate is a measure at "
     "distributor and service-category level, and is applied to the lines inside that "
     "category. Where the ladder was used instead, the position is a proxy and is labelled "
     "as one. The price index is only as good as the benchmark behind it, which is why the "
     "evidence tier sits on every row.", ""),
    ("Carried from the specification rather than computed here: how far each tier may "
     "move a line, and the band edges. Both are cells on the Legend sheet, so they can be "
     "changed and the effect seen.", ""),
    ("", ""),
    ("What this model deliberately does not do", "head"),
    ("It does not change any published number. It does not propose, run or solve a price "
     "change, and it does not touch a price list. It does not run an allocation and it "
     "carries no elasticity coefficient, because a volume response cannot be quoted at "
     "this level in the chain. It does not carry a momentum or growth term. It does not "
     "compute a pricing-risk score. It uses derived tables only, never line-level billing "
     "extracts. Where an input does not exist on disk, the cell says so rather than "
     "holding a placeholder.", ""),
    ("", ""),
    ("How the sheets line up with the earlier workbook", "head"),
    ("    PN data              - the line detail (the earlier simulation sheet, now with a "
     "lane column and the specification columns)", ""),
    ("    Increase by segment  - the new axis view, with the two-gate sign", ""),
    ("    Increase by class    - the retained price class view", ""),
    ("    Israel, CIS          - the two special lanes", ""),
    ("    Legend               - every dial", ""),
    ("    Overview             - the lane roll-up", ""),
    ("    Excluded, Checks     - what is out, and the arithmetic", ""),
]
r = 1
for text, kind in read:
    c = ws_read.cell(r, 1, text)
    if kind == "title":
        c.font = TITLE_FONT
    elif kind == "head":
        c.font = SEC_FONT
    c.alignment = Alignment(wrap_text=True, vertical="top")
    r += 1
ws_read.column_dimensions["A"].width = 132

# ============================================================ delivery format
# The workspace pre-delivery rules: freeze the header on every sheet a reader
# scrolls, give the description column room, and wrap long labels so nothing is
# clipped or spills across a neighbour.
FORMS = {
    "Read me": ("A2", 48),
    "Overview": ("A6", 52),
    "Legend": ("A4", 56),
    "PN data": ("E2", 46),
    "Increase by segment": ("A5", 52),
    "Increase by class": ("A5", 30),
    "Israel": ("A5", 40),
    "CIS": ("A5", 40),
    "Excluded": ("A5", 56),
    "Checks": ("A5", 58),
}
for name, (freeze, desc_width) in FORMS.items():
    ws = wb[name]
    if ws.freeze_panes is None:
        ws.freeze_panes = freeze
    # Column B carries the long labels on the summary sheets; widen it and wrap.
    if name in ("Checks", "Increase by segment", "Increase by class",
                "Israel", "CIS", "Excluded", "Overview", "Legend", "PN data"):
        ws.column_dimensions["B"].width = max(
            ws.column_dimensions["B"].width or 0, 30)
    for row in ws.iter_rows():
        for cell in row:
            v = cell.value
            if isinstance(v, str) and len(v) > 40:
                cell.alignment = Alignment(
                    wrap_text=True,
                    vertical=cell.alignment.vertical if cell.alignment else None,
                    horizontal=cell.alignment.horizontal if cell.alignment else None,
                )

say("Saving ...")
wb.save(XLSX)
say(f"  saved {XLSX}")
zones = priced.apply(
    lambda x: (x["ladder_position"] if x["position_kind"] == "Proxy"
               else ("Captive" if pd.notna(x["capture_rate"]) and x["capture_rate"] >= 0.80
                     else "Contested" if pd.notna(x["capture_rate"])
                     and x["capture_rate"] >= 0.45
                     else "Lost" if pd.notna(x["capture_rate"])
                     else "Not classified")), axis=1)

meta_out = {
    "workbook": XLSX,
    "built": pd.Timestamp.now().isoformat(timespec="seconds"),
    "window": {"start": "2025-07-01", "end": "2026-06-30"},
    "lines_priced": int(len(priced)),
    "qty_priced": float(priced["billed_qty"].sum()),
    "billed_eur_priced": float(priced["net_sales_value"].sum()),
    "step_eur": step_eur,
    "weighted_pct": weighted,
    "unpriced_lines": int(len(unpriced)),
    "unpriced_eur": float(unpriced["net_sales_value"].sum()),
    "zone_counts": zones.value_counts().to_dict(),
    "zone_eur": priced.groupby(zones)["net_sales_value"].sum().to_dict(),
    "tier_counts": priced["evidence_tier"].value_counts().to_dict(),
    "tier_eur": priced.groupby("evidence_tier")["net_sales_value"].sum().to_dict(),
    "no_service_category_lines": n_nocat,
    "unclassified_lines": n_unclass,
    "unclassified_eur": eur_unclass,
    "t5_lines": n_t5,
    "t5_eur": eur_t5,
    "last_pn_row": last,
    "overview_total_row": ov_total,
    "seg_total_rows": seg_total_rows,
    "cls_total_row": cls_total,
    "check_rows": check_rows,
    "error_check_row": err_row,
}
with open(META, "w", encoding="utf-8") as fh:
    json.dump(meta_out, fh, indent=2, default=str)
say(f"  meta {META}")
say("")
say("BUILD_OK")
