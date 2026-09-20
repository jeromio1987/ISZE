/* Module 8: partner league - INTERNAL ONLY.
 *
 * This module declares `audience: ["internal"]`, so the builder never compiles its render
 * source into a customer file. That is stronger than hiding it with CSS: the code and the
 * field names are absent from the customer artefact.
 *
 * ARCHITECTURE NOTE: the builder serialises the render function into the page, so it must be
 * SELF-CONTAINED. Helpers live inside it.
 *
 * Chart forms:
 *   who is critical        -> ranked bars on the composite risk score
 *   evidence per partner   -> a dense table, because the reader here is us
 * The module prints its own calibration caveat and splits recoverable stopped-ordering from
 * categories whose trailing revenue is already zero.
 */
import {
  banner, barRows, esc, fmtEur, fmtInt, fmtPct, kpis, pill, table,
} from "../charts.mjs";

export default {
  id: "league",
  title: "Partner league",
  audience: ["internal"],
  render(ctx) {
    const { L } = ctx;
    const mod = ctx.mod("league") || {};
    const rows = ctx.rowsOf("league") || [];
    if (!rows.length) return banner("No market selected.", "info");

    const txt = (v) => (v === null || v === undefined ? "–" : fmtInt(v));

    const ranked = rows.filter((r) => r.risk_score !== null && r.risk_score !== undefined)
      .sort((a, b) => (b.risk_score || 0) - (a.risk_score || 0));

    const barData = ranked.map((r) => ({
      label: ctx.dbName(r.db),
      value: r.risk_score,
      display: (r.risk_score ?? 0).toFixed(3),
      sub: `${fmtEur(r.gap_eur)} gap, ${fmtPct(r.gps_pct)} of ceiling`,
      cls: (r.risk_score ?? 0) > 0.5 ? "neg" : ((r.risk_score ?? 0) > 0.3 ? "" : "alt"),
      tip: `Composite risk ${(r.risk_score ?? 0).toFixed(3)} for ${ctx.dbName(r.db)}. Built from price undercut exposure, share of value in at-risk part groups, competing-brand capture in contested parts and urgent-order share. Fleet ${fmtInt(r.uio)} vehicles, reachable gap ${fmtEur(r.gap_eur)}.`,
    }));

    const totals = ranked.reduce((a, r) => ({
      gap: a.gap + (r.gap_eur || 0),
      exposed: a.exposed + (r.ew_eur_exposed || 0),
      undercut: a.undercut + (r.undercut_eur || 0),
    }), { gap: 0, exposed: 0, undercut: 0 });

    const cards = kpis([
      { label: "Critical markets",
        value: String(ranked.filter((r) => (r.risk_score ?? 0) > 0.5).length),
        dark: true, sub: `of ${ranked.length} with a risk score`,
        tip: "Markets whose composite risk score is above 0.5. The score combines price undercut exposure, part-group risk, competing-brand capture and urgent-order share." },
      { label: "Reachable gap", value: fmtEur(totals.gap), small: true,
        sub: "across the selected markets",
        tip: "The reachable part of the target spend ceiling that was not billed." },
      { label: "Euro flagged early", value: fmtEur(totals.exposed), small: true,
        sub: "in the early-warning register",
        tip: "Value exposed across the signals in the early-warning register: order silence, capture decline and urgent-order behaviour." },
      { label: "Undercut revenue", value: fmtEur(totals.undercut), small: true,
        sub: "where a rival price is below ours",
        tip: "Revenue exposed to a competing price below ours, from the competitor price survey." },
    ]);

    const body = ranked.map((r, n) => ({
      cls: n < 3 ? "focus" : "",
      cells: [
        { text: String(n + 1), lbl: true },
        { text: ctx.dbName(r.db), lbl: true,
          tip: `${ctx.dbName(r.db)} · ${(ctx.dbInfo(r.db) || {}).scope || ""} · ${(ctx.dbInfo(r.db) || {}).region || ""}` },
        { text: (r.risk_score ?? 0).toFixed(3) },
        { text: fmtEur(r.gap_eur) },
        { text: fmtPct(r.gps_pct) },
        { text: fmtInt(r.uio) },
        { text: r.ew_severity === null || r.ew_severity === undefined ? "–" : String(r.ew_severity),
          tip: r.ew_why || "No early-warning signal for this market." },
        { text: fmtEur(r.ew_eur_exposed) },
        { text: txt(r.defection_categories) },
        { text: fmtEur(r.defection_recoverable_eur),
          tip: "Value in categories that stopped ordering while the distributor still trades other parts. This is the recoverable part." },
        { text: fmtEur(r.defection_zero_revenue_eur, 0),
          tip: "Categories whose trailing revenue is already zero. This is not recoverable and is deliberately not counted as an opportunity." },
        { text: r.health_alert || "–" },
        { text: r.health_reasons || "" },
      ],
    }));

    const dormant = ranked.filter((r) => r.ew_all_dormant).length;

    return `<p class="q">${esc(L.q.league)}</p>
      ${mod.threshold_note ? banner(`<b>${esc(mod.threshold_note)}</b>`, "amber") : ""}
      ${cards}
      <h4>Composite risk, ranked</h4>
      ${barRows(barData, {
        legend: [
          { color: "var(--terra)", label: "Risk score above 0.5" },
          { color: "var(--navy-3)", label: "Risk score at or below 0.5" },
        ] })}
      <p class="note">The score is a ranking device, not a measurement. It orders markets by how much
        evidence of pressure sits on them, which is what makes it useful for deciding where to spend a
        conversation. It is not a probability and it is not comparable across years.</p>
      <h4>Evidence behind the ranking</h4>
      ${table([
        { label: "#" }, { label: "Market" }, { label: "Risk", num: true },
        { label: "Gap", num: true }, { label: "Ceiling billed", num: true }, { label: "Fleet", num: true },
        { label: "EW sev", num: true }, { label: "Euro flagged", num: true },
        { label: "Dormant cat.", num: true }, { label: "Recoverable", num: true },
        { label: "Zero revenue", num: true }, { label: "Account alert" }, { label: "Reason" }],
        body,
        { caption: "Dealer network health, early warning and stopped-ordering status for the selected markets." })}
      <p class="note"><b>How to read the last four columns.</b> Early-warning severity counts the
        signals firing for a market. "Recoverable" is value in categories that stopped ordering while
        the distributor still buys other parts, so it can in principle be won back. "Zero revenue" is
        categories whose trailing revenue is already nothing: that is a closure, not an opportunity,
        and it is shown separately so it cannot inflate the opportunity total.</p>
      ${mod.defection_note ? `<p class="note">${esc(mod.defection_note)}</p>` : ""}
      ${dormant ? banner(`<b>Context for the risk column.</b> ${dormant} market${dormant === 1 ? " has" : "s have"}
        all early-warning signals dormant, which tells you the data has gone quiet rather than that
        the market is healthy. Those rows are listed rather than scored as safe.`, "info") : ""}`;
  },
};
