#!/usr/bin/env python3
"""Data pack for the dynamic pricing-revision HTML.

Everything the page needs is derived from the cube built by
build_pricing_aim_source_cube.py, at the grain the page slices on:

  groups    db x AIM L1 x AIM L2 x AIM L3 x source   (the drill)
  db_pn     db x L1 x L2 x L3 x source x PN          (L3 → part numbers)
  customers customer x db x source                    (the account table)
  dbs       one row per distributor                   (the league)
  l1        one row per AIM family, network           (the reference line)

String columns are pooled into a dictionary so the payload stays inside the size
where the page can embed it and still open straight from Explorer.

Run: python 02_dashboards/pricing/_build/build_pricing_dashboard_data.py
"""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd

ISZE = Path(r"C:\Users\jerom\Desktop\claude\ISZE")
D = ISZE / "01_data" / "00_derived"
OUT = ISZE / "02_dashboards" / "pricing" / "_build" / "pricing_dashboard_data.json"
META = D / "pricing_aim_source_meta.json"
LINES = D / "pricing_aim_source_lines.parquet"

FX = 163.7
PUB_STEP = 1652140.71
PUB_PCT = 5.9616


def pool(series: pd.Series) -> tuple[list[str], dict[str, int]]:
    vals = sorted({str(v) for v in series.dropna().unique()})
    return vals, {v: i for i, v in enumerate(vals)}


def main() -> int:
    lines = pd.read_parquet(LINES)
    meta = json.loads(META.read_text(encoding="utf-8"))
    lines["source"] = lines["source"].map({
        "JP - Japan / IML": "JP - Japan",
        "TH - Thailand / IMIT": "TH - Thailand",
        "Not held": "Not held",
    }).fillna(lines["source"])

    dbs, db_i = pool(lines["db"])
    srcs, src_i = pool(lines["source"])
    l1s, l1_i = pool(lines["aim_l1"])
    l2s, l2_i = pool(lines["aim_l2"])
    l3s, l3_i = pool(lines["aim_l3"])
    custs, cust_i = pool(lines["customer_code"])
    cnames, cname_i = pool(lines["customer_name"])

    pr = lines[lines["priced_both"]].copy()
    pr["pn"] = pr["part_number"].astype(str)

    def agg_priced(frame: pd.DataFrame, keys: list[str]) -> pd.DataFrame:
        return frame.groupby(keys, dropna=False).agg(
            pn=("part_number", "nunique"),
            rows=("billed_eur", "size"),
            qty=("qty", "sum"),
            billed=("billed_eur", "sum"),
            prior=("prior_eur", "sum"),
            new=("new_eur", "sum"),
            step=("step_eur", "sum"),
        ).reset_index()

    def agg_all(frame: pd.DataFrame, keys: list[str]) -> pd.DataFrame:
        return frame.groupby(keys, dropna=False).agg(
            pn=("part_number", "nunique"),
            rows=("billed_eur", "size"),
            qty=("qty", "sum"),
            all_billed=("billed_eur", "sum"),
        ).reset_index()

    def merge_spine(all_keys: list[str]) -> pd.DataFrame:
        """Every in-scope key, with priced metrics left-joined (Not held unpriced kept)."""
        spine = agg_all(lines, all_keys)
        priced = agg_priced(pr, all_keys)
        out = spine.merge(priced, on=all_keys, how="left", suffixes=("", "_pr"))
        for c in ("billed", "prior", "new", "step"):
            out[c] = out[c].fillna(0.0)
        # prefer in-scope pn/rows/qty from the spine; drop priced duplicates if present
        for c in ("pn_pr", "rows_pr", "qty_pr"):
            if c in out.columns:
                out = out.drop(columns=[c])
        return out

    # ---- groups: drill grain — all in-scope keys (Not held pile included)
    gk = ["db", "aim_l1", "aim_l2", "aim_l3", "source"]
    grp = merge_spine(gk)
    groups = [[
        db_i[r.db], l1_i[r.aim_l1], l2_i[r.aim_l2], l3_i[r.aim_l3], src_i[r.source],
        int(r.pn), int(r.rows), round(float(r.qty), 2), round(float(r.billed), 2),
        round(float(r.prior), 2), round(float(r.new), 2), round(float(r.step), 4),
        round(float(r.all_billed), 2),
    ] for r in grp.itertuples(index=False)]

    # ---- customers: account x db x source (incl. Not held / unpriced-only)
    ck = ["customer_code", "customer_name", "db", "source"]
    cus = merge_spine(ck)
    unpriced_by_cust = (lines.loc[~lines["priced_both"]]
                        .groupby("customer_code")
                        .agg(unpriced_eur=("billed_eur", "sum"),
                             unpriced_n=("billed_eur", "size")))
    cus = cus.merge(unpriced_by_cust, left_on="customer_code", right_index=True, how="left")
    cus["unpriced_eur"] = cus["unpriced_eur"].fillna(0.0)
    cus["unpriced_n"] = cus["unpriced_n"].fillna(0).astype(int)
    customers = [[
        cust_i[r.customer_code], cname_i[r.customer_name], db_i[r.db], src_i[r.source],
        int(r.pn), int(r.rows), round(float(r.qty), 2), round(float(r.billed), 2),
        round(float(r.prior), 2), round(float(r.new), 2), round(float(r.step), 4),
        round(float(r.all_billed), 2), round(float(r.unpriced_eur), 2), int(r.unpriced_n),
    ] for r in cus.itertuples(index=False)]

    # customer x AIM L1, so the account table can be drilled to a family
    cf = merge_spine(["customer_code", "db", "aim_l1", "source"])
    cust_fam = [[
        cust_i[r.customer_code], db_i[r.db], l1_i[r.aim_l1], src_i[r.source],
        int(r.pn), round(float(r.billed), 2), round(float(r.prior), 2),
        round(float(r.new), 2), round(float(r.step), 4),
        round(float(r.all_billed), 2),
    ] for r in cf.itertuples(index=False)]

    # customer x AIM L1 x L2 — donut grain for the customer-first drill
    cl2 = merge_spine(["customer_code", "aim_l1", "aim_l2", "source"])
    cust_l2 = [[
        cust_i[r.customer_code], l1_i[r.aim_l1], l2_i[r.aim_l2], src_i[r.source],
        int(r.pn), int(r.rows), round(float(r.qty), 2),
        round(float(r.billed), 2), round(float(r.prior), 2),
        round(float(r.new), 2), round(float(r.step), 4),
        round(float(r.all_billed), 2),
    ] for r in cl2.itertuples(index=False)]

    # customer x AIM L1 x L2 x L3 — third step of the customer drill
    cl3 = merge_spine(["customer_code", "aim_l1", "aim_l2", "aim_l3", "source"])
    cust_l3 = [[
        cust_i[r.customer_code], l1_i[r.aim_l1], l2_i[r.aim_l2], l3_i[r.aim_l3],
        src_i[r.source],
        int(r.pn), int(r.rows), round(float(r.qty), 2),
        round(float(r.billed), 2), round(float(r.prior), 2),
        round(float(r.new), 2), round(float(r.step), 4),
        round(float(r.all_billed), 2),
    ] for r in cl3.itertuples(index=False)]

    # part numbers for customer → L1 → L2 → L3 → PN (priced lines, sources collapsed)
    pns, pn_i = pool(pr["part_number"].astype(str))
    desc_map = (pr.drop_duplicates("part_number")
                .set_index("part_number")["description"]
                .fillna("").astype(str).str.slice(0, 90))
    descs = [str(desc_map.get(p, "")) for p in pns]
    pn_g = (pr.groupby(["customer_code", "aim_l1", "aim_l2", "aim_l3", "part_number"],
                       dropna=False)
            .agg(qty=("qty", "sum"), billed=("billed_eur", "sum"),
                 prior=("prior_eur", "sum"), new=("new_eur", "sum"),
                 step=("step_eur", "sum"))
            .reset_index())
    cust_pn = [[
        cust_i[str(r.customer_code)], l1_i[r.aim_l1], l2_i[r.aim_l2], l3_i[r.aim_l3],
        pn_i[str(r.part_number)],
        round(float(r.qty), 2), round(float(r.billed), 2),
        round(float(r.prior), 2), round(float(r.new), 2),
        round(float(r.step), 4),
    ] for r in pn_g.itertuples(index=False)]

    # ---- league: one row per distributor
    lg = merge_spine(["db"])
    unpriced_by_db = (lines.loc[~lines["priced_both"]]
                      .groupby("db")
                      .agg(unpriced_eur=("billed_eur", "sum"),
                           unpriced_n=("billed_eur", "size")))
    lg = lg.merge(unpriced_by_db, left_on="db", right_index=True, how="left")
    lg["unpriced_eur"] = lg["unpriced_eur"].fillna(0.0)
    lg["unpriced_n"] = lg["unpriced_n"].fillna(0).astype(int)
    db_rows = [[
        db_i[r.db], int(r.pn), int(r.rows), round(float(r.qty), 2),
        round(float(r.billed), 2), round(float(r.prior), 2), round(float(r.new), 2),
        round(float(r.step), 4), round(float(r.all_billed), 2),
        round(float(r.unpriced_eur), 2), int(r.unpriced_n),
    ] for r in lg.itertuples(index=False)]

    # ---- AIM L1 network reference (priced metrics; all_billed on spine)
    net_l1 = merge_spine(["aim_l1"])
    net_rows = [[
        l1_i[r.aim_l1], int(r.pn), round(float(r.billed), 2), round(float(r.prior), 2),
        round(float(r.new), 2), round(float(r.step), 4),
    ] for r in net_l1.itertuples(index=False)]

    # ---- source totals (Not held in-scope euro included via all_billed spine)
    net_src = merge_spine(["source"])
    src_rows = [[src_i[r.source], int(r.pn), round(float(r.all_billed), 2),
                 round(float(r.prior), 2), round(float(r.new), 2), round(float(r.step), 4),
                 round(float(r.qty), 2)] for r in net_src.itertuples(index=False)]

    # ---- brake deep dive -----------------------------------------------------
    # The level-1 chart shows "Brakes" as one bar among twenty-three, so a level-2
    # cut and the part numbers behind the biggest moves are carried here instead.
    # Part numbers come from the priced book only: every line in a step has both
    # base prices, so a part number added up across slices still ties to the
    # level-2 and family totals on the page.
    brake_lines = pr[pr["aim_l1"] == "Brakes"].copy()
    bp = (brake_lines
          .groupby(["db", "source", "aim_l2", "pn"], dropna=False)
          .agg(prior_jpy=("prior_base_jpy", "first"),
               new_jpy=("new_base_jpy", "first"),
               qty=("qty", "sum"), billed=("billed_eur", "sum"),
               step=("step_eur", "sum"))
          .reset_index())
    brake_pn = [[
        db_i[r.db], src_i[r.source], l2_i[r.aim_l2], pn_i[r.pn],
        round(float(r.prior_jpy), 1), round(float(r.new_jpy), 1),
        round(float(r.qty), 2), round(float(r.billed), 2),
        round(float(r.step), 4),
    ] for r in bp.itertuples(index=False)]

    # ---- step concentration --------------------------------------------------
    # How few part numbers carry the increase. Parts that fell in price (a small
    # number) keep the total at the family figure; parts that did not move are
    # left out so the curve is not padded with zeros that carry no step.
    def concentration(vals, head: int = 40, points: int = 110) -> dict:
        v = np.sort(np.asarray(vals, dtype=float))[::-1]
        if not len(v) or v.sum() <= 0:
            return {"n": 0, "total": 0.0, "positive": 0, "half": None,
                    "eighty": None, "curve": []}
        cum = np.cumsum(v)
        n = len(v)
        total = float(v.sum())
        ranks = list(range(1, min(head, n) + 1))
        if n > head:
            ranks += [int(x) for x in np.unique(
                np.linspace(head + 1, n, points - head).astype(int))]
        curve = [[r, round(100 * float(cum[r - 1]) / total, 3)] for r in ranks]
        return {
            "n": n,
            "total": round(total, 2),
            "positive": int((v > 0).sum()),
            "half": int(np.argmax(cum >= 0.5 * total) + 1),
            "eighty": int(np.argmax(cum >= 0.8 * total) + 1),
            "curve": curve,
        }

    step_pos = pr[pr["step_eur"] > 0]
    conc_all, conc_brake = {}, {}
    for db, sub in step_pos.groupby("db"):
        conc_all[db] = concentration(sub.groupby("pn")["step_eur"].sum().values)
    for db, sub in step_pos[step_pos["aim_l1"] == "Brakes"].groupby("db"):
        conc_brake[db] = concentration(sub.groupby("pn")["step_eur"].sum().values)
    conc_all["__net__"] = concentration(
        step_pos.groupby("pn")["step_eur"].sum().values)
    conc_brake["__net__"] = concentration(
        step_pos[step_pos["aim_l1"] == "Brakes"]
        .groupby("pn")["step_eur"].sum().values)

    net = lines[lines["priced_both"]]
    totals = {
        "billed": round(float(lines["billed_eur"].sum()), 2),  # full in-scope
        "priced_billed": round(float(net["billed_eur"].sum()), 2),
        "prior": round(float(net["prior_eur"].sum()), 2),
        "new": round(float(net["new_eur"].sum()), 2),
        "step": round(float(net["step_eur"].sum()), 2),
        "qty": round(float(net["qty"].sum()), 2),
        "pn": int(lines["part_number"].nunique()),
        "lines": int(len(lines)),
        "priced_lines": int(len(net)),
    }
    totals["pct"] = 100 * (totals["new"] / totals["prior"] - 1)

    # top part numbers network-wide, by step, one row per part number x distributor
    # so the movers table can follow the distributor selection too
    mv = (net.groupby(["part_number", "db"])
          .agg(qty=("qty", "sum"), billed=("billed_eur", "sum"), prior=("prior_eur", "sum"),
               new=("new_eur", "sum"), step=("step_eur", "sum")).reset_index())
    top = (net.groupby("part_number")["step_eur"].sum()
           .sort_values(ascending=False).head(300).index)
    attrs = (net.drop_duplicates("part_number")
             .set_index("part_number")[["description", "aim_l1", "aim_l2", "aim_l3", "source"]])
    mv = mv[mv["part_number"].isin(set(top))].copy()
    mv["description"] = mv["part_number"].map(attrs["description"])
    mv["aim_l1"] = mv["part_number"].map(attrs["aim_l1"])
    mv["aim_l2"] = mv["part_number"].map(attrs["aim_l2"])
    mv["aim_l3"] = mv["part_number"].map(attrs["aim_l3"])
    mv["source"] = mv["part_number"].map(attrs["source"])
    mv = mv.sort_values("step", ascending=False)
    movers = [[
        str(r.part_number), str(r.description)[:110], l1_i[r.aim_l1], l2_i[r.aim_l2],
        l3_i[r.aim_l3], src_i[r.source], db_i[r.db], round(float(r.qty), 2),
        round(float(r.billed), 2), round(float(r.prior), 2), round(float(r.new), 2),
        round(float(r.step), 4),
    ] for r in mv.itertuples(index=False)]

    # Full PN grain for network drill L3 → part number (same size class as cust_pn).
    db_pn_g = (net.groupby(["db", "aim_l1", "aim_l2", "aim_l3", "source", "part_number"],
                           dropna=False)
               .agg(qty=("qty", "sum"), billed=("billed_eur", "sum"),
                    prior=("prior_eur", "sum"), new=("new_eur", "sum"),
                    step=("step_eur", "sum"))
               .reset_index())
    db_pn = [[
        db_i[r.db], l1_i[r.aim_l1], l2_i[r.aim_l2], l3_i[r.aim_l3], src_i[r.source],
        pn_i[str(r.part_number)],
        round(float(r.qty), 2), round(float(r.billed), 2),
        round(float(r.prior), 2), round(float(r.new), 2),
        round(float(r.step), 4),
    ] for r in db_pn_g.itertuples(index=False)]

    payload = {
        "generated": datetime.now(timezone.utc).isoformat(),
        "window": {"start": "2025-07-01", "end": "2026-06-30"},
        "fx": FX,
        "published": {"step": PUB_STEP, "pct": PUB_PCT},
        "totals": totals,
        "in_scope": {
            "rows": meta["basis"]["rows_in_scope"],
            "pn": meta["basis"]["part_numbers_in_scope"],
            "billed": meta["basis"]["in_scope_billed_eur"],
            "priced_rows": meta["basis"]["rows_priced_both_sides"],
            "priced_billed": meta["basis"]["priced_billed_eur"],
        },
        "coverage": {
            "spine_pct": meta["taxonomy"]["eur_on_aim_spine_pct"],
            "l3_pct": meta["taxonomy"]["eur_with_l3_pct"],
            "source_pct": meta["source_of_supply"]["share_of_in_scope_eur_labeled_pct"],
        },
        "pool": {"db": dbs, "src": srcs, "l1": l1s, "l2": l2s, "l3": l3s,
                 "cust": custs, "cname": cnames, "pn": pns, "desc": descs},
        "groups": groups,
        "customers": customers,
        "cust_fam": cust_fam,
        "cust_l2": cust_l2,
        "cust_l3": cust_l3,
        "cust_pn": cust_pn,
        "db_pn": db_pn,
        "db_rows": db_rows,
        "brake_pn": brake_pn,
        "conc_all": conc_all,
        "conc_brake": conc_brake,
        "net_l1": net_rows,
        "net_src": src_rows,
        "movers": movers,
    }
    txt = json.dumps(payload, separators=(",", ":"), ensure_ascii=False)
    OUT.write_text(txt, encoding="utf-8")

    print("=" * 74)
    print("PRICING DASHBOARD DATA")
    print("=" * 74)
    print(f"groups        {len(groups):,}")
    print(f"customers     {len(customers):,}")
    print(f"cust_fam      {len(cust_fam):,}")
    print(f"cust_l2       {len(cust_l2):,}")
    print(f"cust_l3       {len(cust_l3):,}")
    print(f"cust_pn       {len(cust_pn):,}")
    print(f"db_pn         {len(db_pn):,}")
    print(f"brake_pn      {len(brake_pn):,}")
    print(f"conc_all      {len(conc_all)} curves; network half "
          f"{conc_all['__net__']['half']} / eighty {conc_all['__net__']['eighty']}")
    print(f"conc_brake    {len(conc_brake)} curves; network half "
          f"{conc_brake['__net__']['half']} / eighty {conc_brake['__net__']['eighty']}")
    print(f"db_rows       {len(db_rows):,}")
    print(f"net_l1        {len(net_rows):,}")
    print(f"movers        {len(movers):,}")
    print(f"payload       {len(txt) / 1024:,.0f} KB")
    print(f"network       step {totals['step']:,.2f}  weighted {totals['pct']:.4f}%")
    print(f"-> {OUT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
