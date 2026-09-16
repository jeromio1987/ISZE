/* Module: GPS-eligible parts — pure sales (euros only)
 *
 * Canonical numerator: gps_pure_sales_2026-08-13_v2.csv `pure_sales_eur`.
 * No UIO, no max spend, no v20, no gps_pct — capture % is omitted on purpose.
 *
 * Audience:
 *   internal — euros, warranty toggle, Shell as a separate lubricants line,
 *              Check 4 / FY23 / negative ex-warranty banners, diagnostic flags
 *   customer — own euros + network position/median/share (no competitor list);
 *              Shell and SaTy/flags stripped
 */

function numOrNull(s) {
  if (s == null) return null;
  const t = String(s).trim();
  if (t === "") return null;
  const n = Number(t);
  return Number.isFinite(n) ? n : null;
}

export default {
  id: "gps_pure_sales",
  title: "Spend — GPS-eligible parts",
  audience: ["internal", "customer"],
  grain: "year",
  source: "01_data/00_derived/gps_pure_sales_2026-08-13_v2.csv",
  dbField: "db", // SAP entity labels (ISD, IBX, Danmark…) -> canonical _db by the shell
  internalOnlyFields: [
    "payer_codes",
    "net_raw",
    "billing_clean_eur",
    "transport_eur",
    "surcharge_stripped_eur",
    "shell_lubricants_eur",
    "other_excl_eur",
    "saty_cr_excl_eur",
    "notes",
  ],

  parse(csvText) {
    const [header, ...lines] = csvText.trim().split(/\r?\n/);
    const cols = header.split(",");
    return lines.filter(Boolean).map((line) => {
      const v = line.split(",");
      const row = {};
      cols.forEach((c, i) => (row[c] = v[i]));
      return {
        period: "FY" + row.fy,
        fy: Number(row.fy),
        db: row.db,
        payer_codes: row.payer_codes,
        net_raw: numOrNull(row.net_raw),
        billing_clean_eur: numOrNull(row.billing_clean_eur),
        transport_eur: numOrNull(row.transport_eur) ?? 0,
        surcharge_stripped_eur: numOrNull(row.surcharge_stripped_eur),
        shell_lubricants_eur: numOrNull(row.shell_lubricants_eur) ?? 0,
        other_excl_eur: numOrNull(row.other_excl_eur) ?? 0,
        saty_cr_excl_eur: numOrNull(row.saty_cr_excl_eur) ?? 0,
        pure_sales_eur: numOrNull(row.pure_sales_eur) ?? 0,
        warranty_eur: numOrNull(row.warranty_eur),
        pure_sales_ex_warranty_eur: numOrNull(row.pure_sales_ex_warranty_eur),
        notes: row.notes || "",
      };
    });
  },

  initialState: { warr: "incl", fy: "2026" },

  onEvent(ev, state) {
    const t = ev.target.closest("[data-act]");
    if (!t) return false;
    if (t.dataset.act === "warr") {
      state.warr = t.value;
      return true;
    }
    if (t.dataset.act === "fy") {
      state.fy = t.value;
      return true;
    }
    return false;
  },

  clientRender: function renderGpsInternal(rows, ctx) {
    const st = ctx.state;
    const warr = st.warr === "ex" ? "ex" : "incl";
    const fyKey = String(st.fy || "2026");
    const fys = [...new Set(rows.map((r) => r.fy))].sort((a, b) => a - b);

    const salesOf = (r) =>
      warr === "ex" ? r.pure_sales_ex_warranty_eur : r.pure_sales_eur;

    const sumKnown = (xs, fn) =>
      xs.reduce((s, r) => {
        const v = fn(r);
        return v == null ? s : s + v;
      }, 0);

    // Global distributor selection from the shared picker.
    const inSel = (r) => ctx.inSelection(r._db);
    const byFy = (fy) => rows.filter((r) => r.fy === fy && inSel(r));
    const viewRows = (fyKey === "all" ? rows.slice() : rows.filter((r) => String(r.fy) === fyKey))
      .filter(inSel);
    const selNote = ctx.selectedDbs.length
      ? `<p class="note">Filtered to ${ctx.selectedDbs.length} selected distributor(s): ${ctx.selectedDbs.join(", ")}.</p>`
      : "";

    const grainExtra =
      ctx.period === "cy"
        ? `<p class="warn">This source is <strong>fiscal year</strong> (Apr–Mar, labeled by the March-end calendar year). Calendar-year GPS is not in the file and is not fabricated — FY figures are shown.</p>`
        : "";

    const otherByFy = Object.fromEntries(
      fys.map((fy) => [fy, sumKnown(byFy(fy), (r) => r.other_excl_eur)])
    );
    const other25 = otherByFy[2025] || 0;
    const other26 = otherByFy[2026] || 0;
    const other24 = otherByFy[2024] || 0;
    const ituk25 = rows.find((r) => r.fy === 2025 && r.db === "ITUK");
    const itukOther25 = ituk25 ? ituk25.other_excl_eur : other25;

    const check4 = `<p class="warn-fail"><strong>Check 4 fails — years are not on the same basis.</strong>
      FY2026 other-exclusions (service / late payment / demurrage) = <strong>${ctx.eur(other26)}</strong>.
      FY2025 = <strong>${ctx.eur(other25)}</strong>${itukOther25 ? ` (all ITUK, ${ctx.eur(itukOther25)})` : ""}.
      FY2024 = ${ctx.eur(other24)} (all ITUK).
      FY2026 €0 is a data-basis break, not evidence those charges stopped.
      Do not read FY25→FY26 as a clean trend.</p>`;

    const fy23on = fyKey === "all" || fyKey === "2023";
    const fy23 = fy23on
      ? `<p class="warn"><strong>FY2023 is partial</strong> (roughly Q4 only). Shell and other-exclusions are also €0 that year. Do not treat FY2023 as a full-year comparable.</p>`
      : "";

    const neg = viewRows.filter(
      (r) => r.pure_sales_ex_warranty_eur != null && r.pure_sales_ex_warranty_eur < 0
    );
    const negBanner =
      warr === "ex" && neg.length
        ? `<p class="warn-fail"><strong>Ex-warranty is negative for ${neg
            .map((r) => `${r.db} FY${r.fy} (${ctx.eur(r.pure_sales_ex_warranty_eur)})`)
            .join(" · ")}</strong> — warranty exceeds GPS-eligible parts. Shown as stored. No capture % is computed from this.</p>`
        : "";

    const unknownWarr = viewRows.filter((r) => r.warranty_eur == null);
    const unknownBanner =
      warr === "ex" && unknownWarr.length
        ? `<p class="warn">Warranty is unknown for <strong>${unknownWarr.length}</strong> row(s) in this view (blank in the file, not €0). Those rows are omitted from the ex-warranty total — they are not treated as zero.</p>`
        : "";

    const netBars = fys
      .map((fy) => {
        const xs = byFy(fy);
        const tot = sumKnown(xs, salesOf);
        const known = xs.filter((r) => salesOf(r) != null).length;
        return { fy, tot, known, n: xs.length };
      })
      .filter((a) => warr !== "ex" || a.known > 0);
    const maxNet = Math.max(0, ...netBars.map((a) => a.tot));
    const bars = netBars
      .map((a) => {
        const h = maxNet ? Math.max(8, (Math.abs(a.tot) / maxNet) * 168) : 0;
        const partial = a.fy === 2023 ? " · partial" : "";
        const anomaly = a.fy === 2026 ? " · other-excl €0" : "";
        const negCls = a.tot < 0 ? " negbar" : "";
        return `<div class="bar-col" title="FY${a.fy}: ${ctx.eur(a.tot)}${partial}${anomaly}">
          <div class="bar${negCls}" style="height:${h}px"></div>
          <span class="bar-lbl">FY${a.fy}</span>
        </div>`;
      })
      .join("");

    const viewKnown = viewRows.filter((r) => salesOf(r) != null);
    const viewTotal = sumKnown(viewRows, salesOf);
    const shellTotal = sumKnown(viewRows, (r) => r.shell_lubricants_eur);
    const shellDbs = viewRows.filter((r) => r.shell_lubricants_eur > 0).map((r) => r.db);
    const warrKnown = viewRows.filter((r) => r.warranty_eur != null);
    const warrTotal = sumKnown(viewRows, (r) => r.warranty_eur);

    const fyOpts = [`<option value="all" ${fyKey === "all" ? "selected" : ""}>All FYs</option>`]
      .concat(
        fys.map(
          (fy) =>
            `<option value="${fy}" ${fyKey === String(fy) ? "selected" : ""}>FY${fy}${
              fy === 2023 ? " (partial)" : ""
            }</option>`
        )
      )
      .join("");

    const metricLbl =
      warr === "ex" ? "GPS-eligible parts, warranty excluded" : "GPS-eligible parts (pure sales)";

    const sorted = viewRows.slice().sort((a, b) => {
      const av = salesOf(a);
      const bv = salesOf(b);
      if (av == null && bv == null) return a.db.localeCompare(b.db);
      if (av == null) return 1;
      if (bv == null) return -1;
      return bv - av;
    });

    const body = sorted
      .map((r) => {
        const v = salesOf(r);
        const israel = /\bisrael_split\b/.test(r.notes)
          ? `<span class="flag">Israel split</span>`
          : "";
        const flags = r.notes
          ? r.notes
              .split("|")
              .filter((f) => f && f !== "israel_split")
              .map((f) => `<span class="flag">${f.replace(/_/g, " ")}</span>`)
              .join(" ")
          : "";
        const salesCell =
          v == null
            ? `<td class="num">—</td>`
            : `<td class="num${v < 0 ? " neg" : ""}">${ctx.eur(v)}</td>`;
        const warrCell =
          r.warranty_eur == null
            ? `<td class="num">—</td>`
            : `<td class="num">${ctx.eur(r.warranty_eur)}</td>`;
        const shellCell =
          r.shell_lubricants_eur > 0
            ? `<td class="num">${ctx.eur(r.shell_lubricants_eur)}</td>`
            : `<td class="num">€0</td>`;
        return `<tr>
          <td><strong>${r._db || r.db}</strong> ${israel}<div class="cats">FY${r.fy}${
            r._db && r._db !== r.db ? ` · SAP ${r.db}` : ""
          }</div></td>
          ${salesCell}
          ${warrCell}
          ${shellCell}
          <td class="cats">${flags || "—"}</td>
        </tr>`;
      })
      .join("");

    return `
      <p class="sub">Capture % waits on signed UIO; this view is <strong>euros only</strong>.
      No GPS% is computed. Source grain is fiscal year — month/quarter GPS is not fabricated.</p>
      ${ctx.grainWarning(ctx, "fiscal year")}
      ${grainExtra}
      ${check4}
      ${fy23}
      ${negBanner}
      ${unknownBanner}
      ${selNote}
      <div class="pickbar">
        <div class="pick-lbl">Fiscal year</div>
        <select data-act="fy">${fyOpts}</select>
        <div class="pick-lbl">Warranty</div>
        <select data-act="warr">
          <option value="incl" ${warr === "incl" ? "selected" : ""}>Include warranty (canonical pure sales)</option>
          <option value="ex" ${warr === "ex" ? "selected" : ""}>Exclude warranty (pure sales − warranty)</option>
        </select>
      </div>
      <div class="kpi-row">
        <div class="kpi" data-tip="pure_sales_eur from gps_pure_sales_2026-08-13_v2.csv (GPS-eligible parts, Shell out). Bare SERVICE on IMIO (€160k) is other-excl, not parts — IMIO is not a network DB so network euros match the previous file. Fiscal year. No GPS%."><span class="kpi-lbl">${metricLbl}</span><span class="kpi-val">${ctx.eur(viewTotal)}</span>
          <span class="kpi-sub">${viewKnown.length} of ${viewRows.length} row(s) in this view${
            warr === "ex" && unknownWarr.length ? ` · ${unknownWarr.length} warranty-unknown omitted` : ""
          }</span></div>
        <div class="kpi"><span class="kpi-lbl">Warranty (known)</span><span class="kpi-val">${
          warrKnown.length ? ctx.eur(warrTotal) : "—"
        }</span>
          <span class="kpi-sub">${warrKnown.length} DB-year(s) with a warranty figure</span></div>
        <div class="kpi"><span class="kpi-lbl">Shell lubricants (not in parts)</span><span class="kpi-val">${ctx.eur(shellTotal)}</span>
          <span class="kpi-sub">${
            shellTotal
              ? `Separate line — ${[...new Set(shellDbs)].join(", ")} only. Never inside UMI parts.`
              : "€0 in this view"
          }</span></div>
      </div>
      <p class="note">Network FY totals below use the same warranty setting. FY2023 is partial; FY2026 other-exclusions are €0 (Check 4). UMI and UTI are stored as a split — do not add them onto one wallet.</p>
      <div class="bars">${bars}</div>
      <table class="tbl">
        <thead><tr>
          <th>Distributor</th>
          <th class="num">${warr === "ex" ? "Pure sales ex-warranty" : "Pure sales"}</th>
          <th class="num">Warranty</th>
          <th class="num">Shell lubricants</th>
          <th>Flags</th>
        </tr></thead>
        <tbody>${
          body || `<tr><td colspan="5" class="empty">No rows for this fiscal year.</td></tr>`
        }</tbody>
      </table>
      <p class="note">Canonical numerator is <em>pure sales</em> (GPS-eligible parts, Shell out).
      Warranty is a client filter, not baked into a percentage.
      Shell is a lubricants line, not parts. SaTy / other-exclusion flags stay on this internal view.</p>
    `;
  },

  clientRenderCustomer: function renderGpsCustomer(rows, ctx) {
    const st = ctx.state;
    const warr = st.warr === "ex" ? "ex" : "incl";
    const fyKey = String(st.fy || "2026");
    const fys = [...new Set(rows.map((r) => r.fy))].sort((a, b) => a - b);
    const focus = ctx.focusDistributor ? String(ctx.focusDistributor) : "";

    const salesOf = (r) =>
      warr === "ex" ? r.pure_sales_ex_warranty_eur : r.pure_sales_eur;

    const grainExtra =
      ctx.period === "cy"
        ? `<p class="warn">This source is <strong>fiscal year</strong> (Apr–Mar). Calendar-year figures are not available and are not fabricated — FY is shown.</p>`
        : "";

    if (!focus) {
      return `<p class="warn">No focus distributor set. Build with
        <code>--audience=customer --focus=&lt;DB&gt;</code> to produce a customer view.</p>`;
    }

    const viewRows =
      fyKey === "all" ? rows.slice() : rows.filter((r) => String(r.fy) === fyKey);
    const meRows = viewRows.filter(
      (r) => String(r._db || r.db).toUpperCase() === focus.toUpperCase()
    );

    if (!meRows.length) {
      return `
        ${ctx.grainWarning(ctx, "fiscal year")}
        <p class="warn">No rows for <strong>${focus}</strong> in this fiscal-year selection.
        Billing names in this file (e.g. ITUK, IUK, UMI, UTI, Norway) must match <code>--focus</code>.</p>`;
    }

    const fyOpts = [`<option value="all" ${fyKey === "all" ? "selected" : ""}>All FYs</option>`]
      .concat(
        fys.map(
          (fy) =>
            `<option value="${fy}" ${fyKey === String(fy) ? "selected" : ""}>FY${fy}${
              fy === 2023 ? " (partial)" : ""
            }</option>`
        )
      )
      .join("");

    const meTotal = meRows.reduce((s, r) => {
      const v = salesOf(r);
      return v == null ? s : s + v;
    }, 0);
    const meUnknown = meRows.filter((r) => salesOf(r) == null).length;
    const meNeg = meRows.filter((r) => salesOf(r) != null && salesOf(r) < 0);

    const metricLbl =
      warr === "ex" ? "Your GPS-eligible parts, warranty excluded" : "Your GPS-eligible parts (pure sales)";

    const rankSrc =
      fyKey === "all"
        ? rows.filter((r) => r.fy === Math.max(...fys))
        : viewRows;
    const rankable = rankSrc
      .map((r) => ({ db: r._db || r.db, v: salesOf(r), fy: r.fy }))
      .filter((r) => r.v != null)
      .sort((a, b) => b.v - a.v);

    // Network context without listing competitors: position, median, share only.
    const myIdx = rankable.findIndex((r) => r.db.toUpperCase() === focus.toUpperCase());
    const netTotal = rankable.reduce((s, r) => s + r.v, 0);
    const netMedian = ctx.median(rankable.map((r) => r.v));
    const myVal = myIdx >= 0 ? rankable[myIdx].v : null;
    const myShare = myVal != null && netTotal ? myVal / netTotal : null;

    const negNote =
      warr === "ex" && meNeg.length
        ? `<p class="warn">Your ex-warranty figure is negative in ${meNeg
            .map((r) => `FY${r.fy}`)
            .join(", ")} — warranty exceeds GPS-eligible parts. Shown as stored. No capture % is computed.</p>`
        : "";

    const ownRows = meRows
      .map((r) => {
        const v = salesOf(r);
        const w = r.warranty_eur;
        return `<tr>
          <td>FY${r.fy}${r.fy === 2023 ? " (partial)" : ""}</td>
          <td class="num${v != null && v < 0 ? " neg" : ""}">${v == null ? "—" : ctx.eur(v)}</td>
          <td class="num">${w == null ? "—" : ctx.eur(w)}</td>
        </tr>`;
      })
      .join("");

    return `
      <p class="sub">Capture % waits on signed UIO; this view is <strong>euros only</strong>.
      No GPS% is computed. Source grain is fiscal year — month/quarter GPS is not fabricated.</p>
      ${ctx.grainWarning(ctx, "fiscal year")}
      ${grainExtra}
      <p class="warn">Fiscal years are not on the same exclusion basis. Do not read year-to-year movement as a clean trend. FY2023 is partial.</p>
      ${negNote}
      ${meUnknown ? `<p class="warn">Warranty is unknown for ${meUnknown} of your row(s) — shown as —, not as €0.</p>` : ""}
      <div class="pickbar">
        <div class="pick-lbl">Fiscal year</div>
        <select data-act="fy">${fyOpts}</select>
        <div class="pick-lbl">Warranty</div>
        <select data-act="warr">
          <option value="incl" ${warr === "incl" ? "selected" : ""}>Include warranty (pure sales)</option>
          <option value="ex" ${warr === "ex" ? "selected" : ""}>Exclude warranty (pure sales − warranty)</option>
        </select>
      </div>
      <div class="kpi-row">
        <div class="kpi"><span class="kpi-lbl">${metricLbl}</span><span class="kpi-val">${
          meUnknown && warr === "ex" && meRows.every((r) => salesOf(r) == null) ? "—" : ctx.eur(meTotal)
        }</span>
          <span class="kpi-sub">${meRows[0]._db || meRows[0].db} · ${meRows.length} FY row(s)</span></div>
      </div>
      <table class="tbl">
        <thead><tr><th>Your FY</th><th class="num">${
          warr === "ex" ? "Pure sales ex-warranty" : "Pure sales"
        }</th><th class="num">Warranty</th></tr></thead>
        <tbody>${ownRows}</tbody>
      </table>
      <div class="kpi-row">
        <div class="kpi"><span class="kpi-lbl">Your position in network</span><span class="kpi-val">${
          myIdx >= 0 ? `#${myIdx + 1}` : "—"
        }</span><span class="kpi-sub">of ${rankable.length} distributors</span></div>
        <div class="kpi"><span class="kpi-lbl">Network median</span><span class="kpi-val">${ctx.eur(
          netMedian
        )}</span><span class="kpi-sub">per distributor</span></div>
        <div class="kpi"><span class="kpi-lbl">Your share of network</span><span class="kpi-val">${
          myShare == null ? "—" : (myShare * 100).toFixed(1) + "%"
        }</span><span class="kpi-sub">of GPS-eligible parts euros</span></div>
      </div>
      <p class="note">Network context uses ${
        fyKey === "all" ? "the latest FY in the file" : "the selected FY"
      }. Individual distributors are not listed and their amounts are not shown.</p>
    `;
  },
};
