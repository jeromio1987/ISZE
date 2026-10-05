# -*- coding: utf-8 -*-
"""QA for ISZE_Price_BP_Weighted_Compare.html.

Renders in real Chrome, takes full-page slices at four widths plus one zoom per
chart and per section, runs DOM assertions (horizontal overflow, clipped text,
white-on-pale, blank charts, banned vocabulary, unresolved values), and writes a
JSON report. Screenshots must then be image-read, one at a time.

Run: python 02_dashboards/pricing/_build/qa_price_bp_weighted_compare.py
"""
import io
import json
import os
import sys

from playwright.sync_api import sync_playwright

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

ROOT = r"C:\Users\jerom\Desktop\claude\ISZE"
HTML = os.path.join(ROOT, "02_dashboards", "pricing",
                    "ISZE_Price_BP_Weighted_Compare.html")
QA = os.path.join(ROOT, "02_dashboards", "pricing", "_qa_bp_weighted")
CHROME = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
URL = "file:///" + HTML.replace("\\", "/")
os.makedirs(QA, exist_ok=True)

WIDTHS = [(1440, "w1440"), (1280, "w1280"), (1024, "w1024"), (390, "w390")]

taken, report = [], {"shots": [], "errors": [], "asserts": {}}


def shot(page, name, clip=None):
    p = os.path.join(QA, name + ".png")
    if clip is not None:
        H = page.evaluate("document.documentElement.scrollHeight")
        W = page.evaluate("document.documentElement.scrollWidth")
        y = max(0, min(clip["y"], max(0, H - 8)))
        h = max(8, min(clip["height"], H - y))
        x = max(0, min(clip["x"], max(0, W - 8)))
        w = max(8, min(clip["width"], W - x))
        clip = {"x": x, "y": y, "width": w, "height": h}
    page.screenshot(path=p, full_page=True, clip=clip, animations="disabled")
    taken.append(p)
    return p


def dom_assert(page):
    js = r"""
    () => {
      const out = {hOverflow: [], clipped: [], paleWhite: [], blank: [],
                   banned: [], nan: [], chartMarks: {}};
      const de = document.documentElement;
      const vw = window.innerWidth;
      if (de.scrollWidth > vw + 2)
        out.hOverflow.push('document scrollWidth ' + de.scrollWidth + ' > ' + vw);
      document.querySelectorAll('body *').forEach(el => {
        const r = el.getBoundingClientRect();
        if (r.width === 0 && r.height === 0) return;
        if (r.right > vw + 2 && !el.closest('.scroll') && !el.closest('canvas'))
          out.hOverflow.push((el.id || el.className || el.tagName) + ' right=' + Math.round(r.right));
        const p = el.parentElement;
        if (p && !p.classList.contains('wrap') && !p.classList.contains('scroll')) {
          const ov = getComputedStyle(p).overflowX;
          if (ov === 'visible' && el.scrollWidth > el.clientWidth + 2
              && el.tagName !== 'TD' && el.tagName !== 'TH'
              && !el.classList.contains('scroll') && !el.closest('.scroll')
              && el.tagName !== 'TABLE' && el.tagName !== 'CANVAS'
              && (el.className || '').indexOf('tip') < 0)
            out.clipped.push((el.id || el.className || el.tagName) + ' '
                             + el.scrollWidth + '>' + el.clientWidth);
        }
      });
      document.querySelectorAll('*').forEach(el => {
        const t = (el.children.length === 0 ? (el.textContent || '') : '');
        if (!t.trim()) return;
        const rc = getComputedStyle(el).color;
        let bg = null, n = el;
        while (n && n !== document.documentElement) {
          const b = getComputedStyle(n).backgroundColor;
          if (b && b !== 'rgba(0, 0, 0, 0)' && b !== 'transparent') { bg = b; break; }
          n = n.parentElement;
        }
        if (!bg) return;
        const lum = c => { const m = c.match(/\d+/g); if (!m) return null;
          const [r, g, b] = m.map(Number);
          return 0.2126 * r + 0.7152 * g + 0.0722 * b; };
        const lc = lum(rc), lb = lum(bg);
        if (lc === null || lb === null) return;
        if (lc > 205 && lb > 170)
          out.paleWhite.push(((el.id || el.className || el.tagName) + ' ' + rc + ' on ' + bg).slice(0, 90));
      });
      document.querySelectorAll('canvas').forEach((c, i) => {
        const ctx = c.getContext('2d');
        let nz = 0;
        try {
          const d = ctx.getImageData(0, 0, c.width, c.height).data;
          for (let k = 3; k < d.length; k += 400) if (d[k] !== 0) nz++;
        } catch (e) { nz = -1; }
        out.chartMarks['canvas' + (i + 1)] = nz;
        if (nz === 0) out.blank.push('canvas ' + (i + 1) + ' is empty');
      });
      const rowsP = document.querySelectorAll('#pnBody tr').length;
      out.chartMarks['pnRows'] = rowsP;
      if (rowsP < 5) out.blank.push('part-number table has ' + rowsP + ' rows');
      // The part-number table must carry descriptions, not a blank column.
      const pnTable = document.getElementById('pnBody')?.closest('table');
      const pnHead = pnTable ? [...pnTable.querySelectorAll('thead th')]
        .map(th => th.innerText.trim()) : [];
      out.chartMarks['pnHead'] = pnHead.join('|');
      if (pnHead[1] !== 'Description')
        out.blank.push('part-number table has no Description column: ' + pnHead.join('|'));
      const descCells = [...document.querySelectorAll('#pnBody tr')]
        .map(tr => (tr.children[1]?.innerText || '').trim());
      const emptyDesc = descCells.filter(d => d === '' || d === 'n/a').length;
      out.chartMarks['pnDescFilled'] = descCells.length - emptyDesc;
      if (emptyDesc > 0)
        out.blank.push(emptyDesc + ' part-number rows have an empty description');
      const shortDesc = descCells.filter(d => d.length > 0 && d.length < 4).length;
      if (shortDesc > 0) out.blank.push(shortDesc + ' descriptions are suspiciously short');
      // A description must either fit its cell or wrap inside it. Clip detection
      // already runs above; this names the column explicitly for this table.
      const descClip = [...document.querySelectorAll('#pnBody tr')].filter(tr => {
        const td = tr.children[1];
        if (!td) return false;
        return td.scrollWidth > td.clientWidth + 2;
      }).length;
      if (descClip > 0) out.blank.push(descClip + ' description cells are clipped');
      // The excluded section must paint identity, not an anonymous bucket total:
      // a plain-English name per bucket, an owner, and the lubricant part numbers.
      const exTable = document.querySelector('table.ex');
      out.chartMarks['excludedRows'] = exTable ? exTable.querySelectorAll('tbody tr').length : 0;
      if (!exTable) out.blank.push('excluded table not found');
      else if (out.chartMarks['excludedRows'] < 5) {
        out.blank.push('excluded table has ' + out.chartMarks['excludedRows'] + ' rows');
      }
      const exTxt = (exTable ? exTable.innerText : '') + ' ' +
        [...document.querySelectorAll('h2')].map(h => h.innerText).join(' ') + ' ' +
        [...document.querySelectorAll('.scroll table')].map(t => t.innerText).join(' ');
      [['Parts with no matching price on one side', 'excluded bucket 1 not named'],
       ['Non-parts lines: rebates', 'excluded bucket 2 not named'],
       ['Lubricants and engine oil, UMI Israel', 'lubricant bucket not named'],
       ['UMI (1797)', 'lubricant bucket owner not named'],
       ['0550047337', 'lubricant part numbers not listed'],
       ['Rimula', 'lubricant description not listed'],
       ['Whose it is', 'excluded table has no owner column']
      ].forEach(([w, msg]) => { if (exTxt.indexOf(w) < 0) out.blank.push(msg); });
      ['no_price_on_one_side', 'rebate_or_non_part_admin', 'lubricant_no_pr00_in_sap']
        .forEach(w => { if (exTxt.indexOf(w) >= 0) out.blank.push('machine label visible: ' + w); });
      const clone = document.body.cloneNode(true);
      clone.querySelectorAll('script,style').forEach(n => n.remove());
      const vis = clone.innerText || '';
      [['sell-out', 'banned term sell-out'], ['sell out', 'banned term sell out'],
       ['sellout', 'banned term sellout'], ['wallet', 'banned term wallet'],
       ['street', 'banned term street'], ['parc ', 'banned term parc'],
       ['IML v7', 'internal codename IML v7'], ['Model B', 'internal codename Model B'],
       ['PRISM lane', 'internal codename PRISM lane'], ['Book B', 'banned term Book B']
      ].forEach(([w, msg]) => { if (vis.toLowerCase().indexOf(w.toLowerCase()) >= 0)
        out.banned.push(msg); });
      [['undefined', 'undefined'], ['NaN', 'NaN'], ['Infinity', 'Infinity'],
       ['[object', '[object']].forEach(([w, msg]) => {
        if (vis.indexOf(w) >= 0) out.nan.push(msg + ' in visible text');
      });
      document.querySelectorAll('[data-tip]').forEach(el => {
        const a = el.getAttribute('data-tip') || '';
        if (/undefined|NaN|Infinity/.test(a))
          out.nan.push('tooltip: ' + a.replace(/\s+/g, ' ').slice(0, 70));
      });
      // The headline must be the same number the JSON payload carries.
      const kpi = document.querySelector('.kpi .val');
      out.headline = kpi ? kpi.textContent.trim() : null;
      return out;
    }
    """
    r = page.evaluate(js)
    for k in r:
        if isinstance(r[k], list):
            r[k] = r[k][:8]
    return r


with sync_playwright() as pw:
    br = pw.chromium.launch(executable_path=CHROME, headless=True)
    ctx = br.new_context(viewport={"width": 1440, "height": 1000}, device_scale_factor=1)
    page = ctx.new_page()
    errs = []
    page.on("console", lambda m: errs.append(m.type + ": " + m.text) if m.type == "error" else None)
    page.on("pageerror", lambda e: errs.append("pageerror: " + str(e)))
    page.goto(URL)
    page.wait_for_timeout(1500)

    payload_ok = page.evaluate(
        "() => { try { const d = JSON.parse(document.getElementById('payload').textContent);"
        " return {customers: d.customers.length, classes: d.by_class.length,"
        " top: d.top_pn.length, net: d.network.pct}; } catch(e) { return {err: String(e)}; } }")
    print("payload:", payload_ok)
    report["payload"] = payload_ok
    if errs:
        report["errors"] = errs[:20]
        print("CONSOLE ERRORS:", errs[:6])

    for w, tag in WIDTHS:
        page.set_viewport_size({"width": w, "height": 900})
        page.wait_for_timeout(420)
        h = page.evaluate("document.body.scrollHeight")
        shot(page, f"00_full_{tag}")
        y, n = 0, 0
        while y < h and n < 14:
            shot(page, f"01_slice_{tag}_{n:02d}",
                 clip={"x": 0, "y": y, "width": w, "height": min(900, h - y)})
            y += 900
            n += 1
        report["slices_" + tag] = n
        report["asserts"]["full_" + tag] = dom_assert(page)

    # one zoom per chart
    page.set_viewport_size({"width": 1440, "height": 1000})
    page.wait_for_timeout(320)
    for i, cid in enumerate(["custChart", "pctChart", "classChart"], 1):
        b = page.evaluate(
            "(id)=>{const e=document.getElementById(id);const r=e.getBoundingClientRect();"
            "return {x:r.left+window.scrollX,y:r.top+window.scrollY,w:r.width,h:r.height};}", cid)
        shot(page, f"02_chart_{i}_{cid}",
             clip={"x": max(0, b["x"] - 8), "y": max(0, b["y"] - 40),
                   "width": min(b["w"] + 16, 1440), "height": min(b["h"] + 60, 1800)})

    # hover a customer bar for the tooltip
    try:
        box = page.evaluate(
            "()=>{const c=document.getElementById('custChart');const r=c.getBoundingClientRect();"
            "return {x:r.left+40,y:r.top+30};}")
        page.mouse.move(box["x"], box["y"])
        page.wait_for_timeout(700)
        shot(page, "03_hover_customer")
    except Exception as exc:
        print("hover failed:", str(exc)[:90])

    br.close()

report["screenshots_taken"] = len(taken)
report["files"] = [os.path.basename(t) for t in taken]
with open(os.path.join(QA, "_qa_report.json"), "w", encoding="utf-8") as f:
    json.dump(report, f, indent=1)
print("SCREENSHOTS TAKEN: %d" % len(taken))
INFO_KEYS = {"chartMarks", "headline"}
for k, v in report["asserts"].items():
    bad = {a: b for a, b in v.items() if b and a not in INFO_KEYS}
    if bad:
        print("ASSERT FAIL @%s: %s" % (k, json.dumps(bad)[:900]))
    else:
        print("asserts clean @%s  headline=%s  marks=%s"
              % (k, v.get("headline"), v.get("chartMarks")))
print("done")
