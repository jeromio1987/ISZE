"""ACCEPT-02 - the complete browser journey, against a real file URL.

What this proves, and what it does not
--------------------------------------
This is a cross-view scenario test, not a set of isolated screens:

    choose a case -> select a ranked alternative -> change an assumption ->
    recalculate -> save -> export -> close the browser -> reopen -> compare

It runs against a real ``file://`` URL in a persistent browser profile, so the
save has to survive an actual browser session ending. The in-memory run in the
supplied review is not acceptance evidence for that, and is not used here.

Coverage: all five cases, all six tabs, both ranking objectives. Both results
(revenue and gross profit) must match after reopen. Changing the objective must
change ordering only, never an assumption.

Screenshots: the script takes them; it does not claim to have read them. The
count taken and the count a person or reviewer actually opened are recorded
separately in the JSON output, because a take-count is not a read-count.

    python tests/accept/accept_02_journey.py
    python tests/accept/accept_02_journey.py --chrome "C:/Program Files/Google/Chrome/Application/chrome.exe"
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import sys
import tempfile
import time
import urllib.parse
from pathlib import Path

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "tests" / "accept" / "_out"
APP = ROOT / "dist" / "ISZE_AIM_Pricing_Decisions_v04_INTERNAL.html"
SHOTS = OUT / "shots"

TABS = ["decision", "position", "objectives", "economics", "candidates", "action"]
OBJECTIVES = ["revenue", "grossProfit"]

RESULTS: list[dict] = []
TAKEN: list[str] = []


def sha256(path: Path) -> str | None:
    if not path.exists():
        return None
    return hashlib.sha256(path.read_bytes()).hexdigest()


def record(check_id: str, name: str, ok: bool, evidence) -> None:
    RESULTS.append({"id": check_id, "name": name, "status": "PASS" if ok else "FAIL",
                    "evidence": evidence})


def scenario_snapshot(page) -> dict:
    """The scenario fields that travel with a decision."""
    return page.evaluate("""() => {
      const s = window.AIMPricing.getScenario();
      return JSON.parse(JSON.stringify(s));
    }""")


def result_snapshot(page) -> dict:
    return page.evaluate("""() => {
      const r = window.AIMPricing.getResult();
      return JSON.parse(JSON.stringify(r));
    }""")


def ranking(page, objective: str) -> dict:
    return page.evaluate("""(obj) => {
      const D = window.AIMPricing.data, E = window.AIMPricing.engine;
      const st = window.AIMPricing.getState();
      const c = D.cases.find(x => x.id === st.caseId);
      const s = window.AIMPricing.getScenario();
      const r = E.rankAlternatives(c, obj, { payload: D,
        pack_size: s.pack_size, offer_effective_date: s.offer_effective_date });
      return {
        objective: obj,
        order: r.ranked.map(x => x.alternative.alternative_id),
        rows: r.ranked.map(x => ({ id: x.alternative.alternative_id,
          price_after: x.result.price_after, quantity_after: x.result.quantity_after,
          revenue_change: x.result.revenue_change, gp_change: x.result.gp_change,
          ok: x.result.ok }))
      };
    }""", objective)


def file_url(case_id: str, view: str) -> str:
    return APP.as_uri() + "#" + urllib.parse.urlencode(
        {"case": case_id, "view": view, "compare": "half"})


def shot(page, name: str) -> None:
    SHOTS.mkdir(parents=True, exist_ok=True)
    p = SHOTS / (name + ".png")
    page.screenshot(path=str(p), full_page=True)
    TAKEN.append(str(p))


def clear_storage(page) -> None:
    try:
        page.evaluate("() => { try { localStorage.clear(); } catch (e) {} }")
    except Exception:
        pass


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--chrome", default=os.environ.get(
        "CHROME_PATH", r"C:\Program Files\Google\Chrome\Application\chrome.exe"))
    ap.add_argument("--keep-profile", action="store_true")
    args = ap.parse_args()

    started = time.time()
    if not APP.is_file():
        print("MISSING BUILD OUTPUT: " + str(APP))
        print("ACCEPT-02 cannot run until tools/build.py has produced the artifact.")
        run = {"check": "ACCEPT-02", "title": "Complete browser journey", "status": "NOT RUN",
               "reason": "the built artifact does not exist", "artifact": str(APP),
               "results": [], "summary": {"pass": 0, "fail": 0, "total": 0}}
        OUT.mkdir(parents=True, exist_ok=True)
        (OUT / "accept_02_journey.json").write_text(json.dumps(run, indent=2) + "\n", encoding="utf-8")
        return 2

    profile = Path(tempfile.mkdtemp(prefix="aim_accept_profile_"))
    profiles = [profile]
    run = {
        "check": "ACCEPT-02",
        "title": "Complete browser journey: select, edit, save, export, restart, reopen",
        "review_date": time.strftime("%Y-%m-%dT%H:%M:%S"),
        "artifact": str(APP),
        "artifact_sha256": sha256(APP),
        "load_mode": "file:// URL in a persistent browser profile",
        "profile": str(profile),
        "profiles": [],
        "environment_note": ("Relaunching Chromium into an already-used profile directory in this "
                             "environment kills the page with 'Target page, context or browser has "
                             "been closed'. Reproduced in tests/accept/_diag_export.py. Each case "
                             "therefore uses its own profile directory, and the export routes are "
                             "exercised on the first launch in that profile."),
        "coverage": {"cases": [], "tabs": TABS, "objectives": OBJECTIVES},
        "deep_links": [],
        "results": [],
        "screenshots": {"taken": 0, "read": 0, "read_by": None, "note":
                        "Taken by this script. The read count is filled in only after a person or "
                        "reviewer opens them; a take-count is not a read-count."},
        "scope": "Browser behaviour against a real file URL in one persistent profile on this "
                 "machine. Not production identity, not a shared backend, not multi-user access."
    }

    errors: list[str] = []
    crashes: list[str] = []

    def open_persistent(pw, profile_dir):
        """A persistent profile, so a restart really reads the store from disk."""
        return pw.chromium.launch_persistent_context(
            user_data_dir=str(profile_dir), headless=True, executable_path=args.chrome,
            viewport={"width": 1440, "height": 900}, accept_downloads=True,
            args=["--allow-file-access-from-files"])

    def attach(page, label):
        page.on("pageerror", lambda e: errors.append(f"{label}:pageerror:{e}"))
        page.on("crash", lambda: crashes.append(f"{label}:crash"))
        try:
            page.on("console", lambda m: errors.append(f"{label}:console:{m.text}")
                    if m.type == "error" else None)
        except Exception:
            pass
        return page

    with sync_playwright() as p:
        def open_page(label, profile_dir):
            """A persistent context on the given profile directory, one alive at a time.

            The context is closed before the next one opens, which is what makes
            the restart phase a real restart and keeps a dead renderer from being
            reused by the next phase.

            A fresh page is used rather than the context's own startup tab: in this
            environment that startup tab dies intermittently, and the resulting
            "context has been closed" error is a harness fault, not a product
            verdict. (Reproduced 6 times in tests/accept/_diag_export.py.)
            """
            c = open_persistent(p, profile_dir)
            pg = c.new_page()
            return c, attach(pg, label)

        ctx, page = open_page("main", profile)
        page.goto(file_url("__none__", "objectives"))
        page.wait_for_function("() => !!window.AIMPricing", timeout=30000)
        clear_storage(page)
        page.reload()
        page.wait_for_function("() => !!window.AIMPricing", timeout=30000)
        page.wait_for_timeout(300)
        # Is the save actually durable on this file:// origin?
        durability = page.evaluate("""() => {
          const r = window.AIMPricing.cases;
          const probe = r.save('__PROBE__', {scenario:{x:1}, result:{y:1}}, {state:'draft'});
          const back = r.load('__PROBE__');
          const durable = r.store.isDurable();
          try { localStorage.removeItem('ISZE_AIM_CASES_V1'); } catch (e) {}
          return { write_ok: !!(probe && probe.ok), readback_ok: !!(back && back.version === 1),
                   store_is_durable: durable, warning: (probe || {}).warning || null };
        }""")
        run["storage_probe"] = durability
        if not durability.get("store_is_durable"):
            record("J00", "The save path warns that the record will not survive a restart",
                   bool(durability.get("warning")),
                   json.dumps(durability))
        else:
            record("J00", "The save path can write to disk on this file:// origin", True,
                   json.dumps(durability))
        clear_storage(page)

        # A blank panel, a NaN or an empty shell where data is simply absent is a
        # FAIL, not a pass. Checked on every tab of every case below.
        record("J01", "The application starts with no uncaught page error",
               not [e for e in errors if "pageerror" in e or "console" in e],
               json.dumps(errors[:5]) if errors else "no page error and no console error on startup")

        cases = page.evaluate("() => window.AIMPricing.data.cases.map(c => c.id)") or ["ITUK-PADS"]
        run["coverage"]["cases"] = cases
        ctx.close()

        for case_id in cases:
            # A fresh profile per case. The first launch in a profile is
            # reliable here; relaunching into an already-used profile directory is
            # not. (Reproduced in tests/accept/_diag_export.py.)
            profile = Path(tempfile.mkdtemp(prefix="aim_accept_%s_" % case_id))
            profiles.append(profile)
            case_rows = {"case": case_id, "tabs": {}, "objectives": {}}
            # ------------------------------------------------------- phase 1 --
            ctx, page = open_page(case_id + "/main", profile)
            page.goto(file_url(case_id, "objectives"))
            page.wait_for_function("() => !!window.AIMPricing", timeout=30000)
            page.wait_for_timeout(250)
            before_errors = len(errors)

            for tab in TABS:
                page.evaluate("([c,v]) => { location.hash = new URLSearchParams("
                              "{case:c, view:v, compare:'half'}).toString(); }", [case_id, tab])
                page.wait_for_timeout(200)
                state = page.evaluate("() => window.AIMPricing.getState()")
                body = page.locator("#content").inner_text()
                new_errors = errors[before_errors:]
                # Blank, not-a-number or undefined content in a live panel is a FAIL.
                # "Cost required" is not a defeat: it is the panel stating an absence.
                defects = []
                if not body.strip():
                    defects.append("the panel is blank")
                if "NaN" in body:
                    defects.append("the panel shows NaN")
                if "undefined" in body:
                    defects.append("the panel shows undefined")
                ok = (state.get("caseId") == case_id and state.get("view") == tab
                      and bool(body.strip()) and not new_errors and not defects)
                case_rows["tabs"][tab] = {"status": "PASS" if ok else "FAIL",
                                          "chars": len(body.strip()),
                                          "defects": defects, "errors": new_errors}
            tabs_fail = [t for t, v in case_rows["tabs"].items() if v["status"] == "FAIL"]
            record(f"J02-{case_id}", f"{case_id}: all six tabs render their own content",
                   not tabs_fail, "failing tabs: " + json.dumps(tabs_fail) if tabs_fail
                   else "all six tabs rendered, no page errors")

            # ------------------------------------------- objective handling --
            page.goto(file_url(case_id, "objectives"))
            page.wait_for_timeout(250)
            scenario_before = scenario_snapshot(page)
            order, rows = {}, {}
            for obj in OBJECTIVES:
                page.select_option("#objective", obj)
                page.wait_for_timeout(200)
                rk = ranking(page, obj)
                order[obj] = rk["order"]
                rows[obj] = rk["rows"]
                case_rows["objectives"][obj] = rk["order"]
            scenario_after = scenario_snapshot(page)

            same_set = sorted(order["revenue"]) == sorted(order["grossProfit"])
            same_results = True
            for r in rows["revenue"]:
                t = next((x for x in rows["grossProfit"] if x["id"] == r["id"]), None)
                if not t or (t["price_after"] != r["price_after"]
                             or t["quantity_after"] != r["quantity_after"]
                             or t["revenue_change"] != r["revenue_change"]
                             or t["gp_change"] != r["gp_change"]):
                    same_results = False
            assumptions_held = json.dumps(scenario_before) == json.dumps(scenario_after)
            record(f"J03-{case_id}", f"{case_id}: changing the objective changes ordering only",
                   same_set and same_results and assumptions_held,
                   json.dumps({"same_alternative_set": same_set, "same_results": same_results,
                               "scenario_unchanged": assumptions_held,
                               "order_revenue": order["revenue"],
                               "order_grossProfit": order["grossProfit"]}))

            # ---------------------------------- select a ranked alternative --
            page.select_option("#objective", "revenue")
            page.wait_for_timeout(200)
            order_now = ranking(page, "revenue")["order"]
            if not order_now:
                record(f"J04-{case_id}", f"{case_id}: a ranked alternative can be selected",
                       False, "the case ranks no alternatives")
                continue
            top = order_now[0]
            page.click(f'[data-select="{top}"]')
            page.wait_for_timeout(250)
            selected = page.evaluate("() => window.AIMPricing.getScenario().selected_alternative_id")
            consistency = page.evaluate("() => window.AIMPricing.consistency()")
            record(f"J04-{case_id}", f"{case_id}: a ranked alternative can be selected into the case",
                   selected == top and bool(consistency.get("ok")),
                   json.dumps({"selected": selected, "expected": top,
                               "consistency": consistency.get("statement")}))
            shot(page, f"{case_id}_01_selected")

            # ------------------------------------------- change assumption --
            page.evaluate("([c]) => { location.hash = new URLSearchParams("
                          "{case:c, view:'economics', compare:'half'}).toString(); }", [case_id])
            page.wait_for_timeout(350)
            before_scenario = scenario_snapshot(page)
            before_result = result_snapshot(page)
            shown_before = page.locator("#economic-results").inner_text()
            current_price = float(page.input_value("#s-newP"))
            new_price = round(current_price * 0.94, 2)
            page.fill("#s-newP", str(new_price))
            page.dispatch_event("#s-newP", "input")
            page.wait_for_timeout(350)
            after_scenario = scenario_snapshot(page)
            after_result = result_snapshot(page)
            shown_after = page.locator("#economic-results").inner_text()
            engine_agrees = page.evaluate("""() => {
              const E = window.AIMPricing.engine, s = window.AIMPricing.getScenario();
              const r = E.calculate({ price_before: s.price_before, price_after: s.price_after,
                quantity_before: s.quantity_before,
                quantity_after: s.quantity_after === null ? null : s.quantity_after,
                scope: s.scope, support_eur: s.support_eur, cost_eur: s.cost_eur,
                pack_size: s.pack_size, quantity_label: s.quantity_label,
                evidence_period: s.evidence_period, offer_effective_date: s.offer_effective_date });
              const shown = window.AIMPricing.getResult();
              return { input: r.revenue_change, shown: shown.revenue_change,
                       gp_input: r.gp_change, gp_shown: shown.gp_change };
            }""")
            recalculated = (after_result.get("revenue_change") != before_result.get("revenue_change")
                            or after_result.get("price_after") != before_result.get("price_after"))
            record(f"J05-{case_id}", f"{case_id}: an edited assumption recalculates the displayed result",
                   recalculated and before_scenario != after_scenario
                   and shown_before != shown_after
                   and engine_agrees["input"] == engine_agrees["shown"],
                   json.dumps({"price_before_change": before_scenario.get("price_after"),
                               "price_after_change": after_scenario.get("price_after"),
                               "revenue_change_before": before_result.get("revenue_change"),
                               "revenue_change_after": after_result.get("revenue_change"),
                               "displayed_matches_engine": engine_agrees["input"] == engine_agrees["shown"]}))
            shot(page, f"{case_id}_02_recalculated")

            # ------------------------------------------------ save a case --
            page.evaluate("([c]) => { location.hash = new URLSearchParams("
                          "{case:c, view:'action', compare:'half'}).toString(); }", [case_id])
            page.wait_for_timeout(350)
            page.fill("#a-next", "Acceptance journey: confirm the recalculated assumption.")
            page.fill("#a-owner", "case_owner")
            page.select_option("#a-status", "ready_for_review")
            page.click("#save-case")
            page.wait_for_timeout(400)
            saved = page.evaluate("""(cid) => {
              const c = window.AIMPricing.cases.load(cid);
              return c ? { version: c.version, state: c.state, revisions: c.revisions.length } : null;
            }""", case_id)
            record(f"J06-{case_id}", f"{case_id}: the case is saved as a revision",
                   bool(saved) and saved.get("revisions", 0) >= 1, json.dumps(saved))

            # ------------------------------------------------ export bytes --
            downloads = {}
            alive_before = not ctx.pages[0].is_closed()
            for button, label in [("#export-json", "internal_record"),
                                  ("#export-member", "participant_brief"),
                                  ("#export-bundle", "recovery_bundle"),
                                  ("#export-review-body", "readable_review")]:
                target = OUT / "exports" / f"{case_id}_{label}.out"
                target.parent.mkdir(parents=True, exist_ok=True)
                try:
                    with page.expect_download(timeout=20000) as dl:
                        page.click(button)
                    dl.value.save_as(str(target))
                    raw = target.read_bytes()
                    downloads[label] = {"bytes": len(raw),
                                        "sha256": hashlib.sha256(raw).hexdigest(),
                                        "saved_to": str(target)}
                except Exception as exc:  # noqa: BLE001 - the failure is the evidence
                    downloads[label] = {"error": str(exc).splitlines()[0][:300],
                                        "session_alive_before_click": alive_before}
                    break
            ok_dl = all("bytes" in v and v["bytes"] > 0 for v in downloads.values())
            record(f"J07-{case_id}", f"{case_id}: every export route writes bytes to disk",
                   ok_dl, json.dumps({"session_alive_before_export": alive_before,
                                      "downloads": downloads}))
            if not alive_before or crashes:
                # A dead renderer is a harness/infrastructure fault, not proof the
                # product is wrong. Say so instead of reporting a false failure.
                run.setdefault("environment_faults", []).append(
                    {"case": case_id, "session_alive": alive_before,
                     "crashes": crashes[:5], "page_errors": errors[-5:]})
                record(f"J07b-{case_id}", f"{case_id}: export step was abandoned because the "
                       "browser session had already ended", False,
                       json.dumps({"session_alive": alive_before, "crashes": crashes[:5],
                                   "note": "environment fault, not a product verdict"}))
            run.setdefault("exports", {})[case_id] = downloads

            # ----------------------------------- phase 2: restart the browser --
            # A new persistent context on the same profile directory, opened only
            # after the first one is closed: the page, the renderer and the
            # session all go away and the case store is read back from disk.
            pre_restart = {"scenario": after_scenario, "result": after_result, "saved": saved}
            ctx.close()

            ctx2, page2 = open_page(case_id + "/restart", profile)
            restart_errors = [e for e in errors if e.startswith(case_id + "/restart")]
            page2.goto(file_url(case_id, "action"))
            page2.wait_for_function("() => !!window.AIMPricing", timeout=30000)
            page2.wait_for_timeout(500)

            reopened = page2.evaluate("""(cid) => {
              const repo = window.AIMPricing.cases;
              const rec = repo.load(cid);
              if (!rec) return { found: false };
              const rev = rec.revisions[rec.revisions.length - 1];
              return { found: true, version: rec.version, state: rec.state,
                       revisions: rec.revisions.length,
                       scenario: rev.record.scenario, result: rev.record.result,
                       reopen: repo.reopen(cid) };
            }""", case_id)
            live = {"scenario": scenario_snapshot(page2), "result": result_snapshot(page2)}

            def same(a, b, keys):
                a = {k: (a or {}).get(k) for k in keys}
                b = {k: (b or {}).get(k) for k in keys}
                return json.dumps(a, sort_keys=True) == json.dumps(b, sort_keys=True)

            keys = ["scenario_id", "case_id", "part_number", "price_before", "price_after",
                    "quantity_before", "quantity_after", "scope", "support_eur", "cost_eur",
                    "cost_basis_id", "pack_size", "quantity_label", "evidence_period",
                    "offer_effective_date", "selected_alternative_id", "objective"]
            res_keys = ["revenue_before", "revenue_after", "revenue_change", "gp_before", "gp_after",
                        "gp_change", "margin_after_pct", "quantity_after", "ok"]
            record(f"J08-{case_id}", f"{case_id}: the saved scenario survives a browser restart",
                   bool(reopened.get("found"))
                   and same(reopened.get("scenario"), pre_restart["scenario"], keys),
                   json.dumps({"found": reopened.get("found"),
                               "before": {k: pre_restart["scenario"].get(k) for k in keys},
                               "after": {k: (reopened.get("scenario") or {}).get(k) for k in keys}}))
            record(f"J09-{case_id}", f"{case_id}: both results match after reopen",
                   same(reopened.get("result"), pre_restart["result"], res_keys),
                   json.dumps({"before": {k: pre_restart["result"].get(k) for k in res_keys},
                               "after": {k: (reopened.get("result") or {}).get(k) for k in res_keys}}))
            # The reopened page must show the saved scenario, not a fresh default.
            # Both are reported, so a failure says which one the page showed.
            fresh = page2.evaluate("""(cid) => {
              const S = window.AIMPricing.scenario, s = S.defaults(cid);
              return JSON.parse(JSON.stringify(s));
            }""", case_id)
            keys_live = keys
            matches_saved = same(live["scenario"], reopened.get("scenario"), keys)
            matches_defaults = same(live["scenario"], fresh, keys)
            record(f"J10-{case_id}", f"{case_id}: the reopened page shows the saved scenario, "
                   "not a fresh default",
                   matches_saved and not matches_defaults,
                   json.dumps({"matches_saved_revision": matches_saved,
                               "matches_a_fresh_default": matches_defaults,
                               "saved": {k: (reopened.get("scenario") or {}).get(k) for k in keys_live},
                               "live": {k: live["scenario"].get(k) for k in keys_live}}))
            record(f"J11-{case_id}", f"{case_id}: no page error on the reopened session",
                   not restart_errors, json.dumps(restart_errors[:5]))
            shot(page2, f"{case_id}_03_reopened")
            ctx2.close()

            run["deep_links"].append({"case": case_id, "url": file_url(case_id, "action")})

    run["screenshots"]["taken"] = len(TAKEN)
    run["profiles"] = [str(p) for p in profiles]
    run["screenshots"]["files"] = TAKEN
    run["elapsed_seconds"] = round(time.time() - started, 1)
    run["results"] = RESULTS
    run["summary"] = {
        "pass": sum(1 for r in RESULTS if r["status"] == "PASS"),
        "fail": sum(1 for r in RESULTS if r["status"] == "FAIL"),
        "total": len(RESULTS),
    }
    run["note"] = ("The persistent profile directory is required for the restart phase and is the "
                   "reason this run is acceptance evidence and the supplied in-memory run is not.")
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "accept_02_journey.json").write_text(json.dumps(run, indent=2) + "\n", encoding="utf-8")

    if not args.keep_profile:
        for prof in profiles:
            shutil.rmtree(prof, ignore_errors=True)

    for r in RESULTS:
        print(f"{r['status']} {r['id']}: {r['name']}"
              + ("" if r["status"] == "PASS" else " -- " + str(r["evidence"])[:400]))
    print(json.dumps(run["summary"]))
    print("screenshots taken: %d" % run["screenshots"]["taken"])
    print("raw: " + str(OUT / "accept_02_journey.json"))
    return 1 if run["summary"]["fail"] else 0


if __name__ == "__main__":
    sys.exit(main())
