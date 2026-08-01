"""Offline visual audit of every dashboard linked from _working/index.html."""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

from playwright.sync_api import sync_playwright

ROOT = Path(r"C:\Users\jerom\Desktop\claude\ISZE\02_dashboards")
INDEX = ROOT / "_working" / "index.html"
OUT_DIR = ROOT / "_working" / "audit"
OUT_DIR.mkdir(parents=True, exist_ok=True)

# Collect relative hrefs from the index (skip self)
hrefs = re.findall(r'href="(\.\./[^"]+\.html)"', INDEX.read_text(encoding="utf-8", errors="replace"))
# Dedupe preserving order
seen = set()
files: list[Path] = []
for h in hrefs:
    p = (INDEX.parent / h).resolve()
    if p in seen:
        continue
    seen.add(p)
    if p.exists() and p != INDEX.resolve():
        files.append(p)

PROBE_JS = r"""
() => {
  const bodyText = (document.body && document.body.innerText || '').replace(/\s+/g, ' ').trim();
  const title = document.title || '';
  const canvases = [...document.querySelectorAll('canvas')];
  const canvasStats = canvases.map((c, i) => {
    let nonZero = 0, w = c.width || 0, h = c.height || 0;
    try {
      const ctx = c.getContext('2d');
      if (ctx && w > 0 && h > 0) {
        const data = ctx.getImageData(0, 0, Math.min(w, 800), Math.min(h, 600)).data;
        for (let j = 3; j < data.length; j += 16) { if (data[j] > 8) nonZero++; }
      }
    } catch (e) { return { i, w, h, nonZero: -1, err: String(e) }; }
    return { i, w, h, nonZero, blank: nonZero < 8 };
  });
  const svgs = [...document.querySelectorAll('svg')];
  const svgStats = svgs.map((s, i) => {
    const box = s.getBoundingClientRect();
    const kids = s.querySelectorAll('path,rect,circle,line,polyline,polygon,text,g > *').length;
    return { i, w: Math.round(box.width), h: Math.round(box.height), kids, blank: kids < 2 || box.width < 4 || box.height < 4 };
  });
  // ECharts / Chart containers that look empty
  const chartHosts = [...document.querySelectorAll('[id*="chart" i], [class*="chart" i], .echarts-for-react, [_echarts_instance_]')]
    .slice(0, 40)
    .map(el => {
      const box = el.getBoundingClientRect();
      const hasCanvas = !!el.querySelector('canvas');
      const hasSvg = !!el.querySelector('svg');
      return { tag: el.tagName, id: el.id || '', cls: (el.className||'').toString().slice(0,80),
               w: Math.round(box.width), h: Math.round(box.height), hasCanvas, hasSvg };
    });
  const unavailable = /data unavailable|failed to load|echarts is not defined|chart\.js.*not|cannot find module|loading\.{3}\s*$|error loading/i.test(bodyText);
  const stuckLoading = /^[\s\S]{0,400}$/i.test(bodyText) && /loading/i.test(bodyText);
  const metaRefresh = !!document.querySelector('meta[http-equiv="refresh" i]');
  const externalScripts = [...document.querySelectorAll('script[src]')].map(s => s.src).filter(s => /^https?:/i.test(s));
  const externalCss = [...document.querySelectorAll('link[rel="stylesheet"]')].map(l => l.href).filter(h => /^https?:/i.test(h));
  return {
    title, bodyLen: bodyText.length, bodySample: bodyText.slice(0, 220),
    canvasStats, svgStats,
    blankCanvases: canvasStats.filter(c => c.blank || c.nonZero === 0).length,
    blankSvgs: svgStats.filter(s => s.blank).length,
    canvasCount: canvases.length, svgCount: svgs.length,
    chartHosts, unavailable, stuckLoading, metaRefresh,
    externalScripts, externalCss,
    typeofChart: typeof window.Chart, typeofEcharts: typeof window.echarts, typeofPlotly: typeof window.Plotly
  };
}
"""


def file_url(p: Path) -> str:
    return p.resolve().as_uri()


results = []

with sync_playwright() as p:
    browser = p.chromium.launch(
        channel="chrome",
        headless=True,
        proxy={"server": "http://127.0.0.1:9"},
        args=["--disable-web-security", "--allow-file-access-from-files"],
    )
    context = browser.new_context(viewport={"width": 1440, "height": 900}, ignore_https_errors=True)
    page = context.new_page()
    console_logs: list[str] = []
    page.on("console", lambda msg: console_logs.append(f"{msg.type}: {msg.text}") if msg.type in ("error", "warning") else None)
    page.on("pageerror", lambda exc: console_logs.append(f"pageerror: {exc}"))

    for i, path in enumerate(files, 1):
        console_logs.clear()
        rel = path.relative_to(ROOT).as_posix()
        print(f"[{i}/{len(files)}] {rel}", flush=True)
        entry = {"file": rel, "exists": path.exists(), "size_kb": round(path.stat().st_size / 1024, 1) if path.exists() else 0}
        try:
            # Redirects are tiny meta-refresh pages — note and skip deep checks
            raw = path.read_text(encoding="utf-8", errors="replace")
            if len(raw) < 800 and ("meta http-equiv" in raw.lower() or "location.replace" in raw or "location.href" in raw):
                entry.update(status="redirect", probe=None, console=[])
                results.append(entry)
                continue

            page.goto(file_url(path), wait_until="domcontentloaded", timeout=45000)
            page.wait_for_timeout(1800)
            probe = page.evaluate(PROBE_JS)
            errs = [c for c in console_logs if c.startswith("error:") or c.startswith("pageerror:")]
            probe["consoleErrors"] = errs[:12]
            probe["consoleWarnCount"] = sum(1 for c in console_logs if c.startswith("warning:"))

            issues = []
            if probe["unavailable"] or probe["stuckLoading"]:
                issues.append("unavailable_or_loading")
            if probe["canvasCount"] > 0 and probe["blankCanvases"] >= max(1, probe["canvasCount"] // 2):
                issues.append("blank_canvases")
            if probe["svgCount"] >= 3 and probe["blankSvgs"] >= max(2, probe["svgCount"] // 2):
                issues.append("blank_svgs")
            if probe["bodyLen"] < 180 and not probe.get("metaRefresh"):
                issues.append("nearly_empty_page")
            if errs and any("is not defined" in e or "Failed to load" in e or "net::" in e for e in errs):
                issues.append("console_fatal")
            # Chart.js expected but missing
            if probe["canvasCount"] > 0 and probe["typeofChart"] == "undefined" and probe["typeofEcharts"] == "undefined" and probe["typeofPlotly"] == "undefined":
                # might still be inline SVG-only; only flag if canvases blank
                if probe["blankCanvases"] > 0:
                    issues.append("chart_lib_missing")

            status = "ok" if not issues else "broken"
            # softer: visual quality soft-flags
            soft = []
            if probe["bodyLen"] < 600:
                soft.append("thin_content")
            if probe["externalScripts"] or [u for u in probe["externalCss"] if "fonts.googleapis" not in u]:
                soft.append("external_assets")
            elif probe["externalCss"]:
                soft.append("webfonts_only")

            entry.update(status=status, issues=issues, soft=soft, probe=probe)

            if status != "ok" or soft:
                shot = OUT_DIR / (rel.replace("/", "__") + ".png")
                page.screenshot(path=str(shot), full_page=False)
                entry["screenshot"] = str(shot)
        except Exception as e:
            entry.update(status="error", error=str(e)[:300], issues=["load_error"])
            try:
                shot = OUT_DIR / (rel.replace("/", "__") + "_ERR.png")
                page.screenshot(path=str(shot), full_page=False)
                entry["screenshot"] = str(shot)
            except Exception:
                pass
        results.append(entry)

    browser.close()

summary = {
    "total": len(results),
    "ok": sum(1 for r in results if r.get("status") == "ok"),
    "broken": sum(1 for r in results if r.get("status") == "broken"),
    "redirect": sum(1 for r in results if r.get("status") == "redirect"),
    "error": sum(1 for r in results if r.get("status") == "error"),
}
report = {"summary": summary, "results": results}
(OUT_DIR / "report.json").write_text(json.dumps(report, indent=2), encoding="utf-8")

print("\n==== SUMMARY ====")
print(json.dumps(summary, indent=2))
print("\n==== BROKEN / ERROR ====")
for r in results:
    if r.get("status") in ("broken", "error"):
        print(f"- {r['file']}: {r.get('issues') or r.get('error')} soft={r.get('soft')}")
print("\n==== THIN / SOFT ====")
for r in results:
    if r.get("status") == "ok" and r.get("soft"):
        print(f"- {r['file']}: {r.get('soft')} bodyLen={r.get('probe',{}).get('bodyLen')}")

print(f"\nReport: {OUT_DIR / 'report.json'}")
