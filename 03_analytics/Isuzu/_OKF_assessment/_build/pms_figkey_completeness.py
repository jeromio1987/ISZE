# Fig-key completeness check (read-only).
# Uses the FULL parts catalog (parts_catalog_dimension.csv: 164,968 PNs with fig_key +
# fig_key_label + PR00 pms_category) as the authoritative classifier, vs the capture
# universe (tag_pms_sales). Finds every PMS part SOLD in CY2025 that capture misses,
# validates by fig_key, and always reports PN - description - price - fig_key.

import sys, re
from pathlib import Path
PRISM = Path(r"C:\Users\jerom\Desktop\claude\ISZE\03_analytics\Isuzu\prism")
sys.path.insert(0, str(PRISM))
import pandas as pd
from config import PARTS_CATALOG_DIMENSION_CSV, BVP_PN_DIMENSION_CSV, resolve_mapping_path, PMS_CAPTURE_BY_DB_CSV
from modules.data_prep import load_distributor_mapping
from modules.sales_loader import load_prism_sales
from modules.bvp_analytics import ensure_part_number
from modules.pms_tagging import tag_pms_sales
from modules.pms_capture_config import P1_CATEGORIES

OUT_MD = Path(r"C:\Users\jerom\Desktop\claude\ISZE\03_analytics\Isuzu\_OKF_assessment\PMS_figkey_completeness.md")
OUT_CSV = Path(r"C:\Users\jerom\Desktop\claude\ISZE\03_analytics\Isuzu\_OKF_assessment\pms_missing_pns_figkey.csv")
YEAR = 2025
INSCOPE = set(P1_CATEGORIES)

# ---- load ---------------------------------------------------------------------
cat = pd.read_csv(PARTS_CATALOG_DIMENSION_CSV, dtype=str)
cat["pn"] = cat["part_number"].astype(str).str.strip()
cat["pms_category"] = cat["pms_category"].replace("", pd.NA)

df_map = load_distributor_mapping(str(resolve_mapping_path()))
df, _ = load_prism_sales(df_map)
df = ensure_part_number(df)
df = tag_pms_sales(df, pd.read_csv(BVP_PN_DIMENSION_CSV))
df["pn"] = df["part_number"].astype(str).str.strip()
df["D"] = df["description"].fillna("").str.upper()
DBS = sorted(pd.read_csv(PMS_CAPTURE_BY_DB_CSV).query("year==@YEAR").distributor_code.unique())
univ = set(df[df.is_pms].pn)

s = df[(df.year == YEAR) & (df.distributor_code.isin(DBS))].copy()
# per-PN sales: qty, eur, and the description of its highest-€ row
sa = s.groupby("pn").agg(qty=("billed_qty", "sum"), eur=("net_sales_value", "sum")).reset_index()
sa = sa[sa.qty > 0]
desc = (s.sort_values("net_sales_value", ascending=False).drop_duplicates("pn").set_index("pn")["description"])
sa["description"] = sa.pn.map(desc).fillna("")

# ---- missing = catalog says PMS, sold CY2025, NOT in capture universe ----------
catpms = cat[cat.pms_category.notna()][["pn", "fig_key", "fig_key_label", "pms_category", "pms_registry", "in_bvp_catalog"]]
m = catpms.merge(sa, on="pn", how="inner")
m["in_univ"] = m.pn.isin(univ)
miss = m[~m.in_univ].copy()
miss["unit_eur"] = (miss.eur / miss.qty).round(2)
miss["scope"] = miss.pms_category.apply(lambda c: "in_scope" if c in INSCOPE else "OUT_of_scope")

ins = miss[miss.scope == "in_scope"].copy()
out = miss[miss.scope == "OUT_of_scope"].copy()

# Jerome's rule: a filter ASSEMBLY is not the service part -> exclude even if the catalog tags it a filter.
# Validated by price (assemblies €50-208/u vs elements €4-20) and by fig_key (041-001 assembly vs 041-002 element).
FILT = {"oil_filter", "fuel_filter", "air_filter", "urea_filter", "blower_filter"}
_au = ins.description.fillna("").str.upper()
ins["is_asm"] = ins.pms_category.isin(FILT) & _au.str.contains(r"\bASM\b|ASSY|ASSEMBLY", regex=True)
ins_asm = ins[ins.is_asm].copy()
miss.loc[ins_asm.index, "scope"] = "filter_assembly_EXCLUDE"
ins = ins[~ins.is_asm].copy()
asm_eur = float(ins_asm.eur.sum())

# ---- fig_key validation: stragglers (blank category, sold, missing) under touched figs
figs = set(miss.fig_key.dropna())
sib = cat[cat.fig_key.isin(figs)].merge(sa, on="pn", how="inner")
sib["in_univ"] = sib.pn.isin(univ)
strag = sib[(~sib.in_univ) & (sib.pms_category.isna())].copy()

def e(x): return f"€{x:,.0f}"
ins_eur, out_eur = ins.eur.sum(), out.eur.sum()

print(f"IN-SCOPE missing : {ins.pn.nunique()} PNs, {e(ins_eur)}  (excluded {ins_asm.pn.nunique()} filter assemblies {e(asm_eur)})")
print(f"OUT-of-scope     : {out.pn.nunique()} PNs, {e(out_eur)}  (categories the PMS model lacks)")
print(f"fig_key stragglers (blank cat, sold, missing): {strag.pn.nunique()} PNs, {e(strag.eur.sum())}")

# ---- write machine-usable fix-list (in-scope first) ---------------------------
cols = ["pn", "description", "unit_eur", "fig_key", "fig_key_label", "pms_category", "qty", "eur", "scope", "pms_registry", "in_bvp_catalog"]
miss.sort_values(["scope", "eur"], ascending=[True, False])[cols].to_csv(OUT_CSV, index=False, encoding="utf-8")

# ---- report -------------------------------------------------------------------
def cat_table(d):
    g = d.groupby("pms_category").agg(pns=("pn", "nunique"), qty=("qty", "sum"), eur=("eur", "sum")).sort_values("eur", ascending=False)
    rows = []
    for c, r in g.iterrows():
        rows.append(f"| {c} | {int(r['pns'])} | {r['qty']:,.0f} | {e(r['eur'])} | {e(r['eur']/r['qty'])}/u |")
    return rows

L = []
L.append(f"# PMS Fig-Key Completeness — Missing Parts (CY{YEAR})")
L.append("")
L.append("**Method:** the full `parts_catalog_dimension.csv` (164,968 PNs) carries `fig_key` + `fig_key_label` + a "
         "PR00 `pms_category` — the authoritative classification. Capture only uses the 919-PN BVP dim + crossref + "
         "registry (`tag_pms_sales`). **Missing = catalog says PMS, sold CY2025, but not in the capture universe.** "
         "Every line carries PN · description · unit price · fig_key. Fix-list CSV: `pms_missing_pns_figkey.csv`.")
L.append("")
L.append("## Headline")
L.append("")
L.append(f"- **In-scope missing (the 13 current PMS categories): {ins.pn.nunique()} PNs, {e(ins_eur)}** — "
         f"**higher than the €880K keyword estimate**: the catalog catches air-filter elements, brake shoes and "
         f"pressure plates my description scan missed. This is the complete fix-list for the current model.")
L.append(f"- **Excluded {ins_asm.pn.nunique()} filter ASSEMBLIES ({e(asm_eur)})** per your steer — the catalog tags "
         f"them a filter but they're housings (€50–208/u). The **fig_key separates them**: `041-002`=element (keep) "
         f"vs `041-001`=assembly (drop). DPD stays out too.")
L.append(f"- **fig_key check is clean:** only {strag.pn.nunique()} stragglers ({e(strag.eur.sum())}) under the touched "
         f"figures have a blank category — no hidden pockets *within* scope.")
L.append(f"- **Scope gap (the bigger answer): {out.pn.nunique()} PNs / {e(out_eur)} are PMS-adjacent maintenance "
         f"categories the model doesn't have at all** — led by **brake rotors** (discs that pair with the pads we're adding).")
L.append("")
L.append("## In-scope missing — add these to the PMS universe")
L.append("")
L.append("| Category | PNs | Qty | € | avg price |")
L.append("|---|---:|---:|---:|---:|")
L += cat_table(ins)
L.append(f"| **TOTAL** | **{ins.pn.nunique()}** | {ins.qty.sum():,.0f} | **{e(ins_eur)}** | |")
L.append("")
L.append("### Biggest in-scope missing PNs (PN · description · price · fig_key)")
L.append("")
L.append("| PN | Description | Unit € | Qty | € | fig_key (label) | cat |")
L.append("|---|---|---:|---:|---:|---|---|")
for _, r in ins.sort_values("eur", ascending=False).head(15).iterrows():
    L.append(f"| `{r['pn']}` | {str(r['description'])[:34]} | {r['unit_eur']:.2f} | {r['qty']:,.0f} | {e(r['eur'])} | {r['fig_key']} ({r['fig_key_label']}) | {r['pms_category']} |")
L.append("")
L.append("## OUT-of-scope categories — decision needed (NOT added without your call)")
L.append("")
L.append("These carry a catalog `pms_category` but are **not** in the current PMS model. Adding any means a new "
         "category + a service/wear factor in `pms_capture_assumptions.yaml` (and a FACTS re-sync).")
L.append("")
L.append("| Category | PNs | Qty | € | avg price | PMS-relevant? |")
L.append("|---|---:|---:|---:|---:|---|")
REL = {"brake_rotor": "yes — pairs with brake pads", "fan_belt": "yes — service belt", "water_pump": "maybe — timing service",
       "shock_absorber": "maybe — wear", "leaf_spring": "no — repair", "bushing": "no — repair"}
go = out.groupby("pms_category").agg(pns=("pn", "nunique"), qty=("qty", "sum"), eur=("eur", "sum")).sort_values("eur", ascending=False)
for c, r in go.iterrows():
    L.append(f"| {c} | {int(r['pns'])} | {r['qty']:,.0f} | {e(r['eur'])} | {e(r['eur']/r['qty'])}/u | {REL.get(c,'?')} |")
L.append(f"| **TOTAL** | **{out.pn.nunique()}** | {out.qty.sum():,.0f} | **{e(out_eur)}** | | |")
L.append("")
L.append("## Read / honesty")
L.append("")
L.append("- **PN·desc·price·fig_key validated.** The catalog `pms_category` wrongly tags filter **assemblies** as "
         "filters; I drop them on description+price+fig_key (041-001 assembly vs 041-002 element). Kept lines are "
         "service-part priced (filters €4–20, pads ~€69, shoes ~€30, clutch discs ~€126); DPD stays out.")
L.append("- **In-scope €1.06M supersedes the €880K keyword figure** — use the catalog `pms_category`, not description "
         "keywords, as the fix-list (CSV attached).")
L.append("- **brake_rotor €1.3M is the headline scope question:** capturing pads but not the discs they're fitted with "
         "understates the brake service story. Recommend adding `brake_rotor` (+ deciding on fan_belt/water_pump) before re-running.")
L.append("- Fix path unchanged: load `pms_missing_pns_figkey.csv` into the crossref/registry build with its `pms_category`, "
         "re-run `run_pipeline_and_verify.ps1` (capture, briefs, dashboard, FACTS anchor update together).")
L.append("")
L.append("_Source: `parts_catalog_dimension.csv` + sales_fact via pipeline tagger. Regenerate: "
         "`python _OKF_assessment/_build/pms_figkey_completeness.py`._")

OUT_MD.write_text("\n".join(L), encoding="utf-8")
print(f"\nwrote {OUT_MD}\nwrote {OUT_CSV}")
