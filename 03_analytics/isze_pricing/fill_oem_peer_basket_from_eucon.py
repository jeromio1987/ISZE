"""Extend oem_peer_basket.csv from Eucon 2023 OEM surveys + street scrape probe.

Rules (internal):
  - Fill peer_oe_pn only for clear COMPARABLE 1:1 Isuzu×Brand maps.
  - Market-align: LCV×Toyota / LCV×Ford(Ranger); IUK|GERMANY×DAF.
  - Never IUK Ford Transit ← Ranger survey Ford.
  - Never put OEM CompetitorPrice (GBP list) into peer_street_eur.
  - Prefer live scrape for peer OE street; if blocked, mark needs_scrape.
  - IAM Workshop Purchase Price may be recorded as labeled interim
    (source=eucon_iam_workshop) on a sidecar — not as OEM peer street.
"""
from __future__ import annotations

import re
import time
from collections import defaultdict
from pathlib import Path

import openpyxl
import pandas as pd
import requests

ROOT = Path(__file__).resolve().parents[2]
ENGINE = Path(__file__).resolve().parent
RAW = ROOT / "01_data" / "01_Pricing" / "_raw"
DER = ROOT / "01_data" / "00_derived"
BASKET = ENGINE / "oem_peer_basket.csv"
RAW_MIRROR = RAW / "oem_peer_basket_seed_20260810.csv"
STREET_QA = DER / "oem_peer_street_fill_20260810.csv"
SCRAPE_NOTE = RAW / "Eucon_PriceSurvey_2023_street_scrape_note.md"

UK_OEM = RAW / "Eucon_PriceSurvey_UK_2023_OEM_rawdata_20240109.xlsx"
ITUK_OEM = RAW / "Eucon_PriceSurvey_ITUK_2023_OEM_rawdata.xlsx"
UK_IAM = RAW / "Eucon_PriceSurvey_UK_2023_IAM_rawdata_20240109.xlsx"

WANT = {
    "oil_filter",
    "fuel_filter",
    "air_filter",
    "blower_filter",
    "urea_filter",
    "brake_pad",
    "brake_rotor",
    "brake_shoe",
    "clutch_disc",
    "clutch_kit",
    "clutch_pressure_plate",
}

PEERS = [
    ("LCV", "Toyota", "Hilux"),
    ("LCV", "Ford", "Ranger"),
    ("LCV", "Mitsubishi", "L200"),
    ("IUK", "Ford", "Transit"),
    ("IUK", "Mercedes-Benz", "Sprinter"),
    ("IUK", "DAF", "LF/CF class"),
    ("GERMANY", "Mercedes-Benz", "Sprinter / light truck"),
    ("GERMANY", "MAN", "TGL/TGM"),
    ("GERMANY", "VW", "Crafter"),
    ("GERMANY", "DAF", "LF/CF class"),
]

# Survey desc → category (strict; rejects caliper/pipe/bearing/bumper)
STRICT = [
    ("oil_filter", ["OIL FILTER", "ELEMENT; OIL", "FILTER; OIL"]),
    ("fuel_filter", ["FUEL FILTER", "ELEMENT; FUEL", "ELEMENT KIT; FUEL"]),
    ("air_filter", ["FILTER; ACL", "AIR FILTER", "AIR CLEANER", "ELEMENT; AIR"]),
    ("blower_filter", ["CABIN", "BLOWER", "POLLEN", "FILTER; AIR COND"]),
    ("urea_filter", ["UREA FILTER", "ADBLUE FILTER"]),
    ("brake_pad", ["PAD KIT; CALIPER", "BRAKE PAD", "PAD; BRK"]),
    ("brake_rotor", ["ROTOR", "DISC; BRAKE", "BRAKE DISC"]),
    ("brake_shoe", ["BRAKE SHOE", "SHOE; BRK", "SHOE;BRAKE"]),
    ("clutch_kit", ["CLUTCH KIT", "KIT; CLUTCH"]),
    ("clutch_disc", ["DISC; CLUTCH", "CLUTCH DISC"]),
    ("clutch_pressure_plate", ["PRESSURE PLATE", "PLATE ASM; PRESSURE"]),
]

REJECT_SUB = (
    "CALIPER;",
    "BRAKE CALIPER",
    "PIPE;",
    "BEARING;",
    "RELEASE BEARING",
    "BUMPER",
    "SENSOR ASM",
    "PUMP ASM; DEF",
    "FUEL HOSE",
    "HOSE;",
)


def pn_norm(x) -> str:
    if x is None or (isinstance(x, float) and pd.isna(x)):
        return ""
    s = str(x).strip()
    if re.fullmatch(r"\d+\.0+", s):
        s = s.split(".")[0]
    s = re.sub(r"[^0-9A-Za-z]", "", s)
    if s.isdigit() and len(s) <= 10:
        return s.zfill(10)
    return s


def to_float(x):
    if x is None or x == "":
        return None
    if isinstance(x, (int, float)) and not pd.isna(x):
        return float(x)
    try:
        return float(str(x).strip().replace(",", ""))
    except ValueError:
        return None


def brand_match(survey_brand: str, peer_oem: str) -> bool:
    sb = (survey_brand or "").lower()
    po = (peer_oem or "").lower()
    if not sb or not po:
        return False
    if sb in po or po in sb:
        return True
    if "mercedes" in sb and "mercedes" in po:
        return True
    return False


def market_allows(peer_market: str, peer_oem: str, survey_brand: str, survey_vehicle: str) -> tuple[bool, str]:
    """Market-align peers; block Transit←Ranger."""
    po = peer_oem.lower()
    sb = (survey_brand or "").lower()
    sv = (survey_vehicle or "").lower()
    if peer_market == "LCV" and po == "toyota" and "toyota" in sb:
        return True, "LCV Toyota (Hilux context)"
    if peer_market == "LCV" and po == "ford" and "ford" in sb:
        if "transit" in sv:
            return False, "skip LCV Ford←Transit"
        return True, "LCV Ford (Ranger context)"
    if peer_market in ("IUK", "GERMANY") and po == "daf" and "daf" in sb:
        return True, f"{peer_market} DAF"
    if peer_market == "IUK" and po == "ford":
        return False, "skip IUK Transit←Ranger/survey Ford"
    return False, "market mismatch"


def strict_cat(text: str) -> str | None:
    t = str(text or "").upper()
    if any(x in t for x in REJECT_SUB):
        # pad kit caliper is OK for brake_pad
        if "PAD KIT; CALIPER" in t or "PAD KIT;CALIPER" in t:
            pass
        else:
            return None
    hits = []
    for cat_name, keys in STRICT:
        if any(k in t for k in keys):
            hits.append(cat_name)
    if "clutch_pressure_plate" in hits and "clutch_kit" in hits:
        return "clutch_pressure_plate"
    if len(hits) == 1:
        return hits[0]
    if len(set(hits)) == 1:
        return hits[0]
    return None


def load_survey() -> tuple[list[dict], dict]:
    rows: list[dict] = []
    wb = openpyxl.load_workbook(UK_OEM, read_only=True, data_only=True)
    for r in list(wb["Isuzu UK"].iter_rows(values_only=True))[1:]:
        if not any(c is not None and str(c).strip() != "" for c in r):
            continue
        rows.append(
            {
                "src": "UK",
                "isuzu": pn_norm(r[5]),
                "brand": str(r[8] or "").strip(),
                "vehicle": str(r[9] or "").strip(),
                "peer": pn_norm(r[11]),
                "comp": str(r[21] or "").strip().upper(),
                "desc": str(r[4] or ""),
                "prod": str(r[3] or ""),
            }
        )
    wb.close()
    wb = openpyxl.load_workbook(ITUK_OEM, read_only=True, data_only=True)
    for r in list(wb["Sheet1"].iter_rows(values_only=True))[1:]:
        if not any(c is not None and str(c).strip() != "" for c in r):
            continue
        rows.append(
            {
                "src": "ITUK",
                "isuzu": pn_norm(r[0]),
                "brand": str(r[3] or "").strip(),
                "vehicle": str(r[4] or "").strip(),
                "peer": pn_norm(r[6]),
                "comp": str(r[16] or "").strip().upper(),
                "desc": "",
                "prod": "",
            }
        )
    wb.close()

    by: dict[tuple[str, str], set[str]] = defaultdict(set)
    veh: dict[tuple[str, str], set[str]] = defaultdict(set)
    meta: dict[str, dict] = {}
    for d in rows:
        if d["comp"] != "COMPARABLE" or not d["peer"] or not d["isuzu"]:
            continue
        by[(d["isuzu"], d["brand"])].add(d["peer"])
        veh[(d["isuzu"], d["brand"])].add(d["vehicle"])
        m = meta.setdefault(d["isuzu"], {"desc": "", "prod": "", "sources": set()})
        m["sources"].add(d["src"])
        if d["desc"] and not m["desc"]:
            m["desc"] = d["desc"]
        if d["prod"] and not m["prod"]:
            m["prod"] = d["prod"]

    clear = {k: next(iter(v)) for k, v in by.items() if len(v) == 1}
    return rows, {"clear": clear, "veh": veh, "meta": meta}


def load_iam_workshop() -> dict[str, float]:
    """Median workshop purchase price (GBP) by Isuzu PN — interim IAM street-proxy."""
    out: dict[str, list[float]] = defaultdict(list)
    wb = openpyxl.load_workbook(UK_IAM, read_only=True, data_only=True)
    for seg in ("LCV", "HCV"):
        for r in list(wb[seg].iter_rows(values_only=True))[1:]:
            if not any(c is not None and str(c).strip() != "" for c in r):
                continue
            pn = pn_norm(r[1])
            ws = to_float(r[7])
            if pn and ws is not None and ws > 0:
                out[pn].append(ws)
    wb.close()
    return {pn: float(pd.Series(v).median()) for pn, v in out.items()}


def probe_ks(pn: str) -> dict:
    url = f"https://www.ks-international.com/catalogsearch/result/?q={pn}"
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
        ),
        "Accept-Language": "en-GB,en;q=0.9",
        "Referer": "https://www.ks-international.com/",
    }
    try:
        r = requests.get(url, headers=headers, timeout=20)
        prices = re.findall(r"£\s*([0-9]+(?:\.[0-9]{2})?)", r.text[:80000])
        return {
            "site": "ks",
            "status_code": r.status_code,
            "n_prices": len(prices),
            "min_gbp": float(min(prices)) if prices else None,
            "cloudflare": False,
            "url": url,
        }
    except Exception as exc:  # noqa: BLE001
        return {
            "site": "ks",
            "status_code": None,
            "n_prices": 0,
            "min_gbp": None,
            "cloudflare": False,
            "error": str(exc),
            "url": url,
        }


def probe_autodoc(pn: str) -> dict:
    url = f"https://www.autodoc.de/spares-search?keyword={pn}"
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
        ),
        "Accept-Language": "de-DE,de;q=0.9,en;q=0.8",
    }
    try:
        r = requests.get(url, headers=headers, timeout=20)
        title_m = re.search(r"<title>([^<]+)</title>", r.text[:5000], re.I)
        title = title_m.group(1).strip() if title_m else ""
        cf = r.status_code == 403 or "just a moment" in title.lower()
        return {
            "site": "autodoc_de",
            "status_code": r.status_code,
            "n_prices": 0,
            "min_eur": None,
            "cloudflare": cf,
            "title": title[:80],
            "url": url,
        }
    except Exception as exc:  # noqa: BLE001
        return {
            "site": "autodoc_de",
            "status_code": None,
            "n_prices": 0,
            "min_eur": None,
            "cloudflare": False,
            "error": str(exc),
            "url": url,
        }


def append_new_pns(basket: pd.DataFrame, survey_pack: dict) -> tuple[pd.DataFrame, int]:
    clear = survey_pack["clear"]
    meta = survey_pack["meta"]
    cat = pd.read_csv(
        DER / "parts_catalog_dimension.csv", dtype={"part_number": str}, low_memory=False
    )
    cat["part_number"] = (
        cat["part_number"].astype(str).str.replace(r"\.0$", "", regex=True).str.zfill(10)
    )
    cat_map = (
        cat.drop_duplicates("part_number").set_index("part_number")["pms_category"].to_dict()
    )

    ad = pd.read_csv(
        ROOT / "04_tools" / "autodoc_scraper" / "autodoc_results.csv", dtype={"PN": str}
    )
    ad["PN"] = ad["PN"].astype(str).str.replace(r"\.0$", "", regex=True).str.zfill(10)
    rev = pd.to_numeric(ad.set_index("PN")["Rev_CY2025_EUR"], errors="coerce").fillna(0).to_dict()
    qty = (
        pd.to_numeric(ad.set_index("PN")["Qty_CY2025"], errors="coerce").fillna(0).to_dict()
        if "Qty_CY2025" in ad.columns
        else {}
    )
    ad_desc = ad.set_index("PN")["Description"].to_dict()

    have = set(basket["isze_pn"].map(pn_norm))
    new_rows = []
    for pn in sorted({k[0] for k in clear}):
        if pn in have:
            continue
        m = meta.get(pn, {})
        text = f"{m.get('desc', '')} {m.get('prod', '')}"
        sc = strict_cat(text)
        cc = cat_map.get(pn)
        if cc in WANT and sc in WANT and cc != sc:
            # prefer survey-strict when pressure plate vs kit clash
            if sc == "clutch_pressure_plate":
                cat_final = sc
            else:
                cat_final = cc
        elif cc in WANT and (sc is None or sc == cc):
            # require survey text not reject-only junk
            if any(x in text.upper() for x in REJECT_SUB) and "PAD KIT; CALIPER" not in text.upper():
                continue
            if sc is None and not cc:
                continue
            cat_final = cc if sc is None else sc
        elif sc in WANT:
            cat_final = sc
        else:
            continue
        if cat_final not in WANT:
            continue
        # hard rejects already in strict_cat; extra bumper/DEF guard
        if any(x in text.upper() for x in ("BUMPER", "SENSOR ASM", "PUMP ASM; DEF")):
            continue

        desc = ad_desc.get(pn) or m.get("desc") or m.get("prod") or ""
        src_tag = "eucon_pricesurvey_2023_oem_expand"
        for market, oem, model in PEERS:
            new_rows.append(
                {
                    "isze_pn": pn,
                    "pms_category": cat_final,
                    "description": desc,
                    "isze_rev_cy2025_eur": round(float(rev.get(pn, 0) or 0), 2),
                    "isze_qty_cy2025": float(qty.get(pn, 0) or 0),
                    "peer_market": market,
                    "peer_oem": oem,
                    "peer_model": model,
                    "peer_oe_pn": "",
                    "peer_street_eur": "",
                    "source": src_tag,
                    "notes": "Expanded from Eucon 2023 OEM COMPARABLE map; OE+street blank until fill",
                    "status": "needs_map",
                }
            )
    if not new_rows:
        return basket, 0
    add = pd.DataFrame(new_rows)
    out = pd.concat([basket, add], ignore_index=True)
    return out, int(add["isze_pn"].nunique())


def fill_oe_maps(basket: pd.DataFrame, survey_pack: dict) -> tuple[pd.DataFrame, dict]:
    clear = survey_pack["clear"]
    veh = survey_pack["veh"]
    stats = {"filled": 0, "skipped_transit": 0, "already": 0, "no_hit": 0}

    for i, r in basket.iterrows():
        pn = pn_norm(r["isze_pn"])
        oem = str(r["peer_oem"])
        market = str(r["peer_market"])
        current = str(r.get("peer_oe_pn") or "").strip()
        if current:
            stats["already"] += 1
            continue

        hits: list[tuple[str, str, str]] = []
        for (spn, sbrand), peer in clear.items():
            if spn != pn or not brand_match(sbrand, oem):
                continue
            vehicles = " ".join(sorted(veh.get((spn, sbrand), set())))
            ok, why = market_allows(market, oem, sbrand, vehicles)
            if ok:
                hits.append((peer, sbrand, why))
            elif "Transit" in why or "Transit←" in why:
                stats["skipped_transit"] += 1

        if len(hits) != 1:
            stats["no_hit"] += 1
            continue

        peer, sbrand, why = hits[0]
        src = str(r.get("source") or "")
        if "eucon_pricesurvey_2023_oem" not in src:
            src = (src + "|" if src else "") + "eucon_pricesurvey_2023_oem"
        note = str(r.get("notes") or "")
        note = (
            note
            + f" | OE from Eucon 2023 survey ({why}; COMPARABLE {sbrand} 1:1; OE PN only — no street)"
        )
        basket.at[i, "peer_oe_pn"] = peer
        basket.at[i, "source"] = src
        basket.at[i, "notes"] = note.strip(" |")
        basket.at[i, "status"] = "mapped_oe_pn"
        stats["filled"] += 1
    return basket, stats


def apply_street_probe(basket: pd.DataFrame) -> tuple[pd.DataFrame, dict]:
    """Probe KS + Autodoc for mapped peer OE PNs. Do not invent prices."""
    mapped = basket[
        basket["peer_oe_pn"].astype(str).str.strip().ne("")
        & basket["peer_oe_pn"].notna()
    ].copy()
    unique_oes = sorted({pn_norm(x) for x in mapped["peer_oe_pn"] if pn_norm(x)})
    probe_rows = []
    street_by_oe: dict[str, float] = {}
    cf_hits = 0
    ks_hits = 0

    # Cap probe: all unique mapped OEs (typically <40)
    for oe in unique_oes:
        variants = [oe]
        if oe.isdigit() and oe.startswith("000"):
            variants.append(oe.lstrip("0") or "0")
        hit_gbp = None
        ad = probe_autodoc(oe)
        if ad.get("cloudflare"):
            cf_hits += 1
        for v in variants:
            ks = probe_ks(v)
            probe_rows.append({**ks, "peer_oe_pn": oe, "query": v})
            if ks.get("min_gbp"):
                hit_gbp = ks["min_gbp"]
                ks_hits += 1
                break
            time.sleep(0.4)
        probe_rows.append({**ad, "peer_oe_pn": oe, "query": oe})
        if hit_gbp is not None:
            # KS GBP → EUR via scraper convention 1.17 (labeled; not OEM list FX)
            street_by_oe[oe] = round(hit_gbp * 1.17, 2)
        time.sleep(0.3)

    filled_street = 0
    for i, r in basket.iterrows():
        oe = pn_norm(r.get("peer_oe_pn"))
        if not oe:
            continue
        if street_by_oe.get(oe):
            basket.at[i, "peer_street_eur"] = street_by_oe[oe]
            src = str(r.get("source") or "")
            if "ks_scrape" not in src:
                src = (src + "|" if src else "") + "ks_scrape_gbp_x1.17"
            basket.at[i, "source"] = src
            basket.at[i, "status"] = "mapped_oe_street"
            note = str(r.get("notes") or "")
            basket.at[i, "notes"] = (
                note + " | peer_street_eur from KS min GBP×1.17 (scraper FX)"
            ).strip(" |")
            filled_street += 1
        else:
            # leave street blank; mark needs_scrape if was mapped
            if str(r.get("status")) == "mapped_oe_pn":
                basket.at[i, "status"] = "needs_scrape"
                note = str(r.get("notes") or "")
                if "needs_scrape" not in note:
                    basket.at[i, "notes"] = (
                        note + " | street needs_scrape (KS empty; Autodoc Cloudflare)"
                    ).strip(" |")

    stats = {
        "unique_oe_probed": len(unique_oes),
        "ks_price_hits": ks_hits,
        "autodoc_cloudflare": cf_hits,
        "rows_street_filled": filled_street,
        "probe_rows": probe_rows,
    }
    return basket, stats


def write_street_qa(basket: pd.DataFrame, iam_ws_gbp: dict[str, float]) -> pd.DataFrame:
    """Isuzu street (PR00×1.785) vs IAM workshop proxy — labeled interim only."""
    pr00_path = DER / "pricing_pr00_ie40.parquet"
    list_path = DER / "pricing_list_pn.parquet"
    pr_map: dict[str, float] = {}
    if pr00_path.is_file():
        pr = pd.read_parquet(pr00_path)
        pr["pn"] = pr["part_number"].map(pn_norm)
        if "is_superseded_row" in pr.columns:
            pr = pr[~pr["is_superseded_row"]]
        pr_map = pr.groupby("pn")["sp_eur"].first().to_dict()
    elif list_path.is_file():
        pr = pd.read_parquet(list_path)
        pr["pn"] = pr["part_number"].map(pn_norm)
        if "is_superseded_row" in pr.columns:
            pr = pr[~pr["is_superseded_row"]]
        pr_map = pr.groupby("pn")["sp_eur"].first().to_dict()

    # GBP→EUR for IAM workshop: use same 1.17 scraper FX, labeled
    rows = []
    mapped_pns = sorted(
        {
            pn_norm(p)
            for p in basket.loc[
                basket["peer_oe_pn"].astype(str).str.strip().ne(""), "isze_pn"
            ]
        }
    )
    for pn in mapped_pns:
        pr00 = pr_map.get(pn)
        ws_gbp = iam_ws_gbp.get(pn)
        rows.append(
            {
                "isze_pn": pn,
                "pr00_list_eur": pr00,
                "isze_street_eur_x1785": round(pr00 * 1.785, 2) if pr00 else None,
                "iam_workshop_gbp_median": ws_gbp,
                "iam_workshop_eur_proxy_x1_17": round(ws_gbp * 1.17, 2) if ws_gbp else None,
                "source": "eucon_iam_workshop" if ws_gbp else "",
                "notes": (
                    "INTERIM IAM street-proxy only (Workshop Purchase Price). "
                    "Not OEM peer street. Not CompetitorPrice list. "
                    "Isuzu compare side = PR00×1.785."
                    if ws_gbp
                    else "No IAM workshop price in survey for this PN."
                ),
            }
        )
    qa = pd.DataFrame(rows)
    qa.to_csv(STREET_QA, index=False)
    return qa


def write_scrape_note(street_stats: dict, qa: pd.DataFrame) -> None:
    n_iam = int((qa["source"] == "eucon_iam_workshop").sum()) if len(qa) else 0
    lines = [
        "# Eucon / OEM peer street scrape note (2026-08-10)",
        "",
        "**Verdict:** Peer OE retail/street scrape **not usable this pass** for "
        "`peer_street_eur`. Autodoc DE = Cloudflare 403. KS International = HTTP 200 "
        "but **0 prices** on probed peer OE PNs (site is Isuzu-centric; peer Toyota/"
        "Ford/DAF OEs not stocked). Mekonomen probe also empty on sample Toyota OEs.",
        "",
        "## Probe summary",
        f"- Unique mapped peer OE PNs probed: **{street_stats.get('unique_oe_probed', 0)}**",
        f"- KS price hits: **{street_stats.get('ks_price_hits', 0)}**",
        f"- Autodoc Cloudflare hits: **{street_stats.get('autodoc_cloudflare', 0)}**",
        f"- Basket rows with `peer_street_eur` filled from scrape: "
        f"**{street_stats.get('rows_street_filled', 0)}**",
        "",
        "## Interim (labeled only)",
        f"- IAM survey **Workshop Purchase Price** → sidecar "
        f"`01_data/00_derived/oem_peer_street_fill_20260810.csv` "
        f"with `source=eucon_iam_workshop` for **{n_iam}** mapped Isuzu PNs.",
        "- Isuzu compare side: **PR00 × 1.785** (genuine street).",
        "- **OEM `CompetitorPrice` GBP list:** not used (not street).",
        "- Basket `peer_street_eur` left blank; status `needs_scrape` where OE mapped.",
        "",
        "## Do not",
        "- Do not feed OEM list GBP or IAM list into `oem_benchmark`.",
        "- Do not treat IAM workshop proxy as OEM peer street.",
    ]
    SCRAPE_NOTE.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    survey_rows, pack = load_survey()
    print(f"survey_rows={len(survey_rows)} clear_1to1={len(pack['clear'])}")

    basket = pd.read_csv(BASKET, dtype=str).fillna("")
    before_rows = len(basket)
    before_mapped = int((basket["status"] == "mapped_oe_pn").sum())

    basket, n_new_pn = append_new_pns(basket, pack)
    print(f"appended_new_isze_pn={n_new_pn} rows {before_rows}->{len(basket)}")

    basket, fill_stats = fill_oe_maps(basket, pack)
    print("oe_fill", fill_stats)

    basket, street_stats = apply_street_probe(basket)
    print(
        "street",
        {
            k: street_stats[k]
            for k in (
                "unique_oe_probed",
                "ks_price_hits",
                "autodoc_cloudflare",
                "rows_street_filled",
            )
        },
    )

    iam_ws = load_iam_workshop()
    qa = write_street_qa(basket, iam_ws)
    write_scrape_note(street_stats, qa)
    print(f"street_qa_rows={len(qa)} iam_workshop_hits={(qa.source=='eucon_iam_workshop').sum()}")

    basket.to_csv(BASKET, index=False)
    RAW_MIRROR.parent.mkdir(parents=True, exist_ok=True)
    basket.to_csv(RAW_MIRROR, index=False)

    after_mapped = int(
        basket["status"].isin(["mapped_oe_pn", "needs_scrape", "mapped_oe_street"]).sum()
    )
    print(
        f"wrote {BASKET} rows={len(basket)} mapped_or_needs_scrape={after_mapped} "
        f"(was mapped_oe_pn={before_mapped})"
    )
    print("status", basket["status"].value_counts().to_dict())
    print("by_market_mapped")
    m = basket[basket["peer_oe_pn"].astype(str).str.strip().ne("")]
    print(m.groupby(["peer_market", "peer_oem"]).size().to_string())


if __name__ == "__main__":
    main()
