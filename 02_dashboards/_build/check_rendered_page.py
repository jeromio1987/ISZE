"""One reusable check for a rendered shared page, pointed at any file.

CM10 in the 18 Sep error register was "check the rendered page before handover",
partly installed: qa_tonnage_keys.py did half of it, by hand, for one page. This
generalises that into a single script that can be pointed at any page under
02_dashboards/.

WHAT IT CHECKS
  1. Charts with more than one series must have a visible legend or key.
  2. Charts and the page carry a period label (CY or FY) so a year is not ambiguous.
  3. Pie or donut charts have four or fewer segments.
  4. The page does not describe a pickup as a truck.

HOW IT DECIDES (read this before trusting a result)
  Checks 1 and 3 are read from the LIVE chart objects in a real headless Chrome
  (Chart.js instances via Chart.getChart / Chart.instances, plus any HTML legend
  elements on the page). Those are structural facts, not string matches, so they
  are reported as GATE.

  Check 2 is a text search of the rendered visible text for a CY/FY pattern. A
  page can legitimately label a period another way ("12 months to June 2026",
  "H1 2025"), so a miss is a FINDING to look at, never a failure.

  Check 4 is a text search too. It cannot tell a legitimate string ("D-Max is a
  pickup, not a truck", a source column named truck, "truck" as a CSS class in
  visible text) from a real mislabel. It is reported as FINDING with the matching
  sentence attached so a human can judge, and it never fails the run.

EXIT CODE
  0 always by default (it is a report). With -GateOnStructural, exit 1 if a
  structural defect (a multi-series chart with no legend, or a donut over four
  segments) is found.

USAGE
  python check_rendered_page.py --path 02_dashboards/sales/ISZE_PMS_Tonnage_Evolution.html
  python check_rendered_page.py --dir 02_dashboards/sales --dir 02_dashboards/pricing
  python check_rendered_page.py --dir 02_dashboards/sales --report _qa_render/report.json
"""
from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

# Windows consoles default to cp1252 and a page's own text may carry arrows or
# accents. Never let a printing error crash a completed scan.
try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")
except Exception:  # noqa: BLE001
    pass

ROOT = Path(r"C:\Users\jerom\Desktop\claude\ISZE")
DEFAULT_REPORT = ROOT / "02_dashboards" / "_build" / "_qa_render" / "rendered_page_report.json"

CHROME_CANDIDATES = (
    r"C:\Program Files\Google\Chrome\Application\chrome.exe",
    r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
    os.path.expandvars(r"%LOCALAPPDATA%\Google\Chrome\Application\chrome.exe"),
)

# The probe runs in the page after its own scripts. It must not import or connect
# to anything; it reads live chart state and the visible text, then hands them
# back through the document title, which --dump-dom prints.
PROBE = r"""
(function(){
  var out = {charts: [], htmlLegends: [], errors: []};
  try {
    function readChart(ch, host){
      try {
        var ds = (ch.data && ch.data.datasets) || [];
        var leg = ch.options && ch.options.plugins && ch.options.plugins.legend;
        var type = (ch.config && ch.config.type) || ch.type || '';
        var series = ds.length;
        var segs = null;
        if ((type === 'doughnut' || type === 'pie') && ds.length > 0) {
          segs = (ds[0].data || []).length;
        }
        out.charts.push({
          host: host || '',
          type: type,
          series: series,
          legendDisplay: leg ? (leg.display !== false) : true,
          segments: segs,
          labels: (ch.data && ch.data.labels) ? ch.data.labels.length : 0,
          title: (ch.options && ch.options.plugins && ch.options.plugins.title
                  && ch.options.plugins.title.text) ? String(ch.options.plugins.title.text) : ''
        });
      } catch (e) { out.errors.push('chart:' + e); }
    }

    // Chart.js 3 and 4: Chart.getChart(canvas). Chart.js 2: Chart.instances.
    var canvases = document.querySelectorAll('canvas');
    for (var i = 0; i < canvases.length; i++) {
      var cv = canvases[i];
      var ch = null;
      if (window.Chart && window.Chart.getChart) { ch = window.Chart.getChart(cv); }
      if (!ch && window.Chart && window.Chart.instances) {
        var insts = window.Chart.instances;
        var keys = Object.keys(insts);
        for (var k = 0; k < keys.length; k++) {
          var c2 = insts[keys[k]];
          if (c2 && c2.canvas === cv) { ch = c2; break; }
        }
      }
      if (ch) { readChart(ch, cv.id || cv.className || ('canvas' + i)); }
    }
    // Some pages build charts on detached canvases or swap them; catch the rest.
    if (window.Chart) {
      var seen = {};
      for (var i2 = 0; i2 < out.charts.length; i2++) { seen[out.charts[i2].host] = 1; }
      if (window.Chart.instances) {
        var ks = Object.keys(window.Chart.instances);
        for (var j = 0; j < ks.length; j++) {
          var c = window.Chart.instances[ks[j]];
          var h = (c && c.canvas) ? (c.canvas.id || c.canvas.className || '') : '';
          if (h && !seen[h]) { seen[h] = 1; readChart(c, h); }
        }
      }
    }
    // HTML legends (a page may show a key outside the canvas).
    var legEls = document.querySelectorAll('.legend, [class*="legend"], [id*="legend"]');
    for (var m = 0; m < legEls.length; m++) {
      var el = legEls[m];
      var visible = !!(el.offsetWidth || el.offsetHeight || el.getClientRects().length);
      out.htmlLegends.push({cls: el.className || el.id || '', visible: visible,
                            text: (el.textContent || '').trim().slice(0, 120)});
    }
    // Static SVG charts (the SSR fallbacks) with more than one colour series.
    out.ssrCharts = document.querySelectorAll('.ssr-chart, .ssr-svg').length;
    // Any visual marker at all, so "no charts found" is only said when the page
    // really carries nothing chart-like rather than when the probe missed a form.
    out.svgCount = document.querySelectorAll('svg').length;
    out.canvasCount = document.querySelectorAll('canvas').length;
    out.tableCount = document.querySelectorAll('table').length;
    out.bodyText = (document.body && document.body.innerText) ? document.body.innerText.slice(0, 300000) : '';
    out.pageTitle = (document.title || '').slice(0, 200);
  } catch (e) {
    out.errors.push('top:' + String(e));
  }
  return JSON.stringify(out);
})()
"""


def find_chrome() -> str:
    for c in CHROME_CANDIDATES:
        if c and Path(c).exists():
            return c
    sys.exit("chrome not found in any known location")


def dump_page(chrome: str, page: Path, timeout: int) -> dict:
    """Load the page in headless Chrome with the probe injected, return its result.

    The probe copy is written beside the original so the page's own relative
    paths (sibling JSON, inline assets) still resolve exactly as they do for
    Jerome. It is removed again in the finally block.
    """
    probe_file = page.parent / f"_qa_render_probe_{os.getpid()}.html"
    try:
        src = page.read_text(encoding="utf-8", errors="replace")
        inject = (
            '<script>window.addEventListener("load",function(){setTimeout(function(){'
            'try{document.title="QA::"+' + PROBE + ';}catch(e){document.title="QA::{\\"errors\\":[\\"inject\\"]}";}'
            '},2500);});</script>'
        )
        if "</body>" in src:
            src = src.replace("</body>", inject + "</body>", 1)
        else:
            src = src + inject
        probe_file.write_text(src, encoding="utf-8")

        profile = tempfile.mkdtemp(prefix="qa_render_")
        try:
            res = subprocess.run(
                [chrome, "--headless=new", "--disable-gpu", "--no-first-run",
                 "--no-default-browser-check", "--allow-file-access-from-files",
                 f"--user-data-dir={profile}", "--virtual-time-budget=12000",
                 "--dump-dom", "file:///" + str(probe_file).replace("\\", "/")],
                capture_output=True, text=True, encoding="utf-8", errors="replace",
                timeout=timeout,
            )
            dom = res.stdout or ""
        finally:
            shutil.rmtree(profile, ignore_errors=True)

        m = re.search(r"<title>QA::(.*?)</title>", dom, re.S)
        if not m:
            return {"errors": ["probe did not run"], "ok": False}
        import html as htmlmod
        data = json.loads(htmlmod.unescape(m.group(1)))
        data["ok"] = True
        return data
    except subprocess.TimeoutExpired:
        return {"errors": ["timeout"], "ok": False}
    except Exception as exc:  # noqa: BLE001
        return {"errors": [f"{type(exc).__name__}: {exc}"], "ok": False}
    finally:
        try:
            probe_file.unlink()
        except OSError:
            pass


# --------------------------------------------------------------------------- #
# The four checks. Each returns (status, message). status is one of:
#   GATE    - a structural defect, measurable, not a string match
#   FINDING - worth a human look, cannot be told from a legitimate string
#   OK
# --------------------------------------------------------------------------- #

PERIOD_RE = re.compile(r"\b(?:CY|FY)\s?-?\d{2,4}\b", re.I)
PERIOD_WORDS_RE = re.compile(
    r"\b(?:calendar year|fiscal year|full year|year to date|ytd|"
    r"12 months to|rolling 12|h[12] \d{4}|jan(?:uary)?\s*[-–]\s*(?:dec|jun))\b", re.I)
PICKUP_WORDS = ("d-max", "dmax", "pickup", "pick-up", "pick up")
TRUCK_RE = re.compile(r"\btrucks?\b", re.I)


def check_legends(data: dict) -> list[tuple[str, str]]:
    """Every chart drawing more than one series must show a visible key."""
    results = []
    charts = data.get("charts") or []
    html_legends = [l for l in (data.get("htmlLegends") or []) if l.get("visible")]
    for c in charts:
        if c.get("series", 0) > 1 and c.get("legendDisplay") is False and not html_legends:
            results.append((
                "GATE",
                f"chart '{c.get('host')}' ({c.get('type')}) draws {c.get('series')} series "
                f"with legend.display=false and no visible HTML key",
            ))
    if not charts and data.get("ssrCharts", 0) == 0:
        # Say this only when the page carries nothing chart-shaped at all.
        if data.get("svgCount", 0) or data.get("canvasCount", 0):
            results.append((
                "FINDING",
                f"no chart object was readable, but the page has {data.get('svgCount', 0)} svg "
                f"and {data.get('canvasCount', 0)} canvas elements. The legend check could not "
                f"be applied here - look at it by eye.",
            ))
        else:
            results.append((
                "FINDING",
                f"no chart of any kind found ({data.get('tableCount', 0)} tables). "
                f"Fine if the page is a table or prose page; check by eye if it should have charts.",
            ))
    return results


def check_period(data: dict) -> list[tuple[str, str]]:
    """Charts carry a period label so a year is not ambiguous."""
    text = data.get("bodyText") or ""
    if PERIOD_RE.search(text) or PERIOD_WORDS_RE.search(text):
        return []
    return [(
        "FINDING",
        "no CY/FY period label found in the visible text; a year could be read ambiguously. "
        "The page may label its period another way - confirm by eye before acting.",
    )]


def check_segments(data: dict) -> list[tuple[str, str]]:
    """Pie or donut charts have four or fewer segments."""
    results = []
    for c in data.get("charts") or []:
        if c.get("segments") is not None and c["segments"] > 4:
            results.append((
                "GATE",
                f"chart '{c.get('host')}' is a {c.get('type')} with {c['segments']} segments "
                f"(more than four; use a ranked bar instead)",
            ))
    return results


def check_body_type(data: dict) -> list[tuple[str, str]]:
    """A pickup is not a truck. Report the sentences so a human can judge."""
    text = data.get("bodyText") or ""
    hits = list(TRUCK_RE.finditer(text))
    if not hits:
        return []
    low = text.lower()
    names_pickup = any(w in low for w in PICKUP_WORDS)
    snippets = []
    for m in hits[:4]:
        s = max(0, m.start() - 90)
        e = min(len(text), m.end() + 90)
        snippets.append(" ".join(text[s:e].split()))
    joined = " | ".join(snippets)
    if not names_pickup:
        return [(
            "FINDING",
            f"the word 'truck' appears {len(hits)}x and the page never names a pickup "
            f"(D-Max). Sentences: {joined}",
        )]
    return [(
        "FINDING",
        f"the word 'truck' appears {len(hits)}x on a page that also names pickups; "
        f"check each use names the right body type. Sentences: {joined}",
    )]


CHECKS = (
    ("multi-series legend", check_legends),
    ("period label", check_period),
    ("pie/donut segments", check_segments),
    ("pickup vs truck", check_body_type),
)


def check_page(chrome: str, page: Path, timeout: int) -> dict:
    data = dump_page(chrome, page, timeout)
    result = {
        "page": str(page),
        "relative": str(page.relative_to(ROOT)) if str(page).startswith(str(ROOT)) else str(page),
        "loaded": bool(data.get("ok")),
        "charts": data.get("charts", []),
        "errors": data.get("errors", []),
        "results": [],
    }
    if not result["loaded"]:
        result["results"].append(["FINDING", "page did not load in headless Chrome: "
                                  + "; ".join(result["errors"])])
        return result
    for name, fn in CHECKS:
        for status, message in fn(data):
            result["results"].append([name, status, message])
    return result


def collect_pages(args) -> list[Path]:
    pages: list[Path] = []
    for p in args.path:
        pages.append(Path(p) if Path(p).is_absolute() else (ROOT / p))
    for d in args.dir:
        base = Path(d) if Path(d).is_absolute() else (ROOT / d)
        if not base.exists():
            print(f"  (no such folder, skipped: {base})")
            continue
        for f in sorted(base.glob("*.html")):
            # Scratch and probe copies are not deliverables.
            if f.name.startswith("_"):
                continue
            pages.append(f)
    seen = set()
    out = []
    for p in pages:
        rp = str(p.resolve())
        if rp not in seen:
            seen.add(rp)
            out.append(p.resolve())
    return out


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--path", action="append", default=[], help="one page")
    ap.add_argument("--dir", action="append", default=[], help="a folder of pages")
    ap.add_argument("--report", default=str(DEFAULT_REPORT))
    ap.add_argument("--timeout", type=int, default=90)
    ap.add_argument("--gate-on-structural", action="store_true",
                    help="exit 1 if a structural defect (legend or donut segments) is found")
    args = ap.parse_args()

    if not args.path and not args.dir:
        ap.error("give --path and/or --dir")

    chrome = find_chrome()
    pages = collect_pages(args)
    print(f"check_rendered_page: {len(pages)} page(s), chrome {chrome}")

    results = []
    for i, page in enumerate(pages, 1):
        print(f"  [{i}/{len(pages)}] {page.name}")
        results.append(check_page(chrome, page, args.timeout))

    import datetime as _dt
    report_path = Path(args.report)
    if not report_path.is_absolute():
        report_path = ROOT / report_path
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report = {
        "generated": _dt.datetime.now().isoformat(timespec="seconds"),
        "pages_checked": len(results),
        "pages": results,
    }
    report_path.write_text(json.dumps(report, indent=1), encoding="utf-8")

    gate_hits = []
    finding_hits = []
    for r in results:
        for row in r["results"]:
            if len(row) == 2:
                name, status, message = "load", row[0], row[1]
            else:
                name, status, message = row
            if status == "GATE":
                gate_hits.append((r["relative"], name, message))
            elif status == "FINDING":
                finding_hits.append((r["relative"], name, message))

    print("\n================ structural (GATE) ================")
    if gate_hits:
        for rel, name, msg in gate_hits:
            print(f"GATE  {rel}\n      [{name}] {msg}")
    else:
        print("none")

    print("\n================ needs a human look (FINDING) ================")
    if finding_hits:
        for rel, name, msg in finding_hits:
            print(f"FIND  {rel}\n      [{name}] {msg}")
    else:
        print("none")

    print(f"\nreport -> {report_path}")
    print(f"pages checked {len(results)}, structural {len(gate_hits)}, findings {len(finding_hits)}")

    if args.gate_on_structural and gate_hits:
        print("RENDERED_PAGE_CHECK: FAIL (structural)")
        return 1
    print("RENDERED_PAGE_CHECK: DONE")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
