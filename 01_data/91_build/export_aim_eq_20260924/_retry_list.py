"""List the parts that still need a lookup (error, or never reached the EPC)."""
from __future__ import annotations

import json
from pathlib import Path

D = Path(r"C:\Users\jerom\Desktop\claude\ISZE\01_data\91_build\export_aim_eq_20260924")


def main() -> None:
    queue = json.loads((D / "queue.json").read_text(encoding="utf-8"))
    queue = [str(p).strip().upper() for p in queue]

    got: dict[str, str] = {}
    for line in (D / "eq_results.jsonl").read_text(encoding="utf-8").splitlines():
        if line.strip():
            r = json.loads(line)
            got[str(r["pn"]).upper()] = r.get("eq_status", "")

    retry = [
        p for p in queue
        if got.get(p, "") in ("", "ERROR")
    ]
    # A FOUND with a blank figure name is worth one more attempt.
    blank = [
        p for p in queue
        if got.get(p) == "FOUND"
        and not next(
            (json.loads(l).get("eq_fig_name") for l in
             (D / "eq_results.jsonl").read_text(encoding="utf-8").splitlines()
             if l.strip() and json.loads(l)["pn"] == p),
            "",
        )
    ]
    out = sorted(set(retry) | set(blank))
    (D / "retry.json").write_text(json.dumps(out, indent=0), encoding="utf-8")
    print(f"never looked up or errored: {len(retry)}")
    print(f"found but no figure name:   {len(blank)}")
    print(f"retry queue:                {len(out)}")


if __name__ == "__main__":
    main()
