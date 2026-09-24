"""Final check: do all four written files agree with the classification?"""
import openpyxl
import pandas as pd

ROOT = r"C:\Users\jerom\Desktop\claude\ISZE"
DER = ROOT + r"\01_data\00_derived"
CLASS = ROOT + r"\01_data\91_build\export_aim_eq_20260924\classified.csv"

c = pd.read_csv(CLASS, dtype=str)
c["pn"] = c["pn"].str.strip().str.upper()
f = c[c["aim_level_1"].fillna("") != ""].drop_duplicates("pn").set_index("pn")
print(f"classified part numbers to apply: {len(f)}")

checks = []

m = pd.read_csv(DER + r"\aim_master_v2.csv", dtype=str, low_memory=False)
m["pn"] = m["part_number"].str.strip().str.upper()
mm = m.drop_duplicates("pn").set_index("pn")
sub = mm.reindex(f.index)
got = sub["aim_l1_fixed"].fillna("")
checks.append(("aim_master_v2.csv", int(sub["part_number"].notna().sum()),
               int((got == f["aim_level_1"]).sum())))

o = pd.read_csv(DER + r"\aim_pn_classification_20260920.csv", dtype=str, low_memory=False)
o["pn"] = o["part_number"].str.strip().str.upper()
oo = o.drop_duplicates("pn").set_index("pn")
osub = oo.reindex(f.index)
checks.append(("aim_pn_classification_20260920.csv", int(osub["part_number"].notna().sum()),
               int((osub["aim_l1_fixed"].fillna("") == f["aim_level_1"]).sum())))

p = pd.read_csv(DER + r"\AIM_Master_PN_Categories_Figkey_20260921.csv", dtype=str, low_memory=False)
p["pn"] = p["part_number"].str.strip().str.upper()
pp = p.drop_duplicates("pn").set_index("pn")
psub = pp.reindex(f.index)
checks.append(("AIM_Master_PN_Categories_Figkey_20260921.csv", int(psub["part_number"].notna().sum()),
               int((psub["aim_level_1"].fillna("") == f["aim_level_1"]).sum())))

wb = openpyxl.load_workbook(DER + r"\AIM_Master_PN_Categories_Figkey_20260921.xlsx", read_only=True)
ws = wb["AIM_PN"]
want = set(f.index)
seen = 0
ok = 0
for r in ws.iter_rows(min_row=2, values_only=True):
    pn = str(r[0]).strip().upper()
    if pn in want:
        seen += 1
        if str(r[3]).strip() == f.loc[pn, "aim_level_1"]:
            ok += 1
checks.append(("AIM_Master_PN_Categories_Figkey_20260921.xlsx", seen, ok))

print(f"\n{'file':44s} {'PNs present':>12s} {'L1 matches':>12s}")
for name, present, match in checks:
    flag = "OK" if match == len(f) and present == len(f) else "CHECK"
    print(f"{name:44s} {present:>12d} {match:>12d}  {flag}")
print(f"\nexpected {len(f)} in every file")
