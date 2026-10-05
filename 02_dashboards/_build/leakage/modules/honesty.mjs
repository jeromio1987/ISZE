/* Module 9: what this page does not claim.
 *
 * Every figure here is re-derived from the derived layer on the build date, never copied
 * from a previous review. This module is the reason a reader can trust the rest of the
 * page: it states the assumptions the numbers rest on, in plain business English, and it
 * puts the fleet base and the model vintage beside every claim.
 *
 * Scope counts are restated per audience by the builder, so a pack for one distributor
 * never describes how many markets exist or which of them are scored.
 */
import { banner, esc, fmtEur, fmtInt, fmtPct, kpis, pill, table } from "../charts.mjs";

export default {
  id: "honesty",
  title: "What this does not claim",
  render(ctx) {
    const { L } = ctx;
    const h = ctx.mod("honesty") || {};
    const sc = h.scope || {};
    const v = h.verification || { pass: 0, fail: 0, generated_at: "" };
    const isCustomer = ctx.audience === "customer";
    const mileage = h.mileage || { model_default_km: 20000, measured: [], spread_note: "" };

    const cards = kpis([
      { label: "Figures rebuilt", value: h.as_of, dark: true,
        sub: "every number re-derived on this date",
        tip: "Nothing on this page is copied from an earlier review. All figures are recomputed from the approved derived layer on this date." },
      { label: "Data checks", value: `${v.pass} passed`,
        sub: v.fail ? `${v.fail} failing` : "no failures",
        subKind: v.fail ? "neg" : "pos",
        tip: "The workspace verification report must be clean before this page is built. A failing check stops the build." },
      { label: isCustomer ? "Service families measured" : "Markets scored",
        value: isCustomer ? fmtInt(sc.captured_cells) : fmtInt(sc.scored_markets_n),
        sub: isCustomer ? "in CY2025" : `of ${fmtInt(sc.network_markets_n)} in the network`,
        tip: "How much of the service-family model is populated for this view." },
      { label: "Capture above 100%", value: fmtInt(sc.over_100), small: true,
        sub: `of ${fmtInt(sc.captured_cells)} measurements`,
        tip: "Measurements where the model says this market captured more demand than the model expected. That means the assumed demand is too low, not that the market over-performs." },
    ]);

    const mileageRows = (mileage.measured || []).map((m) => ({
      cells: [
        { text: m.key, lbl: true },
        { text: `${fmtInt(m.km)} km`, tip: m.note },
        { text: m.source },
      ],
    }));

    /* Dealer coverage: the whole network internally, this market alone in a pack. */
    const dealerCodes = isCustomer ? [ctx.focus] : ctx.networkDbs;
    const coverageFor = (code) => (h.dealer_coverage || {})[code] || null;
    const focusHasDetail = !!(coverageFor(ctx.focus) || {}).has_dealer_detail;
    const dealerRows = dealerCodes.map((code) => {
      const rec = coverageFor(code);
      const has = !!(rec && rec.has_dealer_detail);
      return {
        cells: [
          { text: ctx.dbName(code), lbl: true },
          { text: ctx.dbInfo(code)?.scope || "–" },
          { text: has ? `${fmtInt(rec.max_dealers)} outlets` : "–",
            tip: has ? "Dealer outlet detail is available for this market."
                     : "No dealer outlet file for this market." },
          { text: rec && rec.named_years && rec.named_years.length
            ? rec.named_years.join(", ") : "national total only" },
          { html: has ? pill("dealer detail", "ok") : pill("national only", "mute") },
        ],
      };
    });

    return `<p class="q">${esc(L.q.honesty)}</p>
      ${cards}

      <h4>Distance travelled</h4>
      <p class="sub">Every spend-per-vehicle figure on this page depends on how far the fleet
        drives. The model applies a single flat ${fmtInt(mileage.model_default_km)} km a year to
        every market.</p>
      <p class="note">${esc(mileage.spread_note)}</p>
      ${mileageRows.length
        ? table([{ label: "Fleet" }, { label: "Measured", num: true }, { label: "Source" }],
            mileageRows,
            { caption: "Measured annual distance where a sample exists, against the flat model assumption." })
        : `<p class="note">Where a measured sample exists in our own service records, the model's
            flat assumption is replaced for that fleet. Those figures are not shown here because
            they identify other markets, and our internal settings are not yours to hold.</p>`}

      <h4>Service demand is modelled, not measured</h4>
      ${banner(`<b>${fmtInt(sc.over_100)} of ${fmtInt(sc.captured_cells)}</b> service-family
        measurements on this page read above 100% captured. That means the assumed demand is too
        low for ${sc.over_100 === 1 ? "that family" : "those families"}, not that the market
        over-performs. ${esc(h.expected_demand_note)}`, "amber")}

      <h4>How the target spend figure is built</h4>
      <p class="note">${esc(h.gps_denominator_note)}</p>
      <p class="note">${esc(h.settings_note)}</p>

      <h4>Dealer-level detail</h4>
      <p class="sub">${isCustomer
        ? (focusHasDetail
            ? "Dealer outlet detail is available for this market from your sales-to-dealer file, so this page can be read as a network view."
            : "This market's detail stops at the national total. No dealer outlet file exists, so no network view is shown rather than an implied one.")
        : "Dealer outlet detail exists for some markets and not others. Where it is absent, the national number is shown and labelled rather than implying a network view."}</p>
      ${table([{ label: "Market" }, { label: "Customer type" }, { label: "Outlet detail", num: true },
               { label: "Years with names" }, { label: "Status" }],
        dealerRows,
        { caption: isCustomer ? "What detail exists for this market."
                              : "Where a network view is possible, and where it is not." })}

      <h4>Other limits you should know about</h4>
      <dl class="dl">
        <dt>${esc(L.honesty.vintage)}</dt>
        <dd>${esc(h.gap_vintage)}</dd>

        <dt>${esc(L.honesty.mix)}</dt>
        <dd>${esc(h.mix_note)}</dd>

        <dt>${esc(L.honesty.scope)}</dt>
        <dd>${isCustomer
          ? esc(`Service-family demand is modelled from service records, which not every market has. Where a family is not measured, this page shows a dot rather than a zero, because a zero would read as a real answer and it is not one.`)
          : esc(`Service-family demand is modelled for ${fmtInt(sc.scored_markets_n)} of ${fmtInt(sc.network_markets_n)} markets. The rest have no service records and are not scored.`)}</dd>

        <dt>${esc(L.honesty.fleet)}</dt>
        <dd>${esc(h.uio_note || "–")}</dd>

        <dt>${esc(L.honesty.peer)}</dt>
        <dd>${esc(h.peer_rule)}</dd>

        <dt>Currency</dt>
        <dd>All figures in euro at the rate used by the approved extract. They are not
          exchange-rate adjusted between years.</dd>

        <dt>What this page is for</dt>
        <dd>A shared view of where parts revenue is won and lost, and where the value sits.
          It is not a quotation, an order forecast, or a commitment on pricing.</dd>
      </dl>

      <h4>Where the numbers come from</h4>
      <p class="note">Rebuilt ${esc(h.as_of)}. ${esc(h.sources_note)}
        Data checks dated ${esc(String(v.generated_at || "").slice(0, 10))}, showing
        ${fmtInt(v.pass)} passed and ${fmtInt(v.fail)} failed.
        ${sc.modelled_gap_eur && !isCustomer
          ? `Modelled unbought service-part value across the scored markets is ${fmtEur(sc.modelled_gap_eur)}.`
          : ""}</p>`;
  },
};
