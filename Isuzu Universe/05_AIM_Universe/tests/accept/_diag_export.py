"""Diagnostic: is the repeated export failure a product defect or a harness fault?

Repeats a minimal launch -> save -> export cycle several times in a row on the
same persistent profile, and prints what happens each time. Nothing here is an
acceptance check; it exists only to tell the two causes apart.
"""
from __future__ import annotations

import hashlib
import json
import os
import sys
import tempfile
import time
import urllib.parse
from pathlib import Path

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[2]
APP = ROOT / "dist" / "ISZE_AIM_Pricing_Decisions_v04_INTERNAL.html"
OUT = ROOT / "tests" / "accept" / "_out" / "diag"
CHROME = os.environ.get("CHROME_PATH", r"C:\Program Files\Google\Chrome\Application\chrome.exe")


def url(case_id: str, view: str) -> str:
    return APP.as_uri() + "#" + urllib.parse.urlencode(
        {"case": case_id, "view": view, "compare": "half"})


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    rows = []
    with sync_playwright() as p:
        # ---------------------------------------------------- check A -------
        # Does a page opened at a deep link ever adopt the saved revision by
        # itself? One profile, one launch, save then reopen the same case.
        profile = Path(tempfile.mkdtemp(prefix="aim_diag_reuse_"))
        row_a = {"check": "A", "question": "does a deep-linked page adopt the saved revision on its own?"}
        try:
            ctx = p.chromium.launch_persistent_context(
                user_data_dir=str(profile), headless=True, executable_path=CHROME,
                viewport={"width": 1440, "height": 900}, accept_downloads=True,
                args=["--allow-file-access-from-files"])
            pg = ctx.new_page()
            pg.goto(url("ITUK-PADS", "objectives"))
            pg.wait_for_function("() => !!window.AIMPricing", timeout=30000)
            pg.wait_for_timeout(300)
            pg.evaluate("() => { try { localStorage.clear(); } catch (e) {} }")
            pg.reload()
            pg.wait_for_function("() => !!window.AIMPricing", timeout=30000)
            # Select an alternative so the live scenario differs from the default.
            order = pg.evaluate("""() => {
              const D = window.AIMPricing.data, E = window.AIMPricing.engine;
              const c = D.cases.find(x => x.id === 'ITUK-PADS');
              return E.rankAlternatives(c, 'revenue', { payload: D }).ranked
                       .map(x => x.alternative.alternative_id);
            }""")
            pg.evaluate("(id) => window.AIMPricing.selectAlternative(id)", order[1])
            pg.wait_for_timeout(200)
            live_before = pg.evaluate("() => JSON.parse(JSON.stringify(window.AIMPricing.getScenario()))")
            pg.evaluate("([c]) => { location.hash = new URLSearchParams("
                        "{case:c, view:'action', compare:'half'}).toString(); }", ["ITUK-PADS"])
            pg.wait_for_timeout(300)
            pg.click("#save-case")
            pg.wait_for_timeout(400)
            saved = pg.evaluate("""() => { const c = window.AIMPricing.cases.load('ITUK-PADS');
              const r = c.revisions[c.revisions.length - 1];
              return { version: c.version, scenario: r.record.scenario }; }""")
            row_a["live_before_save"] = {k: live_before.get(k) for k in
                                         ["price_after", "quantity_after", "selected_alternative_id"]}
            row_a["saved_revision"] = {k: saved["scenario"].get(k) for k in
                                       ["price_after", "quantity_after", "selected_alternative_id"]}
            # Reopen the deep link in a brand new page inside the same context.
            pg2 = ctx.new_page()
            pg2.goto(url("ITUK-PADS", "action"))
            pg2.wait_for_function("() => !!window.AIMPricing", timeout=30000)
            pg2.wait_for_timeout(600)
            live_after = pg2.evaluate("() => JSON.parse(JSON.stringify(window.AIMPricing.getScenario()))")
            defaults = pg2.evaluate("() => JSON.parse(JSON.stringify("
                                    "window.AIMPricing.scenario.defaults('ITUK-PADS')))")
            keys_a = ["price_after", "quantity_after", "selected_alternative_id", "cost_eur", "scope"]
            row_a["live_after_reopen"] = {k: live_after.get(k) for k in keys_a}
            row_a["defaults"] = {k: defaults.get(k) for k in keys_a}
            row_a["adopted_saved_revision"] = all(
                live_after.get(k) == saved["scenario"].get(k) for k in keys_a)
            row_a["equals_a_fresh_default"] = all(
                live_after.get(k) == defaults.get(k) for k in keys_a)
            ctx.close()
        except Exception as exc:  # noqa: BLE001
            row_a["fatal"] = str(exc).splitlines()[0][:300]
        rows.append(row_a)
        print(json.dumps(row_a))

        # ---------------------------------------------------- check B -------
        # Same question, but the second page is opened in a genuinely new
        # process on the same profile directory.
        for label, fresh_output in [("new process, same profile", False),
                                    ("new process, fresh profile", True)]:
            row_b = {"check": "B", "variant": label}
            prof2 = Path(tempfile.mkdtemp(prefix="aim_diag_b_")) if fresh_output else profile
            try:
                if fresh_output:
                    # save first in this profile, then reopen it
                    c1 = p.chromium.launch_persistent_context(
                        user_data_dir=str(prof2), headless=True, executable_path=CHROME,
                        viewport={"width": 1440, "height": 900}, accept_downloads=True,
                        args=["--allow-file-access-from-files"])
                    q1 = c1.new_page()
                    q1.goto(url("ITUK-PADS", "objectives"))
                    q1.wait_for_function("() => !!window.AIMPricing", timeout=30000)
                    q1.evaluate("() => { try { localStorage.clear(); } catch (e) {} }")
                    q1.goto(url("ITUK-PADS", "objectives"))
                    q1.wait_for_function("() => !!window.AIMPricing", timeout=30000)
                    q1.wait_for_timeout(300)
                    q1.evaluate("(id) => window.AIMPricing.selectAlternative(id)", order[1])
                    q1.evaluate("([c]) => { location.hash = new URLSearchParams("
                                "{case:c, view:'action', compare:'half'}).toString(); }", ["ITUK-PADS"])
                    q1.wait_for_timeout(300)
                    q1.click("#save-case")
                    q1.wait_for_timeout(400)
                    c1.close()
                c2 = p.chromium.launch_persistent_context(
                    user_data_dir=str(prof2), headless=True, executable_path=CHROME,
                    viewport={"width": 1440, "height": 900}, accept_downloads=True,
                    args=["--allow-file-access-from-files"])
                q2 = c2.new_page()
                q2.goto(url("ITUK-PADS", "action"))
                q2.wait_for_function("() => !!window.AIMPricing", timeout=30000)
                q2.wait_for_timeout(600)
                live2 = q2.evaluate("() => JSON.parse(JSON.stringify(window.AIMPricing.getScenario()))")
                defs2 = q2.evaluate("() => JSON.parse(JSON.stringify("
                                    "window.AIMPricing.scenario.defaults('ITUK-PADS')))")
                rec2 = q2.evaluate("() => { const c = window.AIMPricing.cases.load('ITUK-PADS');"
                                   " return c ? c.revisions[c.revisions.length-1].record.scenario : null; }")
                keys_b = ["price_after", "quantity_after", "selected_alternative_id", "cost_eur", "scope"]
                row_b["store_read_back"] = rec2 is not None
                row_b["live"] = {k: live2.get(k) for k in keys_b}
                row_b["defaults"] = {k: defs2.get(k) for k in keys_b}
                row_b["saved"] = {k: (rec2 or {}).get(k) for k in keys_b}
                row_b["adopted_saved_revision"] = bool(rec2) and all(
                    live2.get(k) == rec2.get(k) for k in keys_b)
                row_b["equals_a_fresh_default"] = all(
                    live2.get(k) == defs2.get(k) for k in keys_b)
                c2.close()
            except Exception as exc:  # noqa: BLE001
                row_b["fatal"] = str(exc).splitlines()[0][:300]
            rows.append(row_b)
            print(json.dumps(row_b))

    (OUT / "diagnostic.json").write_text(json.dumps(rows, indent=2) + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    sys.exit(main())
