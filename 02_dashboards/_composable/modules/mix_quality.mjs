/* Module: Mix quality — genuine vs Best Value inside captured demand
 *
 * BVP is retention inside our channel, not leakage. Aftermarket walk-out is a
 * different measure and is not in this file.
 *
 * Grain: calendar year × distributor × product group (mix_genuine_bvp_by_group.csv).
 */

function splitCsvLine(line) {
  const out = [];
  let cur = "",
    q = false;
  for (let i = 0; i < line.length; i++) {
    const ch = line[i];
    if (q) {
      if (ch === '"' && line[i + 1] === '"') {
        cur += '"';
        i++;
      } else if (ch === '"') q = false;
      else cur += ch;
    } else if (ch === '"') q = true;
    else if (ch === ",") {
      out.push(cur);
      cur = "";
    } else cur += ch;
  }
  out.push(cur);
  return out;
}

function num(s) {
  if (s == null || String(s).trim() === "") return 0;
  const n = Number(s);
  return Number.isFinite(n) ? n : 0;
}

export default {
  id: "mix_quality",
  title: "Mix — genuine vs Best Value",
  audience: ["internal", "customer"],
  grain: "year",
  source: "01_data/00_derived/mix_genuine_bvp_by_group.csv",
  dbField: "distributor_code",
  internalOnlyFields: ["substitution_flag"],

  parse(csvText) {
    const lines = csvText.replace(/^\uFEFF/, "").trim().split(/\r?\n/);
    const cols = splitCsvLine(lines[0]);
    return lines.slice(1).filter(Boolean).map((line) => {
      const v = splitCsvLine(line);
      const r = {};
      cols.forEach((c, i) => (r[c] = v[i] ?? ""));
      return {
        period: String(r.year).replace(/\.0$/, ""),
        year: Number(String(r.year).replace(/\.0$/, "")),
        distributor_code: r.distributor_code,
        product_group: r.product_group,
        group_label: r.product_group_label || r.product_group,
        genuine_eur: num(r.genuine_eur),
        bvp_eur: num(r.bvp_eur),
        total_eur: num(r.total_eur),
        genuine_qty: num(r.genuine_qty),
        bvp_qty: num(r.bvp_qty),
        substitution_flag: r.substitution_flag || "",
      };
    });
  },

  initialState: { year: "2025" },

  onEvent(ev, state) {
    const t = ev.target.closest("[data-act]");
    if (!t) return false;
    if (t.dataset.act === "year") {
      state.year = t.value;
      return true;
    }
    return false;
  },

  clientRender: function renderMixInternal(rows, ctx) {
    const years = [...new Set(rows.map((r) => r.year))].sort((a, b) => a - b);
    const yKey = String(ctx.state.year || "2025");
    const view = rows.filter((r) => String(r.year) === yKey && ctx.inSelection(r._db));
    const yearOpts = years
      .map((y) => `<option value="${y}" ${String(y) === yKey ? "selected" : ""}>CY${y}</option>`)
      .join("");

    const genuine = view.reduce((s, r) => s + r.genuine_eur, 0);
    const bvp = view.reduce((s, r) => s + r.bvp_eur, 0);
    const total = genuine + bvp;
    const share = total ? bvp / total : 0;

    const byG = new Map();
    for (const r of view) {
      const k = r.group_label;
      if (!byG.has(k)) byG.set(k, { label: k, genuine_eur: 0, bvp_eur: 0, total_eur: 0 });
      const g = byG.get(k);
      g.genuine_eur += r.genuine_eur;
      g.bvp_eur += r.bvp_eur;
      g.total_eur += r.total_eur;
    }
    const groups = [...byG.values()].sort((a, b) => b.total_eur - a.total_eur);
    const shown = groups.slice(0, 6);
    const maxTot = Math.max(1, ...shown.map((g) => g.total_eur));

    const CHART_H = 168;
    const bars = shown
      .map((g) => {
        const h = Math.max(8, (g.total_eur / maxTot) * CHART_H);
        const genPct = g.total_eur ? (g.genuine_eur / g.total_eur) * 100 : 0;
        const bvpPct = 100 - genPct;
        const short = g.label.replace(/ & .*$/, "");
        return `<div class="bar-col" title="${g.label}: genuine ${ctx.eur(g.genuine_eur)} · BVP ${ctx.eur(g.bvp_eur)}">
          <div class="stack" style="height:${h}px">
            <div style="height:${bvpPct}%;background:#7fc9ad"></div>
            <div style="height:${genPct}%;background:#15233c"></div>
          </div>
          <span class="bar-lbl">${short}</span>
        </div>`;
      })
      .join("");

    const body = groups
      .map((g) => {
        const sh = g.total_eur ? g.bvp_eur / g.total_eur : 0;
        return `<tr>
          <td>${g.label}</td>
          <td class="num">${ctx.eur(g.genuine_eur)}</td>
          <td class="num">${ctx.eur(g.bvp_eur)}</td>
          <td class="num">${ctx.eur(g.total_eur)}</td>
          <td class="num">${ctx.pct(sh)}</td>
        </tr>`;
      })
      .join("");

    const y26 =
      yKey === "2026"
        ? `<p class="warn">CY2026 in this file is a <strong>partial year</strong> (invoiced-to-date). Do not read it as a full-year mix shift versus CY2025.</p>`
        : "";

    const grainExtra =
      ctx.period === "month" || ctx.period === "quarter"
        ? `<p class="warn">This source is <strong>calendar year</strong>. Month / quarter mix is not in the file and is not fabricated.</p>`
        : "";

    return `
      <p class="sub">Inside the demand we already capture: navy is genuine, green is Best Value. Both stay in our channel. Aftermarket walk-out is a different number — never added here.</p>
      ${ctx.grainWarning(ctx, "calendar year")}
      ${grainExtra}
      ${y26}
      <div class="pickbar">
        <div class="pick-lbl">Calendar year</div>
        <select data-act="year">${yearOpts}</select>
        <span class="sel-note">${ctx.selectedDbs.length ? ctx.selectedDbs.length + " distributor(s)" : "network"}</span>
      </div>
      <div class="kpi-row">
        <div class="kpi" data-tip="genuine_eur + bvp_eur for this selection and calendar year. This is mix inside captured demand, not capture rate and not GPS%.">
          <span class="kpi-lbl">Captured mix</span><span class="kpi-val">${ctx.eur(total)}</span>
          <span class="kpi-sub">CY${yKey} · ${groups.length} group(s)</span></div>
        <div class="kpi" data-tip="Genuine euros inside captured demand. Premium line — still our channel.">
          <span class="kpi-lbl">Genuine</span><span class="kpi-val">${ctx.eur(genuine)}</span></div>
        <div class="kpi" data-tip="Best Value euros inside captured demand. Retention against the aftermarket, not leakage. Down-trade and walk-out are never summed as one euro.">
          <span class="kpi-lbl">Best Value</span><span class="kpi-val">${ctx.eur(bvp)}</span>
          <span class="kpi-sub">${ctx.pct(share)} of this mix</span></div>
      </div>
      <p class="mixleg"><i style="background:#15233c"></i>Genuine <i style="background:#7fc9ad"></i>Best Value — both inside our tent. Top 6 groups by euro.</p>
      <div class="bars">${bars || `<p class="empty">No mix rows for this selection.</p>`}</div>
      <table class="tbl">
        <thead><tr>
          <th>Product group</th>
          <th class="num">Genuine</th>
          <th class="num">Best Value</th>
          <th class="num">Total</th>
          <th class="num">BVP share</th>
        </tr></thead>
        <tbody>${body || `<tr><td colspan="5" class="empty">No rows.</td></tr>`}</tbody>
      </table>
      <p class="note">BVP share is Best Value ÷ (genuine + Best Value) in this view. It is a gross-profit-quality read, not a capture read.</p>
    `;
  },

  clientRenderCustomer: function renderMixCustomer(rows, ctx) {
    const years = [...new Set(rows.map((r) => r.year))].sort((a, b) => a - b);
    const yKey = String(ctx.state.year || "2025");
    const focus = ctx.focusDistributor ? String(ctx.focusDistributor).toUpperCase() : "";
    const yearOpts = years
      .map((y) => `<option value="${y}" ${String(y) === yKey ? "selected" : ""}>CY${y}</option>`)
      .join("");
    if (!focus) {
      return `<p class="warn">No focus distributor set. Build with <code>--audience=customer --focus=&lt;DB&gt;</code>.</p>`;
    }
    const me = rows.filter(
      (r) => String(r.year) === yKey && String(r._db || r.distributor_code).toUpperCase() === focus
    );
    if (!me.length) {
      return `<p class="warn">No mix rows for <strong>${focus}</strong> in CY${yKey}.</p>`;
    }
    const genuine = me.reduce((s, r) => s + r.genuine_eur, 0);
    const bvp = me.reduce((s, r) => s + r.bvp_eur, 0);
    const total = genuine + bvp;
    const net = rows.filter((r) => String(r.year) === yKey);
    const netTot = net.reduce((s, r) => s + r.genuine_eur + r.bvp_eur, 0);
    const netBvp = net.reduce((s, r) => s + r.bvp_eur, 0);
    const netShare = netTot ? netBvp / netTot : 0;
    const y26 =
      yKey === "2026"
        ? `<p class="warn">CY2026 is invoiced-to-date, not a full year. Do not read it as a completed mix shift.</p>`
        : "";

    const byG = new Map();
    for (const r of me) {
      const k = r.group_label;
      if (!byG.has(k)) byG.set(k, { label: k, genuine_eur: 0, bvp_eur: 0, total_eur: 0 });
      const g = byG.get(k);
      g.genuine_eur += r.genuine_eur;
      g.bvp_eur += r.bvp_eur;
      g.total_eur += r.total_eur;
    }
    const groups = [...byG.values()].sort((a, b) => b.total_eur - a.total_eur);
    const body = groups
      .map((g) => {
        const sh = g.total_eur ? g.bvp_eur / g.total_eur : 0;
        return `<tr>
          <td>${g.label}</td>
          <td class="num">${ctx.eur(g.genuine_eur)}</td>
          <td class="num">${ctx.eur(g.bvp_eur)}</td>
          <td class="num">${ctx.pct(sh)}</td>
        </tr>`;
      })
      .join("");

    return `
      <p class="sub">Your genuine vs Best Value split. Best Value is still your channel — it is not a lost sale to the aftermarket.</p>
      ${y26}
      <div class="pickbar"><div class="pick-lbl">Calendar year</div><select data-act="year">${yearOpts}</select></div>
      <div class="kpi-row">
        <div class="kpi" data-tip="Your invoiced genuine + Best Value in this calendar year. Mix inside what you already sell, not a capture rate.">
          <span class="kpi-lbl">Your captured mix</span><span class="kpi-val">${ctx.eur(total)}</span>
          <span class="kpi-sub">${focus} · CY${yKey}</span></div>
        <div class="kpi" data-tip="Best Value share of your captured mix. Network share is an aggregate only — other distributors are not listed.">
          <span class="kpi-lbl">Your Best Value share</span><span class="kpi-val">${ctx.pct(total ? bvp / total : 0)}</span>
          <span class="kpi-sub">network ${ctx.pct(netShare)}</span></div>
      </div>
      <table class="tbl">
        <thead><tr><th>Your product group</th><th class="num">Genuine</th><th class="num">Best Value</th><th class="num">BVP share</th></tr></thead>
        <tbody>${body}</tbody>
      </table>
    `;
  },
};
