import json, re, sys
sys.stdout.reconfigure(encoding="utf-8")
h = open("ISUZU_UNIVERSE_3_0_SHOWCASE.html", encoding="utf-8").read()
m = re.search(r'<script id="universe-data" type="application/json">(.*?)</script>', h, re.S)
d = json.loads(m.group(1))
print("top keys:", list(d.keys()))
for k, v in d.items():
    print("  ", k, type(v).__name__, len(v) if hasattr(v, "__len__") else "")
print()
print("paper entries:", len(d.get("paper", [])))
if d.get("paper"):
    print("  first:", json.dumps(d["paper"][0])[:300])
    print("  last :", json.dumps(d["paper"][-1])[:300])
print("sources:", list(d.get("sources", {}).keys()))
print("products:", list(d.get("products", {}).keys()))
print()
# where does it reference the paper?
for pat in ["80-page", "80 page", "pp. ", "V:"]:
    hits = [mm.start() for mm in re.finditer(re.escape(pat), h)]
    print(f"  '{pat}' occurrences in html: {len(hits)}")
mm = re.findall(r"V:(\d+)", h)
print("  V: refs found:", sorted(set(int(x) for x in mm)))
