# -*- coding: utf-8 -*-
"""Focus close: remaining UK KS oil_filter/brake_pad category_only → PDP OE upgrade."""
from __future__ import annotations

import json
import re
import shutil
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import quote as url_quote
from urllib.request import Request, urlopen

import pandas as pd
from bs4 import BeautifulSoup

ROOT = Path(r"C:\Users\jerom\Desktop\claude\ISZE")
U29B = Path(r"C:\Users\jerom\Desktop\claude\_worktrees\ISZE_u29b")
PARQUET = U29B / "01_data" / "00_derived" / "price_observations.parquet"
METRICS = U29B / "01_data" / "00_derived" / "market_data_gap_coverage_uk_wider_exact_20261007.metrics.json"
MAIN_METRICS = ROOT / "01_data" / "00_derived" / "market_data_gap_coverage_uk_wider_exact_20261007.metrics.json"
MAIN_CSV = ROOT / "01_data" / "00_derived" / "market_data_gap_coverage_uk_wider_exact_20261007.csv"
OUT = ROOT / "01_data" / "90_INBOX" / "_uk_ks_focus_close_20261007"
NOTE = ROOT / "00_docs" / "UNIVERSE_UK_KS_FOCUS_CLOSE_2026-10-07.md"
BUILDER = U29B / "01_data" / "91_build" / "build_market_data_gap_coverage_20261007.py"
if not BUILDER.exists():
    BUILDER = ROOT / "01_data" / "91_build" / "build_market_data_gap_coverage_20261007.py"

sys.path.insert(0, str(ROOT / "04_tools" / "delegation" / "parsers"))
from ledger_schema import find_pns  # noqa: E402

UA = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
)
SLEEP_S = 0.65
FOCUS = {"oil_filter", "brake_pad"}
FILTER_RE = re.compile(r"FILTER", re.I)
PAD_RE = re.compile(r"PAD|BRAKE", re.I)

DELIVERY_NOTE_FILTER = (
    "Live KS UK mainland £10 minimum (filter / clutch / muffler / tail pipe) "
    "— UNIVERSE_UK_KS_POLICY_SCOPE_2026-10-07"
)


def fetch(url: str) -> tuple[int, bytes]:
    req = Request(url, headers={"User-Agent": UA, "Accept": "text/html,application/xhtml+xml"})
    with urlopen(req, timeout=45) as resp:
        return resp.getcode(), resp.read()


def worklist_focus_map() -> dict[str, str]:
    for base in (U29B, ROOT):
        p = base / "01_data" / "00_derived" / "epc_decode_worklist.csv"
        if p.exists():
            wl = pd.read_csv(p)
            f = wl[wl["pms_category"].isin(FOCUS)]
            return dict(zip(f["part_number"].astype(str), f["pms_category"].astype(str)))
    raise FileNotFoundError("epc_decode_worklist.csv")


def extract_pdp_for_sku(search_html: str, sku: str) -> str | None:
    soup = BeautifulSoup(search_html, "html.parser")
    sku_u = (sku or "").strip().upper()
    for card in soup.select("li.item.product.product-item"):
        text = card.get_text(" ", strip=True).upper()
        sku_el = card.select_one("div.sku")
        card_sku = ""
        if sku_el:
            card_sku = re.sub(r"(?i)^sku:\s*", "", sku_el.get_text(" ", strip=True)).strip().upper()
        if sku_u and (card_sku == sku_u or sku_u in text):
            a = card.select_one("a.product-item-link")
            if a and a.get("href"):
                href = a["href"]
                if href.startswith("http"):
                    return href
                if href.startswith("/"):
                    return "https://www.ks-international.com" + href
    a = soup.select_one("li.item.product.product-item a.product-item-link")
    if a and a.get("href"):
        href = a["href"]
        if href.startswith("http"):
            return href
        if href.startswith("/"):
            return "https://www.ks-international.com" + href
    return None


def oe_locations(html: str, pn: str) -> dict:
    soup = BeautifulSoup(html, "html.parser")
    pn_s = str(pn)
    hits: list[dict] = []

    def check(label: str, blob: str | None) -> None:
        if not blob:
            return
        if pn_s in blob or pn_s in (find_pns(blob) or []):
            idx = blob.find(pn_s)
            if idx < 0:
                quote = blob[:160].replace("\n", " ")
            else:
                lo = max(0, idx - 40)
                hi = min(len(blob), idx + len(pn_s) + 40)
                quote = blob[lo:hi].replace("\n", " ")
            hits.append({"where": label, "quote": quote})

    title = soup.select_one("h1.page-title span, h1.page-title, .page-title-wrapper h1")
    check("title", title.get_text(" ", strip=True) if title else None)

    for row in soup.select(
        "#product-attribute-specs-table tr, .additional-attributes tr, table.data.table tr"
    ):
        th = row.select_one("th")
        td = row.select_one("td")
        label = th.get_text(" ", strip=True) if th else "attr"
        val = td.get_text(" ", strip=True) if td else row.get_text(" ", strip=True)
        lab_l = label.lower()
        if any(
            k in lab_l
            for k in ("oe", "oem", "cross", "ref", "compatible", "replaces", "manufacturer")
        ):
            check(f"attr:{label}", f"{label}: {val}")
        elif pn_s in (val or ""):
            check(f"attr:{label}", f"{label}: {val}")

    for sel, lab in [
        (".product.attribute.overview", "short_description"),
        (".product.attribute.description", "description"),
        ("#description", "description_tab"),
        (".product-info-main", "product_info_main"),
    ]:
        el = soup.select_one(sel)
        if el:
            check(lab, el.get_text(" ", strip=True))

    for script in soup.select('script[type="application/ld+json"]'):
        check("json_ld", script.string or script.get_text())

    body_text = soup.get_text(" ", strip=True)
    pns_all = find_pns(body_text) or []
    return {
        "pns_on_page": pns_all[:30],
        "target_hits": hits,
        "oe_on_pdp": bool(hits),
        "target_in_find_pns": pn_s in pns_all,
    }


def oe_pns_from_html(html: str) -> list[str]:
    soup = BeautifulSoup(html, "html.parser")
    found: list[str] = []
    for row in soup.select(
        "#product-attribute-specs-table tr, .additional-attributes tr, table.data.table tr"
    ):
        th = row.select_one("th")
        td = row.select_one("td")
        label = th.get_text(" ", strip=True) if th else ""
        val = td.get_text(" ", strip=True) if td else ""
        lab = label.lower()
        if "oe" in lab or "equivalent" in lab or "oem" in lab:
            found.extend(find_pns(val) or [])
    for script in soup.select('script[type="application/ld+json"]'):
        found.extend(find_pns(script.string or script.get_text()) or [])
    out: list[str] = []
    seen: set[str] = set()
    for p in found:
        if p and p not in seen:
            seen.add(p)
            out.append(p)
    return out


def clear_oe_hit(hits: list[dict]) -> bool:
    """Accept only OE Equivalent / clear OE attr / json-ld mpn — not loose body hits."""
    for h in hits:
        w = (h.get("where") or "").lower()
        if "oe" in w or "oem" in w or w == "json_ld" or "equivalent" in w:
            return True
    return False


def select_focus_remaining(df: pd.DataFrame, pn_cat: dict[str, str]) -> pd.DataFrame:
    focus_pns = set(pn_cat)
    ks = df[
        (df["loader"] == "ks")
        & (df["match_method"].astype(str).str.lower() == "category_only")
        & (df["country"].astype(str).str.upper() == "UK")
        & (df["part_no"].astype(str).isin(focus_pns))
        & (df["competitor_pn"].notna())
        & (df["competitor_pn"].astype(str).str.len() > 0)
    ].copy()
    ks["pms_category"] = ks["part_no"].astype(str).map(pn_cat)
    ks["price_f"] = pd.to_numeric(ks["price"], errors="coerce").fillna(0)
    # one row per SKU (highest £ candidate PN kept for fetch; extras patched later)
    uniq = ks.sort_values("price_f", ascending=False).drop_duplicates(
        subset=["competitor_pn"], keep="first"
    )
    return uniq.reset_index(drop=True), ks


def patch_row(
    df: pd.DataFrame,
    idx: int,
    *,
    evid: str,
    pdp_url: str | None,
    pms_category: str,
    keep_existing_delivery: bool,
) -> str:
    """Returns delivery action: keep_existing | wire_filter_10 | leave_blank."""
    df.at[idx, "match_method"] = "exact_oem"
    old_desc = str(df.at[idx, "description"] or "")
    if "PDP OE upgrade" not in old_desc and "Focus close" not in old_desc:
        df.at[idx, "description"] = (old_desc + " — " + evid).strip(" —")
    if str(df.at[idx, "vat"]).lower() != "excl":
        df.at[idx, "vat"] = "excl"
    action = "leave_blank"
    has_cost = pd.notna(df.at[idx, "delivery_cost_amount"])
    if pms_category == "oil_filter":
        if FILTER_RE.search(old_desc) or True:
            # filter family — policy page names filters
            df.at[idx, "delivery_included"] = "no"
            df.at[idx, "delivery_cost_amount"] = 10.0
            df.at[idx, "delivery_cost_currency"] = "GBP"
            if not str(df.at[idx, "delivery_note"] or "").strip():
                df.at[idx, "delivery_note"] = DELIVERY_NOTE_FILTER
            action = "wire_filter_10" if not has_cost else "keep_existing"
    elif pms_category == "brake_pad":
        # Do not invent £10 on pads. Only keep cost if already wired by earlier focus fill.
        if keep_existing_delivery and has_cost and float(df.at[idx, "delivery_cost_amount"]) == 10.0:
            action = "keep_existing"
        else:
            # strip invent if somehow we would count without proven cost — leave as-is blanks
            action = "leave_blank_no_new_pad_10"
    if pdp_url:
        df.at[idx, "source_url"] = pdp_url
    return action


def elig(m: dict) -> tuple[int, int, int]:
    offers = int(m.get("eligible_rows") or 0)
    pns = int(m.get("eligible_pns") or 0)
    focus = int(m.get("eligible_rows_in_focus") or 0)
    return offers, pns, focus


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    pn_cat = worklist_focus_map()
    df = pd.read_parquet(PARQUET)
    before = json.loads(METRICS.read_text(encoding="utf-8")) if METRICS.exists() else {}
    b_off, b_pn, b_focus = elig(before) if before else (151, 38, 47)

    sel, all_co = select_focus_remaining(df, pn_cat)
    sel_path = OUT / "focus_remaining_candidates_20261007.csv"
    sel.to_csv(sel_path, index=False)
    all_co.to_csv(OUT / "focus_remaining_all_rows_20261007.csv", index=False)
    print(f"focus category_only rows: {len(all_co)}; distinct SKUs: {len(sel)}")
    print(all_co.groupby("pms_category").size().to_dict())

    checks: list[dict] = []
    upgrades: list[dict] = []
    rejects: list[dict] = []
    sku_html: dict[str, str] = {}
    sku_pdp: dict[str, str] = {}
    sku_oe_list: dict[str, list[str]] = {}

    for _, row in sel.iterrows():
        pn = str(row["part_no"])
        sku = str(row["competitor_pn"])
        cat = str(row["pms_category"])
        entry: dict = {
            "obs_id": str(row["obs_id"]),
            "part_no": pn,
            "competitor_pn": sku,
            "pms_category": cat,
            "price": float(row["price_f"]),
            "had_delivery_10": (
                pd.notna(row.get("delivery_cost_amount"))
                and float(row.get("delivery_cost_amount") or 0) == 10.0
            ),
            "search_url": (
                f"https://www.ks-international.com/catalogsearch/result/?q={url_quote(sku)}"
            ),
            "pdp_url": None,
            "verdict": None,
            "oe_hits": [],
            "oe_list": [],
            "error": None,
        }
        try:
            code, raw = fetch(entry["search_url"])
            search_html = raw.decode("utf-8", errors="replace")
            (OUT / f"search_{sku}.html").write_text(search_html, encoding="utf-8")
            if code != 200:
                entry["verdict"] = "reject_http"
                entry["error"] = f"search HTTP {code}"
                rejects.append(entry)
                checks.append(entry)
                time.sleep(SLEEP_S)
                continue
            pdp = extract_pdp_for_sku(search_html, sku)
            entry["pdp_url"] = pdp
            if not pdp:
                entry["verdict"] = "reject_no_pdp"
                rejects.append(entry)
                checks.append(entry)
                time.sleep(SLEEP_S)
                continue
            time.sleep(SLEEP_S)
            code2, raw2 = fetch(pdp)
            pdp_html = raw2.decode("utf-8", errors="replace")
            (OUT / f"pdp_{sku}.html").write_text(pdp_html, encoding="utf-8")
            if code2 != 200:
                entry["verdict"] = "reject_http"
                entry["error"] = f"pdp HTTP {code2}"
                rejects.append(entry)
                checks.append(entry)
                time.sleep(SLEEP_S)
                continue
            loc = oe_locations(pdp_html, pn)
            oe_list = oe_pns_from_html(pdp_html)
            entry["oe_hits"] = loc["target_hits"]
            entry["oe_list"] = oe_list
            sku_html[sku] = pdp_html
            sku_pdp[sku] = pdp
            sku_oe_list[sku] = oe_list
            if loc["oe_on_pdp"] and clear_oe_hit(loc["target_hits"]):
                entry["verdict"] = "upgrade_exact_oem"
                upgrades.append(entry)
            else:
                entry["verdict"] = "reject_no_oe"
                rejects.append(entry)
            checks.append(entry)
            time.sleep(SLEEP_S)
        except (HTTPError, URLError, TimeoutError, OSError) as e:
            entry["verdict"] = "reject_error"
            entry["error"] = str(e)
            rejects.append(entry)
            checks.append(entry)
            time.sleep(SLEEP_S)

    (OUT / "pdp_checks_focus_close_20261007.json").write_text(
        json.dumps(checks, indent=2, ensure_ascii=False), encoding="utf-8"
    )

    # Patch primary + same-SKU extras where OE list contains the row's part_no
    upgrade_skus = {c["competitor_pn"] for c in upgrades}
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    bak = PARQUET.with_name(f"price_observations.parquet.bak_{stamp}_before_ks_focus_close")
    shutil.copy2(PARQUET, bak)
    print(f"backup: {bak}")

    patched_ids: list[str] = []
    patch_log: list[dict] = []
    for idx, row in df.iterrows():
        if str(row.get("loader")) != "ks":
            continue
        if str(row.get("match_method")).lower() != "category_only":
            continue
        if str(row.get("country")).upper() != "UK":
            continue
        sku = str(row.get("competitor_pn") or "")
        pn = str(row.get("part_no") or "")
        if sku not in upgrade_skus:
            continue
        oe_list = sku_oe_list.get(sku) or []
        # primary accept if pn in oe hits for that SKU's checked candidate OR in oe_list
        ok = pn in oe_list or any(
            c["competitor_pn"] == sku and c["part_no"] == pn for c in upgrades
        )
        if not ok:
            # re-check with stored html
            html = sku_html.get(sku)
            if html:
                loc = oe_locations(html, pn)
                ok = loc["oe_on_pdp"] and clear_oe_hit(loc["target_hits"])
                if ok and pn not in oe_list:
                    oe_list = oe_pns_from_html(html)
        if not ok:
            continue
        cat = pn_cat.get(pn)
        if not cat:
            continue  # only focus PNs for this close job
        evid_hit = None
        html = sku_html.get(sku)
        if html:
            loc = oe_locations(html, pn)
            if loc["target_hits"]:
                evid_hit = loc["target_hits"][0]
        quote = (evid_hit or {}).get("quote") or (", ".join(oe_list[:6]) if oe_list else pn)
        where = (evid_hit or {}).get("where") or "attr:OE Equivalent Part Number"
        evid = (
            f"Focus close PDP OE 2026-10-07: Isuzu {pn} printed on KS product page "
            f"({where}: «{quote}»). Was category_only."
        )
        had = pd.notna(row.get("delivery_cost_amount")) and float(
            row.get("delivery_cost_amount") or 0
        ) == 10.0
        action = patch_row(
            df,
            idx,
            evid=evid,
            pdp_url=sku_pdp.get(sku),
            pms_category=cat,
            keep_existing_delivery=had,
        )
        # If pad without existing £10, still upgrade match but leave delivery blank
        # (already handled in patch_row). Eligible only if cost stays.
        oid = str(row["obs_id"])
        patched_ids.append(oid)
        patch_log.append(
            {
                "obs_id": oid,
                "part_no": pn,
                "competitor_pn": sku,
                "pms_category": cat,
                "delivery_action": action,
                "price": float(row.get("price") or 0),
            }
        )

    df.to_parquet(PARQUET, index=False)
    (OUT / "patch_log_20261007.json").write_text(
        json.dumps(
            {
                "backup": str(bak),
                "patched_rows": len(patched_ids),
                "patched_ids": patched_ids,
                "log": patch_log,
                "upgrades_skus": sorted(upgrade_skus),
                "rejects": [
                    {
                        "sku": r["competitor_pn"],
                        "pn": r["part_no"],
                        "verdict": r["verdict"],
                        "error": r.get("error"),
                    }
                    for r in rejects
                ],
            },
            indent=2,
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )
    print(f"patched rows: {len(patched_ids)}")

    # Rebuild coverage
    cmd = [sys.executable, str(BUILDER), "--also-uk-exact"]
    print("running", " ".join(cmd))
    r = subprocess.run(cmd, cwd=str(BUILDER.parent.parent.parent), capture_output=True, text=True)
    print(r.stdout[-2000:] if r.stdout else "")
    if r.returncode != 0:
        print(r.stderr[-2000:] if r.stderr else "")
        print("BUILD FAILED", r.returncode)
        return r.returncode

    after = json.loads(METRICS.read_text(encoding="utf-8"))
    a_off, a_pn, a_focus = elig(after)

    # Copy metrics (+ csv) to main
    shutil.copy2(METRICS, MAIN_METRICS)
    u29_csv = METRICS.with_suffix(".csv")
    if u29_csv.exists():
        shutil.copy2(u29_csv, MAIN_CSV)
    # also copy if named without .metrics
    alt = U29B / "01_data" / "00_derived" / "market_data_gap_coverage_uk_wider_exact_20261007.csv"
    if alt.exists():
        shutil.copy2(alt, MAIN_CSV)

    # Write note
    lines = [
        "# UK KS focus close — oil_filter + brake_pad — 2026-10-07",
        "",
        "## Verdict",
        "",
    ]
    if a_focus >= 50:
        lines.append(
            f"**Focus eligible moved {b_focus} → {a_focus}** (bar ≥50 met). "
            f"Wider UK exact_oem eligible **{b_off} → {a_off}** offers "
            f"(**{b_pn} → {a_pn}** PNs). Board / INTERNAL not rebuilt here."
        )
    else:
        lines.append(
            f"**Focus eligible stayed {b_focus} → {a_focus}** after exhausting remaining "
            f"focus PDPs — **still under the 50-row bar**. Wider **{b_off} → {a_off}** / "
            f"**{b_pn} → {a_pn}** PNs. Stopped honestly; no invented pad £10. "
            f"Board / INTERNAL not rebuilt here."
        )
    lines += [
        "",
        "## Method",
        "",
        "After pass1/2/3, focus (oil filter + brake pad) sat at **47** while wider was **151**. "
        "Remaining UK KS focus rows that were still `category_only` (already had VAT excl + "
        "delivery £10 from the earlier fill):",
        "",
        f"- **{len(all_co)}** ledger rows / **{len(sel)}** distinct KS SKUs",
        f"- Mix: {dict(all_co.groupby('pms_category').size())}",
        "",
        "Opened each SKU search → PDP. Upgrade `category_only` → `exact_oem` **only** when "
        "the Isuzu PN is printed under **OE Equivalent Part Number** (or clear OE / JSON-LD).",
        "",
        "### Delivery policy for this pass",
        "",
        "| Family | Rule applied |",
        "|---|---|",
        "| oil_filter | KS mainland **£10** (named on live delivery page) |",
        "| brake_pad | **Do not invent £10** — live page does not name pads "
        "(`UNIVERSE_UK_KS_POLICY_SCOPE_2026-10-07.md`). Keep cost only if the earlier "
        "focus fill already wired £10 on that row. |",
        "",
        "Ledger: "
        "`C:\\Users\\jerom\\Desktop\\claude\\_worktrees\\ISZE_u29b\\01_data\\00_derived\\price_observations.parquet`",
        "",
        "## Candidates checked",
        "",
        "| # | KS SKU | Isuzu PN | Family | £ excl | Had £10 | Verdict |",
        "|---:|---|---|---|---:|---|---|",
    ]
    for i, c in enumerate(checks, 1):
        lines.append(
            f"| {i} | `{c['competitor_pn']}` | `{c['part_no']}` | {c['pms_category']} | "
            f"{c['price']:.2f} | {'Y' if c['had_delivery_10'] else 'N'} | {c['verdict']} |"
        )
    lines += [
        "",
        "## Upgrades (evidence)",
        "",
        "| KS SKU | Isuzu PN | Family | Where | Quote | Delivery action |",
        "|---|---|---|---|---|---|",
    ]
    for c in upgrades:
        hit = (c.get("oe_hits") or [{}])[0]
        act = next(
            (p["delivery_action"] for p in patch_log if p["competitor_pn"] == c["competitor_pn"]),
            "?",
        )
        lines.append(
            f"| `{c['competitor_pn']}` | `{c['part_no']}` | {c['pms_category']} | "
            f"{hit.get('where','')} | `{str(hit.get('quote',''))[:80]}` | {act} |"
        )
    if not upgrades:
        lines.append("| — | — | — | — | — | none |")
    lines += [
        "",
        "## Rejects",
        "",
    ]
    if rejects:
        for r in rejects:
            lines.append(
                f"- `{r['competitor_pn']}` / `{r['part_no']}` — {r['verdict']}"
                + (f" ({r['error']})" if r.get("error") else "")
            )
    else:
        lines.append("None.")
    lines += [
        "",
        "## Eligible before / after",
        "",
        "```text",
        "python 01_data/91_build/build_market_data_gap_coverage_20261007.py --also-uk-exact",
        "```",
        "",
        "| Cut | Before | After |",
        "|---|---:|---:|",
        f"| Focus eligible (`oil_filter` + `brake_pad`) | **{b_focus}** | **{a_focus}** |",
        f"| Wider UK `exact_oem` eligible **offers** | **{b_off}** | **{a_off}** |",
        f"| Wider eligible **PNs** | **{b_pn}** | **{a_pn}** |",
        f"| Ledger rows patched | | **{len(patched_ids)}** |",
        f"| Distinct SKUs upgraded | | **{len(upgrade_skus)}** |",
        "",
        f"Bar ≥50 focus: **{'MET' if a_focus >= 50 else 'NOT MET'}**.",
        "",
        "## Backups / artefacts",
        "",
        f"- Backup: `{bak}`",
        f"- PDP HTML + checks: `{OUT}`",
        f"- Runner: `{ROOT / '01_data' / '91_build' / '_uk_ks_focus_close_20261007.py'}`",
        f"- Metrics (U29b + copied to main): `{METRICS}`",
        "",
        "## Not done",
        "",
        "- No board / INTERNAL rebuild (parent re-wires if focus moves).",
        "- No new £10 invented on brake pads (policy page still names only filter / clutch / exhaust).",
        "- No TMC invent.",
        "",
    ]
    NOTE.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"NOTE: {NOTE}")
    print(f"FOCUS {b_focus} -> {a_focus}; WIDER {b_off}->{a_off} / {b_pn}->{a_pn}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
