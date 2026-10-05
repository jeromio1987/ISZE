"""Ask the page's own QA script whether it passed BEFORE today's rebuild.

Copies the pre-rebuild HTML into the same folder (so any relative path still
resolves), runs the shipped QA against that copy, then removes the copy.
"""
import os, re, shutil, subprocess, sys, json
sys.stdout.reconfigure(encoding="utf-8")
os.chdir(r"C:\Users\jerom\Desktop\claude\ISZE")

B = "02_dashboards/_build/_aim_refresh/before/"

CASES = [
    ("pricing/ISZE_AIM_Repertoire_Map_2026-09-17.html",
     "02_dashboards/pricing/_build/aim_repertoire_map_2026-09-17/qa_aim_repertoire_map.py"),
    ("pricing/ISZE_AIM_Repertoire_Spider_2026-09-17.html",
     "02_dashboards/pricing/_build/aim_repertoire_map_2026-09-17/qa_aim_spider.py"),
    ("pricing/ISZE_AIM_Truck_Catalogue_2026-09-18.html",
     "02_dashboards/pricing/_build/aim_truck_catalogue_2026-09-18/qa_truck_catalogue.py"),
]

TMP = "02_dashboards/_build/_aim_refresh/_qa_before"
os.makedirs(TMP, exist_ok=True)

for rel, qa in CASES:
    src = "02_dashboards/" + rel
    name = os.path.basename(rel).replace(".html", "__BEFORE.html")
    dst = os.path.join(os.path.dirname(src), name)
    shutil.copy2(src, dst)
    text = open(qa, encoding="utf-8", errors="ignore").read()
    patched = text.replace(os.path.basename(rel), name)
    pqa = os.path.join(TMP, "qa_" + os.path.basename(qa))
    open(pqa, "w", encoding="utf-8").write(patched)
    print("=" * 6, rel)
    try:
        r = subprocess.run([sys.executable, "-X", "utf8", pqa], capture_output=True, text=True,
                           encoding="utf-8", errors="replace", timeout=600)
        tail = [l for l in (r.stdout or "").splitlines() if re.match(r"\s*(PASS|FAIL)\s+\d+|QA_|SHIP", l)]
        print("   exit:", r.returncode)
        for l in tail[-6:]:
            print("   ", l.strip())
    except Exception as e:
        print("   error:", e)
    finally:
        try:
            os.remove(dst)
        except Exception:
            pass
