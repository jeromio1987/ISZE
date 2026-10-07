# -*- coding: utf-8 -*-
"""U26 / agent E -- write the correct page_manifest rows and the page->queried-number
sidecar for the pages the eight agents saved, then leave the manifest to the bridge.

The first pass of `_u26_e_merge.py` appended 96 rows that pointed at pages in the
shared _probe root. The bridge resolves `page_file` relative to the hidden
`.scrape_cache` root (:PROBE = .scrape_cache), so those rows produced 80 "no parser
registered" / "saved page missing" page failures. This script removes that block and
appends rows that point at the real on-disk relative paths:

    _u26/<ID>/pages/<name>          A1 (ks) and C1 (spareto) pages, one per row
    _u26/<ID>/pages/<name>          A2 pages: cat_*.html -> tmc, product_*.html -> tranzparts

The queried-number sidecar `_u26_e_page_query.csv` carries, for each Tranzparts page,
the Isuzu number the shop was searched for. The page must print that number (site
parser `site_tranzparts` refuses anything else), and the community search URL does not
carry it -- it is in each agent row's `description`, written there by the agent that
observed it. Nothing is inferred: a row whose description carries no seeded number is
left out of the sidecar, and its page then emits no row.
"""
from __future__ import annotations

import csv
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

for _s in (sys.stdout, sys.stderr):
    if _s is not None and hasattr(_s, "reconfigure"):
        try:
            _s.reconfigure(encoding="utf-8", errors="replace")
        except Exception:
            pass

HERE = Path(__file__).resolve().parent            # 04_tools/price_ledger
ROOT = Path(__file__).resolve().parents[2]
PROBE = ROOT / "01_data" / "90_INBOX" / "scrape_targets" / "_probe"
U26 = PROBE / "_u26"
MANIFEST = HERE / "page_manifest.csv"
SIDECAR = HERE / "_u26_e_page_query.csv"

AGENTS = ["A1", "A2", "C1"]
E_NOTE_TOKEN = "agent E"


def load_rows(folder: Path) -> list[dict]:
    p = folder / "rows.csv"
    if not p.exists():
        return []
    with p.open(encoding="utf-8", newline="") as fh:
        return [r for r in csv.DictReader(fh)]


def site_for(agent: str, page_name: str) -> str:
    if agent == "A1":
        return "ks"
    if agent == "C1":
        return "spareto"
    return "tmc" if page_name.startswith("cat_") else "tranzparts"


def queried_pn_for(desc: str) -> str:
    """The 10-digit number the shop was searched for, from the agent's own description."""
    m = re.search(r"the number we searched for is printed on this product page", desc or "")
    if m:
        found = re.findall(r"\b(\d{10})\b", desc)
        if found:
            return found[0]
    return ""


def main() -> int:
    log: dict = {"generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds")}

    # --- 1. remove the previous (wrong-path) block ---------------------------
    lines = MANIFEST.read_text(encoding="utf-8").splitlines()
    kept = [ln for ln in lines if E_NOTE_TOKEN not in ln]
    log["manifest_rows_removed"] = len(lines) - len(kept)

    # --- 2. build the correct rows ------------------------------------------
    add: list[dict] = []
    sidecar: list[dict] = []
    per_site: dict[str, int] = {}
    for agent in AGENTS:
        folder = U26 / agent
        rows = load_rows(folder)
        seen: set[str] = set()
        for r in rows:
            pname = (r.get("page_file") or "").strip()
            if not pname or pname in seen:
                continue
            seen.add(pname)
            site = site_for(agent, Path(pname).name)
            rel = f"_u26/{agent}/pages/{Path(pname).name}"
            if not (PROBE / rel).exists():
                log.setdefault("missing_pages", []).append(rel)
                continue
            add.append({
                "site": site,
                "source_url": (r.get("source_url") or "").strip(),
                "page_file": rel,
                "fetched_at": (r.get("observed_at") or "2026-10-07").strip(),
                "note": f"{E_NOTE_TOKEN}: U26 {site} page promoted to _u26/{agent}/pages/; "
                        f"parsed by build_scraped_observations.py",
            })
            per_site[site] = per_site.get(site, 0) + 1
            if site == "tranzparts":
                q = ""
                if "the number we searched for is printed on this product page" in (
                        r.get("description") or ""):
                    pn = (r.get("part_no") or "").strip()
                    if re.fullmatch(r"\d{10}", pn):
                        q = pn
                if q:
                    sidecar.append({"page_file": rel, "queried_pn": q,
                                    "source_url": (r.get("source_url") or "").strip()})
                else:
                    log.setdefault("tranzparts_pages_without_a_seeded_number", []).append(rel)

    # a page can carry several rows; keep one manifest row per page
    dedup: list[dict] = []
    seen_pages: set[str] = set()
    for m in add:
        if m["page_file"] in seen_pages:
            continue
        seen_pages.add(m["page_file"])
        dedup.append(m)

    with MANIFEST.open("w", encoding="utf-8", newline="") as fh:
        fh.write("\n".join(kept) + "\n")
        w = csv.DictWriter(fh, fieldnames=["site", "source_url", "page_file",
                                           "fetched_at", "note"])
        for m in dedup:
            w.writerow(m)

    with SIDECAR.open("w", encoding="utf-8", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=["page_file", "queried_pn", "source_url"])
        w.writeheader()
        for s in sidecar:
            w.writerow(s)

    log["manifest_rows_appended"] = len(dedup)
    log["manifest_rows_by_site"] = per_site
    log["sidecar_rows"] = len(sidecar)
    (HERE / "_u26_e_manifest_log.json").write_text(json.dumps(log, indent=2), encoding="utf-8")
    print(json.dumps(log, indent=2))
    print("WROTE", MANIFEST)
    print("WROTE", SIDECAR)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
