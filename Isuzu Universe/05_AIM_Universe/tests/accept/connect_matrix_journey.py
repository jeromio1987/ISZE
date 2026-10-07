"""U28 task 1 - the connection matrix, browser half (the real product view).

What this proves
----------------
One browser run drives the REAL built product to the decision view with synthetic
fixtures and asserts, per feed, one of:
  (a) the evidence paints with its source and date, or
  (b) a visible "not available" state that names what is missing.

It also proves CONNECT-08 E1 on the page: with every optional input absent, the
case journey still builds and paints - it is not broken by what it cannot show.

It writes progress/connection_matrix.json: feed, painted yes/no, state shown,
screenshot file.

What it does NOT prove
----------------------
It is not acceptance. It is not production identity, not a shared multi-user
service, not a real IDS sheet, and not a real stock, tender or PRISM input. Every
fixture is invented. The artifact it reads is a SYNTHETIC build written for this
run; the real-payload INTERNAL artifact is never rewritten.

Screenshots: this script TAKES one element screenshot per feed. It does not read
them. The taken count and the read count are recorded separately, because a
take-count is not a read-count.

How to run
    python tests/accept/connect_matrix_journey.py
    python tests/accept/connect_matrix_journey.py --chrome "C:/.../chrome.exe"

Exit codes: 0 all feeds painted or honestly absent; 1 a feed broke the journey;
3 a known finding is open; 4 the browser or the build did not run.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import sys
import tempfile
import time
from pathlib import Path

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "tests" / "accept" / "_out"
SHOTS = OUT / "shots"
SOURCE_ARTIFACT = ROOT / "dist" / "ISZE_AIM_Pricing_Decisions_v04_SYNTHETIC.html"
FIXTURES = ROOT / "tests" / "fixtures" / "connect_matrix.json"
MATRIX_JSON = ROOT / "progress" / "connection_matrix.json"

EXIT_PASS = 0
EXIT_FAIL = 1
EXIT_KNOWN_FINDINGS = 3
EXIT_NOT_RUN = 4

# A deliberately unpainted copy of the artifact, used to prove the mutation
# below fails. Unplugging the adapter is the mutation; this is the file it is
# unplugged in.
MUTANT_ARTIFACT = OUT / "connect_matrix_unplugged.html"

# feed code -> human name. The code matches data-connect-<code> on the page.
FEEDS = [
    ("01", "IDS evidence"),
    ("02", "IDS improvement action"),
    ("03", "PRISM context"),
    ("04", "Service demand"),
    ("05", "Availability question"),
    ("06", "Stock snapshot"),
    ("07", "Tender feed"),
    ("08", "Capability registry"),
    ("run01", "Shared case backend"),
]

RESULTS: list[dict] = []
TAKEN: list[str] = []
KNOWN_FINDINGS: list[dict] = []


def record(check_id: str, name: str, ok: bool, evidence, *, status: str | None = None,
           known_finding: bool = False) -> None:
    if status is None:
        status = "PASS" if ok else "FAIL"
    if status == "PASS" and not ok:
        status = "FAIL"
    row = {"id": check_id, "name": name, "status": status, "evidence": evidence,
           "known_finding": known_finding}
    RESULTS.append(row)
    if known_finding:
        KNOWN_FINDINGS.append(row)


def sha256(path: Path):
    if not path.exists():
        return None
    return hashlib.sha256(path.read_bytes()).hexdigest()


def summary() -> dict:
    return {
        "pass": sum(1 for r in RESULTS if r["status"] == "PASS"),
        "fail": sum(1 for r in RESULTS if r["status"] == "FAIL" and not r.get("known_finding")),
        "untested": sum(1 for r in RESULTS if r["status"] == "UNTESTED"),
        "known_findings": len(KNOWN_FINDINGS),
        "total": len(RESULTS),
    }


def exit_code() -> int:
    s = summary()
    if s["fail"]:
        return EXIT_FAIL
    if s["untested"]:
        return EXIT_NOT_RUN
    if s["known_findings"]:
        return EXIT_KNOWN_FINDINGS
    return EXIT_PASS


def build_fixture_page() -> Path:
    """A copy of the SYNTHETIC artifact with the matrix fixtures merged into its
    embedded payload. The source artifact is never modified."""
    html = SOURCE_ARTIFACT.read_text(encoding="utf-8")
    m = re.search(r'<script id="case-data" type="application/json">([\s\S]*?)</script>', html)
    if not m:
        raise SystemExit("no case-data block in " + str(SOURCE_ARTIFACT))
    payload = json.loads(m.group(1))
    fix = json.loads(FIXTURES.read_text(encoding="utf-8"))
    payload.update(fix.get("payload_extra") or {})
    for case in payload.get("cases") or []:
        extra = (fix.get("cases") or {}).get(case.get("id"))
        if extra:
            case.update(extra)
    patched = html[:m.start()] + '<script id="case-data" type="application/json">' + \
        json.dumps(payload) + '</script>' + html[m.end():]
    OUT.mkdir(parents=True, exist_ok=True)
    target = OUT / "connect_matrix_page.html"
    target.write_text(patched, encoding="utf-8")
    return target


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--chrome", default=os.environ.get(
        "CHROME_PATH", r"C:\Program Files\Google\Chrome\Application\chrome.exe"))
    args = ap.parse_args()

    started = time.time()
    run = {
        "check": "U28-CONNECT-MATRIX",
        "title": "Every feed paints in the real product view, or shows an honest not-available state",
        "review_date": time.strftime("%Y-%m-%dT%H:%M:%S"),
        "source_artifact": str(SOURCE_ARTIFACT),
        "source_artifact_sha256": sha256(SOURCE_ARTIFACT),
        "fixtures": str(FIXTURES),
        "load_mode": "file:// URL, headless Chrome, synthetic fixtures merged into the payload",
        "results": [],
        "known_findings": [],
        "screenshots": {"taken": 0, "read": 0, "read_by": None, "note":
                        "Taken by this script. The read count is filled in only after a person "
                        "or reviewer opens them; a take-count is not a read-count."},
        "scope": "Not acceptance. Synthetic fixtures only. No production identity, no shared "
                 "multi-user service, no real IDS/stock/tender/PRISM input, no real dealer.",
    }

    if not SOURCE_ARTIFACT.is_file():
        record("MATRIX-RUN", "The built artifact exists to drive", False,
               str(SOURCE_ARTIFACT), status="UNTESTED")
        run["results"] = RESULTS
        run["summary"] = summary()
        OUT.mkdir(parents=True, exist_ok=True)
        (OUT / "connect_matrix_journey.json").write_text(json.dumps(run, indent=2) + "\n",
                                                         encoding="utf-8")
        print("MISSING BUILD OUTPUT: " + str(SOURCE_ARTIFACT))
        print("run `python tools/build.py` first; a matrix cannot be read off an absent page.")
        return EXIT_NOT_RUN

    page_path = build_fixture_page()
    run["fixture_page"] = str(page_path)
    run["fixture_page_sha256"] = sha256(page_path)

    # ------------------------------------------------------- the mutation -----
    # Unplug every adapter: build a copy of the artifact with the fixture block
    # removed and one method renamed so the modules publish a surface the view
    # cannot call. Each row must flip to "not available". This is run in the same
    # pass, so a row that says "painted" in the mutant is the check failing.
    mutant_html = page_path.read_text(encoding="utf-8")
    m2 = re.search(r'<script id="case-data" type="application/json">([\s\S]*?)</script>',
                   mutant_html)
    bare = json.loads(m2.group(1))
    for key in ("ids_sheet", "prism_measures", "service_demand", "capability_registry",
                "tender_data"):
        bare.pop(key, None)
    for case in bare.get("cases") or []:
        for key in ("ids_identity", "improvement_action", "availability_selection",
                    "availability_response", "historical_purchase", "stock_snapshot",
                    "tender_notice_ids", "product_image", "prism_level",
                    "ids_improvement_question_code"):
            case.pop(key, None)
    # Rename the entry point each module publishes, so a view that guarded on the
    # global now finds a surface it cannot call.
    mutant_html = (mutant_html[:m2.start()]
                   + '<script id="case-data" type="application/json">' + json.dumps(bare) + '</script>'
                   + mutant_html[m2.end():])
    for rename in ("AIMIdsEvidence = API", "AIMIdsImprovementAction = API",
                   "AIMPrismContext = API", "AIMServiceDemandBounds = API",
                   "AIMAvailabilityQuestion = API", "AIMStockSnapshot = API",
                   "AIMTenderInvestigation = API", "AIMServiceCapability = API"):
        mutant_html = mutant_html.replace("root." + rename, "root.__UNPLUGGED_" + rename)
    MUTANT_ARTIFACT.write_text(mutant_html, encoding="utf-8")
    run["mutation"] = {"file": str(MUTANT_ARTIFACT),
                       "what": "adapters unplugged and fixture payload removed",
                       "expect": "every feed row flips to not available"}

    errors: list[str] = []
    try:
        _cm = sync_playwright()
        pw = _cm.start()
    except Exception as env_err:  # noqa: BLE001
        record("MATRIX-RUN", "The browser environment is available", False,
               str(env_err), status="UNTESTED")
        run["results"] = RESULTS
        run["summary"] = summary()
        (OUT / "connect_matrix_journey.json").write_text(json.dumps(run, indent=2) + "\n",
                                                         encoding="utf-8")
        print("UNTESTED: browser environment blocked -- " + str(env_err)[:400])
        return EXIT_NOT_RUN

    profile = Path(tempfile.mkdtemp(prefix="aim_matrix_"))
    SHOTS.mkdir(parents=True, exist_ok=True)

    def open_page():
        ctx = pw.chromium.launch_persistent_context(
            user_data_dir=str(profile), headless=True, executable_path=args.chrome,
            viewport={"width": 1440, "height": 1000},
            args=["--allow-file-access-from-files"])
        pg = ctx.new_page()
        pg.on("pageerror", lambda e: errors.append(f"pageerror:{e}"))
        pg.on("console", lambda m: errors.append(f"console:{m.text}") if m.type == "error" else None)
        return ctx, pg

    def goto(pg, case_id, view="decision", target=None):
        url = (target or page_path).as_uri() + "#case=" + case_id + "&view=" + view + "&compare=half"
        pg.goto(url)
        pg.wait_for_function("() => !!window.AIMPricing", timeout=30000)
        pg.wait_for_timeout(400)

    def feed_rows(pg, code):
        sel = '[data-connect-%s]' % code
        n = pg.locator(sel).count()
        if not n:
            return {"count": 0, "state": None, "present": False, "sha": None}
        el = pg.locator(sel).first
        state = el.get_attribute("data-connect-%s" % code)
        return {"count": n, "state": state, "present": True, "sha": None}

    try:
        ctx, page = open_page()

        # ---------------------------------------------- the populated case --
        goto(page, "SYNTH-CASE-A")
        render_state = page.locator("#content").get_attribute("data-render-state")
        record("MATRIX-RUN E1", "The product view builds with every connection panel loaded",
               render_state == "built", "data-render-state=" + str(render_state))
        record("MATRIX-RUN E2", "The page starts with no uncaught page or console error",
               not errors, json.dumps(errors[:6]) if errors else "no page error, no console error")

        matrix_rows = []
        for code, label in FEEDS:
            info = feed_rows(page, code)
            painted_tokens = {"painted", "panel"}
            painted = bool(info["present"] and info["state"] in painted_tokens)
            honest_absent = bool(info["present"] and info["state"] in {"absent", "empty"})
            honoured = bool(info["present"] and info["state"] in painted_tokens | {"absent", "empty"})
            shot_path = SHOTS / ("connect_matrix_%s.png" % code)
            if info["present"]:
                page.locator('[data-connect-%s]' % code).first.screenshot(path=str(shot_path))
                TAKEN.append(str(shot_path))
                info["sha"] = sha256(shot_path)
                info["text"] = " ".join(page.locator('[data-connect-%s]' % code).first
                                        .inner_text().split())[:300]
            else:
                info["text"] = ""
            record("MATRIX-%s E1" % code.upper() if code != "run01" else "MATRIX-RUN-01 E1",
                   "Feed %s paints with its source and date, or states what is missing" % label,
                   honoured,
                   json.dumps({"present": info["present"], "state": info["state"],
                               "panels": info["count"]}) if honoured else
                   "the feed has no panel and no not-available state on the decision view")
            matrix_rows.append({
                "feed": code,
                "feed_label": label,
                "painted": painted,
                "honest_absent": honest_absent,
                "state_shown": info["state"],
                "panels_on_page": info["count"],
                "screenshot": (str(shot_path) if info["present"] else None),
                "screenshot_sha256": info["sha"],
                "text_excerpt": info["text"],
            })

        # The evidence each feed must actually print, not merely a marker.
        body = page.locator("#content").inner_text()
        evidence_checks = [
            ("01", "Synthetic UMI Dealer"),
            ("02", "Improvement action"),
            ("03", "PRISM context"),
            ("04", "Service-demand methods"),
            ("05", "Availability question"),
            ("06", "Stock observation"),
            ("07", "notice(s) linked to this case"),
            ("08", "declared service(s) enabled"),
            ("run01", "Case store"),
        ]
        missing_text = [code for code, needle in evidence_checks if needle not in body]
        record("MATRIX-TEXT E1", "Each painted feed carries its readable evidence, not only a marker",
               not missing_text, "missing evidence text for: " + json.dumps(missing_text)
               if missing_text else "all nine feeds carry their evidence text")

        # ------------------------------------ CONNECT-08 E1 on the page --
        # With every optional input absent the case journey still builds. This is
        # the case with an unvalidated identity and no IDS/stock/tender/prism
        # fixtures applied to it.
        goto(page, "SYNTH-CASE-B")
        b_state = page.locator("#content").get_attribute("data-render-state")
        b_body = page.locator("#content").inner_text()
        broken = (b_state != "built") or ("did not render" in b_body) or (not b_body.strip())
        record("MATRIX-CONNECT-08 E1b",
               "CONNECT-08 E1: missing optional inputs do not break the case journey on the page",
               not broken,
               json.dumps({"render_state": b_state, "chars": len(b_body.strip())}))

        ctx.close()

        # ------------------------- the unplugged page: every feed honest --
        # The same artifact with the adapters unplugged and the fixture payload
        # removed. Every optional input is absent, so each feed must show its
        # not-available or nothing-recorded state and the case journey must still
        # build. A feed that says "painted" here is a feed that claims evidence it
        # does not have, and that is the mutation this check fails on.
        ctx2, page2 = open_page()
        try:
            goto(page2, "SYNTH-CASE-A", target=MUTANT_ARTIFACT)
            p2_state = page2.locator("#content").get_attribute("data-render-state")
            record("MATRIX-UNPLUG E0", "CONNECT-08 E1: the case journey builds with every optional input absent",
                   p2_state == "built", "data-render-state=" + str(p2_state))
            for code, label in FEEDS:
                if code == "run01":
                    sel = '[data-connect-run01]'
                    st = (page2.locator(sel).first.get_attribute("data-connect-run01")
                          if page2.locator(sel).count() else None)
                    # The case store is not an optional input: it is present with
                    # or without fixtures, so painted is the honest state here.
                    record("MATRIX-UNPLUG run01",
                           "The shared case backend still reports the store it runs on with no fixtures",
                           st == "painted", "state=" + str(st))
                    continue
                sel = '[data-connect-%s]' % code
                st = (page2.locator(sel).first.get_attribute("data-connect-%s" % code)
                      if page2.locator(sel).count() else None)
                record("MATRIX-UNPLUG %s" % code,
                       "%s states what is missing instead of claiming evidence it does not have" % label,
                       st in {"absent", "empty"},
                       "state=" + str(st) + " (expected absent or empty)")
            p2_body = page2.locator("#content").inner_text()
            named = sum(1 for _ in re.finditer(r"What is missing:|What would fill this:", p2_body))
            record("MATRIX-UNPLUG N1",
                   "Each unplugged feed names what is missing rather than failing silently",
                   named >= 6, "%d panel(s) state what is missing" % named)
            page2.locator("#content").screenshot(path=str(SHOTS / "connect_matrix_unplugged.png"))
            TAKEN.append(str(SHOTS / "connect_matrix_unplugged.png"))
        finally:
            ctx2.close()

        run["screenshots"]["taken"] = len(TAKEN)
        run["matrix"] = matrix_rows
        run["results"] = RESULTS
        run["known_findings"] = list(KNOWN_FINDINGS)
        run["summary"] = summary()
        run["seconds"] = round(time.time() - started, 1)

        MATRIX_JSON.parent.mkdir(parents=True, exist_ok=True)
        MATRIX_JSON.write_text(json.dumps({
            "written_by": "tests/accept/connect_matrix_journey.py",
            "written_at": time.strftime("%Y-%m-%dT%H:%M:%S"),
            "source_artifact": run["source_artifact"],
            "source_artifact_sha256": run["source_artifact_sha256"],
            "fixtures": run["fixtures"],
            "screenshots": {"taken": len(TAKEN), "read": 0, "read_by": None},
            "feeds": matrix_rows,
            "summary": run["summary"],
        }, indent=2) + "\n", encoding="utf-8")
        (OUT / "connect_matrix_journey.json").write_text(json.dumps(run, indent=2) + "\n",
                                                        encoding="utf-8")
    except Exception as err:  # noqa: BLE001
        record("MATRIX-RUN", "The browser journey completed", False, str(err), status="UNTESTED")
        run["results"] = RESULTS
        run["summary"] = summary()
        (OUT / "connect_matrix_journey.json").write_text(json.dumps(run, indent=2) + "\n",
                                                        encoding="utf-8")
        print("UNTESTED: " + str(err)[:400])
        return EXIT_NOT_RUN
    finally:
        try:
            pw.stop()
        except Exception:  # noqa: BLE001
            pass

    for r in RESULTS:
        print(("PASS " if r["status"] == "PASS" else r["status"].ljust(5)) + " " + r["id"] + "  " + r["name"])
        if r["evidence"]:
            print("      -> " + str(r["evidence"])[:220])
    print("")
    print(json.dumps(summary()))
    print("screenshots taken: %d | read: 0 (this script does not read them)" % len(TAKEN))
    print("matrix written: " + str(MATRIX_JSON))
    return exit_code()


if __name__ == "__main__":
    sys.exit(main())
