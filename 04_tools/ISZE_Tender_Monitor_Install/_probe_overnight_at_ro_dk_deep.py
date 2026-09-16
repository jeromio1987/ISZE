"""Deep-dive AT USP / RO SEAP / DK for free machine feeds (overnight)."""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

import requests

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
HERE = Path(__file__).resolve().parent
s = requests.Session()
s.headers["User-Agent"] = "Mozilla/5.0 (compatible; ISZE-TenderMonitor/3.0)"

out = {}

# AT USP ausschreibungssuche page
r = s.get(
    "https://www.usp.gv.at/Portal.Node/usp/public/content/ausschreibungen/ausschreibungs_suche/inhalt.html",
    timeout=40,
)
out["at_status"] = r.status_code
out["at_bytes"] = len(r.content or b"")
text = r.text or ""
# find api/rss/json hints
hints = sorted(
    set(
        re.findall(
            r"https?://[^\s\"'<>]+(?:api|rss|atom|json|search|ausschreib)[^\s\"'<>]*",
            text,
            flags=re.I,
        )
    )
)[:40]
out["at_url_hints"] = hints
out["at_has_form"] = "form" in text.lower()
out["at_has_iframe"] = "iframe" in text.lower()
# known Austrian platforms often linked
for m in re.findall(r'href="([^"]+)"', text)[:80]:
    if any(x in m.lower() for x in ("ausschreib", "vergabe", "auftrag", "rss", "atom")):
        hints.append(m)
out["at_href_sample"] = sorted(set(hints))[:50]

# Try common AT aggregator endpoints
at_guesses = [
    "https://www.usp.gv.at/at.gv.bmdw.usp.core/Services/search",
    "https://www.usp.gv.at/at.gv.bmdw.usp.core/Services/Rss",
    "https://www.lieferanzeiger.at/",
    "https://www.auftrag.at/",
    "https://www.oeffentlichausschreiben.at/",
]
at_try = []
for u in at_guesses:
    try:
        rr = s.get(u, timeout=25, allow_redirects=True)
        at_try.append(
            {
                "url": u,
                "status": rr.status_code,
                "bytes": len(rr.content or b""),
                "final": str(rr.url)[:120],
                "rss": b"<item" in (rr.content or b"")[:8000].lower()
                or b"<entry" in (rr.content or b"")[:8000].lower(),
                "json": (rr.content or b"")[:1] in (b"{", b"["),
                "preview": (rr.content or b"")[:120].decode("utf-8", errors="replace"),
            }
        )
    except Exception as exc:
        at_try.append({"url": u, "error": str(exc)})
out["at_guesses"] = at_try

# RO e-licitatie — look for public notice list API
ro = s.get("https://www.e-licitatie.ro/pub", timeout=40)
out["ro_status"] = ro.status_code
out["ro_bytes"] = len(ro.content or b"")
ro_text = ro.text or ""
ro_apis = sorted(
    set(re.findall(r"/[a-zA-Z0-9_./-]*(?:api|notice|anunt|licitat)[a-zA-Z0-9_./-]*", ro_text, flags=re.I))
)[:40]
out["ro_path_hints"] = ro_apis
ro_guesses = [
    "https://www.e-licitatie.ro/api/public/notices",
    "https://www.e-licitatie.ro/pub/notices/c-notice",
    "https://www.e-licitatie.ro/pub/notices/c-contract-notice",
    "https://www.e-licitatie.ro/api-pub/NoticeCommon/GetCNoticeList/",
]
ro_try = []
for u in ro_guesses:
    try:
        rr = s.get(u, timeout=25)
        ro_try.append(
            {
                "url": u,
                "status": rr.status_code,
                "bytes": len(rr.content or b""),
                "json": (rr.content or b"")[:1] in (b"{", b"["),
                "preview": (rr.content or b"")[:150].decode("utf-8", errors="replace"),
            }
        )
    except Exception as exc:
        ro_try.append({"url": u, "error": str(exc)})
out["ro_guesses"] = ro_try

# DK — 902 bytes likely SPA; check content
dk = s.get("https://www.udbud.dk/", timeout=30)
out["dk_home_preview"] = (dk.content or b"")[:400].decode("utf-8", errors="replace")
dk_guesses = [
    "https://www.udbud.dk/api/procurement/search",
    "https://api.udbud.dk/search",
    "https://www.udbud.dk/Pages/Tenders/Search",
]
dk_try = []
for u in dk_guesses:
    try:
        rr = s.get(u, timeout=25)
        dk_try.append(
            {
                "url": u,
                "status": rr.status_code,
                "bytes": len(rr.content or b""),
                "preview": (rr.content or b"")[:120].decode("utf-8", errors="replace"),
            }
        )
    except Exception as exc:
        dk_try.append({"url": u, "error": str(exc)})
out["dk_guesses"] = dk_try

path = HERE / "_probe_overnight_at_ro_dk_deep.json"
path.write_text(json.dumps(out, indent=2, ensure_ascii=False), encoding="utf-8")
print(json.dumps({k: out[k] for k in out if k.endswith("_try") or k.endswith("guesses") or k in ("at_url_hints", "ro_path_hints", "dk_home_preview")}, indent=2, ensure_ascii=False)[:4000])
print("Wrote", path)
