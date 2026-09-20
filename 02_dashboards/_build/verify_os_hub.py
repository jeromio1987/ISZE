# -*- coding: utf-8 -*-
"""
Guard for the ISZE OS hub.
Exit 0 = pass. Exit 1 = fail with a printed reason.

Checks: page exists and is non-trivial; no external requests; the link sidecar shows every target
present on disk; the page carries the four measurement states; every derived figure has a tooltip;
house language is respected in the prose.
"""
import json
import os
import re
import sys

sys.stdout.reconfigure(encoding="utf-8")

HUB = r"C:\Users\jerom\Desktop\claude\ISZE\02_dashboards\hub"
PAGE = os.path.join(HUB, "ISZE_OS_Hub.html")
LINKS = os.path.join(HUB, "ISZE_OS_Hub.links.json")
fails = []


def check(ok, label, detail=""):
    print(("PASS %-34s %s" % (label, detail)).rstrip())
    if not ok:
        fails.append("%s: %s" % (label, detail))


check(os.path.exists(PAGE), "page_exists", PAGE)
if not os.path.exists(PAGE):
    print("FAIL: page missing")
    sys.exit(1)

html = open(PAGE, encoding="utf-8").read()
size = len(html.encode("utf-8"))
check(size >= 40_000, "page_size", "%d bytes" % size)

ext = re.findall(r"https?://", html)
check(len(ext) == 0, "no_external_requests", "%d found" % len(ext))
check("<img" not in html, "no_image_tags", "inline SVG/CSS only")
check(html.count("<script") == 1, "single_inline_script", "%d script tags" % html.count("<script"))

for state in ["measured", "modelled", "excluded", "judge"]:
    check(('class="chip %s"' % state) in html, "state_%s_present" % state)

check(html.count('class="kpi') >= 40, "derived_figures_have_chips",
      "%d kpi chips, %d tooltips" % (html.count('class="kpi'), html.count('class="tip"')))
check(html.count('class="tip"') >= html.count('class="kpi"'), "every_kpi_has_tooltip",
      "tips %d vs kpi %d" % (html.count('class="tip"'), html.count('class="kpi"')))

for token in ["Not included", "Snapshot", "Formula"]:
    check(html.count(token) >= 40, "tooltip_field_%s" % token.lower().replace(" ", "_"),
          "%d occurrences" % html.count(token))

check("NaN" not in html, "no_nan")
check("%s" not in html, "no_unfilled_placeholders")
check("@@" not in html, "no_unfilled_tokens")

# sidecar link inventory
check(os.path.exists(LINKS), "link_sidecar_exists", LINKS)
if os.path.exists(LINKS):
    data = json.load(open(LINKS, encoding="utf-8"))
    check(data["tested"] == data["present"], "all_link_targets_present",
          "%d tested, %d present" % (data["tested"], data["present"]))
    check(len(data["missing"]) == 0, "no_missing_link_targets", str(data["missing"][:4]))
    check(data["tested"] >= 150, "link_breadth", "%d targets" % data["tested"])
    # re-test on disk at verify time, not just at build time
    stale = [t["path"] for t in data["targets"]
             if t["exists"] and not os.path.exists(os.path.join(r"C:\Users\jerom\Desktop\claude", t["path"]))]
    check(len(stale) == 0, "link_targets_still_on_disk", str(stale[:4]))

# house language, prose only: strip tooltips (balancing nested spans), hrefs, style and script
def strip_tooltips(src):
    out = []
    i = 0
    open_tag = '<span class="tip">'
    while True:
        j = src.find(open_tag, i)
        if j < 0:
            out.append(src[i:])
            break
        out.append(src[i:j])
        k = j + len(open_tag)
        depth = 1
        while depth > 0 and k < len(src):
            nxt_open = src.find("<span", k)
            nxt_close = src.find("</span>", k)
            if nxt_close < 0:
                k = len(src)
                break
            if 0 <= nxt_open < nxt_close:
                depth += 1
                k = nxt_open + 5
            else:
                depth -= 1
                k = nxt_close + 7
        i = k
    return "".join(out)


prose = strip_tooltips(html)
prose = re.sub(r'href="[^"]*"', "", prose)
prose = re.sub(r"<style>.*?</style>", " ", prose, flags=re.S)
prose = re.sub(r"<script>.*?</script>", " ", prose, flags=re.S)
prose = re.sub(r"<[^>]+>", " ", prose)
for term in ["parc", "wallet", "sell-out", "sellout", "sell out", "mass-demand", "mass demand"]:
    hits = len(re.findall(term, prose, re.I))
    check(hits == 0, "house_language_%s" % term.replace(" ", "_").replace("-", "_"),
          "%d hits" % hits)

for required in ["units in operation (UIO)", "spend per unit", "sales to dealer",
                 "uncaptured GPS value", "L1 / L2 / L3"]:
    check(required.lower() in prose.lower(), "defines_%s" % required.split(" ")[0].lower().replace("/", ""))

# launcher present and not auto-run
cmd = os.path.join(HUB, "OPEN_ISZE_OS_Hub.cmd")
check(os.path.exists(cmd), "open_cmd_exists", cmd)
if os.path.exists(cmd):
    body = open(cmd, encoding="utf-8").read()
    check("ISZE_OS_Hub.html" in body and body.strip().startswith("@echo off"), "open_cmd_shape")

if fails:
    print("\nHUB_GUARD_FAIL %d" % len(fails))
    for f in fails:
        print("  -", f)
    sys.exit(1)
print("\nHUB_GUARD_OK")
