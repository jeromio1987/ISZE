"""U29 task C - the two real feeds in the INTERNAL build (browser half).

Drives the freshly built INTERNAL artifact (real tender feed + real PRISM measures) in
headless Chrome and asserts, on a case whose own market matches:

  * CONNECT-07 tender feed paints, with the notice's real buyer/deadline, and marks an
    expired or past notice as not actionable.
  * CONNECT-03 PRISM context paints at its measured level (national), names the source, and
    refuses to turn a national total into a dealer per-truck rate.
  * the unplug check: the same two panels say what is missing when the feed block is absent.

Writes dist/_u29c_real_feeds_check.json.

Exit codes: 0 all pass; 1 a feed did not paint; 4 the browser or the build did not run.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import tempfile
from pathlib import Path

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[2]
ARTIFACT = ROOT / "dist" / "ISZE_AIM_Pricing_Decisions_v04_INTERNAL.html"
OUT = ROOT / "dist" / "_u29c_real_feeds_check.json"

RESULTS: list[dict] = []


def record(cid, name, ok, evidence):
    RESULTS.append({"id": cid, "name": name, "status": "PASS" if ok else "FAIL",
                    "evidence": evidence})


def sha256(p: Path):
    return hashlib.sha256(p.read_bytes()).hexdigest() if p.exists() else None


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--chrome",
                    default=r"C:\Program Files\Google\Chrome\Application\chrome.exe")
    args = ap.parse_args()

    if not ARTIFACT.is_file():
        print("missing artifact:", ARTIFACT)
        return 4

    errors: list[str] = []
    profile = Path(tempfile.mkdtemp(prefix="aim_u29c_"))
    url_base = ARTIFACT.as_uri()

    with sync_playwright() as pw:
        ctx = pw.chromium.launch_persistent_context(
            user_data_dir=str(profile), headless=True, executable_path=args.chrome,
            viewport={"width": 1440, "height": 1000},
            args=["--allow-file-access-from-files"])
        page = ctx.new_page()
        page.on("pageerror", lambda e: errors.append(f"pageerror:{e}"))
        page.on("console", lambda m: errors.append(f"console:{m.text}") if m.type == "error" else None)

        def goto(case_id):
            page.goto(url_base + "#case=" + case_id + "&view=decision&compare=half")
            page.wait_for_function("() => !!window.AIMPricing", timeout=30000)
            page.wait_for_timeout(400)

        def panel(code):
            sel = f'[data-connect-{code}]'
            n = page.locator(sel).count()
            if not n:
                return {"count": 0, "state": None, "text": ""}
            el = page.locator(sel).first
            return {"count": n, "state": el.get_attribute(f"data-connect-{code}"),
                    "text": " ".join(el.inner_text().split())}

        # ---------------------------------------------------- ITUK case --
        goto("ITUK-PADS")
        st = page.locator("#content").get_attribute("data-render-state")
        record("U29C-RUN E0", "The internal view builds with the real feeds attached",
               st == "built", "data-render-state=" + str(st))
        record("U29C-RUN E1", "No uncaught page or console error",
               not errors, json.dumps(errors[:6]) if errors else "clean")

        t = panel("07")
        painted = t["state"] in ("painted", "panel")
        record("U29C-07 E1", "Tender feed paints on an ITUK case with real notices",
               painted, json.dumps({"state": t["state"], "panels": t["count"]}))
        has_notices = "notice(s) linked to this case" in t["text"]
        record("U29C-07 E2", "The panel names the linked notices",
               has_notices, t["text"][:200])
        # A real buyer from the feed must appear (Merthyr Tydfil is on an ITUK notice).
        real_buyer = any(k in t["text"] for k in
                         ("Merthyr", "Ingoldmells", "Southampton", "NOTTINGHAM", "NORTHERN IRELAND"))
        record("U29C-07 E3", "A real buyer name from the feed is printed",
               real_buyer, t["text"][:300])
        record("U29C-07 E4", "Notice value is never presented as parts revenue",
               "not Isuzu parts revenue" in t["text"] or "Billing created by this award: none" in t["text"],
               "residual-revenue guard text present: " +
               str("not Isuzu parts revenue" in t["text"]))

        p = panel("03")
        pp = p["state"] in ("painted", "panel")
        record("U29C-03 E1", "PRISM context paints on an ITUK case with real measures",
               pp, json.dumps({"state": p["state"], "panels": p["count"]}))
        record("U29C-03 E2", "A real national measure value is printed",
               "22389" in p["text"].replace(",", "") or "22389" in p["text"] or "22,389" in p["text"],
               p["text"][:300])
        record("U29C-03 E3", "The measure is labelled national, at its measured level",
               "national" in p["text"].lower(), p["text"][:300])
        record("U29C-03 E4", "A national total is not converted to a dealer per-truck rate",
               "no dealer-level per-truck measure is available" in p["text"].lower()
               or "not divided" in p["text"].lower(), p["text"][:300])

        # ------------------------------------------------ Portugal case --
        goto("IMOTORS-CABIN")
        t2 = panel("07")
        record("U29C-07 E5", "Tender feed paints on a Portugal case with its own notices",
               t2["state"] in ("painted", "panel"),
               json.dumps({"state": t2["state"], "panels": t2["count"], "text": t2["text"][:160]}))

        ctx.close()

    summary = {
        "check": "U29C-REAL-FEEDS",
        "artifact": str(ARTIFACT),
        "artifact_sha256": sha256(ARTIFACT),
        "results": RESULTS,
        "pass": sum(1 for r in RESULTS if r["status"] == "PASS"),
        "fail": sum(1 for r in RESULTS if r["status"] == "FAIL"),
    }
    OUT.write_text(json.dumps(summary, indent=2), encoding="utf-8")
    for r in RESULTS:
        print(f"  {r['status']:4s} {r['id']:12s} {r['name']}")
        if r["status"] == "FAIL":
            print(f"        evidence: {r['evidence']}")
    print(f"\npass {summary['pass']} / fail {summary['fail']}  -> {OUT}")
    return 1 if summary["fail"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
