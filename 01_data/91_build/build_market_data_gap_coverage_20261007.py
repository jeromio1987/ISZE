"""
Build MARKET-DATA-GAP coverage from the existing price ledger — U26 rebuild, agent E.

Dated copy of `build_market_data_gap_coverage_20261006.py`. The change is the
generator, not the output shape:

  1. The worktree ledger is tried FIRST in `LEDGER_CANDIDATES`, so this build
     always reads the copy on the branch (the main clone holds no U26 rows). The
     main-clone path stays as the fallback.
  2. `DERIVED` (the inputs: family worklist, euros, meta) points at the worktree
     `01_data/00_derived`, so nothing is silently read from another clone.
  3. Outputs are dated 20261007.
  4. `METRICS` is written next to the outputs: billed euros of the Isuzu numbers
     that now have at least one eligible comparable offer, then rows against the
     50 threshold, then each exclusion reason by count, then the numbers still
     empty with their billed euros.

Read-only on the evidence layer. Does not scrape, does not call outside services,
does not send Eucon rows outside the EU (local Node only).
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import subprocess
import sys
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
# The worktree copy is FIRST on purpose: this branch holds the U26 rows, the main
# clone does not. The main-clone path is kept as the fallback, not the default.
LEDGER_CANDIDATES = [
    ROOT / "01_data" / "00_derived" / "price_observations.parquet",
    Path(r"C:\Users\jerom\Desktop\claude\ISZE\01_data\00_derived\price_observations.parquet"),
]
DERIVED = ROOT / "01_data" / "00_derived"
OUT_DERIVED = ROOT / "01_data" / "00_derived"
OUT_BUILD = ROOT / "01_data" / "91_build"
NODE_RUNNER = OUT_BUILD / "run_u19_ledger_through_evidence_20261007.mjs"

FAMILY_FILE = "epc_decode_worklist.csv"
DEFAULT_FOCUS_FAMILIES = ("brake_pad", "oil_filter")
FOCUS_FAMILIES = DEFAULT_FOCUS_FAMILIES  # mutated only when --families is passed
MARKETS = {
    "UK": {"distributor": "ITUK", "label": "UK (ITUK)"},
    "PT": {"distributor": "PORTUGAL", "label": "Portugal (I-Motors)"},
}
MIN_USABLE = 50
# tranzparts un-retired 2026-10-11: UK exact_oem rows now carry published
# shipping (£5.99 / free ≥£80) from tranzparts.co.uk/policies/shipping-policy.
# Still exclude mekonomen / auto365 / autodoc category scrapes.
RETIRED_LOADERS = {"mekonomen", "auto365", "autodoc"}


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def load_ledger() -> tuple[pd.DataFrame, Path]:
    for p in LEDGER_CANDIDATES:
        if p.exists():
            return pd.read_parquet(p), p
    raise SystemExit("price_observations.parquet not found on disk")


def focus_pn_map(families: tuple[str, ...] | None = None) -> pd.DataFrame:
    path = DERIVED / FAMILY_FILE
    df = pd.read_csv(path, dtype={"part_number": str})
    fams = families if families is not None else FOCUS_FAMILIES
    return df[df["pms_category"].isin(fams)][
        ["part_number", "pms_category", "eur_all"]
    ].drop_duplicates("part_number")


def full_pn_map() -> pd.DataFrame:
    """All classified PNs (any family) — used by the wider UK exact_oem report."""
    path = DERIVED / FAMILY_FILE
    df = pd.read_csv(path, dtype={"part_number": str})
    return df[["part_number", "pms_category", "eur_all"]].drop_duplicates("part_number")


# Pair cover is a coverage label only. It never writes a price-ledger row and
# never changes usable_rows / eligible_rows / eligible_pns (those stay direct offers).
PAIR_SOURCES = ("catalog_paired", "catalog_continuation")


def genuine_pairs_by_bvp() -> dict[str, list[str]]:
    """Own-brand number -> genuine numbers, catalog_paired or catalog_continuation only."""
    path = DERIVED / "genuine_bvp_crossref.csv"
    df = pd.read_csv(path, dtype=str)
    df = df[df["pair_source"].isin(PAIR_SOURCES)]
    out: dict[str, list[str]] = {}
    for bvp, gen in zip(df["bvp_pn"], df["genuine_pn"]):
        bvp_s = str(bvp).strip()
        gen_s = str(gen).strip()
        if not bvp_s or not gen_s or bvp_s == "nan" or gen_s == "nan":
            continue
        bucket = out.setdefault(bvp_s, [])
        if gen_s not in bucket:
            bucket.append(gen_s)
    return out


def pair_cover_for(
    pn: str,
    direct_eligible: int,
    pairs: dict[str, list[str]],
    uk_eligible_rows: dict[str, int],
) -> tuple[bool, str]:
    """True when an empty own-brand number's genuine has at least one eligible UK offer."""
    links = pairs.get(str(pn), [])
    if not links or int(direct_eligible or 0) > 0:
        return False, ""
    qualifying = sorted({g for g in links if uk_eligible_rows.get(g, 0) >= 1})
    if not qualifying:
        return False, ""
    return True, "|".join(qualifying)


def map_tax(vat) -> str | None:
    if vat is None or (isinstance(vat, float) and pd.isna(vat)):
        return None
    s = str(vat).strip().lower()
    if s in {"excl", "excluded", "exclusive", "ex"}:
        return "excluded"
    if s in {"incl", "included", "inclusive", "inc"}:
        return "included"
    if s in {"unknown", "nan", ""}:
        return None
    return None


def amount_scope_from_description(
    desc: str | None, match_method: str | None = None
) -> str:
    """Piece vs pack from listing text. Never invent a piece count.

    exact_oem: the searched OE part number *is* the sellable unit (including when
    that OE unit is itself a kit / pad set). Marking those as per_pack would demand
    pad counts the listing never states, and would block a like-for-like OE-to-OE
    kit price. Those stay per_piece.

    Other match methods: kit/set words in the title still mean per_pack, and pack
    contents stay unknown unless the text states an explicit size (see
    pack_from_description).
    """
    mm = (match_method or "").strip().lower()
    if mm == "exact_oem":
        return "per_piece"
    if not desc:
        return "per_piece"
    d = str(desc).upper()
    markers = (
        "PAD KIT",
        "BRAKE PAD SET",
        "FRONT BRAKE PAD SET",
        "ENGINE FILTER KIT",
        "FILTER KIT",
    )
    if any(tok in d for tok in markers):
        return "per_pack"
    if " KIT" in d or d.startswith("KIT") or ";KIT" in d:
        return "per_pack"
    return "per_piece"


def pack_from_description(desc: str | None) -> dict | None:
    """Fill pack.contents only when the listing states an explicit size.

    Accepts forms like 'set of 4', 'pack of 4', '4 pads', '4 pcs'. Returns None
    when the count is not written — never invents a pad or kit size from the
    part family alone.
    """
    if not desc:
        return None
    s = str(desc)
    m = re.search(
        r"(?:set|pack|kit)\s+of\s+(\d+)\b"
        r"|(\d+)\s*(?:pcs?|pieces?|pads?)\b",
        s,
        flags=re.IGNORECASE,
    )
    if not m:
        return None
    n = int(m.group(1) or m.group(2))
    if n < 1:
        return None
    return {
        "contents": [{"part": "piece", "quantity": n}],
        "pieces_per_pack": n,
        "unit": "piece",
    }


def match_fields(match_method: str | None, competitor_pn) -> dict:
    mm = (match_method or "").strip().lower()
    alt = None
    if competitor_pn is not None and not (isinstance(competitor_pn, float) and pd.isna(competitor_pn)):
        alt = str(competitor_pn)
    if mm == "exact_oem":
        return {
            "status": "unresolved",
            "basis": "exact_part_number",
            "competitor_pn": alt,
            "ledger_match_method": mm,
            "note": "OEM part number used on the listing search; not an approved fitment decision",
        }
    return {
        "status": "unresolved",
        "basis": mm or "unresolved",
        "competitor_pn": alt,
        "ledger_match_method": mm or "unresolved",
        "note": "cross-reference or category hit is a candidate, never an accepted match",
    }


def stock_meaning(stock) -> str | None:
    if stock is None or (isinstance(stock, float) and pd.isna(stock)):
        return None
    s = str(stock).strip().lower()
    if s == "in":
        return "in_stock_stated"
    if s == "out":
        return "out_of_stock_stated"
    return None


def delivery_basis(row: dict) -> tuple:
    """(delivery_included, note) read off the ledger row, honestly.

    The ledger carries two delivery columns since 2026-10-07 (U26):
    `delivery_note` (what the page said) and `delivery_included` (yes / no / blank).
    This maps them into the shape the shared evidence rule reads:

      "yes"   -> True    the listing price includes delivery
      "no"    -> False   the listing price excludes delivery
      blank   -> None    the page said nothing; the rule then excludes the row, correctly

    A blank is NOT the same as "no": the absence of a stated charge is never read as a
    charge. Anything that is not yes / no / blank is treated as blank rather than guessed,
    and `delivery_cost_eur` is taken from ledger `delivery_cost_amount` (+ currency) when present;
    otherwise None, so a "no" row without a stated cost is excluded on DELIVERY_COST_NOT_SUPPLIED.
    This is the ONLY place eligibility learns about delivery.
    """
    raw = row.get("delivery_included")
    note = row.get("delivery_note")
    if note is not None and isinstance(note, float) and pd.isna(note):
        note = None
    note_out = str(note) if note else None
    if raw is None or (isinstance(raw, float) and pd.isna(raw)):
        return None, note_out
    s = str(raw).strip().lower()
    if s == "yes":
        return True, note_out
    if s == "no":
        return False, note_out
    return None, note_out


def row_to_evidence_input(r: dict) -> dict:
    price = r.get("price")
    price_eur = r.get("price_eur")
    fx = None
    if price is not None and price_eur is not None:
        try:
            if float(price) != 0:
                fx = float(price_eur) / float(price)
        except (TypeError, ValueError):
            fx = None
    desc = r.get("description")
    match_method = r.get("match_method")
    tax = map_tax(r.get("vat"))
    alt = r.get("competitor_pn")
    if alt is not None and isinstance(alt, float) and pd.isna(alt):
        alt = None
    elif alt is not None:
        alt = str(alt)
    delivery, delivery_note = delivery_basis(r)
    pack = pack_from_description(desc)
    # Delivery cost when the page/policy states one (e.g. KS UK mainland min GBP 10).
    # Convert with the same observation FX when currency is not EUR. Blank stays None.
    delivery_cost_eur = None
    raw_cost = r.get("delivery_cost_amount")
    cost_ccy = r.get("delivery_cost_currency")
    if raw_cost is not None and not (isinstance(raw_cost, float) and pd.isna(raw_cost)):
        try:
            cost_amt = float(raw_cost)
            ccy = str(cost_ccy or "").strip().upper()
            if ccy in ("", "EUR"):
                delivery_cost_eur = cost_amt
            elif fx is not None and ccy == str(r.get("currency") or "").strip().upper():
                delivery_cost_eur = cost_amt * float(fx)
            elif fx is not None and ccy == "GBP" and str(r.get("currency") or "").strip().upper() == "GBP":
                delivery_cost_eur = cost_amt * float(fx)
            elif fx is not None and ccy == "GBP":
                # observation may already be in EUR; use observation FX only when currency matches GBP
                # else leave None rather than guess a second rate
                if str(r.get("currency") or "").strip().upper() in ("GBP", "GB"):
                    delivery_cost_eur = cost_amt * float(fx)
        except (TypeError, ValueError):
            delivery_cost_eur = None
    return {
        "observation_id": r["obs_id"],
        "source": r.get("source") or r.get("loader"),
        "observed_date": r.get("observed_at"),
        "original_reference": str(r["part_no"]),
        "alternative_reference": alt,
        "seller": r.get("competitor_brand") or r.get("source") or r.get("loader"),
        "market": r["country"],
        "currency": (str(r["currency"]).upper() if r.get("currency") else None),
        "tax": tax,
        "pack": pack,
        "channel": "web_listing",
        "availability_meaning": stock_meaning(r.get("stock")),
        "role": "competitor",
        "level": "public_advertised_retail",
        "part_number": str(r["part_no"]),
        "case_id": f"U19-{r['country']}-{r['part_no']}",
        "amount": None if price is None or (isinstance(price, float) and pd.isna(price)) else float(price),
        "amount_scope": amount_scope_from_description(desc, match_method),
        "unit": "piece",
        "vat_rate": (
            0
            if tax == "excluded"
            else (
                float(r["vat_rate"])
                if r.get("vat_rate") is not None
                and not (isinstance(r.get("vat_rate"), float) and pd.isna(r.get("vat_rate")))
                else None
            )
        ),
        "vat_rate_unit": "percent" if tax in ("excluded", "included") and (
            tax == "excluded"
            or (
                r.get("vat_rate") is not None
                and not (isinstance(r.get("vat_rate"), float) and pd.isna(r.get("vat_rate")))
            )
        ) else None,
        "delivery_included": delivery,
        "delivery_cost_eur": delivery_cost_eur,
        "fx_to_eur": fx,
        "fx_date": "2026-09-24" if fx is not None else None,
        "match": match_fields(match_method, r.get("competitor_pn")),
        "_ledger": {
            "loader": r.get("loader"),
            "price_type": r.get("price_type"),
            "vat": r.get("vat"),
            "match_method": match_method,
            "description": desc,
            "delivery_note": delivery_note,
            "price_eur": None
            if price_eur is None or (isinstance(price_eur, float) and pd.isna(price_eur))
            else float(price_eur),
        },
    }


def euros_table() -> pd.DataFrame:
    gps = pd.read_csv(DERIVED / "gps_spu_pms.csv")
    return gps[
        (gps["year"] == 2025)
        & (gps["line_type"] == "all")
        & (gps["distributor_code"].isin(["ITUK", "PORTUGAL"]))
        & (gps["pms_category"].isin(FOCUS_FAMILIES))
    ][
        [
            "year",
            "distributor_code",
            "pms_category",
            "net_sales_eur",
            "uio_units",
            "spu_eur",
        ]
    ].copy()


def main() -> int:
    OUT_DERIVED.mkdir(parents=True, exist_ok=True)
    OUT_BUILD.mkdir(parents=True, exist_ok=True)

    ledger, ledger_path = load_ledger()
    print(f"ledger read: {ledger_path}  ({len(ledger):,} rows)")
    ledger = ledger[~ledger["loader"].isin(RETIRED_LOADERS)].copy()
    focus = focus_pn_map()
    focus_pns = set(focus["part_number"].astype(str))
    pn_family = dict(zip(focus["part_number"].astype(str), focus["pms_category"]))
    pn_eur = dict(zip(focus["part_number"].astype(str), focus["eur_all"]))

    sufficiency = {}
    focus_rows = ledger[
        ledger["country"].isin(MARKETS.keys())
        & ledger["part_no"].astype(str).isin(focus_pns)
    ].copy()
    focus_rows["pms_category"] = focus_rows["part_no"].astype(str).map(pn_family)

    # U26 2026-10-07 (Jerome: "Fix the sufficiency label to count usable rows only").
    # The old label compared the RAW focus row count to the 50 bar, which printed
    # `sufficient` for UK on 79 rows that the evidence rules then excluded one and all —
    # a row count that flatters a market with no usable comparable. The status is now
    # decided on USABLE rows (rows the evidence checks actually pass), and it is decided
    # AFTER those checks run, below. Both numbers are kept and labelled: `focus_rows` is
    # the raw count, `usable_rows` is the eligible count. The raw count is not deleted;
    # it just no longer decides the label.
    print("=== DATA SUFFICIENCY (focus families via %s) ===" % FAMILY_FILE)
    for country, meta in MARKETS.items():
        sub = focus_rows[focus_rows["country"] == country]
        counts = (
            sub.groupby(["loader", "price_type", "pms_category"], dropna=False)
            .size()
            .reset_index(name="rows")
        )
        n = len(sub)
        sufficiency[country] = {
            "distributor": meta["distributor"],
            "label": meta["label"],
            "focus_rows": n,
            "usable_rows": None,          # filled in after the evidence checks, below
            "focus_pns_with_rows": int(sub["part_no"].nunique()),
            "status": "pending",          # decided on usable rows, after the evidence run
            "status_basis": "usable_rows (rows that pass the evidence checks) against min_usable",
            "min_usable": MIN_USABLE,
            "by_loader_price_type_family": counts.to_dict(orient="records"),
        }
        print(
            f"{meta['label']}: {n} focus rows, {sub['part_no'].nunique()} PNs "
            f"(usable count comes from the evidence run)"
        )
        if len(counts):
            print(counts.to_string(index=False))

    mapped = [row_to_evidence_input(r) for r in focus_rows.to_dict(orient="records")]
    stage_path = OUT_BUILD / "_u19_stage_offers_20261007.json"
    stage_path.write_text(json.dumps({"offers": mapped}, indent=2), encoding="utf-8")

    if not NODE_RUNNER.exists():
        raise SystemExit(f"missing node runner: {NODE_RUNNER}")

    result_path = OUT_BUILD / "_u19_evidence_results_20261007.json"
    proc = subprocess.run(
        ["node", str(NODE_RUNNER), str(stage_path), str(result_path)],
        capture_output=True,
        text=True,
        encoding="utf-8",
    )
    if proc.returncode != 0:
        sys.stderr.write(proc.stdout + "\n" + proc.stderr)
        raise SystemExit(f"node runner failed: {proc.returncode}")
    print(proc.stdout.strip())

    results = json.loads(result_path.read_text(encoding="utf-8"))
    by_obs = {r["observation_id"]: r for r in results["rows"]}

    agg = {}
    exclusion_totals = Counter()
    eligible_total = {c: 0 for c in MARKETS}
    eligible_eur = {c: 0.0 for c in MARKETS}
    eligible_pns = {c: set() for c in MARKETS}
    eligible_eur_pns = {c: [] for c in MARKETS}

    for r in focus_rows.to_dict(orient="records"):
        oid = r["obs_id"]
        er = by_obs.get(oid)
        if not er:
            continue
        key = (str(r["part_no"]), r["country"])
        if key not in agg:
            agg[key] = {
                "part_number": str(r["part_no"]),
                "market": r["country"],
                "distributor": MARKETS[r["country"]]["distributor"],
                "pms_category": pn_family.get(str(r["part_no"])),
                "ledger_rows": 0,
                "eligible_count": 0,
                "newest_observation_date": None,
                "reason_codes": Counter(),
            }
        a = agg[key]
        a["ledger_rows"] += 1
        dates = [d for d in [a["newest_observation_date"], r.get("observed_at")] if d]
        a["newest_observation_date"] = max(dates) if dates else None
        if er.get("eligible"):
            a["eligible_count"] += 1
            eligible_total[r["country"]] += 1
            eligible_pns[r["country"]].add(str(r["part_no"]))
        for code in er.get("reason_codes") or []:
            a["reason_codes"][code] += 1
            exclusion_totals[(r["country"], code)] += 1

    # U26 2026-10-07: the sufficiency label, decided on USABLE rows. A raw focus row that
    # the evidence rules exclude is not evidence a market can be compared on, so it must not
    # make the market read `sufficient`. Both counts are kept in the output.
    for country in MARKETS:
        u = eligible_total[country]
        sufficiency[country]["usable_rows"] = u
        sufficiency[country]["empty_focus_rows"] = sufficiency[country]["focus_rows"] - u
        sufficiency[country]["status"] = "sufficient" if u >= MIN_USABLE else "insufficient"
        print(
            f"{sufficiency[country]['label']}: {sufficiency[country]['focus_rows']} focus rows "
            f"(raw), {u} usable rows (eligible) -> {sufficiency[country]['status']}"
        )

    all_codes = sorted(
        {c for (_, c) in exclusion_totals.keys()}
        | {
            "PRODUCT_MATCH_UNRESOLVED",
            "PACK_CONTENTS_UNKNOWN",
            "CURRENCY_NOT_STATED",
            "TAX_BASIS_NOT_STATED",
            "TAX_RATE_NOT_STATED",
            "DELIVERY_BASIS_NOT_STATED",
            "DELIVERY_COST_NOT_SUPPLIED",
            "NO_ACCEPTED_LEVEL_BRIDGE",
            "NO_DATED_RATE_TO_EUR",
            "FX_DATE_NOT_STATED",
            "NO_AMOUNT_RECORDED",
            "NO_PRICE_LEVEL_DECLARED",
        }
    )

    uk_eligible_rows = {
        pn: int(a["eligible_count"])
        for (pn, market), a in agg.items()
        if market == "UK"
    }
    pairs = genuine_pairs_by_bvp()

    cov_rows = []
    for (pn, market), a in sorted(agg.items()):
        row = {
            "part_number": a["part_number"],
            "market": market,
            "distributor": a["distributor"],
            "pms_category": a["pms_category"],
            "ledger_rows": a["ledger_rows"],
            "eligible_count": a["eligible_count"],
            "newest_observation_date": a["newest_observation_date"],
            "market_sufficiency": sufficiency[market]["status"],
        }
        for code in all_codes:
            row[f"excl_{code}"] = int(a["reason_codes"].get(code, 0))
        covered, gpn = pair_cover_for(
            a["part_number"], a["eligible_count"], pairs, uk_eligible_rows
        )
        row["covered_via_genuine_pair"] = bool(covered)
        row["genuine_pair_pn"] = gpn
        cov_rows.append(row)

    direct_coverage_rows = len(cov_rows)

    empty_rows = []
    for country, meta in MARKETS.items():
        have = set(focus_rows.loc[focus_rows["country"] == country, "part_no"].astype(str))
        for _, fr in focus.iterrows():
            pn = str(fr["part_number"])
            if pn in have:
                continue
            covered, gpn = pair_cover_for(pn, 0, pairs, uk_eligible_rows)
            empty_rows.append(
                {
                    "part_number": pn,
                    "market": country,
                    "distributor": meta["distributor"],
                    "pms_category": fr["pms_category"],
                    "eur_all_billed_all_markets": fr["eur_all"],
                    "ledger_rows": 0,
                    "covered_via_genuine_pair": bool(covered),
                    "genuine_pair_pn": gpn,
                }
            )
    # Empty own-brand numbers are not in the direct coverage rows (no ledger row).
    # Append only the covered ones, with eligible_count 0, so the label sits beside
    # the direct count and does not add to it.
    existing_keys = {(r["part_number"], r["market"]) for r in cov_rows}
    for er in empty_rows:
        if not er["covered_via_genuine_pair"]:
            continue
        key = (er["part_number"], er["market"])
        if key in existing_keys:
            continue
        extra = {
            "part_number": er["part_number"],
            "market": er["market"],
            "distributor": er["distributor"],
            "pms_category": er["pms_category"],
            "ledger_rows": 0,
            "eligible_count": 0,
            "newest_observation_date": None,
            "market_sufficiency": sufficiency[er["market"]]["status"],
        }
        for code in all_codes:
            extra[f"excl_{code}"] = 0
        extra["covered_via_genuine_pair"] = True
        extra["genuine_pair_pn"] = er["genuine_pair_pn"]
        cov_rows.append(extra)
        existing_keys.add(key)

    cov_path = OUT_DERIVED / "market_data_gap_coverage_20261007.csv"
    pd.DataFrame(cov_rows).to_csv(cov_path, index=False)

    empty_path = OUT_DERIVED / "market_data_gap_empty_pns_20261007.csv"
    pd.DataFrame(empty_rows).sort_values(
        ["market", "pms_category", "eur_all_billed_all_markets"],
        ascending=[True, True, False],
    ).to_csv(empty_path, index=False)

    euros = euros_table()

    # --- the U26 question, euros first ---------------------------------------
    for country in MARKETS:
        pns = sorted(eligible_pns[country])
        eligible_eur_pns[country] = [
            {"part_number": p, "pms_category": pn_family.get(p), "eur_all_billed": pn_eur.get(p)}
            for p in pns
        ]
        eligible_eur[country] = float(
            sum((pn_eur.get(p) or 0) for p in pns)
        )
    billed_eur_all_markets = float(focus["eur_all"].sum())
    metrics = {
        "built_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "rule": ("billed euros of the Isuzu numbers that now have at least one eligible "
                 "comparable offer; then usable rows against the 50 threshold; then the "
                 "remaining exclusion reasons by count; then the numbers still empty with "
                 "their billed euros. eur_all is the all-market billed euro for the number "
                 "(epc_decode_worklist.csv); it is a size-of-part measure, not a per-market one."),
        "focus_families": list(FOCUS_FAMILIES),
        "focus_pn_count": int(len(focus_pns)),
        "billed_eur_all_markets_focus": round(billed_eur_all_markets, 2),
        "by_market": {},
    }
    for country, meta in MARKETS.items():
        empt = [r for r in empty_rows if r["market"] == country]
        reason_rows = sorted(
            [{"reason": c, "rows": n} for (m, c), n in exclusion_totals.items() if m == country],
            key=lambda x: -x["rows"],
        )
        metrics["by_market"][country] = {
            "label": meta["label"],
            "distributor": meta["distributor"],
            # U26 2026-10-07: both counts, side by side and labelled. `focus_rows` is the
            # raw count; `usable_rows` is what the evidence checks passed and what the
            # status is now decided on.
            "focus_rows": sufficiency[country]["focus_rows"],
            "usable_rows": sufficiency[country]["usable_rows"],
            "focus_rows_excluded": sufficiency[country].get("empty_focus_rows"),
            "sufficiency_status": sufficiency[country]["status"],
            "sufficiency_basis": sufficiency[country]["status_basis"],
            "focus_rows_status": sufficiency[country]["status"],
            "min_usable": MIN_USABLE,
            "eligible_rows": eligible_total[country],
            "eligible_pns": len(eligible_pns[country]),
            "eligible_pns_detail": eligible_eur_pns[country],
            "billed_eur_of_eligible_pns": round(eligible_eur[country], 2),
            "exclusions_by_reason": reason_rows,
            "rows_stating_a_delivery_basis": int(
                sum(1 for r in focus_rows.to_dict(orient="records")
                    if str(r.get("delivery_included") or "").strip().lower() in ("yes", "no"))
            ),
            "empty_pns": len(empt),
            "empty_pns_billed_eur": round(
                float(sum((r["eur_all_billed_all_markets"] or 0) for r in empt)), 2
            ),
            "empty_pns_top": sorted(
                empt, key=lambda r: -(r["eur_all_billed_all_markets"] or 0)
            )[:15],
        }
    pair_cover_rows = [r for r in cov_rows if r.get("covered_via_genuine_pair")]
    metrics["pair_cover"] = {
        "label": "via matching genuine part",
        "rule": (
            "An empty own-brand number counts as covered via the matching genuine "
            "part when genuine_bvp_crossref.csv links it with pair_source "
            "catalog_paired or catalog_continuation and that genuine number has "
            "at least one eligible UK offer. usable_rows, eligible_rows, "
            "eligible_pns and empty_pns stay direct offers only. This is not a "
            "ledger row."
        ),
        "crossref_file": "01_data/00_derived/genuine_bvp_crossref.csv",
        "direct_coverage_rows": direct_coverage_rows,
        "by_market": {
            country: {
                "covered_via_genuine_pair_count": sum(
                    1 for r in pair_cover_rows if r["market"] == country
                ),
                "covered_via_genuine_pair": [
                    {
                        "part_number": r["part_number"],
                        "genuine_pair_pn": r["genuine_pair_pn"],
                        "eligible_count_direct": int(r["eligible_count"]),
                    }
                    for r in pair_cover_rows
                    if r["market"] == country
                ],
            }
            for country in MARKETS
        },
    }
    metrics_path = OUT_DERIVED / "market_data_gap_coverage_20261007.metrics.json"
    metrics_path.write_text(json.dumps(metrics, indent=2, ensure_ascii=False), encoding="utf-8")

    meta = {
        "built_at": datetime.now(timezone.utc).isoformat(),
        "builder": "01_data/91_build/build_market_data_gap_coverage_20261007.py",
        "node_runner": "01_data/91_build/run_u19_ledger_through_evidence_20261007.mjs",
        "evidence_modules": [
            "Isuzu Universe/05_AIM_Universe/src/data/market_observation.js",
            "Isuzu Universe/05_AIM_Universe/src/data/comparable.js",
        ],
        "family_classification_file": f"01_data/00_derived/{FAMILY_FILE}",
        "euros_file": "01_data/00_derived/gps_spu_pms.csv",
        "ledger_path": str(ledger_path),
        "ledger_path_rule": ("the worktree copy is first in LEDGER_CANDIDATES; the "
                             "main-clone path remains only as a fallback"),
        "ledger_sha256": sha256_file(ledger_path),
        "ledger_meta_sha256": sha256_file(DERIVED / "price_observations.meta.json")
        if (DERIVED / "price_observations.meta.json").exists()
        else None,
        "family_file_sha256": sha256_file(DERIVED / FAMILY_FILE),
        "focus_families": list(FOCUS_FAMILIES),
        "focus_pn_count": int(len(focus_pns)),
        "focus_ledger_rows": int(len(focus_rows)),
        "coverage_rows": direct_coverage_rows,
        "pair_cover_rows_appended": len(cov_rows) - direct_coverage_rows,
        "empty_pn_rows": len(empty_rows),
        # U26 2026-10-07: the sufficiency label now counts USABLE rows (eligible), not raw
        # focus rows. Both are kept, labelled. This file was corrected for the sufficiency
        # fix (and to carry the delivery basis into the evidence row); see
        # `correction_note` below for the backup it was taken from.
        "sufficiency": sufficiency,
        "sufficiency_rule": ("status is decided on usable_rows (rows passing the evidence "
                             "checks) against min_usable; focus_rows is the raw count and is "
                             "retained but no longer decides the label"),
        "eligible_offers_by_market": eligible_total,
        "exclusion_totals_by_market": {
            f"{m}:{c}": n for (m, c), n in sorted(exclusion_totals.items())
        },
        "euros_2025_billed_line_type_all": euros.to_dict(orient="records"),
        "eucon_rule": "Eucon-sourced rows stay local; never sent to DeepSeek or any service outside the EU",
        "mapping_rules": {
            "match": "exact_oem -> basis exact_part_number (product id only); crossref/category_only -> unresolved candidate; never status accepted",
            "pack": ("exact_oem amount_scope=per_piece (OE PN is the sellable unit, even when named "
                     "PAD KIT); other methods: kit/set words -> per_pack. pack.contents filled only "
                     "from explicit size text (set of N / N pads); never inferred from family"),
            "level": "all competitor ledger rows -> public_advertised_retail; price_type kept in stage JSON under _ledger",
            "delivery": ("the ledger's delivery_note / delivery_included are read here (delivery_basis()); "
                         "yes -> true, no -> false, blank -> null. Blank is not 'no'. delivery_cost_eur "
                         "comes from delivery_cost_amount (+ currency) via observation FX when present"),
            "tax": "vat excl->excluded (+vat_rate 0 percent); unknown/blank->null",
        },
        "worktree": str(ROOT),
        # U26 2026-10-07: this build corrected two things in place, without a new version
        # label (this repo's convention), so the replaced files are named here.
        "correction_note": {
            "what": ("the delivery basis is now carried into the evidence row (the ledger's "
                     "delivery_note / delivery_included are read here), and the sufficiency "
                     "label now counts usable rows instead of raw focus rows"),
            "backup_suffix": ".bak_20261007T081251Z_before_delivery_col",
            "backed_up": [
                "market_data_gap_coverage_20261007.csv",
                "market_data_gap_coverage_20261007.meta.json",
                "market_data_gap_coverage_20261007.metrics.json",
            ],
            "convention": ("same date-named files rewritten in place; no new version label "
                           "such as _b was invented"),
        },
        "start_commit": subprocess.check_output(
            ["git", "rev-parse", "HEAD"], cwd=str(ROOT), text=True
        ).strip(),
    }
    meta_path = OUT_DERIVED / "market_data_gap_coverage_20261007.meta.json"
    meta_path.write_text(json.dumps(meta, indent=2), encoding="utf-8")

    summary = {
        "sufficiency": {k: v["status"] for k, v in sufficiency.items()},
        "focus_rows": {k: v["focus_rows"] for k, v in sufficiency.items()},
        "usable_rows": {k: v["usable_rows"] for k, v in sufficiency.items()},
        "eligible": eligible_total,
        "empty_pn_counts": {c: sum(1 for r in empty_rows if r["market"] == c) for c in MARKETS},
        "exclusion_totals": meta["exclusion_totals_by_market"],
        "euros": meta["euros_2025_billed_line_type_all"],
        "paths": {
            "coverage": str(cov_path),
            "meta": str(meta_path),
            "empty": str(empty_path),
            "metrics": str(metrics_path),
        },
    }
    (OUT_BUILD / "_u19_summary_20261007.json").write_text(
        json.dumps(summary, indent=2), encoding="utf-8"
    )
    print(json.dumps(summary, indent=2))
    print("WROTE", cov_path)
    print("WROTE", empty_path)
    print("WROTE", meta_path)
    print("WROTE", metrics_path)
    return 0


def run_uk_wider_exact(ledger: pd.DataFrame, ledger_path: Path) -> dict:
    """Second report: all UK exact_oem (or better) rows through the same evidence rules.

    Does not rewrite the focus coverage CSV. Writes:
      market_data_gap_coverage_uk_wider_exact_20261007.csv
      market_data_gap_coverage_uk_wider_exact_20261007.metrics.json
    """
    uk = ledger[
        (ledger["country"] == "UK")
        & (ledger["match_method"].astype(str).str.lower() == "exact_oem")
    ].copy()
    pn_all = full_pn_map()
    pn_family = dict(zip(pn_all["part_number"].astype(str), pn_all["pms_category"]))
    pn_eur = dict(zip(pn_all["part_number"].astype(str), pn_all["eur_all"]))
    uk["pms_category"] = uk["part_no"].astype(str).map(pn_family)

    mapped = [row_to_evidence_input(r) for r in uk.to_dict(orient="records")]
    stage_path = OUT_BUILD / "_u19_stage_offers_uk_wider_exact_20261007.json"
    stage_path.write_text(json.dumps({"offers": mapped}, indent=2), encoding="utf-8")
    result_path = OUT_BUILD / "_u19_evidence_results_uk_wider_exact_20261007.json"
    proc = subprocess.run(
        ["node", str(NODE_RUNNER), str(stage_path), str(result_path)],
        capture_output=True,
        text=True,
        encoding="utf-8",
    )
    if proc.returncode != 0:
        sys.stderr.write(proc.stdout + "\n" + proc.stderr)
        raise SystemExit(f"node runner failed (uk wider): {proc.returncode}")
    print(proc.stdout.strip())

    results = json.loads(result_path.read_text(encoding="utf-8"))
    by_obs = {r["observation_id"]: r for r in results["rows"]}

    exclusion_totals: Counter = Counter()
    eligible = 0
    eligible_pns: set[str] = set()
    focus_set = set(DEFAULT_FOCUS_FAMILIES)
    eligible_in_focus = 0
    eligible_outside = 0
    rows_out = []

    for r in uk.to_dict(orient="records"):
        oid = r["obs_id"]
        er = by_obs.get(oid) or {}
        fam = pn_family.get(str(r["part_no"]))
        is_el = bool(er.get("eligible"))
        if is_el:
            eligible += 1
            eligible_pns.add(str(r["part_no"]))
            if fam in focus_set:
                eligible_in_focus += 1
            else:
                eligible_outside += 1
        codes = er.get("reason_codes") or []
        for c in codes:
            exclusion_totals[c] += 1
        rows_out.append(
            {
                "part_number": str(r["part_no"]),
                "obs_id": oid,
                "market": "UK",
                "distributor": "ITUK",
                "pms_category": fam,
                "in_focus_brake_pad_oil_filter": bool(fam in focus_set),
                "loader": r.get("loader"),
                "match_method": r.get("match_method"),
                "vat": r.get("vat"),
                "delivery_included": r.get("delivery_included"),
                "delivery_cost_amount": r.get("delivery_cost_amount"),
                "eligible": is_el,
                "reason_codes": "|".join(codes),
                "price": r.get("price"),
                "currency": r.get("currency"),
                "description": r.get("description"),
            }
        )

    cov_path = OUT_DERIVED / "market_data_gap_coverage_uk_wider_exact_20261007.csv"
    pd.DataFrame(rows_out).to_csv(cov_path, index=False)

    metrics = {
        "built_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "scope": "UK exact_oem (or better) rows only — second report; focus CSV unchanged",
        "focus_families_for_split": list(DEFAULT_FOCUS_FAMILIES),
        "ledger_path": str(ledger_path),
        "uk_exact_oem_rows": int(len(uk)),
        "eligible_rows": eligible,
        "eligible_pns": len(eligible_pns),
        "eligible_rows_in_focus": eligible_in_focus,
        "eligible_rows_outside_focus": eligible_outside,
        "eligible_pns_detail": [
            {
                "part_number": p,
                "pms_category": pn_family.get(p),
                "eur_all_billed": pn_eur.get(p),
                "in_focus": pn_family.get(p) in focus_set,
            }
            for p in sorted(eligible_pns)
        ],
        "billed_eur_of_eligible_pns": round(
            float(sum((pn_eur.get(p) or 0) for p in eligible_pns)), 2
        ),
        "exclusions_by_reason": [
            {"reason": c, "rows": n}
            for c, n in sorted(exclusion_totals.items(), key=lambda x: -x[1])
        ],
        "comparison_to_focus_report": {
            "focus_families": list(DEFAULT_FOCUS_FAMILIES),
            "note": (
                "Focus report eligible counts only brake_pad + oil_filter. "
                "This file counts every UK exact_oem row that passes evidence."
            ),
        },
    }
    metrics_path = OUT_DERIVED / "market_data_gap_coverage_uk_wider_exact_20261007.metrics.json"
    metrics_path.write_text(json.dumps(metrics, indent=2, ensure_ascii=False), encoding="utf-8")
    print(
        f"UK wider exact_oem: {len(uk)} rows -> {eligible} eligible "
        f"(in focus {eligible_in_focus}, outside {eligible_outside})"
    )
    print("WROTE", cov_path)
    print("WROTE", metrics_path)
    return metrics


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    ap = argparse.ArgumentParser(
        description="MARKET-DATA-GAP coverage from the price ledger (U26 / 20261007)."
    )
    ap.add_argument(
        "--families",
        type=str,
        default="",
        help=(
            "Comma-separated pms_category list overriding the default focus "
            f"{list(DEFAULT_FOCUS_FAMILIES)}. Focus CSV/metrics are rewritten for that set."
        ),
    )
    ap.add_argument(
        "--also-uk-exact",
        action="store_true",
        help=(
            "Also write a second UK-only report for all exact_oem rows "
            "(market_data_gap_coverage_uk_wider_exact_20261007.*) without breaking the focus report."
        ),
    )
    return ap.parse_args(argv)


if __name__ == "__main__":
    args = parse_args()
    if args.families.strip():
        # Module-level override for focus_pn_map() / euros_table() / main().
        FOCUS_FAMILIES = tuple(  # noqa: F841 — assigned for main() readers of this name
            f.strip() for f in args.families.split(",") if f.strip()
        )
        # Bind into the module dict so focus_pn_map sees it (local assignment would shadow).
        globals()["FOCUS_FAMILIES"] = FOCUS_FAMILIES
        print(f"FOCUS_FAMILIES override: {FOCUS_FAMILIES}")
    rc = main()
    if args.also_uk_exact:
        ledger, ledger_path = load_ledger()
        ledger = ledger[~ledger["loader"].isin(RETIRED_LOADERS)].copy()
        run_uk_wider_exact(ledger, ledger_path)
    raise SystemExit(rc)
