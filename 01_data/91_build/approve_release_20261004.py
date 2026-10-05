#!/usr/bin/env python3
"""Register edit for Jerome's approval of 4 Oct 2026 ("approve" on APPROVAL_SUMMARY_2026-10-04.md), one write:

  2026-10-04                PENDING_APPROVAL -> APPROVED (approved_by Jerome, 2026-10-04)
  2026-10-02-chassis-frame  APPROVED -> SUPERSEDED (superseded_by 2026-10-04)

Fail closed: the new file's sha256 is re-measured and must equal the register entry and the
value measured by the candidate gate run; the candidate gate report must show every check ok
except release_approved PENDING. Register bytes written in the on-disk form (indent 2, CRLF);
fields not named above are left as they are. Approval is of the release file only: no page,
export or deploy copy is changed by this script.
"""
from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

REL = Path(r"C:\Users\jerom\Desktop\claude\ISZE\01_data\00_derived\_releases")
REGISTER = REL / "RELEASES.json"
NEW_ID, OLD_ID = "2026-10-04", "2026-10-02-chassis-frame"
NEW_SHA = "8aad884f49db1a49ab86faca571942d912196ce08f7734f38d5a04f035e18896"
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
    new, old = by[NEW_ID], by[OLD_ID]
    assert new["status"] == "PENDING_APPROVAL" and old["status"] == "APPROVED"
    assert [k for k, v in by.items() if v["status"] == "APPROVED"] == [OLD_ID]
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
    new["approved_on"] = "2026-10-04"
    new["approved_note"] = (
        "Jerome approved in chat on 2026-10-04 (answer 'approve' to APPROVAL_SUMMARY_2026-10-04.md): "
        "24 high-confidence billed parts added; engine gasket sets to Engine > Gasket & Sealing > Gasket; "
        "EVRV valves to EGR Component; antennas to Audio > Radio; rear cameras on the catalogue tree only; "
        "DEF injectors to the new AIM label Intake Exhaust Emission > DEF System > DEF Injector. "
        "Includes the parts whose description is only in the Japanese parts-code file (111 parts, EUR 60). "
        "sha256 re-verified against this register immediately before the status change. "
        f"Candidate gate ({GATE.name}): {n_ok} checks pass, release_approved PENDING, 0 fail. "
        "Supersedes 2026-10-02-chassis-frame in the same edit. Approval covers the release file only; "
        "AIM pages, the page-input export and deploy copies were not changed by it.")
    old["status"] = "SUPERSEDED"
    old["superseded_by"] = NEW_ID
    old["superseded_on"] = "2026-10-04"
    old["superseded_note"] = (f"Superseded when Jerome approved release {NEW_ID} on 2026-10-04. "
                              "Hash, history and the approval record kept unchanged.")

    REGISTER.write_bytes(reg_text(reg))
    chk = json.loads(REGISTER.read_bytes().decode("utf-8"))
    st = {c["release_id"]: c["status"] for c in chk["candidates"]}
    assert [k for k, v in st.items() if v == "APPROVED"] == [NEW_ID]
    print(json.dumps(st, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())