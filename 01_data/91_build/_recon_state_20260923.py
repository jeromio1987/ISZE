"""READ-ONLY reconciliation of today's tonnage-mapping changes.

Writes nothing except its own report file. Never writes a band value anywhere.
"""
from __future__ import annotations

import csv
import hashlib
import json
import re
import sys
from pathlib import Path

ROOT = Path(r"C:\Users\jerom\Desktop\claude\ISZE")
OUT = ROOT / "01_data" / "90_INBOX" / "_recon_state_20260923_out.txt"

sys.path.insert(0, str(ROOT / "03_analytics" / "Isuzu" / "prism"))
from modules.vehicle_bands import band_for, group_for, is_pending_ruling, quarantine_candidates  # noqa: E402

# the correct token pattern for this code family
NMR_RE = re.compile(r"\bNMR(?:85)?\b", re.IGNORECASE)
# the wrong one, kept only to demonstrate the trap
WRONG_RE = re.compile(r"NMR85?")

TEN = ["5876103260", "5878320470", "8975167220", "8978808270", "8982473951",
       "8982482712", "8983320620", "8983459492", "8983550720", "8983753330"]

lines: list[str] = []


def say(*a):
    s = " ".join(str(x) for x in a)
    lines.append(s)


def sha(p: Path) -> str | None:
    if not p.exists():
        return None
    return hashlib.sha256(p.read_bytes()).hexdigest().upper()


def rows(p: Path) -> list[dict]:
    if not p.exists():
        return []
    with open(p, encoding="utf-8-sig", newline="") as fh:
        return list(csv.DictReader(fh))


def linenos(p: Path) -> int:
    if not p.exists():
        return -1
    with open(p, encoding="utf-8-sig", newline="") as fh:
        return sum(1 for _ in fh)


# ── the files under review ────────────────────────────────────────────────────────────────
CUR = {
    "tonnage_capable_part_numbers.csv": ROOT / "01_data/00_derived/tonnage_capable_part_numbers.csv",
    "vehicle_band_applicability.csv": ROOT / "01_data/00_derived/vehicle_band_applicability.csv",
    "epc_decode_nseries_banded.csv": ROOT / "01_data/00_derived/epc_decode_nseries_banded.csv",
    "series_to_tonnage.csv": ROOT / "01_data/00_derived/series_to_tonnage.csv",
    "nseries_tonnage_evolution.csv": ROOT / "01_data/00_derived/nseries_tonnage_evolution.csv",
    "nseries_tonnage_evolution.meta.json": ROOT / "01_data/00_derived/nseries_tonnage_evolution.meta.json",
    "model_code_to_tonnage.csv": ROOT / "03_analytics/Isuzu/prism/data/model_code_to_tonnage.csv",
    "model_code_to_tonnage.meta.json": ROOT / "03_analytics/Isuzu/prism/data/model_code_to_tonnage.meta.json",
}

BACKUPS = {
    "canon_map": ROOT / "01_data/91_build/_backsafe_20260923_canon_map",
    "vocab_trap_before": ROOT / "01_data/91_build/_backsafe_20260923_vocab_trap_before",
    "repair_before": ROOT / "01_data/91_build/_backsafe_20260923_repair_before",
    "rebase_bak": ROOT / "02_dashboards/sales/_backsafe_rebase_20260923",
}

# ── Section A: current state, row counts, hashes vs backups ───────────────────────────────
say("=" * 100)
say("SECTION A — current state of the files under review, hash-compared to every backup")
say("=" * 100)
say()

a_table = []
for name, p in CUR.items():
    h = sha(p)
    nl = linenos(p)
    rws = 0 if p.suffix == ".json" else len(rows(p))
    match = []
    for bname, bdir in BACKUPS.items():
        # try to find a file with this name, or the .bak_pre_rebase suffix
        cands = [bdir / name, bdir / (name + ".bak_pre_rebase")]
        for c in cands:
            if c.exists():
                match.append((bname + "::" + c.name, sha(c) == h))
    a_table.append((name, rws, nl, h[:16] if h else "MISSING", match))
    say(f"{name}")
    say(f"    rows(excl header)={rws}  lines(incl header)={nl}  sha256={h}")
    if match:
        for m, eq in match:
            say(f"    vs {m}: {'IDENTICAL' if eq else 'DIFFERS'}")
    else:
        say("    no backup found for this filename in the four backup dirs")
    say()

# ── Section B: the ten hidden-NMR part numbers ────────────────────────────────────────────
say("=" * 100)
say("SECTION B — the ten part numbers whose NMR token the narrow test missed")
say("=" * 100)
say()

# every file that names a part number, with the text columns worth scanning
SCAN_FILES = {
    "vehicle_band_applicability.csv": ROOT / "01_data/00_derived/vehicle_band_applicability.csv",
    "tonnage_capable_part_numbers.csv": ROOT / "01_data/00_derived/tonnage_capable_part_numbers.csv",
    "epc_decode_nseries_banded.csv": ROOT / "01_data/00_derived/epc_decode_nseries_banded.csv",
    "epc_decode_batch1_banded_20260919.csv": ROOT / "01_data/00_derived/epc_decode_batch1_banded_20260919.csv",
    "genuine_bvp_crossref.csv": ROOT / "01_data/00_derived/genuine_bvp_crossref.csv",
    "vehicle_family_bands.csv": ROOT / "01_data/00_derived/vehicle_family_bands.csv",
    "vehicle_family_bands (canon backup).csv": ROOT / "01_data/91_build/_backsafe_20260923_canon_map/vehicle_family_bands.csv",
    "tonnage_capable_part_numbers (canon backup).csv": ROOT / "01_data/91_build/_backsafe_20260923_canon_map/tonnage_capable_part_numbers.csv",
    "tonnage_capable_part_numbers (pre-rebase backup).csv": ROOT / "02_dashboards/sales/_backsafe_rebase_20260923/tonnage_capable_part_numbers.csv.bak_pre_rebase",
    "epc_decode_nseries_banded (canon backup).csv": ROOT / "01_data/91_build/_backsafe_20260923_canon_map/epc_decode_nseries_banded.csv",
}

PN_COLS = {"pn", "genuine_pn", "bvp_pn"}

# also the EPC decode JSONs, which carry a `models` string per part number
EPC_JSONS = sorted(ROOT.glob("01_data/**/epc_decode_batch*.json"))

say("--- B1. every file and column where an NMR token appears for each of the ten ---")
say()
nmr_locations: dict[str, list[str]] = {pn: [] for pn in TEN}
band_by_file: dict[str, dict[str, dict]] = {pn: {} for pn in TEN}

for fname, fp in SCAN_FILES.items():
    rws = rows(fp)
    if not rws:
        say(f"  [{fname}] MISSING or empty")
        continue
    cols = list(rws[0].keys())
    for r in rws:
        pn = ""
        for c in cols:
            if c.lower() in PN_COLS and (r.get(c) or "").strip() == "":
                continue
            if c.lower() in PN_COLS:
                pn = (r.get(c) or "").strip()
                break
        if pn not in nmr_locations:
            continue
        band_by_file[pn][fname] = r
        for c in cols:
            v = r.get(c) or ""
            if NMR_RE.search(v):
                nmr_locations[pn].append(f"{fname}::{c} = {v!r}")

# EPC decode JSONs
epc_hits: dict[str, list[str]] = {pn: [] for pn in TEN}
for jp in EPC_JSONS:
    try:
        data = json.loads(jp.read_text(encoding="utf-8"))
    except Exception as e:  # noqa: BLE001
        say(f"  [{jp.name}] could not read: {e}")
        continue
    recs = data if isinstance(data, list) else data.get("records") or data.get("rows") or []
    if isinstance(data, dict) and not recs:
        # try a dict keyed by pn
        if all(isinstance(v, (dict, list)) for v in data.values()):
            recs = [{"pn": k, **(v if isinstance(v, dict) else {"value": v})} for k, v in data.items()]
    for r in recs:
        if not isinstance(r, dict):
            continue
        pn = str(r.get("pn") or r.get("part_number") or "").strip()
        if pn not in epc_hits:
            continue
        for c, v in r.items():
            if isinstance(v, str) and NMR_RE.search(v):
                epc_hits[pn].append(f"{jp.name}::{c} = {v!r}")

for pn in TEN:
    say(f"--- {pn} ---")
    hits = nmr_locations[pn] + epc_hits[pn]
    if not hits:
        say("    NO NMR token found anywhere in the scanned set")
    for h in hits:
        say(f"    {h}")
    say()

say("--- B2. band on the current revision of each pn-keyed file that carries a band ---")
say()
for pn in TEN:
    say(f"--- {pn} ---")
    m = band_by_file[pn]
    # tonnage_capable_part_numbers
    if "tonnage_capable_part_numbers.csv" in m:
        r = m["tonnage_capable_part_numbers.csv"]
        say(f"    tonnage_capable_part_numbers.csv: band_list={r.get('band_list')!r} n_bands={r.get('n_bands')!r} "
            f"bands={r.get('bands')!r} exclusive_band={r.get('exclusive_band')!r} band_count={r.get('band_count')!r} "
            f"parked_codes={r.get('parked_codes')!r} eur={r.get('eur')!r}")
    else:
        say("    tonnage_capable_part_numbers.csv: ABSENT")
    if "vehicle_band_applicability.csv" in m:
        r = m["vehicle_band_applicability.csv"]
        say(f"    vehicle_band_applicability.csv: codes_named={r.get('codes_named')!r} parked_codes={r.get('parked_codes')!r} "
            f"wildcards_named={r.get('wildcards_named')!r}")
        say(f"        n_series_bands={r.get('n_series_bands')!r} vehicle_bands={r.get('vehicle_bands')!r} "
            f"exclusive_band={r.get('exclusive_band')!r} band_list={r.get('band_list')!r} bands={r.get('bands')!r} "
            f"band_status={r.get('band_status')!r} eur={r.get('eur')!r}")
    else:
        say("    vehicle_band_applicability.csv: ABSENT")
    if "epc_decode_nseries_banded.csv" in m:
        r = m["epc_decode_nseries_banded.csv"]
        say(f"    epc_decode_nseries_banded.csv: series_from_epc={r.get('series_from_epc')!r} series_all={r.get('series_all')!r} "
            f"tonnage_band={r.get('tonnage_band')!r} registry_model_band={r.get('registry_model_band')!r} "
            f"band_status={r.get('band_status')!r} eur_all_years={r.get('eur_all_years')!r}")
    else:
        say("    epc_decode_nseries_banded.csv: ABSENT")
    if "epc_decode_batch1_banded_20260919.csv" in m:
        r = m["epc_decode_batch1_banded_20260919.csv"]
        say(f"    epc_decode_batch1_banded_20260919.csv: model_codes={r.get('model_codes')!r} tonnage_band={r.get('tonnage_band')!r} "
            f"band_status={r.get('band_status')!r} billed_eur_all={r.get('billed_eur_all')!r}")
    else:
        say("    epc_decode_batch1_banded_20260919.csv: ABSENT")
    if "genuine_bvp_crossref.csv" in m:
        r = m["genuine_bvp_crossref.csv"]
        say(f"    genuine_bvp_crossref.csv: vehicle_model={r.get('vehicle_model')!r}")
    if "vehicle_family_bands.csv" in m:
        r = m["vehicle_family_bands.csv"]
        say(f"    vehicle_family_bands.csv: vehicle_model={r.get('vehicle_model')!r} family={r.get('family')!r}")
    say()

say("--- B3. before/after: each of the ten's band in the current file vs the pre-change backups ---")
say()
BACK_MAP = {
    "tonnage_capable_part_numbers.csv": [
        ("canon_map", ROOT / "01_data/91_build/_backsafe_20260923_canon_map/tonnage_capable_part_numbers.csv"),
        ("pre_rebase", ROOT / "02_dashboards/sales/_backsafe_rebase_20260923/tonnage_capable_part_numbers.csv.bak_pre_rebase"),
    ],
    "epc_decode_nseries_banded.csv": [
        ("canon_map", ROOT / "01_data/91_build/_backsafe_20260923_canon_map/epc_decode_nseries_banded.csv"),
    ],
    "epc_decode_batch1_banded_20260919.csv": [
        ("repair_before", ROOT / "01_data/91_build/_backsafe_20260923_repair_before/epc_decode_batch1_banded_20260919.csv"),
        ("vocab_trap_before", ROOT / "01_data/91_build/_backsafe_20260923_vocab_trap_before/epc_decode_batch1_banded_20260919.csv"),
    ],
    "vehicle_family_bands.csv": [
        ("canon_map", ROOT / "01_data/91_build/_backsafe_20260923_canon_map/vehicle_family_bands.csv"),
    ],
}
BC = {
    "tonnage_capable_part_numbers.csv": ["band_list", "n_bands", "bands", "exclusive_band", "band_count"],
    "epc_decode_nseries_banded.csv": ["tonnage_band", "registry_model_band", "band_count", "band_status"],
    "epc_decode_batch1_banded_20260919.csv": ["tonnage_band", "band_count", "band_status"],
    "vehicle_family_bands.csv": [],  # no band column, only for token location
}

for pn in TEN:
    say(f"--- {pn} ---")
    for fname, bks in BACK_MAP.items():
        bcols = BC[fname]
        if not bcols:
            continue
        cur = band_by_file[pn].get(fname, {})
        curvals = {c: cur.get(c) for c in bcols}
        say(f"    {fname}  CURRENT: {curvals}")
        for blabel, bp in bks:
            brws = {r.get("pn", "").strip(): r for r in rows(bp)}
            b = brws.get(pn)
            if b is None:
                say(f"        {blabel}: ABSENT")
            else:
                bvals = {c: b.get(c) for c in bcols}
                same = bvals == curvals
                say(f"        {blabel}: {bvals}  -> {'SAME' if same else '*** DIFFERS ***'}")
    say()

# ── Section C: the general NMR sweep across every file carrying a band ────────────────────
say("=" * 100)
say("SECTION C — general sweep: did ANY NMR- or NMR85-bearing part number have its band changed?")
say("=" * 100)
say()

BAND_FILES = {
    "tonnage_capable_part_numbers.csv": (ROOT / "01_data/00_derived/tonnage_capable_part_numbers.csv",
                                         ["band_list", "n_bands", "bands", "exclusive_band", "band_count"]),
    "vehicle_band_applicability.csv": (ROOT / "01_data/00_derived/vehicle_band_applicability.csv",
                                       ["n_series_bands", "band_list", "bands", "exclusive_band", "band_count", "band_status"]),
    "epc_decode_nseries_banded.csv": (ROOT / "01_data/00_derived/epc_decode_nseries_banded.csv",
                                      ["tonnage_band", "registry_model_band", "band_count", "band_status"]),
    "epc_decode_batch1_banded_20260919.csv": (ROOT / "01_data/00_derived/epc_decode_batch1_banded_20260919.csv",
                                              ["tonnage_band", "band_count", "band_status"]),
}

say("Pattern used: " + NMR_RE.pattern)
say("Wrong pattern (for contrast): " + WRONG_RE.pattern)
say()

# build, per band file, {pn: (bandtuple, rowtext)}
def band_map(p: Path, bandcols: list[str]) -> dict[str, tuple]:
    out = {}
    for r in rows(p):
        pn = (r.get("pn") or "").strip()
        if not pn:
            continue
        bt = tuple((c, (r.get(c) or "").strip()) for c in bandcols)
        txt = " | ".join(str(v) for v in r.values())
        out[pn] = (bt, txt)
    return out


cur_maps = {k: band_map(v[0], v[1]) for k, v in BAND_FILES.items()}

# sweep: for each band file, which rows carry an NMR token, and did the band move vs a backup?
sweep_result = {}
for fname, (fp, bcols) in BAND_FILES.items():
    cm = cur_maps[fname]
    bearing = {pn: tv for pn, tv in cm.items() if NMR_RE.search(tv[1])}
    with_wrong = {pn for pn, tv in cm.items() if WRONG_RE.search(tv[1])}
    with_right = set(bearing)
    sweep_result[fname] = (len(cm), len(bearing), with_wrong, with_right)
    say(f"[{fname}] rows swept = {len(cm)}")
    say(f"    rows with a correct-pattern NMR token   = {len(with_right)}")
    say(f"    rows with the WRONG-pattern token only  = {len(with_wrong - with_right)}  "
        f"(inflates the parked group / hides rows)")
    say()

say("--- C1. is an NMR-bearing row's band changed vs the pre-change backup, per file? ---")
say()

# tonnage_capable: compare current vs pre_rebase
def compare_bands(fname, curp, bandcols, backp, blabel, only_nmr_only=True):
    cm = cur_maps[fname]
    bm = band_map(backp, bandcols)
    common = set(cm) & set(bm)
    moved = []
    for pn in sorted(common):
        (cb, ctxt) = cm[pn]
        (bb, btxt) = bm[pn]
        nmr_here = bool(NMR_RE.search(ctxt) or NMR_RE.search(btxt))
        if only_nmr_only and not nmr_here:
            continue
        if cb != bb:
            moved.append((pn, bb, cb))
    return len(common), moved, len([p for p in common if NMR_RE.search(cm[p][1]) or NMR_RE.search(bm[p][1])])


say("[tonnage_capable_part_numbers.csv] current vs pre_rebase backup")
n_common, moved, n_nmr = compare_bands(
    "tonnage_capable_part_numbers.csv",
    BAND_FILES["tonnage_capable_part_numbers.csv"][0],
    BAND_FILES["tonnage_capable_part_numbers.csv"][1],
    BACK_MAP["tonnage_capable_part_numbers.csv"][1][1],
    "pre_rebase")
say(f"    pns in both revisions = {n_common}; NMR-token-bearing in either = {n_nmr}; "
    f"of those, band changed = {len(moved)}")
for pn, b, c in moved:
    say(f"    *** {pn}: {b} -> {c}")
say()

say("[tonnage_capable_part_numbers.csv] current vs canon_map backup")
n_common, moved, n_nmr = compare_bands(
    "tonnage_capable_part_numbers.csv",
    BAND_FILES["tonnage_capable_part_numbers.csv"][0],
    BAND_FILES["tonnage_capable_part_numbers.csv"][1],
    BACK_MAP["tonnage_capable_part_numbers.csv"][0][1],
    "canon_map")
say(f"    pns in both revisions = {n_common}; NMR-token-bearing in either = {n_nmr}; "
    f"of those, band changed = {len(moved)}")
for pn, b, c in moved:
    say(f"    *** {pn}: {b} -> {c}")
say()

say("[epc_decode_nseries_banded.csv] current vs canon_map backup")
n_common, moved, n_nmr = compare_bands(
    "epc_decode_nseries_banded.csv",
    BAND_FILES["epc_decode_nseries_banded.csv"][0],
    BAND_FILES["epc_decode_nseries_banded.csv"][1],
    BACK_MAP["epc_decode_nseries_banded.csv"][0][1],
    "canon_map")
say(f"    pns in both revisions = {n_common}; NMR-token-bearing in either = {n_nmr}; "
    f"of those, band changed = {len(moved)}")
for pn, b, c in moved:
    say(f"    *** {pn}: {b} -> {c}")
say()

say("[epc_decode_batch1_banded_20260919.csv] current vs repair_before backup")
n_common, moved, n_nmr = compare_bands(
    "epc_decode_batch1_banded_20260919.csv",
    BAND_FILES["epc_decode_batch1_banded_20260919.csv"][0],
    BAND_FILES["epc_decode_batch1_banded_20260919.csv"][1],
    BACK_MAP["epc_decode_batch1_banded_20260919.csv"][0][1],
    "repair_before")
say(f"    pns in both revisions = {n_common}; NMR-token-bearing in either = {n_nmr}; "
    f"of those, band changed = {len(moved)}")
for pn, b, c in moved:
    say(f"    *** {pn}: {b} -> {c}")
say()

# code-keyed files
say("[series_to_tonnage.csv] the NMR / NMR85 rows in the current revision")
st = rows(ROOT / "01_data/00_derived/series_to_tonnage.csv")
for r in st:
    if NMR_RE.search(r.get("series", "") or ""):
        say(f"    {r}")
say("[model_code_to_tonnage.csv] the NMR / NMR85 rows in the current revision")
mc = rows(ROOT / "03_analytics/Isuzu/prism/data/model_code_to_tonnage.csv")
for r in mc:
    if NMR_RE.search(r.get("model_code", "") or ""):
        say(f"    {r}")
say("[model_code_to_tonnage.csv] (vocab_trap_before backup) the NMR / NMR85 rows")
for r in rows(ROOT / "01_data/91_build/_backsafe_20260923_vocab_trap_before/model_code_to_tonnage.csv"):
    if NMR_RE.search(r.get("model_code", "") or ""):
        say(f"    {r}")
say("[model_code_to_tonnage.csv] (repair_before backup) the NMR / NMR85 rows")
for r in rows(ROOT / "01_data/91_build/_backsafe_20260923_repair_before/model_code_to_tonnage.csv"):
    if NMR_RE.search(r.get("model_code", "") or ""):
        say(f"    {r}")
say("[series_to_band.csv] authored map — NMR / NMR85 rows (read-only)")
for r in rows(ROOT / "03_analytics/Isuzu/prism/data/series_to_band.csv"):
    if NMR_RE.search(r.get("code", "") or ""):
        say(f"    code={r.get('code')!r} vehicle_group={r.get('vehicle_group')!r} "
            f"tonnage_band={r.get('tonnage_band')!r} gvw_t={r.get('gvw_t')!r} status={r.get('status')!r} "
            f"quarantine_candidates={r.get('quarantine_candidates')!r}")
say()

# ── Section D: 176 vs 131 ────────────────────────────────────────────────────────────────
say("=" * 100)
say("SECTION D — the published contradiction: 176 vs 131, on which revision, now")
say("=" * 100)
say()


def short(bandstr: str) -> set[str]:
    """Short band names from a pipe/comma list so a naming difference is not a band difference."""
    if not bandstr:
        return set()
    toks = re.split(r"[|,;]", bandstr)
    out = set()
    for t in toks:
        t = t.strip()
        if not t:
            continue
        m = re.match(r"^(LCV_D-Max|3\.5t_N35|5\.5t_N50_N55|7\.5t_N50_N62_N75|F_series_MD_heavy)$", t)
        if not m:
            continue
        v = m.group(1)
        out.add({"LCV_D-Max": "lcv", "3.5t_N35": "3.5t", "5.5t_N50_N55": "5.5t",
                 "7.5t_N50_N62_N75": "7.5t", "F_series_MD_heavy": "F"}[v])
    return out


def short_list(bandlist: str) -> set[str]:
    if not bandlist:
        return set()
    return {t.strip() for t in re.findall(r"'([^']+)'", bandlist)}


def census(tc_path: Path, ap_path: Path, label: str):
    tc = rows(tc_path)
    ap = {r["pn"].strip(): r for r in rows(ap_path) if r.get("pn")}
    same = diff = 0
    eur_same = eur_diff = 0.0
    parked = free = 0
    eur_parked = eur_free = 0.0
    diff_basis: dict[tuple, list] = {}
    for r in tc:
        pn = r["pn"].strip()
        a = ap.get(pn)
        if not a:
            continue
        pub = set(x.strip() for x in re.split(r"[|,]", (r.get("bands") or "").replace(" ", "")) if x.strip())
        cor = short(a.get("n_series_bands", ""))
        eur = float(r.get("eur") or 0)
        if pub == cor:
            same += 1
            eur_same += eur
        else:
            diff += 1
            eur_diff += eur
            diff_basis.setdefault((tuple(sorted(pub)), tuple(sorted(cor))), []).append((pn, eur))
        # parked test on the corrected mapping's own code columns
        if NMR_RE.search((a.get("codes_named") or "") + " " + (a.get("parked_codes") or "")):
            parked += 1
            eur_parked += eur
        else:
            free += 1
            eur_free += eur
    say(f"--- {label} ---")
    say(f"    tonnage_capable rows = {len(tc)}   (file: {tc_path.name})")
    say(f"    applicability rows joined = {len(ap)}   (file: {ap_path.name})")
    say(f"    band set identical   = {same:4d}   EUR {eur_same:,.2f}")
    say(f"    band set DIFFERENT   = {diff:4d}   EUR {eur_diff:,.2f}")
    say(f"    of the different: names NMR/NMR85 in the mapping's own code columns = {parked} "
        f"EUR {eur_parked:,.2f}")
    say(f"                      names neither                                      = {free} "
        f"EUR {eur_free:,.2f}")
    say(f"    shape of the difference (published bands -> corrected bands):")
    for (pub, cor), lst in sorted(diff_basis.items(), key=lambda kv: -sum(x[1] for x in kv[1])):
        tot = sum(x[1] for x in lst)
        say(f"        {'+'.join(pub) or '(none)':<28} -> {'+'.join(cor) or '(none)':<28} "
            f"{len(lst):4d} pns  EUR {tot:,.2f}")
    say()
    return diff, eur_diff


# current revisions
c_diff, c_eur = census(
    ROOT / "01_data/00_derived/tonnage_capable_part_numbers.csv",
    ROOT / "01_data/00_derived/vehicle_band_applicability.csv",
    "CURRENT revision")

# frozen basis = the pre-rebase backup, with the canon-map applicability
c_diff_b, c_eur_b = census(
    ROOT / "02_dashboards/sales/_backsafe_rebase_20260923/tonnage_capable_part_numbers.csv.bak_pre_rebase",
    ROOT / "01_data/91_build/_backsafe_20260923_canon_map/vehicle_family_bands.csv"
    if False else ROOT / "01_data/00_derived/vehicle_band_applicability.csv",
    "FROZEN basis (pre-rebase tonnage_capable + current applicability)")

# ── Section E: the ten in the frozen 44 context ──────────────────────────────────────────
say("=" * 100)
say("SECTION E — arithmetic: the 44, the 34, the 10, and the corrected free euro")
say("=" * 100)
say()

tc_frozen = rows(ROOT / "02_dashboards/sales/_backsafe_rebase_20260923/tonnage_capable_part_numbers.csv.bak_pre_rebase")
ap_now = {r["pn"].strip(): r for r in rows(ROOT / "01_data/00_derived/vehicle_band_applicability.csv") if r.get("pn")}
eur = {}
for r in tc_frozen:
    eur[r["pn"].strip()] = float(r.get("eur") or 0)

# the 44 = different on the frozen basis and no NMR in the mapping's own code columns
frozen44 = []
for r in tc_frozen:
    pn = r["pn"].strip()
    a = ap_now.get(pn)
    if not a:
        continue
    pub = set(x.strip() for x in re.split(r"[|,]", (r.get("bands") or "").replace(" ", "")) if x.strip())
    cor = short(a.get("n_series_bands", ""))
    if pub == cor:
        continue
    if NMR_RE.search((a.get("codes_named") or "") + " " + (a.get("parked_codes") or "")):
        continue
    frozen44.append(pn)

say(f"frozen-basis free set (different bands, no NMR in the mapping's code columns) = {len(frozen44)} "
    f"EUR {sum(eur[p] for p in frozen44):,.2f}")
ten_in = [p for p in TEN if p in frozen44]
say(f"of which carry an NMR token elsewhere = {len(ten_in)}")
for p in ten_in:
    say(f"    {p}  EUR {eur.get(p,0):,.2f}")
rest = [p for p in frozen44 if p not in TEN]
say(f"the other (genuinely free) = {len(rest)}  EUR {sum(eur[p] for p in rest):,.2f}")
say(f"the ten's total EUR = {sum(eur[p] for p in TEN):,.2f}")
say()

# ── Section F: the current published-share figure, derived read-only ─────────────────────
say("=" * 100)
say("SECTION F — the published exclusive-attribution share, re-derived read-only")
say("=" * 100)
say()

evo = rows(ROOT / "01_data/00_derived/nseries_tonnage_evolution.csv")
single = shared = 0.0
totals = {}
for r in evo:
    if (r.get("membership") or "") == "single_band":
        single += float(r.get("billed_eur") or 0)
    elif (r.get("membership") or "") == "also_fits_band":
        shared += float(r.get("billed_eur") or 0)
    clock = r.get("clock") or ""
    totals.setdefault(clock, 0.0)
    if (r.get("family_scope") or "") == "n_series_truck":
        totals[clock] += float(r.get("billed_eur") or 0)

say("nseries_tonnage_evolution.csv, n_series_truck rows")
say(f"    single_band total = EUR {single:,.2f}")
say(f"    also_fits_band total (raw, both clocks summed) = EUR {shared:,.2f}")
for clock, v in sorted(totals.items()):
    say(f"    n_series_truck grand total, clock={clock}: EUR {v:,.2f}")
if single and max(totals.values()):
    say(f"    share (raw single / single-clock total) = {single / max(totals.values()) * 100:.4f}%")
say()
say("    NOTE: the file carries both clocks; their band-split rows are duplicates of the same")
say("    booking, so summing them double-counts. The denominator must be one clock's total.")
say()
say("    band_split check from the meta:")
meta = json.loads((ROOT / "01_data/00_derived/nseries_tonnage_evolution.meta.json").read_text(encoding="utf-8"))


def find_key(obj, key, path=""):
    out = []
    if isinstance(obj, dict):
        for k, v in obj.items():
            if k == key:
                out.append((path + "/" + k, v))
            out += find_key(v, key, path + "/" + k)
    elif isinstance(obj, list):
        for i, v in enumerate(obj):
            out += find_key(v, key, path + f"[{i}]")
    return out


for p, v in find_key(meta, "band_split_single_versus_shared"):
    say(f"    {p} = {v}")
for p, v in find_key(meta, "single_band_pns"):
    say(f"    {p} = {v}")
say()

OUT.write_text("\n".join(lines), encoding="utf-8")
print(f"wrote {OUT}  ({len(lines)} lines)")
print("\n".join(lines[:60]))
