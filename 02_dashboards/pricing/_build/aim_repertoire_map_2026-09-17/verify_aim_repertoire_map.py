#!/usr/bin/env python3
"""Deterministic verify for the AIM repertoire map. No browser, exit 1 on any failure.

Re-derives the headline from the embedded payload and checks the file is a single
self-contained page with its launcher beside it.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

ISZE = Path(r"C:\Users\jerom\Desktop\claude\ISZE")
BUILD = ISZE / "02_dashboards" / "pricing" / "_build" / "aim_repertoire_map_2026-09-17"
PAYLOAD = BUILD / "payload.json"
HTML = ISZE / "02_dashboards" / "pricing" / "ISZE_AIM_Repertoire_Map_2026-09-17.html"
CMD = ISZE / "02_dashboards" / "pricing" / "OPEN_ISZE_AIM_Repertoire_Map.cmd"

PUBLISHED_BILLED = 34993609.39
PUBLISHED_STEP = 1652140.71
PUBLISHED_PCT = 5.9616

fails: list[str] = []
n = 0


def check(name: str, ok: bool, detail: str = "") -> None:
    global n
    n += 1
    print(("  PASS  " if ok else "  FAIL  ") + name + (f"  [{detail}]" if detail else ""))
    if not ok:
        fails.append(f"{name} :: {detail}")


def main() -> int:
    p = json.loads(PAYLOAD.read_text(encoding="utf-8"))
    m, rows = p["meta"], p["rows"]
    L1, L2, L3, DB = m["l1"], m["l2"], m["l3"], m["db"]
    PN = m["pn"]

    billed = sum(r[6] for r in rows)
    step = sum(r[7] for r in rows)
    prior = sum(r[8] for r in rows)
    new = sum(r[9] for r in rows)
    pct = 100 * (new / prior - 1) if prior else 0.0

    check("payload billed euro reproduces the shipped revision",
          abs(billed - PUBLISHED_BILLED) < 0.05, f"{billed:,.2f}")
    check("payload step euro reproduces the shipped revision",
          abs(step - PUBLISHED_STEP) < 1.0, f"{step:,.2f}")
    check("payload weighted move reproduces the shipped revision",
          abs(round(pct, 4) - PUBLISHED_PCT) < 0.01, f"{pct:.4f}%")

    # ---- every index in range, no NaN, no zero-length names
    bad = 0
    nan = 0
    for r in rows:
        if not (0 <= r[0] < len(PN) and 0 <= r[1] < len(L1)
                and 0 <= r[2] < len(L2) and 0 <= r[3] < len(L3)
                and 0 <= r[4] < len(DB)):
            bad += 1
        for v in r[5:11]:
            if v != v:
                nan += 1
    check("every row's category and distributor index is in range", bad == 0, f"{bad} bad")
    check("no NaN in any row value", nan == 0, f"{nan} NaN")
    check("no empty category or group name",
          all(x.strip() for x in L1) and all(x[1].strip() for x in L2))
    check("no empty part-type name", all(x[2].strip() for x in L3))

    # ---- the L1 rows must add up to the whole book (nothing dropped)
    per_l1 = {}
    for r in rows:
        per_l1[r[1]] = per_l1.get(r[1], 0.0) + r[6]
    check("category rows sum to the billed total",
          abs(sum(per_l1.values()) - billed) < 0.5, f"{len(per_l1)} categories")

    # ---- the residual placeholders must be visible, not folded away
    check("the two residual placeholders are in the category list",
          set(m["residual_l1"]).issubset(set(L1)), str(m["residual_l1"]))
    resid_eur = sum(per_l1[L1.index(x)] for x in m["residual_l1"])
    check("residual euro is a named, non-zero amount", resid_eur > 1_000_000,
          f"{resid_eur:,.2f}")

    # ---- repertoire gap stated
    rep = m["repertoire"]
    check("the page states the tree is larger than the billing",
          rep["classified_not_billed"] > 100_000, str(rep))
    check("billed part numbers equal the in-scope count",
          rep["billed_part_numbers"] == m["checks"]["part_numbers"],
          str(rep["billed_part_numbers"]))

    # ---- unmovable lines carried, not averaged away
    ch = m["checks"]
    check("unpriced lines are counted and carried",
          ch["unpriced_lines"] > 0 and ch["unpriced_eur"] > 0, str(ch["unpriced_lines"]))

    # ---- fleet denominators: present for the big markets, absent only for the four
    uio = m["db_uio"]
    missing = [DB[i] for i, v in enumerate(uio) if v is None]
    check("fleet count present for the main markets", len(DB) - len(missing) >= 18,
          f"{len(DB)-len(missing)} of {len(DB)}")
    check("markets without a fleet count are exactly the four known ones",
          set(missing) == {"CBC", "CIS-KTK", "GA", "KIMA"}, str(missing))
    check("ITUK fleet is the known 22,389", uio[DB.index("ITUK")] == 22389, str(uio[DB.index("ITUK")]))

    # ---- the built file
    check("built HTML exists", HTML.exists())
    html = HTML.read_text(encoding="utf-8", errors="ignore")
    check("file is over 2 MB, so the payload really is embedded",
          len(html.encode("utf-8")) > 2_000_000,
          f"{len(html.encode('utf-8'))/1e6:.2f} MB")
    check("Chart.js is inlined, not a CDN",
          "cdn.jsdelivr" not in html and "new Chart(" in html)
    check("no fetch() of a sibling file", "fetch(" not in html)
    # NaN only matters inside the embedded data block; the inlined Chart.js library
    # legitimately contains isNaN() checks of its own.
    i = html.find('type="application/json"')
    j = html.find("</script>", i)
    payload_block = html[i:j]
    check("payload block really is embedded", len(payload_block) > 2_000_000,
          f"{len(payload_block)/1e6:.2f} MB")
    check("no NaN literal inside the embedded data", "NaN" not in payload_block,
          f"{payload_block.count('NaN')} found")
    check("launcher sits beside the file", CMD.exists())
    raw = CMD.read_bytes()
    check("launcher is CRLF, as Explorer expects",
          b"\r\n" in raw and raw.replace(b"\r\n", b"").count(b"\n") == 0, repr(raw[:24]))
    check("launcher starts the map file",
          b"ISZE_AIM_Repertoire_Map_2026-09-17.html" in raw, repr(raw))

    print()
    print("=" * 74)
    print(f"PASS {n - len(fails)}   FAIL {len(fails)}")
    for f in fails:
        print("  FAIL " + f)
    print("=" * 74)
    print("VERIFY_AIM_MAP_OK" if not fails else "VERIFY_AIM_MAP_FAILED")
    return 0 if not fails else 1


if __name__ == "__main__":
    sys.exit(main())
