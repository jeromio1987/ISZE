---
title: PRISM
hide_title: true
---

<div class="exec-hero">
  <div class="eb">ISZE · ISUZU PARTS INTELLIGENCE</div>
  <h1 class="ht">PR<span>I</span>SM</h1>
  <p class="hp">Parts Revenue Intelligence &amp; Sales Monitor — one helicopter view over the entire Isuzu aftersales network. UIO <strong>v18</strong> + GPS <strong>v9</strong> study rates (Jun 2026). Every board one click away.</p>
</div>

```sql hub_kpi
select
  (select net_sales from prism.network_revenue order by year desc limit 1)::double as net_sales,
  (select parts     from prism.network_revenue order by year desc limit 1)::double as parts,
  (select count(distinct distributor_code) from prism.uio
     where year = (select max(year) from prism.uio))::double as distributors,
  (select max(year) from prism.uio) as latest_year
```

<Grid cols=4>
  <BigValue data={hub_kpi} value=net_sales fmt=eur0 title="💶 Network parts revenue" />
  <BigValue data={hub_kpi} value=distributors fmt=num0 title="🏢 Distributors covered" />
  <BigValue data={hub_kpi} value=parts fmt=num0 title="🔩 Active part numbers" />
  <BigValue data={hub_kpi} value=latest_year title="📅 Latest data year" />
</Grid>

## Network at a glance

GPS capture vs max-spend (v9 study rates, UIO v18) — latest year. Sortable; deeper colour = higher capture.

```sql lights
select
  sum(case when traffic_light='green'  then 1 else 0 end)::double as green,
  sum(case when traffic_light='amber'  then 1 else 0 end)::double as amber,
  sum(case when traffic_light='red'    then 1 else 0 end)::double as red,
  sum(case when traffic_light not in ('green','amber','red') then 1 else 0 end)::double as unverified
from prism.uio where year = (select max(year) from prism.uio)
```

<Grid cols=4>
  <BigValue data={lights} value=green      title="🟢 Green (GPS)" />
  <BigValue data={lights} value=amber      title="🟠 Amber — watch" />
  <BigValue data={lights} value=red        title="🔴 Red" />
  <BigValue data={lights} value=unverified title="⚪ Unverified (no UIO)" />
</Grid>

```sql network
select
  distributor_code,
  spend_per_unit_eur,
  net_sales_eur,
  uio_units,
  traffic_light
from prism.uio
where year = (select max(year) from prism.uio)
order by net_sales_eur desc
```

<DataTable data={network} rows=12 rowShading=true search=true>
  <Column id=distributor_code title="Distributor" />
  <Column id=spend_per_unit_eur title="€ / unit · yr" fmt=eur0 contentType=colorscale />
  <Column id=net_sales_eur title="Net sales" fmt=eur0 contentType=colorscale />
  <Column id=uio_units title="UIO units" fmt=num0 />
  <Column id=traffic_light title="GPS light" />
</DataTable>

## The cockpit — every board, one click

<div class="nav-sec"><span class="bar"></span><div><div class="h">Layer 1 · Fleet</div><div class="b">The denominator under every metric.</div></div></div>
<div class="tiles">
  <a class="tile" href="/uio"><div class="ic">🚛</div><div class="tt">UIO — Units in Operation</div><div class="td">Parc by distributor, country & year — the demand ceiling.</div></a>
</div>

<div class="nav-sec"><span class="bar"></span><div><div class="h">Layer 2 · Methodologies — Revenue &amp; Capture</div><div class="b">The two measurement lenses on the parc.</div></div></div>
<div class="tiles">
  <a class="tile" href="/gps"><div class="ic">📊</div><div class="tt">GPS — Spend per Unit</div><div class="td">Genuine Parts Share: net sales € per truck per year.</div></a>
  <a class="tile" href="/pms"><div class="ic">🔧</div><div class="tt">PMS — Capture Rate</div><div class="td">Service-PN capture vs expected demand from the parc.</div></a>
</div>

<div class="nav-sec"><span class="bar gold"></span><div><div class="h">Product Line · Genuine vs Best Value</div><div class="b">BVP — the second line: capture more parc, defend on price.</div></div></div>
<div class="tiles">
  <a class="tile" href="/bvp"><div class="ic">⚡</div><div class="tt">BVP Intelligence</div><div class="td">Genuine vs Best Value mix, contested capture & SPU.</div></a>
  <a class="tile" href="/db_parts_mix"><div class="ic">🧩</div><div class="tt">DB Parts Mix</div><div class="td">Per-distributor genuine / contested / BVP split.</div></a>
  <a class="tile" href="/aim-leakage"><div class="ic">💶</div><div class="tt">AIM &amp; BVP Leakage</div><div class="td">Where genuine loses to the value line — 15 boards.</div></a>
</div>

<div class="nav-sec"><span class="bar"></span><div><div class="h">Layer 3 · Cross-Module Intelligence</div><div class="b">Where the signals combine into a strategy.</div></div></div>
<div class="tiles">
  <a class="tile" href="/insights"><div class="ic">🧠</div><div class="tt">Cross-Module Insights</div><div class="td">GPS × PMS × BVP fused across distributors & time.</div></a>
  <a class="tile" href="/bi-gallery"><div class="ic">🎯</div><div class="tt">BI Gallery — 15 views</div><div class="td">Five classics, five offsets, five strategic picks.</div></a>
  <a class="tile" href="/offset-insights"><div class="ic">🔀</div><div class="tt">Offset Insights</div><div class="td">Lumpiness, demand Sankey, VOR pricing power.</div></a>
</div>

<div class="nav-sec"><span class="bar"></span><div><div class="h">Distributor &amp; Pricing Lens</div><div class="b">Who carries risk, and where margin leaks.</div></div></div>
<div class="tiles">
  <a class="tile" href="/customer-risk"><div class="ic">⚠️</div><div class="tt">Customer Risk Ranking</div><div class="td">Weighted aftersales-risk index across four signals.</div></a>
  <a class="tile" href="/asp"><div class="ic">📉</div><div class="tt">Street-Price Exposure</div><div class="td">Eucon: where genuine is undercut on the street.</div></a>
  <a class="tile" href="/ituk-story"><div class="ic">📖</div><div class="tt">ITUK PMS Story</div><div class="td">The mix-not-capture narrative for ITUK's PMS book.</div></a>
  <a class="tile" href="/ituk-audit"><div class="ic">🔍</div><div class="tt">ITUK PMS PN Audit</div><div class="td">Line-level part-number audit behind the story.</div></a>
</div>

<div class="nav-sec"><span class="bar"></span><div><div class="h">Pipeline &amp; Governance</div><div class="b">Forward demand and the data it rests on.</div></div></div>
<div class="tiles">
  <a class="tile" href="/tender"><div class="ic">📋</div><div class="tt">Tender Pipeline</div><div class="td">Fleet R&M tender opportunities by distributor.</div></a>
  <a class="tile" href="/data-integrity"><div class="ic">🛡️</div><div class="tt">Data Integrity</div><div class="td">Coverage & cross-system distributor reconciliation.</div></a>
</div>

<style>
  :root { --char:#222018; --gold:#c9a227; --muted:#8a8678; }
  .exec-hero {
    background:#222018; color:#fff; border-radius:14px; padding:2.2rem 2.4rem; position:relative;
    margin:0.2rem 0 1.4rem; overflow:hidden; box-shadow:0 24px 60px -34px rgba(34,32,24,.7);
  }
  .exec-hero::before { content:""; position:absolute; left:0; top:1.6rem; bottom:1.6rem; width:3px; background:var(--gold); }
  .exec-hero .eb { color:var(--gold); font-size:.72rem; font-weight:700; letter-spacing:.24em; padding-left:1.3rem; }
  .exec-hero .ht { color:#fff; font-family:Georgia,'Playfair Display',serif; font-size:2.9rem; font-weight:800; margin:.25rem 0 0; padding-left:1.3rem; letter-spacing:.02em; }
  .exec-hero .ht span { color:var(--gold); }
  .exec-hero .hp { color:#b8b4a8; font-size:1rem; margin:.55rem 0 0; max-width:640px; padding-left:1.3rem; }

  .nav-sec { display:flex; align-items:center; gap:.7rem; margin:1.7rem 0 .85rem; }
  .nav-sec .bar { width:4px; height:30px; border-radius:4px; background:#2C5AA0; }
  .nav-sec .bar.gold { background:var(--gold); }
  .nav-sec .h { font-family:Georgia,serif; font-size:1.2rem; font-weight:700; color:var(--char); }
  .nav-sec .b { font-size:.82rem; color:var(--muted); }

  .tiles { display:grid; grid-template-columns:repeat(3,1fr); gap:.9rem; margin-bottom:.4rem; }
  .tile {
    display:block; text-decoration:none; background:#fff; border:1px solid #e8e4da; border-radius:12px;
    padding:1rem 1.1rem; transition:transform .15s ease, box-shadow .15s ease, border-color .15s ease;
  }
  .tile:hover { transform:translateY(-3px); border-color:var(--gold); box-shadow:0 16px 34px -20px rgba(201,162,39,.55); }
  .tile .ic { font-size:1.5rem; }
  .tile .tt { font-family:Georgia,serif; font-weight:700; font-size:1.02rem; color:var(--char); margin:.45rem 0 .25rem; }
  .tile .td { font-size:.82rem; color:var(--muted); line-height:1.4; }
  @media (max-width:820px){ .tiles { grid-template-columns:1fr; } }
</style>
