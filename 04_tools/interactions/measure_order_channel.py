"""Order channel by distributor — manual (carries a customer PO) vs no PO.

WHAT THIS MEASURES, AND WHAT IT IS NOT
    The billing extract has no order-type field, so there is no column that says
    "this line came in by EDI". What it does carry is the customer purchase-order
    reference. A manual order needs that reference so it can be matched by hand;
    an order placed through an EDI link normally arrives without it.

    So this counts, per distributor and per year, billed lines that carry a
    purchase-order number and lines that do not. The no-PO share is a PROXY for
    the share of ordering that is already automated. It is not a measured EDI
    flag and it must be labelled as a proxy wherever it is shown.

    The proxy is validated against a distributor known to be on EDI (see the
    --validate flag): if that one shows a high no-PO share, the proxy is behaving.

USAGE
    python measure_order_channel.py            # build from the raw extracts
    python measure_order_channel.py --validate # also print the known-EDI check

OUT
    01_data/00_derived/order_channel_by_distributor.csv
    01_data/00_derived/order_channel_by_distributor.meta.json

Read-only over the raw extracts; writes only the two derived files. The raw
line-level billing is never printed to chat.
"""

from __future__ import annotations

import argparse
import json
import os
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

ROOT = Path(os.environ.get("ISZE_ROOT", r"C:\Users\jerom\Desktop\claude\ISZE"))
RAW = ROOT / "01_data" / "12_raw" / "sales"
DERIVED = ROOT / "01_data" / "00_derived"
OUT_CSV = DERIVED / "order_channel_by_distributor.csv"
OUT_META = DERIVED / "order_channel_by_distributor.meta.json"

# Raw extract layout is fixed: header on row 1, columns by position.
#   0 Billing Date | 5 Sold-to pt | 13 Net value | 17 Purchase order no.
COLS = [0, 5, 13, 17]
NAMES = ["billing_date", "sold_to_sap", "net_value", "po"]

# A distributor documented as being on EDI / data exchange (glossary: Jimmy
# Meskens, Petros thread). Used only to sanity-check the proxy.
KNOWN_EDI_HINTS = ("PETROS", "PETROPOULOS")


def load_sold_to_names() -> dict[str, str]:
    """sold-to code -> readable name, from the clean sales fact (mapping only)."""
    try:
        d = pd.read_parquet(
            ROOT / "01_data" / "00_derived" / "sales_fact.parquet",
            columns=["sold_to_sap", "sold_to"],
        )
        d = d.dropna().drop_duplicates()
        return {
            str(k).strip(): str(v).strip()
            for k, v in zip(d["sold_to_sap"], d["sold_to"])
        }
    except Exception as exc:
        print(f"WARN could not read sales_fact mapping: {exc}")
        return {}


def read_raw(path: Path) -> pd.DataFrame | None:
    try:
        d = pd.read_excel(path, sheet_name=0, header=0, usecols=COLS, names=NAMES)
    except Exception as exc:
        print(f"  skip {path.name}: {exc}")
        return None
    d["billing_date"] = pd.to_datetime(d["billing_date"], errors="coerce")
    d = d.dropna(subset=["billing_date"])
    d["sold_to_sap"] = d["sold_to_sap"].astype(str).str.strip()
    d["net_value"] = pd.to_numeric(d["net_value"], errors="coerce").fillna(0.0)
    d["po"] = d["po"].astype(str).str.strip()
    # pandas writes NaN as the string 'nan'; treat blank / nan / none as no PO.
    d["has_po"] = ~d["po"].str.lower().isin(["", "nan", "none", "nat"])
    d["year"] = d["billing_date"].dt.year
    return d[["billing_date", "year", "sold_to_sap", "net_value", "has_po"]]


def build(validate: bool) -> int:
    files = sorted(RAW.glob("*.XLSX"))
    if not files:
        print(f"no raw extracts in {RAW}")
        return 1
    parts = []
    for f in files:
        print(f"reading {f.name} ...")
        d = read_raw(f)
        if d is not None and len(d):
            d["source"] = f.name
            parts.append(d)
    if not parts:
        print("nothing read")
        return 1
    allrows = pd.concat(parts, ignore_index=True)
    # Overlapping extracts: keep one line per (date, sold_to, value, po) signature.
    before = len(allrows)
    allrows = allrows.drop_duplicates(
        subset=["billing_date", "sold_to_sap", "net_value", "has_po"]
    )
    print(f"deduped {before:,} -> {len(allrows):,} lines across {len(files)} extracts")

    names = load_sold_to_names()

    grouped = (
        allrows.groupby(["sold_to_sap", "year"])
        .agg(
            lines=("has_po", "size"),
            no_po_lines=("has_po", lambda s: int((~s).sum())),
            billed_value=("net_value", "sum"),
        )
        .reset_index()
    )
    val_nopo = (
        allrows[~allrows["has_po"]]
        .groupby(["sold_to_sap", "year"])["net_value"]
        .sum()
        .rename("no_po_value")
        .reset_index()
    )
    grouped = grouped.merge(val_nopo, on=["sold_to_sap", "year"], how="left")
    grouped["no_po_value"] = grouped["no_po_value"].fillna(0.0)
    grouped["no_po_line_pct"] = (grouped["no_po_lines"] / grouped["lines"] * 100).round(1)
    grouped["no_po_value_pct"] = (
        grouped["no_po_value"] / grouped["billed_value"].replace(0, pd.NA) * 100
    ).round(1)
    grouped["distributor"] = grouped["sold_to_sap"].map(lambda c: names.get(c, ""))

    out = grouped.sort_values(
        ["year", "billed_value"], ascending=[False, False]
    ).reset_index(drop=True)

    DERIVED.mkdir(parents=True, exist_ok=True)
    out.to_csv(OUT_CSV, index=False)

    totals = (
        allrows.groupby("year")
        .agg(lines=("has_po", "size"), no_po_lines=("has_po", lambda s: int((~s).sum())))
        .reset_index()
    )
    totals["no_po_line_pct"] = (totals["no_po_lines"] / totals["lines"] * 100).round(1)

    meta = {
        "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "method": "PROXY — no-PO line share, NOT a measured EDI flag",
        "why_proxy": (
            "The billing extract has no order-type field. A manual order carries a "
            "customer purchase-order reference; an EDI order normally does not. The "
            "no-PO share is therefore a proxy for the automated share, not a count of "
            "EDI orders. Label it as a proxy wherever it is shown."
        ),
        "columns": ["sold_to_sap", "year", "lines", "no_po_lines", "billed_value",
                    "no_po_value", "no_po_line_pct", "no_po_value_pct", "distributor"],
        "sources": [f.name for f in files],
        "lines_after_dedupe": int(len(allrows)),
        "by_year": totals.to_dict(orient="records"),
        "validation": {
            "known_edi_hint": list(KNOWN_EDI_HINTS),
            "note": "If a distributor known to be on EDI does not show a high no-PO "
                    "share, the proxy is weak and must not be quoted.",
        },
    }
    OUT_META.write_text(json.dumps(meta, indent=2), encoding="utf-8")
    print(f"\nwrote {OUT_CSV}")
    print(f"wrote {OUT_META}")
    print("\nnetwork no-PO line share by year (proxy for automated ordering):")
    print(totals.to_string(index=False))

    if validate:
        hits = out[out["distributor"].str.upper().str.contains("|".join(KNOWN_EDI_HINTS), na=False)]
        if hits.empty:
            print("\nVALIDATION: no known-EDI distributor found in the data — proxy unproven.")
        else:
            print("\nVALIDATION — known-EDI distributor(s):")
            print(hits[["distributor", "year", "lines", "no_po_line_pct", "no_po_value_pct"]]
                  .to_string(index=False))
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--validate", action="store_true")
    args = ap.parse_args()
    return build(args.validate)


if __name__ == "__main__":
    raise SystemExit(main())
