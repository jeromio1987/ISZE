"""Exact semantics of the proposed carry-forward guard, before it is written.

The guard, in the legacy re-base block only:

    rungs = the settled rungs (as now)
    pending = pending-ruling codes named in the raw evidence text, by whole-word scan
    if pending and the pre-change file carries this part number:
        rungs = that pre-change row's three-rung list      <- carried forward, not recomputed
    else:
        rungs = the settled rungs

Rationale: a pending code's band is interim, so recomputing it is the thing that silently dropped
the rung. Carrying the pre-change value forward cannot invent a band and cannot move a row that was
already right.

This measures how many rows that touches, and whether they are the twelve and nothing else.
Nothing is written.
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(r"C:\Users\jerom\Desktop\claude\ISZE")
DER = ROOT / "01_data" / "00_derived"
PRISM = ROOT / "03_analytics" / "Isuzu" / "prism"
BASELINE = ROOT / "01_data" / "91_build" / "_legacy_baseline_tonnage_capable.csv"
BAK = ROOT / "02_dashboards" / "sales" / "_backsafe_rebase_20260923"
sys.path.insert(0, str(PRISM))
from modules.vehicle_bands import pending_ruling_codes  # noqa: E402

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:  # noqa: BLE001
    pass

n = lambda s: str(s).strip().lstrip("0") or "0"  # noqa: E731
ORDER = ["3.5t", "5.5t", "7.5t"]
srt = lambda s: sorted({x for x in s if x}, key=ORDER.index)  # noqa: E731
PENDING = pending_ruling_codes()
PAT = re.compile(r"(?<![A-Z0-9])(" + "|".join(map(re.escape, PENDING)) + r")(?![A-Z0-9])")

TWELVE = ["5876103260", "5878320470", "8975167220", "8978808270", "8982473951",
          "8982482712", "8983320620", "8983459492", "8983550720", "8983753330",
          "8981868281", "8983615742"]


def raw_texts(pns: set[str]) -> dict[str, list[str]]:
    out: dict[str, list[str]] = {p: [] for p in pns}
    for f in ("epc_decode_batch1_20260919.json", "epc_decode_batch2_20260919.json"):
        p = DER / f
        if not p.is_file():
            continue
        for r in json.loads(p.read_text(encoding="utf-8")):
            if isinstance(r, dict):
                k = n(r.get("pn"))
                if k in out:
                    out[k] += (r.get("models") or []) + (r.get("families") or [])
    x = pd.read_csv(DER / "genuine_bvp_crossref.csv", dtype=str, low_memory=False)
    x["g"] = x.genuine_pn.map(n)
    x["b"] = x.bvp_pn.map(n)
    for k in out:
        for r in x[(x.g == k) | (x.b == k)].itertuples():
            for c in ("vehicle_model", "registry_model"):
                v = getattr(r, c)
                if isinstance(v, str) and v.strip():
                    out[k].append(v)
    return out


def main() -> int:
    base = pd.read_csv(BASELINE, dtype=str, low_memory=False).fillna("")
    bak = pd.read_csv(BAK / "tonnage_capable_part_numbers.csv.bak_pre_rebase",
                      dtype=str, low_memory=False).fillna("")
    cur = pd.read_csv(DER / "tonnage_capable_part_numbers.csv", dtype=str, low_memory=False).fillna("")
    for d in (base, bak, cur):
        d["k"] = d.pn.map(n)

    # does the builder's baseline authority agree with the named pre-rebase backup?
    m = base.merge(bak, on="k", suffixes=("_b", "_k"))
    bad = m[m.bands_b.astype(str) != m.bands_k.astype(str)]
    print("=" * 100)
    print("AUTHORITY CHECK: _legacy_baseline_tonnage_capable.csv vs the pre-rebase backup")
    print("=" * 100)
    print(f"  rows in both: {len(m):,}   band values differing: {len(bad)}")
    print(f"  bands identical on all shared rows: {len(bad) == 0}")
    print()

    ev = raw_texts(set(cur.k))
    base_rungs = {r.k: srt(str(r.bands).split("+")) for r in base.itertuples()}
    named = {k: sorted({mm for txt in texts for mm in PAT.findall(txt.upper())})
             for k, texts in ev.items()}
    named = {k: v for k, v in named.items() if v}

    print("=" * 100)
    print("WHAT THE CARRY-FORWARD GUARD WOULD CHANGE IN THE 324-ROW FILE")
    print("=" * 100)
    changed, no_authority = [], []
    for r in cur.itertuples():
        k = r.k
        got = srt(str(r.bands).split("+"))
        if k in named and k in base_rungs:
            want = base_rungs[k]
        elif k in named:
            no_authority.append(k)
            want = got
        else:
            want = got
        if got != want:
            changed.append((k, got, want, named.get(k, [])))
    print(f"  rows naming a pending code          : {len(named)}")
    print(f"  rows that would change              : {len(changed)}")
    print(f"  rows naming a pending code with NO pre-change row to carry forward: "
          f"{len(no_authority)} {no_authority or ''}")
    print()
    for k, got, want, codes in changed:
        print(f"      {k:>12s}  {('+'.join(got) or '(none)'):22s} -> "
              f"{('+'.join(want) or '(none)'):22s}  via {codes}")
    print()
    named12 = {n(x) for x in TWELVE}
    hit = {k for k, _, _, _ in changed}
    print(f"  the twelve named rows that change : {len(named12 & hit)} of 12")
    print(f"  OTHER rows that change            : {sorted(hit - named12) or 'none'}")
    print(f"  twelve rows that do NOT change    : {sorted(named12 - hit) or 'none'}")
    print()
    print("=" * 100)
    print("THE TWELVE, BEFORE (backup) AND AFTER (guard)")
    print("=" * 100)
    for p in TWELVE:
        k = n(p)
        b = bak[bak.k == k]
        c = cur[cur.k == k]
        bv, cv = srt(str(b.bands.iloc[0]).split("+")), srt(str(c.bands.iloc[0]).split("+"))
        av = base_rungs.get(k, cv) if k in named else cv
        print(f"      {k:>12s}  backup {'+'.join(bv) or '(none)':22s} "
              f"current {'+'.join(cv) or '(none)':22s} "
              f"guard {'+'.join(av) or '(none)':22s} "
              f"{'restores backup' if list(av) == list(bv) and list(cv) != list(bv) else 'already correct' if list(cv) == list(bv) else 'CHECK'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
