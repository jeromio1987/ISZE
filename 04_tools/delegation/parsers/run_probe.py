# -*- coding: utf-8 -*-
"""Run every site parser against the page already saved on disk. No network.

    python 04_tools/delegation/parsers/run_probe.py                 # all sites
    python 04_tools/delegation/parsers/run_probe.py --site omega    # one site
    python 04_tools/delegation/parsers/run_probe.py --json out.json # machine-readable

This is the acceptance tool for the Phase 1 parser build: it proves a parser works
without fetching anything.

A parser whose page carries no Isuzu part number at all emits a `match_method="category_only"`
row with a null `part_no`. `ledger_schema.row_problems()` flags that as "no part_no", but
`MATCH_METHODS` allows the method and the ledger's own `validate()` only length-checks numbers
that are present, so it is listed here under "known gaps" and does not fail the probe.
Inventing a number to clear the check is the one thing not allowed.
"""
from __future__ import annotations

import argparse
import json
import sys
import traceback
from pathlib import Path

for _s in (sys.stdout, sys.stderr):
    if _s is not None and hasattr(_s, "reconfigure"):
        try:
            _s.reconfigure(encoding="utf-8", errors="replace")
        except Exception:
            pass

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

import registry                                                   # noqa: E402
from ledger_schema import row_problems, apply_fx                  # noqa: E402


def run_one(name: str, raw: bool = False) -> dict:
    """Parse one site's saved page. Returns a result dict; never raises."""
    out = {"site": name, "ok": False, "rows": 0, "problems": [], "known_gaps": [], "error": None,
           "page": None, "pages_bytes": None, "by_price_type": {}, "sample": []}
    try:
        mod = registry.load(name)
    except Exception as e:                                         # noqa: BLE001
        out["error"] = f"import failed: {type(e).__name__}: {e}"
        return out

    page = registry.probe_path(mod)
    out["page"] = page.name
    if not page.exists():
        out["error"] = f"page not on disk: {page}"
        return out
    out["pages_bytes"] = page.stat().st_size

    html = registry.probe_html(mod)
    observed = getattr(mod, "PROBE_DATE", "2026-09-24")
    try:
        rows = mod.parse(html, source_url=getattr(mod, "PROBE_URL", ""), observed_at=observed)
    except NotImplementedError as e:
        out["error"] = f"still a stub: {e}"
        return out
    except Exception as e:                                         # noqa: BLE001
        out["error"] = f"parse raised: {type(e).__name__}: {e}"
        out["traceback"] = traceback.format_exc()[-1200:]
        return out

    # Native price faithfully read; the euro value is filled centrally from the one
    # shared rate table, so no parser applies its own rate. `--raw` shows it unconverted.
    if not raw:
        rows, note = apply_fx(rows)
        out["fx_note"] = note

    out["rows"] = len(rows)

    # A partial parse is the dangerous shape: a page that used to yield two priced rows
    # quietly yields one, the probe says OK, and an observation disappears without anyone
    # noticing. That is the Mekonomen pattern. So a site module MAY declare how many rows
    # the saved page should produce; a shortfall is reported as a visible gap, not a
    # silent pass. It is not a hard failure — a genuinely thinner page is legitimate, and
    # autoline's 15 price-on-request rows prove thin pages are real.
    expected = getattr(mod, "EXPECTED_ROWS", None)
    if expected is not None and len(rows) != expected:
        out["known_gaps"].append(
            f"row count {len(rows)} does not match the declared EXPECTED_ROWS={expected} "
            f"for this page — a partial parse, check before trusting the rows"
        )

    for r in rows:
        pt = r.get("price_type")
        out["by_price_type"][pt] = out["by_price_type"].get(pt, 0) + 1
        for p in row_problems(r):
            # A `category_only` row carries no Isuzu number by definition: MATCH_METHODS
            # allows that method, and build_price_ledger.validate() only length-checks
            # numbers that are present (its own load_category_site() emits null part
            # numbers). ledger_schema.row_problems() is the stricter reader and flags it
            # anyway. That single finding is a known, reported gap — never a reason to
            # invent a part number — so it is listed but does not by itself fail the
            # probe. Every other finding still does.
            if p == "no part_no" and r.get("match_method") == "category_only":
                where = r.get("description") or r.get("source_url") or r.get("source")
                out["known_gaps"].append(f"{where}: {p} (category row; no Isuzu number on this page)")
            else:
                out["problems"].append(f"{r.get('part_no')}: {p}")

    out["sample"] = [
        {k: r.get(k) for k in ("part_no", "competitor_brand", "price", "currency",
                               "price_eur", "price_type", "vat", "stock", "country")}
        for r in rows[:6]
    ]
    out["ok"] = bool(rows) and not out["problems"]
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--site")
    ap.add_argument("--json")
    ap.add_argument("--raw", action="store_true",
                    help="show native prices only; do not fill price_eur")
    a = ap.parse_args()

    names = [a.site] if a.site else registry.site_names()
    if not names:
        print("no site_*.py modules found")
        return 1

    results = [run_one(n, raw=a.raw) for n in names]

    for r in results:
        print("=" * 78)
        print(f"{r['site']}   page={r['page']}  ({r['pages_bytes'] or 0:,} bytes)")
        if r["error"]:
            print(f"  NOT OK — {r['error']}")
            if "traceback" in r:
                print(r["traceback"])
        else:
            print(f"  rows: {r['rows']}   by price_type: {r['by_price_type']}")
            for s in r["sample"]:
                print(f"    {s}")
            if r["problems"]:
                print(f"  SCHEMA PROBLEMS ({len(r['problems'])}):")
                for p in r["problems"][:12]:
                    print(f"    - {p}")
            else:
                print("  schema: clean")
            if r.get("known_gaps"):
                print(f"  known gaps ({len(r['known_gaps'])}) — reported, not hidden, and not "
                      f"a reason to invent a number:")
                for g in r["known_gaps"][:6]:
                    print(f"    - {g}")
        print(f"  OK: {r['ok']}")

    if a.json:
        Path(a.json).write_text(json.dumps(results, indent=2, ensure_ascii=False), encoding="utf-8")
        print(f"\nwritten {a.json}")

    bad = [r["site"] for r in results if not r["ok"]]
    print("\n" + "=" * 78)
    print(f"{len(results) - len(bad)}/{len(results)} sites OK" + (f" | not OK: {bad}" if bad else ""))
    return 0 if not bad else 1


if __name__ == "__main__":
    raise SystemExit(main())
