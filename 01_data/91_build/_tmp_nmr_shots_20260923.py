"""Paint check for the NMR disclosure: capture the two places a reader sees it.

  N1 the visible limits card, element-clipped, showing the tonnage-weights sentence
  N2 the limits line itself, tight crop, legible
  N3 the folded evidence table, opened, first rows - the 5.5 t band row
  N4 the full page, to confirm nothing else broke

Screenshots are taken from the FILE over file://, one PNG per claim, all read afterwards.
"""
from __future__ import annotations

import json
from pathlib import Path

from playwright.sync_api import sync_playwright

ROOT = Path(r"C:\Users\jerom\Desktop\claude\ISZE")
HTML = ROOT / "02_dashboards" / "sales" / "ISZE_PMS_Family_Evolution_v2.html"
OUT = ROOT / "02_dashboards" / "sales" / "_qa_nmr_20260923"
CHROME = r"C:\Program Files\Google\Chrome\Application\chrome.exe"

taken: list[Path] = []


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    with sync_playwright() as pw:
        br = pw.chromium.launch(executable_path=CHROME if Path(CHROME).is_file() else None)
        pg = br.new_page(viewport={"width": 1440, "height": 1100}, device_scale_factor=1)
        errs: list[str] = []
        pg.on("pageerror", lambda e: errs.append(str(e)))
        pg.goto(HTML.as_uri(), wait_until="load")
        pg.wait_for_timeout(2500)

        def take(name: str, locator) -> None:
            locator.scroll_into_view_if_needed(timeout=10000)
            pg.wait_for_timeout(500)
            p = OUT / f"{name}.png"
            locator.screenshot(path=str(p))
            taken.append(p)
            print(f"  took {name}.png  {p.stat().st_size:,} bytes")

        pg.screenshot(path=str(OUT / "N1_full_page.png"), full_page=True)
        taken.append(OUT / "N1_full_page.png")
        print(f"  took N1_full_page.png  {(OUT / 'N1_full_page.png').stat().st_size:,} bytes")

        # the limits card's tonnage-weights line
        take("N2_weights_limitation", pg.locator("li", has_text="tonnage weights come from").first)
        # the whole card the limitations live in: find it from the line's own ancestors
        card = pg.evaluate("""() => {
            const li = Array.from(document.querySelectorAll('li'))
              .find(e => e.innerText.indexOf('tonnage weights come from') >= 0);
            if (!li) return null;
            let n = li.parentElement;
            while (n && n !== document.body) {
              if (n.id) return n.id;
              n = n.parentElement;
            }
            return null;
        }""")
        print(f"  the limitations card container id: {card!r}")
        if card:
            take("N3_limits_card", pg.locator(f"#{card}").first)
        # the evidence table, opened
        pg.evaluate("() => document.querySelectorAll('details').forEach(d => d.open = true)")
        pg.wait_for_timeout(800)
        take("N4_evidence_table", pg.locator("#evbox table").first)

        # what the two lines actually say, from the live DOM
        text = pg.evaluate("""() => {
            const out = {};
            const li = Array.from(document.querySelectorAll('li'))
              .find(e => e.innerText.indexOf('tonnage weights come from') >= 0);
            out.limits = li ? li.innerText.replace(/\\s+/g,' ').trim() : null;
            const tb = document.querySelector('#evbox table');
            out.evidenceRows = tb ? Array.from(tb.querySelectorAll('tbody tr'))
              .map(tr => Array.from(tr.querySelectorAll('td'))
                .map(td => td.innerText.trim()).join(' | ')) : null;
            out.interimVisible = document.body.innerText.indexOf('INTERIM, NOT SETTLED') >= 0;
            out.agreeGone = document.body.innerText.indexOf('two sources that agree') < 0;
            return out;
        }""")
        (OUT / "visible_text.json").write_text(json.dumps({"text": text, "errors": errs}, indent=1),
                                               encoding="utf-8")
        print()
        print("LIMITS LINE AS RENDERED:")
        print("  ", text["limits"])
        print()
        print("EVIDENCE TABLE ROWS AS RENDERED:")
        for r in text["evidenceRows"] or []:
            print("  ", r)
        print()
        print("INTERIM wording visible on the page :", text["interimVisible"])
        print("old 'two sources that agree' gone    :", text["agreeGone"])
        print("page errors:", errs or "none")
        br.close()
    print()
    print(f"SCREENSHOTS TAKEN: {len(taken)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
