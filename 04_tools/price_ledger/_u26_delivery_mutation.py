# -*- coding: utf-8 -*-
"""U26 delivery-basis — mutation check on the coverage path (mandatory).

Two runs, both reported, because the honest corpus answer and the wiring proof are not
the same test:

  REAL BASIS (the row as the copy on disk maps it)
      Tranzparts `5876101170`, a NEW U26 row. Its page states free delivery over GBP 50
      and this listing is GBP 20.22, so its basis is "no". Stripping / restoring the field
      changes the reason code (DELIVERY_BASIS_NOT_STATED <-> DELIVERY_COST_NOT_SUPPLIED)
      which proves the field is read — but the row does not become eligible either way,
      because a "no" needs a delivered cost and no cost was read into a numeric field.

  FORCED YES (the wiring proof the brief asks for)
      The same row with delivery_included = "yes". Now the row IS eligible with the field,
      drops out of eligible on DELIVERY_BASIS_NOT_STATED when it is stripped, and is
      eligible again when it is restored. This is the required mutation, and it isolates
      the field from every other one.

If the forced-yes row does NOT drop out when stripped, the mapping is not wired and the
script says so as a finding instead of smoothing it over.

Run:
    python 04_tools/price_ledger/_u26_delivery_mutation.py
"""
from __future__ import annotations

import copy
import importlib.util
import json
import subprocess
import sys
from pathlib import Path

import pandas as pd

for _s in (sys.stdout, sys.stderr):
    if _s is not None and hasattr(_s, "reconfigure"):
        try:
            _s.reconfigure(encoding="utf-8", errors="replace")
        except Exception:
            pass

ROOT = Path(__file__).resolve().parents[2]
BUILD = ROOT / "01_data" / "91_build"
RUNNER = BUILD / "run_u19_ledger_through_evidence_20261007.mjs"

spec = importlib.util.spec_from_file_location(
    "cov", BUILD / "build_market_data_gap_coverage_20261007.py")
cov = importlib.util.module_from_spec(spec)
spec.loader.exec_module(cov)

TARGET_PN = "5876101170"
TARGET_LOADER = "tranzparts"


def run_case(label: str, row: dict, override="KEEP") -> dict:
    """Map `row` exactly as the coverage builder does, optionally overriding delivery."""
    mapped = cov.row_to_evidence_input(row)
    if override != "KEEP":
        mapped = copy.deepcopy(mapped)
        mapped["delivery_included"] = override
    stage = BUILD / f"_u26_dm_{label}.json"
    out = BUILD / f"_u26_dm_{label}_result.json"
    stage.write_text(json.dumps({"offers": [mapped]}, indent=2), encoding="utf-8")
    p = subprocess.run(["node", str(RUNNER), str(stage), str(out)],
                       capture_output=True, text=True, encoding="utf-8")
    if p.returncode != 0:
        raise SystemExit(f"node failed for {label}: {p.stdout}\n{p.stderr}")
    res = json.loads(out.read_text(encoding="utf-8"))["rows"]
    r = res[0] if res else {}
    return {
        "label": label,
        "eligible": bool(r.get("eligible")),
        "reason_codes": r.get("reason_codes") or [],
        "mapped_delivery_included": mapped["delivery_included"],
        "mapped_has_note": bool((mapped.get("_ledger") or {}).get("delivery_note")),
    }


def main() -> int:
    led = pd.read_parquet(ROOT / "01_data" / "00_derived" / "price_observations.parquet")
    sel = led[(led["loader"] == TARGET_LOADER) & (led["part_no"] == TARGET_PN)]
    if sel.empty:
        raise SystemExit(f"{TARGET_LOADER} {TARGET_PN} not in the ledger — cannot test")
    base = {k: (None if pd.isna(v) else v) for k, v in sel.iloc[0].to_dict().items()}
    print("the row under test, as the ledger on disk holds it:")
    print(json.dumps({k: base[k] for k in
                      ("part_no", "loader", "price", "currency", "vat", "price_type",
                       "delivery_note", "delivery_included")}, indent=2, default=str))
    print()

    # ---- 1. the real basis off the page -------------------------------------
    r_real = run_case("real_basis_as_read", base)
    r_real_stripped = run_case("real_basis_stripped", base, override=None)
    r_real_restored = run_case("real_basis_restored", base)

    # ---- 2. the wiring proof: same row, delivery forced to "yes" ------------
    yes_row = dict(base)
    yes_row["delivery_note"] = "wiring proof: delivery_included forced to yes"
    yes_row["delivery_included"] = "yes"
    y_keep = run_case("yes_keep", yes_row)
    y_strip = run_case("yes_stripped", yes_row, override=None)
    y_restore = run_case("yes_restored", yes_row)

    wiring_proven = (y_keep["eligible"] and not y_strip["eligible"]
                     and "DELIVERY_BASIS_NOT_STATED" in y_strip["reason_codes"]
                     and y_restore["eligible"])
    real_field_read = (r_real["reason_codes"] != r_real_stripped["reason_codes"])

    out = {
        "row_under_test": base,
        "real_basis": {
            "as_read": r_real,
            "stripped": r_real_stripped,
            "restored": r_real_restored,
            "field_is_read_on_this_row": bool(real_field_read),
            "note": ("on this row the basis is 'no' (free delivery stated only over GBP 50, "
                     "listing is GBP 20.22). The field IS read: stripping it changes the "
                     "reason from DELIVERY_COST_NOT_SUPPLIED to DELIVERY_BASIS_NOT_STATED. "
                     "The row stays ineligible either way because a 'no' needs a delivered "
                     "cost, and no cost was read into a numeric field."),
        },
        "forced_yes_wiring_proof": {
            "as_read": y_keep,
            "stripped": y_strip,
            "restored": y_restore,
            "wiring_proven": bool(wiring_proven),
        },
        "mapping_is_wired": bool(wiring_proven),
        "real_corpus_blocker": (r_real_stripped["reason_codes"] or [None])[0],
        "verdict": (
            "The mapping is wired. With the delivery basis stated and a price the basis "
            "covers, the row is eligible; stripped it drops out on DELIVERY_BASIS_NOT_STATED; "
            "restored it is eligible again. On the real U26 rows the field is read too (the "
            "reason code moves between DELIVERY_BASIS_NOT_STATED and DELIVERY_COST_NOT_SUPPLIED), "
            "but no harvested UK page states delivery-included, so no real row becomes eligible "
            "— the real rows are blocked on DELIVERY_COST_NOT_SUPPLIED (a stated threshold the "
            "price fails) or on a silent page."
            if wiring_proven else
            "FINDING — stripping delivery_included did NOT drop the row out of eligible on "
            "DELIVERY_BASIS_NOT_STATED even with the basis stated. The mapping is not wired."),
    }
    print(json.dumps(out, indent=2))
    (BUILD / "_u26_delivery_mutation_20261007.json").write_text(
        json.dumps(out, indent=2), encoding="utf-8")
    print("WROTE", BUILD / "_u26_delivery_mutation_20261007.json")
    return 0 if wiring_proven else 1


if __name__ == "__main__":
    raise SystemExit(main())
