#!/usr/bin/env python3
"""Loop C  -  A-lite story compiler from Sales Review _summary.json.

Writes Mode B internal spine + optional Mode A brief (no IML v7 / Model B nicknames).

CLI:
  python story_compiler.py --dbs NORWAY
  python story_compiler.py --dbs NORWAY,ICELAND --mode-a-brief
  python story_compiler.py --dbs NORWAY --verify-only

Exit:
  0 = OK / VERIFY_OK
  1 = HOLD (missing summary / invent-block) or VERIFY_FAIL
  3 = bad args
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from datetime import datetime
from pathlib import Path

ISZE = Path(__file__).resolve().parents[4]
MEETINGS = ISZE / "09_meetings"

REQUIRED_SECTIONS = ("VERDICT", "ONE_FIGHT", "ONE_ASK")
MAX_SLIDES = 10

SHELL_HINTS = ("shell", "lubricant", "lube", "oil filter", "5500")


def _eur(n: float | int | None) -> str:
    if n is None:
        return "n/a"
    try:
        v = float(n)
    except (TypeError, ValueError):
        return "n/a"
    sign = "-" if v < 0 else ""
    v = abs(v)
    if v >= 1_000_000:
        return f"{sign}€{v/1_000_000:.2f}M"
    if v >= 1_000:
        return f"{sign}€{v/1_000:.0f}K"
    return f"{sign}€{v:.0f}"


def _pct(x: float | None) -> str:
    if x is None:
        return "n/a"
    return f"{x*100:+.1f}%"


def _meeting_dir(db: str) -> Path:
    return MEETINGS / f"{db.upper()}_Sales_Review_2026"


def _load_summary(db: str) -> dict | None:
    p = _meeting_dir(db) / "_summary.json"
    if not p.is_file():
        return None
    return json.loads(p.read_text(encoding="utf-8"))


def _pick_fight(summary: dict) -> dict:
    """One fight: largest |EUR| category decline, else top decl PN."""
    cats = summary.get("categories") or []
    decl_cats = [c for c in cats if (c.get("d") or 0) < 0]
    decl_cats.sort(key=lambda c: c.get("d") or 0)  # most negative first
    top_pn = (summary.get("top_decl_pn") or [None])[0]
    if decl_cats and abs(decl_cats[0].get("d") or 0) >= abs((top_pn or {}).get("d") or 0):
        c = decl_cats[0]
        return {
            "kind": "category",
            "label": c.get("cat"),
            "d": c.get("d"),
            "dp": c.get("dp"),
            "prior": c.get("prior"),
            "current": c.get("current"),
            "detail": f"{c.get('cat')}: {_eur(c.get('prior'))} → {_eur(c.get('current'))} ({_eur(c.get('d'))}, {_pct(c.get('dp'))})",
        }
    if top_pn:
        return {
            "kind": "pn",
            "label": f"{top_pn.get('pn')} {top_pn.get('desc')}",
            "d": top_pn.get("d"),
            "dp": None,
            "prior": top_pn.get("prior"),
            "current": top_pn.get("current"),
            "detail": (
                f"PN {top_pn.get('pn')} ({top_pn.get('desc')}, {top_pn.get('cat')}): "
                f"{_eur(top_pn.get('prior'))} → {_eur(top_pn.get('current'))} ({_eur(top_pn.get('d'))})"
            ),
        }
    return {
        "kind": "none",
        "label": "no mover",
        "d": None,
        "detail": "No category/PN decline in summary  -  check analysis rebuild.",
    }


def _shell_note(summary: dict) -> str | None:
    notes: list[str] = []
    for c in summary.get("categories") or []:
        cat = str(c.get("cat") or "")
        if any(h in cat.lower() for h in ("consumable", "oil", "lube")):
            if abs(c.get("d") or 0) >= 500:
                notes.append(f"{cat}: {_eur(c.get('d'))}")
    # PN descriptions with Shell / 5500*
    for row in (summary.get("top_grow_pn") or []) + (summary.get("top_decl_pn") or []):
        blob = f"{row.get('pn','')} {row.get('desc','')} {row.get('cat','')}".lower()
        if any(h in blob for h in SHELL_HINTS) or str(row.get("pn", "")).startswith("5500"):
            notes.append(
                f"PN {row.get('pn')} {row.get('desc')}: {_eur(row.get('d'))}"
            )
    if not notes:
        wclaim = summary.get("warranty_claim")
        if wclaim:
            return f"No Shell/lube fight flagged; warranty CY2025 claim-price {_eur(wclaim)} on file."
        return None
    return "; ".join(notes[:3])


def _pbi_block(summary: dict) -> tuple[str, bool]:
    """Return (text, has_official_cut)."""
    pbi = summary.get("pbi")
    if not pbi or not pbi.get("sales"):
        return (
            "Official Power BI cut: NOT in _summary (profile may also be null). "
            "Do not lead Mode A with SAP commercial boom until PBI is entered.",
            False,
        )
    sales = pbi.get("sales") or []
    prev = pbi.get("prev_year") or []
    bp = pbi.get("original_bp") or []
    months = pbi.get("months") or []
    total_s = sum(float(x) for x in sales)
    total_p = sum(float(x) for x in prev) if prev else None
    total_bp = sum(float(x) for x in bp) if bp else None
    yoy = None
    if total_p:
        yoy = total_s / total_p - 1
    gap_bp = None
    if total_bp is not None:
        gap_bp = total_s - total_bp
    lines = [
        f"Official cut ({pbi.get('quarter') or 'PBI'}): months {', '.join(months) or 'n/a'}",
        f"  Sales total {_eur(total_s)}"
        + (f" vs prev-year {_eur(total_p)} ({_pct(yoy)})" if total_p is not None else ""),
    ]
    if gap_bp is not None:
        lines.append(f"  vs original BP {_eur(total_bp)} → gap {_eur(gap_bp)}")
    src = pbi.get("source")
    if src:
        lines.append(f"  Source: {src}")
    return "\n".join(lines), True


def _ext_target_line(summary: dict) -> str:
    fy = summary.get("fy27") or {}
    ext = (fy.get("ext_target") or {}).get("fy27")
    gps = (fy.get("gps") or {}).get("fy27")
    if ext is None:
        return "EXT TARGET (FY27 V3.1 col I): not in summary  -  confirm before Mode A ask."
    return f"EXT TARGET FY27: {_eur(ext)}" + (f" (GPS FY27 {_pct(gps) if gps is not None else 'n/a'})" if gps is not None else "")


def _verdict_line(summary: dict, has_pbi: bool, fight: dict) -> str:
    name = summary.get("display") or summary.get("db")
    comm = summary.get("commercial_delta_pct")
    gross = summary.get("gross_delta_pct")
    if has_pbi:
        return (
            f"{name}: lead with official Power BI cut; commercial SAP H1 "
            f"{_pct(comm)} / gross {_pct(gross)}; one fight = {fight.get('label')}."
        )
    return (
        f"{name}: PBI missing  -  HOLD Mode A to colleagues on official cut; "
        f"SAP commercial H1 {_pct(comm)}; fight draft = {fight.get('label')} (internal only)."
    )


def _one_ask(summary: dict, has_pbi: bool, fight: dict) -> str:
    name = summary.get("display") or summary.get("db")
    if not has_pbi:
        return (
            f"Ask Koen: confirm / supply Power BI monthly sales for {name} "
            f"before we treat SAP H1 as the Mode A headline."
        )
    return (
        f"Ask Koen: agree the one fight on {fight.get('label')} "
        f"({fight.get('detail')}) and confirm EXT TARGET ask for FY27."
    )


def _slide_rec(has_pbi: bool, shell: str | None) -> list[str]:
    slides = [
        "1. Cover / DB context",
        "2. Official Power BI cut (or amber: PBI missing)",
        "3. YoY / BP gap",
        "4. One fight (category or PN)",
        "5. Warranty / Shell callout" if shell else "5. Warranty strip note",
        "6. EXT TARGET / FY27 ask",
        "7. One ask for Koen",
        "8. Appendix pointer (full movers offline)",
    ]
    # Always ≤10
    assert len(slides) <= MAX_SLIDES
    return slides


def compile_story(db: str, *, mode_a_brief: bool = True) -> dict:
    db_u = db.upper()
    summary = _load_summary(db_u)
    if summary is None:
        return {
            "rc": 1,
            "db": db_u,
            "verdict": "HOLD",
            "reason": f"missing _summary.json under {_meeting_dir(db_u)}  -  do not invent numbers",
            "paths": {},
        }

    fight = _pick_fight(summary)
    pbi_text, has_pbi = _pbi_block(summary)
    shell = _shell_note(summary)
    ext = _ext_target_line(summary)
    verdict = _verdict_line(summary, has_pbi, fight)
    ask = _one_ask(summary, has_pbi, fight)
    slides = _slide_rec(has_pbi, shell)
    ts = datetime.now().astimezone().isoformat(timespec="seconds")

    story = f"""# A-lite story  -  {summary.get('display') or db_u} (Mode B internal)

Generated: {ts}
Source: `_summary.json` · window {summary.get('label_prior')} → {summary.get('label_current')}
Slide count recommendation: {len(slides)} (max {MAX_SLIDES})

## VERDICT

{verdict}

## BEATS

### 1. Official cut (PBI)

{pbi_text}

### 2. YoY / BP gap

- Commercial SAP: {_eur(summary.get('commercial_prior'))} → {_eur(summary.get('commercial_current'))} ({_pct(summary.get('commercial_delta_pct'))})
- Gross SAP: {_eur(summary.get('gross_prior'))} → {_eur(summary.get('gross_current'))} ({_pct(summary.get('gross_delta_pct'))})
- Net SAP: {_eur(summary.get('net_prior'))} → {_eur(summary.get('net_current'))} ({_pct(summary.get('net_delta_pct'))})

### 3. ONE_FIGHT

{fight['detail']}

### 4. Warranty / Shell

- Warranty claim CY2025 (claim-price): {_eur(summary.get('warranty_claim'))}
- Note: {summary.get('warranty_note') or 'n/a'}
- Shell / lube: {shell or 'none flagged in top movers'}

### 5. EXT TARGET ask

{ext}

### 6. ONE_ASK

{ask}

## SLIDE_PLAN (≤{MAX_SLIDES})

{chr(10).join(f'- {s}' for s in slides)}

## WATCH

{chr(10).join(f'- {w}' for w in (summary.get('watch') or [])) or '- (none)'}

## ONE_FIGHT

{fight['detail']}

## ONE_ASK

{ask}
"""

    out_dir = _meeting_dir(db_u)
    out_dir.mkdir(parents=True, exist_ok=True)
    story_path = out_dir / "A_LITE_STORY.md"
    story_path.write_text(story, encoding="utf-8")
    paths = {"story": str(story_path)}

    if mode_a_brief:
        # Mode A language  -  no IML v7 / Model B / agent slang
        lube_line = (
            f"Lubricants signal: {shell}"
            if shell
            else "No separate lubricants callout in top movers."
        )
        brief = f"""# Sales Review brief  -  {summary.get('display') or db_u}

Audience: external / shared deck (distributor in the room).
Generated: {ts}
Recommended slides: {len(slides)} (keep ≤{MAX_SLIDES})

## VERDICT

{verdict}

## Official sales cut

{pbi_text}

## Performance gap

Commercial billing H1 moved {_pct(summary.get('commercial_delta_pct'))} ({_eur(summary.get('commercial_prior'))} → {_eur(summary.get('commercial_current'))}).

## ONE_FIGHT

Focus discussion on: {fight['detail']}

## Warranty note

Claim-price warranty CY2025: {_eur(summary.get('warranty_claim'))}.
{lube_line}

## EXT TARGET

{ext}

## ONE_ASK

{ask}
"""
        brief_path = out_dir / "A_LITE_BRIEF.md"
        brief_path.write_text(brief, encoding="utf-8")
        paths["brief"] = str(brief_path)

    verify = verify_outputs(db_u)
    return {
        "rc": 0 if verify["ok"] else 1,
        "db": db_u,
        "verdict": "OK" if verify["ok"] else "VERIFY_FAIL",
        "has_pbi": has_pbi,
        "fight": fight,
        "slide_count": len(slides),
        "paths": paths,
        "verify": verify,
    }


def verify_outputs(db: str) -> dict:
    db_u = db.upper()
    story = _meeting_dir(db_u) / "A_LITE_STORY.md"
    issues: list[str] = []
    if not story.is_file():
        return {"ok": False, "issues": [f"missing {story}"]}
    text = story.read_text(encoding="utf-8")
    for sec in REQUIRED_SECTIONS:
        if sec not in text:
            issues.append(f"missing section {sec}")
    m = re.search(r"Slide count recommendation:\s*(\d+)", text)
    if m and int(m.group(1)) > MAX_SLIDES:
        issues.append(f"slide recommendation {m.group(1)} > {MAX_SLIDES}")
    return {"ok": len(issues) == 0, "issues": issues, "path": str(story)}


def main() -> int:
    ap = argparse.ArgumentParser(description="A-lite story compiler (Loop C)")
    ap.add_argument("--dbs", required=True, help="Comma DB keys")
    ap.add_argument("--mode-a-brief", action="store_true", default=True)
    ap.add_argument("--no-mode-a-brief", action="store_true")
    ap.add_argument("--verify-only", action="store_true")
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args()
    dbs = [d.strip().upper() for d in args.dbs.split(",") if d.strip()]
    if not dbs:
        print("HOLD  -  no --dbs", file=sys.stderr)
        return 3

    mode_a = not args.no_mode_a_brief
    results = []
    rc = 0
    for db in dbs:
        if args.verify_only:
            v = verify_outputs(db)
            results.append({"db": db, "verify": v, "rc": 0 if v["ok"] else 1})
            if not v["ok"]:
                rc = 1
                print(f"{db}: VERIFY_FAIL {v['issues']}")
            else:
                print(f"{db}: VERIFY_OK {v['path']}")
            continue
        r = compile_story(db, mode_a_brief=mode_a)
        results.append(r)
        if r["rc"] != 0:
            rc = 1
        if r.get("reason"):
            print(f"{db}: HOLD  -  {r['reason']}")
        else:
            print(f"{db}: {r['verdict']} slides={r.get('slide_count')} fight={ (r.get('fight') or {}).get('label') }")
            for k, p in (r.get("paths") or {}).items():
                print(f"  {k}: {p}")
            if not (r.get("verify") or {}).get("ok"):
                print(f"  verify issues: {(r.get('verify') or {}).get('issues')}")

    if args.json:
        print(json.dumps(results, ensure_ascii=False, indent=2, default=str))
    return rc


if __name__ == "__main__":
    raise SystemExit(main())
