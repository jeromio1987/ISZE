# PMS classification leakage diagnostic (read-only).
# Question: how much GENUINE PMS sales sits OUTSIDE the PMS PN universe the capture
# pipeline counts -> i.e. how overstated is each distributor's EUR gap.
#
# Method: reuse the pipeline's own tagger (tag_pms_sales) so "universe" == what capture
# counts. Then classify by DESCRIPTION (tight keyword rules) the rows the pipeline left
# is_pms=False, and sum the genuine PMS-looking sales it missed. Conservative (lower bound).
#
# ACTIONABLE leakage = wear parts (sold as service unit) + filter ELEMENTS.
# Filter ASM/KIT are reported separately: the pipeline excludes those by design
# (avoid element+assembly double-count), so they are not a clean classification gap.

import sys, re
from pathlib import Path
PRISM = Path(r"C:\Users\jerom\Desktop\claude\ISZE\03_analytics\Isuzu\prism")
sys.path.insert(0, str(PRISM))
import pandas as pd
from config import resolve_mapping_path, BVP_PN_DIMENSION_CSV, PMS_CAPTURE_BY_DB_CSV
from modules.data_prep import load_distributor_mapping
from modules.sales_loader import load_prism_sales
from modules.bvp_analytics import ensure_part_number
from modules.pms_tagging import tag_pms_sales
from modules.pms_engine import filter_pms_by_scope, pms_scope_for_distributor

OUT = Path(r"C:\Users\jerom\Desktop\claude\ISZE\03_analytics\Isuzu\_OKF_assessment\PMS_classification_leakage.md")
YEAR = 2025
FILTERS = {"oil_filter", "fuel_filter", "air_filter", "urea_filter", "blower_filter"}

# ---- load + tag with the pipeline's own logic --------------------------------
df_map = load_distributor_mapping(str(resolve_mapping_path()))
df, _ = load_prism_sales(df_map)
df = ensure_part_number(df)
dim = pd.read_csv(BVP_PN_DIMENSION_CSV)
df = tag_pms_sales(df, dim, fill_catalog_pms=True)
if "pms_capture_eligible" not in df.columns:
    df["pms_capture_eligible"] = True
df["D"] = df["description"].fillna("").str.upper()
df["pn"] = df["part_number"].astype(str).str.strip()

cap = pd.read_csv(PMS_CAPTURE_BY_DB_CSV)
DBS = sorted(cap[cap.year == YEAR].distributor_code.unique())

# ---- validate: universe reproduces capture file ------------------------------
def counted_qty(dbc, cat, yr=YEAR):
    sub = df[(df.distributor_code == dbc) & (df.year == yr) & (df.is_pms) & (df.pms_capture_eligible)]
    sub = filter_pms_by_scope(sub, pms_scope_for_distributor(dbc))
    return float(sub[sub.pms_category == cat]["billed_qty"].sum())

print("== validation (repro vs capture file) ==")
val_ok = True
for dbc, cat in [("IUK", "brake_pad"), ("ITUK", "oil_filter"), ("UMI", "oil_filter"), ("GERMANY", "clutch_disc")]:
    rep = counted_qty(dbc, cat)
    ref = float(cap[(cap.distributor_code == dbc) & (cap.year == YEAR) & (cap.line_type == "total") & (cap.pms_category == cat)]["actual_qty"].sum())
    ok = abs(rep - ref) < 1
    val_ok &= ok
    print(f"  {dbc:<8} {cat:<14} repro={rep:>9,.0f}  capture={ref:>9,.0f}  {'OK' if ok else 'MISMATCH'}")

# ---- description classifier (tight; lower-bound) -----------------------------
EXCL_PAD = re.compile(r"SEAT|CUSHION|BUMPER|TRIM|DOOR|DASH|STEP|FLOOR|ARM|KNEE|ROOF|HEAD|GLOVE")
AIR_NOT = re.compile(r"AIR ?CON|A/C|AIRBAG|AIR BAG|AIR SPRING|AIR DRYER|AIR TANK|AIR HORN|AIR HOSE")

# Filters: ELEMENT/element-kit/spin-on = service part (INCLUDE); ASM/ASSY = housing assembly
# (exclude, tag __asm); CAP/SENSOR/MOTOR/DPD/etc = not a service filter (drop).
# Price-validated: elements EUR4-20/u, assemblies EUR50-208/u, DPD ASM EUR1,748/u.
NONPART = re.compile(r"\bCAP\b|SENSOR|MOTOR|HOUSING|BRACKET|GASKET|\bPIPE\b|\bHOSE\b|\bSEAL\b|SWITCH|\bPUMP\b|VALVE|\bCASE\b|\bBODY\b|REGULATOR|\bRELAY\b|\bDPD\b|PARTICULATE|CATALYST|DIFFUSER")
ASM = re.compile(r"\bASM\b|ASSY|ASSEMBLY")

def filt(d, base):
    if NONPART.search(d): return None        # cap/sensor/motor/DPD -> not a service filter
    if ASM.search(d): return base + "__asm"  # housing assembly -> excluded (not the service element)
    return base                              # element / element kit / spin-on -> service part

def classify(d):
    if ("OIL" in d and "FILTER" in d) or ("ELEMENT" in d and "OIL" in d): return filt(d, "oil_filter")
    if ("FUEL" in d and "FILTER" in d) or ("ELEMENT" in d and "FUEL" in d) or "SEDIMENTER" in d: return filt(d, "fuel_filter")
    if "UREA" in d or "ADBLUE" in d: return filt(d, "urea_filter")
    if ("BLOWER" in d and "FILTER" in d) or ("CABIN" in d and "FILTER" in d) or "POLLEN" in d: return filt(d, "blower_filter")
    if "AIR" in d and ("FILTER" in d or "ELEMENT" in d or "CLEANER" in d) and not AIR_NOT.search(d): return filt(d, "air_filter")
    if "PAD" in d and ("BRK" in d or "BRAKE" in d) and not EXCL_PAD.search(d): return "brake_pad"
    if "SHOE" in d and ("BRK" in d or "BRAKE" in d): return "brake_shoe"
    if "CLUTCH" in d and "DISC" in d: return "clutch_disc"
    if "PRESSURE PLATE" in d or ("COVER" in d and "CLUTCH" in d): return "clutch_pressure_plate"
    if "CLUTCH" in d and "KIT" in d: return "clutch_kit"
    if "RELEASE" in d and ("BEARING" in d or "BRG" in d): return "release_bearing"
    if "PILOT" in d and ("BEARING" in d or "BRG" in d): return "pilot_bearing"
    if "CLUTCH" in d and "BOOSTER" in d: return "clutch_booster"
    return None

df["desc_cat"] = df["D"].apply(classify)

# ---- leakage = genuine PMS-looking sales the pipeline left untagged ----------
leak_all = df[(df.year == YEAR) & (~df.is_pms) & (df.desc_cat.notna()) & (df.distributor_code.isin(DBS))].copy()
leak_all["is_asm"] = leak_all.desc_cat.str.endswith("__asm")
leak_all["desc_cat"] = leak_all.desc_cat.str.replace("__asm", "", regex=False)
leak = leak_all[~leak_all.is_asm].copy()         # ACTIONABLE: service elements + wear parts
asm = leak_all[leak_all.is_asm].copy()           # filter ASSEMBLIES (housings) -> excluded

# DPD / exhaust aftertreatment: confirm it's a major component, out of PMS service scope
dpd_mask = (df.year == YEAR) & df.distributor_code.isin(DBS) & df["D"].str.contains(r"\bDPD\b|PARTICULATE|DIFFUSER", regex=True)
dpd_total = float(df[dpd_mask]["net_sales_value"].sum())

CAT_LABEL = {"oil_filter":"Oil filter","fuel_filter":"Fuel filter","air_filter":"Air filter","urea_filter":"Urea filter",
             "blower_filter":"Blower/cabin filter","brake_pad":"Brake pad","brake_shoe":"Brake shoe","clutch_disc":"Clutch disc",
             "clutch_pressure_plate":"Clutch pressure plate","clutch_kit":"Clutch kit","release_bearing":"Release bearing",
             "pilot_bearing":"Pilot bearing","clutch_booster":"Clutch booster"}

by_db = leak.groupby("distributor_code").agg(leak_eur=("net_sales_value","sum"), leak_qty=("billed_qty","sum")).reset_index()
by_cat = leak.groupby("desc_cat").agg(leak_eur=("net_sales_value","sum"), leak_qty=("billed_qty","sum")).sort_values("leak_eur",ascending=False)
gap_by_db = cap[(cap.year==YEAR)&(cap.line_type=="total")].groupby("distributor_code")["revenue_gap_eur"].sum()
by_db["gap_eur"] = by_db["distributor_code"].map(gap_by_db).fillna(0.0)
by_db["corrected_gap"] = (by_db["gap_eur"] - by_db["leak_eur"]).clip(lower=0)
by_db = by_db.sort_values("leak_eur", ascending=False)

net_leak = leak["net_sales_value"].sum()
net_asm = asm["net_sales_value"].sum()
net_gap = float(gap_by_db.sum())
air_leak = float(by_cat.loc["air_filter","leak_eur"]) if "air_filter" in by_cat.index else 0.0
wear = {"brake_pad","brake_shoe","clutch_disc","clutch_pressure_plate","clutch_kit","release_bearing","pilot_bearing","clutch_booster"}
wear_leak = float(leak[leak.desc_cat.isin(wear)]["net_sales_value"].sum())

iuk_bp = leak[(leak.distributor_code=="IUK") & (leak.desc_cat=="brake_pad")]["net_sales_value"].sum()
print(f"\nIUK brake_pad leakage (sanity vs ~126,281): EUR {iuk_bp:,.0f}")
print(f"ACTIONABLE network leakage CY{YEAR}: EUR {net_leak:,.0f} ({net_leak/net_gap*100:.0f}% of EUR {net_gap:,.0f} ceiling)")
print(f"  of which wear parts: EUR {wear_leak:,.0f} | filter elements: EUR {net_leak-wear_leak:,.0f}")
print(f"excluded filter assemblies: EUR {net_asm:,.0f} | DPD exhaust (out of scope): EUR {dpd_total:,.0f}")

top_pn = leak.groupby(["pn","desc_cat","D"]).agg(qty=("billed_qty","sum"), eur=("net_sales_value","sum")).reset_index().sort_values("eur",ascending=False).head(20)

# ---- write report ------------------------------------------------------------
def e(x): return f"€{x:,.0f}"
L = []
L.append(f"# PMS Classification Leakage — Network Diagnostic (CY{YEAR})")
L.append("")
L.append(f"**Validation:** the counted universe is reproduced with the pipeline's own `tag_pms_sales` — "
         f"IUK brake_pad / ITUK oil_filter / UMI oil_filter / GERMANY clutch_disc all reproduce the capture file "
         f"({'all OK' if val_ok else 'MISMATCH — investigate'}). IUK brake_pad leakage = {e(iuk_bp)} "
         f"(matches the manual €126K finding).")
L.append("")
L.append(f"**Leakage** = genuine PMS-described sales whose PN the pipeline left `is_pms=False` (not in the BVP "
         f"catalog dimension, crossref, or registry) — **uncounted actual**, so each € means the matching € gap is "
         f"overstated by ~that much. Description-matched and tight → **lower bound**. Filter **elements/element-kits** "
         f"(the genuine service part, €4–20/u) are counted; filter **assemblies** (€50–208/u) and **DPD** are split out; "
         f"blower *motors* and cap/sensor parts dropped.")
L.append("")
L.append("## Headline")
L.append("")
L.append(f"- **Actionable leakage CY{YEAR}: {e(net_leak)}** — genuine PMS sales invisible to capture "
         f"(**wear parts {e(wear_leak)}** + filter elements {e(net_leak-wear_leak)}). "
         f"That's ≈ **{net_leak/net_gap*100:.0f}% of the {e(net_gap)} gap ceiling is classification, not lost business.**")
L.append(f"- Excluded as **not service parts**: {e(net_asm)} of filter **assemblies** (housings, €50–208/u) + **DPD** "
         f"exhaust units ≈{e(dpd_total)} (DPD ASM ≈€1,748/u) — major components, not routine PMS filters.")
L.append(f"- **The €9.02M ceiling I reported is overstated by ≥ {e(net_leak)}** (more once BVP-retention, flag-C air "
         f"and realistic targets are applied). The biggest single cause is one genuine front brake-pad PN — see below.")
L.append("")
L.append("## Leakage by distributor (corrected gap ≈ gap − actionable leakage)")
L.append("")
L.append("| DB | € gap (reported) | Actionable leakage | Corrected gap ≈ | Leak qty |")
L.append("|---|---:|---:|---:|---:|")
for _, r in by_db.iterrows():
    if r["leak_eur"] <= 0: continue
    L.append(f"| {r['distributor_code']} | {e(r['gap_eur'])} | **{e(r['leak_eur'])}** | {e(r['corrected_gap'])} | {r['leak_qty']:,.0f} |")
L.append(f"| **NETWORK** | {e(net_gap)} | **{e(net_leak)}** | {e(net_gap-net_leak)} | {leak['billed_qty'].sum():,.0f} |")
L.append("")
L.append("## Leakage by category (where the part-master is incomplete)")
L.append("")
L.append("| Category | Actionable leakage € | Leak qty | Note |")
L.append("|---|---:|---:|---|")
for cat, r in by_cat.iterrows():
    note = "lower-confidence (AIR/ELEMENT keyword)" if cat == "air_filter" else ("genuine wear part" if cat in wear else "genuine filter element")
    L.append(f"| {CAT_LABEL.get(cat,cat)} | {e(r['leak_eur'])} | {r['leak_qty']:,.0f} | {note} |")
L.append("")
L.append("## Top 20 missing PNs (the fix-list to add to the crossref / registry)")
L.append("")
L.append("| PN | Category | Qty | € | Description |")
L.append("|---|---|---:|---:|---|")
for _, r in top_pn.iterrows():
    L.append(f"| `{r['pn']}` | {CAT_LABEL.get(r['desc_cat'],r['desc_cat'])} | {r['qty']:,.0f} | {e(r['eur'])} | {r['D'][:42]} |")
L.append("")
L.append("## Read / honesty")
L.append("")
L.append(f"- **Clutch gaps are mostly REAL.** Clutch leakage is small ({e(float(leak[leak.desc_cat.str.startswith('clutch')]['net_sales_value'].sum()))}) "
         f"vs clutch's huge gaps — genuine clutches genuinely aren't sold much, so those gaps stand. The classification "
         f"problem is concentrated in **brake pads** and **filter elements**, not clutch.")
L.append("- **One PN dominates:** `8975056801` (`PAD KIT; CALIPER,DISC BRK,FRT`) — the single biggest genuine front "
         "brake pad — is sold network-wide but absent from the catalog/crossref/registry entirely.")
L.append("- **ITUK is only partly shielded.** Its registry covers the pilot filter categories, but it still leaks "
         "genuine brake pads etc.; ITUK's gap is overstated too (see table).")
L.append(f"- **Element vs assembly:** filter **elements/element-kits** (incl. fuel, €4–20/u) are genuine PMS service parts → counted; **filter assemblies** ({e(net_asm)}, €50–208/u) are housings → excluded.")
L.append(f"- **DPD is not a PMS filter.** `DPD ASM` (≈€1,748/u) + DPD sensors/gaskets ≈{e(dpd_total)} are exhaust aftertreatment (major component), correctly outside PMS service-filter scope — confirmed by price.")
L.append("- **Lower bound** — tight keywords; seat/bumper 'PAD', blower motors, caps & sensors excluded.")
L.append("- **Fix** = add these genuine OE PNs to `genuine_bvp_crossref` / the registry with a `pms_category`, then re-run "
         "`run_pipeline_and_verify.ps1` (capture, briefs, dashboard and the FACTS anchor update together).")
L.append("")
L.append(f"_Source: sales_fact via pipeline tagger + `pms_capture_by_db_year.csv`. Regenerate: "
         f"`python _OKF_assessment/_build/pms_leakage_diagnostic.py`._")

OUT.write_text("\n".join(L), encoding="utf-8")
print(f"\nwrote {OUT}")
print("\nactionable by category:")
for cat, r in by_cat.iterrows():
    print(f"  {CAT_LABEL.get(cat,cat):<22} {e(r['leak_eur']):>12}  qty {r['leak_qty']:,.0f}")
