# -*- coding: utf-8 -*-
"""
Task card 5.1 — refresh tiers by billed value.

Tier A  top 300 by billed EUR (trailing 12 months) + maintenance-programme parts inside the top 2,300
Tier B  rest of the top 2,300
Tier C  everything else billed in the window -> estimate only, no scheduled scrape

Billing basis: 01_data/00_derived/sales_fact.parquet, trailing 12 complete months to the
latest billing date. Credit/return order types (CR, RE) excluded; parts with net <= 0 excluded.
This is a RANKING, not a KPI — it is not the audited sales figure.

Outputs:
  04_tools/delegation/state/refresh_tiers.csv          part_no, tier            (safe for fetch queues)
  04_tools/delegation/state/refresh_tiers_LOCAL.csv    + billed EUR and rank    (LOCAL ONLY — never to DeepSeek/GPT)
  04_tools/delegation/state/refresh_tiers.meta.json    coverage by tier
"""
import json
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
STATE = HERE / "state"
TOP_A, TOP_AB = 300, 2300
EXCLUDE_SATY = {"CR", "RE"}


def main():
    s = pd.read_parquet(ROOT / "01_data/00_derived/sales_fact.parquet",
                        columns=["billing_date", "part_number", "net_sales_value", "saty"])
    end = s["billing_date"].max()
    start = (end - pd.DateOffset(months=12)) + pd.Timedelta(days=1)
    w = s[(s["billing_date"] >= start) & (s["billing_date"] <= end) & ~s["saty"].isin(EXCLUDE_SATY)]
    w = w.assign(part_no=w["part_number"].astype(str).str.strip().str.zfill(10))
    g = w.groupby("part_no", as_index=False)["net_sales_value"].sum()
    g = g[g["net_sales_value"] > 0].sort_values("net_sales_value", ascending=False).reset_index(drop=True)
    g["rank"] = g.index + 1

    cat = pd.read_csv(ROOT / "01_data/00_derived/parts_catalog_dimension.csv", dtype=str,
                      usecols=["part_number", "pms_category"])
    pms = set(cat.loc[cat["pms_category"].notna(), "part_number"].str.zfill(10))
    g["is_pms"] = g["part_no"].isin(pms)

    g["tier"] = "C"
    g.loc[g["rank"] <= TOP_AB, "tier"] = "B"
    g.loc[(g["rank"] <= TOP_A) | ((g["rank"] <= TOP_AB) & g["is_pms"]), "tier"] = "A"

    STATE.mkdir(parents=True, exist_ok=True)
    g[["part_no", "tier"]].to_csv(STATE / "refresh_tiers.csv", index=False)
    g.rename(columns={"net_sales_value": "billed_eur_t12m"}).to_csv(STATE / "refresh_tiers_LOCAL.csv", index=False)

    tot = g["net_sales_value"].sum()
    meta = {
        "built_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "window": f"{start.date()} .. {end.date()}",
        "basis": "sales_fact.parquet, CR/RE excluded, net>0 parts only — ranking, not audited KPI",
        "parts_billed": int(len(g)),
        "tiers": {
            t: {"parts": int((g["tier"] == t).sum()),
                "share_of_billed_eur": round(float(g.loc[g["tier"] == t, "net_sales_value"].sum() / tot), 4),
                "pms_parts": int(((g["tier"] == t) & g["is_pms"]).sum())}
            for t in ("A", "B", "C")
        },
    }
    (STATE / "refresh_tiers.meta.json").write_text(json.dumps(meta, indent=2), encoding="utf-8")
    print(json.dumps(meta, indent=2))


if __name__ == "__main__":
    main()
