#!/usr/bin/env python3
"""Cut classification release 2026-10-02 (status PENDING_APPROVAL; Jerome approves, not this script).

What it is, per the 25 Sep retest recommendation (00_docs/AIM_RELEASE_RETEST_2026-09-25.md s7)
and Jerome's decisions of 2 Oct 2026:

  rows / keys       the approved 2026-09-20 release's 164,907 keys, plus the 9 lubricant keys
                    stored a second time in their 9-digit billing form (keys stored both ways)
  catalogue tree    the approved 2026-09-20 release's catalog_* columns, unchanged, except
                    8980913940 FILTER; ACL moved Air conditioning > Other A/C -> Filters > Air
                    filter (retest fix; its figure key 130-006 is labelled Air filter)
  AIM labels        the settled live AIM state as the live pages resolve it: the live overlay
                    aim_pn_classification_20260920.csv per level, the master aim_master_v2.csv
                    where the overlay level is blank (exactly the export's rule), then:
                      - decision 2: side sills 8980554611 / 8980554621 back to
                        Accident & Body > Panels > Panel (their 2026-09-20 release values)
                      - lubricants: the master's own fix (Fluids Chemicals > Lubricants) on
                        the lubricant keys that the overlay still files under Wheel Rim / Unknown
  kept (decision 1) Filters > Filter element, part 5864052180, zero billing: 177 leaves

Inputs are hash-checked against the values the 25 Sep retest and the 1 Oct wiring recorded, so
the release cannot silently be cut from a file that moved. Nothing is overwritten: the release,
its meta and a per-row change log are new files; the register entry is added by this script
with status PENDING_APPROVAL and the 2026-09-20 / 2026-09-24-candidate entries are left
byte-for-byte as they are (checked).

    python build_aim_classification_release_20261002.py            # build (refuses to overwrite)
"""
from __future__ import annotations

import csv
import hashlib
import io
import json
import os
import stat
import sys
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

ISZE = Path(r"C:\Users\jerom\Desktop\claude\ISZE")
DER = ISZE / "01_data" / "00_derived"
REL = DER / "_releases"
REGISTER = REL / "RELEASES.json"

RELEASE_ID = "2026-10-02"
OUT = REL / f"aim_pn_classification_release_{RELEASE_ID}.csv"
OUT_META = OUT.with_suffix(".meta.json")
OUT_LOG = REL / f"aim_pn_classification_release_{RELEASE_ID}.changes.csv"

APPROVED = REL / "aim_pn_classification_release_2026-09-20.csv"
OVERLAY = DER / "aim_pn_classification_20260920.csv"
MASTER = DER / "aim_master_v2.csv"
PR00 = DER / "pr00_classification.csv"

EXPECT_SHA = {
    APPROVED: "60111c104ddeb466e6c15f084039639d35172056b0fd2ea10225a3c50da610e0",
    OVERLAY: "092e981518efc5440ac10972ed2312dcd493c851e39d3d5c278f2ad5d0c27a60",
    MASTER: "8add555669baf1f75b3bb2d203d58960fff7596b26ec5d8645d7ffee45604acf",
}

CAT_COLS = ["catalog_l1", "catalog_l2", "catalog_l3", "catalog_node_present",
            "catalog_residual", "catalog_changed_vs_master", "line_kind", "fig_key",
            "filter_part_role"]
AIM_COLS = ["aim_l1_fixed", "aim_l2_fixed", "aim_l3_fixed"]
WB_COLS = ["workbook_l1", "workbook_l2", "workbook_l3", "workbook_axis_kind", "workbook_source"]

SIDE_SILLS = ["8980554611", "8980554621"]
AIR_FILTER_FIX = "8980913940"
FILTER_ELEMENT_LEAF_PN = "5864052180"
TAG = "20261002"


def sha(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()


def read(path: Path) -> pd.DataFrame:
    return pd.read_csv(path, dtype=str, keep_default_na=False, low_memory=False)


def add_source(cur: str, tag: str) -> str:
    return f"{cur}|{tag}" if cur else tag


def main() -> int:
    if OUT.exists():
        print(f"REFUSED: {OUT.name} already exists; a release file is never overwritten.")
        return 2
    for p, h in EXPECT_SHA.items():
        got = sha(p)
        if got != h:
            print(f"REFUSED: {p.name} sha256 {got[:12]} != expected {h[:12]} (input moved)")
            return 2
    reg_before = REGISTER.read_bytes()

    appr = read(APPROVED)
    ov = read(OVERLAY)
    ms = read(MASTER)
    cols = list(appr.columns)
    assert list(ov.columns) == cols
    assert (appr["part_number"].values == ov["part_number"].values).all(), "key order differs"
    # the catalogue tree is the approved release's: prove the overlay carries the same one,
    # then take it from the release explicitly.
    for c in CAT_COLS + ["description_norm"]:
        n = int((appr[c] != ov[c]).sum())
        assert n == 0, f"overlay differs from approved release on {c}: {n} rows"

    new = ov.copy()
    for c in CAT_COLS:
        new[c] = appr[c]
    log: list[dict] = []

    def note(pn, col, before, after, reason):
        log.append({"part_number": pn, "column": col, "before": before, "after": after,
                    "reason": reason})

    mi = ms.drop_duplicates("part_number").set_index("part_number")

    def m_level(pn: str, lv: int) -> str:
        if pn not in mi.index:
            return ""
        r = mi.loc[pn]
        if lv == 1:
            return (r["aim_l1_fixed"] or r["aim_l1"]).strip()
        if lv == 2:
            return (r["aim_l2_fixed"] or r["aim_l2"]).strip()
        return r["aim_l3"].strip()

    # (1) blank overlay AIM level -> master's level (the export's own per-level rule)
    idx = new.set_index("part_number").index
    for i, pn in enumerate(idx):
        filled = False
        for lv, c in ((1, "aim_l1_fixed"), (2, "aim_l2_fixed"), (3, "aim_l3_fixed")):
            if new.at[i, c].strip() == "":
                mv = m_level(pn, lv)
                if mv:
                    note(pn, c, "", mv, "overlay level blank: master value, the rule the live "
                         "page export already applies (no page change)")
                    new.at[i, c] = mv
                    filled = True
        if filled:
            new.at[i, "aim_source"] = add_source(new.at[i, "aim_source"], f"master_fill_{TAG}")

    pos = {pn: i for i, pn in enumerate(new["part_number"])}

    # (2) decision 2: side sills back to Panels > Panel (their approved-release values)
    for pn in SIDE_SILLS:
        i = pos[pn]
        for c in AIM_COLS + WB_COLS:
            if new.at[i, c] != appr.at[i, c]:
                note(pn, c, new.at[i, c], appr.at[i, c],
                     "Jerome decision 2026-10-02 #2: side sill is a body panel, not a cab assembly")
                new.at[i, c] = appr.at[i, c]
        new.at[i, "aim_source"] = add_source(appr.at[i, "aim_source"], f"side_sill_panel_{TAG}")
        note(pn, "aim_source", ov.at[i, "aim_source"], new.at[i, "aim_source"], "provenance tag")

    # (3) retest fix: 8980913940 FILTER; ACL catalogue tree -> Filters > Air filter
    i = pos[AIR_FILTER_FIX]
    air = appr[(appr["catalog_l3"] == "Air filter") & (appr["part_number"] != AIR_FILTER_FIX)]
    tgt = air[["catalog_l1", "catalog_l2", "catalog_l3"]].value_counts()
    assert len(tgt) == 1, f"Air filter leaf has more than one parent path: {tgt}"
    l1, l2, l3 = tgt.index[0]
    mrow = mi.loc[AIR_FILTER_FIX]
    for c, v in (("catalog_l1", l1), ("catalog_l2", l2), ("catalog_l3", l3)):
        note(AIR_FILTER_FIX, c, new.at[i, c], v,
             "retest 2026-09-25 fix: air filter (figure key 130-006 = Air filter) filed under "
             "Air conditioning")
        new.at[i, c] = v
    # catalog_changed_vs_master compares with the master's cat_* copy, which already reads
    # Competitive parts > Filters > Air filter for this part
    chg = "0" if (mrow["cat_l1"], mrow["cat_l2"], mrow["cat_l3"]) == (l1, l2, l3) else "1"
    note(AIR_FILTER_FIX, "catalog_changed_vs_master", new.at[i, "catalog_changed_vs_master"],
         chg, "recomputed: catalogue now equals the master's cat_* copy")
    new.at[i, "catalog_changed_vs_master"] = chg

    # (4) lubricants: master's fix on the 10-digit keys; then store the 9-digit billing key too
    lub = new[new["line_kind"] == "lubricant_or_tool"]
    lub = lub[lub["part_number"].str.match(r"^05500\d{5}$")]
    lub_pns = list(lub["part_number"])
    for pn in lub_pns:
        i = pos[pn]
        mv = [m_level(pn, lv) for lv in (1, 2, 3)]
        cur = [new.at[i, c] for c in AIM_COLS]
        if all(mv) and mv != cur:
            for c, a, b in zip(AIM_COLS, cur, mv):
                if a != b:
                    note(pn, c, a, b, "lubricant filed under a non-lubricant family in the "
                         "overlay; the master's own fix (retest s4 fault 1) applied")
            for c, b in zip(AIM_COLS, mv):
                new.at[i, c] = b
            new.at[i, "aim_source"] = add_source(new.at[i, "aim_source"], f"lubricant_fix_{TAG}")
        # billing sits on the 9-digit key; the master holds the 10-digit row at its own value
        if pn in mi.index:
            mv_eur = mi.loc[pn, "l12m_billed_eur"]
            if new.at[i, "l12m_billed_eur"] != mv_eur:
                note(pn, "l12m_billed_eur", new.at[i, "l12m_billed_eur"], mv_eur,
                     "billing belongs to the 9-digit billed key; 10-digit row set to the "
                     "master's value so the two key forms do not double-count")
                new.at[i, "l12m_billed_eur"] = mv_eur
    nine_rows = []
    for pn in lub_pns:
        k9 = pn.lstrip("0")
        assert k9 not in pos, f"{k9} already present"
        row = new.loc[pos[pn]].copy()
        row["part_number"] = k9
        row["l12m_billed_eur"] = mi.loc[k9, "l12m_billed_eur"] if k9 in mi.index else "0.0"
        row["aim_source"] = add_source(row["aim_source"], f"lubricant_key9_{TAG}")
        nine_rows.append(row)
        note(k9, "(row)", "", f"copy of {pn}",
             "lubricant stored in its 9-digit billing key form as well (retest s2 key-form defect)")
    # place each 9-digit row right after its 10-digit twin
    parts = []
    last = 0
    for pn, row in sorted(zip(lub_pns, nine_rows), key=lambda t: pos[t[0]]):
        parts.append(new.iloc[last:pos[pn] + 1])
        parts.append(pd.DataFrame([row], columns=cols))
        last = pos[pn] + 1
    parts.append(new.iloc[last:])
    new = pd.concat(parts, ignore_index=True)[cols]

    # ---- invariants
    assert new["part_number"].duplicated().sum() == 0
    assert FILTER_ELEMENT_LEAF_PN in set(new["part_number"])
    fe = new[new["part_number"] == FILTER_ELEMENT_LEAF_PN].iloc[0]
    assert fe["catalog_l3"] == "Filter element", "decision 1: Filter element leaf must stay"
    l3n = new.loc[new["catalog_l3"] != "", "catalog_l3"].nunique()
    l2n = new.loc[new["catalog_l2"] != "", "catalog_l2"].nunique()
    assert (l2n, l3n) == (27, 177), (l2n, l3n)

    # ---- write (CRLF, utf-8, same writer that round-trips the overlay byte-for-byte)
    text = new.to_csv(index=False, lineterminator="\r\n")
    OUT.write_bytes(text.encode("utf-8"))
    out_sha = sha(OUT)
    with OUT_LOG.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=["part_number", "column", "before", "after", "reason"])
        w.writeheader()
        w.writerows(log)

    # ---- copy-integrity vs pr00 (same method as build_aim_classification_v2.py: padded key,
    # (family, group, level3_type) == (catalog_l1, catalog_l2, catalog_l3))
    def pad(k: str) -> str:
        k = (k or "").strip()
        return k.zfill(10) if k.isdigit() else k

    def integrity(pr00_text: str) -> dict:
        pm = {}
        for r in csv.DictReader(io.StringIO(pr00_text)):
            k = pad(r.get("pn_norm") or "")
            if k:
                pm[k] = ((r.get("family") or "").strip(), (r.get("group") or "").strip(),
                         (r.get("level3_type") or "").strip())
        chk = ok = 0
        for pn, a, b, c in zip(new["part_number"], new["catalog_l1"], new["catalog_l2"],
                               new["catalog_l3"]):
            k = pad(pn)
            if k in pm:
                chk += 1
                ok += pm[k] == (a.strip(), b.strip(), c.strip())
        return {"rows_checked": chk, "rows_matching": ok,
                "match_pct": round(100 * ok / chk, 4) if chk else None}

    live_int = integrity(PR00.read_text(encoding="utf-8"))
    import subprocess
    try:
        pr00_0920 = subprocess.run(
            ["git", "-C", str(ISZE), "show", "c813330f:01_data/00_derived/pr00_classification.csv"],
            capture_output=True, check=True).stdout.decode("utf-8")
        commit_int = integrity(pr00_0920)
    except Exception as e:  # noqa: BLE001
        commit_int = {"error": str(e)}

    n = len(new)
    meta = {
        "generated": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "built_by": "01_data/91_build/build_aim_classification_release_20261002.py",
        "release_id": RELEASE_ID,
        "status_at_build": "PENDING_APPROVAL (Jerome approves; this script never sets APPROVED)",
        "purpose": (
            "Two-axes lock 2026-09-17: Axis A = catalog_l1/l2/l3 identity (the catalogue tree "
            "of the approved 2026-09-20 release); Axis B = commercial score beside Axis A, not "
            "built as scored columns here and never the parent of the identity tree. "
            "aim_l*_fixed is the governed AIM family label. legacy workbook_l* is context only. "
            "Do not invent a fourth layer."),
        "rows": n,
        "sha256": out_sha,
        "sources": {
            "catalogue_tree": {"file": str(APPROVED), "sha256": EXPECT_SHA[APPROVED]},
            "aim_labels_overlay": {"file": str(OVERLAY), "sha256": EXPECT_SHA[OVERLAY],
                                   "modified": "2026-09-24 19:21:14 +0200"},
            "aim_labels_master_fallback": {"file": str(MASTER), "sha256": EXPECT_SHA[MASTER],
                                           "modified": "2026-09-24 19:17:03 +0200"},
        },
        "which_aim_state_is_current": (
            "Neither file alone. Both were last written 24 Sep 2026 and are byte-identical to "
            "what the 25 Sep retest hashed. The live AIM pages read the figure-key export, "
            "which takes the overlay per level and the master where the overlay level is "
            "blank; this release stores exactly that resolved state, then applies the changes "
            "listed below."),
        "changes_vs_live_state": {
            "decision_1_keep_filter_element_leaf": FILTER_ELEMENT_LEAF_PN,
            "decision_2_side_sills_to_panel": SIDE_SILLS,
            "air_filter_catalogue_fix": AIR_FILTER_FIX,
            "lubricant_aim_fix_from_master": [p for p in lub_pns],
            "lubricant_9_digit_keys_added": [p.lstrip("0") for p in lub_pns],
            "change_log": OUT_LOG.name,
            "change_log_rows": len(log),
        },
        "catalogue_verification_vs_pr00": {
            **live_int,
            "pr00_file": str(PR00),
            "pr00_sha256": sha(PR00),
            "note": ("COPY-INTEGRITY ONLY, measured on THIS file by this build: catalogue "
                     "columns vs today's pr00_classification.csv on the zero-padded key "
                     "(method of build_aim_classification_v2.py). The 9 lubricant 9-digit keys "
                     "pad to their 10-digit twins and are counted. Does not prove correctness "
                     "vs customs, figures or part text."),
            "vs_pr00_committed_20260920": {**commit_int, "git": "c813330f"},
        },
        "counts": {
            "catalog_l2_count": int(l2n), "catalog_l3_count": int(l3n),
            "line_kind": {k: int(v) for k, v in new["line_kind"].value_counts().items()},
        },
        "consumer_contract": [
            "Axis A (identity): group by catalog_l1/l2/l3; filter catalog_node_present=1.",
            "aim_l1_fixed/aim_l2_fixed/aim_l3_fixed = the governed AIM family (what the AIM "
            "pages chart).",
            "line_kind != 'part' marks freight / rebate / service / lubricant rows; filter "
            "line_kind=='part' for parts revenue.",
            "Lubricants are stored under BOTH key forms (0550xxxxxx and 550xxxxxx); the billing "
            "sits on the 9-digit row, the 10-digit row carries the master's 0.0. Do not sum both "
            "without knowing that.",
        ],
    }
    OUT_META.write_text(json.dumps(meta, indent=2), encoding="utf-8")

    # ---- register: append a PENDING_APPROVAL entry; existing entries untouched
    reg = json.loads(reg_before.decode("utf-8"))
    before_entries = json.dumps(reg["candidates"], sort_keys=True)
    assert all(c["release_id"] != RELEASE_ID for c in reg["candidates"])
    reg["candidates"].append({
        "release_id": RELEASE_ID,
        "path": OUT.name,
        "sha256": out_sha,
        "status": "PENDING_APPROVAL",
        "rows": n,
        "rows_note": "data rows, header excluded (the two earlier entries record 164908 = "
                     "164,907 data rows + header)",
        "source": (f"catalogue tree: {APPROVED.name}; AIM labels: {OVERLAY.name} per level, "
                   f"{MASTER.name} where blank (the live page export's rule)"),
        "recommendation": "00_docs/AIM_RELEASE_RETEST_2026-09-25.md s7 item 4; Jerome decisions "
                          "2026-10-02 (keep Filter element leaf; side sills to Panels > Panel; "
                          "cut a new release)",
        "notes": (
            "Cut 2026-10-02 by claude-opus. Adds the 24 Sep AIM work, the side-sill decision, "
            "the 8980913940 air-filter catalogue fix and both lubricant key forms; change log "
            f"{OUT_LOG.name}. Supersedes the 2026-09-24-candidate as the thing to approve. "
            "Bookkeeping: that candidate's recorded sha256 e5824683... is the hash of "
            "aim_pn_classification_20260920.csv.bak_pre_cab_class_20260924_192113, not of its "
            "recorded path (now 092e9815...); its entry was left unchanged because sha256 is "
            "the identity field the gate matches on."),
    })
    assert json.dumps(reg["candidates"][:-1], sort_keys=True) == before_entries
    REGISTER.write_text(json.dumps(reg, indent=2) + "\n", encoding="utf-8")

    os.chmod(OUT, stat.S_IREAD | stat.S_IRGRP | stat.S_IROTH)  # read-only like the 09-20 file

    print(f"wrote {OUT}  rows={n}  sha256={out_sha}")
    print(f"wrote {OUT_META.name}  copy-integrity vs live pr00 = {live_int}  "
          f"vs pr00@c813330f = {commit_int}")
    print(f"wrote {OUT_LOG.name}  {len(log)} change rows")
    print(f"register: + {RELEASE_ID} PENDING_APPROVAL; earlier entries unchanged")
    return 0


if __name__ == "__main__":
    sys.exit(main())
