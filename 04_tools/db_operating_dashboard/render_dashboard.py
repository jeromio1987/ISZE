#!/usr/bin/env python
"""Render one operating dashboard from NUMBERS_LEDGER.json. No arithmetic."""
from __future__ import annotations

import argparse
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ISZE = r"C:\Users\jerom\Desktop\claude\ISZE"
MEETINGS = os.path.join(ISZE, "09_meetings")
CHART_JS = os.path.join(HERE, "template", "assets", "chart.umd.min.js")


def gps_from_ledger(L: dict) -> dict:
    """Sales-analysis GPS = operating spine only. Never gps_master / €250 UIO."""
    rows = [r for r in (L.get("gps_fy_spine") or {}).get("rows") or [] if r.get("publish")]
    bill, net, warr, incl, ex = {}, {}, {}, {}, {}
    for r in rows:
        fy = f"FY{r['fy']}"
        bill[fy] = r.get("actual_eur")
        warr[fy] = r.get("warranty_eur")
        ok = bool(r.get("ex_warranty_renderable"))
        net[fy] = r.get("ex_warranty_eur") if ok else None
        incl[fy] = r.get("gps_pct")
        ex[fy] = r.get("gps_pct_ex_warranty") if ok else None
    rf = (L.get("hero") or {}).get("rate_footer") or {}
    return {
        "available": bool(rows),
        "source": "operating ledger · V19 parc × current D-Max rate",
        "bill": bill,
        "warr": warr,
        "net": net,
        "gps_pct_incl_warr": incl,
        "gps_pct_ex_warr": ex,
        "formula_incl": "GPS % including warranty = GPS-eligible billed € ÷ (V19 parc × that year’s ISZE-net rate).",
        "formula_ex": "GPS % excluding warranty = GPS-eligible billed € minus warranty € ÷ the same ceiling. Blank when that euro is invalid — never a zero.",
        "rate_current_fy27": rf.get("lcv_rate_eur") or 262.5,
        "note": "Same GPS as the GPS + PMS tab. Mixed LCV + LD rates. Not a second wallet.",
    }


def attach_sales_analysis(L: dict, db: str) -> dict:
    path = os.path.join(MEETINGS, f"{db}_Operating_Dashboard_2026", "_sales_analysis.json")
    if not os.path.isfile(path):
        L["sales_analysis"] = None
        return L
    with open(path, encoding="utf-8") as f:
        S = json.load(f)
    S.pop("monthly", None)
    meta = S.setdefault("meta", {})
    for k in ("sold_to", "not", "uti_rows_in_sales_fact", "umi_rows_sales_fact", "verification"):
        meta.pop(k, None)
    S["gps"] = gps_from_ledger(L)
    L["sales_analysis"] = S
    return L


_CUSTOMER_BANNED = re.compile(
    r"\bUMI\b|\bIsrael\b|\b1797\b|\bUTI\b|Official YTD|July is the miss|FY2024 UMI|Universal Motors",
    re.I,
)


def _scrub_banned_text(obj):
    if isinstance(obj, dict):
        return {k: _scrub_banned_text(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [_scrub_banned_text(v) for v in obj]
    if isinstance(obj, str) and _CUSTOMER_BANNED.search(obj):
        s = re.sub(
            r"Reproduces metrics_snapshot\.json exactly \([^)]+\) — this is the anchor definition\.",
            "This is the catalogue Best Value definition.",
            obj,
            flags=re.I,
        )
        s = re.sub(
            r"The local aftermarket catalogue is only shown for UMI and UTI\.",
            "No local aftermarket catalogue on file for this distributor.",
            s,
            flags=re.I,
        )
        s = _CUSTOMER_BANNED.sub("", s)
        s = re.sub(r"\s{2,}", " ", s)
        s = re.sub(r"\(\s*[,;]?\s*\)", "", s)
        return s.strip(" —-,;")
    return obj


_LEAD_BANNED = re.compile(
    r"sold-?to|\bNuno\b|\bDuncan Young\b|"
    r"\bnot\s+(the\s+)?(UMI|UTI|Motolusa|Ireland|Cyprus|RSA|IUK|Harris|ISD|Portugal|Loutsios)\b|"
    r"Nothing (recycled|copied)",
    re.I,
)


def face_open_lead_from_meta(L: dict) -> str:
    m = L.get("meta") or {}
    bits = [str(m.get("display_name") or "").strip(), str(m.get("country") or "").strip()]
    return " · ".join(p for p in bits if p)


def sanitize_open_lead_payload(L: dict) -> dict:
    """Executive overview lead is always distributor · country. Never agent disambiguation."""
    es = L.setdefault("empty_states", {})
    fe = es.setdefault("F_emails", {})
    if not isinstance(fe, dict):
        return L
    face = face_open_lead_from_meta(L)
    fe["open_lead"] = face
    note = str(fe.get("source_note") or "")
    if note and _LEAD_BANNED.search(note):
        fe["source_note"] = ""
    gm = es.get("G_minutes")
    if isinstance(gm, dict):
        body = str(gm.get("body") or "")
        if body and (_LEAD_BANNED.search(body) or re.search(r"Named Outlook folder", body, re.I)):
            gm["body"] = ""
        ids_on = bool((L.get("sections") or {}).get("ids", {}).get("available"))
        master = (L.get("meta") or {}).get("audience") == "customer" or ids_on
        if master:
            gm["searched"] = []
    return L


def sanitize_customer_payload(L: dict) -> dict:
    """Customer HTML must not embed other-DB names or leftover UMI copy."""
    for chip in (L.get("hero") or {}).get("chips") or []:
        tip = chip.get("tooltip") or {}
        ni = str(tip.get("not_included") or "")
        if re.search(r"UMI|Israel|1797", ni, re.I):
            tip["not_included"] = (
                "Ex-warranty is a toggle of GPS-eligible parts, not a second headline. "
                "A year with an invalid ex-warranty euro is left blank — never drawn as zero."
            )
    loc = (L.get("sections") or {}).get("local_catalogue") or {}
    if loc.get("available") is False and re.search(r"UMI|UTI|Israel", str(loc.get("reason") or ""), re.I):
        loc["reason"] = "No local aftermarket catalogue on file for this distributor."
    peers = ((L.get("compare") or {}).get("lcv_peer_set")) or {}
    n = len(peers.get("members") or [])
    if peers:
        peers["legend_line"] = f"LCV peer (≥90% LCV euros): {n or 'several'} distributors"
        peers["members"] = []
        peers["formula"] = (
            "LCV share = LCV parc × ISZE-net rate ÷ (LCV + CV wallet). "
            "Peer = share ≥ 90%. This distributor versus that peer average."
        )
        tip = peers.get("tooltip") or {}
        if tip:
            tip["formula"] = peers["formula"]
            tip["not_included"] = "Incomplete years. Not a calendar-year GPS%."
        this = peers.get("this_db") or {}
        if this.get("gps_label") in ("RSA", "UMI"):
            this["gps_label"] = L.get("meta", {}).get("country") or this.get("display")
            this["legend_label"] = this.get("display")
    note = (L.get("integrity_strip") or {}).get("integrity_note")
    if note and _CUSTOMER_BANNED.search(str(note)):
        L["integrity_strip"]["integrity_note"] = "Full notes sit in the same folder as this dashboard."
    return L


def load_ledger(db: str) -> dict:
    path = os.path.join(MEETINGS, f"{db}_Operating_Dashboard_2026", "NUMBERS_LEDGER.json")
    with open(path, encoding="utf-8") as f:
        L = json.load(f)
    L = attach_sales_analysis(L, db)
    L = sanitize_open_lead_payload(L)
    if (L.get("meta") or {}).get("audience") == "customer":
        L = sanitize_customer_payload(L)
        L = _scrub_banned_text(L)
    return L


def write_cmd(outdir: str, html_name: str):
    cmd = os.path.join(outdir, f"OPEN_{html_name.replace('.html', '')}.cmd")
    with open(cmd, "w", encoding="ascii") as f:
        f.write(f'@echo off\r\nstart "" "%~dp0{html_name}"\r\n')
    return cmd


def render(db: str) -> str:
    L = load_ledger(db)
    chart = open(CHART_JS, encoding="utf-8").read()
    if "sourceMappingURL" in chart:
        sys.exit("Chart.js still has sourceMappingURL")
    payload = json.dumps(L, ensure_ascii=False)
    if re.search(r"street", payload, re.I):
        sys.exit("ledger payload still contains 'street' — would leak into customer HTML")
    if re.search(r"Not UMI, not Motolusa|sold-to 519 and 92", payload):
        sys.exit("agent disambiguation lead leaked into HTML payload")
    if re.search(r"street", TEMPLATE, re.I):
        sys.exit("render template still contains 'street'")
    html = TEMPLATE.replace("/*__CHART_JS__*/", chart).replace("__PAYLOAD__", payload)
    if re.search(r"""<(?:script|link)[^>]+(?:src|href)=['"]https://""", html, re.I):
        sys.exit("CDN reference slipped into the HTML")
    outdir = os.path.join(MEETINGS, f"{db}_Operating_Dashboard_2026")
    os.makedirs(outdir, exist_ok=True)
    name = f"{db}_Operating_Dashboard.html"
    out = os.path.join(outdir, name)
    with open(out, "w", encoding="utf-8") as f:
        f.write(html)
    with open(out, encoding="utf-8") as f:
        written = f.read()
    if re.search(r"street", written, re.I):
        sys.exit("written HTML still contains 'street'")
    if (L.get("meta") or {}).get("audience") == "customer":
        hit = _CUSTOMER_BANNED.search(payload)
        if hit:
            sys.exit(f"customer HTML still contains banned string: {hit.group(0)!r}")
    cmd = write_cmd(outdir, name)
    kb = os.path.getsize(out) / 1024
    print(f"  -> {out} ({kb:.0f} KB)")
    print(f"  -> {cmd}")
    return out


TEMPLATE = r"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Operating dashboard</title>
<style>
:root{
  --navy:#15233c; --navy2:#1a2b4a; --terra:#c0552d; --paper:#f7f4ee;
  --line:#d9d3c8; --muted:#6b6256; --ink:#222; --green:#1d9e75;
  --amber:#eda100; --red:#b23b3b; --surface:#fff; --blue:#2a78d6;
}
*{box-sizing:border-box}
html,body{margin:0;padding:0;background:var(--paper);color:var(--ink);
  font:15px/1.5 "Segoe UI",Helvetica,Arial,sans-serif;overflow-x:hidden;
  -webkit-print-color-adjust:exact;print-color-adjust:exact}
h1,h2,h3{font-family:Georgia,"Times New Roman",serif;color:var(--navy2);font-weight:400;margin:0}
.sticky-head{position:sticky;top:0;z-index:30}
.hero{background:linear-gradient(155deg,#15233c 0%,#203759 55%,#2b4a78 100%);color:#eef1f6;padding:22px 28px 16px}
.hero-inner{max-width:1180px;margin:0 auto}
.brand{font-family:Georgia,serif;letter-spacing:.16em;text-transform:uppercase;font-size:12px;color:#c9d4e6}
.hero h1{color:#fff;font-size:28px;line-height:1.12;margin:6px 0 8px;font-weight:400}
.hero .rule{width:56px;height:3px;background:var(--terra);margin:0 0 10px}
.hero .lead{color:#d5dce8;max-width:820px;font-size:14.5px;margin:0 0 16px}
.hero-kpis{display:grid;grid-template-columns:repeat(4,1fr);gap:12px}
.hk{background:rgba(255,255,255,.07);border:1px solid rgba(255,255,255,.12);padding:14px 16px;position:relative}
.hk .v{font-size:26px;font-weight:700;letter-spacing:-.4px;color:#fff}
.hk .l{font-size:11px;text-transform:uppercase;letter-spacing:.06em;color:#aeb9cb;margin-top:4px}
.hk .n{font-size:12px;color:#9aa8bd;margin-top:6px;line-height:1.35}
.hk[data-formula]{cursor:help}
.planline{display:flex;flex-wrap:wrap;gap:8px 22px;margin:14px 0 0;font-size:13px;color:#d5dce8}
.planline b{color:#fff;font-weight:700}
.planline .tick{color:#7dcea0;font-weight:700}
.warr{display:flex;align-items:center;gap:8px;margin-top:12px;font-size:12px;color:#aeb9cb}
.warr button{appearance:none;border:1px solid rgba(255,255,255,.25);background:transparent;
  color:#eef1f6;padding:5px 12px;font:inherit;cursor:pointer}
.warr button.on{background:var(--terra);border-color:var(--terra);color:#f7f4ee}
.rate{font-size:12px;color:#9aa8bd;margin:8px 0 0}
.tabs{display:flex;flex-wrap:wrap;gap:0;max-width:1180px;margin:0 auto;padding:0 28px;
  border-bottom:1px solid var(--line);background:var(--paper)}
.tabs button{appearance:none;border:0;background:transparent;padding:13px 16px;font:inherit;
  font-size:13.5px;color:var(--muted);cursor:pointer;border-bottom:3px solid transparent;margin-bottom:-1px}
.tabs button.on{color:var(--navy2);font-weight:600;border-bottom-color:var(--terra)}
.tabs button:hover{color:var(--navy2)}
body.customer .tabs{gap:8px;padding:10px 28px 12px}
body.customer .tabs button{padding:16px 28px;font-size:16px;font-weight:600;color:var(--navy2);
  background:#fff;border:1px solid var(--line);margin-bottom:0}
body.customer .tabs button.on{background:var(--navy);color:#f7f4ee;border-color:var(--navy);font-weight:700}
body.customer .tabs button.on:hover{color:#f7f4ee}
body.customer h2 .no{display:none}
.wrap{max-width:1180px;margin:0 auto;padding:22px 28px 72px}
.panel{display:none}
.panel.on{display:block}
h2{font-size:22px;margin:8px 0 8px;padding-bottom:8px;border-bottom:2px solid var(--navy2)}
h2 .no{color:var(--terra)}
.lead{color:var(--muted);margin:0 0 16px;max-width:820px}
.card{background:var(--surface);border:1px solid var(--line);padding:16px 18px;margin:0 0 14px}
.card h3{font-size:16px;margin:0 0 8px}
.grid2{display:grid;grid-template-columns:1fr 1fr;gap:14px}
.grid3{display:grid;grid-template-columns:repeat(3,1fr);gap:12px}
.chart-wrap{position:relative;height:280px}
.chart-wrap.tall{height:520px}
.chart-wrap.pms{height:640px}
.kpi{background:var(--surface);border:1px solid var(--line);padding:12px 14px;position:relative}
.kpi[data-formula]{cursor:help}
.kpi .l{font-size:11px;text-transform:uppercase;letter-spacing:.05em;color:var(--muted)}
.kpi .v{font-size:22px;font-weight:700;color:var(--navy);margin-top:4px}
.kpi .n{font-size:12px;color:var(--muted);margin-top:4px}
.kpi.ns .v{color:var(--muted);font-weight:600}
table{width:100%;border-collapse:collapse;font-size:13px;background:var(--surface)}
th{background:var(--navy);color:#f7f4ee;text-align:left;padding:10px 12px;font-size:11px;
  text-transform:uppercase;letter-spacing:.05em;font-family:"Segoe UI",sans-serif}
td{padding:9px 12px;border-bottom:1px solid var(--line);color:var(--ink);vertical-align:top}
tbody tr:nth-child(even) td{background:#faf8f4}
tbody tr.shell td{background:#eef3f9;color:#222;border-left:3px solid #888780}
td.n,th.n{text-align:right;font-variant-numeric:tabular-nums;white-space:nowrap}
.tag{display:inline-block;font-size:11px;padding:1px 7px;background:#e8e4dc;color:#444}
.tag.ok{background:#e4f5ee;color:#1d6b4f}
.tag.warn{background:#fff3d6;color:#8a6500}
.tag.bad{background:#fde8e8;color:#8a3030}
.tag.grey{background:#e8e4dc;color:#6b6256}
.callout{border-left:3px solid var(--terra);background:#fff;padding:12px 14px;margin:0 0 16px}
.callout.ok{border-left-color:var(--green)}
.callout.amber{border-left-color:var(--amber)}
.empty{padding:18px;border:1px dashed var(--line);color:var(--muted);background:#fff;margin:0 0 14px}
.heat{display:grid;gap:2px;font-size:11px;min-width:720px}
.heat .row{display:grid;grid-template-columns:200px repeat(5,1fr) 64px;gap:2px}
.heat .h{background:var(--navy);color:#f7f4ee;padding:8px 8px}
.heat .c{padding:8px;text-align:center;color:var(--ink)}
.heat .c.ns{background:#e8e4dc;color:#6b6256}
.sales-sub{display:flex;flex-wrap:wrap;gap:6px;margin:0 0 18px;position:sticky;top:0;z-index:4;background:var(--paper);padding:8px 0}
.sales-sub a{font-size:12px;color:var(--navy2);text-decoration:none;padding:6px 12px;border:1px solid var(--line);background:#fff;cursor:pointer}
.sales-sub a.on{background:var(--navy);color:#f7f4ee;border-color:var(--navy);font-weight:600}
.stat-grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(160px,1fr));gap:10px;margin:0 0 14px}
.stat-grid .kpi .v.good{color:var(--green)}
.stat-grid .kpi .v.bad{color:var(--red)}
.btns{display:flex;flex-wrap:wrap;gap:6px;margin:0 0 12px}
.btns button{appearance:none;background:#fff;border:1px solid var(--line);color:var(--navy2);padding:5px 10px;font:inherit;font-size:13px;cursor:pointer}
.btns button.on{background:var(--navy);color:#f7f4ee;border-color:var(--navy)}
.tblscroll{overflow-x:auto;margin:0 0 12px;background:#fff;border:1px solid var(--line)}
#pntable{margin:0;min-width:880px;font-size:13px}
tbody tr.spa td{background:#f3e4dc;color:#222}
.spa-mark{display:inline-block;background:var(--terra);color:#f7f4ee;font-size:10px;padding:1px 6px;margin-left:6px}
.submeta{display:block;font-size:11px;color:var(--muted);margin-top:2px}
.legend{font-size:13px;color:var(--muted);margin:8px 0 0}
.legend i{display:inline-block;width:.7rem;height:.7rem;margin-right:.25rem;vertical-align:middle}
.scroll{overflow:auto;max-height:560px;border:1px solid var(--line)}
.lane{background:#fff;border:1px solid var(--line);padding:18px;border-top:3px solid var(--navy2)}
.lane h3{font-size:15px;margin:0 0 6px}
.lane .v{font-size:28px;font-weight:700;color:var(--navy);letter-spacing:-.5px}
.lane .n{font-size:12.5px;color:var(--muted);margin-top:8px;line-height:1.45}
.lane.ret{border-top-color:var(--green)}
.ask{background:#fff;border:1px solid var(--line);border-left:4px solid var(--terra);padding:18px 20px;margin:0 0 16px}
.ask h3{font-size:18px;margin:0 0 8px}
.lights{display:grid;grid-template-columns:repeat(4,1fr);gap:10px;margin:0 0 16px}
.light{background:#fff;border:1px solid var(--line);padding:12px 14px;border-top:3px solid #888780}
.light.ok{border-top-color:var(--green)}
.light.warn{border-top-color:var(--amber)}
.light.bad{border-top-color:var(--red)}
.light.off{border-top-color:#d9d3c8}
.light .l{font-size:11px;text-transform:uppercase;letter-spacing:.05em;color:var(--muted)}
.light .v{font-size:13px;font-weight:600;color:var(--navy2);margin-top:4px}
.light .n{font-size:12px;color:var(--muted);margin-top:4px}
.bullet{height:22px;background:#e8e4dc;position:relative;margin:10px 0 4px}
.bullet .fill{height:100%;background:var(--navy)}
.bullet .mark{position:absolute;top:-3px;bottom:-3px;width:3px;background:var(--terra)}
.cap{font-size:12.5px;color:var(--muted);margin:0 0 12px}
table a.offer{color:#c0552d;font-weight:600;text-decoration:underline}
.cta{display:inline-block;background:#c0552d;color:#f7f4ee;padding:4px 8px;font-size:11px;
  letter-spacing:.03em;font-weight:600;white-space:normal;max-width:280px;line-height:1.35}
.honesty{font-size:13px;color:var(--muted);margin:0 0 14px;max-width:900px;line-height:1.5}
.grain-ctl{display:flex;align-items:center;gap:8px;margin:0 0 12px;font-size:13px;color:var(--muted)}
.grain-ctl button{appearance:none;border:1px solid var(--line);background:#fff;color:var(--navy2);
  padding:6px 14px;font:inherit;cursor:pointer}
.grain-ctl button.on{background:var(--navy);border-color:var(--navy);color:#f7f4ee}
.grain-ctl button:disabled{opacity:.45;cursor:not-allowed;background:#f3f0ea;color:var(--muted)}
.drill-ctl{display:flex;flex-wrap:wrap;align-items:center;gap:10px 18px;margin:0 0 14px;font-size:13px;color:var(--muted)}
.drill-ctl label{display:flex;align-items:center;gap:8px;color:var(--navy2)}
.drill-ctl select{border:1px solid var(--line);background:#fff;color:var(--navy2);
  padding:6px 12px;font:inherit;cursor:pointer;min-width:200px}
.cta.none{background:transparent;color:var(--muted);padding:0;font-weight:500}
.grain-on{font-size:12.5px;color:var(--muted);margin:0 0 10px}
.pill{display:inline-block;font-size:11px;padding:1px 8px;background:#e8e4dc;color:#444}
.pill.weak{background:#fde8e8;color:#8a3030}
.pill.medium{background:#fff3d6;color:#8a6500}
.pill.good{background:#e4f5ee;color:#1d6b4f}
.srcchips{display:flex;flex-wrap:wrap;gap:8px;margin:0 0 14px}
.srcchip{background:#fff;border:1px solid var(--line);padding:8px 12px;font-size:12.5px;color:var(--ink)}
.srcchip b{color:var(--navy2)}
.srcchip.lcv{border-color:#c0552d;background:#fff8f4;color:#222;max-width:100%}
.srcchip.lcv b{color:#c0552d}
.srcchip.out{border-color:#eda100}
.srcchip .n{font-size:12px;color:var(--muted);margin-top:4px}
.tag.bvpok{background:#e4f5ee;color:#1d6b4f}
.tag.bvpno{background:#fff3d6;color:#8a6500}
.lev{font-size:12.5px;color:var(--navy2);margin:4px 0 0}
.honesty{font-size:13px;color:var(--muted);margin:0 0 14px;max-width:900px;line-height:1.5}
.digest-grid{display:grid;grid-template-columns:repeat(3,1fr);gap:12px;margin:0 0 20px}
@media(max-width:1100px){.digest-grid{grid-template-columns:1fr 1fr}}
@media(max-width:720px){.digest-grid{grid-template-columns:1fr}}
.dcard{background:var(--surface);border:1px solid var(--line);padding:14px 16px;display:flex;flex-direction:column;min-height:100%}
.dcard .dhead{display:flex;justify-content:space-between;align-items:baseline;gap:8px}
.dcard .l{font-size:11px;text-transform:uppercase;letter-spacing:.05em;color:var(--muted)}
.dcard .src{font-size:10px;color:var(--muted);text-transform:none;letter-spacing:0;white-space:nowrap}
.dcard .sub{font-size:12px;color:var(--muted);margin-top:2px}
.dcard .v{font-size:22px;font-weight:700;color:var(--navy);margin-top:6px}
.dcard .n{font-size:12px;color:var(--muted);margin-top:4px;line-height:1.4}
.dcard .chart-wrap.mini{height:46px;margin-top:8px}
.dcard .dlink{margin-top:auto;padding-top:10px;font-size:12.5px;font-weight:600;color:var(--terra);text-decoration:none;cursor:pointer}
.dcard .dlink:hover{text-decoration:underline}
.dcard[data-formula]{cursor:help}
.foot{margin-top:36px;padding-top:14px;border-top:1px solid var(--line);font-size:11.5px;color:var(--muted);line-height:1.65}
.tipbox{position:fixed;z-index:80;display:none;max-width:360px;padding:10px 12px;
  background:#15233c;color:#f7f4ee;border-left:3px solid #c0552d;
  font:12px/1.45 "Segoe UI",sans-serif;box-shadow:0 8px 24px rgba(21,35,60,.28);pointer-events:none}
.tipbox .k{font-size:10px;letter-spacing:.06em;text-transform:uppercase;color:#c9d4e6;margin-top:6px}
.tipbox .k:first-child{margin-top:0}
@media(max-width:1100px){
  .hero-kpis,.lights{grid-template-columns:1fr 1fr}
  .grid3{grid-template-columns:1fr 1fr}
}
@media(max-width:720px){
  .hero-kpis,.planline,.grid2,.grid3,.lights{grid-template-columns:1fr}
  .hero h1{font-size:22px}
  .wrap,.hero,.tabs{padding-left:16px;padding-right:16px}
}
</style>
</head>
<body>
<div class="sticky-head">
  <div class="hero">
    <div class="hero-inner">
      <div class="brand">ISZE · operating</div>
      <h1 id="title"></h1>
      <div class="rule"></div>
      <p class="lead" id="oneLiner"></p>
      <div class="hero-kpis" id="heroKpis"></div>
      <div class="planline" id="planLine"></div>
      <div class="warr">Warranty
        <button type="button" class="on" data-w="in" id="wIn">Included</button>
        <button type="button" data-w="ex" id="wEx">Excluded</button>
        <span id="warrNote">— toggle of GPS-eligible parts, not a second headline</span>
      </div>
      <p class="rate" id="rateFoot"></p>
    </div>
  </div>
  <nav class="tabs" id="tabs"></nav>
</div>
<main class="wrap">
  <section class="panel" id="p-open"></section>
  <section class="panel" id="p-plan"></section>
  <section class="panel" id="p-gps"></section>
  <section class="panel" id="p-pms"></section>
  <section class="panel" id="p-mix"></section>
  <section class="panel" id="p-ord"></section>
  <section class="panel" id="p-lost"></section>
  <section class="panel" id="p-fam"></section>
  <section class="panel" id="p-spa"></section>
  <section class="panel" id="p-parts"></section>
  <section class="panel" id="p-ids"></section>
  <section class="panel" id="p-sales"></section>
  <section class="panel" id="p-int"></section>
  <p class="foot" id="foot"></p>
</main>
<div class="tipbox" id="tipbox"></div>
<script type="application/json" id="payload">__PAYLOAD__</script>
<script>/*__CHART_JS__*/</script>
<script>if(typeof Chart!=='undefined') window.Chart = Chart;</script>
<script>
(function(){
  const Chart = window.Chart;
  if(!Chart){
    document.body.insertAdjacentHTML('afterbegin','<p class="empty">Chart library did not attach to this window.</p>');
    return;
  }
  const L = JSON.parse(document.getElementById('payload').textContent);
  const customer = L.meta.audience === 'customer';
  if(customer){
    document.body.classList.add('customer');
    const brand = document.querySelector('.brand');
    if(brand) brand.textContent = 'ISZE · ' + (L.meta.country || L.meta.display_name || '');
  }
  const $ = (id) => document.getElementById(id);
  const esc = (s) => String(s==null?'':s).replace(/[&<>"']/g, c=>({ '&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;' }[c]));
  const eur = (v) => v==null ? '—' : '€' + Math.round(v).toLocaleString('en-GB');
  const eurC = (v) => {
    if(v==null) return '—';
    const a = Math.abs(v);
    if(a >= 1e6) return '€' + (v/1e6).toFixed(2) + 'M';
    return eur(v);
  };
  const unit = (v) => v==null ? '—' : '€' + Number(v).toLocaleString('en-GB', {minimumFractionDigits:2, maximumFractionDigits:2});
  const pct = (v,d=1) => v==null ? '—' : Number(v).toFixed(d) + '%';
  const tipBits = (t) => {
    if(!t) return '';
    const bits = [];
    if(t.formula) bits.push('data-formula="'+esc(t.formula)+'"');
    if(t.snapshot) bits.push('data-snapshot="'+esc(t.snapshot)+'"');
    if(t.not_included) bits.push('data-not="'+esc(t.not_included)+'"');
    if(t.warning) bits.push('data-warn="'+esc(t.warning)+'"');
    return bits.join(' ');
  };
  const NAVY='#15233c', TERRA='#c0552d', GREEN='#1d9e75', AMBER='#eda100', MUTED='#888780', BLUE='#2a78d6', PAPER='#f7f4ee';
  Chart.defaults.font.family = '"Segoe UI", Arial, sans-serif';
  Chart.defaults.color = '#6b6256';
  Chart.defaults.plugins.legend.labels.boxWidth = 12;
  Chart.defaults.plugins.legend.labels.color = '#6b6256';
  const yPct = (max) => ({ min:0, max: max==null?100:max, ticks:{ maxTicksLimit:6, callback:v=>v+'%' }, grid:{color:'#eee'} });
  const yEur = () => ({ min:0, ticks:{ maxTicksLimit:6, callback:v=> v>=1e6 ? (v/1e6).toFixed(1)+'M' : Math.round(v).toLocaleString('en-GB') }, grid:{color:'#eee'} });
  const xEur = () => ({ min:0, ticks:{ maxTicksLimit:6, callback:v=> v>=1e6 ? (v/1e6).toFixed(1)+'M' : Math.round(v).toLocaleString('en-GB') }, grid:{color:'#eee'} });
  const lcvSet = (L.compare && L.compare.lcv_peer_set) || {};
  const lcvPeerChip = () => {
    const line = lcvSet.legend_line || 'LCV peer (≥90% LCV euros)';
    const note = lcvSet.this_book_note || '';
    return `<div class="srcchip lcv" ${tipBits(lcvSet.tooltip)}><b>LCV peer</b> (≥90% LCV euros)<div>${esc(line.replace(/^LCV peer \(≥90% LCV euros\):\s*/, ''))}</div>${note? '<div class="n">'+esc(note)+'</div>':''}</div>`;
  };

  const box = $('tipbox');
  document.addEventListener('mouseover', (e) => {
    const el = e.target.closest('[data-formula],[data-not]');
    if(!el){ box.style.display='none'; return; }
    const rows = [];
    if(el.dataset.formula) rows.push('<div class="k">Formula</div><div>'+esc(el.dataset.formula)+'</div>');
    if(el.dataset.snapshot) rows.push('<div class="k">Snapshot</div><div>'+esc(el.dataset.snapshot)+'</div>');
    if(el.dataset.not) rows.push('<div class="k">Not included</div><div>'+esc(el.dataset.not)+'</div>');
    if(el.dataset.warn) rows.push('<div class="k">Watch</div><div>'+esc(el.dataset.warn)+'</div>');
    if(!rows.length){ box.style.display='none'; return; }
    box.innerHTML = rows.join('');
    box.style.display = 'block';
    const r = el.getBoundingClientRect();
    let x = r.left, y = r.bottom + 8;
    if(x + 360 > window.innerWidth) x = window.innerWidth - 372;
    if(y + 160 > window.innerHeight) y = r.top - 8 - box.offsetHeight;
    if(y < 8) y = 8;
    box.style.left = Math.max(8, x) + 'px';
    box.style.top = y + 'px';
  });
  document.addEventListener('mouseout', (e) => {
    if(!e.relatedTarget || !e.relatedTarget.closest('[data-formula],[data-not]')) box.style.display='none';
  });

  document.title = customer
    ? ((L.meta.country || '') + ' · ' + (L.meta.display_name || ''))
    : (L.meta.display_name + ' · operating');
  $('title').textContent = L.meta.display_name;
  $('oneLiner').textContent = L.hero.one_liner || '';
  if(customer && $('warrNote')) $('warrNote').textContent = '— GPS-eligible parts, warranty included or excluded';

  const chips = L.hero.chips || [];
  const plan = L.hero.plan || {};
  function paintHero(warr){
    const gpsId = warr==='in' ? 'gps_in' : 'gps_ex';
    const order = [gpsId, 'pms', 'wallet'];
    const picked = order.map(id => chips.find(c=>c.id===id)).filter(Boolean);
    const gpsHtml = picked.map(c=>{
      const val = c.value_eur!=null ? eurC(c.value_eur) : (c.value_pct!=null ? pct(c.value_pct) : '—');
      return `<div class="hk" ${tipBits(c.tooltip)}><div class="v">${val}</div>
        <div class="l">${esc(c.label)}</div><div class="n">${esc(c.grain||'')} · ${esc(c.sub||'')}</div></div>`;
    }).join('');
    const ext = `<div class="hk" ${tipBits(plan.tooltip)}><div class="v">${eurC(plan.ext_target_fy27_eur)}</div>
      <div class="l">Extended target FY27</div>
      <div class="n">BP ${eurC(plan.bp_fy27_eur)} · ${plan.bp_match==='MATCH'?(customer?'Plan confirmed':'MATCH'):'watch'}</div></div>`;
    $('heroKpis').innerHTML = gpsHtml + ext;
  }
  $('planLine').innerHTML =
    `<span>Business plan FY27 <b>${eurC(plan.bp_fy27_eur)}</b></span>` +
    `<span>Stretch <b>${eurC(plan.stretch_eur)}</b></span>` +
    `<span>Extended target <b>${eurC(plan.ext_target_fy27_eur)}</b></span>` +
    (plan.bp_match==='MATCH'
      ? (customer ? '<span class="tick">Plan confirmed</span>' : '<span class="tick">BP matches the locked workbook</span>')
      : `<span>${esc(plan.bp_match||'')}</span>`);
  const rf = L.hero.rate_footer || {};
  $('rateFoot').textContent = rf.lcv_rate_eur ? ('D-Max rate €' + Number(rf.lcv_rate_eur).toFixed(2) + ' · ' + (rf.as_of||'')) : '';

  let warr = 'in';
  paintHero(warr);
  $('wIn').onclick = () => { warr='in'; $('wIn').classList.add('on'); $('wEx').classList.remove('on'); paintHero(warr); drawGps(); };
  $('wEx').onclick = () => { warr='ex'; $('wEx').classList.add('on'); $('wIn').classList.remove('on'); paintHero(warr); drawGps(); };

  const idsOn = !!(L.sections.ids||{}).available;
  const salesOn = !!(L.sales_analysis);
  const roomK = customer;
  const master = customer;
  const TABS = master
    ? [
        ['p-open','Executive overview'],
        ...(salesOn ? [['p-sales','Sales analysis']] : []),
        ...(idsOn ? [['p-ids','IDS']] : []),
        ['p-gps', 'GPS + PMS'],
        ['p-spa', 'Aftermarket situation']
      ]
    : [
        ['p-open','Open issues'],['p-plan','Plan'],['p-gps','GPS'],['p-pms','PMS'],['p-mix','Mix'],
        ['p-ord','Orders'],['p-lost','Lost sales'],['p-fam','Family strategy'],
        ['p-spa','Aftermarket'],
        ['p-parts','Top parts']
      ];
  if(!master && !customer){
    if(salesOn) TABS.push(['p-sales','Sales analysis']);
    TABS.push(['p-int','Ask']);
  }
  function showPanel(id){
    if(!id) return;
    const panel = document.getElementById(id);
    if(!panel) return;
    document.querySelectorAll('.tabs button').forEach(x=>x.classList.toggle('on', x.dataset.p===id));
    document.querySelectorAll('main .panel').forEach(p=>p.classList.toggle('on', p.id===id));
    if(id==='p-sales') paintSalesBook();
  }
  $('tabs').innerHTML = TABS.map(([id,l],i)=>`<button type="button" class="${i===0?'on':''}" data-p="${id}">${l}</button>`).join('');
  $('tabs').onclick = (e)=>{
    const b=e.target.closest('button'); if(!b) return;
    showPanel(b.dataset.p);
  };
  document.addEventListener('click', (e)=>{
    const a=e.target.closest('[data-go]');
    if(!a) return;
    e.preventDefault();
    showPanel(a.getAttribute('data-go'));
  });

  const esEarly = L.empty_states || {};
  const mailRows = (esEarly.F_emails||{}).rows || [];
  const bartRows = (esEarly.G_minutes||{}).rows || [];
  const issueTable = (rows) => {
    if(!rows.length) return '<p class="empty">None on file.</p>';
    return `<div class="scroll"><table><thead><tr><th>Date</th><th>Item</th><th>Owner</th><th>Asked by</th><th>Source</th></tr></thead><tbody>
      ${rows.map(r=>`<tr><td>${esc(r.date||'')}</td><td>${esc(r.item||'')}</td><td>${esc(r.owner||'')}</td><td>${esc(r.asked_by||'')}</td><td>${esc(r.source||'')}</td></tr>`).join('')}
    </tbody></table></div>`;
  };
  const faceLead = [L.meta.display_name, L.meta.country].filter(Boolean).join(' · ');
  const openLead = faceLead;
  const mailCap = String((esEarly.F_emails||{}).source_note||'');
  const minsCap = String((esEarly.G_minutes||{}).body||'');
  const searched = master ? [] : ((esEarly.G_minutes||{}).searched||[]);
  $('p-open').innerHTML = `
    <h2>${roomK?'Executive overview':'<span class="no">00</span> Open issues'}</h2>
    <p class="lead">${esc(openLead)}</p>
    ${roomK?'<div id="pOpenDigest"></div>':''}
    <div id="pOpenIssues">
    <div class="card"><h3>${esc((esEarly.F_emails||{}).title||(customer?'Next actions':'Open issues from mail'))}</h3>
      <p class="cap">${esc(mailCap)}${mailCap?' · ':''}${mailRows.length} open</p>
      ${issueTable(mailRows)}</div>
    <div class="card"><h3>${esc((esEarly.G_minutes||{}).title||(customer?'Review follow-ups':'Meeting minutes / follow-ups'))}</h3>
      <p class="cap">${esc(minsCap)}${minsCap?' · ':''}${bartRows.length} open</p>
      ${issueTable(bartRows)}
      ${searched.length ? '<p class="cap">Searched: '+searched.map(esc).join(' · ')+'</p>' : ''}</div>
    </div>`;
  document.getElementById('p-plan').classList.remove('on');
  document.getElementById('p-sales').classList.remove('on');
  document.getElementById('p-open').classList.add('on');

  const P = L.sections.plan_tracking || {};
  const bu = P.build_up || [];
  const cap = P.against_capacity || {};
  const avp = P.actual_vs_plan || {};
  const bpStep = bu.find(s=>s.kind==='plan') || {};
  const stStep = bu.find(s=>s.kind==='stretch') || {};
  const tgStep = bu.find(s=>s.kind==='target') || {};
  const gpsPctT = cap.gps_pct_at_ext_target==null ? null : cap.gps_pct_at_ext_target * 100;
  const gpsPctB = cap.gps_pct_at_bp==null ? null : cap.gps_pct_at_bp * 100;
  $('p-plan').innerHTML = `
    <h2>${customer?'Plan':'<span class="no">01</span> Plan tracking'}</h2>
    <p class="lead">${customer
      ? 'Business plan, stretch and the extended target.'
      : 'Business plan, stretch and the extended target. The ceiling is a reference, not a promise.'}</p>
    ${cap.over_ceiling ? '<div class="callout">Extended target sits above the max-spend ceiling — that is the story this quarter.</div>' : ''}
    <div class="grid2">
      <div class="card"><h3>Build-up to the number we steer to</h3>
        <p class="cap">Grey dashed line is max spend on the current D-Max rate.</p>
        <div class="chart-wrap"><canvas id="cPlan" role="img" aria-label="Plan build-up to extended target">Plan build-up</canvas></div></div>
      <div class="card"><h3>Latest FY actual vs extended target</h3>
        <p class="cap">${customer?'Target in terracotta.':'Target in terracotta. Implied growth is the ledger figure, not a forecast.'}</p>
        <div class="chart-wrap"><canvas id="cAct" role="img" aria-label="Actual versus extended target">Actual vs target</canvas></div></div>
    </div>
    <div class="card">
      <h3>Extended target against the ceiling</h3>
      <div class="bullet" title="Extended target as a share of max spend">
        <div class="fill" style="width:${gpsPctT==null?0:gpsPctT}%"></div>
        <div class="mark" style="left:${gpsPctT==null?0:gpsPctT}%"></div>
      </div>
      <p class="cap">${pct(gpsPctT,0)} of max spend · headroom ${eur(cap.headroom_to_ceiling_eur)} · GPS at BP ${pct(gpsPctB,0)}</p>
    </div>
    <div class="grid3">
      <div class="kpi" ${tipBits(plan.tooltip)}><div class="l">FY${avp.fy_latest||''} actual</div><div class="v">${eurC(avp.fy_latest_actual_eur)}</div>
        <div class="n">to hit extended target needs ${avp.implied_growth_pct==null?'—':avp.implied_growth_pct+'%'}</div></div>
      <div class="kpi" ${tipBits(plan.tooltip)}><div class="l">Extended target vs ceiling</div>
        <div class="v">${pct(gpsPctT,0)}</div>
        <div class="n">headroom ${eur(cap.headroom_to_ceiling_eur)}</div></div>
      <div class="kpi"><div class="l">${customer?'Plan':'BP match'}</div><div class="v">${P.bp_match&&P.bp_match.verdict==='MATCH'?(customer?'<span class="tick">Plan confirmed</span>':'<span class="tick">MATCH</span>'):esc((P.bp_match||{}).verdict||'—')}</div>
        <div class="n">${customer?'Business plan vs extended target':'reviewed plan vs locked workbook'}</div></div>
    </div>`;
  const refLine = {
    id:'refLine',
    afterDraw(ch){
      const x = ch.scales.x, y = ch.scales.y, c = ch.ctx;
      if(!x || cap.max_spend_fy27_eur==null) return;
      const px = x.getPixelForValue(cap.max_spend_fy27_eur);
      c.save(); c.setLineDash([6,4]); c.strokeStyle = MUTED; c.beginPath();
      c.moveTo(px, y.top); c.lineTo(px, y.bottom); c.stroke();
      c.fillStyle = '#6b6256'; c.font = '11px "Segoe UI",sans-serif';
      c.fillText('Ceiling', px+6, y.top+12); c.restore();
    }
  };
  new Chart($('cPlan'), {
    type:'bar',
    data:{ labels:['BP FY27','Stretch','EXT TARGET'],
      datasets:[{
        data:[[0, bpStep.eur],[bpStep.eur, tgStep.eur],[0, tgStep.eur]],
        backgroundColor:[NAVY, AMBER, TERRA],
        barThickness: 26, borderSkipped: false
      }]},
    options:{ indexAxis:'y', maintainAspectRatio:false, plugins:{legend:{display:false}},
      scales:{ x: Object.assign(xEur(), {grid:{color:'#eee'}}), y:{ grid:{display:false} } } },
    plugins:[refLine]
  });
  const gpsRowsAll = (L.gps_fy_spine||{}).rows || [];
  const gpsPub = gpsRowsAll.filter(r=> r.publish!==false && !r.partial_year && r.fy!==2023 && r.actual_eur!=null);
  const actLabels = gpsPub.map(r=>'FY'+r.fy).concat(['FY27 target']);
  const actData = gpsPub.map(r=>r.actual_eur).concat([avp.ext_target_fy27_eur]);
  const actColors = actData.map((_,i)=> i===actData.length-1 ? TERRA : NAVY);
  new Chart($('cAct'), {
    type:'bar',
    data:{ labels: actLabels, datasets:[{ data: actData, backgroundColor: actColors, barThickness: 26 }] },
    options:{ maintainAspectRatio:false, plugins:{legend:{display:false}},
      scales:{ y: yEur(), x:{ grid:{display:false} } } }
  });

  const gps = L.gps_fy_spine || {};
  const grainCtl = gps.grain_control || {};
  function drawGps(){
    const el = $('cGps'); if(!el) return;
    if(el._ch) el._ch.destroy();
    const rows = (gps.rows||[]).filter(r=> r.publish!==false && !r.partial_year && r.fy!==2023);
    const labels = rows.map(r=> 'FY'+r.fy);
    const showPct = L.flags.SHOW_GPS_PCT && (grainCtl.fy||{}).available!==false;
    const ds = [];
    if(showPct){
      ds.push({ label:'GPS %', data: rows.map(r=> r.gps_pct==null ? null : r.gps_pct), borderColor:NAVY, backgroundColor:NAVY,
        tension:0, pointRadius:5, spanGaps:false });
      ds.push({ label:'GPS % ex-warranty', data: rows.map(r=> r.ex_warranty_renderable ? r.gps_pct_ex_warranty : null),
        borderColor:TERRA, backgroundColor:TERRA, tension:0, pointRadius:5, spanGaps:false, borderDash:[6,4] });
    } else {
      ds.push({ label:'GPS-eligible €', data: rows.map(r=> r.actual_eur), borderColor:NAVY, backgroundColor:NAVY, tension:0, pointRadius:5, spanGaps:false });
    }
    el._ch = new Chart(el, { type:'line', data:{ labels, datasets: ds },
      options:{ maintainAspectRatio:false, plugins:{legend:{position:'bottom'},
        tooltip:{ callbacks:{
          label:(item)=>{
            const v = item.raw;
            if(v==null) return item.dataset.label + ': not a valid point this year';
            return item.dataset.label + ': ' + (showPct ? Number(v).toFixed(1)+'%' : eur(v));
          },
          afterBody:(items)=>{
            const i = items[0].dataIndex; const row = rows[i]||{};
            const bits = [];
            if(row.actual_eur!=null) bits.push('GPS-eligible billed '+eur(row.actual_eur));
            if(row.max_spend_eur!=null) bits.push('Max-spend '+eur(row.max_spend_eur)+(row.uio_units_v19?(' · V19 '+row.uio_units_v19+' units'):''));
            if(row.max_spend_basis) bits.push(row.max_spend_basis);
            if(row.max_spend_method) bits.push(row.max_spend_method);
            if(row.gps_pct_v31_published!=null) bits.push('Workbook published GPS '+row.gps_pct_v31_published+'% — audit trail, not the headline');
            if(row.ex_warranty_renderable===false) bits.push('Ex-warranty euro is not a valid point this year — blank, not zero');
            return bits;
          }}}},
        scales:{ y: showPct ? yPct(100) : yEur(),
                 x:{ grid:{display:false} } } } });
    const elE = $('cGpsEur');
    if(elE){
      if(elE._ch) elE._ch.destroy();
      elE._ch = new Chart(elE, { type:'bar',
        data:{ labels, datasets:[{ label:'GPS-eligible €', data: rows.map(r=> r.actual_eur), backgroundColor:NAVY, barThickness:22 }] },
        options:{ maintainAspectRatio:false, plugins:{legend:{display:false},
          tooltip:{ callbacks:{ title:(items)=>{
            const i = items[0].dataIndex; const row = rows[i]||{};
            return 'FY'+row.fy;
          }}}},
          scales:{ y: yEur(), x:{ grid:{display:false} } } } });
    }
  }
  const cyWhy = customer ? '' : ((grainCtl.cy||{}).disabled_reason || 'The locked GPS workbook is fiscal-year only. No published calendar-year GPS% exists. A CY GPS% will not be invented from the wallet.');
  const skip23 = customer ? 'FY2023 is a partial year and stays off the chart.' : ((gps.skip_incomplete||{}).reason || 'FY2023 is a partial year and is not published.');
  const fyNote = grainCtl.on_screen_label_fy || 'Fiscal year (Apr–Mar, labelled by end year) — complete years only';
  const methodLine = gps.method_one_line || 'GPS% = GPS-eligible billed ÷ (V19 parc × that year’s ISZE-net rate). This room is fiscal year.';
  const v31d = gps.v31_dashboard || {};
  const uio = v31d.uio_v19 || {};
  const segs = v31d.uio_by_segment || {};
  const uioN = (obj, y) => (obj && obj[y]!=null) ? Number(obj[y]).toLocaleString('en-GB') : '—';
  const uioBlock = customer ? `
    <div class="grid3" style="margin:0 0 14px">
      <div class="kpi"><div class="l">Parc FY2026</div><div class="v">${uioN(uio,'2026')}</div>
        <div class="n">V19 · FY2027 ${uioN(uio,'2027')}</div></div>
      <div class="kpi"><div class="l">LCV</div><div class="v">${uioN(segs.LCV,'2026')}</div>
        <div class="n">FY2026 · LD ${uioN(segs.LD,'2026')}</div></div>
      <div class="kpi"><div class="l">PMS total capture</div><div class="v">${pct((L.sections.pms||{}).capture_pct_total)}</div>
        <div class="n">CY${(L.sections.pms||{}).year||2025} complete · vs network</div></div>
    </div>` : '';
  $('p-gps').innerHTML = `
    <h2>${customer?'GPS + PMS':'<span class="no">02</span> GPS spine'}</h2>
    <p class="lead">${customer
      ? 'Fiscal year (April–March). Complete years FY2024–FY2026. GPS% with and without warranty. Parc is V19.'
      : 'This room is fiscal year (Apr–Mar). Complete years FY2024–FY2026. Two lines: GPS% and GPS% ex-warranty. Mix and orders keep their own CY + FY toggles.'}</p>
    ${uioBlock}
    <p class="grain-on">${esc(fyNote)}</p>
    <p class="cap">${esc(methodLine)}</p>
    <p class="cap">${esc(skip23)}${cyWhy?(' '+esc(cyWhy)):''}</p>
    ${L.flags.SHOW_GPS_PCT?'':'<div class="callout amber">GPS % is suppressed for this distributor — the denominator is not quotable.</div>'}
    ${L.flags.HAS_V31_FY_SERIES?'':'<div class="callout amber">No fiscal GPS % series exists here. Euros and the locked FY27 figures only — nothing is synthesised.</div>'}
    <div class="card"><h3>GPS %</h3>
      <p class="cap">${customer?'Y-axis 0–100%. Hover for parc, rate and billed.':'Y-axis 0–100%. Ex-warranty is a blank point when that year’s euro is invalid — never a zero. Hover for parc, rate and billed.'}</p>
      <div class="chart-wrap"><canvas id="cGps" role="img" aria-label="GPS percent over complete fiscal years">GPS percent</canvas></div></div>
    <div class="card"><h3>GPS-eligible euros — complete years only</h3>
      <p class="cap">${esc(gps.euro_only_caption||'')} ${customer?'Y-axis starts at 0.':'FY2023 is not published. Y-axis starts at 0.'}</p>
      <div class="chart-wrap"><canvas id="cGpsEur" role="img" aria-label="GPS-eligible euros by complete fiscal year">GPS euros</canvas></div></div>`;
  drawGps();

  const pms = L.sections.pms || {};
  if(pms.available===false || (pms.capture_pct_total==null && !pms.by_category)){
    $('p-pms').innerHTML = `<h2>${customer?'PMS capture':'<span class="no">03</span> PMS'}</h2><div class="empty">${esc(pms.reason||'No PMS')}</div>`;
  } else {
    const cats = (pms.by_category||[]).slice();
    const conf = {CONFIRMED:'confirmed', PROVISIONAL:'provisional', 'NO OEM INTERVAL':'no OEM interval', 'WEAR ITEM':'wear'};
    const pl = pms.parallel_lane || {};
    const plNote = pl.warning ? `<div class="callout amber">${esc(pl.warning)}</div>` : '';
    $('p-pms').innerHTML = `
      <h2>${customer?'PMS capture':'<span class="no">03</span> PMS capture'}</h2>
      <p class="lead">${customer
        ? 'Complete calendar year versus the network on the same expected-quantity model. Primary figure is total capture.'
        : 'Complete calendar year against the network on the same expected-quantity model. Not a time series — the parc in this file does not move.'}</p>
      ${lcvPeerChip()}
      ${plNote}
      <div class="grid3">
        <div class="kpi" ${tipBits(pms.tooltip || (chips.find(c=>c.id==='pms')||{}).tooltip)}><div class="l">This distributor</div><div class="v">${pct(pms.capture_pct_total)}</div>
          <div class="n">${esc(L.meta.display_name||'')}${customer?'':' · sold-to '+((L.meta.sold_to_sap||[]).join(' + '))}</div></div>
        <div class="kpi" ${tipBits((L.compare&&L.compare.lcv_peer_set||{}).tooltip)}><div class="l">LCV-peer average</div><div class="v">${pct(pms.lcv_peer_capture_pct)}</div>
          <div class="n">${pms.vs_lcv_peer_pp==null?'—':(pms.vs_lcv_peer_pp+' pp')} · DBs with ≥90% LCV euro-mix</div></div>
        <div class="kpi" ${tipBits(pms.tooltip || (chips.find(c=>c.id==='pms')||{}).tooltip)}><div class="l">All-network</div><div class="v">${pct(pms.network_capture_pct)}</div>
          <div class="n">${pms.vs_network_pp} pp vs all-network · thinner reference</div></div>
      </div>
      <p class="cap">${esc(pms.compare_note||'LCV-peer is the meaningful compare. All-network is the thinner reference.')} Quotable revenue gap ${eurC(pms.quotable_gap_eur)} · ${pms.categories_quotable} of ${pms.categories_total} categories in the euro total.</p>
      <div class="card"><h3>pp versus LCV-peers and all-network, sorted by revenue gap</h3>
        <p class="cap">Grey labels are not in the euro total. Interval confidence is on the axis. Two series: vs LCV-peers (meaningful) and vs all-network.</p>
        <div class="chart-wrap pms"><canvas id="cPms" role="img" aria-label="PMS versus LCV peers and network">PMS versus peers</canvas></div></div>`;
    new Chart($('cPms'), {
      type:'bar',
      data:{ labels: cats.map(c=> (c.label||c.pms_category) + ' · ' + (conf[c.interval_confidence]||'')),
        datasets:[
          { label:'pp vs LCV-peers', data: cats.map(c=> c.vs_lcv_peer_pp),
            backgroundColor: cats.map(c=> c.quotable===false ? MUTED : ((c.vs_lcv_peer_pp||0)>=0 ? GREEN : TERRA)),
            barThickness: 16 },
          { label:'pp vs all-network', data: cats.map(c=> c.vs_network_pp),
            backgroundColor: MUTED, barThickness: 10 }
        ]},
      options:{ indexAxis:'y', maintainAspectRatio:false, plugins:{legend:{position:'bottom'}},
        scales:{ x:{ ticks:{ callback:v=> (v>0?'+':'')+v+' pp', maxTicksLimit:6 }, grid:{color:'#eee'} },
                 y:{ grid:{display:false}, ticks:{autoSkip:false} } } }
    });
  }

  const mixBlk = L.sections.genuine_vs_bvp || {};
  const mix = mixBlk.whole_book || {};
  const paired = mixBlk.paired_basket_only || {};
  const mixEvo = mixBlk.evolution || {};
  const drill = mixBlk.drill || {};
  const famOpts = drill.family_options || [{key:'all',label:'Whole book',children:[]}];
  const peerTip = (L.compare && L.compare.lcv_peer_set || {}).tooltip || mix.tooltip;
  const famSel = famOpts.map(f=>`<option value="${esc(f.key)}">${esc(f.label)}</option>`).join('');
  $('p-mix').innerHTML = `
    <h2><span class="no">04</span> Genuine vs Best Value</h2>
    <p class="lead">Best Value stays in our channel. It is a mix-quality read, not leakage — never red, never in an erosion total. Whole book is the number to show. The dropdown re-filters the same evolution charts and the part-number table — one grain at a time.</p>
    ${lcvPeerChip()}
    <div class="grid2">
      <div class="card"><div class="chart-wrap"><canvas id="cMix" role="img" aria-label="Whole book mix">Whole book mix</canvas></div>
        <p class="cap">Whole book CY${mix.year||''} — this is the number to show. ${mix.n_pns_bvp||0} Best Value PNs of ${mix.n_pns||0}.</p></div>
      <div class="card">
        <div class="kpi" ${tipBits(mix.tooltip)}><div class="l">Whole book Best Value</div><div class="v">${pct(mix.bvp_share_pct)}</div>
          <div class="n">Genuine ${pct(mix.genuine_share_pct)} · ${mix.n_pns_bvp||0} BVP PNs / ${mix.n_pns||0} · CY${mix.year||''} complete</div></div>
        <p>If you only look at the paired basket you will read <strong>${pct(paired.bvp_share_pct)}</strong> Best Value on <strong>${pct(paired.coverage_pct_of_book)}</strong> of euros. That is the trap — not this distributor’s mix.</p>
        <div class="callout ok">Genuine ${pct(mix.genuine_share_pct)} · Best Value ${pct(mix.bvp_share_pct)} of the whole book.</div>
        <p class="cap">Best Value euros falling is not a value-tier switch. Uncaptured wallet is still outside the tent.</p>
      </div>
    </div>
    <div class="grain-ctl">Mix grain
      <button type="button" class="on" id="mixCy">CY</button>
      <button type="button" id="mixFy">FY</button>
      <span id="mixLab">Calendar years, complete only</span>
    </div>
    <div class="drill-ctl">
      <label>Family <select id="mixFam">${famSel}</select></label>
      <label>Then <select id="mixLeaf"><option value="">All in this family</option></select></label>
      <span id="mixDrillLab" ${tipBits(peerTip)}></span>
    </div>
    <div class="grid2">
      <div class="card"><h3>Genuine vs Best Value share</h3>
        <p class="cap">Y-axis 0–100%. Complete years only. Solid terracotta line is the named LCV peer set, not an anonymous network line.</p>
        <div class="chart-wrap"><canvas id="cMixEvo" role="img" aria-label="Genuine versus Best Value over years">Mix evolution</canvas></div></div>
      <div class="card"><h3>Share of euros they bought — same drill</h3>
        <p class="cap" id="mixEurCap">Genuine vs Best Value = 100% of this drill. Y-axis 0–100%. Euro total in the tooltip, not on the axis. Best Value is green — retention, never red.</p>
        <div class="chart-wrap"><canvas id="cMixEur" role="img" aria-label="Genuine and Best Value share of billed euros">Mix share</canvas></div></div>
    </div>
    <div class="card"><h3>Part numbers on this drill</h3>
      <p class="cap" id="bvpPnCap">What they actually bought on the current grain — genuine vs Best Value euros.</p>
      <div class="scroll" id="bvpPnTable"></div></div>`;
  new Chart($('cMix'), {
    type:'doughnut',
    data:{ labels:['Genuine','Best Value'], datasets:[{ data:[mix.genuine_eur, mix.bvp_eur], backgroundColor:[NAVY, GREEN], borderWidth:0 }] },
    options:{ maintainAspectRatio:false, plugins:{legend:{position:'bottom'}}, cutout:'58%' }
  });
  let mixGrain = 'cy';
  function mixKey(){
    const fam = $('mixFam').value || 'all';
    const leaf = $('mixLeaf').value || '';
    if(fam==='all' || !leaf) return fam;
    return fam + '.' + leaf;
  }
  function fillMixLeaf(){
    const fam = famOpts.find(f=>f.key===($('mixFam').value||'all')) || famOpts[0];
    const kids = fam.children || [];
    $('mixLeaf').innerHTML = '<option value="">All in this family</option>' + kids.map(c=>`<option value="${esc(c.key)}">${esc(c.label)}</option>`).join('');
    $('mixLeaf').disabled = fam.key==='all' || !kids.length;
  }
  function paintMixEvo(){
    const key = mixKey();
    const series = ((drill.series||{})[mixGrain]||{})[key] || (mixGrain==='fy' ? (mixEvo.fy||[]) : (mixEvo.cy||[]));
    const pns = ((drill.pns||{})[mixGrain]||{})[key] || [];
    const pref = mixGrain==='fy' ? 'FY' : 'CY';
    $('mixLab').textContent = mixGrain==='fy' ? 'Fiscal years, complete only (FY2023 skipped)' : 'Calendar years, complete only';
    const fam = famOpts.find(f=>f.key===($('mixFam').value||'all'));
    const leafOpt = (fam && (fam.children||[]).find(c=>c.key===$('mixLeaf').value)) || null;
    $('mixDrillLab').textContent = (leafOpt ? leafOpt.label : (fam ? fam.label : 'Whole book')) + ' · named LCV peer overlay on the same grain';
    const lab = series.map(r=> pref+(r.fy||r.cy));
    const el1 = $('cMixEvo'); if(el1._ch) el1._ch.destroy();
    el1._ch = new Chart(el1, {
      type:'bar',
      data:{ labels: lab,
        datasets:[
          { type:'bar', label:'Genuine %', data: series.map(r=>r.genuine_share_pct), backgroundColor:NAVY, stack:'m', barThickness:24 },
          { type:'bar', label:'Best Value %', data: series.map(r=>r.bvp_share_pct), backgroundColor:GREEN, stack:'m', barThickness:24 },
          { type:'line', label:'LCV peer Best Value %', stack:'p', data: series.map(r=>r.lcv_peer_bvp_share_pct),
            borderColor:TERRA, backgroundColor:TERRA, pointRadius:5, tension:0, borderWidth:3 },
          { type:'line', label:'All-network Best Value %', stack:'n', data: series.map(r=>r.network_bvp_share_pct),
            borderColor:MUTED, backgroundColor:MUTED, pointRadius:3, tension:0, borderWidth:1, borderDash:[4,4] }
        ]},
      options:{ maintainAspectRatio:false, plugins:{legend:{position:'bottom'}},
        scales:{ x:{ stacked:true, grid:{display:false} }, y: Object.assign(yPct(100), {stacked:true}) } }
    });
    const el2 = $('cMixEur'); if(el2._ch) el2._ch.destroy();
    el2._ch = new Chart(el2, {
      type:'bar',
      data:{ labels: lab, datasets:[
        { label:'Genuine %', data: series.map(r=>r.genuine_share_pct), backgroundColor:NAVY, stack:'e', barThickness:24 },
        { label:'Best Value %', data: series.map(r=>r.bvp_share_pct), backgroundColor:GREEN, stack:'e', barThickness:24 }
      ]},
      options:{ maintainAspectRatio:false, plugins:{legend:{position:'bottom'},
        tooltip:{ callbacks:{
          label:(item)=> item.dataset.label + ': ' + (item.raw==null?'—':Number(item.raw).toFixed(1)+'%'),
          afterBody:(items)=>{
            const i = items[0].dataIndex; const row = series[i]||{};
            return ['This drill '+eur(row.total_eur), 'Genuine '+eur(row.genuine_eur), 'Best Value '+eur(row.bvp_eur)];
          }
        }}},
        scales:{ x:{ stacked:true, grid:{display:false} }, y: Object.assign(yPct(100), {stacked:true}) } }
    });
    const last = series.slice(-1)[0] || {};
    $('mixEurCap').textContent = (last.cy||last.fy ? (pref+(last.fy||last.cy)+' · ') : '') +
      'Share of this drill (genuine vs Best Value = 100%). Billed '+eur(last.total_eur)+
      ' (genuine '+eur(last.genuine_eur)+' · Best Value '+eur(last.bvp_eur)+'). Y-axis 0–100, not euros.';
    $('bvpPnCap').textContent = (last.cy||last.fy ? (pref+(last.fy||last.cy)+' · ') : '') + 'What they actually bought on this drill. Genuine vs Best Value euros.';
    $('bvpPnTable').innerHTML = !pns.length ? '<p class="empty">No part numbers billed on this drill in the latest complete year.</p>' :
      `<table><thead><tr><th>Part</th><th>Description</th><th>Tier</th><th class="n">Genuine €</th><th class="n">Best Value €</th><th class="n">Qty</th></tr></thead><tbody>
        ${pns.map(r=>`<tr><td>${esc(r.pn)}</td><td>${esc(r.description||'')}</td><td>${esc(r.tier||'')}</td>
          <td class="n">${eur(r.genuine_eur)}</td><td class="n">${eur(r.bvp_eur)}</td>
          <td class="n">${r.qty==null?'—':Number(r.qty).toLocaleString('en-GB')}</td></tr>`).join('')}
      </tbody></table>`;
  }
  fillMixLeaf();
  paintMixEvo();
  $('mixCy').onclick = () => { mixGrain='cy'; $('mixCy').classList.add('on'); $('mixFy').classList.remove('on'); paintMixEvo(); };
  $('mixFy').onclick = () => { mixGrain='fy'; $('mixFy').classList.add('on'); $('mixCy').classList.remove('on'); paintMixEvo(); };
  $('mixFam').onchange = () => { fillMixLeaf(); paintMixEvo(); };
  $('mixLeaf').onchange = () => paintMixEvo();

  const op = L.sections.order_pattern || {};
  const hist = (op.history||{}).rows || [];
  const histFy = (op.history||{}).fy_rows || [];
  const q1 = op.q1_fy2027 || {};
  const oc = op.other_coded || {};
  const mr = op.meeting_read || {};
  const guide = op.guideline || {};
  const remark = (q1.verdict_colour==='red')
    ? `<div class="callout">We want about 80% stock orders and 20% rush. High urgency usually means the network is using us as a same-day warehouse.</div>`
    : (q1.verdict_colour==='amber'
      ? `<div class="callout amber">${esc(q1.verdict_reason||'Coded share too thin to sign the mix.')}</div>`
      : `<div class="callout ok">Rush share is inside the 80/20 guideline on complete years. The warehouse remark does not fire.</div>`);
  const vor = mr.vor_vs_target || {};
  const stockTip = guide.tooltip || {formula:'Stock = SOR + PRD. Rush = VOR / RUSH / SVOR. PRD is treated as stock on this screen.', snapshot:'Complete years', not_included:'Credits. Incomplete years. Not invoicing-by-weekday.'};
  const ocTip = oc.tooltip || stockTip;
  const ocCodes = (oc.codes||[]).join(', ') || 'none — PRD is inside stock';
  const ordCmp = op.compare || {};
  $('p-ord').innerHTML = `
    <h2><span class="no">05</span> Order pattern</h2>
    <p class="lead">Stock versus rush on billed euros, back in time. PRD is treated as stock on this screen. Not invoicing-by-weekday. Overlay: this book vs the named LCV peer set vs all-network.</p>
    ${lcvPeerChip()}
    ${remark}
    <div class="grain-ctl">Order grain
      <button type="button" class="on" id="ordCy">CY</button>
      <button type="button" id="ordFy">FY</button>
      <span id="ordLab">Calendar years, complete only</span>
    </div>
    <div class="grid2">
      <div class="card"><h3>Stock vs rush — evolution</h3>
        <div class="chart-wrap"><canvas id="cSaty" role="img" aria-label="Stock versus rush over years">Order type mix</canvas></div>
        <p class="cap" ${tipBits(stockTip)}>Stock = SOR + PRD. Rush = VOR / RUSH / SVOR. Other coded: ${esc(ocCodes)}. Terracotta line is LCV peer rush % (named set). Grey dashed is all-network.</p></div>
      <div class="card"><h3>Rush share vs 80/20</h3>
        <p class="cap" ${tipBits(stockTip)}>Complete CY${vor.cy||''}. PRD is inside stock. LCV peer is the named ≥90% LCV set, labelled in the chip above.</p>
        <div class="chart-wrap"><canvas id="cVor" role="img" aria-label="Rush versus 80/20 and LCV peers">Rush versus target</canvas></div>
        <p class="lead">Q1 FY2027 coded share ${pct(q1.coded_share_of_eur_pct)} · stock ${pct(q1.stock_pct)} · rush ${pct(q1.rush_class_pct)} of the coded base.</p></div>
    </div>
    <div class="card"><h3>${esc(mr.title||'Rush versus stock by PMS family')}</h3>
      <p class="cap">${esc(mr.grain||'')} · ${esc(mr.lcv_peer_overlay||'LCV peer overlay is the named ≥90% LCV set.')} Default view is share % of each family’s billed euros; tooltip has euros.</p>
      <div class="grain-ctl">Family view
        <button type="button" class="on" id="rushPct">%</button>
        <button type="button" id="rushEur">€</button>
        <span>Share of each family’s billed euros, or euros. LCV peer is labelled, not a thin anonymous line.</span>
      </div>
      <div class="chart-wrap pms"><canvas id="cRushFam" role="img" aria-label="Rush versus stock by PMS family">Rush by family</canvas></div></div>
    <div class="card"><h3>Top rush part numbers</h3>
      ${!(mr.top_rush_pns||[]).length ? '<p class="empty">No rush euros on this book.</p>' :
      `<div class="scroll"><table><thead><tr><th>Part</th><th>Description</th><th>PMS</th><th class="n">Rush €</th></tr></thead><tbody>
        ${(mr.top_rush_pns||[]).map(r=>`<tr><td>${esc(r.pn)}</td><td>${esc(r.description||'')}</td><td>${esc(r.pms_label||'—')}</td><td class="n">${eur(r.rush_eur)}</td></tr>`).join('')}
      </tbody></table></div>`}</div>`;
  let ordGrain = 'cy';
  function paintOrd(){
    const years = ordGrain==='fy' ? (histFy||[]).filter(r=>r.complete) : hist.filter(r=>r.complete_cy||r.complete);
    const cmp = ordGrain==='fy' ? (ordCmp.fy||[]) : (ordCmp.cy||[]);
    const byY = {};
    cmp.forEach(r=> { byY[r.fy||r.cy] = r; });
    const pref = ordGrain==='fy' ? 'FY' : 'CY';
    $('ordLab').textContent = ordGrain==='fy' ? 'Fiscal years, complete only (FY2023 skipped)' : 'Calendar years, complete only';
    const el = $('cSaty'); if(el._ch) el._ch.destroy();
    const hasOther = years.some(r=> (r.other_coded_pct||0) > 0);
    const ds = [
      { type:'bar', label:'Stock (SOR + PRD)', data: years.map(r=>r.stock_pct||0), backgroundColor:NAVY, stack:'m', barThickness:28 },
      { type:'bar', label:'Rush (VOR/RUSH/SVOR)', data: years.map(r=>r.rush_class_pct||0), backgroundColor:TERRA, stack:'m', barThickness:28 }
    ];
    if(hasOther) ds.splice(1,0,{ type:'bar', label: oc.label||'Other coded', data: years.map(r=>r.other_coded_pct||0), backgroundColor:AMBER, stack:'m', barThickness:28 });
    ds.push(
      { type:'line', label:'LCV peer rush %', stack:'p', data: years.map(r=> (byY[r.fy||r.cy]||{}).lcv_peer_rush_pct),
        borderColor:TERRA, backgroundColor:TERRA, pointRadius:5, tension:0, borderWidth:3 },
      { type:'line', label:'All-network rush %', stack:'n', data: years.map(r=> (byY[r.fy||r.cy]||{}).network_rush_pct),
        borderColor:MUTED, backgroundColor:MUTED, pointRadius:3, tension:0, borderWidth:1, borderDash:[4,4] }
    );
    el._ch = new Chart(el, {
      type:'bar',
      data:{ labels: years.map(r=> pref+(r.fy||r.cy)), datasets: ds },
      options:{ maintainAspectRatio:false, plugins:{legend:{position:'bottom'}},
        scales:{ x:{ stacked:true, grid:{display:false} }, y: Object.assign(yPct(100), {stacked:true}) } }
    });
  }
  paintOrd();
  $('ordCy').onclick = () => { ordGrain='cy'; $('ordCy').classList.add('on'); $('ordFy').classList.remove('on'); paintOrd(); };
  $('ordFy').onclick = () => { ordGrain='fy'; $('ordFy').classList.add('on'); $('ordCy').classList.remove('on'); paintOrd(); };
  const lastCmp = (ordCmp.cy||[]).slice(-1)[0] || {};
  new Chart($('cVor'), {
    type:'bar',
    data:{ labels:['Stock','Rush'],
      datasets:[
        { label:'This book', data:[vor.stock_pct, vor.rush_pct], backgroundColor:[NAVY, TERRA], barThickness:28 },
        { label:'LCV peer average', data:[lastCmp.lcv_peer_stock_pct, lastCmp.lcv_peer_rush_pct], backgroundColor:TERRA, barThickness:18 },
        { label:'All-network', data:[lastCmp.network_stock_pct, lastCmp.network_rush_pct], backgroundColor:MUTED, barThickness:12 },
        { label:'80/20 guideline', data:[vor.target_stock_pct, vor.target_rush_pct], backgroundColor:'#c9d4e6', barThickness:10 }
      ]},
    options:{ maintainAspectRatio:false, plugins:{legend:{position:'bottom'}},
      scales:{ y: yPct(100), x:{ grid:{display:false} } } }
  });
  const fams = (mr.by_pms_family||[]).filter(f=>f.pms_category!=='not_pms').slice(0,10);
  let rushFamMode = 'pct';
  function paintRushFam(){
    const el = $('cRushFam');
    if(!el || !fams.length) return;
    if(el._ch) el._ch.destroy();
    const famHasOther = fams.some(f=> (f.other_coded_eur||0) > 0 || (f.other_coded_pct||0) > 0);
    let ds, xScale;
    if(rushFamMode==='pct'){
      ds = [
        { label:'This book stock %', data: fams.map(f=>f.stock_pct), backgroundColor:NAVY, barThickness:18 },
        { label:'This book rush %', data: fams.map(f=>f.rush_pct), backgroundColor:TERRA, barThickness:18 },
        { label:'LCV peer stock %', data: fams.map(f=>f.lcv_peer_stock_pct), backgroundColor:'#7dcea0', barThickness:12 },
        { label:'LCV peer rush %', data: fams.map(f=>f.lcv_peer_rush_pct), backgroundColor:'#c0552d', barThickness:12 }
      ];
      if(famHasOther) ds.splice(2,0,{ label: oc.label||'Other coded %', data: fams.map(f=>f.other_coded_pct), backgroundColor:AMBER, barThickness:12 });
      xScale = Object.assign(yPct(100), {grid:{color:'#eee'}});
    } else {
      ds = [
        { label:'Stock (incl. PRD)', data: fams.map(f=>f.stock_eur), backgroundColor:NAVY, stack:'f', barThickness:18 },
        { label:'Rush', data: fams.map(f=>f.rush_eur), backgroundColor:TERRA, stack:'f', barThickness:18 }
      ];
      if(famHasOther) ds.splice(1,0,{ label: oc.label||'Other coded', data: fams.map(f=>f.other_coded_eur), backgroundColor:AMBER, stack:'f', barThickness:18 });
      xScale = Object.assign(xEur(), {stacked:true, grid:{color:'#eee'}});
    }
    el._ch = new Chart(el, {
      type:'bar',
      data:{ labels: fams.map(f=>f.label||f.pms_category), datasets: ds },
      options:{ indexAxis:'y', maintainAspectRatio:false, plugins:{legend:{position:'bottom'},
        tooltip:{ callbacks:{
          label:(item)=>{
            const v = item.raw;
            if(v==null) return item.dataset.label + ': —';
            if(rushFamMode==='pct') return item.dataset.label + ': ' + Number(v).toFixed(1) + '%';
            return item.dataset.label + ': ' + eur(v);
          },
          afterBody:(items)=>{
            const i = items[0].dataIndex; const f = fams[i]||{};
            return ['Family billed '+eur(f.total_eur), 'Stock '+eur(f.stock_eur)+' · Rush '+eur(f.rush_eur)];
          }
        }}},
        scales:{ x: xScale, y:{ stacked: rushFamMode!=='pct', grid:{display:false}, ticks:{autoSkip:false} } } }
    });
  }
  paintRushFam();
  if($('rushPct')){
    $('rushPct').onclick = () => { rushFamMode='pct'; $('rushPct').classList.add('on'); $('rushEur').classList.remove('on'); paintRushFam(); };
    $('rushEur').onclick = () => { rushFamMode='eur'; $('rushEur').classList.add('on'); $('rushPct').classList.remove('on'); paintRushFam(); };
  }

  const lanes = L.sections.three_lanes || {};
  const g1 = lanes.gps_gap||{}, g2 = lanes.pms_gap||{}, g3 = lanes.iam_gap||{};
  const iamDelta = g3.revenue_weighted_delta_pct;
  const iamGood = iamDelta!=null && iamDelta >= 0;
  const probes = g3.probes||{};
  const bvpAlt = L.sections.bvp_alternatives || {};
  const strat = L.sections.lost_sales_strategy || {};
  const pref = lanes.pricing_reference || strat.pricing_reference || {};
  const prefTip = pref.tooltip || {formula: pref.formula || 'PR00 net × 1.40 × 1.275 = ×1.785', snapshot: pref.source || '', not_included: 'Not ISZE net-to-DB. Not observed SPA terms.'};
  $('p-lost').innerHTML = `
    <h2><span class="no">06</span> Three lanes — never added</h2>
    <p class="lead">${esc(lanes.hard_rule||'Three siblings on different bases. Never summed.')}</p>
    ${lcvPeerChip()}
    <div class="kpi" ${tipBits(prefTip)} style="margin:0 0 14px"><div class="l">Lost-sales price reference</div>
      <div class="v" style="font-size:18px">Projected ISZE retail</div>
      <div class="n">${esc(pref.formula||'PR00 × 1.40 × 1.275 = ×1.785')} · ${esc(pref.source||'config.yaml')} · not ISZE net-to-DB</div></div>
    <div class="grid3">
      <div class="lane"><h3>GPS gap</h3><div class="v">${eurC(g1.value_eur)}</div>
        <p class="n">${esc(g1.meaning||'')} · ${esc(g1.grain||'')}</p></div>
      <div class="lane"><h3>PMS gap</h3><div class="v">${eurC(g2.value_eur)}</div>
        <p class="n">${esc(g2.meaning||'')} · ${esc(g2.grain||'')}</p></div>
      <div class="lane"><h3>Aftermarket</h3>
        <div class="v">${g3.available?eurC(g3.db_revenue_on_exposed_pns_eur):'—'}</div>
        <p class="n">${g3.available
          ? ('This book’s euros on parts where we sit above the aftermarket average. Coverage chips on Aftermarket. Positive delta = we are cheaper ('
             + (iamGood ? '<span class="tag ok">' : '<span class="tag bad">') + pct(iamDelta) + '</span>). Do not add probes.')
          : esc(g3.reason||'Empty')}</p></div>
    </div>
    <p class="cap">No total. No shared axis. Best Value is not in an erosion total — it is the lever below.</p>
    <div class="card"><h3>${esc(bvpAlt.title||'Will Best Value be sufficient?')}</h3>
      <p class="lead">${esc(bvpAlt.lead||'Part-number test: is Best Value projected retail at or below a named T3/T4?')}</p>
      <div class="grid3">
        <div class="kpi" ${tipBits(bvpAlt.tooltip)}><div class="l">Pairs on this book</div><div class="v">${bvpAlt.n||0}</div>
          <div class="n">${bvpAlt.n_filters||0} filters · ${bvpAlt.n_brakes||0} brakes</div></div>
        <div class="kpi"><div class="l">BVP sufficient</div><div class="v">${bvpAlt.n_bvp_sufficient||0}</div>
          <div class="n">At or below named T3/T4, or no quality IAM</div></div>
        <div class="kpi"><div class="l">BVP not enough</div><div class="v">${bvpAlt.n_bvp_not_enough||0}</div>
          <div class="n">Still above T3/T4 — SPA on genuine, not just offer BVP</div></div>
      </div>
      ${!(bvpAlt.rows||[]).length ? '<p class="empty">No Best Value pair on a billed genuine PMS part in the crossref for this sold-to.</p>' :
      `<div class="scroll"><table><thead><tr>
        <th>Genuine</th><th>Best Value PN</th><th>Family</th>
        <th class="n">Genuine billed €</th>
        <th class="n">Genuine ISZE net</th><th class="n">Genuine projected retail</th>
        <th class="n">BVP ISZE net</th><th class="n">BVP projected retail</th>
        <th class="n">Gap (retail)</th>
        <th>Quality IAM</th>
        <th>Verdict</th></tr></thead><tbody>
        ${(bvpAlt.rows||[]).map(r=>{
          const verd = r.bvp_verdict||'';
          const vchip = verd==='bvp_sufficient' ? '<span class="tag bvpok">BVP sufficient</span>'
            : verd==='bvp_not_enough' ? '<span class="tag bvpno">BVP not enough</span>'
            : '<span class="tag grey">No BVP price</span>';
          const iamBits = [r.quality_brand||'', r.quality_tier?('T'+r.quality_tier):'', r.quality_source||'', r.iam_point_kind||''].filter(Boolean).join(' · ');
          return `<tr>
          <td>${esc(r.genuine_pn)}<div class="n" style="text-align:left;color:#6b6256">${esc(r.description||'')}</div></td>
          <td>${(r.bvp_pns||[]).map(esc).join(', ')}${r.bvp_pn_priced?('<div class="n" style="text-align:left;color:#6b6256">priced '+esc(r.bvp_pn_priced)+'</div>'):''}</td>
          <td>${esc(r.family_label||r.family||'')}</td>
          <td class="n">${eur(r.genuine_eur_cy)}</td>
          <td class="n">${unit(r.genuine_isze_net_eur)}</td>
          <td class="n">${unit(r.genuine_proj_retail_eur)}</td>
          <td class="n">${unit(r.bvp_isze_net_eur)}</td>
          <td class="n">${unit(r.bvp_proj_retail_eur)}</td>
          <td class="n">${unit(r.gap_genuine_vs_bvp_retail_eur)}</td>
          <td>${iamBits?esc(iamBits):'—'}<div style="color:#6b6256;font-size:12px">${r.quality_iam_eur==null?'':(unit(r.quality_iam_eur)+(r.iam_like_for_like_note?(' · '+esc(r.iam_like_for_like_note)):''))}</div></td>
          <td>${vchip}<div style="color:#6b6256;font-size:12px">${esc(r.lever||r.verdict_label||'')}</div></td></tr>`;
        }).join('')}
      </tbody></table></div>`}</div>`;

  const bq = L.sections.brand_quality || {};
  const spa = L.sections.spa_candidates || {};
  const il = L.sections.local_catalogue || {};
  const ladder = bq.policy_ladder || [];
  const euroCol = spa.euro_column || {};
  const retailCol = spa.retail_column || {};
  const billedCol = spa.billed_column || {};
  const iamCol = spa.iam_column || {};
  const deltaCol = spa.delta_column || g3.delta_formula || {};
  const ch = L.channel || {};
  const retailTip = retailCol.tooltip || {formula: ch.formula || 'PR00 net × 1.40 × 1.275 = ×1.785', snapshot: ch.as_of || '', not_included: 'Not observed SPA terms. Δ% uses this, not ISZE net.'};
  const offerLink = (u) => {
    const s = String(u||'');
    if(s.indexOf('https://')!==0) return '—';
    return '<a class="offer" href="'+esc(s)+'" target="_blank" rel="noopener">Open offer</a>';
  };
  const probeChip = (key) => {
    const p = probes[key]||{};
    if(!p.available) return '';
    const asofRaw = p.as_of_note || (p.as_of ? ('as-of '+p.as_of) : '');
    const asof = customer ? asofRaw.replace(/\s*[—–-]\s*not the .+$/i,'') : asofRaw;
    const out = p.outdated ? ' out' : '';
    const snapWho = customer ? (L.meta.display_name||'') : ((L.meta.display_name||'')+' '+(L.meta.sold_to_sap||[]).join('/'));
    return `<div class="srcchip${out}" ${tipBits({formula: customer ? 'Share of this book’s CY2025 ISZE net on part numbers matched in this named catalogue. Δ % is vs projected ISZE retail. Positive = ISZE cheaper at retail.' : 'Share of this sold-to’s CY2025 ISZE net (credits excluded) on part numbers matched in this named catalogue. Δ % is vs projected ISZE retail (PR00 × 1.40 × 1.275). Positive = ISZE cheaper at retail. Coverage chips are not added together.', snapshot:(asof||'CY2025 complete')+' · '+snapWho, not_included: customer ? '' : 'Do not add KS + Mekonomen + Eucon. Do not compare IAM retail to ISZE net. Network gp_at_risk is not attributed.'})}><b>${esc(p.label||key)}</b><br>${p.n||0} PNs · ${pct(p.db_revenue_coverage_pct, 2)} of CY2025 euros${asof?('<div class="n">'+esc(asof)+'</div>'):''}</div>`;
  };
  const locChip = (il.available && !il.pn_join)
    ? `<div class="srcchip"><b>${esc(il.label||'Local catalogue')}</b><br>${il.n_priced_rows||0} priced offers · family only, no part-number join</div>` : '';
  const SRC_LAB = {eucon:'Eucon DE/NO', eucon_uk_2023:'Eucon 2023 UK', ks:'KS', mekonomen:'Mekonomen'};
  const srcTags = (hits) => {
    const h = hits||[];
    if(!h.length) return '<span class="tag grey">none</span>';
    return h.map(k=>'<span class="tag">'+esc(SRC_LAB[k]||k)+'</span>').join(' ');
  };
  const famStrat = strat.family_rows || [];
  const sc = strat.counts || {};
  $('p-fam').innerHTML = `
    <h2><span class="no">07</span> Family strategy</h2>
    <p class="lead">Family rollup for the meeting — not a repeat of the part-number BVP test. Filters (oil / air / fuel) first, then brakes, then the rest. PMS capture is versus LCV peer.</p>
    ${lcvPeerChip()}
    ${strat.available===false ? `<div class="empty">${esc(strat.reason||'')}</div>` : `
    <p class="lead">${esc(strat.most_important_lever||'')}</p>
    <p class="cap">${esc(strat.customer_tone||'')}</p>
    <div class="grid3">
      <div class="kpi"><div class="l">Families on screen</div><div class="v">${sc.n_families_on_screen||0}</div>
        <div class="n">${sc.n_priority_families||0} filter / brake first</div></div>
      <div class="kpi"><div class="l">BVP sufficient</div><div class="v">${sc.n_bvp_sufficient||0}</div>
        <div class="n">${sc.n_bvp_not_enough||0} BVP not enough</div></div>
      <div class="kpi"><div class="l">SPA / Hold</div><div class="v">${sc.n_pn_spa||0} / ${sc.n_hold||0}</div>
        <div class="n">SPA only where retail &gt; T3/T4 and no sufficient BVP</div></div>
    </div>
    <div class="card"><h3>One action per family</h3>
      <div class="scroll"><table><thead><tr>
        <th>Family</th><th class="n">Billed €</th>
        <th class="n">PMS capture</th><th class="n">vs LCV peer</th>
        <th class="n">BVP pairs</th><th class="n">BVP sufficient</th><th class="n">BVP not enough</th>
        <th class="n">SPA</th><th class="n">Hold</th><th>Action</th></tr></thead><tbody>
        ${famStrat.map(f=>`<tr><td>${esc(f.label||f.family)}</td>
          <td class="n">${eur(f.billed_eur)}</td>
          <td class="n">${pct(f.pms_capture_pct)}</td>
          <td class="n">${f.pms_vs_lcv_peer_pp==null?'—':((f.pms_vs_lcv_peer_pp>0?'+':'')+f.pms_vs_lcv_peer_pp+' pp')} <span style="color:#6b6256">${pct(f.pms_lcv_peer_capture_pct)}</span></td>
          <td class="n">${f.n_bvp_pairs||0}</td>
          <td class="n">${f.n_bvp_sufficient||0}</td>
          <td class="n">${f.n_bvp_not_enough||0}</td>
          <td class="n">${f.n_spa||0}</td>
          <td class="n">${f.n_hold||0}</td>
          <td>${esc(f.action||f.first_lever||'')}</td></tr>`).join('')}
      </tbody></table></div></div>`}`;
  $('p-spa').innerHTML = `
    <h2>${customer?'Aftermarket situation':'<span class="no">08</span> Aftermarket PNs'}</h2>
    <p class="lead">${customer
      ? 'Named-site matches on this book. Δ % versus projected ISZE retail. SPA where we are still above named T3/T4 and Best Value is missing or not enough. Empty SPA cells mean Hold — already cheaper, or no quality IAM.'
      : 'Named-site matches on this sold-to’s book. Δ % versus projected ISZE retail (PR00 × 1.40 × 1.275). SPA only where we are still above named T3/T4 and Best Value is missing or not enough. Empty SPA cells mean Hold — already cheaper, or no quality IAM.'}</p>
    <p class="honesty">${esc(spa.pricing_honesty||'')}</p>
    <h3 style="font-family:Georgia,serif;color:#1a2b4a;margin:0 0 8px;font-size:16px">Sources on this book</h3>
    <div class="srcchips">${probeChip('eucon')}${probeChip('eucon_uk_2023')}${probeChip('ks')}${probeChip('mekonomen')}${locChip}</div>
    <div class="card"><h3>Policy ladder — max ISZE premium vs aftermarket</h3>
      <div class="chart-wrap"><canvas id="cCeil" role="img" aria-label="Brand quality ceilings">Brand quality ceilings</canvas></div>
      <p class="cap">${esc(bq.render_rule||'')}</p></div>
    <div class="grid2" style="margin-top:14px">
      <div class="kpi"><div class="l">Matched aftermarket lines in this book</div><div class="v">${bq.n_iam_pns_in_this_db||0}</div>
        <div class="n">${bq.n_over_ceiling||0} over their brand ceiling${customer?'':' · probes not added'}</div></div>
      <div class="kpi" ${tipBits({formula: spa.rule, snapshot:'This book ∩ aftermarket probes', not_included:'No aftermarket match is not a SPA. Crossref incomplete is not “no Best Value in catalogue”. T1 never auto-cuts.'})}><div class="l">SPA candidates</div><div class="v">${spa.n||0}</div>
        <div class="n">${esc(spa.note||'')}</div></div>
    </div>
    <div class="card"><h3>SPA list</h3>
      <p class="lead">${esc(spa.cta_block||'Please apply for an SPA')}</p>
      ${!(spa.rows||[]).length ? '<p class="empty">No SPA candidates under the rule. Either Best Value is sufficient, or aftermarket evidence says we are cheaper, or there is no aftermarket match.</p>' :
      `<div class="scroll"><table><thead><tr>
        <th>Part</th><th>Description</th>
        <th class="n" ${tipBits(euroCol.tooltip)}>${esc(euroCol.label||'ISZE net / unit')}</th>
        <th class="n" ${tipBits(retailTip)}>${esc(retailCol.label||'Projected ISZE retail')}</th>
        <th class="n" ${tipBits(iamCol.tooltip)}>${esc(iamCol.label||'IAM quality offer / unit')}</th>
        <th class="n" ${tipBits(deltaCol.tooltip||retailTip)}>${esc(deltaCol.label||'Δ % vs projected ISZE retail')}</th>
        <th class="n">Proposed band</th>
        <th class="n" ${tipBits(billedCol.tooltip)}>${esc(billedCol.label||'Billed CY2025 €')}</th>
        <th>Scrapers on this PN</th><th>Apply SPA</th></tr></thead><tbody>
        ${(spa.rows||[]).map(r=>`<tr><td>${esc(r.pn)}</td><td>${esc(r.description||'')}</td>
          <td class="n">${unit(r.isze_price_eur)}</td>
          <td class="n">${unit(r.proj_retail_eur)}</td>
          <td class="n">${unit(r.competitor_avg_eur)}<div style="color:#6b6256;font-size:12px">${esc(r.quality_brand||r.probe_label||'')} ${r.quality_tier?('T'+r.quality_tier):''} · ${esc(r.iam_point_kind||'')} ${r.iam_like_for_like_note?esc(r.iam_like_for_like_note):''}</div></td>
          <td class="n">${r.delta_pct==null?'—':((r.delta_pct<0?'<span class="tag bad">':'<span class="tag ok">')+pct(r.delta_pct)+'</span>')}</td>
          <td class="n">${r.cta && r.proposed_isze_eur!=null?unit(r.proposed_isze_eur):(r.cta && r.band_high_eur!=null?('up to '+unit(r.band_high_eur)):'—')}</td>
          <td class="n">${eur(r.db_revenue_cy_eur)}</td>
          <td>${srcTags(r.sources_hit)}</td>
          <td>${r.cta?`<span class="cta">${esc(r.cta)}</span>`:'<span class="cta none">—</span>'}</td></tr>`).join('')}
      </tbody></table></div>`}</div>
    <div class="card"><h3>Aftermarket matches in this book</h3>
      <p class="cap" ${tipBits(deltaCol.tooltip||retailTip)}>${customer?'Every named-site match on this CY2025 book. ':'Every named-site match on this sold-to’s CY2025 book. '}${esc(deltaCol.formula||'(IAM − projected ISZE retail) / projected ISZE retail')}. Positive = ISZE cheaper at retail.${customer?'':' ' + esc(deltaCol.compared_to||'IAM trade vs projected retail is still not perfect like-for-like.') + ' Coverage chips above are not added together.'}</p>
      ${!(g3.rows||[]).length ? '<p class="empty">No aftermarket part-number match for this book.</p>' :
      `<div class="scroll"><table><thead><tr>
        <th>Part</th><th>Description</th><th>Scrapers on this PN</th>
        <th class="n" ${tipBits(euroCol.tooltip)}>${esc(euroCol.label||'ISZE net / unit')}</th>
        <th class="n" ${tipBits(retailTip)}>${esc(retailCol.label||'Projected ISZE retail')}</th>
        <th class="n" ${tipBits(iamCol.tooltip)}>${esc(iamCol.label||'IAM quality offer / unit')}</th>
        <th class="n" ${tipBits(deltaCol.tooltip||{})}>${esc(deltaCol.label||'Δ % vs projected retail')}</th>
        <th class="n" ${tipBits(billedCol.tooltip)}>${esc(billedCol.label||'Billed CY2025 €')}</th>
        <th>Offer</th></tr></thead><tbody>
        ${(g3.rows||[]).map(r=>`<tr><td>${esc(r.pn)}</td><td>${esc(r.description||'')}</td>
          <td>${srcTags(r.sources_hit)}${r.iam_point_kind?(' · '+esc(r.iam_point_kind)):''}${r.suspect?' <span class="tag warn">suspect title</span>':''}<div style="color:#6b6256;font-size:12px">${esc(r.iam_like_for_like_note||'')}</div></td>
          <td class="n">${unit(r.isze_price_eur)}</td>
          <td class="n">${unit(r.proj_retail_eur)}</td>
          <td class="n">${unit(r.competitor_avg_eur)}</td>
          <td class="n">${r.delta_pct==null?'—':((r.delta_pct<0?'<span class="tag bad">':'<span class="tag ok">')+pct(r.delta_pct)+'</span>')}</td>
          <td class="n">${eur(r.db_revenue_cy_eur)}</td>
          <td>${offerLink(r.competitor_url)}</td></tr>`).join('')}
      </tbody></table></div>`}</div>
    ${il.available===false ? (customer?'':`<div class="empty">${esc(il.reason||'')}</div>`) : `
      <div class="card"><h3>${esc(il.label||'Local aftermarket catalogue')}</h3>
        <p class="lead">${esc(il.why_no_pn||'')} ${esc(il.fx_note||'')}</p>
        <div class="chart-wrap"><canvas id="c365" role="img" aria-label="Aftermarket catalogue families">Catalogue families</canvas></div>
        <p class="cap">${il.n_priced_rows} priced offers · ${esc(il.quality_note||'')}</p></div>`}`;
  new Chart($('cCeil'), {
    type:'bar',
    data:{ labels: ladder.map(t=>'T'+t.tier+' '+t.label),
      datasets:[{ data: ladder.map(t=>t.ceiling_pct), backgroundColor:[NAVY, BLUE, AMBER, TERRA], barThickness:22 }]},
    options:{ indexAxis:'y', maintainAspectRatio:false, plugins:{legend:{display:false}},
      scales:{ x:{ min:0, ticks:{ callback:v=>'+'+v+'%', maxTicksLimit:6 }, suggestedMax:260, grid:{color:'#eee'} }, y:{ grid:{display:false} } } }
  });
  if(il.available && $('c365')){
    const fams365 = il.families||[];
    new Chart($('c365'), {
      type:'bar',
      data:{ labels: fams365.map(f=>f.family), datasets:[{ label:'Offers', data: fams365.map(f=>f.n), backgroundColor:TERRA, barThickness:22 }] },
      options:{ maintainAspectRatio:false, plugins:{legend:{display:false}},
        scales:{ y: Object.assign(yEur(), {ticks:{ maxTicksLimit:5, callback:v=>v }}), x:{ grid:{display:false} } } }
    });
  }

  const ws = L.sections.working_set || {};
  $('p-parts').innerHTML = `
    <h2><span class="no">09</span> Top parts</h2>
    <p class="lead">Top 30 by euro, complete calendar year. Shell marked and excluded from the GPS numerator. Warranty-adjacent hardware is flagged, not deleted.</p>
    ${ws.warranty_exclusion_warning?`<div class="callout amber">${esc(ws.warranty_exclusion_warning)}</div>`:''}
    <div class="scroll"><table><thead><tr><th>Part</th><th>Description</th><th class="n">€</th><th class="n">Share</th><th>Best Value</th><th>Aftermarket</th><th>Lever</th></tr></thead><tbody>
      ${(ws.rows||[]).map(r=>`<tr class="${r.is_shell_lubricant?'shell':''}">
        <td>${esc(r.pn)}${r.is_shell_lubricant?' <span class="tag grey">Shell</span>':''}</td>
        <td>${esc((r.description||'').trim())}</td>
        <td class="n">${eur(r.eur)}</td>
        <td class="n">${pct(r.share_of_cy_eur_pct)}</td>
        <td>${r.bvp_alternative_in_crossref?'alt in crossref': r.is_itself_a_bvp_pn?'is Best Value':'none in crossref'}</td>
        <td>${r.iam_delta_pct==null?'—': (r.iam_delta_pct<0? '<span class="tag bad">we are dearer</span>':'<span class="tag ok">we are cheaper</span>')}</td>
        <td>${esc(r.lever||'')}</td></tr>`).join('')}
    </tbody></table></div>`;

  const ids = L.sections.ids || {};
  if(!ids.available){
    $('p-ids').innerHTML = `<h2>${customer?'IDS':'<span class="no">10</span> Dealer standard'}</h2><div class="empty">${esc(ids.reason||'No dealer pack for this distributor.')}</div>`;
  } else {
    const sum = ids.summary||[];
    const mat = ids.matrix||[];
    const e = ids.section_e||{};
    const os = ids.os || {};
    const eHeld = e.fill==='not_scored';
    const leadPp = ids.lead_vs_network_pp;
    const leadLab = ids.lead_label || ('Section '+(ids.lead_section||'D'));
    const leadCap = ids.lead_section==='D'
      ? 'versus the network — Parts is the gap to work'
      : (customer ? 'versus the network — weakest scored section' : 'versus the network — weakest scored section (not a sales forecast)');
    const dPp = ids.section_d_vs_network_pp;
    const hits = os.hit_list || [];
    const steps = os.next_steps || [];
    const pull = os.pull_metrics || [];
    const annexRoot = os.annex_root || '';
    const pill = b => {
      const k = (b||'').toLowerCase();
      const cls = k.indexOf('need')>=0 ? 'weak' : k.indexOf('good')>=0 ? 'good' : 'medium';
      return `<span class="pill ${cls}">${esc(b||'')}</span>`;
    };
    const osBlock = os.available ? `
      <div class="callout ok">${esc(os.one_liner||'')}</div>
      <div class="grid3">
        <div class="kpi"><div class="l">Country average</div>
          <div class="v">${os.country_avg_pct==null?'—':os.country_avg_pct+'%'}</div>
          <div class="n">${os.in_average||'—'} of ${os.evaluated||'—'} dealers in the average</div></div>
        <div class="kpi"><div class="l">Hit list</div>
          <div class="v">${hits.length}</div>
          <div class="n">${os.below_average_n==null?'Below average and/or Needs improvement':os.below_average_n+' of '+(os.below_average_of||'')+' below average · cap 12'}</div></div>
        <div class="kpi"><div class="l">Parts versus network</div>
          <div class="v">${dPp==null?'—':dPp+' pp'}</div>
          <div class="n">Section D — keep on the chart even when another section is weaker</div></div>
      </div>
      <div class="card"><h3>Hit list — visit first</h3>
        <p class="cap">Open the workshop pack for the visit. Owner / date stay blank until the planning meeting.</p>
        <div class="scroll"><table><thead><tr><th class="n">#</th><th>Dealer</th><th class="n">Score</th><th class="n">vs average</th><th>Band</th><th>Why</th></tr></thead><tbody>
          ${hits.map(h=>`<tr>
            <td class="n">${h.rank}</td>
            <td>${h.annex?`<a href="${esc(annexRoot+h.annex)}">${esc(h.name)}</a>`:esc(h.name)}</td>
            <td class="n">${h.score_pct}%</td>
            <td class="n">${esc(h.vs_avg||'')}</td>
            <td>${pill(h.band)}</td>
            <td>${esc(h.why||'')}</td></tr>`).join('')}
        </tbody></table></div></div>
      ${os.incomplete_none?(customer?'<p class="cap">Every dealer in this market has a completed assessment.</p>':'<p class="cap">Incomplete / not-completed lane: none in this market.</p>'):
        `<div class="card"><h3>Incomplete</h3>
        <p class="cap">${customer?'These dealers are still incomplete.':'Not a low score. Do not put these on the visit list as a fail.'}</p>
        <table><thead><tr><th>Dealer</th><th class="n">Score</th><th>Band</th><th>Reason</th></tr></thead><tbody>
          ${(os.incomplete||[]).map(r=>`<tr><td>${esc(r.name)}</td><td class="n">${esc(r.score)}</td><td>${pill(r.band)}</td><td>${esc(r.reason)}</td></tr>`).join('')}
        </tbody></table></div>`}
      <div class="card"><h3>Suggested next steps — edit in the planning meeting</h3>
        <table><thead><tr><th class="n">#</th><th>Action</th><th>Owner</th><th>Date</th><th>Proof</th></tr></thead><tbody>
          ${steps.map(s=>`<tr><td class="n">${s.n}</td><td>${esc(s.action)}</td><td></td><td></td><td></td></tr>`).join('')}
        </tbody></table></div>
      <div class="card"><h3>Pull scorecard — fill monthly</h3>
        <p class="cap">${customer?'Fill after each monthly cycle.':'Blank on purpose. Measure the visit process, not a fake monthly dealer-standard score.'}</p>
        <table><thead><tr><th>Metric</th><th class="n">This month</th><th>Definition</th></tr></thead><tbody>
          ${pull.map(p=>`<tr><td>${esc(p.metric)}</td><td class="n fill">&nbsp;</td><td>${esc(p.definition)}</td></tr>`).join('')}
        </tbody></table></div>` : '';
    $('p-ids').innerHTML = `
      <h2>${customer?'IDS':'<span class="no">10</span> Dealer standard'}</h2>
      <p class="lead">${esc(leadLab)} is the weakest scored section versus the network (${leadPp==null?'—':leadPp+' pp'}). ${ids.dealer_count} dealers. ${customer?'Priority dealers for the next visits.':'This room is visit triage — GPS and PMS stay on their own tabs.'}</p>
      <div class="grid2">
        <div class="kpi"><div class="l">${esc(leadLab)}</div>
          <div class="v">${leadPp==null?'—':leadPp+' pp'}</div>
          <div class="n">${esc(leadCap)}</div></div>
        <div class="kpi ${eHeld?'ns':''}"><div class="l">Section E · vehicle sales</div>
          <div class="v">${esc(e.scoreboard||'n/s')}</div>
          <div class="n">${esc(e.prose||'')}</div></div>
      </div>
      ${osBlock}
      <div class="card"><h3>Scored sections versus network</h3>
        <p class="cap">${eHeld?(customer?'Section E is held until it is scored.':'Section E is held out — a flat zero is not a fail.'):'Grey network bar is the anonymous full-network average.'}</p>
        <div class="chart-wrap"><canvas id="cIds" role="img" aria-label="Dealer standard versus network">Dealer standard versus network</canvas></div></div>
      <div class="card scroll"><div class="heat">
        <div class="row"><div class="h">Dealer</div><div class="h">A</div><div class="h">B</div><div class="h">C</div><div class="h">D</div><div class="h">E</div><div class="h">Total</div></div>
        ${mat.map(r=>`<div class="row">
          <div class="c" style="text-align:left;background:#fff;color:#222">${esc(r.name||'')}</div>
          ${['A','B','C','D','E'].map(s=>cell(r[s], s==='E' && eHeld)).join('')}
          <div class="c">${pct(r.total_pct,0)}</div>
        </div>`).join('')}
      </div></div>`;
    const scored = sum.filter(s => !(s.section==='E' && eHeld));
    if($('cIds') && scored.length){
      new Chart($('cIds'), {
        type:'bar',
        data:{ labels: scored.map(s=>'Section '+s.section),
          datasets:[
            { label:'This country', data: scored.map(s=>s.country_avg_pct), backgroundColor:NAVY, barThickness:18 },
            { label:'Network', data: scored.map(s=>s.network_avg_pct), backgroundColor:MUTED, barThickness:18 }
          ]},
        options:{ indexAxis:'y', maintainAspectRatio:false, plugins:{legend:{position:'bottom'}},
          scales:{ x: Object.assign(yPct(100), {grid:{color:'#eee'}}), y:{ grid:{display:false} } } }
      });
    }
  }

  if(roomK){
    const digestHost = $('pOpenDigest');
    if(digestHost){
      const verdictOk = plan.bp_match==='MATCH' && !cap.over_ceiling;
      const verdictText = plan.bp_match!=='MATCH'
        ? 'Business plan does not match the locked workbook — check Plan tracking below.'
        : cap.over_ceiling
          ? 'Business plan confirmed against the locked workbook. Extended target sits above the max-spend ceiling — that is this quarter’s story.'
          : 'Business plan confirmed against the locked workbook, on track for FY27.';
      const os = (ids.os)||{};
      const hits = os.hit_list || [];
      const leadLab = ids.lead_label || ('Section '+(ids.lead_section||'D'));
      const leadPp = ids.lead_vs_network_pp;
      const gpsRowsK = (gps.rows||[]).filter(r=> r.publish!==false && !r.partial_year && r.fy!==2023);
      const gpsLast = gpsRowsK.length ? gpsRowsK[gpsRowsK.length-1] : null;
      const showPctK = !!(L.flags.SHOW_GPS_PCT) && (grainCtl.fy||{}).available!==false;
      const gpsHead = gpsLast
        ? (showPctK && gpsLast.gps_pct!=null
            ? pct(gpsLast.gps_pct)
            : (gpsLast.actual_eur==null ? '—' : eurC(gpsLast.actual_eur)))
        : '—';
      const pmsPp = pms.vs_lcv_peer_pp;
      const pmsSub = 'PMS '+pct(pms.capture_pct_total)+' total capture · '+(
        pmsPp==null ? '— vs LCV-peer' : ((pmsPp>0?'+':'')+pmsPp+' pp vs LCV-peer')
      );
      const spaN = spa.n==null ? '—' : spa.n;
      const holdN = (strat.counts||{}).n_hold;
      const spaRows = spa.rows || [];
      const gapRow = spaRows.slice().sort((a,b)=>Math.abs(b.delta_pct||0)-Math.abs(a.delta_pct||0))[0] || null;
      const gapLine = gapRow
        ? (esc((gapRow.description||gapRow.pn||'Largest gap').toString().slice(0,42))+' · '+(gapRow.delta_pct==null?'—':(gapRow.delta_pct>0?'+':'')+gapRow.delta_pct+'% vs projected retail'))
        : 'No named-site gap on file';
      const sa = (L.sales_analysis||{}).verdict || {};
      const chips = sa.chips || [];
      const comChip = chips.find(c=>c.label==='Commercial H1')
        || chips.find(c=>c.label==='Billing H1')
        || chips[0]
        || null;
      const AIMK = (L.sales_analysis||{}).aim || {};
      const nowW = ((AIMK.windows||{}).amj_2026)||{};
      const priW = ((AIMK.windows||{}).amj_2025)||{};
      const ng = ((nowW.ex_warr)||nowW).groups || {};
      const pg = ((priW.ex_warr)||priW).groups || {};
      let famMover = null, famAbs = 0;
      Object.keys(Object.assign({}, ng, pg)).forEach(id=>{
        if(id==='Unclassified') return;
        const dlt = (ng[id]||0)-(pg[id]||0);
        if(Math.abs(dlt)>famAbs){ famAbs=Math.abs(dlt); famMover={id:id, d:dlt}; }
      });
      const famLabK = famMover
        ? (((AIMK.groups||[]).find(g=>g.id===famMover.id)||{}).label || famMover.id)
        : null;
      const famLine = famMover
        ? (famLabK+' '+(famMover.d>0?'+':'')+eurC(famMover.d)+' Apr–Jun')
        : 'Family movers sit on Sales analysis';
      const sc = strat.counts || {};
      const dcard = (opts) => `<div class="dcard" ${tipBits(opts.tip||{})}>
          <div class="dhead"><span class="l">${esc(opts.title)}</span><span class="src">${esc(opts.src)}</span></div>
          <div class="sub">${esc(opts.sub||'')}</div>
          <div class="v">${opts.value}</div>
          <div class="n">${opts.note}</div>
          ${opts.canvas?`<div class="chart-wrap mini"><canvas id="${opts.canvas}" role="img" aria-label="${esc(opts.title)}">${esc(opts.title)}</canvas></div>`:''}
          ${opts.go
            ? `<a class="dlink" href="#${opts.go}" data-go="${opts.go}">${esc(opts.link)}</a>`
            : `<span class="dlink">${esc(opts.link)}</span>`}
        </div>`;
      const cards = [];
      if(idsOn){
        cards.push(dcard({
          title:'IDS', src:'from IDS tab', sub:'Dealer standard',
          value: os.country_avg_pct==null?'—':os.country_avg_pct+'%',
          note: `${hits.length} on the visit hit list · ${esc(leadLab)} weakest${leadPp==null?'':' ('+leadPp+' pp vs network)'}`,
          canvas:'cIdsMini', go:'p-ids', link:'Open IDS →',
          tip:{formula:'sections.ids.os.country_avg_pct. Hit list = ids.os.hit_list. Weakest = ids.lead_label vs ids.lead_vs_network_pp. Mini bars = ids.summary.', snapshot:L.meta.as_of||'', not_included:'IDS-room block-scoped os/hits/leadLab/leadPp are not reused.'}
        }));
      }
      cards.push(dcard({
        title:'GPS trend', src:'from GPS + PMS tab', sub:'Fiscal GPS, same V19 spine',
        value: gpsHead,
        note: esc(pmsSub),
        canvas:'cGpsMini', go:'p-gps', link:'Open GPS + PMS →',
        tip:{formula: showPctK ? 'Latest complete-FY gps_fy_spine.rows.gps_pct (publish not false, not partial_year, fy not 2023). Same filter as the GPS room.' : 'SHOW_GPS_PCT is false — latest complete-FY gps_fy_spine.rows.actual_eur, not a percentage.', snapshot:L.meta.as_of||'', not_included:'FY2023 and partial years. Calendar-year GPS% is not invented. PMS primary is capture_pct_total.'}
      }));
      cards.push(dcard({
        title:'Aftermarket exposure', src:'from Aftermarket tab', sub:'Named-site matches on this book',
        value: spaN+' SPA candidates',
        note: (holdN==null?'—':holdN)+' Hold families · '+gapLine,
        go:'p-spa', link:'Open Aftermarket situation →',
        tip:{formula:'sections.spa_candidates.n. Hold = sections.lost_sales_strategy.counts.n_hold. Largest gap = spa_candidates.rows delta_pct.', snapshot:L.meta.as_of||'', not_included:'Not a time series. Coverage chips are not added together.'}
      }));
      if(salesOn && comChip){
        cards.push(dcard({
          title:'Sales analysis', src:'from Sales analysis tab', sub: comChip.label||'This window',
          value: esc(comChip.value||'—'),
          note: esc(comChip.sub||'')+' · '+esc(famLine),
          go:'p-sales', link:'Open Sales analysis →',
          tip:{formula:'sales_analysis.verdict chip labelled Commercial H1 (else Billing H1). Family mover is Apr–Jun named family with the largest euro change. Not paintSalesBook().', snapshot:L.meta.as_of||'', not_included:'Credit notes are not sales. GPS euros are not this card.'}
        }));
      }
      cards.push(dcard({
        title:'Family strategy', src:'from Family strategy (currently internal-only)', sub:'BVP / SPA / Hold on this book',
        value: (sc.n_bvp_not_enough==null?'—':sc.n_bvp_not_enough)+' BVP not enough',
        note: (sc.n_pn_spa||0)+' SPA · '+(sc.n_hold||0)+' Hold · '+(sc.n_families_on_screen||0)+' families on screen',
        canvas:'cFamMini',
        go: customer ? '' : 'p-fam',
        link:'Promote to a customer tab? →',
        tip:{formula:'sections.lost_sales_strategy.counts n_bvp_not_enough, n_pn_spa, n_hold, n_families_on_screen.', snapshot:L.meta.as_of||'', not_included:'The full family-by-family action table is not opened on a customer tab from this card.'}
      }));
      digestHost.innerHTML =
        `<div class="callout ${verdictOk?'ok':'amber'}">${esc(verdictText)}</div>` +
        `<div class="digest-grid">${cards.join('')}</div>`;
      const eHeldK = (ids.section_e||{}).fill==='not_scored';
      const scoredK = ((ids.summary)||[]).filter(s => !(s.section==='E' && eHeldK));
      if(idsOn && $('cIdsMini') && scoredK.length){
        new Chart($('cIdsMini'), {
          type:'bar',
          data:{ labels: scoredK.map(s=>'Section '+s.section),
            datasets:[
              { label:'This country', data: scoredK.map(s=>s.country_avg_pct), backgroundColor:NAVY, barThickness:8 },
              { label:'Network', data: scoredK.map(s=>s.network_avg_pct), backgroundColor:MUTED, barThickness:8 }
            ]},
          options:{ indexAxis:'y', maintainAspectRatio:false, plugins:{legend:{display:false}},
            scales:{ x:{ display:false, min:0, max:100 }, y:{ display:false } } }
        });
      }
      if($('cGpsMini') && gpsRowsK.length){
        new Chart($('cGpsMini'), {
          type:'line',
          data:{ labels: gpsRowsK.map(r=>'FY'+r.fy),
            datasets:[{ data: gpsRowsK.map(r=> showPctK ? (r.gps_pct==null?null:r.gps_pct) : r.actual_eur),
              borderColor:NAVY, backgroundColor:NAVY, tension:0, pointRadius:2, spanGaps:false }]},
          options:{ maintainAspectRatio:false, plugins:{legend:{display:false}},
            scales:{ x:{ display:false }, y:{ display:false } } }
        });
      }
      if($('cFamMini')){
        new Chart($('cFamMini'), {
          type:'bar',
          data:{ labels:['SPA','Hold'],
            datasets:[{ data:[sc.n_pn_spa||0, sc.n_hold||0], backgroundColor:[TERRA, MUTED], barThickness:10 }]},
          options:{ indexAxis:'y', maintainAspectRatio:false, plugins:{legend:{display:false}},
            scales:{ x:{ display:false, min:0 }, y:{ display:false } } }
        });
      }
    }
  }

  const es = L.empty_states || {};
  const rec = L.reconciliation || {};
  const ask = (es.J_sales_to_dealer||{}).ask_card || {};
  const lights = (L.integrity_strip||{}).lights || [];
  const CHECK_LABEL = {
    'sales_fact FY vs distributor_dimension fy2026_net_sales_eur': 'Fiscal sales vs distributor dimension',
    'whole-book BVP share vs wallet_waterfall bvp_share_of_captured_pct': 'Whole-book Best Value share vs wallet',
    'V3.1 tab actual vs gps_pure_sales pure_sales_eur, FY latest': 'Locked workbook vs GPS spine, latest FY',
    'BP FY27 json vs V3.1 Dashboard col C': 'Business plan vs locked workbook'
  };
  $('p-int').innerHTML = `
    <h2><span class="no">11</span> The ask, and integrity</h2>
    <div class="ask"><h3>${esc(ask.headline||'Sales-to-dealer is the #1 ask')}</h3>
      <p>${esc(ask.why||'')}</p>
      <p><strong>${esc(ask.ask||'')}</strong></p>
      ${ask.umi_note?`<p>${esc(ask.umi_note)}</p>`:''}
      ${ask.do_not_ask_iuk_for_eur?'<p>Do not ask this distributor for euros — UK value comes from the CV sister.</p>':''}</div>
    <div class="callout">Open issues from mail and minutes sit on the <strong>Open issues</strong> tab — ${((es.F_emails||{}).rows||[]).length} from mail, ${((es.G_minutes||{}).rows||[]).length} from minutes. Not another distributor.</div>
    <h3 style="font-family:Georgia,serif;color:#1a2b4a;margin:8px 0 10px">Integrity lights</h3>
    <div class="lights">${lights.map(x=>`<div class="light ${esc(x.state||'off')}"><div class="l">${esc(x.label)}</div><div class="v">${esc(x.state==='ok'?'On':x.state==='warn'?'Watch':x.state==='bad'?'Gap':'Empty')}</div><div class="n">${esc(x.note||'')}</div></div>`).join('')}</div>
    <div class="card"><h3>Checks that must not silently drift</h3>
      <table><thead><tr><th>Check</th><th class="n">A</th><th class="n">B</th><th>Verdict</th></tr></thead><tbody>
        ${(rec.checks||[]).map(c=>`<tr><td>${esc(CHECK_LABEL[c.check]||c.check)}</td><td class="n">${c.a_eur!=null?eur(c.a_eur):pct(c.a_pct)}</td>
          <td class="n">${c.b_eur!=null?eur(c.b_eur):pct(c.b_pct)}</td>
          <td>${c.verdict==='MATCH'?'<span class="tag ok">MATCH</span>':'<span class="tag warn">'+esc(c.verdict)+'</span>'}</td></tr>`).join('')}
      </tbody></table>
      <p class="lead" style="margin-top:10px">${esc((rec.three_that_must_not_match||{}).why||'')}</p>
      <p class="cap">${esc((L.integrity_strip||{}).integrity_note||'')}</p>
    </div>`;

  let salesPainted = false;
  function paintSalesBook(){
    const D = L.sales_analysis;
    if(!D){
      $('p-sales').innerHTML = '<h2>Sales analysis</h2><p class="empty">No sales-analysis payload for this distributor.</p>';
      return;
    }
    if(salesPainted){
      ['cWin','cAimDelta','cAimQ','cBillMo','cPmsAbove','cPmsBelow','cSalesGps','cPn'].forEach(id=>{
        const c = Chart.getChart(id); if(c) c.resize();
      });
      return;
    }
    salesPainted = true;
    const who = D.meta.customer || L.meta.display_name || '';
    const ink='#52514e', grid='#e1e0d9';
    const se = (s) => esc(s==null?'':s);
    const eurS = (v) => { v=Math.round(v||0); const a=Math.abs(v).toLocaleString('en-GB'); return (v<0?'\u2212':'')+'\u20ac'+a; };
    const V = D.verdict || {chips:[], unit_chips:[], callouts:[]};
    const kpiCard = (c) => `<div class="kpi"${c.tip?' data-formula="'+se(c.tip)+'"':''}><div class="l">${se(c.label)}</div><div class="v ${se(c.cls||'')}">${se(c.value)}</div><div class="n">${se(c.sub||'')}</div></div>`;
    $('p-sales').innerHTML = `
      <h2>Sales analysis</h2>
      <p class="lead">${se(V.cover_line||'Billed sales versus last year. Credit notes are not sales.')}</p>
      <nav class="sales-sub">
        <a href="#sv" data-sec="sv" class="on">01 Verdict</a>
        <a href="#sclocks" data-sec="sclocks">02 Families this window</a>
        <a href="#smix" data-sec="smix">03 Families by quarter</a>
        <a href="#spms" data-sec="spms">04 Above or below</a>
        <a href="#sgps" data-sec="sgps">05 GPS</a>
        <a href="#spn" data-sec="spn">06 Part numbers</a>
        <a href="#sgaps" data-sec="sgaps">07 Same book</a>
      </nav>
      <section id="sv">
        <h3>01 Verdict</h3>
        <div class="stat-grid" id="sHero"></div>
        <div class="stat-grid" id="sHeroUnits"></div>
        <div id="sCallouts"></div>
      </section>
      <section id="sclocks">
        <h3>02 Which families moved in this window</h3>
        <p class="cap">Pale bar = last year. Terracotta = this year. Families are named from <b>this window</b> (€4k in either year, or 3% of the window). Other is unclassified plus families below that cut — not leftover names from Apr–Jun. Hide warranty strips warranty part numbers out of the family bars.</p>
        <div class="btns" id="winbtns"></div>
        <div class="btns" id="winwarr"></div>
        <div class="stat-grid" id="winstats"></div>
        <div class="card"><div class="chart-wrap tall"><canvas id="cWin" role="img" aria-label="Part families this window versus last year"></canvas></div>
          <p class="legend"><i style="background:#c5c0b5"></i>Last year &nbsp; <i style="background:#c0552d"></i>This year</p>
          <p class="cap" id="aimWinNote"></p></div>
        <div class="grid2">
          <div class="card"><h3>${D.pbi && D.pbi.available ? 'Official months' : 'Billing months'}</h3>
            <div class="chart-wrap"><canvas id="cBillMo" role="img" aria-label="Monthly sales versus prior year"></canvas></div>
            <p class="cap">${D.pbi && D.pbi.available ? 'Official sales versus the same months last year.' : 'This distributor has no official sales cut on file. Bars are billed invoices versus the same months last year. Credit notes are not sales.'}</p>
            <div class="tblscroll"><table id="reconTable"><thead></thead><tbody></tbody></table></div>
          </div>
          <div class="card"><h3>Euro change by family</h3>
            <div class="chart-wrap"><canvas id="cAimDelta" role="img" aria-label="Family euro change this window"></canvas></div>
            <p class="cap">This year minus last year, same window. Credit notes are not sales. Other is unclassified plus families below the €4k / 3% cut in this window.</p>
          </div>
        </div>
      </section>
      <section id="smix">
        <h3>03 Part families by quarter</h3>
        <p class="cap" id="aimNote"></p>
        <div class="btns" id="aimwarr"></div>
        <div class="card"><div class="chart-wrap tall"><canvas id="cAimQ" role="img" aria-label="Part families euro by quarter"></canvas></div>
          <p class="legend muted" id="aimLegend"></p></div>
        <div class="callout amber" id="aimCallout"></div>
        <div class="tblscroll"><table id="aimTable"><thead></thead><tbody></tbody></table></div>
      </section>
      <section id="spms">
        <h3>04 Service-part capture — above or below the network</h3>
        <p class="cap">Each family is its own comparison: <b>this distributor total capture</b> versus <b>the rest of the network on that same family</b>. Navy = ${se(who)}. Grey = network. Complete calendar 2025. Primary capture is total, not genuine-only. Same source as the GPS + PMS tab.</p>
        <div class="grid2">
          <div class="card"><h3>Above the network</h3>
            <div class="chart-wrap"><canvas id="cPmsAbove" role="img" aria-label="Families above the network"></canvas></div>
            <table id="pmsAbove"><thead></thead><tbody></tbody></table>
          </div>
          <div class="card"><h3>Below the network</h3>
            <div class="chart-wrap"><canvas id="cPmsBelow" role="img" aria-label="Families below the network"></canvas></div>
            <table id="pmsBelow"><thead></thead><tbody></tbody></table>
          </div>
        </div>
        <div class="stat-grid" id="pmsHero"></div>
      </section>
      <section id="sgps">
        <h3>05 GPS — commercial first</h3>
        <p class="cap">${se((D.gps||{}).note||'Same GPS as the GPS + PMS tab.')}</p>
        <div class="stat-grid" id="gpsHero"></div>
        <div class="card"><div class="chart-wrap"><canvas id="cSalesGps" role="img" aria-label="GPS percent commercial versus including warranty"></canvas></div></div>
      </section>
      <section id="spn">
        <h3>06 Part numbers — still selling, lost volume</h3>
        <p class="cap">Default is live lines: sold last year and still selling this year, but less. Terracotta = quantity effect. Navy = price effect. SPA watch is wear still moving, units down.</p>
        <div class="btns" id="pnbtns"></div>
        <div class="btns" id="pnshell"></div>
        <div class="btns" id="pnwarr"></div>
        <div class="btns" id="pnfocus"></div>
        <div class="card"><div class="chart-wrap tall"><canvas id="cPn" role="img" aria-label="Largest euro declines quantity versus price"></canvas></div>
          <p class="cap" id="pnnote"></p></div>
        <div class="tblscroll"><table id="pntable"><thead></thead><tbody></tbody></table></div>
      </section>
      <section id="sgaps">
        <h3>07 Same book</h3>
        <div id="hygieneNotes"></div>
      </section>`;

    $('sHero').innerHTML = (V.chips||[]).map(kpiCard).join('');
    $('sHeroUnits').innerHTML = (V.unit_chips||[]).map(kpiCard).join('');
    $('sCallouts').innerHTML = (V.callouts||[]).map(c=>{
      const k = c.tone==='warn'?'amber':(c.tone==='ok'?'ok':'');
      return `<div class="callout ${k}">${c.html||''}</div>`;
    }).join('');
    function showSalesSec(which){
      const first = which==='sv' || !which;
      const vis = first ? {sv:1,sclocks:1} : {[which]:1};
      ['sv','sclocks','smix','spms','sgps','spn','sgaps'].forEach(id=>{
        const el=$(id); if(el) el.style.display = vis[id] ? '' : 'none';
      });
      document.querySelectorAll('.sales-sub a').forEach(a=>a.classList.toggle('on', a.getAttribute('data-sec')===(first?'sv':which)));
      ['cWin','cAimDelta','cAimQ','cBillMo','cPmsAbove','cPmsBelow','cSalesGps','cPn'].forEach(id=>{
        const c = Chart.getChart(id); if(c) c.resize();
      });
    }
    document.querySelectorAll('.sales-sub a').forEach(a=>{
      a.onclick = function(ev){ ev.preventDefault(); showSalesSec(a.getAttribute('data-sec')); };
    });
    showSalesSec('sv');

    const AIM=D.aim||{groups:[],windows:{},quarterly:[]};
    const AIM_IDS=AIM.groups.map(g=>g.id);
    const SHOW_SHELL=!!AIM.show_shell;
    const FAM_LABELS=AIM.labels||{};
    const FAM_EUR=AIM.min_eur||4000;
    const FAM_SHARE=AIM.min_share||0.03;
    let win=0, hideAimWarr=true, cWin, cAimDelta, cAimQ, cPn, pnMode='amj';
    const WIN_KEYS=[
      ['amj_2026','Apr–Jun 2026','amj_2025'],
      ['cy_h1_2026','Calendar H1 2026','cy_h1_2025'],
      ['l12_now','Last 12 months','l12_prior'],
      ['fy2026','FY2026 (Apr–Mar)','fy2025'],
      ['cy2025','Calendar 2025','cy2024']
    ];
    function aimSrc(w){
      if(!w) return {shell:0,groups:{},other:0,warranty:0,classified_pct:null};
      return (hideAimWarr && w.ex_warr) ? w.ex_warr : w;
    }
    function famLab(id){
      if(!id) return 'Family';
      const g=(AIM.groups||[]).filter(x=>x.id===id)[0];
      return (g&&g.label)||FAM_LABELS[id]||id;
    }
    function namedAxis(n,p){
      const ng=n.groups||{}, pg=p.groups||{};
      const totN=Object.keys(ng).reduce((s,k)=>s+(+ng[k]||0),0)||1;
      const totP=Object.keys(pg).reduce((s,k)=>s+(+pg[k]||0),0)||1;
      const ids={};
      Object.keys(ng).concat(Object.keys(pg)).forEach(id=>{ids[id]=1;});
      const keep=[], leftover=[];
      let otherN=0, otherP=0;
      Object.keys(ids).forEach(id=>{
        const a=+ng[id]||0, b=+pg[id]||0;
        const named=id!=='Unclassified' && (Math.max(a,b)>=FAM_EUR || Math.max(a/totN,b/totP)>=FAM_SHARE);
        if(!named){
          otherN+=a; otherP+=b;
          if(a>=1) leftover.push({id:id, eur:a});
          return;
        }
        keep.push({id:id, a:a, b:b});
      });
      keep.sort((x,y)=>y.a-x.a);
      leftover.sort((x,y)=>y.eur-x.eur);
      return {keep:keep, otherN:otherN, otherP:otherP, leftover:leftover, totN:totN, classifiedPct:n.classified_pct};
    }
    function paintWin(){
      const k=WIN_KEYS[win], totNow=D.windows[k[0]], totPri=D.windows[k[2]];
      const now=AIM.windows[k[0]]||{}, pri=AIM.windows[k[2]]||{};
      const n=aimSrc(now), p=aimSrc(pri);
      const dp=(a,b)=> b?((a-b)/b*100):null;
      const ax=namedAxis(n,p);
      const g0=ax.keep[0]||{}, g1=ax.keep[1]||{};
      const aN=g0.a||0, aP=g0.b||0, bN=g1.a||0, bP=g1.b||0;
      const totDp=dp(totNow.total, totPri.total);
      $('winstats').innerHTML = [
        kpiCard({label:'This window', value:eurS(totNow.total), sub:'vs '+eurS(totPri.total)+' prior', cls: totDp<0?'bad':'good', tip:'Billing, credit notes out.'}),
        kpiCard({label:'Warranty', value:eurS((now.warranty||0)-(pri.warranty||0)), sub:eurS(now.warranty||0)+' now', cls:((now.warranty||0)<(pri.warranty||0)?'bad':'good'), tip:'Claim-grain + text. Change versus last year; sub is this window’s warranty euro.'}),
        kpiCard({label:famLab(g0.id), value:eurS(aN-aP), sub:eurS(aN)+' now'+(hideAimWarr?' · ex-warranty':''), cls:aN<aP?'bad':'good', tip: hideAimWarr?'Largest named family in this window, warranty part numbers stripped.':'Largest named family in this window.'}),
        kpiCard({label:famLab(g1.id), value:eurS(bN-bP), sub:eurS(bN)+' now'+(hideAimWarr?' · ex-warranty':''), cls:bN<bP?'bad':'good', tip:'Second-largest named family in this window.'})
      ].join('');
      const showOther=Math.abs(ax.otherN)>=50 || Math.abs(ax.otherP)>=50;
      const labs=[], priorVals=[], nowVals=[];
      if(SHOW_SHELL && (Math.abs(n.shell||0)>=50 || Math.abs(p.shell||0)>=50)){
        labs.push('Shell'); priorVals.push(p.shell||0); nowVals.push(n.shell||0);
      }
      ax.keep.forEach(g=>{
        if(Math.abs(g.a)<50 && Math.abs(g.b)<50) return;
        labs.push(famLab(g.id)); priorVals.push(g.b); nowVals.push(g.a);
      });
      if(showOther){ labs.push('Other'); priorVals.push(ax.otherP); nowVals.push(ax.otherN); }
      const ds=[{label:'Last year',data:priorVals,backgroundColor:'#c5c0b5',barThickness:18},
                {label:'This year',data:nowVals,backgroundColor:'#c0552d',barThickness:18}];
      if(cWin){cWin.data.labels=labs; cWin.data.datasets[0].data=ds[0].data; cWin.data.datasets[1].data=ds[1].data; cWin.update();}
      else {
        cWin=new Chart($('cWin'),{type:'bar',data:{labels:labs,datasets:ds},
          options:{responsive:true,maintainAspectRatio:false,plugins:{legend:{labels:{color:ink}}},
            scales:{y:{ticks:{color:ink,callback:v=>Math.round(v/1000)+'k'},grid:{color:grid},beginAtZero:true},
                    x:{ticks:{color:ink,maxRotation:50,minRotation:0},grid:{display:false}}}}});
      }
      const deltas=nowVals.map((v,i)=>v-(priorVals[i]||0));
      const dColors=deltas.map(v=>v<0?'#c0552d':'#1d9e75');
      if(cAimDelta){cAimDelta.data.labels=labs; cAimDelta.data.datasets[0].data=deltas; cAimDelta.data.datasets[0].backgroundColor=dColors; cAimDelta.update();}
      else {
        cAimDelta=new Chart($('cAimDelta'),{type:'bar',
          data:{labels:labs,datasets:[{data:deltas,backgroundColor:dColors,barThickness:16}]},
          options:{indexAxis:'y',responsive:true,maintainAspectRatio:false,plugins:{legend:{display:false}},
            scales:{x:{ticks:{color:ink,callback:v=>Math.round(v/1000)+'k'},grid:{color:grid}},
                    y:{ticks:{color:ink},grid:{display:false}}}}});
      }
      const noteEl=$('aimWinNote');
      if(noteEl){
        const cov=(n.classified_pct==null)?'—':n.classified_pct;
        const bits=ax.leftover.slice(0,8).map(x=>famLab(x.id)+' '+eurS(x.eur)).join(', ');
        noteEl.textContent='Catalogue family is PR00 group. '+cov+'% of euros in this view have a family name. Named if at least €4k in either year of this window, or 3% of the window. Other is unclassified plus families below that cut ('+eurS(ax.otherN)+', '+Math.round(100*ax.otherN/ax.totN)+'%): '+(bits||'none')+'.';
      }
    }
    WIN_KEYS.forEach((k,i)=>{
      const b=document.createElement('button'); b.textContent=k[1]; if(i===0)b.className='on';
      b.onclick=function(){win=i; [].forEach.call($('winbtns').children,(x,j)=>{x.className=j===i?'on':'';}); paintWin();};
      $('winbtns').appendChild(b);
    });
    const PAL=['#c0552d','#15233c','#2a78d6','#c9a227','#1d9e75','#6b4c9a','#3d6b8a','#8b5a2b','#b85c38','#4a7c59','#c47c2b','#5c6b7a'];
    const q=AIM.quarterly||[];
    const lineIds=(AIM.line_ids&&AIM.line_ids.length)?AIM.line_ids:AIM_IDS.slice(0,5);
    function qAim(r){return aimSrc(r);}
    function paintAimQ(){
      $('aimNote').textContent=hideAimWarr
        ? ((AIM.note||'')+' Warranty hidden on the lines below — commercial euro only.')
        : (AIM.note||'');
      const labels=q.map(r=>r.label);
      const sets=lineIds.map((id,i)=>{
        const lab=(AIM.groups.filter(g=>g.id===id)[0]||{}).label||id;
        return {label:lab,data:q.map(r=>(qAim(r).groups&&qAim(r).groups[id])||0),
          borderColor:PAL[i%PAL.length],backgroundColor:'transparent',tension:.2,pointRadius:4,borderWidth:2};
      });
      if(SHOW_SHELL){
        sets.push({label:'Shell lubricants',data:q.map(r=>qAim(r).shell||0),
          borderColor:'#888780',backgroundColor:'transparent',borderDash:[6,4],tension:.2,pointRadius:4,borderWidth:2});
      }
      if(cAimQ){ cAimQ.destroy(); cAimQ=null; }
      cAimQ=new Chart($('cAimQ'),{type:'line', data:{labels,datasets:sets},
        options:{responsive:true,maintainAspectRatio:false,plugins:{legend:{labels:{color:ink}}},
          scales:{y:{beginAtZero:true,ticks:{color:ink,callback:v=>Math.round(v/1000)+'k'},grid:{color:grid}},
                  x:{ticks:{color:ink},grid:{display:false}}}}});
      $('aimLegend').innerHTML=hideAimWarr
        ? (SHOW_SHELL?'Lines are commercial billed euro by family. Dashed grey is Shell. Warranty is off.':'Lines are commercial billed euro by family. Warranty is off.')
        : (SHOW_SHELL?'Lines are billed euro by family. Dashed grey is Shell lubricants.':'Lines are billed euro by family.');
      function qg(qq,gid){
        const row=q.filter(r=>r.q===qq)[0]||{};
        return (qAim(row).groups&&qAim(row).groups[gid])||0;
      }
      const id0=lineIds[0], id1=lineIds[1];
      const lab0=(AIM.groups.filter(g=>g.id===id0)[0]||{}).label||id0||'';
      const lab1=(AIM.groups.filter(g=>g.id===id1)[0]||{}).label||id1||'';
      if(id0 && id1){
        $('aimCallout').innerHTML=se(lab0)+' ran '+eurS(qg('2025Q2',id0))+' in Q2 2025, '+eurS(qg('2025Q3',id0))+' in Q3, then '+eurS(qg('2025Q4',id0))+' in Q4'+(hideAimWarr?' with warranty hidden.':'.')+' '+se(lab1)+' ran '+eurS(qg('2025Q1',id1))+' / '+eurS(qg('2025Q2',id1))+' / '+eurS(qg('2025Q3',id1))+' across the same three quarters.';
      } else {
        $('aimCallout').innerHTML='';
      }
      const thead=document.querySelector('#aimTable thead');
      const tbody=document.querySelector('#aimTable tbody');
      thead.innerHTML='<tr><th>Family</th>'+q.map(r=>'<th class="n">'+se(r.label)+'</th>').join('')+'</tr>';
      let rows=AIM.groups.slice();
      const anyOther=q.some(r=>(qAim(r).other||0)>=50);
      if(anyOther) rows=rows.concat([{id:'_other',label:'Other families'}]);
      if(SHOW_SHELL) rows=rows.concat([{id:'_shell',label:'Shell lubricants'}]);
      tbody.innerHTML=rows.map(g=>{
        return '<tr><td>'+se(g.label)+'</td>'+q.map(r=>{
          const s=qAim(r);
          const v=g.id==='_shell'?s.shell:(g.id==='_other'?s.other:((s.groups&&s.groups[g.id])||0));
          return '<td class="n">'+eurS(v)+'</td>';
        }).join('')+'</tr>';
      }).join('');
    }
    function bindAimWarr(boxId){
      const box=$(boxId); if(!box) return;
      const ba=document.createElement('button'); ba.textContent='Hide warranty';
      const bb=document.createElement('button'); bb.textContent='Show warranty';
      function apply(hide){
        hideAimWarr=hide;
        document.querySelectorAll('[data-aim-warr]').forEach(el=>{
          const hideBtn=el.children[0], showBtn=el.children[1];
          if(hideBtn) hideBtn.className=hide?'on':'';
          if(showBtn) showBtn.className=hide?'':'on';
        });
        paintWin();
        paintAimQ();
      }
      box.setAttribute('data-aim-warr','1');
      ba.onclick=function(){apply(true);};
      bb.onclick=function(){apply(false);};
      box.appendChild(ba); box.appendChild(bb);
      ba.className=hideAimWarr?'on':'';
      bb.className=hideAimWarr?'':'on';
    }
    bindAimWarr('winwarr');
    bindAimWarr('aimwarr');
    paintWin();
    paintAimQ();

    const rec=D.recon||[];
    const billLabels=rec.map(r=>r.month);
    const billNow=rec.map(r=> D.pbi && D.pbi.available ? r.official : r.invoice_eur);
    const billPri=rec.map(r=>r.prior_year);
    new Chart($('cBillMo'),{type:'bar',
      data:{labels:billLabels,datasets:[
        {label:'Prior year',data:billPri,backgroundColor:'#c5c0b5',barThickness:22},
        {label: D.pbi && D.pbi.available ? 'Official this year' : 'Billing this year', data:billNow,backgroundColor:'#c0552d',barThickness:22}
      ]},
      options:{responsive:true,maintainAspectRatio:false,plugins:{legend:{labels:{color:ink}}},
        scales:{y:{beginAtZero:true,ticks:{color:ink,callback:v=>Math.round(v/1000)+'k'},grid:{color:grid}},
                x:{ticks:{color:ink},grid:{display:false}}}}});
    const th=document.querySelector('#reconTable thead');
    const tb=document.querySelector('#reconTable tbody');
    if(D.pbi && D.pbi.available){
      th.innerHTML='<tr><th>Month</th><th class="n">Official</th><th class="n">Invoice lines</th><th class="n">Credit notes</th><th>Note</th></tr>';
      tb.innerHTML=rec.map(r=>{
        const note=!r.in_file?'Not in the billing file yet.':
          (Math.abs(r.credit_note_eur)>1?'Credit note is not sales.':
          (Math.abs(r.gap_invoices_vs_official)<2000?'Same book.':''));
        return '<tr><td>'+se(r.month)+'</td><td class="n">'+eurS(r.official)+'</td><td class="n">'+eurS(r.invoice_eur)+'</td><td class="n">'+(r.credit_note_eur?eurS(r.credit_note_eur):'—')+'</td><td>'+note+'</td></tr>';
      }).join('');
    } else {
      th.innerHTML='<tr><th>Month</th><th class="n">This year billing</th><th class="n">Last year</th><th class="n">Credit notes</th></tr>';
      tb.innerHTML=rec.map(r=>'<tr><td>'+se(r.month)+'</td><td class="n">'+eurS(r.invoice_eur)+'</td><td class="n">'+eurS(r.prior_year)+'</td><td class="n">'+(r.credit_note_eur?eurS(r.credit_note_eur):'—')+'</td></tr>').join('');
    }

    const pms=(D.pms.categories||[]).filter(c=>c.critical && c.cy2025_pct!=null && !c.skip_best_series);
    const above=pms.filter(c=>(c.cy2025_pct||0)>=(c.network_pct||0)).sort((a,b)=>(b.cy2025_pct||0)-(a.cy2025_pct||0));
    const below=pms.filter(c=>(c.cy2025_pct||0)<(c.network_pct||0)).sort((a,b)=>(a.cy2025_pct||0)-(b.cy2025_pct||0));
    function paintPmsSide(canvasId, tableId, rows){
      new Chart($(canvasId),{type:'bar',
        data:{labels:rows.map(c=>c.label),
          datasets:[
            {label:who,data:rows.map(c=>c.cy2025_pct),backgroundColor:'#15233c',barThickness:14},
            {label:'Network',data:rows.map(c=>c.network_pct),backgroundColor:'#c5c0b5',barThickness:14}
          ]},
        options:{indexAxis:'y',responsive:true,maintainAspectRatio:false,plugins:{legend:{labels:{color:ink}}},
          scales:{x:{max:100,ticks:{color:ink,callback:v=>v+'%'},grid:{color:grid}},
                  y:{ticks:{color:ink},grid:{display:false}}}}});
      const th=document.querySelector('#'+tableId+' thead');
      const tb=document.querySelector('#'+tableId+' tbody');
      th.innerHTML='<tr><th>Family</th><th class="n">'+se(who)+'</th><th class="n">Network</th><th class="n">Gap</th></tr>';
      tb.innerHTML=rows.map(c=>{
        const gap=(c.cy2025_pct||0)-(c.network_pct||0);
        return '<tr><td>'+se(c.label)+'</td><td class="n">'+c.cy2025_pct.toFixed(1)+'%</td><td class="n">'+(c.network_pct==null?'—':c.network_pct.toFixed(1)+'%')+'</td><td class="n">'+(gap>=0?'+':'')+gap.toFixed(1)+' pt</td></tr>';
      }).join('');
    }
    if(above.length) paintPmsSide('cPmsAbove','pmsAbove',above);
    if(below.length) paintPmsSide('cPmsBelow','pmsBelow',below);
    const oil=pms.filter(c=>c.id==='oil_filter')[0]||{};
    const pad=pms.filter(c=>c.id==='brake_pad')[0]||{};
    const oilAbove=(oil.cy2025_pct||0)>=(oil.network_pct||0);
    const padBelow=(pad.cy2025_pct||0)<(pad.network_pct||0);
    $('pmsHero').innerHTML=[
      kpiCard({label:'Oil filter', value:(oil.cy2025_pct||0).toFixed(1)+'%', sub:'Network '+(oil.network_pct==null?'—':Number(oil.network_pct).toFixed(1))+'% · '+(oilAbove?'above':'below'), cls:oilAbove?'good':'bad', tip:'Total capture = genuine + BVP units ÷ expected.'}),
      kpiCard({label:'Brake pads', value:(pad.cy2025_pct||0).toFixed(1)+'%', sub:'Network '+(pad.network_pct==null?'—':Number(pad.network_pct).toFixed(1))+'% · '+(padBelow?'below':'above'), cls:padBelow?'bad':'good', tip:'This distributor versus the rest of the network on this family.'}),
      kpiCard({label:'Parc in capture file', value:(D.pms.uio_units||0).toLocaleString('en-GB'), sub:D.pms.uio_note||'', tip:D.pms.uio_note||''})
    ].join('');

    const g=D.gps||{};
    const gIncl=g.gps_pct_incl_warr||{}, gEx=g.gps_pct_ex_warr||{};
    $('gpsHero').innerHTML=[
      kpiCard({label:'GPS commercial FY2024', value:(gEx.FY2024==null?'—':gEx.FY2024+'%'), sub:g.net&&g.net.FY2024!=null?eurS(g.net.FY2024):'—', tip:g.formula_ex}),
      kpiCard({label:'GPS commercial FY2025', value:(gEx.FY2025==null?'—':gEx.FY2025+'%'), sub:g.net&&g.net.FY2025!=null?eurS(g.net.FY2025):'—', tip:g.formula_ex}),
      kpiCard({label:'GPS commercial FY2026', value:(gEx.FY2026==null?'—':gEx.FY2026+'%'), sub:g.net&&g.net.FY2026!=null?eurS(g.net.FY2026):'—', tip:g.formula_ex}),
      kpiCard({label:'GPS incl. warranty FY2026', value:(gIncl.FY2026==null?'—':gIncl.FY2026+'%'), sub:'Same ceiling as GPS + PMS · live €'+Number(g.rate_current_fy27||262.5).toFixed(2), tip:g.formula_incl})
    ].join('');
    const gpsEx=[gEx.FY2024,gEx.FY2025,gEx.FY2026];
    const gpsIn=[gIncl.FY2024,gIncl.FY2025,gIncl.FY2026];
    const gpsVals=[...gpsEx,...gpsIn].filter(v=>v!=null);
    const gpsLo=gpsVals.length?Math.max(0, Math.floor((Math.min.apply(null,gpsVals)-8)/5)*5):0;
    const gpsHi=gpsVals.length?Math.min(100, Math.ceil((Math.max.apply(null,gpsVals)+8)/5)*5):100;
    new Chart($('cSalesGps'),{type:'line',
      data:{labels:['FY2024','FY2025','FY2026'],
        datasets:[
          {label:'Commercial (ex-warranty)',data:gpsEx,spanGaps:false,
            borderColor:'#c0552d',backgroundColor:'rgba(192,85,45,.12)',fill:true,tension:.25,pointRadius:5},
          {label:'Including warranty',data:gpsIn,spanGaps:false,
            borderColor:'#2a78d6',backgroundColor:'transparent',borderDash:[6,4],fill:false,tension:.25,pointRadius:5}
        ]},
      options:{responsive:true,maintainAspectRatio:false,plugins:{legend:{labels:{color:ink}}},
        scales:{y:{min:gpsLo,max:gpsHi,ticks:{color:ink,callback:v=>v+'%'},grid:{color:grid}},
                x:{ticks:{color:ink},grid:{display:false}}}}});

    let hideShell=true, hideWarr=true, pnFocus='live';
    function paintPn(){
      const src=(D.pn[pnMode]||[]).filter(r=>{
        if(hideShell && r.shell) return false;
        if(hideWarr && r.warranty) return false;
        if(pnFocus==='live') return r.still_selling && r.d<0;
        if(pnFocus==='gone') return r.did_not_repeat && r.d<0;
        if(pnFocus==='spa') return r.spa_watch;
        if(pnFocus==='pms') return r.low_pms && r.d<0;
        return r.d<0;
      });
      const rows=src.slice(0,15);
      const labels=rows.map(r=>{
        const d=(r.desc||'').replace(/\s+/g,' ').slice(0,22);
        return (r.pn||'')+'  '+d;
      });
      const cfg={type:'bar',data:{labels,datasets:[
          {label:'Quantity effect',data:rows.map(r=>r.qty_effect),backgroundColor:'#c0552d',barThickness:16},
          {label:'Price effect',data:rows.map(r=>r.price_effect),backgroundColor:'#2a78d6',barThickness:16}
        ]},
        options:{indexAxis:'y',responsive:true,maintainAspectRatio:false,
          plugins:{legend:{labels:{color:ink}}},
          scales:{x:{ticks:{color:ink,callback:v=>Math.round(v/1000)+'k'},grid:{color:grid}},
                  y:{ticks:{color:ink,font:{size:10}},grid:{display:false}}}}};
      if(cPn){cPn.data.labels=cfg.data.labels; cPn.data.datasets[0].data=cfg.data.datasets[0].data; cPn.data.datasets[1].data=cfg.data.datasets[1].data; cPn.update();}
      else {cPn=new Chart($('cPn'),cfg);}
      const bits=[];
      if(SHOW_SHELL) bits.push(hideShell?'Shell lubricants hidden.':'Shell lubricants shown.');
      bits.push(hideWarr?'Warranty hidden.':'Warranty shown.');
      bits.push({live:'Still selling, but less.', gone:'Sold last year and not this year.', spa:'Special Price Agreement watch: wear still moving, units down.', pms:'Service parts whose total capture sits under 30% (or well under the network).'}[pnFocus]||'');
      bits.push(src.length+' part numbers in this cut; table shows the 15 largest euro drops.');
      $('pnnote').textContent=bits.join(' ');
      document.querySelector('#pntable thead').innerHTML='<tr><th>PN</th><th>Part</th><th class="n">Last year</th><th class="n">This year</th><th class="n">Units</th><th class="n">€ change</th><th class="n">Qty effect</th><th class="n">Price effect</th></tr>';
      document.querySelector('#pntable tbody').innerHTML=rows.map(r=>{
        const meta=[];
        if(r.pms_label) meta.push(r.pms_label);
        if(r.pms_capture_pct!=null) meta.push(r.pms_capture_pct.toFixed(1)+'% capture');
        const sub=meta.length?'<span class="submeta">'+se(meta.join(' · '))+'</span>':'';
        const mark=r.spa_watch?'<span class="spa-mark">SPA</span>':'';
        const units=Math.round(r.qty_prior||0)+'\u00a0→\u00a0'+Math.round(r.qty_now||0);
        return '<tr'+(r.spa_watch?' class="spa"':'')+'>'
          +'<td>'+se(r.pn)+mark+'</td><td>'+se(r.desc||'')+sub+'</td>'
          +'<td class="n">'+eurS(r.eur_prior)+'</td><td class="n">'+eurS(r.eur_now)+'</td>'
          +'<td class="n">'+units+'</td><td class="n">'+eurS(r.d)+'</td>'
          +'<td class="n">'+eurS(r.qty_effect)+'</td><td class="n">'+eurS(r.price_effect)+'</td></tr>';
      }).join('');
    }
    [['amj','Apr–Jun'],['cy_h1','Calendar H1'],['l12','Last 12 months']].forEach((k,i)=>{
      const b=document.createElement('button'); b.textContent=k[1]; if(i===0)b.className='on';
      b.onclick=function(){pnMode=k[0]; [].forEach.call($('pnbtns').children,(x,j)=>{x.className=j===i?'on':'';}); paintPn();};
      $('pnbtns').appendChild(b);
    });
    function togglePair(boxId, aLabel, bLabel, setA){
      const box=$(boxId);
      const ba=document.createElement('button'); ba.textContent=aLabel; ba.className='on';
      const bb=document.createElement('button'); bb.textContent=bLabel;
      ba.onclick=function(){setA(true); ba.className='on'; bb.className=''; paintPn();};
      bb.onclick=function(){setA(false); bb.className='on'; ba.className=''; paintPn();};
      box.appendChild(ba); box.appendChild(bb);
    }
    if(SHOW_SHELL){
      togglePair('pnshell','Hide Shell lubricants','Show Shell lubricants', v=>{hideShell=v;});
    } else {
      hideShell=false;
      const sh=$('pnshell'); if(sh) sh.style.display='none';
    }
    togglePair('pnwarr','Hide warranty','Show warranty', v=>{hideWarr=v;});
    [['live','Still selling, lost volume'],['gone','Did not repeat'],['spa','SPA watch'],['pms','Weak capture']].forEach((k,i)=>{
      const b=document.createElement('button'); b.textContent=k[1]; if(i===0)b.className='on';
      b.onclick=function(){pnFocus=k[0]; [].forEach.call($('pnfocus').children,(x,j)=>{x.className=j===i?'on':'';}); paintPn();};
      $('pnfocus').appendChild(b);
    });
    paintPn();

    const hy=D.hygiene||{};
    const notes=[];
    notes.push(`<div class="callout">About <b>${hy.uncoded_share_amj||0}%</b> of April–June invoice euros have no order type coded (${eurS(hy.uncoded_eur_amj)}, ${hy.uncoded_lines_amj||0} lines). Credit notes are not in this mix.</div>`);
    if(hy.credit_eur_h1) notes.push(`<div class="callout">H1 credit notes ${eurS(hy.credit_eur_h1)}. Credit notes are not sales.</div>`);
    if(!hy.jul_in_file) notes.push('<div class="callout amber">July this year is not in the billing file yet, so July cannot be split. Follow-ups stay on Executive overview.</div>');
    $('hygieneNotes').innerHTML=notes.join('');
  }

  if(roomK){
    const ov = $('p-open');
    const planPanel = $('p-plan');
    const issues = $('pOpenIssues');
    while(planPanel.firstChild){
      if(issues) ov.insertBefore(planPanel.firstChild, issues);
      else ov.appendChild(planPanel.firstChild);
    }
  }
  if(master){
    const gpsPanel = $('p-gps');
    const pmsPanel = $('p-pms');
    while(pmsPanel.firstChild) gpsPanel.appendChild(pmsPanel.firstChild);
  }
  if(customer){
    $('foot').textContent = 'Snapshot ' + L.meta.as_of + ' · GPS on V19 parc · PMS complete calendar year · aftermarket = named published offers.';
  } else {
    $('foot').textContent = 'Snapshot ' + L.meta.as_of + ' · GPS fiscal spine on V19 parc and the current D-Max rate · PMS complete calendar year vs network · aftermarket probes are named-site published offers (not added together) plus a local catalogue without part numbers · Best Value is retention · three lost-sales lanes are never added.';
  }
  if(salesOn) paintSalesBook();

  function cell(v, notScored){
    if(notScored) return `<div class="c ns">n/s</div>`;
    const x = Number(v)||0;
    const bg = x>=80? '#d7efe4' : x>=60? '#fff3d6' : '#f8d8d4';
    return `<div class="c" style="background:${bg}">${pct(v,0)}</div>`;
  }
})();
</script>
</body>
</html>
"""


OVERVIEW_DBS = ("ITUK", "GERMANY", "PORTUGAL", "UMI")


def render_overview() -> str:
    """Light network list — does not stamp 18 full packs."""
    sys.path.insert(0, HERE)
    from build_ledger import REGISTRY
    cards = []
    for db in OVERVIEW_DBS:
        reg = REGISTRY[db]
        folder = f"{db}_Operating_Dashboard_2026"
        html_name = f"{db}_Operating_Dashboard.html"
        path = os.path.join(MEETINGS, folder, html_name)
        exists = os.path.exists(path)
        sold = ", ".join(str(x) for x in reg["sold_to"])
        gps = reg["gps_label"]
        cards.append(
            f'<a class="card" href="../{folder}/{html_name}">'
            f"<h2>{reg['display']}</h2>"
            f"<p class='k'>{db} · GPS {gps} · sold-to {sold} · {reg['country']}</p>"
            f"<p>{'Open the operating pack' if exists else 'Ledger exists — HTML not rendered yet'}.</p>"
            f"</a>"
        )
    outdir = os.path.join(MEETINGS, "Operating_Dashboards_Overview_2026")
    os.makedirs(outdir, exist_ok=True)
    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Operating dashboards · four packs</title>
<style>
:root{{--navy:#15233c;--navy2:#1a2b4a;--terra:#c0552d;--paper:#f7f4ee;--line:#d9d3c8;--muted:#6b6256;--ink:#222}}
html,body{{margin:0;background:var(--paper);color:var(--ink);font:15px/1.5 "Segoe UI",Helvetica,Arial,sans-serif}}
.hero{{background:linear-gradient(155deg,#15233c 0%,#203759 55%,#2b4a78 100%);color:#eef1f6;padding:28px}}
.hero h1{{font-family:Georgia,serif;color:#fff;font-weight:400;margin:8px 0}}
.hero .rule{{width:56px;height:3px;background:var(--terra)}}
.wrap{{max-width:960px;margin:0 auto;padding:24px 28px 64px}}
.grid{{display:grid;grid-template-columns:1fr 1fr;gap:14px}}
a.card{{display:block;background:#fff;border:1px solid var(--line);padding:18px;text-decoration:none;color:var(--ink)}}
a.card h2{{font-family:Georgia,serif;color:var(--navy2);font-weight:400;margin:0 0 6px;font-size:20px}}
a.card .k{{font-size:12px;color:var(--muted);margin:0 0 8px}}
a.card:hover{{border-color:var(--terra)}}
.foot{{margin-top:28px;font-size:12px;color:var(--muted)}}
@media(max-width:720px){{.grid{{grid-template-columns:1fr}}}}
</style>
</head>
<body>
<div class="hero"><div class="brand" style="letter-spacing:.16em;text-transform:uppercase;font-size:12px;color:#c9d4e6">ISZE · operating</div>
<h1>Four customer packs</h1><div class="rule"></div>
<p>ITUK, ISD (Germany), I-Motors (Portugal), UMI. Not the full 18. Double-click a card.</p></div>
<div class="wrap"><div class="grid">{''.join(cards)}</div>
<p class="foot">Registry keys: ITUK 2575 · GERMANY 2516+601 (gps ISD) · PORTUGAL 519+92 (gps Imotors) · UMI 1797. UMI is not UTI 1799. Ireland is not ISD.</p></div>
</body></html>"""
    out = os.path.join(outdir, "Operating_Dashboards_Overview.html")
    with open(out, "w", encoding="utf-8") as f:
        f.write(html)
    write_cmd(outdir, "Operating_Dashboards_Overview.html")
    print(f"  -> {out}")
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--db", default="UMI")
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--overview", action="store_true",
                    help="light list of ITUK / GERMANY / PORTUGAL / UMI — not all 18")
    a = ap.parse_args()
    sys.path.insert(0, HERE)
    from build_ledger import REGISTRY
    if a.overview:
        render_overview()
        return
    dbs = sorted(REGISTRY) if a.all else [a.db]
    for db in dbs:
        render(db)


if __name__ == "__main__":
    main()
