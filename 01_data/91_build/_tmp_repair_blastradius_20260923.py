"""Measure the guard before writing it: which rows name a pending code, and would carrying forward
their existing band change exactly the twelve rows and nothing else?

Also tests the brief's hypothesis (that NMR's weight was read from model_code_to_tonnage.csv) by
checking whether that file is read anywhere the builder can reach.
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
BUILDER = ROOT / "01_data" / "91_build" / "pn_ammo_probe_20260918" / "_vehicle_band_applicability.py"
BAK = ROOT / "02_dashboards" / "sales" / "_backsafe_rebase_20260923"

sys.path.insert(0, str(PRISM))
from modules.vehicle_bands import load_map, pending_ruling_codes  # noqa: E402

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:  # noqa: BLE001
    pass

n = lambda s: str(s).strip().lstrip("0") or "0"  # noqa: E731


def raw_evidence(pns: set[str]) -> dict[str, list[str]]:
    """Every model string on disk that names one of these part numbers."""
    out: dict[str, list[str]] = {p: [] for p in pns}
    for f in ("epc_decode_batch1_20260919.json", "epc_decode_batch2_20260919.json"):
        p = DER / f
        if not p.is_file():
            continue
        for r in json.loads(p.read_text(encoding="utf-8")):
            if not isinstance(r, dict):
                continue
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
    base = pd.read_csv(BAK / "tonnage_capable_part_numbers.csv.bak_pre_rebase",
                       dtype=str, low_memory=False).fillna("")
    cur = pd.read_csv(DER / "tonnage_capable_part_numbers.csv", dtype=str, low_memory=False).fillna("")
    for d in (base, cur):
        d["k"] = d.pn.map(n)

    pending = pending_ruling_codes()
    print("=" * 100)
    print("PENDING-RULING CODES AND HOW THEY ARE WRITTEN ON DISK")
    print("=" * 100)
    print(f"  map marks pending_ruling: {pending}")
    for c in pending:
        print(f"      {c:8s} band_for -> {load_map()[c]['tonnage_band']}")
    print()

    # the robust detection: the code as a whole word anywhere in the string
    pat = re.compile(r"(?<![A-Z0-9])(" + "|".join(map(re.escape, pending)) + r")(?![A-Z0-9])")
    ev = raw_evidence(set(cur.k) | set(base.k))
    names_pending = sorted({p for p, texts in ev.items()
                            if any(pat.search(t.upper()) for t in texts)})
    print(f"  part numbers whose raw evidence names a pending code: {len(names_pending)}")

    # how the current file records them
    cur_parked = set(cur[cur.parked_codes.astype(str).str.strip() != ""].k)
    print(f"  part numbers the current file records as parked    : {len(cur_parked)}")
    print(f"  named but NOT recorded as parked (the silent gap)  : "
          f"{len(set(names_pending) - cur_parked)}")
    for p in sorted(set(names_pending) - cur_parked):
        print(f"      {p}")
    print()

    # what carrying forward would do
    m = base.merge(cur, on="k", suffixes=("_b", "_c"))
    would = m[m.k.isin(names_pending)]
    diff = would[would.bands_b != would.bands_c]
    print("=" * 100)
    print("BLAST RADIUS OF THE CARRY-FORWARD GUARD")
    print("=" * 100)
    print(f"  rows naming a pending code                    : {len(would)}")
    print(f"  of those, carry-forward would change the bands: {len(diff)}")
    print()
    for r in diff.itertuples():
        print(f"      {r.k:>12s}  {r.bands_b:22s} -> {r.bands_c:22s}"
              f"  (restore to {r.bands_b})  parked={r.parked_codes_c!r}")
    print()
    print(f"  rows NOT naming a pending code that the guard would touch: "
          f"{len(diff) - len([r for r in diff.itertuples() if r.k in names_pending])}")
    print()
    print("=" * 100)
    print("THE BRIEF'S HYPOTHESIS: was model_code_to_tonnage.csv read?")
    print("=" * 100)
    src = BUILDER.read_text(encoding="utf-8")
    for needle in ("model_code_to_tonnage", "model_code", "7.5", "5.5"):
        hits = [i for i, line in enumerate(src.splitlines(), 1)
                if needle in line and not line.strip().startswith("#")]
        print(f"  builder mentions {needle!r} in code on lines: {hits or 'none'}")
    print()
    print("  the ten rows' 5.5 t evidence, as written on disk:")
    TENSIX = ["5876103260", "5878320470", "8983320620", "8975167220", "8978808270",
              "8982473951", "8982482712", "8983459492", "8983550720", "8983753330"]
    for p in TENSIX:
        texts = [t for t in ev.get(p, []) if pat.search(t.upper())]
        shown = [t for t in ev.get(p, []) if "NMR" in t.upper()]
        print(f"      {p:>12s}  strings naming NMR: {len(shown)}")
        for t in shown[:3]:
            print(f"            {t!r}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
