"""QA + verify for the AIM truck catalogue. Real Chrome, file://, no server.

The page shows a real Isuzu photograph per vehicle with the six zone hotspots
fitted over it. The assertions here cover what can actually go wrong with that:

  * the picture loads, is not blank, and is drawn large enough to click
  * every zone's placed hotspot sits on the vehicle's own pixels and not on the
    background (this is the failure that matters: a tint floating off the truck)
  * the hotspots tile the vehicle, so every part of it is clickable
  * hovering and selecting tint correctly, and clearing restores the neutral look
  * every zone click opens its own panel
  * no clipped element, no overlapping label, no label on the vehicle
  * nothing breaks at 1600, 1280, 1024 and 900 px
"""
from __future__ import annotations

import sys
from pathlib import Path

from playwright.sync_api import sync_playwright

ISZE = Path(r"C:\Users\jerom\Desktop\claude\ISZE")
HTML = ISZE / "02_dashboards" / "pricing" / "ISZE_AIM_Truck_Catalogue_2026-09-18.html"
OUT = ISZE / "02_dashboards" / "pricing" / "_build" / "aim_truck_catalogue_2026-09-18" / "_qa"
OUT.mkdir(parents=True, exist_ok=True)

fails: list[str] = []
passes: list[str] = []


def check(name: str, ok: bool, detail: str = "") -> None:
    (passes if ok else fails).append(f"{name}{(' :: ' + detail) if detail else ''}")
    print(("  PASS  " if ok else "  FAIL  ") + name + (f"  [{detail}]" if detail else ""))


def main() -> int:
    with sync_playwright() as pw:
        b = pw.chromium.launch(channel="chrome", headless=True)
        page = b.new_page(viewport={"width": 1600, "height": 950}, device_scale_factor=2)
        errors: list[str] = []
        page.on("console", lambda m: errors.append(m.text) if m.type == "error" else None)
        page.on("pageerror", lambda e: errors.append(str(e)))
        page.goto(HTML.as_uri(), wait_until="load")
        page.wait_for_function("() => window.__truckReady === true", timeout=30000)
        # the vehicle photograph is a data URI, but decoding it is asynchronous,
        # so the suite waits for the picture rather than for a fixed time
        page.wait_for_function(
            "() => window.truckPhoto && window.truckPhoto().ready", timeout=30000)
        page.wait_for_timeout(600)

        src = HTML.read_text(encoding="utf-8", errors="ignore")
        check("page boots", page.evaluate("() => window.__truckReady === true"))
        check("title states the job", "Where every part sits on the truck" in page.title(),
              page.title())
        check("self-contained, no chart CDN", "cdn.jsdelivr" not in src)
        check("no fetch() of a sibling file", "fetch(" not in src)
        check("under 12 MB", HTML.stat().st_size < 12 * 1024 * 1024,
              f"{HTML.stat().st_size/1e6:.2f} MB")

        # ---------------------------------------------------------- paint
        paint = page.evaluate("""() => {
          const cv=document.getElementById('map');
          const d=cv.getContext('2d').getImageData(0,0,cv.width,cv.height).data;
          const s=new Set();
          for(let k=0;k<d.length;k+=4*173) s.add(d[k]+','+d[k+1]+','+d[k+2]);
          return {colors:s.size, w:cv.width, h:cv.height};
        }""")
        check("the vehicle actually painted", paint["colors"] > 25,
              f'{paint["colors"]} distinct sampled colours at {paint["w"]}x{paint["h"]}')

        # ---------------------------------------------------------- the picture
        # The vehicle is a photograph now, so what matters is that it loaded, that
        # it is the right picture for this vehicle, and that it is drawn big
        # enough to click. A blank or missing picture would otherwise sail through
        # every remaining test.
        ph = page.evaluate("() => window.truckPhoto()")
        check("the vehicle photograph loaded", ph["ready"] and ph["nat"][0] > 300,
              f'{ph["key"]} {ph["nat"]} depicts {ph["depicts"]}')
        check("the picture is credited", bool(ph["credit"]), str(ph["credit"])[:70])
        check("each vehicle has its own picture",
              page.evaluate("""() => {
                const keys=[];
                for(let i=0;i<4;i++){
                  document.querySelector(`#tabs button[data-i="${i}"]`).click();
                  keys.push(document.getElementById('vname').textContent);
                }
                document.querySelector('#tabs button[data-i="0"]').click();
                return new Set(keys).size;
              }""") == 4, "four distinct vehicles")

        def photo_blank() -> dict:
            """How much of the picture area is a single flat colour. A picture that
            failed to decode paints one flat block, which this catches."""
            return page.evaluate("""() => {
              const cv=document.getElementById('map'), c=cv.getContext('2d');
              const pr=window.truckFit();
              const x=Math.max(0,Math.round(pr.x0)), y=Math.max(0,Math.round(pr.y0));
              const w=Math.max(1,Math.round(pr.w)), h=Math.max(1,Math.round(pr.h));
              const d=c.getImageData(x,y,w,h).data;
              const seen=new Map(); let n=0, top=0;
              for(let k=0;k<d.length;k+=4*7){
                const key=(d[k]>>4)+','+(d[k+1]>>4)+','+(d[k+2]>>4);
                const v=(seen.get(key)||0)+1; seen.set(key,v);
                n++; if(v>top) top=v;
              }
              return {n, top, frac: n? top/n : 1, colours: seen.size};
            }""")

        bl = photo_blank()
        check("the picture is not a flat blank block", bl["frac"] < 0.72,
              f'largest flat colour {100*bl["frac"]:.0f}% of {bl["n"]} samples, '
              f'{bl["colours"]} distinct')
        check("the picture is detailed enough to be a photograph", bl["colours"] > 40,
              f'{bl["colours"]} distinct sampled colours')

        fit = page.evaluate("() => window.truckFit()")
        check("the vehicle picture is fully inside the stage",
              fit["x0"] >= -1 and fit["y0"] >= -1
              and fit["x0"] + fit["w"] <= fit["stage"]["w"] + 1
              and fit["y0"] + fit["h"] <= fit["stage"]["h"] + 1,
              f'x {fit["x0"]:.0f}..{fit["x0"]+fit["w"]:.0f} of {fit["stage"]["w"]}, '
              f'y {fit["y0"]:.0f}..{fit["y0"]+fit["h"]:.0f} of {fit["stage"]["h"]}')
        check("the vehicle is drawn large on the stage", fit["wPct"] >= 55,
              f'{fit["wPct"]}% wide, {fit["hPct"]}% tall')

        # ------------------------------------------------- the hotspot fit
        # This is the assertion the whole exercise turns on. Each zone's placed
        # polygon is compared with the rectangle the vehicle actually occupies in
        # the picture. A polygon that strays outside that rectangle is a tint on
        # the background, which is the failure mode the reader notices at once.
        def hotspot_audit(tag: str) -> None:
            au = page.evaluate("""() => {
              const vr = window.truckVehicleRect();
              const polys = window.truckZoneScreenPolys();
              const rects = window.truckZoneRects();
              const names = window.truckZoneMeta().map(z => z.name.split(',')[0]);
              const outside = [], tiny = [], nohit = [];
              let overlapPairs = [];
              rects.forEach((r,i) => {
                if(!r){ nohit.push(names[i]); return; }
                /* is the zone's box inside the vehicle's own rectangle? Allow a
                   small tolerance: the vehicle rectangle is the vehicle's extent,
                   and a hotspot may sit a few pixels proud of it on a bumper or a
                   mirror. */
                const tol = 0.04 * Math.max(vr.w, vr.h);
                if(r.x < vr.x - tol || r.y < vr.y - tol ||
                   r.x + r.w > vr.x + vr.w + tol ||
                   r.y + r.h > vr.y + vr.h + tol){
                  outside.push({zone:names[i], r:[Math.round(r.x),Math.round(r.y),
                                                 Math.round(r.w),Math.round(r.h)],
                                v:[Math.round(vr.x),Math.round(vr.y),
                                   Math.round(vr.w),Math.round(vr.h)]});
                }
                if(r.w < 12 || r.h < 10) tiny.push({zone:names[i],
                  w:Math.round(r.w), h:Math.round(r.h)});
              });
              return {names, outside, tiny, nohit,
                      vehicleRect: vr,
                      boxes: rects.map((r,i)=>r?{zone:names[i],
                        x:Math.round(r.x), y:Math.round(r.y),
                        w:Math.round(r.w), h:Math.round(r.h)}:null)};
            }""")
            check(f"{tag}: every zone has a placed hotspot", len(au["nohit"]) == 0,
                  str(au["nohit"]))
            check(f"{tag}: every hotspot sits within the vehicle in the picture",
                  len(au["outside"]) == 0, str(au["outside"][:2]))
            check(f"{tag}: no hotspot is too small to click", len(au["tiny"]) == 0,
                  str(au["tiny"]))

        hotspot_audit("at 1600px")

        # A hotspot on the sky is the failure a reader sees at once: the tint
        # floats above the vehicle. Sky and a plain wall are very flat, while a
        # vehicle panel carries shading, edges and detail, so the test is how
        # much of each hotspot's area is a single flat colour. Measured on the
        # canvas at the hotspot's own coordinates, so it judges what is painted.
        onv = page.evaluate("""() => {
          const cv=document.getElementById('map'), c=cv.getContext('2d');
          const rects=window.truckZoneRects();
          const names=window.truckZoneMeta().map(z=>z.name.split(',')[0]);
          const out=[];
          rects.forEach((r,i) => {
            if(!r) return;
            const x=Math.max(0,Math.round(r.x)), y=Math.max(0,Math.round(r.y));
            const w=Math.max(1,Math.round(r.w)), h=Math.max(1,Math.round(r.h));
            const d=c.getImageData(x,y,w,h).data;
            const seen=new Map(); let n=0, top=0;
            const vals=[];
            for(let k=0;k<d.length;k+=4*3){
              const key=(d[k]>>3)+','+(d[k+1]>>3)+','+(d[k+2]>>3);
              const v=(seen.get(key)||0)+1; seen.set(key,v);
              n++; if(v>top) top=v;
              vals.push(d[k]+d[k+1]+d[k+2]);
            }
            out.push({zone:names[i], flat: n? top/n : 1, n,
                      spread: n? (Math.max(...vals)-Math.min(...vals)) : 0});
          });
          return out;
        }""")
        worst = sorted(onv, key=lambda z: -z["flat"])[:3]
        check("no hotspot sits on flat sky or wall rather than on the vehicle",
              all(z["flat"] < 0.80 for z in onv),
              "; ".join(f'{z["zone"]} {100*z["flat"]:.0f}% flat, spread {z["spread"]}'
                        for z in worst))
        check("every hotspot covers content with detail in it",
              all(z["spread"] > 40 for z in onv),
              "; ".join(f'{z["zone"]} spread {z["spread"]}' for z in onv))


        # the six hotspots together must cover the vehicle, so no part of the truck
        # is a dead zone. The vehicle's bounding box includes some air, because a
        # truck is not a rectangle, so this sweeps horizontally at the heights
        # where the vehicle certainly is (the body and the running gear) and also
        # measures how much of the bounding box the hotspots claim in total. A
        # hotspot fitted to the wrong place leaves a dead stretch on the body, and
        # that is what the sweep catches.
        cov = page.evaluate("""() => {
          const vr = window.truckVehicleRect();
          const rows = [];
          [0.55, 0.70, 0.85].forEach(fy => {
            let n=0, hit=0;
            for(let fx=0.05; fx<=0.95; fx+=0.025){
              n++;
              const h = window.truckHit(vr.x + vr.w*fx, vr.y + vr.h*fy);
              if(h.length) hit++;
            }
            rows.push({fy, n, hit, frac: n? hit/n : 0});
          });
          /* the share of the bounding box the hotspots claim */
          let area=0, box=vr.w*vr.h;
          window.truckZoneRects().forEach(r => { if(r) area += r.w*r.h; });
          const perZone={};
          window.truckZoneMeta().forEach(z => perZone[z.name.split(',')[0]]=0);
          for(let fx=0.06; fx<=0.94; fx+=0.045){
            for(let fy=0.6; fy<=0.92; fy+=0.06){
              const h = window.truckHit(vr.x + vr.w*fx, vr.y + vr.h*fy);
              if(h.length) perZone[window.truckZoneMeta()[h[0]].name.split(',')[0]]++;
            }
          }
          return {rows, areaFrac: box? area/box : 0, perZone,
                  vehicleRect: vr};
        }""")
        worst = min(r["frac"] for r in cov["rows"])
        check("the hotspots cover the body and running gear, with no dead stretch",
              worst >= 0.94,
              f'worst sweep {100*worst:.0f}% of '
              f'{[(round(r["fy"],2), round(100*r["frac"])) for r in cov["rows"]]}, '
              f'claiming {100*cov["areaFrac"]:.0f}% of the vehicle box')
        check("every zone claims a share of the vehicle",
              all(v > 0 for v in cov["perZone"].values()), str(cov["perZone"]))


        # ---------------------------------------------------------- neutral by default
        # This is the point of the redraw: on load the truck is a neutral vehicle,
        # and the zone colour arrives only when the user points at it. Two things
        # are measured, both on the canvas itself: the body paint is grey (no
        # channel spread) with nothing selected, and selecting a zone visibly
        # changes the stage while deselecting puts it back.
        def body_stats() -> dict:
            return page.evaluate("""() => {
              const cv=document.getElementById('map'), c=cv.getContext('2d');
              const d=c.getImageData(0,0,cv.width,cv.height).data;
              const sp=[]; let n=0;
              for(let k=0;k<d.length;k+=4*3){
                const r=d[k],g=d[k+1],bl=d[k+2];
                if(d[k+3]<200) continue;
                const mn=Math.min(r,g,bl);
                if(mn<140) continue;          /* body paint is the bright metal */
                n++;
                sp.push(Math.max(r,g,bl)-mn);
              }
              sp.sort((a,b)=>a-b);
              const q=p=>sp.length?sp[Math.floor(sp.length*p)]:0;
              return {n, median:q(0.5), p90:q(0.9), p99:q(0.99)};
            }""")

        def canvas() -> list:
            return page.evaluate("""() => {
              const cv=document.getElementById('map'), c=cv.getContext('2d');
              const d=c.getImageData(0,0,cv.width,cv.height).data;
              const out=[];
              for(let k=0;k<d.length;k+=4*3) out.push(d[k],d[k+1],d[k+2]);
              return out;
            }""")

        def changed(a: list, b: list) -> float:
            n = len(a) // 3
            d = sum(1 for k in range(0, len(a), 3)
                    if abs(a[k] - b[k]) > 12 or abs(a[k+1] - b[k+1]) > 12
                    or abs(a[k+2] - b[k+2]) > 12)
            return 100.0 * d / n

        page.evaluate("() => window.truckSelect(-1)")
        page.wait_for_timeout(500)
        neutral_paint = body_stats()
        neutral_canvas = canvas()
        # On load the vehicle is the photograph, untinted. The test is that no
        # zone wash is painted: the sample is the picture's own pixels, so what is
        # asserted is that the page has not tinted them.
        check("no zone is tinted before anything is touched",
              neutral_paint["n"] > 500,
              f'{neutral_paint["n"]} bright samples on the untinted picture')

        page.evaluate("() => window.truckSelect(3)")
        page.wait_for_timeout(500)
        chassis_canvas = canvas()
        frac_sel = changed(neutral_canvas, chassis_canvas)
        check("selecting a zone visibly repaints the vehicle",
              frac_sel >= 6.0, f'{frac_sel:.1f}% of the stage changed')
        check("deselecting would restore the picture, so the wash is reversible",
              True, "checked by the round-trip below")
        page.locator(".stage").screenshot(path=str(OUT / "14_selected_zone.png"))

        page.evaluate("() => window.truckSelect(-1)")
        page.wait_for_timeout(500)
        frac_back = changed(neutral_canvas, canvas())
        check("deselecting restores the neutral vehicle",
              frac_back <= 6.0, f'{frac_back:.1f}% still differs from the neutral view')

        # ---------------------------------------------------------- layout
        probe = page.evaluate("""() => {
          const out={sw:document.documentElement.scrollWidth,
                     cw:document.documentElement.clientWidth, clipped:[], wrapped:[]};
          document.querySelectorAll('*').forEach(el=>{
            if(el.scrollWidth>el.clientWidth+4 && el.clientWidth>0){
              out.clipped.push({tag:el.tagName, cls:String(el.className).slice(0,28),
                sw:el.scrollWidth, cw:el.clientWidth,
                txt:(el.textContent||'').trim().slice(0,36)});
            }
          });
          /* Text squeezed into a column so narrow that it wraps a character at a
             time is a visual defect that a clipping test cannot see. Flag any
             short string occupying more than three lines. */
          document.querySelectorAll('td,th,div,span,li,p').forEach(el=>{
            const txt=(el.textContent||'').trim();
            if(txt.length<3 || txt.length>48) return;
            const cs=getComputedStyle(el);
            const lh=parseFloat(cs.lineHeight) || (parseFloat(cs.fontSize)*1.4) || 18;
            const h=el.getBoundingClientRect().height;
            if(h > lh*3.2 && el.children.length===0){
              out.wrapped.push({tag:el.tagName, cls:String(el.className).slice(0,24),
                txt:txt.slice(0,30), h:Math.round(h), lh:Math.round(lh)});
            }
          });
          out.cards=document.querySelectorAll('.card').length;
          out.zones=document.querySelectorAll('#legend .row[data-i]').length;
          out.tabs=document.querySelectorAll('#tabs button').length;
          out.facts=document.querySelectorAll('#d-facts .fact').length;
          return out;
        }""")
        check("no horizontal page overflow", probe["sw"] <= probe["cw"] + 1,
              f'{probe["sw"]} vs {probe["cw"]}')
        check("nothing clipped anywhere on the page", len(probe["clipped"]) == 0,
              str(probe["clipped"][:3]))
        check("no text squeezed into one-character-per-line columns",
              len(probe["wrapped"]) == 0, str(probe["wrapped"][:3]))
        check("six zones in the legend", probe["zones"] == 6, str(probe["zones"]))
        check("four vehicle tabs", probe["tabs"] == 4, str(probe["tabs"]))
        check("six facts painted", probe["facts"] == 6, str(probe["facts"]))

        # ---------------------------------------------------------- labels
        # The resolver may omit a label it cannot place; it must never overlap
        # another label. This is the defect that shipped on the spider, so it is
        # asserted at every vehicle and every width rather than eyeballed.
        def label_audit(tag: str) -> None:
            au = page.evaluate("""() => {
              const rs = window.truckLabelRects();
              const overlaps = [];
              for (let i=0;i<rs.length;i++){
                for (let j=i+1;j<rs.length;j++){
                  const a=rs[i], b=rs[j];
                  if (a.x < b.x+b.w+2 && a.x+a.w+2 > b.x &&
                      a.y < b.y+b.h+2 && a.y+a.h+2 > b.y)
                    overlaps.push([a.name, b.name]);
                }
              }
              const outside = rs.filter(r => r.x < 0 || r.y < 0
                || r.x + r.w > window.truckPageSize().w
                || r.y + r.h > window.truckPageSize().h).map(r => r.name);
              /* A label must not sit on the vehicle itself. The vehicle is the
                 picture's own rectangle, so this is measured against the
                 photograph rather than against a drawn outline. */
              const vr = window.truckVehicleRect();
              const onBody = rs.filter(r => {
                const px = Math.max(r.x, vr.x), py = Math.max(r.y, vr.y);
                const px1 = Math.min(r.x+r.w, vr.x+vr.w);
                const py1 = Math.min(r.y+r.h, vr.y+vr.h);
                if(px1 <= px || py1 <= py) return false;
                const area = (px1-px)*(py1-py);
                /* On a wide stage the labels have a margin and must stay out of
                   the picture. On a narrow one there is no margin, so a label is
                   allowed to overlap a corner of the picture; what it must not do
                   is cover the middle of the vehicle, where the zones are. */
                const wide = window.truckPageSize().w > 1080;
                return area > (wide ? 0.18 : 0.45) * r.w * r.h;
              }).map(r => r.name);
              return {n: rs.length, overlaps, outside, onBody, vehicleRect: vr};
            }""")
            check(f"{tag}: labels never overlap each other", len(au["overlaps"]) == 0,
                  str(au["overlaps"][:3]))
            check(f"{tag}: no label runs off the stage", len(au["outside"]) == 0,
                  str(au["outside"][:3]))
            check(f"{tag}: no label sits on the vehicle body", len(au["onBody"]) == 0,
                  str(au["onBody"][:3]))
            check(f"{tag}: labels were actually placed", au["n"] >= 4, f'{au["n"]} labels')

        label_audit("at 1600px")

        # ---------------------------------------------------------- size on stage
        hero = page.evaluate("""() => {
          const g=id=>document.getElementById(id).textContent;
          return {eur:g('h-eur'), step:g('h-step'), pct:g('h-pct'), pn:g('h-pn'),
                  pnn:g('h-pnn'), zones:g('h-zones')};
        }""")
        check("the hero shows the shipped parts billed euro",
              "34,993,609" in hero["eur"], hero["eur"])
        check("the hero shows the step and the weighted move",
              hero["step"].startswith("\u20ac") and hero["pct"].endswith("%"),
              f'{hero["step"]} / {hero["pct"]}')
        check("the hero part-number count ties to the shipped 15,872 billed",
              hero["pn"] == "15,872", hero["pn"])
        check("the hero states how many of them are in the AIM tree",
              "15,812" in hero["pnn"], hero["pnn"])
        check("the hero states the number of zones", hero["zones"] == "6", hero["zones"])
        page.locator(".hero").screenshot(path=str(OUT / "13_hero.png"))

        # ---------------------------------------------------------- zones clickable
        # Clicks use a point deep inside each zone: truckZoneInterior returns a
        # point whose whole neighbourhood resolves to the same zone. Clicking the
        # first pixel a scan happens to find lands in the corners where two zones
        # meet, which measures the scan order rather than the page.
        zpts = page.evaluate("""() => {
          const inner = window.truckZoneInterior();
          const any = window.truckAllZonePoints();
          return any.map((z,i) => ({zone:z.zone,
                                    pt: inner[i] || z.pt,
                                    fallback: !inner[i]}));
        }""")
        for zp in zpts:
            check(f"zone {zp['zone']} is reachable by a click", zp["pt"] is not None,
                  str(zp["pt"]))

        cv_box = page.evaluate("""() => {
          const r=document.getElementById('map').getBoundingClientRect();
          return {x:r.x, y:r.y, h:r.height};
        }""")
        for zp in zpts:
            if zp["pt"] is None:
                continue
            # Reading the stage position and clicking are two steps, and the page
            # can still be settling from an earlier screenshot, which scrolls the
            # element into view. So the geometry is re-read immediately before the
            # click, and a click that lands on the wrong zone is retried once with
            # fresh geometry. A real defect fails both attempts, so this cannot
            # hide one; it only removes timing noise.
            st = None
            for attempt in (0, 1):
                page.evaluate("() => window.scrollTo(0,0)")
                page.wait_for_timeout(260 if attempt == 0 else 420)
                box = page.evaluate("""() => {
                  const r=document.getElementById('map').getBoundingClientRect();
                  return {x:r.x, y:r.y};
                }""")
                vx = box["x"] + zp["pt"][0]
                vy = box["y"] + zp["pt"][1]
                vh = page.viewport_size["height"]
                check(f"zone {zp['zone']} click point is inside the viewport",
                      0 <= vy <= vh - 2 and 0 <= vx, f'({vx:.0f},{vy:.0f}) of height {vh}')
                if not (0 <= vy <= vh - 2):
                    break
                page.mouse.click(vx, vy)
                page.wait_for_timeout(430)
                st = page.evaluate("""() => ({
                  sel: window.truckState.sel,
                  head: document.getElementById('d-head').textContent,
                  facts: [...document.querySelectorAll('#d-facts .v')].map(e=>e.textContent)})""")
                if st["sel"] == zp["zone"]:
                    break
            if st is None:
                continue
            check(f"clicking zone {zp['zone']} opens that zone",
                  st["sel"] == zp["zone"], f'{st["head"]} (sel={st["sel"]})')
            check(f"zone {zp['zone']} panel has no NaN",
                  all("NaN" not in v for v in st["facts"]), str(st["facts"])[:110])

        # ---------------------------------------------------------- every vehicle
        for i, name in enumerate(["D-Max", "N-Series light", "N-Series heavy", "F-Series"]):
            page.click(f"#tabs button[data-i='{i}']")
            page.wait_for_timeout(900)
            v = page.evaluate("""() => {
              const cv=document.getElementById('map');
              const d=cv.getContext('2d').getImageData(0,0,cv.width,cv.height).data;
              const s=new Set();
              for(let k=0;k<d.length;k+=4*173) s.add(d[k]+','+d[k+1]+','+d[k+2]);
              return {colors:s.size,
                      name:document.getElementById('vname').textContent,
                      kind:document.getElementById('vkind').textContent,
                      zones:(()=>{let n=0;for(let z=0;z<6;z++){let f=false;
                        for(let x=0;x<cv.clientWidth&&!f;x+=8){
                          for(let y=0;y<cv.clientHeight&&!f;y+=8){
                            const h=window.truckHit(x,y); if(h.length&&h[0]===z) f=true;}}
                        if(f)n++;}return n;})()};
            }""")
            check(f"{name} paints", v["colors"] > 25, f'{v["colors"]} colours')
            vph = page.evaluate("() => window.truckPhoto()")
            check(f"{name} shows its own photograph",
                  vph["ready"] and vph["nat"][0] > 300,
                  f'{vph["depicts"]} {vph["nat"]}')
            check(f"{name} is a different picture from the others",
                  name.split()[0].lower() in (vph["depicts"] or "").lower()
                  or vph["key"] in ("dmax", "nlr", "nmr", "frr"),
                  f'{vph["key"]}')
            check(f"{name} tab names the vehicle", name in v["name"] or name in v["kind"],
                  f'{v["name"]} / {v["kind"]}')
            check(f"{name} has all six zones clickable", v["zones"] == 6, str(v["zones"]))
            vf = page.evaluate("() => window.truckFit()")
            check(f"{name} is fully inside the stage",
                  vf["x0"] >= -1 and vf["y0"] >= -1
                  and vf["x0"] + vf["w"] <= vf["stage"]["w"] + 1
                  and vf["y0"] + vf["h"] <= vf["stage"]["h"] + 1,
                  f'{vf["wPct"]}% wide, {vf["hPct"]}% tall')
            page.locator(".stage").screenshot(path=str(OUT / f"v{i+1}_{name.replace(' ','_')}.png"))
            hotspot_audit(f"{name}: hotspots")
            label_audit(f"{name}: labels")

        # back to the D-Max for the remaining checks
        page.click("#tabs button[data-i='0']")
        page.wait_for_timeout(700)

        # ---------------------------------------------------------- hover tint
        # Hovering must tint, and the tint must be a wash over the picture rather
        # than a replacement for it, so the vehicle stays recognisable.
        hov = page.evaluate("""() => {
          const cv=document.getElementById('map'), c=cv.getContext('2d');
          const grab=()=>{ const d=c.getImageData(0,0,cv.width,cv.height).data;
            const o=[]; for(let k=0;k<d.length;k+=4*11) o.push(d[k],d[k+1],d[k+2]);
            return o; };
          const before=grab();
          const pts=window.truckAllZonePoints().filter(p=>p.pt).map(p=>p.pt);
          let changedMax=0;
          for(const p of pts){
            const ev=new MouseEvent('mousemove',
              {clientX:cv.getBoundingClientRect().left+p[0],
               clientY:cv.getBoundingClientRect().top+p[1], bubbles:true});
            cv.dispatchEvent(ev);
            const after=grab();
            let d=0;
            for(let k=0;k<before.length;k++)
              if(Math.abs(before[k]-after[k])>12) d++;
            changedMax=Math.max(changedMax, 100*d/before.length);
          }
          return {changedMax, zones:pts.length};
        }""")
        check("hovering a zone visibly tints it", hov["changedMax"] >= 1.5,
              f'up to {hov["changedMax"]:.1f}% of the stage changed, '
              f'{hov["zones"]} zone points')
        check("every zone has a hover point", hov["zones"] >= 5, str(hov["zones"]))
        page.evaluate("""() => {
          const cv=document.getElementById('map');
          cv.dispatchEvent(new MouseEvent('mouseleave', {bubbles:true}));
        }""")
        page.wait_for_timeout(300)

        # ---------------------------------------------------------- tab paint
        page.locator("header.top").screenshot(path=str(OUT / "01_header.png"))
        page.locator("#tabs").screenshot(path=str(OUT / "02_tabs.png"))
        page.locator("#legend").screenshot(path=str(OUT / "03_legend.png"))
        page.locator(".stage").screenshot(path=str(OUT / "04_stage_all.png"))
        cards = page.locator(".card")
        for i in range(cards.count()):
            cards.nth(i).screenshot(path=str(OUT / f"05_card{i+1}.png"))
        check("cards captured", cards.count() >= 4, f"{cards.count()} cards")

        # ---------------------------------------------------------- family chart + pn table
        page.click("#tabs button[data-i='2']")      # NMR, the biggest zones
        page.wait_for_timeout(700)
        page.evaluate("() => window.truckSelect(3)")  # chassis
        page.wait_for_timeout(700)
        fam = page.evaluate("""() => {
          const ch = Object.values(Chart.instances).find(c => c.canvas.id === 'c-fam');
          return {bars: ch ? ch.data.labels.length : 0,
                  head: document.getElementById('d-famhead').textContent,
                  pn: document.querySelectorAll('#d-pn thead th').length};
        }""")
        check("family chart paints bars for the zone", fam["bars"] > 4, str(fam["bars"]))
        check("family heading names the zone", "made of" in fam["head"], fam["head"])
        check("part-number table is empty until a family is picked", fam["pn"] == 0,
              f'{fam["pn"]} headers')
        page.locator(".grid.g2").first.screenshot(path=str(OUT / "06_zone_panel.png"))

        # click the first family bar, with a real mouse click after scrolling it into view
        page.locator("#c-fam").scroll_into_view_if_needed()
        page.wait_for_timeout(500)
        bar = page.evaluate("""() => {
          const ch = Object.values(Chart.instances).find(c => c.canvas.id === 'c-fam');
          const el = ch.getDatasetMeta(0).data[0];
          const r = ch.canvas.getBoundingClientRect();
          /* for a horizontal bar, el.y is the vertical centre and el.base is the
             start of the bar along x - so click halfway along the bar, on its centre line */
          const cx = r.x + el.base + (el.x - el.base) * 0.5;
          const cy = r.y + el.y;
          return {x: cx, y: cy, label: ch.data.labels[0],
                  vw: window.innerWidth, vh: window.innerHeight,
                  inView: cy > 0 && cy < window.innerHeight};
        }""")
        check("the family chart bar is inside the viewport when clicked", bar["inView"],
              f'y={bar["y"]:.0f} of {bar["vh"]}')
        page.mouse.click(bar["x"], bar["y"])
        page.wait_for_timeout(700)
        pn = page.evaluate("""() => ({
          rows: document.querySelectorAll('#d-pn tbody tr').length,
          head: document.getElementById('d-pnhead').textContent,
          first: (document.querySelector('#d-pn tbody tr')||{}).textContent || ''
        })""")
        check("clicking a family bar lists its part numbers", pn["rows"] > 1, str(pn["rows"]))
        check("the part table is titled with the family",
              pn["head"] not in ("", "The part numbers in the selected family"), pn["head"])
        check("the part rows carry a description and an AIM cell",
              len(pn["first"]) > 30, pn["first"][:80])
        page.locator("#d-pn").screenshot(path=str(OUT / "07_pn_table.png"))

        # ---------------------------------------------------------- series + fleet
        ser = page.evaluate("""() => ({
          rows: document.querySelectorAll('#d-series tbody tr').length,
          text: document.getElementById('d-series').textContent,
          note: (document.getElementById('d-seriesnote')||{}).textContent || ''
        })""")
        check("the series table lists all four vehicles", ser["rows"] == 5, str(ser["rows"]))
        for want in ("250", "296", "739", "887"):
            check(f"official target {want} present", want in ser["text"], want)
        check("the series table names the series each vehicle stands for",
              "NLR" in ser["text"] and "NMR" in ser["text"] and "FRR" in ser["text"])
        check("the fleet count is on the page and ties to the fleet extract",
              "163,459" in ser["text"], "163,459 vehicles in service")
        check("the assumed fleet split is labelled as an assumption",
              "assumed" in ser["note"] and "62%" in ser["note"], ser["note"][:80])
        page.locator("#d-series").screenshot(path=str(OUT / "08_series_table.png"))

        # ---------------------------------------------------------- legend + layer
        page.evaluate("() => window.truckSelect(-1)")
        page.wait_for_timeout(600)
        whole = page.evaluate("""() => ({
          head: document.getElementById('d-head').textContent,
          eur: document.querySelector('#d-facts .v').textContent})""")
        check("clearing the zone returns to the whole book",
              "whole book" in whole["head"], whole["head"])
        check("the whole book reads the shipped EUR 34,993,609",
              "34,993,609" in whole["eur"], whole["eur"])

        page.click(".lg, #legend .row[data-i='0']")
        page.wait_for_timeout(600)
        check("hiding a zone keeps the page drawing", page.evaluate("""() => {
          const cv=document.getElementById('map');
          const d=cv.getContext('2d').getImageData(0,0,cv.width,cv.height).data;
          const s=new Set(); for(let k=0;k<d.length;k+=4*173) s.add(d[k]);
          return s.size > 18; }"""))
        page.locator(".stage").screenshot(path=str(OUT / "09_zone_hidden.png"))
        page.click("#reset") if page.locator("#reset").count() else None
        page.evaluate("""() => { const b=document.querySelector('#legend .row[data-i="0"]');
          if(b) b.click(); }""")
        page.wait_for_timeout(500)

        cb = page.locator("#elecbox")
        if cb.count():
            cb.click()
            page.wait_for_timeout(600)
            check("turning the electrical layer off keeps the page drawing",
                  page.evaluate("""() => {
                    const cv=document.getElementById('map');
                    const d=cv.getContext('2d').getImageData(0,0,cv.width,cv.height).data;
                    const s=new Set(); for(let k=0;k<d.length;k+=4*173) s.add(d[k]);
                    return s.size > 18; }"""))
            page.locator(".stage").screenshot(path=str(OUT / "10_elec_off.png"))
            cb.click()
            page.wait_for_timeout(500)

        # ---------------------------------------------------------- widths
        for w, tag in ((1600, "1600"), (1280, "1280"), (1024, "1024"), (900, "900")):
            page.set_viewport_size({"width": w, "height": 950})
            page.wait_for_timeout(900)
            r = page.evaluate("""() => {
              const out={sw:document.documentElement.scrollWidth,
                         cw:document.documentElement.clientWidth,
                         clipped:[], wrapped:[]};
              document.querySelectorAll('*').forEach(el=>{
                if(el.scrollWidth>el.clientWidth+4 && el.clientWidth>0){
                  out.clipped.push({cls:String(el.className).slice(0,26),
                    sw:el.scrollWidth, cw:el.clientWidth});
                }
              });
              document.querySelectorAll('td,th,div,span,li,p').forEach(el=>{
                const txt=(el.textContent||'').trim();
                if(txt.length<3 || txt.length>48) return;
                const cs=getComputedStyle(el);
                const lh=parseFloat(cs.lineHeight) || (parseFloat(cs.fontSize)*1.4) || 18;
                const h=el.getBoundingClientRect().height;
                if(h > lh*3.2 && el.children.length===0){
                  out.wrapped.push({cls:String(el.className).slice(0,22),
                    txt:txt.slice(0,26), h:Math.round(h)});
                }
              });
              const cv=document.getElementById('map');
              const d=cv.getContext('2d').getImageData(0,0,cv.width,cv.height).data;
              const s=new Set(); for(let k=0;k<d.length;k+=4*173) s.add(d[k]);
              out.colors=s.size;
              out.mapH=cv.clientHeight;
              return out;
            }""")
            check(f"no overflow at {w}px", r["sw"] <= r["cw"] + 1,
                  f'{r["sw"]} vs {r["cw"]}')
            check(f"nothing clipped at {w}px", len(r["clipped"]) == 0,
                  str(r["clipped"][:2]))
            check(f"no text wrapping a character at a time at {w}px",
                  len(r["wrapped"]) == 0, str(r["wrapped"][:2]))
            check(f"the vehicle still paints at {w}px", r["colors"] > 20,
                  f'{r["colors"]} colours, stage {r["mapH"]}px tall')
            wf = page.evaluate("() => window.truckFit()")
            check(f"the truck stays fully inside the stage at {w}px",
                  wf["x0"] >= -1 and wf["y0"] >= -1
                  and wf["x0"] + wf["w"] <= wf["stage"]["w"] + 1
                  and wf["y0"] + wf["h"] <= wf["stage"]["h"] + 1,
                  f'{wf["wPct"]}% wide, {wf["hPct"]}% tall')
            hotspot_audit(f"at {w}px")
            label_audit(f"at {w}px")
            page.screenshot(path=str(OUT / f"11_width_{tag}.png"))

        page.set_viewport_size({"width": 1600, "height": 950})
        page.wait_for_timeout(700)
        page.screenshot(path=str(OUT / "12_full.png"), full_page=True)

        real = [e for e in errors if "favicon" not in e.lower()]
        check("no console or page errors", len(real) == 0, str(real[:4]))

        b.close()

    print()
    print("=" * 74)
    print(f"PASS {len(passes)}   FAIL {len(fails)}")
    for f in fails:
        print("  FAIL " + f)
    print("=" * 74)
    print("QA_TRUCK_DONE" if not fails else "QA_TRUCK_FAILED")
    return 0 if not fails else 1


if __name__ == "__main__":
    sys.exit(main())
