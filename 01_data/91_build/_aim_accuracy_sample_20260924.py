"""AIM accuracy sample: 50 classified part numbers, weighted toward the highest billed euro.

Read-only. Draws 50 part numbers with probability proportional to L12M billed EUR
over classified parts, fixed seed, so the draw is reproducible. Writes the sample
for review; judgement of agreement is made outside this script.
"""
from __future__ import annotations

import csv
import random
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(r"C:\Users\jerom\Desktop\claude\ISZE")
PRISM = ROOT / "03_analytics" / "Isuzu" / "prism"
sys.path.insert(0, str(PRISM))

from config import resolve_mapping_path  # noqa: E402
from modules.data_prep import EXCLUDED_CODES, load_distributor_mapping  # noqa: E402
from modules.sales_loader import load_prism_sales  # noqa: E402

DER = ROOT / "01_data" / "00_derived"
OUT = ROOT / "01_data" / "91_build" / "_aim_accuracy_sample_20260924.csv"
SEED = 20260924
N = 50
PLACEHOLDER = {"", "Unknown", "Unknown Review", "nan", "None", "NaN"}


def clean(s):
    return s.fillna("").astype(str).str.strip()


def main() -> int:
    df_map = load_distributor_mapping(str(resolve_mapping_path()))
    sales, _ = load_prism_sales(df_map)
    sales = sales[~sales["distributor_code"].isin(EXCLUDED_CODES | {"UNMAPPED"})]
    sales = sales[~sales["is_credit_note"]]
    sales = sales[sales["line_kind"] == "part"]
    sales["billing_date"] = pd.to_datetime(sales["billing_date"], errors="coerce")
    sales = sales.dropna(subset=["billing_date"])
    dmax = sales["billing_date"].max()
    month_end = dmax.replace(day=1) + pd.offsets.MonthEnd(0)
    l12_from = (month_end - pd.offsets.DateOffset(months=11)).replace(day=1)
    p = sales[(sales["billing_date"] >= l12_from) & (sales["billing_date"] <= month_end)].copy()
    p["pn"] = clean(p["part_number"])

    dim = (p.groupby("pn", as_index=False)
             .agg(billed_eur=("net_sales_value", "sum"),
                  billed_qty=("billed_qty", "sum"),
                  n_descs=("description", "nunique")))
    desc = (p.groupby(["pn", "description"], as_index=False)["net_sales_value"].sum()
              .sort_values("net_sales_value", ascending=False)
              .drop_duplicates("pn")[["pn", "description"]])

    m = pd.read_csv(DER / "aim_master_v2.csv", dtype=str, low_memory=False)
    m["pn"] = clean(m["part_number"])
    l1 = clean(m["aim_l1_fixed"]).where(clean(m["aim_l1_fixed"]) != "", clean(m["aim_l1"]))
    l2 = clean(m["aim_l2_fixed"]).where(clean(m["aim_l2_fixed"]) != "", clean(m["aim_l2"]))
    l3 = clean(m["aim_l3"])
    master = pd.DataFrame({
        "pn": m["pn"], "f1": l1, "f2": l2, "f3": l3,
        "has_family": ~l1.isin(PLACEHOLDER),
        "aim_source": clean(m["aim_source"]),
        "fig_key": clean(m["fig_key"]),
        "cat_l2": clean(m["cat_l2"]),
    })
    d = dim.merge(master, on="pn", how="left").merge(desc, on="pn", how="left")
    cls = d[d["has_family"].fillna(False)].copy()
    cls = cls[cls["billed_eur"] > 0].copy()
    print(f"classified PNs with L12M billing: {len(cls):,}")

    rng = random.Random(SEED)
    weights = cls["billed_eur"].tolist()
    picks = rng.choices(range(len(cls)), weights=weights, k=N * 20)
    seen, chosen = set(), []
    for i in picks:
        if i in seen:
            continue
        seen.add(i)
        chosen.append(i)
        if len(chosen) == N:
            break
    sample = cls.iloc[chosen].sort_values("billed_eur", ascending=False)

    with OUT.open("w", encoding="utf-8", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["n", "part_number", "description_as_billed", "l12m_billed_eur",
                    "l12m_qty", "aim_l1", "aim_l2", "aim_l3", "aim_source", "fig_key",
                    "agree", "note"])
        for i, (_, r) in enumerate(sample.iterrows(), 1):
            w.writerow([i, r["pn"], r["description"], f"{r['billed_eur']:.2f}",
                        f"{r['billed_qty']:.0f}", r["f1"], r["f2"], r["f3"],
                        r["aim_source"], r["fig_key"], "", ""])
    print(f"sample written: {OUT}")
    print(sample[["pn", "description", "billed_eur", "f1", "f2", "f3"]]
          .assign(billed_eur=lambda x: x["billed_eur"].round(0))
          .to_string(index=False, max_colwidth=44))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
