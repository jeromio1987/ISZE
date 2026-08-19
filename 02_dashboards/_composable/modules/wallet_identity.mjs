/* Module: Wallet ceiling → captured → addressable gap
 *
 * Same identity the PRISM map chips use (wallet_waterfall.csv, calendar year).
 * Ceiling, not a forecast. Not the live GPS-dashboard %.
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
  const n = Number(s);
  return Number.isFinite(n) ? n : 0;
}

export default {
  id: "wallet_identity",
  title: "Wallet ceiling",
  audience: ["internal", "customer"],
  grain: "year",
  source: "01_data/00_derived/wallet_waterfall.csv",
  dbField: "distributor_code",
  internalOnlyFields: ["assumption_note", "over_target_eur", "structural_nonaddressable_eur"],

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
        uio_units: num(r.uio_units),
        wallet_eur: num(r.theoretical_wallet_eur),
        captured_genuine_eur: num(r.captured_genuine_eur),
        captured_bvp_eur: num(r.captured_bvp_eur),
        captured_total_eur: num(r.captured_total_eur),
        gap_eur: num(r.addressable_uncaptured_eur),
        over_target_eur: num(r.over_target_eur),
        structural_nonaddressable_eur: num(r.structural_nonaddressable_eur),
        assumption_note: r.assumption_note || "",
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

  clientRender: function renderWalletInternal(rows, ctx) {
    const years = [...new Set(rows.map((r) => r.year))].sort((a, b) => a - b);
    const yKey = String(ctx.state.year || years[years.length - 1]);
    const inSel = (r) => ctx.inSelection(r._db);
    const view = rows.filter((r) => String(r.year) === yKey && inSel(r));
    const sum = (k) => view.reduce((s, r) => s + (r[k] || 0), 0);
    const wallet = sum("wallet_eur");
    const captured = sum("captured_total_eur");
    const genuine = sum("captured_genuine_eur");
    const bvp = sum("captured_bvp_eur");
    const gap = sum("gap_eur");
    const uio = sum("uio_units");
    const share = wallet ? captured / wallet : 0;
    const maxBar = Math.max(wallet, 1);

    const yearOpts = years
      .map((y) => `<option value="${y}" ${String(y) === yKey ? "selected" : ""}>CY${y}</option>`)
      .join("");

    const sorted = view.slice().sort((a, b) => b.wallet_eur - a.wallet_eur);
    const body = sorted
      .map((r) => {
        const sh = r.wallet_eur ? r.captured_total_eur / r.wallet_eur : 0;
        return `<tr>
          <td><strong>${r._db || r.distributor_code}</strong></td>
          <td class="num">${Math.round(r.uio_units).toLocaleString("en-GB")}</td>
          <td class="num">${ctx.eur(r.wallet_eur)}</td>
          <td class="num">${ctx.eur(r.captured_total_eur)}</td>
          <td class="num">${ctx.eur(r.gap_eur)}</td>
          <td class="num">${ctx.pct(sh)}</td>
        </tr>`;
      })
      .join("");

    const grainExtra =
      ctx.period === "month" || ctx.period === "quarter"
        ? `<p class="warn">This source is <strong>calendar year</strong>. Month / quarter wallet is not in the file and is not fabricated — CY is shown.</p>`
        : "";

    return `
      <p class="sub">Parc × per-model target spend = the ceiling. Captured is invoiced through the authorised channel. The gap is still in play — not a loss already booked.</p>
      ${ctx.grainWarning(ctx, "calendar year")}
      ${grainExtra}
      <div class="pickbar">
        <div class="pick-lbl">Calendar year</div>
        <select data-act="year">${yearOpts}</select>
        <span class="sel-note">${ctx.selectedDbs.length ? ctx.selectedDbs.length + " distributor(s)" : "network"}</span>
      </div>
      <div class="kpi-row">
        <div class="kpi" data-tip="theoretical_wallet_eur summed for this selection. Parc × per-model GPS max-spend targets. Ceiling, not a forecast. Age-flat until IML's age-spend curve lands. Snapshot from wallet_waterfall.csv, CY${yKey}.">
          <span class="kpi-lbl">Wallet ceiling</span><span class="kpi-val">${ctx.eur(wallet)}</span>
          <span class="kpi-sub">CY${yKey} · ${view.length} market(s)</span></div>
        <div class="kpi" data-tip="captured_total_eur = genuine + Best Value invoiced. Both sit inside our channel. Aftermarket walk-out is not in this number.">
          <span class="kpi-lbl">Captured</span><span class="kpi-val">${ctx.eur(captured)}</span>
          <span class="kpi-sub">genuine ${ctx.eur(genuine)} · BVP ${ctx.eur(bvp)}</span></div>
        <div class="kpi" data-tip="addressable_uncaptured_eur. Identity: wallet → captured → gap. Over-target markets do not shrink someone else's gap.">
          <span class="kpi-lbl">Addressable gap</span><span class="kpi-val">${ctx.eur(gap)}</span>
          <span class="kpi-sub">${ctx.pct(share)} of ceiling captured</span></div>
        <div class="kpi" data-tip="uio_units as stored on wallet_waterfall for this year. This is the waterfall's parc, not a signed GPS denominator. No GPS% is computed from it here.">
          <span class="kpi-lbl">Parc (waterfall)</span><span class="kpi-val">${Math.round(uio).toLocaleString("en-GB")}</span>
          <span class="kpi-sub">units in the file · not a GPS%</span></div>
      </div>
      <div class="bars">
        <div class="bar-col" title="Wallet ${ctx.eur(wallet)}"><div class="bar" style="height:168px;background:#15233c"></div><span class="bar-lbl">Wallet</span></div>
        <div class="bar-col" title="Captured ${ctx.eur(captured)}"><div class="bar" style="height:${Math.max(8, (captured / maxBar) * 168)}px;background:#1d9e75"></div><span class="bar-lbl">Captured</span></div>
        <div class="bar-col" title="Gap ${ctx.eur(gap)}"><div class="bar" style="height:${Math.max(8, (gap / maxBar) * 168)}px"></div><span class="bar-lbl">Gap</span></div>
      </div>
      <table class="tbl">
        <thead><tr>
          <th>Distributor</th><th class="num">UIO</th>
          <th class="num">Wallet</th><th class="num">Captured</th>
          <th class="num">Gap</th><th class="num">Share of ceiling</th>
        </tr></thead>
        <tbody>${body || `<tr><td colspan="6" class="empty">No wallet rows for this selection. The waterfall has 18 network markets — CIS and Palestine are not in it.</td></tr>`}</tbody>
      </table>
      <p class="note">Share of ceiling is captured ÷ wallet in this file. It is not the live GPS dashboard %. Best Value is inside captured, not leakage.</p>
    `;
  },

  clientRenderCustomer: function renderWalletCustomer(rows, ctx) {
    const years = [...new Set(rows.map((r) => r.year))].sort((a, b) => a - b);
    const yKey = String(ctx.state.year || years[years.length - 1]);
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
      return `<p class="warn">No wallet row for <strong>${focus}</strong> in CY${yKey}.</p>`;
    }
    const r = me.reduce(
      (a, x) => ({
        wallet_eur: a.wallet_eur + x.wallet_eur,
        captured_total_eur: a.captured_total_eur + x.captured_total_eur,
        gap_eur: a.gap_eur + x.gap_eur,
        uio_units: a.uio_units + x.uio_units,
      }),
      { wallet_eur: 0, captured_total_eur: 0, gap_eur: 0, uio_units: 0 }
    );
    const net = rows.filter((x) => String(x.year) === yKey);
    const netW = net.reduce((s, x) => s + x.wallet_eur, 0);
    const share = r.wallet_eur ? r.captured_total_eur / r.wallet_eur : 0;
    const ofNet = netW ? r.wallet_eur / netW : 0;
    return `
      <p class="sub">Your ceiling, what was invoiced, and the gap still in play. Calendar year — not fiscal.</p>
      <div class="pickbar"><div class="pick-lbl">Calendar year</div><select data-act="year">${yearOpts}</select></div>
      <div class="kpi-row">
        <div class="kpi" data-tip="Your market's theoretical wallet: parc × per-model target spend. A ceiling of opportunity, not a sales forecast. CY${yKey}.">
          <span class="kpi-lbl">Your wallet ceiling</span><span class="kpi-val">${ctx.eur(r.wallet_eur)}</span>
          <span class="kpi-sub">${focus} · CY${yKey}</span></div>
        <div class="kpi" data-tip="What was invoiced through the authorised channel in this calendar year.">
          <span class="kpi-lbl">Captured</span><span class="kpi-val">${ctx.eur(r.captured_total_eur)}</span>
          <span class="kpi-sub">${ctx.pct(share)} of your ceiling</span></div>
        <div class="kpi" data-tip="Addressable uncaptured — still in play, not a booked loss.">
          <span class="kpi-lbl">Addressable gap</span><span class="kpi-val">${ctx.eur(r.gap_eur)}</span></div>
        <div class="kpi" data-tip="Your ceiling as a share of the network ceiling in this file. Other distributors are not listed.">
          <span class="kpi-lbl">Your share of network ceiling</span><span class="kpi-val">${ctx.pct(ofNet)}</span></div>
      </div>
    `;
  },
};
