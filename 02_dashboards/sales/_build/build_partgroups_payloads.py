#!/usr/bin/env python3
"""Payload builders for Part-Groups GPS+PMS and Aftermarket scrape tabs.

- Ireland / network UIO: overlay CY2025 from UIO_carpark_for_GPS_recalc_2026-07-30.csv
  (V20 carpark hand-off; CY2025 unchanged by scrap-rule fix). Recompute SPU + wallet capture.
- Scrape: street ×1.785 compare, £2 Autodoc filter, GBP/SEK FX, TMC/Tranz/A365 Price_EUR.
"""
from __future__ import annotations

import csv
import json
import math
import shutil
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
DATA = ROOT / "01_data" / "14_dashboards" / "partgroups_explorer"
SIBLING = ROOT / "02_dashboards" / "sales" / "partgroups_data"
PACK = ROOT / "02_dashboards" / "pricing" / "pricing_full_analysis_pack.json"
PMS_CSV = ROOT / "01_data" / "00_derived" / "pricing_pack_pms_total_by_db_year.csv"
GPS_CSV = ROOT / "01_data" / "00_derived" / "pricing_pack_aim_gps_cy2025.csv"
UIO_CSV = ROOT / "01_data" / "00_derived" / "UIO_carpark_for_GPS_recalc_2026-07-30.csv"
SCRAPER = ROOT / "04_tools" / "autodoc_scraper"
IAM_TIERS = SCRAPER / "iam_brand_tiers.csv"

STREET_FACTOR = 1.785  # PR00 × 1.40 × 1.275
GBP_EUR = 1.17
SEK_EUR = 1.0 / 11.5  # directional FX stamp
AUTODOC_PLACEHOLDER_GBP = 2.01


def clean(v):
    if v is None:
        return None
    if isinstance(v, float) and (math.isnan(v) or math.isinf(v)):
        return None
    return v


def _f(x):
    try:
        if x in ("", None):
            return None
        return float(x)
    except Exception:
        return None


def load_uio_v20_cy2025() -> dict[str, dict]:
    """Aggregate CY2025 UIO + wallet by country code from V20 GPS carpark file."""
    by: dict[str, dict] = {}
    with UIO_CSV.open(encoding="utf-8-sig") as f:
        for r in csv.DictReader(f):
            if str(r.get("is_MIDI_exclude", "")).lower() == "true":
                continue
            code = (r.get("country") or "").strip().upper()
            if not code:
                continue
            uio = _f(r.get("uio_CY2025_unchanged")) or 0.0
            wallet = _f(r.get("wallet_CY2025_eur")) or 0.0
            seg = r.get("segment") or ""
            model = r.get("model_type") or ""
            if code not in by:
                by[code] = {
                    "uio": 0.0,
                    "wallet_eur": 0.0,
                    "db_name": r.get("distributor_DB"),
                    "segments": [],
                    "source": "UIO_carpark_for_GPS_recalc_2026-07-30.csv",
                    "note": "CY2025 parc from UIO V20 GPS carpark hand-off (unchanged by scrap-rule fix)",
                }
            by[code]["uio"] += uio
            by[code]["wallet_eur"] += wallet
            by[code]["segments"].append(
                {
                    "segment": seg,
                    "model_type": model,
                    "gps_target_group": r.get("gps_target_group"),
                    "uio": uio,
                    "target_eur_per_vehicle_yr": _f(r.get("target_eur_per_vehicle_yr")),
                    "wallet_eur": wallet,
                }
            )
    return by


def build_gps_pms() -> dict:
    pack = json.loads(PACK.read_text(encoding="utf-8"))
    uio_v20 = load_uio_v20_cy2025()

    pms_by_db = []
    with PMS_CSV.open(encoding="utf-8") as f:
        for r in csv.DictReader(f):
            if r.get("year") != "2025":
                continue
            cap = float(r["capture_rate"])
            pms_by_db.append(
                {
                    "distributor_code": r["distributor_code"],
                    "year": 2025,
                    "actual_qty": float(r["actual_qty"]),
                    "expected_qty": float(r["expected_qty"]),
                    "actual_rev_eur": float(r["actual_rev_eur"]),
                    "capture_rate": cap,
                    "basis_breach": cap > 1.0,
                    "flag": "PMS expected basis breach (>100%) — do not treat as excellence"
                    if cap > 1.0
                    else None,
                }
            )

    scatter = []
    with GPS_CSV.open(encoding="utf-8") as f:
        for r in csv.DictReader(f):
            code = r["distributor_code"]
            sales = _f(r.get("gps_sales_eur"))
            pack_uio = _f(r.get("uio_units"))
            pack_spu = _f(r.get("gps_spu_eur"))
            pms_cap = _f(r.get("pms_capture_all"))

            v20 = uio_v20.get(code.upper()) or uio_v20.get(code)
            # also try country name
            if not v20 and r.get("country"):
                for k, v in uio_v20.items():
                    if (v.get("db_name") or "").upper().find(code.upper()) >= 0:
                        v20 = v
                        break
                    if k.replace("_", " ") == (r.get("country") or "").upper():
                        v20 = v
                        break

            # map common names: IRELAND key exists
            if not v20:
                v20 = uio_v20.get((r.get("country") or "").upper().replace(" ", ""))

            uio_final = pack_uio
            wallet = None
            uio_source = "pricing_pack_aim_gps_cy2025"
            uio_corrected = False
            quality_flags = []

            if v20 and v20["uio"] > 0:
                if pack_uio is None or abs(pack_uio - v20["uio"]) > 0.5:
                    uio_corrected = True
                    quality_flags.append(
                        f"UIO overlay V20 carpark {v20['uio']:.0f} (pack had {pack_uio})"
                    )
                uio_final = v20["uio"]
                wallet = v20["wallet_eur"]
                uio_source = v20["source"]

            spu = (sales / uio_final) if (sales is not None and uio_final and uio_final > 0) else None
            capture_vs_wallet = (
                (sales / wallet) if (sales is not None and wallet and wallet > 0) else None
            )

            if code in ("UTI", "UMI"):
                quality_flags.append("Israel — never blend UTI+UMI")
            if code == "IRELAND":
                quality_flags.append(
                    "Ireland UIO forced to V20 carpark 2,161 (731 LD + 92 F + 1,338 LCV). "
                    "Pack 3,056 was wrong. €/UIO blends CV+LCV — prefer capture-vs-wallet. "
                    "N35 Grafter still billed at N75 rate in wallet mapper (IE ~6% of N-series; small)."
                )
            if pms_cap is not None and pms_cap > 1.0:
                quality_flags.append("PMS total capture >100% — expected-qty basis breach")

            scatter.append(
                {
                    "db": code,
                    "country": r.get("country"),
                    "pms_total_capture": clean(pms_cap),
                    "gps_sales_eur": clean(sales),
                    "uio_units": clean(uio_final),
                    "uio_pack_original": clean(pack_uio),
                    "uio_source": uio_source,
                    "uio_corrected": uio_corrected,
                    "gps_spu_eur": clean(spu),
                    "gps_spu_pack_original": clean(pack_spu),
                    "wallet_eur_v20": clean(wallet),
                    "gps_capture_vs_wallet": clean(capture_vs_wallet),
                    "quadrant": r.get("quadrant_label"),
                    "quality_flags": quality_flags,
                    "israel_note": (
                        "Separate row — never blend UTI+UMI"
                        if code in ("UTI", "UMI")
                        else None
                    ),
                    "segments": (v20 or {}).get("segments"),
                }
            )

    # headline Ireland
    ie = next((s for s in scatter if s["db"] == "IRELAND"), None)
    network_capture = None
    if pms_by_db:
        aq = sum(r["actual_qty"] for r in pms_by_db)
        eq = sum(r["expected_qty"] for r in pms_by_db)
        if eq:
            network_capture = aq / eq

    gps_block = pack.get("gps", {}) or {}
    gps_pms = {
        "built_at_utc": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "mode": "A",
        "quotable_externally": False,
        "integrity": pack.get("integrity", {}),
        "uio_basis": {
            "file": str(UIO_CSV.relative_to(ROOT)).replace("\\", "/"),
            "rule": "CY2025 UIO from UIO V20 GPS carpark hand-off; SPU = GPS sales ÷ that UIO; also show sales ÷ wallet",
            "ireland_cy2025_uio": 2161,
            "ireland_cy2025_wallet_eur": (uio_v20.get("IRELAND") or {}).get("wallet_eur"),
            "ireland_pack_uio_rejected": 3056,
        },
        "headline": {
            "pms_total_capture_cy2025": network_capture,
            "pms_metric": "total capture (genuine + BVP) — not genuine-only",
            "pms_total_capture_basis": "sum(actual_qty)/sum(expected_qty) CY2025",
            "gps_spu_uti": gps_block.get("uti_spu"),
            "gps_spu_umi": gps_block.get("umi_spu"),
            "gps_spu_ireland_corrected": ie["gps_spu_eur"] if ie else None,
            "gps_capture_vs_wallet_ireland": ie["gps_capture_vs_wallet"] if ie else None,
            "israel_rule": "UTI and UMI are separate distributors — never blend",
        },
        "pms_by_db_cy2025": sorted(pms_by_db, key=lambda x: -x["capture_rate"]),
        "gps_pms_scatter_cy2025": scatter,
        "deep_link_gps": "../fleet/ISZE_GPS_Dashboard.html",
        "sources": [
            "01_data/00_derived/UIO_carpark_for_GPS_recalc_2026-07-30.csv",
            "01_data/00_derived/pricing_pack_aim_gps_cy2025.csv",
            "01_data/00_derived/pricing_pack_pms_total_by_db_year.csv",
            "02_dashboards/pricing/pricing_full_analysis_pack.json",
        ],
        "notes": [
            "Network lens: distributor-level PMS total capture and GPS — not joined to the 51-PN Eucon basket.",
            "PMS headline is total capture. Genuine/BVP mix is an extra lens on the Sales tab.",
            "UTI (Israel CV) and UMI (Israel LCV) stay as two rows.",
            "Ireland: UIO forced to V20 carpark 2,161 (rejected pack 3,056). Prefer capture-vs-wallet over €/UIO because CV+LCV mix.",
            "PMS rows with capture >100% are flagged basis breaches (frozen/wrong expected qty).",
        ],
    }
    DATA.mkdir(parents=True, exist_ok=True)
    (DATA / "partgroups_gps_pms.json").write_text(
        json.dumps(gps_pms, indent=2, ensure_ascii=False), encoding="utf-8"
    )
    return gps_pms


def _load_tiers() -> dict[str, int]:
    if not IAM_TIERS.exists():
        return {}
    out = {}
    with IAM_TIERS.open(encoding="utf-8-sig") as f:
        for r in csv.DictReader(f):
            brand = (r.get("brand") or r.get("Brand") or "").strip()
            tier = r.get("tier") or r.get("Tier")
            if brand and tier:
                try:
                    out[brand.lower()] = int(float(tier))
                except Exception:
                    pass
    return out


def build_scrape() -> dict:
    tiers = _load_tiers()
    sources_cfg = [
        {
            "name": "KS International",
            "file": "ks_results.csv",
            "kind": "pn_basket",
            "market": "UK",
            "ccy": "GBP",
        },
        {
            "name": "Autodoc",
            "file": "autodoc_results.csv",
            "kind": "pn_basket",
            "market": "UK",
            "ccy": "GBP",
        },
        {
            "name": "Mekonomen",
            "file": "mekonomen_results.csv",
            "kind": "pn_basket",
            "market": "SE",
            "ccy": "SEK",
        },
        {
            "name": "T&M",
            "file": "tmc_results.csv",
            "kind": "category_shop",
            "market": "UK",
            "ccy": "GBP",
        },
        {
            "name": "Tranzparts",
            "file": "tranzparts_results.csv",
            "kind": "category_shop",
            "market": "UK",
            "ccy": "GBP",
        },
        {
            "name": "Auto 365",
            "file": "auto365_results.csv",
            "kind": "category_shop",
            "market": "IL",
            "ccy": "ILS",
        },
    ]

    source_summaries = []
    street_rows = []  # PN-level street indices
    category_shop_rows = []
    gen_vs_am = []
    placeholders_dropped = 0

    def to_eur(price, ccy):
        if price is None:
            return None
        if ccy == "GBP":
            return price * GBP_EUR
        if ccy == "SEK":
            return price * SEK_EUR
        if ccy in ("EUR", "ILS", None):
            return price  # Auto365 already has Price_EUR
        return price

    for cfg in sources_cfg:
        path = SCRAPER / cfg["file"]
        if not path.exists():
            source_summaries.append(
                {"source": cfg["name"], "file": cfg["file"], "status": "missing"}
            )
            continue
        with path.open(encoding="utf-8-sig", newline="") as f:
            rows = list(csv.DictReader(f))
        cols = list(rows[0].keys()) if rows else []
        last_scrape = None
        n_ok = 0
        n_hit = 0
        n_placeholder = 0
        rev_hit = 0.0

        if cfg["kind"] == "pn_basket":
            pn_col = next((c for c in cols if c.lower() in ("pn", "part_number")), "PN")
            desc_col = next((c for c in cols if "desc" in c.lower()), None)
            pr00_col = next((c for c in cols if c.upper().startswith("PR00")), None)
            rev_col = next((c for c in cols if "rev_cy2025" in c.lower()), None)
            cat_col = next((c for c in cols if "aim_category" in c.lower() or c == "AIM_Category"), None)
            status_col = next((c for c in cols if c.lower() == "status"), None)
            scraped_col = next((c for c in cols if "scraped" in c.lower()), None)

            am_cols = [
                c
                for c in cols
                if any(x in c.lower() for x in ("am_min", "minprice", "min_price"))
                and "gen" not in c.lower()
            ]
            # Autodoc MinPrice
            if not am_cols:
                am_cols = [c for c in cols if "minprice" in c.lower().replace("_", "")]

            gen_cols = [c for c in cols if "gen_min" in c.lower()]
            stock_am = next((c for c in cols if "am_instock" in c.lower()), None)
            brand_col = next(
                (c for c in cols if "brand" in c.lower() and "all" not in c.lower()), None
            )

            for r in rows:
                st = (r.get(status_col) or "").lower() if status_col else ""
                if st in ("ok", "success", "found"):
                    n_ok += 1
                if scraped_col and r.get(scraped_col):
                    last_scrape = r.get(scraped_col)

                am_raw = None
                for c in am_cols:
                    am_raw = _f(r.get(c))
                    if am_raw and am_raw > 0:
                        break
                if not am_raw:
                    continue

                # Autodoc £2 placeholder
                if cfg["name"] == "Autodoc" and am_raw <= AUTODOC_PLACEHOLDER_GBP:
                    n_placeholder += 1
                    placeholders_dropped += 1
                    continue
                if st == "no_results":
                    n_placeholder += 1
                    placeholders_dropped += 1
                    continue

                n_hit += 1
                pr00 = _f(r.get(pr00_col)) if pr00_col else None
                am_eur = to_eur(am_raw, cfg["ccy"])
                street = (pr00 * STREET_FACTOR) if pr00 else None
                index = (am_eur / street) if (am_eur and street and street > 0) else None
                rev = _f(r.get(rev_col)) if rev_col else None
                if rev:
                    rev_hit += rev
                brand = (r.get(brand_col) or "").strip() if brand_col else ""
                tier = tiers.get(brand.lower()) if brand else None

                street_rows.append(
                    {
                        "source": cfg["name"],
                        "market": cfg["market"],
                        "pn": r.get(pn_col),
                        "description": (r.get(desc_col) or "")[:90] if desc_col else "",
                        "aim_category": r.get(cat_col) if cat_col else None,
                        "pr00_eur": round(pr00, 2) if pr00 else None,
                        "street_eur": round(street, 2) if street else None,
                        "am_eur": round(am_eur, 2) if am_eur else None,
                        "street_index": round(index, 3) if index else None,
                        "gap_pct_vs_street": round((index - 1) * 100, 1) if index else None,
                        "rev_cy2025_eur": round(rev, 0) if rev else None,
                        "brand": brand or None,
                        "brand_tier": tier,
                        "in_stock_am": _f(r.get(stock_am)) if stock_am else None,
                        "status": st or None,
                    }
                )

                if gen_cols and pr00:
                    gen_raw = _f(r.get(gen_cols[0]))
                    if gen_raw and gen_raw > AUTODOC_PLACEHOLDER_GBP:
                        gen_eur = to_eur(gen_raw, cfg["ccy"])
                        gen_idx = (gen_eur / street) if (gen_eur and street) else None
                        gen_vs_am.append(
                            {
                                "source": cfg["name"],
                                "pn": r.get(pn_col),
                                "description": (r.get(desc_col) or "")[:60] if desc_col else "",
                                "gen_eur": round(gen_eur, 2) if gen_eur else None,
                                "am_eur": round(am_eur, 2) if am_eur else None,
                                "street_eur": round(street, 2) if street else None,
                                "gen_vs_street": round(gen_idx, 3) if gen_idx else None,
                                "am_vs_street": round(index, 3) if index else None,
                            }
                        )

        else:
            # category shop: Price / Price_EUR
            price_eur_col = "Price_EUR" if "Price_EUR" in cols else None
            price_col = "Price" if "Price" in cols else None
            cat_col = next((c for c in cols if "category" in c.lower() or "pms" in c.lower()), None)
            name_col = next((c for c in cols if "product" in c.lower() and "url" not in c.lower()), None)
            scraped_col = next((c for c in cols if "scraped" in c.lower()), None)
            n_ok = len(rows)
            for r in rows:
                if scraped_col and r.get(scraped_col):
                    last_scrape = r.get(scraped_col)
                pe = _f(r.get(price_eur_col)) if price_eur_col else None
                if pe is None and price_col:
                    pe = to_eur(_f(r.get(price_col)), cfg["ccy"])
                if not pe or pe <= 0:
                    continue
                n_hit += 1
                category_shop_rows.append(
                    {
                        "source": cfg["name"],
                        "market": cfg["market"],
                        "pms_category": (r.get(cat_col) or "").strip() or "(uncategorised)",
                        "product_name": (r.get(name_col) or "")[:80] if name_col else "",
                        "price_eur": round(pe, 2),
                    }
                )

        source_summaries.append(
            {
                "source": cfg["name"],
                "file": cfg["file"],
                "kind": cfg["kind"],
                "market": cfg["market"],
                "rows": len(rows),
                "status_ok_rows": n_ok,
                "real_price_hits": n_hit,
                "placeholders_dropped": n_placeholder,
                "fill_rate_real": round(n_hit / len(rows), 3) if rows else 0,
                "rev_on_hits_eur": round(rev_hit, 0),
                "last_scraped_sample": last_scrape,
            }
        )

    # category heat from PN street rows
    cat_heat = defaultdict(list)
    for r in street_rows:
        if r.get("street_index") is not None and r.get("aim_category"):
            cat_heat[r["aim_category"]].append(r["street_index"])
    category_heat = [
        {
            "aim_category": k,
            "n": len(v),
            "median_street_index": round(sorted(v)[len(v) // 2], 3),
            "p25": round(sorted(v)[max(0, len(v) // 4)], 3),
            "p75": round(sorted(v)[min(len(v) - 1, (3 * len(v)) // 4)], 3),
        }
        for k, v in sorted(cat_heat.items(), key=lambda kv: sorted(kv[1])[len(kv[1]) // 2])
    ]

    # KPIs
    idxs = [r["street_index"] for r in street_rows if r.get("street_index") is not None]
    idxs_sorted = sorted(idxs)
    med = idxs_sorted[len(idxs_sorted) // 2] if idxs_sorted else None
    under = [r for r in street_rows if r.get("street_index") is not None and r["street_index"] < 1]
    under_sorted = sorted(under, key=lambda x: x["street_index"])[:40]
    # revenue-weighted exposure: undercut rows with rev
    exposure = sorted(
        [r for r in under if r.get("rev_cy2025_eur")],
        key=lambda x: x["rev_cy2025_eur"],
        reverse=True,
    )[:30]

    gen_am_med = None
    gen_am_spread_med = None
    if gen_vs_am:
        g = sorted([x["gen_vs_street"] for x in gen_vs_am if x.get("gen_vs_street") is not None])
        a = sorted([x["am_vs_street"] for x in gen_vs_am if x.get("am_vs_street") is not None])
        spreads = sorted(
            [
                (x["gen_vs_street"] - x["am_vs_street"])
                for x in gen_vs_am
                if x.get("gen_vs_street") is not None and x.get("am_vs_street") is not None
            ]
        )
        gen_am_med = {
            "n": len(gen_vs_am),
            "median_gen_vs_street": g[len(g) // 2] if g else None,
            "median_am_vs_street": a[len(a) // 2] if a else None,
        }
        gen_am_spread_med = spreads[len(spreads) // 2] if spreads else None
        for x in gen_vs_am:
            if x.get("gen_vs_street") is not None and x.get("am_vs_street") is not None:
                x["channel_spread"] = round(x["gen_vs_street"] - x["am_vs_street"], 3)

    exp_rev = sum((r.get("rev_cy2025_eur") or 0) for r in exposure)
    # Illustrative pressure: CY25 sales × (1 − street index) on undercut PNs — not a P&L claim
    pressure_eur = sum(
        (r.get("rev_cy2025_eur") or 0) * (1.0 - (r.get("street_index") or 1.0))
        for r in exposure
        if (r.get("street_index") or 1.0) < 1.0
    )

    autodoc = next((s for s in source_summaries if s["source"] == "Autodoc"), None)
    ks = next((s for s in source_summaries if s["source"] == "KS International"), None)

    autodoc_history_note = (
        "No usable Autodoc PN prices on disk — current and archive CSVs are £2 / no_results placeholders "
        f"(last stamp ~{str((autodoc or {}).get('last_scraped_sample') or '2026-05-30')[:10]}). "
        "Drift snapshots never included Autodoc. Do not treat Autodoc as a live competitive signal."
    )

    frame = {
        "title": "What this briefing tracks",
        "track": (
            "Online shop prices versus our reference customer / workshop price — "
            "starting from the ISZE list, then adding distributor margin (+40%), then dealer margin (+27.5%)."
        ),
        "good": (
            "What good looks like depends on the lens: IAM deep under our reference = pressure to watch; "
            "genuine sitting above IAM / above reference can be a deliberate OEM premium, not a miss. "
            "Below 1.0 = shop cheaper than our reference (competitive pressure / undercut). "
            "Near 1.0 = shop near our reference (neutral — not a target). "
            "Above 1.0 = shop dearer than our reference — can include a legitimate OEM / genuine premium."
        ),
        "not_this": (
            "Not Eucon PartsPool (that is the Competitive tab). "
            "Illustrative pressure is not a P&L write-off. "
            "Autodoc is not usable here — no real historical PN prices on disk."
        ),
        "margin_plain": (
            "Reference customer / workshop price = ISZE list → +40% distributor → +27.5% dealer "
            "(combined uplift ×1.785). Exact arithmetic is on hover / footnotes — not the headline."
        ),
        "min_n_rule": "Part-family bars need at least 3 real PN hits; smaller samples are grey and labelled directional only.",
    }

    story = {
        "frame": frame,
        "headline": (
            f"Online aftermarket quotes at about {med:.0%} of our reference customer price"
            if med is not None
            else "Aftermarket vs reference customer price — thin coverage"
        ),
        "bullets": [
            (
                f"{round(100 * (len(under) / len(idxs)))}% of real PN hits sit below our reference customer price"
                if idxs
                else "No PN hits after placeholder cleanup"
            ),
            f"€{exp_rev:,.0f} of CY2025 sales sits on the top undercut PNs (evidence list — not lost revenue)",
            f"Illustrative price pressure on that list ≈ €{pressure_eur:,.0f} (sales × gap to reference — directional, not a write-off)",
            (
                f"On KS dual-listed PNs (n={gen_am_med['n']}): genuine median {gen_am_med['median_gen_vs_street']:.2f}× reference vs AM {gen_am_med['median_am_vs_street']:.2f}× — channel gap ≈ {gen_am_spread_med:.2f}"
                if gen_am_med and gen_am_spread_med is not None
                else "No KS genuine+AM dual hits"
            ),
            autodoc_history_note,
        ],
        "why_ks_gen_vs_am": (
            "KS International lists the same ISZE part number with a genuine quote and an aftermarket quote. "
            "Comparing both to our reference customer price shows the UK catalogue channel gap — "
            "where genuine sits relative to reference (often a deliberate premium) vs how far IAM undercuts. "
            "It is not 'ISZE vs KS'; it is 'genuine vs IAM on one shelf'."
        ),
        "definitions": {
            "reference_sellout": {
                "label": "Reference customer / workshop price",
                "formula": "ISZE list × 1.40 (distributor) × 1.275 (dealer) = list × 1.785",
                "plain": "Start from ISZE list, add distributor margin (+40%), then dealer margin (+27.5%). Management compare point — not raw list.",
            },
            "price_index": {
                "label": "Price index",
                "formula": "shop € ÷ reference customer price €",
                "plain": (
                    "Below 1.0 = shop cheaper than our reference (pressure / undercut). "
                    "Near 1.0 = shop near our reference (neutral — not a target). "
                    "Above 1.0 = shop dearer — can be a legitimate OEM / genuine premium, not a failure."
                ),
            },
            "genuine_index": {
                "label": "Genuine vs reference",
                "formula": "KS genuine € ÷ reference customer price €",
                "plain": "Where the genuine catalogue line sits vs our reference on that PN. Above 1.0 can be a deliberate OEM premium.",
            },
            "am_index": {
                "label": "Aftermarket vs reference",
                "formula": "shop aftermarket € ÷ reference customer price €",
                "plain": "Where the IAM / online aftermarket line sits vs our reference. Deep under 1.0 = competitive pressure.",
            },
            "channel_spread": {
                "label": "Channel spread",
                "formula": "genuine index − aftermarket index",
                "plain": "Width of the genuine vs IAM gap on the same PN in the KS catalogue.",
            },
            "price_pressure": {
                "label": "Illustrative price pressure €",
                "formula": "CY2025 sales € × (1 − aftermarket index) on undercut PNs",
                "plain": "Directional scale of billed sales where the shop sits below our reference — not a booked loss.",
            },
        },
    }

    scrape = {
        "built_at_utc": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "mode": "A",
        "label": "Live shop scrape — not Eucon PartsPool (see Competitive tab)",
        "compare_basis": {
            "street_factor": STREET_FACTOR,
            "formula": "reference_customer_price = ISZE_list × 1.40 × 1.275 (= ×1.785); index = shop_EUR / reference; <1 = shop cheaper; >1 = shop dearer (may include OEM premium)",
            "ui_label": "reference customer / workshop price",
            "distributor_uplift": 1.40,
            "dealer_uplift": 1.275,
            "gbp_eur": GBP_EUR,
            "sek_eur": SEK_EUR,
            "autodoc_placeholder_max_gbp": AUTODOC_PLACEHOLDER_GBP,
            "min_n_family": 3,
        },
        "story": story,
        "autodoc_history": {"usable": False, "note": autodoc_history_note},
        "kpis": {
            "sources": len(source_summaries),
            "real_pn_price_hits": len(street_rows),
            "placeholders_dropped": placeholders_dropped,
            "median_am_vs_street": med,
            "share_undercut_street": round(len(under) / len(idxs), 3) if idxs else None,
            "ks_gen_vs_am": gen_am_med,
            "ks_channel_spread_median": gen_am_spread_med,
            "exposure_rev_cy2025_eur": round(exp_rev, 0),
            "illustrative_price_pressure_eur": round(pressure_eur, 0),
            "ks_last_scrape": (ks or {}).get("last_scraped_sample"),
            "autodoc_last_scrape": (autodoc or {}).get("last_scraped_sample"),
        },
        "sources": source_summaries,
        "category_heat": category_heat,
        "top_undercuts_vs_street": under_sorted,
        "revenue_exposure_undercut": exposure,
        "ks_genuine_vs_am": gen_vs_am[:40],
        "category_shop_samples": [],
        "deep_link_full": "../pricing/ISZE_Parts_Price_Intelligence.html",
        "caveats": [
            "Live shop scrape ≠ Eucon PartsPool (Competitive tab).",
            "Compare point = reference customer / workshop price (ISZE list → +40% distributor → +27.5% dealer).",
            "Illustrative price pressure is sales × gap to reference — not a P&L write-off.",
            autodoc_history_note,
            "Mekonomen fill is thin; SEK FX is directional.",
            "Category shop scrapes (T&M / Tranz / Auto365) have no PN join — excluded from this briefing.",
            "Part-family chart: n<3 shown grey (directional only).",
        ],
    }

    DATA.mkdir(parents=True, exist_ok=True)
    (DATA / "partgroups_scrape.json").write_text(
        json.dumps(scrape, indent=2, ensure_ascii=False), encoding="utf-8"
    )
    return scrape


def sync_sibling() -> None:
    SIBLING.mkdir(parents=True, exist_ok=True)
    for p in DATA.glob("partgroups_*.json"):
        shutil.copy2(p, SIBLING / p.name)


if __name__ == "__main__":
    g = build_gps_pms()
    s = build_scrape()
    sync_sibling()
    # Aftermarket Live Pricing page retired 2026-10-02 (superseded by
    # 02_dashboards/pricing/ISZE_Parts_Price_Intelligence.html); its builder is archived in
    # 01_data/92_archive/price_pages_retired_2026-10-02/. Not regenerated here any more.
    ie = next(x for x in g["gps_pms_scatter_cy2025"] if x["db"] == "IRELAND")
    print(
        "IRELAND uio",
        ie["uio_units"],
        "spu",
        round(ie["gps_spu_eur"], 2),
        "vs wallet",
        round(ie["gps_capture_vs_wallet"], 3),
        "flags",
        ie["quality_flags"][:1],
    )
    print(
        "scrape hits",
        s["kpis"]["real_pn_price_hits"],
        "placeholders dropped",
        s["kpis"]["placeholders_dropped"],
        "median index",
        s["kpis"]["median_am_vs_street"],
    )
    print("aftermarket live page retired 2026-10-02: see 02_dashboards/pricing/ISZE_Parts_Price_Intelligence.html")
