#!/usr/bin/env python
"""
Browser acceptance for the corrected AIM component (ACCEPT-02, BASE-06).

What this proves that the earlier review could not:

  * every case and every tab renders, with no stale previous-tab content under a
    newly selected tab;
  * the ITUK turbo objectives view actually renders;
  * the complete journey - select a ranked option, inspect the inputs, change an
    assumption, save, export, restart the browser, reopen - preserves the same
    assumptions and the same two results;
  * local storage really survives a restart, loaded over file:// on this machine
    rather than in memory;
  * every invalid input is refused rather than silently accepted.

Usage (Chrome must be installed):
    python tests/accept/browser_accept.py --html <path> [--headed]
"""
import argparse
import json
import os
import sys
import time

try:
    from playwright.sync_api import sync_playwright
except ImportError:
    print("This check needs Playwright:  python -m pip install playwright")
    sys.exit(2)

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "_out")
os.makedirs(OUT, exist_ok=True)

CASES = ["IMOTORS-CABIN", "ITUK-TURBO", "ITUK-PADS", "ITUK-DISCS", "IMOTORS-OIL"]
TABS = ["decision", "position", "objectives", "economics", "candidates", "action"]
TAB_LABEL = {
    "decision": "Sales evidence", "position": "Price position", "objectives": "Two objectives",
    "economics": "Price & profit test", "candidates": "Candidates", "action": "Internal action",
}

CHROME_CANDIDATES = [
    r"C:\Program Files\Google\Chrome\Application\chrome.exe",
    r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
    os.path.expandvars(r"%LOCALAPPDATA%\Google\Chrome\Application\chrome.exe"),
]

results = []


def check(cid, name, ok, observed=""):
    results.append({"id": cid, "name": name, "status": "pass" if ok else "FAIL",
                    "observed": str(observed)[:400]})
    print("%-5s %-6s %s%s" % ("PASS" if ok else "FAIL", cid, name,
                              ("  --  " + str(observed)[:200]) if observed else ""))


def find_chrome(explicit=None):
    if explicit and os.path.exists(explicit):
        return explicit
    for path in CHROME_CANDIDATES:
        if os.path.exists(path):
            return path
    return None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--html", required=True)
    ap.add_argument("--browser-path", default=None)
    ap.add_argument("--headed", action="store_true")
    args = ap.parse_args()

    html_path = os.path.abspath(args.html)
    if not os.path.exists(html_path):
        print("Not found: " + html_path)
        return 2
    url = "file:///" + html_path.replace("\\", "/")

    chrome = find_chrome(args.browser_path)
    if not chrome:
        print("No Chrome found. Pass --browser-path.")
        return 2
    print("browser : " + chrome)
    print("url     : " + url)
    print("")

    errors = []
    profile = os.path.join(OUT, "_profile")
    with sync_playwright() as p:
        # A persistent profile is required to test a genuine restart: a fresh
        # browser context gets its own empty storage, which would prove nothing.
        def launch():
            ctx = p.chromium.launch_persistent_context(
                user_data_dir=profile, headless=not args.headed,
                executable_path=chrome, viewport={"width": 1500, "height": 1000},
                args=["--allow-file-access-from-files"])
            pg = ctx.pages[0] if ctx.pages else ctx.new_page()
            pg.on("pageerror", lambda e: errors.append(str(e)))
            pg.on("console", lambda m: errors.append("console." + m.type + ": " + m.text)
                  if m.type == "error" else None)
            return ctx, pg

        context, page = launch()

        # ---------------------------------------------------- load the file
        page.goto(url)
        page.wait_for_timeout(1200)

        # Start from a known state, so a rerun is repeatable and is not affected
        # by a revision left by an earlier run in this profile.
        page.evaluate("""() => {
            try { localStorage.clear(); } catch (e) {}
        }""")
        page.reload()
        page.wait_for_timeout(1400)

        api = page.evaluate("typeof window.AIMPricing")
        check("B01", "The application boots from file:// with its API exposed",
              api == "object", "typeof window.AIMPricing = " + str(api))

        cases_in_page = page.evaluate("(window.AIMPricing&&AIMPricing.data.cases.length)||0")
        check("B02", "All five worked cases are present", cases_in_page == 5,
              "%s cases" % cases_in_page)

        tabs_in_page = page.evaluate(
            "Array.from(document.querySelectorAll('#tabs .tab')).map(t=>t.innerText)")
        check("B03", "All six tabs render", len(tabs_in_page) == 6, tabs_in_page)

        tabs_expected = list(TAB_LABEL.values())
        check("B04", "The tab labels are the intended six",
              tabs_in_page == tabs_expected, tabs_in_page)

        # --------------------------------------- every case, every tab (30)
        renders = []
        for case_id in CASES:
            for tab in TABS:
                page.evaluate(
                    "u=>{location.hash=u;}", "case=%s&view=%s&compare=half" % (case_id, tab))
                page.wait_for_timeout(420)
                info = page.evaluate("""() => {
                    const c = document.getElementById('content');
                    const active = document.querySelector('#tabs .tab.active');
                    return {
                      len: c ? c.innerText.trim().length : 0,
                      active: active ? active.innerText : null,
                      failed: !!c.querySelector('.error-msg'),
                      head: c ? c.innerText.trim().slice(0, 90) : ''
                    };
                }""")
                ok = (info["len"] > 200
                      and not info["failed"]
                      and info["active"] == TAB_LABEL[tab])
                renders.append({"case": case_id, "tab": tab, "ok": ok,
                                "length": info["len"], "failed": info["failed"],
                                "active": info["active"], "head": info["head"]})
                if not ok:
                    check("B05." + case_id + "." + tab,
                          "Renders and matches the active tab", False, info)
        bad = [r for r in renders if not r["ok"]]
        check("B05", "Every case and every tab renders (30 combinations)",
              len(bad) == 0, "30 rendered, %d failed" % len(bad) if not bad else bad[:3])

        # Layout defects that a viewer sees immediately: text spilling out of the
        # page, or two pieces of text drawn on top of each other. Checked on every
        # case and tab rather than eyeballed from a scaled screenshot.
        layout_problems = []
        for case_id in CASES:
            for tab in TABS:
                page.evaluate("u=>{location.hash=u;}",
                              "case=%s&view=%s&compare=half" % (case_id, tab))
                page.wait_for_timeout(300)
                found = page.evaluate("""() => {
                    const problems = [];
                    const wide = document.documentElement.scrollWidth
                               - document.documentElement.clientWidth;
                    if (wide > 2) problems.push({kind:'page overflows horizontally', px: wide});
                    const rows = Array.from(document.querySelectorAll('#content .evidence-line, #content .result-label'));
                    rows.forEach(el => {
                      const kids = Array.from(el.children);
                      for (let i = 0; i + 1 < kids.length; i++) {
                        const a = kids[i].getBoundingClientRect(), b = kids[i+1].getBoundingClientRect();
                        if (b.left < a.right - 1 && Math.abs(b.top - a.top) < 6) {
                          problems.push({kind:'text overlapping',
                            text: (kids[i].innerText||'').slice(0,30) + ' | ' + (kids[i+1].innerText||'').slice(0,30)});
                        }
                      }
                    });
                    return problems;
                }""")
                for problem in found:
                    layout_problems.append({"case": case_id, "tab": tab, "problem": problem})
        check("B34", "No text overlaps and no page overflows on any case or tab",
              len(layout_problems) == 0, layout_problems[:4] or "30 views clean")

        # --------------------------------------------- the turbo repair (F05)
        page.evaluate("()=>{location.hash='case=ITUK-TURBO&view=objectives&compare=half';}")
        page.wait_for_timeout(700)
        turbo = page.evaluate("""() => {
            const c = document.getElementById('content');
            return {
              text: c.innerText,
              failed: !!c.querySelector('.error-msg'),
              hasRef: c.innerText.indexOf('v03fmtPct') >= 0,
              hasRanked: c.innerText.indexOf('Ranked under') >= 0
            };
        }""")
        check("B06", "ITUK turbo / Two objectives renders instead of throwing",
              (not turbo["failed"]) and turbo["hasRanked"] and not turbo["hasRef"],
              "ranked=%s ref-error=%s" % (turbo["hasRanked"], turbo["hasRef"]))

        page_error_text = " ".join(errors)
        check("B07", "No reference error was raised while rendering the objectives view",
              "v03fmtPct is not defined" not in page_error_text,
              page_error_text[:200] or "no page errors")

        # A failed view must not leave the previous tab's body underneath.
        page.evaluate("""() => {
            const c = document.getElementById('content');
            window.__probe = c.innerText.slice(0, 60);
            window.__origRank = AIMPricing.engine.rankAlternatives;
            AIMPricing.engine.rankAlternatives = function(){ throw new Error('deliberate probe'); };
            AIMPricing.render();
        }""")
        page.wait_for_timeout(700)
        stale = page.evaluate("""() => {
            const c = document.getElementById('content');
            return { failed: !!c.querySelector('.error-msg'),
                     sameAsBefore: c.innerText.slice(0,60) === window.__probe,
                     saysCouldNotRender: c.innerText.indexOf('did not load') >= 0 };
        }""")
        check("B08", "A failed view shows an explicit error, not the previous tab's content",
              stale["failed"] and stale["saysCouldNotRender"] and not stale["sameAsBefore"],
              stale)
        page.evaluate("""() => {
            AIMPricing.engine.rankAlternatives = window.__origRank;
            location.hash='case=ITUK-TURBO&view=objectives&compare=half&restored=1';
        }""")
        page.wait_for_timeout(700)

        # -------------------------------------------------- selection journey
        page.evaluate("()=>{location.hash='case=ITUK-PADS&view=objectives&compare=half';}")
        page.wait_for_timeout(600)
        before = page.evaluate("""() => {
            const s = AIMPricing.getScenario();
            return { price: s.price_after, qty: s.quantity_after, selected: s.selected_alternative_id };
        }""")
        picked = page.evaluate("""() => {
            /* select the first genuinely priced alternative that is not 'No action' */
            const c = AIMPricing.data.cases.find(x=>x.id==='ITUK-PADS');
            const rk = AIMPricing.engine.rankAlternatives(c,'revenue',{payload:AIMPricing.data});
            const pick = rk.ranked.find(x=>x.result.ok && x.alternative.kind!=='no-price');
            const res = AIMPricing.selectAlternative(pick.alternative.alternative_id);
            return { id: pick.alternative.alternative_id, ok: res.ok };
        }""")
        page.wait_for_timeout(400)
        check("B09", "A ranked alternative can be selected into the scenario",
              picked["ok"], picked)

        after_select = page.evaluate("() => AIMPricing.getScenario()")
        changed = (after_select["selected_alternative_id"] == picked["id"]
                   and (after_select["price_after"] != before["price"]
                        or after_select["quantity_after"] != before["qty"]))
        check("B10", "Selecting the alternative actually populates the one scenario record",
              changed, {"selected": after_select["selected_alternative_id"],
                        "price": after_select["price_after"],
                        "quantity": after_select["quantity_after"]})

        cons = page.evaluate("() => AIMPricing.consistency()")
        check("B11", "Ranking, manual inputs and the saved record are one scenario",
              cons["ok"], cons["statement"])

        # A manual adjustment has to reach the calculation.
        page.evaluate("() => AIMPricing.setScenario({support_eur: 750})")
        page.wait_for_timeout(300)
        with_support = page.evaluate("() => { const r=AIMPricing.getResult(); return {ok:r.ok, gp:r.gp_change, sup:r.support_eur, bridge:r.bridge_reconciles}; }")
        check("B12", "A manual assumption reaches the same calculation path",
              with_support["ok"] and with_support["sup"] == 750 and with_support["bridge"] is True,
              with_support)

        # -------------------------------------------- objective independence
        page.evaluate("()=>{location.hash='case=ITUK-PADS&view=objectives&compare=half';}")
        page.wait_for_timeout(500)
        obj = page.evaluate("""() => {
            const c = AIMPricing.data.cases.find(x=>x.id==='ITUK-PADS');
            const rev = AIMPricing.engine.rankAlternatives(c,'revenue',{payload:AIMPricing.data});
            const gp  = AIMPricing.engine.rankAlternatives(c,'grossProfit',{payload:AIMPricing.data});
            const q = rk => rk.ranked.map(x=>x.alternative.alternative_id+':'+x.result.quantity_after).sort().join('|');
            return { baseRev: rev.baseline.revenue, baseGp: gp.baseline.revenue,
                     qtySame: q(rev) === q(gp),
                     revOrder: rev.ranked.map(x=>x.alternative.alternative_id).join(','),
                     gpOrder: gp.ranked.map(x=>x.alternative.alternative_id).join(',') };
        }""")
        check("B13", "Changing the objective changes ordering only",
              obj["baseRev"] == obj["baseGp"] and obj["qtySame"], obj)

        # ----------------------------------------------------- invalid inputs
        invalid = page.evaluate("""() => {
            const E = AIMPricing.engine;
            const base = {price_before:100, price_after:100, quantity_before:100,
                          quantity_after:null, cost_eur:60, support_eur:0, scope:'all', pack_size:1};
            const t = extra => E.calculate(Object.assign({}, base, extra));
            return {
              negQty:  t({quantity_after:-1}).ok === false,
              nanQty:  t({quantity_after:NaN}).ok === false,
              infQty:  t({quantity_after:Infinity}).ok === false,
              zeroQty: t({quantity_after:0}).ok === false,
              badSup:  t({support_eur:'invalid'}).ok === false,
              negCost: t({cost_eur:-5}).ok === false,
              incrBelow: t({scope:'incremental', price_after:80, quantity_after:50}).ok === false,
              blankQtyOk: t({quantity_after:''}).ok === true,
              zeroCostOk: t({cost_eur:0}).ok === true
            };
        }""")
        check("B14", "Invalid quantities, support and cost are refused",
              all([invalid["negQty"], invalid["nanQty"], invalid["infQty"], invalid["zeroQty"],
                   invalid["badSup"], invalid["negCost"], invalid["incrBelow"]]), invalid)
        check("B15", "A blank quantity is unchanged, and a zero cost is a value",
              invalid["blankQtyOk"] and invalid["zeroCostOk"], invalid)

        # ------------------------------------------------------- date handling
        dates = page.evaluate("""() => {
            const E = AIMPricing.engine, D = AIMPricing.data;
            const pn = D.cases.find(c=>c.id==='ITUK-TURBO').pn;
            return {
              bad:  E.costForDate(D, pn, 'not-a-date').resolved,
              past: E.costForDate(D, pn, '2035-01-01').resolved,
              blank:E.costForDate(D, pn, '').resolved,
              good: E.costForDate(D, pn, '2026-11-01').basis_id || null,
              sep:  E.costForDate(D, pn, '2026-09-15').basis_id || null
            };
        }""")
        check("B16", "An unusable effective date stays unresolved instead of defaulting",
              dates["bad"] is False and dates["past"] is False and dates["blank"] is False, dates)
        check("B17", "September and October offers resolve to different named bases",
              dates["sep"] == "SEP26" and dates["good"] == "OCT26", dates)

        # --------------------------------------------------- candidate search
        page.evaluate("()=>{location.hash='case=ITUK-PADS&view=candidates&compare=half';}")
        page.wait_for_timeout(700)
        cand = page.evaluate("""() => {
            const C = AIMPricing.candidates, D = AIMPricing.data;
            const all = D.candidateScreen;
            const wb = C.workbench(all, {page: 1, page_size: 50});
            const last = C.workbench(all, {page: wb.page.page_count, page_size: 50});
            const searched = C.workbench(all, {query: 'filter', page:1, page_size: 50});
            const paged = document.querySelector('.pager') ? true : false;
            return { total: wb.page.total, allRows: all.length,
                     pages: wb.page.page_count, lastPageRows: last.page.rows.length,
                     searchHits: searched.page.total, hasPager: paged,
                     unique: wb.coverage.unique_parts };
        }""")
        check("B18", "Every candidate row is reachable, not only the first page",
              cand["total"] == cand["allRows"] and cand["lastPageRows"] > 0
              and cand["hasPager"], cand)
        check("B19", "Search reaches beyond the first page of the screen",
              cand["searchHits"] > 0, "%s hits for 'filter'" % cand["searchHits"])
        check("B20", "Row counts and distinct part counts are reported separately",
              cand["unique"] <= cand["total"],
              "%s rows, %s distinct parts" % (cand["total"], cand["unique"]))

        # ------------------------------------------------------- export bytes
        page.evaluate("()=>{location.hash='case=ITUK-PADS&view=action&compare=half';}")
        page.wait_for_timeout(600)
        exports_check = page.evaluate("""() => {
            const X = AIMPricing.export;
            const c = AIMPricing.data.cases.find(x=>x.id==='ITUK-PADS');
            const s = AIMPricing.getScenario();
            const r = AIMPricing.getResult();
            const co = {case_id:c.id, customer:c.customer, market:c.market,
                        part_number:c.pn, unit:c.unit, title:c.name, version:1, state:'draft'};
            const member = X.memberBrief(co, s, r, {exported_at:'2026-09-22T00:00:00Z'});
            const memberBytes = X.toBytes(member, true);
            const internal = X.internalRecord(co, s, r, {exported_at:'2026-09-22T00:00:00Z'});
            const internalBytes = X.toBytes(internal, true);
            const nested = X.buildAllowed({scenario:{cost:60, margin_pp_change:4}}, X.allowlistFor('member'));
            return {
              memberOk: member.audit.ok,
              memberFindings: member.audit.findings,
              memberLen: memberBytes.length,
              memberHasCost: /"cost/.test(memberBytes.text),
              memberHasGp: /gross profit|gp_change|gross margin/i.test(memberBytes.text),
              internalHasGp: /gp_change/.test(internalBytes.text),
              internalLen: internalBytes.length,
              nestedStripped: JSON.stringify(nested).indexOf('cost') < 0,
              memberText: memberBytes.text.slice(0, 200)
            };
        }""")
        check("B21", "The participant brief is built from permitted fields only",
              exports_check["memberOk"] and not exports_check["memberHasCost"]
              and not exports_check["memberHasGp"], exports_check["memberFindings"])
        check("B22", "A nested cost object cannot survive into a participant brief",
              exports_check["nestedStripped"], "nested cost removed by construction")
        check("B23", "The internal record does keep the profit result",
              exports_check["internalHasGp"], "internal length %s" % exports_check["internalLen"])
        check("B24", "Both exports produce real bytes",
              exports_check["memberLen"] > 200 and exports_check["internalLen"] > 400,
              {"member": exports_check["memberLen"], "internal": exports_check["internalLen"]})

        # ------------------------------------------- save, restart, and reopen
        page.evaluate("""() => {
            location.hash='case=ITUK-PADS&view=action&compare=half';
        }""")
        page.wait_for_timeout(600)
        saved_snapshot = page.evaluate("""() => {
            AIMPricing.setScenario({support_eur: 750, scope:'all', pack_size: 25});
            const r = AIMPricing.getResult();
            const s = AIMPricing.getScenario();
            const res = AIMPricing.cases.save('ITUK-PADS',
              {scenario:s, result:r, part_number:'8982447940'},
              {expected_version:0, state:'ready_for_review', owner_role:'Pricing',
               next_action:'Request the comparable quotation', next_update_due:'2026-10-15',
               recorded_by:'acceptance check'});
            return { ok: res.ok, version: res.version, durable: res.durable,
                     price: s.price_after, qty: s.quantity_after, support: s.support_eur,
                     revChange: r.revenue_change, gpChange: r.gp_change,
                     margin: r.margin_after_pct, bridge: r.bridge_reconciles };
        }""")
        check("B25", "A case revision saves and reports whether the storage is durable",
              saved_snapshot["ok"], saved_snapshot)

        storage_durable = page.evaluate("() => AIMPricing.cases.store.isDurable()")
        check("B26", "Local storage works over file:// on this machine "
                     "(the earlier review could not test this)",
              storage_durable is True, "isDurable=%s" % storage_durable)

        raw_key = page.evaluate("() => { try { return (localStorage.getItem('ISZE_AIM_CASES_V1')||'').length; } catch(e){ return -1; } }")
        check("B27", "The revision was written to the real browser store",
              raw_key > 100, "stored characters: %s" % raw_key)

        # Restart the browser completely. The persistent profile carries the
        # origin storage across the restart, so this is a real reopen and not a
        # fresh context that would be empty by construction.
        context.close()
        context, page = launch()
        page.goto(url)
        page.wait_for_timeout(1600)
        after_restart = page.evaluate("""() => {
            /* load the persisted record directly from the store */
            const repo = AIMPricing.cases;
            const rec = repo.reopen('ITUK-PADS');
            return rec ? { version: rec.version, state: rec.state,
                           price: rec.scenario.price_after,
                           qty: rec.scenario.quantity_after,
                           support: rec.scenario.support_eur,
                           pack: rec.scenario.pack_size,
                           revChange: rec.result.revenue_change,
                           gpChange: rec.result.gp_change } : null;
        }""")
        check("B28", "The saved revision is still readable after a restart",
              after_restart is not None, after_restart)

        same = bool(after_restart) and (
            abs(after_restart["revChange"] - saved_snapshot["revChange"]) < 1e-9
            and abs(after_restart["gpChange"] - saved_snapshot["gpChange"]) < 1e-9
            and after_restart["support"] == saved_snapshot["support"]
            and after_restart["pack"] == 25)
        check("B29", "Reopening reproduces the same assumptions and both results",
              same, {"saved": saved_snapshot, "reopened": after_restart})

        hist = page.evaluate("() => AIMPricing.cases.history('ITUK-PADS').length")
        check("B30", "The revision history is retained, not overwritten", hist >= 1,
              "%s revision(s)" % hist)

        conflict = page.evaluate("""() => {
            const repo = AIMPricing.cases;
            const stale = repo.save('ITUK-PADS', {scenario:{price_after:1}, result:{ok:true}},
                                    {expected_version:0});
            return { ok: stale.ok, conflict: stale.conflict };
        }""")
        check("B31", "A stale write is refused rather than overwriting",
              conflict["ok"] is False and conflict["conflict"] is True, conflict)

        # -------------------------------------------- screenshots for the record
        shots = []
        for case_id, tab in [("ITUK-TURBO", "objectives"), ("ITUK-PADS", "objectives"),
                             ("ITUK-PADS", "economics"), ("ITUK-PADS", "candidates"),
                             ("ITUK-PADS", "action")]:
            page.evaluate("u=>{location.hash=u;}", "case=%s&view=%s&compare=half" % (case_id, tab))
            page.wait_for_timeout(500)
            name = "%s__%s.png" % (case_id, tab)
            page.screenshot(path=os.path.join(OUT, name), full_page=False)
            shots.append(name)
        check("B32", "Screenshots were captured for the record", len(shots) == 5, shots)

        context.close()

    real_errors = [e for e in errors if "favicon" not in e.lower()]
    check("B33", "No uncaught page error occurred across the whole run",
          len(real_errors) == 0, real_errors[:4])

    summary = {"pass": sum(1 for r in results if r["status"] == "pass"),
               "fail": sum(1 for r in results if r["status"] == "FAIL"),
               "total": len(results)}
    payload = {"run_at": time.strftime("%Y-%m-%dT%H:%M:%S"), "html": html_path,
               "chrome": chrome, "summary": summary, "checks": results,
               "renders": renders}
    with open(os.path.join(OUT, "browser_acceptance.json"), "w", encoding="utf-8") as fh:
        json.dump(payload, fh, indent=2)
    print("")
    print(json.dumps(summary))
    return 0 if summary["fail"] == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
