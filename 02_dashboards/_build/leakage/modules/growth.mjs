/* Modules 1-2: sales evolution on a like-for-like basis, and monthly dynamics.
 *
 * ARCHITECTURE NOTE: the builder serialises each `render` function into the page, so a render
 * function must be SELF-CONTAINED. Helpers and colour constants used only by a render live
 * inside it. Only the imported chart bundle travels with it.
 *
 * The like-for-like rule: the current year is six months old, so every comparison uses the
 * SAME months of each year, and an average month is shown so a part year is never set against
 * a full year. The basis is printed on the face of every figure that depends on it.
 */
import {
  banner, barRows, changeBars, donut, esc, fmtEur, fmtEurExact, fmtInt, fmtPct,
  fmtSignedPct, kpis, lineChart, pill, table,
} from "../charts.mjs";

/* ============================================================ 1. evolution */
export const evolution = {
  id: "evolution",
  title: "Sales evolution",
  render(ctx) {
    const { L, peer } = ctx;
    const mod = ctx.mod("evolution") || {};
    const rows = ctx.rowsOf("evolution") || [];
    if (!rows.length) return banner("No market selected.", "info");

    const win = mod.window_label || "the same months of each year";
    const cy = ctx.payload.meta.current_year;

    const block = (r) => {
      if (r.unavailable) {
        return `<h3>${esc(ctx.dbName(r.db))}</h3>${banner(esc(r.unavailable), "amber")}`;
      }
      const ytd = r.ytd || [];
      const full = r.full || [];
      if (!ytd.length) {
        return `<h3>${esc(ctx.dbName(r.db))}</h3>${banner(
          "No monthly billing for this market, so a like-for-like comparison cannot be made.", "amber")}`;
      }
      const cur = ytd.find((x) => x.is_part_year) || ytd[ytd.length - 1];
      const prev = ytd.find((x) => x.year === cy - 1);

      // Movement, each point comparing the same months of consecutive years.
      const growth = [];
      for (let n = 1; n < ytd.length; n++) {
        const a = ytd[n - 1].eur, b = ytd[n].eur;
        if (!a || !b) continue;
        const pct = (b / a - 1) * 100;
        growth.push({
          label: String(ytd[n].year), value: pct, display: fmtSignedPct(pct),
          tip: `${ytd[n].year} against ${ytd[n - 1].year}, same months of each year: ${fmtEur(ytd[n].eur)} against ${fmtEur(ytd[n - 1].eur)}.`,
        });
      }

      const avg = cur.avg_month_eur;
      const prevAvg = prev ? prev.avg_month_eur : null;
      const fullNow = full.find((x) => x.year === cur.year - 1);

      const cards = kpis([
        { label: `Parts, ${win}`, value: fmtEur(cur.eur), small: true, dark: true,
          sub: `${cur.year}, ${cur.months} months`,
          tip: `Parts billed in the first ${cur.months} months of ${cur.year}. Compared with the same months of earlier years, never with a full year.` },
        { label: `Change vs ${cur.year - 1}`, value: fmtSignedPct(r.metric_growth_pct),
          subKind: (r.metric_growth_pct ?? 0) >= 0 ? "pos" : "neg",
          sub: "same months, so like for like",
          tip: `Parts value in the first ${cur.months} months of ${cur.year} against the same months of ${cur.year - 1}.` },
        { label: "Average month", value: avg ? fmtEurExact(avg) : "\u2013",
          sub: prevAvg ? `was ${fmtEurExact(prevAvg)}` : "previous year not available",
          tip: "Parts billed per month in the current window, which is the form that can be compared across years of different length." },
        { label: L.term.fleet, value: fmtInt((r.years.find((y) => y.year === cy - 1) || {}).uio),
          sub: "vehicles in service",
          tip: "Vehicles in service, the denominator behind every per-vehicle figure." },
        { label: `Typical ${peer ? peer.basis : "market"} growth`,
          value: peer && peer.median.metric_growth_pct !== null
            && peer.median.metric_growth_pct !== undefined
            ? fmtSignedPct(peer.median.metric_growth_pct) : "\u2013",
          small: true,
          sub: peer ? peer.note : "no comparable group",
          tip: peer ? peer.tip : "No comparable market group for this selection." },
      ]);

      const decompRows = r.decomp ? [
        { label: "Volume", value: r.decomp.volume_eur, display: fmtEur(r.decomp.volume_eur),
          cls: "alt", tip: "The part of the move explained by how many units moved." },
        { label: "Price", value: r.decomp.price_eur, display: fmtEur(r.decomp.price_eur),
          cls: "alt", tip: "The part of the move explained by the price per unit." },
      ] : null;

      return `<h3>${esc(ctx.dbName(r.db))}${
        r.db === ctx.focus ? ` ${pill("this market", "info")}` : ""}</h3>
      ${cards}
      ${growth.length ? `<h4>Movement, year on year on the same months</h4>
        ${changeBars(growth, {
          caption: `Each bar compares the same months of two consecutive years, so no part year is set against a full year. ${win}.`,
          legend: [
            { color: "var(--green)", label: "Grown" },
            { color: "var(--terra)", label: "Declined" },
          ] })}` : ""}
      <h4>Billed value by year</h4>
      ${table(
        [{ label: "Period" }, { label: "Same months", num: true }, { label: "Average month", num: true },
         { label: "Full year", num: true }, { label: "Per month, full year", num: true }],
        ytd.map((y) => {
          const f = full.find((x) => x.year === y.year);
          return {
            cls: y.is_part_year ? "focus" : "",
            cells: [
              { text: `${y.year}${y.is_part_year ? ` (${y.months} of 12)` : ` (${y.months} months)`}`,
                lbl: true },
              { text: fmtEur(y.eur) },
              { text: fmtEurExact(y.avg_month_eur) },
              { text: f ? fmtEur(f.eur) : "not yet complete",
                tip: f ? `${y.year} full year, from the billing extract.`
                       : `${y.year} is not complete, so no full-year figure exists. It is left blank rather than annualised, because annualising a half year invents a number.` },
              { text: f ? fmtEurExact(f.avg_month_eur) : "\u2013" },
            ],
          };
        }))}
      <p class="note">The same-months column is the one to compare between years. The full-year
        column is shown for context only, and is blank for ${cy} because the year is not over.
        Nothing is annualised.</p>
      ${decompRows ? `<h4>What moved it, CY2024 to CY2025</h4>
        ${barRows(decompRows, { legend: [
          { color: "var(--navy-3)", label: "Contribution to the change" }] })}
        <p class="note">${esc(r.decomp.mix_note)} Across the classified part families only, which
          moved ${fmtEur(r.decomp.total_eur)}.</p>` : ""}
      ${r.forward ? `<p class="note"><b>${esc(L.term.modelled)}.</b> The target spend ceiling for
        this market is modelled to reach ${fmtEur(r.forward.ceiling_2030_eur)} by ${r.forward.year}
        (${fmtSignedPct(r.forward.vs_2024_pct)} against 2024), from the fleet and target-spend
        model. It is a ceiling, not a forecast of what will be billed.</p>` : ""}`;
    };

    const total = ctx.networkSum("evolution", "metric_avg_month_eur");
    return `<p class="q">${esc(L.q.evolution)}</p>
      ${banner(`<b>Like for like.</b> ${cy} is only ${mod.window_months || 6} months old, so every
        figure here compares the same months of each year. A part year is never set against a full
        year, and nothing is annualised.`, "info")}
      <div class="stack">${rows.map(block).join("")}</div>
      ${ctx.audience === "customer" ? "" : `<p class="note">Network average month across the
        selected markets: <b>${fmtEur(total)}</b>. ${esc(L.msg.unitsNeedContext)}</p>`}`;
  },
};

/* ============================================================= 2. dynamics */
export const dynamics = {
  id: "dynamics",
  title: "Monthly dynamics",
  render(ctx) {
    const { L } = ctx;
    const mod = ctx.mod("dynamics") || {};
    const rows = ctx.rowsOf("dynamics") || [];
    if (!rows.length) return banner("No market selected.", "info");

    const N = ["Jan", "Feb", "Mar", "Apr", "May", "Jun",
               "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"];
    const cy = ctx.payload.meta.current_year;

    const block = (r) => {
      if (r.unavailable) {
        return `<h3>${esc(ctx.dbName(r.db))}</h3>${banner(esc(r.unavailable), "amber")}`;
      }
      const series = r.monthly || [];
      if (series.length < 2) {
        return `<h3>${esc(ctx.dbName(r.db))}</h3>${banner(
          "Not enough months of billing to show a trend for this market.", "amber")}`;
      }

      const cur = series.filter((x) => x.ym.startsWith(String(cy)));
      const prev = series.filter((x) => x.ym.startsWith(String(cy - 1)));
      const curAvg = cur.length ? cur.reduce((a, x) => a + (x.eur || 0), 0) / cur.length : null;
      const prevAvg = prev.length ? prev.reduce((a, x) => a + (x.eur || 0), 0) / prev.length : null;

      // Monthly points, each carrying its own prior-year twin so the shape can be judged.
      const prevMap = {};
      for (const p of (r.prior_year || [])) prevMap[p.ym] = p.eur;
      const points = series.filter((x) => x.ym.startsWith(String(cy))).map((x) => {
        const prior = prevMap[`${cy - 1}-${x.ym.slice(5, 7)}`];
        const ml = `${N[Number(x.ym.slice(5, 7)) - 1]} ${x.ym.slice(2, 4)}`;
        return {
          label: ml, value: x.eur,
          sub: prior ? `was ${fmtEur(prior)}` : null,
          tip: `${ml}: ${fmtEurExact(x.eur)}${prior ? `, against ${fmtEurExact(prior)} in the same month last year` : ""}.`,
        };
      });

      const prevPoints = prev.map((x) => ({
        label: `${N[Number(x.ym.slice(5, 7)) - 1]} ${x.ym.slice(2, 4)}`, value: x.eur,
        tip: `${N[Number(x.ym.slice(5, 7)) - 1]} ${x.ym.slice(2, 4)}: ${fmtEurExact(x.eur)}.`,
      }));

      const best = points.slice().sort((a, b) => (b.value || 0) - (a.value || 0))[0];
      const worst = points.slice().sort((a, b) => (a.value || 0) - (b.value || 0))[0];

      const cards = kpis([
        { label: `Average month, ${cy}`, value: curAvg ? fmtEurExact(curAvg) : "\u2013",
          dark: true, sub: `${cur.length} months of data`,
          tip: "Parts billed per month this year. The comparable form, because it does not depend on how many months have elapsed." },
        { label: `Average month, ${cy - 1}`, value: prevAvg ? fmtEurExact(prevAvg) : "\u2013",
          sub: "same months of last year",
          tip: "The same figure for the same months of last year." },
        { label: "Strongest month", value: best && best.value ? fmtEur(best.value) : "\u2013",
          small: true, sub: best ? best.label : null,
          tip: "The best month in the current year, so seasonality can be seen." },
        { label: "Weakest month", value: worst && worst.value ? fmtEur(worst.value) : "\u2013",
          small: true, sub: worst ? worst.label : null,
          tip: "The weakest month in the current year." },
      ]);

      return `<h3>${esc(ctx.dbName(r.db))}${
        r.db === ctx.focus ? ` ${pill("this market", "info")}` : ""}</h3>
      ${cards}
      <h4>Parts billed each month, ${cy}</h4>
      ${lineChart(points, {
        fmt: (v) => fmtEur(v), refValue: prevAvg || undefined,
        refLabel: `${cy - 1} average month`,
        aria: `Monthly parts billed in ${cy}`,
        caption: `Each month can be compared with the same month last year, because the dashed line is last year's average month. A month far above it is a strong month, not just a big number.`,
      })}
      ${prev.length > 2 ? `<h4>${cy - 1} for context</h4>
        ${lineChart(prevPoints, { fmt: (v) => fmtEur(v), aria: `Monthly parts billed in ${cy - 1}` })}`
        : ""}`;
    };

    return `<p class="q">${esc(L.q.dynamics)}</p>
      ${banner(`Billing runs from ${esc(mod.billing_first || "")} to ${esc(mod.billing_last || "")},
        so ${esc(String(mod.month_count || 0))} months are available in total. Each month is shown
        against the same month of the prior year.`, "info")}
      <div class="stack">${rows.map(block).join("")}</div>`;
  },
};

/* ================================================================== 3. GPS */
export const gps = {
  id: "gps",
  title: "Target spend vs billed",
  render(ctx) {
    const { L, peer } = ctx;
    const CAP_COLOR = "#2c6e49";
    const GAP_COLOR = "#c0552d";
    const STRUCT_COLOR = "#b9b0a3";

    const rows = ctx.rowsOf("gps") || [];
    if (!rows.length) return banner("No market selected.", "info");
    const ceiling = (ctx.payload.modules.gps || {}).ceiling || null;

    const block = (r) => {
      if (r.unavailable) {
        return `<h3>${esc(ctx.dbName(r.db))}</h3>${banner(esc(r.unavailable), "amber")}`;
      }
      const ys = r.years || [];
      const y25 = ys.find((y) => y.year === 2025) || ys[ys.length - 1];
      if (!y25) {
        return `<h3>${esc(ctx.dbName(r.db))}</h3>${banner("No CY2025 spend record.", "amber")}`;
      }
      const spu = y25.spend_per_unit_eur;
      const cards = kpis([
        { label: L.term.ceiling, value: fmtEur(y25.ceiling_eur), small: true, dark: true,
          sub: (y25.uio && y25.ceiling_eur) ? `${fmtEurExact(y25.ceiling_eur / y25.uio)} per vehicle` : null,
          tip: "The modelled total this fleet could spend on service parts in a year, built from vehicles in service and a target spend per vehicle." },
        { label: L.term.captured, value: fmtEur(y25.captured_eur), small: true,
          sub: `${fmtPct(y25.gps_pct)} of the ceiling`,
          tip: "Parts actually billed, against the ceiling. The percentage is billed divided by the ceiling." },
        { label: L.term.gap, value: fmtEur(y25.addressable_gap_eur), small: true,
          sub: "could be won",
          tip: "The part of the ceiling not billed and reachable with the right parts and terms." },
        { label: L.term.spendPerTruck, value: spu ? fmtEurExact(spu) : "\u2013",
          sub: "billed per vehicle in service",
          tip: "CY2025 parts billed divided by vehicles in service." },
        { label: L.term.fleet, value: fmtInt(y25.uio), sub: "vehicles in service",
          tip: "Fleet base for this market." },
        peer && peer.median.metric_spu_eur
          ? { label: `Typical ${peer.basis}`, value: fmtEurExact(peer.median.metric_spu_eur),
              sub: peer.note, tip: peer.tip }
          : null,
      ]);

      const segs = [
        { label: "Billed", value: y25.captured_eur || 0, color: CAP_COLOR },
        { label: "Addressable gap", value: y25.addressable_gap_eur || 0, color: GAP_COLOR },
        { label: "Structurally out of reach", value: y25.structural_eur || 0, color: STRUCT_COLOR },
      ].filter((s) => s.value > 0);

      const trend = ys.filter((y) => y.spend_per_unit_eur).map((y) => ({
        label: y.is_part_year ? `${y.year} (part year)` : String(y.year),
        value: y.spend_per_unit_eur, display: fmtEurExact(y.spend_per_unit_eur),
        cls: y.is_part_year ? "neg" : "",
        tip: y.is_part_year
          ? `${y.year} runs to 30 June only, so this figure is a part year and is not comparable with the full years beside it. Compare with the six-month figure in Sales evolution instead.`
          : `${y.year} parts billed per vehicle in service.`,
      }));

      const ph = (ceiling && ceiling.per_market) ? ceiling.per_market[r.db] : null;
      const basis = (y25.uio && y25.ceiling_eur) ? y25.ceiling_eur / y25.uio : null;
      const sens = (ph && ph.is_placeholder && basis && y25.uio)
        ? [[0.8, "+20% to reach"], [1.0, "target as set"], [1.2, "\u221220% tight"]].map(([k, lbl]) => {
            const c = basis * k * y25.uio;
            const gap = Math.max(0, c - (y25.captured_eur || 0));
            return {
              label: lbl, value: gap, display: fmtEur(gap),
              sub: `${fmtEurExact(basis * k)} per vehicle`,
              cls: k === 1 ? "" : "alt",
              tip: `${lbl}: with a target of ${fmtEurExact(basis * k)} per vehicle the ceiling is ${fmtEur(c)} and the gap is ${fmtEur(gap)}.`,
            };
          })
        : null;

      return `<h3>${esc(ctx.dbName(r.db))}${
        r.db === ctx.focus ? ` ${pill("this market", "info")}` : ""}</h3>
      ${cards}
      <div class="cols2">
        <div><h4>Where the ceiling goes, CY2025</h4>
          ${donut(segs, { center: { value: fmtPct(y25.gps_pct), label: "OF CEILING" },
            aria: "Share of target spend ceiling billed" })}
          <p class="note">Billed plus the reachable gap plus the part that is structurally out of
            reach equals the ceiling. "Structurally out of reach" is demand our parts range cannot
            serve, so it is not an opportunity.</p></div>
        <div><h4>${L.term.spendPerTruck} by year</h4>
          ${trend.length > 1 ? barRows(trend, {
            legend: [
              { color: "var(--terra)", label: "Full year" },
              { color: "var(--terra)", label: "Part year, not comparable" },
            ] }) : `<p class="empty">Only one year available.</p>`}
          ${trend.some((t) => t.cls === "neg") ? `<p class="note"><b>Careful with the part year.</b>
            The latest bar covers six months, not twelve, so it sits low for a reason that has
            nothing to do with performance. The like-for-like figure is in Sales evolution.</p>` : ""}
          ${(y25.gps_vs_upper_benchmark_pct !== null && y25.gps_vs_upper_benchmark_pct !== undefined)
            ? `<p class="note"><b>Two constructions of the same ceiling.</b> The share of ceiling
               above is ${fmtPct(y25.gps_pct)}, built from this market's vehicles in service by
               weight class. Measured against the upper reference spend per market it reads
               ${fmtPct(y25.gps_vs_upper_benchmark_pct)}. They differ because the two use different
               fleet vintages and one prices every truck at a single rate. Where they disagree by
               more than a couple of points, treat the lower figure as the safer one and say which
               basis you are quoting.</p>` : ""}
          ${y25.warranty_gap ? banner("Warranty parts are not fully separated for this market, so the spend figures include an unknown warranty share.", "amber") : ""}
        </div>
      </div>
      ${sens ? `<h4>How much of that gap is the target assumption</h4>
        ${barRows(sens, { legend: [
          { color: "var(--terra)", label: "Addressable gap at each target level" }] })}
        <p class="note">This market's target spend per vehicle is a fixed placeholder in the model,
          not a measured figure, so the gap is shown at three target levels. If it swings hard across
          this band, the number is telling you more about the assumption than about the market.</p>` : ""}
      <h4>The gap in euro, ranked</h4>
      ${barRows([
        { label: "Addressable gap", value: y25.addressable_gap_eur, display: fmtEur(y25.addressable_gap_eur),
          sub: "reachable", tip: "Reachable with the right parts and terms." },
        { label: "Structurally out of reach", value: y25.structural_eur, display: fmtEur(y25.structural_eur),
          sub: "not an opportunity", cls: "alt",
          tip: "Demand our parts range cannot serve." },
        { label: "Billed above the ceiling", value: y25.beyond_ceiling_eur,
          display: fmtEur(y25.beyond_ceiling_eur), sub: "over-performance", cls: "pos",
          tip: "Where we billed more than the model expected, which usually means the target spend per vehicle is set low for this market." },
      ])}`;
    };

    const flat = (ctx.audience === "customer" || !ceiling) ? "" : `<p class="note">
      <b>How much of the ceiling is a placeholder.</b> ${ceiling.flat_n} of ${ceiling.n_markets}
      markets sit at exactly €${Math.round(ceiling.placeholder_eur)} per vehicle in service, the
      model's flat placeholder. Those markets hold ${fmtPct(ceiling.flat_share_ceiling_pct, 1)} of
      the ${fmtEur(ceiling.ceiling_total_eur)} network ceiling. Across the network the figure ranges
      from €${Math.round(ceiling.spu_min)} to €${Math.round(ceiling.spu_max)} per vehicle, so the
      placeholder is doing a lot of work in the total, and every gap below inherits that.</p>`;
    return `<p class="q">${esc(L.q.gps)}</p>
      <div class="stack">${rows.map(block).join("")}</div>${flat}`;
  },
};
