# -*- coding: utf-8 -*-
"""Temp geometry probe for the ISZE OS hub layer-stack clipping defect."""
import json
import sys

from playwright.sync_api import sync_playwright

CHROME = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
PAGE = r"C:\Users\jerom\Desktop\claude\ISZE\02_dashboards\hub\ISZE_OS_Hub.html"
sys.stdout.reconfigure(encoding="utf-8")

JS = r"""
(() => {
  const out = {vw: innerWidth, docScroll: document.documentElement.scrollWidth};
  const layers = [...document.querySelectorAll('.layer')];
  out.layers = layers.map((L, i) => {
    const lr = L.getBoundingClientRect();
    const cs = getComputedStyle(L);
    const kids = [...L.children].map(k => {
      const r = k.getBoundingClientRect();
      const kcs = getComputedStyle(k);
      return {
        cls: k.className,
        left: +r.left.toFixed(1), right: +r.right.toFixed(1), w: +r.width.toFixed(1),
        padL: kcs.paddingLeft, padR: kcs.paddingRight,
        text: (k.textContent || '').trim().slice(0, 26)
      };
    });
    return {
      i, iw: innerWidth,
      grid: cs.gridTemplateColumns,
      gap: cs.gap,
      overflow: cs.overflow,
      left: +lr.left.toFixed(1), right: +lr.right.toFixed(1),
      scrollW: L.scrollWidth, clientW: L.clientWidth,
      kids
    };
  });
  // horizontal overflow scan
  out.overflow = [];
  document.querySelectorAll('*').forEach(el => {
    if (el.scrollWidth - el.clientWidth > 1 && el.clientWidth > 0) {
      const cs = getComputedStyle(el);
      if (cs.overflowX === 'visible' || cs.overflowX === 'hidden' || cs.overflowX === 'auto') {
        out.overflow.push({tag: el.tagName, cls: (el.className||'').toString().slice(0,40),
          sw: el.scrollWidth, cw: el.clientWidth, ox: cs.overflowX});
      }
    }
  });
  return out;
})()
"""

with sync_playwright() as p:
    b = p.chromium.launch(executable_path=CHROME, args=["--force-device-scale-factor=1"])
    for w in [390, 1024, 1280, 1440]:
        pg = b.new_page(viewport={"width": w, "height": 900})
        pg.goto("file:///" + PAGE.replace("\\", "/"))
        pg.wait_for_timeout(400)
        data = pg.evaluate(JS)
        print("=" * 70)
        print("VIEWPORT", w, "docScrollWidth", data["docScroll"], "scrollW-ok", data["docScroll"] <= w)
        for L in data["layers"]:
            print(" layer", L["i"], "grid=", L["grid"], "| overflow=", L["overflow"],
                  "| box", L["left"], "->", L["right"], "| scroll/client", L["scrollW"], L["clientW"])
            for k in L["kids"]:
                print("    ", repr(k["cls"])[:20].ljust(20), "x", k["left"], "->", k["right"],
                      "w", k["w"], "padL", k["padL"], "padR", k["padR"], "|", k["text"])
        if data["overflow"]:
            print(" HORIZONTAL OVERFLOW ELEMENTS:")
            seen = set()
            for o in data["overflow"]:
                key = (o["tag"], o["cls"], o["sw"], o["cw"])
                if key in seen:
                    continue
                seen.add(key)
                print("   ", o)
        else:
            print(" no horizontal overflow elements")
        pg.close()
    b.close()
