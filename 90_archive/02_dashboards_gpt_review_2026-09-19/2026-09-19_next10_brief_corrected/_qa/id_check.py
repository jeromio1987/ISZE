"""id integrity + label-reference check on he edited files.

- list every id= in static markup and every getElementById / querySelector('#...') / href="#..."
- flag references with no matching id, and duplicate ids
"""
import os, re, sys

BASE = r"C:\Users\jerom\Desktop\claude\ISZE\02_dashboards\sales\_gpt_review\2026-09-19_next10_brief_corrected"
EDITED = [
    "01_ISZE_Exec_Aftersales_Paper.html",
    "02_ISZE_Leakage_Cockpit.html",
    "03_Warranty_Commercial_Review.html",
    "04_ISZE_AIM_Classification_Paper.html",
    "07_ISZE_Pricing_Revision_AIM_Source.html",
    "10_Dealer_Sellout_AIM_GPS_ITUK_UTI_2025.html",
]
for fn in EDITED:
    t = open(os.path.join(BASE, fn), encoding="utf-8", newline="").read()
    markup = re.sub(r"<script[^>]*>.*?</script>", "", t, flags=re.S | re.I)
    markup = re.sub(r"<style[^>]*>.*?</style>", "", markup, flags=re.S | re.I)
    markup = re.sub(r"<!--.*?-->", "", markup, flags=re.S)
    ids = re.findall(r'\sid="([^"]+)"', markup)
    dupes = sorted({i for i in ids if ids.count(i) > 1})
    gets = set(re.findall(r"getElementById\(\s*['\"]([^'\"]+)['\"]", t))
    sel = set(re.findall(r"querySelector(?:All)?\(\s*['\"]#([A-Za-z0-9_\-]+)", t))
    frags = set(re.findall(r'href="#([A-Za-z0-9_\-]+)"', markup))
    missing_get = sorted(g for g in gets if g not in ids and not any(g in x for x in []))
    missing_sel = sorted(s for s in sel if s not in ids)
    missing_frag = sorted(f for f in frags if f not in ids)
    print(f"== {fn}")
    print(f"   ids in markup: {len(ids)} (unique {len(set(ids))})  duplicates: {dupes}")
    print(f"   getElementById targets: {len(gets)}  not found in static markup: {missing_get}")
    print(f"   querySelector #ids: {len(sel)}  not found: {missing_sel}")
    print(f"   in-page #fragments: {len(frags)}  not found: {missing_frag}")
