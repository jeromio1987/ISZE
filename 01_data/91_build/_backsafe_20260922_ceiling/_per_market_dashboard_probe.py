"""Where does each affected per-market operating dashboard carry its ceiling?

Looks for the market's old and new ceiling values anywhere in the ledger and the HTML,
and reports the JSON path so the field can be located without re-running a 140 KB builder
that has no verified contract.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

ROOT = Path(r"C:\Users\jerom\Desktop\claude\ISZE")
MEET = ROOT / "09_meetings"

SIX = {
    "PORTUGAL": (3052087.0, 2430115.0),
    "IRELAND": (956313.0, 856195.0),
    "GERMANY": (3808128.0, 3740349.0),
    "BELGIUM": (2453507.0, 2410536.0),
    "MALTA": (378827.0, 338957.0),
    "CYPRUS": (676267.0, 671394.0),
}


def walk(o, path, hits, olds, news):
    if isinstance(o, dict):
        for k, v in o.items():
            walk(v, f"{path}.{k}", hits, olds, news)
    elif isinstance(o, list):
        for i, v in enumerate(o):
            walk(v, f"{path}[{i}]", hits, olds, news)
    elif isinstance(o, (int, float)) and not isinstance(o, bool):
        f = float(o)
        for code, (old, new) in list(olds.items()):
            if abs(f - old) < 0.01 and abs(old - new) > 0.01:
                hits.append((code, "OLD/no-split", path, f))
            elif abs(f - new) < 0.01 and abs(old - new) > 0.01:
                hits.append((code, "NEW/corrected", path, f))


def main() -> int:
    for code, (old, new) in SIX.items():
        d = MEET / f"{code}_Operating_Dashboard_2026"
        print(f"\n===== {code}   old {old:,.0f} -> new {new:,.0f}")
        led = d / "NUMBERS_LEDGER.json"
        if led.is_file():
            L = json.loads(led.read_text(encoding="utf-8"))
            hits: list = []
            walk(L, "", hits, {code: (old, new)}, {})
            if hits:
                for c, tag, p, v in hits[:12]:
                    print(f"   ledger {tag:16s} {p} = {v:,.2f}")
            else:
                print("   ledger: neither the old nor the new value found")
        for h in sorted(d.glob("*.html")):
            t = h.read_text(encoding="utf-8", errors="ignore")
            o, n = f"{old:,.0f}", f"{new:,.0f}"
            print(f"   {h.name:44s} old-count={t.count(o)} new-count={t.count(n)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
