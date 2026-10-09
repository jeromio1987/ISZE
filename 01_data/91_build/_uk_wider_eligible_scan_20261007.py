# -*- coding: utf-8 -*-
"""UK wider-eligible scan + optional KS £10 policy patch (filter/clutch/exhaust only).

Policy (live 2026-10-07 https://www.ks-international.com/delivery-information):
  "There is a minimum charge of UK Pounds £10.00 e.g. Filter kits, clutch kit,
   exhaust muffler, tail pipe etc"
  Separate sentence: additional (unspecified) charge for boxed body panels —
  do NOT apply £10 there.

Does not invent TMC rates or VAT %. Does not upgrade category_only → exact_oem.
"""
from __future__ import annotations

import argparse
import json
import re
import shutil
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
LEDGER = ROOT / "01_data" / "00_derived" / "price_observations.parquet"
FAMILY_FILE = ROOT / "01_data" / "00_derived" / "epc_decode_worklist.csv"
OUT_BUILD = ROOT / "01_data" / "91_build"
OUT_DERIVED = ROOT / "01_data" / "00_derived"

KS_NOTE = (
    'KS Delivery Information: "There is a minimum charge of UK Pounds £10.00 '
    'e.g. Filter kits, clutch kit, exhaust muffler, tail pipe etc" '
    "(Delivery & Carriage Charge Information / UK Mainland Delivery). "
    "Live page https://www.ks-international.com/delivery-information 2026-10-07."
)

# Families / keyword classes that match the KS £10 e.g. list (filter / clutch / exhaust).
POLICY_FAMILIES = {
    "oil_filter",
    "air_filter",
    "fuel_filter",
    "blower_filter",
    "cabin_filter",
    "pollen_filter",
    "clutch_kit",
    "clutch_disc",
    "clutch_cover",
    "clutch_pressure_plate",
    "clutch_release_bearing",
    "exhaust",
    "muffler",
    "silencer",
    "tail_pipe",
    "exhaust_pipe",
}

# Explicit exclude: body panels (policy names a separate unspecified charge).
BODY_PANEL_RE = re.compile(
    r"\b(BUMPER|DOOR|FRONT PANEL|GRILLE|GRILL|WING|FENDER|BONNET|HOOD|"
    r"TAILGATE|CAB PANEL|BODY PANEL)\b",
    re.I,
)

FILTER_RE = re.compile(r"\bFILTER\b", re.I)
CLUTCH_RE = re.compile(r"\bCLUTCH\b", re.I)
# Include Isuzu EPC "PIPE; EXH" — exhaust pipe, same class as page examples
# muffler / tail pipe. Do not match bare "EXH" in unrelated codes.
EXHAUST_RE = re.compile(
    r"\b(EXHAUST|MUFFLER|SILENCER|TAIL\s*PIPE|TAILPIPE)\b|"
    r"\bPIPE\s*;\s*EXH\b|"
    r"\bEXH\s*;\s*PIPE\b",
    re.I,
)


def load_family_map() -> dict[str, str]:
    if not FAMILY_FILE.exists():
        return {}
    fam = pd.read_csv(FAMILY_FILE, dtype={"part_number": str})
    return dict(zip(fam["part_number"].astype(str), fam["pms_category"].astype(str)))


def policy_class(desc: str | None, pms: str | None) -> str | None:
    """Return 'filter' | 'clutch' | 'exhaust' if £10 policy applies, else None."""
    d = str(desc or "")
    if BODY_PANEL_RE.search(d):
        return None
    if pms is None or (isinstance(pms, float) and pd.isna(pms)):
        p = ""
    else:
        p = str(pms).strip().lower()
    if p in POLICY_FAMILIES:
        if "filter" in p:
            return "filter"
        if "clutch" in p:
            return "clutch"
        if p in {"exhaust", "muffler", "silencer", "tail_pipe", "exhaust_pipe"}:
            return "exhaust"
        return "filter" if "filter" in p else p
    if FILTER_RE.search(d):
        return "filter"
    if CLUTCH_RE.search(d):
        return "clutch"
    if EXHAUST_RE.search(d):
        return "exhaust"
    return None


def delivery_complete(row: pd.Series) -> bool:
    di = row.get("delivery_included")
    if di is None or (isinstance(di, float) and pd.isna(di)):
        return False
    s = str(di).strip().lower()
    if s == "yes":
        return True
    if s == "no":
        c = row.get("delivery_cost_amount")
        return c is not None and not (isinstance(c, float) and pd.isna(c))
    return False


def tax_ok(row: pd.Series) -> bool:
    return str(row.get("vat") or "").strip().lower() in {"excl", "incl"}


def scan(df: pd.DataFrame, fmap: dict[str, str]) -> dict:
    uk = df[df["country"] == "UK"].copy()
    uk["pms_category"] = uk["part_no"].astype(str).map(fmap)
    uk["policy_class"] = [
        policy_class(d, p) for d, p in zip(uk["description"], uk["pms_category"])
    ]
    exact = uk[uk["match_method"].astype(str).str.lower() == "exact_oem"].copy()
    focus = {"brake_pad", "oil_filter"}
    exact["in_focus"] = exact["pms_category"].isin(focus)
    exact["del_ok"] = exact.apply(delivery_complete, axis=1)
    exact["tax_ok"] = exact.apply(tax_ok, axis=1)
    exact["ready_ledger"] = (
        exact["price"].notna() & exact["del_ok"] & exact["tax_ok"]
    )

    ks = exact[exact["loader"].astype(str).str.lower().str.startswith("ks")].copy()
    need_patch = ks[~ks["del_ok"]].copy()
    need_patch["would_patch"] = need_patch["policy_class"].notna()

    return {
        "uk_rows": int(len(uk)),
        "uk_exact_oem": int(len(exact)),
        "exact_by_loader": exact["loader"].value_counts().to_dict(),
        "exact_by_family": exact["pms_category"]
        .fillna("(none)")
        .value_counts()
        .to_dict(),
        "exact_in_focus": int(exact["in_focus"].sum()),
        "exact_outside_focus": int((~exact["in_focus"]).sum()),
        "exact_tax_ok": int(exact["tax_ok"].sum()),
        "exact_del_ok": int(exact["del_ok"].sum()),
        "exact_ready_ledger": int(exact["ready_ledger"].sum()),
        "exact_ready_in_focus": int((exact["ready_ledger"] & exact["in_focus"]).sum()),
        "exact_ready_outside": int((exact["ready_ledger"] & ~exact["in_focus"]).sum()),
        "ks_exact_oem": int(len(ks)),
        "ks_need_delivery_fill": int(len(need_patch)),
        "ks_policy_match_need_fill": int(need_patch["would_patch"].sum()),
        "ks_policy_match_by_class": need_patch.loc[need_patch["would_patch"], "policy_class"]
        .value_counts()
        .to_dict(),
        "ks_skipped_non_policy": int((~need_patch["would_patch"]).sum()),
        "ks_skipped_by_family": need_patch.loc[~need_patch["would_patch"], "pms_category"]
        .fillna("(none)")
        .value_counts()
        .head(20)
        .to_dict(),
        "patch_obs_ids": need_patch.loc[need_patch["would_patch"], "obs_id"].astype(str).tolist(),
        "patch_detail": need_patch.loc[need_patch["would_patch"]][
            ["obs_id", "part_no", "loader", "pms_category", "policy_class", "vat", "description"]
        ].to_dict(orient="records"),
    }


def apply_ks_patch(df: pd.DataFrame, obs_ids: list[str]) -> tuple[pd.DataFrame, int]:
    ids = set(obs_ids)
    n = 0
    for i in df.index:
        if str(df.at[i, "obs_id"]) not in ids:
            continue
        if str(df.at[i, "country"]) != "UK":
            continue
        # only fill blanks / incomplete — never overwrite a yes or a different cost
        di = df.at[i, "delivery_included"]
        di_s = None if di is None or (isinstance(di, float) and pd.isna(di)) else str(di).strip().lower()
        cost = df.at[i, "delivery_cost_amount"]
        cost_missing = cost is None or (isinstance(cost, float) and pd.isna(cost))
        if di_s == "yes":
            continue
        if di_s == "no" and not cost_missing:
            continue
        df.at[i, "delivery_included"] = "no"
        df.at[i, "delivery_note"] = KS_NOTE
        df.at[i, "delivery_cost_amount"] = 10.0
        df.at[i, "delivery_cost_currency"] = "GBP"
        n += 1
    return df, n


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply-patch", action="store_true", help="Write KS £10 onto policy-matching rows")
    ap.add_argument("--dry-run", action="store_true", help="Scan only (default)")
    args = ap.parse_args()
    if not LEDGER.exists():
        raise SystemExit(f"missing ledger: {LEDGER}")

    fmap = load_family_map()
    df = pd.read_parquet(LEDGER)
    report = scan(df, fmap)
    report["built_at"] = datetime.now(timezone.utc).isoformat(timespec="seconds")
    report["ledger"] = str(LEDGER)
    report["policy_quote"] = (
        "There is a minimum charge of UK Pounds £10.00 e.g. Filter kits, clutch kit, "
        "exhaust muffler, tail pipe etc"
    )
    report["policy_url"] = "https://www.ks-international.com/delivery-information"
    report["patched"] = 0

    if args.apply_patch and not args.dry_run:
        bak = LEDGER.with_suffix(
            LEDGER.suffix
            + f".bak_{datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')}_before_ks_wider_10"
        )
        shutil.copy2(LEDGER, bak)
        df2, n = apply_ks_patch(df, report["patch_obs_ids"])
        df2.to_parquet(LEDGER, index=False)
        report["patched"] = n
        report["backup"] = str(bak)
        # re-scan after patch
        report_after = scan(df2, fmap)
        report["after"] = {
            "exact_ready_ledger": report_after["exact_ready_ledger"],
            "exact_ready_in_focus": report_after["exact_ready_in_focus"],
            "exact_ready_outside": report_after["exact_ready_outside"],
            "ks_need_delivery_fill": report_after["ks_need_delivery_fill"],
        }

    out_json = OUT_BUILD / "_uk_wider_eligible_scan_20261007.json"
    # drop huge detail from console; keep in file
    out_json.write_text(json.dumps(report, indent=2, ensure_ascii=False, default=str), encoding="utf-8")
    print(json.dumps({k: v for k, v in report.items() if k != "patch_detail"}, indent=2, default=str))
    print("WROTE", out_json)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
