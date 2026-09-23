import json, re, sys
sys.stdout.reconfigure(encoding="utf-8")
h = open("ISUZU_UNIVERSE_3_0_SHOWCASE.html", encoding="utf-8").read()
m = re.search(r'<script id="universe-data" type="application/json">(.*?)</script>', h, re.S)
d = json.loads(m.group(1))

print("== chapters ==")
print(json.dumps(d["chapters"][:4], indent=1)[:900])
print("... total", len(d["chapters"]))

print("\n== paper entry shape ==")
e = d["paper"][4]
print(json.dumps(e, indent=1)[:700])

print("\n== which keys does every paper entry carry? ==")
keys = set()
for p in d["paper"]:
    keys |= set(p.keys())
print(sorted(keys))

print("\n== figures ==")
ks = list(d["figures"].keys())
print("count", len(ks), "sample key", ks[0])
print(json.dumps(d["figures"][ks[0]], indent=1)[:500])

print("\n== sources sample ==")
print(json.dumps(d["sources"]["V"], indent=1)[:400])

print("\n== where '80-page' appears ==")
for mm in re.finditer(r"80-page", h):
    print("  ...", h[max(0, mm.start() - 160):mm.start() + 80].replace("\n", " "))

print("\n== product keys and their V refs ==")
for k, v in d["products"].items():
    print(f"  {k:8} {v.get('refs')}")
