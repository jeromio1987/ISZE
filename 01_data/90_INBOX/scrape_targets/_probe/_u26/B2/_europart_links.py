import io, re, sys
from pathlib import Path
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
WT = Path(r"C:\Users\jerom\Desktop\claude\_worktrees\ISZE_u26")
sys.path.insert(0, str(WT / "04_tools" / "delegation" / "parsers"))
from fetch_polite import PoliteFetcher
f = PoliteFetcher(offline=True)
html = f.get("https://www.europart.net/")
print("bytes:", len(html) if html else None)
for pat in [r'href="([^"]*(?:search|suche|product|shop)[^"]*)"', r'action="([^"]+)"', r'name="([^"]*(?:search|query|q)[^"]*)"']:
    hits = sorted(set(re.findall(pat, html or "", re.I)))[:20]
    print(pat[:30], "->", hits)
