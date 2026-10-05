import os, re, sys
sys.stdout.reconfigure(encoding="utf-8")
os.chdir(r"C:\Users\jerom\Desktop\claude\ISZE")
B = "02_dashboards/_build/_aim_refresh/before/"

SPEC = {
    "pricing/ISZE_AIM_Repertoire_Map_2026-09-17.html": [
        ("tree_rows", r'"tree_rows"\s*:\s*(\d+)'),
        ("tree_part_numbers", r'"tree_part_numbers"\s*:\s*(\d+)'),
        ("billed_in_tree", r'"billed_in_tree"\s*:\s*(\d+)'),
        ("classified_not_billed", r'"classified_not_billed"\s*:\s*(\d+)'),
        ("billed_part_numbers", r'"billed_part_numbers"\s*:\s*(\d+)'),
        ("tree_l1", r'"tree_l1"\s*:\s*(\d+)'),
        ("tree_l3", r'"tree_l3"\s*:\s*(\d+)'),
    ],
    "pricing/ISZE_AIM_Repertoire_Spider_2026-09-17.html": [
        ("tree_rows", r'"tree_rows"\s*:\s*(\d+)'),
        ("billed_in_tree", r'"billed_in_tree"\s*:\s*(\d+)'),
        ("classified_not_billed", r'"classified_not_billed"\s*:\s*(\d+)'),
    ],
    "pricing/ISZE_AIM_Truck_Catalogue_2026-09-18.html": [
        ("tree_rows", r'"tree_rows"\s*:\s*(\d+)'),
        ("billed_in_tree", r'"billed_in_tree"\s*:\s*(\d+)'),
        ("classified_not_billed", r'"classified_not_billed"\s*:\s*(\d+)'),
    ],
    "pricing/ISZE_Pricing_Revision_AIM_Source.html": [
        ("weighted_pct", r'"weighted_pct"\s*:\s*([\d.]+)'),
        ("billed_eur", r'"billed_eur"\s*:\s*([\d.]+)'),
        ("step_eur", r'"step_eur"\s*:\s*([\d.]+)'),
        ("not_on_aim", r'"Not on AIM spine"'),
        ("aim_l1_options", r'"l1":\[(.*?)\]'),
    ],
    "pricing/ISZE_Pricing_Revision_AIM_Source_PROTOTYPE_AllDB.html": [
        ("weighted_pct", r'"weighted_pct"\s*:\s*([\d.]+)'),
        ("aim_l1_options", r'"l1":\[(.*?)\]'),
    ],
    "pricing/ISZE_Pricing_Revision_AIM_Source_PROTOTYPE_NordicsCust.html": [
        ("weighted_pct", r'"weighted_pct"\s*:\s*([\d.]+)'),
    ],
}
for rel, spec in SPEC.items():
    a, b = "02_dashboards/" + rel, B + rel.replace("/", "__")
    print("=" * 5, rel)
    for name, pat in spec:
        va = re.search(pat, open(a, encoding="utf-8", errors="ignore").read())
        vb = re.search(pat, open(b, encoding="utf-8", errors="ignore").read())
        ga = (va.group(1)[:120] if va and va.lastindex else ("present" if va else None))
        gb = (vb.group(1)[:120] if vb and vb.lastindex else ("present" if vb else None))
        flag = "" if ga == gb else "   <-- MOVED"
        print(f"    {name:22} before={gb}   after={ga}{flag}")
