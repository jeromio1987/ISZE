"""Brand-quality ceilings and street-premium helpers.

Jerome language: percentages only.
  +30%  = genuine street may sit 30% above the benchmark brand
  FY27 list move (+3% weighted) is separate.

Authority:
  iam_quality_premium_pct.yaml
  04_tools/autodoc_scraper/iam_brand_tiers.csv
"""
from __future__ import annotations

import re
from functools import lru_cache
from pathlib import Path

import pandas as pd
import yaml

ROOT = Path(__file__).resolve().parent
REPO = ROOT.parents[1]
TIERS_CSV = REPO / "04_tools" / "autodoc_scraper" / "iam_brand_tiers.csv"
QUALITY_YAML = ROOT / "iam_quality_premium_pct.yaml"
EUCON_CSV = REPO / "01_data" / "00_derived" / "eucon_price_gap.csv"
CATALOG_CSV = REPO / "01_data" / "00_derived" / "parts_catalog_dimension.csv"


def _norm_brand(name: str) -> str:
    s = re.sub(r"[^A-Z0-9]+", " ", str(name).upper()).strip()
    # common scraper variants
    s = s.replace("FEBI BILSTEIN", "FEBI BILSTEIN")
    s = s.replace("HERTH BUSS JAKOPARTS", "HERTH+BUSS JAKOPARTS")
    s = s.replace("MEAT AMP DORIA", "MEAT DORIA")
    s = s.replace("COOPERSFIAAM FILTERS", "COOPERSFIAAM")
    return s


@lru_cache(maxsize=1)
def load_quality() -> dict:
    return yaml.safe_load(QUALITY_YAML.read_text(encoding="utf-8"))


@lru_cache(maxsize=1)
def brand_tier_map() -> dict[str, int]:
    df = pd.read_csv(TIERS_CSV)
    out: dict[str, int] = {}
    for _, r in df.iterrows():
        out[_norm_brand(r["brand"])] = int(r["tier"])
    return out


def max_premium_pct_for_tier(tier: int) -> int:
    q = load_quality()
    key = q["tier_map"].get(tier) or q["tier_map"]["default"]
    return int(q["max_premium_pct_vs_benchmark"][key])


def _tier_for_brand(name: str) -> int:
    m = brand_tier_map()
    nb = _norm_brand(name)
    if nb in m:
        return m[nb]
    for k, tv in m.items():
        if nb in k or k in nb:
            return tv
    return 1  # unknown / no-name → junk ceiling


def best_tier_for_brands(brands: list[str]) -> tuple[int, str | None]:
    """Highest quality tier among brands (4=best). Unknown → tier 1."""
    if not brands:
        return 1, None
    scored = [(_tier_for_brand(b), b) for b in brands]
    best_t, best_b = max(scored, key=lambda x: x[0])
    return best_t, best_b


def parse_brands(cell) -> list[str]:
    if cell is None or (isinstance(cell, float) and pd.isna(cell)):
        return []
    return [b.strip() for b in str(cell).split(",") if b.strip()]


@lru_cache(maxsize=1)
def category_ceilings_from_eucon() -> pd.DataFrame:
    """Per PMS category: best IAM brand on Eucon rows → max_premium_pct."""
    eu = pd.read_csv(EUCON_CSV, dtype={"pn": str})
    cat = pd.read_csv(CATALOG_CSV, dtype={"part_number": str}, low_memory=False)
    eu = eu.merge(
        cat[["part_number", "pms_category"]].drop_duplicates("part_number"),
        left_on="pn",
        right_on="part_number",
        how="left",
    )
    rows = []
    for cat_name, g in eu.dropna(subset=["pms_category"]).groupby("pms_category"):
        brands: list[str] = []
        for cell in g["Brands_Found"]:
            brands.extend(parse_brands(cell))
        tier, brand = best_tier_for_brands(brands)
        pct = max_premium_pct_for_tier(tier)
        rows.append(
            {
                "cat": cat_name,
                "n_eucon_pns": int(len(g)),
                "best_tier": tier,
                "best_brand": brand,
                "max_premium_pct": pct,
                "basis": "iam_derived",
            }
        )
    return pd.DataFrame(rows)


OEM_PEER_BASKET_CSV = ROOT / "oem_peer_basket.csv"


def apply_ceilings_to_config_block(
    by_category: dict, oem_basket_path: Path | None = None
) -> dict:
    """Merge Eucon-derived ceilings into allocation.policy_premium.by_category.

    Only upgrades basis to iam_derived when Eucon n_pns >= 3 (same bar as min_n).
    Then, if the OEM peer basket has filled peer_street_eur rows, upgrade those
    categories further to oem_benchmark (never invents prices).
    """
    ceilings = category_ceilings_from_eucon()
    out = {k: dict(v) for k, v in by_category.items()}
    for _, r in ceilings.iterrows():
        cat = r["cat"]
        if r["n_eucon_pns"] < 3:
            continue
        if cat not in out:
            continue
        if out[cat].get("basis") == "excluded_blind_spot":
            continue
        pct = int(r["max_premium_pct"])
        out[cat] = {
            "value": 1.0 + pct / 100.0,
            "basis": "iam_derived",
            "max_premium_pct": pct,
            "benchmark_brand": r["best_brand"],
            "benchmark_tier": int(r["best_tier"]),
            "evidence_n_eucon": int(r["n_eucon_pns"]),
        }
    return apply_oem_benchmark_to_config_block(out, path=oem_basket_path)


def load_oem_peer_basket(path: Path | None = None) -> pd.DataFrame:
    """Load PN × peer scaffold. Empty DataFrame if missing."""
    p = Path(path) if path else OEM_PEER_BASKET_CSV
    if not p.is_file():
        return pd.DataFrame()
    df = pd.read_csv(p, dtype={"isze_pn": str, "peer_oe_pn": str})
    if "peer_street_eur" in df.columns:
        df["peer_street_eur"] = pd.to_numeric(df["peer_street_eur"], errors="coerce")
    return df


def load_oem_benchmark_from_basket(path: Path | None = None) -> pd.DataFrame:
    """Category-level oem_benchmark rows from basket where street EUR is filled.

    Returns empty until scrape/map fills peer_street_eur — does not invent prices.
    Premium % is left to policy (brand-quality ceiling) until a measured OE vs
    IAM gap is available; this stub only flips basis + evidence counts.
    """
    df = load_oem_peer_basket(path)
    if df.empty or "peer_street_eur" not in df.columns:
        return pd.DataFrame(
            columns=["cat", "n_priced_peers", "n_isze_pns", "basis", "peer_markets"]
        )
    priced = df[df["peer_street_eur"].notna() & (df["peer_street_eur"] > 0)].copy()
    if priced.empty:
        return pd.DataFrame(
            columns=["cat", "n_priced_peers", "n_isze_pns", "basis", "peer_markets"]
        )
    rows = []
    for cat, g in priced.groupby("pms_category"):
        rows.append(
            {
                "cat": cat,
                "n_priced_peers": int(len(g)),
                "n_isze_pns": int(g["isze_pn"].nunique()),
                "basis": "oem_benchmark",
                "peer_markets": ",".join(sorted(g["peer_market"].dropna().unique())),
            }
        )
    return pd.DataFrame(rows)


def apply_oem_benchmark_to_config_block(
    by_category: dict, path: Path | None = None
) -> dict:
    """Upgrade category basis to oem_benchmark when basket has priced peers.

    Requires >= 3 priced peer rows in the category (same min_n bar). Keeps the
    existing max_premium_pct / value from iam_derived or placeholder — does not
    invent a new % from blank streets.
    """
    oem = load_oem_benchmark_from_basket(path)
    out = {k: dict(v) for k, v in by_category.items()}
    if oem.empty:
        return out
    for _, r in oem.iterrows():
        cat = r["cat"]
        if r["n_priced_peers"] < 3:
            continue
        if cat not in out:
            continue
        if out[cat].get("basis") == "excluded_blind_spot":
            continue
        prev = out[cat]
        pct = int(prev.get("max_premium_pct") or round((float(prev.get("value", 1.3)) - 1) * 100))
        out[cat] = {
            **prev,
            "value": 1.0 + pct / 100.0,
            "basis": "oem_benchmark",
            "max_premium_pct": pct,
            "evidence_n_oem_peers": int(r["n_priced_peers"]),
            "evidence_n_oem_pns": int(r["n_isze_pns"]),
            "oem_peer_markets": r["peer_markets"],
        }
    return out


def oem_readiness_markdown(path: Path | None = None, min_n: int = 3) -> str:
    """Short internal block for alloc summary — priced peers vs oem_benchmark gate."""
    df = load_oem_peer_basket(path)
    if df.empty or "peer_street_eur" not in df.columns:
        return "\n\n### OEM peer readiness\n\nBasket missing — no oem_benchmark gate report.\n"
    priced = df[df["peer_street_eur"].notna() & (df["peer_street_eur"] > 0)]
    rows = []
    for cat, g in priced.groupby("pms_category"):
        n = int(len(g))
        rows.append(
            {
                "cat": cat,
                "n_priced_rows": n,
                "n_oe": int(g["peer_oe_pn"].nunique()),
                "gap": max(0, min_n - n),
                "basis_if_alloc": "oem_benchmark" if n >= min_n else (
                    "near_gate" if n == min_n - 1 else "below_gate"
                ),
            }
        )
    if not rows:
        return "\n\n### OEM peer readiness\n\nNo priced peer streets yet.\n"
    t = pd.DataFrame(rows).sort_values(["gap", "cat"])
    unlocked = t.loc[t["basis_if_alloc"] == "oem_benchmark", "cat"].tolist()
    near = t.loc[t["basis_if_alloc"] == "near_gate", "cat"].tolist()
    lines = [
        "\n\n### OEM peer readiness\n\n",
        f"Gate **n≥{min_n} priced basket rows**/category. "
        f"Unlocked: **{unlocked or 'none'}**. Near gate: **{near or 'none'}**.\n\n",
    ]
    try:
        lines.append(t.to_markdown(index=False))
    except Exception:
        lines.append("```\n" + t.to_string(index=False) + "\n```")
    lines.append("\n")
    return "".join(lines)


# --- LCV / CV OEM peer registry (prices filled when scraped) -----------------

OEM_PEERS = {
    "LCV": {
        "status": "approved",
        "peers": [
            {"brand": "Toyota", "model": "Hilux"},
            {"brand": "Ford", "model": "Ranger"},
            {"brand": "Mitsubishi", "model": "L200"},
        ],
        "basis_when_priced": "oem_benchmark",
        "basket": "oem_peer_basket.csv",
    },
    "CV": {
        "status": "approved",
        "by_market": {
            "IUK": [
                {"brand": "Ford", "model": "Transit", "why": "highest PMS at-risk; UK van/CV IAM overlap"},
                {"brand": "Mercedes-Benz", "model": "Sprinter", "why": "UK CV genuine peer / workshop habit"},
                {"brand": "DAF", "model": "LF/CF class", "why": "UK truck competition; Jerome add-on 2026-08-10"},
            ],
            "GERMANY": [
                {"brand": "Mercedes-Benz", "model": "Sprinter / light truck", "why": "DE defend-heavy; OE street dense"},
                {"brand": "MAN", "model": "TGL/TGM", "why": "light/medium truck peer"},
                {"brand": "VW", "model": "Crafter", "why": "van segment overlap"},
                {"brand": "DAF", "model": "LF/CF class", "why": "DE truck competition; Jerome add-on 2026-08-10"},
            ],
        },
        "pending": {
            "UTI": {"note": "Israel — propose after local scrape; do not blend with UMI"},
            "UMI": {"note": "Israel UMI only for IDS-linked work; separate peer pass"},
        },
        "basis_when_priced": "oem_benchmark",
        "basket": "oem_peer_basket.csv",
    },
    "candidates_not_approved": [
        {"brand": "Iveco", "model": "light CV / Daily", "why": "FY27 incentive MOU mail 2026-04-22; ask before add"},
        {"brand": "Maxus", "model": "LCV-adjacent", "why": "retailer branding (T&M) in weekly briefs only"},
    ],
}
