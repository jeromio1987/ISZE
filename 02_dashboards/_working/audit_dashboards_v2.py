"""Refined audit: ignore webfont proxy noise; capture failed URLs + real pageerrors."""
from __future__ import annotations

import json
import re
from pathlib import Path
from urllib.parse import unquote

from playwright.sync_api import sync_playwright

ROOT = Path(r"C:\Users\jerom\Desktop\claude\ISZE\02_dashboards")
INDEX = ROOT / "_working" / "index.html"
OUT = ROOT / "_working" / "audit"
OUT.mkdir(parents=True, exist_ok=True)

hrefs = re.findall(r'href="(\.\./[^"]+\.html)"', INDEX.read_text(encoding="utf-8", errors="replace"))
files, seen = [], set()
for h in hrefs:
    p = (INDEX.parent / h).resolve()
    if p in seen or p == INDEX.resolve() or not p.exists():
        continue
    seen.add(p)
    files.append(p)

IGNORE_HOST_BITS = ("fonts.googleapis", "fonts.gstatic", "google.com/recaptcha")

PROBE = r"""
() => {
  const bodyText = (document.body && document.body.innerText || '').replace(/\s+/g,' ').trim();
  const canvases = [...document.querySelectorAll('canvas')];
  const canvasStats = canvases.map((c,i) => {
    let nonZero=0, w=c.width||0, h=c.height||0;
    try {
      const ctx=c.getContext('2d');
      if(ctx && w>0 && h>0){
        const d=ctx.getImageData(0,0,Math.min(w,900),Math.min(h,700)).data;
        for(let j=3;j<d.length;j+=12){ if(d[j]>10) nonZero++; }
      }
    } catch(e){ return {i,w,h,nonZero:-1,blank:true,err:String(e)}; }
    return {i,w,h,nonZero,blank: nonZero < 12};
  });
  // meaningful chart SVGs: larger than icon size
  const svgs=[...document.querySelectorAll('svg')].map((s,i)=>{
    const b=s.getBoundingClientRect();
    const kids=s.querySelectorAll('path,rect,circle,line,polyline,polygon,text').length;
    const chartish = b.width>=120 && b.height>=80;
    return {i,w:Math.round(b.width),h:Math.round(b.height),kids,chartish,blank: chartish && kids<3};
  });
  const unavailable=/data unavailable|failed to load|echarts is not defined|chart is not defined|error loading/i.test(bodyText);
  return {
    title: document.title||'',
    bodyLen: bodyText.length,
    bodySample: bodyText.slice(0,240),
    canvasStats,
    blankCanvases: canvasStats.filter(c=>c.blank).length,
    canvasCount: canvases.length,
    chartSvgs: svgs.filter(s=>s.chartish),
    blankChartSvgs: svgs.filter(s=>s.blank).length,
    typeofChart: typeof window.Chart,
    typeofEcharts: typeof window.echarts,
    typeofPlotly: typeof window.Plotly,
    echartsInst: document.querySelectorAll('[_echarts_instance_]').length
  };
}
"""


def is_ignorable(url: str) -> bool:
    u = (url or "").lower()
    return any(b in u for b in IGNORE_HOST_BITS)


results = []
with sync_playwright() as p:
    browser = p.chromium.launch(
        channel="chrome",
        headless=True,
        proxy={"server": "http://127.0.0.1:9"},
        args=["--disable-web-security", "--allow-file-access-from-files"],
    )
    context = browser.new_context(viewport={"width": 1440, "height": 900})
    page = context.new_page()

    failed_reqs = []
    page_errors = []

    def on_request_failed(req):
        failed_reqs.append(req.url)

    def on_pageerror(exc):
        page_errors.append(str(exc))

    def on_console(msg):
        if msg.type == "error":
            # resource failures also show as console error with no URL sometimes
            page_errors.append(f"console:{msg.text}")

    page.on("requestfailed", on_request_failed)
    page.on("pageerror", on_pageerror)
    page.on("console", on_console)

    for i, path in enumerate(files, 1):
        failed_reqs.clear()
        page_errors.clear()
        rel = path.relative_to(ROOT).as_posix()
        print(f"[{i}/{len(files)}] {rel}", flush=True)
        raw = path.read_text(encoding="utf-8", errors="replace")
        if len(raw) < 800 and ("http-equiv" in raw.lower() or "location." in raw):
            results.append({"file": rel, "status": "redirect"})
            continue
        try:
            page.goto(path.resolve().as_uri(), wait_until="domcontentloaded", timeout=45000)
            page.wait_for_timeout(2200)
            probe = page.evaluate(PROBE)
            bad_fails = [u for u in failed_reqs if not is_ignorable(u)]
            # de-noise console resource lines if only fonts failed
            real_page_errors = [
                e
                for e in page_errors
                if "ERR_PROXY" not in e
                and "Failed to load resource" not in e
                and not any(b in e.lower() for b in IGNORE_HOST_BITS)
            ]
            issues = []
            if probe.get("unavailable"):
                issues.append("unavailable_text")
            if probe["canvasCount"] > 0 and probe["blankCanvases"] >= max(1, (probe["canvasCount"] + 1) // 2):
                issues.append("blank_canvases")
            if probe["blankChartSvgs"] > 0:
                issues.append("blank_chart_svgs")
            if probe["canvasCount"] > 0 and probe["typeofChart"] == "undefined" and probe["typeofEcharts"] == "undefined" and probe["typeofPlotly"] == "undefined" and probe["echartsInst"] == 0:
                issues.append("chart_lib_missing")
            if real_page_errors:
                issues.append("js_error")
            missing_files = []
            for u in bad_fails:
                if u.startswith("file:"):
                    fp = Path(unquote(u.replace("file:///", "").replace("file://", "")))
                    if len(str(fp)) > 3 and not fp.exists():
                        missing_files.append(u)
            if missing_files:
                issues.append("missing_local_asset")

            status = "ok" if not issues else "broken"
            entry = {
                "file": rel,
                "status": status,
                "issues": issues,
                "page_errors": real_page_errors[:8],
                "failed_nonfont": bad_fails[:12],
                "missing_files": missing_files[:12],
                "probe": {
                    "bodyLen": probe["bodyLen"],
                    "canvasCount": probe["canvasCount"],
                    "blankCanvases": probe["blankCanvases"],
                    "blankChartSvgs": probe["blankChartSvgs"],
                    "typeofChart": probe["typeofChart"],
                    "typeofEcharts": probe["typeofEcharts"],
                    "echartsInst": probe["echartsInst"],
                    "bodySample": probe["bodySample"],
                },
            }
            if status != "ok":
                shot = OUT / f"fix2__{rel.replace('/', '__')}.png"
                page.screenshot(path=str(shot), full_page=False)
                entry["screenshot"] = str(shot)
            results.append(entry)
        except Exception as e:
            results.append({"file": rel, "status": "error", "issues": ["load_error"], "error": str(e)[:300]})

    browser.close()

summary = {
    "total": len(results),
    "ok": sum(1 for r in results if r.get("status") == "ok"),
    "broken": sum(1 for r in results if r.get("status") == "broken"),
    "redirect": sum(1 for r in results if r.get("status") == "redirect"),
    "error": sum(1 for r in results if r.get("status") == "error"),
}
(OUT / "report2.json").write_text(json.dumps({"summary": summary, "results": results}, indent=2), encoding="utf-8")
print(json.dumps(summary, indent=2))
print("\nBROKEN:")
for r in results:
    if r.get("status") in ("broken", "error"):
        print("-", r["file"], r.get("issues"), r.get("page_errors", [])[:2], "fails=", (r.get("failed_nonfont") or [])[:2])
