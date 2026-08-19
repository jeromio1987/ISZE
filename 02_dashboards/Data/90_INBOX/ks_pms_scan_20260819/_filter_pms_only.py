"""Build PMS-only working set from 19 Aug KS tree scrape (no live fetch)."""
from __future__ import annotations

import csv
import json
import re
from datetime import datetime, timezone
from pathlib import Path

OUT = Path(__file__).resolve().parent
SRC = OUT / "products.json"

# Functions that COUNT (Jerome 19 Aug)
KEEP_RX = re.compile(
    r"oil filter|fuel filter|air filter|cabin filter|"
    r"engine filter kit|filter kit \(oil|"
    r"brake pad|brake disc|discs? ?& ?pad|disc \+ pad|disc and pad|"
    r"clutch kit|clutch release bearing",
    re.I,
)

# Functions that DO NOT COUNT (standalone). Clutch kit still counts even if the
# SKU name also says flywheel/spigot — those two lines are in the 31/29 set.
DROP_RX = re.compile(
    r"caliper|clutch (master|slave|hydraulic|shaft|pedal)|"
    r"\babs\b|speed sensor|lock pin|"
    r"automatic transmission|atf|"
    r"titan cargo|10w40|"
    r"hydraulic fluid|brake cleaner|"
    r"air cleaner assembly|air cleaner asm|"
    r"^(?!.*clutch kit).*flywheel|"
    r"pilot bearing|spigot / pilot|oil.?pump ring|"
    r"clutch fork|release fork|clutch shift fork|"
    r"clutch flex hose|slave cylinder|master cylinder",
    re.I,
)


def sku_norm(s: str) -> str:
    s = (s or "").strip()
    s = re.sub(r"(?i)^sku:\s*", "", s)
    return s.strip()


def classify(name: str) -> str | None:
    n = name or ""
    if DROP_RX.search(n):
        return None
    # air-cleaner assembly already dropped; keep air filter / element
    if KEEP_RX.search(n):
        if re.search(r"oil filter", n, re.I):
            return "oil_filter"
        if re.search(r"fuel filter", n, re.I):
            return "fuel_filter"
        if re.search(r"cabin filter", n, re.I):
            return "cabin_filter"
        if re.search(r"air filter", n, re.I):
            return "air_filter"
        if re.search(r"engine filter kit|filter kit \(oil", n, re.I):
            return "filter_kit"
        if re.search(r"brake pad|discs? ?& ?pad|disc \+ pad|disc and pad", n, re.I):
            return "brake_pad"
        if re.search(r"brake disc", n, re.I):
            return "brake_disc"
        if re.search(r"clutch kit", n, re.I):
            return "clutch_kit"
        if re.search(r"clutch release bearing", n, re.I):
            return "clutch_release_bearing"
        return "pms_other"
    return None


def main() -> None:
    data = json.loads(SRC.read_text(encoding="utf-8"))
    trees = data.get("trees") or {}
    rows: list[dict] = []
    dropped: list[dict] = []
    seen_keys: set[tuple] = set()

    for tree, block in trees.items():
        items = block.get("items") or []
        status = block.get("status")
        page_url = block.get("url") or ""
        for it in items:
            name = it.get("name") or ""
            sku = sku_norm(it.get("sku") or "")
            url = it.get("url") or ""
            key = (tree, sku, url, name)
            if key in seen_keys:
                continue
            seen_keys.add(key)
            fn = classify(name)
            rec = {
                "tree": tree,
                "tree_status": status,
                "tree_url": page_url,
                "function": fn or "",
                "name": name,
                "sku": sku,
                "url": url,
                "price_ex_gbp": it.get("price_ex_gbp"),
                "is_genuine": it.get("is_genuine"),
                "brand": it.get("brand") or "",
                "in_stock": it.get("in_stock"),
            }
            if fn:
                rows.append(rec)
            else:
                dropped.append({**rec, "drop_reason": "not_pms_function"})

    sku_keep = sorted({r["sku"] for r in rows if r["sku"]})
    tree_summary = {
        k: {
            "status": v.get("status"),
            "url": v.get("url"),
            "n_items_fetched": len(v.get("items") or []),
            "n_pms_kept": sum(1 for r in rows if r["tree"] == k),
        }
        for k, v in trees.items()
    }

    ts = datetime.now(timezone.utc).isoformat()
    csv_path = OUT / "ks_pms_only_20260819.csv"
    meta_path = OUT / "ks_pms_only_20260819.meta.json"

    fields = [
        "tree",
        "function",
        "name",
        "sku",
        "url",
        "price_ex_gbp",
        "is_genuine",
        "brand",
        "in_stock",
        "tree_status",
        "tree_url",
    ]
    with csv_path.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fields, extrasaction="ignore")
        w.writeheader()
        w.writerows(rows)

    meta = {
        "n_rows": len(rows),
        "unique_skus": len(sku_keep),
        "timestamp": ts,
        "source_scrape": str(SRC),
        "source_finished": data.get("finished"),
        "trees": tree_summary,
        "exclusion_rule": (
            "Keep only PMS function lines: oil filter, fuel filter, air filter, "
            "cabin filter, filter kit (oil+air+fuel), brake pad (genuine/TBK/unnamed/"
            "disc+pad kit), brake disc, clutch kit, clutch release bearing. "
            "Drop calipers, clutch hydraulics/shaft/pedal, ABS/speed sensors, lock pins, "
            "ATF, Titan 10W40, hydraulic fluid, brake cleaner, air-cleaner assembly, "
            "flywheel/pilot/oil-pump rings. Magento catalogsearch ok-stubs are not in this file."
        ),
        "n_tree_items_fetched": sum(len(v.get("items") or []) for v in trees.values()),
        "n_dropped": len(dropped),
        "unique_skus_list": sku_keep,
        "functions_kept": sorted({r["function"] for r in rows}),
    }
    meta_path.write_text(json.dumps(meta, indent=2), encoding="utf-8")

    print(f"n_rows={len(rows)} unique_skus={len(sku_keep)} fetched={meta['n_tree_items_fetched']} dropped={len(dropped)}")
    print("csv", csv_path)
    print("meta", meta_path)
    from collections import Counter
    print("by_function", dict(Counter(r["function"] for r in rows)))
    print("dropped_names:")
    for r in dropped:
        print(f"  [{r['tree']}] {r['name']} sku={r['sku']}")


if __name__ == "__main__":
    main()
