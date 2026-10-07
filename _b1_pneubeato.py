import re
from pathlib import Path

p = Path("01_data/90_INBOX/scrape_targets/_probe/_u26/B1/pages/pneubeato__product_probe.html")
h = p.read_text(encoding="utf-8", errors="replace")
print("bytes", len(h))
print("product links:", sorted(set(re.findall(r'href="([^"]*(?:produto|travoes|discos)[^"]*)"', h, re.I)))[:12])
print("price-ish json keys:", sorted(set(re.findall(r'"(price|preco|preço|amount)"', h, re.I)))[:10])
print("scripts with api/ajax:", sorted(set(re.findall(r'(?:url|src|href)="([^"]*(?:api|ajax|json)[^"]*)"', h, re.I)))[:12])
i = h.lower().find("isuzu")
print("\ncontext around first isuzu:", re.sub(r"\s+", " ", h[max(0, i - 250): i + 250]))
