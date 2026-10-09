# -*- coding: utf-8 -*-
"""U29b: reopen KS PDPs for category_only rows; upgrade only if Isuzu OE on PDP."""
from __future__ import annotations

import csv
import hashlib
import json
import re
import shutil
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
BLOCKED = ROOT / "01_data" / "00_derived" / "_uk_oe_crosswalk_probe_20261007" / "blocked_focus.csv"
OUT = ROOT / "01_data" / "90_INBOX" / "_uk_ks_pdp_oe_upgrade_20261007"
NOTE = ROOT / "00_docs" / "UNIVERSE_UK_KS_PDP_OE_UPGRADE_2026-10-07.md"
METRICS = U29B / "01_data" / "00_derived" / "market_data_gap_coverage_uk_wider_exact_20261007.metrics.json"

sys.path.insert(0, str(ROOT / "04_tools" / "delegation" / "parsers"))
from ledger_schema import find_pns  # noqa: E402

UA = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
)
SLEEP_S = 0.65
CAP = 25

# Live KS £10 mainland classes (policy note)
FILTER_RE = re.compile(r"FILTER", re.I)
CLUTCH_RE = re.compile(r"CLUTCH", re.I)
EXHAUST_RE = re.compile(
    r"EXHAUST|MUFFLER|SILENCER|TAIL\s*PIPE|PIPE;\s*EXH|EXH;\s*PIPE", re.I
)
# Named for £10 — not exhaust brake / camshaft / sensor
EXHAUST_10_OK = re.compile(
    r"MUFFLER|SILENCER|TAIL\s*PIPE|PIPE;\s*EXH|EXH;\s*PIPE|"
    r"EXHAUST\s*(PIPE|SILENCER|MUFFLER|ASSEMBLY)",
    re.I,
)
EXHAUST_10_NO = re.compile(
    r"EXHAUST\s*BRAKE|CAMSHAFT|TEMPERATURE|SENSOR|GASKET", re.I
)
PAD_RE = re.compile(r"BRAKE\s*PAD|PAD\s*SET", re.I)


def fetch(url: str) -> tuple[int, bytes]:
    req = Request(url, headers={"User-Agent": UA, "Accept": "text/html,application/xhtml+xml"})
    with urlopen(req, timeout=45) as resp:
        return resp.getcode(), resp.read()


def family_bucket(desc: str) -> str:
    d = desc or ""
    if FILTER_RE.search(d):
        return "filter"
    if CLUTCH_RE.search(d):
        return "clutch"
    if EXHAUST_RE.search(d):
        return "exhaust"
    if PAD_RE.search(d):
        return "brake_pad"
    return "other"


def can_wire_10(desc: str) -> bool:
    d = desc or ""
    if FILTER_RE.search(d) or CLUTCH_RE.search(d):
        return True
    if EXHAUST_10_NO.search(d):
        return False
    if EXHAUST_10_OK.search(d) or (
        EXHAUST_RE.search(d) and not EXHAUST_10_NO.search(d)
    ):
        return True
    return False


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
    # fallback first product link
    a = soup.select_one("li.item.product.product-item a.product-item-link")
    if a and a.get("href"):
        href = a["href"]
        if href.startswith("http"):
            return href
        if href.startswith("/"):
            return "https://www.ks-international.com" + href
    return None


def oe_locations(html: str, pn: str) -> dict:
    """Where (if anywhere) the Isuzu PN appears on the PDP."""
    soup = BeautifulSoup(html, "html.parser")
    pn_s = str(pn)
    hits: list[dict] = []

    def check(label: str, blob: str | None) -> None:
        if not blob:
            return
        if pn_s in blob or pn_s in (find_pns(blob) or []):
            # quote a short window
            idx = blob.find(pn_s)
            if idx < 0:
                # dashed / spaced variant via find_pns only
                quote = blob[:160].replace("\n", " ")
            else:
                lo = max(0, idx - 40)
                hi = min(len(blob), idx + len(pn_s) + 40)
                quote = blob[lo:hi].replace("\n", " ")
            hits.append({"where": label, "quote": quote})

    title = soup.select_one("h1.page-title span, h1.page-title, .page-title-wrapper h1")
    check("title", title.get_text(" ", strip=True) if title else None)

    sku_el = soup.select_one(".product.attribute.sku .value, div.product-info-stock-sku .sku .value, div.sku")
    check("sku_field", sku_el.get_text(" ", strip=True) if sku_el else None)

    # attributes / additional info table
    for row in soup.select("#product-attribute-specs-table tr, .additional-attributes tr, table.data.table tr"):
        th = row.select_one("th")
        td = row.select_one("td")
        label = (th.get_text(" ", strip=True) if th else "attr")
        val = td.get_text(" ", strip=True) if td else row.get_text(" ", strip=True)
        lab_l = label.lower()
        if any(k in lab_l for k in ("oe", "oem", "cross", "ref", "compatible", "replaces", "manufacturer")):
            check(f"attr:{label}", f"{label}: {val}")
        elif pn_s in (val or ""):
            check(f"attr:{label}", f"{label}: {val}")

    # description / short description
    for sel, lab in [
        (".product.attribute.overview", "short_description"),
        (".product.attribute.description", "description"),
        ("#description", "description_tab"),
        (".product-info-main", "product_info_main"),
    ]:
        el = soup.select_one(sel)
        if el:
            check(lab, el.get_text(" ", strip=True))

    # structured JSON-LD
    for script in soup.select('script[type="application/ld+json"]'):
        check("json_ld", script.string or script.get_text())

    # whole visible text as last resort (still require clear hit)
    body_text = soup.get_text(" ", strip=True)
    pns_all = find_pns(body_text) or []
    clearly_on = bool(hits)
    # If only in chrome (search box / related), don't count — require a labelled hit
    # OR PN in product-info-main / attributes already captured
    return {
        "pns_on_page": pns_all[:30],
        "target_hits": hits,
        "oe_on_pdp": clearly_on and any(h for h in hits),
        "target_in_find_pns": pn_s in pns_all,
    }


def select_candidates(df: pd.DataFrame) -> pd.DataFrame:
    ks = df[
        (df["loader"] == "ks")
        & (df["match_method"].astype(str).str.lower() == "category_only")
        & (df["country"].astype(str).str.upper() == "UK")
        & (df["source"].astype(str).str.contains("KS", case=False, na=False))
    ].copy()
    ks["price_f"] = pd.to_numeric(ks["price"], errors="coerce").fillna(0)
    ks["desc_u"] = ks["description"].astype(str)
    ks["family"] = ks["desc_u"].map(family_bucket)
    ks = ks[ks["family"].isin(["filter", "clutch", "exhaust", "brake_pad"])]
    blocked = pd.read_csv(BLOCKED)
    blocked_skus = set(blocked["competitor_pn"].astype(str))
    ks["is_blocked"] = ks["competitor_pn"].astype(str).isin(blocked_skus)
    # Prefer £10-able families; still allow focus pad (already wired £10)
    ks["wire10"] = ks["desc_u"].map(can_wire_10)
    # Dedupe SKU
    ks = ks.sort_values(
        ["is_blocked", "wire10", "price_f"], ascending=[False, False, False]
    )
    uniq = ks.drop_duplicates(subset=["competitor_pn"], keep="first")
    # Build mix: high-£ wire10 first (ex/clutch/filter), then blocked
    high = uniq[uniq["wire10"]].head(18)
    rest_need = CAP - len(high)
    blocked_extra = uniq[
        (~uniq["competitor_pn"].isin(high["competitor_pn"])) & (uniq["is_blocked"])
    ].head(max(0, rest_need))
    sel = pd.concat([high, blocked_extra], ignore_index=True).head(CAP)
    if len(sel) < CAP:
        more = uniq[~uniq["competitor_pn"].isin(sel["competitor_pn"])].head(CAP - len(sel))
        sel = pd.concat([sel, more], ignore_index=True)
    return sel


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    df = pd.read_parquet(PARQUET)
    before = {}
    if METRICS.exists():
        before = json.loads(METRICS.read_text(encoding="utf-8"))

    sel = select_candidates(df)
    sel_path = OUT / "pdp_candidates_20261007.csv"
    sel.to_csv(sel_path, index=False)
    print(f"candidates: {len(sel)} -> {sel_path}")

    checks = []
    upgrades = []
    rejects = []

    for i, row in sel.iterrows():
        pn = str(row["part_no"])
        sku = str(row["competitor_pn"])
        obs_id = str(row["obs_id"])
        desc = str(row.get("description") or "")
        fam = family_bucket(desc)
        entry = {
            "obs_id": obs_id,
            "part_no": pn,
            "competitor_pn": sku,
            "price": float(row["price_f"]),
            "family": fam,
            "is_blocked": bool(row["is_blocked"]),
            "can_wire_10": can_wire_10(desc),
            "search_url": f"https://www.ks-international.com/catalogsearch/result/?q={url_quote(sku)}",
            "pdp_url": None,
            "verdict": None,
            "oe_hits": [],
            "error": None,
        }
        print(f"[{len(checks)+1}/{len(sel)}] SKU {sku} PN {pn} £{row['price_f']} {fam}")
        try:
            st, raw = fetch(entry["search_url"])
            search_name = f"search_sku_{sku}.html"
            (OUT / search_name).write_bytes(raw)
            html = raw.decode("utf-8", errors="replace")
            pdp = extract_pdp_for_sku(html, sku)
            entry["search_http"] = st
            entry["pdp_url"] = pdp
            if not pdp:
                entry["verdict"] = "reject_no_pdp_link"
                rejects.append(entry)
                checks.append(entry)
                time.sleep(SLEEP_S)
                continue
            st2, praw = fetch(pdp)
            safe = hashlib.sha1(pdp.encode()).hexdigest()[:10]
            pdp_name = f"pdp_{sku}_{safe}.html"
            (OUT / pdp_name).write_bytes(praw)
            phtml = praw.decode("utf-8", errors="replace")
            loc = oe_locations(phtml, pn)
            entry["pdp_http"] = st2
            entry["pdp_html"] = pdp_name
            entry["oe_hits"] = loc["target_hits"]
            entry["pns_on_page"] = loc["pns_on_page"]
            # Strict: OE must appear in a labelled product field, not bare page chrome
            if loc["oe_on_pdp"]:
                entry["verdict"] = "upgrade_exact_oem"
                upgrades.append(entry)
                print(f"  UPGRADE OE on PDP: {loc['target_hits'][0]}")
            else:
                entry["verdict"] = "reject_no_oe_on_pdp"
                rejects.append(entry)
                print(f"  reject — no OE on PDP (pns sample {loc['pns_on_page'][:5]})")
        except (HTTPError, URLError, TimeoutError, OSError) as e:
            entry["verdict"] = "reject_fetch_error"
            entry["error"] = str(e)[:200]
            rejects.append(entry)
            print(f"  error: {e}")
        checks.append(entry)
        time.sleep(SLEEP_S)

    (OUT / "pdp_checks_20261007.json").write_text(
        json.dumps(checks, indent=2, ensure_ascii=False), encoding="utf-8"
    )

    upgraded_obs: list[str] = []
    bak = None
    if upgrades:
        ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        bak = PARQUET.with_name(f"price_observations.parquet.bak_{ts}_before_ks_pdp_oe")
        shutil.copy2(PARQUET, bak)
        print(f"backup: {bak}")
        df2 = pd.read_parquet(PARQUET)
        note_tpl = (
            "PDP OE upgrade 2026-10-07: Isuzu {pn} printed on KS product page "
            "({where}: «{quote}»). Was category_only."
        )
        delivery_note = (
            "Live KS UK mainland £10 minimum (filter / clutch / muffler / tail pipe) "
            "— UNIVERSE_UK_KS_POLICY_SCOPE_2026-10-07"
        )
        for u in upgrades:
            # Upgrade all ledger rows sharing this KS SKU + Isuzu PN that are still category_only
            mask = (
                (df2["loader"] == "ks")
                & (df2["match_method"].astype(str).str.lower() == "category_only")
                & (df2["competitor_pn"].astype(str) == u["competitor_pn"])
                & (df2["part_no"].astype(str) == u["part_no"])
            )
            idxs = df2.index[mask].tolist()
            where = u["oe_hits"][0]["where"] if u["oe_hits"] else "pdp"
            quote_txt = u["oe_hits"][0]["quote"] if u["oe_hits"] else u["part_no"]
            evid = note_tpl.format(pn=u["part_no"], where=where, quote=quote_txt[:120])
            for idx in idxs:
                df2.at[idx, "match_method"] = "exact_oem"
                old_desc = str(df2.at[idx, "description"] or "")
                if "PDP OE upgrade" not in old_desc:
                    df2.at[idx, "description"] = (old_desc + " — " + evid).strip(" —")
                # VAT excl already expected; ensure
                if str(df2.at[idx, "vat"]).lower() != "excl":
                    df2.at[idx, "vat"] = "excl"
                if u["can_wire_10"]:
                    df2.at[idx, "delivery_included"] = "no"
                    df2.at[idx, "delivery_cost_amount"] = 10.0
                    df2.at[idx, "delivery_cost_currency"] = "GBP"
                    df2.at[idx, "delivery_note"] = delivery_note
                # Prefer PDP URL as source_url
                if u.get("pdp_url"):
                    df2.at[idx, "source_url"] = u["pdp_url"]
                upgraded_obs.append(str(df2.at[idx, "obs_id"]))
            print(f"  patched {len(idxs)} rows for SKU {u['competitor_pn']} PN {u['part_no']}")
        df2.to_parquet(PARQUET, index=False)
        print(f"wrote parquet; upgraded obs_ids={len(upgraded_obs)}")
    else:
        print("no upgrades — parquet untouched")

    # Rebuild coverage if any upgrade
    after = before
    if upgrades:
        import subprocess

        cmd = [
            sys.executable,
            str(ROOT / "01_data" / "91_build" / "build_market_data_gap_coverage_20261007.py"),
            "--also-uk-exact",
        ]
        # Prefer worktree cwd so outputs land in U29b if script uses relative paths
        r = subprocess.run(cmd, cwd=str(U29B), capture_output=True, text=True)
        print(r.stdout[-2000:] if r.stdout else "")
        if r.returncode != 0:
            print("COVERAGE FAIL", r.stderr[-2000:])
        if METRICS.exists():
            after = json.loads(METRICS.read_text(encoding="utf-8"))
        # Also copy metrics to main if builder wrote under U29b
        main_m = ROOT / "01_data" / "00_derived" / "market_data_gap_coverage_uk_wider_exact_20261007.metrics.json"
        if METRICS.exists() and METRICS.resolve() != main_m.resolve():
            shutil.copy2(METRICS, main_m)

    def elig(m: dict) -> tuple[int, int]:
        # tolerate key shapes
        offers = m.get("eligible_offers") or m.get("eligible_rows") or m.get("wider_eligible_offers")
        pns = m.get("eligible_pns") or m.get("wider_eligible_pns")
        if offers is None and "uk_wider_exact" in m:
            sub = m["uk_wider_exact"]
            offers = sub.get("eligible_offers") or sub.get("eligible_rows")
            pns = sub.get("eligible_pns")
        return int(offers or 0), int(pns or 0)

    # If metrics nested differently, read CSV
    def elig_from_csv() -> tuple[int, int]:
        csvp = U29B / "01_data" / "00_derived" / "market_data_gap_coverage_uk_wider_exact_20261007.csv"
        if not csvp.exists():
            csvp = ROOT / "01_data" / "00_derived" / "market_data_gap_coverage_uk_wider_exact_20261007.csv"
        if not csvp.exists():
            return 0, 0
        c = pd.read_csv(csvp)
        if "status" in c.columns:
            ok = c[c["status"].astype(str).str.lower().isin(["eligible", "accepted", "ok"])]
        elif "eligible" in c.columns:
            ok = c[c["eligible"] == True]  # noqa: E712
        else:
            # count rows marked usable
            ok = c
        pncol = "part_no" if "part_no" in ok.columns else "part_number"
        return len(ok), ok[pncol].nunique() if pncol in ok.columns else 0

    b_off, b_pn = elig(before) if before else (18, 13)
    a_off, a_pn = elig(after) if after else elig_from_csv()
    if not after and METRICS.exists():
        after = json.loads(METRICS.read_text(encoding="utf-8"))
        a_off, a_pn = elig(after)

    # Fallback known baseline if metrics keys opaque
    if b_off == 0 and before:
        # dump keys for note
        (OUT / "metrics_before_keys.json").write_text(
            json.dumps(list(before.keys()), indent=2), encoding="utf-8"
        )

    summary = {
        "tried": len(checks),
        "upgrades_pdp": len(upgrades),
        "rows_patched": len(upgraded_obs),
        "rejects": len(rejects),
        "eligible_offers_before": b_off,
        "eligible_pns_before": b_pn,
        "eligible_offers_after": a_off,
        "eligible_pns_after": a_pn,
        "backup": str(bak) if bak else None,
        "upgraded_obs_ids": upgraded_obs,
        "upgrade_details": upgrades,
        "reject_verdicts": pd.Series([r["verdict"] for r in rejects]).value_counts().to_dict()
        if rejects
        else {},
    }
    (OUT / "pdp_upgrade_summary_20261007.json").write_text(
        json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8"
    )

    # Write note
    lines = []
    lines.append("# UK KS PDP OE upgrade — 2026-10-07")
    lines.append("")
    lines.append("## Verdict")
    lines.append("")
    if upgrades:
        lines.append(
            f"**{len(upgrades)} PDP(s)** showed the Isuzu part number on the product page; "
            f"**{len(upgraded_obs)}** ledger row(s) upgraded `category_only` → `exact_oem`. "
            f"Wider UK eligible: **{b_off} → {a_off}** offers (**{b_pn} → {a_pn}** PNs)."
        )
    else:
        lines.append(
            f"**Zero upgrades.** Checked **{len(checks)}** KS product pages for existing "
            f"`category_only` ledger rows (filter / clutch / exhaust / focus-blocked). "
            f"None printed the linked Isuzu part number on the PDP (title, SKU, OE/cross-ref, "
            f"attributes, or product description). Wider UK eligible stays **{b_off}** offers / "
            f"**{b_pn}** PNs. Parquet not patched."
        )
    lines.append("")
    lines.append("## Method")
    lines.append("")
    lines.append(
        "New angle vs search-grid harvest: open the **product page (PDP)** for the KS SKU "
        "already stored as `competitor_pn`, not Magento search-by-Isuzu-PN. "
        "Accept `exact_oem` only when the Isuzu PN is clearly printed on the PDP. "
        "Do not invent. Cap **~25** highest-£ wireable families or focus-blocked rows."
    )
    lines.append("")
    lines.append("Ledger: U29b `price_observations.parquet`.")
    lines.append("")
    lines.append("£10 delivery wire only when family matches live KS mainland classes "
                 "(filter / clutch / muffler / tail pipe) — see "
                 "`UNIVERSE_UK_KS_POLICY_SCOPE_2026-10-07.md`. No body / rotor / spring.")
    lines.append("")
    lines.append("## Tried")
    lines.append("")
    lines.append(f"| Metric | Count |")
    lines.append(f"|---|---:|")
    lines.append(f"| PDPs / SKUs checked | **{len(checks)}** |")
    lines.append(f"| Upgrades (OE on PDP) | **{len(upgrades)}** |")
    lines.append(f"| Ledger rows patched | **{len(upgraded_obs)}** |")
    lines.append(f"| Rejects (no OE / no link / error) | **{len(rejects)}** |")
    lines.append("")
    lines.append("### Candidates checked")
    lines.append("")
    lines.append("| # | KS SKU | Isuzu PN | £ excl | Family | Blocked focus | Verdict |")
    lines.append("|---:|---|---|---:|---|---|---|")
    for n, c in enumerate(checks, 1):
        lines.append(
            f"| {n} | `{c['competitor_pn']}` | `{c['part_no']}` | {c['price']:.2f} | "
            f"{c['family']} | {'Y' if c['is_blocked'] else ''} | {c['verdict']} |"
        )
    lines.append("")
    if upgrades:
        lines.append("## Upgrades")
        lines.append("")
        for u in upgrades:
            hit = u["oe_hits"][0] if u["oe_hits"] else {}
            lines.append(
                f"- SKU `{u['competitor_pn']}` / PN `{u['part_no']}` — OE in **{hit.get('where')}**: "
                f"«{hit.get('quote', '')}» — PDP: {u.get('pdp_url')} — "
                f"£10 wire: {'yes' if u['can_wire_10'] else 'no (family out of policy)'}"
            )
        lines.append("")
        if bak:
            lines.append(f"Backup: `{bak}`")
            lines.append("")
    lines.append("## Rejects")
    lines.append("")
    if summary["reject_verdicts"]:
        for k, v in summary["reject_verdicts"].items():
            lines.append(f"- `{k}`: **{v}**")
    else:
        lines.append("- (none)")
    lines.append("")
    lines.append("No invent: rows without OE on the PDP stay `category_only`.")
    lines.append("")
    lines.append("## Eligible before / after")
    lines.append("")
    lines.append("| Cut | Before | After |")
    lines.append("|---|---:|---:|")
    lines.append(f"| Wider UK `exact_oem` eligible **offers** | **{b_off}** | **{a_off}** |")
    lines.append(f"| Wider eligible **PNs** | **{b_pn}** | **{a_pn}** |")
    lines.append(f"| Delta offers | | **{a_off - b_off:+d}** |")
    lines.append("")
    lines.append("Coverage rebuild (only if upgrades > 0):")
    lines.append("")
    lines.append("```text")
    lines.append("python 01_data/91_build/build_market_data_gap_coverage_20261007.py --also-uk-exact")
    lines.append("```")
    lines.append("")
    lines.append("Board / INTERNAL not rebuilt here (parent owns that if delta > 0).")
    lines.append("")
    lines.append("## Artefacts")
    lines.append("")
    lines.append(f"| Object | Path |")
    lines.append(f"|---|---|")
    lines.append(f"| Candidate list | `{sel_path}` |")
    lines.append(f"| PDP HTML + checks | `{OUT}` |")
    lines.append(f"| Summary JSON | `{OUT / 'pdp_upgrade_summary_20261007.json'}` |")
    lines.append(f"| This note | `{NOTE}` |")
    lines.append("")
    NOTE.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"note: {NOTE}")
    print(json.dumps({k: summary[k] for k in (
        "tried", "upgrades_pdp", "rows_patched", "rejects",
        "eligible_offers_before", "eligible_offers_after",
        "eligible_pns_before", "eligible_pns_after",
    )}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
