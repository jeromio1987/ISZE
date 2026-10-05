"""Step 8 — verify the no-write state (READ ONLY)."""
from __future__ import annotations

import hashlib
from pathlib import Path

import pandas as pd

ROOT = Path(r"C:\Users\jerom\Desktop\claude\ISZE")
DER = ROOT / "01_data" / "00_derived"
TIER = ROOT / "01_data" / "91_build" / "export_aim_tiering_20260924"
OUT = ROOT / "01_data" / "91_build" / "_tmp_apply_export_pr00_20260924"
EQ = ROOT / "01_data" / "91_build" / "export_aim_eq_20260924"

EXPECT_SHA = "4c904357563f611a3421793f17dd424e97d432a8d92d928a04f829a1ff459a6d"
EXPECT_ROWS = 165213


def clean(s):
    x = s.fillna("").astype(str).str.strip()
    return x.where(~x.str.lower().isin(["", "nan", "none", "null"]), "")


def pn_key(s):
    return s.fillna("").astype(str).str.strip().str.upper()


def flags(s):
    return clean(s).str.lower().eq("true")


mp = DER / "aim_master_v2.csv"
raw = mp.read_bytes()
sha = hashlib.sha256(raw).hexdigest()
print("(a) master row count:")
m = pd.read_csv(mp, dtype=str, low_memory=False)
print("    rows:", len(m), "expected:", EXPECT_ROWS, "->", "PASS" if len(m) == EXPECT_ROWS else "FAIL")
print("    sha256:", sha)
print("    sha matches the pre-check value ->", "PASS" if sha == EXPECT_SHA else "FAIL")
print("    bytes:", len(raw), "(was 28,508,322) ->", "PASS" if len(raw) == 28508322 else "FAIL")

print("\n(b) no new aim_source stamp anywhere in the master:")
src = clean(m["aim_source"])
print("    rows stamped 'export_pr00_20260924':", int((src == "export_pr00_20260924").sum()),
      "->", "PASS (none)" if int((src == "export_pr00_20260924").sum()) == 0 else "FAIL")

aud = pd.read_csv(TIER / "tierA_audited.csv", dtype=str, low_memory=False)
defend = aud[flags(aud["tierA"]) & ~(flags(aud["undefendable"]) | flags(aud["convention"]))].copy()
defend["pn"] = pn_key(defend["pn"])
pns = sorted(defend["pn"].unique())

print("\n(c) the 300 still carry their original aim columns (no row changed):")
m["pn"] = pn_key(m["part_number"])
m_hit = m[m["pn"].isin(pns)]
print("    matched rows:", len(m_hit), "unique PNs:", m_hit["pn"].nunique())
print("    aim_l1:", clean(m_hit["aim_l1"]).replace("", "<empty>").value_counts().to_dict())
print("    aim_l2:", clean(m_hit["aim_l2"]).replace("", "<empty>").value_counts().to_dict())
print("    aim_l3:", clean(m_hit["aim_l3"]).replace("", "<empty>").value_counts().to_dict())
print("    aim_l1_fixed:", clean(m_hit["aim_l1_fixed"]).replace("", "<empty>").value_counts().to_dict())
print("    expected: aim_l1 empty 164 / Unknown 87 / Unknown Review 5, aim_l1_fixed same")
print("    ->", "PASS" if clean(m_hit["aim_l1"]).replace("", "<empty>").value_counts().to_dict()
      == {"<empty>": 164, "Unknown": 87, "Unknown Review": 5} else "FAIL")

print("\n(d) no backup file was created in 00_derived:")
baks = sorted(DER.glob("aim_master_v2.csv.bak_pre_export_pr00_20260924_*"))
print("    matching backups:", len(baks), "->", "PASS (none)" if not baks else "FAIL")

print("\n(e) no new dated pair from today:")
today = sorted(DER.glob("AIM_Master_PN_Categories_Figkey_2026092[4-9]*"))
newer = [p for p in sorted(DER.glob("AIM_Master_PN_Categories_Figkey_*.csv"))
         if p.name.split("_")[-1][:8] > "20260921"]
print("    files dated after 20260921:", len(newer), newer)
print("    newest csv:", max(DER.glob("AIM_Master_PN_Categories_Figkey_*.csv"),
                              key=lambda p: p.stat().st_mtime).name)
print("    ->", "PASS (no new pair)" if not newer else "FAIL")

print("\n(f) the report and the carried-out lists exist:")
rep = EQ / "APPLY_REPORT_20260924.md"
print("    report:", rep.exists(), rep.stat().st_size if rep.exists() else "")
for n in ("would_land_free.txt", "carried_out_blocked_precedence.txt", "carried_out_not_in_master.txt"):
    p = OUT / n
    lines = p.read_text(encoding="utf-8").strip().splitlines() if p.exists() else []
    print(f"    {n}: {len(lines)} lines")

print("\n(g) board row appended, existing rows intact:")
board = (ROOT / "00_docs" / "agent" / "DELEGATOR_BOARD.md").read_text(encoding="utf-8")
lines = board.splitlines()
print("    total lines:", len(lines), "(was 97)")
new = [i + 1 for i, l in enumerate(lines) if "PR00 IE40 write-back STOPPED" in l]
print("    new full row index:", new)
print("    header row still present:", any(l.startswith("| Time | Agent | What changed") for l in lines))
print("    other data rows:", sum(1 for l in lines if l.startswith("| 2026-")))
bad = [l for l in lines if l.count("|") > 6]
print("    rows with more than 6 pipes (would break the table):", len(bad),
      "->", "PASS" if not bad else "FAIL")
