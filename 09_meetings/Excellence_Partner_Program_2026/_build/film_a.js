/* Film A - "The life of one monthly file". One continuous rail, camera follows the file. Internal build brief. */
const NAVY='#15233c',INK='#0d1626',TERRA='#c0552d',PAPER='#f7f4ee',AMBER='#d9a441',STEEL='#8aa0bd',GREEN='#5aa886',PANEL='#1f3354',RAILC='#2f4a74';
const clamp=(x,a=0,b=1)=>Math.max(a,Math.min(b,x));
const ease=x=>x<.5?4*x*x*x:1-Math.pow(-2*x+2,3)/2;
const seg=(t,a,b)=>ease(clamp((t-a)/(b-a)));
const lin=(t,a,b)=>clamp((t-a)/(b-a));
const lerp=(a,b,k)=>a+(b-a)*k;
function keyed(kf,t){ if(t<=kf[0][0])return kf[0][1]; for(let i=1;i<kf.length;i++){ if(t<=kf[i][0]){ return lerp(kf[i-1][1],kf[i][1],ease(lin(t,kf[i-1][0],kf[i][0]))); } } return kf[kf.length-1][1]; }
function rr(x,y,w,h,r){ctx.beginPath();ctx.roundRect(x,y,w,h,r);}
function T(s,x,y,o={}){const{size=20,fam='Segoe UI',wt='400',col=PAPER,al='left',a=1}=o;ctx.save();ctx.globalAlpha*=a;ctx.font=`${wt} ${size}px ${fam}`;ctx.fillStyle=col;ctx.textAlign=al;ctx.textBaseline='alphabetic';ctx.fillText(s,x,y);ctx.restore();}
function TL(lines,x,y,lh,o){lines.forEach((s,i)=>T(s,x,y+i*lh,o));}
function hex(seed,n){let s=seed*9301+49297,r='';for(let i=0;i<n;i++){s=(s*9301+49297)%233280;r+='0123456789abcdef'[Math.floor(s/233280*16)];}return r;}

const RAIL=400, ARCH0=1000, ARCHD=125, archX=i=>ARCH0+i*ARCHD;
const SEV=['E','E','E','E','EW','E','E','EW','E','E','I','W','W','IE','W','E','W','E'];
const SEVC={E:[TERRA],W:[AMBER],I:[STEEL],EW:[TERRA,AMBER],IE:[STEEL,TERRA]};
const VNAME={2:'no prices',3:'month',4:'part numbers',7:'dealer list',9:'control record',10:'on time?',11:'volume jump',15:'right distributor',17:'hidden price'};

/* ---- file paths over time ---- */
const copy1X=t=>keyed([[11,215],[14,760],[19,760],[22,900],[26.3,1215],[27.2,1215],[29.5,900]],t);
const copy2X=t=>keyed([[37.2,215],[39,760],[40,900],[52,3100],[54,3470]],t);
function hop(x){const b=clamp(1-Math.abs((x-500)/250));return -170*ease(b);}

function camX(t){
  if(t<39) return keyed([[0,0],[17,0],[22,700],[33,700],[35.5,0],[39,0]],t);
  if(t<52){ return lerp(0,Math.max(0,copy2X(t)-420),seg(t,39,41)); }
  if(t<77) return keyed([[52,Math.max(0,copy2X(52)-420)],[54,3250],[64,3250],[66,4450],[75,4450],[77,5850]],t);
  return keyed([[77,5850],[83,5850],[85,6200],[89,6200],[91,7600],[98,7600]],t);
}

/* ---- drawing pieces ---- */
function fileG(x,y,k,o={}){
  ctx.save();ctx.translate(x,y);ctx.globalAlpha*=(o.a==null?1:o.a);
  const w=150*k,h=100*k;
  rr(-w/2,-h/2,w,h,9*k);ctx.fillStyle=o.fill||PAPER;ctx.fill();
  if(o.edge){ctx.lineWidth=4*k;ctx.strokeStyle=o.edge;if(o.dash)ctx.setLineDash([8*k,6*k]);ctx.stroke();ctx.setLineDash([]);}
  ctx.fillStyle='#c9c3b6';
  for(let r=0;r<4;r++)for(let c=0;c<4;c++){ctx.fillRect(-w/2+14*k+c*30*k,-h/2+36*k+r*14*k,22*k,6*k);}
  T(o.label||'',-w/2+12*k,-h/2+24*k,{size:15*k,col:NAVY,wt:'600'});
  ctx.restore();
}
function lockG(x,y,s,a=1){ctx.save();ctx.globalAlpha*=a;ctx.translate(x,y);ctx.fillStyle=AMBER;rr(-12*s,-4*s,24*s,18*s,3*s);ctx.fill();ctx.strokeStyle=AMBER;ctx.lineWidth=3*s;ctx.beginPath();ctx.arc(0,-4*s,7*s,Math.PI,0);ctx.stroke();ctx.restore();}
function pill(s,x,y,col,tc,size=17,a=1){ctx.save();ctx.globalAlpha*=a;ctx.font=`600 ${size}px Segoe UI`;const w=ctx.measureText(s).width+26;rr(x-w/2,y-size-4,w,size+14,(size+14)/2);ctx.fillStyle=col;ctx.fill();ctx.fillStyle=tc||PAPER;ctx.textAlign='center';ctx.fillText(s,x,y+1);ctx.restore();}

function drawDrop(t){
  const x0=100,x1=330,y=RAIL+30;
  T('drop folder',215,y-155,{al:'center',size:16,col:STEEL});
  T('one folder per distributor',215,y-135,{al:'center',size:13,col:STEEL});
  ctx.strokeStyle=STEEL;ctx.lineWidth=4;ctx.beginPath();ctx.moveTo(x0,y-40);ctx.lineTo(x0,y+20);ctx.lineTo(x1,y+20);ctx.lineTo(x1,y-40);ctx.stroke();
}
function drawVault(t){
  const x=380,w=260,y0=RAIL-110;
  rr(x,y0,w,230,12);ctx.fillStyle=PANEL;ctx.fill();ctx.strokeStyle=RAILC;ctx.lineWidth=3;ctx.stroke();
  T('raw vault',x+w/2,y0-18,{al:'center',size:18,col:STEEL});
  const open=[[12,13.3],[36.6,37.9]];
  for(let d=0;d<3;d++){
    const dy=y0+14+d*70; let slide=0;
    if(d<2){ const [a,b]=open[d]; slide=40*Math.max(seg(t,a,a+.5)-seg(t,b-.4,b),0); }
    rr(x+12+slide,dy,w-24,58,8);ctx.fillStyle='#2a4472';ctx.fill();ctx.strokeStyle='#3c5a8c';ctx.lineWidth=2;ctx.stroke();
    ctx.fillStyle='#0d1626';rr(x+w/2-20+slide,dy+24,40,8,4);ctx.fill();
    const locked=(d===0&&t>13.4)||(d===1&&t>38);
    if(locked) lockG(x+w-34+slide,dy+30,.8);
  }
  if(t>14) T('never edited',x+w/2,y0+250,{al:'center',size:15,col:AMBER,a:seg(t,14,15)});
}
function drawGauntlet(t,passX,hitIdx){
  for(let i=0;i<18;i++){
    const x=archX(i),cols=SEVC[SEV[i]];
    let flash=0;
    if(passX!=null) flash=clamp(1-Math.abs(passX-x)/70);
    const passed=passX!=null&&passX>x+30;
    const hit=(hitIdx===i);
    ctx.save();
    ctx.lineWidth=6;ctx.lineCap='round';
    for(let side=0;side<2;side++){
      ctx.strokeStyle=cols[Math.min(side,cols.length-1)];
      ctx.globalAlpha*=.55+.45*Math.max(flash,hit?1:0);
      ctx.beginPath();
      if(side===0){ctx.moveTo(x-28,RAIL+70);ctx.lineTo(x-28,RAIL-45);ctx.arc(x,RAIL-45,28,Math.PI,1.5*Math.PI);}
      else{ctx.moveTo(x,RAIL-73);ctx.arc(x,RAIL-45,28,1.5*Math.PI,2*Math.PI);ctx.lineTo(x+28,RAIL+70);}
      ctx.stroke();
    }
    ctx.restore();
    if(flash>0.05&&!hit){ctx.save();ctx.globalAlpha=.35*flash;ctx.fillStyle=GREEN;rr(x-26,RAIL-72,52,140,24);ctx.fill();ctx.restore();}
    if(hit){ctx.save();ctx.globalAlpha=.5;ctx.fillStyle=TERRA;rr(x-26,RAIL-72,52,140,24);ctx.fill();ctx.restore();}
    if(passed) T('✓',x,RAIL-82,{al:'center',size:20,col:GREEN,wt:'700'});
    T('V'+String(i+1).padStart(3,'0'),x,RAIL+98,{al:'center',size:13,col:STEEL});
    if(VNAME[i]) T(VNAME[i],x,RAIL+(i%2?138:118),{al:'center',size:13,col:PAPER,a:.8});
  }
}
function drawLedger(t){
  const x=3480,y=170,w=560,h=300;
  rr(x,y,w,h,12);ctx.fillStyle=PANEL;ctx.fill();ctx.strokeStyle=RAILC;ctx.lineWidth=3;ctx.stroke();
  T('ledger',x+20,y-12,{size:18,col:STEEL});
  T('file',x+24,y+36,{size:14,col:STEEL});T('version',x+210,y+36,{size:14,col:STEEL});T('state',x+330,y+36,{size:14,col:STEEL});
  ctx.fillStyle=RAILC;ctx.fillRect(x+16,y+46,w-32,2);
  const rows=[
    {v:'v1',a:54.0,st:()=>['NOT ACCEPTED',TERRA]},
    {v:'v2',a:55.2,st:()=>t>58.6?['SUPERSEDED','#6d7d95']:['ACCEPTED',GREEN]},
    {v:'v3',a:58.2,st:()=>['ACCEPTED',GREEN]}];
  rows.forEach((r,i)=>{
    const k=seg(t,r.a,r.a+.6); if(k<=0)return; const yy=y+84+i*66;
    ctx.save();ctx.globalAlpha=k;
    fileG(x+68,yy-8,.38,{label:'2027-01'});
    T(r.v,x+222,yy,{size:20,col:PAPER,wt:'600'});
    const [s,c]=r.st();pill(s,x+400,yy,c,c===GREEN||c===TERRA?PAPER:PAPER,15);
    ctx.restore();
  });
  if(t>60) T('the original stays on disk',x+w/2,y+h-18,{al:'center',size:15,col:AMBER,a:seg(t,60,61)});
  /* canonical table */
  const bx=4150,by=250;
  const lit=Math.max(seg(t,55.2,56)*(1-seg(t,58.2,58.2)), 0);
  const on=t>55.5?1:0.35;
  rr(bx,by,300,110,12);ctx.fillStyle=PANEL;ctx.fill();ctx.strokeStyle=on>.5?GREEN:RAILC;ctx.lineWidth=3;ctx.stroke();
  T('shared sales-to-dealer table',bx+150,by+46,{al:'center',size:17,col:PAPER,a:on});
  T('existing loaders, one format',bx+150,by+72,{al:'center',size:14,col:STEEL,a:on});
  ctx.strokeStyle=on>.5?GREEN:RAILC;ctx.lineWidth=4;ctx.beginPath();ctx.moveTo(x+w,y+150);ctx.lineTo(bx,by+55);ctx.stroke();
  T('only accepted files get here',bx+150,by+140,{al:'center',size:14,col:AMBER,a:seg(t,56,57)});
}
function drawRecon(t){
  const base=RAIL+110, xb=4850, bw=120;
  T('compare with what we billed',5030,RAIL-190,{al:'center',size:18,col:STEEL});
  const gb=seg(t,65,67), sw=seg(t,67.2,69), gs=seg(t,69,71), br=seg(t,71.5,72.5);
  const H1=240,Hw=70,Hs=130;
  /* billed (without warranty) */
  const hb=(H1-Hw)*gb;
  rr(xb,base-hb,bw,hb,6);ctx.fillStyle='#4a6fa8';ctx.fill();
  T('we billed',xb+bw/2,base+28,{al:'center',size:17});
  /* warranty slice detaches */
  const wx=lerp(xb,xb+bw+40,sw), wy=base-(H1-Hw)*gb-Hw*gb;
  if(gb>0){rr(wx,wy-(sw>0?10*sw:0),bw,Hw*gb,6);ctx.fillStyle=AMBER;ctx.fill();}
  if(sw>0.7) T('warranty, shown apart',wx+bw/2,base+28,{al:'center',size:17,a:clamp((sw-.7)/.3)});
  if(sw>0.3){ctx.save();ctx.globalAlpha=sw*.6;ctx.strokeStyle=AMBER;ctx.setLineDash([6,6]);ctx.beginPath();ctx.moveTo(wx+bw/2,wy+Hw*gb);ctx.lineTo(wx+bw/2,base-4);ctx.stroke();ctx.restore();}
  /* sales to dealer */
  const xs=xb+2*(bw+40)+30,hs=Hs*gs+0;
  rr(xs,base-hs,bw,hs,6);ctx.fillStyle=STEEL;ctx.fill();
  T('sold on to dealers',xs+bw/2,base+28,{al:'center',size:17,a:gs});
  /* gap bracket */
  if(br>0){ctx.save();ctx.globalAlpha=br;ctx.strokeStyle=PAPER;ctx.lineWidth=3;
    const yT=base-(H1-Hw), yB=base-Hs;
    ctx.setLineDash([5,5]);ctx.beginPath();ctx.moveTo(xb+bw,yT);ctx.lineTo(xs+bw,yT);ctx.stroke();ctx.setLineDash([]);
    const bx2=xs+bw+16;ctx.beginPath();ctx.moveTo(bx2-6,yT);ctx.lineTo(bx2,yT);ctx.lineTo(bx2,yB);ctx.lineTo(bx2-6,yB);ctx.stroke();
    T('stock movement',bx2+14,(yT+yB)/2-4,{size:18,col:AMBER,wt:'600'});
    T('read as stock, not as lost sales',bx2+14,(yT+yB)/2+20,{size:15,col:PAPER});
    ctx.restore();}
  T('schematic only: tests use made-up data, no real figures',5030,base+66,{al:'center',size:13,col:STEEL});
}
const GATES=['sales to dealer on time','quality','dealer detail','dealer list current','monthly KPIs','IDS assessed','training done'];
function drawGatesStation(t){
  T('every quarter: seven yes/no gates',5950,RAIL-190,{size:18,col:STEEL,a:1-seg(t,83,84.2)});
  GATES.forEach((g,i)=>{
    const x=5990+i*150, t0=77.5+i*.8, k=seg(t,t0,t0+.5), na=(i===5);
    ctx.beginPath();ctx.arc(x,RAIL-30,34,0,7);ctx.fillStyle=PANEL;ctx.fill();ctx.lineWidth=4;ctx.strokeStyle=RAILC;ctx.stroke();
    if(k>0){ctx.save();ctx.globalAlpha=k;ctx.beginPath();ctx.arc(x,RAIL-30,34*(.6+.4*k),0,7);ctx.fillStyle=na?'#55637a':GREEN;ctx.fill();
      T(na?'n/a':'✓',x,RAIL-20,{al:'center',size:na?20:30,wt:'700',col:PAPER});ctx.restore();}
    T('G'+(i+1),x,RAIL-82,{al:'center',size:15,col:STEEL});
    const words=g.split(' ');const half=Math.ceil(words.length/2);
    T(words.slice(0,half).join(' '),x,RAIL+32,{al:'center',size:14});
    if(words.length>1)T(words.slice(half).join(' '),x,RAIL+50,{al:'center',size:14});
  });
  const na=seg(t,81.8,82.8);
  if(na>0)TL(['no IDS round planned','= not applicable,','never a failure'],5990+5*150,RAIL+100,18,{al:'center',size:14,col:AMBER,a:na});
  const el=seg(t,83.3,84.3);
  if(el>0){pill('ELIGIBLE',6430,RAIL+190,GREEN,PAPER,26,el);}
  /* proposal document */
  const dk=seg(t,84.8,86.4);
  if(dk>0){
    const dx=lerp(6600,7220,dk), dy=RAIL-20;
    ctx.save();ctx.globalAlpha=dk;
    rr(dx-120,dy-80,240,160,10);ctx.fillStyle=PAPER;ctx.fill();
    T('discount proposal',dx,dy-44,{al:'center',size:18,col:NAVY,wt:'700'});
    T('one quarter, per distributor',dx,dy-22,{al:'center',size:14,col:NAVY});
    T('arithmetic shown line by line',dx,dy-4,{al:'center',size:14,col:NAVY});
    ctx.fillStyle='#c9c3b6';for(let r=0;r<3;r++)ctx.fillRect(dx-96,dy+14+r*14,192,6);
    ctx.restore();
    const st=seg(t,86.6,87.2);
    if(st>0){ctx.save();ctx.translate(dx+36,dy+56);ctx.rotate(-.15);ctx.globalAlpha=st;ctx.lineWidth=4;ctx.strokeStyle=TERRA;rr(-92,-24,184,48,6);ctx.stroke();
      T('PROPOSAL ONLY',0,-3,{al:'center',size:20,col:TERRA,wt:'700'});T('people post it',0,17,{al:'center',size:14,col:TERRA});ctx.restore();}
    T('a manual override file is read last',dx,dy+110,{al:'center',size:14,col:STEEL,a:seg(t,87.4,88.2)});
  }
}
function drawReturn(t){
  const cx=8110, y0=170, w=380, h=420;
  const k=seg(t,91,92.5), out=seg(t,96.6,98);
  ctx.save();ctx.translate(0,-out*500);ctx.globalAlpha=k*(1-out);
  rr(cx-w/2,y0,w,h,12);ctx.fillStyle=PAPER;ctx.fill();
  T('Monthly return',cx-w/2+24,y0+42,{size:24,fam:'Georgia',col:NAVY,wt:'700'});
  T('draft, for one distributor',cx-w/2+24,y0+66,{size:14,col:'#666'});
  const tiles=[['Billed and sold on',93],['Genuine and BVP mix, in euros',93.7],['Maintenance parts covered',94.4],['IDS position',95.1]];
  tiles.forEach((tl,i)=>{
    const ty=y0+90+i*76, kk=seg(t,tl[1],tl[1]+.6);
    ctx.save();ctx.globalAlpha*=kk;
    rr(cx-w/2+20,ty,w-40,64,8);ctx.fillStyle='#ece7dc';ctx.fill();
    T(tl[0],cx-w/2+34,ty+24,{size:14,col:NAVY,wt:'600'});
    ctx.fillStyle=TERRA;ctx.fillRect(cx-w/2+34,ty+36,(120+i*18)*kk,10);
    ctx.fillStyle=NAVY;ctx.fillRect(cx-w/2+34,ty+50,(95+(i%2)*30)*kk,6);
    ctx.setLineDash([4,4]);ctx.strokeStyle='#777';ctx.beginPath();ctx.moveTo(cx-w/2+34+140,ty+32);ctx.lineTo(cx-w/2+34+140,ty+60);ctx.stroke();ctx.setLineDash([]);
    ctx.restore();
  });
  T('own figures | dashed = anonymous network average',cx,y0+h-14,{al:'center',size:12,col:'#555'});
  ctx.restore();
  const rt=seg(t,94.8,95.8)*(1-out);
  if(rt>0)TL(['no ranking','no other distributor named','a person sends it'],cx+w/2+30,y0+140,26,{size:19,col:AMBER,a:rt});
}

/* ---- overlays in screen space ---- */
const CAPS=[
 [0.6,5.8,''],
 [6.3,10.8,'A distributor drops its monthly sales-to-dealer file in its own folder.'],
 [10.8,13.8,'We fingerprint it, then lock the original away.'],
 [13.8,16.2,'A copy goes on to be checked. The original is never edited.'],
 [16.5,19.6,'Send the same file twice and nothing changes: same fingerprint, no new version.'],
 [22,26.5,'Eighteen checks. Errors stop the file. Warnings let it through, flagged.'],
 [27.6,33.2,'A file with a price column is rejected, not trimmed. The receipt says what to fix.'],
 [35.4,38.5,'The distributor resends: version 2.'],
 [41,47,'Every check runs, in order. Each one is a plain yes or no.'],
 [47.5,51.5,'On time is information. A volume jump is a warning.'],
 [53,57,'Every file leaves a line in the ledger: when, what, and why.'],
 [58,64,'A correction replaces the version. It never erases the history.'],
 [65,70,'Next, sales to dealer goes beside what ISZE billed. Warranty gets its own line.'],
 [71.5,75.5,'What is left is stock. It is not read as lost sales.'],
 [77,83,'At quarter end, seven gates. Each one is evidence, not opinion.'],
 [85,89.5,'The job writes a proposal. It posts nothing.'],
 [91.5,97,'And every month the distributor gets its own return.']
];
const CHAPS=[[6,20,'1','Receive'],[20,52,'2','Check'],[52,64,'3','Remember'],[64,76,'4','Compare with billing'],[76,90,'5','Quarterly gates'],[90,98,'6','Monthly return']];

function overlay(t){
  /* chapter marker */
  for(const [a,b,n,nm] of CHAPS){ if(t>=a&&t<b){const k=seg(t,a,a+.8)*(1-seg(t,b-.6,b)); ctx.save();ctx.globalAlpha=k;T(n,48,70,{size:44,fam:'Georgia',col:TERRA,wt:'700'});T(nm,82,70,{size:26,fam:'Georgia',col:PAPER});ctx.restore();} }
  /* legend during gauntlet */
  const lg=seg(t,20.5,21.5)*(1-seg(t,47.4,48.4));
  if(lg>0){ctx.save();ctx.globalAlpha=lg;
    [[TERRA,'error: file not accepted'],[AMBER,'warning: accepted, flagged'],[STEEL,'information: noted']].forEach((l,i)=>{ctx.fillStyle=l[0];ctx.fillRect(W-330,92+i*26,18,6);T(l[1],W-302,100+i*26,{size:15});});
    ctx.restore();}
  /* captions */
  for(const [a,b,s] of CAPS){ if(!s)continue; const k=seg(t,a,a+.5)*(1-seg(t,b-.5,b)); if(k<=0)continue;
    ctx.save();ctx.globalAlpha=k;ctx.font='500 26px Segoe UI';const w=Math.min(ctx.measureText(s).width+56,W-80);
    rr(W/2-w/2,H-86,w,52,26);ctx.fillStyle='rgba(13,22,38,.82)';ctx.fill();
    ctx.fillStyle=PAPER;ctx.textAlign='center';ctx.fillText(s,W/2,H-52);ctx.restore(); }
}

/* ---- scenes ---- */
function world(t){
  const cx=camX(t);
  /* parallax dots */
  ctx.fillStyle='#22385c';
  for(let gx=-100;gx<W+200;gx+=80){for(let gy=40;gy<H;gy+=80){const x=((gx-(cx*.45)%80));ctx.fillRect(x,gy,3,3);}}
  ctx.save();ctx.translate(-cx,0);
  /* rail */
  ctx.fillStyle=RAILC;ctx.fillRect(0,RAIL+10,9000,8);
  for(let x=0;x<9000;x+=60){ctx.fillStyle='#3d5f94';ctx.fillRect(x+((t*40)%60),RAIL+12,16,4);}
  drawDrop(t);drawVault(t);
  /* gauntlet pass position */
  let passX=null,hitIdx=null;
  if(t>=22&&t<33){ passX=Math.min(copy1X(t),1215-25); if(t>=26.3&&t<31)hitIdx=2; if(t>=31){passX=null;} }
  else if(t>=39&&t<56){ passX=copy2X(t); }
  drawGauntlet(t,passX,hitIdx);
  drawLedger(t);drawRecon(t);drawGatesStation(t);drawReturn(t);

  /* original v1 */
  if(t>=3&&t<14){
    const fall=seg(t,3,5.4); let y=lerp(-80,RAIL-20,fall); let x=215, k=1;
    if(t>=12){const m=seg(t,12,13.4);x=lerp(215,510,m);y=lerp(RAIL-20,RAIL-76,m);k=lerp(1,.5,m);}
    const gone=t>13.4?1:0; if(!gone)fileG(x,y,k,{label:'2027-01 · v1'});
    if(t>5.6&&t<12){const hk=seg(t,6,7.4)*(1-seg(t,11.2,12));const sd=Math.floor(t*6)<8?Math.floor(t*6):7;T('sha256 '+hex(sd,4+Math.floor(seg(t,6.4,9.2)*20)),215,RAIL-84,{al:'center',size:16,fam:'Consolas',col:AMBER,a:hk});}
  }
  /* duplicate ghost */
  if(t>=16.2&&t<19.8){const g=seg(t,16.2,17.4), d=seg(t,18.6,19.6); fileG(lerp(-60,215,g),RAIL-20,1,{label:'2027-01 · v1',a:g*(1-d),dash:true,edge:STEEL});
    if(t>17.2)T('same fingerprint',215,RAIL-84,{al:'center',size:16,col:AMBER,a:seg(t,17.2,17.8)*(1-d)});}
  /* copy v1 */
  if(t>=11&&t<34){
    const x=copy1X(t); let y=RAIL-20+hop(x); const bounce=t>=26.3; let sh=0;
    if(t>=26.3&&t<27.6)sh=Math.sin(t*60)*5*(1-lin(t,26.3,27.6));
    const a=1-seg(t,32,33.4);
    fileG(x+sh,y,.6,{label:'v1',a:a*(t<11.8?seg(t,11,11.8):1),edge:bounce?TERRA:STEEL,dash:!bounce});
    if(t>=27.2&&t<33) pill('NOT ACCEPTED',x,y-70,TERRA,PAPER,15,a);
  }
  /* receipt v1 flies up */
  if(t>=28.4&&t<33.6){const k=seg(t,28.4,30.0), o=seg(t,32.2,33.6);
    ctx.save();ctx.globalAlpha=k*(1-o);
    const rx=1000+k*0, ry=lerp(RAIL-20,150,k)-o*300;
    rr(rx-215,ry-52,430,116,10);ctx.fillStyle=PAPER;ctx.fill();
    T('Receipt · version 1 · NOT ACCEPTED',rx-197,ry-22,{size:17,col:TERRA,wt:'700'});
    T('Rule V003: a price column was found.',rx-197,ry+4,{size:16,col:NAVY});
    T('Remove it and send the file again as version 2.',rx-197,ry+28,{size:16,col:NAVY});
    ctx.restore();}
  /* v2 file */
  if(t>=34.6&&t<38.2){
    const fall=seg(t,34.6,36.4); let y=lerp(-80,RAIL-20,fall), x=215, k=1;
    if(t>=36.6){const m=seg(t,36.6,37.9);x=lerp(215,510,m);y=lerp(RAIL-20,RAIL-6,m);k=lerp(1,.5,m);}
    if(t<37.9)fileG(x,y,k,{label:'2027-01 · v2'});
    if(t>36.2&&t<36.8)T('new fingerprint',215,RAIL-84,{al:'center',size:16,col:AMBER,a:seg(t,36.2,36.5)*(1-seg(t,36.6,36.8))});
  }
  /* copy v2 */
  if(t>=37.2&&t<59){
    const x=copy2X(t);const y=RAIL-20+hop(x);
    const done=t>51.4;
    fileG(x,y,.6,{label:'v2',edge:done?GREEN:STEEL,dash:!done,a:seg(t,37.2,38)*(1-seg(t,57.2,58)) });
    if(t>45.6&&t<46.4+3)T('ON TIME',x,y-70,{al:'center',size:15,col:GREEN,wt:'700',a:seg(t,45.6,46.2)*(1-seg(t,48,49))});
    if(t>51.4)pill('ACCEPTED',x,y-70,GREEN,PAPER,15,seg(t,51.4,52)*(1-seg(t,53.6,54.4)));
  }
  /* v3 correction flies into ledger */
  if(t>=56.4&&t<58.4){const k=seg(t,56.4,58.2);fileG(lerp(3200,3600,k),lerp(-60,RAIL-170,k),.45,{label:'v3',a:1-seg(t,58,58.4)});}
  ctx.restore();
}

function title(t){
  const k=seg(t,.4,1.4)*(1-seg(t,5,6));
  ctx.save();ctx.globalAlpha=k;
  T('PARTNER INTAKE · PHASE 0',W/2,H/2-60,{al:'center',size:22,col:TERRA,wt:'700'});
  T('The life of one monthly file',W/2,H/2+10,{al:'center',size:64,fam:'Georgia',wt:'700'});
  T('Internal build brief, in motion · 9 October 2026',W/2,H/2+60,{al:'center',size:22,col:STEEL});
  ctx.restore();
}

function timeline(t){
  const k=seg(t,97.4,98.6)*(1-seg(t,107.6,108.6));
  if(k<=0)return;
  ctx.save();ctx.globalAlpha=k;ctx.fillStyle=NAVY;ctx.fillRect(0,0,W,H);
  T('What gets built, and by when',70,90,{size:40,fam:'Georgia',wt:'700'});
  const ly=330, d=seg(t,98.4,100);
  ctx.strokeStyle=RAILC;ctx.lineWidth=6;ctx.beginPath();ctx.moveTo(70,ly);ctx.lineTo(70+(W-140)*d,ly);ctx.stroke();
  const mk=(x,t0,l1,l2,c)=>{const q=seg(t,t0,t0+.6);if(q<=0)return;ctx.save();ctx.globalAlpha*=q;ctx.beginPath();ctx.arc(x,ly,11,0,7);ctx.fillStyle=c;ctx.fill();T(l1,x,ly-26,{al:'center',size:20,wt:'700'});T(l2,x,ly+38,{al:'center',size:15,col:STEEL});ctx.restore();};
  mk(190,98.8,'Jan to Mar 2027','trial months',AMBER);
  mk(520,99.6,'1 April 2027','programme starts (FY2028)',TERRA);
  mk(830,100.4,'End of June 2027','first quarterly check',GREEN);
  mk(1100,101.2,'no fixed date','built alongside',STEEL);
  const chips=(x,t0,items,c)=>items.forEach((s,i)=>{const q=seg(t,t0+i*.45,t0+i*.45+.5);if(q<=0)return;ctx.save();ctx.globalAlpha*=q;
     const y=ly+70+i*58;rr(x-120,y,240,46,10);ctx.fillStyle=PANEL;ctx.fill();ctx.fillStyle=c;ctx.fillRect(x-120,y,6,46);
     T(s[0],x-102,y+29,{size:16,col:c,wt:'700'});T(s[1],x-62,y+29,{size:15});ctx.restore();});
  chips(190,101.6,[['P01','Validator and receipts'],['P02','Intake, ledger, versions'],['P03','Feed status per distributor']],AMBER);
  const nq=seg(t,102.4,103.2);if(nq>0)TL(['P01 to P03 must work','by this date'],520,ly+96,24,{al:'center',size:17,col:AMBER,wt:'600',a:nq});
  chips(830,103.6,[['P04','Reconciliation with billing'],['P05','Eligibility and proposal'],['P06','Monthly return']],GREEN);
  chips(1100,105.4,[['P07','Monitoring page'],['P08','Dealer identity']],STEEL);
  ctx.restore();
}

const DEC=[['1','Credit note or invoice condition?','Finance'],['2','Is warranty inside the stock-order lines?','SAP owners'],['3','What does order type PRD mean? (11.6% of FY2026 billing)','SAP owners'],['4','Where does the drop live, and who holds the access list?','IT'],['5','Which distributors already send files, and in what shape?','Sales review team'],['6','Where does the KPI file land, and in what format?','Jerome'],['7','Training register: format and owner','IMG / ISZE']];
function decisions(t){
  const k=seg(t,107.8,108.8); if(k<=0)return;
  ctx.save();ctx.globalAlpha=k;ctx.fillStyle=NAVY;ctx.fillRect(0,0,W,H);
  T('Seven decisions that are still open',70,90,{size:40,fam:'Georgia',wt:'700'});
  T('The prompts build safe defaults. Cursor asks in its return packet.',70,128,{size:20,col:STEEL});
  DEC.forEach((d,i)=>{
    const q=seg(t,109+i*.55,109.9+i*.55); if(q<=0)return;
    const col=i%4, row=Math.floor(i/4), x=70+col*290, y=lerp(-160,170+row*210,q);
    rr(x,y,270,190,12);ctx.fillStyle=PANEL;ctx.fill();ctx.fillStyle=TERRA;ctx.fillRect(x,y,270,6);
    T(d[0],x+20,y+58,{size:40,fam:'Georgia',col:TERRA,wt:'700'});
    const words=d[1].split(' ');let line='',ly=y+90,lines=[];
    ctx.font='500 17px Segoe UI';words.forEach(w=>{const tr=(line+' '+w).trim();if(ctx.measureText(tr).width>230){lines.push(line);line=w;}else line=tr;});lines.push(line);
    lines.forEach((s,j)=>T(s,x+20,ly+j*22,{size:17,wt:'500'}));
    T('needs: '+d[2],x+20,y+176,{size:15,col:AMBER,wt:'600'});
  });
  const f=seg(t,115,116.2);
  T('Nothing has run in Cursor yet. Start with P01 and check how closely it follows the spec.',W/2,H-60,{al:'center',size:24,col:PAPER,a:f});
  ctx.restore();
}

function draw(t){
  ctx.clearRect(0,0,W,H);ctx.fillStyle=NAVY;ctx.fillRect(0,0,W,H);
  if(t<98){ctx.save();ctx.globalAlpha=seg(t,4.4,6);world(t);ctx.restore();}
  title(t);overlay(t);timeline(t);decisions(t);
  /* fade out at end */
  const f=seg(t,121,122);if(f>0){ctx.fillStyle='rgba(13,22,38,'+f+')';ctx.fillRect(0,0,W,H);}
}
const TOTAL=122,FILM_TITLE='Partner Intake Phase 0 - the life of one monthly file';
