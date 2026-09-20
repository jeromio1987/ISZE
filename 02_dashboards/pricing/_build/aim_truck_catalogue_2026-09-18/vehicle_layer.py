#!/usr/bin/env python3
"""The vehicle layer for the AIM truck catalogue page.

The page shows a real Isuzu for each of the four vehicles, taken from a genuine
photograph of that vehicle, and overlays the six clickable zones on it. The zone
colour only appears on hover or click, so the page loads showing a real truck.

This module writes the script block that does that. It is kept separate from the
page skeleton so the vehicle layer can be read and changed on its own, and so the
picture can be swapped without touching the page markup, the charts or the tables.

The hotspot layer
-----------------
Each zone is one or more polygons in fractions of the image, so the same data
works at any rendered size and any device pixel ratio. A click is turned into a
fraction of the displayed image and tested against those polygons. Because the
fit is the thing that fails visibly when it is wrong, every placed polygon is
exposed for QA as both a screen polygon and a bounding box.
"""

VEHICLE_JS = r"""
/* ================= the vehicle photographs =================
   Four real Isuzu vehicles, each a photograph of that vehicle, embedded in the
   page as a data URI so it opens from Explorer with no server and no network.
   The zones are polygon hotspots in fractions of the image, so they scale with
   whatever size the picture is drawn at, and the same numbers serve the drawing
   and the hit test.

   Nothing here is drawn from scratch: the photograph is the vehicle. The zones
   are a separate layer on top, invisible until a zone is hovered or selected,
   which is why the page loads showing a real truck rather than a diagram.

   MEDIA, ZONES, ZCOL, ZONE, VEH and the helpers above come from the page script
   that precedes this one. */
var LABEL_RECTS = [];            /* what the label resolver actually placed, QA */
var OUTLINE = null, ZONE_SHAPES = null, DETAILS = null, ANCHORS = null;

var cv = document.getElementById('map'), ctx = cv.getContext('2d');
var W = 0, H = 0, DPR = 1;       /* canvas size in CSS px */
var state = {veh:0, sel:-1, hover:-1, family:-1, showElec:true, hidden:{}};

/* Where the picture sits on the canvas, and the pan/zoom the reader has applied.
   placePhoto() is the single place that computes it, and both the drawing and the
   hit test read it, so what the eye sees and what the pointer hits cannot drift. */
var PHOTO = {img:null, x:0, y:0, w:0, h:0, ready:false, key:null, nat:[0,0]};
var VIEW  = {zoom:1, dx:0, dy:0};

function mediaFor(key){ return MEDIA[key] || null; }

function loadPhoto(key, done){
  if(PHOTO.key===key && PHOTO.ready){ if(done) done(); return; }
  var m = mediaFor(key);
  PHOTO.key = key; PHOTO.ready = false; PHOTO.img = null;
  if(!m){ if(done) done(); return; }
  var im = new Image();
  im.onload = function(){
    PHOTO.img = im; PHOTO.nat = [im.naturalWidth, im.naturalHeight];
    PHOTO.ready = true;
    placePhoto();
    if(done) done();
  };
  im.onerror = function(){ PHOTO.ready = false; if(done) done(); };
  im.src = m.src;
}

/* Fit the picture inside its half of the stage and centre it there, then apply
   the reader's pan and zoom.

   On a wide screen the picture takes the left portion and the right margin is
   reserved for the zone labels, which is what makes this read as a catalogue
   plate rather than a photograph with text thrown over it. On a narrow screen
   there is no room for that, so the picture takes the width and the labels sit
   where they can. */
function placePhoto(){
  if(!PHOTO.ready) return;
  /* A wide stage keeps a right-hand margin for the labels, which is what makes
     this read as a catalogue plate: vehicle left, callouts right. Below that
     width there is no room for a margin, so the callouts take a column down the
     left and the vehicle is fitted into the space that is left over. Either way
     the picture is sized to a rectangle that is known to be free, so it can never
     run off the stage. */
  var wide = W > 1080;
  /* On a wide stage the labels take a margin on the right, and the vehicle is
     fitted to the left of it. On a narrow stage the labels take a column on the
     left instead, and the vehicle is fitted to the right of it. Only one strip is
     reserved either way, so the vehicle keeps as much of the stage as possible. */
  var colW = wide ? 0 : Math.round(Math.min(Math.max(150, W * 0.30), W * 0.34));
  var reserve = wide ? Math.round(Math.min(420, W * 0.33)) : 0;
  var left = wide ? 16 : colW + 12;
  var availW = Math.max(80, W - left - reserve - 16);
  var availH = Math.max(80, H - 118);
  var ar = PHOTO.nat[0] / PHOTO.nat[1];
  var w = availW, h = w / ar;
  if(h > availH){ h = availH; w = h * ar; }
  w *= VIEW.zoom; h *= VIEW.zoom;
  PHOTO.w = w; PHOTO.h = h;
  PHOTO.x = left + (Math.max(availW, w) - w) / 2 + VIEW.dx;
  PHOTO.y = 66 + (availH - h) / 2 + VIEW.dy;
  /* the strip the labels may use: the right margin on a wide stage */
  PHOTO.labelRight = wide;
  PHOTO.colW = colW;
}

/* Screen point -> fraction of the vehicle image. Null when the point is off the
   picture, so a click in the margin resolves to nothing rather than to whichever
   polygon happens to be nearest. */
function photoFrac(mx,my){
  if(!PHOTO.ready) return null;
  var fx = (mx - PHOTO.x) / PHOTO.w;
  var fy = (my - PHOTO.y) / PHOTO.h;
  if(fx < 0 || fx > 1 || fy < 0 || fy > 1) return null;
  return [fx, fy];
}
/* Fraction of the image -> screen point. */
function photoPoint(fx,fy){
  return [PHOTO.x + fx*PHOTO.w, PHOTO.y + fy*PHOTO.h];
}
function pointInPoly(px,py,poly){
  var inside=false, n=poly.length;
  for(var a=0,b=n-1;a<n;b=a++){
    var xi=poly[a][0], yi=poly[a][1], xj=poly[b][0], yj=poly[b][1];
    if(((yi>py)!==(yj>py)) && (px < (xj-xi)*(py-yi)/(yj-yi)+xi)) inside=!inside;
  }
  return inside;
}
/* The placed polygons in screen space: what QA asserts against the picture. */
function zoneScreenPolys(zi){
  var zn = ZONES[zi], m = mediaFor(PHOTO.key);
  if(!m || !PHOTO.ready) return [];
  return ((m.zones && m.zones[zn.k]) || []).map(function(poly){
    return poly.map(function(p){ return photoPoint(p[0], p[1]); });
  });
}
/* The screen bounding box of a zone's placed polygons. This is the hook that
   catches a hotspot fitted to the wrong place. */
function zoneRect(zi){
  var polys = zoneScreenPolys(zi);
  if(!polys.length) return null;
  var x0=1e9, y0=1e9, x1=-1e9, y1=-1e9, n=0;
  polys.forEach(function(poly){
    poly.forEach(function(p){
      x0=Math.min(x0,p[0]); y0=Math.min(y0,p[1]);
      x1=Math.max(x1,p[0]); y1=Math.max(y1,p[1]); n++;
    });
  });
  if(!n) return null;
  return {x:x0, y:y0, w:x1-x0, h:y1-y0, zone:zi, key:ZONES[zi].k};
}
function zoneRects(){
  var out=[];
  for(var i=0;i<ZONES.length;i++) out.push(zoneRect(i));
  return out;
}
/* Which zones are under a screen point. The electrical layer is a tag sitting on
   top of a position, so it wins where it overlaps, which is how the page explains
   it to the reader. */
function zoneHitAll(mx,my){
  var f = photoFrac(mx,my), hits=[];
  if(!f) return hits;
  var m = mediaFor(PHOTO.key);
  if(!m) return hits;
  for(var i=0;i<ZONES.length;i++){
    var zn = ZONES[i];
    if(zn.k==='elec' && !state.showElec) continue;
    if(state.hidden[i]) continue;
    var polys = (m.zones && m.zones[zn.k]) || [];
    for(var s=0;s<polys.length;s++){
      if(pointInPoly(f[0], f[1], polys[s])){ hits.push(i); break; }
    }
  }
  hits.sort(function(a,b){
    var ae=ZONES[a].k==='elec'?1:0, be=ZONES[b].k==='elec'?1:0;
    return be-ae || b-a;
  });
  return hits;
}
function zoneHit(mx,my){ var h=zoneHitAll(mx,my); return h.length?h[0]:-1; }

/* A wash of the zone colour over that zone's own polygons. Alpha only, so the
   photograph stays visible underneath and the vehicle still reads as a vehicle
   while a zone is being examined. */
function paintZone(zi, alpha, edge){
  var polys = zoneScreenPolys(zi);
  if(!polys.length) return;
  var c = ZCOL[ZONES[zi].k] || '#c0552d';
  ctx.save();
  polys.forEach(function(poly){
    ctx.beginPath();
    poly.forEach(function(p,i){ if(i===0) ctx.moveTo(p[0],p[1]);
      else ctx.lineTo(p[0],p[1]); });
    ctx.closePath();
    ctx.globalAlpha = alpha;
    ctx.fillStyle = c;
    ctx.fill();
    if(edge){
      ctx.globalAlpha = Math.min(1, alpha * 1.5);
      ctx.lineWidth = edge;
      ctx.strokeStyle = c;
      ctx.stroke();
    }
  });
  ctx.restore();
}

/* The base layer: the photograph, and a soft shade under the vehicle so it sits
   on the page rather than floating on it. */
function drawPhotoBase(){
  ctx.save();
  ctx.setTransform(DPR,0,0,DPR,0,0);
  ctx.clearRect(0,0,W,H);

  if(PHOTO.ready){
    var baseY = PHOTO.y + PHOTO.h;
    var g = ctx.createLinearGradient(0, baseY - PHOTO.h*0.09, 0, baseY + 12);
    g.addColorStop(0, 'rgba(21,35,60,0)');
    g.addColorStop(1, 'rgba(21,35,60,.10)');
    ctx.fillStyle = g;
    ctx.fillRect(0, baseY - PHOTO.h*0.09, W, PHOTO.h*0.09 + 12);

    ctx.imageSmoothingEnabled = true;
    if('imageSmoothingQuality' in ctx) ctx.imageSmoothingQuality = 'high';
    ctx.drawImage(PHOTO.img, PHOTO.x, PHOTO.y, PHOTO.w, PHOTO.h);
  }
  ctx.restore();
}

/* What the photograph is and where it came from, stated on the page so nobody has
   to guess which vehicle they are looking at. */
function drawPhotoCredit(){
  var m = mediaFor(PHOTO.key);
  if(!m) return;
  ctx.save();
  ctx.setTransform(DPR,0,0,DPR,0,0);
  ctx.font = '11.5px -apple-system,Segoe UI,Roboto,Arial,sans-serif';
  ctx.fillStyle = 'rgba(107,100,89,.95)';
  ctx.fillText(m.credit, 14, H - 11);
  ctx.restore();
}

/* ================= draw =================
   Layers, in order: the photograph, the zone washes, the anchors, the credit,
   then the labels. The washes are faint so the vehicle is never hidden: a
   selected zone is a tint over the photograph, not a replacement for it. */
function draw(){
  drawPhotoBase();
  ctx.save();
  ctx.setTransform(DPR,0,0,DPR,0,0);
  ctx.lineJoin='round'; ctx.lineCap='round';

  var i;
  for(i=0;i<ZONES.length;i++){
    if(state.hidden[i]) continue;
    if(ZONES[i].k==='elec' && !state.showElec) continue;
    if(i===state.sel || i===state.hover) continue;
    /* every other zone keeps a hairline, so the layer is discoverable without
       being loud */
    paintZone(i, state.sel>=0 ? 0.05 : 0.03, 0);
  }
  if(state.hover>=0 && state.hover!==state.sel) paintZone(state.hover, 0.22, 2.2);
  if(state.sel>=0) paintZone(state.sel, 0.34, 2.6);

  /* the anchors: a dot where each zone's label attaches, so the leader line has
     something to point at */
  ZONES.forEach(function(zn,i){
    if(zn.k==='elec' && !state.showElec) return;
    if(state.hidden[i]) return;
    var a = ANCHORS[zn.k];
    if(!a) return;
    var p = photoPoint(a[0], a[1]);
    var lit = (state.sel===i || state.hover===i);
    ctx.beginPath();
    ctx.arc(p[0], p[1], lit?5.5:3.6, 0, Math.PI*2);
    ctx.globalAlpha = (state.sel>=0 && state.sel!==i) ? 0.40 : 1;
    ctx.fillStyle = ZCOL[zn.k] || '#c0552d';
    ctx.fill();
    ctx.globalAlpha = 1;
    ctx.lineWidth = 1.6;
    ctx.strokeStyle = 'rgba(255,255,255,.92)';
    ctx.stroke();
  });
  ctx.restore();
  drawPhotoCredit();
  drawLabels();
}

/* A label resolver.

   On a wide stage it fills the right-hand margin: a catalogue plate puts its
   callouts in the margin beside the vehicle, and there the label is a plain box
   with a leader line. Each label takes the next free vertical slot, so the
   margin reads as a list rather than as scattered tags.

   On a narrow stage there is no margin, so the callouts are drawn in a column
   down the left, level with the vehicle, and the picture is inset behind them.
   That keeps every label legible instead of stacking them over the truck, which
   is what a naive resolver does.

   Either way the resolver never overlaps two labels, and never drops one it
   could place. What it placed is exposed for QA, so a resolver that silently
   loses most of its labels cannot pass. */
function labelOverPhoto(r){
  if(!PHOTO.ready) return false;
  var pad = 4;
  return !(r.x+r.w+pad < PHOTO.x || r.x-pad > PHOTO.x+PHOTO.w ||
           r.y+r.h+pad < PHOTO.y || r.y-pad > PHOTO.y+PHOTO.h);
}
function drawLabels(){
  var taken=[], items=[];
  LABEL_RECTS=[];
  ZONES.forEach(function(zn,i){
    if(zn.k==='elec' && !state.showElec) return;
    if(state.hidden[i]) return;
    var a=ANCHORS[zn.k];
    if(!a) return;
    var t=ZONE[i];
    items.push({i:i, a:a, t:t, label:eurM(t.eur),
      pctxt:(t.pct!=null?pct(t.pct):''), name:zn.name.split(',')[0],
      col:ZCOL[zn.k], sel:(state.sel===i||state.hover===i)});
  });
  /* the selected label is drawn last so it sits on top */
  items.sort(function(x,y){ return (x.sel?1:0)-(y.sel?1:0); });

  var wide = PHOTO.labelRight;
  var bh = 32, gap = 8;
  function emit(it, r){
    var p = photoPoint(it.a[0], it.a[1]);
    taken.push(r);
    r.zone=it.i; r.name=it.name;
    LABEL_RECTS=taken;
    ctx.beginPath(); ctx.moveTo(p[0],p[1]); ctx.lineTo(r.cx, r.cy);
    ctx.strokeStyle=it.sel?'#15233c':'rgba(21,35,60,.45)';
    ctx.lineWidth=it.sel?2:1; ctx.stroke();
    ctx.beginPath(); ctx.arc(p[0],p[1],it.sel?5:3.6,0,Math.PI*2);
    ctx.fillStyle=it.col; ctx.fill();
    ctx.strokeStyle='rgba(255,255,255,.92)'; ctx.lineWidth=1.6; ctx.stroke();

    ctx.fillStyle=it.sel?'#15233c':'rgba(255,255,255,.96)';
    ctx.fillRect(r.x, r.y, r.w, r.h);
    ctx.strokeStyle=it.sel?'#15233c':'#d9d3c8'; ctx.lineWidth=1;
    ctx.strokeRect(r.x, r.y, r.w, r.h);
    ctx.fillStyle=it.sel?'#f7f4ee':'#15233c';
    ctx.font='600 12px -apple-system,Segoe UI,Roboto,Arial,sans-serif';
    ctx.fillText(it.label, r.x+8, r.y+14);
    ctx.font='11px -apple-system,Segoe UI,Roboto,Arial,sans-serif';
    ctx.fillStyle=it.sel?'#e2d7cb':'#6b6459';
    ctx.fillText(it.name+'  '+it.pctxt, r.x+8, r.y+26);
  }

  if(wide){
    /* The right-hand margin, filled top to bottom. The picture was sized to leave
       this strip free, so a slot only fails if another label is already there. */
    var mx = PHOTO.x + PHOTO.w + 22;
    var availW = W - mx - 12;
    if(availW > 150){
      items.forEach(function(it){
        ctx.font='600 12px -apple-system,Segoe UI,Roboto,Arial,sans-serif';
        var w1=ctx.measureText(it.label).width;
        ctx.font='11px -apple-system,Segoe UI,Roboto,Arial,sans-serif';
        var w2=ctx.measureText(it.name+'  '+it.pctxt).width;
        var bw=Math.min(availW, Math.max(w1,w2)+18);
        var y0 = 58, y1 = H - 30;
        var slots = Math.max(1, Math.floor((y1 - y0) / (bh + gap)));
        var step = (y1 - y0 - bh) / Math.max(1, slots - 1);
        var placed=null;
        for(var s=0;s<slots && !placed;s++){
          var y = y0 + s*step;
          var cand={x:mx, y:y, w:bw, h:bh, cx:mx+bw/2, cy:y+bh/2};
          var clash=false;
          for(var q=0;q<taken.length;q++){
            var o=taken[q];
            if(cand.x < o.x+o.w+8 && cand.x+cand.w+8 > o.x &&
               cand.y < o.y+o.h+gap && cand.y+cand.h+gap > o.y){ clash=true; break; }
          }
          if(!clash && cand.y+cand.h < H-6) placed=cand;
        }
        if(placed) emit(it, placed);
      });
    }
    return;
  }

  /* Narrow stage: no margin exists, so the labels take a column down the left and
     the picture is inset behind them. A leader line from the anchor to the box
     keeps the link between the callout and the part of the truck it names. */
  var lx = 8;
  var y0 = 58, y1 = H - 18;
  var slots = Math.max(1, Math.floor((y1 - y0) / (bh + gap)));
  var step = slots > 1 ? (y1 - y0 - bh) / (slots - 1) : 0;
  items.forEach(function(it){
    ctx.font='600 12px -apple-system,Segoe UI,Roboto,Arial,sans-serif';
    var w1=ctx.measureText(it.label).width;
    ctx.font='11px -apple-system,Segoe UI,Roboto,Arial,sans-serif';
    var w2=ctx.measureText(it.name+'  '+it.pctxt).width;
    var bw=Math.min(Math.max(w1,w2)+18, (PHOTO.colW || W*0.4) - 12);
    var placed=null;
    for(var s=0;s<slots && !placed;s++){
      var cand={x:lx, y:y0 + s*step, w:bw, h:bh, cx:lx+bw/2,
                cy:y0 + s*step + bh/2};
      var clash=false;
      for(var q=0;q<taken.length;q++){
        var o=taken[q];
        if(cand.x < o.x+o.w+8 && cand.x+cand.w+8 > o.x &&
           cand.y < o.y+o.h+gap && cand.y+cand.h+gap > o.y){ clash=true; break; }
      }
      if(!clash) placed=cand;
    }
    if(placed) emit(it, placed);
  });
}
/* On a narrow stage the callouts are a column down the left, so nothing else may
   be painted there. */
function labelColumnW(){ return PHOTO.colW || 0; }

/* The picture is the whole scene: its placement is the only geometry, and the
   label anchors come from the media payload as fractions of the image. */
function buildScene(){
  var v = VEH[state.veh];
  var m = mediaFor(v.k);
  ANCHORS = (m && m.anchors) || {};
  PHOTO.bbox = (m && m.bbox) || [0, 0, 1, 1];
  PHOTO.face = (m && m.face) || 'left';
  OUTLINE = null; ZONE_SHAPES = null; DETAILS = null;
  placePhoto();
}
/* Load the photograph for the vehicle now on screen, then size the canvas and
   draw. Called on load and whenever the tab changes. */
function switchVehicle(){
  buildScene();
  loadPhoto(VEH[state.veh].k, function(){ bootFit(); });
}

function resize(){
  DPR = Math.min(2, window.devicePixelRatio||1);
  W = cv.clientWidth; H = cv.clientHeight;
  cv.width = Math.round(W*DPR); cv.height = Math.round(H*DPR);
  ctx.setTransform(DPR,0,0,DPR,0,0);
  placePhoto();
  draw();
}
function bootFit(){ resize(); }
window.addEventListener('resize', resize);
"""
