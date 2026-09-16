#!/usr/bin/env python
"""Build INTERNAL UMI SPA proposed-price dashboard.

Not the customer operating dashboard. Proposed ISZE→DB prices stay here.
Does not edit render_dashboard.py or UMI_Operating_Dashboard.html.

    python build_umi_spa_proposed_prices.py
"""
from __future__ import annotations

import json
import os
import re
from datetime import date
from pathlib import Path

import pandas as pd

ISZE = Path(r"C:\Users\jerom\Desktop\claude\ISZE")
DERIVED = ISZE / "01_data" / "00_derived"
SCRAPER = ISZE / "04_tools" / "autodoc_scraper"
UI = ISZE / "02_dashboards" / "_ui"
OUT_DIR = ISZE / "02_dashboards" / "spa_internal"
OUT_HTML = OUT_DIR / "UMI_SPA_Proposed_Prices.html"
OUT_CMD = OUT_DIR / "OPEN_UMI_SPA_Proposed_Prices.cmd"

SOLD_TO_UMI = 1797
CY = 2025
GBP_EUR = 1.17
SEK_EUR = 0.089
QUALITY_TIERS = {3, 4}
CUT_GAP = 0.40
CUT_FACTOR = 0.80
CEILING = {4: 30, 3: 60, 2: 150, 1: 250}

POINT_ISZE = "ISZE → DB (net, PR00 IE40)"
POINT_KS = "IAM trade (KS International, ex-VAT)"
POINT_MEK = "IAM retail (Mekonomen.se)"
POINT_EUCON = "IAM list / workshop mix (Eucon 2023 survey, DE/NO)"

# Brand families used only to flag Mekonomen title/search noise.
# _norm_brand("Lesjöfors") → "LESJ FORS" because ö is stripped.


def r2(x):
    if x is None or (isinstance(x, float) and pd.isna(x)):
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


def load_brand_lookup() -> dict:
    t = pd.read_csv(SCRAPER / "iam_brand_tiers.csv")
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
        "brands": ", ".join(parts[:10]),
        "best_brand": best["brand"],
        "best_tier": int(best["tier"]),
        "ceiling_pct": CEILING.get(int(best["tier"]), 250),
        "n_mapped": mapped,
        "quality": int(best["tier"]) in QUALITY_TIERS,
        "unmapped": mapped == 0,
    }


def iam_cheaper_frac(isze: float, iam: float) -> float | None:
    """(ISZE − IAM) / ISZE. Positive = IAM cheaper than ISZE."""
    if not isze or isze <= 0 or iam is None or iam <= 0:
        return None
    return (isze - iam) / isze


def price_only_title(title: str) -> bool:
    t = str(title or "").strip()
    if not t:
        return True
    return bool(re.fullmatch(r"[\d\s.,]+kr\.?", t, flags=re.I))


def mek_suspect(description: str, brand: str, titles: str, cheaper: float | None) -> str | None:
    """Return a human reason if Mekonomen search looks like a mismatch. Else None."""
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


def load_umi_book(pns: list[str]) -> pd.DataFrame:
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
    umi = sf[
        (sf["sold_to_sap"] == SOLD_TO_UMI)
        & (sf["year"] == CY)
        & (sf["saty"] != "CR")
        & (sf["pn"].isin(pns))
    ]
    g = umi.groupby("pn", as_index=False).agg(
        qty=("billed_qty", "sum"),
        rev_eur=("net_sales_value", "sum"),
        description=("description", "first"),
    )
    return g.set_index("pn")


def load_bvp() -> tuple[dict[str, list[str]], set[str]]:
    xref = pd.read_csv(DERIVED / "genuine_bvp_crossref.csv")
    xref["genuine_pn"] = xref["genuine_pn"].map(norm_pn)
    xref["bvp_pn"] = xref["bvp_pn"].map(norm_pn)
    alts: dict[str, list[str]] = {}
    for _, rw in xref.iterrows():
        if not rw.genuine_pn or not rw.bvp_pn:
            continue
        alts.setdefault(rw.genuine_pn, [])
        if rw.bvp_pn not in alts[rw.genuine_pn]:
            alts[rw.genuine_pn].append(rw.bvp_pn)
    is_bvp = set(xref["bvp_pn"]) - {""}
    return alts, is_bvp


def load_eucon(lookup: dict) -> dict[str, dict]:
    df = pd.read_csv(DERIVED / "eucon_price_gap.csv")
    df["pn"] = df["pn"].map(norm_pn)
    out = {}
    for _, rw in df.iterrows():
        br = score_brand_list(rw.get("Brands_Found") or "", lookup)
        out[rw.pn] = {
            "source": "Eucon 2023 survey",
            "point": POINT_EUCON,
            "like_for_like": False,
            "like_for_like_flag": "Not like-for-like",
            "like_for_like_why": (
                "Both sides sit near list vs IE40, but this is a 2023 DE/NO IAM survey "
                "against genuine OEM — not UMI, not the same commercial point."
            ),
            "iam_min_eur": r2(rw.Min_Competitor_EUR),
            "iam_avg_eur": r2(rw.Avg_Competitor_EUR),
            "iam_max_eur": r2(rw.Max_Competitor_EUR),
            "competitor_count": int(rw.Competitor_Count) if pd.notna(rw.Competitor_Count) else 0,
            "url": "",
            "scraped_at": "2023 survey",
            "titles": "",
            "fx": "survey EUR as published",
            **br,
        }
    return out


def classify_auto365_title(name: str) -> str:
    n = (name or "").lower()
    families = [
        ("lighting", ("פנס", "light", "lamp", "headlamp", "fog")),
        ("body_panel", ("מגן", "bumper", "דלת", "door", "כנף", "mirror", "ראי")),
        ("filter", ("פילטר", "מסנן", "filter")),
        ("brake", ("בלם", "brake", "pad", "disc", "רוטור")),
        ("engine", ("מנוע", "engine", "turbo", "טורבו")),
        ("cooling", ("רדיאטור", "radiator", "מים")),
        ("electrical", ("מצבר", "battery", "אלטרנטור", "sensor")),
    ]
    for fam, keys in families:
        if any(k.lower() in n for k in keys):
            return fam
    return "other"


def load_auto365_family() -> dict:
    fam = pd.read_csv(DERIVED / "iam_israel_street.csv")
    families = fam.to_dict(orient="records")
    raw = pd.read_csv(SCRAPER / "auto365_results.csv")
    raw["family"] = raw["Product_Name"].astype(str).apply(classify_auto365_title)
    examples = []
    for family, g in raw.groupby("family"):
        row = g.iloc[0]
        examples.append({
            "family": family,
            "title": str(row.Product_Name)[:80],
            "ils": r2(row.Price),
            "eur_indicative": r2(row.Price_EUR),
            "url": str(row.Product_URL or ""),
        })
    examples.sort(key=lambda x: x["family"])
    return {
        "n_rows": int(len(raw)),
        "pn_join": False,
        "fx_note": (
            "ILS→EUR 0.25 is a scraper placeholder. Quote shekels when briefing; "
            "euro is indicative only."
        ),
        "families": [
            {
                "family": r["family"],
                "n": int(r["n"]),
                "min_eur": r2(r["min_eur"]),
                "avg_eur": r2(r["avg_eur"]),
                "max_eur": r2(r["max_eur"]),
                "median_ils": r2(r["median_ils"]),
            }
            for r in families
        ],
        "example_urls": examples[:8],
        "scraped_at": "2026-08-10",
    }


def build_payload() -> dict:
    lookup = load_brand_lookup()
    ks = pd.read_csv(DERIVED / "iam_ks_price_gap.csv", dtype={"pn": str})
    mek = pd.read_csv(DERIVED / "iam_mekonomen_price_gap.csv", dtype={"pn": str})
    ks["pn"] = ks["pn"].map(norm_pn)
    mek["pn"] = mek["pn"].map(norm_pn)
    ks_u = ks[ks["db"].astype(str).str.upper() == "UMI"].copy()
    mek_u = mek[mek["db"].astype(str).str.upper() == "UMI"].copy()

    pns = sorted(set(ks_u["pn"]) | set(mek_u["pn"]))
    book = load_umi_book(pns)
    bvp_alts, is_bvp = load_bvp()
    eucon = load_eucon(lookup)

    rows = []
    for pn in pns:
        sources = []
        desc = ""
        isze = None
        isze_src = "IE40_PR00"

        ks_row = ks_u[ks_u["pn"] == pn]
        if len(ks_row):
            rw = ks_row.iloc[0]
            desc = str(rw.description)
            isze = r2(rw.isze_price_eur)
            isze_src = str(rw.isze_price_source)
            br = score_brand_list(rw.get("brands_found") or "", lookup)
            # KS does not name IAM brands — force unmapped T1 unless brands actually present
            if not str(rw.get("brands_found") or "").strip():
                br = score_brand_list("", lookup)
            cheaper = iam_cheaper_frac(float(rw.isze_price_eur), float(rw.ks_am_avg_eur))
            sources.append({
                "source": "KS International",
                "point": POINT_KS,
                "like_for_like": False,
                "like_for_like_flag": "Not like-for-like",
                "like_for_like_why": (
                    "ISZE is net-to-distributor (PR00). KS is IAM trade, ex-VAT, "
                    f"GBP × {GBP_EUR}."
                ),
                "iam_min_eur": r2(rw.ks_am_min_eur),
                "iam_avg_eur": r2(rw.ks_am_avg_eur),
                "iam_max_eur": None,
                "competitor_count": int(rw.competitor_count) if pd.notna(rw.competitor_count) else 0,
                "url": str(rw.ks_url or ""),
                "scraped_at": str(rw.scraped_at or ""),
                "titles": str(rw.scrape_titles or "")[:240],
                "fx": f"GBP_EUR={GBP_EUR} (1 May 2026). Ex-VAT.",
                "cheaper_frac": None if cheaper is None else round(cheaper, 4),
                "suspect": None,
                **br,
            })

        mek_row = mek_u[mek_u["pn"] == pn]
        if len(mek_row):
            rw = mek_row.iloc[0]
            desc = desc or str(rw.description)
            isze = isze if isze is not None else r2(rw.isze_price_eur)
            isze_src = isze_src or str(rw.isze_price_source)
            br = score_brand_list(rw.get("brands_found") or "", lookup)
            cheaper = iam_cheaper_frac(float(rw.isze_price_eur), float(rw.mek_am_avg_eur))
            sus = mek_suspect(str(rw.description), br.get("best_brand") or "", str(rw.scrape_titles or ""), cheaper)
            sources.append({
                "source": "Mekonomen",
                "point": POINT_MEK,
                "like_for_like": False,
                "like_for_like_flag": "Not like-for-like",
                "like_for_like_why": (
                    "ISZE is net-to-distributor (PR00). Mekonomen.se is IAM retail, "
                    f"SEK × {SEK_EUR}. Search quality is noisy."
                ),
                "iam_min_eur": r2(rw.mek_am_min_eur),
                "iam_avg_eur": r2(rw.mek_am_avg_eur),
                "iam_max_eur": None,
                "competitor_count": int(rw.competitor_count) if pd.notna(rw.competitor_count) else 0,
                "url": str(rw.mek_url or ""),
                "scraped_at": str(rw.scraped_at or ""),
                "titles": str(rw.scrape_titles or "")[:240],
                "fx": f"SEK_EUR={SEK_EUR} (1 May 2026).",
                "cheaper_frac": None if cheaper is None else round(cheaper, 4),
                "suspect": sus,
                **br,
            })

        if pn in eucon:
            e = dict(eucon[pn])
            cheaper = iam_cheaper_frac(isze or 0, e["iam_avg_eur"] or 0)
            e["cheaper_frac"] = None if cheaper is None else round(cheaper, 4)
            e["suspect"] = None
            sources.append(e)

        # Quality comparable: T3/T4, not suspect. Eucon may map a brand onto a KS-only row.
        quality_hits = [
            s for s in sources
            if s.get("quality") and not s.get("suspect") and s.get("cheaper_frac") is not None
        ]
        # Prefer the quality source with a real brand name
        quality_hits = [s for s in quality_hits if s.get("n_mapped", 0) > 0]
        best_q = None
        if quality_hits:
            best_q = max(quality_hits, key=lambda s: (s.get("best_tier") or 0, s.get("cheaper_frac") or -9))

        cheaper_vals = [s["cheaper_frac"] for s in sources if s.get("cheaper_frac") is not None]
        cheaper_any = max(cheaper_vals) if cheaper_vals else None

        alts = bvp_alts.get(pn) or []
        itself_bvp = pn in is_bvp
        in_crossref = pn in bvp_alts or itself_bvp

        q_cheaper = best_q.get("cheaper_frac") if best_q else None
        isze_above_quality = bool(best_q and q_cheaper is not None and q_cheaper > 0)

        auto_cut = bool(
            best_q
            and q_cheaper is not None
            and q_cheaper >= CUT_GAP
            and best_q.get("best_tier") in QUALITY_TIERS
            and not itself_bvp
        )
        proposed = r2((isze or 0) * CUT_FACTOR) if auto_cut and isze else None

        spa = bool(
            (not itself_bvp)
            and (len(alts) == 0)
            and isze_above_quality
        )

        if auto_cut:
            action = "cut20"
            proposed_label = f"€{proposed:.2f}"
            proposed_note = (
                f"Quality IAM ({best_q['best_brand']} T{best_q['best_tier']}) is "
                f"{q_cheaper*100:.0f}% cheaper than ISZE net-to-DB. Rule: cut 20%."
            )
        elif itself_bvp or alts:
            action = "has_bvp"
            proposed_label = "—"
            proposed_note = "Best Value already exists in the crossref — not a SPA."
        elif cheaper_any is not None and cheaper_any <= 0:
            action = "isze_cheaper"
            proposed_label = "—"
            proposed_note = "ISZE net-to-DB is not above the observed IAM offer."
        elif any(s.get("suspect") for s in sources) and not best_q:
            action = "suspect"
            proposed_label = "Review"
            proposed_note = "IAM hit looks like a search mismatch — no auto-cut."
        elif isze_above_quality:
            action = "review"
            proposed_label = "Review"
            proposed_note = (
                "Quality IAM is cheaper, but the gap is under 40% — no auto-cut."
            )
        elif cheaper_any is not None and cheaper_any > 0:
            action = "review"
            proposed_label = "Review"
            proposed_note = (
                "IAM is cheaper, but the brand is unmapped (T1) or not quality T3/T4. "
                "KS does not name brands — the 40%→cut-20% rule does not auto-fire."
            )
        else:
            action = "isze_cheaper"
            proposed_label = "—"
            proposed_note = "ISZE net-to-DB is not above the observed IAM offer."

        if spa and action == "review":
            action = "spa_review"

        book_rev = float(book.loc[pn, "rev_eur"]) if pn in book.index else 0.0
        book_qty = float(book.loc[pn, "qty"]) if pn in book.index else 0.0
        if not desc and pn in book.index:
            desc = str(book.loc[pn, "description"])

        rows.append({
            "pn": pn,
            "description": desc.strip(),
            "isze_eur": isze,
            "isze_point": POINT_ISZE,
            "isze_source": isze_src,
            "umi_cy2025_eur": r2(book_rev),
            "umi_cy2025_qty": r2(book_qty),
            "sources": sources,
            "quality_brand": (best_q or {}).get("best_brand") or "",
            "quality_tier": (best_q or {}).get("best_tier"),
            "quality_source": (best_q or {}).get("source") or "",
            "quality_iam_eur": (best_q or {}).get("iam_avg_eur"),
            "quality_cheaper_frac": None if q_cheaper is None else round(q_cheaper, 4),
            "display_cheaper_frac": round(q_cheaper, 4) if q_cheaper is not None else (
                round(cheaper_any, 4) if cheaper_any is not None else None
            ),
            "auto_cut": auto_cut,
            "proposed_isze_eur": proposed,
            "proposed_label": proposed_label,
            "proposed_note": proposed_note,
            "action": action,
            "spa_candidate": spa,
            "bvp_alts": alts,
            "itself_bvp": itself_bvp,
            "in_crossref": in_crossref,
            "crossref_caveat": (not in_crossref),
            "not_like_for_like": True,
        })

    rows.sort(key=lambda r: (-(r["display_cheaper_frac"] or -9), r["pn"]))

    n_cut = sum(1 for r in rows if r["auto_cut"])
    n_spa = sum(1 for r in rows if r["spa_candidate"])
    n_review = sum(1 for r in rows if r["action"] in {"review", "spa_review", "suspect"})
    n_suspect = sum(1 for r in rows if r["action"] == "suspect")
    rev_cut = sum((r["umi_cy2025_eur"] or 0) for r in rows if r["auto_cut"])
    rev_all = sum((r["umi_cy2025_eur"] or 0) for r in rows)

    auto365 = load_auto365_family()

    return {
        "meta": {
            "title": "UMI — proposed ISZE prices",
            "subtitle": "Internal SPA workbench. Not the customer operating screen.",
            "as_of": date.today().isoformat(),
            "pilot": "UMI",
            "sold_to": SOLD_TO_UMI,
            "not_uti": 1799,
            "n_scored": len(rows),
            "n_ks": int(len(ks_u)),
            "n_mek": int(len(mek_u)),
            "n_cut": n_cut,
            "n_spa": n_spa,
            "n_review": n_review,
            "n_suspect": n_suspect,
            "rev_scored_eur": r2(rev_all),
            "rev_cut_eur": r2(rev_cut),
            "cut_gap": CUT_GAP,
            "cut_factor": CUT_FACTOR,
            "gbp_eur": GBP_EUR,
            "sek_eur": SEK_EUR,
            "fx_as_of": "2026-05-01",
            "scrape_as_of": "2026-08-10",
            "cy": CY,
        },
        "points": [
            {"code": "ISZE→DB", "label": POINT_ISZE, "observed": True},
            {"code": "DB→DLR", "label": "Distributor → dealer — not observed on this dashboard", "observed": False},
            {"code": "DLR→WS", "label": "Dealer → workshop — not observed on this dashboard", "observed": False},
            {"code": "IAM", "label": "IAM trade / retail / 2023 list — observed, different point", "observed": True},
        ],
        "ladder": [
            {"tier": "T4", "label": "OE / premium IAM", "ceiling": "+30%", "ex": "Bosch, Raufoss, Lesjöfors"},
            {"tier": "T3", "label": "Mainstream IAM", "ceiling": "+60%", "ex": "Blue Print, GSP, NTY"},
            {"tier": "T2", "label": "Budget IAM", "ceiling": "+150%", "ex": "NB Parts, Ridex"},
            {"tier": "T1", "label": "No-name / unmapped", "ceiling": "+250%", "ex": "KS unnamed listings"},
        ],
        "rows": rows,
        "auto365": auto365,
        "kpis": [
            {
                "id": "scored",
                "label": "UMI PNs scored",
                "value": str(len(rows)),
                "sub": f"{len(ks_u)} KS + {len(mek_u)} Mekonomen",
                "tip": (
                    "Count of distinct UMI (sold-to 1797) part numbers with a usable "
                    "KS or Mekonomen IAM price after dropping no-results and the "
                    "£2 placeholder. Snapshot 10 Aug 2026. Not included: UTI, Auto 365 "
                    "(no OEM PN), Autodoc risk file."
                ),
            },
            {
                "id": "cut",
                "label": "Proposed 20% cut",
                "value": str(n_cut),
                "sub": "quality IAM ≥40% cheaper",
                "tip": (
                    "Fires only when a T3/T4 brand is ≥40% cheaper than ISZE net-to-DB "
                    "and the listing is not a suspect mismatch. Proposed = current PR00 "
                    "× 0.80. KS unnamed T1 never auto-fires unless Eucon (or another "
                    "source) maps a real T3/T4 brand. Not a match-to-IAM price."
                ),
            },
            {
                "id": "spa",
                "label": "SPA candidates",
                "value": str(n_spa),
                "sub": "no Best Value in crossref + ISZE above quality IAM",
                "tip": (
                    "SPA only when (1) no Best Value alternative in the crossref, "
                    "(2) the PN is not itself Best Value, (3) ISZE is dearer than a "
                    "quality T3/T4 IAM offer. Missing from the crossref is not the "
                    "same as no Best Value in the catalogue."
                ),
            },
            {
                "id": "book",
                "label": "UMI CY2025 on these PNs",
                "value": f"€{rev_all:,.0f}",
                "sub": "billed, credits excluded",
                "tip": (
                    "Calendar 2025 net billed to UMI sold-to 1797 on the scored PNs. "
                    "Credit notes excluded, not subtracted. Not a network total and "
                    "not UTI (1799)."
                ),
            },
        ],
    }


def chart_js_inline() -> str:
    raw = (UI / "chart.umd.min.js").read_text(encoding="utf-8")
    lines = [ln for ln in raw.splitlines() if "sourceMappingURL" not in ln]
    return "\n".join(lines)


def html_page(payload: dict, chart_js: str) -> str:
    meta = payload["meta"]
    payload_json = json.dumps(payload, ensure_ascii=False, separators=(",", ":"))
    # Guard against </script> breakout in JSON
    payload_json = payload_json.replace("<", "\\u003c")
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>UMI proposed ISZE prices — internal</title>
<style>
:root {{
  --navy:#15233c; --navy2:#1a2b4a; --terra:#c0552d; --paper:#f7f4ee;
  --line:#d9d3c8; --muted:#6b6256; --ink:#222;
  --good:#1d9e75; --goodt:#2e7d54; --bad:#b23b3b; --amber:#eda100;
  --blue:#2a78d6; --grey:#888780;
}}
*{{box-sizing:border-box}}
html,body{{margin:0;padding:0;background:var(--paper);color:var(--ink);
  font-family:"Segoe UI",Helvetica,Arial,sans-serif;font-size:15px;line-height:1.45}}
h1,h2,h3{{font-family:Georgia,"Times New Roman",serif;color:var(--navy);margin:0}}
.wrap{{max-width:1180px;margin:0 auto;padding:20px 22px 48px}}
.banner{{background:var(--navy);color:#f7f4ee;padding:10px 22px;font-size:12px;letter-spacing:.04em;
  display:flex;justify-content:space-between;gap:16px;flex-wrap:wrap}}
.banner b{{color:#f7f4ee}}
.banner span{{color:#d9d3c8}}
.hero{{background:linear-gradient(155deg,#15233c 0%,#203759 62%,#2b4a78 100%);
  color:#f7f4ee;padding:28px 22px 26px;margin:0 0 18px}}
.hero h1{{color:#fff;font-size:32px;line-height:1.12}}
.hero .rule{{width:72px;height:3px;background:var(--terra);margin:12px 0 14px}}
.hero p{{margin:0;max-width:62ch;color:#eef1f6;font-size:15px}}
.kpis{{display:grid;grid-template-columns:repeat(4,1fr);gap:12px;margin:18px 0 8px}}
.kpi{{background:#fff;border:1px solid var(--line);border-radius:8px;padding:14px 16px;
  cursor:pointer;position:relative}}
.kpi .lbl{{font-size:11px;text-transform:uppercase;letter-spacing:.06em;color:var(--muted)}}
.kpi .val{{font-family:Georgia,serif;font-size:28px;color:var(--navy);margin-top:4px}}
.kpi .sub{{font-size:12px;color:var(--muted);margin-top:2px}}
.kpi[data-tip]:hover::after,.kpi[data-tip]:focus::after{{
  content:attr(data-tip);position:absolute;left:12px;right:12px;top:calc(100% + 8px);
  background:var(--navy);color:#f7f4ee;border-top:3px solid var(--terra);
  padding:10px 12px;border-radius:0 0 6px 6px;font-size:12px;line-height:1.4;
  z-index:40;box-shadow:0 8px 24px rgba(21,35,60,.25);white-space:normal}}
.sec{{margin:28px 0 10px}}
.sec h2{{font-size:22px;padding-bottom:8px;border-bottom:2px solid var(--navy)}}
.sec h2 .no{{color:var(--terra)}}
.lead{{color:var(--muted);margin:8px 0 14px;max-width:78ch}}
.card{{background:#fff;border:1px solid var(--line);border-radius:8px;padding:16px 18px}}
.grid2{{display:grid;grid-template-columns:1.4fr .8fr;gap:14px}}
.chain{{display:grid;grid-template-columns:repeat(4,1fr);gap:10px;margin:8px 0 4px}}
.ch{{border-radius:8px;padding:12px 14px;min-height:92px}}
.ch.on{{background:var(--navy);color:#f7f4ee}}
.ch.off{{background:#eef3f9;color:#222;border:1px dashed var(--line)}}
.ch .k{{font-size:11px;text-transform:uppercase;letter-spacing:.05em;opacity:.85}}
.ch .t{{font-family:Georgia,serif;font-size:16px;margin-top:4px}}
.ch .d{{font-size:12px;margin-top:6px;line-height:1.35}}
.ch.on .t,.ch.on .k,.ch.on .d{{color:#f7f4ee}}
.flag{{display:inline-block;font-size:11px;font-weight:600;padding:2px 8px;border-radius:999px;
  letter-spacing:.03em}}
.flag.nl{{background:#f4d7cc;color:#7a2e16}}
.flag.cut{{background:#c0552d;color:#f7f4ee}}
.flag.rev{{background:#f3e2b3;color:#5c4300}}
.flag.ok{{background:#d5efe6;color:#1a5c45}}
.flag.spa{{background:#15233c;color:#f7f4ee}}
.flag.bvp{{background:#e8e4dc;color:#222}}
.flag.sus{{background:#888780;color:#fff}}
.filters{{display:flex;gap:8px;flex-wrap:wrap;margin:0 0 12px}}
.filters button{{background:#fff;border:1px solid var(--line);color:var(--navy);
  padding:6px 12px;border-radius:999px;cursor:pointer;font:inherit;font-size:13px}}
.filters button.on{{background:var(--navy);color:#f7f4ee;border-color:var(--navy)}}
.tblwrap{{overflow-x:auto;border:1px solid var(--line);border-radius:8px}}
table.pns{{width:100%;border-collapse:collapse;font-size:13px;min-width:960px}}
table.pns thead th{{background:#15233c;color:#f7f4ee;text-align:left;padding:9px 10px;
  font-size:11px;text-transform:uppercase;letter-spacing:.04em;position:sticky;top:0;z-index:2}}
table.pns td{{padding:9px 10px;border-bottom:1px solid var(--line);color:#222;vertical-align:top}}
table.pns tbody tr:nth-child(even) td{{background:#f7f4ee;color:#222}}
table.pns tbody tr:nth-child(odd) td{{background:#fff;color:#222}}
table.pns a{{color:var(--blue);text-decoration:none;border-bottom:1px solid #c5d8f0}}
.src{{font-size:12px;color:var(--muted);margin-top:4px}}
.mono{{font-variant-numeric:tabular-nums}}
.pn{{font-family:Consolas,"Courier New",monospace;font-size:13px;font-weight:600}}
.callout{{border-left:3px solid var(--terra);background:#fff;padding:12px 14px;margin:12px 0}}
.ladder td,.ladder th{{padding:8px 10px}}
.chartbox{{position:relative;width:100%;height:520px}}
.chartbox.sm{{height:260px}}
.foot{{margin-top:36px;padding-top:12px;border-top:1px solid var(--line);
  font-size:12px;color:var(--muted)}}
@media(max-width:900px){{
  .kpis,.grid2,.chain{{grid-template-columns:1fr}}
  .hero h1{{font-size:26px}}
}}
</style>
</head>
<body>
<div class="banner">
  <b>INTERNAL · proposed ISZE → distributor prices</b>
  <span>UMI sold-to {meta['sold_to']} · not the customer operating dashboard · not UTI {meta['not_uti']}</span>
</div>
<div class="hero">
  <h1>UMI — what ISZE should charge the distributor</h1>
  <div class="rule"></div>
  <p>Eleven UMI part numbers with an observed IAM offer. Every price is labelled on the chain
  ISZE → DB → dealer → retail. Points that do not match stay on screen and are flagged
  <b>not like-for-like</b>. A 20% cut is proposed only when a quality T3/T4 brand is at least
  40% cheaper than ISZE net-to-DB.</p>
</div>
<div class="wrap">

<div class="kpis" id="kpis"></div>

<section class="sec">
  <h2><span class="no">1 · </span>Pricing points — say them out loud</h2>
  <p class="lead">ISZE list is net-to-distributor. Scrapers sit further down the chain (IAM trade or retail).
  We still show the row. We never treat those euros as the same commercial point.</p>
  <div class="chain" id="chain"></div>
</section>

<section class="sec">
  <h2><span class="no">2 · </span>How much cheaper is the IAM offer?</h2>
  <p class="lead">Bar = (ISZE net-to-DB − IAM observed) ÷ ISZE. The terracotta line is the 40% auto-cut gate.
  Positive = IAM cheaper. Colour is the action, not a rainbow.</p>
  <div class="card">
    <div class="chartbox"><canvas id="gapChart" role="img" aria-label="IAM cheaper than ISZE net-to-distributor, per UMI part number">IAM gap ranking</canvas></div>
  </div>
</section>

<section class="sec">
  <h2><span class="no">3 · </span>Proposed price to ISZE</h2>
  <p class="lead">Filter the working list. Hover a KPI chip for the formula. Source links open the listing that produced the IAM price.</p>
  <div class="filters" id="filters"></div>
  <div class="tblwrap">
    <table class="pns" id="tbl">
      <thead>
        <tr>
          <th>PN / part</th>
          <th>ISZE → DB</th>
          <th>IAM offer (point labelled)</th>
          <th>Gap</th>
          <th>Like-for-like</th>
          <th>Proposed ISZE→DB</th>
          <th>SPA</th>
        </tr>
      </thead>
      <tbody></tbody>
    </table>
  </div>
</section>

<section class="sec">
  <h2><span class="no">4 · </span>Quality ladder (policy)</h2>
  <p class="lead">Same ceilings as the pricing engine: T4 +30% / T3 +60% / T2 +150% / T1 +250%.
  Auto-cut uses quality T3/T4 only — never a no-name T1.</p>
  <div class="grid2">
    <div class="card">
      <div class="chartbox sm"><canvas id="actionChart" role="img" aria-label="Count of UMI part numbers by proposed action">Action mix</canvas></div>
    </div>
    <div class="card">
      <table class="pns ladder">
        <thead><tr><th>Tier</th><th>Quality</th><th>Ceiling vs IAM</th><th>On this file</th></tr></thead>
        <tbody>
          <tr><td>T4</td><td>OE / premium IAM</td><td class="mono">+30%</td><td>Raufoss, Lesjöfors — Mekonomen hits flagged suspect</td></tr>
          <tr><td>T3</td><td>Mainstream IAM</td><td class="mono">+60%</td><td>GSP / NTY / Borg &amp; Beck via Eucon on the driveshaft</td></tr>
          <tr><td>T2</td><td>Budget IAM</td><td class="mono">+150%</td><td>NB Parts (Mekonomen house brand)</td></tr>
          <tr><td>T1</td><td>Unmapped / no-name</td><td class="mono">+250%</td><td>KS listings — no brand name, no auto-cut</td></tr>
        </tbody>
      </table>
    </div>
  </div>
</section>

<section class="sec">
  <h2><span class="no">5 · </span>Auto 365 — family only, no OEM PN</h2>
  <p class="lead">Local catalogue context for UMI. There is no OEM part-number join. Do not read these bars as a PN gap.
  Euro converted at a 0.25 placeholder — quote shekels.</p>
  <div class="card">
    <div class="chartbox sm"><canvas id="a365Chart" role="img" aria-label="Auto 365 catalogue average euro by part family, indicative FX">Auto 365 families</canvas></div>
    <div class="src" id="a365links"></div>
  </div>
</section>

<div class="callout">
  <b>FX and vintage.</b> KS: GBP × 1.17, ex-VAT, scrape 10 Aug 2026, rate dated 1 May 2026.
  Mekonomen: SEK × 0.089, same rate date. Eucon is a 2023 DE/NO survey vs IE40 list — closer to list-vs-list
  but not UMI and not current. Auto 365 ILS × 0.25 is a placeholder. KS unnamed brands stay T1.
  Mekonomen titles that are only a kronor figure are treated as suspect search noise.
</div>

<p class="foot">
  Internal SPA workbench for UMI (sold-to 1797). Not the customer operating dashboard.
  Sources: KS International trade listings (10 Aug 2026); Mekonomen.se (10 Aug 2026);
  Eucon 2023 IAM survey vs IE40 list; UMI calendar-2025 billed (credits excluded);
  Best Value crossref; Auto 365 family catalogue (no OEM PN). Brand quality from the IAM tier table.
  FX GBP 1.17 / SEK 0.089 as of 1 May 2026. Built {meta['as_of']}.
</p>
</div>
<script>{chart_js}</script>
<script type="application/json" id="payload">{payload_json}</script>
<script>
(function(){{
  var P = JSON.parse(document.getElementById('payload').textContent);
  var ink = '#222', grid = '#e1e0d9';
  var ACTION = {{
    cut20: {{label:'20% cut', color:'#c0552d', flag:'cut'}},
    spa_review: {{label:'SPA · review', color:'#15233c', flag:'spa'}},
    review: {{label:'Review', color:'#eda100', flag:'rev'}},
    suspect: {{label:'Suspect listing', color:'#888780', flag:'sus'}},
    has_bvp: {{label:'Has Best Value', color:'#6b6256', flag:'bvp'}},
    isze_cheaper: {{label:'ISZE not above IAM', color:'#1d9e75', flag:'ok'}}
  }};
  function eur(v){{
    if(v===null||v===undefined) return '—';
    return '€' + Number(v).toLocaleString('en-GB', {{minimumFractionDigits:2, maximumFractionDigits:2}});
  }}
  function pct(f){{
    if(f===null||f===undefined) return '—';
    return (f*100).toLocaleString('en-GB', {{maximumFractionDigits:0}}) + '%';
  }}
  function el(html){{
    var d=document.createElement('div'); d.innerHTML=html.trim(); return d.firstChild;
  }}

  P.kpis.forEach(function(k){{
    document.getElementById('kpis').appendChild(el(
      '<div class="kpi" tabindex="0" data-tip="'+k.tip.replace(/"/g,'&quot;')+'">'+
      '<div class="lbl">'+k.label+'</div><div class="val">'+k.value+'</div>'+
      '<div class="sub">'+k.sub+'</div></div>'
    ));
  }});
  P.points.forEach(function(p){{
    document.getElementById('chain').appendChild(el(
      '<div class="ch '+(p.observed?'on':'off')+'"><div class="k">'+(p.observed?'Observed':'Not on this file')+
      '</div><div class="t">'+p.code+'</div><div class="d">'+p.label+'</div></div>'
    ));
  }});

  var filt = 'all';
  var filters = [
    ['all','All '+P.rows.length],
    ['cut20','20% cut'],
    ['spa','SPA candidates'],
    ['review','Review / suspect'],
    ['isze_cheaper','ISZE not above IAM']
  ];
  var fbar = document.getElementById('filters');
  filters.forEach(function(pair,i){{
    var b=document.createElement('button');
    b.textContent=pair[1]; b.dataset.f=pair[0]; if(i===0) b.className='on';
    b.onclick=function(){{
      filt=pair[0];
      Array.prototype.forEach.call(fbar.children, function(x){{ x.className = x.dataset.f===filt?'on':''; }});
      renderTable();
    }};
    fbar.appendChild(b);
  }});

  function showRow(r){{
    if(filt==='all') return true;
    if(filt==='cut20') return r.auto_cut;
    if(filt==='spa') return r.spa_candidate;
    if(filt==='review') return r.action==='review'||r.action==='spa_review'||r.action==='suspect';
    if(filt==='isze_cheaper') return r.action==='isze_cheaper';
    return true;
  }}
  function srcBlock(s){{
    var url = s.url ? ' · <a href="'+s.url+'" target="_blank" rel="noopener">Open listing</a>' : '';
    var brand = s.best_brand ? (s.best_brand+' T'+s.best_tier) : 'brand unmapped T1';
    var sus = s.suspect ? '<div class="src">Suspect: '+s.suspect+'</div>' : '';
    return '<div><b>'+s.source+'</b> · '+s.point+'<div class="src">'+
      eur(s.iam_avg_eur)+(s.iam_min_eur&&s.iam_min_eur!==s.iam_avg_eur?' (min '+eur(s.iam_min_eur)+')':'')+
      ' · '+brand+' · '+s.fx+url+'</div>'+sus+'</div>';
  }}
  function renderTable(){{
    var tb=document.querySelector('#tbl tbody'); tb.innerHTML='';
    P.rows.filter(showRow).forEach(function(r){{
      var a=ACTION[r.action]||ACTION.review;
      var spa = r.spa_candidate
        ? '<span class="flag spa">SPA candidate</span>'+(r.crossref_caveat?'<div class="src">Not in crossref — that is not “no Best Value in the catalogue”.</div>':'')
        : (r.bvp_alts&&r.bvp_alts.length
            ? '<span class="flag bvp">Best Value in crossref</span><div class="src">'+r.bvp_alts.join(', ')+'</div>'
            : '<span class="flag bvp">Not SPA</span>'+(r.crossref_caveat?'<div class="src">Crossref has no Best Value row. Incomplete ≠ none in catalogue.</div>':''));
      var gap = r.display_cheaper_frac===null ? '—' :
        (r.display_cheaper_frac>=0 ? pct(r.display_cheaper_frac)+' IAM cheaper' : pct(-r.display_cheaper_frac)+' ISZE cheaper');
      var prop = r.auto_cut
        ? '<span class="flag cut">'+r.proposed_label+'</span><div class="src">'+r.proposed_note+'</div>'
        : '<span class="flag '+a.flag+'">'+r.proposed_label+'</span><div class="src">'+r.proposed_note+'</div>';
      var tr=document.createElement('tr');
      tr.innerHTML =
        '<td><div class="pn">'+r.pn+'</div>'+r.description+
          '<div class="src">UMI CY2025 '+eur(r.umi_cy2025_eur)+' · qty '+r.umi_cy2025_qty+'</div></td>'+
        '<td class="mono">'+eur(r.isze_eur)+'<div class="src">'+r.isze_point+'</div></td>'+
        '<td>'+r.sources.map(srcBlock).join('')+'</td>'+
        '<td class="mono">'+gap+'</td>'+
        '<td><span class="flag nl">Not like-for-like</span><div class="src">'+r.sources[0].like_for_like_why+'</div></td>'+
        '<td>'+prop+'</td>'+
        '<td>'+spa+'</td>';
      tb.appendChild(tr);
    }});
  }}
  renderTable();

  var labels = P.rows.map(function(r){{ return r.pn.slice(-4)+'  '+r.description.split(';')[0]; }});
  var data = P.rows.map(function(r){{ return r.display_cheaper_frac===null?0:Math.round(r.display_cheaper_frac*1000)/10; }});
  var cols = P.rows.map(function(r){{ return (ACTION[r.action]||ACTION.review).color; }});
  var thresh = {{
    id:'gate',
    afterDraw:function(ch){{
      var x=ch.scales.x.getPixelForValue(40), y=ch.scales.y;
      var c=ch.ctx; c.save(); c.strokeStyle='#c0552d'; c.lineWidth=2; c.setLineDash([5,4]);
      c.beginPath(); c.moveTo(x,y.top); c.lineTo(x,y.bottom); c.stroke();
      c.fillStyle='#c0552d'; c.font='11px Segoe UI,sans-serif'; c.fillText('40% auto-cut gate', x+6, y.top+12);
      c.restore();
    }}
  }};
  new Chart(document.getElementById('gapChart'), {{
    type:'bar',
    data:{{labels:labels, datasets:[{{data:data, backgroundColor:cols, borderRadius:3, barThickness:22}}]}},
    options:{{
      indexAxis:'y', responsive:true, maintainAspectRatio:false,
      plugins:{{legend:{{display:false}}, tooltip:{{callbacks:{{
        label:function(ctx){{
          var v=ctx.parsed.x;
          return v>=0 ? v+'% IAM cheaper than ISZE net-to-DB' : (-v)+'% ISZE cheaper';
        }}
      }}}}}},
      scales:{{
        x:{{min:-100, max:100, ticks:{{color:ink, callback:function(v){{return v+'%';}}}}, grid:{{color:grid}},
           title:{{display:true, text:'ISZE cheaper ←  0  → IAM cheaper than ISZE net-to-DB', color:'#6b6256'}}}},
        y:{{ticks:{{color:ink, font:{{size:11}}}}, grid:{{display:false}}}}
      }}
    }},
    plugins:[thresh]
  }});

  var mixMap = {{cut20:0, spa_review:0, review:0, suspect:0, has_bvp:0, isze_cheaper:0}};
  P.rows.forEach(function(r){{ mixMap[r.action] = (mixMap[r.action]||0)+1; }});
  var mixLabels = Object.keys(ACTION).filter(function(k){{ return mixMap[k]; }});
  new Chart(document.getElementById('actionChart'), {{
    type:'bar',
    data:{{
      labels: mixLabels.map(function(k){{ return ACTION[k].label; }}),
      datasets:[{{data:mixLabels.map(function(k){{ return mixMap[k]; }}),
        backgroundColor:mixLabels.map(function(k){{ return ACTION[k].color; }}),
        borderRadius:3, barThickness:22}}]
    }},
    options:{{
      indexAxis:'y', responsive:true, maintainAspectRatio:false,
      plugins:{{legend:{{display:false}}}},
      scales:{{
        x:{{beginAtZero:true, max:8, ticks:{{color:ink, stepSize:1}}, grid:{{color:grid}}}},
        y:{{ticks:{{color:ink}}, grid:{{display:false}}}}
      }}
    }}
  }});

  var fam = P.auto365.families;
  new Chart(document.getElementById('a365Chart'), {{
    type:'bar',
    data:{{
      labels: fam.map(function(f){{ return f.family+' ('+f.n+')'; }}),
      datasets:[{{data:fam.map(function(f){{ return f.avg_eur; }}),
        backgroundColor:'#2a78d6', borderRadius:3, barThickness:22}}]
    }},
    options:{{
      indexAxis:'y', responsive:true, maintainAspectRatio:false,
      plugins:{{legend:{{display:false}}, tooltip:{{callbacks:{{
        label:function(ctx){{ return 'Avg €'+ctx.parsed.x+' (indicative FX 0.25) · median ₪'+fam[ctx.dataIndex].median_ils; }}
      }}}}}},
      scales:{{
        x:{{beginAtZero:true, ticks:{{color:ink, callback:function(v){{ return '€'+v; }}}}, grid:{{color:grid}}}},
        y:{{ticks:{{color:ink}}, grid:{{display:false}}}}
      }}
    }}
  }});
  var links = document.getElementById('a365links');
  links.innerHTML = 'Example catalogue pages (family, not a PN match): ' +
    P.auto365.example_urls.slice(0,5).map(function(e){{
      return e.url ? '<a href="'+e.url+'" target="_blank" rel="noopener">'+e.family+'</a>' : e.family;
    }}).join(' · ') + '. ' + P.auto365.fx_note;
}})();
</script>
</body>
</html>
"""


def write_cmd() -> None:
    OUT_CMD.write_text(
        '@echo off\r\nstart "" "%~dp0UMI_SPA_Proposed_Prices.html"\r\n',
        encoding="ascii",
    )


def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    payload = build_payload()
    html = html_page(payload, chart_js_inline())
    OUT_HTML.write_text(html, encoding="utf-8")
    write_cmd()
    m = payload["meta"]
    print("UMI SPA proposed prices (internal)")
    print(f"  HTML  {OUT_HTML}")
    print(f"  CMD   {OUT_CMD}")
    print(f"  UMI PNs scored: {m['n_scored']}  (KS {m['n_ks']} + Mekonomen {m['n_mek']})")
    print(f"  20% proposed cuts: {m['n_cut']}")
    print(f"  SPA candidates: {m['n_spa']}")
    print(f"  UMI CY2025 on scored set: €{m['rev_scored_eur']:,.2f}")
    for r in payload["rows"]:
        print(
            f"    {r['pn']}  {r['action']:12}  cheaper={r['display_cheaper_frac']}  "
            f"proposed={r['proposed_isze_eur']}  spa={r['spa_candidate']}"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
