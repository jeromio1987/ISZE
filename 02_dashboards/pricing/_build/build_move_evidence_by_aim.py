# -*- coding: utf-8 -*-
"""Price move, rival-price evidence and tender demand, per AIM parts category.

Reads (read-only):
  02_dashboards/pricing/_build/price_tool_html_v6_2026-10-15/payload6.json   billed base + base price step per part
  01_data/00_derived/price_observations.parquet                               rival and genuine prices seen
  01_data/00_derived/parts_catalog_dimension.csv                              part -> PMS category
  01_data/14_dashboards/tender_data.json                                      tender demand by PMS category
Writes: 02_dashboards/pricing/_build/move_evidence_by_aim.json
"""
from __future__ import annotations
import json, sys
from pathlib import Path
import pandas as pd

ROOT = Path(__file__).resolve().parents[3]
PAY = ROOT / "02_dashboards/pricing/_build/price_tool_html_v6_2026-10-15/payload6.json"
OBS = ROOT / "01_data/00_derived/price_observations.parquet"
CAT = ROOT / "01_data/00_derived/parts_catalog_dimension.csv"
TEN = ROOT / "01_data/14_dashboards/tender_data.json"
OUT = ROOT / "02_dashboards/pricing/_build/move_evidence_by_aim.json"

RIVAL = {"aftermarket_retail", "aftermarket_trade", "aftermarket_rrp", "online_median",
         "marketplace", "quote", "survey_workshop", "survey_list"}
GENUINE = {"genuine_grey", "dealer"}


def main() -> int:
    D = json.loads(PAY.read_text(encoding="utf-8"))
    parts = pd.DataFrame(D["parts"])
    parts.columns = ["pn", "desc", "l1", "l2", "l3", "step", "bp0", "bp1", "c8", "c9", "c10", "c11", "c12", "pms", "pms_cell", "c15"]
    lines = pd.DataFrame(D["lines"])
    billed = lines.groupby(0)[3].sum()
    parts["billed"] = billed.reindex(parts.index).fillna(0.0)
    base_total = float(parts["billed"].sum())
    parts["l1name"] = parts["l1"].map(lambda i: D["l1"][i])
    parts["pmsname"] = parts["pms"].map(lambda i: D["pms"]["labels"][i] if i >= 0 else None)
    parts["pmskey"] = parts["pms"].map(lambda i: D["pms"]["cats"][i] if i >= 0 else None)

    obs = pd.read_parquet(OBS)
    obs = obs[obs["price"].notna()].copy()
    obs["part_no"] = obs["part_no"].astype(str)
    pnm = obs[obs["match_method"].isin(["exact_oem", "crossref"])]   # same part, not just same family
    rival_pns = set(pnm[pnm["price_type"].isin(RIVAL)]["part_no"])
    genuine_pns = set(pnm[pnm["price_type"].isin(GENUINE)]["part_no"])
    parts["rival"] = parts["pn"].isin(rival_pns)
    parts["genuine_out"] = parts["pn"].isin(genuine_pns)

    def roll(g: pd.DataFrame) -> pd.Series:
        b = g["billed"].sum()
        return pd.Series({
            "billed": b,
            "parts": len(g),
            "step": float((g["billed"] * g["step"]).sum() / b) if b else None,
            "rival_parts": int(g["rival"].sum()),
            "rival_billed": float(g.loc[g["rival"], "billed"].sum()),
            "genuine_out_parts": int(g["genuine_out"].sum()),
        })

    by_l1 = parts.groupby("l1name").apply(roll, include_groups=False).sort_values("billed", ascending=False)
    by_l1["extra"] = by_l1["billed"] * by_l1["step"]
    by_l1["rival_share"] = by_l1["rival_billed"] / by_l1["billed"]
    by_pms = parts[parts["pmskey"].notna()].groupby("pmskey").apply(roll, include_groups=False)
    by_pms["label"] = parts[parts["pmskey"].notna()].groupby("pmskey")["pmsname"].first()

    # tender demand per PMS category, at today's price and at the revised list
    ten = json.loads(TEN.read_text(encoding="utf-8"))
    opp = []
    for o in ten["opportunities"]:
        dem = o.get("pms_demand_by_category")
        if not dem or not o.get("distributor_code"):
            continue
        opp.append(o)
    rows = []
    for o in opp:
        dem = o["pms_demand_by_category"]
        items = [(d.get("pms_category"), d) for d in dem]
        for k, v in items:
            eur = v.get("addressable_eur") if isinstance(v, dict) else v
            if eur is None or k not in by_pms.index:
                continue
            rows.append({"opp": o["opportunity_id"], "title": o["title"][:90], "buyer": o.get("buyer"),
                         "dist": o["distributor_code"], "cat": k, "label": by_pms.loc[k, "label"],
                         "now": float(eur), "step": float(by_pms.loc[k, "step"]),
                         "rival_share": float(by_pms.loc[k, "rival_billed"] / by_pms.loc[k, "billed"])})
    T = pd.DataFrame(rows)
    if len(T):
        T["after"] = T["now"] * (1 + T["step"])

    out = {
        "base_total": base_total,
        "weighted_step": float((parts["billed"] * parts["step"]).sum() / base_total),
        "l1": [{"name": k, **{c: (None if pd.isna(v) else float(v)) for c, v in r.items()}} for k, r in by_l1.iterrows()],
        "pms": [{"key": k, **{c: (v if c == "label" else (None if pd.isna(v) else float(v))) for c, v in r.items()}} for k, r in by_pms.iterrows()],
        "tender_rows": T.to_dict("records") if len(T) else [],
        "tender_total_now": float(T["now"].sum()) if len(T) else 0.0,
        "tender_total_after": float(T["after"].sum()) if len(T) else 0.0,
        "tender_opps": int(T["opp"].nunique()) if len(T) else 0,
        "tender_opps_book": len(opp),
        "tender_generated": ten["meta"].get("generated_at"),
        "obs_rows": int(len(obs)), "rival_pns": len(rival_pns), "rival_pns_in_base": int(parts["rival"].sum()),
        "genuine_pns_in_base": int(parts["genuine_out"].sum()), "parts_in_base": len(parts),
    }
    OUT.write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
    print("base", round(base_total, 2), "step", round(out["weighted_step"], 6))
    print(by_l1[["billed", "step", "rival_parts", "rival_share"]].round(4).to_string())
    print("PMS cats", len(by_pms)); print(by_pms[["billed", "step", "rival_parts"]].round(4).to_string())
    print("tender rows", len(T), "opps", out["tender_opps"], "of in-book w/ demand", len(opp), "now", out["tender_total_now"], "after", out["tender_total_after"])
    return 0


if __name__ == "__main__":
    sys.exit(main())
