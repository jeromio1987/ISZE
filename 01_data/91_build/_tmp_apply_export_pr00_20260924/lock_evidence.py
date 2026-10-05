"""Step 1f — lock evidence, hashes, encoding, and the carried-out lists (READ ONLY)."""
from __future__ import annotations

import hashlib
from pathlib import Path

import pandas as pd

ROOT = Path(r"C:\Users\jerom\Desktop\claude\ISZE")
DER = ROOT / "01_data" / "00_derived"
TIER = ROOT / "01_data" / "91_build" / "export_aim_tiering_20260924"
OUT = ROOT / "01_data" / "91_build" / "_tmp_apply_export_pr00_20260924"


def clean(s):
    x = s.fillna("").astype(str).str.strip()
    return x.where(~x.str.lower().isin(["", "nan", "none", "null"]), "")


def pn_key(s):
    return s.fillna("").astype(str).str.strip().str.upper()


def flags(s):
    return clean(s).str.lower().eq("true")


master_path = DER / "aim_master_v2.csv"
raw = master_path.read_bytes()
print("master bytes:", len(raw))
print("master sha256:", hashlib.sha256(raw).hexdigest())
print("has BOM:", raw[:3] == b"\xef\xbb\xbf")
print("CRLF count:", raw.count(b"\r\n"), "bare LF count:", raw.count(b"\n") - raw.count(b"\r\n"))

aud = pd.read_csv(TIER / "tierA_audited.csv", dtype=str, low_memory=False)
defend = aud[flags(aud["tierA"]) & ~(flags(aud["undefendable"]) | flags(aud["convention"]))].copy()
defend["pn"] = pn_key(defend["pn"])
pns = sorted(defend["pn"].unique())

master = pd.read_csv(master_path, dtype=str, low_memory=False)
master["pn"] = pn_key(master["part_number"])
m_hit = master[master["pn"].isin(pns)].copy()
fx = clean(m_hit["aim_l1_fixed"]) != ""

free = sorted(set(m_hit.loc[~fx, "pn"]))
blocked = sorted(set(m_hit.loc[fx, "pn"]))
notin = sorted(set(pns) - set(master["pn"]))

print("\nfree (write would land):", len(free))
print("blocked (precedence):   ", len(blocked))
print("not in master:          ", len(notin))
assert len(free) + len(blocked) + len(notin) == 300

assert not (set(free) & set(blocked)) and not (set(free) & set(notin)) and not (set(blocked) & set(notin))
print("sets are disjoint: True")

OUT.mkdir(parents=True, exist_ok=True)
(OUT / "carried_out_blocked_precedence.txt").write_text("\n".join(blocked), encoding="utf-8")
(OUT / "carried_out_not_in_master.txt").write_text("\n".join(notin), encoding="utf-8")
(OUT / "would_land_free.txt").write_text("\n".join(free), encoding="utf-8")
print("lists written to", OUT)

# the 4 on master but absent from classification overlay: free or blocked?
print("\nthe 4 on master but absent from classification:")
for p in ("280510800", "36091500", "440110250", "915105080"):
    row = m_hit[m_hit["pn"] == p]
    if len(row):
        r = row.iloc[0]
        print(f"  {p}: aim_l1={r['aim_l1']!r} aim_l1_fixed={r['aim_l1_fixed']!r} "
              f"-> {'BLOCKED' if clean(pd.Series([r['aim_l1_fixed']])).iat[0] else 'FREE'}")

# the date pair currently on disk
print("\ncurrent dated pair:")
for p in sorted(DER.glob("AIM_Master_PN_Categories_Figkey_*")):
    print(f"  {p.name}  {p.stat().st_size:,} bytes  mtime={pd.Timestamp(p.stat().st_mtime, unit='s')}")

print("\nmaster mtime:", pd.Timestamp(master_path.stat().st_mtime, unit="s"))
