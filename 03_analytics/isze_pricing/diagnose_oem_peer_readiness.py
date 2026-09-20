"""OEM peer readiness + street-vs-Isuze diagnostic (internal).

Does not invent prices. Writes derived CSVs and prints a gate summary.

Usage:
  python 03_analytics/isze_pricing/diagnose_oem_peer_readiness.py
"""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

ENGINE = Path(__file__).resolve().parent
REPO = ENGINE.parents[1]
DER = REPO / "01_data" / "00_derived"
BASKET = ENGINE / "oem_peer_basket.csv"
SCRAPE = ENGINE / "oem_peer_scrape_list.csv"
PR00 = DER / "pricing_pr00_ie40.parquet"
STREET_FACTOR = 1.785  # PR00 × DB × dealer — config formula.street_factor
MIN_N = 3

OUT_READY = DER / "oem_peer_readiness_20260810.csv"
OUT_PN = DER / "oem_peer_street_vs_isze_20260810.csv"
OUT_JSON = DER / "oem_peer_readiness_20260810.json"


def _pn(s) -> str:
    t = str(s or "").strip()
    if t.endswith(".0") and t[:-2].isdigit():
        t = t[:-2]
    if t.isdigit() and len(t) <= 10:
        return t.zfill(10)
    return t


def load_pr00() -> pd.Series:
    """Isuzu PN → PR00 list EUR."""
    if not PR00.is_file():
        return pd.Series(dtype=float)
    df = pd.read_parquet(PR00)
    # tolerate column name variants
    pn_col = next(
        (
            c
            for c in ("part_number", "pn", "Material", "material")
            if c in df.columns
        ),
        None,
    )
    sp_col = next(
        (
            c
            for c in ("sp_eur", "PR00", "price_eur", "Amount", "amount", "list_eur")
            if c in df.columns
        ),
        None,
    )
    if pn_col is None or sp_col is None:
        # probe
        cols = list(df.columns)
        raise SystemExit(f"PR00 parquet columns unexpected: {cols[:20]}")
    s = df[[pn_col, sp_col]].copy()
    s[pn_col] = s[pn_col].map(_pn)
    s[sp_col] = pd.to_numeric(s[sp_col], errors="coerce")
    return s.dropna().drop_duplicates(pn_col).set_index(pn_col)[sp_col]


def readiness(basket: pd.DataFrame) -> pd.DataFrame:
    b = basket.copy()
    b["peer_street_eur"] = pd.to_numeric(b["peer_street_eur"], errors="coerce")
    b["has_oe"] = b["peer_oe_pn"].astype(str).str.strip().ne("") & b[
        "peer_oe_pn"
    ].notna()
    b["priced"] = b["peer_street_eur"].notna() & (b["peer_street_eur"] > 0)
    rows = []
    for cat, g in b.groupby("pms_category"):
        priced = g[g["priced"]]
        mapped = g[g["has_oe"]]
        n_priced = int(len(priced))
        rows.append(
            {
                "pms_category": cat,
                "n_basket_rows": int(len(g)),
                "n_mapped_oe_rows": int(len(mapped)),
                "n_unique_oe": int(mapped["peer_oe_pn"].nunique()),
                "n_priced_rows": n_priced,
                "n_priced_oe": int(priced["peer_oe_pn"].nunique()),
                "n_priced_isze_pn": int(priced["isze_pn"].nunique()),
                "gap_to_oem_benchmark": max(0, MIN_N - n_priced),
                "basis_if_alloc": (
                    "oem_benchmark"
                    if n_priced >= MIN_N
                    else ("near_gate" if n_priced == MIN_N - 1 else "below_gate")
                ),
                "peer_markets_priced": ",".join(
                    sorted(priced["peer_market"].dropna().astype(str).unique())
                ),
            }
        )
    return pd.DataFrame(rows).sort_values(
        ["gap_to_oem_benchmark", "n_priced_rows", "pms_category"]
    )


def street_vs_isze(basket: pd.DataFrame, pr00: pd.Series) -> pd.DataFrame:
    b = basket.copy()
    b["peer_street_eur"] = pd.to_numeric(b["peer_street_eur"], errors="coerce")
    priced = b[b["peer_street_eur"].notna() & (b["peer_street_eur"] > 0)].copy()
    if priced.empty:
        return priced
    priced["isze_pn"] = priced["isze_pn"].map(_pn)
    priced["pr00_eur"] = priced["isze_pn"].map(pr00)
    priced["isze_street_eur"] = priced["pr00_eur"] * STREET_FACTOR
    priced["peer_vs_isze_street_pct"] = (
        priced["peer_street_eur"] / priced["isze_street_eur"] - 1.0
    ) * 100.0
    priced["street_factor"] = STREET_FACTOR
    keep = [
        "isze_pn",
        "pms_category",
        "description",
        "peer_market",
        "peer_oem",
        "peer_model",
        "peer_oe_pn",
        "peer_street_eur",
        "pr00_eur",
        "isze_street_eur",
        "peer_vs_isze_street_pct",
        "street_factor",
        "source",
        "status",
    ]
    return priced[[c for c in keep if c in priced.columns]].sort_values(
        ["pms_category", "peer_vs_isze_street_pct"]
    )


def scrape_gaps(scrape: pd.DataFrame) -> pd.DataFrame:
    s = scrape.copy()
    eur = pd.to_numeric(s.get("peer_street_eur"), errors="coerce")
    native = pd.to_numeric(s.get("peer_street_native"), errors="coerce")
    filled = (eur.fillna(0) > 0) | (native.fillna(0) > 0)
    g = s.loc[~filled].copy()
    g["fill_state"] = "not_found"
    return g[
        [
            c
            for c in (
                "isze_pn",
                "pms_category",
                "peer_oem",
                "peer_oe_pn",
                "notes",
                "fill_state",
            )
            if c in g.columns
        ]
    ]


def main() -> None:
    basket = pd.read_csv(BASKET, dtype={"isze_pn": str, "peer_oe_pn": str})
    scrape = pd.read_csv(SCRAPE, dtype={"isze_pn": str, "peer_oe_pn": str})
    ready = readiness(basket)
    pr00 = load_pr00()
    pn = street_vs_isze(basket, pr00)
    gaps = scrape_gaps(scrape)

    DER.mkdir(parents=True, exist_ok=True)
    ready.to_csv(OUT_READY, index=False)
    pn.to_csv(OUT_PN, index=False)

    n_oe = basket["peer_oe_pn"].dropna().astype(str).str.strip()
    n_oe = n_oe[n_oe.ne("")].nunique()
    priced_oe = basket.copy()
    priced_oe["peer_street_eur"] = pd.to_numeric(
        priced_oe["peer_street_eur"], errors="coerce"
    )
    n_priced_oe = priced_oe.loc[
        priced_oe["peer_street_eur"].notna() & (priced_oe["peer_street_eur"] > 0),
        "peer_oe_pn",
    ].nunique()

    summary = {
        "as_of_utc": datetime.now(timezone.utc).isoformat(),
        "unique_oe_mapped": int(n_oe),
        "unique_oe_street_filled": int(n_priced_oe),
        "scrape_gaps": int(len(gaps)),
        "oem_benchmark_cats": ready.loc[
            ready["basis_if_alloc"] == "oem_benchmark", "pms_category"
        ].tolist(),
        "near_gate_cats": ready.loc[
            ready["basis_if_alloc"] == "near_gate", "pms_category"
        ].tolist(),
        "street_factor": STREET_FACTOR,
        "n_pn_street_vs_isze_rows": int(len(pn)),
        "files": {
            "readiness": str(OUT_READY),
            "street_vs_isze": str(OUT_PN),
            "eucon_gap_scan": str(DER / "eucon_comparable_oem_gap_20260810.csv"),
        },
        "notes": [
            "Eucon 2023 COMPARABLE brands present: DAF, Toyota Hilux, Ford Ranger only.",
            "No Mitsubishi L200 / Transit / Sprinter / MAN / Crafter COMPARABLE maps in survey.",
            "Do not invent OE maps or street. FEBI/aftermarket ≠ OEM street.",
            "Ford shop Ranger shoes Product No 2138025 — not proven supersession of 1713904.",
        ],
    }
    OUT_JSON.write_text(json.dumps(summary, indent=2), encoding="utf-8")

    print("=== OEM peer readiness ===")
    print(ready.to_string(index=False))
    print()
    print(
        f"Street filled: {n_priced_oe}/{n_oe} unique OEs | "
        f"oem_benchmark: {summary['oem_benchmark_cats']} | "
        f"near_gate: {summary['near_gate_cats']}"
    )
    print(f"Scrape gaps ({len(gaps)}):")
    if len(gaps):
        print(gaps[["peer_oe_pn", "peer_oem", "pms_category"]].to_string(index=False))
    if len(pn):
        print("\nPeer street vs Isuzu street (PR00×1.785) — extremes:")
        show = pn.dropna(subset=["peer_vs_isze_street_pct"])
        if len(show):
            print(show.head(5)[
                ["isze_pn", "pms_category", "peer_oem", "peer_street_eur",
                 "isze_street_eur", "peer_vs_isze_street_pct"]
            ].round(2).to_string(index=False))
            print("...")
            print(show.tail(5)[
                ["isze_pn", "pms_category", "peer_oem", "peer_street_eur",
                 "isze_street_eur", "peer_vs_isze_street_pct"]
            ].round(2).to_string(index=False))
    print("\nWrote:")
    print(" ", OUT_READY)
    print(" ", OUT_PN)
    print(" ", OUT_JSON)


if __name__ == "__main__":
    main()
