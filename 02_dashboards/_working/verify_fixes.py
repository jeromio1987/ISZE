"""Quick re-check of fixed dashboards."""
from pathlib import Path
from playwright.sync_api import sync_playwright

ROOT = Path(r"C:\Users\jerom\Desktop\claude\ISZE\02_dashboards")
targets = [
    "sales/ISZE_Monthly_Sales_Tracker.html",
    "sales/ISZE_Competitiveness_Dashboard.html",
    "sales/Dealer_Sellout_AIM_GPS_ITUK_UTI_2025.html",
    "side/PROPERTIQ.html",
    "hub/PROJECT_HUB.html",
]

PROBE = """() => {
  const body = (document.body.innerText||'').replace(/\\s+/g,' ').trim();
  const canvases = [...document.querySelectorAll('canvas')].map(c => {
    let nz=0; try {
      const ctx=c.getContext('2d'); const w=Math.min(c.width||0,600), h=Math.min(c.height||0,400);
      if(!w||!h) return {blank:true,w,h,nz:0};
      const d=ctx.getImageData(0,0,w,h).data; for(let i=3;i<d.length;i+=16) if(d[i]>10) nz++;
    } catch(e){ return {blank:true, err:String(e)}; }
    return {w:c.width,h:c.height,nz, blank: nz<10};
  });
  const imgs = [...document.querySelectorAll('img')].map(i => ({src:i.currentSrc||i.src, ok:i.complete && i.naturalWidth>0}));
  const bars = document.querySelectorAll('#revenueChart .bar, .bar-group').length;
  const tableRows = document.querySelectorAll('#monthlyTableBody tr').length;
  return {bodyLen: body.length, bars, tableRows, canvases, imgsBad: imgs.filter(i=>!i.ok).map(i=>i.src),
          sample: body.slice(0,180)};
}"""

with sync_playwright() as p:
    browser = p.chromium.launch(
        channel="chrome",
        headless=True,
        proxy={"server": "http://127.0.0.1:9"},
        args=["--disable-web-security", "--allow-file-access-from-files"],
    )
    for rel in targets:
        page = browser.new_page(viewport={"width": 1440, "height": 900})
        errs = []
        page.on("pageerror", lambda e: errs.append(str(e)))
        path = ROOT / rel
        page.goto(path.resolve().as_uri(), wait_until="domcontentloaded", timeout=45000)
        page.wait_for_timeout(2500)
        probe = page.evaluate(PROBE)
        shot = ROOT / "_working" / "audit" / f"fixed__{rel.replace('/', '__')}.png"
        page.screenshot(path=str(shot), full_page=False)
        print("==", rel)
        print("  errs", errs[:3])
        print("  bars", probe["bars"], "rows", probe["tableRows"], "blankCanvases", sum(1 for c in probe["canvases"] if c.get("blank")))
        print("  imgsBad", len(probe["imgsBad"]), probe["imgsBad"][:2])
        print("  shot", shot.name)
        page.close()
    browser.close()
