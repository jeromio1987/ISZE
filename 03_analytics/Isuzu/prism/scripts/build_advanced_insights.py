#!/usr/bin/env python3
"""
Advanced sales-intelligence layer — three analyses on the real sales_fact, all
numbers derived from ISZE/Data/derived/sales_fact.parquet (no fabricated values).

  #4  Demand volatility / intermittency  (Syntetos-Boylan ADI x CV^2 quadrants)
  #5  VOR willingness-to-pay             (same-PN ASP: expedited vs standard)
  #6  Competitor leakage band            (INFERRED — under-service gap, never a fact)

Outputs:
  Data/derived/demand_classification.csv
  Data/derived/vor_willingness_to_pay.csv
  Data/derived/leakage_band.csv
  Data/derived/insights/*.png   (charts)

Reuses PRISM's own loaders so distributor mapping == the rest of the pipeline.
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

PRISM_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PRISM_ROOT))

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

from config import DERIVED_DIR  # noqa: E402
from modules.strategic_build import load_sales_tagged  # noqa: E402

OUT_IMG = DERIVED_DIR / "insights"
OUT_IMG.mkdir(parents=True, exist_ok=True)

FOCUS = "ITUK"  # default distributor for single-distributor charts

# Syntetos-Boylan cut points
ADI_CUT = 1.32
CV2_CUT = 0.49


def _clean(df: pd.DataFrame) -> pd.DataFrame:
    """Positive billed lines only; drop credit notes and zero/neg qty."""
    df = df.copy()
    df = df[(df["billed_qty"] > 0) & (df["net_sales_value"] > 0)]
    df = df[df["year"].between(2023, 2025)]
    return df


# ───────────────────────── #4 demand classification ─────────────────────────
def build_demand_classification(sales: pd.DataFrame) -> pd.DataFrame:
    df = _clean(sales)
    # period index = year*12 + month over the 36-month window
    df["period"] = (df["year"].astype(int) - 2023) * 12 + df["month"].astype(int)
    n_periods = 36

    grp = df.groupby(["distributor_code", "part_number"])
    rows = []
    for (dist, pn), g in grp:
        monthly = g.groupby("period")["billed_qty"].sum()
        n_nonzero = int((monthly > 0).sum())
        if n_nonzero < 2:
            continue  # need >=2 demand events to characterise interval/variation
        adi = n_periods / n_nonzero
        sizes = monthly[monthly > 0].values
        mean_size = sizes.mean()
        cv2 = float((sizes.std(ddof=0) / mean_size) ** 2) if mean_size > 0 else 0.0

        lumpy = adi >= ADI_CUT
        erratic = cv2 >= CV2_CUT
        if not lumpy and not erratic:
            cls, rec = "smooth", "JIT / minimal stock — forecastable"
        elif not lumpy and erratic:
            cls, rec = "erratic", "Safety stock for size spikes"
        elif lumpy and not erratic:
            cls, rec = "intermittent", "Reorder point + buffer"
        else:
            cls, rec = "lumpy", "Make-to-order / consignment — do NOT JIT"

        rows.append({
            "distributor_code": dist,
            "part_number": pn,
            "adi": round(adi, 3),
            "cv2": round(cv2, 3),
            "n_demand_months": n_nonzero,
            "total_qty": int(g["billed_qty"].sum()),
            "total_revenue_eur": round(float(g["net_sales_value"].sum()), 2),
            "demand_class": cls,
            "stocking_reco": rec,
        })
    return pd.DataFrame(rows)


def chart_demand(dc: pd.DataFrame) -> None:
    sub = dc[dc["distributor_code"] == FOCUS].copy()
    if sub.empty:
        return
    colors = {"smooth": "#2ca02c", "erratic": "#ff7f0e",
              "intermittent": "#1f77b4", "lumpy": "#d62728"}
    fig, ax = plt.subplots(figsize=(9, 6.5))
    for cls, c in colors.items():
        s = sub[sub["demand_class"] == cls]
        ax.scatter(s["adi"], s["cv2"], s=np.sqrt(s["total_revenue_eur"].clip(lower=1)) * 1.2,
                   alpha=0.45, color=c, label=f"{cls} ({len(s)})", edgecolors="none")
    ax.axvline(ADI_CUT, ls="--", color="grey", lw=1)
    ax.axhline(CV2_CUT, ls="--", color="grey", lw=1)
    ax.set_xlabel("ADI  (avg months between orders → higher = more intermittent)")
    ax.set_ylabel("CV²  (order-size variability → higher = more erratic)")
    ax.set_title(f"{FOCUS} — demand DNA per part (bubble = revenue)\nSyntetos-Boylan quadrants")
    ax.set_xlim(left=0.8)
    ax.legend(title="class (n parts)", loc="upper right")
    fig.tight_layout()
    fig.savefig(OUT_IMG / "demand_quadrant.png", dpi=120)
    plt.close(fig)

    # revenue share by class, top distributors
    piv = (dc.pivot_table(index="distributor_code", columns="demand_class",
                          values="total_revenue_eur", aggfunc="sum", fill_value=0))
    piv["__tot"] = piv.sum(axis=1)
    piv = piv.sort_values("__tot", ascending=False).head(12).drop(columns="__tot")
    pct = piv.div(piv.sum(axis=1), axis=0) * 100
    order = [c for c in ["smooth", "erratic", "intermittent", "lumpy"] if c in pct.columns]
    fig, ax = plt.subplots(figsize=(10, 6))
    bottom = np.zeros(len(pct))
    for cls in order:
        ax.bar(pct.index, pct[cls], bottom=bottom, label=cls, color=colors[cls])
        bottom += pct[cls].values
    ax.set_ylabel("% of revenue")
    ax.set_title("Revenue mix by demand class — top 12 distributors\n(red/blue heavy = stockout & VOR exposure)")
    ax.legend(ncol=4, loc="lower center", bbox_to_anchor=(0.5, -0.22))
    plt.xticks(rotation=45, ha="right")
    fig.tight_layout()
    fig.savefig(OUT_IMG / "demand_revenue_mix.png", dpi=120)
    plt.close(fig)


# ───────────────────────── #5 VOR willingness-to-pay ────────────────────────
def build_vor_wtp(sales: pd.DataFrame) -> pd.DataFrame:
    df = _clean(sales)
    df["bucket"] = np.where(df["is_vor_urgent"], "expedited", "standard")
    g = (df.groupby(["distributor_code", "part_number", "bucket"])
           .agg(qty=("billed_qty", "sum"), rev=("net_sales_value", "sum"))
           .reset_index())
    g["asp"] = g["rev"] / g["qty"]
    piv = g.pivot_table(index=["distributor_code", "part_number"],
                        columns="bucket", values=["asp", "qty", "rev"]).reset_index()
    piv.columns = ["_".join([c for c in col if c]).strip("_") for col in piv.columns]
    # need both buckets present for same PN/distributor
    need = ["asp_expedited", "asp_standard", "qty_expedited", "rev_expedited"]
    for c in need:
        if c not in piv.columns:
            piv[c] = np.nan
    paired = piv.dropna(subset=["asp_expedited", "asp_standard"]).copy()
    paired = paired[paired["asp_standard"] > 0]
    paired["premium_pct"] = (paired["asp_expedited"] - paired["asp_standard"]) / paired["asp_standard"]
    paired["expedited_revenue_eur"] = paired["rev_expedited"]
    # money on the table if expedited had been priced at +10pp vs standard
    paired["uplift_at_plus10pp_eur"] = (
        paired["qty_expedited"] * paired["asp_standard"] * 0.10
    )
    return paired.sort_values("expedited_revenue_eur", ascending=False)


def chart_vor(wtp: pd.DataFrame) -> None:
    if wtp.empty:
        return
    fig, ax = plt.subplots(figsize=(9, 5.5))
    prem = wtp["premium_pct"].clip(-0.5, 1.0) * 100
    ax.hist(prem, bins=40, color="#1f77b4", alpha=0.8)
    ax.axvline(0, color="red", ls="--", lw=1.5, label="zero premium (cost eaten)")
    med = wtp["premium_pct"].median() * 100
    ax.axvline(med, color="green", ls="-", lw=1.5, label=f"median {med:.1f}%")
    ax.set_xlabel("Expedited-vs-standard ASP premium (%) per part")
    ax.set_ylabel("# part/distributor pairs")
    ax.set_title("Are we charging for speed?\nSame-PN price premium on VOR/urgent vs standard")
    ax.legend()
    fig.tight_layout()
    fig.savefig(OUT_IMG / "vor_premium_dist.png", dpi=120)
    plt.close(fig)


# ───────────────────────── #6 leakage band (INFERRED) ───────────────────────
def build_leakage_band() -> pd.DataFrame:
    rec = pd.read_csv(DERIVED_DIR / "capture_recovery_model.csv")
    # under_service = demand exists, not substituted to BVP, not a catalog gap
    # => most-likely served by independent aftermarket / OE competitor (INFERRED)
    g = (rec.groupby(["distributor_code", "gap_type"])["gap_revenue_at_genuine"]
            .sum().reset_index())
    piv = g.pivot_table(index="distributor_code", columns="gap_type",
                        values="gap_revenue_at_genuine", fill_value=0).reset_index()
    for c in ["substitution", "under_service", "catalog_gap"]:
        if c not in piv.columns:
            piv[c] = 0.0
    piv = piv.rename(columns={"under_service": "leakage_band_eur"})
    piv["total_gap_eur"] = piv[["substitution", "leakage_band_eur", "catalog_gap"]].sum(axis=1)
    return piv.sort_values("leakage_band_eur", ascending=False)


def chart_leakage(lb: pd.DataFrame) -> None:
    sub = lb[lb["total_gap_eur"] > 0].head(12).iloc[::-1]
    if sub.empty:
        return
    fig, ax = plt.subplots(figsize=(10, 6))
    ax.barh(sub["distributor_code"], sub["substitution"], color="#ff7f0e", label="substitution (to BVP)")
    ax.barh(sub["distributor_code"], sub["leakage_band_eur"], left=sub["substitution"],
            color="#d62728", label="leakage band (INFERRED → competitor)")
    ax.barh(sub["distributor_code"], sub["catalog_gap"],
            left=sub["substitution"] + sub["leakage_band_eur"], color="#7f7f7f", label="catalog gap")
    ax.set_xlabel("€ gap at genuine ASP (latest year)")
    ax.set_title("Capture gap decomposition — red band is INFERRED leakage, not measured")
    ax.legend()
    fig.tight_layout()
    fig.savefig(OUT_IMG / "leakage_decomposition.png", dpi=120)
    plt.close(fig)


def eur(x: float) -> str:
    return f"€{x:,.0f}"


def main() -> int:
    print(">> loading sales (PRISM loaders) …", flush=True)
    sales = load_sales_tagged()

    print(">> #4 demand classification …", flush=True)
    dc = build_demand_classification(sales)
    dc.to_csv(DERIVED_DIR / "demand_classification.csv", index=False)
    chart_demand(dc)

    print(">> #5 VOR willingness-to-pay …", flush=True)
    wtp = build_vor_wtp(sales)
    wtp.to_csv(DERIVED_DIR / "vor_willingness_to_pay.csv", index=False)
    chart_vor(wtp)

    print(">> #6 leakage band …", flush=True)
    lb = build_leakage_band()
    lb.to_csv(DERIVED_DIR / "leakage_band.csv", index=False)
    chart_leakage(lb)

    # ── headline numbers (all real, from this run) ──
    print("\n================ HEADLINES (real, this run) ================")
    foc = dc[dc["distributor_code"] == FOCUS]
    if not foc.empty:
        rev_by_cls = foc.groupby("demand_class")["total_revenue_eur"].sum()
        tot = rev_by_cls.sum()
        print(f"\n[#4] {FOCUS}: {len(foc)} parts classified, {eur(tot)} revenue")
        for cls in ["smooth", "erratic", "intermittent", "lumpy"]:
            v = rev_by_cls.get(cls, 0.0)
            print(f"     {cls:13s} {eur(v):>14s}  ({v/tot*100:4.1f}% of rev)")
        lumpy_rev = rev_by_cls.get("lumpy", 0) + rev_by_cls.get("intermittent", 0)
        print(f"     -> {eur(lumpy_rev)} ({lumpy_rev/tot*100:.0f}%) in hard-to-stock demand")

    if not wtp.empty:
        med = wtp["premium_pct"].median() * 100
        zero_or_neg = wtp[wtp["premium_pct"] <= 0.01]
        exp_rev_total = wtp["expedited_revenue_eur"].sum()
        zero_rev = zero_or_neg["expedited_revenue_eur"].sum()
        uplift = wtp["uplift_at_plus10pp_eur"].sum()
        print(f"\n[#5] {len(wtp)} PN/distributor pairs sold BOTH expedited & standard")
        print(f"     median VOR price premium: {med:.1f}%")
        print(f"     expedited revenue priced at ZERO/neg premium: {eur(zero_rev)} "
              f"of {eur(exp_rev_total)} ({zero_rev/exp_rev_total*100:.0f}%)")
        print(f"     theoretical uplift if expedited repriced +10pp: {eur(uplift)} "
              f"(ASSUMPTION, not a forecast)")

    if not lb.empty:
        leak = lb["leakage_band_eur"].sum()
        subst = lb["substitution"].sum()
        print(f"\n[#6] INFERRED leakage band (under-service gap): {eur(leak)}")
        print(f"     substitution-to-BVP gap (measured): {eur(subst)}")
        print("     NB: leakage is an inference, NOT a measured competitor figure — do not quote externally.")

    print(f"\nCharts -> {OUT_IMG}")
    print("CSVs   -> demand_classification.csv, vor_willingness_to_pay.csv, leakage_band.csv")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
