#!/usr/bin/env python3
"""P1.4 — list-to-pocket validation note (PR00/ZPR1 2023–25 vs billing).

Thin wrapper around build_pricing_history_findings outputs + validation CSV.
"""

from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

HERE = Path(__file__).resolve().parent
DER = HERE.parent / "00_derived"
OUT_CSV = DER / "list_to_pocket_validation_2023_2025.csv"
OUT_NOTE = HERE.parent / "01_Pricing" / "LIST_TO_POCKET_VALIDATION_20260819.md"
META_PATH = DER / "list_to_pocket_validation.meta.json"


def main() -> int:
    net_path = DER / "pr00_realization_network_cy.csv"
    by_db_path = DER / "pr00_realization_by_db_cy.csv"
    zpr1_path = DER / "zpr1_vs_pr00_by_payer_year.csv"
    hist_meta = DER / "pricing_history_findings.meta.json"

    if not net_path.is_file():
        print("Run build_pricing_history_findings.py first", file=sys.stderr)
        return 1

    net = pd.read_csv(net_path)
    by_db = pd.read_csv(by_db_path) if by_db_path.is_file() else pd.DataFrame()
    zpr1 = pd.read_csv(zpr1_path) if zpr1_path.is_file() else pd.DataFrame()

    rows = []
    for _, r in net.iterrows():
        rows.append(
            {
                "grain": "network",
                "year": r.get("year"),
                "payer_or_db": "ALL",
                "list_eur": r.get("list_eur"),
                "realized_eur": r.get("realized_eur"),
                "realization_pct": r.get("realization_pct"),
                "n_lines": r.get("n_lines"),
                "integrity_flag": "provisional_qa_pending",
            }
        )
    if not by_db.empty:
        for _, r in by_db.iterrows():
            rows.append(
                {
                    "grain": "db",
                    "year": r.get("year"),
                    "payer_or_db": r.get("distributor_code") or r.get("payer"),
                    "list_eur": r.get("list_eur"),
                    "realized_eur": r.get("realized_eur"),
                    "realization_pct": r.get("realization_pct"),
                    "n_lines": r.get("n_lines"),
                    "integrity_flag": "provisional_qa_pending",
                }
            )

    out = pd.DataFrame(rows)
    out.to_csv(OUT_CSV, index=False)

    integ = {}
    if hist_meta.is_file():
        integ = json.loads(hist_meta.read_text(encoding="utf-8")).get("integrity", {})

    note = [
        "# List-to-pocket validation (Mode B · 2026-08-19)",
        "",
        "PR00 list vs realized net billing by CY 2023–2025. **Provisional — QA pending.**",
        "",
        f"Integrity score (pricing history pack): **{integ.get('score', 'n/a')}/100** ({integ.get('band', 'unknown')})",
        "",
        "## Network realization",
        "",
    ]
    for _, r in net.iterrows():
        note.append(
            f"- **CY{int(r['year'])}**: list €{float(r.get('list_eur', 0)):,.0f} → realized €{float(r.get('realized_eur', 0)):,.0f} "
            f"({float(r.get('realization_pct', 0)):.1f}%)"
        )
    if not zpr1.empty:
        note += ["", "## ZPR1 vs PR00 (payer-year)", ""]
        for _, r in zpr1.head(10).iterrows():
            note.append(f"- {r.get('payer')} CY{int(r.get('year', 0))}: median gap {r.get('median_gap_pct', 'n/a')}%")

    note += [
        "",
        f"CSV: `{OUT_CSV.name}` · Full pack: `build_pricing_history_findings.py`",
        "",
        "Do not quote externally until integrity band is green.",
    ]
    OUT_NOTE.write_text("\n".join(note), encoding="utf-8")

    meta = {
        "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "rows": len(out),
        "integrity": integ,
        "outputs": {
            "csv": str(OUT_CSV.relative_to(HERE.parents[1])),
            "note": str(OUT_NOTE.relative_to(HERE.parents[1])),
        },
    }
    META_PATH.write_text(json.dumps(meta, indent=2), encoding="utf-8")
    print(f"wrote {OUT_CSV} ({len(out)} rows)")
    print(f"wrote {OUT_NOTE}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
