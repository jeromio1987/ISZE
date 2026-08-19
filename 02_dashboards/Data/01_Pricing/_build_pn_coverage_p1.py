"""P1 data foundation — coverage classification + supersession map.

Outputs (01_data/00_derived/):
  - pn_coverage_classification.csv (+ .meta.json)
  - pn_supersession_map.csv (+ .meta.json)

No email / Graph. Safe to re-run. Does not mutate PR00 parquet.
"""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
DER = ROOT / "01_data" / "00_derived"


def norm_pn(v) -> str:
    if v is None or (isinstance(v, float) and pd.isna(v)):
        return ""
    s = str(v).strip().upper().replace(" ", "")
    if s.endswith(".0") and s[:-2].isdigit():
        s = s[:-2]
    if s.isdigit():
        s = s.lstrip("0") or "0"
    return s


def usable_pr00_set(pr: pd.DataFrame) -> set[str]:
    sp = pd.to_numeric(pr["sp_eur"], errors="coerce")
    m = sp.notna() & (sp > 0)
    return set(pr.loc[m, "pn"].astype(str))


def main() -> None:
    ranked = pd.read_csv(DER / "no_pr00_gap_cy2025_ranked.csv")
    closed = pd.read_csv(DER / "no_pr00_gap_cy2025_closed_20260812.csv")
    gap_meta = json.loads((DER / "no_pr00_gap_cy2025_ranked.meta.json").read_text(encoding="utf-8"))

    pr = pd.read_parquet(DER / "pricing_pr00_ie40.parquet")
    pr = pr.copy()
    pr["pn"] = pr["part_number"].map(norm_pn)
    pr["newest"] = pr["newest_pn"].map(norm_pn)
    usable = usable_pr00_set(pr)

    sales = pd.read_parquet(
        DER / "sales_fact.parquet",
        columns=["part_number", "year", "net_sales_value", "description"],
    )
    sales = sales[sales["year"] == 2025].copy()
    sales["pn"] = sales["part_number"].map(norm_pn)
    sales = sales[sales["pn"] != ""]
    sales["net_sales_value"] = pd.to_numeric(sales["net_sales_value"], errors="coerce").fillna(0.0)
    by_pn = (
        sales.groupby("pn", as_index=False)
        .agg(
            cy2025_eur=("net_sales_value", "sum"),
            billed_qty=("net_sales_value", "size"),
            description=("description", "first"),
        )
        .query("cy2025_eur > 0")
    )
    total_parts = float(by_pn["cy2025_eur"].sum())

    # --- supersession map from current IE40 (old → newest) ---
    chain = (
        pr.loc[pr["pn"] != "", ["pn", "newest", "description", "is_superseded_row", "sp_eur"]]
        .drop_duplicates(subset=["pn", "newest"])
        .copy()
    )
    chain = chain[chain["newest"] != ""]
    # Prefer row that marks superseded when pn != newest
    chain["is_superseded_row"] = chain["is_superseded_row"].fillna(False)
    chain = chain.sort_values(["pn", "is_superseded_row"], ascending=[True, False])
    chain = chain.drop_duplicates(subset=["pn"], keep="first")
    chain["maps_to_self"] = chain["pn"] == chain["newest"]
    chain["newest_has_usable_pr00"] = chain["newest"].isin(usable)
    chain["old_has_usable_pr00"] = chain["pn"].isin(usable)

    # Only keep edges where billed CY2025 used the old number, or pn != newest
    billed_pns = set(by_pn["pn"])
    super_map = chain[(~chain["maps_to_self"]) | (chain["pn"].isin(billed_pns))].copy()
    super_map = super_map[~super_map["maps_to_self"]].copy()
    super_map = super_map.merge(
        by_pn[["pn", "cy2025_eur"]].rename(columns={"cy2025_eur": "billed_on_old_pn_eur"}),
        on="pn",
        how="left",
    )
    super_map["billed_on_old_pn_eur"] = super_map["billed_on_old_pn_eur"].fillna(0.0)
    billed_superseded = super_map[super_map["billed_on_old_pn_eur"] > 0].copy()
    billed_superseded = billed_superseded.sort_values("billed_on_old_pn_eur", ascending=False)

    map_out = billed_superseded.rename(
        columns={
            "pn": "old_pn",
            "newest": "current_pn",
            "description": "old_description",
        }
    )[
        [
            "old_pn",
            "current_pn",
            "old_description",
            "billed_on_old_pn_eur",
            "old_has_usable_pr00",
            "newest_has_usable_pr00",
        ]
    ]
    map_path = DER / "pn_supersession_map.csv"
    map_out.to_csv(map_path, index=False)

    # --- classification universe: closed + remaining Spec C4 + any other CY2025 gaps ---
    ranked = ranked.copy()
    ranked["pn"] = ranked["part_number"].map(norm_pn)
    closed = closed.copy()
    closed["pn"] = closed["part_number"].map(norm_pn)

    ADMIN_NON_CATALOGUE = {
        "REBATE": "Rebate / commercial adjustment — not a catalogue PN",
        "TRANSPORT": "Transporting cost — not a catalogue PN",
        "LATEPAYMENTINTEREST": "Late payment interest — not a catalogue PN",
    }

    rows = []
    seen: set[str] = set()
    for _, r in ranked.iterrows():
        pn = r["pn"]
        flag = str(r.get("flag") or "")
        reason = str(r.get("gap_reason") or "")
        desc = str(r.get("description") or "")
        eur = float(r.get("cy2025_eur") or 0)
        if flag == "UMI_SHELL_LUBE_PARKED":
            cls = "non_catalogue"
            detail = "Shell lubricant (5500*) — parked; not PR00 catalogue path"
        elif flag == "NO_PR00_IN_SAP" or reason == "absent_from_pr00":
            cls = "new_not_yet_listed"
            detail = "No usable PR00 in SAP; billed under ZPR1 / customer condition"
        elif reason == "on_list_no_usable_price":
            cls = "data_error"
            detail = "On IE40 list but blank/zero PR00; SAP pull returned #N/A"
        else:
            cls = "data_error"
            detail = f"residual gap ({reason or flag or 'unknown'})"
        rows.append(
            {
                "part_number": pn,
                "description": desc,
                "cy2025_eur": eur,
                "classification": cls,
                "detail": detail,
                "status": "open",
                "flag": flag,
                "gap_reason": reason,
                "successor_pn": "",
            }
        )
        seen.add(pn)

    for _, r in closed.iterrows():
        pn = r["pn"]
        if pn in seen:
            continue
        rows.append(
            {
                "part_number": pn,
                "description": str(r.get("description") or ""),
                "cy2025_eur": float(r.get("cy2025_eur") or 0),
                "classification": "closed_pr00_filled",
                "detail": "Filled from SAP PR00 pull return 2026-08-12",
                "status": "closed",
                "flag": "CLOSED_PR00_PULL",
                "gap_reason": str(r.get("gap_reason") or ""),
                "successor_pn": "",
            }
        )
        seen.add(pn)

    # Full current gap (catches admin codes Spec C4 numeric filter dropped)
    gap_now = by_pn[~by_pn["pn"].isin(usable)].copy()
    for _, r in gap_now.iterrows():
        pn = str(r["pn"])
        if pn in seen:
            continue
        eur = float(r["cy2025_eur"])
        desc = str(r.get("description") or "")
        if pn in ADMIN_NON_CATALOGUE:
            cls, detail, flag = "non_catalogue", ADMIN_NON_CATALOGUE[pn], "ADMIN_NON_PN"
        elif not pn.isdigit():
            cls, detail, flag = "non_catalogue", "Non-numeric billing code — not catalogue PN", "NON_NUMERIC"
        else:
            cls, detail, flag = "new_not_yet_listed", "CY2025 gap outside Spec C4 ranked list", "OUTSIDE_SPEC_C4"
        rows.append(
            {
                "part_number": pn,
                "description": desc,
                "cy2025_eur": eur,
                "classification": cls,
                "detail": detail,
                "status": "open",
                "flag": flag,
                "gap_reason": "absent_from_pr00",
                "successor_pn": "",
            }
        )
        seen.add(pn)

    # Annotate open PNs that are superseded-only on current list
    newest_by_pn = dict(zip(chain["pn"], chain["newest"]))
    for row in rows:
        if row["status"] != "open":
            continue
        pn = row["part_number"]
        nxt = newest_by_pn.get(pn, "")
        if nxt and nxt != pn:
            row["successor_pn"] = nxt
            if row["classification"] in ("data_error", "new_not_yet_listed"):
                row["classification"] = "superseded"
                row["detail"] = f"List points to successor {nxt}; billed under old number"

    clf = pd.DataFrame(rows).sort_values("cy2025_eur", ascending=False)
    clf_path = DER / "pn_coverage_classification.csv"
    clf.to_csv(clf_path, index=False)

    # --- coverage after close ---
    covered_eur = float(by_pn.loc[by_pn["pn"].isin(usable), "cy2025_eur"].sum())
    gap_eur = total_parts - covered_eur
    coverage_pct = covered_eur / total_parts if total_parts else 0.0

    # residual explained: open classified
    open_eur = float(clf.loc[clf["status"] == "open", "cy2025_eur"].sum())
    parked_eur = float(
        clf.loc[clf["flag"] == "UMI_SHELL_LUBE_PARKED", "cy2025_eur"].sum()
    )
    admin_eur = float(clf.loc[clf["flag"] == "ADMIN_NON_PN", "cy2025_eur"].sum())
    non_cat_eur = float(
        clf.loc[
            (clf["status"] == "open") & (clf["classification"] == "non_catalogue"),
            "cy2025_eur",
        ].sum()
    )
    active_open = clf[
        (clf["status"] == "open") & (clf["classification"] != "non_catalogue")
    ]
    active_open_eur = float(active_open["cy2025_eur"].sum())

    # Catalogue parts view (exclude admin non-PN codes from denominator)
    parts_like = by_pn[~by_pn["pn"].isin(ADMIN_NON_CATALOGUE.keys())]
    parts_total = float(parts_like["cy2025_eur"].sum())
    parts_covered = float(parts_like.loc[parts_like["pn"].isin(usable), "cy2025_eur"].sum())
    parts_coverage_pct = parts_covered / parts_total if parts_total else 0.0

    # After classify-and-exclude non_catalogue residual (Shell + admin)
    explained_residual_eur = non_cat_eur
    unexplained_eur = active_open_eur
    coverage_after_classify = (
        (total_parts - unexplained_eur) / total_parts if total_parts else 0.0
    )
    g1_met = (parts_coverage_pct >= 0.97) or (
        coverage_after_classify >= 0.97 and unexplained_eur >= 0
    )
    # stricter: every open euro must be classified (always true if we built from full gap)
    residual_fully_classified = abs(open_eur - (non_cat_eur + active_open_eur)) < 1.0
    g1_met = bool(
        (parts_coverage_pct >= 0.97)
        or (residual_fully_classified and coverage_after_classify >= 0.97)
    )

    # billed-on-superseded € (roadmap 800 PN / €1.82M claim)
    billed_super_eur = float(map_out["billed_on_old_pn_eur"].sum())
    billed_super_n = int(len(map_out))
    no_price_on_old = map_out[~map_out["old_has_usable_pr00"]]
    no_price_on_old_eur = float(no_price_on_old["billed_on_old_pn_eur"].sum())

    by_cls = (
        clf.groupby(["status", "classification"], as_index=False)
        .agg(pn_count=("part_number", "count"), eur=("cy2025_eur", "sum"))
        .sort_values("eur", ascending=False)
    )

    measured_at = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    meta = {
        "measured_at_utc": measured_at,
        "phase": "P1",
        "task": "1.1 + 1.2 starter",
        "cy2025_parts_eur": total_parts,
        "pr00_covered_eur": covered_eur,
        "pr00_coverage_pct_all_billing": round(coverage_pct, 6),
        "pr00_gap_eur": gap_eur,
        "catalogue_parts_eur": parts_total,
        "pr00_coverage_pct_catalogue_parts": round(parts_coverage_pct, 6),
        "coverage_after_classify_exclude_non_catalogue": round(
            coverage_after_classify, 6
        ),
        "g1_target_pct": 0.97,
        "g1_met": g1_met,
        "g1_basis": (
            "catalogue_parts>=97%"
            if parts_coverage_pct >= 0.97
            else "residual_classified_line_by_line"
        ),
        "spec_c4_prior": {
            "pn_count": gap_meta.get("pn_count"),
            "gap_eur": gap_meta.get("gap_eur"),
            "closed_by_pr00_pull": gap_meta.get("closed_by_pr00_pull"),
            "remaining_pn": gap_meta.get("remaining_pn"),
            "remaining_eur": gap_meta.get("remaining_eur"),
        },
        "open_classified_eur": open_eur,
        "non_catalogue_eur": non_cat_eur,
        "admin_non_pn_eur": admin_eur,
        "parked_umi_shell_eur": parked_eur,
        "active_open_eur": active_open_eur,
        "active_open_pn": int(len(active_open)),
        "classification_breakdown": by_cls.to_dict(orient="records"),
        "supersession_billed": {
            "pn_count": billed_super_n,
            "billed_on_old_pn_eur": billed_super_eur,
            "old_without_usable_pr00_eur": no_price_on_old_eur,
            "note": "Map from IE40 newest_pn; not yet EPC-validated (task 1.2 remaining).",
        },
        "outputs": {
            "pn_coverage_classification.csv": str(clf_path),
            "pn_supersession_map.csv": str(map_path),
        },
    }
    (DER / "pn_coverage_classification.meta.json").write_text(
        json.dumps(meta, indent=2), encoding="utf-8"
    )
    (DER / "pn_supersession_map.meta.json").write_text(
        json.dumps(
            {
                "measured_at_utc": measured_at,
                "source": "pricing_pr00_ie40.parquet newest_pn",
                "epc_validated": False,
                "pn_count": billed_super_n,
                "billed_on_old_pn_eur": billed_super_eur,
            },
            indent=2,
        ),
        encoding="utf-8",
    )

    print(
        json.dumps(
            {
                "coverage_all_pct": round(coverage_pct * 100, 2),
                "coverage_catalogue_parts_pct": round(parts_coverage_pct * 100, 2),
                "coverage_after_classify_pct": round(coverage_after_classify * 100, 2),
                "gap_eur": round(gap_eur, 2),
                "g1_met": meta["g1_met"],
                "g1_basis": meta["g1_basis"],
                "open_pn": int((clf["status"] == "open").sum()),
                "open_eur": round(open_eur, 2),
                "non_catalogue_eur": round(non_cat_eur, 2),
                "active_open_eur": round(active_open_eur, 2),
                "active_open_pn": int(len(active_open)),
                "supersession_billed_pn": billed_super_n,
                "supersession_billed_eur": round(billed_super_eur, 2),
                "classification_rows": len(clf),
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
