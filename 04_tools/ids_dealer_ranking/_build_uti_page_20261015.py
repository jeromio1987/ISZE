# -*- coding: utf-8 -*-
"""Build the UTI national dealer-compare page. One-off runner."""
from datetime import datetime, timezone
from pathlib import Path
from statistics import mean

from build_ids_country_packs_v13 import filter_country_payload, render_country_html
from build_ids_dashboard import render_html
from ids_dashboard_qa import format_qa_report, validate_dashboard_payload
from ids_dealer_geo import attach_geo_to_dealers, format_geo_sanity_report, sanity_check_geo_clustering
from ids_paths import IDS_RESULT_REPORTS_DIR, ISZE_ROOT
from ids_report_extract import build_dashboard_payload

OUT = ISZE_ROOT / "02_dashboards" / "ids" / "IDS_2026_dealer_compare_UTI.html"
CMD = ISZE_ROOT / "02_dashboards" / "ids" / "OPEN_IDS_2026_dealer_compare_UTI.cmd"

payload = build_dashboard_payload(IDS_RESULT_REPORTS_DIR)
uti = [d for d in payload["dealers"] if d.get("country") == "UTI"]
print("UTI dealers", len(uti))
if not uti:
    raise SystemExit("no UTI dealers in payload")
print("sample", uti[0]["name"], "pct", round(uti[0]["total_pct"] * 100, 1), "basis", uti[0].get("score_basis"))
print("sections", {k: (v or {}).get("fill") or (v or {}).get("pct") for k, v in uti[0]["sections"].items()})

# Network benchmark = the other markets. UTI's total is service and parts only.
others = [d for d in payload["dealers"] if d.get("country") != "UTI" and not d.get("excluded_from_average")]
net = payload["network"]
sec_ids = [s["id"] for s in payload["sections"]]
sec_pct = {}
for sid in sec_ids:
    vals = []
    for d in others:
        if d.get("score_basis") == "UKCV-AH" or d.get("country") == "UK CV":
            continue
        block = (d.get("sections") or {}).get(sid) or {}
        if block.get("pct") is not None:
            vals.append(block["pct"])
    sec_pct[sid] = mean(vals) if vals else None
net["sections_pct"] = sec_pct
net["dealer_count"] = sum(1 for d in payload["dealers"] if d.get("country") != "UTI")
tvals = [d["total_pct"] for d in others if d.get("total_pct") is not None and d.get("score_basis") != "C-D"]
net["total_pct"] = mean(tvals) if tvals else net.get("total_pct")
# Question network line, same exclusion.
q_out = []
n_q = len(payload.get("questions") or [])
for i in range(n_q):
    vals = []
    for d in others:
        if d.get("score_basis") == "UKCV-AH" or d.get("country") == "UK CV":
            continue
        q = d.get("q")
        if isinstance(q, list) and i < len(q) and isinstance(q[i], (int, float)):
            vals.append(q[i])
    q_out.append(round(mean(vals), 4) if vals else None)
net["q_pct"] = q_out
net["avg_hover"] = (
    "Anonymous average of the other IDS markets. "
    "UTI is not inside this figure. "
    "UTI's own percentage is service and parts only. "
    "Premises, organisation and vehicle sales were not filled, so they are not a 0%. "
    "Section E is left out where a market did not score it."
)

geo_counts = attach_geo_to_dealers(payload["dealers"])
print("geo", geo_counts)
uti_only = [d for d in payload["dealers"] if d.get("country") == "UTI"]
sanity = sanity_check_geo_clustering(uti_only)
print(format_geo_sanity_report(sanity))
for d in uti_only:
    g = d.get("geo") or {}
    print(f"  {d['name'][:28]:28} {g.get('place') or g.get('label') or ''} {g.get('lat')} {g.get('lon')} src={g.get('source')}")

country = filter_country_payload(payload, "UTI")
country["version"] = "v1.5"
# Keep the other-markets network object after the filter copies it.
country["network"] = net
for d in country["dealers"]:
    for sid, sec in (d.get("sections") or {}).items():
        if isinstance(sec, dict):
            sec["network_avg_pct"] = sec_pct.get(sid)

errs = validate_dashboard_payload(country)
print(format_qa_report(country, errs))

built = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
html = render_country_html(country, "UTI", built_at=built)
html = html.replace(
    ">v1.4</span>",
    ">v1.5</span>",
    1,
)
html = html.replace("v1.4 · UTI dealers", "v1.5 · UTI dealers", 1)
html = html.replace(
    f"built {built}",
    f"built {built}<br /><strong>Self-assessment.</strong> Scores are each dealer's own marks. "
    "The percentage is service and parts. Premises, organisation and vehicle sales were not filled, "
    "so they are left out. They are not shown as 0%.",
    1,
)
OUT.write_text(html, encoding="utf-8")
CMD.write_bytes(b'@echo off\r\nstart "" "%~dp0IDS_2026_dealer_compare_UTI.html"\r\n')
print("WROTE", OUT, OUT.stat().st_size)
print("country avg", round(country["country_profiles"]["UTI"]["total_pct"] * 100, 1))
print("network dealers", net["dealer_count"], "network pct", round(net["total_pct"] * 100, 1))
