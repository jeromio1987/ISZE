#!/usr/bin/env python3
"""
Build 2 — Join Book B provisional weights + revision exception queue.

Does NOT run +3% alloc or isze_pricing.cli alloc.

Inputs:
  01_data/00_derived/book_b_provisional_weights.csv   — network APL seeds (PN grain)
  01_data/00_derived/revision_exception_queue.csv     — PN × DB guardrails

Outputs (01_data/00_derived/):
  revision_book_b_review_pack.csv       — Book B PN × DB (where revision exists)
  revision_book_b_action_summary.csv    — counts by recommended_action × book_b_bucket
  revision_book_b_top_review.csv        — non-HOLD / non-RAISE_OK, top 500 by volume
  revision_book_b_pack.meta.json
"""
from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))

import db_dlr_commercial_common as C  # noqa: E402

BOOK_B = C.DERIVED / "book_b_provisional_weights.csv"
REVISION = C.DERIVED / "revision_exception_queue.csv"

OUT_PACK = C.DERIVED / "revision_book_b_review_pack.csv"
OUT_SUMMARY = C.DERIVED / "revision_book_b_action_summary.csv"
OUT_TOP = C.DERIVED / "revision_book_b_top_review.csv"
OUT_META = C.DERIVED / "revision_book_b_pack.meta.json"

BUILDER_VERSION = "revision-book-b-pack-v1"
TOP_REVIEW_CAP = 500

# Actions that do not need Jerome-first review in this pack
SKIP_ACTIONS = frozenset({"HOLD_DEFAULT", "RAISE_OK_ROOM_VS_IAM"})


def _load_book_b() -> pd.DataFrame:
    bb = pd.read_csv(BOOK_B, dtype={"pn": str})
    for col in ("l12m_eur", "growth_factor", "forecast_weight_eur"):
        if col in bb.columns:
            bb[col] = pd.to_numeric(bb[col], errors="coerce")
    bb["_pn"] = C.norm_pn(bb["pn"])
    return bb


def _load_revision() -> pd.DataFrame:
    rev = pd.read_csv(REVISION, dtype={"part_number": str, "distributor_code": str})
    for col in ("bill_qty", "bill_eur", "sellout_qty", "sell_through_ratio", "ks_price_index"):
        if col in rev.columns:
            rev[col] = pd.to_numeric(rev[col], errors="coerce")
    rev["_pn"] = C.norm_pn(rev["part_number"])
    return rev


def build_review_pack(bb: pd.DataFrame, rev: pd.DataFrame) -> pd.DataFrame:
    """
    Left join Book B (network PN) → revision queue (PN × DB).

    Grain mismatch: Book B has one row per network APL seed; revision is per DB
    with CY2025 bill/sell-out. A matched Book B PN may fan out to ≤4 DB rows.
    Book B PNs with no revision activity get a single row (distributor_code blank,
    recommended_action=NO_REVISION_ACTIVITY).
    """
    rev_slim = rev[
        [
            "_pn",
            "distributor_code",
            "part_number",
            "category",
            "bill_qty",
            "bill_eur",
            "sellout_qty",
            "pipeline_signal",
            "ks_price_index",
            "ks_has_quote",
            "recommended_action",
            "planned_sp_pct_chg_2025_2026",
            "proxy_adverse",
        ]
    ].copy()

    merged = bb.merge(rev_slim, on="_pn", how="left", suffixes=("", "_rev"))

    # Book B PNs never seen in revision queue → one placeholder row each
    no_rev = merged["distributor_code"].isna()
    merged.loc[no_rev, "recommended_action"] = "NO_REVISION_ACTIVITY"
    merged.loc[no_rev, "pipeline_signal"] = ""
    merged["grain"] = np.where(
        no_rev,
        "book_b_pn_only",
        "book_b_pn_x_db",
    )

    pack_cols = [
        "pn",
        "distributor_code",
        "grain",
        "description",
        "packs",
        "book_b_bucket",
        "growth_factor",
        "forecast_weight_eur",
        "l12m_eur",
        "status",
        "on_uti_p700_recommended",
        "category",
        "bill_qty",
        "bill_eur",
        "sellout_qty",
        "pipeline_signal",
        "ks_price_index",
        "ks_has_quote",
        "recommended_action",
        "planned_sp_pct_chg_2025_2026",
        "proxy_adverse",
        "flags",
    ]
    pack_cols = [c for c in pack_cols if c in merged.columns]
    out = merged[pack_cols].sort_values(
        ["book_b_bucket", "recommended_action", "forecast_weight_eur", "sellout_qty"],
        ascending=[True, True, False, False],
        na_position="last",
    )
    return out


def build_action_summary(pack: pd.DataFrame) -> pd.DataFrame:
    action = pack["recommended_action"].fillna("NO_REVISION_ACTIVITY")
    summary = (
        pack.assign(recommended_action=action)
        .groupby(["recommended_action", "book_b_bucket"], dropna=False)
        .size()
        .reset_index(name="row_count")
        .sort_values(["recommended_action", "row_count"], ascending=[True, False])
    )
    return summary


def build_top_review(pack: pd.DataFrame) -> pd.DataFrame:
    action = pack["recommended_action"].fillna("NO_REVISION_ACTIVITY")
    mask = ~action.isin(SKIP_ACTIONS)
    top = pack.loc[mask].copy()
    top["_sort_vol"] = top["sellout_qty"].fillna(0)
    top["_sort_fw"] = top["forecast_weight_eur"].fillna(0)
    top = top.sort_values(["_sort_vol", "_sort_fw"], ascending=[False, False])
    top = top.drop(columns=["_sort_vol", "_sort_fw"], errors="ignore")
    return top.head(TOP_REVIEW_CAP)


def main() -> int:
    if not BOOK_B.is_file():
        raise SystemExit(f"Missing Book B weights: {BOOK_B}")
    if not REVISION.is_file():
        raise SystemExit(f"Missing revision queue: {REVISION}")

    bb = _load_book_b()
    rev = _load_revision()

    pack = build_review_pack(bb, rev)
    pack.to_csv(OUT_PACK, index=False)

    summary = build_action_summary(pack)
    summary.to_csv(OUT_SUMMARY, index=False)

    top = build_top_review(pack)
    top.to_csv(OUT_TOP, index=False)

    bb_pn = int(bb["pn"].nunique())
    rev_pn = int(rev["part_number"].nunique())
    overlap_pn = int(bb["_pn"].isin(rev["_pn"]).sum())
    meta = {
        "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "builder_version": BUILDER_VERSION,
        "no_alloc_run": True,
        "inputs": {
            "book_b_provisional_weights": str(BOOK_B.relative_to(C.ISZE_ROOT)),
            "revision_exception_queue": str(REVISION.relative_to(C.ISZE_ROOT)),
        },
        "outputs": {
            "review_pack": str(OUT_PACK.relative_to(C.ISZE_ROOT)),
            "action_summary": str(OUT_SUMMARY.relative_to(C.ISZE_ROOT)),
            "top_review": str(OUT_TOP.relative_to(C.ISZE_ROOT)),
        },
        "grain": {
            "book_b": "network APL seed — one row per PN (no DB column)",
            "revision_queue": "PN × distributor_code (ITUK, UTI, IRELAND, IUK)",
            "review_pack": "Book B left-join revision — fan-out to PN×DB where activity exists; "
            "else single book_b_pn_only row with NO_REVISION_ACTIVITY",
        },
        "counts": {
            "book_b_pn": bb_pn,
            "revision_queue_rows": int(len(rev)),
            "revision_pn_unique": rev_pn,
            "book_b_pn_in_revision": overlap_pn,
            "review_pack_rows": int(len(pack)),
            "review_pack_pn_x_db": int((pack["grain"] == "book_b_pn_x_db").sum()),
            "review_pack_pn_only": int((pack["grain"] == "book_b_pn_only").sum()),
            "action_summary_rows": int(len(summary)),
            "top_review_rows": int(len(top)),
            "top_review_cap": TOP_REVIEW_CAP,
        },
        "action_counts_in_pack": pack["recommended_action"]
        .fillna("NO_REVISION_ACTIVITY")
        .value_counts()
        .to_dict(),
        "notes": [
            "Book B is network-level ambition seeds; revision guardrails are per DB — do not blend UTI≠UMI, IUK≠ITUK.",
            "NO_REVISION_ACTIVITY = Book B seed with no CY2025 bill/sell-out row in revision queue.",
            "Top review excludes HOLD_DEFAULT and RAISE_OK_ROOM_VS_IAM.",
            "Cannot apply ambition % or alloc targets until Jerome sets Book B target and runs alloc.",
        ],
    }
    with open(OUT_META, "w", encoding="utf-8") as fh:
        json.dump(meta, fh, indent=2)

    print("=== Build 2: revision × Book B pack ===")
    print(json.dumps(meta["counts"], indent=2))
    print(f"\nwrote {OUT_PACK}")
    print(f"wrote {OUT_SUMMARY}")
    print(f"wrote {OUT_TOP}")
    print(f"wrote {OUT_META}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
