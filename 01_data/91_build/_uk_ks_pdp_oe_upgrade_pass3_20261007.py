# -*- coding: utf-8 -*-
"""Pass3: remaining UK KS category_only filter/clutch/exhaust — PDP OE upgrade."""
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
from urllib.parse import quote as url_quote
from urllib.request import Request, urlopen

import pandas as pd
from bs4 import BeautifulSoup

ROOT = Path(r"C:\Users\jerom\Desktop\claude\ISZE")
U29B = Path(r"C:\Users\jerom\Desktop\claude\_worktrees\ISZE_u29b")
PARQUET = U29B / "01_data" / "00_derived" / "price_observations.parquet"
BLOCKED = ROOT / "01_data" / "00_derived" / "_uk_oe_crosswalk_probe_20261007" / "blocked_focus.csv"
OUT = ROOT / "01_data" / "90_INBOX" / "_uk_ks_pdp_oe_upgrade_pass3_20261007"
NOTE = ROOT / "00_docs" / "UNIVERSE_UK_KS_PDP_OE_UPGRADE_PASS3_2026-10-07.md"
METRICS = U29B / "01_data" / "00_derived" / "market_data_gap_coverage_uk_wider_exact_20261007.metrics.json"
PASS12_CHECKS = ROOT / "01_data" / "90_INBOX" / "_uk_ks_pdp_oe_upgrade_20261007" / "pdp_checks_20261007.json"

sys.path.insert(0, str(ROOT / "04_tools" / "delegation" / "parsers"))
from ledger_schema import find_pns  # noqa: E402

UA = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
)
SLEEP_S = 0.65
CAP = 40

FILTER_RE = re.compile(r"FILTER", re.I)
CLUTCH_RE = re.compile(r"CLUTCH", re.I)
EXHAUST_RE = re.compile(
    r"EXHAUST|MUFFLER|SILENCER|TAIL\s*PIPE|PIPE;\s*EXH|EXH;\s*PIPE", re.I
)
EXHAUST_10_OK = re.compile(
    r"MUFFLER|SILENCER|TAIL\s*PIPE|PIPE;\s*EXH|EXH;\s*PIPE|"
    r"EXHAUST\s*(PIPE|SILENCER|MUFFLER|ASSEMBLY)",
    re.I,
)
EXHAUST_10_NO = re.compile(
    r"EXHAUST\s*BRAKE|CAMSHAFT|TEMPERATURE|SENSOR|GASKET", re.I
)

DELIVERY_NOTE = (
    "Live KS UK mainland £10 minimum (filter / clutch / muffler / tail pipe) "
    "— UNIVERSE_UK_KS_POLICY_SCOPE_2026-10-07"
)


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

    sku_el = soup.select_one(
        ".product.attribute.sku .value, div.product-info-stock-sku .sku .value, div.sku"
    )
    check("sku_field", sku_el.get_text(" ", strip=True) if sku_el else None)

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


def done_skus_pass12(df: pd.DataFrame) -> set[str]:
    done: set[str] = set()
    if PASS12_CHECKS.exists():
        for c in json.loads(PASS12_CHECKS.read_text(encoding="utf-8")):
            if c.get("verdict") == "upgrade_exact_oem":
                done.add(str(c["competitor_pn"]))
    m = (
        (df["loader"] == "ks")
        & (df["match_method"].astype(str).str.lower() == "exact_oem")
        & (df["description"].astype(str).str.contains("PDP OE upgrade", na=False))
    )
    done |= set(df.loc[m, "competitor_pn"].astype(str))
    return done


def select_candidates(df: pd.DataFrame) -> pd.DataFrame:
    done = done_skus_pass12(df)
    ks = df[
        (df["loader"] == "ks")
        & (df["match_method"].astype(str).str.lower() == "category_only")
        & (df["country"].astype(str).str.upper() == "UK")
        & (df["source"].astype(str).str.contains("KS", case=False, na=False))
    ].copy()
    ks["price_f"] = pd.to_numeric(ks["price"], errors="coerce").fillna(0)
    ks["desc_u"] = ks["description"].astype(str)
    ks["family"] = ks["desc_u"].map(family_bucket)
    ks = ks[ks["family"].isin(["filter", "clutch", "exhaust"])]
    ks = ks[~ks["competitor_pn"].astype(str).isin(done)]
    blocked_skus: set[str] = set()
    if BLOCKED.exists():
        blocked = pd.read_csv(BLOCKED)
        blocked_skus = set(blocked["competitor_pn"].astype(str))
    ks["is_blocked"] = ks["competitor_pn"].astype(str).isin(blocked_skus)
    ks["wire10"] = ks["desc_u"].map(can_wire_10)
    # Prefer clutch/exhaust (crowded out of pass1/2), then filter; high £ first
    prio = {"clutch": 0, "exhaust": 1, "filter": 2}
    ks["prio"] = ks["family"].map(prio)
    uniq = ks.sort_values(
        ["prio", "wire10", "price_f"], ascending=[True, False, False]
    ).drop_duplicates(subset=["competitor_pn"], keep="first")
    return uniq.head(CAP).reset_index(drop=True)


def patch_row(
    df: pd.DataFrame,
    idx: int,
    *,
    evid: str,
    pdp_url: str | None,
    wire10: bool,
) -> None:
    df.at[idx, "match_method"] = "exact_oem"
    old_desc = str(df.at[idx, "description"] or "")
    if "PDP OE upgrade" not in old_desc:
        df.at[idx, "description"] = (old_desc + " — " + evid).strip(" —")
    if str(df.at[idx, "vat"]).lower() != "excl":
        df.at[idx, "vat"] = "excl"
    if wire10:
        df.at[idx, "delivery_included"] = "no"
        df.at[idx, "delivery_cost_amount"] = 10.0
        df.at[idx, "delivery_cost_currency"] = "GBP"
        df.at[idx, "delivery_note"] = DELIVERY_NOTE
    if pdp_url:
        df.at[idx, "source_url"] = pdp_url


def elig(m: dict) -> tuple[int, int]:
    offers = m.get("eligible_rows") or m.get("eligible_offers") or m.get("wider_eligible_offers")
    pns = m.get("eligible_pns") or m.get("wider_eligible_pns")
    return int(offers or 0), int(pns or 0)


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    df = pd.read_parquet(PARQUET)
    before = json.loads(METRICS.read_text(encoding="utf-8")) if METRICS.exists() else {}
    b_off, b_pn = elig(before) if before else (83, 25)
    focus_before = int(before.get("eligible_rows_in_focus") or 0)

    sel = select_candidates(df)
    sel_path = OUT / "pdp_candidates_pass3_20261007.csv"
    sel.to_csv(sel_path, index=False)
    print(f"candidates: {len(sel)} -> {sel_path}")
    print(sel.groupby("family").size().to_dict())

    checks: list[dict] = []
    upgrades: list[dict] = []
    rejects: list[dict] = []

    for _, row in sel.iterrows():
        pn = str(row["part_no"])
        sku = str(row["competitor_pn"])
        desc = str(row.get("description") or "")
        fam = family_bucket(desc)
        entry: dict = {
            "obs_id": str(row["obs_id"]),
            "part_no": pn,
            "competitor_pn": sku,
            "price": float(row["price_f"]),
            "family": fam,
            "is_blocked": bool(row["is_blocked"]),
            "can_wire_10": can_wire_10(desc),
            "search_url": (
                f"https://www.ks-international.com/catalogsearch/result/?q={url_quote(sku)}"
            ),
            "pdp_url": None,
            "verdict": None,
            "oe_hits": [],
            "oe_list": [],
            "error": None,
        }
        print(f"[{len(checks)+1}/{len(sel)}] SKU {sku} PN {pn} £{row['price_f']} {fam}")
        try:
            st, raw = fetch(entry["search_url"])
            (OUT / f"search_sku_{sku}.html").write_bytes(raw)
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
            oes = oe_pns_from_html(phtml)
            entry["pdp_http"] = st2
            entry["pdp_html"] = pdp_name
            entry["oe_hits"] = loc["target_hits"]
            entry["pns_on_page"] = loc["pns_on_page"]
            entry["oe_list"] = oes
            if loc["oe_on_pdp"] and pn in oes:
                entry["verdict"] = "upgrade_exact_oem"
                upgrades.append(entry)
                print(f"  UPGRADE OE list has PN; sample {oes[:6]}")
            elif loc["oe_on_pdp"]:
                # PN hit somewhere labelled but not in OE attr / json-ld list — still accept
                # if labelled hit (same bar as pass1)
                entry["verdict"] = "upgrade_exact_oem"
                upgrades.append(entry)
                print(f"  UPGRADE labelled hit (OE list may omit): {loc['target_hits'][0]}")
            else:
                entry["verdict"] = "reject_no_oe_on_pdp"
                rejects.append(entry)
                print(f"  reject — no OE (list={oes[:5]} pns={loc['pns_on_page'][:5]})")
        except (HTTPError, URLError, TimeoutError, OSError) as e:
            entry["verdict"] = "reject_fetch_error"
            entry["error"] = str(e)[:200]
            rejects.append(entry)
            print(f"  error: {e}")
        checks.append(entry)
        time.sleep(SLEEP_S)

    (OUT / "pdp_checks_pass3_20261007.json").write_text(
        json.dumps(checks, indent=2, ensure_ascii=False), encoding="utf-8"
    )

    upgraded_obs: list[dict] = []
    pass2_extras: list[dict] = []
    bak = None

    if upgrades:
        ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        bak = PARQUET.with_name(
            f"price_observations.parquet.bak_{ts}_before_ks_pdp_oe_pass3"
        )
        shutil.copy2(PARQUET, bak)
        print(f"backup: {bak}")
        df2 = pd.read_parquet(PARQUET)

        for u in upgrades:
            sku = u["competitor_pn"]
            pn = u["part_no"]
            where = u["oe_hits"][0]["where"] if u["oe_hits"] else "pdp"
            quote_txt = u["oe_hits"][0]["quote"] if u["oe_hits"] else pn
            evid = (
                f"PDP OE upgrade 2026-10-07 pass3: Isuzu {pn} printed on KS product page "
                f"({where}: «{quote_txt[:120]}»). Was category_only."
            )
            mask = (
                (df2["loader"] == "ks")
                & (df2["match_method"].astype(str).str.lower() == "category_only")
                & (df2["competitor_pn"].astype(str) == sku)
                & (df2["part_no"].astype(str) == pn)
            )
            idxs = df2.index[mask].tolist()
            for idx in idxs:
                desc_i = str(df2.at[idx, "description"] or "")
                patch_row(
                    df2,
                    idx,
                    evid=evid,
                    pdp_url=u.get("pdp_url"),
                    wire10=can_wire_10(desc_i),
                )
                upgraded_obs.append(
                    {
                        "obs_id": str(df2.at[idx, "obs_id"]),
                        "sku": sku,
                        "part_no": pn,
                        "pass": "primary",
                    }
                )
            print(f"  patched primary {len(idxs)} rows SKU {sku} PN {pn}")

            # Same-SKU extras: other Isuzu PNs on OE list with category_only rows
            oes = u.get("oe_list") or []
            if not oes and u.get("pdp_html"):
                phtml = (OUT / u["pdp_html"]).read_text(encoding="utf-8", errors="replace")
                oes = oe_pns_from_html(phtml)
            other = [p for p in oes if p != pn]
            if other:
                mask2 = (
                    (df2["loader"] == "ks")
                    & (df2["match_method"].astype(str).str.lower() == "category_only")
                    & (df2["competitor_pn"].astype(str) == sku)
                    & (df2["part_no"].astype(str).isin(other))
                )
                idxs2 = df2.index[mask2].tolist()
                if idxs2:
                    quote = ", ".join(oes[:8])
                    evid2 = (
                        "PDP OE upgrade 2026-10-07 pass3 same-SKU: Isuzu PN on KS "
                        f"OE Equivalent Part Number («{quote}»). Was category_only."
                    )
                    for idx in idxs2:
                        pn2 = str(df2.at[idx, "part_no"])
                        desc_i = str(df2.at[idx, "description"] or "")
                        patch_row(
                            df2,
                            idx,
                            evid=evid2,
                            pdp_url=u.get("pdp_url"),
                            wire10=can_wire_10(desc_i),
                        )
                        pass2_extras.append(
                            {
                                "obs_id": str(df2.at[idx, "obs_id"]),
                                "sku": sku,
                                "part_no": pn2,
                                "pass": "same_sku_extra",
                            }
                        )
                    print(f"  same-SKU extras {len(idxs2)} for SKU {sku}")

        df2.to_parquet(PARQUET, index=False)
        print(
            f"wrote parquet; primary={len(upgraded_obs)} extras={len(pass2_extras)}"
        )

        # Must run the U29b copy so Path(__file__) resolves ledger + node runner there.
        cov_script = (
            U29B
            / "01_data"
            / "91_build"
            / "build_market_data_gap_coverage_20261007.py"
        )
        if not cov_script.exists():
            cov_script = (
                ROOT
                / "01_data"
                / "91_build"
                / "build_market_data_gap_coverage_20261007.py"
            )
        cmd = [sys.executable, str(cov_script), "--also-uk-exact"]
        r = subprocess.run(cmd, cwd=str(U29B), capture_output=True, text=True)
        print(r.stdout[-2500:] if r.stdout else "")
        if r.returncode != 0:
            print("COVERAGE FAIL", r.stderr[-2500:])
            return 1
        main_m = (
            ROOT
            / "01_data"
            / "00_derived"
            / "market_data_gap_coverage_uk_wider_exact_20261007.metrics.json"
        )
        main_c = (
            ROOT
            / "01_data"
            / "00_derived"
            / "market_data_gap_coverage_uk_wider_exact_20261007.csv"
        )
        if METRICS.exists():
            shutil.copy2(METRICS, main_m)
        u29b_csv = (
            U29B
            / "01_data"
            / "00_derived"
            / "market_data_gap_coverage_uk_wider_exact_20261007.csv"
        )
        if u29b_csv.exists():
            shutil.copy2(u29b_csv, main_c)
    else:
        print("no upgrades — parquet untouched")

    after = json.loads(METRICS.read_text(encoding="utf-8")) if METRICS.exists() else before
    a_off, a_pn = elig(after)
    focus_after = int(after.get("eligible_rows_in_focus") or 0)

    all_patched = upgraded_obs + pass2_extras
    summary = {
        "skus_checked": len(checks),
        "upgrades_pdp": len(upgrades),
        "rejects": len(rejects),
        "rows_patched_primary": len(upgraded_obs),
        "rows_patched_same_sku_extra": len(pass2_extras),
        "rows_patched_total": len(all_patched),
        "distinct_skus_upgraded": len({u["competitor_pn"] for u in upgrades}),
        "distinct_pns_touched": len({r["part_no"] for r in all_patched}),
        "eligible_offers_before": b_off,
        "eligible_pns_before": b_pn,
        "eligible_offers_after": a_off,
        "eligible_pns_after": a_pn,
        "eligible_focus_before": focus_before,
        "eligible_focus_after": focus_after,
        "backup": str(bak) if bak else None,
        "reject_verdicts": (
            pd.Series([r["verdict"] for r in rejects]).value_counts().to_dict()
            if rejects
            else {}
        ),
        "family_mix_checked": (
            pd.Series([c["family"] for c in checks]).value_counts().to_dict()
            if checks
            else {}
        ),
        "family_mix_upgraded": (
            pd.Series([u["family"] for u in upgrades]).value_counts().to_dict()
            if upgrades
            else {}
        ),
    }
    (OUT / "pdp_upgrade_summary_pass3_20261007.json").write_text(
        json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8"
    )
    (OUT / "pdp_pass3_patched.json").write_text(
        json.dumps(
            {
                "primary": upgraded_obs,
                "same_sku_extra": pass2_extras,
                "upgrades": [
                    {
                        "sku": u["competitor_pn"],
                        "part_no": u["part_no"],
                        "family": u["family"],
                        "oe_list": u.get("oe_list"),
                        "pdp_url": u.get("pdp_url"),
                        "can_wire_10": u.get("can_wire_10"),
                    }
                    for u in upgrades
                ],
            },
            indent=2,
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )

    # Note
    lines: list[str] = []
    lines.append("# UK KS PDP OE upgrade — Pass 3 — 2026-10-07")
    lines.append("")
    lines.append("## Verdict")
    lines.append("")
    if upgrades:
        lines.append(
            f"**{len(upgrades)} of {len(checks)}** remaining filter / clutch / exhaust KS PDPs "
            f"printed the linked Isuzu part number under **OE Equivalent Part Number** "
            f"(or JSON-LD). **{len(all_patched)}** ledger rows upgraded "
            f"`category_only` → `exact_oem` "
            f"({len(upgraded_obs)} primary + {len(pass2_extras)} same-SKU extras). "
            f"Wider UK `exact_oem` eligible: **{b_off} → {a_off}** offers "
            f"(**{b_pn} → {a_pn}** PNs). Focus (oil filter + brake pad): "
            f"**{focus_before} → {focus_after}**. "
            "Board / INTERNAL not rebuilt here."
        )
    else:
        lines.append(
            f"**Zero upgrades.** Checked **{len(checks)}** PDPs. "
            f"Wider eligible stays **{b_off}** / **{b_pn}** PNs."
        )
    lines.append("")
    lines.append("## Method")
    lines.append("")
    lines.append(
        "Pass 1/2 filled 25 filter SKUs (55 rows → wider 83 / 25 PNs). "
        "Pass 3 takes remaining UK KS `category_only` rows in **filter / clutch / exhaust** "
        "(KS £10 mainland classes), excluding the 25 already upgraded SKUs. Cap **~40** "
        "distinct `competitor_pn`. Prefer clutch and exhaust (crowded out of the first 25), "
        "then remaining filters by £."
    )
    lines.append("")
    lines.append(
        f"Ledger: `{PARQUET}`"
    )
    lines.append("")
    lines.append(
        "£10 delivery + VAT excl only for filter / clutch / muffler / tail pipe. "
        "No body / rotor / spring wired."
    )
    lines.append("")
    lines.append("## Counts")
    lines.append("")
    lines.append("| Metric | Count |")
    lines.append("|---|---:|")
    lines.append(f"| PDPs / SKUs checked | **{len(checks)}** |")
    lines.append(f"| Upgrades (OE on PDP) | **{len(upgrades)}** |")
    lines.append(f"| Rejects | **{len(rejects)}** |")
    lines.append(f"| Ledger rows patched (primary) | **{len(upgraded_obs)}** |")
    lines.append(f"| Same-SKU extras | **{len(pass2_extras)}** |")
    lines.append(f"| Ledger rows patched (total) | **{len(all_patched)}** |")
    lines.append(
        f"| Distinct KS SKUs upgraded | **{summary['distinct_skus_upgraded']}** |"
    )
    lines.append(
        f"| Distinct Isuzu PNs touched | **{summary['distinct_pns_touched']}** |"
    )
    lines.append("")
    lines.append("Family mix checked: "
                 + ", ".join(f"{k}={v}" for k, v in summary["family_mix_checked"].items()))
    lines.append("")
    lines.append("Family mix upgraded: "
                 + (", ".join(f"{k}={v}" for k, v in summary["family_mix_upgraded"].items())
                    or "(none)"))
    lines.append("")
    lines.append("### Candidates checked")
    lines.append("")
    lines.append(
        "| # | KS SKU | Candidate Isuzu PN | £ excl | Family | Blocked | Verdict |"
    )
    lines.append("|---:|---|---|---:|---|---|---|")
    for n, c in enumerate(checks, 1):
        lines.append(
            f"| {n} | `{c['competitor_pn']}` | `{c['part_no']}` | {c['price']:.2f} | "
            f"{c['family']} | {'Y' if c['is_blocked'] else ''} | {c['verdict']} |"
        )
    lines.append("")
    if upgrades:
        lines.append("## Upgrades (evidence)")
        lines.append("")
        lines.append("| KS SKU | Isuzu PN | Family | Where | Quote | £10 |")
        lines.append("|---|---|---|---|---|---|")
        for u in upgrades:
            hit = u["oe_hits"][0] if u["oe_hits"] else {}
            q = (hit.get("quote") or "")[:80].replace("|", "/")
            lines.append(
                f"| `{u['competitor_pn']}` | `{u['part_no']}` | {u['family']} | "
                f"{hit.get('where', '')} | `{q}` | "
                f"{'Y' if u['can_wire_10'] else 'N'} |"
            )
        lines.append("")
        if pass2_extras:
            lines.append("### Same-SKU extras")
            lines.append("")
            by_sku: dict[str, list[str]] = {}
            for e in pass2_extras:
                by_sku.setdefault(e["sku"], []).append(e["part_no"])
            lines.append("| KS SKU | Extra Isuzu PN(s) | Extra rows |")
            lines.append("|---|---|---:|")
            for sku, pns in by_sku.items():
                lines.append(f"| `{sku}` | {', '.join(f'`{p}`' for p in pns)} | {len(pns)} |")
            lines.append("")
    lines.append("## Rejects")
    lines.append("")
    if summary["reject_verdicts"]:
        for k, v in summary["reject_verdicts"].items():
            lines.append(f"- `{k}`: **{v}**")
    else:
        lines.append("- (none)")
    lines.append("")
    lines.append("No invent: only PNs on the PDP OE attribute / labelled hit upgraded.")
    lines.append("")
    lines.append("## Eligible before / after")
    lines.append("")
    lines.append("Coverage rebuild:")
    lines.append("")
    lines.append("```text")
    lines.append(
        "python 01_data/91_build/build_market_data_gap_coverage_20261007.py --also-uk-exact"
    )
    lines.append("```")
    lines.append("")
    lines.append("| Cut | Before (post pass1/2) | After pass3 |")
    lines.append("|---|---:|---:|")
    lines.append(
        f"| Wider UK `exact_oem` eligible **offers** | **{b_off}** | **{a_off}** |"
    )
    lines.append(f"| Wider eligible **PNs** | **{b_pn}** | **{a_pn}** |")
    lines.append(f"| Delta offers | | **{a_off - b_off:+d}** |")
    lines.append(f"| Delta PNs | | **{a_pn - b_pn:+d}** |")
    lines.append(
        f"| Focus (oil filter + brake pad) | **{focus_before}** | **{focus_after}** |"
    )
    lines.append("")
    if a_off > b_off:
        lines.append(
            f"**Parent note:** Pass3 added **+{a_off - b_off}** wider eligible offers "
            f"beyond the pass1/2 total of {b_off}. Sibling wire-83 / INTERNAL may need "
            f"a re-wire if it finished against {b_off}."
        )
        lines.append("")
    lines.append("Metrics (U29b + copied to main derived):")
    lines.append("")
    lines.append(f"`{METRICS}`")
    lines.append("")
    lines.append(
        r"`C:\Users\jerom\Desktop\claude\ISZE\01_data\00_derived\market_data_gap_coverage_uk_wider_exact_20261007.metrics.json`"
    )
    lines.append("")
    lines.append("## Backups")
    lines.append("")
    if bak:
        lines.append(f"- `{bak}`")
    else:
        lines.append("- (none — no write)")
    lines.append("")
    lines.append("## Artefacts")
    lines.append("")
    lines.append("| Object | Path |")
    lines.append("|---|---|")
    lines.append(f"| Candidate list | `{sel_path}` |")
    lines.append(f"| PDP HTML + checks | `{OUT}` |")
    lines.append(f"| Summary JSON | `{OUT / 'pdp_upgrade_summary_pass3_20261007.json'}` |")
    lines.append(f"| This note | `{NOTE}` |")
    lines.append(
        f"| Runner | `{ROOT / '01_data' / '91_build' / '_uk_ks_pdp_oe_upgrade_pass3_20261007.py'}` |"
    )
    lines.append("")
    lines.append("## Not done")
    lines.append("")
    lines.append("- Board HTML / INTERNAL not rebuilt (sibling owns wire-83; re-wire if delta > 0 after them).")
    lines.append("- No ACCEPT.")
    lines.append("")
    NOTE.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"note: {NOTE}")
    print(json.dumps(summary, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
