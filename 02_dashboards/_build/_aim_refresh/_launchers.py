import os, re, sys
sys.stdout.reconfigure(encoding="utf-8")
os.chdir(r"C:\Users\jerom\Desktop\claude\ISZE")

PAGES = [e["page"] for e in __import__("json").load(open("02_dashboards/_build/_aim_refresh/pages.json", encoding="utf-8"))]

print("### LAUNCHERS: name vs what it opens")
for rel in PAGES:
    if not os.path.exists(rel):
        print("missing page", rel); continue
    d = os.path.dirname(rel)
    base = os.path.basename(rel)
    cands = [f for f in os.listdir(d) if f.lower().startswith("open_") and f.lower().endswith(".cmd")]
    hits = []
    for c in cands:
        raw = open(os.path.join(d, c), "rb").read()
        txt = raw.decode("ascii", errors="ignore")
        crlf = raw.count(b"\r\n")
        lf = raw.count(b"\n")
        opens = base in txt
        if opens:
            # does the launcher name match the file it opens?
            stem = c[5:-4].lower()
            namematch = stem in base.lower() or base.lower().startswith(stem)
            hits.append((c, crlf, lf, namematch, " ".join(txt.split())))
    print(f"--- {rel}")
    if not hits:
        print("      NO launcher opens this page")
    for c, crlf, lf, nm, body in hits:
        flag = []
        if lf and crlf != lf:
            flag.append("MIXED/LF endings")
        if not nm:
            flag.append("NAME MISMATCH")
        print(f"      {c}  crlf={crlf} lf={lf}  {'OK' if not flag else ' / '.join(flag)}")
        print(f"          {body[:120]}")
