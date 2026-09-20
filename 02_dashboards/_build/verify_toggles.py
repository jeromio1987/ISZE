import os, sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
from playwright.sync_api import sync_playwright

H = r'C:\Users\jerom\Desktop\claude\ISZE\02_dashboards\sales\ISZE_DB_Leakage_Review_CY2025.html'
CHROME = r'C:\Program Files\Google\Chrome\Application\chrome.exe'

with sync_playwright() as pw:
    br = pw.chromium.launch(executable_path=CHROME, args=['--no-sandbox'])
    ctx = br.new_context(viewport={'width': 1440, 'height': 950})
    pg = ctx.new_page()
    pg.goto('file:///' + H.replace('\\', '/'), wait_until='load')
    pg.wait_for_timeout(700)

    def snap(tag):
        row1 = pg.eval_on_selector('#league-tbody tr:first-child', 'el => el.innerText')
        head3 = pg.eval_on_selector_all('.hstat .v', 'els => els.map(e=>e.textContent)')
        hd = pg.eval_on_selector('#league-hd', 'el => el.textContent')
        return f'{tag}\n   header={head3}\n   col7="{hd}"\n   row1={row1[:110]}'

    print(snap('DEFAULT (CY / ISZE->DB / warranty incl)'))

    pg.click('.tgl button[data-t="warr"][data-v="exc"]'); pg.wait_for_timeout(400)
    print(snap('WARRANTY EXCLUDED'))

    pg.click('.tgl button[data-t="dir"][data-v="dealer"]'); pg.wait_for_timeout(400)
    print(snap('DIRECTION DB->DEALER'))

    pg.click('.tgl button[data-t="period"][data-v="fy"]'); pg.wait_for_timeout(400)
    print(snap('PERIOD FISCAL'))

    # blank check for the 12 DBs with no dealer file
    blanks = pg.eval_on_selector_all('#league-tbody tr',
        'els => els.filter(e=>e.children[6].textContent.includes("—")).length')
    print()
    print('rows blank on the dealer column (expect 16 of 18 + no-data rows):', blanks)
    nrows = pg.eval_on_selector_all('#league-tbody tr', 'els => els.length')
    print('total league rows:', nrows)
    ctx.close(); br.close()
