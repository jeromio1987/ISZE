# -*- coding: utf-8 -*-
"""B1 phase 13 — classify WHY each non-allowed host failed, so the report is exact:
DNS failure / connect error / HTTP status on robots.txt / bot-check page.
Also probes the paths that were robots-blocked, to record the verdict precisely.
"""
from __future__ import annotations

import csv
import re
import sys
from pathlib import Path

import requests

for _s in (sys.stdout, sys.stderr):
    if _s is not None and hasattr(_s, "reconfigure"):
        try:
            _s.reconfigure(encoding="utf-8", errors="replace")
        except Exception:
            pass

UA = "ISZE-parts-research/1.0 (+aftersales analytics; contact via IML)"
HERE = Path(__file__).resolve().parent
for c in [HERE, *HERE.parents]:
    if (c / "04_tools" / "autodoc_scraper" / "check_scrape_consent.py").exists():
        ISZE = c
        break
B1 = ISZE / "01_data" / "90_INBOX" / "scrape_targets" / "_probe" / "_u26" / "B1"

# hosts that came back "unreachable" and matter for the PT conclusion
HOSTS = [
    "https://www.norauto.pt", "https://www.olx.pt", "https://www.b-parts.pt",
    "https://www.pecasauto.pt", "https://www.sidat.pt", "https://www.jcparts.pt",
    "https://www.endado.com", "https://www.skruvat.com", "https://www.recambiosviaweb.com",
    "https://www.autodoc.pt", "https://www.autodoc.co.uk", "https://www.oscaro.com",
    "https://www.trodo.com", "https://www.euautoparts.pt", "https://www.alvadi.pt",
    "https://www.winparts.pt", "https://www.auto5.pt", "https://www.blacklotus.pt",
    "https://www.jap.pt", "https://www.bomcar.pt", "https://www.ipecas.pt",
]


def classify(base: str) -> tuple[str, str]:
    try:
        r = requests.get(base + "/robots.txt", timeout=25, headers={"User-Agent": UA},
                         allow_redirects=True)
    except requests.exceptions.SSLError as e:
        return "SSL error", str(e)[:110]
    except requests.exceptions.ConnectionError as e:
        msg = str(e)
        if "Name or service not known" in msg or "getaddrinfo" in msg or "No address" in msg:
            return "DNS failure", msg[:110]
        return "connection error", msg[:110]
    except requests.exceptions.Timeout:
        return "timeout", "no response in 25 s"
    except Exception as e:                                       # noqa: BLE001
        return "error", str(e)[:110]
    body = r.text[:400]
    challenge = bool(re.search(r"(?i)just a moment|cloudflare|cf-chl|captcha|turnstile|"
                               r"checking your browser|access denied|attention required",
                               r.text[:4000]))
    return f"HTTP {r.status_code}", ("BOT-CHECK page" if challenge else "") + " | " + \
        re.sub(r"\s+", " ", body)[:90]


def main() -> int:
    out = B1 / "why_failed.csv"
    with out.open("w", encoding="utf-8", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["host", "robots_status", "detail"])
        for base in HOSTS:
            st, det = classify(base)
            print(f"  {base:<38} {st:<16} {det[:80]}")
            w.writerow([base.split("//", 1)[-1], st, det])
    print(f"\nwrote {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
