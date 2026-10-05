/* Modules 5-7: our own part-group classification, subcategories, and unbought demand.
 *
 * ARCHITECTURE NOTE: the builder serialises each `render` function into the page, so a
 * render function must be SELF-CONTAINED. Colour constants and helpers used only by a
 * render live inside it.
 *
 * Chart forms:
 *   5. rank of revenue at risk     -> horizontal bars per own top-level group
 *      trajectory of a share       -> change bars
 *   6. rank inside a hierarchy     -> horizontal bars with the other-brand split
 *      why the gap exists          -> a capped donut, 3 gap types
 *   7. where demand was unbilled   -> horizontal bars, euro led, with units as support
 *
 * Vintages differ between these panels and are printed on the face of each: the part-group
 * mix is a CY2025 sales-to-dealer file, the trajectory is CY2023 to CY2026 billing, and the
 * gap typing is a CY2026 model with no history.
 */
import {
  banner, barRows, donut, esc, fmtEur, fmtEurExact, fmtInt, fmtPct, fmtPP, kpis, pill, table,
} from "../charts.mjs";

/* ================================================= 5. part-group risk (own taxonomy) */
export const aim = {
  id: "aim",
  title: "Part-group risk",
  render(ctx) {
    const { L } = ctx;
    const rows = ctx.rowsOf("aim") || [];
    if (!rows.length) return banner("No market selected.", "info");

    const block = (r) => {
      if (r.unavailable) {
        return `<h3>${esc(ctx.dbName(r.db))}</h3>${banner(esc(r.unavailable), "amber")}`;
      }
      const ys = r.years || [];
      const y25 = ys.find((y) => y.year === 2025) || ys[ys.length - 1] || {};

      const famRows = (r.families || []).filter((f) => f.high_risk_eur).map((f) => ({
        label: f.family,
        value: f.high_risk_eur,
        display: fmtEur(f.high_risk_eur),
        sub: `${fmtPct(f.high_risk_pct)} of ${fmtEur(f.total_eur)}`,
        ref: f.network_median_pct,
        cls: (f.vs_network_pp ?? 0) > 0 ? "neg" : "alt",
        tip: `${f.family}: ${fmtEur(f.high_risk_eur)} of ${fmtEur(f.total_eur)} sits in the part groups most likely to be replaced by another brand, which is ${fmtPct(f.high_risk_pct)}. The same-type market median is ${fmtPct(f.network_median_pct)}, so this market is ${fmtPP(f.vs_network_pp)} against it.`,
      }));

      const groupRows = (r.groups || []).slice(0, 12).map((g) => ({
        label: g.group, value: g.eur, display: fmtEur(g.eur),
        sub: r.group_total_eur ? `${fmtPct((g.eur / r.group_total_eur) * 100)} of parts value` : null,
        cls: (g.bvp_eur || 0) > (g.genuine_only_eur || 0) ? "neg" : "alt",
        tip: g.bvp_eur !== null && g.bvp_eur !== undefined
          ? `${g.group}: ${fmtEur(g.eur)} of parts value. Our brand only ${fmtEur(g.genuine_only_eur)}, our brand where another brand also fits ${fmtEur(g.genuine_contested_eur)}, another brand ${fmtEur(g.bvp_eur)}.`
          : `${g.group}: ${fmtEur(g.eur)} of parts value.`,
      }));

      const riskTrend = ys.filter((y) => y.high_risk_pct !== null && y.high_risk_pct !== undefined)
        .map((y, n, arr) => {
          const prev = arr[n - 1];
          const v = prev ? (y.high_risk_pct - prev.high_risk_pct) : y.high_risk_pct;
          return { label: y.year === ctx.payload.meta.current_year ? `${y.year} YTD` : String(y.year),
                   value: v, display: fmtPP(v) };
        });

      const cards = kpis([
        { label: L.term.highRisk, value: fmtEur(y25.high_risk_eur), small: true, dark: true,
          sub: `CY2025, ${fmtPct(y25.high_risk_pct)} of parts value`,
          tip: "Parts value in the groups most likely to be taken by another brand, based on our own part-group classification." },
        { label: "Part-group match", value: fmtPct(y25.match_rate_pct),
          sub: "of value classified",
          tip: "The share of parts value we could place in our own part-group classification. Unclassified value cannot be counted as at risk." },
        { label: "Protected value", value: fmtEur(y25.strategic_eur), small: true,
          sub: "in groups we are likely to keep",
          tip: "Parts value in groups where we are the natural source." },
        { label: "Risk position", value: (r.aim_risk_percentile === null || r.aim_risk_percentile === undefined)
            ? "–" : `${Math.round(r.aim_risk_percentile)}th of 100`,
          sub: "higher means more revenue in at-risk groups",
          tip: "Where this market sits against the others on the share of its revenue in the part groups most likely to be replaced by another brand. A high position means more of the book is exposed than in most markets." },
      ]);

      return `<h3>${esc(ctx.dbName(r.db))}${
        r.db === ctx.focus ? ` ${pill("this market", "info")}` : ""}</h3>
      ${cards}
      <h4>Revenue at risk, by part family</h4>
      ${famRows.length ? barRows(famRows, {
        legend: [
          { color: "var(--terra)", label: "More exposed than comparable markets" },
          { color: "var(--navy-3)", label: "Less exposed" },
          { color: "var(--navy)", label: "Reference: same-type market median exposure" },
        ] }) : `<p class="empty">No family-level risk for this market.</p>`}
      <p class="note">The bar is euro, not a percentage. The percentage underneath is the share of
        that family's value sitting in at-risk groups, and the marker is the median across comparable
        markets, so the bar can be read as above or below normal.</p>
      <div class="cols2">
        <div><h4>Parts value by our own top-level group</h4>
          ${groupRows.length ? barRows(groupRows.slice(0, 8), {
            legend: [
              { color: "var(--navy-3)", label: "Our brand is the larger part of the group" },
              { color: "var(--terra)", label: "Other brands are the larger part" },
            ] })
            : banner("No group-level mix for this market. The part-group mix comes from a sales-to-dealer file, which exists for six markets only, so the revenue-at-risk figures above are shown without a group breakdown here.", "amber")}
          ${groupRows.length ? `<p class="note">${esc(L.msg.vintage(ctx.payload.modules.aim.group_vintage))}</p>` : ""}</div>
        <div><h4>Movement in the at-risk share</h4>
          ${riskTrend.length ? barRows(riskTrend, {
            legend: [{ color: "var(--terra)", label: "Change in percentage points" }] })
            : `<p class="empty">Not enough years.</p>`}
          <p class="note">${esc(L.msg.vintage(ctx.payload.modules.aim.trajectory_vintage))} A positive
            bar means a larger share of the book sits in groups we are less likely to keep.</p></div>
      </div>
      ${(r.groups || []).length > 8 ? `<h4>All ${r.groups.length} part groups</h4>
      ${table([{ label: "Part group" }, { label: "Parts value", num: true },
               { label: "Our brand only", num: true }, { label: "Rival also fits", num: true },
               { label: "Other brand", num: true }],
        r.groups.map((g) => ({ cells: [
          { text: g.group, lbl: true }, { text: fmtEur(g.eur) },
          { text: fmtEur(g.genuine_only_eur) }, { text: fmtEur(g.genuine_contested_eur) },
          { text: fmtEur(g.bvp_eur) }] })),
        { foot: [{ text: "Total" }, { text: fmtEur(r.group_total_eur) }, { text: "" },
                 { text: "" }, { text: "" }] })}` : ""}`;
    };

    return `<p class="q">${esc(L.q.aim)}</p>
      <div class="stack">${rows.map(block).join("")}</div>
      <p class="note">This section uses our own part-group classification, not the service-family
        model. The two answer different questions: service families say whether the fleet's routine
        service demand was captured, part groups say where the value sits and how exposed it is.</p>`;
  },
};

/* ======================================================= 6. subcategories */
export const subgroup = {
  id: "subgroup",
  title: "Subcategories",
  render(ctx) {
    const { L } = ctx;
    const HIGH = "#c0552d";
    const MID = "#b98a52";
    const NEUTRAL = "#7f93b5";

    const rows = ctx.rowsOf("subgroup") || [];
    if (!rows.length) return banner("No market selected.", "info");

    const block = (r) => {
      if (r.unavailable) {
        return `<h3>${esc(ctx.dbName(r.db))}</h3>${banner(esc(r.unavailable), "amber")}`;
      }
      const groups = (r.groups || []).filter((g) => g.total_eur);
      const top = groups.slice(0, 12);

      const subRows = top.map((g) => ({
        label: g.subgroup,
        value: g.total_eur,
        display: fmtEur(g.total_eur),
        sub: (g.bvp_share_pct === null || g.bvp_share_pct === undefined)
          ? null : `${fmtPct(g.bvp_share_pct)} other brand`,
        cls: (g.bvp_share_pct ?? 0) > 50 ? "neg" : "alt",
        tip: `${g.subgroup}: ${fmtEur(g.total_eur)} of parts value. Other brands hold ${fmtPct(g.bvp_share_pct)} of units. ${fmtInt(g.bvp_only_pairs)} part pairings are bought only as another brand, against ${fmtInt(g.genuine_only_pairs)} bought only as our brand.`,
      }));

      const gapSegs = (r.gap_types || []).map((g, n) => ({
        label: g.label, value: g.eur, color: [HIGH, MID, NEUTRAL][n] || NEUTRAL,
      })).filter((s) => s.value > 0);
      const gapTotal = gapSegs.reduce((a, s) => a + s.value, 0);

      const pairRows = top.filter((g) => g.genuine_only_pairs || g.bvp_only_pairs).map((g) => ({
        label: g.subgroup,
        value: g.bvp_only_pairs || 0,
        display: fmtInt(g.bvp_only_pairs),
        sub: `${fmtInt(g.genuine_only_pairs)} our brand only`,
        cls: "neg",
        tip: `${g.subgroup}: ${fmtInt(g.bvp_only_pairs)} part pairings are bought only as another brand, against ${fmtInt(g.genuine_only_pairs)} bought only as our brand.`,
      }));

      const cards = kpis([
        { label: "Other-brand share", value: fmtPct(r.metric_bvp_share_pct), dark: true,
          sub: "of units, CY2025",
          tip: "The share of parts units billed as a brand other than the vehicle manufacturer's own." },
        { label: "Subcategories with trade", value: fmtInt(groups.length), sub: "in CY2025",
          tip: "The number of subcategories where this market billed anything in CY2025." },
        { label: "Unbought value typed", value: fmtEur(gapTotal), small: true,
          sub: ctx.payload.modules.subgroup.gap_vintage,
          tip: "Unbought service-part value the model was able to attribute to a cause." },
      ]);

      return `<h3>${esc(ctx.dbName(r.db))}${
        r.db === ctx.focus ? ` ${pill("this market", "info")}` : ""}</h3>
      ${cards}
      <h4>Parts value, and how contested each subcategory is</h4>
      ${subRows.length ? barRows(subRows, {
        legend: [
          { color: "var(--navy-3)", label: "Other brands below half of units" },
          { color: "var(--terra)", label: "Other brands above half" },
        ] }) : `<p class="empty">No subcategory trade for this market.</p>`}
      <div class="cols2">
        <div><h4>Why the unbought value is unbought</h4>
          ${gapSegs.length ? donut(gapSegs, {
            center: { value: fmtEur(gapTotal), label: "TYPED GAP" },
            aria: "Unbought value by cause" })
            : `<p class="empty">No typed gap for this market.</p>`}
          <p class="note">${esc(L.msg.vintage(ctx.payload.modules.subgroup.gap_vintage))}. Each cause
            needs a different response, which is why they are separated rather than summed.</p></div>
        <div><h4>Subcategories where another brand is the only purchase</h4>
          ${pairRows.length ? barRows(pairRows.slice(0, 8), {
            legend: [{ color: "var(--terra)", label: "Part pairings bought only as another brand" }] })
            : `<p class="empty">No such subcategory.</p>`}
          <p class="note">A pairing is a part number and the part that fits the same vehicle. Where a
            pairing is only ever bought as another brand, our route is not being chosen at all in
            that subcategory.</p></div>
      </div>
      ${(r.top_gaps || []).length ? `<h4>Largest single unbought lines</h4>
      ${table([
        { label: L.term.serviceFamily }, { label: "Cause" }, { label: "Unbought value", num: true },
        { label: "Units", num: true }, { label: "Captured", num: true }],
        r.top_gaps.map((g) => ({ cells: [
          { text: g.category, lbl: true }, { text: g.label }, { text: fmtEur(g.eur) },
          { text: fmtInt(g.gap_units) }, { text: fmtPct(g.capture_pct) }] })),
        { caption: `Largest unbought lines, ${ctx.payload.modules.subgroup.gap_vintage}` })}` : ""}`;
    };

    return `<p class="q">${esc(L.q.subgroup)}</p>
      <div class="stack">${rows.map(block).join("")}</div>`;
  },
};

/* ===================================================== 7. unbought demand */
export const unbilled = {
  id: "unbilled",
  title: "Unbought demand",
  render(ctx) {
    const { L } = ctx;
    const rows = ctx.rowsOf("unbilled") || [];
    if (!rows.length) return banner("No market selected.", "info");

    const block = (r) => {
      if (r.unavailable) {
        return `<h3>${esc(ctx.dbName(r.db))}</h3>${banner(esc(r.unavailable), "amber")}`;
      }
      const fams = (r.families || []).filter((f) => f.gap_eur);
      const withContext = fams.map((f) => ({
        ...f, per_truck: (r.uio && f.gap_eur) ? f.gap_eur / r.uio : null,
      }));

      const gapRows = withContext.slice(0, 12).map((f) => ({
        label: f.category,
        value: f.gap_eur,
        display: fmtEur(f.gap_eur),
        sub: (f.capture_pct === null || f.capture_pct === undefined)
          ? null : `${fmtPct(f.capture_pct)} captured of ${fmtInt(f.expected_qty)} expected`,
        cls: (f.capture_pct ?? 100) < 40 ? "neg" : "alt",
        tip: `${f.category}: ${fmtEur(f.gap_eur)} of unbought service-part value on ${fmtInt(f.unbought_qty)} units the fleet's service schedule implies were needed but were not billed for. Captured ${fmtPct(f.capture_pct)} of expected demand. Expected value on this family is ${fmtEur(f.tam_eur)}.`,
      }));

      const perTruckRows = withContext.filter((f) => f.per_truck).slice(0, 12).map((f) => ({
        label: f.category,
        value: f.per_truck,
        display: fmtEurExact(f.per_truck),
        sub: `per vehicle, ${fmtEur(f.gap_eur)} total`,
        cls: "alt",
        tip: `${f.category}: ${fmtEurExact(f.per_truck)} of unbought value for every vehicle in service in this market. That is the comparable form, because a large absolute gap in a large fleet is not the same as a large gap per vehicle.`,
      }));

      const totalGap = withContext.reduce((a, f) => a + (f.gap_eur || 0), 0);
      const cards = kpis([
        { label: L.term.gap, value: fmtEur(totalGap), small: true, dark: true,
          sub: "unbought service-part value, CY2025",
          tip: "The value of service parts the fleet's schedule implies were needed but that were not billed, valued at the observed average price." },
        { label: L.term.fleet, value: fmtInt(r.uio), sub: "vehicles in service",
          tip: "The denominator. The same absolute gap means opposite things in a large and a small fleet." },
        { label: "Gap per vehicle", value: (r.uio && totalGap) ? fmtEurExact(totalGap / r.uio) : "–",
          sub: "unbought value per vehicle in service",
          tip: "Total unbought value divided by vehicles in service, which is the form that can be compared across markets of different size." },
        { label: "Largest family", value: withContext[0] ? fmtEur(withContext[0].gap_eur) : "–",
          sub: withContext[0] ? withContext[0].category : null, small: true,
          tip: "The service family carrying the largest share of the unbought value." },
      ]);

      return `<h3>${esc(ctx.dbName(r.db))}${
        r.db === ctx.focus ? ` ${pill("this market", "info")}` : ""}</h3>
      ${cards}
      <h4>Unbought service-part value, by service family</h4>
      ${gapRows.length ? barRows(gapRows, {
        legend: [
          { color: "var(--terra)", label: "Captured under 40% of expected demand" },
          { color: "var(--navy-3)", label: "Captured 40% or more" },
        ] }) : `<p class="empty">No unbought value for this market.</p>`}
      <h4>The same gap, per vehicle in service</h4>
      ${perTruckRows.length ? barRows(perTruckRows, {
        legend: [{ color: "var(--navy-3)", label: "Unbought value per vehicle in service" }] })
        : `<p class="empty">No fleet base for this market.</p>`}
      <p class="note">${esc(L.msg.unitsNeedContext)} The per-vehicle form is the one to compare
        across markets: a large absolute gap in a large fleet is not the same problem as a large gap
        per vehicle.</p>
      <h4>Expected demand against what was billed</h4>
      ${table([
        { label: L.term.serviceFamily }, { label: "Captured", num: true },
        { label: "Expected", num: true }, { label: "Billed", num: true },
        { label: "Not billed", num: true }, { label: "Average price", num: true },
        { label: "Value", num: true }],
        withContext.map((f) => ({ cells: [
          { text: f.category, lbl: true }, { text: fmtPct(f.capture_pct) },
          { text: fmtInt(f.expected_qty) }, { text: fmtInt(f.actual_qty) },
          { text: fmtInt(f.unbought_qty) }, { text: fmtEurExact(f.avg_price_eur) },
          { text: fmtEur(f.gap_eur) }] })),
        { foot: [{ text: "Total" }, { text: "" },
                 { text: fmtInt(withContext.reduce((a, f) => a + (f.expected_qty || 0), 0)) },
                 { text: fmtInt(withContext.reduce((a, f) => a + (f.actual_qty || 0), 0)) },
                 { text: fmtInt(withContext.reduce((a, f) => a + (f.unbought_qty || 0), 0)) },
                 { text: "" }, { text: fmtEur(totalGap) }],
          caption: "Units are shown so the euro can be checked, never on their own." })}`;
    };

    return `<p class="q">${esc(L.q.unbilled)}</p>
      <div class="stack">${rows.map(block).join("")}</div>`;
  },
};
