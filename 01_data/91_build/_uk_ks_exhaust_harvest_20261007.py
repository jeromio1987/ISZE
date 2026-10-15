# -*- coding: utf-8 -*-
"""Fetch + parse KS search for exhaust shortlist. Accept exact_oem only."""
from __future__ import annotations

import csv
import hashlib
import json
import re
import sys
import time
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "04_tools" / "delegation" / "parsers"))
from site_ks import ParseError, parse  # noqa: E402

OUT = ROOT / "01_data" / "90_INBOX" / "_uk_ks_exhaust_harvest_20261007"
SHORTLIST = OUT / "shortlist_exhaust_20261007.csv"
UA = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
)
OBS_AT = "2026-10-07"


def fetch(pn: str) -> tuple[bytes, str, int | None]:
    url = f"https://www.ks-international.com/catalogsearch/result/?q={pn}"
    req = Request(url, headers={"User-Agent": UA, "Accept": "text/html,application/xhtml+xml"})
    try:
        with urlopen(req, timeout=45) as resp:
            data = resp.read()
            return data, url, getattr(resp, "status", 200)
    except HTTPError as e:
        return e.read() if e.fp else b"", url, e.code
    except URLError as e:
        return b"", url, None


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    sl = pd.read_csv(SHORTLIST, dtype=str)
    results = []
    accepted_rows = []
    rejects = []

    for _, row in sl.iterrows():
        pn = str(row["part_number"]).strip()
        fam_desc = str(row.get("description") or "")
        data, url, status = fetch(pn)
        path = OUT / f"search_{pn}.html"
        path.write_bytes(data)
        html = data.decode("utf-8", errors="replace")
        title_m = re.search(r"<title[^>]*>(.*?)</title>", html, re.I | re.S)
        title = re.sub(r"\s+", " ", title_m.group(1).strip()) if title_m else "?"
        h = hashlib.sha1(data).hexdigest()[:12]
        entry = {
            "part_no": pn,
            "epc_desc": fam_desc,
            "http_status": status,
            "bytes": len(data),
            "sha1_12": h,
            "title": title[:160],
            "url": url,
            "parse_error": None,
            "rows": [],
            "verdict": None,
        }
        try:
            parsed = parse(html, source_url=url, observed_at=OBS_AT)
            for r in parsed:
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
                        "source_url": r.get("source_url"),
                        "obs_id": r.get("obs_id"),
                        "loader": r.get("loader"),
                        "currency": r.get("currency"),
                        "country": r.get("country"),
                        "observed_at": r.get("observed_at"),
                        "vintage": r.get("vintage"),
                        "source": r.get("source"),
                        "n_obs": r.get("n_obs"),
                        "competitor_brand": r.get("competitor_brand"),
                    }
                )
            exact = [r for r in parsed if r.get("match_method") == "exact_oem"]
            # Must print the *searched* Isuzu PN (not some other OE)
            exact_ok = []
            for r in exact:
                card_has = pn in (r.get("description") or "") or str(r.get("part_no")) == pn
                # site_ks sets part_no to first PN found on card; require searched PN on card text
                raw_card_ok = pn in html
                if card_has and raw_card_ok and str(r.get("part_no")) == pn:
                    exact_ok.append(r)
            if exact_ok:
                entry["verdict"] = "accepted_exact_oem"
                for r in exact_ok:
                    accepted_rows.append(r)
            elif any(r.get("match_method") == "category_only" for r in parsed):
                entry["verdict"] = "rejected_category_only"
            else:
                entry["verdict"] = "rejected_no_exact_oem"
        except ParseError as e:
            entry["parse_error"] = str(e)
            msg = str(e).lower()
            if "0 product cards" in msg or "no results" in msg:
                entry["verdict"] = "rejected_no_product_cards"
            else:
                entry["verdict"] = "rejected_parse_error"

        results.append(entry)
        rejects.append(
            {
                "part_no": pn,
                "epc_desc": fam_desc,
                "verdict": entry["verdict"],
                "http_status": status,
                "cards": len(entry["rows"]),
                "parse_error": entry["parse_error"] or "",
            }
        )
        print(
            pn,
            entry["verdict"],
            "bytes",
            len(data),
            "cards",
            len(entry["rows"]),
            (entry["parse_error"] or "")[:80],
        )
        time.sleep(0.8)

    (OUT / "harvest_parse_summary.json").write_text(
        json.dumps(results, indent=2, default=str), encoding="utf-8"
    )
    with (OUT / "harvest_rejects_20261007.csv").open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(
            f,
            fieldnames=["part_no", "epc_desc", "verdict", "http_status", "cards", "parse_error"],
        )
        w.writeheader()
        w.writerows(rejects)

    # staging accepted
    staging = OUT / "staging_exact_oem_accepted_exhaust_20261007.csv"
    if accepted_rows:
        pd.DataFrame(accepted_rows).to_csv(staging, index=False)
    else:
        staging.write_text(
            "part_no,match_method,price,vat,competitor_pn,description,source_url\n",
            encoding="utf-8",
        )

    n_acc = sum(1 for e in results if e["verdict"] == "accepted_exact_oem")
    n_rej = len(results) - n_acc
    print("SUMMARY accepted_pns", n_acc, "rejected", n_rej, "tried", len(results))
    print("accepted_rows", len(accepted_rows))


if __name__ == "__main__":
    main()
