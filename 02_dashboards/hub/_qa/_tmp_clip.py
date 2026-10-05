# -*- coding: utf-8 -*-
"""Temp: rigorous clipped-text / out-of-parent detector, swept across widths."""
import json
import sys

from playwright.sync_api import sync_playwright

CHROME = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
PAGE = r"C:\Users\jerom\Desktop\claude\ISZE\02_dashboards\hub\ISZE_OS_Hub.html"
sys.stdout.reconfigure(encoding="utf-8")

JS = r"""
(() => {
  const res = {clipped: [], outside: [], covered: []};

  function clipBoxes(el) {
    // ancestors (incl. self) that clip overflow
    const boxes = [];
    let p = el.parentElement;
    while (p) {
      const cs = getComputedStyle(p);
      if (cs.overflowX !== 'visible' || cs.overflowY !== 'visible') {
        const r = p.getBoundingClientRect();
        const bcs = getComputedStyle(p);
        const bl = parseFloat(bcs.borderLeftWidth) || 0;
        const bt = parseFloat(bcs.borderTopWidth) || 0;
        const br = parseFloat(bcs.borderRightWidth) || 0;
        const bb = parseFloat(bcs.borderBottomWidth) || 0;
        boxes.push({el: p, l: r.left + bl, t: r.top + bt, r: r.right - br, b: r.bottom - bb});
      }
      p = p.parentElement;
    }
    return boxes;
  }

  function textRects(el) {
    const rects = [];
    const walker = document.createTreeWalker(el, NodeFilter.SHOW_TEXT);
    let n;
    while ((n = walker.nextNode())) {
      if (!n.textContent.trim()) continue;
      const r = document.createRange();
      r.selectNodeContents(n);
      for (const rr of r.getClientRects()) {
        if (rr.width > 0.5 && rr.height > 0.5) rects.push({rect: rr, txt: n.textContent.trim().slice(0, 40)});
      }
    }
    return rects;
  }

  const all = [...document.querySelectorAll('body *')];
  for (const el of all) {
    const cs = getComputedStyle(el);
    if (cs.display === 'none' || cs.visibility === 'hidden') continue;
    // direct text nodes only (avoid duplicating parents)
    const hasText = [...el.childNodes].some(n => n.nodeType === 3 && n.textContent.trim());
    if (!hasText) continue;
    const clips = clipBoxes(el);
    for (const t of textRects(el)) {
      for (const c of clips) {
        const dx = Math.max(c.l - t.rect.left, t.rect.right - c.r);
        const dy = Math.max(c.t - t.rect.top, t.rect.bottom - c.b);
        if (dx > 0.6 && t.rect.width > 2) {
          res.clipped.push({
            el: el.tagName + '.' + (el.className || '').toString().slice(0, 26),
            clip: c.el.tagName + '.' + (c.el.className || '').toString().slice(0, 26),
            text: t.txt, cutLeft: +(c.l - t.rect.left).toFixed(1), cutRight: +(t.rect.right - c.r).toFixed(1),
            x: +t.rect.left.toFixed(1)
          });
        }
        if (dy > 0.6 && t.rect.height > 2) {
          res.clipped.push({
            el: el.tagName + '.' + (el.className || '').toString().slice(0, 26),
            clip: c.el.tagName + '.' + (c.el.className || '').toString().slice(0, 26),
            text: t.txt, cutTop: +(c.t - t.rect.top).toFixed(1), cutBottom: +(t.rect.bottom - c.b).toFixed(1)
          });
        }
      }
      // covered by another element?
      const cx = t.rect.left + Math.min(4, t.rect.width / 2);
      const cy = t.rect.top + t.rect.height / 2;
      const top = document.elementFromPoint(cx, cy);
      if (top && top !== el && !el.contains(top) && !top.contains(el)) {
        const tcs = getComputedStyle(top);
        if (tcs.backgroundColor !== 'rgba(0, 0, 0, 0)' || tcs.backgroundImage !== 'none') {
          res.covered.push({el: el.tagName + '.' + (el.className||'').toString().slice(0,20),
            cover: top.tagName + '.' + (top.className||'').toString().slice(0,24), text: t.txt});
        }
      }
    }
    // outside parent content box
    const pr = el.parentElement && el.parentElement.getBoundingClientRect();
    if (pr) {
      const r = el.getBoundingClientRect();
      const pcs = getComputedStyle(el.parentElement);
      const pl = pr.left + (parseFloat(pcs.paddingLeft) || 0) + (parseFloat(pcs.borderLeftWidth) || 0);
      const prr = pr.right - (parseFloat(pcs.paddingRight) || 0) - (parseFloat(pcs.borderRightWidth) || 0);
      if (r.left < pl - 1.5 || r.right > prr + 1.5) {
        res.outside.push({el: el.tagName + '.' + (el.className||'').toString().slice(0,26),
          parent: el.parentElement.tagName + '.' + (pcs.gridTemplateColumns||'').slice(0,30),
          dxL: +(pl - r.left).toFixed(1), dxR: +(r.right - prr).toFixed(1),
          text: (el.textContent||'').trim().slice(0, 30)});
      }
    }
  }
  // ragged card heights in the stack
  res.heights = [...document.querySelectorAll('.layer')].map(l => +l.getBoundingClientRect().height.toFixed(0));
  return res;
})()
"""

with sync_playwright() as p:
    b = p.chromium.launch(executable_path=CHROME, args=["--force-device-scale-factor=1"])
    for w in [390, 480, 640, 760, 900, 1024, 1080, 1081, 1180, 1280, 1366, 1440]:
        pg = b.new_page(viewport={"width": w, "height": 1000})
        pg.goto("file:///" + PAGE.replace("\\", "/"))
        pg.wait_for_timeout(300)
        d = pg.evaluate(JS)
        print("=" * 72)
        print("WIDTH", w, "| docScrollW", pg.evaluate("document.documentElement.scrollWidth"),
              "| layer heights", d["heights"])
        print("  clipped:", len(d["clipped"]))
        seen = set()
        for c in d["clipped"]:
            k = (c["el"], c.get("cutLeft"), c.get("cutRight"), c.get("cutTop"), c.get("cutBottom"), c["text"][:24])
            if k in seen: continue
            seen.add(k)
            print("    ", c)
        print("  outside parent:", len(d["outside"]))
        seen2 = set()
        for c in d["outside"]:
            k = (c["el"], c["dxL"], c["dxR"], c["text"][:20])
            if k in seen2: continue
            seen2.add(k)
            print("    ", c)
        print("  covered:", len(d["covered"]))
        for c in d["covered"][:6]:
            print("    ", c)
        pg.close()
    b.close()
