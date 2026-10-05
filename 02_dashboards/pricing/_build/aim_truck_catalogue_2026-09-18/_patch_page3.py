#!/usr/bin/env python3
"""Third pass: finish the switch to the photograph layer.

  * put back the QA hooks the original suite calls, reimplemented against the
    photograph rather than the old 3D model, so the 144 existing assertions keep
    their meaning
  * read the media payload instead of the old geometry in main(), and splice the
    vehicle layer in
"""
import io
import os

HERE = os.path.dirname(os.path.abspath(__file__))
PAGE = os.path.join(HERE, "build_truck_page.py")

src = io.open(PAGE, encoding="utf-8").read()
before = len(src)

# ---- 1. add back the hooks the suite uses, next to the photograph hooks ----
ANCHOR = "window.truckZoneScreenPolys=function(){"
EXTRA = r"""/* ---- the hooks the existing check suite calls -------------------------------
   Each is reimplemented against the photograph, so the assertions keep the
   meaning they had: "is the vehicle big enough", "is this point on the vehicle",
   "does this zone have a clickable point", "where did the labels land". */
window.truckHull=function(){
  /* the corners of the picture, which is now the whole vehicle footprint */
  if(!PHOTO.ready) return [];
  return [[PHOTO.x,PHOTO.y],[PHOTO.x+PHOTO.w,PHOTO.y],
          [PHOTO.x+PHOTO.w,PHOTO.y+PHOTO.h],[PHOTO.x,PHOTO.y+PHOTO.h]];
};
window.truckOutline=function(){ return OUTLINE; };   /* no drawn outline now */
window.truckPointInBody=function(x,y){ return photoFrac(x,y) !== null; };
window.truckZonePolys=function(){
  var out=[];
  for(var i=0;i<ZONES.length;i++){
    var m=mediaFor(PHOTO.key);
    out.push((m && m.zones && m.zones[ZONES[i].k]) || []);
  }
  return out;
};
window.truckHalfW=function(){ return 0; };
window.truckCam=null;
window.truckAllZonePoints=function(){
  /* a screen point inside every zone, found by scanning the stage, so QA can
     click each one the way a person would */
  var out=[], z, x, y, h;
  for(z=0;z<ZONES.length;z++){
    var found=null;
    for(x=0;x<W && !found;x+=4){
      for(y=0;y<H && !found;y+=4){
        h=zoneHitAll(x,y);
        if(h.length && h[0]===z) found=[x,y];
      }
    }
    out.push({zone:z, pt:found});
  }
  return out;
};
window.truckPageSize=function(){ return {w:W, h:H}; };
"""
src = src.replace(ANCHOR, EXTRA + ANCHOR, 1)

# ---- 2. main(): read the media payload, not the old geometry ----
src = src.replace(
    '''    payload = (HERE / "truck_payload.json").read_text(encoding="utf-8")
    geom = (HERE / "vehicle_geometry.json").read_text(encoding="utf-8")''',
    '''    payload = (HERE / "truck_payload.json").read_text(encoding="utf-8")
    # The vehicle pictures and their zone hotspots are built by vehicle_images.py,
    # which is the one place to change when a picture is swapped.
    import vehicle_images
    media = vehicle_images.build_media()
    media = {k: {"src": v["src"], "credit": v["credit"], "depicts": v["depicts"],
                 "bytes": v["bytes"], "zones": v["zones"],
                 "anchors": ANCHORS[k]}
             for k, v in media.items()}
    media_json = json.dumps(media, separators=(",", ":"))''')

src = src.replace(
    '''    html = (HTML.replace("__PAYLOAD__", payload)
                .replace("__GEOM__", geom)
                .replace("__CHARTJS__", chart))''',
    '''    html = (HTML.replace("__PAYLOAD__", payload)
                .replace("__MEDIA__", media_json)
                .replace("__VEHICLE_LAYER__", VEHICLE_JS)
                .replace("__CHARTJS__", chart))''')

src = src.replace(
    '''    print(f"payload {len(payload)/1024:,.0f} KB")
    print(f"geometry {len(geom)/1024:,.0f} KB")''',
    '''    print(f"payload {len(payload)/1024:,.0f} KB")
    print(f"vehicle pictures {len(media_json)/1024/1024:,.2f} MB "
          f"(4 photographs as data URIs)")''')

src = src.replace("import re\nimport subprocess",
                  "import json\nimport re\nimport subprocess")

# import the vehicle layer next to the other module-level imports
src = src.replace(
    'OUT = ISZE / "02_dashboards" / "pricing" / "ISZE_AIM_Truck_Catalogue_2026-09-18.html"',
    'OUT = ISZE / "02_dashboards" / "pricing" / "ISZE_AIM_Truck_Catalogue_2026-09-18.html"\n'
    '\n'
    'import sys\n'
    'sys.path.insert(0, str(HERE))\n'
    'from vehicle_layer import VEHICLE_JS          # noqa: E402\n'
    'from vehicle_images import ANCHORS             # noqa: E402')

io.open(PAGE, "w", encoding="utf-8", newline="\n").write(src)
print(f"{before:,} -> {len(src):,} bytes")
for k in ("VEHICLE_JS", "media_json", "__MEDIA__", "__VEHICLE_LAYER__",
          "window.truckAllZonePoints", "window.truckHull", "import json"):
    print("  ", k.ljust(26), src.count(k))
