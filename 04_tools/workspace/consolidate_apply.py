"""Apply Jerome's 2026-08-13 follow-up: delete proven doubles, regenerate
manifest, merge unique leftovers, drop the rest.

Does not touch 07_deploy/ or .claude/worktrees/.
Does not open raw sales XLSX.
"""
from __future__ import annotations

import csv
import hashlib
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

WORKSPACE = Path(r"C:\Users\jerom\Desktop\claude")
ISZE = WORKSPACE / "ISZE"
DATA01 = ISZE / "01_data"
DASH = ISZE / "02_dashboards"
DATA_MIRROR = DASH / "Data"
QUAR = WORKSPACE / "_quarantine" / "2026-08-13"
PLAN = ISZE / "04_tools" / "workspace" / "consolidate_plan.csv"
MYPENS = WORKSPACE / "Projects" / "mypens"

SKIP_DIR = {
    "node_modules", ".next", ".git", ".vercel", "dist", "coverage",
    "__pycache__", ".turbo", "out",
}
SKIP_FILE = {".env", ".env.local", ".env.production"}


def sha256(p: Path) -> str:
    h = hashlib.sha256()
    with p.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def ensure_dir(p: Path) -> None:
    p.mkdir(parents=True, exist_ok=True)


def copy_unique(src: Path, dest: Path) -> str:
    if dest.exists():
        return "exists"
    ensure_dir(dest.parent)
    shutil.copy2(src, dest)
    return "copied"


def win_junction(link: Path, target: Path) -> None:
    if link.exists() or link.is_symlink():
        if link.is_dir() and not link.is_symlink():
            # real directory — caller must have emptied/removed it
            raise SystemExit(f"junction dest is a real dir: {link}")
        link.unlink()
    cmd = ["cmd", "/c", "mklink", "/J", str(link), str(target)]
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode != 0:
        raise SystemExit(f"mklink failed: {r.stdout} {r.stderr}")
    print(f"  junction {link} -> {target}")


def rmtree(p: Path) -> None:
    def onerr(fn, path, exc):
        try:
            os.chmod(path, 0o700)
            fn(path)
        except Exception:
            pass
    shutil.rmtree(p, onerror=onerr)


def step_delete_quarantine() -> None:
    print("=== delete verified doubles (quarantine) ===")
    if not PLAN.exists():
        raise SystemExit("plan csv missing")
    keepers_ok = 0
    missing = []
    with PLAN.open(encoding="utf-8") as f:
        for row in csv.DictReader(f):
            if row["action"] != "quarantine":
                continue
            keeper = WORKSPACE / Path(*row["keeper_path"].split("/"))
            if not keeper.exists():
                missing.append(row["keeper_path"])
            else:
                keepers_ok += 1
    if missing:
        print("ABORT: keepers missing, not deleting quarantine:")
        for m in missing[:20]:
            print(" ", m)
        raise SystemExit(1)
    print(f"  {keepers_ok} keepers still present")
    if QUAR.exists():
        n = sum(1 for p in QUAR.rglob("*") if p.is_file())
        rmtree(QUAR)
        # remove empty date dir parent if empty
        parent = QUAR.parent
        if parent.exists() and not any(parent.iterdir()):
            parent.rmdir()
        print(f"  deleted quarantine ({n} files)")
    else:
        print("  quarantine already gone")

    cy = ISZE / "09_meetings" / "PMS_BVP_Regain_2026" / "PMS_BVP_Regain_CY2025.html"
    keep = ISZE / "09_meetings" / "PMS_BVP_Regain_2026" / "PMS_BVP_Regain.html"
    if cy.exists() and keep.exists() and sha256(cy) == sha256(keep):
        cy.unlink()
        print("  deleted PMS_BVP_Regain_CY2025.html (identical to PMS_BVP_Regain.html)")


def step_manifest() -> None:
    print("=== regenerate manifest.yaml from disk ===")
    skip = {"_archive", "_build", "Data", "_ui", "propertiq-assets", "_composable"}
    labels = {
        "hub": "Entry points and navigation",
        "sales": "AIM, competitiveness, sell-out, monthly sales, SPA",
        "pricing": "Pricing engine, live, history, proposals",
        "fleet": "UIO, ZEV, plan tracker, year-end, GPS canonical",
        "gps": "GPS stubs + kickback (canonical GPS lives in fleet/)",
        "ids": "IDS 2026 dealer evaluation",
        "ops": "Tender, AI tools, legal map",
        "md_pack": "MD pack",
        "side": "Non-ISZE (PROPERTIQ)",
        "_working": "Working / scratch",
        "_composable": "Composable master dashboard (source; deliverable is dist/)",
    }
    files: dict[str, list[str]] = {}
    stubs: list[str] = []
    for child in sorted(DASH.iterdir()):
        if not child.is_dir() or child.name in skip or child.name.startswith("since_"):
            continue
        htmls = sorted(p for p in child.glob("*.html") if p.is_file())
        if not htmls:
            continue
        live = []
        for p in htmls:
            head = p.read_text(encoding="utf-8", errors="replace")[:1200]
            if p.stat().st_size < 4096 and "http-equiv" in head.lower() and "refresh" in head.lower():
                stubs.append(f"{child.name}/{p.name}")
            else:
                live.append(p.name)
        if live:
            files[child.name] = live
    lines = [
        "# ISZE HTML dashboard layout — regenerated from disk 2026-08-13",
        "# Deploy is flat via sync_to_deploys.ps1 (does not read this file for the copy list).",
        "# Stubs are listed separately; they are not dashboards.",
        "",
        "version: 2",
        "",
        "folders:",
    ]
    for folder, names in files.items():
        lines.append(f"  {folder}: {labels.get(folder, folder)}")
    lines.append("")
    lines.append("files:")
    for folder, names in files.items():
        lines.append(f"  {folder}:")
        for n in names:
            lines.append(f"    - {n}")
    lines.append("")
    lines.append("stubs:")
    for s in stubs:
        lines.append(f"  - {s}")
    lines += [
        "",
        "deploy:",
        "  flatten_on_sync: true",
        "  skip_dirs:",
        "    - _archive",
        "    - _build",
        "    - Data",
        "",
    ]
    out = DASH / "manifest.yaml"
    out.write_text("\n".join(lines), encoding="utf-8")
    nfiles = sum(len(v) for v in files.values())
    print(f"  wrote {out} ({nfiles} live, {len(stubs)} stubs, {len(files)} folders)")


def step_restore_dashboards_alias() -> None:
    print("=== restore 01_data/dashboards -> 14_dashboards ===")
    link = DATA01 / "dashboards"
    target = DATA01 / "14_dashboards"
    if not target.is_dir():
        raise SystemExit("14_dashboards missing")
    if link.exists() or link.is_symlink():
        print("  already present")
        return
    win_junction(link, target)


def step_merge_data_mirror() -> None:
    print("=== merge unique 02_dashboards/Data into 01_data, then junction ===")
    if not DATA_MIRROR.exists():
        print("  Data/ already gone — creating junction")
        win_junction(DATA_MIRROR, DATA01)
        return
    if DATA_MIRROR.is_symlink() or DATA_MIRROR.is_junction():
        print("  Data/ is already a junction — leave it")
        return
    copied = skipped = 0
    for src in DATA_MIRROR.rglob("*"):
        if not src.is_file():
            continue
        rel = src.relative_to(DATA_MIRROR)
        dest = DATA01 / rel
        if dest.exists():
            skipped += 1
            continue
        ensure_dir(dest.parent)
        shutil.copy2(src, dest)
        copied += 1
    print(f"  copied {copied} unique files into 01_data; skipped {skipped} (01_data already had them)")
    print("  removing Data/ mirror…")
    rmtree(DATA_MIRROR)
    win_junction(DATA_MIRROR, DATA01)
    probe = DATA_MIRROR / "dashboards" / "isze_data.json"
    alt = DATA_MIRROR / "14_dashboards" / "isze_data.json"
    if probe.exists() or alt.exists():
        print("  hub ../Data/dashboards/ (or 14_dashboards) reachable via junction")
    else:
        print("  WARN: isze_data.json not visible via Data junction — check 14_dashboards")


def should_skip_dir(name: str) -> bool:
    return name in SKIP_DIR or name == "build" and False


def walk_source(root: Path):
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [d for d in dirnames if d not in SKIP_DIR and d != ".git"]
        # skip android intermediates
        if f"{os.sep}android{os.sep}app{os.sep}build" in dirpath or dirpath.endswith(f"{os.sep}android{os.sep}app{os.sep}build"):
            dirnames[:] = []
            continue
        for fn in filenames:
            if fn in SKIP_FILE:
                continue
            yield Path(dirpath) / fn


def step_mypens() -> None:
    print("=== myPENS: keep Projects/mypens; merge unique; delete forks ===")
    if not MYPENS.is_dir():
        raise SystemExit("canonical mypens missing")
    forks = [
        (WORKSPACE / "Projects" / "mypens-feedback-test", "mypens-feedback-test"),
        (WORKSPACE / "Projects" / "mypens-region-deploy", "mypens-region-deploy"),
        (WORKSPACE / "my-pens-app", "my-pens-app"),
    ]
    private = WORKSPACE / "Private"
    for src_root, label in forks:
        if not src_root.exists():
            print(f"  {label}: already gone")
            continue
        copied = 0
        for src in walk_source(src_root):
            rel = src.relative_to(src_root)
            parts = rel.parts
            # Personal dump inside my-pens-app
            if parts and parts[0] == "Private":
                dest = private / Path(*parts[1:])
            elif parts and parts[0] == "waaslandia-coolify-test":
                dest = WORKSPACE / "Projects" / "waaslandia-coolify-test" / Path(*parts[1:])
            else:
                dest = MYPENS / "_from_forks" / label / rel
            # if the same relative path already lives in canonical mypens, skip
            canon = MYPENS / rel
            if parts and parts[0] not in {"Private", "waaslandia-coolify-test"} and canon.exists():
                continue
            if dest.exists():
                continue
            ensure_dir(dest.parent)
            try:
                shutil.copy2(src, dest)
                copied += 1
            except OSError as e:
                print(f"  skip copy {src}: {e}")
        print(f"  {label}: merged {copied} unique files")
        print(f"  deleting {src_root} …")
        rmtree(src_root)
        print(f"  deleted {label}")


def patch_bvp_builder() -> None:
    p = ISZE / "09_meetings" / "PMS_BVP_Regain_2026" / "_build_dashboard.py"
    text = p.read_text(encoding="utf-8")
    old = '''    out = OUT_DIR / "PMS_BVP_Regain_CY2025.html"
    # Keep stable filename Jerome already has open; also write period-neutral alias
    out.write_text(html, encoding="utf-8")
    alias = OUT_DIR / "PMS_BVP_Regain.html"
    alias.write_text(html, encoding="utf-8")
    return out'''
    new = '''    out = OUT_DIR / "PMS_BVP_Regain.html"
    out.write_text(html, encoding="utf-8")
    return out'''
    if old in text:
        p.write_text(text.replace(old, new), encoding="utf-8")
        print("  patched _build_dashboard.py to write only PMS_BVP_Regain.html")
    p2 = ISZE / "09_meetings" / "PMS_BVP_Regain_2026" / "_build_report.py"
    if p2.exists():
        t2 = p2.read_text(encoding="utf-8")
        t2n = t2.replace(
            'html_path = OUT_DIR / "PMS_BVP_Regain_CY2025.html"',
            'html_path = OUT_DIR / "PMS_BVP_Regain.html"',
        )
        if t2n != t2:
            p2.write_text(t2n, encoding="utf-8")
            print("  patched _build_report.py")


def main() -> None:
    step_delete_quarantine()
    patch_bvp_builder()
    step_manifest()
    step_restore_dashboards_alias()
    step_merge_data_mirror()
    step_mypens()
    print("=== done ===")


if __name__ == "__main__":
    main()
