#!/usr/bin/env python3
"""P1.3 — supersession delta: billing still on old PN vs current PN.

Reads  : pn_supersession_map.csv, sales_fact.parquet
Writes : supersession_billing_delta.csv, SUPERSESSION_DELTA_NOTE_20260819.md
"""

from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

HERE = Path(__file__).resolve().parent
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))

import db_dlr_commercial_common as C  # noqa: E402

MAP_SRC = C.DERIVED / "pn_supersession_map.csv"
OUT_CSV = C.DERIVED / "supersession_billing_delta.csv"
OUT_NOTE = C.ISZE_ROOT / "01_data" / "01_Pricing" / "SUPERSESSION_DELTA_NOTE_20260819.md"
OUT_META = C.DERIVED / "supersession_billing_delta.meta.json"


def main() -> int:
    if not MAP_SRC.is_file():
        print(f"MISSING {MAP_SRC}", file=sys.stderr)
        return 1

    mp = pd.read_csv(MAP_SRC, dtype=str)
    mp["old_pn"] = mp["old_pn"].map(C.normalize_pn_scalar)
    mp["current_pn"] = mp["current_pn"].map(C.normalize_pn_scalar)
    mp["billed_on_old_pn_eur"] = pd.to_numeric(mp.get("billed_on_old_pn_eur"), errors="coerce").fillna(0)

    C._ensure_prism()
    from config import SALES_FACT_PARQUET  # noqa: WPS433

    sf = pd.read_parquet(
        SALES_FACT_PARQUET,
        columns=["billing_date", "part_number", "net_sales_value", "billed_qty", "year"],
    )
    sf["pn"] = sf["part_number"].map(C.normalize_pn_scalar)
    sf = sf.dropna(subset=["pn"])
    sf["net_sales_value"] = pd.to_numeric(sf["net_sales_value"], errors="coerce").fillna(0)
    sf["billed_qty"] = pd.to_numeric(sf["billed_qty"], errors="coerce").fillna(0)

    old_set = set(mp["old_pn"].dropna())
    cur_set = set(mp["current_pn"].dropna())

    old_bill = (
        sf[sf["pn"].isin(old_set)]
        .groupby("pn", as_index=False)
        .agg(old_bill_eur_l12m=("net_sales_value", "sum"), old_bill_qty=("billed_qty", "sum"), last_bill=("billing_date", "max"))
    )
    cur_bill = (
        sf[sf["pn"].isin(cur_set)]
        .groupby("pn", as_index=False)
        .agg(cur_bill_eur=("net_sales_value", "sum"), cur_bill_qty=("billed_qty", "sum"))
    )

    out = mp.merge(old_bill, left_on="old_pn", right_on="pn", how="left").drop(columns=["pn"], errors="ignore")
    out = out.merge(cur_bill, left_on="current_pn", right_on="pn", how="left", suffixes=("", "_cur")).drop(
        columns=["pn"], errors="ignore"
    )
    for c in ("old_bill_eur_l12m", "old_bill_qty", "cur_bill_eur", "cur_bill_qty"):
        out[c] = pd.to_numeric(out.get(c), errors="coerce").fillna(0)
    out["delta_eur_vs_map"] = out["old_bill_eur_l12m"] - out["billed_on_old_pn_eur"]
    out["still_billing_old"] = out["old_bill_eur_l12m"] > 0
    out = out.sort_values("old_bill_eur_l12m", ascending=False)

    out.to_csv(OUT_CSV, index=False)
    still = out[out["still_billing_old"]]
    top = still.head(15)

    note_lines = [
        "# Supersession billing delta (Mode B · 2026-08-19)",
        "",
        f"Map rows: **{len(mp):,}** · still billing on old PN: **{len(still):,}** · € on old PN (all-time in sales_fact): **€{still['old_bill_eur_l12m'].sum():,.0f}**",
        "",
        "## Top still-billing old PNs",
        "",
        "| Old PN | Current PN | Old bill € | Map € | Current bill € |",
        "|--------|------------|------------|-------|----------------|",
    ]
    for _, r in top.iterrows():
        note_lines.append(
            f"| {r['old_pn']} | {r['current_pn']} | {r['old_bill_eur_l12m']:,.0f} | {float(r['billed_on_old_pn_eur']):,.0f} | {r['cur_bill_eur']:,.0f} |"
        )
    note_lines += [
        "",
        "Source: `pn_supersession_map.csv` + `sales_fact.parquet`. IE40 `newest_pn` only — no EPC supersession chain.",
    ]
    OUT_NOTE.write_text("\n".join(note_lines), encoding="utf-8")

    meta = {
        "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "map_rows": len(mp),
        "still_billing_old": int(len(still)),
        "old_pn_eur_total": float(still["old_bill_eur_l12m"].sum()),
        "outputs": {"csv": str(OUT_CSV.relative_to(C.ISZE_ROOT)), "note": str(OUT_NOTE.relative_to(C.ISZE_ROOT))},
    }
    OUT_META.write_text(json.dumps(meta, indent=2), encoding="utf-8")
    print(f"wrote {OUT_CSV} ({len(out)} rows, {len(still)} still on old PN)")
    print(f"wrote {OUT_NOTE}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
