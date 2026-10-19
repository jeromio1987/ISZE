# -*- coding: utf-8 -*-
"""Deep version of the price-move evidence: per AIM category.

Adds to build_move_evidence_by_aim.py:
  A  what alternative is known for each billed part (rival price / rival number / own value line / nothing)
  B  genuine Isuzu parts offered outside our network, and how many are below our own list price
  C  how volume reacted to our own list price changes in 2023-2025 (per category)
  D  tender result notices already collected, what they carry
  E  drill-down data (second and third AIM level, parts)
Read-only on every input. Writes 02_dashboards/pricing/_build/move_evidence_deep.json
"""
from __future__ import annotations
import json, sys
from pathlib import Path
import numpy as np
import pandas as pd

ROOT = Path(r"C:\Users\jerom\Desktop\claude\ISZE")
D = ROOT / "01_data" / "00_derived"
PAY = ROOT / "02_dashboards/pricing/_build/price_tool_html_v6_2026-10-15/payload6.json"
OUT = ROOT / "02_dashboards/pricing/_build/move_evidence_deep.json"
TEN = ROOT / "01_data/14_dashboards/tender_data.json"
GRADED = ROOT / "04_tools/aftermarket_intelligence/state/crossref_graded.csv"

RIVAL = {"aftermarket_retail", "aftermarket_trade", "aftermarket_rrp", "online_median",
         "marketplace", "quote", "survey_workshop", "survey_list"}
GENUINE = {"genuine_grey", "dealer"}


def num(s):
    return pd.to_numeric(s, errors="coerce")


def main() -> int:
    P = json.loads(PAY.read_text(encoding="utf-8"))
    parts = pd.DataFrame(P["parts"])
    parts.columns = ["pn", "desc", "l1", "l2", "l3", "step", "bp0", "bp1", "c8", "c9", "c10", "c11", "c12", "pms", "pms_cell", "c15"]
    lines = pd.DataFrame(P["lines"])
    parts["billed"] = lines.groupby(0)[3].sum().reindex(parts.index).fillna(0.0)
    parts["l1name"] = parts["l1"].map(lambda i: P["l1"][i])
    parts["l2name"] = parts["l2"].map(lambda i: P["l2"][i][1])
    parts["l3name"] = parts["l3"].map(lambda i: P["l3"][i][1])
    base = float(parts["billed"].sum())

    # ---- rival and genuine observations (same part only)
    obs = pd.read_parquet(D / "price_observations.parquet")
    obs = obs[obs["price"].notna() & obs["match_method"].isin(["exact_oem", "crossref"])].copy()
    obs["part_no"] = obs["part_no"].astype(str)
    riv = obs[obs["price_type"].isin(RIVAL)].groupby("part_no")["price_eur"].agg(riv_n="size", riv_min="min", riv_max="max")
    gen = obs[obs["price_type"].isin(GENUINE)].groupby("part_no")["price_eur"].agg(gen_n="size", gen_min="min", gen_max="max")
    parts = parts.join(riv, on="pn").join(gen, on="pn")
    parts["has_riv_price"] = parts["riv_n"].notna()
    parts["has_gen"] = parts["gen_n"].notna()

    # our current list price (PR00, IE40) per part
    pl = pd.read_parquet(D / "pricing_pr00_ie40.parquet", columns=["part_number", "sp_eur"])
    pl["part_number"] = pl["part_number"].astype(str)
    pl = pl[pl["sp_eur"] > 0].groupby("part_number")["sp_eur"].median().rename("our_list")
    parts = parts.join(pl, on="pn")

    # ---- A: alternative known
    g = pd.read_csv(GRADED, dtype=str)
    usable = set(g[g["tier"].isin(["confirmed", "likely"])]["part_no"])
    anyedge = set(g[g["tier"] != "reject"]["part_no"])
    own = set(pd.read_parquet(D / "genuine_bvp_crossref.parquet")["genuine_pn"].astype(str))

    def alt(r):
        if r["has_riv_price"]:
            return "rival_price"
        if r["pn"] in usable:
            return "rival_number"
        if r["pn"] in own:
            return "own_line"
        if r["pn"] in anyedge:
            return "weak_edge"
        return "nothing"
    parts["alt"] = parts.apply(alt, axis=1)

    # ---- B: genuine outside our network, below our own list?
    parts["gen_below_list"] = parts["has_gen"] & parts["our_list"].notna() & (parts["gen_min"] < parts["our_list"])
    parts["gen_ratio"] = parts["gen_min"] / parts["our_list"]

    # ---- C: reaction of volume to our own list changes
    s = pd.read_parquet(D / "sales_fact.parquet", columns=["part_number", "year", "billed_qty", "net_sales_value"])
    s = s[(s.billed_qty > 0) & (s.net_sales_value > 0) & s["year"].isin([2023, 2024, 2025])]
    s["pn"] = num(s["part_number"])
    s = s.dropna(subset=["pn"])
    s["pn"] = s["pn"].astype("int64")
    pq = s.groupby(["pn", "year"]).agg(q=("billed_qty", "sum"), v=("net_sales_value", "sum")).reset_index()
    L = {}
    for y in (2023, 2024, 2025):
        d = pd.read_parquet(D / f"pricing_pr00_ie40_{y}.parquet").dropna().drop_duplicates("Material")
        d["Material"] = d["Material"].astype("int64")
        L[y] = d.set_index("Material")["Price_EUR"].astype(float)
    aim = pd.read_csv(D / "AIM_Master_PN_Categories_Figkey_release_2026-10-15.csv", dtype=str, usecols=["part_number", "aim_level_1", "line_kind"])
    aim = aim[aim["line_kind"] == "part"].copy()
    aim["pn"] = num(aim["part_number"])
    aim = aim.dropna(subset=["pn"]).drop_duplicates("pn")
    aim["pn"] = aim["pn"].astype("int64")
    l1_of = aim.set_index("pn")["aim_level_1"]
    rows = []
    for y in (2024, 2025):
        a = pq[pq.year == y - 1].set_index("pn")
        b = pq[pq.year == y].set_index("pn")
        j = a.join(b, lsuffix="0", rsuffix="1", how="inner")
        j["p0"] = L[y - 1].reindex(j.index).values
        j["p1"] = L[y].reindex(j.index).values
        j = j.dropna(subset=["p0", "p1"])
        j = j[(j.p0 > 0) & (j.p1 > 0)]
        j["dq"] = np.log(j.q1 / j.q0).clip(-2.5, 2.5)
        j["dp"] = np.log(j.p1 / j.p0)
        j["w"] = j.v0
        j["year"] = y
        j["l1"] = l1_of.reindex(j.index).values
        rows.append(j.reset_index()[["pn", "year", "dq", "dp", "w", "l1"]])
    pan = pd.concat(rows, ignore_index=True).dropna(subset=["l1"])

    def fit(df: pd.DataFrame) -> dict:
        out = {}
        xs, ys, ws = [], [], []
        for _, k in df.groupby("year"):
            w = k["w"].values
            xm = np.average(k["dp"], weights=w)
            ym = np.average(k["dq"], weights=w)
            xs.append(k["dp"].values - xm); ys.append(k["dq"].values - ym); ws.append(w)
        x = np.concatenate(xs); y = np.concatenate(ys); w = np.concatenate(ws)
        sxx = float(np.sum(w * x * x))
        if sxx <= 0 or len(x) < 30:
            return {"n": int(len(x)), "beta": None, "se": None, "sd_dp": None}
        beta = float(np.sum(w * x * y) / sxx)
        e = y - beta * x
        se = float(np.sqrt(np.sum((w * x * e) ** 2)) / sxx)
        sd = float(np.sqrt(np.sum(w * x * x) / np.sum(w)))
        return {"n": int(len(x)), "beta": beta, "se": se, "sd_dp": sd, "w": float(w.sum())}

    react = {"ALL": fit(pan)}
    p2 = pan.copy(); p2["w"] = 1.0
    robust = {"unweighted": fit(p2),
              "small_moves_only": fit(pan[pan["dp"].abs() <= 0.15]),
              "only_2025": fit(pan[pan["year"] == 2025]),
              "only_2024": fit(pan[pan["year"] == 2024])}
    mov = pan["dp"]
    spread = {"share_moved_over_1pct": float((mov.abs() > 0.01).mean()), "share_moved_over_5pct": float((mov.abs() > 0.05).mean()),
              "weighted_share_over_5pct": float(pan.loc[mov.abs() > 0.05, "w"].sum() / pan["w"].sum())}
    for k, df in pan.groupby("l1"):
        react[k] = fit(df)

    # ---- D: result notices already collected
    ten = json.loads(TEN.read_text(encoding="utf-8"))
    import re
    res = [n for n in ten["notices"] if re.search(r"RESULT|can-standard|can-modif|conclusion", str(n.get("Notice Type")), re.I)]
    tender_res = {"result_notices": len(res), "by_country": pd.Series([n.get("Country") for n in res]).value_counts().to_dict(),
                  "with_value": sum(1 for n in res if n.get("Est. Value")), "with_isuzu_hit": sum(1 for n in res if "isuzu" in json.dumps(n.get("brand_hits") or "").lower()),
                  "notices_total": len(ten["notices"])}

    # ---- roll-ups per L1
    def roll(gp: pd.DataFrame) -> dict:
        b = float(gp["billed"].sum())
        r = {"billed": b, "parts": int(len(gp)), "step": float((gp["billed"] * gp["step"]).sum() / b) if b else None}
        for k in ("rival_price", "rival_number", "own_line", "weak_edge", "nothing"):
            r["alt_" + k] = float(gp.loc[gp["alt"] == k, "billed"].sum())
            r["n_" + k] = int((gp["alt"] == k).sum())
        r["gen_billed"] = float(gp.loc[gp["has_gen"], "billed"].sum())
        r["gen_n"] = int(gp["has_gen"].sum())
        r["genb_billed"] = float(gp.loc[gp["gen_below_list"], "billed"].sum())
        r["genb_n"] = int(gp["gen_below_list"].sum())
        return r

    l1 = []
    for k, gp in parts.groupby("l1name"):
        r = roll(gp); r["name"] = k
        r["react"] = react.get(k)
        l2 = []
        for k2, g2 in gp.groupby("l2name"):
            r2 = roll(g2); r2["name"] = k2
            l3 = []
            for k3, g3 in g2.groupby("l3name"):
                r3 = roll(g3); r3["name"] = k3; l3.append(r3)
            r2["l3"] = sorted(l3, key=lambda z: -z["billed"])
            l2.append(r2)
        r["l2"] = sorted(l2, key=lambda z: -z["billed"])
        top = gp.sort_values("billed", ascending=False).head(60)
        keep = pd.concat([top, gp[gp["has_riv_price"] | gp["gen_below_list"]]]).drop_duplicates("pn")
        r["parts_list"] = [{
            "pn": x.pn, "desc": x.desc, "l2": x.l2name, "l3": x.l3name, "billed": float(x.billed), "step": float(x.step),
            "alt": x.alt, "riv_n": None if pd.isna(x.riv_n) else int(x.riv_n), "riv_min": None if pd.isna(x.riv_min) else float(x.riv_min),
            "riv_max": None if pd.isna(x.riv_max) else float(x.riv_max), "gen_min": None if pd.isna(x.gen_min) else float(x.gen_min),
            "our_list": None if pd.isna(x.our_list) else float(x.our_list)} for x in keep.sort_values("billed", ascending=False).itertuples()]
        l1.append(r)
    l1 = sorted(l1, key=lambda z: -z["billed"])

    tot = roll(parts)
    bands = {"below_list": int(parts["gen_below_list"].sum()),
             "list_to_ref": int((parts["has_gen"] & (parts["gen_min"] >= parts["our_list"]) & (parts["gen_min"] < parts["our_list"] * 1.785)).sum()),
             "above_ref": int((parts["has_gen"] & (parts["gen_min"] >= parts["our_list"] * 1.785)).sum()),
             "no_list": int((parts["has_gen"] & parts["our_list"].isna()).sum())}
    bb = lambda m: float(parts.loc[m, "billed"].sum())
    bands_eur = {"below_list": bb(parts["gen_below_list"]),
                 "list_to_ref": bb(parts["has_gen"] & (parts["gen_min"] >= parts["our_list"]) & (parts["gen_min"] < parts["our_list"] * 1.785)),
                 "above_ref": bb(parts["has_gen"] & (parts["gen_min"] >= parts["our_list"] * 1.785)),
                 "no_list": bb(parts["has_gen"] & parts["our_list"].isna())}
    med = float(parts.loc[parts["has_gen"] & parts["our_list"].notna(), "gen_ratio"].median())
    out = {"base_total": base, "total": tot, "react_all": react["ALL"], "robust": robust, "spread": spread,
           "gen_bands": bands, "gen_bands_eur": bands_eur, "gen_median_ratio": med, "l1": l1, "tender_results": tender_res,
           "panel_rows": int(len(pan)), "panel_years": [2024, 2025]}
    OUT.write_text(json.dumps(out, ensure_ascii=False), encoding="utf-8")

    print("base", round(base, 2))
    for k in ("rival_price", "rival_number", "own_line", "weak_edge", "nothing"):
        print(f"{k:13s} parts {tot['n_'+k]:6d}  billed {tot['alt_'+k]:12,.0f}  {tot['alt_'+k]/base:6.1%}")
    print("genuine outside: parts", tot["gen_n"], "billed", round(tot["gen_billed"]), f"{tot['gen_billed']/base:.1%}",
          "| below our list: parts", tot["genb_n"], "billed", round(tot["genb_billed"]), f"{tot['genb_billed']/base:.1%}")
    print("reaction ALL", react["ALL"]); print("robust", {k: (round(v["beta"], 3), round(v["se"], 3), v["n"]) for k, v in robust.items()}); print("spread", spread)
    print("bands", bands, {k: round(v) for k, v in bands_eur.items()}, "median ratio", round(med, 3))
    for r in l1[:12]:
        q = r["react"] or {}
        b = q.get("beta"); se = q.get("se")
        print(f"{r['name'][:24]:24s} n={q.get('n')} beta={None if b is None else round(b,3)} se={None if se is None else round(se,3)} sd_dp={None if q.get('sd_dp') is None else round(q['sd_dp'],3)}")
    print(tender_res)
    return 0


if __name__ == "__main__":
    sys.exit(main())
