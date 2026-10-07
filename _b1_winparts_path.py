import re
from pathlib import Path

import sys
sys.path.insert(0, "04_tools/delegation/parsers")
from fetch_polite import PoliteFetcher, ConsentRefused   # noqa: E402

B1 = Path("01_data/90_INBOX/scrape_targets/_probe/_u26/B1")
PAGES = B1 / "pages"
PRICE = re.compile(r"\d{1,4}[.,]\d{2}\s?€|€\s?\d{1,4}[.,]\d{2}")
f = PoliteFetcher()
for pn in ["8982447940", "8975546610", "8982705240"]:
    for path in [f"https://www.winparts.es/piezas-de-auto/{pn}",
                 f"https://www.winparts.es/piezas-de-auto/c0/{pn}.html"]:
        try:
            h = f.get(path)
        except ConsentRefused as e:
            print(f"REFUSED {path} ({e})")
            continue
        if not h:
            print(f"err {path}")
            continue
        pr = PRICE.findall(h)
        print(f"{path}\n   {len(h):,}B prices={len(pr)}{pr[:5]} pn={pn in h} "
              f"isuzu={h.lower().count('isuzu')}")
        name = re.sub(r"[^a-z0-9]+", "_", path.split("winparts.es/")[-1].lower())[:50]
        (PAGES / f"winparts_es__{name}.html").write_text(h, encoding="utf-8", errors="replace")
print(f.stats)
