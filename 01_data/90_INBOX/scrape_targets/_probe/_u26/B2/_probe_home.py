# -*- coding: utf-8 -*-
"""B2: fetch homepages of allowed hosts to locate their real search endpoint."""
from __future__ import annotations
import io, json, re, sys
from pathlib import Path
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
WT = Path(r"C:\Users\jerom\Desktop\claude\_worktrees\ISZE_u26")
sys.path.insert(0, str(WT / "04_tools" / "delegation" / "parsers"))
from fetch_polite import PoliteFetcher, ConsentRefused
HERE = Path(__file__).resolve().parent
HOMES = {
    "truckparts.pt": "https://www.truckparts.pt/",
    "sotecnica.pt": "https://www.sotecnica.pt/",
    "turbopecas.pt": "https://www.turbopecas.pt/",
    "b-parts.com": "https://www.b-parts.com/pt/",
    "pecauto.com": "https://www.pecauto.com/",
}
FORM_RE = re.compile(r"<form[^>]*>", re.I)
ACTION_RE = re.compile(r'action=["\']([^"\']+)', re.I)
INPUT_RE = re.compile(r'name=["\']([^"\']+)', re.I)
LINK_RE = re.compile(r'href=["\']([^"\']*(?:search|pesquisa|procur|recambio|peca|part)[^"\']*)', re.I)
f = PoliteFetcher()
res = {}
for host, url in HOMES.items():
    try:
        html = f.get(url)
    except ConsentRefused:
        print(host, "CONSENT REFUSED"); res[host] = {"verdict":"consent_refused"}; continue
    if not html:
        print(host, "NO BODY"); res[host] = {"verdict":"no_body"}; continue
    forms = FORM_RE.findall(html)
    actions = ACTION_RE.findall(html)
    names = INPUT_RE.findall(html)
    links = sorted(set(LINK_RE.findall(html)))[:15]
    title = re.search(r"<title[^>]*>(.*?)</title>", html, re.I|re.S)
    res[host] = {"url": url, "bytes": len(html), "title": (title.group(1).strip()[:90] if title else ""),
                 "forms": len(forms), "actions": actions[:6], "inputs": sorted(set(names))[:12], "links": links}
    print(f"== {host} bytes={len(html)} title={res[host]['title']!r}")
    print("   actions:", actions[:6])
    print("   inputs :", sorted(set(names))[:12])
    print("   links  :", links)
(HERE / "_homepages.json").write_text(json.dumps(res, indent=1, ensure_ascii=False), encoding="utf-8")
