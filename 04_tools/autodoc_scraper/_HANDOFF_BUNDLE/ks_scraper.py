"""
ISZE — KS International Competitive Price Scraper
===================================================
KS International (ks-international.com) is the UK's largest independent
stockist of Isuzu truck parts — selling both aftermarket AND genuine OEM.

Why this matters for ISZE:
  - Aftermarket prices = specialist Isuzu competition (more relevant than Autodoc)
  - Genuine prices    = parallel import / grey market pressure on ISZE PR00
  - Stock status      = availability signal

Site is server-side Magento → simple requests, NO Playwright needed.
URL: https://www.ks-international.com/catalogsearch/result/?q={PN}

Output: ks_results.csv  (incremental, resumes on restart)

Usage:
    python ks_scraper.py [--top N] [--delay MIN MAX]
"""

import argparse
import csv
import os
import random
import re
import sys
import time
from datetime import datetime
from pathlib import Path

SCRIPT_DIR = Path(__file__).parent

V3_CANDIDATES = [
    SCRIPT_DIR / "ISZE_Parts_Intelligence_v3.xlsx",
    SCRIPT_DIR.parent.parent / "Isuzu" / "data" / "ISZE_Parts_Intelligence_v3.xlsx",
]

OUTPUT_CSV = SCRIPT_DIR / "ks_results.csv"
BASE_URL   = "https://www.ks-international.com/catalogsearch/result/?q={pn}"

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/122.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "en-GB,en;q=0.9",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Referer": "https://www.ks-international.com/",
}

CSV_FIELDS = [
    "PN", "Description", "PR00_EUR", "Rev_CY2025_EUR", "Qty_CY2025",
    "Source", "Class", "AIM_Category",
    "KS_ResultCount",
    # Aftermarket (non-genuine)
    "KS_AM_MinPrice_GBP", "KS_AM_AvgPrice_GBP", "KS_AM_Count",
    "KS_AM_InStock_Count", "KS_AM_SKUs",
    # Genuine OEM (parallel import)
    "KS_GEN_MinPrice_GBP", "KS_GEN_AvgPrice_GBP", "KS_GEN_Count",
    "KS_GEN_InStock_Count", "KS_GEN_SKUs",
    # All products
    "KS_AllProducts",
    "KS_URL", "Scraped_At", "Status", "Notes",
]


# ─── Helpers ───────────────────────────────────────────────────────────────────

def find_v3():
    import pandas as pd
    for p in V3_CANDIDATES:
        if p.exists():
            return p
    for root, _, files in os.walk(Path(__file__).resolve().parents[3]):
        if "ISZE_Parts_Intelligence_v3.xlsx" in files:
            return Path(root) / "ISZE_Parts_Intelligence_v3.xlsx"
    return None


def load_top_pns(n):
    import pandas as pd
    fpath = find_v3()
    if not fpath:
        sys.exit("❌  Cannot find ISZE_Parts_Intelligence_v3.xlsx")
    print(f"📂  V3: {fpath}")
    df = pd.read_excel(fpath, sheet_name="PN_Price_Matrix", dtype={"PN": str})
    df["PN"] = df["PN"].astype(str).str.zfill(10)
    df["Rev_CY2025_EUR"] = pd.to_numeric(df.get("Rev_CY2025_EUR", 0), errors="coerce").fillna(0)
    cols = [c for c in ["PN", "Description", "PR00_EUR", "Rev_CY2025_EUR",
                        "Qty_CY2025", "Source", "Class", "AIM_Category"]
            if c in df.columns]
    top = (df[df["Rev_CY2025_EUR"] > 0]
             .sort_values("Rev_CY2025_EUR", ascending=False)
             .head(n)[cols]
             .reset_index(drop=True))
    print(f"✅  {len(top)} PNs loaded")
    return top


def already_done():
    if not OUTPUT_CSV.exists():
        return set()
    done = set()
    with open(OUTPUT_CSV, newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            done.add(row.get("PN", ""))
    return done


def init_csv():
    if OUTPUT_CSV.exists():
        return
    with open(OUTPUT_CSV, "w", newline="", encoding="utf-8") as f:
        csv.DictWriter(f, fieldnames=CSV_FIELDS).writeheader()


def append_row(row):
    with open(OUTPUT_CSV, "a", newline="", encoding="utf-8") as f:
        csv.DictWriter(f, fieldnames=CSV_FIELDS).writerow(row)


# ─── Parsing ───────────────────────────────────────────────────────────────────

def parse_ks_page(html: str, pn: str) -> dict:
    """
    Parse KS International search results page.
    Returns structured dict with aftermarket and genuine sections.
    """
    try:
        from bs4 import BeautifulSoup
    except ImportError:
        sys.exit("❌  BeautifulSoup not installed. Run: pip install beautifulsoup4")

    soup = BeautifulSoup(html, "html.parser")

    # Result count
    count_el = soup.select_one(".toolbar-amount")
    result_count = 0
    if count_el:
        m = re.search(r"(\d+)", count_el.get_text())
        if m:
            result_count = int(m.group(1))

    # No results page
    if result_count == 0:
        no_res = soup.select_one(".message.empty, .search-no-results")
        return {
            "result_count": 0,
            "aftermarket": [],
            "genuine": [],
            "notes": "No results",
        }

    products = []
    for item in soup.select(".product-item"):
        name = (item.select_one(".product-item-name a") or
                item.select_one(".product-item-name"))
        name_text = name.get_text(strip=True) if name else ""

        # SKU
        sku_el = item.select_one(".product-sku")
        if sku_el:
            sku = sku_el.get_text(strip=True).replace("SKU:", "").strip()
        else:
            m = re.search(r"SKU:\s*(\S+)", item.get_text())
            sku = m.group(1) if m else ""

        # Price ex-VAT (preferred for comparison with ISZE PR00 which is ex-VAT)
        price_ex_el = item.select_one(".price-excluding-tax .price")
        if not price_ex_el:
            price_ex_el = item.select_one("[data-price-type='finalPrice'] .price")
        price_ex = None
        if price_ex_el:
            m = re.search(r"[\d,]+\.?\d*", price_ex_el.get_text().replace(",", ""))
            if m:
                try:
                    price_ex = float(m.group().replace(",", ""))
                except ValueError:
                    pass

        # Price inc-VAT
        price_inc_el = item.select_one(".price-including-tax .price")
        price_inc = None
        if price_inc_el:
            m = re.search(r"[\d,]+\.?\d*", price_inc_el.get_text().replace(",", ""))
            if m:
                try:
                    price_inc = float(m.group().replace(",", ""))
                except ValueError:
                    pass

        # Is genuine OEM?
        item_text = item.get_text()
        is_genuine = ("GENUINE" in name_text.upper() or
                      "GENUINE OEM" in item_text.upper() or
                      bool(item.select_one('.genuine-badge, [class*="genuine"]')))

        # Out of stock?
        out_of_stock = bool(
            item.select_one(".stock.unavailable, .out-of-stock") or
            "out of stock" in item_text.lower()
        )

        if price_ex is not None:
            products.append({
                "name": name_text,
                "sku": sku,
                "price_ex": price_ex,
                "price_inc": price_inc,
                "is_genuine": is_genuine,
                "in_stock": not out_of_stock,
            })

    aftermarket = [p for p in products if not p["is_genuine"]]
    genuine     = [p for p in products if p["is_genuine"]]

    return {
        "result_count": result_count,
        "aftermarket": aftermarket,
        "genuine": genuine,
        "notes": "",
    }


def summarise_group(products: list) -> dict:
    """Summarise a list of products (aftermarket or genuine) into scalar metrics."""
    if not products:
        return {
            "min_price": None, "avg_price": None,
            "count": 0, "in_stock_count": 0, "skus": "",
        }
    prices = [p["price_ex"] for p in products if p["price_ex"] is not None]
    return {
        "min_price":      min(prices) if prices else None,
        "avg_price":      round(sum(prices) / len(prices), 2) if prices else None,
        "count":          len(products),
        "in_stock_count": sum(1 for p in products if p["in_stock"]),
        "skus":           "|".join(p["sku"] for p in products),
    }


# ─── Main ──────────────────────────────────────────────────────────────────────

def run(top_n: int, delay_min: float, delay_max: float):
    try:
        import requests
        from bs4 import BeautifulSoup  # noqa – just verify installed
    except ImportError as e:
        sys.exit(f"❌  Missing package: {e}. Run: pip install requests beautifulsoup4")

    import pandas as pd
    pn_df   = load_top_pns(top_n)
    done    = already_done()
    pending = pn_df[~pn_df["PN"].isin(done)]

    print(f"\n📋  {len(done)} already done → {len(pending)} remaining")
    init_csv()

    if pending.empty:
        print("✅  All done. Delete ks_results.csv to restart.")
        return

    session = requests.Session()
    session.headers.update(HEADERS)

    total  = len(pending)
    errors = 0

    for i, (_, row) in enumerate(pending.iterrows(), 1):
        pn  = row["PN"]
        url = BASE_URL.format(pn=pn)
        ts  = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        print(f"[{i:>3}/{total}]  {pn}  {str(row.get('Description', ''))[:38]}  …",
              end=" ", flush=True)

        out = {f: "" for f in CSV_FIELDS}
        out.update({
            "PN":             pn,
            "Description":    row.get("Description", ""),
            "PR00_EUR":       row.get("PR00_EUR", ""),
            "Rev_CY2025_EUR": row.get("Rev_CY2025_EUR", ""),
            "Qty_CY2025":     row.get("Qty_CY2025", ""),
            "Source":         row.get("Source", ""),
            "Class":          row.get("Class", ""),
            "AIM_Category":   row.get("AIM_Category", ""),
            "KS_URL":         url,
            "Scraped_At":     ts,
            "Status":         "error",
        })

        try:
            resp = session.get(url, timeout=20)
            resp.raise_for_status()
            parsed = parse_ks_page(resp.text, pn)

            out["KS_ResultCount"] = parsed["result_count"]
            out["Notes"]          = parsed.get("notes", "")

            am  = summarise_group(parsed["aftermarket"])
            gen = summarise_group(parsed["genuine"])

            out["KS_AM_MinPrice_GBP"]  = am["min_price"] or ""
            out["KS_AM_AvgPrice_GBP"]  = am["avg_price"] or ""
            out["KS_AM_Count"]         = am["count"]
            out["KS_AM_InStock_Count"] = am["in_stock_count"]
            out["KS_AM_SKUs"]          = am["skus"]

            out["KS_GEN_MinPrice_GBP"]  = gen["min_price"] or ""
            out["KS_GEN_AvgPrice_GBP"]  = gen["avg_price"] or ""
            out["KS_GEN_Count"]         = gen["count"]
            out["KS_GEN_InStock_Count"] = gen["in_stock_count"]
            out["KS_GEN_SKUs"]          = gen["skus"]

            # All products summary
            all_prods = parsed["aftermarket"] + parsed["genuine"]
            out["KS_AllProducts"] = "|".join(
                f"{p['name']}({p['sku']})=£{p['price_ex']:.2f}"
                f"{'[OOS]' if not p['in_stock'] else ''}"
                for p in all_prods
            )

            if parsed["result_count"] == 0:
                out["Status"] = "no_results"
                print("—  no results")
            else:
                out["Status"] = "ok"
                am_str  = f"AM: £{am['min_price']:.2f}" if am["min_price"] else "AM: none"
                gen_str = f"  GEN: £{gen['min_price']:.2f}" if gen["min_price"] else ""
                print(f"✅  {parsed['result_count']} results  {am_str}{gen_str}")

        except Exception as e:
            out["Status"] = "error"
            out["Notes"]  = str(e)[:120]
            errors += 1
            print(f"❌  {e}")

        append_row(out)

        if i % 25 == 0:
            pct = (i + len(done)) / len(pn_df) * 100
            print(f"\n── Progress: {i+len(done)}/{len(pn_df)} ({pct:.0f}%)  errors: {errors} ──\n")

        if i < total:
            time.sleep(random.uniform(delay_min, delay_max))

    print(f"\n{'='*60}")
    print(f"✅  Done — {total} PNs  ({errors} errors)")
    print(f"📄  Results: {OUTPUT_CSV}")
    print(f"{'='*60}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="KS International price scraper")
    parser.add_argument("--top",   type=int, default=300)
    parser.add_argument("--delay", type=float, nargs=2, default=[1, 3],
                        metavar=("MIN", "MAX"))
    args = parser.parse_args()

    print("=" * 60)
    print("  ISZE KS International Price Scraper")
    print(f"  Top {args.top} PNs | delay {args.delay[0]}–{args.delay[1]}s")
    print("  Scrapes both aftermarket AND genuine OEM prices")
    print("=" * 60 + "\n")

    run(top_n=args.top, delay_min=args.delay[0], delay_max=args.delay[1])
