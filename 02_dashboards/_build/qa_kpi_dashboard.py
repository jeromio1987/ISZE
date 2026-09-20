# -*- coding: utf-8 -*-
"""QA for ISZE_KPI_Dashboard.html.

Renders in real Chrome via executable_path, sweeps the eight toggle combinations,
takes full-page slices plus one zoom per section and per chart, runs DOM assertions
(overflow, element-outside-parent, clipped text, white-on-pale, blank charts), and
writes a JSON report. Screenshots must then be image-read, one at a time.
"""
import os, sys, io, json, time, re
from playwright.sync_api import sync_playwright

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

HTML = r'C:\Users\jerom\Desktop\claude\ISZE\02_dashboards\sales\ISZE_KPI_Dashboard.html'
QA = r'C:\Users\jerom\Desktop\claude\ISZE\02_dashboards\sales\_qa_kpi'
CHROME = r'C:\Program Files\Google\Chrome\Application\chrome.exe'
URL = 'file:///' + HTML.replace('\\', '/')
os.makedirs(QA, exist_ok=True)

WIDTHS = [(1024, 'w1024'), (1280, 'w1280'), (1440, 'w1440'), (390, 'w390')]
COMBOS = [('cy', 'db', 'inc'), ('cy', 'db', 'ex'), ('cy', 'dlr', 'inc'), ('cy', 'dlr', 'ex'),
          ('fy', 'db', 'inc'), ('fy', 'db', 'ex'), ('fy', 'dlr', 'inc'), ('fy', 'dlr', 'ex')]
SECTIONS = [('hero', '#hero'), ('coverage', '#coverage'), ('league', '#league'),
            ('growth', '#growth'), ('growth2', '#growth2'), ('bvp', '#bvp'),
            ('story', '#story'), ('honesty', '#notshown')]

taken, report = [], {'shots': [], 'errors': [], 'asserts': {}}


def shot(page, name, full=False, clip=None):
    p = os.path.join(QA, name + '.png')
    if clip is not None:
        H = page.evaluate('document.documentElement.scrollHeight')
        W = page.evaluate('document.documentElement.scrollWidth')
        y = max(0, min(clip['y'], max(0, H - 8)))
        h = max(8, min(clip['height'], H - y))
        x = max(0, min(clip['x'], max(0, W - 8)))
        w = max(8, min(clip['width'], W - x))
        clip = {'x': x, 'y': y, 'width': w, 'height': h}
        full = True
    page.screenshot(path=p, full_page=full, clip=clip, animations='disabled')
    taken.append(p)
    return p


def set_mode(page, combo):
    cy, d, w = combo
    for k, v in (('period', cy), ('dir', d), ('warr', w)):
        page.click(f'.bar button[data-k="{k}"][data-v="{v}"]')
    page.wait_for_timeout(260)


def dom_assert(page, tag):
    js = r"""
    () => {
      const out = {hOverflow: [], outside: [], clipped: [], paleWhite: [], blank: [],
                   banned: [], nan: []};
      const de = document.documentElement;
      const vw = window.innerWidth;
      if (de.scrollWidth > vw + 2) out.hOverflow.push('document scrollWidth ' + de.scrollWidth + ' > ' + vw);
      document.querySelectorAll('body *').forEach(el => {
        const r = el.getBoundingClientRect();
        if (r.width === 0 && r.height === 0) return;
        if (r.right > vw + 2 && !el.closest('.tbl') && !el.closest('.svgwrap') && !el.closest('svg'))
          out.hOverflow.push((el.id || el.className || el.tagName) + ' right=' + Math.round(r.right));
        const p = el.parentElement;
        if (p && !p.classList.contains('wrap')) {
          const pr = p.getBoundingClientRect();
          const pr2 = getComputedStyle(p);
          const over = pr2.overflowX;
          if (over === 'visible' && el.scrollWidth > el.clientWidth + 2 && el.tagName !== 'TD' && el.tagName !== 'TH'
              && !el.classList.contains('tbl') && !el.classList.contains('svgwrap') && !el.closest('.tbl')
              && !el.closest('.svgwrap') && el.className.indexOf('tip') < 0 && el.tagName !== 'TABLE')
            out.clipped.push((el.id || el.className || el.tagName) + ' ' + el.scrollWidth + '>' + el.clientWidth);
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
        if (lc > 205 && lb > 170) out.paleWhite.push(((el.id || el.className || el.tagName) + ' ' + rc + ' on ' + bg).slice(0, 90));
      });
      document.querySelectorAll('.chart').forEach((c, i) => {
        const svgs = c.querySelectorAll('svg');
        let drawn = 0;
        svgs.forEach(s => { drawn += s.querySelectorAll('rect,circle,polyline,path,text').length; });
        const cells = c.querySelectorAll('.hm .cell, .mini .m, .rc .r, .flow .f, .chip').length;
        const rows = c.querySelectorAll('tbody tr').length;
        const marks = Math.max(drawn, cells, rows);
        const txt = (c.innerText || '').trim();
        // A chart that deliberately states it is unavailable in this setting is not blank.
        const declaredOut = /unavailable in this setting|no family carries a usable|Unavailable in this setting/i.test(txt);
        if (marks < 4 && !declaredOut)
          out.blank.push('chart ' + (i + 1) + ' drew only ' + marks + ' marks (svg=' + drawn + ', cells=' + cells + ', rows=' + rows + ')');
        if (txt.length < 40 && !declaredOut) out.blank.push('chart ' + (i + 1) + ' has almost no text: ' + txt.length + ' chars');
      });

      // Banned vocabulary and unresolved values anywhere in the USER-VISIBLE text.
      // Script and style bodies are stripped first: the source file names legitimately
      // carry words like "wallet" and never reach the reader.
      const clone = document.body.cloneNode(true);
      clone.querySelectorAll('script,style').forEach(n => n.remove());
      const vis = clone.innerText || '';
      [['sell-out','banned term sell-out'], ['sell out','banned term sell out'],
       ['sellout','banned term sellout'], ['wallet','banned term wallet'],
       ['parc ','banned term parc'], ['mass-demand','banned term mass-demand']
      ].forEach(([w, msg]) => { if (vis.toLowerCase().indexOf(w) >= 0) out.banned.push(msg); });
      [['undefined','undefined'], ['NaN','NaN'], ['Infinity','Infinity'], ['[object','[object']
      ].forEach(([w, msg]) => {
        if (vis.indexOf(w) >= 0) out.nan.push(msg + ' in visible text');
      });
      document.querySelectorAll('[data-tip]').forEach(el => {
        const a = el.getAttribute('data-tip') || '';
        if (/undefined|NaN|Infinity/.test(a)) out.nan.push('tooltip: ' + a.replace(/\s+/g,' ').slice(0, 70));
      });

      // The league share column must add to 100 and the footer billed figure must equal
      // the sum of the rows, whatever the toggles say.
      const rowsEl = [...document.querySelectorAll('table.league tbody tr')];
      const shares = rowsEl.map(r => parseFloat(String(r.children[2].innerText).replace('%','')))
                           .filter(x => !isNaN(x));
      if (shares.length) {
        const sm = shares.reduce((a, b) => a + b, 0);
        if (Math.abs(sm - 100) > 2.5) out.basis.push('league share column sums to ' + sm.toFixed(1) + '% not 100%');
      }
      const foot = document.querySelector('table.league tfoot tr');
      if (foot && shares.length) {
        const ft = foot.children[1].innerText.replace(/[^0-9]/g, '');
        const rowSum = rowsEl.filter(r => !r.classList.contains('cis'))
          .map(r => Number(String(r.children[1].innerText).replace(/[^0-9]/g, '')) || 0)
          .reduce((a, b) => a + b, 0);
        if (ft && rowSum && Math.abs(Number(ft) - rowSum) > 2000)
          out.basis.push('footer billed ' + ft + ' != row sum ' + rowSum);
      }
      return out;
    }
    """
    r = page.evaluate(js)
    for k in r:
        r[k] = r[k][:8]
    return r

with sync_playwright() as pw:
    br = pw.chromium.launch(executable_path=CHROME, headless=True)
    ctx = br.new_context(viewport={'width': 1440, 'height': 1000}, device_scale_factor=1)
    page = ctx.new_page()
    errs = []
    page.on('console', lambda m: errs.append(m.type + ': ' + m.text) if m.type == 'error' else None)
    page.on('pageerror', lambda e: errs.append('pageerror: ' + str(e)))
    page.goto(URL)
    page.wait_for_timeout(1200)

    nch = page.evaluate('document.querySelectorAll(".chart").length')
    meta = page.evaluate('window.__KPI_META__ || null')
    print('charts on page:', nch, '| meta:', meta)
    report['chart_count'] = nch
    if errs:
        report['errors'] = errs[:20]
        print('CONSOLE ERRORS:', errs[:6])

    # 1) slices at four widths, default mode
    set_mode(page, ('cy', 'db', 'inc'))
    for w, tag in WIDTHS:
        page.set_viewport_size({'width': w, 'height': 900})
        page.wait_for_timeout(320)
        h = page.evaluate('document.body.scrollHeight')
        shot(page, f'00_full_{tag}')
        step = 900
        n = 0
        y = 0
        while y < h and n < 14:
            clip = {'x': 0, 'y': y, 'width': w, 'height': min(step, h - y)}
            shot(page, f'01_slice_{tag}_{n:02d}', clip=clip)
            y += step
            n += 1
        report['slices_' + tag] = n
        report['asserts']['full_' + tag] = dom_assert(page, tag)

    # 2) section zooms at 1440
    page.set_viewport_size({'width': 1440, 'height': 1000})
    page.wait_for_timeout(320)
    for name, sel in SECTIONS:
        el = page.query_selector(sel)
        if not el:
            continue
        el.scroll_into_view_if_needed()
        page.wait_for_timeout(220)
        box = page.evaluate('(s)=>{const b=document.querySelector(s).getBoundingClientRect();'
                            'return {y:b.top+window.scrollY,h:b.height,w:b.width};}', sel)
        shot(page, f'02_sec_{name}_top', clip={'x': 0, 'y': box['y'], 'width': 1440, 'height': min(box['h'], 1400)})
        if box['h'] > 1400:
            shot(page, f'02_sec_{name}_mid', clip={'x': 0, 'y': box['y'] + 1400, 'width': 1440,
                                                  'height': min(1400, box['h'] - 1400)})
        if box['h'] > 2800:
            shot(page, f'02_sec_{name}_bot', clip={'x': 0, 'y': box['y'] + 2800, 'width': 1440,
                                                   'height': min(1400, box['h'] - 2800)})

    # 3) one zoom per chart
    charts = page.query_selector_all('.chart')
    for i, c in enumerate(charts, 1):
        c.scroll_into_view_if_needed()
        page.wait_for_timeout(180)
        b = page.evaluate('(n)=>{const e=document.querySelectorAll(".chart")[n];const r=e.getBoundingClientRect();'
                          'return {x:r.left+window.scrollX,y:r.top+window.scrollY,w:r.width,h:r.height};}', i - 1)
        if not b:
            continue
        shot(page, f'03_chart_{i:02d}', clip={'x': max(0, b['x'] - 4), 'y': max(0, b['y'] - 4),
                                             'width': min(b['w'] + 8, 1440), 'height': min(b['h'] + 8, 2200)})
    report['charts_zoomed'] = len(charts)

    # 4) hover states
    for sel, nm in [('.kpi .tip', 'hero_tip'), ('.league .tip', 'league_tip'),
                    ('.bar button[data-k="period"][data-v="fy"]', 'ctrl_tip'),
                    ('.chart .tip', 'chart_tip'), ('.chip.n', 'chip_tip')]:
        # the CY25 chips only exist on the fiscal toggle; find the first visible match
        el = None
        for cand in page.query_selector_all(sel):
            try:
                if cand.is_visible() and cand.bounding_box():
                    el = cand
                    break
            except Exception:
                continue
        if el is None:
            print('hover skip (no visible element):', sel)
            continue
        try:
            el.scroll_into_view_if_needed()
            page.wait_for_timeout(120)
            el.hover(timeout=5000)
            page.wait_for_timeout(420)
            shot(page, f'04_hover_{nm}')
        except Exception as exc:
            print('hover failed:', sel, str(exc)[:90])

    # 5) the eight toggle combinations
    for combo in COMBOS:
        set_mode(page, combo)
        page.wait_for_timeout(260)
        nm = '05_' + '_'.join(combo)
        h = page.evaluate('document.body.scrollHeight')
        shot(page, nm + '_full')
        shot(page, nm + '_league', clip={'x': 0, 'y': page.evaluate('document.querySelector("#league").getBoundingClientRect().top + window.scrollY'),
                                        'width': 1440, 'height': 900})
        report['asserts']['combo_' + nm] = dom_assert(page, nm)
        # The sales-to-dealer file carries no warranty split. On a warranty-excluded setting
        # in that direction the page must say so rather than repeat the figure silently.
        _per, _dir, _wr = combo
        if _dir == 'dlr' and _wr == 'ex':
            _wb = page.evaluate(
                '() => { const w=document.querySelector(".warnbar");'
                'return w && w.offsetParent!==null ? w.innerText.replace(/\\s+/g," ").trim() : null; }')
            report.setdefault('warrsplit', {})[nm] = _wb
            if not _wb:
                report['asserts']['combo_' + nm].setdefault('basis', []).append(
                    'warranty-excluded + sales-to-dealer shows no split warning')
        st = page.evaluate('document.getElementById("stateChip").textContent')
        report.setdefault('combo_states', {})[nm] = st
        # sanity: a figure must actually change between combinations
        report.setdefault('figures', {})[nm] = page.evaluate(
            '() => { const t=document.querySelectorAll("#league tbody tr")[0];'
            'return t? Array.from(t.querySelectorAll("td")).slice(0,6).map(x=>x.innerText.replace(/\\s+/g," ").trim()).join(" | ") : null; }')

    # narrowest + widest with FY to catch overflow in the worst settings
    for w, tag in [(390, 'w390'), (1024, 'w1024')]:
        set_mode(page, ('fy', 'db', 'ex'))
        page.set_viewport_size({'width': w, 'height': 900})
        page.wait_for_timeout(320)
        shot(page, f'06_fyex_{tag}_full')
        report['asserts']['fyex_' + tag] = dom_assert(page, tag)

    br.close()

report['screenshots_taken'] = len(taken)
report['files'] = [os.path.basename(t) for t in taken]
with open(os.path.join(QA, '_qa_report.json'), 'w', encoding='utf-8') as f:
    json.dump(report, f, indent=1)
print('SCREENSHOTS TAKEN: %d' % len(taken))
for k, v in report['asserts'].items():
    bad = {a: b for a, b in v.items() if b}
    if bad:
        print('ASSERT FAIL @%s: %s' % (k, json.dumps(bad)[:900]))
print('done')
