import os, json, re, sys

ROOT = r"C:\Users\jerom\Desktop\claude\ISZE"
SKIP_DIRS = {".git", "node_modules", "__pycache__", "07_deploy", ".venv", "venv"}
pat = re.compile(rb'"pass"\s*:\s*(143|116)\b|143\s*pass|Pass\s*116|143/0/0|143 passed')

hits = []
for dirpath, dirnames, filenames in os.walk(ROOT):
    dirnames[:] = [d for d in dirnames if d not in SKIP_DIRS]
    for fn in filenames:
        if not fn.lower().endswith((".json", ".md", ".txt", ".csv")):
            continue
        p = os.path.join(dirpath, fn)
        try:
            if os.path.getsize(p) > 8 * 1024 * 1024:
                continue
            with open(p, "rb") as f:
                data = f.read()
        except Exception:
            continue
        if pat.search(data):
            try:
                with open(p, "r", encoding="utf-8", errors="replace") as f:
                    txt = f.read()
            except Exception:
                txt = ""
            snips = []
            for m in re.finditer(r'"pass"\s*:\s*(143|116)\b|143\s*pass|Pass\s*116|143/0/0|143 passed', txt):
                a = max(0, m.start() - 90)
                b = min(len(txt), m.end() + 90)
                snips.append(txt[a:b].replace("\n", " "))
                if len(snips) >= 3:
                    break
            hits.append((p, os.path.getsize(p), snips))

print("files:", len(hits))
for p, sz, snips in hits:
    print("-" * 100)
    print(p, f"({sz} bytes)")
    for s in snips:
        print("    ...", s)
