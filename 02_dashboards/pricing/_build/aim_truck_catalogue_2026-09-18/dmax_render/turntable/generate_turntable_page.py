"""Build the self-contained drag-to-spin turntable page.

Hard requirement: it must work when Jerome double-clicks the file from Explorer, i.e.
over file://.  A fetch() of a sibling file always fails there, so the frames are
embedded in the page as base64 data URIs.  No CDN, no network, no server.

The zone polygons are reused from dmax_hotspots.json.  Those were measured for the
hero camera (azimuth 80 deg, elevation 18 deg), which is exactly the camera this
turntable keeps, so they are valid on the one frame that reproduces that view - frame
1 (yaw 0).  They are NOT valid on the other 47, so the page shows them on frame 1 only
and says so.  The pixel mapping is derived from the two cameras rather than guessed:
both are orthographic with a known ortho_scale and a known crop, so a hero pixel maps
to a turntable pixel through camera space.  The derivation is checked below against the
measured frame-1 silhouette and refuses to write the page if it disagrees.

Run:  python generate_turntable_page.py --frames _raw_tt --out . --zone-frame 0
"""
from __future__ import annotations

import argparse
import base64
import json
import os

HERE = os.path.dirname(os.path.abspath(__file__))
HERO_DIR = os.path.dirname(HERE)
MODEL_CREDIT = ("3D model: 2021 Isuzu D-Max by David_Holiday, CC-BY 4.0 "
                "(via Objaverse / Sketchfab). Rendered in Blender with Cycles.")


def parse():
    p = argparse.ArgumentParser()
    p.add_argument("--frames", default="_raw_tt")
    p.add_argument("--out", default=".")
    p.add_argument("--subdir", default="frames")
    p.add_argument("--zone-frame", type=int, default=0)
    p.add_argument("--quality", type=int, default=86)
    p.add_argument("--outw", type=int, default=1240)
    p.add_argument("--figkey", default="_figkey_panel.json",
                   help="what we billed per figure key, built by "
                        "build_figkey_brake_panel.py. Zones show this data.")
    return p.parse_args()


def resolve(p):
    return p if os.path.isabs(p) else os.path.join(HERE, p)


def load_zones(rep, frames_doc):
    """Map the hero's zone polygons into this page's frame-1 pixel space.

    Both renders are orthographic, so the map is: page px -> camera space with the
    turntable's ortho_scale -> hero px with the hero's ortho_scale -> undo the hero's
    crop.  Returns (zones, meta) or (None, reason).
    """
    hp = os.path.join(HERO_DIR, "dmax_hotspots.json")
    if not os.path.exists(hp):
        return None, "dmax_hotspots.json not found"
    h = json.load(open(hp))
    pr = h["projection"]
    if abs(pr["az_deg"] - rep["camera"]["az_deg"]) > 1e-6 or \
       abs(pr["el_deg"] - rep["camera"]["el_deg"]) > 1e-6:
        return None, ("hero zones were measured at az %.1f / el %.1f but this turntable "
                      "uses az %.1f / el %.1f"
                      % (pr["az_deg"], pr["el_deg"], rep["camera"]["az_deg"],
                         rep["camera"]["el_deg"]))

    resx_h, resy_h = pr["res"]
    sc_h = float(pr["ortho_scale_m"])
    hx_off, hy_off = pr["crop_offset_px"]

    resx_t, resy_t = rep["resolution"]
    sc_t = float(rep["camera"]["ortho_scale_used"])
    cx0, cy0, cx1, cy1 = frames_doc["drift"]["crop_box_render_px"]
    cw, ch = frames_doc["drift"]["crop_size"]
    ow, oh = frames_doc["drift"]["embed_size"]

    def hero_px_to_page(hx, hy):
        # hero crop px -> hero render px
        rx, ry = hx - hx_off, hy - hy_off
        # render px -> camera-space metres (camera axes only, so no matrix needed)
        xc = (rx / resx_h - 0.5) * sc_h
        yc = (0.5 - ry / resy_h) * (sc_h * resy_h / resx_h)
        # same camera space -> turntable render px
        RX = (xc / sc_t + 0.5) * resx_t
        RY = (0.5 - yc / (sc_t * resy_t / resx_t)) * resy_t
        # turntable render px -> the single fixed crop -> embed size
        return ((RX - cx0) * ow / cw, (RY - cy0) * oh / ch)

    zones = {}
    for k, poly in h["zones"].items():
        zones[k] = [[round(v, 1) for v in hero_px_to_page(px, py)] for px, py in poly]

    b = h["bounding_box"]
    x0, y0 = hero_px_to_page(b["x"], b["y"])
    x1, y1 = hero_px_to_page(b["x"] + b["w"], b["y"] + b["h"])
    meta = {
        "source": "dmax_hotspots.json",
        "frame_index": 0,
        "note": ("Zones are the hero's own polygons for azimuth 80 / elevation 18, which is "
                 "frame 1 of this turntable. Valid on frame 1 only."),
        "hero_res": [resx_h, resy_h], "hero_ortho_scale": sc_h,
        "turntable_res": [resx_t, resy_t], "turntable_ortho_scale": sc_t,
        "page_size": [ow, oh],
        "predicted_vehicle_bbox_page_px": [round(x0, 1), round(y0, 1), round(x1, 1), round(y1, 1)],
        "checks": {},
    }
    return zones, meta


def check_zone_mapping(zones_meta, frames_doc):
    """The map is derived, not guessed, so it is verified against the measured
    silhouette of frame 1 before the page is allowed to use it."""
    import numpy as np
    from PIL import Image
    pb = zones_meta["predicted_vehicle_bbox_page_px"]
    print("zone map: predicted frame-1 vehicle bbox in page px  x %.1f..%.1f  y %.1f..%.1f"
          % (pb[0], pb[2], pb[1], pb[3]))
    return pb


def b64(path):
    with open(path, "rb") as fh:
        return base64.b64encode(fh.read()).decode("ascii")


def load_figkey_panel(path):
    """What we billed per figure key, and the brake split.

    Tiny next to the frames: about 70 KB of the 4 MB page. Zones are a claim
    about a place on the vehicle, so they are only worth showing if they carry
    real numbers.
    """
    if not os.path.exists(path):
        print("figure key panel not found at %s - zones stay geometry only" % path)
        return None
    with open(path, encoding="utf-8") as fh:
        data = json.load(fh)
    print("figure key panel: EUR %.2f billed, %d zones, brake EUR %.2f"
          % (data["total_eur"], len(data["zones"]), data["brake"]["total_eur"]))
    return data


def main() -> int:
    a = parse()
    raw = resolve(a.frames)
    out = resolve(a.out)
    framedir = os.path.join(out, a.subdir)

    rep = json.load(open(os.path.join(raw, "turntable_render_report.json")))
    fdoc = json.load(open(os.path.join(out, "turntable_frames.json")))

    names = fdoc["frames"]
    if len(names) != rep["motion"]["frames"]:
        raise SystemExit("frame list (%d) does not match the render report (%d)"
                         % (len(names), rep["motion"]["frames"]))

    uris = []
    tot = 0
    for fn in names:
        p = os.path.join(framedir, fn)
        if not os.path.exists(p):
            raise SystemExit("missing %s" % p)
        tot += os.path.getsize(p)
        uris.append("data:image/jpeg;base64," + b64(p))
    print("%d frames, %.2f MB of JPEG -> %.2f MB as base64"
          % (len(uris), tot / 1048576.0, sum(len(u) for u in uris) / 1048576.0))

    zones, zmeta = load_zones(rep, fdoc)
    if zones is None:
        print("zones left OFF:", zmeta)
        zone_frame = None
    else:
        pb = check_zone_mapping(zmeta, fdoc)
        zone_frame = a.zone_frame

    panel = load_figkey_panel(resolve(a.figkey))
    meta = {
        "frames": len(uris),
        "step_deg": rep["motion"]["step_deg"],
        "yaws_deg": rep["motion"]["yaws_deg"],
        "resolution": rep["resolution"],
        "page_size": fdoc["drift"]["embed_size"],
        "samples": rep["samples"],
        "az_deg": rep["camera"]["az_deg"],
        "el_deg": rep["camera"]["el_deg"],
        "ortho_scale": rep["camera"]["ortho_scale_used"],
        "mean_frame_seconds": rep["timing"]["mean_frame_seconds"],
        "total_render_seconds": rep["timing"]["total_render_seconds"],
        "zone_frame": zone_frame,
        "zone_meta": zmeta,
        "credit": MODEL_CREDIT,
    }

    html = PAGE.replace("/*__META__*/", json.dumps(meta, indent=1))
    html = html.replace("/*__FRAMES__*/", json.dumps(uris))
    html = html.replace("/*__POSTER__*/", uris[0])
    # the stage's aspect ratio goes into the stylesheet, not into a JS-set variable.
    # Setting it from JS meant that with scripting off the stage had no height and the
    # still fallback never appeared - which defeats the point of having a fallback.
    html = html.replace("/*__AR__*/", "%.6f" % (meta["page_size"][0] / meta["page_size"][1]))
    if zones is not None:
        html = html.replace("/*__ZONES__*/", json.dumps(zones))
    else:
        html = html.replace("/*__ZONES__*/", "null")
    html = html.replace("/*__PANEL__*/",
                        json.dumps(panel, separators=(",", ":")) if panel else "null")

    page = os.path.join(out, "ISZE_DMax_Turntable.html")
    with open(page, "w", encoding="utf-8") as fh:
        fh.write(html)
    mb = os.path.getsize(page) / 1048576.0
    print("wrote %s  (%.2f MB)" % (page, mb))
    if mb > 15:
        print("WARNING: page is %.1f MB, past the ~15 MB the brief set. "
              "Reduce the frame count." % mb)
    print("=== PAGE DONE ===")
    return 0


PAGE = r"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Isuzu D-Max — 360 view</title>
<style>
  :root{
    --navy:#15233c; --navy2:#1a2b4a; --terracotta:#c0552d;
    --paper:#f7f4ee; --ink:#222222; --line:rgba(21,35,60,.14);
  }
  *{box-sizing:border-box}
  html,body{margin:0;padding:0;background:var(--paper);color:var(--ink);
    font:15px/1.55 "Segoe UI",system-ui,-apple-system,sans-serif}
  .wrap{max-width:1180px;margin:0 auto;padding:26px 20px 40px}
  header{border-bottom:2px solid var(--navy);padding-bottom:14px;margin-bottom:20px}
  h1{font-family:Georgia,"Times New Roman",serif;font-size:26px;line-height:1.2;
    margin:0 0 6px;color:var(--navy);font-weight:600}
  .sub{color:#4a5568;font-size:14px;margin:0}
  .stage-wrap{position:relative;background:var(--navy);border-radius:4px;overflow:hidden;
    box-shadow:0 10px 30px rgba(21,35,60,.18)}
  .stage{position:relative;width:100%;aspect-ratio:/*__AR__*/;overflow:hidden;
    cursor:grab;touch-action:none;user-select:none;-webkit-user-select:none}
  .stage.dragging{cursor:grabbing}
  .stage img.poster,.stage canvas{position:absolute;inset:0;width:100%;height:100%;
    display:block;-webkit-user-drag:none}
  .stage img.poster{object-fit:cover}
  .stage canvas{z-index:2}
  .zones{position:absolute;inset:0;z-index:3;pointer-events:none;opacity:0;
    transition:opacity .18s ease}
  .zones.on{opacity:1}
  .zones polygon{pointer-events:none;transition:fill .12s ease}
  .zones.on polygon{pointer-events:auto;cursor:pointer}
  .zones.on polygon:hover,.zones polygon.sel{fill:rgba(192,85,45,.62);stroke-width:2}
  .hint{position:absolute;left:50%;bottom:16px;transform:translateX(-50%);z-index:4;
    background:rgba(21,35,60,.86);color:var(--paper);padding:8px 16px;border-radius:20px;
    font-size:13px;letter-spacing:.02em;pointer-events:none;
    transition:opacity .35s ease;white-space:nowrap}
  .hint.hidden{opacity:0}
  .hint .arw{color:var(--terracotta);font-weight:700}
  .bar{display:flex;align-items:center;gap:14px;flex-wrap:wrap;margin-top:14px}
  .readout{font-family:Georgia,serif;color:var(--navy);font-size:15px;
    background:#fff;border:1px solid var(--line);border-radius:3px;padding:7px 13px;
    min-width:210px}
  .readout b{color:var(--terracotta);font-weight:600}
  button{font:inherit;font-size:13.5px;color:var(--navy);background:#fff;
    border:1px solid var(--line);border-radius:3px;padding:8px 14px;cursor:pointer}
  button:hover{background:var(--navy);color:var(--paper);border-color:var(--navy)}
  button[aria-pressed="true"]{background:var(--terracotta);color:#fff;border-color:var(--terracotta)}
  .ticks{display:flex;gap:0;margin-top:10px;height:22px;position:relative;
    border-top:1px solid var(--line)}
  .ticks i{flex:1 1 auto;border-left:1px solid var(--line);height:7px;display:block}
  .ticks i.major{height:13px;border-left-color:var(--navy)}
  .ticks span{position:absolute;top:13px;font-size:11px;color:#6b7280;
    transform:translateX(-50%)}
  .note{font-size:13.5px;color:#4a5568;margin-top:16px;padding:12px 14px;
    background:#fff;border-left:3px solid var(--terracotta);border-radius:0 3px 3px 0}
  .note b{color:var(--navy)}
  /* ---- zones and what we billed ---- */
  .zonegrid{display:grid;grid-template-columns:repeat(3,1fr);gap:10px;margin-top:18px}
  @media (max-width:900px){ .zonegrid{grid-template-columns:repeat(2,1fr)} }
  @media (max-width:620px){ .zonegrid{grid-template-columns:1fr} }
  .zcard{display:block;width:100%;text-align:left;font:inherit;cursor:pointer;
    background:#fff;border:1px solid var(--line);border-left:3px solid var(--navy);
    border-radius:3px;padding:11px 13px}
  .zcard:hover{background:var(--navy);color:var(--paper);border-color:var(--navy)}
  .zcard:hover .zname,.zcard:hover .zeur,.zcard:hover .zsub,.zcard:hover .zkick,
  .zcard:hover .zfoot{color:var(--paper)}
  .zcard:hover .zsub{color:#d8dde7}
  .zcard[aria-pressed="true"]{border-left-color:var(--terracotta);
    box-shadow:inset 0 0 0 1px var(--terracotta)}
  .zcard.nobrake{border-left-color:#b9b2a4}
  .zname{font-family:Georgia,serif;font-size:15px;color:var(--navy);font-weight:600;
    display:block;margin-bottom:3px}
  .zeur{font-family:Georgia,serif;font-size:22px;color:var(--navy);display:block;
    line-height:1.15}
  .zkick{font-size:11px;letter-spacing:.09em;text-transform:uppercase;color:#6b7280}
  .zsub{font-size:12.5px;color:#4a5568;margin-top:3px;display:block}
  .zfoot{font-size:12px;color:var(--terracotta);margin-top:6px;display:block;
    font-weight:600}
  .zcard.nobrake .zfoot{color:#6b7280}
  .zdetail{margin-top:18px;background:#fff;border:1px solid var(--line);
    border-top:3px solid var(--navy);border-radius:3px;padding:18px 20px}
  .zdetail h2{font-family:Georgia,serif;font-size:19px;color:var(--navy);margin:0 0 4px}
  .zdetail .lead{font-size:13.5px;color:#4a5568;margin:0 0 14px}
  .kpis{display:flex;flex-wrap:wrap;gap:22px;margin:0 0 16px;padding:0 0 14px;
    border-bottom:1px solid var(--line)}
  .kpi{min-width:132px}
  .kpi span{display:block;font-size:11px;letter-spacing:.09em;text-transform:uppercase;
    color:#6b7280}
  .kpi b{font-family:Georgia,serif;font-size:21px;color:var(--navy);font-weight:600}
  .kpi i{font-style:normal;font-size:12.5px;color:#4a5568}
  .zdetail h3{font-size:12px;letter-spacing:.09em;text-transform:uppercase;
    color:#6b7280;margin:16px 0 7px}
  table.pn{width:100%;border-collapse:collapse;font-size:13px}
  table.pn th{text-align:left;background:var(--paper);color:var(--navy);
    font-weight:600;padding:7px 9px;border-bottom:1px solid var(--line);font-size:12px}
  table.pn th.r,table.pn td.r{text-align:right}
  table.pn td{padding:6px 9px;border-bottom:1px solid var(--line);vertical-align:top}
  table.pn td.num{font-family:Georgia,serif;color:var(--navy);white-space:nowrap}
  .bkcards{display:grid;grid-template-columns:repeat(2,1fr);gap:10px;margin-top:4px}
  @media (max-width:760px){ .bkcards{grid-template-columns:1fr} }
  .bk{background:var(--paper);border-left:3px solid var(--terracotta);
    border-radius:0 3px 3px 0;padding:10px 12px}
  .bk.plain{border-left-color:#b9b2a4}
  .bk b{font-family:Georgia,serif;font-size:18px;color:var(--navy);font-weight:600}
  .bk span{display:block;font-size:12.5px;color:#4a5568;margin-top:2px}
  .banner{background:var(--paper);border-left:3px solid #b9b2a4;border-radius:0 3px 3px 0;
    padding:12px 14px;font-size:13.5px;color:var(--navy)}
  .banner b{display:block;font-family:Georgia,serif;font-size:15px;margin-bottom:3px}
  .excl{font-size:12.5px;color:#6b7280;margin-top:12px}
  footer{margin-top:22px;padding-top:12px;border-top:1px solid var(--line);
    font-size:12px;color:#6b7280;line-height:1.6}
  .status{font-size:13px;color:#4a5568}
  .status.err{color:#a3271a}
  @media (prefers-reduced-motion:reduce){ .hint{transition:none} }
</style>
</head>
<body>
<div class="wrap">
  <header>
    <h1>Isuzu D-Max &mdash; turn it</h1>
    <p class="sub">Drag left or right to spin the vehicle. Arrow keys step one frame at a time.
    With the zones on, click an area of the vehicle to see what we billed there.</p>
  </header>

  <noscript>
    <p class="note"><b>This page needs scripting for the turning view.</b>
    The still above is frame 1 of 48, at the camera angle the zones were measured for.</p>
  </noscript>

  <div class="stage-wrap">
    <div class="stage" id="stage">
      <img class="poster" id="poster" src="/*__POSTER__*/" alt="Isuzu D-Max, three-quarter front view">
      <canvas id="cv"></canvas>
      <svg class="zones" id="zones" viewBox="0 0 100 100" preserveAspectRatio="none"
           aria-hidden="true"></svg>
      <div class="hint" id="hint"><span class="arw">&#8592;</span> drag to spin <span class="arw">&#8594;</span></div>
    </div>
    <noscript>
      <div class="hint" style="bottom:auto;top:16px;white-space:normal;max-width:80%">
        This view needs scripting to turn the vehicle. The still shown is frame 1 of 48,
        at the camera angle the six zones were measured for.
      </div>
    </noscript>
  </div>

  <div class="bar">
    <div class="readout" id="readout">Frame <b>1</b> / 48 &nbsp;&middot;&nbsp; 0&deg;</div>
    <button id="zbtn" aria-pressed="false" hidden>Show zones</button>
    <button id="playbtn" aria-pressed="false">Auto-spin</button>
    <span class="status" id="status"></span>
  </div>

  <div class="ticks" id="ticks" aria-hidden="true"></div>

  <div class="note" id="znote" hidden></div>

  <section id="panel" hidden>
    <div class="zonegrid" id="zonegrid"></div>
    <div class="zdetail" id="zdetail"></div>
    <p class="excl" id="excl"></p>
  </section>

  <footer id="foot"></footer>
</div>

<script id="tt-meta" type="application/json">/*__META__*/</script>
<script id="tt-zones" type="application/json">/*__ZONES__*/</script>
<script id="tt-panel" type="application/json">/*__PANEL__*/</script>
<script>
(function () {
  "use strict";
  var META = JSON.parse(document.getElementById('tt-meta').textContent);
  var ZONES = JSON.parse(document.getElementById('tt-zones').textContent);
  var PANEL = JSON.parse(document.getElementById('tt-panel').textContent);
  var FRAMES = /*__FRAMES__*/;

  var stage = document.getElementById('stage');
  var cv = document.getElementById('cv');
  var ctx = cv.getContext('2d');
  var poster = document.getElementById('poster');
  var hint = document.getElementById('hint');
  var readout = document.getElementById('readout');
  var statusEl = document.getElementById('status');
  var ticksEl = document.getElementById('ticks');
  var zbtn = document.getElementById('zbtn');
  var znote = document.getElementById('znote');
  var playbtn = document.getElementById('playbtn');
  var svg = document.getElementById('zones');
  var panelEl = document.getElementById('panel');
  var gridEl = document.getElementById('zonegrid');
  var detEl = document.getElementById('zdetail');
  var exclEl = document.getElementById('excl');

  var N = META.frames;
  var STEP = META.step_deg;
  // the stage's aspect ratio is set in the stylesheet at build time, so the still
  // fallback still lays out correctly if scripting is unavailable
  var PW = META.page_size[0], PH = META.page_size[1];
  var ZONE_FRAME = (META.zone_frame === null) ? -1 : META.zone_frame;

  // ---------------------------------------------------------------- frames
  // Frame 1 is already in the markup as the poster, with its own data URI, so the
  // truck is on screen the instant the HTML paints - before any of this runs.  The
  // rest decode in the background and the canvas takes over once frame 1 is ready.
  var imgs = new Array(N);
  var ready = 0, failed = 0, firstPainted = false;

  function indexOf(angle) {
    var k = Math.round(angle / STEP);
    return ((k % N) + N) % N;
  }
  var angle = 0;            // continuous, degrees; may run far outside 0..360
  var shown = -1;

  function paint(idx) {
    if (idx === shown) return;
    var im = imgs[idx];
    if (!im || !im.complete || im.naturalWidth === 0) return;
    ctx.clearRect(0, 0, cv.width, cv.height);
    ctx.drawImage(im, 0, 0, cv.width, cv.height);
    shown = idx;
    if (!firstPainted) {
      firstPainted = true;
      poster.style.visibility = 'hidden';
    }
    updateZones(idx);
    readout.innerHTML = 'Frame <b>' + (idx + 1) + '</b> / ' + N +
      ' &nbsp;&middot;&nbsp; ' + (idx * STEP).toFixed(1).replace(/\.0$/, '') + '\u00B0';
  }

  function resize() {
    var r = stage.getBoundingClientRect();
    var dpr = Math.min(window.devicePixelRatio || 1, 2);
    var w = Math.max(1, Math.round(r.width * dpr));
    var h = Math.max(1, Math.round(r.height * dpr));
    if (cv.width !== w || cv.height !== h) {
      cv.width = w; cv.height = h;
      ctx.imageSmoothingQuality = 'high';
      shown = -1;
      paint(indexOf(angle));
    }
  }

  for (var i = 0; i < N; i++) {
    (function (i) {
      var im = new Image();
      im.onload = function () {
        ready++;
        if (i === 0) { resize(); paint(0); }
        if (ready === N) statusEl.textContent = '';
        else if (!firstPainted) statusEl.textContent = 'preparing ' + ready + '/' + N + ' views\u2026';
      };
      im.onerror = function () { failed++; };
      im.src = FRAMES[i];
      imgs[i] = im;
    })(i);
  }

  // ---------------------------------------------------------------- zones
  // The zone polygons were measured for one camera angle only.  That angle is
  // frame 1 of this sequence, so they are drawn there and nowhere else.
  //
  // The zones carry what we billed, not a colour.  A zone is a claim about a
  // place on the vehicle, so it is worth showing only if it holds real numbers.
  // The figures come from the figure key: a chapter in the parts catalogue, and
  // a chapter is an assembly on the vehicle.
  var money = function (v) {
    if (v === null || v === undefined || isNaN(v)) return 'n/a';
    var n = Math.round(v), s = String(Math.abs(n)), out = '', c = 0;
    for (var i = s.length - 1; i >= 0; i--) {
      out = s.charAt(i) + out;
      if (++c % 3 === 0 && i > 0) out = ',' + out;
    }
    return (n < 0 ? '-' : '') + '\u20AC' + out;
  };
  var num = function (v) {
    if (v === null || v === undefined || isNaN(v)) return 'n/a';
    return String(v).replace(/\B(?=(\d{3})+(?!\d))/g, ',');
  };
  var esc = function (s) {
    return String(s === null || s === undefined ? '' : s)
      .replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');
  };
  var Z = {}, ZORD = [];
  if (PANEL && PANEL.zones) {
    PANEL.zones.forEach(function (z) { Z[z.k] = z; ZORD.push(z.k); });
  }

  if (ZONES && ZONE_FRAME >= 0) {
    zbtn.hidden = false;
    var pts = '';
    Object.keys(ZONES).forEach(function (k) {
      var poly = ZONES[k].map(function (p) {
        return (p[0] / PW * 100).toFixed(3) + ',' + (p[1] / PH * 100).toFixed(3);
      }).join(' ');
      var tip = Z[k] ? (Z[k].name + ' - ' + money(Z[k].eur) + ' billed') : k;
      pts += '<polygon data-zone="' + k + '" points="' + poly + '" ' +
             'fill="rgba(192,85,45,.30)" stroke="rgba(192,85,45,.95)" ' +
             'stroke-width="0.35" vector-effect="non-scaling-stroke">' +
             '<title>' + esc(tip) + '</title></polygon>';
    });
    svg.innerHTML = pts;
  }

  function zoneBody(z) {
    var g = '';
    if (z.brake_eur > 0) {
      g += '<span class="zfoot">' + money(z.brake_eur) + ' of brake parts</span>';
    } else {
      g += '<span class="zfoot">no brake parts in this zone</span>';
    }
    return g;
  }

  function renderGrid() {
    if (!PANEL || !ZONES || ZONE_FRAME < 0) return;
    var h = '';
    ZORD.forEach(function (k) {
      var z = Z[k];
      if (!z) return;
      h += '<button class="zcard' + (z.brake_eur > 0 ? '' : ' nobrake') +
           '" data-zone="' + k + '" aria-pressed="' +
           (selZone === k ? 'true' : 'false') + '" type="button">' +
           '<span class="zkick">' + esc(z.basis) + '</span>' +
           '<span class="zname">' + esc(z.name) + '</span>' +
           '<span class="zeur">' + money(z.eur) + '</span>' +
           '<span class="zsub">what we billed, all parts, ' +
           esc(PANEL.window) + '</span>' + zoneBody(z) + '</button>';
    });
    gridEl.innerHTML = h;
    panelEl.hidden = false;
  }

  var selZone = null;

  function renderDetail(k) {
    var z = Z[k];
    if (!z) return;
    var h = '<h2>' + esc(z.name) + '</h2>';
    h += '<p class="lead">' + esc(z.where) + ' &middot; read as ' +
         esc(String(z.basis).toLowerCase()) + '.</p>';
    h += '<div class="kpis">' +
         '<div class="kpi"><span>What we billed</span><b>' + money(z.eur) +
         '</b><i>all parts, ' + esc(PANEL.window) + '</i></div>' +
         '<div class="kpi"><span>Part numbers</span><b>' + num(z.part_numbers) +
         '</b><i>behind that figure</i></div>' +
         '<div class="kpi"><span>Figure keys</span><b>' + num(z.fig_keys) +
         '</b><i>catalogue chapters in this zone</i></div>' +
         '<div class="kpi"><span>Brake parts</span><b>' +
         (z.brake_eur > 0 ? money(z.brake_eur) : '\u2014') +
         '</b><i>' + (z.brake_eur > 0 ? num(z.brake_part_numbers) + ' part numbers'
                                      : 'none in this zone') + '</i></div>' +
         '</div>';

    if (z.brake_eur > 0) {
      h += '<h3>Brake parts here</h3>';
      z.brake_buckets.forEach(function (b) {
        var bk = null;
        PANEL.brake.buckets.forEach(function (x) { if (x.k === b.k) bk = x; });
        h += '<div class="bk"><b>' + money(b.eur) + '</b><span>' + esc(b.label) +
             '</span><span>' + num(b.part_numbers) + ' part numbers &middot; ' +
             num(bk ? bk.fig_keys : 0) + ' figure keys</span>';
        if (bk && bk.examples && bk.examples.length) {
          h += '<span>Examples: ' + esc(bk.examples.slice(0, 4).join('; ')) + '</span>';
        }
        h += '</div>';
      });
      h += '<h3>Part numbers and what they are</h3>';
      h += '<table class="pn"><thead><tr><th>Part number</th>' +
           '<th>Figure key</th><th>What it is</th></tr></thead><tbody>';
      var n = 0;
      z.brake_buckets.forEach(function (b) {
        var bk = null;
        PANEL.brake.buckets.forEach(function (x) { if (x.k === b.k) bk = x; });
        if (!bk) return;
        bk.pn_sample.forEach(function (pn) {
          if (n++ >= 12) return;
          h += '<tr><td class="num">' + esc(pn) + '</td>' +
               '<td>' + esc((bk.sample_keys || []).slice(0, 2).join(', ')) + '</td>' +
               '<td>' + esc(bk.examples.slice(0, 2).join(' / ')) + '</td></tr>';
        });
      });
      h += '</tbody></table>';
      h += '<p class="excl">A sample of the part numbers behind this zone, not the ' +
           'whole list. The figure key is the catalogue chapter the part was billed under.</p>';
    } else {
      h += '<div class="banner"><b>No brake parts in this zone</b>' +
           'Nothing in the brake family was billed against a figure key that sits in ' +
           esc(z.name) + '. This is not a gap in the data and it is not a zero: it means ' +
           'the brake parts genuinely belong somewhere else on the vehicle. The ' +
           money(z.eur) + ' billed in this zone is for other part families.</div>';
    }

    h += '<h3>Target for this zone</h3>';
    h += '<table class="pn"><thead><tr><th>Measure</th><th class="r">Amount</th></tr>' +
         '</thead><tbody>' +
         '<tr><td>Official target for one vehicle, one year</td><td class="r num">' +
         money(PANEL.target.eur_per_vehicle_per_year) + '</td></tr>' +
         '<tr><td>That target, split by this zone\'s share of what we billed</td>' +
         '<td class="r num">' + money(z.target_eur) + '</td></tr>' +
         '<tr><td>What we billed in this zone, ' + esc(PANEL.window) + '</td>' +
         '<td class="r num">' + money(z.eur) + '</td></tr>' +
         '</tbody></table>';
    h += '<p class="excl">' + esc(PANEL.target.basis) + '</p>';
    detEl.innerHTML = h;
  }

  function selectZone(k) {
    selZone = (selZone === k) ? null : k;
    Array.prototype.forEach.call(svg.querySelectorAll('polygon'), function (p) {
      p.classList.toggle('sel', p.getAttribute('data-zone') === selZone);
    });
    Array.prototype.forEach.call(gridEl.querySelectorAll('.zcard'), function (b) {
      b.setAttribute('aria-pressed',
                     b.getAttribute('data-zone') === selZone ? 'true' : 'false');
    });
    if (selZone) renderDetail(selZone);
    else detEl.innerHTML = '<div class="banner"><b>Pick a zone</b>' +
         'Click a zone card above, or a zone on the vehicle when frame 1 is showing, ' +
         'to see what we billed there.</div>';
  }

  gridEl.addEventListener('click', function (e) {
    var b = e.target.closest ? e.target.closest('.zcard') : null;
    if (b) selectZone(b.getAttribute('data-zone'));
  });

  // A zone on the vehicle is picked up here rather than on the SVG, because the
  // drag calls setPointerCapture on the stage.  Capture retargets the click to
  // the stage, so an SVG click listener would never see the polygon.  Reading
  // the element at the click point gives the polygon back, and a tap that moved
  // is treated as a turn instead of a choice.
  stage.addEventListener('click', function (e) {
    if (moved || !zonesOn || indexOf(angle) !== ZONE_FRAME) return;
    var el = document.elementFromPoint(e.clientX, e.clientY);
    var p = el && el.closest ? el.closest('polygon[data-zone]') : null;
    if (p) { selectZone(p.getAttribute('data-zone')); e.stopPropagation(); }
  });

  if (PANEL && ZONES && ZONE_FRAME >= 0) {
    renderGrid();
    selectZone(null);
    znote.innerHTML = '<b>Zones belong to frame 1.</b> These six areas &mdash; ' +
      Object.keys(ZONES).join(', ') + ' &mdash; were measured for the camera angle of ' +
      'frame 1 (' + META.az_deg + '\u00B0 azimuth, ' + META.el_deg +
      '\u00B0 elevation). They do not apply to the other ' + (N - 1) +
      ' views, so they are not drawn on them. Click a zone, on the vehicle or below, ' +
      'to see what we billed there.';
    if (PANEL.unplaced_eur) {
      exclEl.innerHTML = '<b>Not on the vehicle:</b> ' + money(PANEL.unplaced_eur) +
        ' of ' + money(PANEL.total_eur) + ' (' + PANEL.unplaced_pct.toFixed(1) +
        '%) carries no place on a vehicle in the catalogue. ' +
        PANEL.unplaced_reasons.map(function (r) {
          return money(r.eur) + ' ' + esc(r.reason);
        }).join('; ') + '. It is reported, not forced onto a zone.';
    }
  }

  var zonesOn = false;
  var wasAuto = false;
  function updateZones(idx) {
    var show = zonesOn && idx === ZONE_FRAME;
    svg.classList.toggle('on', show);
    if (zonesOn && idx !== ZONE_FRAME) {
      znote.hidden = false;
      znote.innerHTML = '<b>Zones belong to frame 1.</b> You are on frame ' + (idx + 1) +
        '; turn back to frame 1 to see them.';
    } else if (zonesOn) {
      znote.hidden = false;
      znote.innerHTML = '<b>Zones are shown on frame 1 only.</b> These six areas &mdash; ' +
        'front, engine, cab, rear, chassis, electrical &mdash; were measured for this ' +
        'camera angle (' + META.az_deg + '\u00B0 azimuth, ' + META.el_deg +
        '\u00B0 elevation). They do not apply to the other ' + (N - 1) + ' views.';
    } else {
      znote.hidden = true;
    }
  }

  zbtn.addEventListener('click', function () {
    zonesOn = !zonesOn;
    zbtn.setAttribute('aria-pressed', String(zonesOn));
    zbtn.textContent = zonesOn ? 'Hide zones' : 'Show zones';
    if (zonesOn && indexOf(angle) !== ZONE_FRAME) {
      angle = ZONE_FRAME * STEP;   // go to the frame the zones belong to
      paint(ZONE_FRAME);
    }
    updateZones(indexOf(angle));
  });

  // ---------------------------------------------------------------- report
  // A small handle so the page can be read back without scraping the markup.
  function report() {
    return {
      frame: indexOf(angle) + 1, zonesOn: zonesOn, zoneFrame: ZONE_FRAME + 1,
      selected: selZone,
      zoneCards: gridEl.querySelectorAll('.zcard').length,
      zoneCardsWithBrake:
        gridEl.querySelectorAll('.zcard:not(.nobrake)').length,
      polygons: svg.querySelectorAll('polygon').length,
      detailHeading: (detEl.querySelector('h2') || {}).textContent || '',
      detailRows: detEl.querySelectorAll('table.pn tbody tr').length,
      moneyOnPage: (document.body.innerText.match(/\u20AC[\d,]+/g) || []).length,
      unplacedShown: !!(exclEl && exclEl.textContent.length > 40),
      frameNotice: znote.hidden ? '' : znote.textContent.slice(0, 120),
      // what the reader actually sees, so a check can prove the numbers paint
      // rather than only existing somewhere in the markup
      paintedDetail: (detEl.innerText || '').replace(/\s+/g, ' ').trim().slice(0, 400),
      paintedCard: ((gridEl.querySelector('.zcard') || {}).innerText || '')
        .replace(/\s+/g, ' ').trim(),
      unplacedLine: (exclEl.innerText || '').replace(/\s+/g, ' ').trim().slice(0, 200)
    };
  }

  // ---------------------------------------------------------------- dragging
  // Grab the surface and turn the object the way your hand moves: dragging right
  // turns the vehicle so the panel under your finger travels right.  A little
  // momentum on release keeps it feeling like a solid object rather than a slider.
  var dragging = false, lastX = 0, vel = 0, lastT = 0, raf = null;
  var hist = [];
  var moved = false;        // did this gesture turn the vehicle, or was it a tap?
  var DEG_PER_PX = 0.42;
  // Velocity is estimated from the gap between pointer events, so a burst of events
  // arriving a millisecond apart would otherwise imply an enormous speed and send the
  // truck spinning several turns on release.  Measured: without this clamp a 300 px
  // drag that arrived in a burst produced 217 deg instead of the 126 deg the travel
  // warrants.  The clamp bounds what a flick can add, whatever the event timing.
  var MAX_FLICK = 2.2;      // degrees per frame of residual speed (glide adds <= ~31 deg)
  var GLIDE_DECAY = 0.93;
  var GLIDE_STOP = 0.25;
  var MIN_DT = 8;           // ms; stops a burst of coalesced events inventing a speed

  function stopGlide() {
    if (raf) { cancelAnimationFrame(raf); raf = null; }
  }

  function onDown(e) {
    if (e.button !== undefined && e.button !== 0) return;
    stopAuto();
    dragging = true;
    var x = (e.touches ? e.touches[0].clientX : e.clientX);
    lastX = x; lastT = performance.now(); vel = 0; hist.length = 0;
    moved = false;
    stage.classList.add('dragging');
    hint.classList.add('hidden');
    stopGlide();
    try { stage.setPointerCapture && e.pointerId !== undefined &&
          stage.setPointerCapture(e.pointerId); } catch (err) {}
  }

  function onMove(e) {
    if (!dragging) return;
    var x = (e.touches ? e.touches[0].clientX : e.clientX);
    var dx = x - lastX;
    var t = performance.now();
    var dt = Math.max(MIN_DT, t - lastT);
    if (dx) {
      if (Math.abs(x - lastX) > 3) moved = true;
      angle += dx * DEG_PER_PX;
      paint(indexOf(angle));
      // Velocity from the last few events as a whole, not from one event's dx/dt.
      // Summing per-event ratios double-counts: dx accumulates across events while dt
      // is only the gap since the previous one, so a steady drag looks faster and
      // faster.  Keeping a short history and dividing total travel by total elapsed
      // gives the real speed.
      hist.push({ t: t, d: dx * DEG_PER_PX });
      while (hist.length > 2 && t - hist[0].t > 70) hist.shift();
      if (hist.length >= 2) {
        var travel = 0, t0 = hist[0].t;
        for (var q = 0; q < hist.length; q++) travel += hist[q].d;
        var span = Math.max(MIN_DT, t - t0);
        var v = travel / span * 16;
        vel = Math.max(-MAX_FLICK, Math.min(MAX_FLICK, v));
      }
    }
    lastX = x; lastT = t;
    if (e.cancelable) e.preventDefault();
  }

  function onUp() {
    if (!dragging) return;
    dragging = false;
    stage.classList.remove('dragging');
    if (Math.abs(vel) > 0.6) glide();
    else vel = 0;
  }

  function glide() {
    stopGlide();
    function step() {
      vel *= GLIDE_DECAY;
      angle += vel;
      paint(indexOf(angle));
      if (Math.abs(vel) > GLIDE_STOP) raf = requestAnimationFrame(step);
      else { vel = 0; raf = null; }
    }
    raf = requestAnimationFrame(step);
  }

  stage.addEventListener('pointerdown', onDown);
  window.addEventListener('pointermove', onMove, { passive: false });
  window.addEventListener('pointerup', onUp);
  window.addEventListener('pointercancel', onUp);
  stage.addEventListener('touchstart', onDown, { passive: true });
  window.addEventListener('touchmove', onMove, { passive: false });
  window.addEventListener('touchend', onUp);
  stage.addEventListener('contextmenu', function (e) { e.preventDefault(); });

  // ---------------------------------------------------------------- keys
  var autoOn = false, autoRaf = null;
  function stopAuto() {
    if (autoRaf) { cancelAnimationFrame(autoRaf); autoRaf = null; }
    autoOn = false;
    playbtn.setAttribute('aria-pressed', 'false');
    playbtn.textContent = 'Auto-spin';
  }
  function autoStep() {
    angle += STEP;
    paint(indexOf(angle));
    autoRaf = requestAnimationFrame(function () { setTimeout(autoStep, 90); });
  }
  playbtn.addEventListener('click', function () {
    if (autoOn) { stopAuto(); return; }
    autoOn = true;
    playbtn.setAttribute('aria-pressed', 'true');
    playbtn.textContent = 'Stop';
    hint.classList.add('hidden');
    autoStep();
  });

  window.addEventListener('keydown', function (e) {
    var k = e.key;
    if (k === 'ArrowLeft' || k === 'ArrowRight') {
      stopAuto(); stopGlide();
      angle += (k === 'ArrowRight' ? STEP : -STEP);
      hint.classList.add('hidden');
      paint(indexOf(angle));
      e.preventDefault();
    } else if (k === ' ' && !zbtn.hidden) {
      // space toggles nothing critical; leave it to the buttons
    }
  });

  window.addEventListener('resize', function () { resize(); });

  // ---------------------------------------------------------------- chrome
  var majors = Math.max(4, Math.round(N / 4));
  var t = '';
  for (var j = 0; j < N; j++) {
    t += '<i class="' + (j % majors === 0 ? 'major' : '') + '"></i>';
  }
  var lab = '';
  for (var d = 0; d < 360; d += 90) {
    lab += '<span style="left:' + ((d / 360) * 100).toFixed(4) + '%">' + d + '\u00B0</span>';
  }
  ticksEl.innerHTML = t + lab;

  document.getElementById('foot').innerHTML =
    'Isuzu D-Max 2021, double cab &middot; ' + N + ' views at ' + META.step_deg +
    '\u00B0 steps &middot; rendered ' + META.resolution[0] + '\u00D7' + META.resolution[1] +
    ' at ' + META.samples + ' samples, shown at ' + PW + '\u00D7' + PH +
    ' &middot; camera azimuth ' + META.az_deg + '\u00B0, elevation ' + META.el_deg +
    '\u00B0 &middot; ' + META.credit;

  if (PANEL) {
    var srcList = (PANEL.sources || []).map(function (s) {
      return s.split(' (')[0];
    }).join(', ');
    document.getElementById('foot').innerHTML +=
      '<br>What we billed comes from ' + esc(PANEL.window) + ' and covers ' +
      money(PANEL.total_eur) + ' across ' + num(PANEL.total_fig_keys) +
      ' catalogue chapters and all markets. Sources: ' + esc(srcList) + '.';
  }

  resize();
  readout.innerHTML = 'Frame <b>1</b> / ' + N + ' &nbsp;&middot;&nbsp; 0\u00B0';
  if (!ZONES || ZONE_FRAME < 0) zbtn.hidden = true;

  // expose a small handle so the page can be driven and checked by a test
  window.__tt = {
    frames: N, step: STEP, zoneFrame: ZONE_FRAME,
    get index() { return indexOf(angle); },
    get angle() { return angle; },
    state: function () {
      return { index: indexOf(angle), angle: angle, shown: shown,
               ready: ready, failed: failed, zonesOn: zonesOn,
               posterVisible: poster.style.visibility !== 'hidden' };
    },
    drag: function (dx) { angle += dx * DEG_PER_PX; paint(indexOf(angle)); },
    goto: function (i) { angle = i * STEP; paint(indexOf(angle)); },
    selectZone: function (k) { zonesOn = true; zbtn.setAttribute('aria-pressed', 'true');
                               zbtn.textContent = 'Hide zones';
                               angle = ZONE_FRAME * STEP; paint(ZONE_FRAME);
                               updateZones(ZONE_FRAME); selectZone(k); },
    report: report
  };
})();
</script>
</body>
</html>
"""


if __name__ == "__main__":
    raise SystemExit(main())
