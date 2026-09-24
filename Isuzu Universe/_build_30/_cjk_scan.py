import os, re, sys, zipfile, time
sys.stdout.reconfigure(encoding="utf-8")
import fitz

CJK = re.compile(r"[\u3000-\u9fff\uff00-\uffef]")
CUT = time.time() - 2 * 86400

def text_of(p):
    low = p.lower()
    try:
        if low.endswith(".pdf"):
            return "".join(pg.get_text() for pg in fitz.open(p))
        if low.endswith((".md", ".txt", ".html", ".csv", ".json", ".cmd", ".py")):
            return open(p, encoding="utf-8", errors="replace").read()
        if low.endswith((".pptx", ".xlsx", ".docx")):
            z = zipfile.ZipFile(p)
            return "".join(z.read(n).decode("utf-8", "replace")
                           for n in z.namelist() if n.endswith(".xml"))
    except Exception:
        return None
    return None

roots = [".", os.path.join("..", "01_data", "90_INBOX")]
hits = []
for root in roots:
    for dirpath, dirs, files in os.walk(root):
        if any(x in dirpath for x in ("_qa", "figures", "node_modules", "05_AIM_Universe",
                                      "\\dist", "\\tests", "_backsafe")):
            continue
        for f in files:
            p = os.path.join(dirpath, f)
            try:
                if os.path.getmtime(p) < CUT:
                    continue
            except OSError:
                continue
            t = text_of(p)
            if not t:
                continue
            n = len(CJK.findall(t))
            if n:
                m = CJK.search(t)
                hits.append((n, p, t[max(0, m.start() - 70):m.start() + 50].replace("\n", " | ")))

hits.sort(reverse=True)
print("files modified in the last 48 hours carrying CJK:")
for n, p, s in hits[:30]:
    print(f"  CJK {n:6d}  {p}")
    print(f"            ...{s}...")
if not hits:
    print("  none found")
