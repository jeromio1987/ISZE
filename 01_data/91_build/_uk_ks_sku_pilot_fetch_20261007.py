# -*- coding: utf-8 -*-
"""Fetch KS search-by-competitor-SKU for the 8-PN pilot. Accept exact_oem only if Isuzu PN on card."""
from __future__ import annotations

import csv
import hashlib
import json
import re
import sys
import time
import urllib.parse
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

ROOT = Path(r"C:\Users\jerom\Desktop\claude\ISZE")
sys.path.insert(0, str(ROOT / "04_tools" / "delegation" / "parsers"))
from ledger_schema import find_pns  # noqa: E402
from site_ks import ParseError, parse  # noqa: E402
from bs4 import BeautifulSoup  # noqa: E402

OUT = ROOT / "01_data" / "90_INBOX" / "_uk_ks_sku_pilot_20261007"
QUEUE = OUT / "sku_search_queue_20261007.csv"
BRIDGES = OUT / "sku_bridges_20261007.json"
UA = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
)
OBSERVED = "2026-10-07"
SLEEP_S = 0.7
MAX_PER_PN = 8


def compact(sku: str) -> str:
    return re.sub(r"[^A-Za-z0-9]", "", sku or "").upper()


def prefer_sku_form(a: str, b: str) -> str:
    """Prefer denser form (fewer separators) for the HTTP query."""
    score = lambda s: (-len(re.findall(r"[^A-Za-z0-9]", s)), -len(s))
    return a if score(a) <= score(b) else b


def load_queue() -> list[dict]:
    rows = list(csv.DictReader(QUEUE.open(encoding="utf-8")))
    # Dedupe per (part_no, compact sku); keep preferred form + best tier
    tier_rank = {"confirmed": 0, "likely": 1, "doubtful": 2, "ungraded": 3, "reject": 4}
    best: dict[tuple[str, str], dict] = {}
    for r in rows:
        key = (r["part_no"], compact(r["sku"]))
        if not key[1]:
            continue
        prev = best.get(key)
        if prev is None:
            best[key] = dict(r)
            continue
        if tier_rank.get(r["tier"], 9) < tier_rank.get(prev["tier"], 9):
            best[key] = dict(r)
        else:
            best[key]["sku"] = prefer_sku_form(prev["sku"], r["sku"])
    # Cap per PN
    by_pn: dict[str, list[dict]] = {}
    for r in best.values():
        by_pn.setdefault(r["part_no"], []).append(r)
    out = []
    for pn, items in by_pn.items():
        items.sort(key=lambda x: tier_rank.get(x["tier"], 9))
        out.extend(items[:MAX_PER_PN])
    return out


def fetch(url: str) -> tuple[int, bytes]:
    req = Request(url, headers={"User-Agent": UA, "Accept": "text/html,application/xhtml+xml"})
    with urlopen(req, timeout=45) as resp:
        return resp.getcode(), resp.read()


def card_has_isuzu(card_html_text: str, isuzu_pn: str) -> bool:
    pns = find_pns(card_html_text) or []
    return isuzu_pn in pns


def extract_pdp_links(html: str) -> list[str]:
    soup = BeautifulSoup(html, "html.parser")
    links = []
    for a in soup.select("li.item.product.product-item a.product-item-link"):
        href = a.get("href") or ""
        if href.startswith("http"):
            links.append(href)
        elif href.startswith("/"):
            links.append("https://www.ks-international.com" + href)
    # dedupe preserve order
    seen = set()
    out = []
    for u in links:
        if u not in seen:
            seen.add(u)
            out.append(u)
    return out


def main() -> int:
    queue = load_queue()
    bridges = json.loads(BRIDGES.read_text(encoding="utf-8"))
    no_bridge = [
        e["part_no"]
        for e in bridges["summary"]
        if e["bridge_status"] == "no_SKU_bridge"
    ]

    results = []
    accepted = []
    rejects = []

    print(f"queue after dedupe/cap: {len(queue)}")
    print(f"no_SKU_bridge PNs: {no_bridge}")

    for pn in no_bridge:
        rejects.append(
            {
                "part_no": pn,
                "sku": "",
                "reject_class": "no_SKU_bridge",
                "reject_reason": "no competitor/OE SKU on disk (graded/edges/spareto/oe_bridge/iam_ks)",
                "search_url": "",
                "html_path": "",
            }
        )

    for i, item in enumerate(queue, 1):
        pn = item["part_no"]
        sku = item["sku"]
        fam = item["family"]
        q = urllib.parse.quote(sku)
        url = f"https://www.ks-international.com/catalogsearch/result/?q={q}"
        safe = re.sub(r"[^A-Za-z0-9._-]+", "_", sku)[:80]
        html_name = f"search_sku_{pn}_{safe}.html"
        html_path = OUT / html_name
        entry = {
            "part_no": pn,
            "family": fam,
            "sku": sku,
            "brand": item.get("brand"),
            "tier": item.get("tier"),
            "source": item.get("source"),
            "search_url": url,
            "html_path": html_name,
            "http_status": None,
            "bytes": 0,
            "sha1_12": None,
            "title": None,
            "parse_error": None,
            "n_cards": 0,
            "rows": [],
            "pdp_urls": [],
            "pdp_checks": [],
            "verdict": None,
        }
        print(f"[{i}/{len(queue)}] {pn} <- {sku} ({item.get('tier')})")
        try:
            status, raw = fetch(url)
            entry["http_status"] = status
            entry["bytes"] = len(raw)
            entry["sha1_12"] = hashlib.sha1(raw).hexdigest()[:12]
            html_path.write_bytes(raw)
            html = raw.decode("utf-8", errors="replace")
            title_m = re.search(r"<title[^>]*>(.*?)</title>", html, re.I | re.S)
            entry["title"] = re.sub(r"\s+", " ", title_m.group(1).strip()) if title_m else None
            entry["n_cards"] = html.count('li class="item product product-item"')
            try:
                rows = parse(html, source_url=url, observed_at=OBSERVED)
            except ParseError as e:
                entry["parse_error"] = str(e)
                entry["verdict"] = "rejected_no_cards" if "0 product cards" in str(e) else "rejected_parse"
                rejects.append(
                    {
                        "part_no": pn,
                        "sku": sku,
                        "reject_class": entry["verdict"],
                        "reject_reason": entry["parse_error"][:240],
                        "search_url": url,
                        "html_path": html_name,
                    }
                )
                results.append(entry)
                time.sleep(SLEEP_S)
                continue

            # Re-check each card: accept only if OUR Isuzu PN prints on the card
            soup = BeautifulSoup(html, "html.parser")
            cards = soup.select("li.item.product.product-item")
            exact_hits = []
            for r, card in zip(rows, cards):
                card_text = card.get_text(" ", strip=True)
                pns_on_card = find_pns(card_text) or []
                has_ours = pn in pns_on_card
                row_out = {
                    "match_method": r.get("match_method"),
                    "part_no_parsed": r.get("part_no"),
                    "price": r.get("price"),
                    "vat": r.get("vat"),
                    "competitor_pn": r.get("competitor_pn"),
                    "price_type": r.get("price_type"),
                    "stock": r.get("stock"),
                    "description": (r.get("description") or "")[:240],
                    "source_url": r.get("source_url"),
                    "pns_on_card": pns_on_card,
                    "has_target_isuzu_pn": has_ours,
                }
                entry["rows"].append(row_out)
                if has_ours and r.get("price") is not None:
                    exact_hits.append((r, row_out, card))
                elif has_ours:
                    # OE on card but no price — still note
                    exact_hits.append((r, row_out, card))

            entry["pdp_urls"] = extract_pdp_links(html)[:5]
            # Open first PDP for any exact hit (or first card if we want OE confirmation)
            pdp_targets = entry["pdp_urls"][:2] if exact_hits or entry["rows"] else []
            for pdp_url in pdp_targets:
                pdp_safe = hashlib.sha1(pdp_url.encode()).hexdigest()[:10]
                pdp_name = f"pdp_{pn}_{pdp_safe}.html"
                pdp_path = OUT / pdp_name
                try:
                    st, praw = fetch(pdp_url)
                    pdp_path.write_bytes(praw)
                    phtml = praw.decode("utf-8", errors="replace")
                    pns = find_pns(BeautifulSoup(phtml, "html.parser").get_text(" ", strip=True)) or []
                    entry["pdp_checks"].append(
                        {
                            "url": pdp_url,
                            "http_status": st,
                            "html_path": pdp_name,
                            "bytes": len(praw),
                            "pns_found": pns,
                            "has_target_isuzu_pn": pn in pns,
                        }
                    )
                    time.sleep(SLEEP_S)
                except (HTTPError, URLError, TimeoutError) as e:
                    entry["pdp_checks"].append({"url": pdp_url, "error": str(e)[:160]})

            # Accept gate: target Isuzu PN on search card (or PDP) + ex-VAT £ present
            accept_row = None
            evidence = None
            for r, row_out, _card in exact_hits:
                if row_out.get("has_target_isuzu_pn") and r.get("price") is not None:
                    accept_row = r
                    evidence = "search_card"
                    break
            if accept_row is None:
                pdp_ok = any(chk.get("has_target_isuzu_pn") for chk in entry["pdp_checks"])
                if pdp_ok:
                    for r in rows:
                        if r.get("price") is not None:
                            accept_row = r
                            evidence = "pdp_oe"
                            break

            if accept_row is not None:
                r = accept_row
                entry["verdict"] = "accepted_exact_oem"
                accepted.append(
                    {
                        "part_no": pn,
                        "family": fam,
                        "sku_searched": sku,
                        "brand_bridge": item.get("brand"),
                        "tier": item.get("tier"),
                        "match_method": "exact_oem",
                        "competitor_pn": r.get("competitor_pn"),
                        "price": r.get("price"),
                        "currency": "GBP",
                        "vat": r.get("vat") or "excl",
                        "price_type": r.get("price_type"),
                        "stock": r.get("stock"),
                        "description": r.get("description"),
                        "source_url": url,
                        "evidence": evidence,
                        "search_html": html_name,
                        "pdp_html": (entry["pdp_checks"][0]["html_path"] if entry["pdp_checks"] else ""),
                    }
                )
                print(f"  ACCEPT exact_oem £{r.get('price')} sku={r.get('competitor_pn')}")
            else:
                if entry["rows"]:
                    entry["verdict"] = "rejected_no_isuzu_on_card"
                    rejects.append(
                        {
                            "part_no": pn,
                            "sku": sku,
                            "reject_class": "no_isuzu_on_card",
                            "reject_reason": "cards present but target Isuzu PN not printed on card/PDP",
                            "search_url": url,
                            "html_path": html_name,
                        }
                    )
                    print(f"  REJECT no Isuzu on card ({len(entry['rows'])} cards)")
                else:
                    entry["verdict"] = "rejected_empty"
                    rejects.append(
                        {
                            "part_no": pn,
                            "sku": sku,
                            "reject_class": "empty",
                            "reject_reason": "no usable rows",
                            "search_url": url,
                            "html_path": html_name,
                        }
                    )
            results.append(entry)
        except (HTTPError, URLError, TimeoutError) as e:
            entry["verdict"] = "rejected_fetch"
            entry["parse_error"] = str(e)[:240]
            rejects.append(
                {
                    "part_no": pn,
                    "sku": sku,
                    "reject_class": "fetch_error",
                    "reject_reason": str(e)[:240],
                    "search_url": url,
                    "html_path": html_name,
                }
            )
            results.append(entry)
            print("  FETCH ERR", e)
        time.sleep(SLEEP_S)

    # Per-PN rollup
    by_pn: dict[str, dict] = {}
    for e in bridges["summary"]:
        by_pn[e["part_no"]] = {
            "part_no": e["part_no"],
            "family": e["family"],
            "bridge_status": e["bridge_status"],
            "n_skus_tried": 0,
            "accepted": False,
            "accepted_price": None,
            "accepted_ks_sku": None,
        }
    for a in accepted:
        by_pn[a["part_no"]]["accepted"] = True
        by_pn[a["part_no"]]["accepted_price"] = a["price"]
        by_pn[a["part_no"]]["accepted_ks_sku"] = a["competitor_pn"]
    for e in results:
        if e["part_no"] in by_pn:
            by_pn[e["part_no"]]["n_skus_tried"] += 1

    summary = {
        "observed_at": OBSERVED,
        "n_sku_searches": len(queue),
        "n_accepted_exact_oem": len(accepted),
        "n_rejects": len(rejects),
        "no_SKU_bridge": no_bridge,
        "per_pn": list(by_pn.values()),
        "accepted": accepted,
        "results": results,
    }
    (OUT / "sku_pilot_fetch_summary_20261007.json").write_text(
        json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8"
    )
    with (OUT / "sku_pilot_rejects_20261007.csv").open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(
            f,
            fieldnames=["part_no", "sku", "reject_class", "reject_reason", "search_url", "html_path"],
        )
        w.writeheader()
        w.writerows(rejects)

    print("=" * 60)
    print("accepted", len(accepted))
    for a in accepted:
        print(" ", a["part_no"], a["price"], a["competitor_pn"], a["sku_searched"])
    print("no_SKU_bridge", no_bridge)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
