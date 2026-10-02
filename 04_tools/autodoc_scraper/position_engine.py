"""ISZE vs IAM quality-positioning engine.

Numbers live here. HTML renderers must not recompute proposed prices, bands,
or actions — only stacked share-of-total is allowed in the browser.

Positioning is NOT “be 20% dearer than the cheapest listing.”
It depends on (1) IAM brand quality tier, (2) product-type tightness,
(3) captive vs competitive, (4) system completeness when it can be inferred.

Per-DB books from the operating-dashboard REGISTRY (sold_to lists).
Never blend UMI 1797 with UTI 1799, or ITUK 2575 with IUK 2574.
GERMANY (ISD) 2516+601 and PORTUGAL (Imotors) 519+92 are one distributor each.
Sign: delta_pct = (IAM − ISZE) / ISZE. Positive = ISZE cheaper.
"""
from __future__ import annotations

import re
from pathlib import Path

import pandas as pd

SCRIPT_DIR = Path(__file__).resolve().parent
ISZE = SCRIPT_DIR.parents[1]
DERIVED = ISZE / "01_data" / "00_derived"
DEFAULT_TIER_CSV = SCRIPT_DIR / "iam_brand_tiers.csv"
PMS_INTERVALS_CSV = SCRIPT_DIR / "pms_intervals.csv"

SOLD_TO_UMI = 1797
NOT_UTI = 1799
CY = 2025
GBP_EUR = 1.17
SEK_EUR = 0.089
KS_PLACEHOLDER_GBP = 2.00

# Mirrors ISZE\04_tools\db_operating_dashboard\build_ledger.py REGISTRY.
# Aliases: ISD → GERMANY, IMOTORS → PORTUGAL. Keys are distributor_code.
DB_REGISTRY = {
    "UMI": dict(
        sold_to=[1797], display="Universal Motors Israel",
        short="UMI", country="Israel", gps_label="UMI",
        not_blend="not UTI sold-to 1799 (shared payer — split at sold_to)",
        sold_to_note="1797 only",
    ),
    "ITUK": dict(
        sold_to=[2575], display="Isuzu Truck UK",
        short="ITUK", country="United Kingdom", gps_label="ITUK",
        not_blend="not IUK sold-to 2574 (UK LCV — separate book)",
        sold_to_note="2575 only",
    ),
    "GERMANY": dict(
        sold_to=[2516, 601], display="Isuzu Sales Deutschland",
        short="ISD", country="Germany", gps_label="ISD",
        not_blend="ISD only — 2516 and 601 are this distributor, not other DBs",
        sold_to_note="2516 + 601 (one ISD book, two SAP codes)",
    ),
    "PORTUGAL": dict(
        sold_to=[519, 92], display="I-Motors",
        short="Imotors", country="Portugal", gps_label="Imotors",
        not_blend="Imotors only — 519 and 92 are this distributor, not other DBs",
        sold_to_note="519 + 92 (one Imotors book, two SAP codes)",
    ),
}
DB_ALIASES = {
    "UMI": "UMI",
    "ITUK": "ITUK",
    "ISD": "GERMANY",
    "GERMANY": "GERMANY",
    "IMOTORS": "PORTUGAL",
    "I-MOTORS": "PORTUGAL",
    "PORTUGAL": "PORTUGAL",
}


def resolve_db(key: str) -> str:
    k = (key or "").strip().upper().replace(" ", "")
    if k not in DB_ALIASES:
        known = ", ".join(sorted(DB_ALIASES))
        raise ValueError(f"Unknown DB key {key!r}. Use one of: {known}")
    return DB_ALIASES[k]

# Ladder authority: iam_quality_premium_pct.yaml + pricing engine BRAND_TIERS.
CEILING_PCT = {4: 30, 3: 60, 2: 150, 1: 250}
QUALITY_TIERS = {3, 4}

# Channel MARKUP (not gross margin). Canonical pricing-engine rule — edit here.
# ISZE net (PR00) × (1 + DB_MARKUP) = DB sell
# DB sell × (1 + DLR_MARKUP) = DLR sell = projected retail
# No extra retail markup exists in local files.
#
# Source (already in files — not invented 20/25/30):
#   ISZE\03_analytics\isze_pricing\config.yaml
#     formula.street_factor: 1.785          # 1.40 * 1.275
#     comment: genuine [channel] = list x DB margin x dealer margin
#   ISZE\03_analytics\isze_pricing\iam_quality_premium_pct.yaml  as_of 2026-08-10
#     street_basis: "PR00_EUR × 1.785 vs IAM retail (channel rule)"
#   ISZE\01_data\92_archive\price_pages_retired_2026-10-02\ISZE_Aftermarket_Live_Pricing_Dashboard.html (retired 2026-10-02)
#     distributor_uplift: 1.4 / dealer_uplift: 1.275
#   ISZE\03_analytics\isze_pricing\OEM_PEERS.md
#     PR00 × 1.40 × 1.275 = ×1.785
#
# Do NOT use iam_scoring.py db_gm=0.37 / dlr_gm=0.25 (GM divide: PR00/(1−gm)).
# Do NOT use enrich_chain_pricing.py --db-gm 0.40 --dlr-gm 0.275 as GM either:
#   that is ÷(1−gm), not ×1.40 × 1.275.
# Working channel assumption for comparison — not observed UMI SPA terms.
DB_MARKUP = 0.40
DLR_MARKUP = 0.275
DB_FACTOR = 1.0 + DB_MARKUP       # 1.40
DLR_FACTOR = 1.0 + DLR_MARKUP     # 1.275
CHANNEL_FACTOR = round(DB_FACTOR * DLR_FACTOR, 3)  # 1.785 as in config.yaml
CHANNEL_ORIGIN = "local_file"  # not a labelled assumption
CHANNEL_SOURCE_FILE = r"ISZE\03_analytics\isze_pricing\config.yaml"
CHANNEL_SOURCE_AS_OF = "config.yaml v1.0.0 · iam_quality_premium_pct.yaml as_of 2026-08-10"
CHANNEL_CROSS_CHECK = (
    r"ISZE\01_data\92_archive\price_pages_retired_2026-10-02\ISZE_Aftermarket_Live_Pricing_Dashboard.html "
    "(distributor_uplift 1.4, dealer_uplift 1.275); "
    r"ISZE\03_analytics\isze_pricing\OEM_PEERS.md"
)

POINT_ISZE = "ISZE → DB (net, PR00 IE40)"
POINT_KS = "IAM trade (KS International, ex-VAT)"
POINT_MEK = "IAM retail (Mekonomen.se)"
POINT_EUCON = "IAM online (Autodoc DE/NO, PartsPool 29 Mar 2026) — not the 2023 UK workshop survey"

# Product-type tightness: multiplier on T3/T4 ceilings only.
# Pads are the competitive extreme (UMI genuine pad capture ~4%, total ~9% CY2025).
# T1/T2 ceilings are not tightened — unmapped / no-name brands do not compress ISZE.
FAMILY_TIGHTNESS = {
    "brake_pad": 0.50,
    "brake_rotor": 0.60,
    "brake_shoe": 0.60,
    "brake_drum": 0.60,
    "clutch_disc": 0.55,
    "clutch_kit": 0.70,
    "clutch_pressure_plate": 0.70,
    "fuel_filter": 0.80,
    "air_filter": 0.85,
    "blower_filter": 0.85,
    "oil_filter": 1.00,
    "lighting": 1.00,
    "body": 1.00,
    "turbo": 0.90,
    "injection": 1.00,
    "egr": 0.90,
    "cooling": 0.90,
    "hose": 1.10,
    "driveshaft": 0.85,
    "joint": 0.85,
    "other": 1.00,
}

FAMILY_LABEL = {
    "brake_pad": "Brake pads",
    "brake_rotor": "Brake disc / rotor",
    "brake_shoe": "Brake shoes",
    "brake_drum": "Brake drum",
    "clutch_disc": "Clutch disc",
    "clutch_kit": "Clutch kit",
    "clutch_pressure_plate": "Clutch pressure plate",
    "fuel_filter": "Fuel filter",
    "air_filter": "Air filter",
    "blower_filter": "Cabin / blower filter",
    "oil_filter": "Oil filter",
    "lighting": "Lighting",
    "body": "Body / panel",
    "turbo": "Turbocharger",
    "injection": "Injector / nozzle",
    "egr": "EGR valve",
    "cooling": "Cooling module / pump",
    "hose": "Hose / pipe",
    "driveshaft": "Driveshaft",
    "joint": "Ball joint",
    "other": "Other / unclassified",
}

# AIM L1 families that are typically contestable even without a priced scrape.
AIM_CONTESTED = {
    "Competitive parts",
    "Brakes",
    "Maintenance Service",
    "Clutch",
    "Cooling",
    "Suspension",
    "Filters",
}

FAMILY_FROM_DESC = [
    (r"pad kit|pad;.*brk|pad.*caliper|brake pad", "brake_pad"),
    (r"shoe kit;?\s*brk|brake shoe", "brake_shoe"),
    (r"rotor;|disc brk", "brake_rotor"),
    (r"drum;?\s*brk", "brake_drum"),
    (r"clutch kit|kit;?\s*clu", "clutch_kit"),
    (r"disc;?\s*clutch|clutch.*disc", "clutch_disc"),
    (r"plate asm;?\s*pressure|pressure plate", "clutch_pressure_plate"),
    (r"oil filter", "oil_filter"),
    (r"fuel filter", "fuel_filter"),
    (r"filter;?\s*acl|air filter|air cleaner|filter; acl", "air_filter"),
    (r"blower", "blower_filter"),
    (r"lamp asm|headlamp|comb lamp", "lighting"),
    (r"bumper|door asm|panel asm|support;.*bumper", "body"),
    (r"turbocharger", "turbo"),
    (r"nozzle asm|injector", "injection"),
    (r"valve;?\s*egr", "egr"),
    (r"pump;?\s*water|water pump", "cooling"),
    (r"hose;|pipe;", "hose"),
    (r"shaft asm", "driveshaft"),
    (r"joint asm;?\s*ball", "joint"),
]


def r2(x):
    if x is None:
        return None
    try:
        if pd.isna(x):
            return None
    except (TypeError, ValueError):
        pass
    return round(float(x), 2)


def r1(x):
    v = r2(x)
    return None if v is None else round(v, 1)


def norm_pn(val) -> str:
    if val is None or (isinstance(val, float) and pd.isna(val)):
        return ""
    s = str(val).strip()
    if s.endswith(".0") and s[:-2].replace("-", "").isdigit():
        s = s[:-2]
    digits = re.sub(r"\D", "", s)
    return digits.zfill(10)[-10:] if digits else ""


def _norm_brand(s: str) -> str:
    s = str(s or "").upper()
    s = s.replace("&", " ").replace("+", " ").replace("AMP", " ")
    s = re.sub(r"[^A-Z0-9]+", " ", s)
    return re.sub(r"\s+", " ", s).strip()


def load_brand_lookup(path: Path | None = None) -> dict:
    t = pd.read_csv(path or DEFAULT_TIER_CSV)
    lookup = {}
    for _, rw in t.iterrows():
        key = _norm_brand(rw.brand)
        if key:
            lookup[key] = {
                "brand": str(rw.brand),
                "tier": int(rw.tier) if pd.notna(rw.tier) else 1,
                "oe": bool(int(rw.oe_supplier)) if pd.notna(rw.oe_supplier) else False,
            }
    return lookup


def score_brand_list(raw: str, lookup: dict) -> dict:
    parts = [p.strip() for p in re.split(r"[|,;/]+", str(raw or "")) if p.strip()]
    if not parts:
        return {
            "brands": "",
            "best_brand": "",
            "best_tier": 1,
            "ceiling_pct": 250,
            "n_mapped": 0,
            "quality": False,
            "unmapped": True,
            "oe": False,
        }
    scored = []
    mapped = 0
    for p in parts:
        hit = lookup.get(_norm_brand(p))
        if hit:
            scored.append(hit)
            mapped += 1
        else:
            scored.append({"brand": p, "tier": 1, "oe": False})
    best = max(scored, key=lambda x: (x["tier"], x["oe"]))
    return {
        "brands": ", ".join(parts[:12]),
        "best_brand": best["brand"],
        "best_tier": int(best["tier"]),
        "ceiling_pct": CEILING_PCT.get(int(best["tier"]), 250),
        "n_mapped": mapped,
        "quality": int(best["tier"]) in QUALITY_TIERS,
        "unmapped": mapped == 0,
        "oe": bool(best.get("oe")),
    }


def classify_family(description: str, pms_category: str | None = None) -> str:
    if pms_category:
        key = str(pms_category).strip().lower()
        if key in FAMILY_TIGHTNESS:
            return key
    desc = (description or "").lower()
    for pat, fam in FAMILY_FROM_DESC:
        if re.search(pat, desc, re.I):
            return fam
    return "other"


def tightness_for(family: str) -> float:
    return float(FAMILY_TIGHTNESS.get(family or "other", 1.0))


def project_channel(isze) -> dict:
    """ISZE net → DB sell → DLR sell = projected retail. Markup, not GM."""
    if not isze:
        return {
            "proj_db_eur": None,
            "proj_dlr_eur": None,
            "proj_retail_eur": None,
        }
    db = r2(float(isze) * DB_FACTOR)
    dlr = r2(db * DLR_FACTOR) if db is not None else None
    return {
        "proj_db_eur": db,
        "proj_dlr_eur": dlr,
        "proj_retail_eur": dlr,  # no extra retail markup in local files
    }


def iam_offer_kind(source: str) -> tuple[str, str]:
    s = (source or "").lower()
    if "mekonomen" in s:
        return (
            "retail",
            "IAM retail (Mekonomen) — same side of the counter as projected retail, still a different shop.",
        )
    if "ks" in s:
        return (
            "trade",
            "IAM trade (KS International) — not like-for-like vs projected retail.",
        )
    if "eucon" in s:
        return (
            "mix",
            "IAM online Autodoc DE/NO (PartsPool 29 Mar 2026) — not like-for-like vs projected retail.",
        )
    return "unknown", "IAM point not classified — treat as not like-for-like."


def channel_meta() -> dict:
    return {
        "db_markup_pct": round(DB_MARKUP * 100, 1),
        "dlr_markup_pct": round(DLR_MARKUP * 100, 1),
        "db_factor": DB_FACTOR,
        "dlr_factor": DLR_FACTOR,
        "combined_factor": CHANNEL_FACTOR,
        "kind": "markup",
        "origin": CHANNEL_ORIGIN,
        "source_file": CHANNEL_SOURCE_FILE,
        "source_as_of": CHANNEL_SOURCE_AS_OF,
        "cross_check": CHANNEL_CROSS_CHECK,
        "note": (
            "Working channel markup from the pricing engine. "
            "Not observed SPA terms. Distributors set their own resale prices. "
            "Projected retail = DLR sell (no extra retail markup in local files). "
            "Not the iam_scoring.py 37/25 gross-margin divide."
        ),
    }


def effective_ceiling(tier: int, family: str) -> int:
    """T3/T4 ceilings are multiplied by product-type tightness. T1/T2 stay full.

    T4 pad: 30 × 0.50 = 15. T4 oil filter: 30 × 1.00 = 30.
    Floor 10 pp so a tight T4 never collapses to 'match a T1 listing'.
    """
    base = int(CEILING_PCT.get(int(tier), 250))
    if int(tier) < 3:
        return base
    adj = round(base * tightness_for(family))
    return max(10, int(adj))


def system_role(description: str, titles: str = "") -> dict:
    """Infer kit vs component from ISZE description + listing titles.

    There is no dedicated system-offer table in derived data. Missing → unknown.
    """
    d = (description or "").lower()
    t = (titles or "").lower()
    blob = d + " " + t
    if re.search(r"clutch kit|kit;?\s*clu", blob):
        return {
            "role": "full_system",
            "score": 90,
            "label": "Clutch kit",
            "note": "ISZE description is a kit. A cheap pad or disc listing is not this system.",
            "inferred": True,
        }
    if re.search(r"pad kit|pad;.*brk|pad.*caliper", d):
        return {
            "role": "component",
            "score": 30,
            "label": "Pads only",
            "note": "Pad kit — not a disc+pad brake kit. A T1 pad is not a system offer.",
            "inferred": True,
        }
    if re.search(r"rotor;|disc brk", d) and "pad" not in d:
        return {
            "role": "component",
            "score": 30,
            "label": "Disc / rotor only",
            "note": "Disc only — not a complete brake kit.",
            "inferred": True,
        }
    if re.search(r"shoe kit", d):
        return {
            "role": "component",
            "score": 35,
            "label": "Shoes only",
            "note": "Shoe kit — not a drum+shoe system.",
            "inferred": True,
        }
    if re.search(r"element;|element kit", d):
        return {
            "role": "component",
            "score": 30,
            "label": "Filter element",
            "note": "Element only — not a housing / module.",
            "inferred": True,
        }
    if re.search(r"filter asm", d):
        return {
            "role": "assembly",
            "score": 70,
            "label": "Filter assembly",
            "note": "Assembly on the ISZE description (housing + element).",
            "inferred": True,
        }
    if re.search(r"throttle asm|turbocharger asm|nozzle asm|pump;?\s*water", d):
        return {
            "role": "assembly",
            "score": 75,
            "label": "Module / assembly",
            "note": "Complete module on the ISZE description. A hose listing is not this offer.",
            "inferred": True,
        }
    if re.search(r"hose;|pipe;", d):
        return {
            "role": "component",
            "score": 25,
            "label": "Hose / pipe",
            "note": "Hose/pipe only — not a cooling module.",
            "inferred": True,
        }
    if re.search(r"lamp asm", d):
        return {
            "role": "assembly",
            "score": 70,
            "label": "Lamp assembly",
            "note": "Lamp assembly on the ISZE description.",
            "inferred": True,
        }
    if re.search(r"shaft asm", d):
        return {
            "role": "assembly",
            "score": 70,
            "label": "Driveshaft assembly",
            "note": "Assembly on the ISZE description.",
            "inferred": True,
        }
    return {
        "role": "unknown",
        "score": None,
        "label": "Not scored",
        "note": "No system-offer table in derived data. Role not invented.",
        "inferred": False,
    }


def iam_cheaper_frac(isze: float, iam: float) -> float | None:
    """(ISZE − IAM) / ISZE. Positive = IAM cheaper. Internal helper only."""
    if not isze or isze <= 0 or iam is None or iam <= 0:
        return None
    return (isze - iam) / isze


def delta_isze_cheaper(isze: float, iam: float) -> float | None:
    """(IAM − ISZE) / ISZE. Positive = ISZE cheaper. Display sign."""
    if not isze or isze <= 0 or iam is None or iam <= 0:
        return None
    return (iam - isze) / isze


def price_only_title(title: str) -> bool:
    t = str(title or "").strip()
    if not t:
        return True
    return bool(re.fullmatch(r"[\d\s.,]+kr\.?", t, flags=re.I))


def mek_suspect(description: str, brand: str, titles: str, cheaper: float | None) -> str | None:
    reasons = []
    if price_only_title(titles):
        reasons.append("listing title is only a kronor figure — no product name captured")
    bkey = _norm_brand(brand)
    desc = (description or "").lower()
    pad_words = ("pad", "caliper", "brake", "disc", "rotor", "lamp", "filter")
    body_words = ("lamp", "bumper", "support", "shaft", "filter")
    if "LESJ" in bkey and any(w in desc for w in pad_words):
        reasons.append(f"{brand} is a spring maker — not this part family")
    if bkey == "RAUFOSS" and any(w in desc for w in body_words):
        reasons.append(f"{brand} is not a typical maker of this part family")
    if cheaper is not None and cheaper >= 0.75 and price_only_title(titles):
        reasons.append("gap over 75% on a single unnamed listing")
    return "; ".join(reasons) if reasons else None


def load_book(sold_tos: list[int], pns: list[str] | None = None) -> pd.DataFrame:
    """CY billed book for one distributor's sold-to list. Never mix other DBs."""
    path = DERIVED / "sales_fact.parquet"
    sf = pd.read_parquet(
        path,
        columns=[
            "sold_to_sap", "part_number", "description",
            "billed_qty", "net_sales_value", "saty", "year",
        ],
    )
    sf["sold_to_sap"] = pd.to_numeric(sf["sold_to_sap"], errors="coerce")
    sf["year"] = pd.to_numeric(sf["year"], errors="coerce")
    sf["saty"] = sf["saty"].astype(str).str.upper().str.strip()
    sf["pn"] = sf["part_number"].map(norm_pn)
    codes = {int(x) for x in sold_tos}
    book = sf[
        (sf["sold_to_sap"].isin(codes))
        & (sf["year"] == CY)
        & (sf["saty"] != "CR")
    ]
    if pns is not None:
        book = book[book["pn"].isin(pns)]
    g = book.groupby("pn", as_index=False).agg(
        qty=("billed_qty", "sum"),
        rev_eur=("net_sales_value", "sum"),
        description=("description", "first"),
    )
    return g.set_index("pn")


def load_umi_book(pns: list[str] | None = None) -> pd.DataFrame:
    return load_book([SOLD_TO_UMI], pns)


def load_bvp() -> tuple[dict[str, list[str]], set[str], dict[str, str]]:
    xref = pd.read_csv(DERIVED / "genuine_bvp_crossref.csv")
    xref["genuine_pn"] = xref["genuine_pn"].map(norm_pn)
    xref["bvp_pn"] = xref["bvp_pn"].map(norm_pn)
    alts: dict[str, list[str]] = {}
    fam: dict[str, str] = {}
    for _, rw in xref.iterrows():
        if not rw.genuine_pn or not rw.bvp_pn:
            continue
        alts.setdefault(rw.genuine_pn, [])
        if rw.bvp_pn not in alts[rw.genuine_pn]:
            alts[rw.genuine_pn].append(rw.bvp_pn)
        fam[rw.genuine_pn] = str(rw.get("product_family") or "")
        fam[rw.bvp_pn] = str(rw.get("product_family") or "")
    is_bvp = set(xref["bvp_pn"]) - {""}
    return alts, is_bvp, fam


def load_aim() -> pd.DataFrame:
    aim = pd.read_csv(
        DERIVED / "aim_pn_classification.csv",
        dtype={"part_number": str},
        usecols=["part_number", "aim_l1", "aim_l2"],
    )
    aim["pn"] = aim["part_number"].map(norm_pn)
    return aim.drop_duplicates("pn").set_index("pn")


def load_catalog_pms() -> dict[str, str]:
    path = DERIVED / "parts_catalog_dimension.csv"
    if not path.exists():
        return {}
    cat = pd.read_csv(
        path,
        dtype={"part_number": str},
        usecols=["part_number", "pms_category"],
        low_memory=False,
    )
    cat["pn"] = cat["part_number"].map(norm_pn)
    cat = cat.dropna(subset=["pms_category"])
    cat = cat[cat["pms_category"].astype(str).str.strip() != ""]
    return dict(zip(cat["pn"], cat["pms_category"].astype(str)))


def load_pms_capture(distributor_code: str) -> list[dict]:
    path = DERIVED / "pms_capture_by_db_year.csv"
    df = pd.read_csv(path)
    code = str(distributor_code).strip().upper()
    u = df[
        (df["distributor_code"].astype(str).str.upper() == code)
        & (pd.to_numeric(df["year"], errors="coerce") == CY)
        & (df["line_type"].astype(str).str.lower() == "total")
    ].copy()
    out = []
    for _, rw in u.iterrows():
        cat = str(rw.get("pms_category") or "")
        cap = pd.to_numeric(rw.get("capture_rate"), errors="coerce")
        gap = pd.to_numeric(rw.get("revenue_gap_eur"), errors="coerce")
        out.append({
            "cat": cat,
            "label": str(rw.get("category_label") or cat),
            "capture_pct": r1(100 * float(cap)) if pd.notna(cap) else None,
            "gap_eur": r2(gap),
            "tightness": tightness_for(cat),
        })
    out.sort(key=lambda x: (x["capture_pct"] is None, x["capture_pct"] or 99))
    return out


def load_umi_pms_capture() -> list[dict]:
    return load_pms_capture("UMI")


def _ks_skip_placeholder(gbp) -> bool:
    try:
        v = float(gbp)
    except (TypeError, ValueError):
        return True
    return v <= KS_PLACEHOLDER_GBP


def load_eucon(lookup: dict) -> dict[str, dict]:
    df = pd.read_csv(DERIVED / "eucon_price_gap.csv")
    df["pn"] = df["pn"].map(norm_pn)
    out = {}
    for _, rw in df.iterrows():
        br = score_brand_list(rw.get("Brands_Found") or "", lookup)
        out[rw.pn] = {
            "source": "PartsPool Autodoc DE/NO 2026-03-29",
            "point": POINT_EUCON,
            "like_for_like": False,
            "like_for_like_flag": "Not like-for-like",
            "like_for_like_why": (
                "2023 DE/NO IAM survey against genuine OEM list. Mix of brands "
                "including budget. Quality price uses the survey maximum as the quality-end "
                "proxy — Eucon does not isolate Bosch vs Ridex on this PN."
            ),
            "iam_min_eur": r2(rw.Min_Competitor_EUR),
            "iam_avg_eur": r2(rw.Avg_Competitor_EUR),
            "iam_max_eur": r2(rw.Max_Competitor_EUR),
            # Eucon does not isolate the named T3/T4 brand. Quality-end proxy =
            # survey MAX when a quality brand is present; never the cheapest.
            "quality_price_eur": r2(rw.Max_Competitor_EUR) if br.get("quality") else r2(rw.Avg_Competitor_EUR),
            "competitor_count": int(rw.Competitor_Count) if pd.notna(rw.Competitor_Count) else 0,
            "url": "",
            "scraped_at": "2023 survey",
            "titles": "",
            "fx": "survey EUR as published",
            "isze_eur": r2(rw.ISZE_IE40_Price_EUR),
            "description": str(rw.get("description") or ""),
            **br,
        }
    return out


def decide_action(row_ctx: dict) -> dict:
    """Hold / review / SPA / cut-to-band / monitor. Numbers already on ctx."""
    isze = row_ctx.get("isze_eur")
    q_price = row_ctx.get("quality_iam_eur")
    q_tier = row_ctx.get("quality_tier")
    captive = row_ctx["captive_flag"] == "captive"
    t1_only = row_ctx["captive_flag"] == "t1_only"
    itself_bvp = row_ctx["itself_bvp"]
    alts = row_ctx["bvp_alts"]
    suspect = row_ctx.get("suspect")
    band_high = row_ctx.get("band_high_eur")
    proposed = row_ctx.get("proposed_isze_eur")

    if itself_bvp or alts:
        return {
            "action": "has_bvp",
            "action_label": "Push Best Value",
            "proposed_label": "—",
            "proposed_note": "Best Value already exists in the crossref — retention, not a cut.",
            "spa_candidate": False,
        }

    if captive:
        return {
            "action": "hold",
            "action_label": "Hold",
            "proposed_label": "Hold",
            "proposed_note": (
                "No credible named IAM (T3/T4) and no Best Value in the crossref. "
                "Do not discount because a random listing exists. Crossref is incomplete — "
                "this is not ‘no Best Value in the catalogue’."
            ),
            "spa_candidate": False,
        }

    if t1_only or (q_tier is not None and int(q_tier) <= 1 and not row_ctx.get("quality_brand")):
        return {
            "action": "monitor",
            "action_label": "Monitor (T1 only)",
            "proposed_label": "—",
            "proposed_note": (
                "Only an unmapped / no-name listing. ISZE does not auto-cut 20% "
                "just because a T1 listing is cheaper. Optional monitor."
            ),
            "spa_candidate": False,
        }

    if suspect and not row_ctx.get("quality_brand"):
        return {
            "action": "review",
            "action_label": "Review (suspect listing)",
            "proposed_label": "Review",
            "proposed_note": "IAM hit looks like a search mismatch — no auto-cut.",
            "spa_candidate": False,
        }

    spa = bool(
        (not itself_bvp)
        and (len(alts) == 0)
        and q_price
        and isze
        and isze > q_price
        and (q_tier in QUALITY_TIERS)
    )

    sys_block = bool(row_ctx.get("system_block_cut"))
    if q_price and isze and band_high and isze > band_high + 0.005 and q_tier in QUALITY_TIERS:
        note = (
            f"ISZE net-to-DB sits above the band vs {row_ctx.get('quality_brand')} "
            f"T{q_tier} ({FAMILY_LABEL.get(row_ctx.get('family'), row_ctx.get('family'))}). "
            f"Proposed = quality IAM × (1 + {row_ctx.get('effective_ceiling_pct')}% ceiling). "
            "Not a 20% haircut vs the cheapest listing."
        )
        if sys_block:
            return {
                "action": "spa_review" if spa else "review",
                "action_label": "SPA · review (system)" if spa else "Review (system)",
                "proposed_label": "Review",
                "proposed_note": (
                    note + " Auto-cut blocked: ISZE looks like an assembly/kit and the IAM "
                    "price is a mixed listing — not confirmed as the same system."
                ),
                "spa_candidate": spa,
            }
        if spa:
            return {
                "action": "spa_cut",
                "action_label": "SPA · cut to band",
                "proposed_label": f"€{proposed:.2f}" if proposed else "—",
                "proposed_note": note + " No Best Value in the crossref — SPA is the lever.",
                "spa_candidate": True,
            }
        return {
            "action": "cut_to_band",
            "action_label": "Cut to band",
            "proposed_label": f"€{proposed:.2f}" if proposed else "—",
            "proposed_note": note,
            "spa_candidate": False,
        }

    if spa:
        return {
            "action": "spa_review",
            "action_label": "SPA · review",
            "proposed_label": "Review",
            "proposed_note": (
                "Quality IAM is cheaper than ISZE net-to-DB and there is no Best Value "
                "in the crossref. Gap is inside the quality ceiling — review, do not auto-cut."
            ),
            "spa_candidate": True,
        }

    if q_price and isze and isze > q_price and q_tier in QUALITY_TIERS:
        return {
            "action": "review",
            "action_label": "Review",
            "proposed_label": "Review",
            "proposed_note": (
                "Quality IAM is cheaper, but ISZE is still inside the allowed premium band "
                f"(+{row_ctx.get('effective_ceiling_pct')}% vs T{q_tier}). Hold the position unless a SPA is wanted."
            ),
            "spa_candidate": False,
        }

    return {
        "action": "hold",
        "action_label": "Hold",
        "proposed_label": "Hold",
        "proposed_note": "ISZE net-to-DB is not above the quality IAM band — no cut.",
        "spa_candidate": False,
    }


def _pick_quality_source(sources: list[dict]) -> dict | None:
    quality_hits = [
        s for s in sources
        if s.get("quality") and not s.get("suspect") and s.get("n_mapped", 0) > 0
        and s.get("quality_price_eur")
    ]
    if not quality_hits:
        return None
    return max(
        quality_hits,
        key=lambda s: (
            s.get("best_tier") or 0,
            1 if s.get("oe") else 0,
            s.get("quality_price_eur") or 0,
        ),
    )


def score_pn(
    pn: str,
    *,
    desc: str,
    isze: float | None,
    sources: list[dict],
    book_rev: float,
    book_qty: float,
    bvp_alts: list[str],
    itself_bvp: bool,
    aim_l1: str,
    aim_l2: str,
    pms_cat: str | None,
) -> dict:
    family = classify_family(desc, pms_cat)
    titles = " | ".join(str(s.get("titles") or "") for s in sources)
    role = system_role(desc, titles)

    best_q = _pick_quality_source(sources)
    cheapest = None
    for s in sources:
        p = s.get("iam_min_eur") or s.get("iam_avg_eur")
        if p and (cheapest is None or p < cheapest):
            cheapest = p

    q_tier = (best_q or {}).get("best_tier")
    q_price = (best_q or {}).get("quality_price_eur")
    q_brand = (best_q or {}).get("best_brand") or ""
    mapped_any = any(s.get("n_mapped", 0) > 0 for s in sources)
    quality_present = bool(best_q)
    t1_only = (not quality_present) and any(s.get("iam_avg_eur") or s.get("iam_min_eur") for s in sources)

    in_crossref = bool(bvp_alts) or itself_bvp
    if itself_bvp or bvp_alts or quality_present:
        captive_flag = "competitive"
    elif t1_only:
        captive_flag = "t1_only"
    else:
        captive_flag = "captive"

    eff = effective_ceiling(int(q_tier or 1), family) if q_tier else None
    band_high = r2(q_price * (1 + eff / 100.0)) if q_price and eff is not None else None
    band_low = r2(q_price * (1 + 0.5 * (eff or 0) / 100.0)) if q_price and eff is not None else None
    proposed = band_high

    delta_q = delta_isze_cheaper(isze or 0, q_price or 0) if (isze and q_price) else None
    delta_cheap = delta_isze_cheaper(isze or 0, cheapest or 0) if (isze and cheapest) else None

    suspect = next((s.get("suspect") for s in sources if s.get("suspect")), None)
    q_src = (best_q or {}).get("source") or ""
    system_block_cut = bool(
        role["role"] in {"assembly", "full_system"}
        and "Eucon" in q_src
    )

    ctx = {
        "isze_eur": isze,
        "quality_iam_eur": q_price,
        "quality_tier": q_tier,
        "quality_brand": q_brand,
        "captive_flag": captive_flag,
        "itself_bvp": itself_bvp,
        "bvp_alts": bvp_alts,
        "suspect": suspect,
        "band_high_eur": band_high,
        "proposed_isze_eur": proposed,
        "effective_ceiling_pct": eff,
        "family": family,
        "system_block_cut": system_block_cut,
    }
    decision = decide_action(ctx)
    if decision["action"] not in {"cut_to_band", "spa_cut"}:
        proposed = None

    offers = {
        "isze": True,
        "bvp": bool(itself_bvp or bvp_alts),
        "named_iam": quality_present,
        "t1_listing": t1_only,
    }

    chain = project_channel(isze)
    q_src = (best_q or {}).get("source") or ""
    iam_kind, iam_kind_note = iam_offer_kind(q_src)
    proj_ret = chain["proj_retail_eur"]
    gap_ret = None
    gap_ret_eur = None
    if q_price and proj_ret:
        gap_ret = round((q_price - proj_ret) / proj_ret, 4)
        gap_ret_eur = r2(q_price - proj_ret)

    return {
        "pn": pn,
        "description": (desc or "").strip(),
        "family": family,
        "family_label": FAMILY_LABEL.get(family, family),
        "tightness": tightness_for(family),
        "pms_category": pms_cat or "",
        "aim_l1": aim_l1 or "",
        "aim_l2": aim_l2 or "",
        "isze_eur": isze,
        "isze_point": POINT_ISZE,
        "proj_db_eur": chain["proj_db_eur"],
        "proj_dlr_eur": chain["proj_dlr_eur"],
        "proj_retail_eur": chain["proj_retail_eur"],
        "iam_offer_eur": q_price,
        "iam_point_kind": iam_kind,
        "iam_point_note": iam_kind_note,
        "gap_vs_proj_retail": gap_ret,
        "gap_vs_proj_retail_eur": gap_ret_eur,
        "umi_cy2025_eur": r2(book_rev),
        "umi_cy2025_qty": r2(book_qty),
        "book_cy2025_eur": r2(book_rev),
        "book_cy2025_qty": r2(book_qty),
        "sources": sources,
        "quality_brand": q_brand,
        "quality_tier": q_tier,
        "quality_source": (best_q or {}).get("source") or "",
        "quality_iam_eur": q_price,
        "quality_oe": bool((best_q or {}).get("oe")),
        "cheapest_iam_eur": cheapest,
        "delta_vs_quality": None if delta_q is None else round(delta_q, 4),
        "delta_vs_cheapest": None if delta_cheap is None else round(delta_cheap, 4),
        "base_ceiling_pct": CEILING_PCT.get(int(q_tier), 250) if q_tier else None,
        "effective_ceiling_pct": eff,
        "band_low_eur": band_low,
        "band_high_eur": band_high,
        "proposed_isze_eur": proposed if decision["action"] in {"cut_to_band", "spa_cut"} else None,
        "proposed_label": decision["proposed_label"],
        "proposed_note": decision["proposed_note"],
        "action": decision["action"],
        "action_label": decision["action_label"],
        "spa_candidate": decision["spa_candidate"],
        "captive_flag": captive_flag,
        "captive_label": {
            "captive": "Captive (hold)",
            "competitive": "Competitive",
            "t1_only": "T1 listing only",
        }[captive_flag],
        "bvp_alts": bvp_alts,
        "itself_bvp": itself_bvp,
        "in_crossref": in_crossref,
        "crossref_caveat": (not in_crossref),
        "not_like_for_like": True,
        "system_role": role["role"],
        "system_score": role["score"],
        "system_label": role["label"],
        "system_note": role["note"],
        "system_inferred": role["inferred"],
        "offers": offers,
        "mapped_any": mapped_any,
        "suspect": suspect,
        "primary_url": next((s.get("url") for s in sources if s.get("url")), ""),
    }


def load_ks(lookup: dict) -> dict[str, dict]:
    """PN-level IAM trade prices. File `db` is scrape-target, not a sold-to filter."""
    df = pd.read_csv(DERIVED / "iam_ks_price_gap.csv", dtype={"pn": str})
    df["pn"] = df["pn"].map(norm_pn)
    if "competitor_count" in df.columns:
        df = df.sort_values("competitor_count", ascending=False)
    df = df.drop_duplicates("pn")
    out = {}
    for _, rw in df.iterrows():
        gbp_min = None
        if pd.notna(rw.get("ks_am_min_eur")) and GBP_EUR:
            gbp_min = float(rw.ks_am_min_eur) / GBP_EUR
        if gbp_min is not None and _ks_skip_placeholder(gbp_min):
            continue
        br = score_brand_list(rw.get("brands_found") or "", lookup)
        if not str(rw.get("brands_found") or "").strip():
            br = score_brand_list("", lookup)
        out[rw.pn] = {
            "source": "KS International",
            "point": POINT_KS,
            "like_for_like": False,
            "like_for_like_flag": "Not like-for-like",
            "like_for_like_why": (
                f"ISZE is net-to-distributor (PR00). KS is IAM trade, ex-VAT, GBP × {GBP_EUR}."
            ),
            "iam_min_eur": r2(rw.ks_am_min_eur),
            "iam_avg_eur": r2(rw.ks_am_avg_eur),
            "iam_max_eur": None,
            "quality_price_eur": r2(rw.ks_am_avg_eur),
            "competitor_count": int(rw.competitor_count) if pd.notna(rw.competitor_count) else 0,
            "url": str(rw.ks_url or ""),
            "scraped_at": str(rw.scraped_at or ""),
            "titles": str(rw.scrape_titles or "")[:240],
            "fx": f"GBP_EUR={GBP_EUR} (1 May 2026). Ex-VAT. AM ≤ £{KS_PLACEHOLDER_GBP:.0f} dropped.",
            "isze_eur": r2(rw.isze_price_eur),
            "description": str(rw.get("description") or ""),
            "suspect": None,
            **br,
        }
    return out


def load_ks_umi(lookup: dict) -> dict[str, dict]:
    return load_ks(lookup)


def load_mek(lookup: dict) -> dict[str, dict]:
    """PN-level IAM retail prices. File `db` is scrape-target, not a sold-to filter."""
    df = pd.read_csv(DERIVED / "iam_mekonomen_price_gap.csv", dtype={"pn": str})
    df["pn"] = df["pn"].map(norm_pn)
    if "competitor_count" in df.columns:
        df = df.sort_values("competitor_count", ascending=False)
    df = df.drop_duplicates("pn")
    out = {}
    for _, rw in df.iterrows():
        br = score_brand_list(rw.get("brands_found") or "", lookup)
        cheaper = iam_cheaper_frac(float(rw.isze_price_eur or 0), float(rw.mek_am_avg_eur or 0))
        sus = mek_suspect(
            str(rw.description),
            br.get("best_brand") or "",
            str(rw.scrape_titles or ""),
            cheaper,
        )
        rec = {
            "source": "Mekonomen",
            "point": POINT_MEK,
            "like_for_like": False,
            "like_for_like_flag": "Not like-for-like",
            "like_for_like_why": (
                f"ISZE is net-to-distributor (PR00). Mekonomen.se is IAM retail, SEK × {SEK_EUR}. "
                "Search quality is noisy."
            ),
            "iam_min_eur": r2(rw.mek_am_min_eur),
            "iam_avg_eur": r2(rw.mek_am_avg_eur),
            "iam_max_eur": None,
            "quality_price_eur": r2(rw.mek_am_avg_eur),
            "competitor_count": int(rw.competitor_count) if pd.notna(rw.competitor_count) else 0,
            "url": str(rw.mek_url or ""),
            "scraped_at": str(rw.scraped_at or ""),
            "titles": str(rw.scrape_titles or "")[:240],
            "fx": f"SEK_EUR={SEK_EUR} (1 May 2026).",
            "isze_eur": r2(rw.isze_price_eur),
            "description": str(rw.get("description") or ""),
            "suspect": sus,
            **br,
        }
        if sus:
            rec["quality"] = False
        out[rw.pn] = rec
    return out


def load_mek_umi(lookup: dict) -> dict[str, dict]:
    return load_mek(lookup)


def book_mix(book: pd.DataFrame, scored_by_pn: dict, bvp_alts, is_bvp, aim: pd.DataFrame) -> list[dict]:
    buckets = {
        "bvp_retention": {"label": "Best Value in play", "eur": 0.0, "pns": 0, "kind": "bvp"},
        "iam_quality": {"label": "Named quality IAM (T3/T4)", "eur": 0.0, "pns": 0, "kind": "competitive"},
        "t1_listing": {"label": "T1 / unnamed listing only", "eur": 0.0, "pns": 0, "kind": "monitor"},
        "aim_contested_unpriced": {"label": "Contested family, no priced IAM", "eur": 0.0, "pns": 0, "kind": "incomplete"},
        "body_no_pn": {"label": "Body — family IAM exists, no PN join", "eur": 0.0, "pns": 0, "kind": "incomplete"},
        "no_evidence": {"label": "No IAM / Best Value observed", "eur": 0.0, "pns": 0, "kind": "captive"},
    }
    for pn, rw in book.iterrows():
        rev = float(rw.rev_eur or 0)
        sc = scored_by_pn.get(pn)
        alts = bvp_alts.get(pn) or []
        itself = pn in is_bvp
        l1 = ""
        if pn in aim.index:
            l1 = str(aim.loc[pn, "aim_l1"] or "")
        if itself or alts:
            k = "bvp_retention"
        elif sc and sc["captive_flag"] == "competitive":
            k = "iam_quality"
        elif sc and sc["captive_flag"] == "t1_only":
            k = "t1_listing"
        elif l1 == "Body Exterior":
            k = "body_no_pn"
        elif l1 in AIM_CONTESTED:
            k = "aim_contested_unpriced"
        else:
            k = "no_evidence"
        buckets[k]["eur"] += rev
        buckets[k]["pns"] += 1
    out = []
    for k, v in buckets.items():
        out.append({
            "id": k,
            "label": v["label"],
            "kind": v["kind"],
            "eur": r2(v["eur"]),
            "pns": v["pns"],
        })
    return out


def _eur(v) -> str:
    if v is None:
        return "—"
    return f"€{float(v):,.0f}"


def _pct(v, d=0) -> str:
    if v is None:
        return "—"
    return f"{float(v):.{d}f}%"


def build_conclusion(d: dict) -> dict:
    """Data-backed positioning conclusion for this DB's billed book. Not a slogan."""
    meta = d["meta"]
    rows = d["rows"]
    mix = d["mix"]
    pms = d["pms_capture"]
    ch = d["channel"]
    short = meta["db_short"]
    n = meta["n_scored"]
    n_comp = meta["n_competitive"]
    n_t1 = meta["n_t1_only"]
    n_cut = meta["n_cut"]
    n_spa = meta["n_spa"]
    n_hold_priced = meta["n_captive"]
    rev_scored = meta["rev_scored_eur"] or 0
    rev_book = meta["rev_book_eur"] or 0
    cover = (100.0 * rev_scored / rev_book) if rev_book else 0.0

    act = {}
    for a in d.get("actions") or []:
        act[a["action"]] = a["n"]
    n_bvp = int(act.get("has_bvp") or 0)
    n_hold = int(act.get("hold") or 0)
    n_rev = int(act.get("review") or 0) + int(act.get("spa_review") or 0)

    spa_eur = sum((r.get("book_cy2025_eur") or r.get("umi_cy2025_eur") or 0) for r in rows if r.get("spa_candidate"))
    bvp_eur = sum((r.get("book_cy2025_eur") or r.get("umi_cy2025_eur") or 0) for r in rows if r.get("action") == "has_bvp")
    cut_eur = sum((r.get("book_cy2025_eur") or r.get("umi_cy2025_eur") or 0) for r in rows if r.get("action") in {"cut_to_band", "spa_cut"})
    hold_eur = sum((r.get("book_cy2025_eur") or r.get("umi_cy2025_eur") or 0) for r in rows if r.get("action") == "hold")

    with_gap = [r for r in rows if r.get("gap_vs_proj_retail") is not None]
    cheaper_ret = sum(1 for r in with_gap if (r.get("gap_vs_proj_retail") or 0) > 0)
    dearer_ret = sum(1 for r in with_gap if (r.get("gap_vs_proj_retail") or 0) < 0)
    kind_n = {}
    for r in rows:
        k = r.get("iam_point_kind") or "unknown"
        kind_n[k] = kind_n.get(k, 0) + 1
    trade_n = kind_n.get("trade", 0)
    retail_n = kind_n.get("retail", 0)
    mix_n = kind_n.get("mix", 0)

    pad_pms = next((x for x in pms if x.get("cat") == "brake_pad"), None)
    oil_pms = next((x for x in pms if x.get("cat") == "oil_filter"), None)
    n_pads = meta["n_pads"]
    mix_none = next((m for m in mix if m.get("id") == "no_evidence"), {}) or {}
    mix_bvp = next((m for m in mix if m.get("id") == "bvp_retention"), {}) or {}
    mix_inc = next((m for m in mix if m.get("id") == "aim_contested_unpriced"), {}) or {}

    def _cap_txt(label: str, rec) -> str:
        if not rec or rec.get("capture_pct") is None:
            return f"{label} is not in the PMS extract."
        pct = rec["capture_pct"]
        if pct > 100:
            return (
                f"{label} prints {_pct(pct, 1)} in the PMS extract — over 100% is a denominator issue, "
                "not complete capture. Do not quote it as GPS%."
            )
        return f"{label} is {_pct(pct, 1)}."

    if pad_pms and pad_pms.get("capture_pct") is not None and pad_pms["capture_pct"] <= 100:
        pad_txt = (
            f"{short} pad capture (PMS, CY{meta['cy']}, total line) is {_pct(pad_pms['capture_pct'], 1)}."
        )
    else:
        pad_txt = _cap_txt(f"{short} pad capture (PMS, CY{meta['cy']}, total line)", pad_pms)
    oil_txt = _cap_txt("Oil-filter capture", oil_pms)
    pad_pn_txt = (
        "1 scored PN in this book is a pad"
        if n_pads == 1
        else f"{n_pads} scored PNs in this book are pads"
    )

    bullets = [
        (
            f"Sit vs T4/T3, not vs T1. On {n} scored {short} PNs, {n_comp} have a named T3/T4 IAM "
            f"or Best Value; {n_t1} are T1/unmapped listings only. Genuine may sit up to +30% vs T4 "
            f"and +60% vs T3. T1 never auto-cuts — a cheaper no-name listing does not set the price."
        ),
        (
            f"Pads vs filters. {pad_txt} Tightness 0.50 compresses the T4 pad ceiling to +15% "
            f"(T3 pad +30%). {oil_txt} Filters keep the full T4 +30%. {pad_pn_txt} — "
            "do not copy a pad haircut onto filters or lighting."
        ),
        (
            f"Captive hold. The priced set is almost all listings (captive-on-priced = {n_hold_priced}). "
            f"On the full CY{meta['cy']} book, {_eur(mix_none.get('eur'))} / {mix_none.get('pns') or 0} PNs "
            f"show no named IAM and no Best Value in the crossref — hold that slice. "
            f"Incomplete crossref is not ‘no Best Value in the catalogue’ "
            f"({_eur(mix_inc.get('eur'))} contested-family with no priced IAM)."
        ),
        (
            f"Projected retail vs IAM. Channel rule is PR00 × {ch['db_factor']:.2f} DB × {ch['dlr_factor']:.3f} DLR "
            f"= ×{ch['combined_factor']:.3f} projected retail (equals DLR sell). "
            f"Of {len(with_gap)} scored PNs with both sides, projected retail is cheaper than the IAM offer on "
            f"{cheaper_ret} and dearer on {dearer_ret}. IAM points on the scored set: "
            f"{trade_n} trade (KS), {retail_n} retail (Mekonomen), {mix_n} mix (Eucon) — "
            "not like-for-like vs ISZE net-to-DB. Flag, do not treat as street."
        ),
        (
            f"SPA. {n_spa} scored PN{'' if n_spa == 1 else 's'} are SPA candidates "
            f"({_eur(spa_eur)} billed on those lines); {n_cut} fire cut-to-band "
            f"({_eur(cut_eur)}). Cut only vs the best-quality named IAM, to the band high — not a flat 20%."
        ),
        (
            f"Hold / review. {n_hold} hold and {n_rev} review on the priced set "
            f"(hold billed {_eur(hold_eur)}). Inside the quality ceiling: keep the position unless a SPA is wanted. "
            f"Suspect Mekonomen titles and mixed Eucon kits stay review, not auto-cut."
        ),
        (
            f"Push Best Value. {n_bvp} scored PN{'' if n_bvp == 1 else 's'} already have Best Value in the crossref "
            f"({_eur(bvp_eur)} billed). Book-level Best Value in play: {_eur(mix_bvp.get('eur'))} / "
            f"{mix_bvp.get('pns') or 0} PNs. Retention — never a red cut."
        ),
        (
            f"Coverage. {n} PNs scored = {_eur(rev_scored)} of {_eur(rev_book)} {short} CY{meta['cy']} billed "
            f"({cover:.1f}% of the book, {meta['n_book']} PNs). KS {meta['n_ks']} + Mekonomen {meta['n_mek']} + "
            f"Eucon-in-book {meta['n_eucon_in_book']}. IAM prices are PN-level market observations joined to this "
            f"sold-to list only ({meta['sold_to_note']}; {meta['not_blend']}). Scrapes 10 Aug 2026; Eucon is 2023. "
            f"Not a network total."
        ),
    ]
    return {
        "title": f"Positioning conclusion — {short}",
        "lead": (
            f"How ISZE should sit on the {short} book versus quality IAM, and which lever to use. "
            f"Numbers are this distributor only."
        ),
        "bullets": bullets,
    }


def score_db(key: str = "UMI") -> dict:
    db_key = resolve_db(key)
    cfg = DB_REGISTRY[db_key]
    lookup = load_brand_lookup()
    ks = load_ks(lookup)
    mek = load_mek(lookup)
    eucon = load_eucon(lookup)
    bvp_alts, is_bvp, _bvp_fam = load_bvp()
    aim = load_aim()
    pms_map = load_catalog_pms()

    book_all = load_book(cfg["sold_to"], None)
    iam_pns = set(ks) | set(mek) | set(eucon)
    pns = sorted(iam_pns & set(book_all.index))
    book = book_all.loc[book_all.index.isin(pns)] if pns else book_all.iloc[0:0]

    rows = []
    for pn in pns:
        sources = []
        desc = ""
        isze = None
        if pn in ks:
            s = dict(ks[pn])
            desc = s.get("description") or desc
            isze = s.get("isze_eur") or isze
            sources.append(s)
        if pn in mek:
            s = dict(mek[pn])
            desc = desc or s.get("description")
            isze = isze or s.get("isze_eur")
            sources.append(s)
        if pn in eucon:
            s = dict(eucon[pn])
            desc = desc or s.get("description")
            isze = isze or s.get("isze_eur")
            sources.append(s)
        if pn in book_all.index:
            desc = desc or str(book_all.loc[pn, "description"] or "")
        aim_l1 = str(aim.loc[pn, "aim_l1"]) if pn in aim.index else ""
        aim_l2 = str(aim.loc[pn, "aim_l2"]) if pn in aim.index else ""
        book_rev = float(book_all.loc[pn, "rev_eur"]) if pn in book_all.index else 0.0
        book_qty = float(book_all.loc[pn, "qty"]) if pn in book_all.index else 0.0
        row = score_pn(
            pn,
            desc=desc,
            isze=isze,
            sources=sources,
            book_rev=book_rev,
            book_qty=book_qty,
            bvp_alts=bvp_alts.get(pn) or [],
            itself_bvp=pn in is_bvp,
            aim_l1=aim_l1,
            aim_l2=aim_l2,
            pms_cat=pms_map.get(pn),
        )
        rows.append(row)

    rows.sort(key=lambda r: (
        0 if r["action"] in {"spa_cut", "cut_to_band"} else 1,
        r["delta_vs_quality"] if r["delta_vs_quality"] is not None else 9,
        r["pn"],
    ))

    scored_by_pn = {r["pn"]: r for r in rows}
    mix = book_mix(book_all, scored_by_pn, bvp_alts, is_bvp, aim)

    n_captive = sum(1 for r in rows if r["captive_flag"] == "captive")
    n_comp = sum(1 for r in rows if r["captive_flag"] == "competitive")
    n_t1 = sum(1 for r in rows if r["captive_flag"] == "t1_only")
    n_pads = sum(1 for r in rows if r["family"] == "brake_pad")
    n_cut = sum(1 for r in rows if r["action"] in {"cut_to_band", "spa_cut"})
    n_spa = sum(1 for r in rows if r["spa_candidate"])
    n_sys_unknown = sum(1 for r in rows if r["system_role"] == "unknown")
    rev_scored = sum((r["book_cy2025_eur"] or 0) for r in rows)

    fam_agg = {}
    for r in rows:
        fam_agg.setdefault(r["family"], {"family": r["family"], "label": r["family_label"],
                                         "pns": 0, "tightness": r["tightness"],
                                         "t4_eff": effective_ceiling(4, r["family"]),
                                         "t3_eff": effective_ceiling(3, r["family"])})
        fam_agg[r["family"]]["pns"] += 1
    families = sorted(fam_agg.values(), key=lambda x: (x["tightness"], -x["pns"]))

    offers = {
        "isze": sum(1 for r in rows if r["offers"]["isze"]),
        "bvp": sum(1 for r in rows if r["offers"]["bvp"]),
        "named_iam": sum(1 for r in rows if r["offers"]["named_iam"]),
        "t1_listing": sum(1 for r in rows if r["offers"]["t1_listing"]),
    }
    role_counts = {}
    for r in rows:
        role_counts[r["system_label"]] = role_counts.get(r["system_label"], 0) + 1

    actions = {}
    for r in rows:
        actions[r["action"]] = actions.get(r["action"], 0) + 1

    ladder = []
    for tier, label, ex in [
        (4, "OE / premium IAM", "Bosch, Delphi, Febi, Denso"),
        (3, "Mainstream IAM", "Blue Print, Kavo, Triscan"),
        (2, "Budget IAM", "Ridex, Remsa, NB Parts"),
        (1, "No-name / unmapped", "KS unnamed listings"),
    ]:
        ladder.append({
            "tier": tier,
            "code": f"T{tier}",
            "label": label,
            "example": ex,
            "ceiling_pct": CEILING_PCT[tier],
            "pad_ceiling_pct": effective_ceiling(tier, "brake_pad"),
            "filter_ceiling_pct": effective_ceiling(tier, "oil_filter"),
            "compresses_isze": tier >= 3,
        })

    sold_disp = ", ".join(str(x) for x in cfg["sold_to"])
    d = {
        "meta": {
            "pilot": cfg["short"],
            "db_key": db_key,
            "db_short": cfg["short"],
            "db_display": cfg["display"],
            "country": cfg["country"],
            "gps_label": cfg["gps_label"],
            "sold_to": cfg["sold_to"][0] if len(cfg["sold_to"]) == 1 else sold_disp,
            "sold_tos": list(cfg["sold_to"]),
            "sold_to_note": cfg["sold_to_note"],
            "not_blend": cfg["not_blend"],
            "not_uti": NOT_UTI,
            "cy": CY,
            "gbp_eur": GBP_EUR,
            "sek_eur": SEK_EUR,
            "fx_as_of": "2026-05-01",
            "scrape_as_of": "2026-08-10",
            "eucon_vintage": "PartsPool Autodoc DE/NO 2026-03-29",
            "n_scored": len(rows),
            "n_ks": sum(1 for p in pns if p in ks),
            "n_mek": sum(1 for p in pns if p in mek),
            "n_eucon_in_book": sum(1 for p in pns if p in eucon),
            "n_captive": n_captive,
            "n_competitive": n_comp,
            "n_t1_only": n_t1,
            "n_pads": n_pads,
            "n_cut": n_cut,
            "n_spa": n_spa,
            "n_system_unknown": n_sys_unknown,
            "rev_scored_eur": r2(rev_scored),
            "rev_book_eur": r2(float(book_all["rev_eur"].sum()) if len(book_all) else 0.0),
            "n_book": int(len(book_all)),
            "ks_placeholder_gbp": KS_PLACEHOLDER_GBP,
        },
        "rows": rows,
        "mix": mix,
        "families": families,
        "ladder": ladder,
        "offers": offers,
        "role_counts": [{"label": k, "n": v} for k, v in sorted(role_counts.items(), key=lambda x: -x[1])],
        "actions": [{"action": k, "n": v} for k, v in actions.items()],
        "pms_capture": load_pms_capture(db_key),
        "ceiling": CEILING_PCT,
        "tightness": FAMILY_TIGHTNESS,
        "channel": channel_meta(),
        "points": [
            {
                "code": "ISZE net",
                "label": POINT_ISZE,
                "observed": True,
                "factor": 1.0,
            },
            {
                "code": "DB sell",
                "label": (
                    f"ISZE net × {DB_FACTOR:.2f} (+{DB_MARKUP*100:.0f}% DB markup). "
                    "Pricing-engine channel rule — not observed SPA terms."
                ),
                "observed": False,
                "factor": DB_FACTOR,
            },
            {
                "code": "DLR sell",
                "label": (
                    f"DB sell × {DLR_FACTOR:.3f} (+{DLR_MARKUP*100:.1f}% DLR markup). "
                    "Same rule. Projected, not observed."
                ),
                "observed": False,
                "factor": DLR_FACTOR,
            },
            {
                "code": "Projected retail",
                "label": "Equals DLR sell — no extra retail markup in local files. Compare to IAM (retail vs trade flagged).",
                "observed": False,
                "factor": CHANNEL_FACTOR,
            },
        ],
    }
    d["conclusion"] = build_conclusion(d)
    return d


def score_umi() -> dict:
    return score_db("UMI")
