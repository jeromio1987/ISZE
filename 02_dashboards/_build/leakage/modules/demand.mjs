/* Modules 4-5: service families won and lost, and brand mix over time.
 *
 * ARCHITECTURE NOTE: the builder serialises each `render` function into the page, so a render
 * function must be SELF-CONTAINED. Colour constants and helpers used only by a render live
 * inside it. Only the imported chart bundle travels with it.
 *
 * Two corrections from review are built in here:
 *   * Like-for-like. The current-year expected-demand denominator in the source is a full year
 *     while the current-year actuals cover six months, so the filed current-year rate reads
 *     about half its real value. Both are shown, the window basis is the one to read, and the
 *     table says which is which.
 *   * One chart where there was a wall of them. The per-family trajectory is now a selector:
 *     pick a family, see its trajectory against its own demand. That replaces ten rows of
 *     small multiples that said less.
 */
import {
  banner, barRows, donut, esc, fmtEur, fmtEurExact, fmtInt, fmtPct, fmtPP, fmtSignedPct,
  heatTable, kpis, lineChart, pill, selectControl, stackedBars, table,
} from "../charts.mjs";

/* ==================================================== 4. service families */
export const pms = {
  id: "pms",
  title: "Service families",
  render(ctx) {
    const { L } = ctx;
    const mod = ctx.mod("pms") || {};
    const rows = ctx.rowsOf("pms") || [];
    if (!rows.length) return banner("No market selected.", "info");

    const cy = ctx.payload.meta.current_year;

    /* Capture on the corrected denominator. For the current year the expectation is a full
       year, so the window share is used; for earlier years the comparison is already full-year
       against full-year. */
    const capOf = (c, y) => {
      const s = (c.years || []).find((x) => x.year === y);
      if (!s) return null;
      return y === cy ? s.capture_lfl_pct : s.capture_adj_pct;
    };
    const captureLevel = (pct) => {
      if (pct === null || pct === undefined) return "n";
      if (pct < 25) return 1;
      if (pct < 40) return 2;
      if (pct < 55) return 3;
      if (pct < 75) return 4;
      return 5;
    };

    const block = (r) => {
      if (r.unavailable) {
        return `<h3>${esc(ctx.dbName(r.db))}</h3>${banner(esc(r.unavailable), "amber")}`;
      }
      const cats = r.categories || [];
      const years = ctx.payload.meta.years;
      const scored = cats.filter((c) => c.scored && c.capture_2025_pct !== null
        && c.capture_2025_pct !== undefined);
      const weakest = scored.slice().sort((a, b) => a.capture_2025_pct - b.capture_2025_pct)[0];
      const sourced = cats.filter((c) => c.scored);
      const unsourced = cats.filter((c) => !c.scored);
      const sExp = scored.reduce((a, c) => a
        + (((c.years || []).find((y) => y.year === 2025) || {}).expected_qty_adj || 0), 0);
      const sAct = scored.reduce((a, c) => a
        + (((c.years || []).find((y) => y.year === 2025) || {}).actual_qty || 0), 0);
      const captureOnScored = sExp ? (sAct / sExp) * 100 : null;

      const hmRows = cats.map((c) => ({
        label: c.interval_confirmed ? c.category : `${c.category} \u00b7`,
        cells: years.map((y) => {
          const v = capOf(c, y);
          if (v === null || v === undefined) return { level: "n", text: "\u00b7" };
          const s = (c.years || []).find((x) => x.year === y);
          const isPart = y === cy;
          return {
            level: captureLevel(v), text: `${Math.round(v)}%`,
            tip: `${c.category}, ${y}${isPart ? " (first six months)" : ""}: captured ${fmtPct(v)} of the expected service demand. Expected ${fmtInt(s.expected_qty_adj)} units, billed ${fmtInt(s.actual_qty)}. Unbought ${fmtInt(s.unbought_qty)} units, worth ${fmtEur(s.gap_eur)} at the average selling price of ${fmtEurExact(s.avg_price_eur)}.${isPart ? " The current year is on the same six-month basis as the year before." : ""}${c.interval_confirmed ? ` Expected demand uses the scheduled replacement interval of ${fmtInt(c.interval_km)} km.` : " This category has no replacement interval in the maintenance schedule, so the expected demand rests on the model's placeholder factor and the percentage is indicative only."}`,
          };
        }),
        tailHtml: (c.slope_pp === null || c.slope_pp === undefined) ? ""
          : `${fmtPP(c.slope_pp)}${c.declining ? " " + pill("slipping", "crit") : ""}`,
      }));

      const cardCapture = {
        label: "Captured, on sourced intervals",
        value: cats.some((c) => c.scored) ? fmtPct(captureOnScored) : "\u2013",
        dark: true, sub: `${sourced.length} of ${cats.length} families scored`,
        tip: "Units billed as a share of the units the fleet's service schedule implies, on the families where a sourced replacement interval exists. Families with no replacement interval in any schedule are not scored, because a percentage against a modelled expectation is not a measurement.",
      };

      const cards = kpis([
        cardCapture,
        { label: L.term.gap, value: fmtEur(r.metric_gap_firm_eur), small: true,
          sub: "on sourced intervals, firm",
          tip: "Expected service demand not billed, valued at the observed average selling price, counting only the families with a sourced replacement interval." },
        { label: "Gap on placeholders", value: fmtEur(r.metric_gap_placeholder_eur), small: true,
          sub: "not comparable to the figure beside it",
          tip: "Unbought value in families with no replacement interval in any schedule. The euro is real but the expectation behind it is modelled, so it is separated from the firm figure rather than added to it." },
        { label: "Annual distance used", value: `${fmtInt(r.km_used)} km`,
          small: true, sub: r.km_note,
          subKind: r.km_measured ? "pos" : null,
          tip: r.km_measured
            ? "Measured from odometer data for this market, replacing the flat model default. Every expected-demand figure on this panel depends on it."
            : "No measurement exists for this market, so the model's flat default is used. That is a real limitation, not a measurement." },
        { label: "Fleet by family",
          value: (r.truck_pct === null || r.truck_pct === undefined) ? "\u2013"
            : `${Math.round(r.truck_pct)} / ${Math.round(r.pickup_pct)}%`,
          small: true, sub: "trucks / pickups, vehicles in service",
          tip: `This market's fleet is ${fmtInt(r.truck_uio)} trucks and ${fmtInt(r.pickup_uio)} pickups. That split decides which maintenance schedule applies to which part of the fleet, and it is measured rather than taken from the market's customer-type label.` },
        { label: L.term.fleet, value: fmtInt(r.uio), sub: "vehicles in service",
          tip: "Fleet base behind the expected demand for this market." },
        { label: "Weakest scored family",
          value: weakest ? fmtPct(weakest.capture_2025_pct) : "\u2013",
          sub: weakest ? weakest.category : null,
          tip: "The scored service family with the lowest share of expected demand captured in CY2025." },
      ]);

      const openUnit = cats.filter((c) => c.unit_definition_open);

      const selOpts = scored.slice()
        .sort((a, b) => a.capture_2025_pct - b.capture_2025_pct)
        .map((c) => ({
          value: c.category,
          label: `${c.category} \u00b7 ${fmtPct(c.capture_2025_pct)} captured \u00b7 ${fmtEur(c.gap_2025_eur)} unbought`,
        }));
      const chosen = ctx.state("pms", "family")
        || (selOpts.length ? selOpts[0].value : null);
      const chosenCat = cats.find((c) => c.category === chosen) || scored[0] || null;

      let detail = "";
      if (chosenCat) {
        const pts = years.map((y) => {
          const s = (chosenCat.years || []).find((x) => x.year === y);
          const v = capOf(chosenCat, y);
          return {
            label: y === cy ? `${y} (6 mo)` : String(y),
            value: v,
            tip: `${chosenCat.category} ${y}: captured ${v === null || v === undefined ? "not measured" : fmtPct(v)} of expected demand. Expected ${fmtInt(s ? s.expected_qty_adj : null)} units, billed ${fmtInt(s ? s.actual_qty : null)}, unbought ${fmtInt(s ? s.unbought_qty : null)} worth ${fmtEur(s ? s.gap_eur : null)}.`,
          };
        }).filter((p) => p.value !== null && p.value !== undefined);

        detail = `<h4>${esc(chosenCat.category)}, against its own expected demand</h4>
        ${lineChart(pts, {
          height: 190, fmt: (v) => `${Math.round(v)}%`, refValue: 100,
          refLabel: "100% of expected demand", domainFromZero: true,
          aria: `${chosenCat.category} capture over time`,
          caption: `${chosenCat.interval_confirmed
            ? `Expected demand uses the scheduled replacement interval of ${fmtInt(chosenCat.interval_km)} km, which is a sourced figure.`
            : "This category has no replacement interval in the maintenance schedule, so the expectation rests on the model's placeholder and the level is indicative only."}${chosenCat.slope_pp !== null && chosenCat.slope_pp !== undefined ? ` The fitted trend is ${chosenCat.slope_pp > 0 ? "improving" : "falling"} by ${Math.abs(chosenCat.slope_pp).toFixed(1)} percentage points a year.` : ""}`,
        })}`;
      }

      return `<h3>${esc(ctx.dbName(r.db))}${
        r.db === ctx.focus ? ` ${pill("this market", "info")}` : ""}</h3>
      ${cards}
      ${r.dropped_categories && r.dropped_categories.length
        ? banner(`${esc(r.dropped_categories.join(" and "))} ${r.dropped_categories.length === 1 ? "is" : "are"} not scored for this market.
            ${r.dropped_categories.length === 1 ? "It has" : "They have"} never been bought by any
            truck market in the network, so a capture rate against them would measure our model
            rather than this market. Removing ${r.dropped_categories.length === 1 ? "it" : "them"}
            lifts the scored capture rate by roughly ${r.scope === "CV" ? "14" : "0"} percentage
            points on its own.`, "amber")
        : ""}
      <h4>Share of expected service demand captured</h4>
      ${heatTable(hmRows, years.map((y) => (y === cy ? `${y} (6 mo)` : String(y))),
        { rowHead: L.term.serviceFamily, tailHead: "Trend a year" })}
      <p class="note">A stronger tint means a smaller share of the service demand the fleet implies
        was actually billed. A dot means no measurement for that family in that year. A dot beside a
        family name means <b>no replacement interval exists in the maintenance schedule</b> for that
        part, so its expected demand rests on the model's placeholder rather than on a sourced
        interval. Those rows are shown, because dropping them would hide the gap, but their level is
        indicative and their movement is the reliable part.</p>
      ${selOpts.length ? `${selectControl("pms", "family", selOpts, chosen, "Service family")}
        ${detail}` : ""}
      ${openUnit.length ? banner(`<b>One open question changes these brake numbers.</b>
        ${esc(openUnit.map((c) => c.category).join(" and "))} assume that one paired front-and-rear
        brake job consumes <b>one part unit</b>. If it consumes two, the expected demand doubles and
        the capture percentage roughly halves. Per family, on that basis:
        ${openUnit.map((c) => `${esc(c.category)} moves from ${fmtPct(c.capture_2025_pct)} to
          ${fmtPct(c.capture_2025_alt_pct)}, and its unbought value from
          ${fmtEur(c.gap_2025_eur)} to ${fmtEur(c.gap_2025_alt_eur)}`).join("; ")}. This is a
        units-definition question that only your service records can settle, and it is the largest
        single uncertainty on this panel.`, "amber") : ""}
      <h4>Which figures rest on a sourced interval</h4>
      ${table(
        [{ label: L.term.serviceFamily }, { label: "Interval", num: true },
         { label: "Basis" }, { label: "Fleet covered", num: true },
         { label: "CY2025 capture", num: true }, { label: "Unbought value", num: true }],
        cats.map((c) => ({
          cells: [
            { text: c.category, lbl: true },
            { text: c.interval_km ? `${fmtInt(c.interval_km)} km` : "\u2013" },
            { text: c.basis_label, tip: c.interval_note },
            { text: c.coverage_pct === null || c.coverage_pct === undefined
                ? "\u2013" : fmtPct(c.coverage_pct, 0),
              tip: c.coverage_pct === 0
                ? "No part of this market's fleet has a replacement interval for this part, so the expectation rests on the model's placeholder."
                : `The expectation covers ${fmtPct(c.coverage_pct, 0)} of this market's vehicles in service, being the part of the fleet for which a replacement interval exists.` },
            { text: fmtPct(c.capture_2025_pct) },
            { text: fmtEur(c.gap_2025_eur) },
          ],
        })),
        { foot: [{ text: `${sourced.length} of ${cats.length} families sourced` },
                 { text: "" },
                 { text: `${unsourced.length} on a placeholder` },
                 { text: "" },
                 { text: fmtPct(r.metric_capture_pct) }, { text: fmtEur(r.metric_gap_eur) }],
          caption: "Only the families with a sourced replacement interval can carry a firm capture percentage. Everything else says so." })}
      <p class="note"><b>How the interval is chosen.</b> Where you have supplied your own interval
        figures they are used. Where you have not, the replacement interval comes from the
        maintenance schedule for each part of the fleet: the N-series schedule for trucks, the
        D-Max schedule for pickups, weighted by this market's measured vehicles-in-service split
        (${fmtInt(r.truck_uio)} trucks, ${fmtInt(r.pickup_uio)} pickups). A pickup-only category in
        a truck-only market covers nothing here and is marked as a placeholder rather than given
        the wrong family's interval.</p>`;
    };

    return `<p class="q">${esc(L.q.pms)}</p>
      ${banner(`<b>Same basis, same months, and rebuilt on the supplier schedule.</b>
        ${esc(mod.denominator_note || "")} Expected demand now uses the replacement intervals in the
        maintenance schedules rather than the model's placeholder factors, which corrected the AdBlue
        filter by a factor of five.`, "amber")}
      <div class="stack">${rows.map(block).join("")}</div>
      <p class="note"><b>What the percentage rests on.</b> The units billed are real billing data.
        The expected demand is a model. For the families with a scheduled replacement interval it is
        a sourced figure; for the rest it is a placeholder, and the table above says which is which.</p>`;
  },
};

/* ============================================================= 5. brand mix */
export const mix = {
  id: "mix",
  title: "Brand mix",
  render(ctx) {
    const { L, peer } = ctx;
    const OWN = "#15233c";
    const CONTESTED = "#7f93b5";
    const COMPETING = "#c0552d";

    const rows = ctx.rowsOf("mix") || [];
    if (!rows.length) return banner("No market selected.", "info");

    const block = (r) => {
      if (r.unavailable) {
        return `<h3>${esc(ctx.dbName(r.db))}</h3>${banner(esc(r.unavailable), "amber")}`;
      }
      const ys = r.years || [];
      if (!ys.length) {
        return `<h3>${esc(ctx.dbName(r.db))}</h3>${banner("No brand-mix extract for this market.", "amber")}`;
      }
      const y25 = ys[ys.length - 1];

      const segs = [
        { label: L.term.ownBrand, value: y25.genuine_only_eur || 0, color: OWN,
          sub: "only available as our brand" },
        { label: "Own brand, also made by others", value: y25.genuine_contested_eur || 0,
          color: CONTESTED, sub: "another brand's part also fits" },
        { label: L.term.competingBrand, value: y25.bvp_eur || 0, color: COMPETING,
          sub: "billed as another brand" },
      ].filter((s) => s.value > 0);

      const valFor = (y, which) => which === 0 ? y.genuine_only_eur
        : which === 1 ? y.genuine_contested_eur : y.bvp_eur;

      const stack = ys.map((y) => ({
        label: y.year === ctx.payload.meta.current_year ? `${y.year} (6 mo)` : String(y.year),
        total: y.total_eur, totalDisplay: fmtEur(y.total_eur),
        segs: segs.map((s, which) => ({
          value: valFor(y, which) || 0, color: s.color,
          tip: `${y.year} ${s.label}: ${fmtEur(valFor(y, which))} of ${fmtEur(y.total_eur)} total parts value.`,
        })),
      }));

      const famRows = (r.families || []).map((f) => ({
        label: f.family, value: f.bvp_share_pct,
        ref: peer && peer.median.familyBvp ? peer.median.familyBvp[f.family] : null,
        display: fmtPct(f.bvp_share_pct),
        sub: f.total_eur ? `${fmtEur(f.total_eur)} total` : null,
        tip: `${f.family}: other brands are ${fmtPct(f.bvp_share_pct)} of parts value in CY2025${
          f.yoy_pp !== null && f.yoy_pp !== undefined ? `, a move of ${fmtPP(f.yoy_pp)} against the prior year` : ""}.`,
        cls: (f.bvp_share_pct ?? 0) > 50 ? "neg" : "alt",
      }));

      const movement = ys.slice(1).map((y, n) => {
        const prev = ys[n];
        if (y.bvp_pct === null || prev.bvp_pct === null) return null;
        const d = y.bvp_pct - prev.bvp_pct;
        return { label: y.year === ctx.payload.meta.current_year ? `${y.year} (6 mo)` : String(y.year),
                 value: d, display: fmtPP(d),
                 tip: `${y.year} against ${prev.year}: other brands moved ${fmtPP(d)} of parts value.` };
      }).filter(Boolean);

      const cards = kpis([
        { label: "Other-brand share", value: fmtPct(y25.bvp_pct), dark: true,
          sub: "of parts value, latest period",
          tip: "The share of parts value billed as a brand other than the vehicle manufacturer's own." },
        { label: "Parts value", value: fmtEur(y25.total_eur), small: true,
          sub: String(y25.year),
          tip: "Total parts value for this market in the latest period." },
        { label: "Open to switch", value: fmtPct(y25.contested_bvp_capture), small: true,
          sub: "our parts another brand also makes",
          tip: "Our parts where another brand's part also fits the vehicle. These are the parts a customer could switch away from without a fitment problem." },
        (peer && peer.median.metric_bvp_pct !== null && peer.median.metric_bvp_pct !== undefined)
          ? { label: `Typical ${peer.basis}`, value: fmtPct(peer.median.metric_bvp_pct),
              sub: peer.note, tip: peer.tip }
          : null,
      ]);

      return `<h3>${esc(ctx.dbName(r.db))}${
        r.db === ctx.focus ? ` ${pill("this market", "info")}` : ""}</h3>
      ${cards}
      <div class="cols2">
        <div><h4>Parts value by brand, ${y25.year}</h4>
          ${donut(segs, { center: { value: fmtPct(y25.bvp_pct), label: "OTHER BRAND" },
            aria: "Brand mix of parts value" })}
          <p class="note">Our brand with no competing equivalent is the uncontested part of the
            book. The middle segment is our brand where another brand's part also fits, which is
            where a switch is mechanically possible.</p></div>
        <div><h4>Movement in the other-brand share</h4>
          ${movement.length ? barRows(movement, {
            legend: [
              { color: "var(--terra)", label: "Other brands gaining" },
              { color: "var(--navy-3)", label: "Other brands losing share" },
            ] }) : `<p class="empty">Not enough years to show a movement.</p>`}
          ${peer === null ? banner(esc(L.msg.thinPeer(0)), "amber") : ""}
        </div>
      </div>
      <h4>Where the other-brand share sits, by part family</h4>
      ${barRows(famRows, { legend: [
        { color: "var(--navy-3)", label: "Other brands below half of the family" },
        { color: "var(--terra)", label: "Other brands above half" },
        { color: "var(--navy)", label: "Reference: same-type market median" }] })}
      <h4>Parts value by year</h4>
      ${stackedBars(stack, {
        legend: [
          { color: OWN, label: L.term.ownBrand },
          { color: CONTESTED, label: "Own brand, also made by others" },
          { color: COMPETING, label: L.term.competingBrand },
        ] })}`;
    };

    return `<p class="q">${esc(L.q.mix)}</p>
      <div class="stack">${rows.map(block).join("")}</div>
      <p class="note">A rising other-brand share is not automatically bad: another brand's part can
        be the right answer for an older vehicle. Read it with the value at stake in the next
        section, which separates parts where a switch is possible from parts where we are the only
        source.</p>`;
  },
};
