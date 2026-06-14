"""
Fast diagnostic — fetches 1 high-revenue Isuzu PN per failing site,
captures body text + page title, and reports what each site shows.

Tells us: anti-bot? selector drift? no-Isuzu-coverage?

Run: python diagnose_scrapers.py
"""
from __future__ import annotations
import re, sys
from pathlib import Path
from playwright.sync_api import sync_playwright, TimeoutError as PwTimeout

SCRIPT_DIR = Path(__file__).parent
DIAG_DIR = SCRIPT_DIR / "_diag"
DIAG_DIR.mkdir(exist_ok=True)

# Top-revenue PNs from v3. 8983767550 (brake rotor) is the most universal —
# every European AM site should carry brake discs. If they don't, anti-bot.
TEST_PNS = ["8983767550", "8975056801"]  # ROTOR DISC BRK FRT, PAD KIT CALIPER FRT

SITES = [
    ("AD_EU",  "https://www.autodoc.eu/spares-search?keyword={pn}",                  "en-GB", "Europe/London"),
    ("AD_DE",  "https://www.autodoc.de/spares-search?keyword={pn}",                  "de-DE", "Europe/Berlin"),
    ("AD_UK",  "https://www.autodoc.co.uk/spares-search?keyword={pn}",               "en-GB", "Europe/London"),  # control
    ("MA",     "https://www.mister-auto.com/en/parts/search/?query={pn}",            "en-GB", "Europe/London"),
    ("OSC",    "https://www.oscaro.com/en/parts/search?query={pn}",                  "fr-FR", "Europe/Paris"),
    ("MEK",    "https://www.mekonomen.se/catalogsearch/result/?q={pn}",              "sv-SE", "Europe/Stockholm"),
]


def classify(title: str, body: str) -> str:
    t = title.lower()
    b = body.lower()
    blockers = ["access denied", "blocked", "cloudflare", "are you human", "captcha", "robot", "forbidden", "checking your browser"]
    if any(k in t or k in b[:3000] for k in blockers):
        return "BLOCKED (anti-bot)"
    if re.search(r"\b0\s+results?\b|no results|aucun résultat|keine ergebnisse|inga produkter|inga resultat", b, re.I):
        return "GENUINELY no results"
    if re.search(r"\d+\s+results?\s+found|\d+\s+produits|\d+\s+artikel|\d+\s+produkter", b, re.I):
        return "HAS results (selector drift?)"
    if re.search(r"€\s*\d|\d+[,.]\d{2}\s*€|£\s*\d|\d+\s*kr", b):
        return "HAS prices (selector drift?)"
    return f"UNCLEAR — body {len(b)} chars"


def run():
    with sync_playwright() as pw:
        browser = pw.chromium.launch(
            headless=True,
            args=["--no-sandbox", "--disable-blink-features=AutomationControlled"],
        )
        results = []
        for site, tpl, loc, tz in SITES:
            ctx = browser.new_context(
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
                viewport={"width": 1366, "height": 768},
                locale=loc,
                timezone_id=tz,
            )
            page = ctx.new_page()
            page.set_default_timeout(25_000)
            for pn in TEST_PNS:
                url = tpl.format(pn=pn)
                print(f"[{site}] PN={pn} -> {url}", flush=True)
                try:
                    page.goto(url, wait_until="domcontentloaded", timeout=25_000)
                    try:
                        page.wait_for_load_state("networkidle", timeout=8_000)
                    except PwTimeout:
                        pass
                    body = page.inner_text("body")[:8000]
                    title = page.title()
                    verdict = classify(title, body)
                    (DIAG_DIR / f"{site}_{pn}.txt").write_text(
                        f"URL: {url}\nTITLE: {title}\nVERDICT: {verdict}\n\n--- BODY (first 8000 chars) ---\n{body}",
                        encoding="utf-8",
                    )
                    print(f"  -> {verdict}", flush=True)
                    results.append((site, pn, verdict, title[:80]))
                except Exception as e:
                    err = str(e)[:200]
                    print(f"  -> ERROR: {err}", flush=True)
                    results.append((site, pn, f"ERROR: {err}", ""))
            ctx.close()
        browser.close()

    print("\n" + "=" * 80)
    print("SUMMARY")
    print("=" * 80)
    print(f"{'SITE':<8} {'PN':<12} {'VERDICT':<35} TITLE")
    for site, pn, verdict, title in results:
        print(f"{site:<8} {pn:<12} {verdict:<35} {title}")


if __name__ == "__main__":
    run()
