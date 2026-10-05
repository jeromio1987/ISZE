import os, glob, re
from playwright.sync_api import sync_playwright

H = r'C:\Users\jerom\Desktop\claude\ISZE\02_dashboards\sales\ISZE_DB_Leakage_Review_CY2025.html'
QA = r'C:\Users\jerom\Desktop\claude\ISZE\02_dashboards\sales\_qa_db_leakage'
os.makedirs(QA, exist_ok=True)

CHROME = None
for c in [r'C:\Program Files\Google\Chrome\Application\chrome.exe',
          r'C:\Program Files (x86)\Google\Chrome\Application\chrome.exe',
          r'C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe',
          r'C:\Program Files\Microsoft\Edge\Application\msedge.exe']:
    if os.path.exists(c):
        CHROME = c
        break
print('browser:', CHROME)

# geometry audit
def audit(page, tag):
    js = """() => {
      const bad = [];
      document.querySelectorAll('body *').forEach(el => {
        const r = el.getBoundingClientRect();
        if (r.width === 0 || r.height === 0) return;
        if (el.scrollWidth > el.clientWidth + 2 && getComputedStyle(el).overflowX === 'visible')
          bad.push(['overflowX', el.tagName + '.' + el.className, el.scrollWidth, el.clientWidth]);
        const pr = el.parentElement ? el.parentElement.getBoundingClientRect() : null;
        if (pr && (r.right > pr.right + 3 || r.left < pr.left - 3))
          bad.push(['outside', el.tagName + '.' + el.className, Math.round(r.left), Math.round(r.right)]);
      });
      const de = document.documentElement;
      return {bad: bad.slice(0, 25), n_bad: bad.length,
              hscroll: de.scrollWidth > de.clientWidth + 2};
    }"""
    r = page.evaluate(js)
    print(f'  [{tag}] horizontalScroll={r["hscroll"]} issues={r["n_bad"]}')
    for b in r['bad'][:8]:
        print('      ', b)
    return r


with sync_playwright() as pw:
    br = pw.chromium.launch(executable_path=CHROME, args=['--no-sandbox'])
    allres = {}
    for w in [1440, 1280, 1024, 390]:
        ctx = br.new_context(viewport={'width': w, 'height': 950}, device_scale_factor=1)
        pg = ctx.new_page()
        pg.goto('file:///' + H.replace('\\', '/'), wait_until='load')
        pg.wait_for_timeout(700)
        allres[w] = audit(pg, f'{w}px')

        # full page slices
        total = pg.evaluate('document.body.scrollHeight')
        step = 950
        i = 1
        y = 0
        while y < total:
            pg.evaluate(f'window.scrollTo(0,{y})')
            pg.wait_for_timeout(160)
            pg.screenshot(path=os.path.join(QA, f'w{w}_slice{i:02d}.png'))
            i += 1
            y += step
        # section zooms
        for sel, name in [('section:nth-of-type(2)', 'league'),
                          ('section:nth-of-type(3)', 'replenishment'),
                          ('section:nth-of-type(4)', 'substitution'),
                          ('section:nth-of-type(5)', 'noprice'),
                          ('section:nth-of-type(6)', 'actions'),
                          ('.tgl', 'toggles')]:
            el = pg.query_selector(sel)
            if el:
                try:
                    el.scroll_into_view_if_needed()
                    pg.wait_for_timeout(180)
                    el.screenshot(path=os.path.join(QA, f'w{w}_zoom_{name}.png'))
                except Exception as e:
                    print('   zoom fail', name, e)
        if w == 1440:
            # toggle states
            for grp, val, nm in [('warr', 'exc', 'warranty_excluded'),
                                 ('dir', 'dealer', 'direction_dealer'),
                                 ('period', 'fy', 'period_fy')]:
                b = pg.query_selector(f'.tgl button[data-t="{grp}"][data-v="{val}"]')
                if b:
                    b.click()
                    pg.wait_for_timeout(350)
                    pg.screenshot(path=os.path.join(QA, f'tg_{nm}.png'))
            # tooltip hover
            k = pg.query_selector('.kpi')
            if k:
                k.hover()
                pg.wait_for_timeout(400)
                pg.screenshot(path=os.path.join(QA, 'hover_tooltip.png'))
        ctx.close()
    br.close()

imgs = sorted(glob.glob(os.path.join(QA, '*.png')))
print()
print('screenshots written:', len(imgs))
for i in imgs:
    print('  ', os.path.basename(i), round(os.path.getsize(i)/1024), 'KB')
