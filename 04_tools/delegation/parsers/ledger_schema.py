# -*- coding: utf-8 -*-
"""Ledger schema — the single definition of a price-observation row.

`build_price_ledger.py` remains the authority for what the ledger accepts; this
module mirrors its `COLUMNS`, `PRICE_TYPES` and `MATCH_METHODS` so every per-site
parser builds rows the same way and none of them keeps a private copy.

If the ledger's schema changes, change it THERE first and re-copy the three
constants here. `--selftest` in `price_parsers.py` asserts the two agree.
"""
from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent                  # 04_tools/delegation/parsers
ISZE = HERE.parents[2]
CONSENT_SCRIPT = ISZE / "04_tools" / "autodoc_scraper" / "check_scrape_consent.py"

COLUMNS = [
    "obs_id", "part_no", "match_method", "competitor_brand", "competitor_pn", "description",
    "source", "source_url", "country", "observed_at", "vintage",
    "price", "price_avg", "currency", "price_eur", "fx_note", "vat",
    "price_type", "stock", "n_obs", "loader",
]

PRICE_TYPES = {
    "aftermarket_trade", "aftermarket_retail", "genuine_grey", "online_median",
    "survey_workshop", "survey_list", "dealer", "quote", "oem_value_line", "marketplace", "estimate",
    "aftermarket_rrp",
}

MATCH_METHODS = {"exact_oem", "crossref", "category_only"}

CURRENCIES = {"GBP", "EUR", "NOK", "SEK", "DKK", "USD", "ILS", "PLN"}

# Isuzu part numbers: 10 digits, written in several ways on the sites.
#   8974995480            bare
#   8-97499-548-0         dashed
#   ISU8983417890         geparden slug suffix (13 chars)
#   8980139111.UMI        suffix form
_PN_DASHED_RE = re.compile(r"\b(?:8[- ]?)?\d{2,3}[- ]?\d{3,4}[- ]?\d{3,4}[- ]?\d?\b")


_PN_SEPARATORS = re.compile(r"[\s\-\./]")
_PN_KNOWN_PREFIX = re.compile(r"^(?:ISU|ISZ)", re.I)     # geparden writes `ISU` + digits
_PN_KNOWN_SUFFIX = re.compile(r"\.(?:UMI)$", re.I)       # savion writes `<digits>.UMI`


def normalise_pn(raw: str | None) -> str | None:
    """Any Isuzu part-number shape -> bare 10 digits, or None.

    Never guesses: anything that does not reduce to exactly 10 digits returns None
    rather than a padded or truncated number.

    STRICT, since 2026-10-01. This used to strip *every* non-digit character, which
    meant any competitor code that happened to leave ten digits behind became an
    "Isuzu part number". Caught in the field: asking Omegaspareparts for our
    0082213890 returned a **Jeep Cherokee door mirror cover** whose
    `Part Manufacturer Number` is `00K82213890`; deleting the `K` left `0082213890`,
    exactly ten digits. Two more the same way — VW `3B2880261D84L` -> `3288026184` and
    VW `7E0-847-758-AA-9B9` -> `7084775899`. All three were Isuzu part numbers on paper
    and Jeep/VW parts in reality, which is the Mekonomen failure mode again.

    The rule now: remove only the separators a part number legitimately carries
    (`-`, space, `.`, `/`) and a recognised marker prefix/suffix (`ISU`, `.UMI`).
    **Any other letter means this is not an Isuzu number**, and it is refused.
    """
    if not raw:
        return None
    s = str(raw).strip()
    if not s:
        return None

    s = _PN_KNOWN_PREFIX.sub("", s)
    s = _PN_KNOWN_SUFFIX.sub("", s)
    s = _PN_SEPARATORS.sub("", s)

    if not s.isdigit():
        return None
    if len(s) == 10:
        return s
    if len(s) == 11 and s.startswith("0"):
        return s[1:]
    return None


def find_pns(text: str | None, limit: int = 200) -> list[str]:
    """Every distinct Isuzu part number in a blob of text, in order of first sight."""
    if not text:
        return []
    out: list[str] = []
    seen: set[str] = set()
    for m in _PN_DASHED_RE.finditer(text):
        pn = normalise_pn(m.group(0))
        if pn and pn not in seen:
            seen.add(pn)
            out.append(pn)
            if len(out) >= limit:
                break
    return out


def make_row(**kw) -> dict:
    """Fill every ledger COLUMNS key with None so each row is schema-complete.

    A parser that leaves a required field unset must say so explicitly — the
    loader refuses rows without `price_type` or `vintage`.
    """
    out = {c: None for c in COLUMNS}
    out.update(kw)
    return out


def row_problems(row: dict) -> list[str]:
    """Mechanical acceptance checks (plan §5, the cheap ones a script can do).

    Returns a list of reasons the row is not acceptable. Empty list = clean.
    """
    problems: list[str] = []
    missing = [c for c in COLUMNS if c not in row]
    if missing:
        problems.append(f"schema: missing keys {missing}")
    if not row.get("part_no"):
        problems.append("no part_no")
    elif not re.fullmatch(r"\d{10}", str(row["part_no"])):
        problems.append(f"part_no not 10 digits: {row['part_no']!r}")
    if row.get("price_type") not in PRICE_TYPES:
        problems.append(f"price_type not allowed: {row.get('price_type')!r}")
    if row.get("match_method") not in MATCH_METHODS:
        problems.append(f"match_method not allowed: {row.get('match_method')!r}")
    if not row.get("vintage"):
        problems.append("no vintage")
    if not row.get("source"):
        problems.append("no source")
    # `match_method` is how the ledger decides how much to trust `part_no`. A row
    # that carries a number under `exact_oem` asserts the number IS this part, so it
    # must have one. A row whose page only ties the number to the SEARCH (KS returns
    # a relevance hit that does not contain the searched number) belongs in
    # `category_only` instead — and still carries the number, or it is not joinable.
    if row.get("match_method") == "exact_oem" and not row.get("part_no"):
        problems.append("exact_oem but no part_no — cannot claim an exact match without a number")
    price = row.get("price")
    if price is not None:
        try:
            price = float(price)
        except (TypeError, ValueError):
            problems.append(f"price not numeric: {row.get('price')!r}")
        else:
            if price <= 0:
                problems.append(f"price not > 0: {price}")
            cur = row.get("currency")
            if cur is not None and cur not in CURRENCIES:
                problems.append(f"currency not allowed: {cur!r}")
    return problems


def consent_ok(url: str, path: str = "/") -> bool:
    """The existing robots gate, for one target. Never fetches the part page.

    Kept here so a per-site parser has exactly one documented way to check.
    """
    proc = subprocess.run(
        [sys.executable, str(CONSENT_SCRIPT), "--url", url, "--path", path],
        capture_output=True, text=True,
    )
    return proc.returncode == 0


def issue_obs_id(source: str, part_no: str, observed_at: str, price_type: str) -> str:
    """Stable observation id: same source+part+date+type gives the same id."""
    import hashlib
    raw = f"{source}|{part_no}|{observed_at}|{price_type}"
    return hashlib.sha1(raw.encode("utf-8")).hexdigest()[:16]


# ---------------------------------------------------------------------------
# FX — applied centrally, never by a parser
# ---------------------------------------------------------------------------
# A parser's job is to read the native price and currency off the page, faithfully.
# Converting to euro is done ONCE, here, so no two parsers can use different rates.
# The rates come from `04_tools/price_ledger/fx_rates.json`, written by
# `build_fx_rates.py` from the ECB's daily euro reference rates.
#
# Until 2026-09-24 the ledger's table held only EUR, GBP and SEK, so NOK, DKK and
# USD rows would have been refused outright. That gap is closed.
FX_FILE = ISZE / "04_tools" / "price_ledger" / "fx_rates.json"


def load_fx_rates() -> tuple[dict, str]:
    """{currency: eur_per_unit} plus a note naming the source. Never raises.

    REBASED 2026-09-25 on Jerome's instruction. GBP and SEK now take the ECB rate in
    `fx_rates.json` instead of the 2026-05-01 working rates, so this schema and the
    ledger builder can no longer disagree about the same currency. Before the rebase
    they could, and did: the ledger kept GBP at 1.17 while this file added only the
    currencies the working table lacked.

    The fallback below is only used when `fx_rates.json` is missing or unreadable, and
    carries the same ECB values so a fallback row cannot differ from a normal one.
    """
    fx = {"EUR": 1.0, "GBP": 1.16298002, "SEK": 0.0887744685}
    note = ("ECB euro reference rates (fallback: fx_rates.json not readable)")
    try:
        import json as _json
        payload = _json.loads(FX_FILE.read_text(encoding="utf-8"))
        rates = {k: float(v) for k, v in (payload.get("eur_per_unit") or {}).items()}
        if rates.get("EUR") == 1.0:
            fx.update(rates)
            note = (f"ECB euro reference rates, reference date "
                    f"{payload.get('reference_date')}")
    except Exception:                                          # noqa: BLE001
        pass
    return fx, note


def price_eur_for(price, currency, fx: dict | None = None) -> float | None:
    """Native price -> euro. Returns None when there is no price or no rate."""
    if price is None or not currency:
        return None
    if fx is None:
        fx, _ = load_fx_rates()
    rate = fx.get(str(currency).upper())
    if rate is None:
        return None
    try:
        return round(float(price) * rate, 2)
    except (TypeError, ValueError):
        return None


def apply_fx(rows: list[dict]) -> tuple[list[dict], str]:
    """Fill `price_eur` and `fx_note` on every row from the one shared rate table.

    Used by the runner so a parsed row carries its euro value, and so the source of
    the rate travels with the observation. The ledger applies the same rates again at
    load time; this keeps the two consistent rather than duplicated by hand.
    """
    fx, note = load_fx_rates()
    for r in rows:
        if r.get("price") is not None and r.get("currency"):
            got = price_eur_for(r["price"], r["currency"], fx)
            if got is not None:
                r["price_eur"] = got
                r["fx_note"] = note
    return rows, note
