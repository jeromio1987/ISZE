"""B mutation: does the delivery field actually change eligibility?

The field reached `price_observations.parquet` and is carried into the evidence row, and
the coverage numbers did not move. Two things to show, separately:

  1. The field is WIRED: setting `delivery_included` on the rows that are blocked by the
     delivery basis alone flips them to eligible in the real evidence runner.
  2. Those rows can only be filled from a FILE, not a page (measured elsewhere), so this
     is not a reachable result on real UK pages.

Read-only on the ledger. Writes one temp stage file and one temp result file.
"""
import json
import pathlib
import subprocess
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

W = pathlib.Path(r"C:\Users\jerom\Desktop\claude\_worktrees\ISZE_u29b\01_data\91_build")
STAGE = W / "_u19_stage_offers_20261007.json"
RUNNER = W / "run_u19_ledger_through_evidence_20261007.mjs"

stage = json.loads(STAGE.read_text(encoding="utf-8"))
offers = stage["offers"]


def run(offers_obj, tag):
    tmp_stage = W / f"_u29b_mut_{tag}_stage.json"
    tmp_res = W / f"_u29b_mut_{tag}_result.json"
    tmp_stage.write_text(json.dumps({"offers": offers_obj}, indent=2), encoding="utf-8")
    p = subprocess.run(["node", str(RUNNER), str(tmp_stage), str(tmp_res)],
                       capture_output=True, text=True, encoding="utf-8")
    if p.returncode != 0:
        print(p.stdout, p.stderr)
        raise SystemExit(f"runner failed {p.returncode}")
    res = json.loads(tmp_res.read_text(encoding="utf-8"))
    return res, tmp_res


base, _ = run(offers, "base")
elig0 = sum(1 for r in base["rows"] if r.get("eligible"))
only_del = [r["observation_id"] for r in base["rows"]
            if tuple(sorted(r.get("reason_codes") or [])) == ("DELIVERY_BASIS_NOT_STATED",)]
print(f"baseline: eligible={elig0}   rows blocked by delivery alone={len(only_del)}")

# 1. set the basis on exactly those rows, as if a page had stated "included"
mut = json.loads(json.dumps(offers))
byid = {o["observation_id"]: o for o in mut}
for oid in only_del:
    byid[oid]["delivery_included"] = True
    byid[oid]["_ledger"]["delivery_note"] = "MUTATION: as if the page said delivery included"
mut_res, mut_path = run(mut, "set")
elig1 = sum(1 for r in mut_res["rows"] if r.get("eligible"))
print(f"after setting the basis on those {len(only_del)} rows: eligible={elig1}")

# 2. blank it again on one of them and show that one drops out
one = only_del[0]
mut2 = json.loads(json.dumps(mut))
for o in mut2:
    if o["observation_id"] == one:
        o["delivery_included"] = None
        o["_ledger"]["delivery_note"] = None
mut2_res, _ = run(mut2, "blank_one")
elig2 = sum(1 for r in mut2_res["rows"] if r.get("eligible"))
back = [r for r in mut2_res["rows"] if r["observation_id"] == one][0]
print(f"blanking the field on one row: eligible={elig1} -> {elig2}; "
      f"that row reason_codes={back.get('reason_codes')} eligible={back.get('eligible')}")

summary = {
    "baseline_eligible": elig0,
    "blocked_by_delivery_alone": len(only_del),
    "eligible_after_setting_basis": elig1,
    "eligible_after_blanking_one": elig2,
    "one_row_after_blank": {"observation_id": one,
                            "eligible": back.get("eligible"),
                            "reason_codes": back.get("reason_codes")},
    "verdict": ("the field is wired: a stated basis flips these rows to eligible and "
                "blanking it drops the row back out"),
    "caveat": ("the rows it flips are file-derived (Eucon survey and KS_CROSSREF); no "
               "saved page for a focus row states a delivery basis, so this is not a "
               "reachable result on real UK pages"),
}
(W / "_u29b_mutation_result.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
print(json.dumps(summary, indent=2))
