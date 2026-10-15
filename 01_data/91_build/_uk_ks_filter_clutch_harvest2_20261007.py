# -*- coding: utf-8 -*-
"""KS Isuzu-PN harvest2 — next ~12 filter/clutch PNs never tried in 8-PN pilots.

Accept exact_oem only when the searched Isuzu PN is printed on the card.
Wire VAT excl + £10 for filter/clutch accepts. Rebuild --also-uk-exact.
"""
from __future__ import annotations

import csv
import hashlib
import json
import re
import shutil
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

import pandas as pd

ROOT = Path(r"C:\Users\jerom\Desktop\claude\ISZE")
WT = Path(r"C:\Users\jerom\Desktop\claude\_worktrees\ISZE_u29b")
sys.path.insert(0, str(ROOT / "04_tools" / "delegation" / "parsers"))
from ledger_schema import COLUMNS, find_pns, issue_obs_id  # noqa: E402
from site_ks import ParseError, parse  # noqa: E402

OUT = ROOT / "01_data" / "90_INBOX" / "_uk_ks_filter_clutch_harvest2_20261007"
OUT.mkdir(parents=True, exist_ok=True)

CLOSED_PILOT_PNS = {
    "5876150170",
    "1876100934",
    "1876101132",
    "8975488420",
    "8975425390",
    "8982120690",
    "8975056801",
    "8978279610",
}

FILTER_CLUTCH_FAMS = {
    "fuel_filter",
    "air_filter",
    "blower_filter",
    "oil_filter",
    "cabin_filter",
    "clutch_disc",
    "clutch_pressure_plate",
}

UA = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
)
OBSERVED = "2026-10-07"
SLEEP_S = 0.7
DELIVERY_NOTE = (
    'KS Delivery Information: "There is a minimum charge of UK Pounds £10.00 '
    'e.g. Filter kits, clutch kit, exhaust muffler, tail pipe etc" '
    "(Delivery & Carriage Charge Information / UK Mainland Delivery). "
    "Live page https://www.ks-international.com/delivery-information 2026-10-07."
)

N = 12


def pick_pns() -> list[tuple[str, str, float]]:
    csv_path = ROOT / "01_data" / "90_INBOX" / "UNIVERSE_UK_NEXT_HARVEST_PNS_20261007.csv"
    df = pd.read_csv(csv_path, dtype={"part_number": str})
    df["eur"] = pd.to_numeric(df["eur_all_billed_all_markets"], errors="coerce").fillna(0.0)
    rows = []
    for _, r in df.iterrows():
        pn = str(r["part_number"])
        fam = str(r["pms_category"])
        if pn in CLOSED_PILOT_PNS:
            continue
        if fam not in FILTER_CLUTCH_FAMS:
            continue
        if str(r.get("uk_status") or "") != "no_uk_ledger_row":
            continue
        rows.append((pn, fam, float(r["eur"])))
    rows.sort(key=lambda x: -x[2])
    return rows[:N]


def fetch(url: str) -> tuple[int, bytes]:
    req = Request(url, headers={"User-Agent": UA, "Accept": "text/html,application/xhtml+xml"})
    with urlopen(req, timeout=45) as resp:
        return resp.getcode(), resp.read()


def loader_for(price_type: str | None) -> str:
    if price_type == "genuine_grey":
        return "ks_gen"
    if price_type == "aftermarket_retail":
        return "ks_am"
    return "ks"


def main() -> int:
    picks = pick_pns()
    print("PNS:", [(p, f, e) for p, f, e in picks])
    assert len(picks) == N, f"expected {N} picks, got {len(picks)}"
    for pn, _, _ in picks:
        assert pn not in CLOSED_PILOT_PNS

    (OUT / "harvest2_pn_queue_20261007.json").write_text(
        json.dumps(
            [
                {"part_no": pn, "family": fam, "eur_all_billed": eur}
                for pn, fam, eur in picks
            ],
            indent=2,
        ),
        encoding="utf-8",
    )

    results = []
    accepted_rows = []
    rejects = []

    for i, (pn, fam, eur) in enumerate(picks, 1):
        url = f"https://www.ks-international.com/catalogsearch/result/?q={pn}"
        html_name = f"search_{pn}.html"
        html_path = OUT / html_name
        entry = {
            "part_no": pn,
            "family": fam,
            "eur_all_billed": eur,
            "search_url": url,
            "html_path": html_name,
            "http_status": None,
            "bytes": 0,
            "sha1_12": None,
            "title": None,
            "parse_error": None,
            "n_cards": 0,
            "rows": [],
            "verdict": None,
            "reject_reason": None,
        }
        print(f"[{i}/{N}] {pn} {fam}")
        try:
            status, raw = fetch(url)
            entry["http_status"] = status
            entry["bytes"] = len(raw)
            entry["sha1_12"] = hashlib.sha1(raw).hexdigest()[:12]
            html_path.write_bytes(raw)
            html = raw.decode("utf-8", errors="replace")
            title_m = re.search(r"<title[^>]*>(.*?)</title>", html, re.I | re.S)
            entry["title"] = (
                re.sub(r"\s+", " ", title_m.group(1).strip()) if title_m else None
            )
            entry["n_cards"] = html.count('li class="item product product-item"')
            try:
                rows = parse(html, source_url=url, observed_at=OBSERVED)
            except ParseError as e:
                entry["parse_error"] = str(e)
                entry["verdict"] = (
                    "rejected_no_cards"
                    if "0 product cards" in str(e)
                    else "rejected_parse"
                )
                entry["reject_reason"] = str(e)[:240]
                rejects.append(entry)
                results.append(entry)
                time.sleep(SLEEP_S)
                continue

            for r in rows:
                entry["rows"].append(
                    {
                        "match_method": r.get("match_method"),
                        "part_no": r.get("part_no"),
                        "price": r.get("price"),
                        "vat": r.get("vat"),
                        "competitor_pn": r.get("competitor_pn"),
                        "price_type": r.get("price_type"),
                        "stock": r.get("stock"),
                        "description": (r.get("description") or "")[:240],
                    }
                )

            # Accept only when searched Isuzu PN is on a card (strict).
            exact = [
                r
                for r in rows
                if r.get("match_method") == "exact_oem"
                and (
                    str(r.get("part_no")) == pn
                    or pn in (find_pns(r.get("description") or "") or [])
                )
            ]
            # Double-check: PN must appear inside a product card element text.
            if exact and entry["n_cards"] > 0:
                from bs4 import BeautifulSoup

                soup = BeautifulSoup(html, "html.parser")
                card_hit = False
                for card in soup.select("li.item.product.product-item"):
                    if pn in (find_pns(card.get_text(" ", strip=True)) or []):
                        card_hit = True
                        break
                if not card_hit:
                    exact = []
                    entry["reject_reason"] = (
                        "parser said exact_oem but searched PN not in card text"
                    )

            if exact:
                entry["verdict"] = "accepted_exact_oem"
                for r in exact:
                    if str(r.get("part_no")) != pn:
                        # Prefer the searched PN when OE is on card.
                        r = dict(r)
                        r["part_no"] = pn
                    r["vat"] = "excl"
                    r["delivery_included"] = "no"
                    r["delivery_cost_amount"] = 10.0
                    r["delivery_cost_currency"] = "GBP"
                    r["delivery_note"] = DELIVERY_NOTE
                    r["loader"] = loader_for(r.get("price_type"))
                    r["source"] = "ks-international.com"
                    r["obs_id"] = issue_obs_id(
                        r["source"], pn, OBSERVED, str(r.get("price_type") or "na")
                    )
                    r["family"] = fam
                    accepted_rows.append(r)
                results.append(entry)
            else:
                if any(r.get("match_method") == "category_only" for r in rows):
                    entry["verdict"] = "rejected_category_only"
                    entry["reject_reason"] = (
                        "product card(s) but searched Isuzu PN not on card"
                    )
                elif entry["n_cards"] == 0:
                    entry["verdict"] = "rejected_no_cards"
                    entry["reject_reason"] = "no product cards"
                else:
                    entry["verdict"] = "rejected_no_exact_oem"
                    entry["reject_reason"] = entry["reject_reason"] or "no exact_oem with searched PN"
                rejects.append(entry)
                results.append(entry)
        except (HTTPError, URLError, TimeoutError, OSError) as e:
            entry["verdict"] = "rejected_fetch"
            entry["reject_reason"] = str(e)[:240]
            rejects.append(entry)
            results.append(entry)
        time.sleep(SLEEP_S)

    # Write artefacts
    (OUT / "harvest2_parse_summary_20261007.json").write_text(
        json.dumps(results, indent=2), encoding="utf-8"
    )

    rej_path = OUT / "harvest2_rejects_20261007.csv"
    with rej_path.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(
            f,
            fieldnames=[
                "part_no",
                "family",
                "reject_class",
                "reject_reason",
                "search_url",
                "html_path",
                "n_cards",
            ],
        )
        w.writeheader()
        for e in rejects:
            w.writerow(
                {
                    "part_no": e["part_no"],
                    "family": e["family"],
                    "reject_class": e["verdict"],
                    "reject_reason": e.get("reject_reason") or "",
                    "search_url": e["search_url"],
                    "html_path": e["html_path"],
                    "n_cards": e.get("n_cards"),
                }
            )

    staging = OUT / "staging_exact_oem_accepted_harvest2_20261007.csv"
    stage_fields = list(COLUMNS) + ["family", "pilot_verdict"]
    with staging.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=stage_fields, extrasaction="ignore")
        w.writeheader()
        for r in accepted_rows:
            row = {c: r.get(c) for c in COLUMNS}
            row["family"] = r.get("family")
            row["pilot_verdict"] = "accepted_exact_oem"
            w.writerow(row)

    print("accepted", len(accepted_rows), "rejected_pns", len(rejects))

    # Before metrics
    metrics_paths = [
        WT / "01_data/00_derived/market_data_gap_coverage_uk_wider_exact_20261007.metrics.json",
        ROOT / "01_data/00_derived/market_data_gap_coverage_uk_wider_exact_20261007.metrics.json",
    ]
    before = None
    before_path = None
    for p in metrics_paths:
        if p.exists():
            before = json.loads(p.read_text(encoding="utf-8"))
            before_path = p
            break
    before_rows = before.get("eligible_rows") if before else None
    before_pns = before.get("eligible_pns") if before else None
    print("BEFORE eligible", before_rows, before_pns, "from", before_path)

    ledger_appended = False
    backup_path = None
    if accepted_rows:
        ledger = WT / "01_data/00_derived/price_observations.parquet"
        stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        backup_path = ledger.with_name(
            f"price_observations.parquet.bak_{stamp}_before_ks_harvest2"
        )
        shutil.copy2(ledger, backup_path)
        df = pd.read_parquet(ledger)
        new = pd.DataFrame([{c: r.get(c) for c in COLUMNS} for r in accepted_rows])
        # Avoid duplicate obs_id
        new = new[~new["obs_id"].isin(set(df["obs_id"].astype(str)))]
        if len(new):
            out_df = pd.concat([df, new], ignore_index=True)
            out_df.to_parquet(ledger, index=False)
            ledger_appended = True
            print("appended", len(new), "rows; backup", backup_path)
        else:
            print("all accepted obs_ids already in ledger — no append")
    else:
        print("0 accepts — no ledger append")

    builder = WT / "01_data/91_build/build_market_data_gap_coverage_20261007.py"
    if not builder.exists():
        builder = ROOT / "01_data/91_build/build_market_data_gap_coverage_20261007.py"
    rc = subprocess.call(
        [sys.executable, str(builder), "--also-uk-exact"],
        cwd=str(builder.parent.parent.parent),
    )
    print("rebuild rc", rc)

    after_path = WT / "01_data/00_derived/market_data_gap_coverage_uk_wider_exact_20261007.metrics.json"
    if not after_path.exists():
        after_path = ROOT / "01_data/00_derived/market_data_gap_coverage_uk_wider_exact_20261007.metrics.json"
    after = json.loads(after_path.read_text(encoding="utf-8")) if after_path.exists() else {}
    after_rows = after.get("eligible_rows")
    after_pns = after.get("eligible_pns")
    print("AFTER eligible", after_rows, after_pns)

    # Mirror metrics to main clone if rebuild wrote to worktree
    main_metrics = ROOT / "01_data/00_derived/market_data_gap_coverage_uk_wider_exact_20261007.metrics.json"
    if after_path.exists() and after_path.resolve() != main_metrics.resolve():
        main_metrics.write_text(after_path.read_text(encoding="utf-8"), encoding="utf-8")

    # Also copy metrics CSV if present
    for name in [
        "market_data_gap_coverage_uk_wider_exact_20261007.csv",
        "market_data_gap_coverage_uk_wider_exact_20261007.metrics.json",
    ]:
        src = after_path.parent / name
        dst = main_metrics.parent / name
        if src.exists() and src.resolve() != dst.resolve():
            shutil.copy2(src, dst)

    rollup = {
        "pns_tried": [
            {"part_no": pn, "family": fam, "eur_all_billed": eur}
            for pn, fam, eur in picks
        ],
        "accepted_exact_oem": len(accepted_rows),
        "accepted_part_nos": sorted({str(r["part_no"]) for r in accepted_rows}),
        "rejected_pns": len(rejects),
        "before": {"eligible_rows": before_rows, "eligible_pns": before_pns},
        "after": {"eligible_rows": after_rows, "eligible_pns": after_pns},
        "eligible_delta_rows": (
            None
            if before_rows is None or after_rows is None
            else after_rows - before_rows
        ),
        "eligible_delta_pns": (
            None if before_pns is None or after_pns is None else after_pns - before_pns
        ),
        "ledger_appended": ledger_appended,
        "backup": str(backup_path) if backup_path else None,
        "staging": str(staging),
        "rebuild_rc": rc,
    }
    (OUT / "harvest2_eligible_before_after_20261007.json").write_text(
        json.dumps(rollup, indent=2), encoding="utf-8"
    )
    print(json.dumps(rollup, indent=2))
    return 0 if rc == 0 else rc


if __name__ == "__main__":
    raise SystemExit(main())
