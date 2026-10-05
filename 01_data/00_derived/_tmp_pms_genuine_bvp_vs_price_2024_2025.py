"""PMS: genuine price ↑ 2024→2025 vs BVP € share ↑ (substitution signal).

Writes:
  01_data/00_derived/pms_genuine_bvp_vs_price_2024_2025.csv
  01_data/90_INBOX/PMS_GENUINE_BVP_SUBSTITUTION_VS_PRICE_2024_2025.md

UTI≠UMI, IUK≠ITUK kept as separate distributor_code rows.
Primary volume = total €; genuine/BVP are mix lenses.
"""
from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(r"C:\Users\jerom\Desktop\claude\ISZE")
DER = ROOT / "01_data" / "00_derived"
INBOX = ROOT / "01_data" / "90_INBOX"

# Classification thresholds (documented in markdown)
PRICE_UP_PCT = 2.0          # genuine ASP or PR00 list ≥ +2%
SHARE_UP_PP = 2.0           # BVP € share ≥ +2 percentage points
SHARE_FLAT_PP = 1.0         # |Δ share| < 1 pp = flat
MIN_TOTAL_EUR_2025 = 5_000  # drop noise cells
MIN_GENUINE_QTY_BOTH = 5    # need genuine qty both years for ASP


def _asp(eur, qty) -> float:
    eur = float(eur) if pd.notna(eur) else 0.0
    qty = float(qty) if pd.notna(qty) else 0.0
    return eur / qty if qty > 0 else np.nan


def build_mix_pairs() -> pd.DataFrame:
    mix = pd.read_csv(DER / "mix_genuine_bvp_pms.csv")
    mix = mix[mix["year"].isin([2024, 2025])].copy()

    # Sanity: keep Israel / UK lanes separate
    codes = set(mix["distributor_code"].astype(str))
    assert "UTI" in codes and "UMI" in codes
    assert "IUK" in codes and "ITUK" in codes

    rows_2024 = mix[mix["year"] == 2024].set_index(
        ["distributor_code", "product_subgroup"]
    )
    rows_2025 = mix[mix["year"] == 2025].set_index(
        ["distributor_code", "product_subgroup"]
    )
    common = rows_2024.index.intersection(rows_2025.index)

    out = []
    for idx in common:
        a = rows_2024.loc[idx]
        b = rows_2025.loc[idx]
        if isinstance(a, pd.DataFrame):
            a = a.iloc[0]
        if isinstance(b, pd.DataFrame):
            b = b.iloc[0]

        g_asp_24 = _asp(a["genuine_eur"], a["genuine_qty"])
        g_asp_25 = _asp(b["genuine_eur"], b["genuine_qty"])
        b_asp_24 = _asp(a["bvp_eur"], a["bvp_qty"])
        b_asp_25 = _asp(b["bvp_eur"], b["bvp_qty"])

        if pd.notna(g_asp_24) and g_asp_24 > 0 and pd.notna(g_asp_25):
            g_asp_yoy_pct = (g_asp_25 / g_asp_24 - 1.0) * 100.0
        else:
            g_asp_yoy_pct = np.nan

        bvp_share_24 = float(a["bvp_share_eur"]) if pd.notna(a["bvp_share_eur"]) else np.nan
        bvp_share_25 = float(b["bvp_share_eur"]) if pd.notna(b["bvp_share_eur"]) else np.nan
        if pd.notna(bvp_share_24) and pd.notna(bvp_share_25):
            bvp_share_yoy_pp = (bvp_share_25 - bvp_share_24) * 100.0
            bvp_share_gain_eur = (bvp_share_25 - bvp_share_24) * float(b["total_eur"] or 0)
        else:
            bvp_share_yoy_pp = np.nan
            bvp_share_gain_eur = np.nan

        out.append(
            {
                "distributor_code": idx[0],
                "product_subgroup": idx[1],
                "product_group": b.get("product_group", a.get("product_group")),
                "product_family": b.get("product_family", a.get("product_family")),
                "product_group_label": b.get(
                    "product_group_label", a.get("product_group_label")
                ),
                "total_eur_2024": round(float(a["total_eur"] or 0), 2),
                "total_eur_2025": round(float(b["total_eur"] or 0), 2),
                "total_qty_2024": float(a["total_qty"] or 0),
                "total_qty_2025": float(b["total_qty"] or 0),
                "genuine_eur_2024": round(float(a["genuine_eur"] or 0), 2),
                "genuine_eur_2025": round(float(b["genuine_eur"] or 0), 2),
                "genuine_qty_2024": float(a["genuine_qty"] or 0),
                "genuine_qty_2025": float(b["genuine_qty"] or 0),
                "bvp_eur_2024": round(float(a["bvp_eur"] or 0), 2),
                "bvp_eur_2025": round(float(b["bvp_eur"] or 0), 2),
                "bvp_qty_2024": float(a["bvp_qty"] or 0),
                "bvp_qty_2025": float(b["bvp_qty"] or 0),
                "genuine_share_eur_2024": (
                    round(1.0 - bvp_share_24, 6) if pd.notna(bvp_share_24) else np.nan
                ),
                "genuine_share_eur_2025": (
                    round(1.0 - bvp_share_25, 6) if pd.notna(bvp_share_25) else np.nan
                ),
                "bvp_share_eur_2024": (
                    round(bvp_share_24, 6) if pd.notna(bvp_share_24) else np.nan
                ),
                "bvp_share_eur_2025": (
                    round(bvp_share_25, 6) if pd.notna(bvp_share_25) else np.nan
                ),
                "bvp_share_eur_yoy_pp": (
                    round(bvp_share_yoy_pp, 3) if pd.notna(bvp_share_yoy_pp) else np.nan
                ),
                "genuine_asp_2024": (
                    round(g_asp_24, 4) if pd.notna(g_asp_24) else np.nan
                ),
                "genuine_asp_2025": (
                    round(g_asp_25, 4) if pd.notna(g_asp_25) else np.nan
                ),
                "genuine_asp_yoy_pct": (
                    round(g_asp_yoy_pct, 3) if pd.notna(g_asp_yoy_pct) else np.nan
                ),
                "bvp_asp_2024": round(b_asp_24, 4) if pd.notna(b_asp_24) else np.nan,
                "bvp_asp_2025": round(b_asp_25, 4) if pd.notna(b_asp_25) else np.nan,
                "bvp_share_gain_eur": (
                    round(bvp_share_gain_eur, 2)
                    if pd.notna(bvp_share_gain_eur)
                    else np.nan
                ),
            }
        )
    return pd.DataFrame(out)


def build_pr00_by_subgroup() -> pd.DataFrame:
    """Network-level PR00 list YoY by product_subgroup (genuine PNs in crossref)."""
    xr = pd.read_csv(DER / "genuine_bvp_crossref.csv", dtype=str)
    xr["genuine_pn"] = xr["genuine_pn"].astype(str).str.strip()
    xr["product_subgroup"] = (
        xr["product_subgroup"].fillna("").str.strip().str.lower()
    )
    pn_sub = xr[["genuine_pn", "product_subgroup"]].drop_duplicates()
    pn_sub = pn_sub[pn_sub["product_subgroup"] != ""]

    pr24 = pd.read_parquet(DER / "pricing_pr00_ie40_2024.parquet")
    pr25 = pd.read_parquet(DER / "pricing_pr00_ie40_2025.parquet")
    pr24["Material"] = pr24["Material"].astype(str).str.strip()
    pr25["Material"] = pr25["Material"].astype(str).str.strip()
    pr = pr24.rename(columns={"Price_EUR": "pr00_2024"})[
        ["Material", "pr00_2024"]
    ].merge(
        pr25.rename(columns={"Price_EUR": "pr00_2025"})[["Material", "pr00_2025"]],
        on="Material",
        how="inner",
    )
    pr = pr[(pr["pr00_2024"] > 0) & (pr["pr00_2025"] > 0)].copy()
    pr["pr00_yoy_pct"] = (pr["pr00_2025"] / pr["pr00_2024"] - 1.0) * 100.0

    pr_sub = pr.merge(pn_sub, left_on="Material", right_on="genuine_pn", how="inner")

    # Volume-weight with 2024 network genuine qty on those PNs
    sf = pd.read_parquet(
        DER / "sales_fact.parquet",
        columns=["part_number", "billed_qty", "year"],
    )
    sf = sf[sf["year"] == 2024].copy()
    sf["part_number"] = sf["part_number"].astype(str).str.strip()
    qty = sf.groupby("part_number", as_index=False)["billed_qty"].sum()
    qty = qty.rename(columns={"billed_qty": "qty_2024_network"})
    pr_sub = pr_sub.merge(qty, left_on="Material", right_on="part_number", how="left")
    pr_sub["qty_2024_network"] = pr_sub["qty_2024_network"].fillna(0.0)

    def _wavg(g: pd.DataFrame) -> pd.Series:
        w = g["qty_2024_network"].to_numpy(dtype=float)
        y = g["pr00_yoy_pct"].to_numpy(dtype=float)
        if w.sum() > 0:
            wavg = float(np.average(y, weights=w))
        else:
            wavg = float(np.median(y)) if len(y) else np.nan
        return pd.Series(
            {
                "pr00_yoy_pct_wavg": round(wavg, 3) if pd.notna(wavg) else np.nan,
                "pr00_yoy_pct_median": round(float(np.median(y)), 3) if len(y) else np.nan,
                "n_genuine_pns_with_pr00": int(g["Material"].nunique()),
                "pr00_weight_qty_2024": float(w.sum()),
            }
        )

    return pr_sub.groupby("product_subgroup", as_index=False).apply(
        _wavg, include_groups=False
    )


def classify(row: pd.Series) -> str:
    """Label substitution / no-switch / other using observed genuine ASP."""
    asp = row["genuine_asp_yoy_pct"]
    share = row["bvp_share_eur_yoy_pp"]
    pr00 = row.get("pr00_yoy_pct_wavg", np.nan)

    # Prefer observed ASP; fall back to PR00 if ASP missing but list moved
    price_up = (pd.notna(asp) and asp >= PRICE_UP_PCT) or (
        pd.isna(asp) and pd.notna(pr00) and pr00 >= PRICE_UP_PCT
    )
    price_down = (pd.notna(asp) and asp <= -PRICE_UP_PCT) or (
        pd.isna(asp) and pd.notna(pr00) and pr00 <= -PRICE_UP_PCT
    )
    share_up = pd.notna(share) and share >= SHARE_UP_PP
    share_down = pd.notna(share) and share <= -SHARE_UP_PP
    share_flat = pd.notna(share) and abs(share) < SHARE_FLAT_PP

    if price_up and share_up:
        return "substitution_signal"  # genuine price ↑ + BVP share ↑
    if price_up and share_flat:
        return "price_up_share_flat"  # no switch
    if price_up and share_down:
        return "price_up_genuine_held"  # price ↑ but BVP lost share
    if (not price_up) and (not price_down) and share_up:
        return "share_up_price_flat"
    if price_down and share_up:
        return "price_down_share_up"
    if price_down and share_down:
        return "price_down_share_down"
    return "other"


def main() -> None:
    df = build_mix_pairs()
    pr00 = build_pr00_by_subgroup()
    df = df.merge(pr00, on="product_subgroup", how="left")

    # Size / ASP eligibility
    df["eligible"] = (
        (df["total_eur_2025"] >= MIN_TOTAL_EUR_2025)
        & (df["genuine_qty_2024"] >= MIN_GENUINE_QTY_BOTH)
        & (df["genuine_qty_2025"] >= MIN_GENUINE_QTY_BOTH)
    )

    # Primary price signal = observed genuine ASP; list as secondary
    df["price_up_asp"] = df["genuine_asp_yoy_pct"] >= PRICE_UP_PCT
    df["price_up_pr00"] = df["pr00_yoy_pct_wavg"] >= PRICE_UP_PCT
    df["bvp_share_up"] = df["bvp_share_eur_yoy_pp"] >= SHARE_UP_PP

    df["signal"] = df.apply(classify, axis=1)

    # Rank within substitution: by EUR of share gain (positive first)
    df["rank_substitution_eur"] = np.nan
    mask = (df["signal"] == "substitution_signal") & df["eligible"]
    ranked = df.loc[mask].sort_values("bvp_share_gain_eur", ascending=False)
    df.loc[ranked.index, "rank_substitution_eur"] = range(1, len(ranked) + 1)

    # Column order
    cols = [
        "distributor_code",
        "product_group_label",
        "product_group",
        "product_family",
        "product_subgroup",
        "signal",
        "eligible",
        "rank_substitution_eur",
        "total_eur_2024",
        "total_eur_2025",
        "total_qty_2024",
        "total_qty_2025",
        "genuine_eur_2024",
        "genuine_eur_2025",
        "genuine_qty_2024",
        "genuine_qty_2025",
        "bvp_eur_2024",
        "bvp_eur_2025",
        "bvp_qty_2024",
        "bvp_qty_2025",
        "genuine_share_eur_2024",
        "genuine_share_eur_2025",
        "bvp_share_eur_2024",
        "bvp_share_eur_2025",
        "bvp_share_eur_yoy_pp",
        "bvp_share_gain_eur",
        "genuine_asp_2024",
        "genuine_asp_2025",
        "genuine_asp_yoy_pct",
        "bvp_asp_2024",
        "bvp_asp_2025",
        "pr00_yoy_pct_wavg",
        "pr00_yoy_pct_median",
        "n_genuine_pns_with_pr00",
        "pr00_weight_qty_2024",
        "price_up_asp",
        "price_up_pr00",
        "bvp_share_up",
    ]
    df = df[cols].sort_values(
        ["signal", "bvp_share_gain_eur"], ascending=[True, False]
    )

    out_csv = DER / "pms_genuine_bvp_vs_price_2024_2025.csv"
    df.to_csv(out_csv, index=False)

    # ── Markdown for Jerome ────────────────────────────────────────────────
    elig = df[df["eligible"]].copy()
    sub = elig[elig["signal"] == "substitution_signal"].sort_values(
        "bvp_share_gain_eur", ascending=False
    )
    flat = elig[elig["signal"] == "price_up_share_flat"].sort_values(
        "total_eur_2025", ascending=False
    )
    held = elig[elig["signal"] == "price_up_genuine_held"].sort_values(
        "total_eur_2025", ascending=False
    )

    sub_eur = float(sub["bvp_share_gain_eur"].sum()) if len(sub) else 0.0
    n_elig = len(elig)
    n_sub = len(sub)
    n_flat = len(flat)
    n_held = len(held)

    # Family rollup of substitution EUR
    fam = (
        sub.groupby(["product_group_label", "product_subgroup"], as_index=False)
        .agg(
            n_dbs=("distributor_code", "nunique"),
            bvp_share_gain_eur=("bvp_share_gain_eur", "sum"),
            total_eur_2025=("total_eur_2025", "sum"),
            median_asp_yoy=("genuine_asp_yoy_pct", "median"),
            median_share_pp=("bvp_share_eur_yoy_pp", "median"),
        )
        .sort_values("bvp_share_gain_eur", ascending=False)
    )

    def _fmt_eur(x: float) -> str:
        if abs(x) >= 1_000_000:
            return f"EUR {x/1_000_000:.2f}M"
        if abs(x) >= 1_000:
            return f"EUR {x/1_000:.1f}k"
        return f"EUR {x:.0f}"

    lines = []
    lines.append("# PMS genuine price vs BVP mix — 2024 → 2025")
    lines.append("")
    lines.append("**Verdict:** On PMS families, some distributor×category cells show genuine "
                 "selling prices rising while BVP takes a larger share of the same basket — "
                 "a substitution signal. Others show genuine prices rising with little or no "
                 "BVP share gain (no switch). This is association, not proof of cause.")
    lines.append("")
    lines.append("## What was measured")
    lines.append("")
    lines.append("- Grain: distributor × PMS subgroup (filters, brakes, clutch, etc.), "
                 "calendar 2024 vs 2025.")
    lines.append("- Volume lens: **total billed €** in that cell. Genuine and BVP are the "
                 "**mix** on top of that total.")
    lines.append("- Price lenses: (1) observed genuine average selling price "
                 "(genuine € ÷ genuine qty from the mix file); "
                 "(2) official IE40 list (PR00) YoY on genuine part numbers in the crossref, "
                 "weighted by 2024 network qty — same list for all distributors.")
    lines.append("- BVP share gain in € = (BVP € share 2025 − BVP € share 2024) × total € 2025. "
                 "That is the euro that moved into BVP **because the mix changed**, not the "
                 "full BVP euro growth (which also includes basket growth).")
    lines.append("- Israel: UTI and UMI stay separate. UK: IUK and ITUK stay separate.")
    lines.append("- Eligible cells: ≥ EUR 5k total in 2025 and ≥ 5 genuine units in both years "
                 "(so ASP is usable).")
    lines.append(f"- Thresholds: genuine ASP (or PR00 fallback) ≥ +{PRICE_UP_PCT:.0f}%; "
                 f"BVP € share ≥ +{SHARE_UP_PP:.0f} pp for “up”; "
                 f"|Δ share| < {SHARE_FLAT_PP:.0f} pp for “flat”.")
    lines.append("")
    lines.append("## Counts (eligible cells only)")
    lines.append("")
    lines.append(f"- Eligible distributor×subgroup cells with both years: **{n_elig}**")
    lines.append(f"- Substitution signal (genuine price ↑ and BVP share ↑): **{n_sub}** "
                 f"— combined BVP-share-gain euro **{_fmt_eur(sub_eur)}**")
    lines.append(f"- Genuine price ↑, BVP share flat: **{n_flat}** (no switch)")
    lines.append(f"- Genuine price ↑, BVP share down: **{n_held}** (genuine held mix)")
    lines.append("")

    lines.append("## Top substitution signals")
    lines.append("")
    if sub.empty:
        lines.append("No eligible cells met both thresholds.")
    else:
        lines.append("| Rank | Distributor | Family / subgroup | Genuine ASP YoY | "
                     "BVP € share YoY | BVP share-gain € | Total € 2025 |")
        lines.append("|---:|---|---|---:|---:|---:|---:|")
        for i, r in enumerate(sub.head(15).itertuples(index=False), 1):
            fam_lab = f"{r.product_group_label} / {r.product_subgroup}"
            lines.append(
                f"| {i} | {r.distributor_code} | {fam_lab} | "
                f"{r.genuine_asp_yoy_pct:+.1f}% | {r.bvp_share_eur_yoy_pp:+.1f} pp | "
                f"{_fmt_eur(r.bvp_share_gain_eur)} | {_fmt_eur(r.total_eur_2025)} |"
            )
    lines.append("")

    lines.append("## Same signal, rolled up by subgroup")
    lines.append("")
    if fam.empty:
        lines.append("n/a")
    else:
        lines.append("| Family / subgroup | DBs with signal | Median ASP YoY | "
                     "Median BVP share YoY | Sum of share-gain € |")
        lines.append("|---|---:|---:|---:|---:|")
        for r in fam.head(12).itertuples(index=False):
            lines.append(
                f"| {r.product_group_label} / {r.product_subgroup} | {r.n_dbs} | "
                f"{r.median_asp_yoy:+.1f}% | {r.median_share_pp:+.1f} pp | "
                f"{_fmt_eur(r.bvp_share_gain_eur)} |"
            )
    lines.append("")

    lines.append("## Price up, BVP share flat (no switch) — largest baskets")
    lines.append("")
    if flat.empty:
        lines.append("None in the eligible set.")
    else:
        lines.append("| Distributor | Family / subgroup | Genuine ASP YoY | "
                     "BVP € share YoY | Total € 2025 |")
        lines.append("|---|---|---:|---:|---:|")
        for r in flat.head(10).itertuples(index=False):
            fam_lab = f"{r.product_group_label} / {r.product_subgroup}"
            lines.append(
                f"| {r.distributor_code} | {fam_lab} | "
                f"{r.genuine_asp_yoy_pct:+.1f}% | {r.bvp_share_eur_yoy_pp:+.1f} pp | "
                f"{_fmt_eur(r.total_eur_2025)} |"
            )
    lines.append("")

    lines.append("## Confounds — read this before acting")
    lines.append("")
    lines.append("- **Catalogue expansion:** a new BVP part entering the basket raises BVP "
                 "share even if nobody switched off an existing genuine line. Crossref pairs "
                 "help, but this cut does not require a paired switch.")
    lines.append("- **SPA / commercial programmes:** a SPA or stock push can move mix without "
                 "a list-price story.")
    lines.append("- **Stock and timing:** year-end stocking, one large VOR order, or a delayed "
                 "shipment can move ASP and share in a single cell.")
    lines.append("- **Mix inside the cell:** genuine ASP is an average across part numbers. "
                 "A shift toward dearer genuine SKUs looks like a price rise even if each "
                 "list price was flat.")
    lines.append("- **PR00 is network list, not dealer invoice:** the observed ASP is closer "
                 "to what was billed; PR00 is the official IE40 list change on genuine PNs.")
    lines.append("- **Correlation ≠ causation:** price ↑ with BVP share ↑ is a signal to "
                 "investigate, not a closed case that the price rise caused the switch.")
    lines.append("")
    lines.append("## Files")
    lines.append("")
    lines.append(f"- Detail CSV: `{out_csv}`")
    lines.append("- Mix source: `01_data/00_derived/mix_genuine_bvp_pms.csv`")
    lines.append("- List prices: `pricing_pr00_ie40_2024.parquet` / "
                 "`pricing_pr00_ie40_2025.parquet`")
    lines.append("- Crossref: `01_data/00_derived/genuine_bvp_crossref.csv`")
    lines.append("")

    md_path = INBOX / "PMS_GENUINE_BVP_SUBSTITUTION_VS_PRICE_2024_2025.md"
    md_path.write_text("\n".join(lines) + "\n", encoding="utf-8")

    print("WROTE", out_csv)
    print("WROTE", md_path)
    print("eligible", n_elig, "substitution", n_sub, "share_gain_eur", round(sub_eur, 2))
    print("--- TOP 10 ---")
    if not sub.empty:
        for r in sub.head(10).itertuples(index=False):
            print(
                f"{r.distributor_code:12} {r.product_subgroup:22} "
                f"ASP {r.genuine_asp_yoy_pct:+6.1f}%  "
                f"share {r.bvp_share_eur_yoy_pp:+6.1f}pp  "
                f"gain {_fmt_eur(r.bvp_share_gain_eur):>12}  "
                f"tot {_fmt_eur(r.total_eur_2025)}"
            )


if __name__ == "__main__":
    main()
