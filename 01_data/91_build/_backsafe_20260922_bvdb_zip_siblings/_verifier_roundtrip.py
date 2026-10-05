#!/usr/bin/env python3
"""Snapshot / diff the verifier's outputs around a check run.

  python _verifier_roundtrip.py before    -> copy the 3 outputs into .\\verifier_before\\
  python _verifier_roundtrip.py compare   -> run the verifier, then diff statuses

The verifier is run with `python scripts/verify_derived_pipeline.py` from
03_analytics/Isuzu/prism, exactly as the brief asks. The full pipeline is NOT run.
"""
from __future__ import annotations

import json
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(r"C:\Users\jerom\Desktop\claude\ISZE")
PRISM = ROOT / "03_analytics" / "Isuzu" / "prism"
DER = ROOT / "01_data" / "00_derived"
HERE = Path(__file__).resolve().parent

OUTPUTS = ["_verification_report.json", "_verification_report.md", "metrics_snapshot.json"]
BEFORE_DIR = HERE / "verifier_before"
AFTER_DIR = HERE / "verifier_after"


def snapshot(dest: Path) -> None:
    dest.mkdir(parents=True, exist_ok=True)
    for n in OUTPUTS:
        src = DER / n
        if src.is_file():
            shutil.copy2(src, dest / n)


def statuses(path: Path) -> dict[str, str]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    checks = payload.get("checks") or []
    return {(c.get("id") or c.get("name")): str(c.get("status")) for c in checks}


def summarise(path: Path) -> str:
    p = json.loads(path.read_text(encoding="utf-8"))
    s = p.get("summary") or {}
    return (f"pass={s.get('pass')} warn={s.get('warn')} fail={s.get('fail')} "
            f"ok={s.get('ok')} generated_at={p.get('generated_at')}")


def main() -> int:
    mode = sys.argv[1] if len(sys.argv) > 1 else "compare"
    if mode == "before":
        snapshot(BEFORE_DIR)
        print("snapshotted to", BEFORE_DIR)
        print(summarise(DER / "_verification_report.json"))
        return 0

    snapshot(AFTER_DIR)
    r = subprocess.run([sys.executable, "scripts/verify_derived_pipeline.py"],
                       cwd=str(PRISM), capture_output=True, text=True, encoding="utf-8")
    print("--- stdout tail")
    print("\n".join(r.stdout.splitlines()[-25:]))
    if r.stderr.strip():
        print("--- stderr")
        print(r.stderr[-4000:])
    print("exit code:", r.returncode)
    snapshot(AFTER_DIR)

    before_p = BEFORE_DIR / "_verification_report.json"
    after_p = AFTER_DIR / "_verification_report.json"
    print("\n--- SUMMARY")
    if before_p.exists():
        print("before:", summarise(before_p))
    print("after :", summarise(after_p))

    if before_p.exists():
        b, a = statuses(before_p), statuses(after_p)
        changed = {k: (b.get(k), a[k]) for k in a if b.get(k) != a[k]}
        added = [k for k in a if k not in b]
        removed = [k for k in b if k not in a]
        print(f"\nchecks before={len(b)} after={len(a)}")
        print("added  :", added or "none")
        print("removed:", removed or "none")
        print("STATUS CHANGED:")
        for k, v in changed.items():
            print(f"   {k}: {v[0]} -> {v[1]}")
        if not changed:
            print("   none")
    print("\n--- every non-pass check after")
    p = json.loads(after_p.read_text(encoding="utf-8"))
    for c in p.get("checks") or []:
        if str(c.get("status")).lower() != "pass":
            print(f"   [{c.get('status')}] {c.get('id')}: {c.get('message')}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
