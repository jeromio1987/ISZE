"""
ISZE — scheduled refresh + price-drift check (roadmap item 6, started 2026-07-10).

Runs the working scrapers (KS International, Tranzparts, T&M Commercials,
Mekonomen, Auto 365), snapshots the previous results before overwriting them,
compares min price per (Site, PMS_Category) [or PN for KS, which is per-PN] against
the last snapshot, flags moves past DRIFT_THRESHOLD, then rebuilds the executive
HTML dashboards.

Every run's comparison (flagged or not) is appended to _snapshots/drift_history.csv
so price moves can be read as a trend across runs, not just a single-step delta
against whatever the last run happened to be. Build the trend view with
build_drift_trend_view.py.

Deliberately excludes autodoc_scraper.py / autodoc_tld_scraper.py / oscaro_scraper.py
(Cloudflare-blocked, confirmed dead — see README.md) and mister_auto_scraper.py
(different unconfirmed failure, not worth a recurring blocked run) — no point
re-hammering sites that don't answer.

Usage:
    python refresh_and_check_drift.py
"""
from __future__ import annotations

import os
import subprocess
import sys
from datetime import datetime
from pathlib import Path

import pandas as pd

SCRIPT_DIR = Path(__file__).parent
SNAPSHOT_DIR = SCRIPT_DIR / "_snapshots"
DRIFT_HISTORY_CSV = SNAPSHOT_DIR / "drift_history.csv"
DRIFT_THRESHOLD = 0.15  # 15% move in min price triggers a flag

# Task Scheduler runs the pipeline with a cp1252 console; ks_scraper.py's emoji
# status prints crashed with UnicodeEncodeError on 2026-07-13 before scraping a
# single PN (after the reset had already removed ks_results.csv). Force UTF-8 in
# every child so a cosmetic print can never kill a scraper again.
SUBPROC_ENV = {**os.environ, "PYTHONUTF8": "1", "PYTHONIOENCODING": "utf-8"}

# (scraper script, results csv, key columns for the comparison, price col, needs_reset, timeout_s)
# needs_reset=True: this scraper uses _shared/scraper_io.py's IncrementalCsvWriter,
# which treats any PN already marked "ok"/"no_results" as permanently done -- built
# to resume an interrupted run, not to support a recurring refresh. Confirmed
# 2026-07-10: first scheduled run left mekonomen_results.csv untouched ("Nothing to
# scrape") because every PN was already marked done from a prior manual run over a
# month old -- silently produces "no drift" forever if not reset. Tranzparts/TMC/
# Auto365 use cv_category_crawler.py's write_products_csv(), which is a full
# overwrite every run (no resume state), so they don't need this.
# Mekonomen gets 5400s: Playwright + per-PN waits run ~24s/PN, so 200 PNs need
# ~4800s — the old blanket 1800s cut the 2026-07-13 run off at PN 75/200.
JOBS = [
    ("ks_scraper.py", "ks_results.csv", ["PN"], "KS_AM_MinPrice_GBP", True, 1800),
    ("tranzparts_scraper.py", "tranzparts_results.csv", ["PMS_Category"], "Price_EUR", False, 1800),
    ("tmc_scraper.py", "tmc_results.csv", ["PMS_Category"], "Price_EUR", False, 1800),
    ("mekonomen_scraper.py", "mekonomen_results.csv", ["PN"], "MEK_AM_MinPrice_SEK", True, 5400),
    ("auto365_scraper.py", "auto365_results.csv", ["PMS_Category"], "Price_EUR", False, 1800),
]


def _snapshot_existing(csv_path: Path, stamp: str) -> Path | None:
    if not csv_path.exists():
        return None
    dest_dir = SNAPSHOT_DIR / stamp
    dest_dir.mkdir(parents=True, exist_ok=True)
    dest = dest_dir / csv_path.name
    dest.write_bytes(csv_path.read_bytes())
    return dest


def _latest_prior_snapshot(csv_name: str, before_stamp: str) -> Path | None:
    if not SNAPSHOT_DIR.exists():
        return None
    stamps = sorted(p.name for p in SNAPSHOT_DIR.iterdir() if p.is_dir() and p.name < before_stamp)
    for stamp in reversed(stamps):
        cand = SNAPSHOT_DIR / stamp / csv_name
        if cand.exists():
            return cand
    return None


def _data_row_count(csv_path: Path) -> int:
    if not csv_path.exists():
        return 0
    with csv_path.open(encoding="utf-8", errors="replace") as f:
        return max(0, sum(1 for _ in f) - 1)  # minus header


def _min_price_by_key(csv_path: Path, key_cols: list[str], price_col: str) -> pd.Series:
    df = pd.read_csv(csv_path, dtype=str, low_memory=False)
    if price_col not in df.columns or not all(k in df.columns for k in key_cols):
        return pd.Series(dtype=float)
    df[price_col] = pd.to_numeric(df[price_col], errors="coerce")
    df = df.dropna(subset=[price_col])
    if df.empty:
        return pd.Series(dtype=float)
    key = df[key_cols[0]] if len(key_cols) == 1 else df[key_cols].astype(str).agg("|".join, axis=1)
    return df.groupby(key)[price_col].min()


def compare_prices(csv_name: str, csv_path: Path, prior_path: Path | None,
                    key_cols: list[str], price_col: str, stamp: str) -> list[dict]:
    """All (key, old, new) comparisons for this run — not just the ones past
    DRIFT_THRESHOLD — so drift_history.csv can be read as a trend, not a
    single-step delta against whatever the previous run happened to be."""
    new = _min_price_by_key(csv_path, key_cols, price_col)
    if new.empty:
        return []
    old = _min_price_by_key(prior_path, key_cols, price_col) if prior_path else pd.Series(dtype=float)
    rows = []
    for k in new.index:
        n = new[k]
        o = old.get(k)
        change = (n - o) / o if (o is not None and o > 0) else None
        rows.append({
            "run_date": stamp,
            "source": csv_name,
            "key": k,
            "old_price_eur": o,
            "new_price_eur": n,
            "change_pct": change,
            "flagged": bool(change is not None and abs(change) >= DRIFT_THRESHOLD),
        })
    return rows


def append_drift_history(rows: list[dict]) -> None:
    if not rows:
        return
    df = pd.DataFrame(rows)
    SNAPSHOT_DIR.mkdir(parents=True, exist_ok=True)
    if DRIFT_HISTORY_CSV.exists():
        df.to_csv(DRIFT_HISTORY_CSV, mode="a", header=False, index=False)
    else:
        df.to_csv(DRIFT_HISTORY_CSV, mode="w", header=True, index=False)


def main():
    stamp = datetime.now().strftime("%Y-%m-%d")
    print("=" * 60)
    print(f"  ISZE scraper refresh + drift check — {stamp}")
    print("=" * 60)

    prior_paths: dict[str, Path | None] = {}
    for _, csv_name, _, _, _, _ in JOBS:
        csv_path = SCRIPT_DIR / csv_name
        _snapshot_existing(csv_path, stamp)
        prior_paths[csv_name] = _latest_prior_snapshot(csv_name, stamp)

    for script, csv_name, _, _, needs_reset, timeout_s in JOBS:
        print(f"\n--- {script} ---")
        csv_path = SCRIPT_DIR / csv_name
        # Non-destructive reset: the incremental writer would otherwise skip
        # everything as already-done, but a plain delete lost ks_results.csv on
        # 2026-07-13 when the scraper crashed at startup. Park the old file as a
        # .bak and only drop it once the new run actually produced rows.
        backup_path = None
        if needs_reset and csv_path.exists():
            backup_path = csv_path.with_name(csv_name + ".pre_reset.bak")
            if backup_path.exists():
                backup_path.unlink()
            csv_path.rename(backup_path)
            print(f"  (reset {csv_name} — previous results kept at {backup_path.name} until this run succeeds)")
        try:
            subprocess.run(
                [sys.executable, str(SCRIPT_DIR / script)],
                cwd=SCRIPT_DIR, check=False, timeout=timeout_s, env=SUBPROC_ENV,
            )
        except Exception as e:
            print(f"  !! failed to run {script}: {e}")
        if backup_path:
            if _data_row_count(csv_path) > 0:
                backup_path.unlink()
            else:
                if csv_path.exists():
                    csv_path.unlink()  # header-only / empty file from the failed run
                backup_path.rename(csv_path)
                print(f"  !! {script} produced no rows — restored previous {csv_name} from backup")

    print("\n" + "=" * 60)
    print("  Price drift since last run (>= {:.0%} move)".format(DRIFT_THRESHOLD))
    print("=" * 60)
    any_drift = False
    history_rows: list[dict] = []
    for _, csv_name, key_cols, price_col, _, _ in JOBS:
        csv_path = SCRIPT_DIR / csv_name
        prior = prior_paths.get(csv_name)
        if not csv_path.exists():
            print(f"  {csv_name}: no results this run, skipping")
            continue
        rows = compare_prices(csv_name, csv_path, prior, key_cols, price_col, stamp)
        history_rows.extend(rows)
        if not prior:
            print(f"  {csv_name}: no prior snapshot to compare (first run) — logged {len(rows)} rows to history")
            continue
        flagged = [r for r in rows if r["flagged"]]
        if flagged:
            any_drift = True
            print(f"  {csv_name}:")
            for r in flagged:
                direction = "up" if r["change_pct"] > 0 else "down"
                print(f"    {r['key']}: {r['old_price_eur']:.2f} -> {r['new_price_eur']:.2f} "
                      f"({r['change_pct']:+.0%}, {direction})")
        else:
            print(f"  {csv_name}: no moves >= {DRIFT_THRESHOLD:.0%}")
    append_drift_history(history_rows)
    print(f"\n  Logged {len(history_rows)} price points to {DRIFT_HISTORY_CSV}")
    if not any_drift:
        print("\n  No significant drift detected.")

    print("\n--- rebuilding executive dashboards ---")
    subprocess.run(
        [sys.executable, str(SCRIPT_DIR / "build_executive_dashboard.py"), "--variant", "all"],
        cwd=SCRIPT_DIR, check=False, env=SUBPROC_ENV,
    )

    print("\n--- rebuilding drift trend view ---")
    subprocess.run(
        [sys.executable, str(SCRIPT_DIR / "build_drift_trend_view.py")],
        cwd=SCRIPT_DIR, check=False, env=SUBPROC_ENV,
    )

    print("\n--- rebuilding PMS x IAM bridge (internal, unaudited) ---")
    subprocess.run(
        [sys.executable, str(SCRIPT_DIR / "build_pms_iam_bridge.py")],
        cwd=SCRIPT_DIR, check=False, env=SUBPROC_ENV,
    )

    print("\nDone.")


if __name__ == "__main__":
    main()
