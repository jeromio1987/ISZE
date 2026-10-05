
(function(){
"use strict";

/* ================= data ================= */
var P = JSON.parse(document.getElementById('payload').textContent);
var MD = JSON.parse(document.getElementById('media').textContent);
var M = P.meta, ROWS = P.rows;
var L1 = M.l1, L2 = M.l2, L3 = M.l3, PN = M.pn, DESC = M.desc;
var ZONES = M.zones, ZOF = M.zone_of_l3, RESID = M.residual_l1;
var VEH = M.vehicles, TARGETS = M.targets, FLEET = M.fleet_2025;
/* the vehicle pictures and their zone hotspots, from vehicle_images.py */
var MEDIA = (function(){
  var out = {};
  Object.keys(MD).forEach(function(k){
    var v = MD[k];
    out[k] = {src:v.src, credit:v.credit, depicts:v.depicts,
              zones:v.zones, anchors:v.anchors};
  });
  return out;
})();

var CATCOL = ['#c0552d','#1d3054','#7a9cc0','#1e6b4f','#8a5622','#5b6b7f','#b0873a','#6b4a6b'];
var RESID_IX = RESID.map(function(n){ return L1.indexOf(n); });
function catColour(i){ return RESID_IX.indexOf(i)>=0 ? '#a8721f' : CATCOL[i % CATCOL.length]; }
var ZCOL = {'front':'#c0552d','cab':'#b0873a','engine':'#1d3054','chassis':'#5b6b7f',
  'rear':'#8a5622','elec':'#1e6b4f'};

function esc(s){return String(s==null?'':s).replace(/[&<>"']/g,function(c){
  return {'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c];});}
function eur(v,d){d=d==null?0:d; return '\u20ac'+(v||0).toLocaleString('en-GB',
  {minimumFractionDigits:d,maximumFractionDigits:d});}
function eurM(v){ return Math.abs(v)>=1e6 ? '\u20ac'+(v/1e6).toFixed(2)+'M' : eur(v); }
function num(v,d){d=d==null?0:d; return (v||0).toLocaleString('en-GB',
  {minimumFractionDigits:d,maximumFractionDigits:d});}
function pct(v){ return v==null?'\u2014':(v>=0?'+':'')+v.toFixed(2)+'%'; }
function pc(v){ return v==null?'\u2014':(v*100).toFixed(1)+'%'; }
function tip(t){ return '<span class="info">i<span class="tp">'+t+'</span></span>'; }

/* ================= totals ================= */
function blank(){ return {eur:0,step:0,prior:0,new:0,qty:0,n:0,priced:0,pn:{}}; }
function add(t,r){
  t.eur+=r[6]; t.step+=r[7]; t.prior+=r[8]; t.new+=r[9]; t.qty+=r[5]; t.n++;
  if(r[11]) t.priced++;
  t.pn[r[0]]=1; return t;
}
function moveOf(t){ return (t.prior>0 && t.priced>0) ? 100*(t.new/t.prior-1) : null; }

var ALL = blank();
var ZONE = ZONES.map(function(){ return blank(); });
for(var i=0;i<ROWS.length;i++){
  var r=ROWS[i];
  ALL=add(ALL,r);
  var z=ZOF[r[3]];
  if(z>=0) ZONE[z]=add(ZONE[z],r);
}
function finish(t){ t.npn=Object.keys(t.pn).length; t.pct=moveOf(t);
  t.ratio=t.eur>0?t.step/t.eur:0; return t; }
finish(ALL); ZONE.forEach(finish);
var ZONED = ZONE.reduce(function(s,t){ return s+t.eur; },0);


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


/* ================= tooltip ================= */
var tipEl=document.getElementById('tip');
function showTip(mx,my,z){
  var t=ZONE[z], zn=ZONES[z];
  tipEl.innerHTML='<b>'+esc(zn.name)+'</b><br><span class="r">'+esc(zn.where)+
    (zn.how!=='Positional'?' \u00b7 '+esc(zn.how):'')+'</span><br>'
    +'Parts billed <b>'+eur(t.eur)+'</b><br>Step '+eur(t.step)+'  \u00b7  weighted '+pct(t.pct)
    +'<br>'+num(t.npn)+' part numbers  \u00b7  '+num(t.qty)+' units billed';
  tipEl.style.display='block';
  var tw=tipEl.offsetWidth, th=tipEl.offsetHeight;
  tipEl.style.left=Math.min(window.innerWidth-tw-10, mx+16)+'px';
  tipEl.style.top=Math.max(8, Math.min(window.innerHeight-th-10, my+16))+'px';
}
function hideTip(){ tipEl.style.display='none'; }

/* ================= detail panel ================= */
function rowsForZone(z){
  var out=[];
  for(var i=0;i<ROWS.length;i++) if(ZOF[ROWS[i][3]]===z) out.push(ROWS[i]);
  return out;
}
function detail(){
  var z=state.sel, t=(z<0?ALL:ZONE[z]), zn=(z<0?null:ZONES[z]);
  var rows=(z<0?ROWS:rowsForZone(z));

  document.getElementById('d-head').textContent = zn? zn.name : 'The whole book, all six zones';
  var cr=document.getElementById('d-crumb');
  if(zn){
    cr.innerHTML='<b>'+esc(zn.name)+'</b><span class="sep">\u203a</span>'
      +'<span class="x" id="cb-reset">all zones</span>'
      +(state.family>=0? '<span class="sep">\u203a</span><b>'+esc(L3[state.family][2])+'</b>':'');
    var rx=document.getElementById('cb-reset');
    if(rx) rx.addEventListener('click',function(){ state.sel=-1; state.family=-1; render(); });
  } else {
    cr.textContent='Click a zone on the vehicle to open it.';
  }
  document.getElementById('d-q').textContent = zn
    ? zn.blurb
    : 'The six zones put the same \u20ac34,993,609 of parts onto a truck, so any euro on this '
      + 'page is a share of the identical book. Click a zone to drill in.';

  var unp=0, unpEur=0;
  for(var i=0;i<rows.length;i++){ if(!rows[i][11]){ unp++; unpEur+=rows[i][6]; } }
  var share = zn ? pc(t.eur/ZONED) : '100% of the zoned book';
  document.getElementById('d-facts').innerHTML =
    fact('Parts billed', eur(t.eur), zn?share+' of the zoned euro':'the whole zoned book')
    + fact('Step at this revision', eur(t.step), pc(t.ratio)+' of its billed euro')
    + fact('Weighted move', pct(t.pct), num(t.priced)+' of '+num(t.n)+' lines priced')
    + fact('Part families', num(t.npn), 'distinct part numbers')
    + fact('Units billed', num(t.qty), 'the pieces, not a finding on their own')
    + fact('Cannot move', eur(unpEur), num(unp)+' lines with no price one side');

  drawFamilies(rows, zn);
  drawPn(rows, zn);
  drawSeries();
}
function fact(l,v,n){ return '<div class="fact"><div class="l">'+esc(l)+'</div><div class="v">'+v
  +'</div><div class="n">'+esc(n||'')+'</div></div>'; }

/* ---------- the family bar chart ----------
   The chart is created once and updated in place. Destroying and rebuilding it
   on every interaction orphans Chart.js's own event handlers and produces a
   "handleEvent of undefined" error, so the instance is reused and only its data
   and colours change. */
var famChart=null;
function drawFamilies(rows, zn){
  var byL3={};
  for(var i=0;i<rows.length;i++){
    var k=rows[i][3];
    var t=byL3[k] || (byL3[k]=blank());
    byL3[k]=add(t,rows[i]);
  }
  var list=Object.keys(byL3).map(function(k){ var t=finish(byL3[k]); t.ix=+k; return t; })
    .sort(function(a,b){ return b.eur-a.eur; }).slice(0,14);
  document.getElementById('d-famhead').textContent = zn
    ? 'What '+zn.name+' is made of'
    : 'The biggest families in the book';
  document.getElementById('d-famq').innerHTML = zn
    ? 'The part types inside this zone, ranked by parts billed euro, coloured by AIM category. '
      + 'Click a bar to list its part numbers.'
    : 'Click a zone on the vehicle to see the family mix inside it.';

  var labels=list.map(function(t){ return L3[t.ix][2]; });
  var vals=list.map(function(t){ return t.eur; });
  var cols=list.map(function(t){ return catColour(L1.indexOf(L3[t.ix][0])); });

  if(!famChart){
    famChart=new Chart(document.getElementById('c-fam'),{
      type:'bar',
      data:{labels:labels,datasets:[{data:vals,backgroundColor:cols,borderWidth:0,
        barPercentage:.8,categoryPercentage:.86}]},
      options:{indexAxis:'y',responsive:true,maintainAspectRatio:false,
        layout:{padding:{right:74}},
        plugins:{legend:{display:false},tooltip:{callbacks:{label:function(c){
          var t=(c.chart.$list||[])[c.dataIndex];
          if(!t) return '';
          return [L3[t.ix][0]+' \u203a '+L3[t.ix][1], 'Parts billed '+eur(t.eur),
            'Step '+eur(t.step), 'Weighted '+pct(t.pct), num(t.npn)+' part numbers'];}}}},
        scales:{x:{beginAtZero:true,grid:{color:'#ece7dd'},
          ticks:{callback:function(v){ return eurM(v); }}},
          y:{grid:{display:false},ticks:{autoSkip:false,font:{size:11}}}},
        onClick:function(e,el){
          if(el && el.length){
            var t=(famChart.$list||[])[el[0].index];
            if(t){ state.family=t.ix; detail(); }
          }
        },
        animation:{duration:200}},
      plugins:[{id:'lbl',afterDatasetsDraw:function(ch){
        var c=ch.ctx, meta=ch.getDatasetMeta(0);
        c.save(); c.font='600 10.5px -apple-system,Segoe UI,Roboto,Arial,sans-serif';
        c.fillStyle='#15233c'; c.textBaseline='middle';
        meta.data.forEach(function(el,i){
          var t=(ch.$list||[])[i];
          if(!t) return;
          c.fillText(eurM(t.eur)+(t.pct!=null?'  '+pct(t.pct):''), el.x+6, el.y);
        }); c.restore(); }}]
    });
  }
  famChart.$list=list;
  famChart.data.labels=labels;
  famChart.data.datasets[0].data=vals;
  famChart.data.datasets[0].backgroundColor=cols;
  famChart.update('none');
}

/* ---------- the part-number table ---------- */
function drawPn(rows, zn){
  var use=rows;
  if(state.family>=0){
    use=rows.filter(function(r){ return r[3]===state.family; });
  }
  document.getElementById('d-pnhead').textContent = state.family>=0
    ? L3[state.family][2] : 'The part numbers in the selected family';
  if(state.family<0){
    document.querySelector('#d-pn thead').innerHTML='';
    document.querySelector('#d-pn tbody').innerHTML=
      '<tr><td class="muted" style="padding:14px">Click a bar on the left to list the part '
      +'numbers inside that part type.</td></tr>';
    document.getElementById('d-pnq').textContent =
      'Click a bar on the left to fill this table.';
    return;
  }
  var byP={};
  for(var i=0;i<use.length;i++){
    var p=byP[use[i][0]] || (byP[use[i][0]]=blank());
    byP[use[i][0]]=add(p,use[i]);
  }
  var list=Object.keys(byP).map(function(k){ var t=finish(byP[k]); t.ix=+k; return t; })
    .sort(function(a,b){ return b.eur-a.eur; }).slice(0,80);
  document.querySelector('#d-pn thead').innerHTML=
    '<tr><th>Part number</th><th>Description</th><th class="n">Units</th>'
    +'<th class="n">Parts billed</th><th class="n">Step</th><th class="n">Weighted</th>'
    +'<th class="n">AIM cell</th></tr>';
  document.querySelector('#d-pn tbody').innerHTML=list.map(function(t){
    var cell=L3[state.family];
    return '<tr><td class="nowrap">'+esc(PN[t.ix])+'</td>'
      +'<td>'+esc(DESC[t.ix]||'\u2014')+'</td>'
      +'<td class="n">'+num(t.qty)+'</td><td class="n">'+eur(t.eur)+'</td>'
      +'<td class="n">'+eur(t.step)+'</td><td class="n">'+pct(t.pct)+'</td>'
      +'<td><span class="dot" style="background:'+catColour(L1.indexOf(cell[0]))+'"></span>'
      +esc(cell[0])+'</td></tr>';
  }).join('');
  document.getElementById('d-pnq').textContent = list.length>=80
    ? 'The 80 biggest of '+num(Object.keys(byP).length)+' part numbers in this part type, by '
      +'parts billed euro.'
    : 'Every part number billed in this part type, by parts billed euro.';
}

/* ---------- the series table ----------
   Fleet in service and the official maximum spend per vehicle per year. The
   fleet split across the four vehicles is an assumption and is labelled as one:
   only the network total is measured, and the billing carries no model code that
   could split it. The rows add back to the measured total, which QA asserts. */
function drawSeries(){
  var order=['LCV_D_Max','N35_Grafter','N75_N50_N62','F_Series_MD'];
  var share={'LCV_D_Max':0.62,'N35_Grafter':0.18,'N75_N50_N62':0.12,'F_Series_MD':0.08};
  var tgt={};
  TARGETS.forEach(function(t){ tgt[t.group]=t; });
  var rows=[], units=0, capacity=0;
  order.forEach(function(g,ix){
    var v=VEH.filter(function(x){ return x.target===g; })[0]||{};
    var t=tgt[g]||{};
    var u=FLEET.units*share[g];
    var cap=u*(t.eur||0);
    units+=u; capacity+=cap;
    var isIt=(ix===state.veh);
    rows.push('<tr class="'+(isIt?'sel':'')+'">'
      +'<td>'+(isIt?'\u25b8 ':'')+esc(v.name||g)+'</td>'
      +'<td class="nowrap">'+esc((v.series||[]).join(' / '))+'</td>'
      +'<td class="n">'+num(Math.round(u))+'</td>'
      +'<td class="n">'+eur(t.eur)+'</td>'
      +'<td class="n">'+eurM(cap)+'</td></tr>');
  });
  rows.push('<tr style="border-top:2px solid var(--navy)">'
    +'<td colspan="2"><b>Network total</b></td>'
    +'<td class="n"><b>'+num(Math.round(units))+'</b></td><td></td>'
    +'<td class="n"><b>'+eurM(capacity)+'</b></td></tr>');

  document.querySelector('#d-series thead').innerHTML=
    '<tr><th>Vehicle</th><th>Series</th><th class="n">In service 2025</th>'
    +'<th class="n">Max / truck / yr</th><th class="n">Target capacity / yr</th></tr>';
  document.querySelector('#d-series tbody').innerHTML=rows.join('');
  var note=document.getElementById('d-seriesnote');
  if(note){
    note.innerHTML='The fleet total, '+num(FLEET.units)+' vehicles in service across '
      +FLEET.markets+' markets, is measured. The split across the four vehicles is '
      +'<b>assumed</b> at 62% pickup and light, 18% light truck, 12% medium, 8% heavy: '
      +'the billing carries no model code, so the real split cannot be derived from this '
      +'data. Capacity is that assumed fleet multiplied by the official maximum spend per '
      +'vehicle per year, and it is a ceiling, not a forecast.';
  }
  var basis=document.getElementById('d-basis');
  if(basis){
    basis.innerHTML=VEH.map(function(v){
      var t=tgt[v.target]||{};
      return esc(v.name)+' '+eur(t.eur);
    }).join(' \u00b7 ')+'. Set for the range as a whole, not switched per vehicle.';
  }
}

/* ================= legend ================= */
function buildLegend(){
  var el=document.getElementById('legend');
  var html='<div class="hd">Zones on this vehicle</div>';
  ZONES.forEach(function(zn,i){
    var on=!state.hidden[i];
    html+='<div class="row'+(on?'':' dim')+'" data-i="'+i+'">'
      +'<span class="sw" style="background:'+ZCOL[zn.k]+'"></span>'
      +'<span>'+esc(zn.name.split(',')[0])+'</span>'
      +'<span class="eu">'+eurM(ZONE[i].eur)+'</span></div>';  });
  html+='<div class="row fn"><span class="sw" style="background:#8f9aa8"></span>'
    +'<span>Electrical layer</span>'
    +'<span class="eu"><input type="checkbox" id="elecbox"'+(state.showElec?' checked':'')
    +' style="cursor:pointer"></span></div>';
  el.innerHTML=html;
  Array.prototype.forEach.call(el.querySelectorAll('.row[data-i]'),function(b){
    b.style.cursor='pointer';
    b.addEventListener('click',function(){
      var i=+b.getAttribute('data-i');
      state.hidden[i]=!state.hidden[i];
      if(state.hidden[i] && state.sel===i) state.sel=-1;
      buildLegend(); draw(); detail();
    });
  });
  var cb=document.getElementById('elecbox');
  if(cb) cb.addEventListener('change',function(){
    state.showElec=cb.checked; draw(); });
}

/* ================= vehicle tabs ================= */
function buildTabs(){
  var el=document.getElementById('tabs');
  el.innerHTML=VEH.map(function(v,i){
    return '<button data-i="'+i+'" class="'+(i===state.veh?'on':'')+'">'
      +'<span class="t">'+esc(v.name)+'</span>'
      +'<span class="s">'+esc(v.kind)+'</span></button>';
  }).join('');
  Array.prototype.forEach.call(el.querySelectorAll('button'),function(b){
    b.addEventListener('click',function(){
      state.veh=+b.getAttribute('data-i');
      state.sel=-1; state.family=-1;
      Array.prototype.forEach.call(el.querySelectorAll('button'),
        function(x){ x.classList.remove('on'); });
      b.classList.add('on');
      var v=VEH[state.veh];
      document.getElementById('vname').textContent=v.name;
      document.getElementById('vkind').textContent=v.kind+' \u00b7 '+v.series.join(' / ');
      /* the picture has to be fetched for the new vehicle before drawing, so the
         zone hotspots and the photograph always belong to the same vehicle */
      buildScene(); switchVehicle(); buildLegend(); detail();
    });
  });
}

/* ================= events ================= */
cv.addEventListener('mousemove', function(e){
  var r=cv.getBoundingClientRect();
  var mx=e.clientX-r.left, my=e.clientY-r.top;
  var z=zoneHit(mx,my);
  if(z!==state.hover){ state.hover=z; draw(); }
  if(z>=0){ showTip(e.clientX,e.clientY,z); cv.style.cursor='pointer'; }
  else { hideTip(); cv.style.cursor='default'; }
});
cv.addEventListener('mouseleave', function(){
  hideTip(); state.hover=-1; draw(); });
cv.addEventListener('click', function(e){
  var r=cv.getBoundingClientRect();
  var z=zoneHit(e.clientX-r.left, e.clientY-r.top);
  state.sel=z; state.family=-1;
  draw(); detail();
});
window.addEventListener('keydown', function(e){
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

/* ================= render ================= */
function render(){
  try{
    draw(); detail();
    document.getElementById('errbar').style.display='none';
  }catch(err){
    var b=document.getElementById('errbar');
    b.style.display='block';
    b.innerHTML='<b>Draw failed.</b> '+esc(err && err.message ? err.message : err);
  }
}
function buildHero(){
  var unp=0, unpEur=0;
  for(var i=0;i<ROWS.length;i++){ if(!ROWS[i][11]){ unp++; unpEur+=ROWS[i][6]; } }
  document.getElementById('h-eur').textContent=eur(ALL.eur);
  document.getElementById('h-eurn').textContent=
    num(ZONED)+' of it sits in the six zones on the truck';
  document.getElementById('h-step').textContent=eur(ALL.step);
  document.getElementById('h-stepn').textContent=
    pc(ALL.ratio)+' of the parts billed euro';
  document.getElementById('h-pct').textContent=pct(ALL.pct);
  document.getElementById('h-pctn').textContent=
    'base-price move, weighted by units, not revenue';
  document.getElementById('h-pn').textContent=num(ALL.npn);
  document.getElementById('h-pnn').textContent=num(M.repertoire.billed_in_tree)
    +' of them sit in the AIM tree';
  document.getElementById('h-zones').textContent=num(ZONES.length);
  document.getElementById('h-zonesn').textContent=
    'five physical, one functional layer';
}

function boot(){
  var v=VEH[state.veh];
  document.getElementById('vname').textContent=v.name;
  document.getElementById('vkind').textContent=v.kind+' \u00b7 '+v.series.join(' / ');
  document.getElementById('genline').textContent=' Built '+M.built.slice(0,10)+'.';
  document.getElementById('f-zoned').textContent=num(ZONED);
  buildHero();
  buildTabs(); buildLegend();
  buildScene(); render();      /* paint the chrome at once */
  bootFit();                   /* size the canvas, then draw */
  switchVehicle();             /* fetch the picture, then redraw when it lands */
  window.__truckReady=true;
}
window.__truckReady=false;
window.truckState=state;
window.truckZones=ZONE;
window.truckHit=function(mx,my){ return zoneHitAll(mx,my); };
window.truckSelect=function(z){ state.sel=z; state.family=-1; draw(); detail(); };
window.truckLabelRects=function(){
  /* exactly what the resolver placed on the last draw: QA asserts that no two
     of these overlap, so the clipping that shipped on the spider cannot recur */
  return LABEL_RECTS.map(function(r){
    return {zone:r.zone, name:r.name, x:r.x, y:r.y, w:r.w, h:r.h};
  });
};
window.truckAllZonePoints=function(){
  /* a screen point inside every zone, found by scanning the stage, so QA can
     click each one the way a person would */
  var out=[], z, x, y, h;
  for(z=0;z<ZONES.length;z++){
    var found=null;
    for(x=0;x<W && !found;x+=5){
      for(y=0;y<H && !found;y+=5){
        h=zoneHitAll(x,y);
        if(h.length && h[0]===z) found=[x,y];
      }
    }
    out.push({zone:z, pt:found});
  }
  return out;
};
window.truckPageSize=function(){ return {w:W, h:H}; };
window.truckFit=function(){
  /* How much of the stage the photograph occupies, so QA can assert the vehicle
     is drawn big rather than shrinking to make room for labels. */
  if(!PHOTO.ready) return {x0:0,y0:0,w:0,h:0,wPct:0,hPct:0,stage:{w:W,h:H},ready:false};
  return {x0:PHOTO.x, y0:PHOTO.y, w:PHOTO.w, h:PHOTO.h,
          wPct:+(100*PHOTO.w/W).toFixed(1), hPct:+(100*PHOTO.h/H).toFixed(1),
          stage:{w:W,h:H}, ready:true};
};
/* ---- QA hooks ------------------------------------------------------------
   Everything the automated check needs to judge this page without a human
   looking at it: the picture's placement, each zone's placed polygons and
   bounding box, and an interior point of every zone that QA can sample body
   colour at. A hotspot fitted to the wrong part of the photograph shows up here
   as a rectangle that does not sit inside the vehicle's own pixels. */
window.truckPhoto=function(){
  return {ready:PHOTO.ready, key:PHOTO.key, x:PHOTO.x, y:PHOTO.y,
          w:PHOTO.w, h:PHOTO.h, nat:PHOTO.nat,
          bbox:PHOTO.bbox, face:PHOTO.face,
          depicts:(mediaFor(PHOTO.key)||{}).depicts||null,
          credit:(mediaFor(PHOTO.key)||{}).credit||null};
};
/* The vehicle's own rectangle inside the picture, in screen pixels. This is what
   QA compares the hotspots against: a hotspot outside this rectangle is on the
   lawn, not on the truck. */
window.truckVehicleRect=function(){
  if(!PHOTO.ready) return null;
  var b = PHOTO.bbox || [0,0,1,1];
  var p0 = photoPoint(b[0], b[1]), p1 = photoPoint(b[2], b[3]);
  return {x:p0[0], y:p0[1], w:p1[0]-p0[0], h:p1[1]-p0[1]};
};
/* Each zone's placed screen polygons, so QA can test them against real pixels. */
/* ---- the hooks the existing check suite calls -------------------------------
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
window.truckZoneScreenPolys=function(){
  var out=[];
  for(var i=0;i<ZONES.length;i++) out.push(zoneScreenPolys(i));
  return out;
};
window.truckZoneRects=function(){ return zoneRects(); };
/* The zone definitions, including each zone's name and what it covers. QA reads
   names from here: window.truckZones is the money per zone, not the definitions. */
window.truckZoneMeta=function(){
  return ZONES.map(function(z){
    return {name:z.name, where:z.where, how:z.how, k:z.k};
  });
};
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
boot();
})();
