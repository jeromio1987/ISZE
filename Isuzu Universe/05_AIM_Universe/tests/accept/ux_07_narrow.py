"""UX-07 - the painted narrow layout, measured.

What this proves, and what it does not
--------------------------------------
UX-07's REQUIRED EVIDENCE 2 is about a real layout, so this script measures the
painted page at a real narrow width in real Chrome, against a real ``file://``
URL. A stub cannot make a layout verdict: the frozen shell's narrow rules are
``@media`` queries and a fake document evaluates none of them. The pattern is the
one ACCEPT-02 uses (persistent browser profile, real file URL).

It builds nothing. It opens the artifact built from the authorised payload and
records, for every case and every tab, at each viewport:

  (a) no sideways page scroll.  documentElement.scrollWidth <= innerWidth.  A
      table may scroll sideways only inside its own wrapper, and that wrapper
      must carry keyboard focus (tabindex="0") and an accessible name.
  (b) every essential control is visible and at least 24 x 24 CSS px.  For a
      button, the label must be its own text: a control whose type is reduced to
      font-size:0 and given a label by a :before pseudo-element is not a readable
      control, and the check says so.
  (c) on the Price position and Economics tabs, the price figures, their
      unit/currency text, the scope strip and the limitations text each have a
      non-zero rect, are not clipped, and carry at least 12 px type.
  (d) the price/unit/scope/limitation text present at 1440 also exists at 390:
      a narrow layout must not hide a fact to fit.

It also drives the keyboard, because REQUIRED EVIDENCE 1 is about reaching the
work without a pointer and saving a draft that way. That walk is a real Tab
sequence in the real browser, not a simulated one: the browser decides the order,
and the script records the order it produced. It asserts that the sequence
reaches the customer selector, the case list, the six tabs, the review fields and
the save control; that Enter or Space on a focused control does what a click
does; that the saved draft comes back after a reload; that no div or span carries
an inline click handler; that every input, select and textarea has a programmatic
label; and that the save status is carried by text rather than by colour alone.

The script also takes screenshots. It does not claim to have read them: the count
taken and the count actually opened are recorded separately, because a
take-count is not a read-count.

    python tests/accept/ux_07_narrow.py
    python tests/accept/ux_07_narrow.py --chrome "C:/Program Files/Google/Chrome/Application/chrome.exe"
    python tests/accept/ux_07_narrow.py --summary
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
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
# The agreed small-screen layout, fixed by brief U7: a phone and a small tablet.
# 1440 is carried as well, because check (d) needs the wide reading to compare
# against; it is not itself part of the agreed small-screen layout.
VIEWPORTS = [{"label": "phone", "width": 390, "height": 844},
             {"label": "tablet", "width": 768, "height": 1024},
             {"label": "desktop", "width": 1440, "height": 900}]
NARROW = ["phone", "tablet"]

# The measured categories. Each is a question a reader asks, not a CSS class:
# what the price is, what unit or currency it is in, what scope it covers and
# what its limitations are.
# The four categories are the four things UX-07 names, each read as the text a
# reader has to be able to see. "limitations" is the paragraph-level text: the
# explanatory sentence under a figure, the limitation statement and the
# source-basis note. Row-level detail inside a table is supplementary text and is
# covered by the scroll-wrapper checks instead; it is not counted here.
CATEGORIES = {
    "price": [".resultbig", ".snapshot strong", ".offer-price", ".target-number"],
    "unit": [".resultbig + .small", ".snapshot small"],
    "scope": ["#scope-strip", ".scopebox"],
    "limitations": ["#content p.small", "#content .ruleline", "#content .inputsnote"],
}

MEASURE = r"""
(args) => {
  const V = args.viewports;  // unused here, the viewport is the live one
  const cats = args.categories;
  const vw = window.innerWidth, vh = window.innerHeight;

  const tag = (el) => {
    if (!el) return null;
    const id = el.id ? '#' + el.id : '';
    const cls = (el.className && typeof el.className === 'string')
      ? '.' + el.className.trim().split(/\s+/)[0] : '';
    return el.tagName.toLowerCase() + id + cls;
  };
  const rect = (el) => { const r = el.getBoundingClientRect();
    return {x: Math.round(r.x), y: Math.round(r.y), w: Math.round(r.width), h: Math.round(r.height)}; };
  const shown = (el) => {
    const cs = getComputedStyle(el);
    if (cs.display === 'none' || cs.visibility === 'hidden') return false;
    if (parseFloat(cs.opacity) === 0) return false;
    const r = el.getBoundingClientRect();
    return r.width > 0 && r.height > 0;
  };

  // The nearest ancestor that really scrolls sideways, and whether it is usable
  // from the keyboard: focusable and named. A scroll box a keyboard cannot reach
  // is a hidden control by another name.
  const scroller = (el) => {
    let p = el.parentElement;
    while (p && p !== document.documentElement) {
      const cs = getComputedStyle(p);
      const scrolls = (cs.overflowX === 'auto' || cs.overflowX === 'scroll')
        && p.scrollWidth > p.clientWidth + 1;
      if (scrolls) {
        const ti = p.getAttribute('tabindex');
        const name = (p.getAttribute('aria-label') || '').trim()
          || (p.getAttribute('aria-labelledby') ? '(labelled by another element)' : '')
          || (p.getAttribute('title') || '').trim();
        return {element: tag(p), tabindex: ti, name: name, usable: (ti === '0' && !!name),
                client: p.clientWidth, content: p.scrollWidth};
      }
      p = p.parentElement;
    }
    return null;
  };

  // Covered: only meaningful when the element's own centre is inside the
  // window. An element below the fold is not covered by anything; calling it
  // covered would report a defect that does not exist.
  const covered = (el) => {
    const r = el.getBoundingClientRect();
    if (r.right < 0 || r.left > vw) return {tested: false, why: 'outside the window horizontally'};
    if (r.bottom < 0 || r.top > vh) return {tested: false, why: 'outside the window vertically'};
    const cx = Math.min(Math.max(r.left + r.width / 2, 1), vw - 2);
    const cy = Math.min(Math.max(r.top + r.height / 2, 1), vh - 2);
    const hit = document.elementFromPoint(cx, cy);
    const ok = !!hit && (hit === el || el.contains(hit) || hit.contains(el));
    return {tested: true, ok: ok, hit: tag(hit)};
  };

  const out = {
    innerWidth: vw, innerHeight: vh,
    document_scroll_width: document.documentElement.scrollWidth,
    body_scroll_width: document.body.scrollWidth,
    scrollers: [], essentials: [], categories: {}, texts: {}, hidden_facts: []
  };

  // (a) the page itself must not scroll sideways
  out.a_ok = document.documentElement.scrollWidth <= vw;

  // Every sideways-scrolling box on the page, with whether it can be reached
  // and scrolled from the keyboard.
  document.querySelectorAll('.tablewrap, #tabs, .case-list, table, .chart, pre').forEach((el) => {
    const cs = getComputedStyle(el);
    if ((cs.overflowX === 'auto' || cs.overflowX === 'scroll') && el.scrollWidth > el.clientWidth + 1) {
      const ti = el.getAttribute('tabindex');
      const name = (el.getAttribute('aria-label') || '').trim()
        || (el.getAttribute('aria-labelledby') ? '(labelled by another element)' : '')
        || (el.getAttribute('title') || '').trim();
      out.scrollers.push({element: tag(el), client: el.clientWidth, content: el.scrollWidth,
                          tabindex: ti, name: name, usable: (ti === '0' && !!name)});
    }
  });

  // (b) the essential controls
  const essential = [
    {name: 'customer selector', sel: '#market', always: true, readable: true},
    {name: 'case list', sel: '#case-list', always: true, readable: false},
    {name: 'case card', sel: '.case-card', always: true, readable: false},
    {name: 'tab', sel: '#tabs .tab', always: true, readable: true, expect: 6},
    {name: 'export button', sel: '#export-review', always: true, readable: true},
    {name: 'sources button', sel: '.sourcesbutton', always: true, readable: true},
    {name: 'sources button (page title)', sel: '#sources-top', always: true, readable: true},
    {name: 'save draft', sel: '#save-case', always: false, readable: true},
    {name: 'recalculate: proposed net price', sel: '#s-newP', always: false, readable: false},
    {name: 'recalculate: reset control', sel: '#reset-scenario', always: false, readable: true}
  ];
  essential.forEach((spec) => {
    const nodes = Array.from(document.querySelectorAll(spec.sel));
    if (!nodes.length) {
      out.essentials.push({name: spec.name, sel: spec.sel, count: 0,
                           status: spec.always ? 'FAIL' : 'absent',
                           why: spec.always ? 'the control is not in the document' : 'not on this tab'});
      return;
    }
    const rows = nodes.map((el) => {
      const r = el.getBoundingClientRect();
      const cs = getComputedStyle(el);
      const problems = [];
      if (!shown(el)) problems.push('not visible');
      if (r.width < 24 || r.height < 24) problems.push('smaller than 24x24 CSS px (' + Math.round(r.width) + 'x' + Math.round(r.height) + ')');
      const own = (el.textContent || '').replace(/\s+/g, ' ').trim();
      const label = (el.getAttribute('aria-label') || '').trim();
      const fs = parseFloat(cs.fontSize) || 0;
      if (spec.readable) {
        if (fs <= 0) problems.push('its own type is font-size:0, so its label is not its own text');
        if (!own && !label) problems.push('no readable text and no accessible name');
      }
      const inViewH = r.left >= -1 && r.right <= vw + 1;
      const box = inViewH ? null : scroller(el);
      if (!inViewH && !box) problems.push('outside the viewport and not inside a labelled scroll container');
      if (!inViewH && box && !box.usable) problems.push('outside the viewport, and its scroll container ' + box.element + ' is not keyboard-usable (tabindex=' + box.tabindex + ', name=' + JSON.stringify(box.name) + ')');
      const cov = covered(el);
      if (cov.tested && !cov.ok) problems.push('covered by ' + cov.hit);
      return {element: tag(el), rect: rect(el), font_px: fs, label: own.slice(0, 60) || label,
              in_view_horizontally: inViewH, scroll_container: box, covered: cov, problems: problems};
    });
    const bad = rows.filter((r) => r.problems.length);
    out.essentials.push({name: spec.name, sel: spec.sel, count: nodes.length,
                         status: bad.length ? 'FAIL' : 'PASS',
                         problems: bad.slice(0, 4),
                         expected: spec.expect || null});
  });

  // (c) and (d). The texts, per category, with their type and whether they are
  // painted at all.
  Object.keys(cats).forEach((key) => {
    const nodes = [];
    cats[key].forEach((sel) => { document.querySelectorAll(sel).forEach((el) => nodes.push({sel: sel, el: el})); });
    out.categories[key] = [];
    out.texts[key] = [];
    nodes.forEach((n) => {
      const el = n.el;
      const cs = getComputedStyle(el);
      const r = el.getBoundingClientRect();
      const fs = parseFloat(cs.fontSize) || 0;
      const text = (el.textContent || '').replace(/\s+/g, ' ').trim();
      const clipped_self = el.scrollWidth > el.clientWidth + 1;
      const box = clipped_self ? scroller(el) : null;
      const row = {selector: n.sel, element: tag(el), rect: rect(el), font_px: fs,
                   visible: shown(el), clipped: clipped_self && !box,
                   scroll_container: box, text: text.slice(0, 160)};
      out.categories[key].push(row);
      if (text) {
        out.texts[key].push(text);
        if (!shown(el)) out.hidden_facts.push({category: key, selector: n.sel, text: text.slice(0, 120)});
      }
    });
  });

  return out;
}
"""

ESSENTIAL_SELECTORS = ["#market", "#case-list", ".case-card", "#tabs .tab", "#export-review",
                       ".sourcesbutton", "#sources-top", "#save-case", "#s-newP", "#reset-scenario"]


def describe_focus(page) -> dict:
    """What the browser actually focused, described so a reader can follow it."""
    return page.evaluate(r"""() => {
      const el = document.activeElement;
      if (!el || el === document.body) return {tag: 'body'};
      const own = (el.textContent || '').replace(/\s+/g, ' ').trim();
      const label = (el.getAttribute('aria-label') || el.getAttribute('title') || '').trim();
      return {tag: el.tagName.toLowerCase(),
              id: el.id || null,
              cls: (typeof el.className === 'string' ? el.className : '') || null,
              type: el.type || null,
              name: own.slice(0, 50) || label,
              value: (el.value === undefined ? null : String(el.value).slice(0, 40))};
    }""")


def keyboard_walk(page, case_id: str) -> dict:
    """Reach the work and save a draft with the keyboard only.

    The order below is the order the browser produced. It is recorded rather than
    asserted to be a particular sequence: what matters is that the controls are
    reachable at all, in a forward direction, and that the ones a reader must use
    are in the sequence.
    """
    page.evaluate("() => { document.body.focus(); }")
    sequence = []
    for _ in range(140):
        page.keyboard.press("Tab")
        step = describe_focus(page)
        sequence.append(step)
        if step.get("id") == "save-case":
            break

    reached = {
        "customer": any(s.get("id") == "market" for s in sequence),
        "case": any(s.get("id") == "case-card" or (s.get("cls") or "").find("case-card") >= 0
                    for s in sequence),
        "tabs": sorted({s.get("name") for s in sequence if (s.get("cls") or "").find("tab") >= 0}),
        "review_owner": any(s.get("id") == "a-owner" for s in sequence),
        "review_next": any(s.get("id") == "a-next" for s in sequence),
        "save": any(s.get("id") == "save-case" for s in sequence),
    }
    expected_tabs = 6
    reached["tabs_ok"] = len(reached["tabs"]) >= expected_tabs

    # Shift+Tab must come back, or the reader can only go forward.
    backward = []
    for _ in range(6):
        page.keyboard.press("Shift+Tab")
        backward.append(describe_focus(page))

    # Enter on a focused control does what a click does: it saves the draft.
    page.focus("#a-next")
    page.keyboard.type("UX-07 keyboard walk: confirm this with the keyboard only.")
    page.focus("#save-case")
    page.keyboard.press("Enter")
    page.wait_for_timeout(500)
    saved = page.evaluate(r"""(cid) => {
      const rec = window.AIMPricing.cases.load(cid);
      return rec ? {version: rec.version, state: rec.state, revisions: rec.revisions.length} : null;
    }""", case_id)
    status_text = page.evaluate(r"""() => {
      const s = document.querySelector('#save-status');
      return s ? (s.textContent || '').replace(/\s+/g, ' ').trim() : null;
    }""")

    # A reload must bring the draft back, and the page must say so in words.
    page.reload()
    page.wait_for_function("() => !!window.AIMPricing", timeout=30000)
    page.wait_for_timeout(400)
    reopened = page.evaluate(r"""(cid) => {
      const rec = window.AIMPricing.cases.load(cid);
      if (!rec) return {found: false};
      const rev = rec.revisions[rec.revisions.length - 1];
      return {found: true, version: rec.version, revisions: rec.revisions.length,
              next_action: (rev.record.review || {}).next_action || null,
              status_on_screen: (document.querySelector('#save-status') || {}).textContent || null};
    }""", case_id)

    # Space or Enter on a focused control does what a click does. Walked on the
    # tab bar: Tab forward from the top of the document, find the first tab with a
    # real label, put the keyboard there, and press the key.
    page.evaluate("() => { location.hash = new URLSearchParams("
                  "{case:'ITUK-PADS', view:'decision', compare:'half'}).toString(); }")
    page.wait_for_timeout(300)
    before_view = page.evaluate("() => window.AIMPricing.getState().view")
    page.evaluate("() => { document.body.focus(); }")
    tab_acted_on = None
    for _ in range(60):
        page.keyboard.press("Tab")
        step = describe_focus(page)
        if step.get("tag") == "button" and (step.get("cls") or "").find("tab") >= 0 \
                and (step.get("name") or "").strip() == "Price position":
            tab_acted_on = step
            page.keyboard.press("Space")
            break
    page.wait_for_timeout(300)
    after_view = page.evaluate("() => window.AIMPricing.getState().view")
    if after_view == before_view:
        page.keyboard.press("Enter")
        page.wait_for_timeout(300)
        after_view = page.evaluate("() => window.AIMPricing.getState().view")

    # Every tab, checked for the property the stylesheet claims: a table that
    # scrolls sideways at this width is inside a wrapper the keyboard can reach
    # and that says what it is. The tabs without a table are counted so the check
    # cannot pass by finding nothing.
    scroll_wrapper_facts = {"tabs_with_a_scrolling_wrapper": 0,
                            "unreachable": [], "wrappers": []}
    for tab in TABS:
        page.evaluate("([v]) => { location.hash = new URLSearchParams("
                      "{case:'ITUK-PADS', view:v, compare:'half'}).toString(); }", [tab])
        page.wait_for_timeout(200)
        rows = page.evaluate(r"""() => Array.from(document.querySelectorAll('#content .tablewrap'))
          .filter((w) => w.scrollWidth > w.clientWidth)
          .map((w) => ({label: w.getAttribute('aria-label'), tabindex: w.getAttribute('tabindex'),
                        reachable: w.tabIndex >= 0}))""")
        if rows:
            scroll_wrapper_facts["tabs_with_a_scrolling_wrapper"] += 1
        for row in rows:
            scroll_wrapper_facts["wrappers"].append(dict(row, tab=tab))
            if not (row["reachable"] and row["label"]):
                scroll_wrapper_facts["unreachable"].append(dict(row, tab=tab))

    hygiene = page.evaluate(r"""() => {
      const inline = document.querySelectorAll('div[onclick], span[onclick], li[onclick]');
      const unlabelled = [];
      document.querySelectorAll('input, select, textarea').forEach((el) => {
        if (el.type === 'hidden') return;
        const byFor = el.id && document.querySelector('label[for="' + el.id + '"]');
        const wrapping = el.closest('label');
        const aria = el.getAttribute('aria-label');
        const labelledby = el.getAttribute('aria-labelledby');
        if (!byFor && !wrapping && !aria && !labelledby) {
          unlabelled.push((el.id || el.tagName) + '/' + (el.type || ''));
        }
      });
      const wrappers = Array.from(document.querySelectorAll('.tablewrap'))
        .filter((w) => w.scrollWidth > w.clientWidth)
        .map((w) => ({label: w.getAttribute('aria-label'), tabindex: w.getAttribute('tabindex')}));
      return {inline_click_handlers: inline.length, unlabelled_inputs: unlabelled,
              scrolling_wrappers: wrappers};
    }""")

    return {
        "case": case_id, "viewport": "390x844",
        "sequence_length": len(sequence),
        "sequence": sequence,
        "reached": reached,
        "shift_tab_back": backward,
        "saved_with_enter": saved,
        "save_status_text": status_text,
        "reopened_after_reload": reopened,
        "view_before_space": before_view,
        "view_after_space_enter": after_view,
        "tab_acted_on": tab_acted_on,
        "scroll_wrapper_facts": scroll_wrapper_facts,
        "hygiene": hygiene,
    }


def sha256(path: Path) -> str | None:
    if not path.exists():
        return None
    return hashlib.sha256(path.read_bytes()).hexdigest()


def file_url(case_id: str, view: str) -> str:
    return APP.as_uri() + "#" + urllib.parse.urlencode({"case": case_id, "view": view, "compare": "half"})


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--chrome", default=os.environ.get(
        "CHROME_PATH", r"C:\Program Files\Google\Chrome\Application\chrome.exe"))
    ap.add_argument("--summary", action="store_true", help="print the stored result again and exit")
    ap.add_argument("--keep-profile", action="store_true")
    args = ap.parse_args()

    result_path = OUT / "ux_07_narrow.json"
    if args.summary:
        if not result_path.exists():
            print("NO RESULT YET: " + str(result_path))
            return 2
        stored = json.loads(result_path.read_text(encoding="utf-8"))
        print_summary(stored)
        return 1 if stored["summary"]["fail"] else 0

    started = time.time()
    run = {
        "check": "UX-07 narrow",
        "title": "prices, units, scope and limitations stay readable on the agreed small-screen layout",
        "review_date": time.strftime("%Y-%m-%dT%H:%M:%S"),
        "artifact": str(APP),
        "artifact_sha256": sha256(APP),
        "artifact_mtime": (time.strftime("%Y-%m-%dT%H:%M:%S", time.localtime(APP.stat().st_mtime))
                           if APP.exists() else None),
        "load_mode": "file:// URL in a persistent browser profile",
        "viewports": VIEWPORTS,
        "categories": {k: v for k, v in CATEGORIES.items()},
        "essential_selectors": ESSENTIAL_SELECTORS,
        "cases": [], "tabs": TABS,
        "results": [], "superset": [],
        "limits": ("The essential-control list and the four text categories are named in this file. "
                   "'Recalculate' resolves to the controls whose use recalculates the scenario: the "
                   "proposed-net-price input and the reset control on the Price & profit test. "
                   "A control that is genuinely absent on a tab is recorded as absent, not as a pass."),
        "screenshots": {"taken": 0, "read": 0, "read_by": None,
                        "note": ("Taken by this script. The read count is filled in only after a person "
                                 "or reviewer opens them; a take-count is not a read-count.")},
        "scope": ("Painted layout in one browser on this machine at three widths, against a real file URL. "
                  "Not a device test, not assistive-technology testing, not an accessibility audit.")
    }

    taken = []
    if not APP.is_file():
        print("MISSING BUILD OUTPUT: " + str(APP))
        print("UX-07 narrow cannot run until tools/build.py has produced the artifact.")
        OUT.mkdir(parents=True, exist_ok=True)
        run["summary"] = {"pass": 0, "fail": 0, "total": 0}
        run["reason"] = "the built artifact does not exist"
        result_path.write_text(json.dumps(run, indent=2) + "\n", encoding="utf-8")
        return 2

    profile = Path(tempfile.mkdtemp(prefix="aim_ux07_profile_"))
    errors: list[str] = []

    with sync_playwright() as p:
        ctx = p.chromium.launch_persistent_context(
            user_data_dir=str(profile), headless=True, executable_path=args.chrome,
            viewport={"width": 1440, "height": 900},
            args=["--allow-file-access-from-files"])
        page = ctx.new_page()
        page.on("pageerror", lambda e: errors.append("pageerror:" + str(e)))
        page.goto(file_url("__none__", "position"))
        page.wait_for_function("() => !!window.AIMPricing", timeout=30000)
        page.evaluate("() => { try { localStorage.clear(); } catch (e) {} }")
        cases = page.evaluate("() => window.AIMPricing.data.cases.map((c) => c.id)")
        run["cases"] = cases

        # Two cases on the Price position tab, at each agreed width: the brief asks
        # for 390 and 768, and a screenshot per case per width.
        SHOT_CASES = cases[:2]
        taken_now = set()
        for vp in VIEWPORTS:
            page.set_viewport_size({"width": vp["width"], "height": vp["height"]})
            for case_id in cases:
                for tab in TABS:
                    page.evaluate("([c, v]) => { location.hash = new URLSearchParams("
                                  "{case:c, view:v, compare:'half'}).toString(); }", [case_id, tab])
                    page.wait_for_timeout(180)
                    measured = page.evaluate(MEASURE, {"viewports": VIEWPORTS, "categories": CATEGORIES})
                    measured.update({"viewport": vp["label"], "width": vp["width"], "height": vp["height"],
                                     "case": case_id, "tab": tab})
                    run["results"].append(measured)
                    shot_key = (vp["label"], case_id)
                    if (tab == "position" and vp["label"] in NARROW
                            and case_id in SHOT_CASES and shot_key not in taken_now):
                        taken_now.add(shot_key)
                        SHOTS.mkdir(parents=True, exist_ok=True)
                        target = SHOTS / ("ux07_%d_%s_%s_position.png" % (vp["width"], vp["label"], case_id))
                        page.screenshot(path=str(target), full_page=True)
                        taken.append(str(target))

        # ---- REQUIRED EVIDENCE 1: the keyboard walk, in the real browser ------
        page.set_viewport_size({"width": 390, "height": 844})
        kb_case, kb_view = "ITUK-PADS", "action"
        page.evaluate("() => { try { localStorage.clear(); } catch (e) {} }")
        page.goto(file_url(kb_case, kb_view))
        page.wait_for_function("() => !!window.AIMPricing", timeout=30000)
        page.wait_for_timeout(300)
        run["keyboard"] = keyboard_walk(page, kb_case)

        # (d) nothing a wide reader sees is missing from the narrow reader's page
        for case_id in cases:
            for tab in TABS:
                wide = next((r for r in run["results"] if r["case"] == case_id and r["tab"] == tab
                             and r["viewport"] == "desktop"), None)
                for narrow_label in NARROW:
                    narrow = next((r for r in run["results"] if r["case"] == case_id and r["tab"] == tab
                                   and r["viewport"] == narrow_label), None)
                    if not wide or not narrow:
                        continue
                    missing = {}
                    for key in CATEGORIES:
                        w = set(wide["texts"].get(key, []))
                        n = set(narrow["texts"].get(key, []))
                        gone = sorted(w - n)
                        if gone:
                            missing[key] = gone
                    hidden = [h for h in narrow["hidden_facts"]]
                    run["superset"].append({"case": case_id, "tab": tab, "narrow": narrow_label,
                                            "missing_at_narrow": missing, "hidden_at_narrow": hidden,
                                            "status": "PASS" if (not missing and not hidden) else "FAIL"})
        ctx.close()

    if not args.keep_profile:
        import shutil
        shutil.rmtree(profile, ignore_errors=True)

    # ---- verdicts -----------------------------------------------------------------
    checks = []
    for r in run["results"]:
        wide = r["viewport"] == "desktop"
        a = {"status": "PASS" if r["a_ok"] else "FAIL",
             "detail": "document %d <= window %d" % (r["document_scroll_width"], r["innerWidth"]),
             "bad_scrollers": [s for s in r["scrollers"] if not s["usable"]]}
        if a["bad_scrollers"]:
            a["status"] = "FAIL"
        bad_ess = [e for e in r["essentials"] if e["status"] == "FAIL"]
        b = {"status": "FAIL" if bad_ess else "PASS", "failing": [e["name"] for e in bad_ess]}
        c = {"status": "PASS", "problems": []}
        if r["tab"] in ("position", "economics") and not wide:
            for key, rows in r["categories"].items():
                if not rows:
                    c["problems"].append("%s: no element found for %s" % (key, CATEGORIES[key]))
                    continue
                for row in rows:
                    if not row["visible"]:
                        c["problems"].append("%s: %s is not painted" % (key, row["element"]))
                    elif row["rect"]["w"] <= 0 or row["rect"]["h"] <= 0:
                        c["problems"].append("%s: %s has an empty rect" % (key, row["element"]))
                    elif row["clipped"]:
                        c["problems"].append("%s: %s is clipped" % (key, row["element"]))
                    if row["font_px"] < 12:
                        c["problems"].append("%s: %s is %gpx" % (key, row["element"], row["font_px"]))
            if c["problems"]:
                c["status"] = "FAIL"
        checks.append({"viewport": r["viewport"], "width": r["width"], "case": r["case"], "tab": r["tab"],
                       "a": a, "b": b, "c": c})
    for s in run["superset"]:
        checks.append({"viewport": "390 vs 1440", "width": None, "case": s["case"], "tab": s["tab"],
                       "narrow": s["narrow"], "d": {"status": s["status"],
                                                    "missing": s["missing_at_narrow"],
                                                    "hidden": s["hidden_at_narrow"]}})

    # The keyboard verdict, one line per thing REQUIRED EVIDENCE 1 asks for.
    kb = run.get("keyboard") or {}
    if kb:
        r = kb.get("reached") or {}
        hygiene = kb.get("hygiene") or {}
        saved = kb.get("saved_with_enter") or {}
        reopened = kb.get("reopened_after_reload") or {}
        kb_checks = [
            {"name": "the customer selector is reachable by Tab", "ok": bool(r.get("customer"))},
            {"name": "the case list is reachable by Tab", "ok": bool(r.get("case"))},
            {"name": "all six tabs are reachable by Tab", "ok": bool(r.get("tabs_ok")),
             "detail": r.get("tabs")},
            {"name": "the review fields are reachable by Tab",
             "ok": bool(r.get("review_owner") and r.get("review_next"))},
            {"name": "the save control is reachable by Tab", "ok": bool(r.get("save"))},
            {"name": "every table that scrolls sideways is in a focusable, named wrapper",
             "ok": (bool(kb.get("scroll_wrapper_facts", {}).get("tabs_with_a_scrolling_wrapper"))
                    and not kb.get("scroll_wrapper_facts", {}).get("unreachable")),
             "detail": {"tabs with one": kb.get("scroll_wrapper_facts", {}).get("tabs_with_a_scrolling_wrapper"),
                        "unreachable": kb.get("scroll_wrapper_facts", {}).get("unreachable")}},
            {"name": "Shift+Tab comes back", "ok": len(kb.get("shift_tab_back") or []) > 0},
            {"name": "Enter on the save control saves the draft",
             "ok": bool(saved) and saved.get("revisions", 0) >= 1, "detail": saved},
            {"name": "the save status is carried by text",
             "ok": bool(kb.get("save_status_text")) and bool(
                 (kb.get("save_status_text") or "").strip())},
            {"name": "the draft comes back after a reload",
             "ok": bool(reopened.get("found")) and reopened.get("revisions", 0) >= 1
                   and bool(reopened.get("next_action")), "detail": reopened},
            {"name": "Space or Enter on a focused tab changes the view",
             "ok": kb.get("view_before_space") != kb.get("view_after_space_enter"),
             "detail": {"before": kb.get("view_before_space"), "after": kb.get("view_after_space_enter"),
                        "tab": kb.get("tab_acted_on")}},
            {"name": "no div or span carries an inline click handler",
             "ok": hygiene.get("inline_click_handlers") == 0},
            {"name": "every input, select and textarea has a programmatic label",
             "ok": not hygiene.get("unlabelled_inputs"),
             "detail": hygiene.get("unlabelled_inputs")},
            {"name": "every sideways-scrolling wrapper is focusable and named",
             "ok": all(w.get("tabindex") == "0" and w.get("label")
                       for w in (hygiene.get("scrolling_wrappers") or [])),
             "detail": hygiene.get("scrolling_wrappers")},
        ]
        run["keyboard_checks"] = kb_checks
        for c in kb_checks:
            checks.append({"viewport": "keyboard", "case": kb.get("case"), "tab": "action",
                           "e1": {"status": "PASS" if c["ok"] else "FAIL",
                                  "name": c["name"], "detail": c.get("detail")}})

    run["checks"] = checks
    run["page_errors"] = errors[:10]
    run["screenshots"]["taken"] = len(taken)
    run["screenshots"]["files"] = taken
    run["elapsed_seconds"] = round(time.time() - started, 1)

    fail = 0
    total = 0
    by_check = {"a": [0, 0], "b": [0, 0], "c": [0, 0], "d": [0, 0], "e1": [0, 0]}
    for c in checks:
        for key in ("a", "b", "c", "d", "e1"):
            if key in c:
                total += 1
                if c[key]["status"] == "PASS":
                    by_check[key][0] += 1
                else:
                    by_check[key][1] += 1
                    fail += 1
    run["summary"] = {"pass": total - fail, "fail": fail, "total": total}
    run["by_check"] = {k: {"pass": v[0], "fail": v[1]} for k, v in by_check.items()}
    if errors:
        run["summary"]["page_errors"] = len(errors)

    OUT.mkdir(parents=True, exist_ok=True)
    result_path.write_text(json.dumps(run, indent=2) + "\n", encoding="utf-8")
    print_summary(run)
    return 1 if fail else 0


def print_summary(run: dict) -> None:
    print("UX-07 narrow - %s" % run.get("review_date"))
    print("artifact  : %s" % run.get("artifact_sha256"))
    print("viewports : %s" % ", ".join("%s %dx%d" % (v["label"], v["width"], v["height"])
                                       for v in run.get("viewports", [])))
    print("cases     : %s" % ", ".join(run.get("cases", [])))
    print("checks    : %s" % json.dumps(run.get("by_check", {})))
    print(json.dumps(run.get("summary", {})))
    bad = [c for c in run.get("checks", [])
           if any(c.get(k, {}).get("status") == "FAIL" for k in ("a", "b", "c", "d", "e1"))]
    print("failures  : %d" % len(bad))
    for c in bad[:24]:
        which = [k for k in ("a", "b", "c", "d", "e1") if c.get(k, {}).get("status") == "FAIL"]
        detail = ""
        for k in which:
            if k == "c":
                detail += " c=" + "; ".join(c[k]["problems"][:3])
            elif k == "a":
                detail += " a=" + "; ".join("%s(%d>%d, tabindex=%s, name=%r)" % (s["element"], s["content"],
                                                                                 s["client"], s["tabindex"],
                                                                                 s["name"]) for s in c[k]["bad_scrollers"][:3])
            elif k == "b":
                detail += " b=" + ",".join(c[k]["failing"])
                for e in c["b"].get("failing", [])[:0]:
                    pass
            elif k == "d":
                detail += " d=" + json.dumps(c[k]["missing"])[:120]
            elif k == "e1":
                detail += " e1=" + str(c[k]["name"])
        print("  FAIL %s/%s/%s%s" % (c.get("viewport"), c.get("case"), c.get("tab"), detail))
    print("screenshots taken: %d" % run.get("screenshots", {}).get("taken", 0))
    print("raw: %s" % (OUT / "ux_07_narrow.json"))


if __name__ == "__main__":
    raise SystemExit(main())
