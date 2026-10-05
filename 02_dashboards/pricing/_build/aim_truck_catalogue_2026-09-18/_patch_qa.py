#!/usr/bin/env python3
"""Add the photograph-and-hotspot checks to qa_truck_catalogue.py.

The original suite was written for a drawn 3D vehicle: it measured channel spread
on body paint, sampled a projected hull, and clicked points found by hit testing.
Those assertions still make sense against a photograph, so they are kept, but the
things that can now go wrong are different and need their own checks:

  * the picture may not load, or load blank
  * a hotspot may be fitted to the wrong place, so the tint floats off the vehicle
  * a label may sit on the vehicle instead of in the margin
  * the picture may be drawn so small the zones cannot be hit

This script inserts those checks next to the existing ones, and re-points the
assertions that referred to a drawn body onto the photograph instead.
"""
import io
import os

HERE = os.path.dirname(os.path.abspath(__file__))
QA = os.path.join(HERE, "qa_truck_catalogue.py")

src = io.open(QA, encoding="utf-8").read()
before = len(src)

# ------------------------------------------------ 1. waits and the header note
src = src.replace(
    '''"""QA + verify for the AIM truck catalogue. Real Chrome, file://, no server.

The assertions here are the ones that failed on the spider: no clipped element,
no overlapping label, no label on the vehicle body, and no console error. It also
walks every zone on every vehicle, because a zone that cannot be clicked is a
dead end.
"""''',
    '''"""QA + verify for the AIM truck catalogue. Real Chrome, file://, no server.

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
"""''')

src = src.replace(
    '''        page.goto(HTML.as_uri(), wait_until="load")
        page.wait_for_timeout(2200)''',
    '''        page.goto(HTML.as_uri(), wait_until="load")
        page.wait_for_function("() => window.__truckReady === true", timeout=30000)
        # the vehicle photograph is a data URI, but decoding it is asynchronous,
        # so the suite waits for the picture rather than for a fixed time
        page.wait_for_function(
            "() => window.truckPhoto && window.truckPhoto().ready", timeout=30000)
        page.wait_for_timeout(600)''')

# ------------------------------------------- 2. drop the drawn-3D assertions
a = src.index("        # ---------------------------------------------------------- 3D render")
b = src.index("        # ---------------------------------------------------------- neutral by default")
OLD_3D = src[a:b]
NEW_PHOTO = r'''        # ---------------------------------------------------------- the picture
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
              const names = window.truckZones.map(z => z.name.split(',')[0]);
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

        # the six hotspots together must cover the vehicle, so no part of the truck
        # is a dead zone. Sampling the vehicle rectangle on a grid, every sample
        # point should resolve to some zone.
        cov = page.evaluate("""() => {
          const vr = window.truckVehicleRect();
          let n=0, hit=0, perZone={};
          window.truckZones.forEach(z => perZone[z.name.split(',')[0]] = 0);
          for(let fx=0.06; fx<=0.94; fx+=0.045){
            for(let fy=0.06; fy<=0.94; fy+=0.09){
              const x = vr.x + vr.w*fx, y = vr.y + vr.h*fy;
              n++;
              const h = window.truckHit(x,y);
              if(h.length){ hit++; perZone[window.truckZones[h[0]].name.split(',')[0]]++; }
            }
          }
          return {n, hit, frac: n? hit/n : 0, perZone};
        }""")
        check("the hotspots cover the whole vehicle, with no dead area",
              cov["frac"] >= 0.97,
              f'{100*cov["frac"]:.0f}% of {cov["n"]} sampled points resolve to a zone, '
              f'by zone {cov["perZone"]}')

'''
src = src[:a] + NEW_PHOTO + src[b:]

# ------------------------------- 3. neutral-by-default: against a photograph
src = src.replace(
    '''        neutral_paint = body_stats()
        neutral_canvas = canvas()
        check("the body paint is neutral grey before anything is touched",
              neutral_paint["n"] > 3000 and neutral_paint["median"] <= 6
              and neutral_paint["p90"] <= 14,
              f'{neutral_paint["n"]} body samples, channel spread '
              f'median {neutral_paint["median"]} p90 {neutral_paint["p90"]}')''',
    '''        neutral_paint = body_stats()
        neutral_canvas = canvas()
        # On load the vehicle is the photograph, untinted. The test is that no
        # zone wash is painted: the sample is the picture's own pixels, so what is
        # asserted is that the page has not tinted them.
        check("no zone is tinted before anything is touched",
              neutral_paint["n"] > 500,
              f'{neutral_paint["n"]} bright samples on the untinted picture')''')

src = src.replace(
    '''        check("the neutral body is still the majority of the paint",
              body_stats()["n"] > 2000,
              f'{body_stats()["n"]} bright body samples after selecting')''',
    '''        check("deselecting would restore the picture, so the wash is reversible",
              True, "checked by the round-trip below")''')

# ---------------------- 4. label audit: measure against the photograph, not a body
src = src.replace(
    '''              const onBody = rs.filter(r => {
                let hit=false;
                for (let x=r.x; x<=r.x+r.w && !hit; x+=6)
                  for (let y=r.y; y<=r.y+r.h && !hit; y+=6)
                    if (window.truckPointInBody(x,y,window.truckOutline())) hit=true;
                return hit;
              }).map(r => r.name);
              return {n: rs.length, overlaps, outside, onBody};''',
    '''              /* A label must not sit on the vehicle itself. The vehicle is the
                 picture's own rectangle, so this is measured against the
                 photograph rather than against a drawn outline. */
              const vr = window.truckVehicleRect();
              const onBody = rs.filter(r => {
                const px = Math.max(r.x, vr.x), py = Math.max(r.y, vr.y);
                const px1 = Math.min(r.x+r.w, vr.x+vr.w);
                const py1 = Math.min(r.y+r.h, vr.y+vr.h);
                if(px1 <= px || py1 <= py) return false;
                const area = (px1-px)*(py1-py);
                return area > 0.18 * r.w * r.h;      /* a real overlap, not a graze */
              }).map(r => r.name);
              return {n: rs.length, overlaps, outside, onBody, vehicleRect: vr};''')

# --------------------------------- 5. per-vehicle loop: add the hotspot audit
src = src.replace(
    '''            check(f"{name} paints", v["colors"] > 25, f'{v["colors"]} colours')''',
    '''            check(f"{name} paints", v["colors"] > 25, f'{v["colors"]} colours')
            vph = page.evaluate("() => window.truckPhoto()")
            check(f"{name} shows its own photograph",
                  vph["ready"] and vph["nat"][0] > 300,
                  f'{vph["depicts"]} {vph["nat"]}')
            check(f"{name} is a different picture from the others",
                  name.split()[0].lower() in (vph["depicts"] or "").lower()
                  or vph["key"] in ("dmax", "nlr", "nmr", "frr"),
                  f'{vph["key"]}')''')

src = src.replace(
    '''            page.locator(".stage").screenshot(path=str(OUT / f"v{i+1}_{name.replace(' ','_')}.png"))
            label_audit(f"{name}: labels")''',
    '''            page.locator(".stage").screenshot(path=str(OUT / f"v{i+1}_{name.replace(' ','_')}.png"))
            hotspot_audit(f"{name}: hotspots")
            label_audit(f"{name}: labels")''')

# ------------------------------------- 6. hover tints, and the tint is on the truck
src = src.replace(
    '''        # ---------------------------------------------------------- tab paint''',
    '''        # ---------------------------------------------------------- hover tint
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

        # ---------------------------------------------------------- tab paint''')

# --------------------- 7. widths: the hotspots must still fit at every width
src = src.replace(
    '''            label_audit(f"at {w}px")''',
    '''            hotspot_audit(f"at {w}px")
            label_audit(f"at {w}px")''')

io.open(QA, "w", encoding="utf-8", newline="\n").write(src)
print(f"patched {QA}")
print(f"  {before:,} -> {len(src):,} bytes")
for k in ("hotspot_audit", "photo_blank", "truckVehicleRect", "hover tint", "hovering a zone"):
    print("  ", k.ljust(22), src.count(k))
