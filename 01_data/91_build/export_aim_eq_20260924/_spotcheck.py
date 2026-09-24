"""Spot check: do the new labels appear in the rebuilt Excel?"""
import openpyxl
import pandas as pd

XLSX = r"C:\Users\jerom\Desktop\claude\ISZE\01_data\00_derived\AIM_Master_PN_Categories_Figkey_20260921.xlsx"
CLASS = r"C:\Users\jerom\Desktop\claude\ISZE\01_data\91_build\export_aim_eq_20260924\classified.csv"

c = pd.read_csv(CLASS, dtype=str)
c["pn"] = c["pn"].str.strip().str.upper()
f = c[c["aim_level_1"].fillna("") != ""].drop_duplicates("pn").set_index("pn")

want = ["5876102381", "8976646550", "8983753331", "7553116080", "8975270373",
        "8979477690", "8981394311", "7552710010", "8972500731", "1136741600"]

wb = openpyxl.load_workbook(XLSX, read_only=True)
ws = wb["AIM_PN"]
found: dict[str, tuple] = {}
for r in ws.iter_rows(min_row=2, values_only=True):
    pn = str(r[0]).strip()
    if pn in want and pn not in found:
        found[pn] = (r[1], r[3], r[4], r[5])
        if len(found) == len(want):
            break

ok = 0
for pn in want:
    exp = tuple(f.loc[pn, ["aim_level_1", "aim_level_2", "aim_level_3"]]) if pn in f.index else None
    got = found.get(pn)
    same = got is not None and exp is not None and (got[1], got[2], got[3]) == exp
    ok += same
    print(f"{pn}  {'OK ' if same else 'DIFF'}")
    print(f"    description : {got[0] if got else '-'}")
    print(f"    expected    : {exp}")
    print(f"    in excel    : {(got[1], got[2], got[3]) if got else None}")
print(f"\nmatched {ok} of {len(want)}")
