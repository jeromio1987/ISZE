"""
AIM Gap Closer
==============
Suggests L1/L2 classifications for the "Other / review" bucket in IE40
using three signals: description token match, price-band fit, and (reserved)
eQ HIT lookup populated by a separate Chrome pass.

Inputs:
    - IE40 Price list (...PR00_3_level_classified_GPT.xlsx) — source of truth
    - sales_fact.parquet — CY2025 revenue per PN (for ranking by € at stake)

Output:
    - aim_gap_suggestions_YYYYMMDD.csv next to the IE40 file
    - Sorted by CY2025 revenue € desc so highest-impact rows are at top
"""

from __future__ import annotations

import argparse
import math
import re
import sys
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path

import openpyxl
import pandas as pd

_WORKSPACE = Path(__file__).resolve().parents[1] / "workspace"
sys.path.insert(0, str(_WORKSPACE))
from isze_paths import DATA_ROOT, DERIVED_DIR, ISZE_ROOT  # noqa: E402

DEFAULT_IE40 = DATA_ROOT / "IE40 Price list as of 13.03.2026 PR00_3_level_classified_GPT.xlsx"
DEFAULT_SALES = DERIVED_DIR / "sales_fact.parquet"

UNCLASSIFIED_L1 = "Other / review"
DESC_WEIGHT = 0.70
PRICE_WEIGHT = 0.30
BIGRAM_BOOST = 2.5
MIN_TOKEN_LEN = 3
SALES_YEAR = 2025
TOP_N_SUGGESTIONS = 3

TOKEN_RE = re.compile(r"[A-Za-z]+")

# Generic structural / positional tokens that appear in every L2 and carry
# no classification signal. Dropped before scoring.
STOPWORDS = {
    "asm", "kit", "assy", "comp", "set", "sub", "ass",
    "frt", "front", "rr", "rear", "lh", "rh", "left", "right",
    "upr", "upper", "lwr", "lower", "inr", "inner", "otr", "outer",
    "for", "and", "the", "with", "kit;", "wo", "w/o",
}

# Lubricants L2 has no classified peers in IE40 (taxonomy gap), but the
# Lubricants channel is live (IML signed off 8 May 2026). Inject a seed
# vocabulary so fluid/oil/grease items get classified into a real bucket
# instead of being misrouted to Transmission parts.
SYNTHETIC_LUBRICANTS_KEY = "Hardware & consumables||Lubricants"
SYNTHETIC_LUBRICANTS_UNIGRAMS = {
    "oil": 50, "grease": 40, "fluid": 40, "coolant": 30, "antifreeze": 25,
    "lubricant": 30, "lube": 20, "atf": 25, "besco": 35, "shell": 20,
    "clean": 15, "cleaner": 20, "super": 10, "washer": 15, "brake": 10,
    "engine": 8, "transmission": 8, "gear": 8, "hydraulic": 10,
    "diesel": 8, "petrol": 8, "additive": 20, "treatment": 15,
    "synthetic": 15, "mineral": 10, "rust": 10, "spray": 10,
}
SYNTHETIC_LUBRICANTS_BIGRAMS = {
    "engine_oil": 30, "gear_oil": 25, "brake_fluid": 30, "atf_oil": 25,
    "coolant_super": 15, "washer_fluid": 25, "hydraulic_oil": 20,
    "rust_remover": 15, "diesel_additive": 15, "besco_clean": 25,
}
SYNTHETIC_LUBRICANTS_PRICES = {  # observed lubricant price band, € per pack
    "q25": 12.0, "q50": 35.0, "q75": 80.0, "min": 5.0, "max": 250.0,
}


def tokenize(desc: str) -> list[str]:
    if not desc:
        return []
    return [
        t.lower() for t in TOKEN_RE.findall(str(desc))
        if len(t) >= MIN_TOKEN_LEN and t.lower() not in STOPWORDS
    ]


def bigrams(tokens: list[str]) -> list[str]:
    return [f"{a}_{b}" for a, b in zip(tokens, tokens[1:])]


def parse_price(raw) -> float | None:
    if raw is None:
        return None
    s = str(raw).strip().replace(",", ".")
    try:
        return float(s)
    except ValueError:
        return None


def load_ie40(path: Path) -> pd.DataFrame:
    wb = openpyxl.load_workbook(path, read_only=True, data_only=True)
    ws = wb["Sheet1"]
    rows = ws.iter_rows(values_only=True)
    headers = next(rows)
    recs = []
    for r in rows:
        recs.append(r)
    df = pd.DataFrame(recs, columns=headers)
    df["Price_eur"] = df["Price"].apply(parse_price)
    df = df.rename(columns={
        "P/N": "pn",
        "Description": "description",
        "Level 1 Family": "l1",
        "Level 2 Group": "l2",
        "Level 3 Type": "l3",
    })
    return df[["pn", "description", "Price_eur", "l1", "l2", "l3"]]


def load_revenue(sales_path: Path, year: int) -> pd.DataFrame:
    df = pd.read_parquet(sales_path)
    df = df[df["year"] == year]
    rev = (
        df.groupby("part_number", as_index=False)["net_sales_value"]
        .sum()
        .rename(columns={"part_number": "pn", "net_sales_value": "revenue_eur"})
    )
    rev["pn"] = rev["pn"].astype(str)
    return rev


def build_l2_vocab(classified: pd.DataFrame) -> tuple[dict[str, Counter], dict[str, Counter]]:
    """Per-L2 unigram and bigram counts (raw)."""
    uni: dict[str, Counter] = defaultdict(Counter)
    bi: dict[str, Counter] = defaultdict(Counter)
    for _, row in classified.iterrows():
        toks = tokenize(row["description"])
        if not toks:
            continue
        key = f"{row['l1']}||{row['l2']}"
        uni[key].update(toks)
        bi[key].update(bigrams(toks))
    return uni, bi


def compute_idf(vocab: dict[str, Counter]) -> dict[str, float]:
    """IDF over L2 buckets: rare-across-buckets tokens get high weight."""
    n_buckets = len(vocab)
    df = Counter()
    for counter in vocab.values():
        for tok in counter:
            df[tok] += 1
    return {tok: math.log(n_buckets / d) for tok, d in df.items() if d > 0}


def tfidf_vector(counter: Counter, idf: dict[str, float]) -> dict[str, float]:
    """Convert a raw count Counter into a TF-IDF weight dict, L2-normalized."""
    if not counter:
        return {}
    total = sum(counter.values())
    tfidf = {t: (c / total) * idf.get(t, 0.0) for t, c in counter.items()}
    norm = math.sqrt(sum(v * v for v in tfidf.values()))
    if norm == 0:
        return tfidf
    return {t: v / norm for t, v in tfidf.items()}


def build_l2_price_stats(classified: pd.DataFrame) -> dict[str, dict]:
    stats: dict[str, dict] = {}
    for key, grp in classified.groupby([classified["l1"], classified["l2"]]):
        prices = grp["Price_eur"].dropna()
        if len(prices) < 5:
            continue
        k = f"{key[0]}||{key[1]}"
        stats[k] = {
            "q25": prices.quantile(0.25),
            "q50": prices.quantile(0.50),
            "q75": prices.quantile(0.75),
            "min": prices.quantile(0.05),
            "max": prices.quantile(0.95),
        }
    return stats


def desc_score(
    tokens: list[str],
    bi_tokens: list[str],
    l2_uni_tfidf: dict[str, float],
    l2_bi_tfidf: dict[str, float],
    idf_uni: dict[str, float],
    idf_bi: dict[str, float],
) -> float:
    """Cosine-style TF-IDF dot product, with bigram boost."""
    if not tokens:
        return 0.0
    q_uni_raw = Counter(tokens)
    q_bi_raw = Counter(bi_tokens)
    q_total = sum(q_uni_raw.values()) or 1
    q_uni = {t: (c / q_total) * idf_uni.get(t, 0.0) for t, c in q_uni_raw.items()}
    q_bi = {t: c * idf_bi.get(t, 0.0) for t, c in q_bi_raw.items()}
    uni_dot = sum(q_uni.get(t, 0.0) * v for t, v in l2_uni_tfidf.items())
    bi_dot = sum(q_bi.get(t, 0.0) * v for t, v in l2_bi_tfidf.items())
    return uni_dot + BIGRAM_BOOST * bi_dot


def price_score(price: float | None, stats: dict) -> float:
    if price is None or not stats:
        return 0.0
    if stats["q25"] <= price <= stats["q75"]:
        return 1.0
    if price < stats["q25"]:
        span = max(stats["q25"] - stats["min"], 1e-6)
        return max(0.0, 1.0 - (stats["q25"] - price) / span)
    span = max(stats["max"] - stats["q75"], 1e-6)
    return max(0.0, 1.0 - (price - stats["q75"]) / span)


def classify_row(
    desc: str,
    price: float | None,
    uni_tfidf: dict[str, dict[str, float]],
    bi_tfidf: dict[str, dict[str, float]],
    idf_uni: dict[str, float],
    idf_bi: dict[str, float],
    price_stats: dict[str, dict],
) -> list[tuple[str, float, float, float]]:
    tokens = tokenize(desc)
    bi_tokens = bigrams(tokens)
    scores = []
    for key, l2_uni in uni_tfidf.items():
        d = desc_score(tokens, bi_tokens, l2_uni, bi_tfidf.get(key, {}), idf_uni, idf_bi)
        p = price_score(price, price_stats.get(key, {}))
        combined = DESC_WEIGHT * d + PRICE_WEIGHT * p
        if combined > 0:
            scores.append((key, d, p, combined))
    scores.sort(key=lambda x: x[3], reverse=True)
    return scores[:TOP_N_SUGGESTIONS]


def run(ie40_path: Path, sales_path: Path, out_path: Path) -> None:
    print(f"[1/5] Loading IE40 from {ie40_path.name} …")
    ie40 = load_ie40(ie40_path)
    print(f"      {len(ie40):,} total rows")

    classified = ie40[ie40["l1"] != UNCLASSIFIED_L1].copy()
    unclassified = ie40[ie40["l1"] == UNCLASSIFIED_L1].copy()
    print(f"      classified={len(classified):,}, unclassified={len(unclassified):,}")

    print(f"[2/5] Loading CY{SALES_YEAR} revenue from {sales_path.name} …")
    rev = load_revenue(sales_path, SALES_YEAR)
    print(f"      {len(rev):,} PNs with CY{SALES_YEAR} sales")

    unclassified["pn"] = unclassified["pn"].astype(str)
    unclassified = unclassified.merge(rev, on="pn", how="left")
    unclassified["revenue_eur"] = unclassified["revenue_eur"].fillna(0)
    revenue_bearing = unclassified[unclassified["revenue_eur"] > 0]
    print(
        f"      revenue-bearing unclassified: {len(revenue_bearing):,} "
        f"(€{revenue_bearing['revenue_eur'].sum():,.0f})"
    )

    print("[3/5] Building TF-IDF vocab (uni + bigram) + price stats …")
    uni_raw, bi_raw = build_l2_vocab(classified)
    # Inject synthetic Lubricants bucket — no classified peers in IE40
    uni_raw[SYNTHETIC_LUBRICANTS_KEY] = Counter(SYNTHETIC_LUBRICANTS_UNIGRAMS)
    bi_raw[SYNTHETIC_LUBRICANTS_KEY] = Counter(SYNTHETIC_LUBRICANTS_BIGRAMS)
    idf_uni = compute_idf(uni_raw)
    idf_bi = compute_idf(bi_raw)
    uni_tfidf = {k: tfidf_vector(c, idf_uni) for k, c in uni_raw.items()}
    bi_tfidf = {k: tfidf_vector(c, idf_bi) for k, c in bi_raw.items()}
    price_stats = build_l2_price_stats(classified)
    price_stats[SYNTHETIC_LUBRICANTS_KEY] = SYNTHETIC_LUBRICANTS_PRICES
    print(
        f"      {len(uni_tfidf):,} L2 buckets (incl. synthetic Lubricants), "
        f"{len(idf_uni):,} unique unigrams, {len(idf_bi):,} bigrams, "
        f"{len(price_stats):,} buckets with price stats"
    )

    print("[4/5] Scoring unclassified rows …")
    rows_out = []
    for _, row in revenue_bearing.iterrows():
        suggestions = classify_row(
            row["description"], row["Price_eur"],
            uni_tfidf, bi_tfidf, idf_uni, idf_bi, price_stats,
        )
        rec = {
            "pn": row["pn"],
            "description": row["description"],
            "price_eur": row["Price_eur"],
            "revenue_cy25_eur": round(row["revenue_eur"], 2),
            "current_l1": row["l1"],
        }
        for i, (key, d, p, c) in enumerate(suggestions, start=1):
            l1, l2 = key.split("||", 1)
            rec[f"sug{i}_l1"] = l1
            rec[f"sug{i}_l2"] = l2
            rec[f"sug{i}_desc"] = round(d, 4)
            rec[f"sug{i}_price"] = round(p, 4)
            rec[f"sug{i}_combined"] = round(c, 4)
        if len(suggestions) >= 2:
            rec["confidence"] = round(suggestions[0][3] / max(suggestions[1][3], 1e-6), 2)
        elif suggestions:
            rec["confidence"] = 99.0
        else:
            rec["confidence"] = 0.0
        rec["eq_hit"] = ""
        rec["validated"] = ""
        rows_out.append(rec)

    out = pd.DataFrame(rows_out)
    out = out.sort_values("revenue_cy25_eur", ascending=False)
    out.to_csv(out_path, index=False, encoding="utf-8-sig")
    print(f"[5/5] Wrote {len(out):,} rows -> {out_path}")
    print()
    print("TOP 10 BY REVENUE:")
    cols = ["pn", "description", "revenue_cy25_eur", "sug1_l1", "sug1_l2", "sug1_combined", "confidence"]
    print(out[cols].head(10).to_string(index=False))


def main():
    p = argparse.ArgumentParser(description="Suggest AIM classifications for 'Other / review' bucket.")
    p.add_argument("--ie40", type=Path, default=DEFAULT_IE40)
    p.add_argument("--sales", type=Path, default=DEFAULT_SALES)
    p.add_argument(
        "--out",
        type=Path,
        default=DERIVED_DIR / f"aim_gap_suggestions_{datetime.now().strftime('%Y%m%d')}.csv",
    )
    args = p.parse_args()

    if not args.ie40.exists():
        sys.exit(f"ERROR: IE40 not found at {args.ie40}")
    if not args.sales.exists():
        sys.exit(f"ERROR: sales_fact not found at {args.sales}")

    run(args.ie40, args.sales, args.out)


if __name__ == "__main__":
    main()
