/* Module: DB comparison vs peer groups
 * Select any distributors, benchmark them against a peer group.
 *
 * Peer group membership (CV / LCV / mixed) is NOT guessed — it comes from the
 * `scope` field of the live GPS dashboard's embedded DUAL dataset, which is the
 * authoritative CV/LCV classification per DB.
 *
 * Audience:
 *   internal — full table, all DBs by name, revenue gap included
 *   customer — focus DB + peer-group aggregates only. No competitor rows at all
 *              (so no anonymised "Distributor B" placeholders).
 */

const SCOPE = {
  ITUK: "CV", UTI: "CV",
  IUK: "LCV", UMI: "LCV", NORWAY: "LCV", SWEDEN: "LCV", DENMARK: "LCV",
  FINLAND: "LCV", ICELAND: "LCV", ROMANIA: "LCV", HUNGARY: "LCV",
  GERMANY: "MIXED", BELGIUM: "MIXED", IRELAND: "MIXED", CYPRUS: "MIXED",
  GREECE: "MIXED", MALTA: "MIXED", PORTUGAL: "MIXED",
};

const NORDICS = ["NORWAY", "SWEDEN", "DENMARK", "FINLAND", "ICELAND"];

// CIS is declared but has no members in the current source. It is shown as
// unavailable rather than silently omitted or filled with non-CIS DBs.
const CIS = [];

export const PEER_GROUPS = {
  network: { label: "Network average", match: () => true },
  cv: { label: "CV customers", match: (d) => SCOPE[d] === "CV" },
  mixed: { label: "Mixed (CV + LCV)", match: (d) => SCOPE[d] === "MIXED" },
  lcv: { label: "LCV customers", match: (d) => SCOPE[d] === "LCV" },
  nordics: { label: "Nordics", match: (d) => NORDICS.includes(d) },
  cis: {
    label: "CIS countries",
    match: (d) => CIS.includes(d),
    unavailable: "No CIS distributor present in pms_summary_by_db.csv",
  },
};

/* Resolved at BUILD time into plain member arrays, so the client never needs the
 * match closures (which reference module-level constants that don't exist in the browser). */
export function resolvePeerGroups(rows) {
  const dbs = rows.map((r) => r.distributor);
  const out = {};
  for (const [k, g] of Object.entries(PEER_GROUPS)) {
    out[k] = { label: g.label, members: dbs.filter(g.match) };
    if (g.unavailable) out[k].unavailable = g.unavailable;
  }
  return out;
}

export default {
  id: "db_compare",
  title: "Capture — PMS",
  audience: ["internal", "customer"],
  grain: "year",
  source: "01_data/00_derived/pms_summary_by_db.csv",
  dbField: "distributor", // resolved to canonical _db by the shell
  internalOnlyFields: ["revenue_gap_eur", "top_gap_categories"],

  parse(csvText) {
    const [header, ...lines] = csvText.trim().split(/\r?\n/);
    const cols = header.split(",");
    return lines.filter(Boolean).map((line) => {
      const v = line.split(",");
      const row = {};
      cols.forEach((c, i) => (row[c] = v[i]));
      return {
        period: row.year,
        distributor: row.distributor_code,
        scope: SCOPE[row.distributor_code] || "?",
        uio_units: Number(row.uio_units),
        capture_total: Number(row.capture_rate_total_wtd),
        capture_genuine: Number(row.capture_rate_genuine_wtd),
        oil_filter_capture: Number(row.oil_filter_capture),
        revenue_gap_eur: Number(row.revenue_gap_eur_sum),
        top_gap_categories: row.top_gap_categories,
      };
    });
  },

  clientRender: function renderCompareInternal(rows, ctx) {
    const peer = ctx.peer;
    const peerRows = rows.filter((r) => ctx.inPeer(r._db));
    const sel = rows
      .filter((r) => ctx.inSelection(r._db))
      .sort((a, b) => b.capture_total - a.capture_total);

    const avg = (xs, k) => (xs.length ? xs.reduce((s, r) => s + r[k], 0) / xs.length : 0);
    const wavg = (xs, k) => {
      const u = xs.reduce((s, r) => s + r.uio_units, 0);
      return u ? xs.reduce((s, r) => s + r[k] * r.uio_units, 0) / u : 0;
    };

    const peerNote = peer.unavailable
      ? `<p class="warn"><strong>${peer.label}</strong> — ${peer.unavailable}. No benchmark can be computed; pick another peer group.</p>`
      : peerRows.length === 0
        ? `<p class="warn"><strong>${peer.label}</strong> has ${peer.members.length} member(s), but none appear in the PMS capture extract (18 of 22 network distributors). No benchmark shown.</p>`
        : "";

    const pAvg = avg(peerRows, "capture_total");
    const pWavg = wavg(peerRows, "capture_total");
    // Selected DBs that are themselves members of the benchmark group.
    const overlap = sel.map((r) => r._db).filter((d) => ctx.inPeer(d));

    const body = sel.length
      ? sel
          .map((r) => {
            const d = r.capture_total - pAvg;
            const sign = d >= 0 ? "pos" : "neg";
            return `<tr>
            <td><strong>${r.distributor}</strong></td>
            <td>${r.scope}</td>
            <td class="num">${r.uio_units.toLocaleString("en-GB")}</td>
            <td class="num">${ctx.pct(r.capture_total)}</td>
            <td class="num">${ctx.pct(r.capture_genuine)}</td>
            <td class="num">${ctx.pct(r.oil_filter_capture)}</td>
            <td class="num ${sign}">${ctx.pp(d)}</td>
            <td class="num">${ctx.eur(r.revenue_gap_eur)}</td>
            <td class="cats">${String(r.top_gap_categories || "—").replace(/\|/g, " · ")}</td>
          </tr>`;
          })
          .join("")
      : ctx.selectedDbs.length
        ? `<tr><td colspan="9" class="empty">${ctx.selectedDbs.length} distributor(s) selected
           (${ctx.selectedDbs.join(", ")}), but none appear in the PMS capture extract.
           Ukraine, Armenia, Kazakhstan and Palestine have no PMS capture rows.</td></tr>`
      : `<tr><td colspan="9" class="empty">No capture rows for this selection. PMS covers 18 of 22 network distributors — CIS and Palestine have no rows here.</td></tr>`;

    return `
      ${ctx.grainWarning(ctx, "year")}
      ${peerNote}
      <div class="kpi-row">
        <div class="kpi" data-tip="Unweighted mean of capture_rate_total_wtd across distributors in the benchmark group that appear in the PMS extract (18 of 22 network DBs)."><span class="kpi-lbl">${peer.label} — avg across DBs</span><span class="kpi-val">${ctx.pct(pAvg)}</span><span class="kpi-sub">${peerRows.length} DB(s), unweighted</span></div>
        <div class="kpi" data-tip="Same capture rates weighted by UIO units in that extract. Not spend-weighted. Ukraine, Armenia, Kazakhstan and Palestine have no PMS rows."><span class="kpi-lbl">${peer.label} — UIO-weighted</span><span class="kpi-val">${ctx.pct(pWavg)}</span><span class="kpi-sub">weighted by UIO units</span></div>
        <div class="kpi" data-tip="How many of the picker selection exist in this PMS file."><span class="kpi-lbl">Selected</span><span class="kpi-val">${sel.length}</span></div>
      </div>
      <table class="tbl">
        <thead><tr>
          <th>Distributor</th><th>Scope</th><th class="num">UIO</th>
          <th class="num">Capture total</th><th class="num">Capture genuine</th>
          <th class="num">Oil filter</th><th class="num">vs ${peer.label}</th>
          <th class="num">Revenue gap</th><th>Top gap categories</th>
        </tr></thead>
        <tbody>${body}</tbody>
      </table>
      ${
        overlap.length
          ? `<p class="note"><strong>Note:</strong> ${overlap.join(", ")} ${overlap.length === 1 ? "is" : "are"} part of
             the “${peer.label}” group (${peerRows.length} DB${peerRows.length === 1 ? "" : "s"}), so
             ${overlap.length === 1 ? "it is" : "they are"} being compared against an average that includes
             ${overlap.length === 1 ? "itself" : "themselves"}. With a small group this makes the delta
             mechanically symmetric — read it as position within the group, not as a gap to an
             independent benchmark.</p>`
          : ""
      }
      <p class="note">Delta is vs the <em>unweighted</em> peer average. Neither average is
      spend-weighted — the source carries UIO units and the revenue gap, but not addressable
      spend, so a true spend-weighted benchmark cannot be computed from this file.</p>
    `;
  },

  // Customer view: the focus DB against peer-group averages. No competitor rows,
  // named or anonymised.
  clientRenderCustomer: function renderCompareCustomer(rows, ctx) {
    const G = ctx.peerGroups;
    const focus = String(ctx.focusDistributor || "").toUpperCase();
    const me = focus ? rows.find((r) => String(r._db).toUpperCase() === focus) : null;

    if (!me) {
      return `<p class="warn">No focus distributor set. Build with
        <code>--audience=customer --focus=&lt;DB&gt;</code> to produce a customer view.</p>`;
    }

    const avg = (xs, k) => (xs.length ? xs.reduce((s, r) => s + r[k], 0) / xs.length : 0);

    const cards = Object.entries(G)
      .map(([k, g]) => {
        const members = rows.filter((r) => g.members.includes(r._db));
        if (g.unavailable || !members.length) return "";
        const a = avg(members, "capture_total");
        const d = me.capture_total - a;
        const sign = d >= 0 ? "pos" : "neg";
        return `<tr>
          <td>${g.label}</td>
          <td class="num">${members.length}</td>
          <td class="num">${ctx.pct(a)}</td>
          <td class="num ${sign}">${ctx.pp(d)}</td>
        </tr>`;
      })
      .filter(Boolean)
      .join("");

    return `
      ${ctx.grainWarning(ctx, "year")}
      <div class="kpi-row">
        <div class="kpi"><span class="kpi-lbl">${me.distributor} — capture total</span><span class="kpi-val">${ctx.pct(me.capture_total)}</span></div>
        <div class="kpi"><span class="kpi-lbl">Capture genuine</span><span class="kpi-val">${ctx.pct(me.capture_genuine)}</span></div>
        <div class="kpi"><span class="kpi-lbl">Oil filter</span><span class="kpi-val">${ctx.pct(me.oil_filter_capture)}</span></div>
        <div class="kpi"><span class="kpi-lbl">UIO</span><span class="kpi-val">${me.uio_units.toLocaleString("en-GB")}</span></div>
      </div>
      <table class="tbl">
        <thead><tr><th>Benchmark</th><th class="num">DBs in group</th>
          <th class="num">Group average</th><th class="num">${me.distributor} vs group</th></tr></thead>
        <tbody>${cards}</tbody>
      </table>
      <p class="note">Group averages are unweighted means across the distributors in each
      group. Individual distributor figures are not shown.</p>
    `;
  },
};
