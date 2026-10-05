#!/usr/bin/env python3
"""Register edit for Jerome's approval of 2 Oct 2026 ("all yes"), one write:

  2026-10-02-chassis-frame  PENDING_APPROVAL -> APPROVED (approved_by Jerome, 2026-10-02)
  2026-10-02                APPROVED -> SUPERSEDED (superseded_by 2026-10-02-chassis-frame)
  2026-10-02-candidate      PENDING_APPROVAL -> NOT_RELEASED (replaced, never approved; hash kept)

Fail closed: the new file's sha256 is re-measured and must equal the register entry and the
value measured by the candidate gate run; the candidate gate report must show every check ok
except release_approved PENDING. Register bytes written in the on-disk form (indent 2, CRLF);
fields not named above are left as they are.
"""
from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

REL = Path(r"C:\Users\jerom\Desktop\claude\ISZE\01_data\00_derived\_releases")
REGISTER = REL / "RELEASES.json"
NEW_ID, OLD_ID, CAND_ID = "2026-10-02-chassis-frame", "2026-10-02", "2026-10-02-candidate"
NEW_SHA = "9bb86a9b4d89c5954cd6dd15fdc977db44e66cddaa15e3e70bd0285e3bf3e65b"
GATE = REL / f"aim_pn_classification_release_{NEW_ID}.gate.json"


def sha(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def reg_text(reg: dict) -> bytes:
    return (json.dumps(reg, indent=2) + "\n").replace("\n", "\r\n").encode("utf-8")


def main() -> int:
    raw = REGISTER.read_bytes()
    reg = json.loads(raw.decode("utf-8"))
    assert reg_text(reg) == raw, "register does not round-trip"
    by = {c["release_id"]: c for c in reg["candidates"]}
    new, old, cand = by[NEW_ID], by[OLD_ID], by[CAND_ID]
    assert new["status"] == "PENDING_APPROVAL" and old["status"] == "APPROVED"
    assert cand["status"] == "PENDING_APPROVAL"
    got = sha(REL / new["path"])
    if not (got == new["sha256"] == NEW_SHA):
        print(f"STOP: sha256 {got} vs register {new['sha256']} vs gate {NEW_SHA}")
        return 1
    g = json.loads(GATE.read_text(encoding="utf-8"))
    assert g["mode"] == "candidate" and g["classifier_sha256"] == NEW_SHA
    bad = [c["id"] for c in g["checks"] if not c["ok"] and not c.get("pending")]
    pend = [c["id"] for c in g["checks"] if c.get("pending")]
    if bad or pend != ["release_approved"]:
        print(f"STOP: gate failures {bad}, pending {pend}")
        return 1
    n_ok = sum(1 for c in g["checks"] if c["ok"])

    new["status"] = "APPROVED"
    new["approved_by"] = "Jerome"
    new["approved_on"] = "2026-10-02"
    new["approved_note"] = (
        "Jerome approved in chat on 2026-10-02 ('all yes' on APPROVAL_SUMMARY_2026-10-02-candidate.md): "
        "cab mounting members to AIM Chassis Frame > Crossmember & Brackets > Bracket (catalogue "
        "Body structure); the 4 to-check parts as proposed, PCV kits 8981065790 / 8980023462 to be "
        "checked against the parts catalogue (EPC). sha256 re-verified against this register "
        f"immediately before the status change. Candidate gate ({GATE.name}): {n_ok} checks pass, "
        "release_approved PENDING, 0 fail. Supersedes 2026-10-02 in the same edit; replaces the "
        "unapproved 2026-10-02-candidate.")
    old["status"] = "SUPERSEDED"
    old["superseded_by"] = NEW_ID
    old["superseded_on"] = "2026-10-02"
    old["superseded_note"] = (f"Superseded when Jerome approved release {NEW_ID} on 2026-10-02. "
                              "Hash, history and the approval record kept unchanged.")
    cand["status"] = "NOT_RELEASED"
    cand["replaced_by"] = NEW_ID
    cand["replaced_note"] = (
        "Never approved. Jerome's 2026-10-02 decisions changed one thing (cab mounting members to "
        f"Chassis Frame), cut as {NEW_ID}; this entry's sha256 and file are kept unchanged because "
        "sha256 is the identity the gate matches on and release files are never overwritten.")

    REGISTER.write_bytes(reg_text(reg))
    chk = json.loads(REGISTER.read_bytes().decode("utf-8"))
    st = {c["release_id"]: c["status"] for c in chk["candidates"]}
    assert [k for k, v in st.items() if v == "APPROVED"] == [NEW_ID]
    print(json.dumps(st, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
