"""Room-to-raise scan, per part number: where can the +5% best come from once the market holds apply?

Jerome's go, 2 Oct 2026. Read-only on every source; writes only into this folder.
Does NOT touch the proposal workbook, the market exercise or the pricing paper.

Inputs (all local, read-only):
  proposal base + evidence  ../evidence_lib.py (price_bp_weighted_compare_pn.csv, in scope and movable)
  proposal move per part    recomputed here with the builder's own formula (asserted against its summary JSON)
  market holds              ../market_exercise_decisions_2026-09-30.json + the exercise's segment rule (market_facts.py)
  outside prices            01_data/00_derived/price_observations.parquet, method of
                            04_tools/aftermarket_intelligence/build_parts_price_dashboard.py (x 2.19, VAT strip, median per part)
  competitor numbers        04_tools/aftermarket_intelligence/state/crossref_graded.csv (confirmed / likely)
  AIM family                approved release via 04_tools/_shared/classification_paths.approved_release()
  order lines / order type  01_data/00_derived/sales_fact.parquet (parquet, never the raw XLSX)
  dealer response           ../response_lib.py loaders, sales-to-dealer monthly files (UK trucks, UK D-Max, Ireland, Portugal)
  vehicle line              vehicle_family_bands.csv, APL part lists 2026-08-12, distributor_dimension.csv scope
  P700 new-only             book_b_provisional_weights.csv (bucket p700_new_only_seed)

Run:  python build_room_to_raise_20261002.py
      python build_room_to_raise_20261002.py --variant-b-iuk-exempt
        (opt-in, added 2 Oct for the pricing paper: option B with IUK lines kept at their proposal move.
         Writes ONLY room_to_raise_variant_B_iuk_exempt_2026-10-02.{csv,json}; every default output is left untouched.)
"""
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
PROP = HERE.parent
ISZE = Path(r"C:\Users\jerom\Desktop\claude\ISZE")
D = ISZE / "01_data" / "00_derived"
sys.path.insert(0, str(PROP))
sys.path.insert(0, str(ISZE / "04_tools" / "_shared"))
sys.path.insert(0, str(ISZE / "04_tools" / "aftermarket_intelligence"))
from evidence_lib import attach_evidence, load_base  # noqa: E402
from response_lib import load_ituk_monthly, load_lists, window_qty, z10  # noqa: E402
from classification_paths import approved_release  # noqa: E402
import build_parts_price_dashboard as ppd  # noqa: E402  (constants only; main() not run)

TODAY = pd.Timestamp("2026-10-02")
TARGET = 0.05
W0, W1 = pd.Timestamp("2025-07-01"), pd.Timestamp("2026-06-30")   # the proposal base window
CIS = {"ARMENIA", "KAZAKHSTAN"}                                    # as in the market exercise (Ukraine is not in it)
OUT_PART = HERE / "room_to_raise_by_part_2026-10-02.csv"
OUT_PM = HERE / "room_to_raise_by_part_market_2026-10-02.csv"
OUT_SCN = HERE / "room_to_raise_scenarios_2026-10-02.csv"
OUT_SEG = HERE / "room_to_raise_scenarios_by_segment_market_2026-10-02.csv"
OUT_LEV = HERE / "lever4_order_terms_2026-10-02.csv"
OUT_JSON = HERE / "room_to_raise_summary_2026-10-02.json"
VARIANT_IUK = "--variant-b-iuk-exempt" in sys.argv   # opt-in; default run unchanged
OUT_VAR_CSV = HERE / "room_to_raise_variant_B_iuk_exempt_2026-10-02.csv"
OUT_VAR_JSON = HERE / "room_to_raise_variant_B_iuk_exempt_2026-10-02.json"
S = {}   # summary written at the end

# ===================================================================== 0. proposal, recomputed
PSUM = json.loads((PROP / "price_5pct_proposal_summary_2026-09-29.json").read_text(encoding="utf-8"))
DEC = json.loads((PROP / "market_exercise_decisions_2026-09-30.json").read_text(encoding="utf-8"))
ins = load_base()
L = attach_evidence(ins[ins.movable].copy())
assert len(L) == 47617
L["c"] = L.bp_new_jpy / L.bp_prior_revised - 1
ks = L.evidence_tier.isin(["T1", "T2"])
L["idx_ks"] = np.where(ks, L.ref_dealer_price_eur / L.independent_price_eur, np.nan)
L["lost"] = (L.zone_basis == "Measured") & (L.zone == "Lost")
TL = {"T1": 0.10, "T2": 0.06}
import yaml  # noqa: E402
CFG = yaml.safe_load((ISZE / "03_analytics" / "isze_pricing" / "config.yaml").read_text(encoding="utf-8"))
TL = {"T1": CFG["allocation"]["tier_limit"]["T1_ks_observed"], "T2": CFG["allocation"]["tier_limit"]["T2_ks_derived"]}
L["room_line"] = ks & (L.idx_ks < 0.95) & ~L.lost
L["room"] = np.where(L.room_line, np.minimum(L.evidence_tier.map(TL).fillna(0),
                                             np.clip(1.15 / L.idx_ks - 1, 0, None)), 0.0)
g = L.groupby("pn")
P = pd.DataFrame({"billed": g.net_sales_value.sum(), "qty": g.billed_qty.sum(), "c": g.c.first()})
desc = L.sort_values("net_sales_value", ascending=False).drop_duplicates("pn").set_index("pn").billed_description
P["desc"] = desc.reindex(P.index).fillna("").astype(str).str.slice(0, 60)
P["padkit"] = P.desc.str.upper().str.contains(r"PAD\s*KIT").astype(int)
P["h_lost"] = (L[L.lost].groupby("pn").net_sales_value.sum().reindex(P.index).fillna(0) / P.billed).clip(0, 1)
P["r"] = (L.room * L.net_sales_value).groupby(L.pn).sum().reindex(P.index).fillna(0) / P.billed
cpos = P.c.clip(lower=0)
keep = 1 - P.padkit
k = (TARGET * P.billed.sum() - (P.billed * P.r * keep).sum()) / (P.billed * cpos * (1 - P.h_lost) * keep).sum()
P["prop"] = keep * (cpos * k * (1 - P.h_lost) + P.r)
TOT_BASE = float(P.billed.sum())
TOT_STEP = float((P.billed * P.prop).sum())
assert abs(k - PSUM["k"]) < 1e-6 and abs(TOT_STEP - PSUM["step_eur"]) < 0.5, (k, TOT_STEP)
S["proposal"] = {"base_eur": TOT_BASE, "step_eur": TOT_STEP, "scaling_k": k, "parts": int(len(P)),
                 "pad_kits": int(P.padkit.sum()), "check": "k and step equal price_5pct_proposal_summary_2026-09-29.json"}

# ===================================================================== 1. segments + markets (exercise rule)
dd = pd.read_csv(D / "distributor_dimension.csv", dtype=str)
code_of = dict(zip(dd.sold_to_sap, dd.distributor_code))
scope_of = dict(zip(dd.distributor_code, dd.scope))
L["db"] = L.customer_code.astype(str).map(code_of)
aimv2 = pd.read_csv(D / "aim_master_v2.csv", dtype=str, usecols=["part_number", "aim_l1", "cat_pms_flag"])
aimv2["pn"] = z10(aimv2.part_number)
aimv2 = aimv2.drop_duplicates("pn").set_index("pn")
bvp = pd.read_csv(D / "genuine_bvp_crossref.csv", dtype=str)
pms = set(z10(bvp.dropna(subset=["pms_category"]).genuine_pn)) | set(z10(bvp.dropna(subset=["pms_category"]).bvp_pn)) \
    | set(aimv2.index[aimv2.cat_pms_flag == "1"])
bvp_alt = set(z10(bvp.genuine_pn.dropna()))
# exercise rule (aim_master_v2 family), kept only to reconcile with the published EUR 388,040
P["seg_ex"] = np.select([P.index.map(aimv2.aim_l1).astype(str) == "Accident & Body", P.index.isin(pms)],
                        ["body", "service"], default="repair")

# approved AIM release
rel_path, rel_entry = approved_release()
rel = pd.read_csv(rel_path, dtype=str, usecols=["part_number", "catalog_l1", "catalog_l2", "aim_l1_fixed",
                                                 "aim_l2_fixed", "aim_l3_fixed", "line_kind"])
rel["pn"] = z10(rel.part_number)
rel = rel.drop_duplicates("pn").set_index("pn")
for col in ["catalog_l1", "catalog_l2", "aim_l1_fixed", "aim_l2_fixed", "aim_l3_fixed", "line_kind"]:
    P[col] = rel[col].reindex(P.index)
# segment on the APPROVED release family (coordinator 2 Oct: release labels, not pr00 / master)
P["seg"] = np.select([P.aim_l1_fixed.astype(str) == "Accident & Body", P.index.isin(pms)],
                     ["body", "service"], default="repair")
L["seg"] = L.pn.map(P.seg)
L["seg_ex"] = L.pn.map(P.seg_ex)
S["segment_rule"] = {"used": "body = release aim_l1 Accident & Body; service = BVP-crossref PMS categories + master PMS flag; repair = rest",
                     "parts_changed_vs_exercise_rule": int((P.seg != P.seg_ex).sum()),
                     "billed_changed_vs_exercise_rule": round(float(P.billed[P.seg != P.seg_ex].sum()), 0)}
S["aim_release"] = {"release_id": rel_entry["release_id"], "status": rel_entry["status"], "sha256": rel_entry["sha256"],
                    "path": str(rel_path), "parts_in_base_found": int(P.catalog_l1.notna().sum())}

# lubricants (standing exclusion): same rule as the proposal + release lubricant labels
P["lubricant"] = ((P.index.str.startswith("05") & P.desc.str.upper().str.contains("RIM|TELLUS|SHELL|HELIX|SPIRAX|OMALA|GADUS"))
                  | (P.line_kind == "lubricant_or_tool") | (P.aim_l2_fixed.fillna("") == "Lubricants")).astype(int)

# ===================================================================== 2. market holds
held_service = {k_ for k_, v in DEC["decisions"].items() if v["service"].startswith("hold")}
UTI_LIGHT_PNS = set()
psl = pd.read_csv(ISZE / "01_data" / "90_INBOX" / "pricing_system_lines_2026-09-19.csv", dtype=str)
UTI_LIGHT_PNS = set(z10(psl[(psl.market == "UTI") & (psl.aim_l2 == "Lighting")].part_number))
is_light = P.index.isin(UTI_LIGHT_PNS) | (P.catalog_l2.fillna("") == "Lighting")
P["lighting"] = is_light.astype(int)
P["panel"] = ((P.aim_l1_fixed == "Accident & Body") & (P.aim_l2_fixed == "Panels")).astype(int)
L["lighting"] = L.pn.map(P.lighting)
L["panel"] = L.pn.map(P.panel)
L["cis"] = L.db.isin(CIS)
L["hold_reason"] = np.select(
    [L.db.isin(held_service) & (L.seg == "service"),
     (L.db == "UMI") & (L.seg == "body"),
     (L.db == "UMI") & (L.lighting == 1),
     (L.db == "UTI") & L.pn.isin(UTI_LIGHT_PNS)],
    ["service hold (market exercise)", "UMI body/collision hold", "UMI lighting hold", "UTI lighting hold"], default="")
L["hold_panel"] = (L.db == "UTI") & (L.panel == 1) & (L.hold_reason == "")
L["step_prop"] = L.net_sales_value * L.pn.map(P.prop)
ex_hold = (L.db.isin(held_service) & (L.seg_ex == "service")) | ((L.db == "UMI") & (L.seg_ex == "body"))     | ((L.db == "UTI") & L.pn.isin(UTI_LIGHT_PNS))
S["holds_exercise_rule_step"] = round(float(L[ex_hold].step_prop.sum()), 2)
hs = L[L.hold_reason != ""].groupby("hold_reason").agg(billed=("net_sales_value", "sum"), step=("step_prop", "sum"))
S["holds"] = {"exercise_published_held_step": DEC["held_step"], "exercise_published_held_base": DEC["held_base"],
              "recomputed_here": {k_: {"billed": round(v.billed, 2), "step": round(v.step, 2)} for k_, v in hs.iterrows()},
              "recomputed_total_step": round(float(hs.step.sum()), 2),
              "uti_panels_optional": {"billed": round(float(L[L.hold_panel].net_sales_value.sum()), 2),
                                      "step": round(float(L[L.hold_panel].step_prop.sum()), 2),
                                      "parts": int(L[L.hold_panel].pn.nunique())},
              "uti_lighting_rule": "UTI lines on the 87 part numbers the 19 Sep pricing lines file files under Lighting "
                                   "(the exercise's EUR 133,712 selection)",
              "umi_lighting_rule": "UMI lines whose release catalogue L2 is Lighting, not already in UMI body; the "
                                   "exercise named this hold but counted only body in its EUR 388,040"}

# ===================================================================== 3. sales: lines, order type, slow movers
sf = pd.read_parquet(D / "sales_fact.parquet", columns=["billing_date", "sold_to_sap", "part_number", "description",
                                                        "billed_qty", "net_sales_value", "saty"])
sf["db"] = sf.sold_to_sap.astype("Int64").astype(str).map(code_of)
sf["pn"] = z10(sf.part_number)
sf = sf[sf.db.notna() & ~sf.db.isin(["GERMANY_SERVICE", "MIDI"]) & (sf.billed_qty > 0) & (sf.net_sales_value > 0)]
lub = sf.pn.str.startswith("05") & sf.description.fillna("").str.upper().str.contains("RIM|TELLUS|SHELL|HELIX|SPIRAX")
sf = sf[~lub & sf.pn.str.fullmatch(r"\d{10}")]
w12 = sf[(sf.billing_date >= W0) & (sf.billing_date <= W1)]
pnl = w12.groupby("pn").agg(lines=("billed_qty", "size"), months=("billing_date", lambda s: s.dt.to_period("M").nunique()),
                            urgent=("net_sales_value", lambda s: s[w12.loc[s.index, "saty"].isin(["VOR", "RUSH"])].sum()),
                            val=("net_sales_value", "sum"), n_db=("db", "nunique"))
P["lines_l12m"] = pnl.lines.reindex(P.index).fillna(0).astype(int)
P["months_l12m"] = pnl.months.reindex(P.index).fillna(0).astype(int)
P["n_markets_l12m"] = pnl.n_db.reindex(P.index).fillna(0).astype(int)
P["urgent_share"] = (pnl.urgent / pnl.val).reindex(P.index)
pm_lines = w12.groupby(["pn", "db"]).size()
SLOW_LINES = 6        # network-wide: at most 6 order lines in 12 months (one order every two months or less)
P["slow_mover"] = (P.lines_l12m <= SLOW_LINES).astype(int)
S["slow_mover_rule"] = f"at most {SLOW_LINES} order lines network-wide, Jul 2025-Jun 2026 (sales_fact.parquet)"
S["lines_quantiles"] = {str(q): float(P.lines_l12m.quantile(q)) for q in (0.1, 0.25, 0.5, 0.75, 0.9)}

# ===================================================================== 4. angle 1: outside prices (dashboard method)
obs = pd.read_parquet(D / "price_observations.parquet")
obs = obs[obs.price_eur.notna()].copy()
obs["grp"] = obs.price_type.map(ppd.GROUP)
obs = obs[obs.grp.notna() & obs.part_no.notna()].copy()
obs["pn"] = ppd.pn10(obs.part_no)
obs["observed_at"] = obs.observed_at.astype(str).str[:10]
obs["eur"] = np.where((obs.vat == "incl") & obs.country.map(ppd.VAT).notna(),
                      obs.price_eur / (1 + obs.country.map(ppd.VAT).fillna(0)), obs.price_eur)
pl = pd.read_parquet(D / "pricing_pr00_ie40.parquet", columns=["part_number", "sp_eur", "valid_start", "valid_end"])
pl = pl[(pl.valid_start <= TODAY) & (pl.valid_end >= TODAY) & (pl.sp_eur > 0)]
pl = pl.sort_values("valid_start").drop_duplicates("part_number", keep="last").set_index("part_number").sp_eur
obs["ref"] = obs.pn.map(pl) * ppd.REF_MULTIPLE
obs["ratio"] = obs.eur / obs.ref
obs = obs[obs.ratio.notna()]
fresh = (TODAY - pd.Timedelta(days=365)).strftime("%Y-%m-%d")
for grp_ in ["street", "rrp", "trade", "genuine"]:
    o = obs[obs.grp == grp_]
    P[f"idx_{grp_}_all"] = o.groupby("pn").ratio.median().reindex(P.index)
    P[f"idx_{grp_}_12m"] = o[o.observed_at >= fresh].groupby("pn").ratio.median().reindex(P.index)
    P[f"n_obs_{grp_}"] = o.groupby("pn").size().reindex(P.index).fillna(0).astype(int)
P["list_eur_now"] = pl.reindex(P.index)
P["ref_dealer_price_eur"] = P.list_eur_now * ppd.REF_MULTIPLE
# aftermarket brand index used for the score: street (shop) price, last 12 months first, else any date
P["am_idx"] = P.idx_street_12m.fillna(P.idx_street_all)
P["am_idx_basis"] = np.where(P.idx_street_12m.notna(), "street, last 12 months",
                             np.where(P.idx_street_all.notna(), "street, older than 12 months", ""))
P["gg_idx"] = P.idx_genuine_12m.fillna(P.idx_genuine_all)

# ===================================================================== 5. angle 2: captive vs competitive
gr = pd.read_csv(ISZE / "04_tools" / "aftermarket_intelligence" / "state" / "crossref_graded.csv", dtype=str)
use = gr[gr.tier.isin(["confirmed", "likely"])]
use_n = use.groupby(ppd.pn10(use.part_no)).competitor_pn.nunique()
P["edges_usable"] = use_n.reindex(P.index).fillna(0).astype(int)
P["edge_spareto_upgraded"] = P.index.isin(set(ppd.pn10(use[use.tier_eucon_only.fillna("") != use.tier].part_no))).astype(int)
P["am_price_observed"] = P.index.isin(set(obs[obs.grp.isin(["street", "rrp", "trade"])].pn)).astype(int)
P["bvp_alternative"] = P.index.isin(bvp_alt).astype(int)
zone_pn = L[L.zone_basis == "Measured"].groupby("pn").zone.agg(lambda s: ",".join(sorted(set(s))))
P["zone_measured"] = zone_pn.reindex(P.index).fillna("")
P["family_competitive"] = (P.catalog_l1 == "Competitive parts").astype(int)
P["competitive_evidence"] = ((P.edges_usable > 0) | (P.am_price_observed == 1)).astype(int)   # the brief's definition
P["captive"] = 1 - P.competitive_evidence
P["captive_strict"] = ((P.captive == 1) & (P.bvp_alternative == 0) & (P.family_competitive == 0)
                       & ~P.zone_measured.str.contains("Lost|Contested")).astype(int)

# ===================================================================== 6. angle 5: dealer response per part
lists, superseded, origin = load_lists()
MK = {"ITUK": (load_ituk_monthly(), ("2025-04", "2025-08"), ("2026-04", "2026-08")),
      "IUK": (["dealer_sellout_long_IUK_CY2025.csv", "dealer_sellout_long_IUK_CY2026YTD.csv"], ("2025-04", "2025-07"), ("2026-04", "2026-07")),
      "IRELAND": (["dealer_sellout_long_IRELAND_CY2025.csv", "dealer_sellout_long_IRELAND_CY2026YTD.csv"], ("2025-04", "2025-07"), ("2026-04", "2026-07")),
      "PORTUGAL": (["dealer_sellout_long_PORTUGAL_CY2025.csv", "dealer_sellout_long_PORTUGAL_CY2026YTD.csv"], ("2025-04", "2025-08"), ("2026-04", "2026-08"))}
frames = []
for name, (src, pre, post) in MK.items():
    if isinstance(src, list):
        xs = []
        for f in src:
            x = pd.read_csv(D / f, dtype={"part_number": str, "period": str})
            xs.append(x[x.period_grain == "month"][["part_number", "period", "qty"]])
        x = pd.concat(xs)
        x["pn"], x["ym"] = z10(x.part_number), pd.PeriodIndex(x.period, freq="M")
        mm = x.groupby(["pn", "ym"], as_index=False).qty.sum()
    else:
        mm = src
    q0, q1 = window_qty(mm, *pre), window_qty(mm, *post)
    pns = q0.index.union(q1.index)
    d = pd.DataFrame({"q_pre": q0.reindex(pns).fillna(0), "q_post": q1.reindex(pns).fillna(0)})
    d["dlp"] = np.log(lists[2026].reindex(pns) / lists[2025].reindex(pns))
    d["market"] = name
    frames.append(d.reset_index(names="pn"))
A = pd.concat(frames, ignore_index=True)
A["grp"] = rel.aim_l2_fixed.reindex(A.pn).fillna("unclassified").to_numpy()   # release family, not pr00
A = A[(A.q_pre >= 3) & A.dlp.notna() & (A.dlp.abs() < 0.5)].copy()
A["chg"] = np.log((A.q_post + 0.5) / (A.q_pre + 0.5))
A["chg_rel"] = A.chg - A.groupby(["market", "grp"]).chg.transform("median")
# flag: got a rise of 3%+ in April 2026, at least 10 dealer units before, and fell 30%+ more than its own family in that market
A["fell"] = (A.dlp >= np.log(1.03)) & (A.q_pre >= 10) & (A.chg_rel <= np.log(0.70))
fell = A[A.fell].groupby("pn").market.agg(lambda s: ",".join(sorted(s)))
P["resp_measured_markets"] = A.groupby("pn").market.agg(lambda s: ",".join(sorted(s))).reindex(P.index).fillna("")
P["resp_fell_after_rise"] = fell.reindex(P.index).fillna("")
# category view: release AIM L1, rise-receiving parts vs the market's own median, per market
A["aim_l1"] = rel.aim_l1_fixed.reindex(A.pn).fillna("Not in release").to_numpy()
cat_resp = (A[A.dlp >= np.log(1.03)].assign(rel=lambda d: d.chg - d.groupby("market").chg.transform("median"))
            .groupby(["market", "aim_l1"]).agg(parts=("pn", "size"), units_before=("q_pre", "sum"),
                                               median_rel_change=("rel", "median"), fell_parts=("fell", "sum")))
cat_resp = cat_resp[cat_resp.parts >= 20].reset_index()
cat_resp["median_rel_change_pct"] = np.exp(cat_resp.median_rel_change) - 1
if not VARIANT_IUK:
    cat_resp.sort_values("median_rel_change").to_csv(HERE / "dealer_response_by_category_2026-10-02.csv", index=False)

# ===================================================================== 7. angle 6: LCV vs truck
vfb = pd.read_csv(D / "vehicle_family_bands.csv", dtype=str)
vfb["pn"] = z10(vfb.pn)
vmap = {"light_vehicle": "LCV (D-Max)", "n_series_truck": "Truck", "f_series": "Truck"}
fam1 = vfb[vfb.resolution == "single_family"].set_index("pn").family.map(lambda f: vmap.get(f, "Truck" if "series" in str(f) else None))
fam_shared = set(vfb[vfb.resolution != "single_family"].pn)
apl = pd.read_csv(D / "apl_pn_list_long_20260812.csv", dtype=str, usecols=["part_number", "source_pack"])
apl["pn"] = z10(apl.part_number)
apk = apl.groupby("pn").source_pack.agg(set)
apl_line = apk.map(lambda s: "LCV (D-Max)" if s == {"RG21_2.2L"} else ("Truck" if "RG21_2.2L" not in s else "Both"))
# buyer pattern: share of 2023-Aug 2026 billing from LCV-only vs truck-only distributors (distributor_dimension scope)
sf["scope"] = sf.db.map(scope_of)
bp_ = sf[sf.scope.isin(["LCV", "CV"])].pivot_table(index="pn", columns="scope", values="net_sales_value", aggfunc="sum", fill_value=0)
lcv_sh = bp_["LCV"] / (bp_["LCV"] + bp_["CV"])
buyer_line = pd.Series(np.select([lcv_sh >= 0.95, lcv_sh <= 0.05], ["LCV (D-Max)", "Truck"], default="Both"), index=lcv_sh.index)
P["line_band_file"] = fam1.reindex(P.index)
P.loc[P.index.isin(fam_shared), "line_band_file"] = "Both"
P["line_apl"] = apl_line.reindex(P.index)
P["line_buyers"] = buyer_line.reindex(P.index)
P["lcv_buyer_share"] = lcv_sh.reindex(P.index)
P["vehicle_line"] = P.line_band_file.fillna(P.line_apl.replace({"Both": np.nan})).fillna(P.line_buyers).fillna("Unknown")
P["vehicle_line_source"] = np.where(P.line_band_file.notna(), "vehicle_family_bands.csv",
                                    np.where(P.line_apl.isin(["LCV (D-Max)", "Truck"]), "APL part lists 2026-08-12",
                                             np.where(P.line_buyers.notna(), "who buys it (LCV-only vs truck-only distributors)", "")))
agree = P[P.line_band_file.isin(["LCV (D-Max)", "Truck"]) & P.line_buyers.isin(["LCV (D-Max)", "Truck"])]
agree2 = P[P.line_apl.isin(["LCV (D-Max)", "Truck"]) & P.line_buyers.isin(["LCV (D-Max)", "Truck"])]
S["vehicle_line_checks"] = {
    "band_file_vs_buyers": {"parts": int(len(agree)), "agree": int((agree.line_band_file == agree.line_buyers).sum())},
    "apl_vs_buyers": {"parts": int(len(agree2)), "agree": int((agree2.line_apl == agree2.line_buyers).sum())}}

# ===================================================================== 8. angles 7 + 8
bb = pd.read_csv(D / "book_b_provisional_weights.csv", dtype=str)
bb["pn"] = z10(bb.pn)
p700 = set(bb[bb.book_b_bucket == "p700_new_only_seed"].pn)
P["p700_new_only"] = P.index.isin(p700).astype(int)
sf_all = sf.groupby("pn").agg(eur=("net_sales_value", "sum"), first=("billing_date", "min"), last=("billing_date", "max"))
p7 = sf_all.reindex(sorted(p700))
S["p700_new_only"] = {"parts": len(p700), "with_any_billing_2023_aug2026": int(p7.eur.notna().sum()),
                      "billed_eur_2023_aug2026": round(float(p7.eur.sum()), 2),
                      "with_billing_l12m": int(len(set(w12.pn) & p700)),
                      "billed_eur_l12m": round(float(w12[w12.pn.isin(p700)].net_sales_value.sum()), 2),
                      "in_proposal_base": int(P.p700_new_only.sum()),
                      "proposal_base_billed": round(float(P.billed[P.p700_new_only == 1].sum()), 2)}
if not VARIANT_IUK:
    p7.assign(desc=bb.set_index("pn").description.reindex(p7.index)).reset_index(names="pn").to_csv(
        HERE / "p700_new_only_billing_2026-10-02.csv", index=False)
umi_service = L[(L.db == "UMI") & (L.seg == "service")].groupby("pn").net_sales_value.sum()
P["umi_service_billed"] = umi_service.reindex(P.index).fillna(0)
P["umi_leasing_flag"] = np.where(P.umi_service_billed > 0, "depends on UMI leasing share (unknown)", "")

# ===================================================================== 9. room score (angles 1-5)
P["s_captive"] = 2 * P.captive_strict
P["s_aftermarket"] = np.select([P.am_idx >= 1.0, P.am_idx < 0.8], [2, -2], default=0)
P["s_genuine_grey"] = np.select([P.gg_idx >= 1.0, P.gg_idx < 0.8], [1, -1], default=0)
P["s_slow"] = P.slow_mover
P["s_urgent"] = (P.urgent_share >= 0.5).astype(int)
P["s_response"] = -(P.resp_fell_after_rise != "").astype(int)
P["room_score"] = (P.s_captive + P.s_aftermarket + P.s_genuine_grey + P.s_slow + P.s_urgent + P.s_response).clip(lower=0)
P.loc[(P.h_lost > 0) | (P.padkit == 1) | (P.lubricant == 1), "room_score"] = 0

# ===================================================================== 10. scenarios
# Free lines = not held, not CIS (CIS keeps the proposal move: untouched). One list move per part on its free lines.
TGT = TARGET * TOT_BASE


def run(name, panels_held, ceiling, weight):
    hold = (L.hold_reason != "") | (L.hold_panel if panels_held else False)
    free = ~hold & ~L.cis
    Wf = L[free].groupby("pn").net_sales_value.sum().reindex(P.index).fillna(0)
    cis_step = float(L[L.cis].step_prop.sum())
    need = TGT - cis_step
    base = P.prop.where(P.padkit == 0, 0.0)
    cap = (P.c.clip(lower=0) + 0.05) if ceiling == "factory+5pts" else pd.Series(0.12, index=P.index)
    cap = cap.where((P.padkit == 0) & (P.lubricant == 0), 0.0)
    v = weight(base).fillna(0).clip(lower=0)
    v[(P.padkit == 1) | (P.lubricant == 1)] = 0
    f = lambda t: float((Wf * np.minimum(cap, base + t * v)).sum())
    lo, hi = -1.0, 50.0
    feasible = f(hi) >= need - 0.01
    if feasible:
        for _ in range(200):
            mid = (lo + hi) / 2
            lo, hi = (mid, hi) if f(mid) < need else (lo, mid)
        t = hi
    else:
        t = hi
    mv = np.minimum(cap, base + t * v)
    line_mv = np.where(free, L.pn.map(mv), np.where(L.cis, L.pn.map(P.prop), 0.0))
    return t, mv, pd.Series(line_mv, index=L.index), feasible, f(t) + cis_step, cap


eligible_B = (((P.seg == "repair") | (P.seg == "body")) & (P.captive_strict == 1)).astype(float)
WEIGHTS = {"A flat rest of book": lambda b: b,
           "B captive repair + non-competitive body": lambda b: eligible_B,
           "C room-weighted (angles 1-5)": lambda b: P.room_score.astype(float)}


def run_b_exempt(exempt):
    """Option B (factory+5 ceiling, no panels hold) with the free lines of the `exempt` markets kept at their
    proposal move (a distributor condition, like the holds); the B uplift is re-solved on the other free lines."""
    hold = L.hold_reason != ""
    free = ~hold & ~L.cis
    fixed = free & L.db.isin(exempt)
    flex = free & ~L.db.isin(exempt)
    Wflex = L[flex].groupby("pn").net_sales_value.sum().reindex(P.index).fillna(0)
    Wfix = L[fixed].groupby("pn").net_sales_value.sum().reindex(P.index).fillna(0)
    cis_step = float(L[L.cis].step_prop.sum())
    base = P.prop.where(P.padkit == 0, 0.0)
    cap = (P.c.clip(lower=0) + 0.05).where((P.padkit == 0) & (P.lubricant == 0), 0.0)
    v = eligible_B.copy()
    v[(P.padkit == 1) | (P.lubricant == 1)] = 0
    mv_fix = np.minimum(cap, base)
    need = TGT - cis_step - float((Wfix * mv_fix).sum())
    f = lambda t: float((Wflex * np.minimum(cap, base + t * v)).sum())
    lo, hi = -1.0, 50.0
    for _ in range(200):
        mid = (lo + hi) / 2
        lo, hi = (mid, hi) if f(mid) < need else (lo, mid)
    t = hi
    mv = np.minimum(cap, base + t * v)
    line_mv = np.where(flex, L.pn.map(mv), np.where(fixed, L.pn.map(mv_fix), np.where(L.cis, L.pn.map(P.prop), 0.0)))
    line_base = np.where(free, L.pn.map(base), 0.0)
    line_extra = (L.net_sales_value * (line_mv - line_base)).clip(lower=0).where(free, 0.0)   # free lines only (CIS keeps its proposal move)
    extra_p = (Wflex * (mv - base)).clip(lower=0)
    at_cap = (mv >= cap - 1e-9) & (Wflex > 0) & (cap > 0)
    step_line = L.net_sales_value * line_mv
    by_mk = pd.DataFrame({"db": L.db, "b": L.net_sales_value, "s": step_line, "p": L.step_prop, "x": line_extra,
                          "seg": L.seg}).groupby("db")
    mk_tab = pd.DataFrame({"billed_eur": by_mk.b.sum(), "proposal_avg_move": by_mk.p.sum() / by_mk.b.sum(),
                           "avg_move": by_mk.s.sum() / by_mk.b.sum(), "uplift_eur": by_mk.x.sum()})
    seg_x = pd.Series(line_extra.to_numpy(), index=L.index).groupby(L.seg).sum()
    iuk_rb = L.db.eq("IUK") & L.seg.isin(["repair", "body"])
    return {"exempt_markets": list(exempt), "solver_t_pts": round(t, 6),
            "total_step_eur": round(f(t) + float((Wfix * mv_fix).sum()) + cis_step, 0),
            "total_pct": round((f(t) + float((Wfix * mv_fix).sum()) + cis_step) / TOT_BASE, 5),
            "uplift_above_proposal_eur": round(float(line_extra.sum()), 0),
            "uplift_on_iuk_repair_body_eur": round(float(line_extra[iuk_rb].sum()), 0),
            **{f"uplift_{s_}_eur": round(float(seg_x.get(s_, 0)), 0) for s_ in ("service", "repair", "body")},
            "eligible_parts_with_flex_billing": int(((v > 0) & (Wflex > 0)).sum()),
            "parts_at_ceiling": int(at_cap.sum()), "billed_at_ceiling_eur": round(float(Wflex[at_cap].sum()), 0),
            "median_move_flex_parts": round(float(mv[Wflex > 0].median()), 4),
            "uplift_on_captive_strict_pct": round(float(extra_p[P.captive_strict == 1].sum() / extra_p.sum()), 4)}, mk_tab


if VARIANT_IUK:
    b_ref, mk_ref = run_b_exempt([])
    pub = pd.read_csv(OUT_SCN)
    pub = pub[(pub.scenario == "B captive repair + non-competitive body") & (~pub.uti_panels_held)
              & (pub.ceiling == "factory+5pts")].iloc[0]
    # the variant code must reproduce the published option B before its IUK-exempt result is used
    assert abs(b_ref["solver_t_pts"] - pub.solver_t) < 1e-5, (b_ref["solver_t_pts"], pub.solver_t)
    assert abs(b_ref["uplift_above_proposal_eur"] - pub.uplift_above_proposal_eur) < 2, b_ref
    assert b_ref["parts_at_ceiling"] == pub.parts_at_ceiling, b_ref
    b_iuk, mk_iuk = run_b_exempt(["IUK"])
    tab = mk_ref.rename(columns={"avg_move": "B_avg_move", "uplift_eur": "B_uplift_eur"}).join(
        mk_iuk[["avg_move", "uplift_eur"]].rename(columns={"avg_move": "B_iuk_exempt_avg_move",
                                                           "uplift_eur": "B_iuk_exempt_uplift_eur"}))
    tab.sort_values("billed_eur", ascending=False).round(5).to_csv(OUT_VAR_CSV, index_label="market")
    OUT_VAR_JSON.write_text(json.dumps({
        "what": "Option B (captive repair + body, factory move + 5 pts ceiling, no UTI panels hold) as published, "
                "and the same with IUK free lines kept at their proposal move; SUGGESTED, NOT DECIDED",
        "check": "B reproduced from the published scenarios CSV (solver t, uplift, parts at ceiling) before the variant ran",
        "B_as_published": b_ref, "B_iuk_exempt": b_iuk,
        "inputs_note": "same inputs as the default run of this script; default outputs not rewritten"},
        indent=1, default=float), encoding="utf-8")
    print(json.dumps({"B": b_ref, "B_iuk_exempt": b_iuk}, indent=1, default=float))
    print(tab.sort_values("billed_eur", ascending=False).round(4).to_string())
    sys.exit(0)

rows, segrows = [], []
L["main_mv_prop"] = np.where(L.hold_reason != "", 0.0, L.pn.map(P.prop))
for panels in (False, True):
    for ceil in ("factory+5pts", "12% max"):
        for sname, wf in WEIGHTS.items():
            t, mv, lmv, feas, achieved, cap = run(sname, panels, ceil, wf)
            col = f"mv_{sname[0]}_{'pan' if panels else 'nopan'}_{'f5' if ceil == 'factory+5pts' else 'c12'}"
            P[col] = mv.round(6)
            L[col] = lmv
            hold = (L.hold_reason != "") | (L.hold_panel if panels else False)
            free = ~hold & ~L.cis
            step_line = L.net_sales_value * lmv
            Wf = L[free].groupby("pn").net_sales_value.sum().reindex(P.index).fillna(0)
            at_cap = (mv >= cap - 1e-9) & (Wf > 0) & (cap > 0)
            extra = (Wf * (mv - P.prop.where(P.padkit == 0, 0))).clip(lower=0)     # gross uplift above the proposal
            cut = (Wf * (P.prop.where(P.padkit == 0, 0) - mv)).clip(lower=0)      # ceiling cuts below the proposal
            held_step = float(L[hold].step_prop.sum())
            cap_move = P.prop.where(P.padkit == 0, 0) > cap + 1e-9
            rows.append({
                "scenario": sname, "uti_panels_held": panels, "ceiling": ceil, "feasible": feas,
                "total_step_eur": round(achieved, 0), "total_pct": round(achieved / TOT_BASE, 5),
                "held_step_given_up_eur": round(held_step, 0),
                "proposal_moves_cut_by_ceiling_parts": int((cap_move & (Wf > 0)).sum()),
                "proposal_moves_cut_by_ceiling_eur": round(float((Wf * (P.prop - cap).clip(lower=0) * cap_move).sum()), 0),
                "free_base_eur": round(float(L[free].net_sales_value.sum()), 0),
                "avg_move_on_free_lines": round(float(step_line[free].sum() / L[free].net_sales_value.sum()), 5),
                "uplift_above_proposal_eur": round(float(extra.sum()), 0),
                "cut_below_proposal_by_ceiling_eur": round(float(cut.sum()), 0),
                "uplift_on_captive_strict_pct": round(float(extra[P.captive_strict == 1].sum() / extra.sum()), 4),
                "uplift_on_captive_brief_pct": round(float(extra[P.captive == 1].sum() / extra.sum()), 4),
                **{f"uplift_{s_}_eur": round(float(extra[P.seg == s_].sum()), 0) for s_ in ("service", "repair", "body")},
                **{f"uplift_{vl}_eur": round(float(extra[P.vehicle_line == vl].sum()), 0)
                   for vl in ("LCV (D-Max)", "Truck", "Both", "Unknown")},
                "weighted_base_eur": round(float(Wf[wf(P.prop).fillna(0) > 0].sum()), 0),
                "weighted_parts": int(((wf(P.prop).fillna(0) > 0) & (Wf > 0)).sum()),
                "step_on_captive_strict_pct": round(float(step_line[L.pn.map(P.captive_strict) == 1].sum() / step_line.sum()), 4),
                "parts_at_ceiling": int(at_cap.sum()), "billed_at_ceiling_eur": round(float(Wf[at_cap].sum()), 0),
                "parts_moved_above_proposal": int(((mv > P.prop + 1e-9) & (Wf > 0)).sum()),
                "max_move": round(float(mv[Wf > 0].max()), 4), "median_move_free_parts": round(float(mv[Wf > 0].median()), 4),
                "solver_t": round(t, 6),
            })
            for dim, key in (("segment", L.seg), ("market", L.db), ("vehicle_line", L.pn.map(P.vehicle_line))):
                gq = pd.DataFrame({"k": key, "b": L.net_sales_value, "s": step_line, "p": L.step_prop}).groupby("k")
                for kk, gg in gq:
                    segrows.append({"scenario": sname, "uti_panels_held": panels, "ceiling": ceil, "dimension": dim,
                                    "group": kk, "billed_eur": round(gg.b.sum(), 0), "step_eur": round(gg.s.sum(), 0),
                                    "avg_move": round(gg.s.sum() / gg.b.sum(), 5) if gg.b.sum() else None,
                                    "proposal_step_eur": round(gg.p.sum(), 0)})
SCN = pd.DataFrame(rows)
SCN.to_csv(OUT_SCN, index=False)
pd.DataFrame(segrows).to_csv(OUT_SEG, index=False)

# ===================================================================== 11. lever 4: order terms (separate from the price list)
lst25 = pd.read_parquet(D / "pricing_pr00_ie40_2025.parquet")
lst25["pn"] = z10(lst25.Material.astype("Int64"))
lst25 = lst25[lst25.Price_EUR > 0].groupby("pn").Price_EUR.max()
y25 = sf[sf.billing_date.dt.year == 2025].copy()
y25["lv"] = y25.pn.map(lst25) * y25.billed_qty
y25 = y25[y25.lv > 0]
lev = y25[y25.saty.isin(["SOR", "RUSH", "VOR"])].pivot_table(index="db", columns="saty", values=["net_sales_value", "lv"],
                                                             aggfunc="sum", fill_value=0)
LV = pd.DataFrame(index=lev.index)
for s_ in ["SOR", "RUSH", "VOR"]:
    LV[f"{s_}_billed"] = lev[("net_sales_value", s_)] if ("net_sales_value", s_) in lev else 0
    LV[f"{s_}_list_value"] = lev[("lv", s_)] if ("lv", s_) in lev else 0
    LV[f"{s_}_pays_pct_list"] = (LV[f"{s_}_billed"] / LV[f"{s_}_list_value"]).where(LV[f"{s_}_list_value"] > 0)
LV["cis_untouched"] = LV.index.isin(CIS)
LV["service_held_in_exercise"] = LV.index.isin(held_service)
LV["a_stock_narrow_1pt_eur"] = 0.01 * LV.SOR_list_value
gap = (1 - LV.SOR_pays_pct_list).clip(lower=0).fillna(0)
LV["a_stock_halve_gap_to_list_eur"] = 0.5 * gap * LV.SOR_list_value
LV["b_urgent_surcharge_plus1pt_eur"] = 0.01 * (LV.RUSH_list_value + LV.VOR_list_value)
LV["b_urgent_surcharge_plus2pt_eur"] = 0.02 * (LV.RUSH_list_value + LV.VOR_list_value)
LV.loc[LV.cis_untouched, [c for c in LV.columns if c.startswith(("a_", "b_"))]] = 0
LV.sort_values("SOR_billed", ascending=False).round(4).to_csv(OUT_LEV)
nc = LV[~LV.cis_untouched]
S["lever4_cy2025"] = {
    "basis": "CY2025 sales_fact lines x 2025 PR00 list (market_facts.py method); CIS left at 0 (untouched)",
    "stock_narrow_1pt_eur": round(float(nc.a_stock_narrow_1pt_eur.sum()), 0),
    "stock_narrow_1pt_eur_excl_service_hold_markets": round(float(nc[~nc.service_held_in_exercise].a_stock_narrow_1pt_eur.sum()), 0),
    "stock_halve_gap_eur": round(float(nc.a_stock_halve_gap_to_list_eur.sum()), 0),
    "urgent_plus1pt_eur": round(float(nc.b_urgent_surcharge_plus1pt_eur.sum()), 0),
    "urgent_plus2pt_eur": round(float(nc.b_urgent_surcharge_plus2pt_eur.sum()), 0),
    "sor_list_value": round(float(nc.SOR_list_value.sum()), 0),
    "urgent_list_value": round(float((nc.RUSH_list_value + nc.VOR_list_value).sum()), 0)}

# ===================================================================== 12. sufficiency (step 0)
Wp = P.billed
tot = Wp.sum()


def cov(mask, note):
    return {"parts": int(mask.sum()), "parts_pct": round(float(mask.mean()), 4),
            "billed_eur": round(float(Wp[mask].sum()), 0), "billed_pct": round(float(Wp[mask].sum() / tot), 4), "note": note}


S["sufficiency"] = {
    "base": {"parts": int(len(P)), "billed_eur": round(float(tot), 2)},
    "1_outside_prices_aftermarket_street_any_date": cov(P.idx_street_all.notna(), "aftermarket shop price on file"),
    "1_outside_prices_aftermarket_street_12m": cov(P.idx_street_12m.notna(), "dated in the last 12 months"),
    "1_outside_prices_aftermarket_any_group": cov(P[["idx_street_all", "idx_rrp_all", "idx_trade_all"]].notna().any(axis=1), "street, RRP or trade"),
    "1_outside_prices_genuine_grey": cov(P.idx_genuine_all.notna(), "genuine Isuzu sold outside our network"),
    "1_rival_above_ref_dealer_price": cov(P.am_idx >= 1.0, "aftermarket street price at or above our reference dealer price"),
    "2_competitor_number_confirmed_likely": cov(P.edges_usable > 0, "crossref_graded.csv tier confirmed/likely"),
    "2_competitive_evidence_brief_definition": cov(P.competitive_evidence == 1, "edge or aftermarket price"),
    "2_family_competitive_release": cov(P.family_competitive == 1, "release catalogue L1 = Competitive parts"),
    "2_release_found": cov(P.catalog_l1.notna(), "part number found in the approved release"),
    "2_captive_strict": cov(P.captive_strict == 1, "no edge, no aftermarket price, no BVP alternative, not a competitive family, not measured lost/contested"),
    "3_order_lines_found": cov(P.lines_l12m > 0, "order lines in sales_fact, same window"),
    "3_slow_movers": cov(P.slow_mover == 1, S["slow_mover_rule"]),
    "4_order_type_found": cov(P.urgent_share.notna(), "order type on the sales lines"),
    "5_dealer_response_measured": cov(P.resp_measured_markets != "", "part in the April 2026 dealer-response frame (UK trucks, UK D-Max, Ireland, Portugal; 3+ units before)"),
    "5_fell_after_rise": cov(P.resp_fell_after_rise != "", "rise of 3%+, 10+ units before, fell 30%+ more than its own family"),
    "6_vehicle_line_any": cov(P.vehicle_line != "Unknown", "any of the three routes"),
    "6_vehicle_line_band_file": cov(P.line_band_file.notna(), "vehicle_family_bands.csv"),
    "6_vehicle_line_apl": cov(P.line_apl.notna(), "APL part lists"),
    "7_p700_new_only_in_base": cov(P.p700_new_only == 1, "Book B bucket p700_new_only_seed"),
    "8_umi_service": cov(P.umi_service_billed > 0, "parts with UMI service billing"),
}

S["vehicle_line_split"] = {k_: {"parts": int(v.size), "billed": round(float(v.sum()), 0)}
                           for k_, v in P.groupby("vehicle_line").billed}
S["vehicle_line_by_source"] = {k_: {"parts": int(v.size), "billed": round(float(v.sum()), 0)}
                               for k_, v in P.groupby("vehicle_line_source").billed}


def idx_dist(col):
    x = P[[col, "billed"]].dropna()
    return {"parts": int(len(x)), "median": round(float(x[col].median()), 3),
            "billed_weighted_median": round(float(x.sort_values(col).assign(cw=lambda d: d.billed.cumsum() / d.billed.sum())
                                                  .query("cw >= 0.5")[col].iloc[0]), 3),
            "parts_at_or_above_1": int((x[col] >= 1).sum()), "billed_at_or_above_1": round(float(x.billed[x[col] >= 1].sum()), 0),
            "parts_below_0_8": int((x[col] < 0.8).sum()), "billed_below_0_8": round(float(x.billed[x[col] < 0.8].sum()), 0)}


S["index_distribution"] = {"aftermarket_street": idx_dist("am_idx"), "genuine_grey": idx_dist("gg_idx")}
gsrc = obs[obs.grp == "genuine"].groupby("loader").pn.nunique().to_dict()
S["genuine_grey_sources_parts"] = {k_: int(v) for k_, v in gsrc.items()}
S["p700_new_only"]["with_billing_jul_aug_2026"] = int(sf[(sf.billing_date > W1) & sf.pn.isin(p700)].pn.nunique())
S["p700_new_only"]["billed_eur_jul_aug_2026"] = round(float(sf[(sf.billing_date > W1) & sf.pn.isin(p700)].net_sales_value.sum()), 2)
S["p700_new_only"]["by_year"] = {str(int(y)): round(float(v), 0) for y, v in
                                 sf[sf.pn.isin(p700)].groupby(sf.billing_date.dt.year).net_sales_value.sum().items()}

# ===================================================================== 13. write per part + per part x market
out_cols = ["desc", "seg", "seg_ex", "catalog_l1", "catalog_l2", "aim_l1_fixed", "aim_l2_fixed", "aim_l3_fixed", "vehicle_line",
            "vehicle_line_source", "lcv_buyer_share", "billed", "qty", "lines_l12m", "months_l12m", "n_markets_l12m",
            "c", "prop", "padkit", "lubricant", "lighting", "panel", "h_lost", "zone_measured",
            "list_eur_now", "ref_dealer_price_eur", "am_idx", "am_idx_basis", "idx_street_12m", "idx_street_all",
            "idx_rrp_all", "idx_trade_all", "gg_idx", "n_obs_street", "n_obs_rrp", "n_obs_trade", "n_obs_genuine",
            "edges_usable", "edge_spareto_upgraded", "am_price_observed", "bvp_alternative", "family_competitive",
            "competitive_evidence", "captive", "captive_strict", "slow_mover", "urgent_share",
            "resp_measured_markets", "resp_fell_after_rise", "p700_new_only", "umi_service_billed", "umi_leasing_flag",
            "s_captive", "s_aftermarket", "s_genuine_grey", "s_slow", "s_urgent", "s_response", "room_score"]
mk = L.pivot_table(index="pn", columns="db", values="net_sales_value", aggfunc="sum", fill_value=0)
P["main_market"] = mk.idxmax(axis=1).reindex(P.index)
P["markets"] = mk.gt(0).apply(lambda r: ",".join(r.index[r]), axis=1).reindex(P.index)
held_b = L[L.hold_reason != ""].groupby("pn").net_sales_value.sum().reindex(P.index).fillna(0)
P["held_share"] = (held_b / P.billed).round(4)
P["cis_share"] = (L[L.cis].groupby("pn").net_sales_value.sum().reindex(P.index).fillna(0) / P.billed).round(4)
mv_cols = [c for c in P.columns if c.startswith("mv_")]
OUTP = P[["main_market", "markets", "held_share", "cis_share"] + out_cols + mv_cols].rename(
    columns={"billed": "billed_eur_l12m", "c": "factory_move", "prop": "proposal_move", "seg": "segment", "seg_ex": "segment_exercise_rule",
             "am_idx": "aftermarket_index", "gg_idx": "genuine_grey_index"})
OUTP.sort_values("billed_eur_l12m", ascending=False).to_csv(OUT_PART, index_label="pn", float_format="%.6g")
PM = L.groupby(["pn", "db"]).agg(billed_eur=("net_sales_value", "sum"), qty=("billed_qty", "sum"),
                                 hold_reason=("hold_reason", "first"), uti_panel=("hold_panel", "max"),
                                 **{c: (c, "first") for c in mv_cols}).reset_index()
PM["order_lines_l12m"] = [int(pm_lines.get((a, b), 0)) for a, b in zip(PM.pn, PM.db)]
PM["slow_in_market"] = (PM.order_lines_l12m <= 2).astype(int)
PM["cis"] = PM.db.isin(CIS)
PM.to_csv(OUT_PM, index=False, float_format="%.6g")

import hashlib, datetime as _dt
FP = {}
for f in [D / "price_observations.parquet", ISZE / "04_tools/aftermarket_intelligence/state/crossref_graded.csv",
          D / "pr00_classification.csv", D / "parts_catalog_dimension.parquet", rel_path, D / "sales_fact.parquet",
          D / "price_bp_weighted_compare_pn.csv", D / "pricing_pr00_ie40.parquet", PROP / "market_exercise_decisions_2026-09-30.json"]:
    f = Path(f)
    FP[f.name] = {"sha256_12": hashlib.sha256(f.read_bytes()).hexdigest()[:12],
                  "modified": _dt.datetime.fromtimestamp(f.stat().st_mtime).strftime("%Y-%m-%d %H:%M")}
S["input_fingerprints"] = FP
S["usable_edges_rows"] = int(len(use))
S["room_score_rule"] = {"captive_strict": "+2", "aftermarket street index >= 1.0 / < 0.8": "+2 / -2",
                        "genuine grey index >= 1.0 / < 0.8": "+1 / -1", "slow mover": "+1",
                        "urgent (VOR+RUSH) share >= 50%": "+1", "fell after April 2026 rise": "-1",
                        "floor": "0; forced 0 for pad kits, lubricants and parts the proposal already holds (distributor sells under 45% of need)"}
S["room_score_dist"] = {str(int(k_)): {"parts": int(v.size), "billed": round(float(v.sum()), 0)}
                        for k_, v in P.groupby("room_score").billed}
S["scenarios"] = rows
S["inputs"] = {"price_observations": str(D / "price_observations.parquet"), "obs_rows_used": int(len(obs)),
               "crossref_graded_rows": int(len(gr)), "ref_multiple": ppd.REF_MULTIPLE}
OUT_JSON.write_text(json.dumps(S, indent=1, default=float), encoding="utf-8")
print(json.dumps({k_: S[k_] for k_ in ["proposal", "aim_release", "holds", "p700_new_only", "lever4_cy2025",
                                       "vehicle_line_checks", "lines_quantiles", "room_score_dist"]}, indent=1, default=float))
print(json.dumps(S["sufficiency"], indent=1))
print(SCN.to_string())
