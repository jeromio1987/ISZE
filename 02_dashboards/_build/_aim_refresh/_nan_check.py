"""Narrow NaN check: only embedded JSON payloads and visible text, not JS source."""
import json, os, re, sys
sys.stdout.reconfigure(encoding="utf-8")
os.chdir(r"C:\Users\jerom\Desktop\claude\ISZE")

PAGES = [e["page"] for e in json.load(open("02_dashboards/_build/_aim_refresh/pages.json", encoding="utf-8"))]

JSON_BLOCK = re.compile(r'<script[^>]*type="(?:application/json|application/ld\+json)"[^>]*>(.*?)</script>', re.S)
JS_ASSIGN = re.compile(r'(?:window\.\w+|\w+)\s*=\s*(\{[\s\S]{200,}?\})\s*;', re.S)

for rel in PAGES:
    p = rel
    if not os.path.exists(p):
        print("missing", rel); continue
    t = open(p, encoding="utf-8", errors="ignore").read()
    n_json = 0
    bad_json = []
    for m in JSON_BLOCK.finditer(t):
        blk = m.group(1)
        n_json += 1
        if re.search(r'\bNaN\b', blk):
            bad_json.append(blk[:120])
    # data.js style assignments (aim_cy2026)
    n_assign = 0
    bad_assign = []
    for m in JS_ASSIGN.finditer(t):
        blk = m.group(1)
        if len(blk) < 5000:
            continue
        n_assign += 1
        if re.search(r'(?<!is)\bNaN\b', blk):
            bad_assign.append(len(blk))
    # visible text nan: strip script/style then look
    stripped = re.sub(r'<script[\s\S]*?</script>', ' ', t)
    stripped = re.sub(r'<style[\s\S]*?</style>', ' ', stripped)
    vis_nan = re.search(r'NaN', stripped)
    print(f"{rel}")
    print(f"    json blocks={n_json} withNaN={len(bad_json)}   js payloads={n_assign} withNaN={len(bad_assign)}   visible NaN={'YES' if vis_nan else 'no'}")
    for b in bad_json[:2]:
        print("      json:", " ".join(b.split())[:150])
