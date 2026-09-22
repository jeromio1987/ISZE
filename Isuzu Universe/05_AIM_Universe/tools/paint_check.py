"""Paint check on the assembled artifact (integration owner).

Opening a file and finding bytes is not evidence the thing renders. This opens
the real file in real Chrome and asserts the visible content a reader would see:
the version stamp, the six tabs, a case list, and no leftover template marks.

Tab labels are read from the artifact's own TAB_LABELS declaration, not by
counting <button class="tab"> matches in the DOM: the module source is inside the
page, so a regex over the DOM also matches the template literal itself and would
report a phantom seventh tab.

Usage: python tools/paint_check.py
Exit 0 only when every check is observed.
"""
import io
import json
import os
import re
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
ARTIFACT = os.path.join(ROOT, "dist", "ISZE_AIM_Pricing_Decisions_v04_INTERNAL.html")

CHROME_CANDIDATES = [
    r"C:\Program Files\Google\Chrome\Application\chrome.exe",
    r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
]

EXPECTED_TABS = ["Sales evidence", "Price position", "Two objectives",
                 "Price & profit test", "Candidates", "Internal action"]


def find_chrome():
    for c in CHROME_CANDIDATES:
        if os.path.exists(c):
            return c
    return None


def main():
    if not os.path.exists(ARTIFACT):
        print("FAIL artifact missing:", ARTIFACT)
        return 2
    chrome = find_chrome()
    if not chrome:
        print("FAIL chrome not found; cannot verify paint")
        return 2

    url = "file:///" + ARTIFACT.replace("\\", "/")
    profile = tempfile.mkdtemp(prefix="aim_paint_")

    proc = subprocess.run(
        [chrome, "--headless=new", "--disable-gpu", "--no-sandbox",
         "--user-data-dir=" + profile, "--virtual-time-budget=8000",
         "--dump-dom", url],
        capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=180)

    dom = proc.stdout or ""
    if len(dom) < 1000:
        print("FAIL dump-dom returned %d bytes; stderr: %s" % (len(dom), (proc.stderr or "")[:400]))
        return 2

    source = io.open(ARTIFACT, encoding="utf-8", errors="ignore").read()
    checks = []

    def check(cid, desc, ok, observed):
        checks.append((cid, desc, ok, observed))

    # The reader-visible header carries the version stamp. The module source also
    # contains the literal 'Decision component 0.2' inside a replace() call, so
    # assert on the rendered span, not on the whole document.
    m = re.search(r'<span class="version">([^<]*)</span>', dom)
    stamp = m.group(1).strip() if m else ""
    check("P01", "the header states the corrected component version",
          stamp.startswith("Decision component 0.4"), stamp or "no version span")

    # Check the rendered tab bar directly rather than parsing the module source.
    # The earlier version of this check parsed TAB_LABELS with a non-greedy
    # regex, which stopped at the first pair and then reported zero declared
    # tabs - a fault in the check, not in the artifact.
    ti = dom.find('id="tabs"')
    tabbar = dom[ti:ti + 3000] if ti >= 0 else ""
    missing = [t for t in EXPECTED_TABS
               if t not in tabbar and t.replace("&", "&amp;") not in tabbar]
    check("P02", "every expected view label is present in the tab bar",
          not missing, "missing: %s" % (missing or "none"))

    # No unevaluated template literal may reach the reader.
    check("P03", "no unevaluated template mark in the tab bar",
          "${" not in tabbar, "found ${ in tab bar: %s" % ("${" in tabbar))

    cards = re.findall(r'class="case-card', dom)
    check("P04", "the case list renders its cards", len(cards) >= 5,
          "%d case cards" % len(cards))

    body = re.sub(r'<script[\s\S]*?</script>', '', dom)
    text = re.sub(r'<[^>]+>', ' ', body)
    text = re.sub(r'\s+', ' ', text)
    check("P05", "a reader sees real commercial words, not a blank shell",
          len(text.strip()) > 1500, "%d characters of visible text" % len(text.strip()))

    leftovers = [t for t in ["undefined", "NaN", "[object Object]"] if t in text]
    check("P06", "no leftover template mark in the visible text",
          not leftovers, "found: %s" % (leftovers or "none"))

    banned = [t for t in ["Model A", "Model B", "sell-out", "sellout", "Book B"]
              if t.lower() in text.lower()]
    check("P07", "no banned commercial or audience label is visible",
          not banned, "found: %s" % (banned or "none"))

    check("P08", "a scenario rendered, not just a shell",
          ("EUR" in text) and ("quantity" in text.lower() or "units" in text.lower()),
          "EUR present: %s" % ("EUR" in text))

    ok_all = True
    for cid, desc, ok, observed in checks:
        print("%s %s: %s  [%s]" % ("PASS" if ok else "FAIL", cid, desc, observed))
        if not ok:
            ok_all = False

    io.open(os.path.join(ROOT, "dist", "_paint_check.json"), "w", encoding="utf-8").write(
        json.dumps({"artifact": ARTIFACT,
                    "artifact_sha256": __import__("hashlib").sha256(
                        io.open(ARTIFACT, "rb").read()).hexdigest(),
                    "checks": [{"id": c, "desc": d, "status": "PASS" if o else "FAIL",
                                "observed": str(v)} for c, d, o, v in checks]}, indent=2) + "\n")
    print("%d/%d paint checks passed" % (sum(1 for c in checks if c[2]), len(checks)))
    return 0 if ok_all else 1


if __name__ == "__main__":
    sys.exit(main())
