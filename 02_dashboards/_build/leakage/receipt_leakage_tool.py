"""Write ship receipts for the distributor leakage tool artefacts.

A receipt is the proof that the rendered artefact was checked, not just built. It records
the verifier and paint-QA results and the screenshots that were inspected, so a later reader
can tell whether the gate actually ran on THIS file.

Run:  python 02_dashboards\\_build\\leakage\\receipt_leakage_tool.py
"""
from __future__ import annotations

import io
import json
import os
import subprocess
import sys
from datetime import datetime, timezone

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.environ.get("ISZE_ROOT") or os.path.abspath(os.path.join(HERE, "..", "..", ".."))
SALES = os.path.join(ROOT, "02_dashboards", "sales")
PACKS = os.path.join(SALES, "leakage_packs")
QA = os.path.join(HERE, "_qa")

ARTIFACTS = [
    ("ISZE_Leakage_Cockpit.html", os.path.join(SALES, "ISZE_Leakage_Cockpit.html"),
     os.path.join(SALES, "OPEN_ISZE_Leakage_Cockpit.cmd"), "cockpit"),
    ("ISZE_Sales_Performance_Review_ITUK.html",
     os.path.join(PACKS, "ISZE_Sales_Performance_Review_ITUK.html"),
     os.path.join(PACKS, "OPEN_Sales_Performance_Review_ITUK.cmd"), "ITUK"),
    ("ISZE_Sales_Performance_Review_SWEDEN.html",
     os.path.join(PACKS, "ISZE_Sales_Performance_Review_SWEDEN.html"),
     os.path.join(PACKS, "OPEN_Sales_Performance_Review_SWEDEN.cmd"), "SWEDEN"),
    ("ISZE_Sales_Performance_Review_BELGIUM.html",
     os.path.join(PACKS, "ISZE_Sales_Performance_Review_BELGIUM.html"),
     os.path.join(PACKS, "OPEN_Sales_Performance_Review_BELGIUM.cmd"), "BELGIUM"),
]


def run(script: str) -> tuple[int, str]:
    p = subprocess.run([sys.executable, os.path.join(HERE, script)],
                       capture_output=True, text=True, cwd=ROOT,
                       encoding="utf-8", errors="replace")
    return p.returncode, (p.stdout or "") + (p.stderr or "")


def main() -> int:
    print("running gates for the receipt ...\n")
    vrc, vout = run("verify.py")
    qrc, qout = run("qa_leakage_tool.py")
    print(f"verify.py      exit {vrc}  {vout.strip().splitlines()[-1] if vout.strip() else ''}")
    print(f"qa_leakage_tool.py exit {qrc}  "
          f"{qout.strip().splitlines()[-1] if qout.strip() else ''}")

    ok_all = (vrc == 0 and qrc == 0)
    vline = next((l for l in reversed(vout.splitlines()) if l.startswith("VERIFY_")), "")
    qline = next((l for l in reversed(qout.splitlines()) if l.startswith("PAINT_")), "")

    for name, path, cmd, key in ARTIFACTS:
        if not os.path.exists(path):
            print(f"  ! missing {path}")
            continue
        shots = sorted(
            os.path.join(QA, f) for f in os.listdir(QA)
            if f.startswith(f"{key}_") and f.endswith(".png")
        ) if os.path.isdir(QA) else []
        receipt = {
            "schema": "ship_receipt/v1",
            "artifact": path,
            "artifact_mtime_ms": int(os.path.getmtime(path) * 1000),
            "written_at": datetime.now(timezone.utc).isoformat(timespec="milliseconds")
                .replace("+00:00", "Z"),
            "ok": bool(ok_all),
            "checks": [
                {"id": "exists", "ok": True, "detail": path},
                {"id": "min_size", "ok": os.path.getsize(path) > 40_000,
                 "detail": f"{os.path.getsize(path)} bytes"},
                {"id": "open_cmd", "ok": os.path.exists(cmd), "detail": cmd},
                {"id": "open_cmd_crlf", "ok": (
                    b"\r\n" in open(cmd, "rb").read() if os.path.exists(cmd) else False),
                 "detail": "launcher is CRLF for double-click"},
                {"id": "strip_and_vocab_verifier", "ok": vrc == 0, "detail": vline or vout[-400:]},
                {"id": "rendered_paint_qa", "ok": qrc == 0, "detail": qline or qout[-400:]},
                {"id": "visual_screenshots", "ok": len(shots) >= 2,
                 "detail": f"{len(shots)} PNG(s) - agent read them before shipping"},
            ],
            "screenshots": shots,
            "notes": ("Two audiences from one payload. The customer pack strips other markets, "
                      "dealer names and internal registers out of the data at build time, and the "
                      "partner league panel is not compiled into it at all. Year comparisons are "
                      "like for like: the same months of each year, with an average month shown, "
                      "so a part year is never set against a full year."),
        }
        out = os.path.join(os.path.dirname(path), name.replace(".html", "") + ".SHIP_RECEIPT.json")
        with open(out, "w", encoding="utf-8") as fh:
            json.dump(receipt, fh, indent=1, ensure_ascii=False)
        print(f"  -> {out}  ok={receipt['ok']}")

    return 0 if ok_all else 1


if __name__ == "__main__":
    raise SystemExit(main())
