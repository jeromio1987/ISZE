"""U28 task 3 (UX-01..08) - the real built layout, measured narrow and wide.

What this proves
----------------
UX-01..08 were covered by stub-DOM tests. A stub evaluates no @media query and
paints no real shell, so it cannot answer "does this screen exist on the page a
person opens". This drives the REAL built artifact in real Chrome, at a wide and
at a narrow viewport, on every screen the product serves, and records:

  * painted            - the screen built its own content (not blank, no NaN,
                         no "undefined", no failure card)
  * part_reference_carried / context_carried - the exact part reference and the
                         working context strip travel with the screen
  * visible_controls / hidden_essential_controls
  * absent_source      - with an optional source removed, is there a LABELLED
                         narrower review rather than a blank panel (UX-06 E1)

It builds nothing and rewrites nothing. It writes the reading to
tests/accept/_out/ux_screens_wide_narrow.json, which tests/ux_screens_browser
.test.mjs reads and, in effect, dates against the artifact.

Screenshots: taken, not read by this script. The two counts are recorded
separately.

    python tests/accept/ux_screens_wide_narrow.py
    python tests/accept/ux_screens_wide_narrow.py --chrome "C:/.../chrome.exe"
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import tempfile
import time
from pathlib import Path

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "tests" / "accept" / "_out"
SHOTS = OUT / "shots"
APP = ROOT / "dist" / "ISZE_AIM_Pricing_Decisions_v04_INTERNAL.html"

VIEWPORTS = [{"label": "wide", "width": 1440, "height": 900},
             {"label": "narrow", "width": 1280, "height": 820}]

VIEWS = ["decision", "position", "objectives", "economics", "candidates", "case", "action"]

MEASURE = r"""
() => {
  const content = document.querySelector('#content');
  const text = content ? (content.innerText || '') : '';
  const defects = [];
  if (!text.trim()) defects.push('the content region is blank');
  if (text.includes('NaN')) defects.push('the screen shows NaN');
  if (text.includes('undefined')) defects.push('the screen shows undefined');
  const state = content ? content.getAttribute('data-render-state') : null;
  if (state === 'failed') defects.push('the screen painted the failure card');

  const vis = (el) => {
    if (!el) return false;
    const cs = getComputedStyle(el);
    if (cs.display === 'none' || cs.visibility === 'hidden') return false;
    if (parseFloat(cs.opacity) === 0) return false;
    const r = el.getBoundingClientRect();
    return r.width > 1 && r.height > 1;
  };

  const controls = [...document.querySelectorAll('#content button, #content select, #content input')];
  const visible = controls.filter(vis);
  const controlsInRegion = document.querySelector('#tabs') ? controls.length : controls.length;
  const hiddenEssential = controls.filter((el) => {
    const name = (el.innerText || el.getAttribute('aria-label') || el.value || '').trim();
    if (!name) return false;                    // unlabelled is a different defect
    return !vis(el);                            // named but not visible
  }).length;

  const ctx = document.querySelector('#scope-strip');
  const caseHeader = document.querySelector('#case-header');
  const headerText = caseHeader ? (caseHeader.innerText || '') : '';
  const pn = (window.AIMPricing && window.AIMPricing.data && window.AIMPricing.data.cases
    .find((c) => c.id === window.AIMPricing.getState().caseId));
  const partReferenceCarried = !!(pn && headerText.includes(pn.pn));

  return {
    render_state: state,
    chars: text.trim().length,
    defects,
    visible_controls: visible.length,
    all_controls: controlsInRegion,
    hidden_essential_controls: hiddenEssential,
    context_carried: !!(ctx && (ctx.innerText || '').trim().length > 0),
    part_reference_carried: partReferenceCarried,
    title: document.querySelector('#tabs .tab.active') ? document.querySelector('#tabs .tab.active').innerText.trim() : null
  };
}
"""


def sha256(path: Path):
    if not path.exists():
        return None
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--chrome", default=os.environ.get(
        "CHROME_PATH", r"C:\Program Files\Google\Chrome\Application\chrome.exe"))
    args = ap.parse_args()

    if not APP.is_file():
        print("MISSING BUILD OUTPUT: " + str(APP))
        print("run `python tools/build.py` first.")
        return 4

    started = time.time()
    run = {
        "check": "U28-UX-SCREENS",
        "title": "UX-01..08 measured on the real built layout, narrow and wide",
        "generated_at": time.strftime("%Y-%m-%dT%H:%M:%S"),
        "artifact": str(APP),
        "artifact_sha256": sha256(APP),
        "artifact_mtime": APP.stat().st_mtime,
        "viewports": VIEWPORTS,
        "screens": [],
        "screenshots": {"taken": 0, "read": 0, "read_by": None, "note":
                        "Taken by this script. The read count is filled in only after a person "
                        "or reviewer opens them; a take-count is not a read-count."},
        "scope": "The built synthetic-or-real artifact on this machine. A reading, not acceptance.",
    }

    profile = Path(tempfile.mkdtemp(prefix="aim_ux_screens_"))
    SHOTS.mkdir(parents=True, exist_ok=True)
    taken = []

    with sync_playwright() as pw:
        ctx = pw.chromium.launch_persistent_context(
            user_data_dir=str(profile), headless=True, executable_path=args.chrome,
            viewport={"width": 1440, "height": 900},
            args=["--allow-file-access-from-files"])
        page = ctx.new_page()

        for vp in VIEWPORTS:
            page.set_viewport_size({"width": vp["width"], "height": vp["height"]})
            for view in VIEWS:
                url = APP.as_uri() + "#case=IMOTORS-CABIN&view=" + view + "&compare=half"
                page.goto(url)
                page.wait_for_function("() => !!window.AIMPricing", timeout=30000)
                page.wait_for_timeout(250)
                row = page.evaluate(MEASURE)
                row["view"] = view
                row["viewport"] = vp["label"]
                row["width"] = vp["width"]
                row["painted"] = (row["render_state"] == "built") and not row["defects"]
                shot = SHOTS / ("ux_screens_%s_%s.png" % (view, vp["label"]))
                page.locator("#content").screenshot(path=str(shot))
                taken.append(str(shot))
                row["screenshot"] = str(shot)
                row["screenshot_sha256"] = sha256(shot)
                row["absent_source_state"] = None
                run["screens"].append(row)

        # UX-06 E1: remove an optional source and paint again. The screen must show
        # a labelled narrower review, not a blank panel.
        page.set_viewport_size({"width": 1440, "height": 900})
        page.goto(APP.as_uri() + "#case=IMOTORS-CABIN&view=decision&compare=half")
        page.wait_for_function("() => !!window.AIMPricing", timeout=30000)
        page.wait_for_timeout(250)
        removed = page.evaluate("""() => {
          const D = window.AIMPricing.data;
          const st = window.AIMPricing.getState();
          const c = D.cases.find((x) => x.id === st.caseId);
          if (!c) return { removed: false, reason: 'no case' };
          /* The optional source is the distributor's sales-to-dealer rows. Removing
             it must leave a labelled narrower review, not a blank panel. */
          (c.series || []).forEach((r) => { if (r) r.onwardQuantity = null; });
          window.AIMPricing.render();
          const content = document.querySelector('#content');
          const text = content ? (content.innerText || '') : '';
          const absent = document.querySelector('#content [data-unavailable]');
          const narrower = document.querySelector('#content [data-review-scope="narrower"]');
          const supplied = content ? content.innerText.indexOf('What ISZE billed') >= 0 : false;
          return {
            removed: true,
            panel_present: !!(absent || narrower),
            label: narrower ? (narrower.innerText || '').trim().slice(0, 120)
                 : (absent ? (absent.innerText || '').trim().split('\\n')[0] : null),
            blank: !text.trim(),
            billing_still_shown: supplied,
            defect: text.includes('NaN') || text.includes('undefined') || text.includes('did not render')
          };
        }""")
        for row in run["screens"]:
            if row["view"] == "decision" and row["viewport"] == "wide":
                row["absent_source_state"] = removed
        shot = SHOTS / "ux_screens_absent_source.png"
        page.locator("#content").screenshot(path=str(shot))
        taken.append(str(shot))

        ctx.close()

    run["screenshots"]["taken"] = len(taken)
    run["screenshots"]["files"] = taken
    run["seconds"] = round(time.time() - started, 1)
    run["summary"] = {
        "painted": sum(1 for s in run["screens"] if s["painted"]),
        "total": len(run["screens"]),
        "defects": [{"view": s["view"], "viewport": s["viewport"], "defects": s["defects"]}
                    for s in run["screens"] if s["defects"]],
    }

    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "ux_screens_wide_narrow.json").write_text(json.dumps(run, indent=2) + "\n",
                                                     encoding="utf-8")
    print(json.dumps(run["summary"], indent=2))
    print("screenshots taken: %d | read: 0 (this script does not read them)" % len(taken))
    print("reading written: " + str(OUT / "ux_screens_wide_narrow.json"))
    return 0 if not run["summary"]["defects"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
