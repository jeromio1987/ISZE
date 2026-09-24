"""Blast radius of the proposed structural guard, measured properly.

Proposed guard: a code the authored map marks `pending_ruling` is recognised by a WHOLE-WORD scan of
the raw evidence string, in addition to the exact-token split. Narrow on purpose - only pending codes,
so it cannot widen detection for ordinary codes and reintroduce the `TF*` / `F*` class of error.

This asks: if that detection is added, which rows in tonnage_capable_part_numbers.csv would change,
and would the twelve named rows land exactly on their pre-rebase values?

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
BAK = ROOT / "02_dashboards" / "sales" / "_backsafe_rebase_20260923"
sys.path.insert(0, str(PRISM))
from modules.vehicle_bands import (  # noqa: E402
    N_SERIES_BANDS, NOT_IN_SCOPE, UNRESOLVED, band_for, pending_ruling_codes,
)

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:  # noqa: BLE001
    pass

n = lambda s: str(s).strip().lstrip("0") or "0"  # noqa: E731
SHORT = {"3.5t_N35": "3.5t", "5.5t_N50_N55": "5.5t", "7.5t_N50_N62_N75": "7.5t"}
ORDER = ["3.5t", "5.5t", "7.5t"]
srt = lambda s: sorted(s, key=ORDER.index)  # noqa: E731
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
    cur = pd.read_csv(DER / "tonnage_capable_part_numbers.csv", dtype=str, low_memory=False).fillna("")
    bak = pd.read_csv(BAK / "tonnage_capable_part_numbers.csv.bak_pre_rebase",
                      dtype=str, low_memory=False).fillna("")
    app = pd.read_csv(DER / "vehicle_band_applicability.csv", dtype=str, low_memory=False).fillna("")
    for d in (cur, bak, app):
        d["k"] = d.pn.map(n)
    A = app.set_index("k")
    ev = raw_texts(set(cur.k))

    # what the guard ADDS: pending codes visible as whole words in the raw text
    extra: dict[str, list[str]] = {}
    for k, texts in ev.items():
        found = sorted({m for t in texts for m in PAT.findall(t.upper())})
        if found:
            extra[k] = found
    print("=" * 100)
    print("WHAT THE GUARD ADDS")
    print("=" * 100)
    print(f"  part numbers whose raw text names a pending code : {len(extra)}")
    cur_park = {k for k in extra if str(cur[cur.k == k].parked_codes.iloc[0]).strip()}
    print(f"  already recorded as parked in the file           : {len(cur_park)}")
    gap = sorted(set(extra) - cur_park)
    print(f"  NOT recorded as parked (the silent gap)          : {len(gap)}")
    for k in gap:
        print(f"      {k:>12s} pending named {extra[k]}")
    print()

    # simulate the re-run: legacy three-rung columns from the neutral table's settled rungs plus
    # every pending code the raw text names
    changed = []
    rows = []
    for r in cur.itertuples():
        k = r.k
        if k not in A.index:
            continue
        settled = {b for b in str(A.loc[k].n_series_bands).split("|") if b}
        bands = set(settled)
        for c in extra.get(k, []):
            b = band_for(c)
            if b not in (UNRESOLVED, NOT_IN_SCOPE) and b in N_SERIES_BANDS:
                bands.add(b)
        if not bands:
            continue
        want = srt({SHORT[b] for b in bands})
        got = srt({x for x in str(r.bands).split("+") if x})
        rows.append((k, got, want))
        if got != want:
            changed.append((k, got, want))
    print("=" * 100)
    print("WHAT WOULD CHANGE IN THE FILE (324 rows)")
    print("=" * 100)
    print(f"  rows whose three-rung list would move: {len(changed)}")
    for k, got, want in changed:
        b = bak[bak.k == k]
        bv = "+".join(srt({x for x in str(b.bands.iloc[0]).split('+') if x})) if len(b) else "(absent)"
        print(f"      {k:>12s}  {('+'.join(got) or '(none)'):22s} -> {('+'.join(want) or '(none)'):22s}"
              f"  backup {bv:22s} {'MATCHES BACKUP' if bv == '+'.join(want) else 'differs from backup'}")
    print()
    named = {n(x) for x in TWELVE}
    hit = {k for k, _, _ in changed}
    print(f"  the twelve named rows that would move : {len(named & hit)} of 12")
    print(f"  OTHER rows that would move            : {sorted(hit - named) or 'none'}")
    print()
    print("=" * 100)
    print("WOULD THE GUARD LAND THE TWELVE ON THEIR BACKUP VALUES?")
    print("=" * 100)
    for p in TWELVE:
        k = n(p)
        b = bak[bak.k == k]
        bv = srt({x for x in str(b.bands.iloc[0]).split("+") if x}) if len(b) else []
        want = dict((kk, w) for kk, _, w in rows).get(k)
        ok = want is not None and list(want) == list(bv)
        print(f"      {k:>12s} backup {'+'.join(bv) or '(none)':22s} "
              f"guard {'+'.join(want) if want else '(row leaves file)':22s} {'OK' if ok else 'NO'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
