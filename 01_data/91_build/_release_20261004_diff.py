"""Independent re-read of release 2026-10-04 against its base (approved 2026-10-02-chassis-frame).

Opens the written files again (no state from the builder) and checks, point by point, that the
seven decisions of Jerome (4 Oct 2026) are literally in the file, that nothing else differs from
the base, and that the register / meta / gate agree with the file's sha256. Read-only; writes only
_release_20261004_diff.json beside itself (numbers for the approval summary).

Euro: sales_fact.parquet net_sales_value 2025-09-01..2026-08-31, all sold-to, 10-digit padded key.
"""
from __future__ import annotations

import hashlib
import json
import subprocess
from collections import defaultdict
from pathlib import Path

import pandas as pd

ISZE = Path(r"C:\Users\jerom\Desktop\claude\ISZE")
DER = ISZE / "01_data" / "00_derived"
REL = DER / "_releases"
NEW = REL / "aim_pn_classification_release_2026-10-04.csv"
OLD = REL / "aim_pn_classification_release_2026-10-02-chassis-frame.csv"
LOG = REL / "aim_pn_classification_release_2026-10-04.changes.csv"
META = REL / "aim_pn_classification_release_2026-10-04.meta.json"
GATE = REL / "aim_pn_classification_release_2026-10-04.gate.json"
REG = REL / "RELEASES.json"
PROP = REL / "next_release_proposal_missing_billed_2026-10-02.csv"
OUT = Path(__file__).with_suffix(".json")
AIM = ["aim_l1_fixed", "aim_l2_fixed", "aim_l3_fixed"]
CAT = ["catalog_l1", "catalog_l2", "catalog_l3"]


def rd(p):
    return pd.read_csv(p, dtype=str, keep_default_na=False, low_memory=False)


def pad(k):
    k = str(k).strip()
    return k.zfill(10) if k.isdigit() else k


def sha(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()


sf = pd.read_parquet(DER / "sales_fact.parquet", columns=["billing_date", "part_number", "net_sales_value"])
sf = sf[(sf.billing_date >= "2025-09-01") & (sf.billing_date <= "2026-08-31")]
sf["pn"] = sf.part_number.astype(str).map(pad)
L12 = sf.groupby("pn").net_sales_value.sum()
TOTAL_L12 = float(sf.net_sales_value.sum())


def eur(pns):
    return round(float(sum(L12.get(pad(p), 0.0) for p in pns)), 2)


res: dict = {"checks": {}}


def check(name, ok, detail=""):
    res["checks"][name] = {"ok": bool(ok), "detail": detail}
    print(("PASS " if ok else "FAIL ") + name + (f"  {detail}" if detail else ""))


# ---- hashes and register
new_sha, old_sha = sha(NEW), sha(OLD)
reg = json.loads(REG.read_bytes().decode("utf-8"))
ent = next(c for c in reg["candidates"] if c["release_id"] == "2026-10-04")
meta = json.loads(META.read_text(encoding="utf-8"))
gate = json.loads(GATE.read_text(encoding="utf-8"))
check("base file sha256 = 9bb86a9b... (approved, unchanged)",
      old_sha == "9bb86a9b4d89c5954cd6dd15fdc977db44e66cddaa15e3e70bd0285e3bf3e65b", old_sha)
check("register entry sha256 = file sha256", ent["sha256"] == new_sha, f"{new_sha}")
check("meta sha256 = file sha256", meta["sha256"] == new_sha)
check("gate report sha256 = file sha256", gate["classifier_sha256"] == new_sha)
check("register status PENDING_APPROVAL (not approved)", ent["status"] == "PENDING_APPROVAL")
check("only one entry is APPROVED and it is the base",
      [c["release_id"] for c in reg["candidates"] if c["status"] == "APPROVED"] == ["2026-10-02-chassis-frame"])
try:
    head = subprocess.run(["git", "-C", str(ISZE), "show",
                           "HEAD:01_data/00_derived/_releases/RELEASES.json"],
                          capture_output=True, check=True).stdout
    head_reg = json.loads(head.decode("utf-8"))
    same = json.dumps(reg["candidates"][:-1], sort_keys=True) == json.dumps(head_reg["candidates"], sort_keys=True)
    check("earlier register entries identical to git HEAD", same, f"{len(head_reg['candidates'])} entries")
except Exception as e:  # noqa: BLE001
    check("earlier register entries identical to git HEAD", False, repr(e))
check("row count in register = file rows", ent["rows"] == len(rd(NEW)))
check("gate verdict PENDING_APPROVAL, 0 failed", gate["verdict"] == "PENDING_APPROVAL" and gate["failed"] == 0,
      f"passed {gate['passed']} failed {gate['failed']} pending {gate['checks_pending']}")

# ---- file vs base
new, old = rd(NEW), rd(OLD)
log = rd(LOG)
cols = list(new.columns)
check("same columns as base", cols == list(old.columns))
kn, ko = set(new.part_number), set(old.part_number)
added = sorted(kn - ko)
check("rows added = 24, none removed", len(added) == 24 and not (ko - kn), f"rows {len(old)} -> {len(new)}")
n, o = new.set_index("part_number"), old.set_index("part_number")
common = sorted(ko)
nc, oc = n.loc[common], o.loc[common]
dmask = (nc != oc)
changed = sorted(nc.index[dmask.any(axis=1)])
res["parts_changed_existing"] = len(changed)
res["columns_changed"] = {c: int(dmask[c].sum()) for c in nc.columns if dmask[c].any()}
grp = log.groupby("part_number").change_group.first()
check("parts that differ = parts in the change log (existing rows)",
      set(changed) | set(added) == set(grp.index), f"{len(changed)} existing + {len(added)} added = {len(set(grp.index))}")
# every logged cell is literally in the file, and every differing cell is logged
cells_log = {(r.part_number, r.column): (r.before, r.after) for r in log.itertuples() if r.column != "(row)"}
bad = [(k, v, n.at[k[0], k[1]]) for k, v in cells_log.items() if n.at[k[0], k[1]] != v[1] or (k[0] in o.index and o.at[k[0], k[1]] != v[0])]
check("every logged cell: before = base, after = new file", not bad, f"{len(cells_log)} cells; bad {bad[:3]}")
diff_cells = {(p, c) for p in changed for c in cols[1:] if nc.at[p, c] != oc.at[p, c]}
check("every differing cell is logged (no unlogged change)", diff_cells == set(cells_log), f"{len(diff_cells)} cells")
untouched = [k for k in ko if k not in set(changed)]
check("untouched rows identical to base", (o.loc[untouched] == n.loc[untouched]).all().all(), f"{len(untouched)} rows")
check("untouched rows byte-identical (raw CSV lines)", True)  # replaced below by raw-line check

# raw byte-level: every base line not belonging to a changed part is present, in order
raw_new = NEW.read_bytes().split(b"\r\n")
raw_old = OLD.read_bytes().split(b"\r\n")
chg_set = set(changed)
def key_of(line):
    return line.split(b",", 1)[0].decode("utf-8", "replace").strip('"')
new_keep = [l for l in raw_new if key_of(l) not in chg_set and key_of(l) not in set(added)]
old_keep = [l for l in raw_old if key_of(l) not in chg_set]
check("raw bytes: all other lines identical and in the same order", new_keep == old_keep, f"{len(old_keep)} lines")
res["checks"]["untouched rows byte-identical (raw CSV lines)"] = res["checks"]["raw bytes: all other lines identical and in the same order"]

# ---- the seven points
G = lambda df, c3: df[c3].agg(" > ".join, axis=1)
n["aim"], n["cat"] = G(n, AIM), G(n, CAT)
o["aim"], o["cat"] = G(o, AIM), G(o, CAT)

# 1: added parts
prop = rd(PROP)
high = prop[prop.confidence == "high"].set_index("part_number")
ok1 = set(added) == set(high.index) and len(high) == 24
for p in high.index:
    r = n.loc[p]
    ok1 &= (r.catalog_l1, r.catalog_l2, r.catalog_l3) == (high.at[p, "proposed_catalog_l1"], high.at[p, "proposed_catalog_l2"], high.at[p, "proposed_catalog_l3"])
    ok1 &= (r.aim_l1_fixed, r.aim_l2_fixed, r.aim_l3_fixed) == (high.at[p, "proposed_aim_l1"], high.at[p, "proposed_aim_l2"], high.at[p, "proposed_aim_l3"])
    ok1 &= len(p) == 10 and r.line_kind == "part" and r.fig_key == high.at[p, "fig_key"] and r.description_norm == high.at[p, "description"]
check("1  24 High parts added with the file's labels, 10-digit keys", ok1, f"EUR {eur(added):,.2f}")
check("1  Medium / Low / 8974923852 not in the release",
      not (set(prop[prop.confidence != 'high'].part_number) & kn) and "8974923852" not in kn)
res["added_eur"] = eur(added)

# helper: description (release, else JP) for group definitions
jp = rd(DER / "jp_codes_cache_20260920.csv")
jp["pn"] = jp.pn.map(pad)
jpd = jp.drop_duplicates("pn").set_index("pn").jp_description
o["anyd"] = o.description_norm.where(o.description_norm != "", pd.Series({k: jpd.get(pad(k), "") for k in o.index}))

import re
# 2: engine gasket sets
eng = o.index[o.anyd.map(lambda s: bool(re.match(r"^GASKET SET;\s*ENG", s)))]
eng_tr = [p for p in eng if o.at[p, "aim"] == "Transmission > Bearings & Seals > Gasket"]
eng_nolab = [p for p in eng if o.at[p, "aim"] == " >  > "]
ok2 = all(n.at[p, "aim"] == "Engine > Gasket & Sealing > Gasket" for p in eng_tr)
ok2 &= all(n.at[p, "cat"] == o.at[p, "cat"] for p in eng_tr)
trans = o.index[o.anyd.str.match(r"^GASKET SET; TRANS")]
ok2 &= all(n.at[p, "aim"] == o.at[p, "aim"] for p in trans) and len(trans) == 17
check("2  engine gasket sets now Engine > Gasket & Sealing > Gasket; catalogue unchanged",
      ok2, f"{len(eng_tr)} changed; {len(eng_nolab)} engine sets with no AIM family left; "
           f"{len(trans)} TRANS OVERHAUL sets unchanged on Transmission > Bearings & Seals > Gasket")
res["gasket_eur"] = eur(eng_tr)
# 3: EVRV
ev = o.index[o.anyd.str.contains("EVRV")]
ok3 = all(n.at[p, "aim"] == "Intake Exhaust Emission > EGR > EGR Component" and n.at[p, "cat"] == o.at[p, "cat"] for p in ev)
check("3  EVRV valves now EGR Component; catalogue unchanged", ok3, f"{len(ev)} parts, EUR {eur(ev):,.2f}")
# 4: antennas
def kind(s):
    return "antenna" if s in {"ANTENNA", "ANTENNA ASM", "ROD; ANTENNA"} else "gps" if s == "ANTENNA; GPS" else "keyless" if s.startswith("ANTENNA; KEYLES") else ""
ak = o.anyd.map(kind)
ant = o.index[ak != ""]
ok4 = True
kept = []
for p in ant:
    b = o.at[p, "aim"]
    if b in ("Electrical > Instruments > Instrument Cluster", "Unknown > Unknown > Unknown", " >  > "):
        ok4 &= n.at[p, "aim"] == "Electrical > Audio > Radio"
    else:
        ok4 &= n.at[p, "aim"] == b
        if b != "Electrical > Audio > Radio":
            kept.append(p)
    ok4 &= n.at[p, "cat"] == o.at[p, "cat"]
check("4  antennas now Electrical > Audio > Radio (other existing labels kept); catalogue unchanged", ok4,
      f"{len(ant)} antenna-list parts; kept with their own label: {kept}")
# 5: cameras
cam = o.index[o.anyd.str.contains("CAMERA") & (o.cat == "Repair parts > Engine parts > Other engine") & ~o.anyd.str.startswith("TARGET")]
ok5 = all(n.at[p, "cat"] == "Repair parts > Electrical sensors > Other electrical" and n.at[p, "aim"] == o.at[p, "aim"] and n.at[p, "aim_source"] == o.at[p, "aim_source"] for p in cam)
harn = o.index[o.anyd == "HARNESS; CAMERA"]
ok5 &= all(n.at[p, "cat"] == o.at[p, "cat"] == "Repair parts > Electrical sensors > Harness / cable" for p in harn)
tgt = o.index[o.anyd.str.contains("CAMERA") & o.anyd.str.startswith("TARGET")]
ok5 &= all(n.at[p, "cat"] == o.at[p, "cat"] and n.at[p, "aim"] == o.at[p, "aim"] for p in tgt)
check("5  camera parts on Other engine now Other electrical (catalogue only); HARNESS; CAMERA and AEBS targets not moved",
      ok5, f"{len(cam)} moved, EUR {eur(cam):,.2f}; {len(harn)} HARNESS; CAMERA stay; {len(tgt)} AEBS targets stay")
# 6: DEF injectors
dpn = list(o.index[o.description_norm.isin(["INJECTOR ASM; DEF DCM", "CONNECTOR KIT; COOLANT,INJECTOR ASM DEF", "GASKET; INJECTOR ASM,DEF DCM"])])
ok6 = len(dpn) == 5 and all(n.at[p, "aim"] == "Intake Exhaust Emission > DEF System > DEF Injector" and n.at[p, "cat"] == "High value repair > Injectors > Injector" == o.at[p, "cat"] for p in dpn)
inj3 = [p for p in dpn if o.at[p, "description_norm"] == "INJECTOR ASM; DEF DCM"]
check("6  5 DEF injector parts on the new label DEF Injector; catalogue stays Injectors > Injector", ok6,
      f"{len(dpn)} parts, EUR {eur(dpn):,.2f} (3 injector assemblies EUR {eur(inj3):,.2f})")
new_labels = set(n.aim) - set(o.aim)
check("6  DEF Injector is the only new AIM label", new_labels == {"Intake Exhaust Emission > DEF System > DEF Injector"}, str(new_labels))
check("catalogue tree: no new group or type (27 / 177)",
      (new[new.catalog_l2 != ""].catalog_l2.nunique(), new[new.catalog_l3 != ""].catalog_l3.nunique()) == (27, 177))
check("catalogue triples all exist in the base", set(n.cat) <= set(o.cat))
# 7: the named not-changed parts and siblings
sev = ["8981065790", "8980023462", "8983941570", "8983941544", "8982154541"]
check("7  PCV kits, skid plates, rear modulator unchanged", all((n.loc[p, cols[1:]] == o.loc[p, cols[1:]]).all() for p in sev))
sib = list(o.index[o.anyd.isin(["ELEMENT KIT; PCV", "PLATE; SKID,RAD", "MODULATOR; RR"])])
check("7  their siblings unchanged", all(p not in set(changed) for p in sib), f"{len(sib)} sibling parts")

# ---- per-group numbers
grp_all = grp.copy()
out_groups = {}
for g in sorted(grp.unique()):
    pns = list(grp.index[grp == g])
    out_groups[g] = {"parts": len(pns), "eur": eur(pns)}
res["groups"] = out_groups
res["total_parts_changed"] = len(grp)
res["total_eur"] = eur(list(grp.index))
res["l12m_total_sales_fact_eur"] = round(TOTAL_L12, 2)

def before_after(mask_pns, cols_, label):
    d = defaultdict(lambda: {"parts": 0, "eur": 0.0})
    for p in mask_pns:
        a = " > ".join(o.loc[p, cols_]) if p in o.index else "(not in release)"
        b = " > ".join(n.loc[p, cols_])
        if a == b:
            continue
        d[f"{a}  ->  {b}"]["parts"] += 1
        d[f"{a}  ->  {b}"]["eur"] += eur([p])
    return sorted(({"move": k, "parts": v["parts"], "eur": round(v["eur"], 2)} for k, v in d.items()),
                  key=lambda r: (-r["eur"], -r["parts"]))

for g, cols_ in (("D2_engine_gasket_sets", AIM), ("D3_evrv_valves", AIM), ("D4_antennas", AIM),
                 ("D5_cameras_catalogue", CAT), ("D6_def_injectors", AIM)):
    res["groups"][g]["moves"] = before_after(list(grp.index[grp == g]), cols_, g)
# antennas split by kind
res["antenna_by_kind"] = {}
for k_ in ("antenna", "gps", "keyless"):
    ps = [p for p in grp.index[grp == "D4_antennas"] if kind(o.at[p, "anyd"]) == k_]
    res["antenna_by_kind"][k_] = {"parts": len(ps), "eur": eur(ps),
                                  "japanese_file_only": sum(o.at[p, "description_norm"] == "" for p in ps)}
OUT.write_text(json.dumps(res, indent=2, default=str), encoding="utf-8")
fails = [k for k, v in res["checks"].items() if not v["ok"]]
print("\nGROUPS", json.dumps(res["groups"], indent=1)[:4000])
print("FAILED CHECKS:", fails if fails else "none")
