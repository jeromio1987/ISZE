"""Ingest filled OEM peer street EUR from scrape list → oem_peer_basket.csv.

Does **not** invent prices. Only writes rows where peer_street_eur (or
native+FX) is a positive number. Then reports whether apply_oem_benchmark
would upgrade any category (≥3 priced peers/cat).

Usage:
  python 03_analytics/isze_pricing/ingest_oem_peer_street.py
  python 03_analytics/isze_pricing/ingest_oem_peer_street.py --dry-run
  python 03_analytics/isze_pricing/ingest_oem_peer_street.py --scrape-list PATH

Fill columns on oem_peer_scrape_list.csv:
  peer_street_eur   — preferred (already EUR street/retail)
  peer_street_native + currency + fx_rate_to_eur + fx_as_of
                    — if only GBP/etc.; EUR = native * fx_rate_to_eur
  source / notes    — provenance (required for audit)

Never paste Eucon OEM list GBP as street. See OEM_STREET_ARRANGE.md.
"""
from __future__ import annotations

import argparse
import sys
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

ENGINE = Path(__file__).resolve().parent
if str(ENGINE) not in sys.path:
    sys.path.insert(0, str(ENGINE))

from premiums import (  # noqa: E402
    apply_oem_benchmark_to_config_block,
    load_oem_benchmark_from_basket,
)

DEFAULT_LIST = ENGINE / "oem_peer_scrape_list.csv"
DEFAULT_BASKET = ENGINE / "oem_peer_basket.csv"


def _num(s) -> float | None:
    if s is None or (isinstance(s, float) and pd.isna(s)):
        return None
    t = str(s).strip().replace(",", "")
    if t == "" or t.lower() == "nan":
        return None
    try:
        v = float(t)
    except ValueError:
        return None
    return v if v > 0 else None


def resolve_street_eur(row: pd.Series) -> tuple[float | None, str]:
    """Return (eur, note). Prefer peer_street_eur; else native×FX."""
    eur = _num(row.get("peer_street_eur"))
    if eur is not None:
        return eur, "peer_street_eur"
    native = _num(row.get("peer_street_native"))
    fx = _num(row.get("fx_rate_to_eur"))
    if native is None or fx is None:
        return None, ""
    cur = str(row.get("currency") or "").strip().upper() or "?"
    as_of = str(row.get("fx_as_of") or "").strip() or "fx_date_unspecified"
    return native * fx, f"converted {cur}→EUR @ {fx} as_of {as_of}"


def load_fills(path: Path) -> pd.DataFrame:
    df = pd.read_csv(path, dtype={"peer_oe_pn": str, "isze_pn": str})
    rows = []
    for _, r in df.iterrows():
        oe = str(r.get("peer_oe_pn") or "").strip()
        if not oe or oe.lower() == "nan":
            continue
        eur, how = resolve_street_eur(r)
        if eur is None:
            continue
        note_bits = [how]
        if str(r.get("notes") or "").strip():
            note_bits.append(str(r["notes"]).strip())
        fx_note = how if how.startswith("converted") else ""
        rows.append(
            {
                "peer_oe_pn": oe,
                "isze_pn": str(r.get("isze_pn") or "").strip(),
                "peer_market": str(r.get("peer_market") or "").strip(),
                "peer_oem": str(r.get("peer_oem") or "").strip(),
                "peer_street_eur": round(eur, 4),
                "fill_source": str(r.get("source") or "manual_scrape").strip(),
                "fill_notes": " | ".join(b for b in note_bits if b),
                "fx_labeled": fx_note,
            }
        )
    return pd.DataFrame(rows)


def apply_fills(basket: pd.DataFrame, fills: pd.DataFrame) -> tuple[pd.DataFrame, int]:
    """Apply street fills by peer_oe_pn.

    Propagates to **all** basket rows sharing the OE (+ oem/market when set).
    Scrape-list ``isze_pn`` is provenance only — do not leave sibling
    Isuzu PNs / GERMANY twin rows blank when the same Paccar/Ford OE is priced.
    """
    out = basket.copy()
    if "peer_street_eur" in out.columns:
        out["peer_street_eur"] = pd.to_numeric(out["peer_street_eur"], errors="coerce")
    n = 0
    for _, f in fills.iterrows():
        oe = f["peer_oe_pn"]
        m = out["peer_oe_pn"].astype(str).str.strip() == oe
        if f["peer_oem"]:
            m = m & (out["peer_oem"].astype(str) == f["peer_oem"])
        # Do not filter by scrape-list peer_market / isze_pn — same OE street
        # applies to IUK+GERMANY twins and sibling Isuzu PNs sharing the OE.
        if not m.any():
            continue
        out.loc[m, "peer_street_eur"] = f["peer_street_eur"]
        src = out.loc[m, "source"].astype(str)
        out.loc[m, "source"] = src.where(
            src.str.contains("street_fill", na=False),
            src + "|street_fill",
        )
        note_add = (
            f"street EUR {f['peer_street_eur']} via {f['fill_source']}"
            + (f"; {f['fx_labeled']}" if f["fx_labeled"] else "")
        )
        for idx in out.index[m]:
            prev = str(out.at[idx, "notes"] or "")
            if note_add not in prev:
                out.at[idx, "notes"] = (prev + " | " + note_add).strip(" |")
            out.at[idx, "status"] = "priced"
        n += int(m.sum())
    return out, n


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--scrape-list", type=Path, default=DEFAULT_LIST)
    ap.add_argument("--basket", type=Path, default=DEFAULT_BASKET)
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    fills = load_fills(args.scrape_list)
    print(f"scrape_list: {args.scrape_list}")
    print(f"fills with street: {len(fills)}")
    if fills.empty:
        print("No positive street prices found — nothing to write (no invent).")
        print("Fill peer_street_eur (or native+fx_rate_to_eur) then re-run.")
        return

    basket = pd.read_csv(args.basket, dtype={"isze_pn": str, "peer_oe_pn": str})
    updated, n_rows = apply_fills(basket, fills)
    print(f"basket rows updated: {n_rows}")

    if args.dry_run:
        tmp = ENGINE / "_tmp_oem_peer_basket_ingest_preview.csv"
        updated.to_csv(tmp, index=False, encoding="utf-8")
        oem = load_oem_benchmark_from_basket(tmp)
        tmp.unlink(missing_ok=True)
        print("DRY-RUN — basket not written")
    else:
        stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        bak = args.basket.with_suffix(f".bak_{stamp}.csv")
        basket.to_csv(bak, index=False, encoding="utf-8")
        updated.to_csv(args.basket, index=False, encoding="utf-8")
        print(f"wrote: {args.basket}")
        print(f"backup: {bak}")
        oem = load_oem_benchmark_from_basket(args.basket)

    if oem.empty:
        print("oem_benchmark: still blocked (need ≥3 priced peers per category)")
    else:
        print("oem_benchmark candidates:")
        print(oem.to_string(index=False))
        stub = {
            c: {"value": 1.3, "basis": "iam_derived", "max_premium_pct": 30}
            for c in oem["cat"]
        }
        merged = apply_oem_benchmark_to_config_block(stub)
        upgraded = [c for c, v in merged.items() if v.get("basis") == "oem_benchmark"]
        print(f"categories that would upgrade on next alloc: {upgraded or '(none — n<3)'}")

    print(
        "\nNext: cd 03_analytics; python -m isze_pricing.cli alloc "
        "--set allocation.target=0.03"
        "\n(apply_oem_benchmark runs via runlog.load_config)"
    )


if __name__ == "__main__":
    main()
