import re
import sys
from pathlib import Path

sys.path.insert(0, "04_tools/delegation/parsers")
from fetch_polite import PoliteFetcher   # noqa: E402

B1 = Path("01_data/90_INBOX/scrape_targets/_probe/_u26/B1")
f = PoliteFetcher()
for u in ["https://megapecas.pt/pt/marcas/isuzu"]:
    h = f.get(u)
    if not h:
        print("err", u)
        continue
    (B1 / "pages" / "megapecas__marca_isuzu.html").write_text(h, encoding="utf-8", errors="replace")
    print(len(h))
    pr = re.findall(r"\d{1,4}[.,]\d{2}\s?€", h)
    print("prices", len(pr), pr[:8])
    print("iva", bool(re.search(r"(?i)iva", h)))
    for m in sorted(set(re.findall(r'href="([^"]*isuzu[^"]*)"', h, re.I)))[:20]:
        print(" ", m)
print(f.stats)
