"""Full QA of IDS 2026 DB Feedback Sheet v0.4. Prints FAIL lines + JSON summary."""
from __future__ import annotations

import json
import re
from collections import Counter
from html.parser import HTMLParser
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BANNED = (
    "slecht",
    " goed",
    "IML v7",
    "Model B",
    "PRISM lane",
    "Changelog",
    "NaN",
)
EMPTY_MARKERS = ("DATA UNAVAILABLE",)
KPI_RE = re.compile(r"\d+(?:\.\d+)?%")
TBODY_ROW_RE = re.compile(r"<tbody>.*?<tr", re.I | re.S)
EXPECTED = {
    "Belgium": 34,
    "Netherlands": 9,
    "Luxembourg": 1,
    "Denmark": 20,
    "Poland": 23,
    "Greece": 34,
    "Norway": 38,
    "Hungary": 19,
    "Romania": 15,
    "Malta": 1,
    "Cyprus": 1,
    "UK_CV": 44,
    "UK_LCV": 45,
    "Portugal": 16,
    "Israel_LCV": 29,
    "France": 84,
    "Italy": 41,
    "Spain": 45,
    "Switzerland": 22,
}
ROLLUP = {
    k: f"IDS_2026_DB_Rollup_{k}_v0.4.html" for k in EXPECTED
}

fails: list[str] = []
warns: list[str] = []
stats = Counter()


def fail(msg: str) -> None:
    fails.append(msg)
    print("FAIL", msg)


def warn(msg: str) -> None:
    warns.append(msg)
    print("WARN", msg)


def html_ok(path: Path, *, min_bytes: int, need_kpi: bool, need_tbody: bool, extra: list[str] | None = None) -> None:
    stats["html_checked"] += 1
    if not path.is_file():
        fail(f"missing {path}")
        return
    size = path.stat().st_size
    if size < min_bytes:
        fail(f"tiny {path.name} {size}B")
        return
    text = path.read_text(encoding="utf-8", errors="replace")
    low = text.lower()
    for b in BANNED:
        if b.lower() in low:
            fail(f"banned '{b}' in {path}")
    if "file://" in text:
        fail(f"file:// in {path}")
    if need_kpi and not KPI_RE.search(text):
        fail(f"no % KPI in {path}")
    if need_tbody and not TBODY_ROW_RE.search(text):
        fail(f"empty/no tbody rows in {path}")
    for s in extra or []:
        if s.lower() not in low:
            fail(f"missing '{s}' in {path.name}")


# --- INDEX ---
index = ROOT / "INDEX.html"
html_ok(index, min_bytes=1500, need_kpi=False, need_tbody=True, extra=["521"])
idx = index.read_text(encoding="utf-8") if index.is_file() else ""
hrefs = re.findall(r'href="([^"]+)"', idx)
for href in hrefs:
    target = (ROOT / href).resolve()
    if not target.is_file():
        fail(f"INDEX broken link {href}")
    stats["index_links"] += 1

cmd = ROOT / "OPEN_IDS_2026_DB_Feedback_v0.4.cmd"
if not cmd.is_file():
    fail("missing OPEN cmd")
else:
    body = cmd.read_text(encoding="utf-8", errors="replace")
    if "INDEX.html" not in body:
        fail("OPEN cmd does not start INDEX.html")

# --- per market ---
for folder, n_exp in EXPECTED.items():
    d = ROOT / folder
    dealers = d / "dealers"
    rollup = d / ROLLUP[folder]
    rollup_xlsx = d / f"IDS_2026_DB_Rollup_{folder}_v0.4.xlsx"
    ws = sorted(dealers.glob("*_workshop_pack.html")) if dealers.is_dir() else []
    ex = sorted(dealers.glob("*_exec_summary.html")) if dealers.is_dir() else []
    xl = sorted(dealers.glob("*.xlsx")) if dealers.is_dir() else []
    if len(ws) != n_exp:
        fail(f"{folder} workshop={len(ws)} expected {n_exp}")
    if len(ex) != n_exp:
        fail(f"{folder} exec={len(ex)} expected {n_exp}")
    if len(xl) != n_exp:
        fail(f"{folder} xlsx={len(xl)} expected {n_exp}")
    html_ok(rollup, min_bytes=4000, need_kpi=True, need_tbody=True)
    if not rollup_xlsx.is_file():
        fail(f"missing rollup xlsx {folder}")
    extra_ws = ["section scorecard", "kaizen"]
    extra_ex = ["total score"]
    if folder == "Spain":
        extra_r = ["40 of 45", "red-marked"]
    elif folder == "France":
        extra_r = ["red-marked"]
    elif folder == "Italy":
        extra_r = ["every evaluated dealer"]
    elif folder == "Switzerland":
        extra_r = ["every evaluated dealer"]
    elif folder == "Israel_LCV":
        extra_r = []
    else:
        extra_r = []
    if extra_r:
        html_ok(rollup, min_bytes=4000, need_kpi=True, need_tbody=True, extra=extra_r)
        stats["html_checked"] -= 1  # already counted
    for p in ws:
        html_ok(p, min_bytes=2500, need_kpi=True, need_tbody=True, extra=extra_ws)
    for p in ex:
        html_ok(p, min_bytes=1500, need_kpi=True, need_tbody=True, extra=extra_ex)
    # pairing: each workshop has matching exec stem
    ws_stems = {p.name.replace("_workshop_pack.html", "") for p in ws}
    ex_stems = {p.name.replace("_exec_summary.html", "") for p in ex}
    if ws_stems != ex_stems:
        fail(f"{folder} workshop/exec stem mismatch {len(ws_stems ^ ex_stems)}")
    stats["markets"] += 1
    stats["workshop"] += len(ws)
    stats["exec"] += len(ex)
    stats["xlsx"] += len(xl)

# Israel LCV Section E
il = ROOT / "Israel_LCV" / "IDS_2026_DB_Rollup_Israel_LCV_v0.4.html"
if il.is_file():
    t = il.read_text(encoding="utf-8", errors="replace").lower()
    if "not scored" not in t and "section e" in t:
        # still ok if A-D only is stated
        if "a–d" not in t and "a-d" not in t and "not scored" not in t:
            warn("Israel LCV rollup does not say Section E not scored / A-D")

# France exclusion count
fr = ROOT / "France" / "IDS_2026_DB_Rollup_France_v0.4.html"
if fr.is_file():
    t = fr.read_text(encoding="utf-8", errors="replace")
    if "of 84" not in t and "84" in t:
        warn("France rollup: check excluded-from-average wording")

out = {
    "ok": not fails,
    "fail_count": len(fails),
    "warn_count": len(warns),
    "fails": fails,
    "warns": warns,
    "stats": dict(stats),
}
(ROOT / "_qa" / "AUDIT.json").write_text(json.dumps(out, indent=2), encoding="utf-8")
print("STATS", json.dumps(dict(stats)))
print("FAIL_COUNT", len(fails), "WARN_COUNT", len(warns))
print("OK" if not fails else "NOT_OK")
