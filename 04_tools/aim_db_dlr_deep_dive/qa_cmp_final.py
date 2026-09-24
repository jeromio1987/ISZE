"""Final QA pass: the fixed screenshot set, the refusal path, and the launcher check.

1. Takes exactly eight screenshots (four full pages, two lower sections, two part-number drills).
2. Probes the "cannot compare" path by loading a temporary copy of the Portugal page whose pairs
   are emptied, so the panel that refuses a comparison is actually exercised rather than assumed.
3. Confirms the OPEN_*.cmd files exist beside each HTML with CRLF line endings.
"""
import json
import re
import shutil
from pathlib import Path

from playwright.sync_api import sync_playwright

DASH = Path(r"C:\Users\jerom\Desktop\claude\ISZE\02_dashboards\sales")
QA = Path(r"C:\Users\jerom\Desktop\claude\ISZE\04_tools\aim_db_dlr_deep_dive\_qa")
TMP = QA / "_tmp_nocmp.html"


def crlf_check(p: Path):
    b = p.read_bytes()
    return {"exists": p.exists(), "bytes": len(b),
            "crlf_first": b[:2] == b"\r\n" or b"\r\n" in b[:80],
            "lf_only": b.count(b"\n") - b.count(b"\r\n"), "text": b.decode("utf-8")}


def main():
    QA.mkdir(parents=True, exist_ok=True)
    report = {"shots": [], "refusal": None, "launchers": []}

    # ---- the launchers
    for run in ("PORTUGAL", "ALL"):
        cmd = DASH / f"OPEN_AIM_COMPARISON_{run}.cmd"
        info = crlf_check(cmd)
        report["launchers"].append({"run": run, **info})
        html = DASH / f"ISZE_AIM_Comparison_{run}.html"
        info2 = crlf_check(html)
        report["html"] = report.get("html", {}) or {}
        report["html"][run] = {"exists": html.exists(), "mb": round(info2["bytes"]/1024/1024, 2)}

    # ---- the refusal path: empty the pair list for PORTUGAL and see what the page says
    src = DASH / "ISZE_AIM_Comparison_PORTUGAL.html"
    text = src.read_text(encoding="utf-8")
    m = re.search(r'(<script type="application/json" id="data">)(.*?)(</script>)', text, re.S)
    payload = json.loads(m.group(2).replace("<\\/", "</"))
    payload["pairs"]["PORTUGAL"] = []
    patched = text[:m.start(2)] + json.dumps(payload, separators=(",", ":")) + text[m.end(2):]
    TMP.write_text(patched, encoding="utf-8")

    with sync_playwright() as pw:
        b = pw.chromium.launch(
            executable_path=r"C:\Program Files\Google\Chrome\Application\chrome.exe",
            args=["--allow-file-access-from-files"])
        # --- the eight screenshots
        plan = [
            ("PORTUGAL", "desktop", 1500, 5600, None),
            ("PORTUGAL", "narrow", 390, 6400, None),
            ("ALL", "desktop", 1500, 5600, None),
            ("ALL", "narrow", 390, 6400, None),
            ("PORTUGAL", "coverage", 1500, 900, "s4"),
            ("ALL", "coverage", 1500, 900, "s4"),
            ("PORTUGAL", "drill_pn", 1500, 1000, None),
            ("ALL", "drill_pn", 1500, 1000, None),
        ]
        for run, tag, w, h, scroll in plan:
            pg = b.new_page(viewport={"width": w, "height": h})
            errs = []
            pg.on("pageerror", lambda e: errs.append(str(e)))
            pg.goto((DASH / f"ISZE_AIM_Comparison_{run}.html").as_uri(), wait_until="load")
            pg.wait_for_timeout(2600)
            if run.endswith("drill_pn") or tag == "drill_pn":
                for _ in range(3):
                    pg.click("#t-up tbody tr:first-child")
                    pg.wait_for_timeout(1000)
            if scroll:
                pg.evaluate(f"document.getElementById('{scroll}').scrollIntoView()")
                pg.wait_for_timeout(700)
            if tag != "drill_pn":
                pg.screenshot(path=str(QA / f"final_{run}_{tag}.png"), full_page=True)
            else:
                pg.screenshot(path=str(QA / f"final_{run}_{tag}.png"))
            report["shots"].append({"run": run, "tag": tag, "w": w, "h": h,
                                    "path": str(QA / f"final_{run}_{tag}.png"),
                                    "errors": errs})
            pg.close()

        # --- the refusal probe
        pg = b.new_page(viewport={"width": 1500, "height": 1000})
        errs = []
        pg.on("pageerror", lambda e: errs.append(str(e)))
        pg.on("console", lambda mm: errs.append(mm.text) if mm.type == "error" else None)
        pg.goto(TMP.as_uri(), wait_until="load")
        pg.wait_for_timeout(2200)
        report["refusal"] = pg.evaluate("""() => ({
          pairDisabled: document.getElementById('pair').disabled,
          pairText: document.getElementById('pair').options[0].text,
          blockedNote: document.getElementById('pairnote').textContent.replace(/\\s+/g,' ').trim(),
          kpiCount: document.querySelectorAll('#kpis .kpi').length,
          kpiHtml: document.getElementById('kpis').innerHTML.length,
          tableRows: document.querySelectorAll('#t-drilltb tbody tr').length,
          upRows: document.querySelectorAll('#t-up tbody tr').length,
          title: document.getElementById('t-drill').textContent,
          crumb: document.getElementById('crumb').textContent.trim(),
          coverRows: document.querySelectorAll('#t-cover tbody tr').length,
          footChars: document.getElementById('foot').textContent.length,
          jsErrors: 0
        })""")
        report["refusal"]["errors"] = errs
        pg.screenshot(path=str(QA / "final_refusal.png"))
        report["shots"].append({"run": "REFUSAL", "tag": "probe", "w": 1500, "h": 1000,
                                "path": str(QA / "final_refusal.png"), "errors": errs})
        pg.close()
        b.close()

    (QA / "final_qa.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    print("screenshots taken:", len(report["shots"]))
    for s in report["shots"]:
        print(f"  {s['run']:<9} {s['tag']:<9} {s['w']}x{s['h']}  errors={s['errors'] or 'none'}")
    print("\nlaunchers:")
    for l in report["launchers"]:
        print(f"  {l['text'].strip()!r}  exists={l['exists']} bytes={l['bytes']} "
              f"crlf={l['crlf_first']} bare_lf={l['lf_only']}")
    print("\nhtml sizes:", report["html"])
    print("\nrefusal probe:")
    for k, v in report["refusal"].items():
        print(f"  {k}: {str(v)[:200]}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
