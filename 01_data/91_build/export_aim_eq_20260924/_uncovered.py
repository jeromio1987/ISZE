"""Report the EPC figure names that no AIM rule covers yet."""
from __future__ import annotations

import json
import re
import sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from classify import aim_from_fig_name  # noqa: E402

D = Path(r"C:\Users\jerom\Desktop\claude\ISZE\01_data\91_build\export_aim_eq_20260924")


def main() -> None:
    names, hit, miss = Counter(), Counter(), Counter()
    for line in (D / "eq_results.jsonl").read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        r = json.loads(line)
        n = (r.get("eq_fig_name") or "").strip()
        if not n:
            continue
        key = re.sub(r"^\s*[\dA-Z]+\s*-\s*[\dA-Z]*\s*-\s*", "", n.upper()).strip()
        names[key] += 1
        (hit if aim_from_fig_name(n) else miss)[key] += 1
    print(f"distinct figure names: {len(names)} | covered: {len(hit)} | not covered: {len(miss)}")
    print("\n--- NOT COVERED (count, name) ---")
    for k, v in miss.most_common():
        print(f"{v:4d}  {k}")


if __name__ == "__main__":
    main()
