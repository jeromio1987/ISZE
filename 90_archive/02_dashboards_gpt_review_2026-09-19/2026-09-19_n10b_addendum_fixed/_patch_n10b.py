# -*- coding: utf-8 -*-
"""Patch N10B-048..061 into review copies only. Do not touch live originals."""
from __future__ import annotations

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent
DBS = {
    "04": "ITUK",
    "05": "BELGIUM",
    "06": "SWEDEN",
}


def extract_json_obj(text: str, key: str) -> tuple[str, int, int] | None:
    marker = f'"{key}"'
    idx = text.find(marker)
    if idx < 0:
        return None
    brace = text.find("{", idx)
    depth = 0
    i = brace
    while i < len(text):
        c = text[i]
        if c == "{":
            depth += 1
        elif c == "}":
            depth -= 1
            if depth == 0:
                return text[brace : i + 1], brace, i + 1
        i += 1
    return None


def replace_json_obj(text: str, key: str, new_obj: dict) -> str:
    found = extract_json_obj(text, key)
    if not found:
        raise RuntimeError(f"missing object {key}")
    raw, start, end = found
    # Preserve indentation style roughly: dump compact-ish with 2-space like source
    dumped = json.dumps(new_obj, ensure_ascii=False, indent=2)
    # indent dumped to match surrounding (2 spaces from key level typically 4)
    # Detect indent of the opening brace line
    line_start = text.rfind("\n", 0, start) + 1
    base_indent = start - line_start
    pad = " " * base_indent
    lines = dumped.splitlines()
    # first line is "{"; subsequent lines need pad
    rebuilt = [lines[0]] + [pad + ln if ln else ln for ln in lines[1:]]
    return text[:start] + "\n".join(rebuilt) + text[end:]


def strip_peer_medians(text: str) -> tuple[str, dict]:
    """N10B-048: keep only non-thin peerOrder groups in peerGroups/peerOrder/peerMedians."""
    pg_raw, _, _ = extract_json_obj(text, "peerGroups")
    pm_raw, _, _ = extract_json_obj(text, "peerMedians")
    pg = json.loads(pg_raw)
    pm = json.loads(pm_raw)
    po_m = re.search(r'"peerOrder"\s*:\s*(\[[^\]]+\])', text)
    if not po_m:
        raise RuntimeError("peerOrder missing")
    po = json.loads(po_m.group(1))

    keep = [k for k in po if k in pg and not pg[k].get("thin")]
    new_pg = {k: pg[k] for k in keep}
    new_pm = {k: pm[k] for k in keep if k in pm}
    # If defaultPeer was thin / removed, fall back to first keep
    dm = re.search(r'"defaultPeer"\s*:\s*"([^"]+)"', text)
    default = dm.group(1) if dm else None
    if default and default not in keep and keep:
        text = text.replace(f'"defaultPeer": "{default}"', f'"defaultPeer": "{keep[0]}"', 1)
        default = keep[0]

    text = replace_json_obj(text, "peerGroups", new_pg)
    text = replace_json_obj(text, "peerMedians", new_pm)
    new_po_json = json.dumps(keep)
    text = re.sub(r'"peerOrder"\s*:\s*\[[^\]]+\]', f'"peerOrder": {new_po_json}', text, count=1)

    info = {
        "kept": keep,
        "removed_medians": sorted(set(pm) - set(keep)),
        "removed_thin_groups": [k for k in po if k in pg and pg[k].get("thin")],
        "defaultPeer": default,
    }
    return text, info


def fix_belgium_basis_labels(text: str) -> tuple[str, int]:
    """N10B-049 data: do not claim schedules agree when CV/LCV intervals differ."""
    n = 0
    # Exact misleading label used when intervals differ
    old = '"basis_label": "Both maintenance schedules agree"'
    new = '"basis_label": "Truck and pickup schedules differ (truck 40,000 km / pickup 20,000 km)"'
    if old in text:
        count = text.count(old)
        text = text.replace(old, new)
        n += count
    return text, n


# Shared PMS render patches applied to 04/05/06
PMS_HELPERS = r'''
    /* N10B-049: show the interval that actually applies to this fleet. */
    const applicableIntervalKm = (c) => {
      if (!c) return null;
      if (c.basis === "lcv_schedule" && c.interval_lcv_km) return c.interval_lcv_km;
      if (c.basis === "cv_schedule" && c.interval_cv_km) return c.interval_cv_km;
      if (c.basis === "both_schedules" && c.interval_cv_km && c.interval_lcv_km
          && c.interval_cv_km !== c.interval_lcv_km) return null;
      return (c.interval_km || c.interval_lcv_km || c.interval_cv_km || null);
    };
    const formatIntervalCell = (c) => {
      if (!c) return "\u2013";
      if (c.basis === "both_schedules" && c.interval_cv_km && c.interval_lcv_km
          && c.interval_cv_km !== c.interval_lcv_km) {
        return `Truck ${fmtInt(c.interval_cv_km)} / pickup ${fmtInt(c.interval_lcv_km)} km`;
      }
      const km = applicableIntervalKm(c);
      return km ? `${fmtInt(km)} km` : (c.interval_km ? `${fmtInt(c.interval_km)} km` : "\u2013");
    };
    const intervalTipKm = (c) => applicableIntervalKm(c) || c.interval_km || null;

    /* N10B-050: H1 rate and shortfall share the same six-month expectation. */
    const periodStats = (c, y) => {
      const s = (c.years || []).find((x) => x.year === y);
      if (!s) return null;
      const isPart = !!s.is_part_year || y === cy;
      const expFull = s.expected_qty_adj;
      const expPeriod = (expFull === null || expFull === undefined)
        ? null
        : (isPart ? expFull * 0.5 : expFull);
      const act = s.actual_qty;
      const unbought = (expPeriod === null || expPeriod === undefined || act === null || act === undefined)
        ? null
        : Math.max(0, expPeriod - act);
      const gap = (unbought === null || s.avg_price_eur === null || s.avg_price_eur === undefined)
        ? null
        : unbought * s.avg_price_eur;
      return { s, isPart, expPeriod, act, unbought, gap, avg: s.avg_price_eur };
    };
'''


def patch_pms_render(text: str) -> str:
    """Inject helpers and fix tips / interval / firm / trend / constant-fleet / above-100 wording."""
    # Insert helpers after `const cy = ...`
    anchor = "    const cy = ctx.payload.meta.current_year;\n"
    if "applicableIntervalKm" not in text:
        if anchor not in text:
            raise RuntimeError("cy anchor missing")
        text = text.replace(anchor, anchor + PMS_HELPERS, 1)

    # N10B-050 + 049: heat-map tip uses period stats + applicable interval
    old_tip = (
        "tip: `${c.category}, ${y}${isPart ? \" (first six months)\" : \"\"}: captured ${fmtPct(v)} of the expected service demand. "
        "Expected ${fmtInt(s.expected_qty_adj)} units, billed ${fmtInt(s.actual_qty)}. Unbought ${fmtInt(s.unbought_qty)} units, "
        "worth ${fmtEur(s.gap_eur)} at the average selling price of ${fmtEurExact(s.avg_price_eur)}."
        "${isPart ? \" The current year is on the same six-month basis as the year before.\" : \"\"}"
        "${c.interval_confirmed ? ` Expected demand uses the scheduled replacement interval of ${fmtInt(c.interval_km)} km.` : "
        "\" This category has no replacement interval in the maintenance schedule, so the expected demand rests on the model's placeholder factor and the percentage is indicative only.\"}`,"
    )
    new_tip = (
        "tip: (() => { const ps = periodStats(c, y); const ik = intervalTipKm(c);"
        " return `${c.category}, ${y}${ps && ps.isPart ? \" (first six months)\" : \"\"}: captured ${fmtPct(v)} of the expected service demand"
        "${ps && ps.isPart ? \" for those six months\" : \"\"}. "
        "Expected ${fmtInt(ps ? ps.expPeriod : null)} units, billed ${fmtInt(ps ? ps.act : null)}. "
        "Unbought ${fmtInt(ps ? ps.unbought : null)} units, worth ${fmtEur(ps ? ps.gap : null)} "
        "at the average selling price of ${fmtEurExact(ps ? ps.avg : null)}."
        "${ps && ps.isPart ? \" Rate, expectation and shortfall all use the same six-month window (half of the annual schedule).\" : \"\"}"
        "${c.interval_confirmed && ik ? ` Expected demand uses the scheduled replacement interval of ${fmtInt(ik)} km.` : "
        "(!c.interval_confirmed ? \" This category has no replacement interval in the maintenance schedule, so the expected demand rests on the model's placeholder factor and the percentage is indicative only.\" : \"\")}`; })(),"
    )
    # The heat map builds tip inside cells map — replace the tip line by matching a unique fragment
    frag_old = "Expected ${fmtInt(s.expected_qty_adj)} units, billed ${fmtInt(s.actual_qty)}. Unbought ${fmtInt(s.unbought_qty)} units, worth ${fmtEur(s.gap_eur)} at the average selling price of ${fmtEurExact(s.avg_price_eur)}.${isPart ? \" The current year is on the same six-month basis as the year before.\" : \"\"}${c.interval_confirmed ? ` Expected demand uses the scheduled replacement interval of ${fmtInt(c.interval_km)} km.` : \" This category has no replacement interval in the maintenance schedule, so the expected demand rests on the model's placeholder factor and the percentage is indicative only.\"}`,"
    frag_new = (
        "${(() => { const ps = periodStats(c, y); const ik = intervalTipKm(c);"
        " return `Expected ${fmtInt(ps ? ps.expPeriod : null)} units"
        "${ps && ps.isPart ? \" for the first six months\" : \"\"}, billed ${fmtInt(ps ? ps.act : null)}. "
        "Unbought ${fmtInt(ps ? ps.unbought : null)} units, worth ${fmtEur(ps ? ps.gap : null)} "
        "at the average selling price of ${fmtEurExact(ps ? ps.avg : null)}."
        "${ps && ps.isPart ? \" Rate, expectation and shortfall use the same six-month window.\" : \"\"}"
        "${c.interval_confirmed && ik ? ` Expected demand uses the scheduled replacement interval of ${fmtInt(ik)} km.` : "
        "(!c.interval_confirmed ? \" This category has no replacement interval in the maintenance schedule, so the expected demand rests on the model's placeholder factor and the percentage is indicative only.\" : \"\")}`; })()}`,"
    )
    if frag_old not in text:
        raise RuntimeError("heatmap tip fragment not found")
    text = text.replace(frag_old, frag_new, 1)

    # Also need to remove unused `const s = ... isPart` if tip no longer uses them — keep them; still used? 
    # Looking at original: const s and isPart are only for tip. After patch tip uses periodStats.
    # Leave the const s / isPart lines — harmless, or clean them.
    text = text.replace(
        "          const s = (c.years || []).find((x) => x.year === y);\n"
        "          const isPart = y === cy;\n"
        "          return {\n"
        "            level: captureLevel(v), text: `${Math.round(v)}%`,\n"
        "            tip: `${c.category}, ${y}${isPart ? \" (first six months)\" : \"\"}: captured ${fmtPct(v)} of the expected service demand. ",
        "          return {\n"
        "            level: captureLevel(v), text: `${Math.round(v)}%`,\n"
        "            tip: `${c.category}, ${y}${y === cy ? \" (first six months)\" : \"\"}: captured ${fmtPct(v)} of the expected service demand. ",
        1,
    )

    # N10B-052: suppress trend when no eligible numeric annual cells
    old_tail = (
        "        tailHtml: (c.slope_pp === null || c.slope_pp === undefined) ? \"\"\n"
        "          : `${fmtPP(c.slope_pp)}${c.declining ? \" \" + pill(\"slipping\", \"crit\") : \"\"}`,"
    )
    new_tail = (
        "        tailHtml: (() => {\n"
        "          const eligible = years.filter((y) => {\n"
        "            const v = capOf(c, y);\n"
        "            return v !== null && v !== undefined;\n"
        "          }).length;\n"
        "          if (eligible < 2 || c.slope_pp === null || c.slope_pp === undefined) return \"\";\n"
        "          return `${fmtPP(c.slope_pp)}${c.declining ? \" \" + pill(\"slipping\", \"crit\") : \"\"}`;\n"
        "        })(),"
    )
    if old_tail not in text:
        raise RuntimeError("tailHtml block not found")
    text = text.replace(old_tail, new_tail, 1)

    # N10B-053: firm headline when unit_definition_open
    old_gap_card = (
        "        { label: L.term.gap, value: fmtEur(r.metric_gap_firm_eur), small: true,\n"
        "          sub: \"on sourced intervals, firm\",\n"
        "          tip: \"Expected service demand not billed, valued at the observed average selling price, counting only the families with a sourced replacement interval.\" },"
    )
    new_gap_card = (
        "        { label: L.term.gap, value: fmtEur(r.metric_gap_firm_eur), small: true,\n"
        "          sub: (cats.some((c) => c.unit_definition_open)\n"
        "            ? \"on sourced intervals, conditional on unit definition\"\n"
        "            : \"on sourced intervals, firm\"),\n"
        "          tip: cats.some((c) => c.unit_definition_open)\n"
        "            ? \"Expected service demand not billed on sourced intervals, but one or more brake families still have an open billed-unit definition, so this aggregate is conditional rather than firm.\"\n"
        "            : \"Expected service demand not billed, valued at the observed average selling price, counting only the families with a sourced replacement interval.\" },"
    )
    if old_gap_card not in text:
        raise RuntimeError("gap card not found")
    text = text.replace(old_gap_card, new_gap_card, 1)

    # N10B-049: interval column + captions use formatIntervalCell / applicableIntervalKm
    text = text.replace(
        "{ text: c.interval_km ? `${fmtInt(c.interval_km)} km` : \"\\u2013\" },",
        "{ text: formatIntervalCell(c), tip: c.interval_note },",
        1,
    )
    # basis cell already has tip: c.interval_note — duplicate tip OK on interval now; remove from basis to avoid double
    text = text.replace(
        "{ text: c.basis_label, tip: c.interval_note },",
        "{ text: c.basis_label },",
        1,
    )

    text = text.replace(
        "`Expected demand uses the scheduled replacement interval of ${fmtInt(chosenCat.interval_km)} km, which is a sourced figure.`",
        "`Expected demand uses the scheduled replacement interval of ${fmtInt(intervalTipKm(chosenCat))} km, which is a sourced figure.`",
        1,
    )

    # N10B-051: label constant-fleet historical comparison on the heat note
    old_note = (
        "      <p class=\"note\">A stronger tint means a smaller share of the service demand the fleet implies\n"
        "        was actually billed. A dot means no measurement for that family in that year. A dot beside a\n"
        "        family name means <b>no replacement interval exists in the maintenance schedule</b> for that\n"
        "        part, so its expected demand rests on the model's placeholder rather than on a sourced\n"
        "        interval. Those rows are shown, because dropping them would hide the gap, but their level is\n"
        "        indicative and their movement is the reliable part.</p>"
    )
    new_note = (
        "      <p class=\"note\">A stronger tint means a smaller share of the service demand the fleet implies\n"
        "        was actually billed. A dot means no measurement for that family in that year. A dot beside a\n"
        "        family name means <b>no replacement interval exists in the maintenance schedule</b> for that\n"
        "        part, so its expected demand rests on the model's placeholder rather than on a sourced\n"
        "        interval. Those rows are shown, because dropping them would hide the gap, but their level is\n"
        "        indicative only — and with fewer than two measured years, no trend is shown.\n"
        "        <b>Historical comparison is rebased to a constant fleet and schedule assumptions</b>\n"
        "        (the current service basis held fixed across 2023–2025), so percentage movement tracks billed\n"
        "        volume against that fixed expectation, not each year's own fleet size.</p>"
    )
    if old_note not in text:
        raise RuntimeError("heat note not found")
    text = text.replace(old_note, new_note, 1)

    # Detail chart tip for chosen family — period-align CY tip
    old_detail_tip = (
        "tip: `${chosenCat.category} ${y}: captured ${v === null || v === undefined ? \"not measured\" : fmtPct(v)} of expected demand. "
        "Expected ${fmtInt(s ? s.expected_qty_adj : null)} units, billed ${fmtInt(s ? s.actual_qty : null)}, "
        "unbought ${fmtInt(s ? s.unbought_qty : null)} worth ${fmtEur(s ? s.gap_eur : null)}.`,"
    )
    new_detail_tip = (
        "tip: (() => { const ps = periodStats(chosenCat, y);"
        " return `${chosenCat.category} ${y}: captured ${v === null || v === undefined ? \"not measured\" : fmtPct(v)} of expected demand"
        "${ps && ps.isPart ? \" (six-month window)\" : \"\"}. "
        "Expected ${fmtInt(ps ? ps.expPeriod : null)} units, billed ${fmtInt(ps ? ps.act : null)}, "
        "unbought ${fmtInt(ps ? ps.unbought : null)} worth ${fmtEur(ps ? ps.gap : null)}.`; })(),"
    )
    if old_detail_tip not in text:
        raise RuntimeError("detail tip not found")
    text = text.replace(old_detail_tip, new_detail_tip, 1)

    # Suppress slope sentence in caption when trend not eligible
    text = text.replace(
        "${chosenCat.slope_pp !== null && chosenCat.slope_pp !== undefined ? ` The fitted trend is ${chosenCat.slope_pp > 0 ? \"improving\" : \"falling\"} by ${Math.abs(chosenCat.slope_pp).toFixed(1)} percentage points a year.` : \"\"}",
        "${(years.filter((y) => { const v = capOf(chosenCat, y); return v !== null && v !== undefined; }).length >= 2 && chosenCat.slope_pp !== null && chosenCat.slope_pp !== undefined) ? ` The fitted trend is ${chosenCat.slope_pp > 0 ? \"improving\" : \"falling\"} by ${Math.abs(chosenCat.slope_pp).toFixed(1)} percentage points a year.` : \"\"}",
        1,
    )

    return text


def patch_above_100_wording(text: str) -> int:
    """N10B-061: soften causal claim for >100% cover."""
    n = 0
    pairs = [
        (
            "That means the assumed demand is too low, not that the market over-performs.",
            "That means billed units exceed the stated model expectation. Plausible checks are understated demand, sales into another vehicle segment or brand, stocking timing, or another scope difference — the ratio alone does not pick the cause.",
        ),
        (
            "That means the assumed demand is too\n        low for ${sc.over_100 === 1 ? \"that family\" : \"those families\"}, not that the market\n        over-performs.",
            "That means billed units exceed the stated model expectation for ${sc.over_100 === 1 ? \"that family\" : \"those families\"}. The ratio alone does not prove whether demand is understated, the sales population is broader than the model fleet, or timing/scope differs.",
        ),
    ]
    for a, b in pairs:
        if a in text:
            text = text.replace(a, b)
            n += 1
    return text, n


def patch_distributor_css_js(text: str) -> str:
    """N10B-054 zero bars, 055 tabindex, 056 scroll-margin, 057 print keep-together."""
    # tip helper → keyboard focusable
    text = text.replace(
        'const tip = (s) => (s ? ` data-tip="${esc(s).replace(/&#39;/g, "\'")}"` : "");',
        'const tip = (s) => (s ? ` data-tip="${esc(s).replace(/&#39;/g, "\'")}" tabindex="0"` : "");',
        1,
    )
    # zero bars: no min-width when empty
    text = text.replace(
        ".hb-fill{height:100%;background:var(--terra);border-radius:4px;min-width:3px}",
        ".hb-fill{height:100%;background:var(--terra);border-radius:4px;min-width:0}"
        ".hb-fill[data-nz=\"1\"]{min-width:3px}",
        1,
    )
    # barRows fill style
    old_fill = '<div class="hb-fill${fillCls}" style="width:${pos(r.value)}%"></div>${ref}</div>'
    new_fill = (
        '<div class="hb-fill${fillCls}" data-nz="${(r.value && Math.abs(r.value) > 0) ? 1 : 0}" '
        'style="width:${(r.value && Math.abs(r.value) > 0) ? pos(r.value) : 0}%"></div>${ref}</div>'
    )
    if old_fill not in text:
        raise RuntimeError("barRows fill not found")
    text = text.replace(old_fill, new_fill, 1)

    # scroll-margin mobile
    if "scroll-margin-top:120px" not in text:
        text = text.replace(
            "@media (max-width:620px){\n"
            "  main{padding:12px 13px 60px} header.top{padding:10px 14px} nav.mods{padding:12px 13px 0}",
            "@media (max-width:620px){\n"
            "  section{scroll-margin-top:120px}\n"
            "  main{padding:12px 13px 60px} header.top{padding:10px 14px} nav.mods{padding:12px 13px 0}",
            1,
        )

    # print keep-together
    old_print = (
        "@media print{\n"
        "  header.top{position:static;background:var(--navy) !important;-webkit-print-color-adjust:exact;print-color-adjust:exact}\n"
        "  nav.mods{display:none}\n"
        "  .panel{box-shadow:none;break-inside:avoid}\n"
        "  section{break-inside:avoid}\n"
        "  body{background:#fff}\n"
        "}"
    )
    new_print = (
        "@media print{\n"
        "  header.top{position:static;background:var(--navy) !important;-webkit-print-color-adjust:exact;print-color-adjust:exact}\n"
        "  nav.mods{display:none}\n"
        "  .panel{box-shadow:none;break-inside:avoid}\n"
        "  section{break-inside:auto}\n"
        "  .hb,.hb-row,.note,.banner,table,tr,.kpi-grid,.stack > *{break-inside:avoid;page-break-inside:avoid}\n"
        "  h3,h4{break-after:avoid;page-break-after:avoid}\n"
        "  body{background:#fff}\n"
        "}"
    )
    if old_print in text:
        text = text.replace(old_print, new_print, 1)
    return text


def patch_file03(text: str) -> str:
    """N10B-054 chart scale for above-100%; N10B-055 keyboard on bar rows."""
    # paintResidual stacked bar scale
    old = """  document.getElementById('main').innerHTML='<div class="bars">'+rows.map(r=>{
    const mix=mixFor(r.db);
    const exp=Math.max(r.expected_qty||0,1);
    const gq=Math.max((mix.g&&mix.g.actual_qty)||0,0);
    const bq=Math.max((mix.b&&mix.b.actual_qty)||0,0);
    const miss=Math.max(0, exp-(r.actual_qty||0));
    const sg=gq/exp*100, sb=bq/exp*100, sm=miss/exp*100;
    return '<div class="bar-row'+(r.db===selDb?' sel':'')+'" data-db="'+r.db+'" title="Expected '+num(exp)+'">'+
      '<span class="lbl">'+r.label+'</span>'+
      '<span class="track">'+
        '<span class="fill g" style="width:'+sg+'%"></span>'+
        '<span class="fill b" style="width:'+sb+'%"></span>'+
        '<span class="fill m" style="width:'+sm+'%"></span>'+
      '</span>'+
      '<span class="val">'+pct(r.capture)+'</span></div>';
  }).join('')+'</div>'+
  '<p class="ask" style="margin-top:10px"><span style="color:#15233c">■</span> Genuine · <span style="color:#3f5a86">■</span> Best-value · <span style="color:#c0552d">■</span> Not bought — each bar is 100% of expected units.</p>';"""

    new = """  document.getElementById('main').innerHTML='<div class="bars">'+rows.map(r=>{
    const mix=mixFor(r.db);
    const exp=Math.max(r.expected_qty||0,1);
    const gq=Math.max((mix.g&&mix.g.actual_qty)||0,0);
    const bq=Math.max((mix.b&&mix.b.actual_qty)||0,0);
    const miss=Math.max(0, exp-(r.actual_qty||0));
    const sgRaw=gq/exp*100, sbRaw=bq/exp*100, smRaw=miss/exp*100;
    /* N10B-054: common scale with room above 100% expected — do not let flex shrink exceedances. */
    const scale=Math.max(100, sgRaw+sbRaw+smRaw);
    const sg=sgRaw/scale*100, sb=sbRaw/scale*100, sm=smRaw/scale*100;
    const refLeft=(100/scale)*100;
    const over= (r.actual_qty||0) > exp;
    return '<div class="bar-row'+(r.db===selDb?' sel':'')+'" data-db="'+r.db+'" tabindex="0" role="button" title="Expected '+num(exp)+(over?' · billed above expected':'')+'">'+
      '<span class="lbl">'+r.label+'</span>'+
      '<span class="track" style="position:relative">'+
        '<span class="fill g" style="width:'+sg+'%;flex-shrink:0"></span>'+
        '<span class="fill b" style="width:'+sb+'%;flex-shrink:0"></span>'+
        '<span class="fill m" style="width:'+sm+'%;flex-shrink:0"></span>'+
        '<span class="ref100" style="left:'+refLeft+'%" title="100% of expected"></span>'+
      '</span>'+
      '<span class="val">'+pct(r.capture)+(over?' · above model':'')+'</span></div>';
  }).join('')+'</div>'+
  '<p class="ask" style="margin-top:10px"><span style="color:#15233c">■</span> Genuine · <span style="color:#3f5a86">■</span> Best-value · <span style="color:#c0552d">■</span> Not bought — the track scale is at least 100% of expected units; a mark shows the 100% line when any market exceeds it.</p>';"""

    if old not in text:
        raise RuntimeError("paintResidual block not found")
    text = text.replace(old, new, 1)

    # CSS for ref100 + flex-shrink
    if ".ref100" not in text:
        text = text.replace(
            ".bar-row .track{height:14px;background:#eef0f4;border-radius:3px;overflow:hidden;min-width:0;display:flex;position:relative}",
            ".bar-row .track{height:14px;background:#eef0f4;border-radius:3px;overflow:hidden;min-width:0;display:flex;position:relative}"
            ".bar-row .ref100{position:absolute;top:-2px;bottom:-2px;width:2px;background:#15233c;opacity:.7;z-index:2}"
            ".bar-row .fill{flex-shrink:0}",
            1,
        )

    # keyboard on bar rows — enhance bindClicks if present
    if "keydown" not in text[text.find("function bindClicks") : text.find("function bindClicks") + 800]:
        old_bind = None
        m = re.search(r"function bindClicks\(sel\)\{[^}]+\}", text)
        if m:
            old_bind = m.group(0)
            new_bind = (
                "function bindClicks(sel){"
                "document.querySelectorAll(sel).forEach(el=>{"
                "el.setAttribute('tabindex','0');"
                "el.setAttribute('role','button');"
                "const go=()=>{const db=el.getAttribute('data-db'); if(!db) return; selDb=db; paint();};"
                "el.addEventListener('click',go);"
                "el.addEventListener('keydown',e=>{if(e.key==='Enter'||e.key===' '){e.preventDefault();go();}});"
                "});}"
            )
            # Only replace if simple enough — check original
            text = text.replace(old_bind, new_bind, 1)

    return text


def patch_file07(text: str) -> str:
    """N10B-059 dark chart contrast; N10B-060 substitution sensitivity label."""
    if "chart-label-dark" not in text and "prefers-color-scheme: dark" in text:
        # Append chart text overrides inside existing dark block if possible
        dark_m = re.search(
            r"@media\s*\(prefers-color-scheme:\s*dark\)\s*\{([^}]*(?:\{[^}]*\}[^}]*)*)\}",
            text,
            re.S,
        )
        extra = (
            "\n  /* N10B-059: chart labels must follow dark containers */\n"
            "  .chart text, svg text, .legend, .legend text { fill: #e8e4dc !important; color: #e8e4dc !important; }\n"
            "  .chart line, .chart .grid, svg .grid { stroke: #6a6770 !important; }\n"
            "  .chart-panel, .card.chart, [class*=\"chart\"] { color: #e8e4dc; }\n"
        )
        # Simpler: append a second dark media block before </style>
        if "</style>" in text:
            text = text.replace(
                "</style>",
                "@media (prefers-color-scheme: dark){\n"
                "  svg text{fill:#e8e4dc!important}\n"
                "  .chart text,.legend,.legend span{color:#e8e4dc!important;fill:#e8e4dc!important}\n"
                "}\n</style>",
                1,
            )

    # Profit wording — soften to conditional substitution
    replacements = [
        (
            "profit given up",
            "unit-profit difference under a substitution scenario",
        ),
        (
            "became value-part sales",
            "are compared as if they had otherwise been original-part sales (conditional substitution sensitivity, not proven displacement)",
        ),
        (
            "Value-part sales",
            "Value-part sales (substitution sensitivity)",
        ),
    ]
    # Only apply careful unique phrases — read actual content
    return text


def patch_file07_content(text: str) -> tuple[str, list[str]]:
    notes = []
    # Find profit / value paragraphs
    if "prefers-color-scheme: dark" in text and "svg text{fill:#e8e4dc" not in text:
        text = text.replace(
            "</style>",
            "@media (prefers-color-scheme: dark){\n"
            "  svg text{fill:#e8e4dc!important}\n"
            "  .chart text,.legend,.legend span,.chart-caption{color:#e8e4dc!important;fill:#e8e4dc!important}\n"
            "  /* Keep chart plot area readable: lighten container text */\n"
            "  .card svg, figure svg { color: #e8e4dc; }\n"
            "}\n</style>",
            1,
        )
        notes.append("059 dark-mode svg/legend contrast")

    # Insert explicit counterfactual banner near value-part profit discussion
    markers = [
        "original-part",
        "value-part",
        "Value part",
        "value part",
        "profit",
    ]
    # Look for a heading or first strong claim
    inserted = False
    for pat in [
        r"(<h[1-4][^>]*>[^<]*(?:[Vv]alue.?part|profit)[^<]*</h[1-4]>)",
        r"(<p>[^<]{0,40}value.?part[^<]{0,200}</p>)",
    ]:
        m = re.search(pat, text, re.I)
        if m:
            banner = (
                '<p class="note" style="border-left:3px solid #c0552d;padding:8px 12px;background:#f7f4ee">'
                "<b>Conditional substitution sensitivity.</b> "
                "The unit-profit comparison treats observed value-part volume as if it had otherwise been "
                "original-part volume at the assumed price. It does not establish displacement: the same "
                "sale could replace an original sale, retain a customer who would otherwise leave, or win "
                "volume that would not have occurred. No displacement percentage is assumed."
                "</p>\n"
            )
            if "Conditional substitution sensitivity" not in text:
                text = text[: m.end()] + "\n" + banner + text[m.end() :]
                notes.append("060 substitution sensitivity banner")
                inserted = True
            break
    if not inserted and "Conditional substitution sensitivity" not in text:
        # Fall back: inject after <body> first content block
        body = text.find("<body")
        if body > 0:
            gt = text.find(">", body)
            banner = (
                '\n<p class="note" id="n10b-060" style="border-left:3px solid #c0552d;padding:8px 12px;margin:12px 0;background:#f7f4ee">'
                "<b>Conditional substitution sensitivity.</b> "
                "Any original-to-value unit-profit difference on this page is a scenario if value-part sales "
                "had otherwise been original-part sales. It is not a measured realised profit loss, and it "
                "does not assume a displacement rate."
                "</p>"
            )
            text = text[: gt + 1] + banner + text[gt + 1 :]
            notes.append("060 banner after body (fallback)")
    return text, notes


def patch_file08(text: str) -> str:
    """N10B-055 keyboard focus on explanation targets."""
    # Common patterns: data-tip without tabindex; class tip targets
    if 'data-tip' in text and 'tabindex="0"' not in text:
        text = text.replace(" data-tip=", ' tabindex="0" data-tip=')
    # Also elements with title-only explanations used as tips
    text = re.sub(
        r'(<(?:span|div|th|td|button)[^>]*class="[^"]*tip[^"]*"[^>]*)(?![^>]*tabindex)',
        r'\1 tabindex="0"',
        text,
        count=40,
    )
    return text


def patch_file09(text: str) -> str:
    """N10B-058 print scope label + print-all option."""
    if "n10b-print-scope" in text:
        return text
    # CSS
    text = text.replace(
        "</style>",
        """
.print-toolbar{display:flex;gap:12px;align-items:center;margin:0 0 12px;font-size:12px;color:#444}
.print-toolbar label{cursor:pointer}
@media print{
  .nav,.print-toolbar{display:none!important}
  body.print-all .panel{display:block!important;page-break-before:always}
  body.print-all .panel:first-of-type{page-break-before:auto}
  .print-scope{display:block!important;font-size:11px;color:#333;margin:0 0 10px;padding:6px 10px;border:1px solid #ccc}
}
.print-scope{display:none}
</style>""",
        1,
    )
    # Toolbar after nav
    if '<div class="nav">' in text or 'class="nav"' in text:
        # Find end of nav
        m = re.search(r'<div class="nav">.*?</div>', text, re.S)
        if m:
            insert = (
                '\n<div class="print-toolbar">'
                '<label><input type="checkbox" id="printAllTabs"> Print all tabs (not only the active view)</label>'
                '<span id="printScopeLive" style="color:#666"></span>'
                "</div>\n"
                '<p class="print-scope" id="n10b-print-scope"></p>\n'
            )
            text = text[: m.end()] + insert + text[m.end() :]

    # JS before closing script or after tab handler
    js = r"""
(function(){
  function activeTabLabel(){
    var on=document.querySelector('.nav button.on');
    return on ? (on.textContent||on.dataset.tab||'active view').trim() : 'active view';
  }
  function refreshPrintScope(){
    var all=document.getElementById('printAllTabs');
    var scope=document.getElementById('n10b-print-scope');
    var live=document.getElementById('printScopeLive');
    if(all && all.checked){
      document.body.classList.add('print-all');
      if(scope) scope.textContent='Printed scope: all dashboard tabs (Network, ITUK, FY2027).';
      if(live) live.textContent='Print will include every tab.';
    } else {
      document.body.classList.remove('print-all');
      if(scope) scope.textContent='Printed scope: selected view only — '+activeTabLabel()+'. Other tabs are hidden in this print.';
      if(live) live.textContent='Print = '+activeTabLabel()+' only (unless you tick print all).';
    }
  }
  var all=document.getElementById('printAllTabs');
  if(all) all.addEventListener('change', refreshPrintScope);
  document.querySelectorAll('.nav button').forEach(function(btn){
    btn.addEventListener('click', function(){ setTimeout(refreshPrintScope, 0); });
  });
  window.addEventListener('beforeprint', refreshPrintScope);
  refreshPrintScope();
})();
"""
    # Insert before last </script>
    idx = text.rfind("</script>")
    if idx > 0:
        text = text[:idx] + js + "\n" + text[idx:]
    return text


def patch_file10(text: str) -> tuple[str, str]:
    """Mobile bars — label equal-width behaviour (design note from addendum)."""
    status = "deferred"
    if "equal-width" in text or "not proportional on small screens" in text:
        return text, "already labelled"
    # Find mobile media query mentioning bars
    if "@media" in text and ("bar" in text.lower()):
        note = (
            '<p class="note mobile-bar-note" style="font-size:12px;color:#555">'
            "On narrow screens these bars switch to equal-width labelled blocks so values stay readable; "
            "they are not the same proportional geometry as the desktop chart."
            "</p>"
        )
        # insert before </body>
        if "</body>" in text and "mobile-bar-note" not in text:
            text = text.replace("</body>", note + "\n</body>", 1)
            status = "labelled mobile equal-width behaviour"
    else:
        status = "deferred — no clear mobile bar switch found to annotate"
    return text, status


def main():
    log = []

    # --- Distributor reviews 04/05/06 ---
    for num, db in DBS.items():
        path = ROOT / f"{num}_ISZE_Sales_Performance_Review_{db}.html"
        text = path.read_text(encoding="utf-8")
        text, info048 = strip_peer_medians(text)
        log.append(f"{path.name} N10B-048 kept={info048['kept']} removed_medians={len(info048['removed_medians'])} thin_removed={info048['removed_thin_groups']}")

        if db == "BELGIUM":
            text, nlab = fix_belgium_basis_labels(text)
            log.append(f"{path.name} N10B-049 basis_label fixes={nlab}")

        text = patch_pms_render(text)
        text, n061 = patch_above_100_wording(text)
        text = patch_distributor_css_js(text)
        log.append(f"{path.name} N10B-049/050/051/052/053/054/055/056/057/061 applied (061 hits={n061})")
        path.write_text(text, encoding="utf-8")

    # --- 03 ---
    p03 = ROOT / "03_ISZE_PMS_Family_Compare.html"
    t03 = p03.read_text(encoding="utf-8")
    t03 = patch_file03(t03)
    p03.write_text(t03, encoding="utf-8")
    log.append("03 N10B-054/055 paintResidual scale + keyboard")

    # --- 07 ---
    p07 = ROOT / "07_ISZE_MD_Pack_Capture_FY27_FY28.html"
    t07 = p07.read_text(encoding="utf-8")
    t07, notes07 = patch_file07_content(t07)
    p07.write_text(t07, encoding="utf-8")
    log.append("07 " + "; ".join(notes07))

    # --- 08 ---
    p08 = ROOT / "08_ISZE_UIO_Car_Park_V19_V20.html"
    t08 = p08.read_text(encoding="utf-8")
    t08 = patch_file08(t08)
    p08.write_text(t08, encoding="utf-8")
    log.append("08 N10B-055 tabindex on tip targets")

    # --- 09 ---
    p09 = ROOT / "09_ISZE_GPS_Dashboard.html"
    t09 = p09.read_text(encoding="utf-8")
    t09 = patch_file09(t09)
    p09.write_text(t09, encoding="utf-8")
    log.append("09 N10B-058 print scope + print-all")

    # --- 10 ---
    p10 = ROOT / "10_ISZE_OS_Console.html"
    t10 = p10.read_text(encoding="utf-8")
    t10, st10 = patch_file10(t10)
    p10.write_text(t10, encoding="utf-8")
    log.append(f"10 N10B mobile note: {st10}")

    (ROOT / "_patch_log.txt").write_text("\n".join(log), encoding="utf-8")
    print("\n".join(log))


if __name__ == "__main__":
    main()
