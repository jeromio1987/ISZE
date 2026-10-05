/* Module: warranty monthly (network total)
 * Audience: INTERNAL ONLY — network-level warranty spend is not distributor-shareable.
 * This module is dropped entirely from a customer build (module-level gating).
 */

export default {
  id: "warranty_monthly",
  title: "Warranty — network, monthly",
  audience: ["internal"],
  grain: "month",
  source: "01_data/00_derived/warranty_fy26_monthly.csv",

  // Runs at BUILD time (node). Returns plain rows.
  parse(csvText) {
    const [header, ...lines] = csvText.trim().split(/\r?\n/);
    const cols = header.split(",");
    return lines.filter(Boolean).map((line) => {
      const v = line.split(",");
      const row = {};
      cols.forEach((c, i) => (row[c] = v[i]));
      return {
        period: row.AssessMonth,               // YYYYMM
        claims: Number(row.Claims),
        total_usd: Number(row.Total_USD),
        parts_usd: Number(row.PartsAmt_USD),
      };
    });
  },

  // Stringified into the output bundle and run in the browser.
  clientRender: function renderWarranty(rows, ctx) {
    const agg = ctx.rollup(rows, ctx.period, "period");
    const gaps = ctx.findGaps(rows.map((r) => r.period));

    const max = Math.max(...agg.map((a) => a.total_usd));
    const bars = agg
      .map((a) => {
        const h = max ? (a.total_usd / max) * 100 : 0;
        return `<div class="bar-col" title="${a.label}: ${ctx.usd(a.total_usd)} · ${a.claims} claims">
          <div class="bar" style="height:${h}%"></div>
          <span class="bar-lbl">${a.label}</span>
        </div>`;
      })
      .join("");

    const totalUsd = agg.reduce((s, a) => s + a.total_usd, 0);
    const totalClaims = agg.reduce((s, a) => s + a.claims, 0);

    // The source changes what it counts from Dec-2025 onward: earlier months count only
    // claim lines carrying a part number, later months count every claim line including
    // labour-only lines. Parts USD is unaffected; the claim count and total USD are not.
    const BREAK = "202512";
    const spansBreak = rows.some((r) => r.period <= BREAK) && rows.some((r) => r.period >= BREAK);

    return `
      <div class="kpi-row">
        <div class="kpi" data-tip="Sum of Total_USD in warranty_fy26_monthly.csv for the selected period rollup. USD as stored — not converted to euro."><span class="kpi-lbl">Total warranty</span><span class="kpi-val">${ctx.usd(totalUsd)}</span></div>
        <div class="kpi" data-tip="Claim count in the same monthly file. Not a € figure."><span class="kpi-lbl">Claims</span><span class="kpi-val">${totalClaims.toLocaleString("en-GB")}</span></div>
        <div class="kpi" data-tip="How many buckets the current period control produced. Gaps in the source are listed below — they are not filled."><span class="kpi-lbl">Periods shown</span><span class="kpi-val">${agg.length}</span></div>
      </div>
      ${spansBreak ? `<p class="warn">The source changes what it counts from <strong>Dec-2025</strong> onward: earlier months count only claim lines that carry a part number, later months count every claim line including labour-only ones. Parts USD is unaffected. The claim count and total USD step up there by more than the volume did — do not read the two halves against each other.</p>` : ""}
      ${gaps.length ? `<p class="warn">Source is missing ${gaps.length} month(s): ${gaps.join(", ")}. Totals below are therefore <strong>not</strong> a full year.</p>` : ""}
      <div class="bars">${bars}</div>
    `;
  },
};
