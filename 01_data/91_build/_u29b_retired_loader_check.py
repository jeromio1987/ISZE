"""B: does the coverage builder drop the only loader that now fills the field?

`build_market_data_gap_coverage_20261007.py` has RETIRED_LOADERS including `tranzparts`,
but the U26 ledger declares the page-derived Tranzparts rows LIVE (loader `tranzparts`,
match_method exact_oem, the searched number printed on the product page). So the rows that
newly carry a delivery basis are filtered out before the evidence run.

This runs the real evidence runner over those rows, with and without the retired-loader
filter, and reports the eligibility outcome and the reason codes. Read-only on the ledger.
"""
import importlib.util
import json
import pathlib
import subprocess
import sys

import pandas as pd

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

W = pathlib.Path(r"C:\Users\jerom\Desktop\claude\_worktrees\ISZE_u29b")
BUILD = W / "01_data" / "91_build"
RUNNER = BUILD / "run_u19_ledger_through_evidence_20261007.mjs"

spec = importlib.util.spec_from_file_location(
    "cov", BUILD / "build_market_data_gap_coverage_20261007.py")
cov = importlib.util.module_from_spec(spec)
spec.loader.exec_module(cov)

ledger, path = cov.load_ledger()
print("ledger:", path, len(ledger), "rows")
print("RETIRED_LOADERS in the coverage builder:", sorted(cov.RETIRED_LOADERS))

focus = cov.focus_pn_map()
fpns = set(focus["part_number"].astype(str))

base = ledger[ledger["country"].isin(cov.MARKETS) & ledger["part_no"].astype(str).isin(fpns)].copy()
with_filter = base[~base["loader"].isin(cov.RETIRED_LOADERS)]
without = base

print(f"\nfocus rows with the retired-loader filter applied : {len(with_filter)}")
print(f"focus rows without that filter                   : {len(without)}")


def stage_and_run(df, tag):
    mapped = [cov.row_to_evidence_input(r) for r in df.to_dict(orient="records")]
    stage = BUILD / f"_u29b_{tag}_stage.json"
    res = BUILD / f"_u29b_{tag}_result.json"
    stage.write_text(json.dumps({"offers": mapped}, indent=2), encoding="utf-8")
    p = subprocess.run(["node", str(RUNNER), str(stage), str(res)],
                       capture_output=True, text=True, encoding="utf-8")
    if p.returncode != 0:
        raise SystemExit(p.stdout + p.stderr)
    return json.loads(res.read_text(encoding="utf-8")), mapped


for tag, df in (("filtered", with_filter), ("unfiltered", without)):
    r, mapped = stage_and_run(df, tag)
    elig = [x for x in r["rows"] if x.get("eligible")]
    from collections import Counter
    c = Counter(tuple(sorted(x.get("reason_codes") or [])) for x in r["rows"])
    print(f"\n--- {tag}: {len(df)} rows, eligible={len(elig)} ---")
    for rc, n in c.most_common():
        print(f"   {n:4d}  {rc}")

# the tranzparts rows specifically
tr = without[without["loader"] == "tranzparts"]
r, mapped = stage_and_run(tr, "tranzparts_only")
print(f"\n--- tranzparts focus rows only: {len(tr)} offered ---")
for o in mapped:
    print(f"  pn={o['part_number']} match={o['match']['status']} "
          f"tax={o['tax']} pack={o['pack']} deliv={o['delivery_included']} "
          f"cost={o['delivery_cost_eur']} scope={o['amount_scope']}")
for x in r["rows"]:
    print(f"  -> {x['observation_id']} eligible={x.get('eligible')} {x.get('reason_codes')}")
