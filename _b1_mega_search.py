import re
from pathlib import Path

B1 = Path("01_data/90_INBOX/scrape_targets/_probe/_u26/B1/pages")
h = (B1 / "www.megapecas.pt__home.html").read_text(encoding="utf-8", errors="replace")
print("bytes", len(h))
for needle in ["ProductListForm", "referencia", "Refer", "pesquisa", "Pesquisa", "search",
               "Search", "searchForm", "partnumber", "clientpart", "ClientPart", "q="]:
    idxs = [m.start() for m in re.finditer(re.escape(needle), h)]
    print(f"\n### {needle}: {len(idxs)} hits")
    for i in idxs[:3]:
        print("   ", re.sub(r"\s+", " ", h[max(0, i - 160): i + 160]))
