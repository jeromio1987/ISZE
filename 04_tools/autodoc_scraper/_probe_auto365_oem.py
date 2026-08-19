"""One-shot probe: do Auto 365 product pages carry Isuzu OEM PNs?"""
from __future__ import annotations

import json
import re
from pathlib import Path

from bs4 import BeautifulSoup
from curl_cffi import requests as creq

# 10-digit Isuzu-like: typically 7/8/89... plus other 10-digit OEM PNs
PN_RE = re.compile(r"\b([789]\d{9}|0\d{9}|\d{10})\b")
# Hebrew / English labels that might sit next to an OEM number
LABEL_RE = re.compile(
    r"(oem|mpn|sku|part[\s_-]?no|part[\s_-]?number|מקט|מספר[\s_-]?חלק|"
    r"מספר[\s_-]?יצרן|מקורי|קוד[\s_-]?חלק|catalog)",
    re.I,
)

URLS = [
    "https://www.auto365.co.il/product/5108/",
    "https://www.auto365.co.il/product/5128/",
    "https://www.auto365.co.il/product/5134/",
    "https://www.auto365.co.il/product/9444/",
    "https://www.auto365.co.il/product/19740/",
    "https://www.auto365.co.il/product/27563/",
    "https://www.auto365.co.il/product/28585/",
    "https://www.auto365.co.il/product/29547/",
]

OUT = Path(__file__).parent / "_probe_auto365_oem.json"


def extract(html: str, url: str) -> dict:
    soup = BeautifulSoup(html, "html.parser")
    title = (soup.title.get_text(strip=True) if soup.title else "")[:200]
    h1 = soup.select_one("h1")
    h1t = h1.get_text(strip=True) if h1 else ""

    ids = {}
    for sel in [
        "[itemprop=sku]", "[itemprop=mpn]", "[itemprop=productID]",
        ".sku", ".mpn", ".product-sku", ".product-code", ".catalog-number",
        "[class*=sku]", "[class*=mpn]", "[class*=oem]", "[id*=sku]",
    ]:
        els = soup.select(sel)
        if els:
            ids[sel] = [e.get_text(" ", strip=True)[:120] for e in els[:6]]

    ld = []
    for tag in soup.find_all("script", type="application/ld+json"):
        try:
            ld.append(json.loads(tag.string or "{}"))
        except Exception:
            ld.append({"_raw": (tag.string or "")[:400]})

    meta = {}
    for m in soup.find_all("meta"):
        name = (m.get("property") or m.get("name") or "").lower()
        if any(k in name for k in ("sku", "mpn", "product", "price", "title")):
            meta[name] = (m.get("content") or "")[:160]

    # visible label-ish snippets
    labels = []
    text = soup.get_text("\n", strip=True)
    for i, line in enumerate(text.splitlines()):
        if LABEL_RE.search(line) and len(line) < 180:
            labels.append(line.strip())
            if len(labels) >= 12:
                break

    pns = sorted(set(PN_RE.findall(html)))
    # drop obvious years / product ids in URL
    url_id = re.search(r"/product/(\d+)", url)
    pid = url_id.group(1) if url_id else ""
    pns10 = [p for p in pns if len(p) == 10]
    isuzu_like = [p for p in pns10 if p[0] in "78" or p.startswith("89")]
    contexts = []
    for p in pns10[:12]:
        m = re.search(re.escape(p), html)
        if not m:
            continue
        a, b = max(0, m.start() - 80), min(len(html), m.end() + 80)
        contexts.append({"pn": p, "ctx": re.sub(r"\s+", " ", html[a:b])[:220]})

    # JSON blobs
    json_hits = []
    for m in re.finditer(r"\{[^{}]{20,800}\}", html):
        chunk = m.group(0)
        if re.search(r"mpn|oem|sku|partNumber|part_number", chunk, re.I):
            json_hits.append(chunk[:400])
            if len(json_hits) >= 8:
                break

    return {
        "url": url,
        "status_ok": True,
        "title": title,
        "h1": h1t,
        "product_id": pid,
        "html_bytes": len(html),
        "ld_json": ld[:4],
        "meta": meta,
        "id_selectors": ids,
        "label_lines": labels,
        "pn10_in_html": pns10[:30],
        "isuzu_like_7_8_89": isuzu_like,
        "pn_contexts": contexts,
        "json_field_hits": json_hits,
    }


def main():
    results = []
    for url in URLS:
        print("GET", url)
        try:
            r = creq.get(url, impersonate="chrome", timeout=30, headers={
                "Accept-Language": "he-IL,he;q=0.9,en;q=0.8",
            })
            rec = extract(r.text, url)
            rec["http_status"] = r.status_code
            rec["final_url"] = str(r.url)
        except Exception as e:
            rec = {"url": url, "status_ok": False, "error": str(e)}
        results.append(rec)
        h1a = (rec.get("h1") or "").encode("ascii", "replace").decode("ascii")[:60]
        print("  status", rec.get("http_status"), "isuzu", rec.get("isuzu_like_7_8_89"),
              "pn10", rec.get("pn10_in_html"), "h1", h1a)

    OUT.write_text(json.dumps(results, ensure_ascii=False, indent=2), encoding="utf-8")
    print("Wrote", OUT)


if __name__ == "__main__":
    main()
