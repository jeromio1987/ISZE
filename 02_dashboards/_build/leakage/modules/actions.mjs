/* Module 8: what to act on, at part-number level.
 *
 * This is the conclusions layer. The review asked for conclusions with part numbers, so every
 * line names a part, says what is happening to it, what it is worth, and what we propose to do.
 * A part with no description anywhere in the approved layers is shown by its group and flagged
 * rather than dropped or given an invented name.
 *
 * ARCHITECTURE NOTE: the builder serialises each `render` function into the page, so a render
 * function must be SELF-CONTAINED. Helpers live inside it.
 *
 * The panel is a short list, not a data dump: the top lines by value, grouped by what the
 * problem is, with the remainder behind a selector so the page stays readable.
 */
import {
  banner, barRows, esc, fmtEur, fmtEurExact, fmtInt, fmtPct, kpis, pill, selectControl, table,
} from "../charts.mjs";

export default {
  id: "actions",
  title: "What to act on",
  audience: ["internal", "customer"],
  render(ctx) {
    const { L } = ctx;
    const mod = ctx.mod("actions") || {};
    const rows = ctx.rowsOf("actions") || [];
    if (!rows.length) return banner("No market selected.", "info");

    const SHOW = 25;

    const block = (r) => {
      if (r.unavailable) {
        // A market with no PN actions still gets an explanation and this market's own value at
        // family level, so the panel is never a bare sentence. Another market's part numbers are
        // deliberately not shown: that would leak their detail even without naming them.
        const mine = (ctx.mod("unbilled").rows || []).find((x) => x.db === r.db);
        const fams = (mine && mine.families ? mine.families : [])
          .filter((f) => f.gap_eur).slice(0, 8);
        return `<h3>${esc(ctx.dbName(r.db))}</h3>
          ${banner(`No part-level actions have been worked up for this market yet, so there is no
            list of part numbers to show. That is a gap in our analysis, not a clean bill of health.
            What we can show is where the value sits at service-family level, which is the step
            before the part numbers.`, "amber")}
          ${fams.length ? `<h4>Where the value sits, by service family</h4>
            ${barRows(fams.map((f) => ({
              label: f.category, value: f.gap_eur, display: fmtEur(f.gap_eur),
              sub: `${fmtInt(f.unbought_qty)} units not billed`,
              cls: "alt",
              tip: `${f.category}: ${fmtEur(f.gap_eur)} of unbought service-part value on ${fmtInt(f.unbought_qty)} units the fleet's service schedule implies were needed. Captured ${fmtPct(f.capture_pct)} of expected demand.`,
            })), { legend: [
              { color: "var(--navy-3)", label: "Unbought value at service-family level" }] })}
            <p class="note">This is the family level, which is where a part-number list would come
              from. The part numbers behind these families are the work still to do for this
              market.</p>` : ""}`;
      }
      const lines = r.top || [];
      const groups = r.by_signal || [];

      const sigRows = groups.map((g) => ({
        label: g.label, value: g.eur, display: fmtEur(g.eur),
        sub: `${fmtInt(g.n)} part${g.n === 1 ? "" : "s"}`,
        cls: g.signal === "LEAKAGE" || g.signal === "REPLENISHMENT" ? "neg" : "alt",
        tip: `${g.label}: ${fmtInt(g.n)} parts, ${fmtEur(g.eur)} of value in the trailing period.`,
      }));

      const cards = kpis([
        { label: "Value in raised actions", value: fmtEur(r.metric_eur_at_stake), small: true, dark: true,
          sub: `${fmtInt(r.n_lines)} part lines`,
          tip: "The value tied up in the part-level actions raised for this market. This is the size of the conversation, not a promise of revenue." },
        { label: "Parts named", value: `${fmtInt(r.n_named)} of ${fmtInt(Math.min(SHOW, lines.length))}`,
          small: true, sub: "shown with a full description",
          tip: "Parts where an approved layer carries a description. A part without one is listed by its number and group rather than given a name we cannot source." },
        { label: "Largest single part",
          value: lines.length && lines[0].eur ? fmtEur(lines[0].eur) : "\u2013",
          small: true, sub: lines.length ? (lines[0].description || lines[0].pn) : null,
          tip: "The single largest part-level action by value in this market." },
      ]);

      // Selector: switch which consequence the list is sorted by, so the reader can look at
      // what is being lost, what is stocked wrong, or what has gone silent.
      const selOpts = groups.length > 1
        ? [{ value: "__all", label: `Everything, ranked by value (${fmtInt(r.n_lines)} parts)` }]
            .concat(groups.map((g) => ({
              value: g.signal,
              label: `${g.label} \u00b7 ${fmtInt(g.n)} parts \u00b7 ${fmtEur(g.eur)}`,
            })))
        : [];
      const chosen = ctx.state("actions", "view") || "__all";

      let shown = lines;
      if (chosen !== "__all") shown = lines.filter((l) => l.signal === chosen);
      shown = shown.slice(0, SHOW);

      const body = shown.map((l) => ({
        cells: [
          { text: l.pn, lbl: true,
            tip: `Part ${l.pn}${l.basis ? ` \u00b7 value basis ${l.basis}` : ""}${l.seen ? ` \u00b7 last seen ${l.seen}` : ""}` },
          { text: l.description || "\u2014",
            tip: l.description ? l.description
              : "No description in an approved layer for this part number. Shown as a number rather than given a name we cannot source." },
          { text: l.signal_label, tip: `Signal: ${l.signal}` },
          { text: fmtEur(l.eur) },
          { text: l.action || "\u2014" },
        ],
      }));

      return `<h3>${esc(ctx.dbName(r.db))}${
        r.db === ctx.focus ? ` ${pill("this market", "info")}` : ""}</h3>
      ${cards}
      <h4>What the value is tied up in</h4>
      ${sigRows.length ? barRows(sigRows, {
        legend: [
          { color: "var(--terra)", label: "Value at risk of being lost" },
          { color: "var(--navy-3)", label: "Value tied up in how we supply" },
        ] }) : `<p class="empty">No grouped actions for this market.</p>`}
      <p class="note">Every part below sits inside one of these groups. The groups are the short
        version: they say what kind of problem this market has, before the part numbers say where.</p>
      ${selOpts.length ? selectControl("actions", "view", selOpts, chosen, "Show") : ""}
      <h4>Part numbers, largest first</h4>
      ${body.length ? table(
        [{ label: "Part number" }, { label: "Description" }, { label: "What is happening" },
         { label: "Value", num: true }, { label: "Proposed action" }],
        body,
        { caption: `${esc(mod.basis_note || "")} ${shown.length < r.n_lines
            ? `Showing the largest ${shown.length} of ${fmtInt(r.n_lines)} lines for this market.`
            : `All ${fmtInt(r.n_lines)} lines shown.`}` })
        : `<p class="empty">Nothing raised for this market.</p>`}`;
    };

    const total = ctx.networkSum("actions", "metric_eur_at_stake");
    return `<p class="q">${esc(L.q.actions)}</p>
      ${banner(`<b>What this section is.</b> These are the part numbers the analysis says to talk
        about, with the value attached and what we propose to do. It is a conversation list, not a
        forecast: the value is what sits in those parts today, not what we expect to recover.`,
        "info")}
      <div class="stack">${rows.map(block).join("")}</div>
      ${ctx.audience === "customer" ? "" : `<p class="note">Across the selected markets,
        <b>${fmtEur(total)}</b> of value sits in raised part-level actions.</p>`}`;
  },
};
