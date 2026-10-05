#!/usr/bin/env python3
"""Cut classification release 2026-10-02-candidate (status PENDING_APPROVAL; Jerome approves).

Jerome's go of 2 Oct 2026: the next release after the approved 2026-10-02 release.

Release id: 2026-10-02 is taken (APPROVED). The register's only way of giving a second
release the same date is a hyphen suffix on the date (2026-09-24-candidate). This script uses
the same form, 2026-10-02-candidate. No version label (b, v2, ...) is introduced.

What changes, starting from the approved release 2026-10-02 (sha256 0ac91379...):

  A  pr00 21 Sep review (next_release_proposal_2026-10-02.csv), 42 parts, catalogue axis
     (catalog_l1/l2/l3): 40 proposed values + 2 keep-21-Sep values. AIM labels unchanged.
     4 low-confidence parts marked "to check" in the change log (2x PLATE; SKID,RAD and
     2x ELEMENT KIT; PCV).
  B  body parts the release does not file under body (UTI back-order findings, 2 Oct):
     roof panel 7552077720, upper cowl panel 7475447681, front inner lid 7552895450 and the
     cab mounting members (MEMBER; CAB MTG). AIM axis -> Accident & Body > Panels > Panel
     (no body-structure leaf exists on the AIM axis; no new AIM leaf invented). Catalogue
     axis -> Accident parts > Body parts (Panel; the cab members already sit on Body
     structure). Siblings with the same description on the same figure key are filed the
     same way. Parts that are not in the release at all get a row only if they are one of
     the named parts or are billed in the last 12 months.
  C  "wrong in both files" items from REVIEW.md (last section) with a clear verdict only:
     5878305371 (REPAIR KIT on king-pin key 410-004) and 9443730060 (SPRING SEAT on
     drag-link key 410-076). Catalogue axis only.

Not changed: PMS rules (the king-pin rule is reported, not edited), pr00, the approved
release, earlier register entries, live pages.

    python build_aim_classification_release_20261002_candidate.py   # refuses to overwrite
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

RELEASE_ID = "2026-10-02-candidate"
BASE_ID = "2026-10-02"
OUT = REL / f"aim_pn_classification_release_{RELEASE_ID}.csv"
OUT_META = OUT.with_suffix(".meta.json")
OUT_LOG = REL / f"aim_pn_classification_release_{RELEASE_ID}.changes.csv"

BASE = REL / f"aim_pn_classification_release_{BASE_ID}.csv"
PROPOSAL = REL / "next_release_proposal_2026-10-02.csv"
PR00_REF = REL / "pr00_classification_reference_20260920.csv"
PR00_LIVE = DER / "pr00_classification.csv"
MASTER = DER / "aim_master_v2.csv"
JP = DER / "jp_codes_cache_20260920.csv"
SALES = DER / "sales_fact.parquet"

EXPECT_SHA = {
    BASE: "0ac9137903a326430c68e4d619fa4f836a796a01d9d40f6f6f1183e7d4c52360",
    PROPOSAL: "e3dbc746fe14241cbc4c8e0d608916fba593ea50fd05f7034e61b1309627b1b6",
    PR00_REF: "98e64b5bdaef73819cf954ce96241f1a9b49d8fbd998d02700ae8494028bea34",
    MASTER: "8add555669baf1f75b3bb2d203d58960fff7596b26ec5d8645d7ffee45604acf",
}
TAG = "20261002c"
TO_CHECK = {"8983941570", "8983941544", "8981065790", "8980023462"}
AIM_BODY = ("Accident & Body", "Panels", "Panel")
CAT_PANEL = ("Accident parts", "Body parts", "Panel")
L12M_FROM, L12M_TO = "2025-09-01", "2026-08-31"   # same window as the 21 Sep review

# B: body filing. (figure key, jp description) groups; every release row on the key whose
# description (release or JP code file) equals the type, or is blank, is filed.
BODY_GROUPS = [
    {"name": "roof panel", "named": "7552077720", "fig_key": "660-001", "desc": "PANEL; ROOF"},
    {"name": "upper cowl panel", "named": "7475447681", "fig_key": "605-030",
     "desc": "PANEL; COWL UPR"},
    {"name": "cab mounting member", "named": "7552008820 / 8982268360 / 8980107565",
     "fig_key": "510-173", "desc": "MEMBER; CAB MTG"},
    {"name": "front inner lid", "named": "7552895450", "fig_key": "605-632",
     "desc": "LID; FRT INNER"},
]
# C: clear verdicts from REVIEW.md "Seen in passing" (catalogue only)
WRONG_BOTH = {
    "5878305371": (("Competitive parts", "Steering", "Knuckle / arm"),
                   "REVIEW.md last section: REPAIR KIT on king-pin key 410-004 filed under Air "
                   "system > Other air system in both files; the other 128 rows on 410-004 are "
                   "all Steering > Knuckle / arm (king-pin kits)"),
    "9443730060": (("Competitive parts", "Steering", "Other steering"),
                   "REVIEW.md last section: SPRING SEAT on drag-link key 410-076 filed under "
                   "Body parts > Interior trim in both files; its two siblings on 410-076 are "
                   "SEAT; SPR,DRAG LINK on Steering > Other steering"),
}


def sha(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()


def read(path: Path) -> pd.DataFrame:
    return pd.read_csv(path, dtype=str, keep_default_na=False, low_memory=False)


def pad(k: str) -> str:
    k = (k or "").strip()
    return k.zfill(10) if k.isdigit() else k


def reg_text(reg: dict) -> bytes:
    """RELEASES.json as it sits on disk: indent 2, CRLF, trailing newline."""
    return (json.dumps(reg, indent=2) + "\n").replace("\n", "\r\n").encode("utf-8")


def add_source(cur: str, tag: str) -> str:
    return f"{cur}|{tag}" if cur else tag


def main() -> int:
    for p in (OUT, OUT_META, OUT_LOG):
        if p.exists():
            print(f"REFUSED: {p.name} already exists; a release file is never overwritten.")
            return 2
    for p, h in EXPECT_SHA.items():
        got = sha(p)
        if got != h:
            print(f"REFUSED: {p.name} sha256 {got[:12]} != expected {h[:12]} (input moved)")
            return 2
    reg_before = REGISTER.read_bytes()
    reg = json.loads(reg_before.decode("utf-8"))
    # the writer below re-serialises the register; prove it reproduces today's bytes first,
    # so the existing entries stay byte-for-byte as they are
    # (the register is CRLF on disk)
    assert reg_text(reg) == reg_before, \
        "register re-serialisation does not round-trip"
    assert all(c["release_id"] != RELEASE_ID for c in reg["candidates"])
    base_entry = next(c for c in reg["candidates"] if c["release_id"] == BASE_ID)
    assert base_entry["status"] == "APPROVED" and base_entry["sha256"] == EXPECT_SHA[BASE]

    base_bytes = BASE.read_bytes()
    base = pd.read_csv(io.BytesIO(base_bytes), dtype=str, keep_default_na=False, low_memory=False)
    cols = list(base.columns)
    # byte-exact proof: the writer used below reproduces the approved file unchanged
    assert base.to_csv(index=False, lineterminator="\r\n").encode("utf-8") == base_bytes, \
        "writer does not round-trip the approved release byte-for-byte"
    new = base.copy()
    pos = {pn: i for i, pn in enumerate(new["part_number"])}

    # ---- L12M parts billed per part (information for the change log, not a release column)
    sf = pd.read_parquet(SALES, columns=["billing_date", "part_number", "net_sales_value"])
    sf = sf[(sf.billing_date >= L12M_FROM) & (sf.billing_date <= L12M_TO)]
    sf["pn"] = sf["part_number"].astype(str).map(pad)
    l12 = sf.groupby("pn")["net_sales_value"].sum()

    sfa = pd.read_parquet(SALES, columns=["billing_date", "part_number", "net_sales_value"])
    sfa["pn"] = sfa["part_number"].astype(str).map(pad)
    first_bill = sfa.groupby("pn")["billing_date"].min().dt.strftime("%Y-%m-%d")
    w = sfa[(sfa.billing_date >= "2025-01-01") & (sfa.billing_date <= "2026-06-30")]
    l12_col = w.groupby("pn")["net_sales_value"].sum()
    del sfa, w

    def eur(pn: str) -> float:
        return round(float(l12.get(pad(pn), 0.0)), 2)

    ms = read(MASTER).drop_duplicates("part_number").set_index("part_number")
    jp = read(JP)
    jp["pn"] = jp["pn"].map(pad)
    jpi = jp.drop_duplicates("pn").set_index("pn")

    log: list[dict] = []

    def note(pn, col, before, after, group, reason, to_check=""):
        log.append({"part_number": pn, "column": col, "before": before, "after": after,
                    "change_group": group, "to_check": to_check,
                    "l12m_eur_sep25_aug26": eur(pn), "reason": reason})

    def set_catalog(pn: str, tgt: tuple, group: str, reason: str, to_check: str = "") -> None:
        i = pos[pn]
        for c, v in zip(("catalog_l1", "catalog_l2", "catalog_l3"), tgt):
            if new.at[i, c] != v:
                note(pn, c, new.at[i, c], v, group, reason, to_check)
                new.at[i, c] = v
        # derived columns, same rules the release carries on every row
        resid = "1" if tgt[2] == "Review needed" else "0"
        node = "0" if tgt[2] == "Review needed" else "1"
        for c, v in (("catalog_residual", resid), ("catalog_node_present", node)):
            if new.at[i, c] != v:
                note(pn, c, new.at[i, c], v, group, "derived: Review needed <-> named leaf", to_check)
                new.at[i, c] = v
        if pn in ms.index:
            m = ms.loc[pn]
            chg = "0" if (m["cat_l1"], m["cat_l2"], m["cat_l3"]) == tgt else "1"
            if new.at[i, "catalog_changed_vs_master"] != chg:
                note(pn, "catalog_changed_vs_master", new.at[i, "catalog_changed_vs_master"], chg,
                     group, "recomputed: catalogue vs the master's cat_* copy", to_check)
                new.at[i, "catalog_changed_vs_master"] = chg

    def set_aim(pn: str, tgt: tuple, group: str, reason: str) -> None:
        i = pos[pn]
        changed = False
        for c, v in zip(("aim_l1_fixed", "aim_l2_fixed", "aim_l3_fixed"), tgt):
            if new.at[i, c] != v:
                note(pn, c, new.at[i, c], v, group, reason)
                new.at[i, c] = v
                changed = True
        if changed:
            old = new.at[i, "aim_source"]
            new.at[i, "aim_source"] = add_source(old, f"body_filing_{TAG}")
            note(pn, "aim_source", old, new.at[i, "aim_source"], group, "provenance tag")

    # ---- A: the 42-part proposal (catalogue axis)
    prop = read(PROPOSAL)
    assert len(prop) == 42 and prop["part_number"].is_unique
    for _, p in prop.iterrows():
        pn = p["part_number"]
        i = pos[pn]
        cur = (new.at[i, "catalog_l1"], new.at[i, "catalog_l2"], new.at[i, "catalog_l3"])
        assert cur == (p["release_family"], p["release_group"], p["release_level3_type"]), (pn, cur)
        tgt = (p["proposed_family"], p["proposed_group"], p["proposed_level3_type"])
        tc = "to check" if pn in TO_CHECK else ""
        why = ("pr00 21 Sep review: keep the 21 Sep value" if p["verdict"] == "keep_21sep"
               else "pr00 21 Sep review: neither side right, third value proposed")
        set_catalog(pn, tgt, "A_review_proposal",
                    f"{why} ({p['description'] or 'no description'}; confidence {p['confidence']})", tc)
    assert set(prop.loc[prop["note"] == "to check", "part_number"]) == TO_CHECK

    # ---- B: body filing
    new["_jp_desc"] = new["part_number"].map(lambda k: jpi["jp_description"].get(pad(k), ""))
    body_rows: list[dict] = []
    for g in BODY_GROUPS:
        on_key = new[(new["fig_key"] == g["fig_key"])]
        desc_any = on_key["description_norm"].where(on_key["description_norm"] != "",
                                                     on_key["_jp_desc"])
        keep = on_key[(desc_any == "") | desc_any.str.startswith(g["desc"])]
        other = on_key[~on_key.index.isin(keep.index)]
        assert other.empty or g["fig_key"] == "605-632", (g["name"], other["part_number"].tolist())
        # same description off this key (release rows), e.g. a row with no figure key
        off_key = new[(new["fig_key"] != g["fig_key"]) & (
            (new["description_norm"] == g["desc"]) | (new["_jp_desc"] == g["desc"]))]
        for i in list(keep.index) + list(off_key.index):
            pn = new.at[i, "part_number"]
            who = "named part" if pn in g["named"] else (
                "same figure key" if i in keep.index else "same description, no figure key")
            reason = (f"body part not filed under body ({g['name']}, UTI back-order findings "
                      f"2 Oct; {who}, figure key {g['fig_key']})")
            cat_before = (new.at[i, "catalog_l1"], new.at[i, "catalog_l2"], new.at[i, "catalog_l3"])
            aim_before = tuple(new.at[i, c] for c in ("aim_l1_fixed", "aim_l2_fixed", "aim_l3_fixed"))
            if cat_before[:2] != ("Accident parts", "Body parts"):
                set_catalog(pn, CAT_PANEL, "B_body_filing", reason)
            set_aim(pn, AIM_BODY, "B_body_filing", reason)
            body_rows.append({"group": g["name"], "part_number": pn,
                              "description": new.at[i, "description_norm"] or new.at[i, "_jp_desc"],
                              "fig_key": new.at[i, "fig_key"], "how": who,
                              "catalog_before": " > ".join(cat_before),
                              "catalog_after": " > ".join(new.loc[i, ["catalog_l1", "catalog_l2", "catalog_l3"]]),
                              "aim_before": " > ".join(aim_before),
                              "aim_after": " > ".join(AIM_BODY), "row_added": False,
                              "l12m_eur": eur(pn)})

    # parts of these types that are not in the release: add a row only when named or billed
    added: list[pd.Series] = []
    not_added: dict[str, dict] = {}
    for g in BODY_GROUPS:
        cand = set(jp.loc[jp["jp_description"] == g["desc"], "pn"]) - set(pos)
        named = {k.strip() for k in g["named"].split("/")}
        cand |= {k for k in named if k not in pos}
        skipped = []
        for pn in sorted(cand):
            if pn not in named and eur(pn) == 0.0:
                skipped.append(pn)
                continue
            j = jpi.loc[pn] if pn in jpi.index else None
            fk = j["jp_fig_key"] if j is not None else ""
            fk = f"{fk[:3]}-{fk[3:]}" if len(fk) == 6 else ""
            d = {c: "" for c in cols}
            d.update({
                "part_number": pn,
                "description_norm": g["desc"],
                "catalog_l1": CAT_PANEL[0], "catalog_l2": CAT_PANEL[1], "catalog_l3": CAT_PANEL[2],
                "catalog_node_present": "1", "catalog_residual": "0",
                "workbook_axis_kind": "blank",
                "aim_source": f"body_filing_{TAG}",
                "aim_l1_fixed": AIM_BODY[0], "aim_l2_fixed": AIM_BODY[1], "aim_l3_fixed": AIM_BODY[2],
                "jp_zkk": j["zkk"] if j is not None else "",
                "jp_zuk": j["zuk"] if j is not None else "",
                "jp_hkk": j["hkk"] if j is not None else "",
                "jp_class_new": j["class_new"] if j is not None else "",
                "l12m_billed_eur": str(round(float(l12_col.get(pn, 0.0)), 2)),
                "axis_conflict": "0", "desc_ambiguous": "0", "catalog_changed_vs_master": "0",
                "line_kind": "part", "fig_key": fk,
            })
            row = pd.Series(d)
            added.append(row)
            src = "JP code file + price file" if j is not None else "UTI back-order lists + sales_fact description (no JP code / figure key on file)"
            note(pn, "(row)", "", "added", "B_body_filing",
                 f"{g['name']} not in the release; added because "
                 f"{'named in the brief' if pn in named else 'billed in the last 12 months'}; "
                 f"description and codes from {src}; l12m_billed_eur 0.0 = the column's own "
                 "window (Jan 2025-Jun 2026, master convention), first billed Jul 2026")
            body_rows.append({"group": g["name"], "part_number": pn, "description": g["desc"],
                              "fig_key": fk, "how": "row added (named)" if pn in named else "row added (billed L12M)",
                              "catalog_before": "(not in release)",
                              "catalog_after": " > ".join(CAT_PANEL),
                              "aim_before": "(not in release)", "aim_after": " > ".join(AIM_BODY),
                              "row_added": True, "l12m_eur": eur(pn)})
        not_added[g["name"]] = {"parts_of_this_type_not_in_release_not_added": len(skipped),
                                "billed_l12m_among_them_eur": round(sum(eur(p) for p in skipped), 2)}

    # ---- C: wrong in both files, clear verdicts (catalogue only)
    for pn, (tgt, why) in WRONG_BOTH.items():
        set_catalog(pn, tgt, "C_wrong_in_both", why)

    new = new.drop(columns=["_jp_desc"])
    # insert added rows in key order (the release is sorted by part_number apart from the
    # lubricant 9-digit twins, which sit at the top)
    for row in sorted(added, key=lambda r: r["part_number"]):
        k = row["part_number"]
        after = new.index[(new["part_number"].str.len() == 10) & (new["part_number"] < k)].max()
        new = pd.concat([new.iloc[:after + 1], pd.DataFrame([row], columns=cols),
                         new.iloc[after + 1:]], ignore_index=True)
    new = new[cols]

    # ---- invariants
    assert new["part_number"].duplicated().sum() == 0
    assert len(new) == len(base) + len(added)
    l3n = new.loc[new["catalog_l3"] != "", "catalog_l3"].nunique()
    l2n = new.loc[new["catalog_l2"] != "", "catalog_l2"].nunique()
    assert (l2n, l3n) == (27, 177), (l2n, l3n)
    assert new.loc[new["part_number"] == "5864052180", "catalog_l3"].iloc[0] == "Filter element"
    # rows not touched by this script are byte-identical to the base
    touched = {r["part_number"] for r in log}
    b = base.set_index("part_number")
    n_ = new.set_index("part_number")
    untouched = [k for k in b.index if k not in touched]
    assert (b.loc[untouched] == n_.loc[untouched]).all().all()

    # ---- write (CRLF, utf-8: the writer proven above to round-trip the approved file)
    OUT.write_bytes(new.to_csv(index=False, lineterminator="\r\n").encode("utf-8"))
    out_sha = sha(OUT)
    with OUT_LOG.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=["part_number", "column", "before", "after", "change_group",
                                          "to_check", "l12m_eur_sep25_aug26", "reason"],
                           lineterminator="\r\n")
        w.writeheader()
        w.writerows(log)
    body_csv = REL / f"aim_pn_classification_release_{RELEASE_ID}.body_filing.csv"
    b_changed = {r["part_number"] for r in log if r["change_group"] == "B_body_filing"}
    for r in body_rows:
        r["changed"] = r["part_number"] in b_changed  # False = already on body on both axes
    pd.DataFrame(body_rows).to_csv(body_csv, index=False, lineterminator="\r\n")

    # ---- copy integrity vs the PINNED 20 Sep pr00 reference (gate method)
    def integrity(text: str) -> dict:
        pm = {}
        for r in csv.DictReader(io.StringIO(text)):
            k = pad(r.get("pn_norm") or "")
            if k:
                pm[k] = ((r.get("family") or "").strip(), (r.get("group") or "").strip(),
                         (r.get("level3_type") or "").strip())
        chk = ok = 0
        miss = []
        for pn, a, b_, c in zip(new["part_number"], new["catalog_l1"], new["catalog_l2"],
                                new["catalog_l3"]):
            k = pad(pn)
            if k in pm:
                chk += 1
                if pm[k] == (a.strip(), b_.strip(), c.strip()):
                    ok += 1
                else:
                    miss.append(pn)
        return {"rows_checked": chk, "rows_matching": ok,
                "match_pct": round(100 * ok / chk, 4) if chk else None}, miss

    ref_int, ref_miss = integrity(PR00_REF.read_text(encoding="utf-8"))
    live_int, live_miss = integrity(PR00_LIVE.read_text(encoding="utf-8"))
    ref_meta = json.loads(PR00_REF.with_suffix(".meta.json").read_text(encoding="utf-8"))

    base_meta = json.loads((BASE.with_suffix(".meta.json")).read_text(encoding="utf-8"))
    n = len(new)
    meta = {
        "generated": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "built_by": "01_data/91_build/build_aim_classification_release_20261002_candidate.py",
        "release_id": RELEASE_ID,
        "release_id_note": ("2026-10-02 is taken (APPROVED). The register's only precedent for a "
                            "second release on one date is a hyphen suffix on the date "
                            "(2026-09-24-candidate); the same form is used. No version label."),
        "status_at_build": "PENDING_APPROVAL (Jerome approves; this script never sets APPROVED)",
        "purpose": base_meta["purpose"],
        "rows": n,
        "sha256": out_sha,
        "base_release": {"release_id": BASE_ID, "file": BASE.name, "sha256": EXPECT_SHA[BASE],
                         "rows": len(base)},
        "sources": {
            "proposal": {"file": PROPOSAL.name, "sha256": EXPECT_SHA[PROPOSAL]},
            "review": "01_data/91_build/pr00_21sep_review_2026-10-02/REVIEW.md",
            "body_findings": ("02_dashboards/pricing/_build/price_5pct_proposal_2026-09-29/"
                              "uti_panels_2026-10-02/FINDINGS.md (back-order trend section)"),
            "jp_codes": {"file": JP.name, "sha256": sha(JP)},
            "master": {"file": MASTER.name, "sha256": EXPECT_SHA[MASTER]},
            "l12m_eur_in_change_log": (f"sales_fact.parquet net_sales_value {L12M_FROM}..{L12M_TO}, "
                                       "all sold-to, 10-digit padded key (the review's window)"),
        },
        "changes_vs_base": {
            "A_review_proposal_parts": int(len(prop)),
            "A_to_check": sorted(TO_CHECK),
            "B_body_filing_parts": len(body_rows),
            "B_rows_added": [r["part_number"] for r in added],
            "B_types_not_added": not_added,
            "C_wrong_in_both_parts": sorted(WRONG_BOTH),
            "change_log": OUT_LOG.name,
            "change_log_rows": len(log),
            "body_filing_list": body_csv.name,
            "parts_touched": len(touched),
        },
        "catalogue_verification_vs_pr00": {
            **ref_int,
            "reference_file": PR00_REF.name,
            "reference_sha256": EXPECT_SHA[PR00_REF],
            "reference_source": base_meta["catalogue_verification_vs_pr00"]["reference_source"],
            "reference_reason": base_meta["catalogue_verification_vs_pr00"]["reference_reason"],
            "non_matching_parts": len(ref_miss),
            "note": ("COPY-INTEGRITY ONLY, measured on THIS file: catalogue columns vs the pinned "
                     "20 Sep pr00 reference on the zero-padded key (method of "
                     "build_aim_classification_v2.py). Every non-matching row is a deliberate "
                     "change listed in the change log (or the 8980913940 air-filter fix carried "
                     "from 2026-10-02). Does not prove correctness vs customs, figures or part text."),
            "vs_pr00_today_information_only": {
                **live_int, "pr00_file": str(PR00_LIVE), "pr00_sha256": sha(PR00_LIVE),
                "non_matching_parts": live_miss,
                "note": ("today's pr00 = the 2 Oct correction; it already carries the 42 proposal "
                         "values, so the remaining differences are this release's B/C catalogue "
                         "changes (pr00 not edited by this script)")},
        },
        "counts": {
            "catalog_l2_count": int(l2n), "catalog_l3_count": int(l3n),
            "line_kind": {k: int(v) for k, v in new["line_kind"].value_counts().items()},
        },
        "consumer_contract": base_meta["consumer_contract"],
    }
    assert all(p in set(log_pn["part_number"] for log_pn in log) or p == "8980913940"
               for p in ref_miss), "a reference mismatch that is not a logged change"
    OUT_META.write_text(json.dumps(meta, indent=2), encoding="utf-8")

    # ---- register: append a PENDING_APPROVAL entry; existing entries untouched
    before_entries = json.dumps(reg["candidates"], sort_keys=True)
    reg["candidates"].append({
        "release_id": RELEASE_ID,
        "path": OUT.name,
        "sha256": out_sha,
        "status": "PENDING_APPROVAL",
        "rows": n,
        "rows_note": "data rows, header excluded (same as 2026-10-02)",
        "source": (f"release {BASE_ID} ({BASE.name}, sha256 {EXPECT_SHA[BASE][:8]}...) + "
                   f"{PROPOSAL.name} (42 parts) + body filing + 2 wrong-in-both fixes"),
        "recommendation": ("01_data/91_build/pr00_21sep_review_2026-10-02/REVIEW.md; UTI back-order "
                           "findings 2 Oct (body parts not filed under body); Jerome go 2026-10-02"),
        "notes": (f"Cut 2026-10-02 by claude-opus as the candidate after {BASE_ID}. Change log "
                  f"{OUT_LOG.name}; body list {body_csv.name}. Release id: 2026-10-02 taken; "
                  "hyphen suffix on the date per the 2026-09-24-candidate precedent, no version label."),
    })
    assert json.dumps(reg["candidates"][:-1], sort_keys=True) == before_entries
    REGISTER.write_bytes(reg_text(reg))
    after = json.loads(REGISTER.read_bytes().decode("utf-8"))
    assert json.dumps(after["candidates"][:-1], sort_keys=True) == before_entries

    os.chmod(OUT, stat.S_IREAD | stat.S_IRGRP | stat.S_IROTH)

    print(f"wrote {OUT}  rows={n}  sha256={out_sha}")
    print(f"copy integrity vs pinned 20 Sep pr00 = {ref_int}  non-matching {len(ref_miss)}")
    print(f"vs today's pr00 = {live_int}  non-matching {live_miss}")
    print(f"wrote {OUT_LOG.name}  {len(log)} change rows, {len(touched)} parts")
    print(f"wrote {body_csv.name}  {len(body_rows)} rows; added rows {[r['part_number'] for r in added]}")
    print(f"not added: {not_added}")
    print(f"register: + {RELEASE_ID} PENDING_APPROVAL; earlier entries unchanged")
    return 0


if __name__ == "__main__":
    sys.exit(main())
