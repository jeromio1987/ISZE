import base64
import json
import re
from pathlib import Path

src = Path(
    r"C:\Users\jerom\Desktop\claude\ISZE\01_data\90_INBOX\_eq_hit_overnight_scraper_20260919.js"
).read_text(encoding="utf-8")
# ASCII-safe: replace fancy dashes / non-ascii in comments
src = src.replace("\u2014", "-").replace("\u2013", "-")
src = re.sub(r"[^\x00-\x7F]", "?", src)
src = re.sub(r'"scraper_v2_ok";\s*$', "", src).rstrip() + "\n"
b64 = base64.b64encode(src.encode("ascii")).decode("ascii")
expr = (
    "(function(){try{eval(atob("
    + json.dumps(b64)
    + ")); return typeof window.__eqDoubtLookup;}catch(e){return 'ERR:'+e.message;}})()"
)
out = Path(r"C:\Users\jerom\Desktop\claude\ISZE\01_data\91_build\eq_oneshot_ascii.js")
out.write_text(expr, encoding="utf-8")
print("ascii_src", len(src), "expr", len(expr), "nonascii", any(ord(c) > 127 for c in src))
