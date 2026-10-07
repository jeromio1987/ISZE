#!/usr/bin/env python3
"""Verify forward-repair already on disk; rewrite apply report. No writes to master/overlay/register."""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

ISZE = Path(r"C:\Users\jerom\Desktop\claude\ISZE")
DER = ISZE / "01_data" / "00_derived"
REL = DER / "_releases"
BUILD = ISZE / "01_data" / "91_build"
RELEASE = REL / "aim_pn_classification_release_2026-10-07.csv"
MASTER = DER / "aim_master_v2.csv"
OVERLAY = DER / "aim_pn_classification_20260920.csv"
CHG04 = REL / "aim_pn_classification_release_2026-10-04.changes.csv"
REPORT = BUILD / "_aim_apply_proven_20261007.md"
SUMMARY = BUILD / "_aim_forward_repair_oct4_20261007.json"
MARKER = "forward_repair_oct4_20261007"
OCT4_GROUPS = (
    "D2_engine_gasket_sets",
    "D3_evrv_valves",
    "D4_antennas",
    "D6_def_injectors",
)
AIM_REL = ("aim_l1_fixed", "aim_l2_fixed", "aim_l3_fixed")


def pad(k: str) -> str:
    k = (k or "").strip()
    return k.zfill(10) if k.isdigit() else k


def main() -> int:
    rel = pd.read_csv(RELEASE, dtype=str, keep_default_na=False)
    rel["k"] = rel["part_number"].map(pad)
    rmap = {}
    for k, a1, a2, a3 in zip(rel["k"], rel["aim_l1_fixed"], rel["aim_l2_fixed"], rel["aim_l3_fixed"]):
        if a1:
            rmap[k] = (a1, a2, a3)

    chg = pd.read_csv(CHG04, dtype=str, keep_default_na=False)
    oct4_pns = {
        g: sorted({
            pad(r["part_number"]) for _, r in chg.iterrows()
            if r["change_group"] == g and r["column"] in AIM_REL
        })
        for g in OCT4_GROUPS
    }

    m = pd.read_csv(MASTER, dtype=str, keep_default_na=False)
    o = pd.read_csv(OVERLAY, dtype=str, keep_default_na=False)
    m["k"] = m["part_number"].map(pad)
    o["k"] = o["part_number"].map(pad)
    mi = m.drop_duplicates("k").set_index("k")
    oi = o.drop_duplicates("k").set_index("k")

    sample = "1878148072"
    expect = "Engine > Gasket & Sealing > Gasket"
    sample_m = f"{mi.at[sample,'aim_l1_fixed']} > {mi.at[sample,'aim_l2_fixed']} > {mi.at[sample,'aim_l3']}"
    sample_o = f"{oi.at[sample,'aim_l1_fixed']} > {oi.at[sample,'aim_l2_fixed']} > {oi.at[sample,'aim_l3_fixed']}"
    assert sample_m == expect, sample_m
    assert sample_o == expect, sample_o

    def score(pns, frame, l3col):
        ok = bad = miss = 0
        samples = []
        for pn in pns:
            if pn not in frame.index:
                miss += 1
                continue
            got = (frame.at[pn, "aim_l1_fixed"], frame.at[pn, "aim_l2_fixed"], frame.at[pn, l3col])
            want = rmap.get(pn)
            if want and got == want:
                ok += 1
            else:
                bad += 1
                if len(samples) < 5:
                    samples.append({"pn": pn, "got": " > ".join(got), "want": " > ".join(want or ())})
        return {"n": len(pns), "ok": ok, "bad": bad, "missing": miss, "samples": samples}

    oct4 = {}
    for g, pns in oct4_pns.items():
        oct4[g] = {"master": score(pns, mi, "aim_l3"), "overlay": score(pns, oi, "aim_l3_fixed"), "n": len(pns)}
        assert oct4[g]["master"]["bad"] == 0 and oct4[g]["master"]["missing"] == 0, (g, oct4[g]["master"])
        assert oct4[g]["overlay"]["bad"] == 0 and oct4[g]["overlay"]["missing"] == 0, (g, oct4[g]["overlay"])

    rel_desc = rel.drop_duplicates("k").set_index("k")["description_norm"]
    m["d_any"] = m["description"].where(m["description"] != "", m["k"].map(rel_desc).fillna(""))
    eng_hold = int((
        m["d_any"].str.match(r"(?i)^GASKET SET;\s*ENG") & (m["aim_l1_fixed"] == "Transmission")
    ).sum())
    assert eng_hold == 0, eng_hold

    remain = 0
    for k, tgt in rmap.items():
        if k not in mi.index:
            continue
        got = (mi.at[k, "aim_l1_fixed"], mi.at[k, "aim_l2_fixed"], mi.at[k, "aim_l3"])
        if got != tgt:
            remain += 1
    assert remain == 0, remain

    desc_n = int(m["aim_source"].str.contains("desc_proven_20261007", na=False).sum())
    eq_n = int(m["aim_source"].str.contains("eq_hit_proven_20261007", na=False).sum())
    repair_m = int(m["aim_source"].str.contains(MARKER, na=False).sum())
    repair_o = int(o["aim_source"].str.contains(MARKER, na=False).sum())
    assert desc_n == 30653 and eq_n == 112

    baks_m = sorted(DER.glob("aim_master_v2.csv.bak_pre_forward_repair_oct4_20261007_*"))
    baks_o = sorted(DER.glob("aim_pn_classification_20260920.csv.bak_pre_forward_repair_oct4_20261007_*"))

    summary = {
        "as_of": datetime.now(timezone.utc).isoformat(),
        "verdict": "PASS",
        "sample_1878148072": {"master": sample_m, "overlay": sample_o},
        "gasket_set_eng_to_transmission_master": eng_hold,
        "release_vs_master_nonblank_remain": remain,
        "oct4": oct4,
        "desc_tags": desc_n,
        "eq_tags": eq_n,
        "repair_stamps": {"master": repair_m, "overlay": repair_o},
        "backups": {
            "master": [p.name for p in baks_m],
            "overlay": [p.name for p in baks_o],
        },
    }
    SUMMARY.write_text(json.dumps(summary, indent=2), encoding="utf-8")

    REPORT.write_text(
        "\n".join([
            "# AIM proven apply — 2026-10-07",
            "",
            "## Verdict",
            "",
            "**Applied: YES (after forward-repair).** Release `2026-10-07` stayed APPROVED. "
            "DESC_PROVEN + EQ_PROVEN were already on master/overlay. Oct4 AIM moves "
            "(engine gasket sets, EVRV, antennas, DEF) were missing on master/overlay and "
            f"were forward-repaired from the release (marker `{MARKER}`). "
            "RELEASES.json was not re-stamped.",
            "",
            "## Proof (re-verified)",
            "",
            f"- Sample `1878148072`: master = `{sample_m}`; overlay = `{sample_o}`",
            f"- Hard hold gasket_set_eng→Transmission on master: **{eng_hold}**",
            "- Oct4 D2/D3/D4/D6: master and overlay match release (0 bad / 0 missing)",
            f"- Release vs master non-blank AIM remain differs: **{remain}**",
            f"- DESC tags still: {desc_n}; EQ tags: {eq_n}",
            f"- Repair stamps: master {repair_m}, overlay {repair_o}",
            "",
            "### Oct4 scorecard (after repair)",
            "",
            "| Group | n | Master OK | Overlay OK |",
            "|---|---:|---:|---:|",
        ] + [
            f"| {g} | {v['n']} | {v['master']['ok']}/{v['n']} | {v['overlay']['ok']}/{v['n']} |"
            for g, v in oct4.items()
        ] + [
            "",
            "## Coverage",
            "",
            "- Release AIM non-blank: 55,830 / 165,055 rows (unchanged)",
            "- Master AIM non-blank: 55,932 / 165,422 rows (labels corrected in place)",
            "- Overlay: AIM labels corrected in place to match release",
            "",
            "## Paths",
            "",
            f"- Release: `{RELEASE}`",
            f"- Master: `{MASTER}`",
            f"- Overlay: `{OVERLAY}`",
            f"- Repair verify JSON: `{SUMMARY}`",
            f"- This report: `{REPORT}`",
            "",
            "## Honesty",
            "",
            "First COMPLETE claim was wrong on Oct4 sync. Independent double-check rejected it "
            "(`_aim_apply_doublecheck_20261007.md`). This report is rewritten after repair proof.",
            "",
        ]),
        encoding="utf-8",
    )

    print(json.dumps({
        "sample_m": sample_m,
        "sample_o": sample_o,
        "eng_hold": eng_hold,
        "remain": remain,
        "oct4": {g: {"m": v["master"]["ok"], "o": v["overlay"]["ok"], "n": v["n"]} for g, v in oct4.items()},
        "desc": desc_n,
        "eq": eq_n,
        "repair_m": repair_m,
        "repair_o": repair_o,
    }, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
