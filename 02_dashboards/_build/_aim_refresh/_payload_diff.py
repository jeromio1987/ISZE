import os, re, sys, json
sys.stdout.reconfigure(encoding="utf-8")
os.chdir(r"C:\Users\jerom\Desktop\claude\ISZE")
B = "02_dashboards/_build/_aim_refresh/before/"

# pages whose payload is a JSON blob: compare them key by key at the level that matters
PAIR = {
    "pricing/ISZE_Pricing_Revision_AIM_Source.html": "pricing_dashboard_data.json",
    "pricing/ISZE_Pricing_Revision_AIM_Source_PROTOTYPE_AllDB.html": "pricing_dashboard_data.json",
}


def biggest_json(path):
    t = open(path, encoding="utf-8", errors="ignore").read()
    best = None
    for m in re.finditer(r'<script[^>]*type="application/json"[^>]*>(.*?)</script>', t, re.S):
        s = m.group(1)
        if best is None or len(s) > len(best):
            best = s
    return best


def summarise(blob):
    d = json.loads(blob)
    out = {}
    for k, v in d.items():
        if isinstance(v, list):
            out[k] = f"list[{len(v)}]"
        elif isinstance(v, dict):
            out[k] = f"dict[{len(v)}] " + ",".join(list(v)[:6])
        else:
            out[k] = v
    return out


for rel in PAIR:
    a, b = "02_dashboards/" + rel, B + rel.replace("/", "__")
    ja, jb = biggest_json(a), biggest_json(b)
    sa, sb = summarise(ja), summarise(jb)
    print("=" * 5, rel)
    for k in sorted(set(sa) | set(sb)):
        if sa.get(k) != sb.get(k):
            print(f"    {k}: before={sb.get(k)}  after={sa.get(k)}")
