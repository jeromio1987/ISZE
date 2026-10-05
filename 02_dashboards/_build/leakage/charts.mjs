/* Chart and layout primitives for the distributor leakage tool.
 *
 * Chart form is chosen per question, not per habit (skill isze-best-chart):
 *   rank / who wins        -> horizontal bars with a reference mark
 *   direction over time    -> change bars (growth green, decline terracotta)
 *   mix inside one family  -> donut, 4 segments maximum
 *   many families x years  -> small multiples / heat table, never 18 overlapping lines
 *
 * Every euro figure is paired with the fleet base, because a quantity without its
 * denominator cannot be judged (rule isze-gaps-need-context).
 */

export const esc = (s) =>
  String(s ?? "").replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;").replace(/'/g, "&#39;");

const NBSP = "\u2009"; // thin space for thousands

export function fmtInt(n) {
  if (n === null || n === undefined || Number.isNaN(n)) return "–";
  return Math.round(n).toLocaleString("en-GB");
}

export function fmtEur(n, dp = 1) {
  if (n === null || n === undefined || Number.isNaN(n)) return "–";
  const a = Math.abs(n);
  const sign = n < 0 ? "\u2212" : "";
  if (a >= 1e9) return `${sign}€${(a / 1e9).toFixed(dp)}bn`;
  if (a >= 1e6) return `${sign}€${(a / 1e6).toFixed(dp)}M`;
  if (a >= 1000) return `${sign}€${Math.round(a / 1e3)}K`;
  return `${sign}€${Math.round(a)}`;
}

export function fmtEurExact(n) {
  if (n === null || n === undefined || Number.isNaN(n)) return "–";
  return `${n < 0 ? "\u2212" : ""}€${Math.abs(Math.round(n)).toLocaleString("en-GB")}`;
}

export function fmtPct(n, dp = 1) {
  if (n === null || n === undefined || Number.isNaN(n)) return "–";
  return `${n.toFixed(dp)}%`;
}

export function fmtPP(n, dp = 1) {
  if (n === null || n === undefined || Number.isNaN(n)) return "–";
  const s = n > 0 ? "+" : n < 0 ? "\u2212" : "";
  return `${s}${Math.abs(n).toFixed(dp)} pp`;
}

export function fmtSignedPct(n, dp = 1) {
  if (n === null || n === undefined || Number.isNaN(n)) return "–";
  const s = n > 0 ? "+" : n < 0 ? "\u2212" : "";
  return `${s}${Math.abs(n).toFixed(dp)}%`;
}

export const tip = (s) => (s ? ` data-tip="${esc(s).replace(/&#39;/g, "'")}"` : "");

export function pill(text, kind = "mute") {
  return `<span class="pill ${kind}">${esc(text)}</span>`;
}

export function banner(html, kind = "info") {
  return `<p class="banner ${kind}">${html}</p>`;
}

/* ----------------------------------------------------------------- KPI cards */
export function kpis(cards) {
  const out = cards.filter(Boolean).map((c) => `
    <div class="kpi${c.dark ? " dark" : ""}"${tip(c.tip).replace('class=', 'data-x=')}>
      <span class="kpi-l">${esc(c.label)}</span>
      <span class="kpi-v${c.small ? " sm" : ""}">${c.value}</span>
      ${c.sub ? `<span class="kpi-s${c.subKind ? " " + c.subKind : ""}">${esc(c.sub)}</span>` : ""}
    </div>`).join("");
  return `<div class="kpis">${out}</div>`;
}

/* ------------------------------------------------------ horizontal bar rows */
/**
 * rows: [{label, value, sub?, display?, tip?, ref?, cls?, compare?}]
 * opts: {unit, refLabel, refValue, trackMax, legend:[{color,label}], showAxis:[min,max]}
 * A reference mark is drawn at opts.refValue so a peer median reads as a benchmark,
 * not as another bar.
 */
export function barRows(rows, opts = {}) {
  const vals = rows.map((r) => Math.abs(r.value ?? 0));
  const max = opts.trackMax || Math.max(...vals, opts.refValue ?? 0, 1);
  const pos = (v) => Math.min(100, Math.max(0, (Math.abs(v ?? 0) / max) * 100));

  const legend = opts.legend
    ? `<div class="hb-legend">${opts.legend.map((l) =>
        `<span><i style="background:${l.color}"></i>${esc(l.label)}</span>`).join("")}</div>`
    : "";

  const body = rows.map((r) => {
    const fillCls = r.cls ? ` ${r.cls}` : "";
    const ref = r.ref !== undefined && r.ref !== null
      ? `<span class="hb-ref" style="left:${pos(r.ref)}%" title="Reference"></span>` : "";
    return `<div class="hb-row">
      <div class="hb-lab"${tip(r.tip).replace('class=', 'data-x=')}>${esc(r.label)}${
        r.labelSub ? `<span class="hb-sub">${esc(r.labelSub)}</span>` : ""}</div>
      <div class="hb-track"><div class="hb-fill${fillCls}" style="width:${pos(r.value)}%"></div>${ref}</div>
      <div class="hb-val">${r.display ?? fmtEur(r.value)}${
        r.sub ? `<span class="u">${esc(r.sub)}</span>` : ""}</div>
    </div>`;
  }).join("");

  const axis = opts.showAxis
    ? `<div class="hb-axis"><span>${esc(opts.showAxis[0])}</span><span>${esc(opts.showAxis[1])}</span></div>`
    : "";
  return `<div class="hb">${legend}${body}${axis}</div>`;
}

/* ------------------------------------------------------------- change bars */
/**
 * Direction of travel across years, on a like-for-like basis.
 *
 * Layout note: an earlier version positioned the value label absolutely inside a fixed-height
 * box, so the label of a tall bar was clipped at the top and the year labels collided with the
 * axis caption. This version reserves explicit headroom for the tallest bar, keeps the value
 * label inside the plot box, and puts the year labels in their own row so they cannot overlap
 * the caption. A percentage label needs 16px, so the plot box gets that much padding.
 *
 * series: [{label, value, display, sub?, tip?}]  value is a signed percentage or euro change.
 */
export function changeBars(series, opts = {}) {
  const max = Math.max(...series.map((s) => Math.abs(s.value ?? 0)), 1);
  const MAXBAND = 40;                       // worst case uses 40% of the box, leaving headroom
  const cols = series.map((s) => {
    const v = s.value ?? 0;
    const h = Math.min((Math.abs(v) / max) * MAXBAND, MAXBAND);
    const up = v >= 0;
    const bar = up
      ? `top:${(50 - h).toFixed(3)}%;bottom:50%`
      : `top:50%;bottom:${(50 - h).toFixed(3)}%`;
    const lbl = up
      ? `top:calc(${(50 - h).toFixed(3)}% - 15px)`
      : `top:calc(${(50 + h).toFixed(3)}% + 2px)`;
    return `<div class="cb2-col">
      <span class="cb2-zero"></span>
      <span class="cb2-bar ${up ? "up" : "dn"}" style="${bar}"${
        tip(s.tip || `${s.label}: ${s.display}`).replace('class=', 'data-x=')}></span>
      <span class="cb2-val" style="${lbl}">${esc(s.display)}</span>
    </div>`;
  }).join("");

  const legend = opts.legend
    ? `<div class="hb-legend">${opts.legend.map((l) =>
        `<span><i style="background:${l.color}"></i>${esc(l.label)}</span>`).join("")}</div>`
    : "";
  const xs = `<div class="cb2-xrow">${series.map((s) =>
    `<span>${esc(s.label)}</span>`).join("")}</div>`;

  return `<div class="cb2">${legend}
    <div class="cb2-plot">${cols}</div>
    ${xs}
    ${opts.caption ? `<div class="cb2-cap">${esc(opts.caption)}</div>` : ""}
  </div>`;
}

/* ------------------------------------------------------------ line chart */
/**
 * A trend over time as a real line, with an optional reference line and a shaded band.
 * Used for monthly dynamics, where change bars cannot show shape.
 *
 * Drawn as inline SVG with a fixed viewBox and preserveAspectRatio, so it scales without
 * distorting and never clips its own axis labels. Each point carries a native title tooltip,
 * which works from file:// with no JavaScript.
 *
 * points: [{label, value, sub?, tip?}]
 * opts:   {height, fmt, refValue, refLabel, band, domainFromZero, aria, every}
 */
export function lineChart(points, opts = {}) {
  const pts = points.filter((p) => typeof p.value === "number" && Number.isFinite(p.value));
  if (pts.length < 2) {
    return `<p class="empty">${esc(opts.emptyText || "Not enough periods to show a trend.")}</p>`;
  }
  const W = 760, H = opts.height || 210;
  const PADL = 10, PADR = 10, PADT = 26, PADB = 30;
  const iw = W - PADL - PADR, ih = H - PADT - PADB;

  const vals = pts.map((p) => p.value);
  const lo0 = Math.min(...vals, opts.refValue ?? Infinity);
  const hi0 = Math.max(...vals, opts.refValue ?? -Infinity);
  const fromZero = opts.domainFromZero !== false;
  let lo = fromZero ? Math.min(0, lo0) : lo0;
  let hi = hi0;
  if (hi === lo) hi = lo + 1;
  const pad = (hi - lo) * 0.08;
  hi += pad;
  if (!fromZero) lo -= pad;

  const X = (n) => PADL + (pts.length === 1 ? iw / 2 : (n / (pts.length - 1)) * iw);
  const Y = (v) => PADT + ih - ((v - lo) / (hi - lo)) * ih;

  const line = pts.map((p, n) => `${n ? "L" : "M"}${X(n).toFixed(1)},${Y(p.value).toFixed(1)}`).join(" ");
  const areaP = `${line} L${X(pts.length - 1).toFixed(1)},${(PADT + ih).toFixed(1)} L${PADL.toFixed(1)},${(PADT + ih).toFixed(1)} Z`;

  // Reference line: the benchmark the reader should judge the shape against.
  const ref = (typeof opts.refValue === "number" && Number.isFinite(opts.refValue)
               && opts.refValue >= lo && opts.refValue <= hi)
    ? `<line x1="${PADL}" x2="${W - PADR}" y1="${Y(opts.refValue).toFixed(1)}"
         y2="${Y(opts.refValue).toFixed(1)}" stroke="#15233c" stroke-width="1.5"
         stroke-dasharray="5 4" opacity="0.65"></line>
       <text x="${W - PADR}" y="${(Y(opts.refValue) - 5).toFixed(1)}" text-anchor="end"
         font-family="Inter,sans-serif" font-size="10" fill="#5f6b80">${esc(opts.refLabel || "reference")}</text>`
    : "";

  // Shaded band between two series values, e.g. a peer range.
  const band = (opts.band && opts.band.low && opts.band.high)
    ? `<path d="${opts.band.high.map((v, n) => `${n ? "L" : "M"}${X(n).toFixed(1)},${Y(v).toFixed(1)}`).join(" ")}
         ${opts.band.low.slice().reverse().map((v, n) =>
           `L${X(opts.band.low.length - 1 - n).toFixed(1)},${Y(v).toFixed(1)}`).join(" ")} Z"
         fill="#15233c" opacity="0.07"></path>`
    : "";

  const step = opts.every || Math.max(1, Math.ceil(pts.length / 9));
  const labels = pts.map((p, n) => (n % step === 0 || n === pts.length - 1)
    ? `<text x="${X(n).toFixed(1)}" y="${(H - 10).toFixed(1)}" text-anchor="middle"
         font-family="Inter,sans-serif" font-size="10" fill="#5f6b80">${esc(p.label)}</text>`
    : "").join("");

  const dots = pts.map((p, n) => {
    const t = p.tip || `${p.label}: ${opts.fmt ? opts.fmt(p.value) : p.value}`;
    return `<g><circle cx="${X(n).toFixed(1)}" cy="${Y(p.value).toFixed(1)}" r="3.2"
        fill="#c0552d"><title>${esc(t)}</title></circle></g>`;
  }).join("");

  const grid = [0, 0.5, 1].map((f) => {
    const v = lo + (hi - lo) * f;
    return `<line x1="${PADL}" x2="${W - PADR}" y1="${Y(v).toFixed(1)}" y2="${Y(v).toFixed(1)}"
      stroke="#e3dcd1" stroke-width="1"></line>
      <text x="${PADL}" y="${(Y(v) - 4).toFixed(1)}" font-family="Inter,sans-serif"
        font-size="9.5" fill="#8b97ab">${esc(opts.fmt ? opts.fmt(v) : Math.round(v))}</text>`;
  }).join("");

  return `<div class="lc">
    <svg viewBox="0 0 ${W} ${H}" preserveAspectRatio="xMidYMid meet" role="img"
         aria-label="${esc(opts.aria || "Trend over time")}">
      ${grid}${band}${ref}${grid ? "" : ""}
      <path d="${areaP}" fill="#c0552d" opacity="0.10"></path>
      <path d="${line}" fill="none" stroke="#c0552d" stroke-width="2.2"
        stroke-linejoin="round" stroke-linecap="round"></path>
      ${dots}${labels}
    </svg>
    ${opts.caption ? `<p class="note">${esc(opts.caption)}</p>` : ""}
  </div>`;
}

/* --------------------------------------------------- in-panel selector */
/**
 * A labelled dropdown that drives a panel. Used where a panel would otherwise show a wall of
 * small multiples: one chart, and the reader picks which part to look at.
 *
 * options: [{value, label}]
 * onSet:   the name of a global function called as fn(moduleId, key, value)
 */
export function selectControl(moduleId, key, options, current, label, onSet = "__LEAK_SET") {
  const opts = options.map((o) =>
    `<option value="${esc(o.value)}"${o.value === current ? " selected" : ""}>${esc(o.label)}</option>`
  ).join("");
  return `<div class="selctl">
    <label for="sel-${esc(moduleId)}-${esc(key)}">${esc(label)}</label>
    <select id="sel-${esc(moduleId)}-${esc(key)}"
      onchange="${esc(onSet)}('${esc(moduleId)}','${esc(key)}',this.value)">${opts}</select>
  </div>`;
}

/* --------------------------------------------------------- bullet bar rows */
/**
 * A value against a target, on one line. Used for a monthly figure against a target month,
 * where two separate bars would mislead by implying two different quantities.
 */
export function bulletRows(rows, opts = {}) {
  const max = opts.max || Math.max(...rows.map((r) => Math.max(r.value || 0, r.target || 0)), 1);
  const body = rows.map((r) => {
    const vp = (Math.abs(r.value || 0) / max) * 100;
    const tp = (Math.abs(r.target || 0) / max) * 100;
    return `<div class="hb-row">
      <div class="hb-lab">${esc(r.label)}${r.sub ? `<span class="hb-sub">${esc(r.sub)}</span>` : ""}</div>
      <div class="hb-track"><div class="hb-fill${r.cls ? " " + r.cls : ""}" style="width:${vp}%"></div>
        ${r.target ? `<span class="hb-ref" style="left:${tp}%" title="${esc(opts.targetLabel || "Target")}"></span>` : ""}</div>
      <div class="hb-val">${r.display}
        ${r.targetNote ? `<span class="u">${esc(r.targetNote)}</span>` : ""}</div>
    </div>`;
  }).join("");
  const legend = opts.legend
    ? `<div class="hb-legend">${opts.legend.map((l) =>
        `<span><i style="background:${l.color}"></i>${esc(l.label)}</span>`).join("")}</div>`
    : "";
  return `<div class="hb">${legend}${body}</div>`;
}

/* ------------------------------------------------------------ stacked bars */
/** series: [{label, total, totalDisplay, segs:[{value, color, tip}]}] */
export function stackedBars(series, opts = {}) {
  const max = Math.max(...series.map((s) => s.total ?? 0), 1);
  const cols = series.map((s) => {
    const h = ((s.total ?? 0) / max) * 100;
    const segs = (s.segs || []).map((g) => {
      const share = s.total ? (g.value / s.total) * 100 : 0;
      return `<div class="stk-seg" style="height:${(share * h / 100).toFixed(3)}%;background:${g.color}"${
        tip(g.tip).replace('class=', 'data-x=')}></div>`;
    }).join("");
    return `<div class="stk-col" style="height:${Math.max(h, 2)}%">
      ${s.totalDisplay ? `<span class="stk-tot">${esc(s.totalDisplay)}</span>` : ""}
      ${segs}<span class="stk-x">${esc(s.label)}</span></div>`;
  }).join("");
  const legend = opts.legend
    ? `<div class="hb-legend">${opts.legend.map((l) =>
        `<span><i style="background:${l.color}"></i>${esc(l.label)}</span>`).join("")}</div>`
    : "";
  return `${legend}<div class="stk">${cols}</div>`;
}

/* --------------------------------------------------------------- donut */
/** segs: [{label, value, color}] - hard cap at 4 segments; caller must pre-group. */
export function donut(segs, opts = {}) {
  const tot = segs.reduce((a, s) => a + (s.value || 0), 0);
  if (!tot) return `<p class="empty">${esc(opts.emptyText || "Nothing to show")}</p>`;
  const R = 62, SW = 26, C = 2 * Math.PI * R;
  let off = 0;
  const arcs = segs.map((s) => {
    const frac = (s.value || 0) / tot;
    const el = `<circle cx="88" cy="88" r="${R}" fill="none" stroke="${s.color}"
      stroke-width="${SW}" stroke-dasharray="${(frac * C).toFixed(2)} ${C.toFixed(2)}"
      stroke-dashoffset="${(-off * C).toFixed(2)}" transform="rotate(-90 88 88)"></circle>`;
    off += frac;
    return el;
  }).join("");
  const center = opts.center
    ? `<text x="88" y="84" text-anchor="middle" font-family="Georgia,serif" font-size="21"
         fill="#15233c">${esc(opts.center.value)}</text>
       <text x="88" y="101" text-anchor="middle" font-family="Inter,sans-serif" font-size="9.5"
         fill="#5f6b80" letter-spacing="0.06em">${esc(opts.center.label)}</text>` : "";
  const key = segs.map((s) => `<div><i style="background:${s.color}"></i>${esc(s.label)}
    <b>${fmtPct((s.value / tot) * 100)}</b>${s.sub ? ` <span style="color:#5f6b80">${esc(s.sub)}</span>` : ""}</div>`).join("");
  return `<div class="donut">
    <svg width="176" height="176" viewBox="0 0 176 176" role="img" aria-label="${esc(opts.aria || "Mix")}">
      <circle cx="88" cy="88" r="${R}" fill="none" stroke="#efe9df" stroke-width="${SW}"></circle>
      ${arcs}${center}
    </svg>
    <div class="donut-key">${key}</div>
  </div>`;
}

/* ------------------------------------------------------- small multiples */
/**
 * rows: [{label, sub?, cells:[{value, display, state}], tailHtml}]
 * Used for family x year trajectories. Never overlays many series on one axis.
 */
export function smallMultiples(rows, cols, opts = {}) {
  const max = opts.max || Math.max(...rows.flatMap((r) => r.cells.map((c) => Math.abs(c.value ?? 0))), 1);
  const head = `<div class="tr-head"><div>${esc(opts.rowHead || "")}</div>
    <div>${cols.map((c) => `<span style="margin-right:14px">${esc(c)}</span>`).join("")}</div>
    <div class="c">${esc(opts.valHead || "")}</div></div>`;
  const body = rows.map((r) => {
    const cells = r.cells.map((c, n) => {
      const h = Math.max(2, (Math.abs(c.value ?? 0) / max) * 100);
      const cls = c.state === "weak" ? " weak" : c.state === "good" ? " good" : "";
      return `<div class="tr-cell">
        <div class="tr-bar${cls}" style="height:${h}%"${
          tip(c.tip).replace('class=', 'data-x=')}></div>
        <span class="tr-yr">${esc(cols[n] ?? "")}</span>
      </div>`;
    }).join("");
    return `<div class="tr-row">
      <div class="tr-lab"${tip(r.tip).replace('class=', 'data-x=')}>${esc(r.label)}${
        r.sub ? `<span class="u">${esc(r.sub)}</span>` : ""}</div>
      <div class="tr-cells">${cells}</div>
      <div class="tr-val">${r.tailHtml || ""}</div>
    </div>`;
  }).join("");
  return `<div class="tr">${head}${body}</div>`;
}

/* ----------------------------------------------------------- heat table */
/**
 * rows: [{label, cells:[{text, level, tip}]}]  level 1 = worst .. 5 = best, n = not measured
 * A heat table replaces 18 overlapping lines: same question, readable at a glance.
 */
export function heatTable(rows, cols, opts = {}) {
  const head = `<tr><th>${esc(opts.rowHead || "")}</th>${
    cols.map((c) => `<th class="s">${esc(c)}</th>`).join("")}${
    opts.tailHead ? `<th class="s">${esc(opts.tailHead)}</th>` : ""}</tr>`;
  const body = rows.map((r) => `<tr>
    <td class="lbl">${esc(r.label)}</td>
    ${r.cells.map((c) => c.level === "n"
      ? `<td class="cell cn">·</td>`
      : `<td class="cell c${c.level}"${tip(c.tip).replace('class=', 'data-x=')}>${esc(c.text)}</td>`).join("")}
    ${opts.tailHead ? `<td class="cell">${r.tailHtml || ""}</td>` : ""}
  </tr>`).join("");
  return `<div class="tw"><table class="hm"><thead>${head}</thead><tbody>${body}</tbody></table></div>`;
}

/* ---------------------------------------------------------------- table */
export function table(headers, rows, opts = {}) {
  const th = headers.map((h) => `<th${h.num ? ' class="s"' : ""}>${esc(h.label)}</th>`).join("");
  const body = rows.map((r) => `<tr${r.cls ? ` class="${r.cls}"` : ""}>${
    r.cells.map((c, n) => `<td${headers[n]?.num ? ' class="num"' : c.lbl ? ' class="lbl"' : ""}${
      c.tip ? tip(c.tip).replace('class=', 'data-x=') : ""}>${c.html ?? esc(c.text ?? "")}</td>`).join("")}</tr>`).join("");
  const foot = opts.foot
    ? `<tfoot><tr>${opts.foot.map((c, n) =>
        `<td${headers[n]?.num ? ' class="num"' : ""}>${c.html ?? esc(c.text ?? "")}</td>`).join("")}</tr></tfoot>`
    : "";
  return `<div class="tw"><table>${opts.caption ? `<caption>${esc(opts.caption)}</caption>` : ""}
    <thead><tr>${th}</tr></thead><tbody>${body}</tbody>${foot}</table></div>`;
}

/* ------------------------------------------------------------ peer helper */
/**
 * Peer comparison is always anonymous and always the same customer type.
 * Groups with fewer than `min` members are suppressed rather than averaged, because a
 * median of two reads as a benchmark when it is not one.
 * Returns null when there is nothing legitimate to show.
 */
export function peerView(stats, members, min = 3, opts = {}) {
  if (!stats || members < min) return null;
  return {
    ...stats,
    note: opts.note || `Median across ${members} comparable markets`,
    anonymous: true,
  };
}
