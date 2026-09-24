import csv, sys, json
sys.stdout.reconfigure(encoding="utf-8")
import os
os.chdir(r"C:\Users\jerom\Desktop\claude\ISZE")

NEW = "01_data/00_derived/aim_master_v2.csv"
OLD = "01_data/00_derived/aim_master_v2.csv.bak_pre_export_aim_eq_20260924_20260924_142051"

def load(p):
    out = {}
    with open(p, encoding="utf-8-sig", newline="") as f:
        for r in csv.DictReader(f):
            pn = (r.get("part_number") or "").strip()
            out[pn] = ((r.get("aim_l1") or "").strip(), (r.get("aim_l1_fixed") or "").strip(),
                       (r.get("has_aim") or "").strip(),
                       float(r.get("l12m_billed_eur") or 0))
    return out

new = load(NEW)
old = load(OLD)
moved = [pn for pn in new if new[pn][:2] != old.get(pn, ("", "", "", 0))[:2]]
print("rows whose AIM label moved:", len(moved))
eur_moved = sum(new[pn][3] for pn in moved)
eur_all = sum(v[3] for v in new.values())
print(f"billed euro on the moved rows (12m): {eur_moved:,.0f} of {eur_all:,.0f} "
      f"({100*eur_moved/eur_all if eur_all else 0:.2f}%)")

# how many of the moved rows carry any billing at all
withb = [pn for pn in moved if new[pn][3] > 0]
print("moved rows with any billed euro:", len(withb))

# the old vs new Unknown counts
print("old has_aim=1:", sum(1 for v in old.values() if v[2] == "1"))
print("new has_aim=1:", sum(1 for v in new.values() if v[2] == "1"))
