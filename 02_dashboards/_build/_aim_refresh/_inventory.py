import os, re, sys, json
sys.stdout.reconfigure(encoding="utf-8")
os.chdir(r"C:\Users\jerom\Desktop\claude\ISZE")

AIM21 = ["Accident & Body", "Electrical", "Chassis Frame", "Transmission", "Cabin Interior",
         "Intake Exhaust Emission", "Engine", "Wheels Hub", "Fuel System", "Brakes",
         "Suspension", "Cooling", "Maintenance Service", "Steering", "Driveline Axle",
         "Clutch", "Lubrication", "Fluids Chemicals", "Tools Equipment",
         "Literature Marketing", "Logistics Packaging"]
CAT7 = ["Repair parts", "Competitive parts", "Accident parts", "Hardware & consumables",
        "High value repair", "Body Exterior", "Comfort parts"]

KEYS = ["coverage", "classified", "unclassified", "not on aim", "aim famil", "aim level",
        "aim l1", "catalogue node", "aim path", "on the master", "aim class"]

SKIP = ("_gpt_review", "_archive", "_backsafe", "_qa", "\\_composable", "\\_design",
        "\\_working", "\\_audit", "\\Data\\", "\\side\\", "spa_internal", "\\_build\\")
CAP = 600_000
SRC = re.compile(r"([A-Za-z0-9_]+(?:aim|AIM)[A-Za-z0-9_]*\.(?:csv|json|parquet|js|xlsx))")

def scan(root):
    for dp, dn, fn in os.walk(root):
        if any(s in dp for s in SKIP):
            continue
        for f in fn:
            if f.lower().endswith(".html"):
                yield os.path.join(dp, f)

rows = []
for p in list(scan("02_dashboards")) + list(scan("09_meetings")):
    size = os.path.getsize(p)
    try:
        t = open(p, "rb").read(min(size, CAP)).decode("utf-8", errors="ignore")
    except Exception:
        continue
    low = t.lower()
    a21 = [n for n in AIM21 if n in t]
    c7 = [n for n in CAT7 if n in t]
    hits = []
    for k in KEYS:
        start = 0
        cnt = 0
        while cnt < 4:
            i = low.find(k, start)
            if i < 0:
                break
            start = i + len(k) + 60
            frag = t[max(0, i - 110): i + 130]
            frag = re.sub(r"<[^>]{0,400}>", " ", frag)
            frag = re.sub(r"\s+", " ", frag).strip()
            if re.search(r"\d", frag) and 20 < len(frag) < 210:
                hits.append(frag)
                cnt += 1
    # only pages where AIM is a real subject
    aim_n = low.count("aim")
    if len(a21) >= 3 or (hits and aim_n >= 6):
        rows.append({"path": p, "bytes": size, "aim_mentions": aim_n,
                     "aim21": a21, "cat7": c7, "hits": hits[:8],
                     "aim_srcs": sorted(set(SRC.findall(t)))[:8]})

rows.sort(key=lambda r: (-len(r["aim21"]), -r["aim_mentions"], r["path"]))
json.dump(rows, open("02_dashboards/_build/_aim_refresh/inventory.json", "w", encoding="utf-8"), indent=1)
print("CANDIDATE PAGES:", len(rows))
for r in rows:
    print("=" * 4, r["path"], f'{r["bytes"]:,}', "aimx", r["aim_mentions"], "names", len(r["aim21"]))
    if r["cat7"]:
        print("     cat7:", r["cat7"][:7])
    if r["aim_srcs"]:
        print("     refs:", r["aim_srcs"])
    seen = set()
    for h in r["hits"]:
        if h[:60] in seen:
            continue
        seen.add(h[:60])
        print("     >", h[:168])
