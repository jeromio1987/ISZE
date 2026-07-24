---
title: Data Integrity
---

[← Command Centre](/) · Governance · coverage of the network and where UIO actuals are missing.

```sql di_kpi
select
  count(*)::double as total,
  sum(case when uio_units > 0 then 1 else 0 end)::double as with_uio,
  sum(case when coalesce(uio_units,0) = 0 then 1 else 0 end)::double as no_uio
from prism.uio where year = (select max(year) from prism.uio)
```

<Grid cols=3>
  <BigValue data={di_kpi} value=total fmt=num0 title="🏢 Distributors in scope" />
  <BigValue data={di_kpi} value=with_uio fmt=num0 title="✅ With verified UIO" />
  <BigValue data={di_kpi} value=no_uio fmt=num0 title="⚪ Awaiting UIO" />
</Grid>

<Alert status=info>
Pipeline contract verification runs in the PRISM build — see <code>Data/derived/_verification_report.json</code>.
GPS warranty + per-DB PMS + BVP sanity checks are in <code>Data/derived/_gps_integrity_audit.md</code>.
</Alert>

## GPS warranty & BVP 0% sanity (latest year)

Cross-check: ex-warranty GPS, contested BVP capture, and PMS oil-filter capture. **Low BVP % with warranty present is usually correct** — warranty parts bill as genuine, not BVP down-trade.

```sql di_audit
select distributor_code,
  spend_per_unit_eur::double as spu_incl,
  spend_per_unit_ex_warranty_eur::double as spu_ex,
  warranty_parts_eur::double as warranty_eur,
  contested_bvp_capture::double as bvp_contested,
  bvp_low_capture_verdict,
  oil_filter_capture::double as oil_cap,
  traffic_light_shift_ex_warranty
from prism.integrity_audit
order by warranty_eur desc nulls last
```

<DataTable data={di_audit} rows=20 rowShading=true>
  <Column id=distributor_code title="DB" />
  <Column id=warranty_eur fmt=eur0 title="Warranty €" />
  <Column id=spu_incl fmt=eur0 title="SPU incl" />
  <Column id=spu_ex fmt=eur0 title="SPU ex-warr" />
  <Column id=bvp_contested fmt=pct0 title="BVP contested" />
  <Column id=bvp_low_capture_verdict title="BVP verdict" />
  <Column id=traffic_light_shift_ex_warranty title="GPS TL shift" />
</DataTable>

## Distributors awaiting verified UIO

These bill parts but have no confirmed parc, so they appear as “unverified” on the Command Centre and are excluded from spend-per-unit.

```sql di_unv
select distributor_code, country,
  net_sales_eur::double as net_sales,
  uio_units::double as uio_units,
  traffic_light
from prism.uio
where year = (select max(year) from prism.uio) and coalesce(uio_units,0) = 0
order by net_sales desc
```

<DataTable data={di_unv} rows=10 rowShading=true>
  <Column id=distributor_code title="Distributor" />
  <Column id=country title="Country" />
  <Column id=net_sales title="Net sales" fmt=eur0 />
  <Column id=traffic_light title="Status" />
</DataTable>
