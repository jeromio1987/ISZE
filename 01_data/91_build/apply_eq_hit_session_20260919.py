# -*- coding: utf-8 -*-
"""Apply EQ-Hit overnight PROPOSE_PATCH rows into aim_master_v2.

Jerome: update aim master please (2026-09-20).

Rules:
  - Only verdict == PROPOSE_PATCH with proposed_l1/l2/l3 filled.
  - Remap overnight fig_to_aim parallel labels (Powertrain/Chassis/…) onto
    existing aim_master spine leaves. Never invent new L1/L2/L3 strings.
  - NEEDS_HUMAN and unmapped triples are skipped (logged).
  - Does NOT touch attributes. Does NOT rebuild shared HTML.

Pattern mirrors apply_not_on_aim_spine_high_20260919.py.
"""
from __future__ import annotations

import json
import re
import shutil
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

ISZE = Path(r"C:\Users\jerom\Desktop\claude\ISZE")
D = ISZE / "01_data" / "00_derived"
INBOX = ISZE / "01_data" / "90_INBOX"
MASTER = D / "aim_master_v2.csv"
RESULTS = INBOX / "_EQ_HIT_SESSION_20260919_RESULTS.csv"
PATCH = D / "aim_gap_eq_session_20260919_patch.csv"
SKIPPED = D / "aim_gap_eq_session_20260919_skipped.csv"
NOTE = INBOX / "_EQ_HIT_SESSION_20260919_AIM_APPLY_NOTE.md"
STATE = INBOX / "_EQ_HIT_SESSION_20260919_overnight_state.json"
LOG = INBOX / "_EQ_HIT_SESSION_20260919_log.txt"

MARKER = "eq_session_20260919"
PLACEHOLDER = {"", "Unknown", "Unknown Review", "Not on AIM spine", "nan", "None"}
STAMP = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")


def norm_pn(s: object) -> str:
    return re.sub(r"\D", "", str(s or "")).zfill(10)


def clean_label(s: object) -> str:
    t = str(s or "").strip()
    if "Not classified" in t or "\n" in t:
        return ""
    return t


# EQ overnight parallel taxonomy → existing spine triple (all must exist in master).
# Fig text can refine Brakes / Pipes further in remap_row().
EQ_TRIPLE_REMAP: dict[tuple[str, str, str], tuple[str, str, str]] = {
    ("Powertrain", "Clutch", "Slave cylinder"): ("Clutch", "Release System", "Pivot"),
    ("Powertrain", "Clutch", "Clutch parts"): ("Clutch", "Clutch Kit", "Clutch Kit"),
    ("Powertrain", "Fuel system", "Injection pipe / rail"): (
        "Fuel System",
        "Injection",
        "Injection Pipe",
    ),
    ("Powertrain", "Fuel system", "Fuel system parts"): (
        "Fuel System",
        "Fuel Lines & Hoses",
        "Fuel Pipe",
    ),
    ("Chassis", "Brakes", "Brake parts"): ("Brakes", "Caliper", "Brake Caliper"),
    ("Powertrain", "Pipes / hoses", "Pipe / hose"): (
        "Cooling",
        "Cooling Hoses & Pipes",
        "Water Pipe",
    ),  # refined by fig (fuel inj / heater / radiator) below when possible
    ("Chassis", "Steering", "Steering parts"): ("Steering", "Linkage", "Tie Rod"),
    ("Chassis", "Suspension", "Suspension parts"): (
        "Suspension",
        "Bush & Mount",
        "Bushing",
    ),
    ("Chassis", "Axle", "Axle parts"): ("Driveline Axle", "Axle Shaft", "Axle Shaft"),
    ("Body", "Bumper", "Bumper"): ("Accident & Body", "Bumpers", "Bumper Assembly"),
    ("Powertrain", "Cooling", "Cooling parts"): ("Cooling", "Radiator", "Radiator Assembly"),
    ("Powertrain", "Turbo", "Turbo parts"): (
        "Intake Exhaust Emission",
        "Turbo",
        "Turbocharger",
    ),
    ("Powertrain", "Gaskets / seals", "Gasket"): ("Engine", "Gasket & Sealing", "Oil Seal"),
    ("Filters", "Engine oil filtration", "Oil filter"): (
        "Maintenance Service",
        "Oil Filter",
        "Oil Filter Element",
    ),
    ("Filters", "Engine air filtration", "Air cleaner element"): (
        "Maintenance Service",
        "Air Filter",
        "Air Cleaner Filter",
    ),
    ("Cabin Interior", "Air conditioning", "Heater core / heater"): (
        "Cooling",
        "Cooling Hoses & Pipes",
        "Water Pipe",
    ),
    ("Cabin Interior", "HVAC", "Heater"): (
        "Cooling",
        "Cooling Hoses & Pipes",
        "Water Pipe",
    ),
}


def load_known_triples(master: pd.DataFrame) -> set[tuple[str, str, str]]:
    out: set[tuple[str, str, str]] = set()
    for _, r in master.iterrows():
        l1 = clean_label(r.get("aim_l1_fixed"))
        l2 = clean_label(r.get("aim_l2_fixed"))
        l3 = clean_label(r.get("aim_l3"))
        if l1 in PLACEHOLDER or not l1 or not l2 or not l3:
            continue
        out.add((l1, l2, l3))
    return out


def refine_by_fig(
    l1: str, l2: str, l3: str, fig: str, part: str, known: set[tuple[str, str, str]]
) -> tuple[str, str, str]:
    t = f"{fig} {part}".upper()
    candidates: list[tuple[str, str, str]] = []

    if l1 == "Brakes" or (l2 == "Brakes"):
        if "CALIPER" in t:
            candidates.append(("Brakes", "Caliper", "Brake Caliper"))
        if "PAD" in t or "SHOE" in t:
            candidates.append(("Brakes", "Pads & Shoes", "Brake Pad"))
        if "DISC" in t or "DRUM" in t:
            candidates.append(("Brakes", "Discs & Drums", "Brake Disc"))
        if "PIPE" in t or "HOSE" in t:
            candidates.append(("Brakes", "Hydraulic", "Brake Pipe"))

    if "INJ" in t and ("PIPE" in t or "C/R" in t or "COMMON RAIL" in t or "FUEL" in t):
        candidates.append(("Fuel System", "Injection", "Injection Pipe"))
        candidates.append(("Fuel System", "Fuel Rail", "Fuel Rail"))

    if "FUEL" in t and ("PIPE" in t or "HOSE" in t) and "INJ" not in t:
        candidates.append(("Fuel System", "Fuel Lines & Hoses", "Fuel Pipe"))
        candidates.append(("Fuel System", "Fuel Lines & Hoses", "Fuel Hose"))

    if "HEATER" in t or "A/C" in t or "AIR CONDITION" in t:
        # Prefer any existing cabin HVAC-like leaf; fall back to cooling hose for heater piping
        if "PIPE" in t or "HOSE" in t:
            candidates.append(("Cooling", "Cooling Hoses & Pipes", "Water Pipe"))

    if "RADIATOR" in t:
        candidates.append(("Cooling", "Radiator", "Radiator Assembly"))
    if "WATER" in t and ("PIPE" in t or "HOSE" in t):
        candidates.append(("Cooling", "Cooling Hoses & Pipes", "Water Pipe"))

    if "LEAF" in t and "SPRING" in t:
        candidates.append(("Suspension", "Leaf Springs", "Leaf Spring Asm"))
    if "PROP" in t and "SHAFT" in t:
        candidates.append(("Driveline Axle", "Axle Shaft", "Prop Shaft"))
    if "DRIVE" in t and "SHAFT" in t:
        candidates.append(("Driveline Axle", "Axle Shaft", "Drive Shaft"))

    if "BUMPER" in t:
        candidates.append(("Accident & Body", "Bumpers", "Bumper Assembly"))
        candidates.append(("Accident & Body", "Panels", "Bumper"))

    if "SLAVE" in t or "CLU" in t:
        candidates.append(("Clutch", "Release System", "Pivot"))
        candidates.append(("Clutch", "Release System", "Release Bearing"))

    if "JACK" in t:
        candidates.append(("Tools Equipment", "Workshop Tools", "Gauge"))

    if "HARNESS" in t or "WIRE" in t:
        candidates.append(("Electrical", "Harness & Connectors", "Harness"))

    for c in candidates:
        if c in known:
            return c
    # Soft: accept L1/L2 match with any known L3 under that pair
    for c in candidates:
        for k in known:
            if k[0] == c[0] and k[1] == c[1]:
                return k
    return (l1, l2, l3)


def remap_row(
    proposed: tuple[str, str, str],
    fig: str,
    part: str,
    known: set[tuple[str, str, str]],
) -> tuple[str, str, str] | None:
    p1, p2, p3 = (clean_label(x) for x in proposed)
    if not p1 or not p2 or not p3:
        return None

    # Already a live spine triple
    if (p1, p2, p3) in known:
        return refine_by_fig(p1, p2, p3, fig, part, known)

    # Explicit EQ parallel remap
    base = EQ_TRIPLE_REMAP.get((p1, p2, p3))
    if base:
        l1, l2, l3 = refine_by_fig(*base, fig, part, known)
        if (l1, l2, l3) in known:
            return (l1, l2, l3)
        # accept any known L3 under remapped L1/L2
        for k in known:
            if k[0] == base[0] and k[1] == base[1]:
                return k

    # L1 already on spine: try keep L1 and find known (L1, L2, *) or (L1, *, *)
    if p1 in {k[0] for k in known}:
        for k in known:
            if k[0] == p1 and k[1] == p2 and k[2] == p3:
                return k
        for k in known:
            if k[0] == p1 and k[1] == p2:
                return k

    refined = refine_by_fig(p1, p2, p3, fig, part, known)
    if refined in known:
        return refined
    return None


def append_marker(series: pd.Series, marker: str) -> list[str]:
    out = []
    for x in series.fillna("").astype(str):
        if not x.strip():
            out.append(marker)
        elif marker in x:
            out.append(x)
        else:
            out.append(f"{x}|{marker}")
    return out


def main() -> int:
    results = pd.read_csv(RESULTS, dtype=str)
    propose = results[results["verdict"] == "PROPOSE_PATCH"].copy()
    needs = results[results["verdict"] == "NEEDS_HUMAN"].copy()
    print(f"results={len(results)} PROPOSE_PATCH={len(propose)} NEEDS_HUMAN={len(needs)}")

    master = pd.read_csv(MASTER, dtype=str, low_memory=False)
    known = load_known_triples(master)
    print(f"known_spine_triples={len(known)}")

    # Sanity: Air Filter L3
    if ("Maintenance Service", "Air Filter", "Air Filter") not in known:
        # pick real oil/air filter leaves
        for k in sorted(known):
            if k[0] == "Maintenance Service" and "Filter" in k[1]:
                print("filter leaf example", k)

    applied_rows = []
    skipped_rows = []

    for _, r in propose.iterrows():
        pn = norm_pn(r["pn"])
        fig = r.get("eq_fig_name") or ""
        part = r.get("eq_part_name") or ""
        proposed = (
            r.get("proposed_l1") or "",
            r.get("proposed_l2") or "",
            r.get("proposed_l3") or "",
        )
        mapped = remap_row(proposed, fig, part, known)
        if not mapped:
            skipped_rows.append(
                {
                    "pn": pn,
                    "reason": "no_safe_spine_leaf",
                    "proposed_l1": proposed[0],
                    "proposed_l2": proposed[1],
                    "proposed_l3": proposed[2],
                    "eq_fig_name": fig,
                    "eq_part_name": part,
                    "billed_eur": r.get("billed_eur"),
                    "description": r.get("description"),
                }
            )
            continue
        l1, l2, l3 = mapped
        applied_rows.append(
            {
                "part_number": pn,
                "description": r.get("description") or "",
                "billed_eur": r.get("billed_eur"),
                "aim_l1_fixed": l1,
                "aim_l2_fixed": l2,
                "aim_l3": l3,
                "eq_proposed_l1": proposed[0],
                "eq_proposed_l2": proposed[1],
                "eq_proposed_l3": proposed[2],
                "eq_fig_name": fig,
                "eq_part_name": part,
                "method": MARKER,
                "notes": r.get("notes") or "",
            }
        )

    # NEEDS_HUMAN always skipped
    for _, r in needs.iterrows():
        skipped_rows.append(
            {
                "pn": norm_pn(r["pn"]),
                "reason": "NEEDS_HUMAN",
                "proposed_l1": r.get("proposed_l1"),
                "proposed_l2": r.get("proposed_l2"),
                "proposed_l3": r.get("proposed_l3"),
                "eq_fig_name": r.get("eq_fig_name"),
                "eq_part_name": r.get("eq_part_name"),
                "billed_eur": r.get("billed_eur"),
                "description": r.get("description"),
            }
        )

    patch = pd.DataFrame(applied_rows)
    skip_df = pd.DataFrame(skipped_rows)
    patch.to_csv(PATCH, index=False)
    skip_df.to_csv(SKIPPED, index=False)
    print(f"apply_candidates={len(patch)} skipped={len(skip_df)}")
    if len(patch) == 0:
        raise SystemExit("no safe PROPOSE_PATCH rows to apply")

    # Verify every patch triple is known
    bad = []
    for _, r in patch.iterrows():
        t = (r["aim_l1_fixed"], r["aim_l2_fixed"], r["aim_l3"])
        if t not in known:
            bad.append(t)
    if bad:
        raise SystemExit(f"abort: {len(bad)} patch triples not in master spine e.g. {bad[:5]}")

    bak = D / f"aim_master_v2.csv.bak_pre_eq_session_20260919_{STAMP}"
    shutil.copy2(MASTER, bak)
    print("backup", bak)

    m = master.copy()
    m["pn_key"] = m["part_number"].map(norm_pn)
    patch["pn_key"] = patch["part_number"].map(norm_pn)

    before_unknown = m["aim_l1_fixed"].fillna("").isin(PLACEHOLDER).sum()

    upd = 0
    add = 0
    for _, r in patch.iterrows():
        hit = m["pn_key"] == r["pn_key"]
        n = int(hit.sum())
        l1, l2, l3 = r["aim_l1_fixed"], r["aim_l2_fixed"], r["aim_l3"]
        if n == 0:
            row = {c: "" for c in m.columns}
            row["part_number"] = r["part_number"]
            row["pn_key"] = r["pn_key"]
            row["description"] = r.get("description") or ""
            row["aim_l1_fixed"] = l1
            row["aim_l2_fixed"] = l2
            row["aim_l3"] = l3
            if "aim_l1" in m.columns:
                row["aim_l1"] = l1
            if "aim_l2" in m.columns:
                row["aim_l2"] = l2
            if "has_aim" in m.columns:
                row["has_aim"] = "1"
            row["aim_changed"] = MARKER
            row["aim_source"] = MARKER
            m = pd.concat([m, pd.DataFrame([row])], ignore_index=True)
            add += 1
            continue
        m.loc[hit, "aim_l1_fixed"] = l1
        m.loc[hit, "aim_l2_fixed"] = l2
        m.loc[hit, "aim_l3"] = l3
        if "aim_l1" in m.columns:
            m.loc[hit, "aim_l1"] = l1
        if "aim_l2" in m.columns:
            m.loc[hit, "aim_l2"] = l2
        if "has_aim" in m.columns:
            m.loc[hit, "has_aim"] = "1"
        m.loc[hit, "aim_changed"] = append_marker(m.loc[hit, "aim_changed"], MARKER)
        m.loc[hit, "aim_source"] = append_marker(m.loc[hit, "aim_source"], MARKER)
        upd += n

    m = m.drop(columns=["pn_key"])
    m.to_csv(MASTER, index=False)

    after_unknown = m["aim_l1_fixed"].fillna("").isin(PLACEHOLDER).sum()
    billed = float(pd.to_numeric(patch["billed_eur"], errors="coerce").sum())

    skipped_propose = int((skip_df["reason"] == "no_safe_spine_leaf").sum()) if len(skip_df) else 0
    skipped_human = int((skip_df["reason"] == "NEEDS_HUMAN").sum()) if len(skip_df) else 0

    summary = {
        "as_of": datetime.now(timezone.utc).isoformat(),
        "status": "AIM_APPLY_DONE",
        "aim_apply": True,
        "marker": MARKER,
        "n_results": int(len(results)),
        "n_propose_patch": int(len(propose)),
        "n_needs_human": int(len(needs)),
        "n_applied": int(len(patch)),
        "n_skipped_unmapped": skipped_propose,
        "n_skipped_needs_human": skipped_human,
        "master_rows_updated": int(upd),
        "master_rows_added": int(add),
        "unknown_l1_before": int(before_unknown),
        "unknown_l1_after": int(after_unknown),
        "billed_eur_applied": billed,
        "backup": str(bak),
        "patch": str(PATCH),
        "skipped": str(SKIPPED),
        "master": str(MASTER),
    }

    STATE.write_text(json.dumps(summary, indent=2), encoding="utf-8")
    NOTE.write_text(
        "\n".join(
            [
                "# EQ-Hit session 20260919 — AIM apply",
                "",
                f"Applied **{summary['n_applied']}** PROPOSE_PATCH rows into `aim_master_v2.csv` "
                f"with source stamp `{MARKER}`.",
                "",
                f"- Skipped NEEDS_HUMAN: **{skipped_human}**",
                f"- Skipped unmapped (no safe spine leaf): **{skipped_propose}**",
                f"- Master rows updated: **{upd}** · added: **{add}**",
                f"- Backup: `{bak}`",
                f"- Patch: `{PATCH}`",
                f"- Skipped log: `{SKIPPED}`",
                "",
                "Overnight fig_to_aim labels (Powertrain/Chassis/…) were remapped onto existing "
                "AIM spine leaves only. Attribute layer not touched. No shared pack rebuild.",
                "",
                "AIM apply was authorized by Jerome: update aim master please.",
                "",
            ]
        ),
        encoding="utf-8",
    )
    with LOG.open("a", encoding="utf-8") as f:
        f.write(
            f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] AIM_APPLY "
            f"applied={summary['n_applied']} skipped_human={skipped_human} "
            f"skipped_unmap={skipped_propose} bak={bak.name}\n"
        )

    print(json.dumps(summary, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
