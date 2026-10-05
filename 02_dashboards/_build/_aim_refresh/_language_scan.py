import os, re, sys, json
sys.stdout.reconfigure(encoding="utf-8")
os.chdir(r"C:\Users\jerom\Desktop\claude\ISZE")

PAGES = [e["page"] for e in json.load(open("02_dashboards/_build/_aim_refresh/pages.json", encoding="utf-8"))]
PAGES.append("02_dashboards/sales/AIM_Dashboard_CY2026.html")

BAD = [
    (r"rebuilt by", "rebuilt by"),
    (r"changelog", "changelog"),
    (r"agent build note", "agent build note"),
    (r"Mode A", "Mode A"),
    (r"Mode B", "Mode B"),
    (r"\bsell-?out\b", "sell-out"),
    (r"\bstreet\b", "street"),
    (r"\bwallet\b", "wallet"),
    (r"\bIML v7\b", "IML v7"),
    (r"\bModel B\b", "Model B"),
    (r"PRISM lane", "PRISM lane"),
    (r"\bhardware PN\b", "hardware PN"),
    (r"\bBook B\b", "Book B"),
    (r"1\.785", "1.785"),
    (r"\bSPAR\b", "SPAR"),
    (r"ship-gate", "ship-gate"),
    (r"\bharness\b", "harness"),
    (r"do not edit", "do not edit"),
]

print("### shared-language / build-note scan")
for rel in PAGES:
    if not os.path.exists(rel):
        print("missing", rel); continue
    raw = open(rel, encoding="utf-8", errors="ignore").read()
    # ignore script/style bodies for the language scan (library code has none of these but be safe)
    vis = re.sub(r"<script[\s\S]*?</script>", " ", raw)
    vis = re.sub(r"<style[\s\S]*?</style>", " ", vis)
    hits = []
    for pat, label in BAD:
        n = len(re.findall(pat, vis, re.I))
        if n:
            m = re.search(pat, vis, re.I)
            ctx = " ".join(re.sub(r"<[^>]+>", " ", vis[max(0, m.start() - 90): m.start() + 90]).split())
            hits.append((label, n, ctx[:130]))
    # build-note style comments in the HTML (outside scripts)
    notes = re.findall(r"<!--[^>]{0,200}?(?:rebuilt|build|agent|generated|todo|fixme)[^>]{0,200}?-->", raw, re.I)
    print(f"--- {rel}")
    if not hits and not notes:
        print("      clean")
    for label, n, ctx in hits:
        print(f"      {label} x{n}: {ctx}")
    for nt in notes[:3]:
        print("      HTML comment:", " ".join(nt.split())[:150])
