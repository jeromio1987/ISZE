# -*- coding: utf-8 -*-
"""Fetch KS by competitor SKU (pilot2). Accept only if SKU + Isuzu OE on same card/PDP."""
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

OUT = ROOT / "01_data" / "90_INBOX" / "_uk_ks_sku_pilot2_20261007"
QUEUE = OUT / "sku_search_queue_pilot2_20261007.csv"
UA = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
)
OBSERVED = "2026-10-07"
SLEEP_S = 0.7


def compact(sku: str) -> str:
    return re.sub(r"[^A-Za-z0-9]", "", sku or "").upper()


def fetch(url: str) -> tuple[int, bytes]:
    req = Request(url, headers={"User-Agent": UA, "Accept": "text/html,application/xhtml+xml"})
    with urlopen(req, timeout=45) as resp:
        return resp.getcode(), resp.read()


def extract_pdp_links(html: str) -> list[str]:
    soup = BeautifulSoup(html, "html.parser")
    links = []
    for a in soup.select("li.item.product.product-item a.product-item-link"):
        href = a.get("href") or ""
        if href.startswith("http"):
            links.append(href)
        elif href.startswith("/"):
            links.append("https://www.ks-international.com" + href)
    seen: set[str] = set()
    out: list[str] = []
    for u in links:
        if u not in seen:
            seen.add(u)
            out.append(u)
    return out


def text_has_sku(text: str, sku: str) -> bool:
    """True if competitor SKU appears in text (compact or spaced forms)."""
    t = text or ""
    if not sku:
        return False
    if sku in t:
        return True
    ct = compact(t)
    cs = compact(sku)
    if cs and cs in ct:
        return True
    # also allow last alphanumeric token match for SKUs with spaces
    return False


def card_sku_label(card) -> str:
    sku_div = card.select_one("div.sku")
    if not sku_div:
        return ""
    lab = sku_div.get_text(" ", strip=True)
    # "Sku: 0707723G"
    m = re.search(r"(?i)sku\s*:\s*(\S+)", lab)
    return m.group(1) if m else lab.replace("Sku:", "").strip()


def main() -> int:
    queue = list(csv.DictReader(QUEUE.open(encoding="utf-8")))
    results = []
    accepted = []
    rejects = []

    print(f"queue: {len(queue)}")

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
            entry["title"] = (
                re.sub(r"\s+", " ", title_m.group(1).strip()) if title_m else None
            )
            entry["n_cards"] = html.count('li class="item product product-item"')
            try:
                rows = parse(html, source_url=url, observed_at=OBSERVED)
            except ParseError as e:
                entry["parse_error"] = str(e)
                entry["verdict"] = (
                    "rejected_no_cards" if "0 product cards" in str(e) else "rejected_parse"
                )
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
                print(f"  REJECT {entry['verdict']}")
                time.sleep(SLEEP_S)
                continue

            soup = BeautifulSoup(html, "html.parser")
            cards = soup.select("li.item.product.product-item")
            exact_hits = []
            for r, card in zip(rows, cards):
                card_text = card.get_text(" ", strip=True)
                pns_on_card = find_pns(card_text) or []
                ks_sku = card_sku_label(card)
                has_ours = pn in pns_on_card
                has_comp = text_has_sku(card_text, sku) or text_has_sku(ks_sku, sku)
                # competitor_pn from parser may be KS sku — also check it
                if r.get("competitor_pn"):
                    has_comp = has_comp or text_has_sku(r.get("competitor_pn") or "", sku)
                row_out = {
                    "match_method": r.get("match_method"),
                    "part_no_parsed": r.get("part_no"),
                    "price": r.get("price"),
                    "vat": r.get("vat"),
                    "competitor_pn": r.get("competitor_pn"),
                    "ks_sku_label": ks_sku,
                    "price_type": r.get("price_type"),
                    "stock": r.get("stock"),
                    "description": (r.get("description") or "")[:240],
                    "source_url": r.get("source_url"),
                    "pns_on_card": pns_on_card,
                    "has_target_isuzu_pn": has_ours,
                    "has_competitor_sku": has_comp,
                }
                entry["rows"].append(row_out)
                if has_ours and has_comp:
                    exact_hits.append((r, row_out, card))

            entry["pdp_urls"] = extract_pdp_links(html)[:5]
            # PDP for exact hits, else first 2 cards for OE+SKU confirmation
            pdp_targets = entry["pdp_urls"][:3] if (exact_hits or entry["rows"]) else []
            for pdp_url in pdp_targets:
                pdp_safe = hashlib.sha1(pdp_url.encode()).hexdigest()[:10]
                pdp_name = f"pdp_{pn}_{pdp_safe}.html"
                pdp_path = OUT / pdp_name
                try:
                    st, praw = fetch(pdp_url)
                    pdp_path.write_bytes(praw)
                    phtml = praw.decode("utf-8", errors="replace")
                    ptext = BeautifulSoup(phtml, "html.parser").get_text(" ", strip=True)
                    pns = find_pns(ptext) or []
                    has_oe = pn in pns
                    has_sku = text_has_sku(ptext, sku)
                    entry["pdp_checks"].append(
                        {
                            "url": pdp_url,
                            "http_status": st,
                            "html_path": pdp_name,
                            "bytes": len(praw),
                            "pns_found": pns,
                            "has_target_isuzu_pn": has_oe,
                            "has_competitor_sku": has_sku,
                        }
                    )
                    time.sleep(SLEEP_S)
                except (HTTPError, URLError, TimeoutError) as e:
                    entry["pdp_checks"].append({"url": pdp_url, "error": str(e)[:160]})

            accept_row = None
            evidence = None
            for r, row_out, _card in exact_hits:
                if (
                    row_out.get("has_target_isuzu_pn")
                    and row_out.get("has_competitor_sku")
                    and r.get("price") is not None
                ):
                    accept_row = r
                    evidence = "search_card"
                    break
            if accept_row is None:
                for chk in entry["pdp_checks"]:
                    if chk.get("has_target_isuzu_pn") and chk.get("has_competitor_sku"):
                        for r in rows:
                            if r.get("price") is not None:
                                accept_row = r
                                evidence = "pdp"
                                break
                        if accept_row is not None:
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
                        "pdp_html": (
                            entry["pdp_checks"][0]["html_path"] if entry["pdp_checks"] else ""
                        ),
                    }
                )
                print(
                    f"  ACCEPT exact_oem £{r.get('price')} ks_sku={r.get('competitor_pn')} evidence={evidence}"
                )
            else:
                if entry["rows"]:
                    any_oe = any(x.get("has_target_isuzu_pn") for x in entry["rows"])
                    any_sku = any(x.get("has_competitor_sku") for x in entry["rows"])
                    pdp_oe = any(c.get("has_target_isuzu_pn") for c in entry["pdp_checks"])
                    pdp_sku = any(c.get("has_competitor_sku") for c in entry["pdp_checks"])
                    entry["verdict"] = "rejected_gate"
                    reason = (
                        f"cards={len(entry['rows'])}; "
                        f"card_oe={any_oe} card_sku={any_sku}; "
                        f"pdp_oe={pdp_oe} pdp_sku={pdp_sku}"
                    )
                    rejects.append(
                        {
                            "part_no": pn,
                            "sku": sku,
                            "reject_class": "gate_fail",
                            "reject_reason": reason,
                            "search_url": url,
                            "html_path": html_name,
                        }
                    )
                    print(f"  REJECT gate ({reason})")
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
                    print("  REJECT empty")
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

    by_pn: dict[str, dict] = {}
    for item in queue:
        pn = item["part_no"]
        by_pn.setdefault(
            pn,
            {
                "part_no": pn,
                "family": item["family"],
                "n_skus_tried": 0,
                "accepted": False,
                "accepted_price": None,
                "accepted_ks_sku": None,
            },
        )
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
        "per_pn": list(by_pn.values()),
        "accepted": accepted,
        "results": results,
    }
    (OUT / "sku_pilot2_fetch_summary_20261007.json").write_text(
        json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8"
    )
    with (OUT / "sku_pilot2_rejects_20261007.csv").open(
        "w", encoding="utf-8", newline=""
    ) as f:
        w = csv.DictWriter(
            f,
            fieldnames=[
                "part_no",
                "sku",
                "reject_class",
                "reject_reason",
                "search_url",
                "html_path",
            ],
        )
        w.writeheader()
        w.writerows(rejects)

    print("=" * 60)
    print("accepted", len(accepted))
    for a in accepted:
        print(" ", a["part_no"], a["price"], a["competitor_pn"], a["sku_searched"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
