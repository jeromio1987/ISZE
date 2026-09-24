"""Root-cause probe: why did the ten rows lose their 5.5 t rung?

Reads the raw evidence (EPC decode + cross-reference) for the twelve rows that moved and reports,
for every model string, what the builder's own tokenizer extracts versus what an anchored
prefix match would find. No files are written; nothing is changed.
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
sys.path.insert(0, str(PRISM))
from modules.vehicle_bands import band_for, is_pending_ruling, load_map  # noqa: E402

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:  # noqa: BLE001
    pass

n = lambda s: str(s).strip().lstrip("0") or "0"  # noqa: E731
WILDCARD_RE = re.compile(r"^[A-Z]{1,4}\d{0,3}\*$")

TWELVE = ["5876103260", "5878320470", "8975167220", "8978808270", "8982473951",
          "8982482712", "8983320620", "8983459492", "8983550720", "8983753330",
          "8981868281", "8983615742"]

# the builder's own tokenizer, copied verbatim from _vehicle_band_applicability.py
def tokens_from_text(text: str) -> tuple[list[str], list[str]]:
    known = set(load_map())
    out: list[str] = []
    wild: list[str] = []
    raw = str(text or "").upper()
    for tok in re.split(r"[,\s/;]+", raw):
        t = tok.strip().strip("()[]{}").strip()
        if not t:
            continue
        if WILDCARD_RE.match(t) or t.endswith("*"):
            wild.append(t)
            continue
        if t in known:
            out.append(t)
    return out, wild


def prefix_hits(text: str) -> list[str]:
    """A code recognised anywhere in the string, which is what caught NMR before 2026-09-23."""
    known = set(load_map())
    raw = str(text or "").upper()
    return sorted({c for c in known if re.search(rf"(?<![A-Z0-9]){re.escape(c)}(?![A-Z0-9])", raw)})


def main() -> int:
    ev: dict[str, list[tuple[str, str]]] = {n(p): [] for p in TWELVE}
    for f in ("epc_decode_batch1_20260919.json", "epc_decode_batch2_20260919.json"):
        p = DER / f
        if not p.is_file():
            continue
        for r in json.loads(p.read_text(encoding="utf-8")):
            if not isinstance(r, dict):
                continue
            key = n(r.get("pn"))
            if key in ev:
                for m in (r.get("models") or []):
                    ev[key].append((f, m))
    x = pd.read_csv(DER / "genuine_bvp_crossref.csv", dtype=str, low_memory=False)
    x["g"] = x.genuine_pn.map(n)
    x["b"] = x.bvp_pn.map(n)
    for key in ev:
        m = x[(x.g == key) | (x.b == key)]
        for r in m.itertuples():
            for col in ("vehicle_model", "registry_model"):
                v = getattr(r, col)
                if isinstance(v, str) and v.strip():
                    ev[key].append((f"crossref.{col}", v))

    print("=" * 100)
    print("ROOT CAUSE: what the builder's tokenizer sees in each model string")
    print("=" * 100)
    for key in [n(p) for p in TWELVE]:
        print()
        print(f"### {key}   band_for(NMR)={band_for('NMR')}  pending(NMR)={is_pending_ruling('NMR')}")
        seen_exact: set[str] = set()
        seen_prefix: set[str] = set()
        for src, txt in ev[key]:
            ex, wild = tokens_from_text(txt)
            px = prefix_hits(txt)
            seen_exact.update(ex)
            seen_prefix.update(px)
            dropped = sorted(set(px) - set(ex) - {"NAN"})
            if dropped:
                print(f"   [{src}] {txt[:96]!r}")
                print(f"       tokenizer found : {sorted(set(ex))}  wildcards {sorted(set(wild))}")
                print(f"       prefix would add: {dropped}")
        print(f"   EXACT tokens anywhere : {sorted(seen_exact)}")
        print(f"   PREFIX tokens anywhere: {sorted(seen_prefix)}")
        print(f"   missed by the exact match: {sorted(seen_prefix - seen_exact)}")
    print()
    print("=" * 100)
    print("THE SPECIFIC TOKEN SHAPES INVOLVED")
    print("=" * 100)
    for raw in ("18- NLR/NMR-RHD EURO6 EUROPE 18.0 -",
                "2016 NLR/NMR-LHD EURO6 EUROPE 16.0 - 17.0",
                "2018- NHR EURO6 18.0 -",
                "2018 NNR/NPR-LHD EURO6 EUROPE 18.0 - 20.0"):
        ex, wild = tokens_from_text(raw)
        print(f"   {raw!r}")
        print(f"       split on [,\\s/;]+ -> {re.split(r'[,\\s/;]+', raw.upper())}")
        print(f"       exact-match codes  -> {ex}")
        print(f"       prefix codes       -> {prefix_hits(raw)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
