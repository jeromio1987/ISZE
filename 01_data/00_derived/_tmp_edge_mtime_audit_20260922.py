"""Ad-hoc: mtime edge audit for the tonnage chain, 2026-09-22 rebuild.

Derives the read/write graph from the builders as written on disk and compares mtimes.
Not a pipeline script; diagnosis only.
"""
import csv
import os
from datetime import datetime

ROOT = r"C:\Users\jerom\Desktop\claude\ISZE"
DER = os.path.join(ROOT, "01_data", "00_derived")
PDATA = os.path.join(ROOT, "03_analytics", "Isuzu", "prism", "data")
BUILD = os.path.join(ROOT, "02_dashboards", "sales", "_build")
REBUILD_START = datetime(2026, 9, 22, 18, 20, 0)


def st(p):
    try:
        return datetime.fromtimestamp(os.path.getmtime(p))
    except OSError:
        return None


def show(p):
    t = st(p)
    return t.strftime("%Y-%m-%d %H:%M:%S") if t else "MISSING"


EDGES = [
    # (consumer, consumer mtime path, consumed input, note)
    ("build_vehicle_family_bands.py", os.path.join(ROOT, "03_analytics/Isuzu/prism/scripts/build_vehicle_family_bands.py"),
     os.path.join(DER, "genuine_bvp_crossref.csv"), "crossref vehicle_model"),
    ("build_vehicle_family_bands.py", os.path.join(DER, "vehicle_family_bands.csv"),
     os.path.join(DER, "epc_decode_batch1_banded_20260919.csv"), "EPC banded batch 1"),
    ("build_vehicle_family_bands.py", os.path.join(DER, "vehicle_family_bands.csv"),
     os.path.join(DER, "epc_decode_batch2_20260919.json"), "EPC batch 2 json"),
    ("build_vehicle_family_bands.py", os.path.join(DER, "vehicle_family_bands.csv"),
     os.path.join(DER, "bvp_pn_dimension.csv"), "universe"),
    ("build_vehicle_family_bands.py", os.path.join(DER, "vehicle_family_bands.csv"),
     os.path.join(PDATA, "pms_capture_supplement.csv"), "universe supplement"),
    ("build_vehicle_family_bands.py", os.path.join(DER, "vehicle_family_bands.csv"),
     os.path.join(DER, "sales_fact.parquet"), "euro per pn"),
    # The two rows below are NOT read by build_vehicle_family_bands.py. Verified by grep: the
    # script names series_to_tonnage.csv only inside its own "not_attempted" prose. They are kept
    # here so the cycle question is answered on the record rather than assumed.
    ("build_vehicle_family_bands.py", os.path.join(DER, "vehicle_family_bands.csv"),
     os.path.join(DER, "series_to_tonnage.csv"), "NOT READ (prose mention only)"),
    ("build_vehicle_family_bands.py", os.path.join(DER, "vehicle_family_bands.csv"),
     os.path.join(DER, "epc_decode_nseries_banded.csv"), "NOT READ (no reference in code)"),

    ("build_pms_tonnage_model.py", os.path.join(DER, "pms_tonnage_model.csv"),
     os.path.join(PDATA, "uio_by_model_bucket.csv"), "fleet buckets"),
    ("build_pms_tonnage_model.py", os.path.join(DER, "pms_tonnage_model.csv"),
     os.path.join(PDATA, "uio_ld_n35_share.csv"), "n35 share"),
    ("build_pms_tonnage_model.py", os.path.join(DER, "pms_tonnage_model.csv"),
     os.path.join(DER, "pms_capture_by_db_year.csv"), "actuals"),
    ("build_pms_tonnage_model.py", os.path.join(DER, "pms_tonnage_model.csv"),
     os.path.join(DER, "sales_fact.parquet"), "aim evolution billing"),
    ("build_pms_tonnage_model.py", os.path.join(DER, "pms_tonnage_model.csv"),
     os.path.join(DER, "aim_master_v2.csv"), "aim levels"),
    ("build_pms_tonnage_model.py", os.path.join(DER, "pms_tonnage_model.csv"),
     os.path.join(DER, "distributor_dimension.csv"), "db mapping"),

    ("build_nseries_tonnage_bands.py", os.path.join(DER, "nseries_tonnage_evolution.csv"),
     os.path.join(DER, "vehicle_family_bands.csv"), "family + universe"),
    ("build_nseries_tonnage_bands.py", os.path.join(DER, "nseries_tonnage_evolution.csv"),
     os.path.join(DER, "pms_tonnage_model.csv"), "lane column"),
    ("build_nseries_tonnage_bands.py", os.path.join(DER, "nseries_tonnage_evolution.csv"),
     os.path.join(DER, "epc_decode_batch1_banded_20260919.csv"), "model_codes tokens"),
    ("build_nseries_tonnage_bands.py", os.path.join(DER, "nseries_tonnage_evolution.csv"),
     os.path.join(DER, "epc_decode_batch2_20260919.json"), "edition strings"),
    ("build_nseries_tonnage_bands.py", os.path.join(DER, "nseries_tonnage_evolution.csv"),
     os.path.join(DER, "genuine_bvp_crossref.csv"), "series + registry_model"),
    ("build_nseries_tonnage_bands.py", os.path.join(DER, "nseries_tonnage_evolution.csv"),
     os.path.join(DER, "bvp_pn_dimension.csv"), "categories"),
    ("build_nseries_tonnage_bands.py", os.path.join(DER, "nseries_tonnage_evolution.csv"),
     os.path.join(PDATA, "pms_capture_supplement.csv"), "categories supplement"),
    ("build_nseries_tonnage_bands.py", os.path.join(DER, "nseries_tonnage_evolution.csv"),
     os.path.join(BUILD, "_deep_billing_cache.parquet"), "billing"),
    ("build_nseries_tonnage_bands.py", os.path.join(DER, "nseries_tonnage_evolution.csv"),
     os.path.join(DER, "pms_capture_by_db_year.csv"), "book markets"),

    ("_tonnage_capable.py", os.path.join(DER, "tonnage_capable_part_numbers.csv"),
     os.path.join(DER, "bvp_pn_dimension.csv"), "categories"),
    ("_tonnage_capable.py", os.path.join(DER, "tonnage_capable_part_numbers.csv"),
     os.path.join(DER, "genuine_bvp_crossref.csv"), "series evidence 1"),
    ("_tonnage_capable.py", os.path.join(DER, "tonnage_capable_part_numbers.csv"),
     os.path.join(DER, "epc_decode_batch1_20260919.json"), "series evidence 2"),
    ("_tonnage_capable.py", os.path.join(DER, "tonnage_capable_part_numbers.csv"),
     os.path.join(DER, "epc_decode_batch2_20260919.json"), "series evidence 2"),
    ("_tonnage_capable.py", os.path.join(DER, "tonnage_capable_part_numbers.csv"),
     os.path.join(DER, "sales_fact.parquet"), "billing weight"),

    ("build_model_code_to_tonnage.py (NOT run 22 Sep)", os.path.join(PDATA, "model_code_to_tonnage.csv"),
     os.path.join(DER, "epc_decode_batch1_20260919.json"), "decode"),
    ("build_model_code_to_tonnage.py (NOT run 22 Sep)", os.path.join(DER, "epc_decode_batch1_banded_20260919.csv"),
     os.path.join(DER, "epc_decode_worklist.csv"), "billed euro"),
]

OUT = os.path.join(DER, "_tmp_edge_mtime_audit_20260922.csv")
rows = []
for consumer, cons_path, inp, note in EDGES:
    ct, it = st(cons_path), st(inp)
    if ct is None or it is None:
        verdict = "MISSING FILE"
    elif ct < it:
        verdict = "STALE EDGE (consumer older than input)"
    else:
        verdict = "ok"
    rows.append({"consumer": consumer, "consumer_file": os.path.basename(cons_path),
                 "consumer_mtime": ct.strftime("%Y-%m-%d %H:%M:%S") if ct else "",
                 "reads": os.path.basename(inp),
                 "input_mtime": it.strftime("%Y-%m-%d %H:%M:%S") if it else "",
                 "input_before_rebuild_start": "yes" if (it and it < REBUILD_START) else "no",
                 "verdict": verdict, "note": note})

with open(OUT, "w", newline="", encoding="utf-8") as f:
    w = csv.DictWriter(f, fieldnames=list(rows[0]))
    w.writeheader()
    w.writerows(rows)

print(f"{'consumer':46s} {'reads':44s} {'consumer mtime':20s} {'input mtime':20s} verdict")
for r in rows:
    print(f"{r['consumer_file']:46s} {r['reads']:44s} {r['consumer_mtime']:20s} "
          f"{r['input_mtime']:20s} {r['verdict']}")
print()
bad = [r for r in rows if r["verdict"] != "ok"]
print(f"stale or missing edges: {len(bad)}")
for r in bad:
    print("  ", r)
print()
print("rebuild started:", REBUILD_START)
print("wrote", OUT)
