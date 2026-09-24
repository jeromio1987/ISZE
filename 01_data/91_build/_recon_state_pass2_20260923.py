"""READ-ONLY pass 2: the NMR sweep, 131 vs 176, and map agreement. Writes no band value."""
from __future__ import annotations

import csv
import hashlib
import io
import json
import re
import sys
from pathlib import Path

ROOT = Path(r"C:\Users\jerom\Desktop\claude\ISZE")
OUT = ROOT / "01_data" / "90_INBOX" / "_recon_state_pass2_20260923.txt"

sys.path.insert(0, str(ROOT / "03_analytics" / "Isuzu" / "prism"))
from modules.vehicle_bands import (band_for, group_for, is_pending_ruling,  # noqa: E402
                                   pending_ruling_codes, quarantine_candidates)

NMR_RE = re.compile(r"\bNMR(?:85)?\b", re.IGNORECASE)
WRONG_RE = re.compile(r"NMR85?")
L: list[str] = []


def say(*a):
    L.append(" ".join(str(x) for x in a))


def rows(p: Path):
    if not p.exists():
        return []
    with open(p, encoding="utf-8-sig", newline="") as fh:
        return list(csv.DictReader(fh))


def sha(p: Path):
    return hashlib.sha256(p.read_bytes()).hexdigest().upper() if p.exists() else None


def txt(p: Path):
    return p.read_text(encoding="utf-8-sig") if p.exists() else ""


# ── A. every file carrying a band column ────────────────────────────────────────────────
say("=" * 110)
say("A. EVERY FILE THAT CARRIES A BAND COLUMN — rows, band columns, map agreement")
say("=" * 110)
say()

CANDIDATES = [
    ("01_data/00_derived/tonnage_capable_part_numbers.csv", "pn",
     ["band_list", "n_bands", "bands", "exclusive_band", "band_count"]),
    ("01_data/00_derived/vehicle_band_applicability.csv", "pn",
     ["n_series_bands", "band_list", "bands", "exclusive_band", "band_count", "band_status"]),
    ("01_data/00_derived/epc_decode_nseries_banded.csv", "pn",
     ["tonnage_band", "registry_model_band", "band_count", "band_status"]),
    ("01_data/00_derived/epc_decode_batch1_banded_20260919.csv", "pn",
     ["tonnage_band", "band_count", "band_status"]),
    ("01_data/00_derived/series_to_tonnage.csv", "series", ["tonnage_band"]),
    ("01_data/00_derived/nseries_tonnage_evolution.csv", "family_scope", ["tonnage_band", "band_label"]),
    ("03_analytics/Isuzu/prism/data/model_code_to_tonnage.csv", "model_code", ["tonnage_band"]),
    ("03_analytics/Isuzu/prism/data/series_to_band.csv", "code", ["tonnage_band"]),
]

for rel, keycol, bandcols in CANDIDATES:
    p = ROOT / rel
    rws = rows(p)
    hdr = list(rws[0].keys()) if rws else []
    present = [c for c in bandcols if c in hdr]
    say(f"{rel}")
    say(f"    rows={len(rws)}  key={keycol}  band columns present={present}")
    say(f"    sha256={sha(p)}")
    # map agreement: only meaningful for key == a series/model code
    if keycol in ("series", "model_code", "code") and "tonnage_band" in hdr:
        agree = disagree = 0
        mism = []
        for r in rws:
            k = (r.get(keycol) or "").strip()
            v = (r.get("tonnage_band") or "").strip()
            m = band_for(k)
            if v == m:
                agree += 1
            else:
                disagree += 1
                mism.append((k, v, m))
        say(f"    vs authored map band_for(): agree={agree} differ={disagree}")
        for k, v, m in mism:
            say(f"        *** {k}: file={v!r}  map={m!r}")
    say()

# ── B. the union of NMR-bearing part numbers across ALL sources ─────────────────────────
say("=" * 110)
say("B. NMR sweep — build the union from every source, then check band movement in every band file")
say("=" * 110)
say()
say("token regex  = " + NMR_RE.pattern)
say("wrong regex  = " + WRONG_RE.pattern)
say()

TEN = ["5876103260", "5878320460", "5878320470", "8975167220", "8978808270", "8982473951",
       "8982482712", "8983320620", "8983459492", "8983550720", "8983753330"]
TEN = ["5876103260", "5878320470", "8975167220", "8978808270", "8982473951",
       "8982482712", "8983320620", "8983459492", "8983550720", "8983753330"]

PN_SOURCES = [
    ROOT / "01_data/00_derived/vehicle_band_applicability.csv",
    ROOT / "01_data/00_derived/tonnage_capable_part_numbers.csv",
    ROOT / "01_data/00_derived/epc_decode_nseries_banded.csv",
    ROOT / "01_data/00_derived/epc_decode_batch1_banded_20260919.csv",
    ROOT / "01_data/00_derived/genuine_bvp_crossref.csv",
    ROOT / "01_data/00_derived/vehicle_family_bands.csv",
    # pre-change revisions too, so a token the re-base REMOVED is still counted
    ROOT / "01_data/91_build/_backsafe_20260923_canon_map/tonnage_capable_part_numbers.csv",
    ROOT / "02_dashboards/sales/_backsafe_rebase_20260923/tonnage_capable_part_numbers.csv.bak_pre_rebase",
    ROOT / "01_data/91_build/_backsafe_20260923_canon_map/epc_decode_nseries_banded.csv",
    ROOT / "01_data/91_build/_backsafe_20260923_canon_map/vehicle_family_bands.csv",
]

union: set[str] = set()
per_file: dict[str, int] = {}
for p in PN_SOURCES:
    rws = rows(p)
    hit = 0
    for r in rws:
        pn = ""
        for c in ("pn", "genuine_pn", "bvp_pn"):
            if r.get(c):
                pn = r[c].strip()
                break
        if not pn:
            continue
        if NMR_RE.search(" | ".join(str(v) for v in r.values())):
            hit += 1
            union.add(pn)
    per_file[p.name + (" <backup>" if "_backsafe" in str(p) else "")] = hit
    say(f"    {p.relative_to(ROOT)}  NMR-bearing rows = {hit}")
say()
say(f"union of NMR-bearing part numbers across all the above = {len(union)}")
say()

# EPC JSONs
for jp in sorted(ROOT.glob("01_data/**/epc_decode_batch*.json")):
    try:
        data = json.loads(jp.read_text(encoding="utf-8"))
    except Exception:  # noqa: BLE001
        continue
    recs = data if isinstance(data, list) else (data.get("records") or data.get("rows") or [])
    n = 0
    for r in recs:
        if not isinstance(r, dict):
            continue
        pn = str(r.get("pn") or "").strip()
        if pn and NMR_RE.search(" | ".join(str(v) for v in r.values())):
            union.add(pn)
            n += 1
    if n:
        say(f"    {jp.relative_to(ROOT)}  NMR-bearing records = {n}")
say()
say(f"union incl. EPC JSONs = {len(union)}")

# are the ten inside the union?
say()
say("the ten, present in the union?")
for pn in TEN:
    say(f"    {pn}: {'YES' if pn in union else 'no'}")

# ── C. band movement of every union member in every band file ───────────────────────────
say()
say("=" * 110)
say("C. did a band move for ANY union member? current vs each pre-change backup")
say("=" * 110)
say()

BAND_FILES = [
    ("tonnage_capable_part_numbers.csv",
     ROOT / "01_data/00_derived/tonnage_capable_part_numbers.csv",
     ["band_list", "n_bands", "bands", "exclusive_band", "band_count"],
     [("canon_map", ROOT / "01_data/91_build/_backsafe_20260923_canon_map/tonnage_capable_part_numbers.csv"),
      ("pre_rebase", ROOT / "02_dashboards/sales/_backsafe_rebase_20260923/tonnage_capable_part_numbers.csv.bak_pre_rebase")]),
    ("epc_decode_nseries_banded.csv",
     ROOT / "01_data/00_derived/epc_decode_nseries_banded.csv",
     ["tonnage_band", "registry_model_band", "band_count", "band_status"],
     [("canon_map", ROOT / "01_data/91_build/_backsafe_20260923_canon_map/epc_decode_nseries_banded.csv")]),
    ("epc_decode_batch1_banded_20260919.csv",
     ROOT / "01_data/00_derived/epc_decode_batch1_banded_20260919.csv",
     ["tonnage_band", "band_count", "band_status"],
     [("repair_before", ROOT / "01_data/91_build/_backsafe_20260923_repair_before/epc_decode_batch1_banded_20260919.csv"),
      ("vocab_trap_before", ROOT / "01_data/91_build/_backsafe_20260923_vocab_trap_before/epc_decode_batch1_banded_20260919.csv")]),
]

for fname, curp, bcols, bks in BAND_FILES:
    rws = rows(curp)
    cur = {(r.get("pn") or "").strip(): r for r in rws if r.get("pn")}
    say(f"[{fname}]  rows={len(cur)}  band cols compared={bcols}")
    tot = 0
    for blabel, bp in bks:
        old = {(r.get("pn") or "").strip(): r for r in rows(bp) if r.get("pn")}
        common = sorted(set(cur) & set(old))
        moved_all = []
        moved_nmr = []
        for pn in common:
            ct = tuple((cur[pn].get(c) or "").strip() for c in bcols)
            ot = tuple((old[pn].get(c) or "").strip() for c in bcols)
            if ct == ot:
                continue
            moved_all.append((pn, ot, ct))
            if pn in union:
                moved_nmr.append((pn, ot, ct))
        say(f"    vs {blabel}: common pns={len(common)}  rows changed (any)={len(moved_all)}  "
            f"of which NMR-bearing={len(moved_nmr)}")
        tot += len(moved_nmr)
        for pn, o, c in moved_nmr:
            mark = "  <-- one of the ten" if pn in TEN else ""
            say(f"        *** {pn}: {o} -> {c}{mark}")
    say(f"    => NMR-bearing rows whose band moved in this file = {tot}")
    say()

# ── D. 176 vs 131 vs 146: test every plausible comparison ───────────────────────────────
say("=" * 110)
say("D. the published contradiction — every plausible way to compute it")
say("=" * 110)
say()

ap = {r["pn"].strip(): r for r in rows(ROOT / "01_data/00_derived/vehicle_band_applicability.csv") if r.get("pn")}


def plist(s: str) -> set[str]:
    return {t.strip() for t in re.findall(r"'([^']+)'", s or "")}


def compact(s: str) -> set[str]:
    return {t.strip() for t in re.split(r"\+", (s or "")) if t.strip()}


def run(label, tc_path, col, valfn):
    tc = rows(tc_path)
    same = diff = 0
    eur_same = eur_diff = 0.0
    nojoin = 0
    for r in tc:
        pn = r["pn"].strip()
        a = ap.get(pn)
        if not a:
            nojoin += 1
            continue
        pub = valfn(r.get(col) or "")
        cor = {t.strip() for t in re.split(r"[|,]", (a.get("n_series_bands") or "")) if t.strip()}
        e = float(r.get("eur") or 0)
        if pub == cor:
            same += 1
            eur_same += e
        else:
            diff += 1
            eur_diff += e
    say(f"    {label:<62} rows={len(tc):4d} no-join={nojoin:3d} identical={same:4d} "
        f"DIFFERENT={diff:4d}  EUR {eur_diff:,.2f}")
    return diff, eur_diff


say("CURRENT revision:")
run("`band_list` vs n_series_bands", ROOT / "01_data/00_derived/tonnage_capable_part_numbers.csv",
    "band_list", plist)
run("`bands` vs n_series_bands", ROOT / "01_data/00_derived/tonnage_capable_part_numbers.csv",
    "bands", compact)
run("`bands` split on + with t suffix normalised", ROOT / "01_data/00_derived/tonnage_capable_part_numbers.csv",
    "bands", lambda s: {t.strip() for t in re.split(r"\+", s or "") if t.strip()})
say()
say("FROZEN revision (pre-rebase backup, 23/09 05:37:27):")
run("`band_list` vs n_series_bands", ROOT / "02_dashboards/sales/_backsafe_rebase_20260923/tonnage_capable_part_numbers.csv.bak_pre_rebase",
    "band_list", plist)
run("`bands` vs n_series_bands", ROOT / "02_dashboards/sales/_backsafe_rebase_20260923/tonnage_capable_part_numbers.csv.bak_pre_rebase",
    "bands", compact)
say()
say("EARLIEST revision (canon_map backup, 22/09 18:22:40):")
run("`band_list` vs n_series_bands", ROOT / "01_data/91_build/_backsafe_20260923_canon_map/tonnage_capable_part_numbers.csv",
    "band_list", plist)
say()

# how many rows in each revision, and how many join
for lbl, p in [("current", ROOT / "01_data/00_derived/tonnage_capable_part_numbers.csv"),
               ("pre_rebase", ROOT / "02_dashboards/sales/_backsafe_rebase_20260923/tonnage_capable_part_numbers.csv.bak_pre_rebase"),
               ("canon_map", ROOT / "01_data/91_build/_backsafe_20260923_canon_map/tonnage_capable_part_numbers.csv")]:
    rws = rows(p)
    join = sum(1 for r in rws if r["pn"].strip() in ap)
    say(f"    {lbl}: tonnage_capable rows={len(rws)} joined to applicability={join} "
        f"eur_total={sum(float(r.get('eur') or 0) for r in rws):,.2f}")
say()
say("applying XOR-style by band only (ignore n_bands/order) on CURRENT:")
cur_rows = rows(ROOT / "01_data/00_derived/tonnage_capable_part_numbers.csv")
xor = 0
eur_x = 0.0
for r in cur_rows:
    pn = r["pn"].strip()
    a = ap.get(pn)
    if not a:
        continue
    pub = plist(r.get("band_list") or "")
    cor = {t.strip() for t in re.split(r"[|,]", (a.get("n_series_bands") or "")) if t.strip()}
    if pub != cor:
        xor += 1
        eur_x += float(r.get("eur") or 0)
say(f"    band_list vs n_series_bands: DIFFERENT={xor} EUR {eur_x:,.2f}")

# ── E. nseries_tonnage_evolution membership values and the share ────────────────────────
say()
say("=" * 110)
say("E. the published share — membership values actually present, and the arithmetic")
say("=" * 110)
say()
evo = rows(ROOT / "01_data/00_derived/nseries_tonnage_evolution.csv")
from collections import Counter
say("    distinct `membership` values: " + str(Counter(r.get("membership") for r in evo)))
say("    distinct `clock` values: " + str(Counter(r.get("clock") for r in evo)))
say("    distinct `family_scope` values: " + str(Counter(r.get("family_scope") for r in evo)))
n_series = [r for r in evo if (r.get("family_scope") or "") == "n_series_truck"]
say(f"    n_series_truck rows = {len(n_series)}")
byclock = {}
for r in n_series:
    byclock.setdefault(r.get("clock"), 0.0)
    byclock[r.get("clock")] += float(r.get("billed_eur") or 0)
say(f"    n_series_truck grand total per clock = " + str({k: round(v, 2) for k, v in byclock.items()}))
for m in sorted(set(r.get("membership") for r in n_series)):
    sub = [r for r in n_series if r.get("membership") == m]
    for clock in sorted(set(r.get("clock") for r in sub)):
        s2 = [r for r in sub if r.get("clock") == clock]
        say(f"      membership={m!r} clock={clock}: rows={len(s2)} eur={sum(float(r.get('billed_eur') or 0) for r in s2):,.2f}")
say()
meta = json.loads((ROOT / "01_data/00_derived/nseries_tonnage_evolution.meta.json").read_text(encoding="utf-8"))


def fk(obj, key, path=""):
    out = []
    if isinstance(obj, dict):
        for k, v in obj.items():
            if k == key:
                out.append((path + "/" + k, v))
            out += fk(v, key, path + "/" + k)
    elif isinstance(obj, list):
        for i, v in enumerate(obj):
            out += fk(v, key, path + f"[{i}]")
    return out


for p, v in fk(meta, "band_split_single_versus_shared"):
    say(f"    meta {p} = {v}")
for p, v in fk(meta, "generated_at"):
    say(f"    meta {p} = {v}")
say()

# ── F. mtimes of everything, and any applicability backup ───────────────────────────────
say("=" * 110)
say("F. mtimes, and does a backup of vehicle_band_applicability.csv exist?")
say("=" * 110)
say()
import datetime
for rel in [c[0] for c in CANDIDATES] + [
        "01_data/00_derived/vehicle_band_applicability.meta.json",
        "01_data/00_derived/nseries_tonnage_evolution.meta.json",
        "03_analytics/Isuzu/prism/data/model_code_to_tonnage.meta.json",
        "01_data/00_derived/tonnage_capable_categories.csv"]:
    p = ROOT / rel
    if p.exists():
        mt = datetime.datetime.fromtimestamp(p.stat().st_mtime)
        say(f"    {mt:%Y-%m-%d %H:%M:%S}  {p.stat().st_size:>9,}  {rel}")
say()
say("    any file on disk named vehicle_band_applicability* :")
for p in sorted(ROOT.rglob("vehicle_band_applicability*")):
    say(f"        {p.relative_to(ROOT)}  {p.stat().st_size:,}  "
        f"{datetime.datetime.fromtimestamp(p.stat().st_mtime):%Y-%m-%d %H:%M:%S}")
say()
say("    the _tmp_rebase44_20260923 dir — 6 newest files (is anyone still writing?)")
tmp = ROOT / "01_data/91_build/_tmp_rebase44_20260923"
if tmp.exists():
    fs = sorted(tmp.glob("*"), key=lambda x: x.stat().st_mtime, reverse=True)[:6]
    for p in fs:
        say(f"        {datetime.datetime.fromtimestamp(p.stat().st_mtime):%Y-%m-%d %H:%M:%S}  {p.name}")
say()
say("    programmatic pending_ruling codes from the module: " + str(pending_ruling_codes()))
for c in pending_ruling_codes():
    say(f"        {c}: band_for={band_for(c)!r} group={group_for(c)!r} "
        f"candidates={quarantine_candidates(c)}")

OUT.write_text("\n".join(L), encoding="utf-8")
print("wrote", OUT, len(L), "lines")
