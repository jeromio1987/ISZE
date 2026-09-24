import os, sys, json, hashlib, io
sys.stdout.reconfigure(encoding="utf-8")
os.chdir(r"C:\Users\jerom\Desktop\claude\ISZE")

B = "02_dashboards/_build/_aim_refresh/before/"
REL = [
    "sales/ISZE_AIM_Classification_Paper.html",
    "sales/ISZE_AIM_Comparison_ALL.html",
    "sales/ISZE_AIM_Comparison_PORTUGAL.html",
    "sales/ISZE_AIM_DB_DLR_Deep_Dive_ALL.html",
    "sales/ISZE_AIM_DB_DLR_Deep_Dive_PORTUGAL.html",
    "pricing/ISZE_AIM_Repertoire_Map_2026-09-17.html",
    "pricing/ISZE_AIM_Repertoire_Spider_2026-09-17.html",
    "pricing/ISZE_AIM_Truck_Catalogue_2026-09-18.html",
    "pricing/ISZE_Pricing_Revision_AIM_Source.html",
    "pricing/ISZE_Pricing_Revision_AIM_Source_PROTOTYPE_AllDB.html",
    "pricing/ISZE_Pricing_Revision_AIM_Source_PROTOTYPE_NordicsCust.html",
    "pricing/ISZE_Pricing_Revision_AIM_FX_20261001.html",
    "pricing/ISZE_Price_Increase_5pct_Flat_REVIEW_2026-09-17.html",
    "pricing/ISZE_Price_Increase_5pct_Flat_SIMULATION_2026-09-22.html",
    "pricing/ISZE_PMS_Price_Response_Brief_2026-09-22.html",
    "pricing/ISZE_Pricing_Policy_Paper.html",
    "sales/Dealer_Sellout_AIM_GPS_ITUK_UTI_2025.html",
    "hub/ISZE_OS_Hub.html",
    "ops/ISZE_OS_Console.html",
]

# strings we expect today's classification to move, read with plain find/in
NEEDLES = [
    "Classified part numbers",
    "system names",
    "parts with AIM labels",
    "Real catalogue node",
    "still unattributed",
    "unclassified",
    "Not on AIM spine",
    "tree_rows",
    "billed_in_tree",
    "tree_l1",
    "aim_l1_fixed",
]


def grab(path, needle, span=90):
    b = open(path, "rb").read()
    t = b.decode("utf-8", errors="ignore")
    out = []
    i = 0
    while True:
        i = t.find(needle, i)
        if i < 0 or len(out) >= 3:
            break
        out.append(t[max(0, i - span): i + span].replace("\n", " "))
        i += len(needle)
    return len(b), out


for rel in REL:
    after = "02_dashboards/" + rel
    before = B + rel.replace("/", "__")
    if not (os.path.exists(after) and os.path.exists(before)):
        print("== SKIP", rel, os.path.exists(after), os.path.exists(before))
        continue
    na, oa = grab(after, "Classified part numbers")
    nb, ob = grab(before, "Classified part numbers")
    print("=" * 4, rel)
    print(f"     bytes {nb:,} -> {na:,}")
    for n in NEEDLES:
        _, a = grab(after, n)
        _, b = grab(before, n)
        if a != b and (a or b):
            print(f"     [{n}]")
            for x in b[:1]:
                print("        before:", " ".join(x.split())[:170])
            for x in a[:1]:
                print("        after :", " ".join(x.split())[:170])
