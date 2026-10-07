import subprocess
import sys
from pathlib import Path

GATE = Path("04_tools/autodoc_scraper/check_scrape_consent.py")
CASES = [
    ("https://www.oscaro.pt", "/pt/search?q=8982447940&x=1"),
    ("https://www.oscaro.pt", "/search?q=8982447940"),
    ("https://www.oscaro.pt", "/pt/search?q=8982447940"),
    ("https://www.winparts.es", "/search?q=8982447940"),
    ("https://www.winparts.es", "/piezas-de-auto/8982447940"),
    ("https://megapecas.pt", "/pt/produtos?Search=8982447940"),
    ("https://megapecas.pt", "/pt/ProductListForm"),
    ("https://www.b-parts.com", "/pt/pecas-auto/"),
    ("https://autocenter.pt", "/?s=8982447940&post_type=product"),
    ("https://www.pneubeato.com", "/travoes-ebc/isuzu/d-max"),
    ("https://www.motointegrator.pt", "/"),
    ("https://www.autoparts24.eu", "/search?q=8982447940"),
]
for base, path in CASES:
    p = subprocess.run([sys.executable, str(GATE), "--url", base, "--path", path],
                       capture_output=True, text=True)
    print(f"rc={p.returncode}  {base}{path}   -> {(p.stdout or '').strip()[:70]}")
