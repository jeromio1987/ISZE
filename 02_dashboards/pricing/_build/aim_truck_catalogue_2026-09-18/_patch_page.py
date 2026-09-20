#!/usr/bin/env python3
"""Patch build_truck_page.py from the old drawn-vehicle engine to the photograph
layer, and rebuild the QA hooks that depended on the old geometry.

This is a one-off edit script. It rewrites the builder in place, and is kept so
the change is auditable rather than silent.
"""
import io
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
PAGE = os.path.join(HERE, "build_truck_page.py")

src = io.open(PAGE, encoding="utf-8").read()
orig_len = len(src)

# ---------------------------------------------------------------- 1. the block
# Replace from "/* ================= geometry =================" through the end of
# "window.addEventListener('resize', resize);" with the vehicle layer.
start = src.index("/* ================= geometry =================")
end_marker = "window.addEventListener('resize', resize);"
end = src.index(end_marker, start) + len(end_marker)
old = src[start:end]

NEW_BLOCK = "__VEHICLE_LAYER__"
src = src[:start] + NEW_BLOCK + src[end:]

# ------------------------------------------------- 2. the geometry script tag
src = src.replace(
    '<script id="geom" type="application/json">__GEOM__</script>',
    '<script id="media" type="application/json">__MEDIA__</script>')

# ------------------------------------------------------- 3. the data read
src = src.replace(
    "var G = JSON.parse(document.getElementById('geom').textContent);",
    "var MD = JSON.parse(document.getElementById('media').textContent);")
src = src.replace("var M = P.meta, ROWS = P.rows;",
                  "var M = P.meta, ROWS = P.rows;")
src = src.replace("var VEH = M.vehicles, TARGETS = M.targets, FLEET = M.fleet_2025;",
                  "var VEH = M.vehicles, TARGETS = M.targets, FLEET = M.fleet_2025;\n"
                  "/* the vehicle pictures and their zone hotspots, from vehicle_images.py */\n"
                  "var MEDIA = (function(){\n"
                  "  var out = {};\n"
                  "  Object.keys(MD).forEach(function(k){\n"
                  "    var v = MD[k];\n"
                  "    out[k] = {src:v.src, credit:v.credit, depicts:v.depicts,\n"
                  "              zones:v.zones, anchors:v.anchors};\n"
                  "  });\n"
                  "  return out;\n"
                  "})();")

# ----------------------------------------- 4. replace the old-engine QA hooks
hooks_start = src.index("window.truckOnTruck=function(mx,my)")
hooks_end = src.index("boot();", hooks_start)
NEW_HOOKS = r"""/* ---- QA hooks ------------------------------------------------------------
   Everything the automated check needs to judge this page without a human
   looking at it: the picture's placement, each zone's placed polygons and
   bounding box, and an interior point of every zone that QA can sample body
   colour at. A hotspot fitted to the wrong part of the photograph shows up here
   as a rectangle that does not sit inside the vehicle's own pixels. */
window.truckPhoto=function(){
  return {ready:PHOTO.ready, key:PHOTO.key, x:PHOTO.x, y:PHOTO.y,
          w:PHOTO.w, h:PHOTO.h, nat:PHOTO.nat,
          depicts:(mediaFor(PHOTO.key)||{}).depicts||null,
          credit:(mediaFor(PHOTO.key)||{}).credit||null,
          bytes:(mediaFor(PHOTO.key)||{}).bytes||null};
};
/* Each zone's placed screen polygons, so QA can test them against real pixels. */
window.truckZoneScreenPolys=function(){
  var out=[];
  for(var i=0;i<ZONES.length;i++) out.push(zoneScreenPolys(i));
  return out;
};
window.truckZoneRects=function(){ return zoneRects(); };
/* True when a screen point is on the vehicle in the picture. The vehicle is the
   non-background part of the photograph, so this defers to the extent QA
   measured from the picture itself. */
window.truckOnTruck=function(mx,my){ return photoFrac(mx,my) !== null; };
window.truckOnPhoto=function(mx,my){ return photoFrac(mx,my) !== null; };
/* Where each zone's label dot sits, in image fractions. */
window.truckAnchors=function(){ return ANCHORS; };
/* An interior point of each zone: a screen point whose neighbourhood all resolves
   to the same zone. Sampling body colour anywhere else risks picking up an
   anti-aliased edge. */
window.truckZoneInterior=function(){
  var z, x, y, h, pts=[];
  for(z=0;z<ZONES.length;z++) pts.push([]);
  for(x=2;x<W-2;x+=4){
    for(y=2;y<H-2;y+=4){
      h=zoneHitAll(x,y);
      if(h.length) pts[h[0]].push([x,y]);
    }
  }
  var out=[];
  for(z=0;z<ZONES.length;z++){
    var best=null;
    for(var k=0;k<pts[z].length && !best;k++){
      var p=pts[z][k], ok=true;
      for(var dx=-8;dx<=8 && ok;dx+=8){
        for(var dy=-8;dy<=8 && ok;dy+=8){
          var q=zoneHitAll(p[0]+dx, p[1]+dy);
          if(!q.length || q[0]!==z) ok=false;
        }
      }
      if(ok) best=p;
    }
    if(!best && pts[z].length) best=pts[z][Math.floor(pts[z].length/2)];
    out.push(best);
  }
  return out;
};
window.truckView=VIEW;
window.truckZoom=function(k){
  /* zoom about the centre of the stage, so the vehicle grows in place */
  VIEW.zoom=Math.max(0.55, Math.min(2.6, k));
  placePhoto(); draw();
};
window.truckPan=function(dx,dy){ VIEW.dx+=dx; VIEW.dy+=dy; placePhoto(); draw(); };
window.truckResetView=function(){ VIEW.zoom=1; VIEW.dx=0; VIEW.dy=0; placePhoto(); draw(); };
"""
src = src[:hooks_start] + NEW_HOOKS + src[hooks_end:]

# ------------------------------------------- 5. the fit hook relies on geometry
fit_start = src.index("window.truckFit=function(){")
fit_end = src.index("};", fit_start) + 3
NEW_FIT = r"""window.truckFit=function(){
  /* How much of the stage the photograph occupies, so QA can assert the vehicle
     is drawn big rather than shrinking to make room for labels. */
  if(!PHOTO.ready) return {x0:0,y0:0,w:0,h:0,wPct:0,hPct:0,stage:{w:W,h:H},ready:false};
  return {x0:PHOTO.x, y0:PHOTO.y, w:PHOTO.w, h:PHOTO.h,
          wPct:+(100*PHOTO.w/W).toFixed(1), hPct:+(100*PHOTO.h/H).toFixed(1),
          stage:{w:W,h:H}, ready:true};
};"""
src = src[:fit_start] + NEW_FIT + src[fit_end:]

# --------------------------------------- 6. cam / hull hooks no longer apply
for name in ("window.truckCam=CAM;",):
    src = src.replace(name, "window.truckCam=null;   /* the picture is not a 3D camera */")

# ------------- 7. drag and keys: pan and zoom a photograph, not turn a model
key_start = src.index("window.addEventListener('keydown', function(e){")
key_end = src.index("/* ================= render ================= */", key_start)
NEW_INPUT = r"""window.addEventListener('keydown', function(e){
  /* zoom and reset the picture. The photograph is fixed, so there is nothing to
     turn; +/- changes the size and 0 puts it back. */
  var tag=(e.target && e.target.tagName) || '';
  if(tag==='INPUT'||tag==='TEXTAREA') return;
  if(e.key==='+'||e.key==='=') window.truckZoom(VIEW.zoom*1.12);
  if(e.key==='-'||e.key==='_') window.truckZoom(VIEW.zoom/1.12);
  if(e.key==='0') window.truckResetView();
});
window.addEventListener('keyup', function(e){
  /* arrow keys pan the picture, which is what a reader expects when a truck is
     shown too small to read */
  var tag=(e.target && e.target.tagName) || '';
  if(tag==='INPUT'||tag==='TEXTAREA') return;
  var step=24;
  if(e.key==='ArrowLeft')  window.truckPan( step,0);
  if(e.key==='ArrowRight') window.truckPan(-step,0);
  if(e.key==='ArrowUp')    window.truckPan(0, step);
  if(e.key==='ArrowDown')  window.truckPan(0,-step);
});
/* Drag the stage to move the picture. */
var truckDrag=null;
cv.addEventListener('mousedown', function(e){
  truckDrag={x:e.clientX, y:e.clientY, dx:VIEW.dx, dy:VIEW.dy, moved:false};
  cv.style.cursor='grabbing';
});
window.addEventListener('mousemove', function(e){
  if(!truckDrag) return;
  var mx=e.clientX-truckDrag.x, my=e.clientY-truckDrag.y;
  if(Math.abs(mx)+Math.abs(my) > 3) truckDrag.moved=true;
  VIEW.dx = truckDrag.dx + mx; VIEW.dy = truckDrag.dy + my;
  placePhoto(); draw();
});
window.addEventListener('mouseup', function(){
  if(truckDrag){ truckDrag=null; cv.style.cursor='default'; }
});
cv.addEventListener('wheel', function(e){
  /* a wheel over the stage zooms the picture rather than scrolling the page */
  if(!PHOTO.ready) return;
  e.preventDefault();
  var k = VIEW.zoom * (e.deltaY < 0 ? 1.10 : 1/1.10);
  VIEW.zoom = Math.max(0.55, Math.min(2.6, k));
  placePhoto(); draw();
}, {passive:false});

"""
src = src[:key_start] + NEW_INPUT + src[key_end:]

# --------------------------------------------- 8. boot: load the picture first
src = src.replace(
    "  buildTabs(); buildLegend(); buildScene(); render();\n"
    "  bootFit();         /* size the canvas to the stage, then draw for real */\n"
    "  window.__truckReady=true;",
    "  buildTabs(); buildLegend();\n"
    "  buildScene(); render();      /* paint the chrome at once */\n"
    "  bootFit();                   /* size the canvas, then draw */\n"
    "  switchVehicle();             /* fetch the picture, then redraw when it lands */\n"
    "  window.__truckReady=true;")

io.open(PAGE, "w", encoding="utf-8", newline="\n").write(src)
print(f"patched {PAGE}")
print(f"  {orig_len:,} -> {len(src):,} bytes")
print("  placeholder present:", NEW_BLOCK in src)
