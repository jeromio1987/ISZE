"""Israel HTML/API probe — write results to JSON."""
import json
import re
from pathlib import Path

import requests

url = "https://mr.gov.il/ilgstorefront/he/rss/Tenders.xml"
r = requests.get(url, timeout=60)
text = r.text
out = {
    "status": r.status_code,
    "bytes": len(r.content),
    "ctype": r.headers.get("Content-Type"),
    "title": None,
    "scripts": [],
    "apiish": [],
}
m = re.search(r"<title>([^<]+)", text, re.I)
if m:
    out["title"] = m.group(1)
out["scripts"] = re.findall(r"<script[^>]+src=[\"']([^\"']+)", text, re.I)[:20]
out["apiish"] = re.findall(r"https?://[^\"'\s]{10,120}", text)[:30]
# look for embedded JSON arrays
out["has_ng"] = "ng-app" in text or "angular" in text.lower()
out["snippet"] = text[text.find("<body"): text.find("<body") + 400] if "<body" in text else text[:400]
Path(__file__).with_name("_tmp_il_html_probe.json").write_text(
    json.dumps(out, indent=2, ensure_ascii=False), encoding="utf-8"
)
print("wrote probe", out["status"], out["bytes"], out["title"])
