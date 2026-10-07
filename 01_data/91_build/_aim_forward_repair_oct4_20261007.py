#!/usr/bin/env python3
"""Forward-repair aim_master_v2 + overlay AIM from APPROVED release 2026-10-07.

Does NOT touch RELEASES.json. Does NOT rewrite the release CSV.
Copies release aim_l*_fixed onto master/overlay wherever release AIM is non-blank
and the consumer differs (covers Oct4 D2/D3/D4/D6 and any other drift).

DESC/EQ stamps are left alone; only AIM label columns (+ provenance marker) change.
"""
from __future__ import annotations

import csv
import hashlib
import io
import json
import shutil
import sys
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

ISZE = Path(r"C:\Users\jerom\Desktop\claude\ISZE")
DER = ISZE / "01_data" / "00_derived"
REL = DER / "_releases"
BUILD = ISZE / "01_data" / "91_build"
REGISTER = REL / "RELEASES.json"
RELEASE = REL / "aim_pn_classification_release_2026-10-07.csv"
MASTER = DER / "aim_master_v2.csv"
OVERLAY = DER / "aim_pn_classification_20260920.csv"
CHG04 = REL / "aim_pn_classification_release_2026-10-04.changes.csv"
MARKER = "forward_repair_oct4_20261007"
REPORT = BUILD / "_aim_apply_proven_20261007.md"
LOG = BUILD / "_aim_forward_repair_oct4_20261007.log.csv"
SUMMARY = BUILD / "_aim_forward_repair_oct4_20261007.json"

EXPECT_SHA = "aba81764e9aa3defaaa1636a9dfd13c520aadb4dfc2879e318f5c4e390010210"
OCT4_GROUPS = (
    "D2_engine_gasket_sets",
    "D3_evrv_valves",
    "D4_antennas",
    "D6_def_injectors",
)
AIM_REL = ("aim_l1_fixed", "aim_l2_fixed", "aim_l3_fixed")


def sha(p: Path) -> str:
    h = hashlib.sha256()
    with p.open("rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()


def pad(k: str) -> str:
    k = (k or "").strip()
    return k.zfill(10) if k.isdigit() else k


def add_source(cur: str, tag: str) -> str:
    cur = (cur or "").strip()
    if not cur:
        return tag
    return cur if tag in cur else f"{cur}|{tag}"


def aim_tuple_rel(row) -> tuple[str, str, str]:
    return (row["aim_l1_fixed"], row["aim_l2_fixed"], row["aim_l3_fixed"])


def main() -> int:
    reg = json.loads(REGISTER.read_text(encoding="utf-8"))
    entry = next(c for c in reg["candidates"] if c["release_id"] == "2026-10-07")
    if entry["status"] != "APPROVED":
        print("STOP: release 2026-10-07 is not APPROVED")
        return 2
    got = sha(RELEASE)
    if got != entry["sha256"] or got != EXPECT_SHA:
        print(f"STOP: release sha {got} vs register {entry['sha256']} vs expected {EXPECT_SHA}")
        return 2

    ts = datetime.now().strftime("%H%M%S")
    bak_m = DER / f"aim_master_v2.csv.bak_pre_forward_repair_oct4_20261007_{ts}"
    bak_o = DER / f"aim_pn_classification_20260920.csv.bak_pre_forward_repair_oct4_20261007_{ts}"
    for b in (bak_m, bak_o):
        if b.exists():
            print("STOP: backup exists", b.name)
            return 2

    rel = pd.read_csv(RELEASE, dtype=str, keep_default_na=False)
    rel["k"] = rel["part_number"].map(pad)
    # lubricant 9-digit + 10-digit key forms pad to the same key; AIM must agree
    dup = rel[rel["k"].duplicated(keep=False)]
    if len(dup):
        nu = dup.groupby("k")[list(AIM_REL)].nunique().max().max()
        assert nu <= 1, "release key forms disagree on AIM"
    rmap = {}
    for k, a1, a2, a3 in zip(
        rel["k"], rel["aim_l1_fixed"], rel["aim_l2_fixed"], rel["aim_l3_fixed"]
    ):
        if not a1:
            continue
        t = (a1, a2, a3)
        if k in rmap:
            assert rmap[k] == t
        else:
            rmap[k] = t

    chg = pd.read_csv(CHG04, dtype=str, keep_default_na=False)
    oct4_pns = {
        g: sorted({
            pad(r["part_number"])
            for _, r in chg.iterrows()
            if r["change_group"] == g and r["column"] in AIM_REL
        })
        for g in OCT4_GROUPS
    }

    # ---- master
    raw_m = MASTER.read_bytes()
    crlf_m = b"\r\n" in raw_m[:5000]
    shutil.copy2(MASTER, bak_m)
    assert bak_m.read_bytes() == raw_m
    m = pd.read_csv(MASTER, dtype=str, keep_default_na=False)
    m["k"] = m["part_number"].map(pad)
    if m["k"].duplicated().any():
        # keep first; AIM repair still applied to every matching row below by iterate
        print("WARN: master has duplicate padded keys", int(m["k"].duplicated().sum()))

    log_rows = []
    master_changed = 0
    for i, row in m.iterrows():
        k = row["k"]
        if k not in rmap:
            continue
        tgt = rmap[k]
        cur = (row["aim_l1_fixed"], row["aim_l2_fixed"], row.get("aim_l3", ""))
        if cur == tgt:
            continue
        # write AIM from release
        for col, before, after in (
            ("aim_l1_fixed", row["aim_l1_fixed"], tgt[0]),
            ("aim_l2_fixed", row["aim_l2_fixed"], tgt[1]),
            ("aim_l3", row.get("aim_l3", ""), tgt[2]),
        ):
            if before != after:
                log_rows.append({
                    "file": "aim_master_v2.csv",
                    "part_number": row["part_number"],
                    "column": col,
                    "before": before,
                    "after": after,
                })
        m.at[i, "aim_l1_fixed"] = tgt[0]
        m.at[i, "aim_l2_fixed"] = tgt[1]
        m.at[i, "aim_l3"] = tgt[2]
        if "aim_l1" in m.columns:
            m.at[i, "aim_l1"] = tgt[0]
        if "aim_l2" in m.columns:
            m.at[i, "aim_l2"] = tgt[1]
        if "has_aim" in m.columns:
            m.at[i, "has_aim"] = "1"
        m.at[i, "aim_source"] = add_source(row["aim_source"], MARKER)
        if "aim_changed" in m.columns:
            m.at[i, "aim_changed"] = add_source(row.get("aim_changed", ""), MARKER)
        master_changed += 1

    m = m.drop(columns=["k"])
    tmp_m = MASTER.with_suffix(".csv.tmp")
    tmp_m.write_bytes(
        m.to_csv(index=False, lineterminator="\r\n" if crlf_m else "\n").encode("utf-8")
    )
    tmp_m.replace(MASTER)

    # ---- overlay
    raw_o = OVERLAY.read_bytes()
    crlf_o = b"\r\n" in raw_o[:5000]
    shutil.copy2(OVERLAY, bak_o)
    assert bak_o.read_bytes() == raw_o
    o = pd.read_csv(OVERLAY, dtype=str, keep_default_na=False)
    o["k"] = o["part_number"].map(pad)
    # overlay can have duplicate lubricant key forms historically — use first for lookup
    opos: dict[str, list[int]] = {}
    for i, k in enumerate(o["k"]):
        opos.setdefault(k, []).append(i)

    overlay_changed = 0
    for k, tgt in rmap.items():
        idxs = opos.get(k)
        if not idxs:
            continue
        for i in idxs:
            cur = (
                o.at[i, "aim_l1_fixed"],
                o.at[i, "aim_l2_fixed"],
                o.at[i, "aim_l3_fixed"],
            )
            if cur == tgt:
                continue
            for col, before, after in (
                ("aim_l1_fixed", cur[0], tgt[0]),
                ("aim_l2_fixed", cur[1], tgt[1]),
                ("aim_l3_fixed", cur[2], tgt[2]),
            ):
                if before != after:
                    log_rows.append({
                        "file": "aim_pn_classification_20260920.csv",
                        "part_number": o.at[i, "part_number"],
                        "column": col,
                        "before": before,
                        "after": after,
                    })
            o.at[i, "aim_l1_fixed"] = tgt[0]
            o.at[i, "aim_l2_fixed"] = tgt[1]
            o.at[i, "aim_l3_fixed"] = tgt[2]
            o.at[i, "aim_source"] = add_source(o.at[i, "aim_source"], MARKER)
            overlay_changed += 1

    o = o.drop(columns=["k"])
    tmp_o = OVERLAY.with_suffix(".csv.tmp")
    tmp_o.write_bytes(
        o.to_csv(index=False, lineterminator="\r\n" if crlf_o else "\n").encode("utf-8")
    )
    tmp_o.replace(OVERLAY)

    with LOG.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(
            f,
            fieldnames=["file", "part_number", "column", "before", "after"],
            lineterminator="\r\n",
        )
        w.writeheader()
        w.writerows(log_rows)

    # ---- verify
    m2 = pd.read_csv(MASTER, dtype=str, keep_default_na=False)
    o2 = pd.read_csv(OVERLAY, dtype=str, keep_default_na=False)
    m2["k"] = m2["part_number"].map(pad)
    o2["k"] = o2["part_number"].map(pad)
    mi = m2.drop_duplicates("k").set_index("k")
    oi = o2.drop_duplicates("k").set_index("k")

    sample = "1878148072"
    sample_m = (
        f"{mi.at[sample, 'aim_l1_fixed']} > {mi.at[sample, 'aim_l2_fixed']} > {mi.at[sample, 'aim_l3']}"
    )
    sample_o = (
        f"{oi.at[sample, 'aim_l1_fixed']} > {oi.at[sample, 'aim_l2_fixed']} > {oi.at[sample, 'aim_l3_fixed']}"
    )
    expect = "Engine > Gasket & Sealing > Gasket"
    assert sample_m == expect, sample_m
    assert sample_o == expect, sample_o

    def score(group_pns, frame, l3col):
        ok = bad = miss = 0
        bad_samples = []
        for pn in group_pns:
            if pn not in frame.index:
                miss += 1
                continue
            got = (
                frame.at[pn, "aim_l1_fixed"],
                frame.at[pn, "aim_l2_fixed"],
                frame.at[pn, l3col],
            )
            want = rmap.get(pn)
            if want and got == want:
                ok += 1
            else:
                bad += 1
                if len(bad_samples) < 5:
                    bad_samples.append({"pn": pn, "got": " > ".join(got), "want": " > ".join(want or ())})
        return {"n": len(group_pns), "ok": ok, "bad": bad, "missing": miss, "samples": bad_samples}

    oct4_score = {
        g: {
            "master": score(pns, mi, "aim_l3"),
            "overlay": score(pns, oi, "aim_l3_fixed"),
            "release_n": len(pns),
        }
        for g, pns in oct4_pns.items()
    }
    for g, sc in oct4_score.items():
        assert sc["master"]["bad"] == 0 and sc["master"]["missing"] == 0, (g, sc["master"])
        assert sc["overlay"]["bad"] == 0 and sc["overlay"]["missing"] == 0, (g, sc["overlay"])

    # eng gasket set hard hold on master
    eng = m2[
        m2["description"].fillna("").str.match(r"(?i)^GASKET SET;\s*ENG")
        & (m2["aim_l1_fixed"] == "Transmission")
    ]
    # also use release description via join for blank master descriptions
    rel_desc = rel.drop_duplicates("k").set_index("k")["description_norm"]
    m2["d_any"] = m2["description"].where(
        m2["description"] != "", m2["k"].map(rel_desc).fillna("")
    )
    eng2 = m2[
        m2["d_any"].str.match(r"(?i)^GASKET SET;\s*ENG")
        & (m2["aim_l1_fixed"] == "Transmission")
    ]
    eng_hold = int(len(eng2))
    assert eng_hold == 0, ("gasket_set_eng_to_transmission still", eng_hold, eng2["part_number"].head(5).tolist())

    # remaining non-blank release vs master differs
    remain = 0
    for k, tgt in rmap.items():
        if k not in mi.index:
            continue
        got = (mi.at[k, "aim_l1_fixed"], mi.at[k, "aim_l2_fixed"], mi.at[k, "aim_l3"])
        if got != tgt:
            remain += 1
    assert remain == 0, remain

    # DESC/EQ stamps preserved
    desc_n = int(m2["aim_source"].str.contains("desc_proven_20261007", na=False).sum())
    eq_n = int(m2["aim_source"].str.contains("eq_hit_proven_20261007", na=False).sum())
    assert desc_n == 30653, desc_n
    assert eq_n == 112, eq_n

    summary = {
        "as_of": datetime.now(timezone.utc).isoformat(),
        "release_id": "2026-10-07",
        "release_sha256": got,
        "register_untouched": True,
        "marker": MARKER,
        "master_changed_pns": master_changed,
        "overlay_changed_pns": overlay_changed,
        "log_rows": len(log_rows),
        "sample_1878148072": {"master": sample_m, "overlay": sample_o, "expect": expect},
        "gasket_set_eng_to_transmission_master": eng_hold,
        "oct4": oct4_score,
        "desc_tags_still": desc_n,
        "eq_tags_still": eq_n,
        "backups": {"master": bak_m.name, "overlay": bak_o.name},
        "log": str(LOG),
    }
    SUMMARY.write_text(json.dumps(summary, indent=2), encoding="utf-8")

    # rewrite apply report honestly
    REPORT.write_text(
        "\n".join([
            "# AIM proven apply — 2026-10-07",
            "",
            "## Verdict",
            "",
            "**Applied: YES (after forward-repair).** Release `2026-10-07` was already APPROVED "
            "with DESC_PROVEN + EQ_PROVEN. An independent check found Oct4 AIM moves still "
            "missing on master/overlay. Those were forward-repaired from the release on "
            f"2026-10-07 (marker `{MARKER}`). RELEASES.json was not re-stamped.",
            "",
            "## Release (unchanged by repair)",
            "",
            "- Release id: `2026-10-07` APPROVED; base `2026-10-04` SUPERSEDED",
            f"- sha256: `{got}`",
            "- Rows: 165,055",
            "- DESC AIM fills + EQ appends intact on the release",
            "",
            "## Forward-repair (this pass)",
            "",
            f"- Master PNs AIM-aligned to release: **{master_changed}**",
            f"- Overlay PNs AIM-aligned to release: **{overlay_changed}**",
            f"- Sample `1878148072`: master + overlay = `{expect}`",
            f"- Hard hold gasket_set_eng→Transmission on master: **{eng_hold}**",
            "- Oct4 groups D2/D3/D4/D6: master and overlay match release (0 bad)",
            f"- DESC tags still on master: {desc_n}; EQ tags: {eq_n}",
            f"- Backups: `{bak_m.name}`, `{bak_o.name}`",
            f"- Change log: `{LOG}`",
            "",
            "## Coverage (AIM family non-blank)",
            "",
            "- Release: 25,155 → 55,830 (from the dated apply; not re-cut)",
            f"- Master: still 55,932 filled / 165,422 rows (labels corrected in place; "
            f"{master_changed} PNs overwritten from release)",
            f"- Overlay: labels corrected in place ({overlay_changed} PNs)",
            "",
            "## Zero-checks",
            "",
            f"- gasket_set_eng_to_transmission on master = **{eng_hold}** (must be 0)",
            "- Oct4 engine gasket / EVRV / antenna / DEF match release on master and overlay",
            "",
            "## EQ skipped (unchanged)",
            "",
            "4 camera PNs still skipped (no Camera leaf): 7552230171, 7552325041, "
            "8978451060, 8978451070.",
            "",
            "## Paths",
            "",
            f"- Release: `{RELEASE}`",
            f"- Master: `{MASTER}`",
            f"- Overlay: `{OVERLAY}`",
            f"- Repair summary: `{SUMMARY}`",
            f"- This report: `{REPORT}`",
            "",
            "## Honesty note",
            "",
            "The first COMPLETE claim was wrong on Oct4 sync. DESC/EQ counts were real; "
            "master/overlay still carried pre-Oct4 Transmission gasket (and related) labels "
            "until this forward-repair. Double-check: "
            "`_aim_apply_doublecheck_20261007.md`.",
            "",
        ]),
        encoding="utf-8",
    )

    print(json.dumps({
        "master_changed": master_changed,
        "overlay_changed": overlay_changed,
        "sample": sample_m,
        "eng_hold": eng_hold,
        "oct4": {g: {"m_ok": v["master"]["ok"], "o_ok": v["overlay"]["ok"], "n": v["release_n"]}
                 for g, v in oct4_score.items()},
        "desc": desc_n,
        "eq": eq_n,
    }, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
