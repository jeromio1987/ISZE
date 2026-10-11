"""Numbers for the pricing revision deck (charcoal, 11 Oct 2026). Writes pricing_numbers.json.

Everything that can be recomputed is read from the +5% workbook with the market layer (built 4 Oct 2026, reproduced
here on 11 Oct): Summary and Market layer sheets (cached values) and the sheet 'Layer by part and market'
(45,581 rows, one per part number and market). Parts categories come from the AIM release of 7 Oct 2026 and are
named 'parts category' in the deck. Figures that exist only in the pricing policy paper of 2 Oct 2026 are typed in
PAPER with the section they come from; they are reported, not recomputed.
"""
import json
from pathlib import Path

import openpyxl
import pandas as pd

ROOT = Path(__file__).resolve().parents[5]
BUILD = ROOT / "02_dashboards" / "pricing" / "_build" / "price_5pct_proposal_2026-09-29"
# 11 Oct workbook: filters follow the factory increase (branch cursor/2026-10-11-pricing-grid, commit 73b07b8e)
XLSX = Path("C:/Users/jerom/Desktop/claude/_worktrees/ISZE_u26/02_dashboards/pricing/_build/price_5pct_proposal_2026-09-29/"
            "stage_grid_2026-10-11/Price_Increase_5pct_Proposal_GRID_DRAFT_2026-10-11.xlsx")
SUMJ = BUILD / "price_5pct_proposal_summary_2026-09-29.json"
RESP = BUILD / "dealer_price_response_2026-09-29.json"
REL = ROOT / "01_data" / "00_derived" / "_releases" / "aim_pn_classification_release_2026-10-07.csv"
OUT = Path(__file__).with_name("pricing_numbers.json")

res = {}
sj = json.loads(SUMJ.read_text(encoding="utf-8"))
res["summary"] = {k: sj[k] for k in ["k", "k_factory_only", "step_eur", "parts", "parts_at_zero", "eur_at_zero",
                                     "median_move", "p90_move", "max_move", "recipe_check", "pad_kits", "pad_kits_billed",
                                     "margin_pts_proposal", "revenue_none", "revenue_central", "revenue_stress"]}
res["summary"]["full_factory_eur"] = round(sj["step_eur"] / sj["k_factory_only"], 2)
res["summary"]["scaled_eur"] = round(res["summary"]["full_factory_eur"] * sj["k"], 2)

rj = json.loads(RESP.read_text(encoding="utf-8"))
bm = rj["four_markets_april_2026"]["by_market"]
du = rj["four_markets_april_2026"]["dealer_units"]
res["dealer_response"] = {
    "pooled": rj["four_markets_april_2026"]["pooled"],
    "iuk_beta": bm["IUK (UK D-Max)"]["beta_dlp"], "iuk_se": bm["IUK (UK D-Max)"]["se_dlp"],
    "iuk_ci95": round(1.96 * bm["IUK (UK D-Max)"]["se_dlp"], 2),
    "iuk_units_change": du["IUK (UK D-Max)"]["change"],
    "invoice_check_median_list": rj["invoice_check_ituk"]["April 2026"]["median_list_change"]}

wb = openpyxl.load_workbook(XLSX, read_only=True, data_only=True)

# ---- Market layer sheet: reconciliation and the per-market table
ws = wb["Market layer"]
rows = [list(r) for r in ws.iter_rows(values_only=True)]
rec, mk, hdr, worth = {}, [], None, {}
for r in rows:
    a = r[0]
    if isinstance(a, str):
        if a.startswith("Less: given up by the holds"):
            rec["given_up"] = r[1]
        elif a.startswith("Less: cut by the ceiling"):
            rec["ceiling_cut"] = r[1]
        elif a.startswith("Plus: recovery extra"):
            rec["recovered"] = r[1]
        elif a.startswith("Own increase on all parts and markets"):
            rec["own_total"] = r[1]
        elif a.startswith("Extra points on top of own increase") or a.startswith("Base points behind the grid ("):
            rec["t_off"], rec["t_on"] = r[1], r[2]
            rec["t_off_2oct"], rec["t_on_2oct"] = r[4], r[5]  # published column: the 2 October position, filters held
        elif a.startswith("Recovery extra on repair parts"):
            rec["rec_repair_off"], rec["rec_repair_on"] = r[1], r[2]
        elif a.startswith("Recovery extra on body parts"):
            rec["rec_body_off"], rec["rec_body_on"] = r[1], r[2]
        elif a.startswith("Recovery extra on service parts"):
            rec["rec_service"] = r[1]
        elif a.startswith("Recovery extra on Isuzu UK"):
            rec["rec_iuk_off"], rec["rec_iuk_on"] = r[1], r[2]
        elif a.startswith("Part numbers that"):
            rec["pn_extra_off"], rec["pn_extra_on"] = r[1], r[2]
        elif a.startswith("Billed base, EUR"):
            rec["base"] = r[1]
        elif a.startswith("Filters (") and r[1] and str(r[1]).startswith("Summary"):
            worth["filters_eur"] = r[5]
        elif a.startswith("Intake, exhaust and emission parts") and r[1] and str(r[1]).startswith("Summary"):
            worth["intake_exhaust_emission_eur"] = r[5]
        elif a == "Brake discs and drums" and r[1] == "not a switch":
            worth["discs_drums_eur"] = r[5]
        elif a == "All holds":
            worth["all_if_held_eur"] = r[5]
        if a == "Market" and r[1] == "Code" and r[2] == "Billed EUR":
            hdr = [str(c) for c in r]
            continue
        if hdr and a == "All markets":
            hdr = None
            continue
    if hdr and isinstance(a, str) and a != "Market":
        mk.append(dict(zip(hdr, r)))
res["reconciliation"] = rec
res["market_table"] = [{"market": m["Market"], "code": m["Code"], "billed": m["Billed EUR"],
                        "own": m["Own increase (average)"], "given_up": m["Given up by holds, EUR"],
                        "service": m["of which service parts"], "israel": m["of which Israel body, collision, lighting"],
                        "ceiling_cut": m["Cut by ceiling, EUR"], "recovered": m["Recovered by extra, EUR"],
                        "decided": m["Increase after treatment (average)"]} for m in mk if m.get("Code")]

# ---- Layer by part and market: group averages, market averages in three states, given up by category
ws = wb["Layer by part and market"]
hdr, data = None, []
for r in ws.iter_rows(values_only=True):
    if hdr is None:
        if r and r[0] == "Part number":
            hdr = list(r)
        continue
    data.append(r)
df = pd.DataFrame(data, columns=hdr)
df.columns = ["pn", "market", "mnum", "cat", "billed", "cond", "reason", "own", "inc_now", "pts", "eur_at", "eur_vs_own",
              "margin", "line_type", "row", "hk", "role", "own_cap", "room", "mult", "free_billed", "exempt", "inc_off",
              "inc_on", "paper_hold_text"]
df["pn"] = df.pn.astype(str)
for c in ["billed", "own", "inc_off", "inc_on", "eur_vs_own"]:
    df[c] = pd.to_numeric(df[c], errors="coerce")
w = lambda g, col: float((g.billed * g[col]).sum() / g.billed.sum())  # noqa: E731
res["group_avg"] = {k: {"billed": round(float(g.billed.sum()), 2), "own": w(g, "own"), "decided": w(g, "inc_off"),
                        "exempt": w(g, "inc_on")} for k, g in df.groupby("cat")}
res["market_avg"] = {k: {"billed": round(float(g.billed.sum()), 2), "own": w(g, "own"), "decided": w(g, "inc_off"),
                         "exempt": w(g, "inc_on")} for k, g in df.groupby("market")}
held = df[df.line_type == "hold"].copy()
held["given_up"] = -held.eur_vs_own
rel = pd.read_csv(REL, dtype=str, low_memory=False).drop_duplicates("part_number")
h = held.merge(rel[["part_number", "aim_l1_fixed", "aim_l2_fixed", "aim_l3_fixed"]], left_on="pn", right_on="part_number", how="left")
isfilt = h.aim_l2_fixed.fillna("").str.contains("Filter") | h.aim_l3_fixed.fillna("").str.contains("Filter")
res["held"] = {
    "rows": int(len(held)), "given_up_eur": round(float(held.given_up.sum()), 2),
    # worth of each hold as the workbook states it ('What each hold is worth'): filters are released now, so their
    # euro is what they would give up if held; the other two are still held
    "filters_eur": round(float(worth["filters_eur"]), 2),
    "discs_drums_eur": round(float(worth["discs_drums_eur"]), 2),
    "intake_exhaust_emission_eur": round(float(worth["intake_exhaust_emission_eur"]), 2),
    "all_if_held_eur": round(float(worth["all_if_held_eur"]), 2),
    "filters_still_held_check_eur": round(float(h.given_up[isfilt].sum()), 2)}
kind = h.cond.astype(str)
split = {}
for mkt, g in h.groupby("market"):
    k = g.cond.astype(str)
    split[mkt] = {"service": round(float(g.given_up[k.str.startswith("Service")].sum()), 2),
                  "body_collision": round(float(g.given_up[k.str.startswith("Body")].sum()), 2),
                  "lighting": round(float(g.given_up[k.str.startswith("Lighting")].sum()), 2)}
res["held_by_market"] = split

# ---- matrix market x part group (billed, own increase, increase after the proposed treatment) and what sits in each group
mx = {}
for (mkt, cat), g in df.groupby(["market", "cat"]):
    mx.setdefault(mkt, {})[cat] = {"billed": round(float(g.billed.sum()), 2), "own": w(g, "own"), "decided": w(g, "inc_off")}
res["matrix"] = mx
dd = df.drop_duplicates("pn").merge(rel[["part_number", "aim_l1_fixed", "aim_l2_fixed"]], left_on="pn", right_on="part_number", how="left")
bil = df.groupby("pn").billed.sum()
dd["bil"] = dd.pn.map(bil)
res["group_content"] = {c: [[a, round(float(b), 0)] for a, b in
                            g.groupby("aim_l1_fixed").bil.sum().sort_values(ascending=False).head(8).items()]
                        for c, g in dd.groupby("cat")}
res["group_content_l2"] = {c: [[a, round(float(b), 0)] for a, b in
                               g.groupby("aim_l2_fixed").bil.sum().sort_values(ascending=False).head(8).items()]
                           for c, g in dd.groupby("cat")}

# ---- typed from the pricing policy paper of 2 October 2026 (reported, not recomputed here)
res["paper"] = {
    "iml_imit": {"all": 6.0, "service": 5.5, "repair": 6.6, "body": 7.0, "japan": 6.2, "thailand": 6.3, "previous_sep_2025": 3.2,
                 "billed_service_m": 19.2, "billed_repair_m": 8.8, "billed_body_m": 4.6, "src": "paper section 2"},
    "waterfall_to_5pct_k": {"pad_kits": -109, "categories_lost": -56, "uk_web_shops": 21, "src": "paper section 2"},
    "typical_part": {"median_pct": 6.4, "p90_pct": 7.3, "above_15pct_parts": 99, "src": "paper section 4"},
    "service_share_2025_pct": {"IUK": 17, "ITUK": 51, "UTI": 55, "UMI": 21, "GERMANY": 14, "BELGIUM": 26, "PORTUGAL": 30,
                               "NORWAY": 27, "SWEDEN": 24, "IRELAND": "100*", "CYPRUS": 50, "HUNGARY": 19, "MALTA": 33,
                               "src": "paper section 5; network 28% in 2025"},
    "three_ways_k": {"a_spread": {"service": 137.023, "repair": 167.961, "body": 91.583, "cap": 56},
                     "b_decided": {"service": 0.0, "repair": 252.972, "body": 143.596, "cap": 5},
                     "c_weighted": {"service": 90.683, "repair": 199.856, "body": 106.029, "cap": 8},
                     "src": "paper section 6; decided way checked against the workbook"},
    "typical_extra_part": {"decided_pct": 10.1, "before_pct": 6.3, "dmax_avg_pct": 4.8, "truck_avg_pct": 5.8,
                           "dmax_before_pct": 5.1, "truck_before_pct": 5.2, "src": "paper section 6"},
    "evidence_pct": [["Order lines and order type", 100.0, "sufficient"], ["Vehicle line (D-Max or truck)", 97.7, "sufficient"],
                     ["Dealer response to the April 2026 rise", 73.7, "partial: a flag only"],
                     ["Genuine Isuzu sold outside our network", 50.4, "partial: one main source"],
                     ["Any competitor evidence", 24.5, "too thin to prove no alternative"],
                     ["Aftermarket shop price", 21.0, "partial: top sellers only"],
                     ["Competitor part number, confirmed or likely", 15.4, "thin"]],
    "outside_prices": {"aftermarket_median_index": 0.56, "aftermarket_parts": 266, "aftermarket_weighted_index": 0.44,
                       "genuine_outside_median_index": 1.17, "genuine_outside_parts": 1167, "genuine_outside_main_source": 1093,
                       "src": "paper section 8 (index on a provisional reference dealer price)"},
    "israel": {"total_loss_pct": 60, "constructive_from_pct": "50 to 55", "verified_up_to_t": 3.5,
               "panels_billed_jan_aug_2025": 165232, "panels_billed_jan_aug_2026": 135548, "panels_change_pct": -18.0,
               "backorder_weeks": "4 to 16", "backorder_median_weeks": 13, "panels_increase_kept_eur": 13795,
               "dmax_body_light_given_up_k": 20, "trucks_lighting_given_up_k": 8, "src": "paper sections 9 and 10"},
    "terms_outside_list": {"halve_gap_stock_k": 452, "one_point_stock_discount_k": 213, "urgent_plus2_k": 93, "urgent_plus1_k": 46,
                           "src": "paper section 11, calendar 2025 order lines at the 2025 list"},
    "n_series": {"part_numbers": 826, "ever_billed": 135, "in_base": 14, "in_base_eur": 660, "src": "paper section 12"},
    "leasing_open": {"increase_at_stake_k": 65, "service_billed_m": 1.48, "src": "paper section 14"}}

OUT.write_text(json.dumps(res, indent=1, ensure_ascii=False, default=float), encoding="utf-8")
print(json.dumps(res["reconciliation"], indent=1))
print(json.dumps(res["held"], indent=1))
print(json.dumps(res["held_by_market"], indent=1))
print({k: {kk: round(vv, 4) if isinstance(vv, float) else vv for kk, vv in v.items()} for k, v in res["group_avg"].items()})
print(len(res["market_table"]), "market rows;", res["market_table"][0])
