"""Street / brand-quality / Auto365 / IDS / hero / empty-states for the operating ledger.

Called from build_ledger.py immediately before reconciliation.
Never invents a PN join for Auto 365 — that catalog is not OEM-indexed.
"""
from __future__ import annotations

import json
import os
import re
import sys
from html import unescape

import pandas as pd

from db_open_items import face_open_lead, open_items_for

ISZE = r"C:\Users\jerom\Desktop\claude\ISZE"
DERIVED = os.path.join(ISZE, "01_data", "00_derived")
TIERS_CSV = os.path.join(ISZE, "04_tools", "autodoc_scraper", "iam_brand_tiers.csv")
AUTO365 = os.path.join(ISZE, "04_tools", "autodoc_scraper", "auto365_results.csv")
IDS_DIR = os.path.join(ISZE, "02_dashboards", "ids")

# Pricing-engine Mode A policy ladder (same numbers as the readiness dashboard).
BRAND_CEILINGS = [
    {"tier": 4, "label": "OE / premium IAM", "ceiling_pct": 30,
     "example": "Bosch, Denso, Delphi, Febi, Hengst"},
    {"tier": 3, "label": "Mainstream IAM", "ceiling_pct": 60,
     "example": "Blue Print, DT Spare Parts, Kavo"},
    {"tier": 2, "label": "Budget IAM", "ceiling_pct": 150,
     "example": "Ridex, Kamoka, Stark"},
    {"tier": 1, "label": "No-name / CN", "ceiling_pct": 250,
     "example": "Unmapped brands default here"},
]
CEILING_BY_TIER = {t["tier"]: t["ceiling_pct"] for t in BRAND_CEILINGS}

# Projected ISZE retail = PR00 × DB 1.40 × DLR 1.275. Do not copy the yaml key name into HTML.
CHANNEL_DB_FACTOR = 1.40
CHANNEL_DLR_FACTOR = 1.275
CHANNEL_COMBINED = 1.785
CHANNEL_AS_OF = "config.yaml v1.0.0 · quality-premium yaml as_of 2026-08-10"
PROBE_IAM_KIND = {
    "ks": ("trade", "IAM trade vs projected retail — still not perfect like-for-like"),
    "mekonomen": ("retail", "IAM retail vs projected retail — closer, still a different shop"),
    "eucon": ("mix", "PartsPool Autodoc DE/NO online IAM (2026-03-29) vs projected retail — still not perfect like-for-like"),
    "eucon_uk_2023": ("workshop", "UK IAM workshop 2023 vs projected retail — vintage trade, not a 2026 shop crawl"),
}

# Auto 365 is Hebrew product titles, no OEM PN. Family from the title only.
_AUTO365_FAMILIES = [
    ("lighting", ("פנס", "light", "lamp", "headlamp", "fog")),
    ("body_panel", ("מגן", "bumper", "דלת", "door", "כנף", "mirror", "ראי")),
    ("filter", ("פילטר", "מסנן", "filter")),
    ("brake", ("בלם", "brake", "pad", "disc", "רוטור")),
    ("engine", ("מנוע", "engine", "turbo", "טורבו")),
    ("cooling", ("רדיאטור", "radiator", "מים")),
    ("electrical", ("מצבר", "battery", "אלטרנטור", "sensor")),
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


def tip(formula, snapshot, not_included, warning=None):
    out = {"formula": formula, "snapshot": snapshot, "not_included": not_included}
    if warning:
        out["warning"] = warning
    return out


def like_for_like_note(kind, existing=None):
    if kind == "trade":
        return "IAM trade vs projected retail — still not perfect like-for-like"
    if kind == "retail":
        return "IAM retail vs projected retail — closer, still a different shop"
    if kind == "mix":
        return "IAM list/workshop mix vs projected retail — still not perfect like-for-like"
    if kind == "workshop":
        return "UK IAM workshop 2023 vs projected retail — vintage trade, not a 2026 shop crawl"
    return existing


def stamp_projected_retail(row):
    """Attach projected retail and rewrite display Δ% to vs projected retail (not vs net)."""
    net = row.get("isze_price_eur")
    if net is None:
        net = row.get("isze_eur")
    iam = row.get("competitor_avg_eur")
    if iam is None:
        iam = row.get("quality_iam_eur")
    pr = None
    if net is not None:
        try:
            pr = round(float(net) * CHANNEL_COMBINED, 2)
        except (TypeError, ValueError):
            pr = None
    if pr is None and row.get("proj_retail_eur") is not None:
        pr = row.get("proj_retail_eur")
    row["proj_retail_eur"] = pr
    if row.get("delta_vs_isze_net_pct") is None and row.get("delta_pct") is not None:
        row["delta_vs_isze_net_pct"] = row.get("delta_pct")
    dlt = None
    if pr and iam is not None:
        try:
            if float(pr) != 0:
                dlt = round(100.0 * (float(iam) - float(pr)) / float(pr), 1)
        except (TypeError, ValueError):
            dlt = None
    if dlt is None and row.get("gap_vs_proj_retail") is not None:
        try:
            dlt = round(100.0 * float(row["gap_vs_proj_retail"]), 1)
        except (TypeError, ValueError):
            dlt = None
    row["delta_vs_proj_retail_pct"] = dlt
    if dlt is not None:
        row["delta_pct"] = dlt
        row["isze_exposed"] = bool(dlt < 0)
    probe = row.get("probe") or ""
    kind, note = PROBE_IAM_KIND.get(probe, (row.get("iam_point_kind"), None))
    if kind:
        row["iam_point_kind"] = kind
        row["iam_like_for_like_note"] = note or like_for_like_note(kind, row.get("iam_point_note"))
    elif row.get("iam_point_kind"):
        row["iam_like_for_like_note"] = like_for_like_note(row.get("iam_point_kind"), row.get("iam_point_note"))
    return row


def _norm_brand(s: str) -> str:
    s = str(s or "").upper()
    s = s.replace("&", " ").replace("+", " ").replace("AMP", " ")
    s = re.sub(r"[^A-Z0-9]+", " ", s)
    return re.sub(r"\s+", " ", s).strip()


def load_brand_lookup():
    if not os.path.exists(TIERS_CSV):
        return {}
    t = pd.read_csv(TIERS_CSV)
    lookup = {}
    for _, rw in t.iterrows():
        key = _norm_brand(rw.brand)
        lookup[key] = {
            "brand": str(rw.brand),
            "tier": int(rw.tier) if pd.notna(rw.tier) else 1,
            "oe_supplier": bool(int(rw.oe_supplier)) if pd.notna(rw.oe_supplier) else False,
            "notes": str(rw.notes) if pd.notna(rw.get("notes")) else "",
        }
    return lookup


def score_brands(brands_found: str, lookup: dict):
    if not brands_found or not isinstance(brands_found, str):
        return None
    parts = [p.strip() for p in brands_found.split(",") if p.strip()]
    scored = []
    for p in parts:
        hit = lookup.get(_norm_brand(p))
        if hit:
            scored.append(hit)
        else:
            scored.append({"brand": p, "tier": 1, "oe_supplier": False, "notes": "unmapped — treated as T1"})
    if not scored:
        return None
    best = max(scored, key=lambda x: (x["tier"], x["oe_supplier"]))
    ceiling = CEILING_BY_TIER.get(best["tier"], 250)
    return {
        "n_brands": len(parts),
        "n_mapped": sum(1 for s in scored if s["tier"] > 1 or s.get("notes") != "unmapped — treated as T1"),
        "best_brand": best["brand"],
        "best_tier": best["tier"],
        "oe_supplier": best["oe_supplier"],
        "ceiling_pct": ceiling,
        "brands_excerpt": ", ".join(p for p in parts[:8]),
    }


def classify_auto365_title(name: str) -> str:
    n = (name or "").lower()
    for fam, keys in _AUTO365_FAMILIES:
        if any(k.lower() in n for k in keys):
            return fam
    return "other"


def build_auto365_street():
    """Category-level Israel street. No PN key exists — do not invent one."""
    if not os.path.exists(AUTO365):
        return {"available": False, "reason": "Auto 365 scrape file is missing."}
    df = pd.read_csv(AUTO365)
    n = len(df)
    priced = df[pd.to_numeric(df.get("Price_EUR"), errors="coerce").notna()].copy()
    priced["family"] = priced["Product_Name"].astype(str).apply(classify_auto365_title)
    fams = []
    for fam, g in priced.groupby("family"):
        fams.append({
            "family": fam,
            "n": int(len(g)),
            "min_eur": r2(g.Price_EUR.min()),
            "avg_eur": r2(g.Price_EUR.mean()),
            "max_eur": r2(g.Price_EUR.max()),
            "median_ils": r2(pd.to_numeric(g.Price, errors="coerce").median()),
        })
    fams.sort(key=lambda x: -x["n"])
    out_csv = os.path.join(DERIVED, "iam_israel_street.csv")
    os.makedirs(DERIVED, exist_ok=True)
    pd.DataFrame(fams).to_csv(out_csv, index=False)
    scraped = None
    if "Scraped_At" in priced.columns and len(priced):
        scraped = str(priced.Scraped_At.max())
    return {
        "available": True,
        "pn_join": False,
        "label": "Auto 365 — local aftermarket catalogue (category, not PN)",
        "n_priced_rows": int(len(priced)),
        "n_rows_in_scrape": int(n),
        "scraped_at": scraped,
        "fx_note": "ILS→EUR 0.25 is an approximate placeholder in the scraper. Quote ILS when briefing; EUR is indicative only.",
        "families": fams,
        "why_no_pn": "Auto 365 is not indexed by Isuzu OEM part number. A PN-shaped gap file would be fabricated. Family-level local catalogue only.",
        "quality_note": "Auto 365 sells certified new aftermarket (Ministry of Transport approved), not salvage. Distinct from a breakers yard.",
    }


def extract_ids_os(ids_key: str | None) -> dict:
    """v0.4 rollup OS — hit list, next steps, Pull scaffold. Render never recomputes."""
    if not ids_key:
        return {"available": False}
    path = os.path.join(
        ISZE, "09_meetings", "IDS_2026_DB_Feedback_Sheet_v0.4",
        ids_key, f"IDS_2026_DB_Rollup_{ids_key}_v0.4.html",
    )
    if not os.path.exists(path):
        return {"available": False}
    html = open(path, encoding="utf-8").read()
    hit_chunk = re.search(
        r"Hit list — priority dealers to visit(.*?)Incomplete / not-completed lane",
        html, re.S,
    )
    hits = []
    if hit_chunk:
        for m in re.finditer(
            r'<td class="num">(\d+)</td><td><a href="([^"]+)">([^<]+)</a></td>'
            r'<td class="num">([0-9.]+)%</td><td class="num">([^<]+)</td>'
            r'<td><span class="pill[^"]*">([^<]+)</span></td><td>([^<]*)</td>',
            hit_chunk.group(1),
        ):
            hits.append({
                "rank": int(m.group(1)),
                "annex": m.group(2),
                "name": unescape(m.group(3)),
                "score_pct": float(m.group(4)),
                "vs_avg": unescape(m.group(5)).strip(),
                "band": unescape(m.group(6)).strip(),
                "why": unescape(m.group(7)).strip(),
            })
    inc_chunk = re.search(
        r"Incomplete / not-completed lane(.*?)Average basis",
        html, re.S,
    )
    incomplete = []
    incomplete_none = True
    if inc_chunk:
        body = inc_chunk.group(1)
        incomplete_none = "None." in body
        if not incomplete_none:
            for m in re.finditer(
                r"<td>([^<]+)</td><td class=\"num\">([^<]+)</td>"
                r"<td><span class=\"pill[^\"]*\">([^<]+)</span></td><td>([^<]*)</td>",
                body,
            ):
                incomplete.append({
                    "name": unescape(m.group(1)),
                    "score": unescape(m.group(2)).strip(),
                    "band": unescape(m.group(3)).strip(),
                    "reason": unescape(m.group(4)).strip(),
                })
    steps = []
    for m in re.finditer(
        r'<tr class="suggest"><td class="num">(\d+)</td><td class="action">([^<]+)</td>',
        html,
    ):
        steps.append({"n": int(m.group(1)), "action": unescape(m.group(2)).strip()})
    pull = []
    pull_chunk = re.search(r"Pull scorecard — monthly return.*?</table>", html, re.S)
    if pull_chunk:
        for m in re.finditer(
            r"<tr><td>([^<]+)</td><td class=\"num fill\"[^>]*>.*?</td><td>([^<]+)</td>",
            pull_chunk.group(0),
        ):
            pull.append({
                "metric": unescape(m.group(1)).strip(),
                "definition": unescape(m.group(2)).strip(),
            })
    avg_m = re.search(
        r'<div class="v">([0-9.]+)%</div>\s*<div class="l">Network average</div>'
        r'\s*<div class="n">(\d+) of (\d+) dealers in average</div>',
        html,
    )
    below_m = re.search(r"(\d+) of (\d+) dealers \((\d+)%\) currently below the market average", html)
    return {
        "available": True,
        "version": "v0.4",
        "country_avg_pct": float(avg_m.group(1)) if avg_m else None,
        "in_average": int(avg_m.group(2)) if avg_m else None,
        "evaluated": int(avg_m.group(3)) if avg_m else None,
        "below_average_n": int(below_m.group(1)) if below_m else None,
        "below_average_of": int(below_m.group(2)) if below_m else None,
        "hit_list": hits,
        "incomplete": incomplete,
        "incomplete_none": incomplete_none,
        "next_steps": steps,
        "pull_metrics": pull,
        "one_liner": (
            "Use the hit list to visit, agree three to five actions, pull monthly. "
            "Do not treat a higher dealer-standard score as a parts-sales forecast."
        ),
        "annex_root": (
            f"../IDS_2026_DB_Feedback_Sheet_v0.4/{ids_key}/"
        ),
    }


def extract_ids(ids_key: str | None):
    if not ids_key:
        return {"available": False, "reason": "No IDS country pack for this distributor."}
    # File names: IDS_2026_dealer_compare_Israel_LCV.html
    candidates = [
        os.path.join(IDS_DIR, f"IDS_2026_dealer_compare_{ids_key}.html"),
        os.path.join(IDS_DIR, f"IDS_2026_dealer_compare_{ids_key.replace('_', ' ')}.html"),
    ]
    path = next((p for p in candidates if os.path.exists(p)), None)
    if not path:
        return {"available": False, "reason": f"IDS pack '{ids_key}' not found on disk."}
    text = open(path, encoding="utf-8").read()
    m = re.search(r"const DATA = (\{.*?\});", text, re.S)
    if not m:
        return {"available": False, "reason": "IDS HTML has no embedded DATA object."}
    D = json.loads(m.group(1))
    sections = {s["id"]: s["label"] for s in D.get("sections", [])}
    dealers = D.get("dealers") or []
    sec_ids = list(sections)
    country = {"A": [], "B": [], "C": [], "D": [], "E": []}
    matrix = []
    e_q = [q for q in D.get("questions", []) if q.get("section") == "E"]
    e_max = sum(float(q.get("max") or 0) for q in e_q)
    for dlr in dealers:
        row = {"name": dlr.get("name"), "total_pct": r2((dlr.get("total_pct") or 0) * 100)}
        for sid in sec_ids:
            s = (dlr.get("sections") or {}).get(sid) or {}
            pct = r2((s.get("pct") or 0) * 100)
            row[sid] = pct
            if sid in country:
                country[sid].append(s)
        matrix.append(row)
    summary = []
    for sid in ["A", "B", "C", "D", "E"]:
        sample = country[sid][:1]
        net = r2((sample[0].get("network_avg_pct") or 0) * 100) if sample else None
        ctry = r2((sample[0].get("country_avg_pct") or 0) * 100) if sample else None
        n_zero = sum(1 for s in country[sid] if (s.get("score") or 0) == 0)
        n_all = len(country[sid])
        summary.append({
            "section": sid,
            "label": sections.get(sid, sid),
            "country_avg_pct": ctry,
            "network_avg_pct": net,
            "vs_network_pp": r2((ctry or 0) - (net or 0)) if ctry is not None and net is not None else None,
            "dealers_at_zero": n_zero,
            "dealers": n_all,
            "all_zero": n_zero == n_all and n_all > 0,
        })
    e = next((s for s in summary if s["section"] == "E"), None)
    dsec = next((s for s in summary if s["section"] == "D"), None)
    scored = [s for s in summary if not s.get("all_zero")]
    lead = dsec if dsec and not dsec.get("all_zero") else (scored[0] if scored else None)
    if scored:
        lead = min(scored, key=lambda s: s.get("vs_network_pp") if s.get("vs_network_pp") is not None else 0)
    e_fill = "not_scored" if (e and e.get("all_zero")) else "scored"
    d_pp = (dsec or {}).get("vs_network_pp")
    if e_fill == "not_scored":
        e_board = f"0/{int(e_max) if e_max else 27}"
        e_prose = "Not scored / participation to confirm — a flat 0% is not a vehicle-sales fail."
    else:
        e_board = f"{e.get('country_avg_pct')}%" if e and e.get("country_avg_pct") is not None else "scored"
        e_prose = (e.get("label") if e else "Vehicle sales") + " — scored in this market"
    return {
        "available": True,
        "pack": ids_key,
        "dealer_count": len(dealers),
        "section_e_questions": len(e_q),
        "section_e_points_max": int(e_max) if e_max else 27,
        "section_d_vs_network_pp": d_pp,
        "section_e": {
            "all_zero": bool(e and e["all_zero"]),
            "scoreboard": e_board,
            "fill": e_fill,
            "prose": e_prose,
        },
        "lead_section": (lead or {}).get("section") if lead else "D",
        "lead_label": (lead or {}).get("label"),
        "lead_vs_network_pp": (lead or {}).get("vs_network_pp"),
        "summary": summary,
        "matrix": matrix,
        "os": extract_ids_os(ids_key),
        "source_note": "IDS 2026 dealer compare pack. Network average is the full IDS network, anonymous.",
    }


def spa_cta_allowed(row):
    """SPA only when projected retail is above a named T3/T4 IAM.

    If Best Value is sufficient (or we are already cheaper at retail), no SPA.
    If Best Value exists but is not enough vs named T3/T4, SPA on genuine is the next lever.
    """
    if row.get("is_itself_a_bvp_pn") or row.get("itself_bvp") or row.get("action") == "is_bvp":
        return False
    verd = row.get("bvp_verdict")
    if verd == "bvp_sufficient":
        return False
    proj = row.get("proj_retail_eur")
    iam = row.get("quality_iam_eur")
    if iam is None:
        iam = row.get("competitor_avg_eur")
    if proj is not None and iam is not None:
        try:
            if float(proj) <= float(iam):
                return False
        except (TypeError, ValueError):
            pass
    if verd != "bvp_not_enough":
        if row.get("bvp_alts") or row.get("action") == "has_bvp" or row.get("bvp_alternative_in_crossref"):
            return False
    tier = row.get("quality_tier")
    try:
        if int(tier) not in (3, 4):
            return False
    except (TypeError, ValueError):
        return False
    if proj is None or iam is None:
        return False
    try:
        return float(proj) > float(iam)
    except (TypeError, ValueError):
        return False


def spa_cta_text(row):
    if not spa_cta_allowed(row):
        return None
    proposed = row.get("proposed_isze_eur")
    if proposed:
        try:
            return f"Please apply for an SPA — proposed ISZE net up to €{float(proposed):.2f}"
        except (TypeError, ValueError):
            pass
    return "Please apply for an SPA"


def spa_lever(row, iam_row):
    """SPA only when aftermarket evidence says ISZE is dearer at retail.

    Best Value sufficient → push BVP (never red). BVP not enough → SPA on genuine.
    Already cheaper at projected retail → Hold, never an SPA button.
    """
    if row.get("is_shell_lubricant"):
        return "EXCLUDED FROM GPS — Shell lubricant"
    verd = row.get("bvp_verdict")
    if verd == "bvp_not_enough":
        return "BVP not enough — SPA on genuine vs named T3/T4, not just offer Best Value"
    if verd == "bvp_sufficient" or row.get("bvp_alternative_in_crossref"):
        return "push Best Value — crossref alternative exists"
    if row.get("is_itself_a_bvp_pn"):
        return "already the value tier — this PN IS the BVP"
    if iam_row and iam_row.get("delta_pct") is not None:
        if iam_row["delta_pct"] < 0:
            return "SPA candidate — no BVP in crossref AND ISZE above projected retail vs named IAM"
        return "no SPA — ISZE is cheaper at projected retail vs named IAM"
    return "no SPA yet — no aftermarket evidence that we are more expensive"


_IE40 = None
_PMS_MAP = None
_PROBE_AS_OF = {
    "eucon": {"as_of": "2026-03-29", "outdated": True,
              "as_of_note": "PartsPool Autodoc DE/NO 2026-03-29 — not the 2023 UK survey"},
    "eucon_uk_2023": {"as_of": "2023 UK IAM workshop", "outdated": True,
                      "as_of_note": "Eucon UK IAM Price Survey 2023 — workshop GBP, outdated"},
    "ks": {"as_of": None, "outdated": False, "as_of_note": None},
    "mekonomen": {"as_of": None, "outdated": False, "as_of_note": None},
}
FILTER_FIRST = ["oil_filter", "air_filter", "fuel_filter", "blower_filter"]
BRAKE_NEXT = ["brake_pad", "brake_shoe", "brake_rotor"]
FAMILY_SORT = FILTER_FIRST + BRAKE_NEXT


def load_ie40_pr00():
    global _IE40
    if _IE40 is not None:
        return _IE40
    path = os.path.join(DERIVED, "pricing_pr00_ie40.parquet")
    if not os.path.exists(path):
        _IE40 = pd.Series(dtype=float)
        return _IE40
    pr = pd.read_parquet(path, columns=["part_number", "sp_eur", "price_condition"])
    pr = pr[pr["price_condition"].astype(str).str.upper() == "PR00"]
    pr["pn"] = pr["part_number"].astype(str)
    pr["sp_eur"] = pd.to_numeric(pr["sp_eur"], errors="coerce")
    pr = pr[(pr["pn"] != "") & (pr["sp_eur"] > 0)]
    _IE40 = pr.drop_duplicates("pn").set_index("pn")["sp_eur"]
    return _IE40


def pms_category_map():
    global _PMS_MAP
    if _PMS_MAP is not None:
        return _PMS_MAP
    path = os.path.join(DERIVED, "parts_catalog_dimension.csv")
    out = {}
    if os.path.exists(path):
        cat = pd.read_csv(path, dtype={"part_number": str},
                          usecols=["part_number", "pms_category"], low_memory=False)
        cat = cat.dropna(subset=["pms_category"])
        cat = cat[cat.pms_category.astype(str).str.strip() != ""]
        out = dict(zip(cat.part_number.astype(str), cat.pms_category.astype(str)))
    _PMS_MAP = out
    return _PMS_MAP


def _unit_net(pn, ie40, realized=None):
    pn = str(pn or "")
    if pn and pn in ie40.index:
        try:
            return r2(float(ie40.loc[pn])), "IE40_PR00"
        except (TypeError, ValueError):
            pass
    if realized is not None:
        try:
            if float(realized) > 0:
                return r2(float(realized)), "realized_on_this_book"
        except (TypeError, ValueError):
            pass
    return None, "missing"


def _proj(net):
    if net is None:
        return None
    try:
        return round(float(net) * CHANNEL_COMBINED, 2)
    except (TypeError, ValueError):
        return None


def pick_quality_iam(pns, iam_hits, lookup, eng_by_pn=None):
    """Best named T3/T4 among Eucon/KS/Mekonomen hits on genuine or BVP PNs."""
    eng_by_pn = eng_by_pn or {}
    best = None
    for pn in pns:
        hit_eng = eng_by_pn.get(str(pn))
        if hit_eng and hit_eng.get("quality_tier") in (3, 4) and hit_eng.get("quality_iam_eur") is not None:
            rec = {
                "quality_brand": hit_eng.get("quality_brand"),
                "quality_tier": hit_eng.get("quality_tier"),
                "quality_source": hit_eng.get("quality_source"),
                "quality_iam_eur": hit_eng.get("quality_iam_eur"),
                "iam_point_kind": hit_eng.get("iam_point_kind"),
                "iam_like_for_like_note": like_for_like_note(
                    hit_eng.get("iam_point_kind"), hit_eng.get("iam_point_note")),
                "matched_pn": str(pn),
            }
            if best is None or (rec["quality_tier"], -(rec["quality_iam_eur"] or 0)) > (
                    best["quality_tier"], -(best["quality_iam_eur"] or 0)):
                best = rec
        for row in iam_hits.get(str(pn), []) or []:
            bq = score_brands(row.get("brands"), lookup) or {}
            tier = bq.get("best_tier") or row.get("quality_tier")
            try:
                tier = int(tier) if tier is not None else None
            except (TypeError, ValueError):
                tier = None
            if tier not in (3, 4):
                continue
            iam = row.get("quality_iam_eur")
            if iam is None:
                iam = row.get("competitor_avg_eur")
            if iam is None:
                continue
            rec = {
                "quality_brand": bq.get("best_brand") or row.get("quality_brand"),
                "quality_tier": tier,
                "quality_source": row.get("probe_label") or row.get("probe"),
                "quality_iam_eur": r2(iam),
                "iam_point_kind": row.get("iam_point_kind"),
                "iam_like_for_like_note": row.get("iam_like_for_like_note"),
                "matched_pn": str(pn),
                "probe": row.get("probe"),
            }
            if best is None or (rec["quality_tier"], -(rec["quality_iam_eur"] or 0)) > (
                    best["quality_tier"], -(best["quality_iam_eur"] or 0)):
                best = rec
    return best


def bvp_verdict_of(bvp_retail, iam_eur, iam_tier):
    """BVP sufficient if BVP projected retail ≤ quality IAM, or no named T3/T4."""
    if bvp_retail is None:
        return "unknown", "No Best Value list price on file"
    try:
        tier = int(iam_tier) if iam_tier is not None else None
    except (TypeError, ValueError):
        tier = None
    if iam_eur is None or tier not in (3, 4):
        return "bvp_sufficient", "BVP sufficient — no named T3/T4 to beat"
    try:
        if float(bvp_retail) <= float(iam_eur):
            return "bvp_sufficient", "BVP sufficient — projected retail at or below named quality IAM"
        return (
            "bvp_not_enough",
            "BVP not enough — projected retail still above named T3/T4; next lever is SPA on genuine, not just offer Best Value",
        )
    except (TypeError, ValueError):
        return "unknown", "No Best Value list price on file"


def family_action_sentence(f):
    ns = f.get("n_bvp_sufficient") or 0
    nn = f.get("n_bvp_not_enough") or 0
    nspa = f.get("n_spa") or 0
    nhold = f.get("n_hold") or 0
    if nn:
        return (
            f"BVP is not enough on {nn} pair(s) — next lever is SPA on genuine, "
            "not just offer Best Value."
        )
    if ns:
        return (
            f"Offer Best Value on {ns} pair(s) — retention sits at or below named "
            "quality IAM (or no T3/T4 on file)."
        )
    if nspa:
        return (
            f"No Best Value pair — SPA on {nspa} PN(s) where projected retail is "
            "still above named T3/T4."
        )
    if nhold:
        return (
            f"Hold — already cheaper at projected retail, or no quality IAM match "
            f"({nhold} PN(s))."
        )
    return "No Best Value pair and no named T3/T4 on this family — Hold."


def enrich_bvp_alternatives(L, iam_hits, lookup, eng_by_pn=None):
    """Stamp genuine/BVP net + projected retail, quality IAM, and BVP-sufficient verdict."""
    ie40 = load_ie40_pr00()
    blk = L["sections"].get("bvp_alternatives") or {}
    rows = blk.get("rows") or []
    n_suf = n_not = n_unk = 0
    for rec in rows:
        gen = str(rec.get("genuine_pn") or "")
        bvp_list = list(rec.get("bvp_pns") or [])
        qty = rec.get("genuine_qty_cy")
        realized = None
        if rec.get("genuine_eur_cy") and qty:
            try:
                if float(qty) != 0:
                    realized = float(rec["genuine_eur_cy"]) / float(qty)
            except (TypeError, ValueError, ZeroDivisionError):
                realized = None
        gen_net, gen_src = _unit_net(gen, ie40, realized)
        rec["genuine_isze_net_eur"] = gen_net
        rec["genuine_isze_net_source"] = gen_src
        rec["genuine_proj_retail_eur"] = _proj(gen_net)
        best_bvp_pn, best_bvp_net, best_bvp_src = None, None, "missing"
        for bp in bvp_list:
            net, src = _unit_net(bp, ie40, None)
            if net is None:
                continue
            if best_bvp_net is None or net < best_bvp_net:
                best_bvp_pn, best_bvp_net, best_bvp_src = bp, net, src
        rec["bvp_pn_priced"] = best_bvp_pn
        rec["bvp_isze_net_eur"] = best_bvp_net
        rec["bvp_isze_net_source"] = best_bvp_src
        rec["bvp_proj_retail_eur"] = _proj(best_bvp_net)
        gpr, bpr = rec["genuine_proj_retail_eur"], rec["bvp_proj_retail_eur"]
        rec["gap_genuine_vs_bvp_retail_eur"] = (
            r2(float(gpr) - float(bpr)) if gpr is not None and bpr is not None else None
        )
        rec["gap_genuine_vs_bvp_net_eur"] = (
            r2(float(gen_net) - float(best_bvp_net))
            if gen_net is not None and best_bvp_net is not None else None
        )
        q = pick_quality_iam([gen] + bvp_list, iam_hits, lookup, eng_by_pn)
        if q:
            rec["quality_brand"] = q.get("quality_brand")
            rec["quality_tier"] = q.get("quality_tier")
            rec["quality_source"] = q.get("quality_source")
            rec["quality_iam_eur"] = q.get("quality_iam_eur")
            rec["iam_point_kind"] = q.get("iam_point_kind")
            rec["iam_like_for_like_note"] = q.get("iam_like_for_like_note")
            rec["quality_matched_pn"] = q.get("matched_pn")
        else:
            rec["quality_brand"] = rec["quality_source"] = rec["iam_point_kind"] = None
            rec["quality_tier"] = rec["quality_iam_eur"] = None
            rec["iam_like_for_like_note"] = rec["quality_matched_pn"] = None
        verd, lab = bvp_verdict_of(
            rec["bvp_proj_retail_eur"], rec.get("quality_iam_eur"), rec.get("quality_tier"))
        rec["bvp_verdict"] = verd
        rec["verdict_label"] = lab
        cheaper = False
        if rec["genuine_proj_retail_eur"] is not None and rec.get("quality_iam_eur") is not None:
            try:
                cheaper = float(rec["genuine_proj_retail_eur"]) <= float(rec["quality_iam_eur"])
            except (TypeError, ValueError):
                cheaper = False
        rec["already_cheaper_at_retail"] = cheaper
        if cheaper:
            rec["lever"] = "Hold — already cheaper at projected retail; do not SPA"
            rec["spa_on_genuine"] = False
        elif verd == "bvp_not_enough":
            rec["lever"] = lab
            rec["spa_on_genuine"] = True
        elif verd == "bvp_sufficient":
            rec["lever"] = lab
            rec["spa_on_genuine"] = False
        else:
            rec["lever"] = lab
            rec["spa_on_genuine"] = False
        if verd == "bvp_sufficient":
            n_suf += 1
        elif verd == "bvp_not_enough":
            n_not += 1
        else:
            n_unk += 1
    blk["rows"] = rows
    blk["n_bvp_sufficient"] = n_suf
    blk["n_bvp_not_enough"] = n_not
    blk["n_unknown"] = n_unk
    blk["title"] = "Will Best Value be sufficient?"
    blk["lead"] = (
        "Part-number test: is the Best Value projected retail at or below a named quality IAM "
        "(T3/T4)? If yes, or if there is no quality IAM, offer Best Value — retention, never red. "
        "If Best Value is still above that T3/T4, the next lever is SPA on genuine, not just offer BVP. "
        "Do not SPA when we are already cheaper at projected retail."
    )
    blk["verdict_rule"] = {
        "bvp_sufficient": "BVP projected retail ≤ named T3/T4, or no quality IAM on file.",
        "bvp_not_enough": "BVP projected retail still above named T3/T4 — SPA on genuine, not just offer BVP.",
        "no_spa_if_cheaper": "Do not SPA when genuine projected retail is already at or below the named IAM.",
        "projected_retail": "PR00 × 1.40 × 1.275 = ×1.785",
    }
    blk["tooltip"] = {
        "formula": (
            "Genuine and Best Value ISZE net from IE40 PR00 (or realised unit on this book). "
            "Projected retail = net × 1.40 × 1.275. BVP sufficient if BVP retail ≤ named T3/T4 "
            "or no T3/T4. Gap = genuine retail − BVP retail (how much cheaper the retention offer is)."
        ),
        "snapshot": CHANNEL_AS_OF,
        "not_included": "Not an erosion euro. T1 listings do not set ‘not enough’. Unpaired genuine PNs are not listed here.",
    }
    L["sections"]["bvp_alternatives"] = blk
    return {str(r.get("genuine_pn")): r.get("bvp_verdict") for r in rows}


def rebuild_family_strategy(L, iam_hits, lookup, spa_rows, verdict_by_gen):
    """Family rollup for the meeting — not the PN BVP-sufficient table."""
    pms = L["sections"].get("pms") or {}
    cats = list(pms.get("by_category") or [])
    pms_map = pms_category_map()
    bvp_rows = (L["sections"].get("bvp_alternatives") or {}).get("rows") or []
    gen_with_bvp = {str(r.get("genuine_pn")) for r in bvp_rows}

    fam = {}
    for c in cats:
        key = c.get("pms_category")
        if not key:
            continue
        fam[key] = {
            "family": key,
            "label": c.get("label") or key,
            "billed_eur": c.get("revenue_eur"),
            "pms_capture_pct": c.get("capture_pct"),
            "pms_lcv_peer_capture_pct": c.get("lcv_peer_capture_pct"),
            "pms_vs_lcv_peer_pp": c.get("vs_lcv_peer_pp"),
            "pms_network_capture_pct": c.get("network_capture_pct"),
            "pms_gap_eur": c.get("revenue_gap_eur"),
            "n_bvp_pairs": 0,
            "n_bvp_sufficient": 0,
            "n_bvp_not_enough": 0,
            "n_spa": 0,
            "n_hold": 0,
            "pns": 0,
        }
    for r in bvp_rows:
        key = r.get("family")
        rec = fam.setdefault(key, {
            "family": key, "label": r.get("family_label") or key,
            "billed_eur": None, "pms_capture_pct": r.get("pms_capture_pct"),
            "pms_lcv_peer_capture_pct": None, "pms_vs_lcv_peer_pp": None,
            "pms_network_capture_pct": None, "pms_gap_eur": r.get("pms_gap_eur"),
            "n_bvp_pairs": 0, "n_bvp_sufficient": 0, "n_bvp_not_enough": 0,
            "n_spa": 0, "n_hold": 0, "pns": 0,
        })
        rec["n_bvp_pairs"] += 1
        rec["pns"] += 1
        if r.get("bvp_verdict") == "bvp_sufficient":
            rec["n_bvp_sufficient"] += 1
        elif r.get("bvp_verdict") == "bvp_not_enough":
            rec["n_bvp_not_enough"] += 1

    seen_spa_hold = set()
    for r in spa_rows or []:
        pn = str(r.get("pn") or "")
        if not pn or pn in seen_spa_hold:
            continue
        seen_spa_hold.add(pn)
        key = pms_map.get(pn) or r.get("family")
        if not key:
            continue
        rec = fam.setdefault(key, {
            "family": key, "label": r.get("family_label") or key,
            "billed_eur": None, "pms_capture_pct": None,
            "pms_lcv_peer_capture_pct": None, "pms_vs_lcv_peer_pp": None,
            "pms_network_capture_pct": None, "pms_gap_eur": None,
            "n_bvp_pairs": 0, "n_bvp_sufficient": 0, "n_bvp_not_enough": 0,
            "n_spa": 0, "n_hold": 0, "pns": 0,
        })
        rec["pns"] += 1
        rec["n_spa"] += 1

    for pn, hits in iam_hits.items():
        if pn in gen_with_bvp or pn in seen_spa_hold:
            continue
        key = pms_map.get(pn)
        if not key or key not in fam:
            if not key:
                continue
            fam.setdefault(key, {
                "family": key, "label": key, "billed_eur": None,
                "pms_capture_pct": None, "pms_lcv_peer_capture_pct": None,
                "pms_vs_lcv_peer_pp": None, "pms_network_capture_pct": None,
                "pms_gap_eur": None, "n_bvp_pairs": 0, "n_bvp_sufficient": 0,
                "n_bvp_not_enough": 0, "n_spa": 0, "n_hold": 0, "pns": 0,
            })
        row0 = hits[0] if hits else {}
        q = pick_quality_iam([pn], iam_hits, lookup)
        tmp = stamp_projected_retail({
            "pn": pn,
            "isze_price_eur": row0.get("isze_price_eur"),
            "quality_iam_eur": (q or {}).get("quality_iam_eur") or row0.get("competitor_avg_eur"),
            "quality_tier": (q or {}).get("quality_tier"),
            "bvp_verdict": verdict_by_gen.get(pn),
            "bvp_alts": [pn] if pn in gen_with_bvp else [],
        })
        rec = fam[key]
        rec["pns"] += 1
        if spa_cta_allowed(tmp):
            rec["n_spa"] += 1
        else:
            rec["n_hold"] += 1

    def fam_sort(x):
        famk = x["family"] or ""
        pri = FAMILY_SORT.index(famk) if famk in FAMILY_SORT else 80
        return (pri, -(x.get("billed_eur") or 0))

    families = sorted(fam.values(), key=fam_sort)
    for f in families:
        f["action"] = family_action_sentence(f)
        f["first_lever"] = f["action"]

    strat = L["sections"].get("lost_sales_strategy") or {}
    if not strat.get("available"):
        strat["available"] = True
        strat["reason"] = None
    strat["screen_role"] = (
        "Family rollup for the meeting. Part-number ‘is BVP enough?’ lives on Lost sales."
    )
    strat["most_important_lever"] = (
        "Filters first (oil / air / fuel), then brakes, then the rest. "
        "Offer Best Value where it is sufficient. SPA only where projected retail is still "
        "above named T3/T4 and Best Value is missing or not enough. Hold when already cheaper."
    )
    strat["customer_tone"] = (
        "This table is the family decision, not a repeat of the part-number BVP test. "
        "PMS capture is versus LCV peer, not only versus all-network."
    )
    strat["family_rows"] = families
    strat["counts"] = dict(strat.get("counts") or {})
    strat["counts"]["n_families_on_screen"] = len(families)
    strat["counts"]["n_priority_families"] = sum(1 for f in families if f["family"] in FAMILY_SORT)
    strat["counts"]["n_bvp_sufficient"] = sum(f["n_bvp_sufficient"] for f in families)
    strat["counts"]["n_bvp_not_enough"] = sum(f["n_bvp_not_enough"] for f in families)
    strat["counts"]["n_pn_spa"] = sum(f["n_spa"] for f in families)
    strat["counts"]["n_hold"] = sum(f["n_hold"] for f in families)
    L["sections"]["lost_sales_strategy"] = strat
    return strat


def load_extra_iam_probes(db, book_pn, book_tot, top30_pns):
    """KS + Mekonomen PN joins, this DB only. Never Auto365 PN. Never network gp_at_risk.

    delta_pct in the CSV is a fraction; ledger rows store percent (same as Eucon).
    """
    probes, extra = {}, []
    specs = [
        ("ks", "iam_ks_price_gap.csv", "ks_url", "ks_am_avg_eur", "ks_am_min_eur",
         "KS International (UK, ex-VAT)"),
        ("mekonomen", "iam_mekonomen_price_gap.csv", "mek_url", "mek_am_avg_eur", "mek_am_min_eur",
         "Mekonomen (Sweden)"),
        ("eucon_uk_2023", "eucon_uk_survey_2023_price_gap.csv",
         None, "competitor_avg_eur", "competitor_min_eur",
         "Eucon UK IAM workshop 2023 — outdated"),
    ]
    for kind, fname, url_col, avg_col, min_col, label in specs:
        path = os.path.join(DERIVED, fname)
        if not os.path.exists(path):
            probes[kind] = {"available": False, "n": 0, "reason": f"{label} join file is not on disk."}
            continue
        df = pd.read_csv(path)
        df["pn"] = df["pn"].astype(str)
        if "db" in df.columns and db:
            df = df[df["db"].astype(str) == str(db)].copy()
        elif book_pn is not None:
            df = df[df["pn"].isin(getattr(book_pn, "index", book_pn))].copy()
        else:
            df = df.iloc[0:0]
        if "competitor_count" in df.columns and len(df):
            df = df.sort_values("competitor_count", ascending=False)
        if len(df):
            df = df.drop_duplicates("pn")
        if book_pn is not None:
            df["db_rev_cy_eur"] = df["pn"].map(book_pn)
        else:
            df["db_rev_cy_eur"] = None
        cov = float(pd.to_numeric(df["db_rev_cy_eur"], errors="coerce").fillna(0).sum()) if len(df) else 0.0
        n_exp = int(df["isze_exposed"].sum()) if "isze_exposed" in df.columns and len(df) else 0
        as_of = None
        if "scraped_at" in df.columns and len(df):
            try:
                as_of = str(df["scraped_at"].dropna().astype(str).max())[:10]
            except Exception:
                as_of = None
        probes[kind] = {
            "available": bool(len(df)),
            "label": label,
            "n": int(len(df)),
            "isze_exposed_pns": n_exp,
            "db_revenue_covered_eur": r2(cov),
            "db_revenue_coverage_pct": round(100 * cov / book_tot, 2) if book_tot else None,
            "grain": "CY2025 ISZE net to this sold-to, credits excluded",
            "do_not_sum_with_other_probes": True,
            "gp_at_risk": "not attributed — source has no DB-scoped margin figure",
            "as_of": as_of,
            "outdated": False,
            "as_of_note": (f"{label} · as-of {as_of}" if as_of else label),
        }
        preset = _PROBE_AS_OF.get(kind) or {}
        if preset.get("as_of") and not probes[kind]["as_of"]:
            probes[kind]["as_of"] = preset["as_of"]
        if preset.get("outdated"):
            probes[kind]["outdated"] = True
        if preset.get("as_of_note"):
            probes[kind]["as_of_note"] = preset["as_of_note"]
        for _, rw in df.iterrows():
            url = None
            if url_col:
                url = str(rw.get(url_col) or "").strip()
                if not url.startswith("https://"):
                    url = None
            extra.append(stamp_projected_retail({
                "pn": rw.pn,
                "description": None if pd.isna(rw.get("description")) else rw.get("description"),
                "isze_price_eur": r2(rw.get("isze_price_eur")),
                "isze_price_source": None if pd.isna(rw.get("isze_price_source")) else rw.get("isze_price_source"),
                "competitor_avg_eur": r2(rw.get(avg_col)),
                "competitor_min_eur": r2(rw.get(min_col)),
                "delta_pct": round(100 * float(rw.delta_pct), 1) if pd.notna(rw.get("delta_pct")) else None,
                "competitor_count": int(rw.competitor_count) if pd.notna(rw.get("competitor_count")) else None,
                "brands": None if pd.isna(rw.get("brands_found")) else rw.get("brands_found"),
                "isze_exposed": bool(rw.isze_exposed) if pd.notna(rw.get("isze_exposed")) else None,
                "db_revenue_cy_eur": r2(rw.get("db_rev_cy_eur")),
                "in_working_set": rw.pn in (top30_pns or set()),
                "competitor_url": url,
                "probe": kind,
                "probe_label": label,
            }))
    return probes, extra


def umi_open_items():
    """Curated UMI 1797 open items. Not UTI. Not invented. Not another DB’s minutes."""
    src_mail = "Outlook mail (UMI 1797)"
    src_ap = "Action plan FY2027 (July)"
    src_bart = "Outlook · Bart UMI notes 12 Aug 2026"
    src_mins = "Outlook · ISZE–UMI minutes 27 Oct 2025"
    src_train = "Outlook · Parts training ISZE 12–13 Aug 2026"
    src_rm = "Outlook · R&M briefing 26 May 2026"
    src_cn = "Outlook · Credit Control 10 Feb 2026"
    return {
        "F_emails": {
            "available": True,
            "title": "Open issues from mail",
            "open_lead": "Universal Motors Israel · Israel",
            "source_note": "Open items from mail",
            "rows": [
                {
                    "item": "12 Aug call happened. Shelly asked ISZE to send the presentation; several issues still to review and follow up.",
                    "owner": "ISZE (Jerome)",
                    "asked_by": "Shelly Cohen",
                    "date": "2026-08-12",
                    "status": "open",
                    "source": src_mail,
                    "lane": "shelly",
                },
                {
                    "item": "After the 12 Aug call Shelly sent a Shell old-vs-target price table. Review with UMI. This screen does not propose a new ISZE price.",
                    "owner": "ISZE",
                    "asked_by": "Shelly Cohen",
                    "date": "2026-08-12",
                    "status": "open",
                    "source": src_mail,
                    "lane": "shelly",
                },
                {
                    "item": "Confirm whether the Aftersales Awards 2026 survey UMI submitted meets ISZE reporting needs, or what else is required.",
                    "owner": "ISZE (Jerome)",
                    "asked_by": "Shelly Cohen",
                    "date": "2026-08-01",
                    "status": "open",
                    "source": src_mail,
                    "lane": "shelly",
                },
                {
                    "item": "Sales-to-dealer for Isuzu parts: July figure plus a line of operational news (campaign, stock, new dealer) for the Japan report. Target cited 98% on 30/07.",
                    "owner": "UMI (Shelly / Netanel)",
                    "asked_by": "Jerome Van Der Pluym",
                    "date": "2026-07-30",
                    "status": "open",
                    "source": src_mail,
                    "lane": "shelly",
                },
                {
                    "item": "SPA programme: Netanel asked for the specific part numbers behind the YoY drop; he will consult Shelly. No PN list on file in the reply.",
                    "owner": "ISZE to send the list · UMI to decide",
                    "asked_by": "Netanel Buchnik (cc Shelly Cohen)",
                    "date": "2026-07-26",
                    "status": "open",
                    "source": src_mail,
                    "lane": "shelly",
                },
                {
                    "item": "Shell lubricants: UMI will not order at the current ISZE price. Shelly’s market read is about €2.2/L; they would review again near €2/L. This is not a proposed ISZE cut.",
                    "owner": "ISZE",
                    "asked_by": "Shelly Cohen",
                    "date": "2026-07-07",
                    "status": "open",
                    "source": src_mail,
                    "lane": "shelly",
                },
                {
                    "item": "Conference follow-up: UMI wants joint ideas on the oil business (inventory, competitiveness, purchasing with Isuzu). June StD figure was given in that mail (€190,016 that month).",
                    "owner": "UMI + ISZE",
                    "asked_by": "Shelly Cohen",
                    "date": "2026-06-30",
                    "status": "open",
                    "source": src_mail,
                    "lane": "shelly",
                },
                {
                    "item": "UMI stock scrap campaign — action-plan line (€80K sales).",
                    "owner": "ISZE (Jerome)",
                    "asked_by": "Action plan FY2027 (July)",
                    "date": "2026-07",
                    "status": "open",
                    "source": src_ap,
                    "lane": "planning",
                },
                {
                    "item": "UMI support €20K — Credit Control asked 10 Feb 2026 which incentive CN 202647076 (20K) is for (scrap vs yearly), and for the signed MOU. Lubricants 20K was already used on CN 202646681.",
                    "owner": "ISZE (Jerome)",
                    "asked_by": "Credit Control / Action plan FY2027 (July)",
                    "date": "2026-02-10",
                    "status": "open",
                    "source": src_cn,
                    "lane": "planning",
                },
            ],
        },
        "G_minutes": {
            "available": True,
            "title": "Bart follow-ups (12 Aug 2026 notes + 27 Oct 2025 minutes)",
            "body": "Follow-ups from the 12 August call and the October review.",
            "searched": [
                "Local Outlook COM across Sales, Parts, and Jerome mailbox (260 folders)",
                "Named Outlook minutes folder under archive/customers — still 0 items",
                "Inbox, Sent, Archive and Parts vehicle-customer folders — Bart from/to/cc × UMI",
                "Attachments on those threads: 12 Aug 2026 UMI notes and 27 Oct 2025 ISZE–UMI minutes",
            ],
            "rows": [
                {
                    "item": "Parts training (EDI, order types, procedures): UMI booked Wednesday 26 August, 11:00 Belgian. Bart sends the invite two days before. Netanel confirmed receipt 13 Aug. Same mail: EQ-Hit training plus the online test for dealership staff is mandatory for the Isuzu Dealer Standards awarding.",
                    "owner": "Bart Symons",
                    "asked_by": "Netanel Buchnik (cc Shelly Cohen)",
                    "date": "2026-08-13",
                    "status": "open",
                    "source": src_train,
                    "lane": "bart",
                },
                {
                    "item": "5-litre Shell oil packaging: Jerome to check availability and pricing. Shelly to send the parts/oil list; Jerome then reviews and looks at alternative suppliers. This screen does not propose an ISZE price.",
                    "owner": "ISZE (Jerome) · UMI (Shelly)",
                    "asked_by": "12 Aug UMI notes (Bart)",
                    "date": "2026-08-12",
                    "status": "open",
                    "source": src_bart,
                    "lane": "bart",
                },
                {
                    "item": "Genuine-parts-share incentive: notes cite 54.2% now vs about 57% extended target. Pending approval from Japan. Jerome to communicate status once approved.",
                    "owner": "ISZE (Jerome)",
                    "asked_by": "12 Aug UMI notes (Bart)",
                    "date": "2026-08-12",
                    "status": "open",
                    "source": src_bart,
                    "lane": "bart",
                },
                {
                    "item": "Dealer Standards: Jerome to send the overview and heat-map tool. Shelly to consider completing Section E (vehicle sales). Notes cite UMI network 60.9% vs 74.8% network average, mainly incomplete Section E.",
                    "owner": "ISZE (Jerome) · UMI (Shelly)",
                    "asked_by": "12 Aug UMI notes (Bart)",
                    "date": "2026-08-12",
                    "status": "open",
                    "source": src_bart,
                    "lane": "bart",
                },
                {
                    "item": "SPA: Shelly to propose part numbers, estimated 12-month quantities, and UMI target prices. ISZE reviews and seeks management approval. No ISZE price on this screen.",
                    "owner": "UMI (Shelly) then ISZE",
                    "asked_by": "12 Aug UMI notes (Bart)",
                    "date": "2026-08-12",
                    "status": "open",
                    "source": src_bart,
                    "lane": "bart",
                },
                {
                    "item": "R&M / fleet tenders: UMI to review the Electric Company of Israel tender and tell ISZE if special-pricing support is needed. May 2026: Nadav confirmed UMI would attend the Real Garant briefing (Bart on copy).",
                    "owner": "UMI (Shelly / Nadav) · ISZE",
                    "asked_by": "12 Aug UMI notes (Bart) / Nadav Libes",
                    "date": "2026-08-12",
                    "status": "open",
                    "source": src_bart,
                    "lane": "bart",
                },
                {
                    "item": "Sales-to-dealer extract: ISZE asked monthly part-level from 1 January 2025 (part number, invoice date, quantity; prices not required). UMI will review the request internally.",
                    "owner": "UMI (Shelly)",
                    "asked_by": "12 Aug UMI notes (Bart)",
                    "date": "2026-08-12",
                    "status": "open",
                    "source": src_bart,
                    "lane": "bart",
                },
                {
                    "item": "27 Oct 2025 minutes (still on file): lubricant wide-container supply to be reassessed; Jerome to wait before open lubricant orders; Sarah to refresh KPI reporting with Nadav; Jerome to send competitive-parts breakdown. Not restated on 12 Aug — older than the notes above.",
                    "owner": "ISZE (Jerome) · UMI",
                    "asked_by": "27 Oct 2025 minutes (Hadi / Bart on copy)",
                    "date": "2025-10-27",
                    "status": "open",
                    "source": src_mins,
                    "lane": "bart",
                },
            ],
        },
    }


def _strip_banned(s):
    """Ledger HTML forbids the word that would leak an internal label."""
    if s is None:
        return s
    t = str(s)
    t = re.sub(r"\bstreet\b", "aftermarket", t, flags=re.I)
    t = t.replace("junk", "no-name listing")
    return t


def meeting_strategy_from_engine(db: str, pms_block: dict) -> dict:
    """Slim quality-engine payload for the customer meeting. Numbers from score_db only."""
    sys.path.insert(0, os.path.join(ISZE, "04_tools", "autodoc_scraper"))
    try:
        from position_engine import score_db, DB_REGISTRY
    except Exception as e:
        return {"available": False, "reason": f"Quality engine could not load ({e})."}
    if db not in DB_REGISTRY:
        return {"available": False,
                "reason": "Quality engine is wired for UMI, ITUK, ISD (Germany) and Imotors (Portugal) only."}
    try:
        eng = score_db(db)
    except Exception as e:
        return {"available": False, "reason": f"Quality engine did not score this book ({e})."}

    pms_cap = {c.get("pms_category") or c.get("cat"): c for c in (pms_block.get("by_category") or [])}
    if not pms_cap:
        for c in (eng.get("pms_capture") or []):
            pms_cap[c.get("cat")] = {
                "pms_category": c.get("cat"), "label": c.get("label"),
                "capture_pct": c.get("capture_pct"), "revenue_gap_eur": c.get("gap_eur"),
            }

    PRIORITY = ["oil_filter", "fuel_filter", "air_filter", "blower_filter",
                "brake_pad", "brake_shoe", "brake_rotor"]
    rows = eng.get("rows") or []
    fam_map = {}
    for r in rows:
        fam = r.get("family") or "other"
        rec = fam_map.setdefault(fam, {
            "family": fam,
            "label": r.get("family_label") or fam,
            "tightness": r.get("tightness"),
            "pns": 0,
            "billed_eur": 0.0,
            "n_bvp": 0,
            "n_spa": 0,
            "n_cut": 0,
            "n_hold": 0,
            "n_t1": 0,
            "pms_capture_pct": (pms_cap.get(fam) or {}).get("capture_pct") or (pms_cap.get(fam) or {}).get("capture_pct_total"),
            "pms_gap_eur": (pms_cap.get(fam) or {}).get("revenue_gap_eur") or (pms_cap.get(fam) or {}).get("gap_eur"),
        })
        rec["pns"] += 1
        rec["billed_eur"] += float(r.get("book_cy2025_eur") or 0)
        act = r.get("action") or ""
        if act == "has_bvp":
            rec["n_bvp"] += 1
        tmp = stamp_projected_retail({
            "action": act,
            "bvp_alts": r.get("bvp_alts") or [],
            "quality_tier": r.get("quality_tier"),
            "quality_iam_eur": r.get("quality_iam_eur") or r.get("iam_offer_eur"),
            "proj_retail_eur": r.get("proj_retail_eur"),
            "isze_eur": r.get("isze_eur"),
            "isze_price_eur": r.get("isze_eur"),
        })
        if spa_cta_allowed(tmp):
            rec["n_spa"] += 1
        if act in ("cut_to_band", "spa_cut") and spa_cta_allowed(tmp):
            rec["n_cut"] += 1
        if act == "hold":
            rec["n_hold"] += 1
        if r.get("captive_flag") == "t1_only":
            rec["n_t1"] += 1
        rec["first_lever"] = (
            "Offer Best Value (retention)" if rec["n_bvp"]
            else "SPA vs named quality IAM" if rec["n_spa"]
            else "Hold — T1 listings do not set a cut" if rec["n_t1"]
            else "Hold — already cheaper than the named IAM, or no quality match"
        )

    def fam_sort(x):
        fam = x["family"]
        pri = PRIORITY.index(fam) if fam in PRIORITY else 80
        return (pri, -(x["billed_eur"] or 0))

    families = sorted(fam_map.values(), key=fam_sort)
    for f in families:
        f["billed_eur"] = r2(f["billed_eur"])

    pn_keep = []
    for r in rows:
        act = r.get("action")
        fam = r.get("family")
        keep = (
            act in ("has_bvp", "cut_to_band", "spa_cut", "spa_review")
            or (fam in PRIORITY and act in ("review", "hold") and r.get("quality_tier") in (3, 4))
        )
        if not keep:
            continue
        band = r.get("band_high_eur")
        proposed = r.get("proposed_isze_eur")
        rec = {
            "pn": r.get("pn"),
            "description": r.get("description"),
            "family": fam,
            "family_label": r.get("family_label"),
            "action": act,
            "action_label": _strip_banned(r.get("action_label")),
            "isze_eur": r.get("isze_eur"),
            "quality_brand": r.get("quality_brand"),
            "quality_tier": r.get("quality_tier"),
            "quality_iam_eur": r.get("quality_iam_eur") or r.get("iam_offer_eur"),
            "quality_source": r.get("quality_source"),
            "band_high_eur": band,
            "proposed_isze_eur": proposed,
            "billed_cy_eur": r.get("book_cy2025_eur"),
            "bvp_alts": r.get("bvp_alts") or [],
            "spa_candidate": False,
            "suspect": r.get("suspect"),
            "primary_url": r.get("primary_url") or None,
            "cta": None,
            "proposed_note": _strip_banned(r.get("proposed_note")),
            "iam_point_note": _strip_banned(r.get("iam_point_note")),
            "iam_point_kind": r.get("iam_point_kind"),
            "iam_like_for_like_note": like_for_like_note(r.get("iam_point_kind"), r.get("iam_point_note")),
            "proj_retail_eur": r.get("proj_retail_eur"),
            "delta_vs_proj_retail_pct": (
                round(100.0 * float(r["gap_vs_proj_retail"]), 1)
                if r.get("gap_vs_proj_retail") is not None else None
            ),
        }
        rec = stamp_projected_retail(rec)
        rec["spa_candidate"] = spa_cta_allowed(rec)
        rec["cta"] = spa_cta_text(rec)
        if not rec["spa_candidate"]:
            rec["proposed_isze_eur"] = None
            rec["band_high_eur"] = None
        pn_keep.append(rec)
    pn_keep.sort(key=lambda x: (
        0 if x["family"] in PRIORITY[:3] else 1 if x["family"] in PRIORITY else 2,
        0 if x["action"] == "has_bvp" else 1 if x["action"] in ("spa_cut", "cut_to_band") else 2,
        -(x["billed_cy_eur"] or 0),
    ))

    ch = eng.get("channel") or {}
    meta = eng.get("meta") or {}
    n_bvp = sum(1 for r in pn_keep if r["action"] == "has_bvp")
    n_cut = sum(1 for r in pn_keep if r["action"] in ("cut_to_band", "spa_cut"))
    n_spa = sum(1 for r in pn_keep if r["spa_candidate"])
    n_fam_priority = sum(1 for f in families if f["family"] in PRIORITY)

    return {
        "available": True,
        "most_important_lever": (
            "1) Offer Best Value where a crossref pair exists — that is retention, not a cut. "
            "2) Only then a special price, and only versus a named quality IAM (T3/T4), never a T1 listing. "
            "Projected retail uses distributor ×1.40 then dealer ×1.275 on ISZE net."
        ),
        "channel": {
            "db_factor": ch.get("db_factor"),
            "dlr_factor": ch.get("dlr_factor"),
            "combined_factor": ch.get("combined_factor"),
            "note": _strip_banned(ch.get("note")),
        },
        "counts": {
            "n_families_on_screen": len(families),
            "n_priority_families": n_fam_priority,
            "n_pn_strategy": len(pn_keep),
            "n_pn_bvp": n_bvp,
            "n_pn_cut": n_cut,
            "n_pn_spa": n_spa,
            "n_engine_scored": meta.get("n_scored"),
        },
        "family_rows": families,
        "pn_rows": pn_keep[:60],
        "customer_tone": (
            "First lever: push Best Value where a pair exists. SPA only on lines where projected "
            "ISZE retail sits above a named quality IAM (T3/T4) and there is no Best Value in the "
            "crossref. If we are already cheaper at retail, there is no SPA button — Hold."
        ),
        "rules": [
            "Sit versus the best-quality named IAM (T3/T4), not T1.",
            "T1 never auto-cuts.",
            "Pads are tighter than filters.",
            "Projected retail = PR00 × 1.40 (distributor) × 1.275 (dealer) = ×1.785 (config.yaml).",
            "SPA CTA only if projected ISZE retail > quality named IAM (T3/T4) AND no BVP in the crossref. The quality-band ceiling is not a reason to SPA when we already sit below IAM.",
        ],
        "scrape_as_of": meta.get("scrape_as_of"),
        "eucon_vintage": meta.get("eucon_vintage"),
        "pricing_reference": {
            "label": "Projected ISZE retail",
            "formula": "PR00 net × 1.40 × 1.275 = ×1.785",
            "source": CHANNEL_AS_OF,
        },
    }


def enrich(L, db, reg, book_tot, ws_rows, iam_lane, book_pn=None, top30_pns=None):
    lookup = load_brand_lookup()
    extra_probes, extra_rows = load_extra_iam_probes(db, book_pn, book_tot, top30_pns or set())
    iam_lane.setdefault("probes", {})
    iam_lane["probes"].update(extra_probes)
    merged_rows = [stamp_projected_retail(dict(r)) for r in (iam_lane.get("rows") or [])]
    for r in extra_rows:
        merged_rows.append(stamp_projected_retail(dict(r)))
    iam_lane["rows"] = merged_rows
    if extra_rows:
        iam_lane["available"] = True
    eucon_p = iam_lane["probes"].setdefault("eucon", {})
    if eucon_p.get("available") or eucon_p.get("n"):
        eucon_p["as_of"] = "2026-03-29"
        eucon_p["outdated"] = True
        eucon_p["as_of_note"] = "PartsPool Autodoc DE/NO 2026-03-29 — not the 2023 UK survey"
    hits_by_pn = {}
    for r in merged_rows:
        pn = str(r.get("pn") or "")
        if pn:
            hits_by_pn.setdefault(pn, set()).add(r.get("probe"))
    iam_hits = {}
    for r in merged_rows:
        pn = str(r.get("pn") or "")
        r["sources_hit"] = sorted(p for p in (hits_by_pn.get(pn) or set()) if p)
        if pn:
            iam_hits.setdefault(pn, []).append(r)
    iam_by_pn = {pn: rows[0] for pn, rows in iam_hits.items()}
    exposed = [r for r in merged_rows if r.get("delta_pct") is not None and r["delta_pct"] < 0]
    iam_lane["db_revenue_on_exposed_pns_eur"] = r2(sum((r.get("db_revenue_cy_eur") or 0) for r in exposed))
    iam_lane["isze_exposed_pns"] = len(exposed)
    wsum = sum((r.get("db_revenue_cy_eur") or 0) for r in merged_rows if r.get("delta_pct") is not None)
    if wsum:
        iam_lane["revenue_weighted_delta_pct"] = round(
            sum((r.get("delta_pct") or 0) * (r.get("db_revenue_cy_eur") or 0)
                for r in merged_rows if r.get("delta_pct") is not None) / wsum, 1)
    negs = [r["delta_pct"] for r in merged_rows if r.get("delta_pct") is not None]
    iam_lane["worst_delta_pct"] = min(negs) if negs else None

    # Brand quality on IAM-matched PNs + rewrite SPA levers on the working set.
    brand_rows = []
    for r in iam_lane.get("rows") or []:
        bq = score_brands(r.get("brands"), lookup)
        premium = None
        over = None
        if r.get("delta_pct") is not None:
            # delta_pct = (competitor - ISZE) / ISZE * 100. Negative => ISZE more expensive.
            premium = round(-r["delta_pct"], 1)
        if bq and premium is not None:
            over = premium > bq["ceiling_pct"]
        rec = {**r, "brand_quality": bq, "isze_premium_vs_iam_pct": premium,
               "over_brand_ceiling": over}
        brand_rows.append(rec)

    for r in ws_rows:
        iam = iam_by_pn.get(str(r["pn"]))
        r["iam_delta_pct"] = iam.get("delta_pct") if iam else None
        r["iam_isze_exposed"] = iam.get("isze_exposed") if iam else None
        r["brand_quality"] = score_brands(iam.get("brands"), lookup) if iam else None
        r["lever"] = spa_lever(r, iam)

    spa_n = sum(1 for r in ws_rows if str(r.get("lever", "")).startswith("SPA candidate"))
    L["sections"]["working_set"]["rows"] = ws_rows
    L["sections"]["working_set"]["counts"]["spa_candidates"] = spa_n
    L["sections"]["working_set"]["spa_rule"] = (
        "SPA CTA only if projected ISZE retail (PR00 × 1.40 × 1.275) is above a named quality IAM "
        "(T3/T4) and Best Value is missing or not enough. Cheaper rows and BVP-sufficient rows "
        "get Push Best Value or Hold — never an SPA button."
    )
    L["sections"]["working_set"]["bvp_lever_note"] = L["sections"]["working_set"]["spa_rule"]

    xref_path = os.path.join(DERIVED, "genuine_bvp_crossref.csv")
    gen_pns, bvp_pns = set(), set()
    if os.path.exists(xref_path):
        xr = pd.read_csv(xref_path, dtype=str)
        if "genuine_pn" in xr.columns:
            gen_pns = set(xr.genuine_pn.dropna().astype(str))
        if "bvp_pn" in xr.columns:
            bvp_pns = set(xr.bvp_pn.dropna().astype(str))

    strategy = meeting_strategy_from_engine(db, L["sections"].get("pms") or {})
    def _walk_clean(o):
        if isinstance(o, dict):
            return {k: _walk_clean(v) for k, v in o.items()}
        if isinstance(o, list):
            return [_walk_clean(x) for x in o]
        if isinstance(o, str):
            return _strip_banned(o)
        return o
    L["sections"]["lost_sales_strategy"] = _walk_clean(strategy)
    eng_by_pn = {str(r["pn"]): r for r in (strategy.get("pn_rows") or [])}
    verdict_by_gen = enrich_bvp_alternatives(L, iam_hits, lookup, eng_by_pn)
    for r in ws_rows:
        r["bvp_verdict"] = verdict_by_gen.get(str(r["pn"]))
        iam = iam_by_pn.get(str(r["pn"]))
        r["lever"] = spa_lever(r, iam)
    spa_n = sum(1 for r in ws_rows if str(r.get("lever", "")).startswith("SPA") or "SPA on genuine" in str(r.get("lever", "")))
    L["sections"]["working_set"]["rows"] = ws_rows
    L["sections"]["working_set"]["counts"]["spa_candidates"] = spa_n

    spa_book = []
    for r in brand_rows:
        pn = str(r.get("pn") or "")
        if pn.startswith("5500") or pn in bvp_pns:
            continue
        verd = verdict_by_gen.get(pn)
        if pn in gen_pns and verd != "bvp_not_enough":
            continue
        if r.get("delta_pct") is not None and r["delta_pct"] < 0:
            spa_book.append({
                "pn": pn, "description": r.get("description"),
                "db_revenue_cy_eur": r.get("db_revenue_cy_eur"),
                "isze_price_eur": r.get("isze_price_eur"),
                "isze_eur": r.get("isze_price_eur"),
                "proj_retail_eur": r.get("proj_retail_eur"),
                "competitor_avg_eur": r.get("competitor_avg_eur"),
                "quality_iam_eur": r.get("competitor_avg_eur"),
                "quality_tier": (r.get("brand_quality") or {}).get("best_tier") or (r.get("brand_quality") or {}).get("tier"),
                "delta_pct": r.get("delta_pct"),
                "delta_vs_proj_retail_pct": r.get("delta_vs_proj_retail_pct"),
                "isze_premium_vs_iam_pct": r.get("isze_premium_vs_iam_pct"),
                "over_brand_ceiling": r.get("over_brand_ceiling"),
                "brand_quality": r.get("brand_quality"),
                "in_working_set": r.get("in_working_set"),
                "competitor_url": r.get("competitor_url"),
                "probe": r.get("probe"),
                "probe_label": r.get("probe_label"),
                "iam_point_kind": r.get("iam_point_kind"),
                "iam_like_for_like_note": r.get("iam_like_for_like_note"),
                "sources_hit": r.get("sources_hit") or [],
                "bvp_verdict": verd,
                "cta": None,
                "spa_candidate": False,
            })
    spa_book.sort(key=lambda x: -(x.get("db_revenue_cy_eur") or 0))
    for r in (iam_lane.get("rows") or []):
        hit = eng_by_pn.get(str(r.get("pn") or ""))
        if not hit:
            continue
        if hit.get("suspect"):
            r["suspect"] = hit["suspect"]
        url = hit.get("primary_url") or ""
        if (not r.get("competitor_url")) and str(url).startswith("https://"):
            r["competitor_url"] = url
    for r in spa_book:
        hit = eng_by_pn.get(str(r.get("pn") or ""))
        if hit:
            r["proposed_isze_eur"] = hit.get("proposed_isze_eur")
            r["band_high_eur"] = hit.get("band_high_eur")
            r["quality_brand"] = hit.get("quality_brand")
            if hit.get("quality_tier") is not None:
                r["quality_tier"] = hit.get("quality_tier")
            if hit.get("quality_iam_eur") is not None:
                r["quality_iam_eur"] = hit.get("quality_iam_eur")
            r["proj_retail_eur"] = hit.get("proj_retail_eur") or r.get("proj_retail_eur")
            r["action_label"] = hit.get("action_label")
            r["bvp_alts"] = hit.get("bvp_alts") or []
            r["action"] = hit.get("action")
        r = stamp_projected_retail(r)
        r["bvp_verdict"] = r.get("bvp_verdict") or verdict_by_gen.get(str(r.get("pn") or ""))
        if not r.get("sources_hit"):
            r["sources_hit"] = sorted({x.get("probe") for x in iam_hits.get(str(r.get("pn") or ""), []) if x.get("probe")})
        r["spa_candidate"] = spa_cta_allowed(r)
        r["cta"] = spa_cta_text(r)
        if not r["spa_candidate"]:
            r["proposed_isze_eur"] = None
            r["band_high_eur"] = None
    spa_book = [r for r in spa_book if r.get("spa_candidate") and r.get("cta")]
    rebuild_family_strategy(L, iam_hits, lookup, spa_book, verdict_by_gen)
    L["sections"]["lost_sales_strategy"] = _walk_clean(L["sections"].get("lost_sales_strategy") or {})

    L["sections"]["spa_candidates"] = {
        "rule": L["sections"]["working_set"]["spa_rule"],
        "n": len(spa_book),
        "rows": spa_book[:20],
        "note": "From this distributor’s CY2025 billed book intersected with aftermarket probes, not the whole catalogue.",
        "cta_block": (
            "SPA only where projected ISZE retail sits above a named quality IAM (T3/T4) and "
            "Best Value is missing or not enough. Already-cheaper rows have no SPA button."
        ),
        "euro_column": {
            "label": "ISZE net / unit",
            "grain": "unit price, IE40 PR00",
            "field": "isze_price_eur",
            "tooltip": tip(
                "ISZE net to this distributor, current list (IE40 PR00), per unit.",
                "Joined to this sold-to’s CY2025 book",
                "Not billed euros and not a dealer or retail price.",
            ),
        },
        "retail_column": {
            "label": "Projected ISZE retail",
            "field": "proj_retail_eur",
            "tooltip": tip(
                "PR00 net × 1.40 (distributor) × 1.275 (dealer) = ×1.785 projected ISZE retail.",
                CHANNEL_AS_OF,
                "Not observed SPA terms. Not a scraped shop price. Δ% uses this, not ISZE net.",
            ),
        },
        "billed_column": {
            "label": "Billed CY2025 €",
            "field": "db_revenue_cy_eur",
            "tooltip": tip(
                "ISZE net sales billed to this sold-to in calendar year 2025. Credit notes excluded, never subtracted.",
                "CY2025 complete",
                "Not a unit price.",
            ),
        },
        "iam_column": {
            "label": "IAM quality offer / unit",
            "field": "competitor_avg_eur",
            "tooltip": tip(
                "Named-site published offer used for Δ % vs projected retail. Brand/tier/source and trade-vs-retail are on the row.",
                "Latest named-site scrape on file · Eucon is 2023",
                "IAM trade vs projected retail is still not perfect like-for-like. T1 listings do not set a cut.",
            ),
        },
        "delta_column": (iam_lane.get("delta_formula") or {}),
        "pricing_honesty": (
            "ISZE net / unit is net to the distributor (current list, IE40 PR00). "
            "Projected ISZE retail = PR00 × 1.40 × 1.275 = ×1.785 "
            f"({CHANNEL_AS_OF}). "
            "Δ % = (IAM published − projected ISZE retail) / projected ISZE retail. "
            "Positive = ISZE cheaper at retail. Negative = ISZE dearer. "
            "IAM published is the named-site offer on that row "
            "(KS International UK, ex-VAT trade; Mekonomen Sweden retail; PartsPool Autodoc DE/NO 2026-03-29; Eucon UK IAM workshop 2023). "
            "IAM trade vs projected retail — still not perfect like-for-like. "
            "Do not compare IAM retail to ISZE net-to-distributor."
        ),
    }

    over_n = sum(1 for r in brand_rows if r.get("over_brand_ceiling"))
    L["sections"]["brand_quality"] = {
        "policy_ladder": BRAND_CEILINGS,
        "source": "iam_brand_tiers.csv + pricing-engine Mode A ceilings (+30/+60/+150/+250)",
        "n_iam_pns_in_this_db": len(brand_rows),
        "n_over_ceiling": over_n,
        "rows": [
            {
                "pn": r["pn"], "description": r.get("description"),
                "delta_pct": r.get("delta_pct"),
                "isze_premium_vs_iam_pct": r.get("isze_premium_vs_iam_pct"),
                "isze_exposed": r.get("isze_exposed"),
                "db_revenue_cy_eur": r.get("db_revenue_cy_eur"),
                "in_working_set": r.get("in_working_set"),
                "brand_quality": r.get("brand_quality"),
                "over_brand_ceiling": r.get("over_brand_ceiling"),
            }
            for r in sorted(brand_rows, key=lambda x: -(x.get("db_revenue_cy_eur") or 0))
        ],
        "render_rule": "A high-quality IAM brand (T4) undercutting ISZE is a real threat. "
                       "A T1 no-name undercut is not the same meeting. Colour by tier, not by "
                       "price gap alone. SPA still requires no BVP.",
    }

    auto = build_auto365_street()
    if db in ("UMI", "UTI"):
        L["sections"]["local_catalogue"] = auto
    else:
        L["sections"]["local_catalogue"] = {
            "available": False,
            "reason": "The local aftermarket catalogue is only shown for UMI and UTI.",
        }

    L["sections"]["ids"] = extract_ids(reg.get("ids"))

    # Hero — all numbers already in the ledger, assembled not recomputed.
    gps_rows = L.get("gps_fy_spine", {}).get("rows") or []
    fy = next((r for r in gps_rows if r.get("fy") == 2026), {}) or {}
    pms = L["sections"].get("pms") or {}
    wal = L["sections"].get("wallet_cy") or {}
    bp = L.get("business_plan") or {}
    plan = L["sections"].get("plan_tracking") or {}
    show_pct = L["flags"].get("SHOW_GPS_PCT")
    L["hero"] = {
        "chips": [
            {
                "id": "gps_in",
                "label": "GPS-eligible parts",
                "value_eur": fy.get("actual_eur"),
                "grain": "FY2026 · warranty included",
                "sub": (f"{fy.get('gps_pct')}% of ceiling" if show_pct and fy.get("gps_pct") is not None else "euros only"),
                "toggle_group": "warranty",
                "tooltip": tip(
                    "pure_sales_eur for this sold-to, FY = Apr–Mar. Shell lubricants stripped.",
                    "FY2026 (Apr 2025–Mar 2026)",
                    "Warranty is inside this number. Shell is not. GPS% uses V19 UIO × current D-Max rate.",
                ),
            },
            {
                "id": "gps_ex",
                "label": "Same, warranty out",
                "value_eur": fy.get("ex_warranty_eur") if fy.get("ex_warranty_renderable") else None,
                "grain": "FY2026 · warranty excluded",
                "sub": (f"{fy.get('gps_pct_ex_warranty')}% of ceiling" if show_pct and fy.get("ex_warranty_renderable") else "not a valid euro this year" if fy.get("ex_warranty_renderable") is False else "—"),
                "toggle_group": "warranty",
                "hidden_default": True,
                "renderable": fy.get("ex_warranty_renderable"),
                "tooltip": tip(
                    "pure_sales_ex_warranty_eur. Claim-price warranty minus ISZE-net sales is not a clean euro when it goes negative.",
                    "FY2026",
                    "Ex-warranty is a toggle of GPS-eligible parts, not a second headline. A year with an invalid ex-warranty euro is left blank — never drawn as zero.",
                    warning="Never a rival headline to GPS-eligible parts.",
                ),
            },
            {
                "id": "pms",
                "label": "PMS capture",
                "value_pct": pms.get("capture_pct_total") if pms.get("capture_pct_total") is not None else None,
                "grain": f"CY{pms.get('year') or 2025} complete",
                "sub": (f"network {pms.get('network_capture_pct')}% · {pms.get('vs_network_pp')} pp"
                        if pms.get("network_capture_pct") is not None else pms.get("reason") or "no PMS"),
                "tooltip": pms.get("tooltip") or tip(
                    "actual_qty ÷ expected_qty, line_type=total, complete calendar year. Always shown vs network on the same model.",
                    f"CY{pms.get('year') or 2025}",
                    "Partial-year 2026 file. Frozen UIO — do not chart capture over time. Quotable categories only in the euro gap.",
                ),
            },
            {
                "id": "wallet",
                "label": "Wallet ceiling",
                "value_eur": wal.get("ceiling_eur"),
                "grain": f"CY{wal.get('year') or 2025} · ceiling, not a forecast",
                "sub": (f"captured {wal.get('captured_total_eur'):,.0f} · gap {wal.get('addressable_uncaptured_eur'):,.0f}".replace(",", " ")
                        if wal.get("captured_total_eur") is not None else wal.get("status") or "—"),
                "tooltip": tip(
                    "Parc × per-model target. Captured = genuine + Best Value invoiced. Gap is still in play, not a booked loss.",
                    f"CY{wal.get('year') or 2025}",
                    "Baked at €250/unit. Live GPS% uses the FY spine at the current D-Max rate. BVP is inside captured.",
                ),
            },
        ],
        "plan": {
            "bp_fy27_eur": bp.get("bp_fy27_eur"),
            "ext_target_fy27_eur": bp.get("ext_target_fy27_eur"),
            "stretch_eur": bp.get("stretch_eur"),
            "bp_match": (plan.get("bp_match") or {}).get("verdict"),
            "tooltip": tip(
                "EXT TARGET = BP FY2027 + locked stretch. Do not recompute from sales-to-dealer.",
                "FY2027",
                "The /0.65 StD gross-up was invalidated 17-07-2026.",
            ),
        },
        "rate_footer": {
            "lcv_rate_eur": (L["sections"].get("rate_change_impact") or {}).get("current_lcv_rate_eur"),
            "as_of": "FY2027 current D-Max rate, confirmed 2026-08-14",
        },
        "one_liner": "Where we are with this customer this quarter — plan, capture, mix, aftermarket, dealers, what they should send.",
    }
    if db == "GREECE":
        L["hero"]["one_liner"] = (
            "Greece this quarter: plan, GPS, PMS, parc, dealer visits, and aftermarket."
        )
        for c in L["hero"]["chips"]:
            if c.get("id") == "wallet":
                c["grain"] = f"CY{wal.get('year') or 2025} · reference ceiling"
            if c.get("id") == "gps_ex" and fy.get("ex_warranty_renderable") is False:
                c["sub"] = "—"
        ids_blk = L["sections"].get("ids") or {}
        osb = ids_blk.get("os") or {}
        if osb.get("available"):
            osb["one_liner"] = (
                "Visit the hit-list dealers first, agree three to five actions, and pull monthly."
            )
        eblk = ids_blk.get("section_e") or {}
        if eblk.get("fill") == "not_scored":
            eblk["prose"] = "Awaiting score — participation to confirm."
        probes = ((L.get("sections") or {}).get("three_lanes") or {}).get("iam_gap", {}).get("probes") or {}
        if probes.get("eucon"):
            probes["eucon"]["as_of_note"] = "PartsPool Autodoc DE/NO · 29 Mar 2026"
        if probes.get("eucon_uk_2023"):
            probes["eucon_uk_2023"]["as_of_note"] = "Eucon UK IAM workshop 2023"

    std_reg = os.path.join(ISZE, "01_data", "12_raw", "dealer_sales", "_registry.yaml")
    has_std = False
    if os.path.exists(std_reg):
        txt = open(std_reg, encoding="utf-8").read()
        has_std = f"distributor_code: {db}" in txt or f"distributor_code: {db}\n" in txt
        # UTI files are not UMI coverage
        if db == "UMI":
            has_std = False
    packed = umi_open_items() if db == "UMI" else open_items_for(db)
    meta = L.get("meta") or {}
    face = face_open_lead(meta.get("display_name") or db, meta.get("country") or "")
    open_items = packed if packed else {
        "F_emails": {
            "available": False,
            "title": "Open issues from mail",
            "open_lead": face,
            "body": "No mailbox extract on file for this distributor.",
            "rows": [],
        },
        "G_minutes": {
            "available": False,
            "title": "Meeting minutes",
            "body": "No minutes file on file for this distributor.",
        },
    }
    fe = open_items.setdefault("F_emails", {})
    fe["open_lead"] = face
    L["empty_states"] = {
        "F_emails": open_items["F_emails"],
        "G_minutes": open_items["G_minutes"],
        "J_sales_to_dealer": {
            "available": has_std,
            "ask_card": {
                "headline": "Sales-to-dealer is the #1 ask",
                "why": "Dealers do not really overstock. Monthly invoice date + part number + quantity is real demand and it feeds replenishment. We adapt to their layout.",
                "ask": "Monthly StD from January 2025: invoice date, PN, qty. EUR optional. Dealer dimension if they have it.",
                "do_not_ask_iuk_for_eur": db == "IUK",
                "umi_note": ("UTI PartSales files are CV sold-to 1799 — they are not this LCV book."
                             if db == "UMI" else None),
            },
        },
        "fill_rate": {
            "available": False,
            "body": "No Individual Fill Rate series filed for this distributor.",
        },
    }

    ids = L["sections"].get("ids") or {}
    e = ids.get("section_e") or {}
    pms = L["sections"].get("pms") or {}
    iam = (L["sections"].get("three_lanes") or {}).get("iam_gap") or {}
    plan = L["sections"].get("plan_tracking") or {}
    bp_ok = (plan.get("bp_match") or {}).get("verdict") == "MATCH"
    std_on = bool((L["empty_states"].get("J_sales_to_dealer") or {}).get("available"))
    cov = iam.get("db_revenue_coverage_pct")
    mail = L["empty_states"].get("F_emails") or {}
    mins = L["empty_states"].get("G_minutes") or {}
    probes = iam.get("probes") or {}
    ks = probes.get("ks") or {}
    mek = probes.get("mekonomen") or {}
    ks_cov = ks.get("db_revenue_coverage_pct")
    mek_cov = mek.get("db_revenue_coverage_pct")
    cov_bits = []
    if iam.get("available") and cov is not None:
        cov_bits.append(f"Eucon {cov}% of CY2025 euros")
    if ks.get("available"):
        cov_bits.append(f"KS {ks.get('n')} PNs · {ks_cov}% of CY2025 euros")
    if mek.get("available"):
        cov_bits.append(f"Mekonomen {mek.get('n')} PNs · {mek_cov}% of CY2025 euros")
    loc = L["sections"].get("local_catalogue") or {}
    if loc.get("available") and not loc.get("pn_join"):
        cov_bits.append(f"Local catalogue {loc.get('n_priced_rows') or 0} priced offers · family only, no part-number join")
    iam_note = " · ".join(cov_bits) if cov_bits else (iam.get("reason") or "No aftermarket match")
    L["integrity_strip"] = {
        "lights": [
            {
                "id": "bp",
                "label": "Business plan vs locked workbook",
                "state": "ok" if bp_ok else "bad",
                "note": "MATCH" if bp_ok else ((plan.get("bp_match") or {}).get("verdict") or "unresolved"),
            },
            {
                "id": "gps",
                "label": "GPS % on this book",
                "state": "ok" if L["flags"].get("SHOW_GPS_PCT") else "warn",
                "note": ("Released on V19 parc and the current D-Max rate"
                         if L["flags"].get("SHOW_GPS_PCT")
                         else "Percentage suppressed — the denominator is not quotable"),
            },
            {
                "id": "pms",
                "label": "PMS complete calendar year vs network",
                "state": "ok" if pms.get("capture_pct_total") is not None else "off",
                "note": "Frozen parc — not a time series" if pms.get("capture_pct_total") is not None
                        else (pms.get("reason") or "No PMS"),
            },
            {
                "id": "iam",
                "label": "Aftermarket probe coverage of this book",
                "state": "warn" if iam.get("available") or ks.get("available") or mek.get("available") else "off",
                "note": iam_note + " — do not add probes",
            },
            {
                "id": "std",
                "label": "Sales-to-dealer received",
                "state": "ok" if std_on else "bad",
                "note": "On file" if std_on else "Nothing on file — this is the #1 ask",
            },
            {
                "id": "ids_e",
                "label": "Dealer standard — vehicle sales",
                "state": "off" if e.get("fill") == "not_scored" else ("ok" if ids.get("available") else "off"),
                "note": (f"{e.get('scoreboard')} not scored"
                         if e.get("fill") == "not_scored"
                         else ("No dealer pack" if not ids.get("available") else "Scored")),
            },
            {
                "id": "mail",
                "label": "Open issues from mail",
                "state": "warn" if mail.get("available") else "off",
                "note": (f"{len(mail.get('rows') or [])} open items"
                         if mail.get("available") else (mail.get("body") or "Empty")),
            },
            {
                "id": "minutes",
                "label": mins.get("title") or "Meeting minutes / follow-ups",
                "state": "warn" if (mins.get("rows") or []) else "off",
                "note": (f"{len(mins.get('rows') or [])} open from minutes and follow-ups"
                         if (mins.get("rows") or []) else (mins.get("body") or "Empty — not borrowed from another distributor")),
            },
        ],
        "integrity_note": "Full notes sit in the same folder as this dashboard.",
    }

    if db == "ITUK":
        pms_ituk = L["sections"].setdefault("pms", {})
        yaml_path = os.path.join(ISZE, "03_analytics", "Isuzu", "prism", "data", "iml_v7_ituk_cy2025.yaml")
        cover, gap, oil, uio = 35.9, 2038471, 35.1, 22389
        if os.path.exists(yaml_path):
            try:
                import yaml
                y = yaml.safe_load(open(yaml_path, encoding="utf-8"))
                h = y.get("headline") or {}
                cover = h.get("weighted_cover_pct", cover)
                gap = h.get("revenue_gap_eur_sum", gap)
                oil = h.get("oil_filter_cover_pct", oil)
                uio = y.get("uio_dvla", uio)
            except Exception:
                pass
        pms_ituk["parallel_lane"] = {
            "label": "IML / ITUK signed-off lane (v7)",
            "cover_pct": cover,
            "oil_filter_cover_pct": oil,
            "revenue_gap_eur": int(gap) if gap is not None else None,
            "uio": int(uio) if uio is not None else None,
            "warning": (
                "This room is the network league (same expected-qty model as the other 17). "
                f"The IML/ITUK signed-off lane is {cover}% cover / EUR {int(gap):,} gap on DVLA {int(uio)} "
                f"at 1.25× filters (oil filter {oil}%). Do not show both as the capture rate."
            ).replace(",", " "),
        }
    L["sections"] = _walk_clean(L.get("sections") or {})
    return L


def write_integrity_md(L: dict, outdir: str) -> str:
    """Per-DB DATA_INTEGRITY.md. Names this distributor's holes only."""
    db = L["meta"]["distributor_code"]
    sold = L["meta"].get("sold_to_sap")
    display = L["meta"]["display_name"]
    flags = L.get("flags") or {}
    pms = (L.get("sections") or {}).get("pms") or {}
    ids = (L.get("sections") or {}).get("ids") or {}
    mix = ((L.get("sections") or {}).get("genuine_vs_bvp") or {}).get("whole_book") or {}
    paired = ((L.get("sections") or {}).get("genuine_vs_bvp") or {}).get("paired_basket_only") or {}
    gps = L.get("gps_fy_spine") or {}
    es = L.get("empty_states") or {}
    mail = es.get("F_emails") or {}
    mins = es.get("G_minutes") or {}
    rec = L.get("reconciliation") or {}
    diffs = [c for c in (rec.get("checks") or []) if str(c.get("verdict") or "").startswith("DIFF")]
    n_mail = len(mail.get("rows") or [])
    n_mins = len(mins.get("rows") or [])
    pl = pms.get("parallel_lane") or {}
    lines = [
        f"# DATA_INTEGRITY — {db} operating dashboard",
        "",
        f"**TARGET_DB** {db} · sold_to **{sold}** · {display} · {L['meta'].get('country')} · {L['meta'].get('segment')}",
        f"**AS_OF** {L['meta'].get('as_of')} · **audience** ISZE internal",
        "Holes for **this distributor only**. Nothing copied from UMI, IUK, Ireland, or any other pack.",
        "",
        "## PMS capture audit (complete CY, this sold-to)",
        "",
    ]
    aud = pms.get("audit") or {}
    if aud:
        lines += [
            f"- File: `{aud.get('file')}`",
            f"- Filter: `{aud.get('filter')}`",
            f"- sold_to SAP: **{aud.get('sold_to_sap')}**",
            f"- expected qty: **{aud.get('expected_qty')}**",
            f"- sold qty (actual): **{aud.get('actual_qty')}**",
            f"- capture %: **{aud.get('arithmetic')}**",
            f"- network: {aud.get('network_actual_qty')} sold ÷ {aud.get('network_expected_qty')} expected = {aud.get('network_capture_pct')}%",
            f"- Ireland sold-to 76 in this slice? **{aud.get('not_ireland_76')}** (True = Ireland is NOT in this pack)",
            f"- ITUK sold-to 2575 in this slice? **{aud.get('not_ituk_2575')}** (True = ITUK is NOT in this pack)",
            "",
        ]
    else:
        lines += ["- PMS audit block missing on this ledger.", ""]
    bvp_aud = mix.get("audit") or {}
    lines += [
        "## BVP mix audit (whole book — not the paired basket)",
        "",
    ]
    if bvp_aud:
        lines += [
            f"- {bvp_aud.get('arithmetic')}",
            f"- Genuine: €{bvp_aud.get('genuine_eur')} / {bvp_aud.get('n_pns_genuine')} PNs",
            f"- BVP: €{bvp_aud.get('bvp_eur')} / {bvp_aud.get('n_pns_bvp')} PNs",
            f"- Book: €{bvp_aud.get('total_eur')} / {bvp_aud.get('n_pns')} PNs",
            f"- Definition: {bvp_aud.get('definition')}",
            f"- Paired-basket trap (do **not** show as mix): {paired.get('bvp_share_pct')}% BVP on {paired.get('coverage_pct_of_book')}% of book euros"
            if paired.get("bvp_share_pct") is not None else
            "- Paired-basket file empty for this distributor.",
            "",
        ]
    else:
        lines += ["- BVP audit block missing on this ledger.", ""]
    skip = gps.get("skip_incomplete") or {}
    lines += [
        "## GPS publish rules",
        "",
        f"- Skip incomplete: FY{skip.get('fy')} — {skip.get('reason')}",
        f"- Publish years: {gps.get('publish_years')}",
        f"- CY GPS% toggle: **off**. {(gps.get('grain_control') or {}).get('cy', {}).get('disabled_reason')}",
        "",
        "## Open issues on the dashboard",
        "",
        f"| Lane | n | Source |",
        f"|---|---|---|",
        f"| Mail | {n_mail} | {(mail.get('source_note') or mail.get('body') or '—')[:160]} |",
        f"| Minutes / follow-ups | {n_mins} | {(mins.get('title') or '—')} |",
        "",
        "## Holes that belong to this distributor",
        "",
    ]
    n = 1
    if not flags.get("HAS_V31_FY_SERIES"):
        lines += [
            f"### {n}. No fiscal GPS % series in the locked workbook",
            "",
            "This distributor sits on the Dashboard row only (V4 as-presented). The GPS room shows euros and the locked FY27 figures. Nothing is synthesised.",
            "",
        ]
        n += 1
    if not flags.get("SHOW_GPS_PCT"):
        lines += [
            f"### {n}. GPS % is suppressed",
            "",
            flags.get("GPS_PCT_NOT_QUOTABLE_REASON") or "The denominator is not quotable for this distributor.",
            "",
        ]
        n += 1
    if pl:
        lines += [
            f"### {n}. Two PMS lanes — do not swap them in an ITUK/IML meeting",
            "",
            pl.get("warning") or "",
            "",
            f"- Network league on this dashboard: capture {pms.get('capture_pct_total')}% vs network {pms.get('network_capture_pct')}%.",
            f"- IML signed-off lane: cover {pl.get('cover_pct')}% · oil filter {pl.get('oil_filter_cover_pct')}% · gap EUR {pl.get('revenue_gap_eur')} · DVLA UIO {pl.get('uio')}.",
            "",
        ]
        n += 1
    if not ids.get("available"):
        lines += [
            f"### {n}. No dealer-standard pack",
            "",
            ids.get("reason") or "No IDS country pack for this distributor. The Dealers room is dropped.",
            "",
        ]
        n += 1
    std = es.get("J_sales_to_dealer") or {}
    if not std.get("available"):
        lines += [
            f"### {n}. Sales-to-dealer is not on file as a filed series",
            "",
            "The #1 ask stands. Do not treat another distributor's extract as this one.",
            "",
        ]
        n += 1
    if db == "GREECE":
        lines += [
            f"### {n}. Billing name on the GPS extract is not South Africa",
            "",
            "Sold-to 66 is Petros. The GPS extract still labels that payer with an RSA tag. Never join warranty or GPS files on that name — it collides with Norway. This pack filters sold-to 66 only.",
            "",
        ]
        n += 1
        osb = ids.get("os") or {}
        if osb.get("available"):
            lines += [
                f"### {n}. Dealer-standard OS is visit triage, not a sales forecast",
                "",
                f"v0.4 hit list has {len(osb.get('hit_list') or [])} dealers. Do not claim a higher dealer-standard score moves GPS or PMS.",
                "",
            ]
            n += 1
    if diffs:
        lines += [
            f"### {n}. Reconciliation diffs",
            "",
        ]
        for c in diffs:
            lines.append(f"- {c.get('check')}: {c.get('verdict')} (A={c.get('a_eur', c.get('a_pct'))} B={c.get('b_eur', c.get('b_pct'))})")
        lines.append("")
        n += 1
    lines += [
        "### Shared bans (apply here, not copied numbers)",
        "",
        "- Do not read the AutoDoc risk file (GBP 2.00 placeholder as a competitor price).",
        "- Do not read the partial-year PMS-by-DB summary (calendar 2026 vs a full-year expected).",
        "- Do not load raw sales workbooks into this pack.",
        "- Three lost-sales lanes are never added.",
        "- UMI 1797 is not UTI 1799. Turkey and MIDI are not ISZE distributors.",
        "",
        f"Generated from the {db} ledger. Do not paste another distributor's pings into this file.",
        "",
    ]
    path = os.path.join(outdir, "DATA_INTEGRITY.md")
    with open(path, "w", encoding="utf-8") as fh:
        fh.write("\n".join(lines))
    return path

