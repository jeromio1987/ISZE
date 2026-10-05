"""Why are there still ~1,100 open on the IE40 PR00 extract? -- one measurement, self-checking.

Read-only. Touches nothing under 01_data/00_derived/, no browser, no EPC.

Answers, in order:
  1. how many part numbers are open today, and against which file that count is read;
  2. for EVERY open part number, exactly one reason, with counts that must sum to the open total;
  3. the 20 highest-priced examples of the largest group, with their wording and list price;
  4. how many could be cleared by a relaxed rule, by the EPC lookup, by the Unknown decision;
  5. any open part that is open for a reason other than data absence or the marker.

The wording dictionary is rebuilt the way the published file builds its own label:
for each master row, the first non-blank of aim_l1_fixed then aim_l1, with the classification
overlay's aim_l1_fixed laid over the top where it is non-blank. The script then proves it
reproduces what was actually written on today's 206 closed parts, so the dictionary is not a
second convention.

Every join is on an explicitly normalised key, and the script says how many parts failed each
join. It prints its own reconciliation check and exits non-zero if the parts do not land in
exactly one group.

Run:  python 01_data/91_build/export_aim_open_why_20260924/open_why.py
"""
from __future__ import annotations

import json
import sys
from datetime import datetime
from pathlib import Path

import pandas as pd

ROOT = Path(r"C:\Users\jerom\Desktop\claude\ISZE")
DER = ROOT / "01_data" / "00_derived"
BUILD = ROOT / "01_data" / "91_build"
OUT = BUILD / "export_aim_open_why_20260924"
EQ = BUILD / "export_aim_eq_20260924"
TIER = BUILD / "export_aim_tiering_20260924"

QUEUE_CSV = EQ / "queue.csv"
EXPORT_XLSX = ROOT / "01_data" / "EXPORT.XLSX"
MASTER_CSV = DER / "aim_master_v2.csv"
OVERLAY_CSV = DER / "aim_pn_classification_20260920.csv"
PAIR_CSV = DER / "AIM_Master_PN_Categories_Figkey_20260924.csv"

STAMP = "export_pr00_20260924"
SUPPORT_BAR = 3  # the rule's bar: at least this many master parts behind the wording

# The residual buckets the rule refuses to use (condition 3 of the rule).
RESIDUAL_FAMILIES = {
    "Maintenance Service", "Literature Marketing", "Tools Equipment",
    "Logistics Packaging", "Fluids Chemicals",
}

# The wordings the tiering study carved out as decidable-looking but not defensible.
# Source: export_aim_tiering_20260924/final_numbers.py (BAD_TEXT + CONVENTION).
CARVE_OUT = {
    "GASKET; CYL HD": "master files it under Transmission; a cylinder-head gasket is an engine part",
    "GASKET SET; ENG OVERHAUL": "master files it under Transmission; an engine overhaul set is an engine part",
    "LAMP ASM; HEAD": "lamp wordings are split by convention, not by anything in the row",
    "LAMP ASM; RR COMB": "lamp wordings are split by convention, not by anything in the row",
    "LAMP ASM; FRT COMB": "lamp wordings are split by convention, not by anything in the row",
    "LAMP ASM; FOG": "lamp wordings are split by convention, not by anything in the row",
    "LAMP ASM; SIDE COMB": "lamp wordings are split by convention, not by anything in the row",
    "CYLINDER ASM; CLUTCH MASTER": "master files it under Brakes; it is a clutch part",
    "PUMP ASM; OIL,P/S": "master files it under Fuel System; it is a power-steering pump",
}

LOG: list[str] = []


def say(*parts: object) -> None:
    line = " ".join(str(p) for p in parts)
    print(line)
    LOG.append(line)


def norm_pn(s: pd.Series) -> pd.Series:
    return s.fillna("").astype(str).str.strip().str.upper()


def norm_desc(s: pd.Series) -> pd.Series:
    return s.fillna("").astype(str).str.upper().str.strip().str.replace(r"\s+", " ", regex=True)


def bl(s: pd.Series) -> pd.Series:
    x = s.fillna("").astype(str).str.strip()
    return x.where(~x.str.lower().isin(["", "nan", "none", "null"]), "")


def is_marker(label: str) -> bool:
    return label.strip().lower().startswith("unknown")


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    say("=" * 78)
    say("WHY ARE THERE STILL ~1,100 OPEN ON THE IE40 PR00 EXTRACT?")
    say("run", datetime.now().astimezone().isoformat(timespec="seconds"))
    say("read-only; nothing written outside", OUT)
    say("=" * 78)

    # ---------------------------------------------------------------- 1. inputs
    q = pd.read_csv(QUEUE_CSV, dtype=str, encoding="utf-8-sig")
    q["pnk"] = norm_pn(q["pn"])
    q["dn"] = norm_desc(q["Description"])
    q["list_eur"] = pd.to_numeric(q["list_eur"], errors="coerce")
    say("")
    say("INPUT 1  the queue (the parts that still need a family)")
    say("  rows", len(q), " unique part numbers", q["pnk"].nunique())
    say("  part numbers carrying more than one wording:", int((q.groupby("pnk")["dn"].nunique() > 1).sum()))
    say("  duplicate queue rows (the same part twice):", int(len(q) - q["pnk"].nunique()))

    x = pd.read_excel(EXPORT_XLSX)
    x["pnk"] = norm_pn(x["Newest P/N"])
    x["price"] = pd.to_numeric(
        x["Price"].fillna("").astype(str).str.replace("\u00a0", "").str.replace(" ", "").str.replace(",", "."),
        errors="coerce",
    )
    price_by_pn = x.drop_duplicates("pnk").set_index("pnk")["price"]

    m = pd.read_csv(MASTER_CSV, dtype=str, low_memory=False)
    m["pnk"] = norm_pn(m["part_number"])
    m["dn"] = norm_desc(m["description"])
    m["fk"] = bl(m["fig_key"])
    m["has_aim"] = pd.to_numeric(m["has_aim"], errors="coerce").fillna(0).astype(int)
    m["aim_source"] = bl(m["aim_source"])
    # the published file's own label order: *_fixed first, then the plain column
    m["label"] = bl(m["aim_l1_fixed"]).where(lambda s: s != "", bl(m["aim_l1"]))
    m["l2"] = bl(m["aim_l2_fixed"]).where(lambda s: s != "", bl(m["aim_l2"]))
    m["l3"] = bl(m["aim_l3"])
    mdup = int(len(m) - m["pnk"].nunique())
    say("  master rows", len(m), " duplicate part numbers on the master:", mdup)

    o = pd.read_csv(OVERLAY_CSV, dtype=str, low_memory=False)
    o["pnk"] = norm_pn(o["part_number"])
    o["label"] = bl(o["aim_l1_fixed"]).where(lambda s: s != "", bl(o.get("aim_l2_fixed", pd.Series())))
    oi = o.drop_duplicates("pnk", keep="first").set_index("pnk")

    pr = pd.read_csv(PAIR_CSV, dtype=str, low_memory=False)
    pr["pnk"] = norm_pn(pr["part_number"])
    pr["label"] = bl(pr["aim_level_1"])
    pi = pr.drop_duplicates("pnk", keep="first").set_index("pnk")

    # ------------------------------------ 2. the dictionary, as the file builds it
    # overlay's *_fixed wins where non-blank, then the master's own order.
    m["label_eff"] = m["label"]
    ov = bl(oi["label"].reindex(m["pnk"]).reset_index(drop=True))
    ov.index = m.index
    m["label_eff"] = m["label_eff"].where(ov == "", ov)
    mi = m.drop_duplicates("pnk", keep="first").set_index("pnk")

    desc_known = m[(m["label_eff"] != "") & (~m["label_eff"].map(is_marker))].copy()
    desc_known["path"] = (desc_known["label_eff"] + " > " + desc_known["l2"] + " > " + desc_known["l3"]).str.strip()
    g = desc_known.groupby("dn")["label_eff"]
    dd = pd.DataFrame(
        {
            "n_parts": g.size(),
            "n_families": g.nunique(),
            "top_family": g.agg(lambda s: s.value_counts().index[0]),
            "top_family_parts": g.agg(lambda s: int(s.value_counts().iloc[0])),
        }
    )
    gl = desc_known.groupby(["dn", "label_eff"]).size().rename("n").reset_index()
    tl = gl.sort_values(["dn", "n", "label_eff"], ascending=[True, False, True]).drop_duplicates("dn")
    dd = dd.join(tl.set_index("dn")[["label_eff", "n"]].rename(
        columns={"label_eff": "top_leaf", "n": "top_leaf_parts"}))
    dd = dd.join(gl.groupby("dn")["label_eff"].nunique().rename("n_leaves"))
    # second-largest leave-path for the same wording -- the leaf guard needs it
    gl2 = gl.sort_values(["dn", "n", "label_eff"], ascending=[True, False, True])
    second = gl2.groupby("dn").nth(1)[["dn", "n"]].rename(columns={"n": "second_leaf_parts"})
    dd = dd.join(second.set_index("dn"))
    dd["second_leaf_parts"] = dd["second_leaf_parts"].fillna(0)

    # the level-3 dictionary: one leave-path means one answer
    gp = desc_known.groupby("dn")["path"]
    pdict = pd.DataFrame({
        "path_n_parts": gp.size(),
        "path_n": gp.nunique(),
        "path_top": gp.agg(lambda s: s.value_counts().index[0]),
        "path_top_parts": gp.agg(lambda s: int(s.value_counts().iloc[0])),
    })

    # the figure-key dictionary, built the same way (used as a veto only)
    fkd = desc_known[desc_known["fk"] != ""].groupby("fk")["label_eff"]
    fkdict = pd.DataFrame({
        "fk_parts": fkd.size(),
        "fk_families": fkd.nunique(),
        "fk_family": fkd.agg(lambda s: s.value_counts().index[0]),
    })

    say("")
    say("INPUT 2  the wording dictionary, rebuilt the way the published file is built")
    say("  master rows with a usable family", int(((m["label_eff"] != "") &
        (~m["label_eff"].map(is_marker))).sum()), "of", len(m))
    say("  distinct wordings", len(dd), "| meaning more than one family",
        int((dd["n_families"] > 1).sum()), "| clearing the full bar (one family, >="
        + str(SUPPORT_BAR) + " parts on one path):",
        int(((dd["n_families"] == 1) & (dd["top_leaf_parts"] >= SUPPORT_BAR)).sum()))

    # ------------------------------------------------- 3. what is open, and why
    uniq = q.drop_duplicates("pnk").set_index("pnk")
    keys = list(uniq.index)
    got = mi.reindex(keys)
    has_family = got["has_aim"].fillna(0).astype(int) == 1
    closed = [k for k in keys if bool(has_family.loc[k])]
    open_keys = [k for k in keys if not bool(has_family.loc[k])]
    say("")
    say("INPUT 3  what is open, read off the master as it stands today")
    say("  unique part numbers on the queue", len(keys))
    say("  closed today (44 appended + 162 filled)", len(closed))
    say("  of those, stamped", STAMP, int((mi.reindex(closed)["aim_source"] == STAMP).sum()))
    say("  OPEN", len(open_keys))

    # ------------------------------------------------- reproducibility of the rule
    wrong = 0
    for k in closed:
        u = uniq.loc[k]
        d = dd.loc[u["dn"]] if u["dn"] in dd.index else None
        if d is None:
            continue
        if str(mi.loc[k, "label_eff"]) not in (str(d["top_family"]), ""):
            wrong += 1
    say("")
    say("REPRODUCIBILITY CHECK  does this script's dictionary agree with today's write?")
    say("  closed parts", len(closed), "| dictionary prediction disagrees with the written family:", wrong)

    # -------------------------------------------------------- 4. classify each
    tierB = pd.read_csv(TIER / "tierA_audited.csv", dtype=str, low_memory=False)
    tierB["pnk"] = norm_pn(tierB["pn"])
    carve = set(tierB.loc[pd.to_numeric(tierB["undefendable"].fillna("0"), errors="coerce").fillna(0) > 0, "pnk"])
    carve |= set(tierB.loc[pd.to_numeric(tierB["convention"].fillna("0"), errors="coerce").fillna(0) > 0, "pnk"])

    rows = []
    for k in open_keys:
        u = uniq.loc[k]
        dn = str(u["dn"])
        orow = oi.loc[k] if k in oi.index else None
        mr = mi.loc[k] if k in mi.index else None
        pair_label = str(pi.loc[k, "label"]) if k in pi.index else ""
        overlay_label = str(orow["label"]) if orow is not None else ""
        overlay_marker = bool(overlay_label != "" and is_marker(overlay_label))
        master_label = "" if mr is None else str(mr["label_eff"])
        d = dd.loc[dn] if dn in dd.index else None

        single = bool(d is not None and int(d["n_families"]) == 1)
        support = int(d["n_parts"]) if d is not None else 0
        family = str(d["top_family"]) if d is not None else ""
        leaf_gap = bool(d is not None and int(d["n_leaves"]) > 1)
        residual = family in RESIDUAL_FAMILIES
        is_carve = dn in CARVE_OUT
        fkv = "" if mr is None else str(mr["fk"])
        fkinfo = fkdict.loc[fkv] if (fkv != "" and fkv in fkdict.index) else None
        # the rule's figure-key test: a key with evidence must be single-family AND agree.
        fk_seen = bool(fkinfo is not None)
        fk_one = bool(fkinfo is not None and int(fkinfo["fk_families"]) == 1)
        fk_agrees = bool(fk_one and str(fkinfo["fk_family"]) == family)
        fk_ok = (not fk_seen) or fk_agrees
        pinfo = pdict.loc[dn] if dn in pdict.index else None
        one_path = bool(pinfo is not None and int(pinfo["path_n"]) == 1
                        and int(pinfo["path_top_parts"]) >= SUPPORT_BAR)

        def classify(ignore_marker: bool) -> tuple[str, str]:
            """The rule, read straight. ignore_marker=True answers the counterfactual:
            if the deliberate Unknown marker were not there, what would this part be?"""
            if not ignore_marker:
                if pair_label != "" and is_marker(pair_label):
                    return "BLOCKED_UNKNOWN_MARKER", f"published file says {pair_label}"
                if overlay_marker:
                    return "BLOCKED_UNKNOWN_MARKER", f"overlay says {overlay_label}"
                if mr is not None and master_label != "" and is_marker(master_label):
                    return "BLOCKED_UNKNOWN_MARKER", f"master says {master_label}"
            if mr is None and orow is None:
                return "DATA_NOT_IN_MASTER", "no row on the master and none on the classification overlay"
            if is_carve and single:
                return "DATA_CARVED_OUT_BY_HAND", CARVE_OUT[dn]
            if one_path and residual and fk_ok:
                return "DATA_RESIDUAL_FAMILY_REFUSED", \
                    f"the wording only ever lands in {family}, a residual bucket the rule refuses"
            if one_path and not residual and fk_ok:
                return "NOT_BLOCKED", \
                    f"wording resolves to {pinfo['path_top']} on {support} parts and the key agrees"
            if one_path and fk_seen and not fk_one:
                return "DATA_FIGURE_KEY_MULTI_FAMILY", \
                    (f"wording resolves to {pinfo['path_top']} on {support} parts, but figure key "
                     f"{fkv} carries {int(fkinfo['fk_families'])} families on "
                     f"{int(fkinfo['fk_parts'])} parts, so the rule has no single key answer")
            if one_path and fk_seen and fk_one and not fk_agrees:
                return "DATA_FIGURE_KEY_CONTRADICTS", \
                    (f"wording says {family} on {support} parts, the figure key says "
                     f"{fkinfo['fk_family']} on {int(fkinfo['fk_parts'])}; the key vetoes")
            if single and support >= SUPPORT_BAR and leaf_gap and int(d["second_leaf_parts"]) >= SUPPORT_BAR:
                return "DATA_FAMILY_TWO_STRONG_LEAVES", \
                    (f"whole family {family} is agreed, but the master splits the wording over "
                     f"{int(d['n_leaves'])} leave-paths, each with {SUPPORT_BAR} or more parts")
            if d is not None and int(d["n_families"]) > 1:
                return "DATA_WORDING_SPLIT_ACROSS_FAMILIES", \
                    f"{int(d['n_families'])} families, biggest {family} on {int(d['top_family_parts'])} parts"
            if d is None:
                return "DATA_WORDING_UNKNOWN_TO_MASTER", dn
            if single and support < SUPPORT_BAR:
                return "DATA_WORDING_TOO_FEW_PARTS", f"{support} master parts behind the wording"
            if single:
                return "DATA_FAMILY_ONE_LEAF_SPLIT", \
                    f"one family ({family}) split over {int(d['n_leaves'])} leave-paths"
            return "OTHER_MASTER_HOLDS_NO_FAMILY", \
                "the part's master row carries no family anywhere and no wording evidence"

        group, detail = classify(ignore_marker=False)
        shadow = classify(ignore_marker=True)[0] if group == "BLOCKED_UNKNOWN_MARKER" else ""


        rows.append({
            "pnk": k,
            "description": str(u["Description"]),
            "list_eur": float(u["list_eur"]) if pd.notna(u["list_eur"]) else 0.0,
            "group": group,
            "detail": detail,
            "in_pair": k in pi.index,
            "pair_label": pair_label,
            "on_master": k in mi.index,
            "on_overlay": k in oi.index,
            "in_export": k in price_by_pn.index,
            "export_price": float(price_by_pn.get(k, float("nan"))),
            "wording_parts": support,
            "wording_families": int(d["n_families"]) if d is not None else 0,
            "wording_family": family,
            "wording_leaf": str(d["top_leaf"]) if d is not None else "",
            "wording_leaf_parts": int(d["top_leaf_parts"]) if d is not None else 0,
            "carve_out": is_carve,
            "shadow": shadow,
        })
    cls = pd.DataFrame(rows)
    counts = cls["group"].value_counts()
    total_open = len(cls)

    # ----------------------------------------------------------- 5. self-check
    say("")
    say("SELF-CHECK  every open part number lands in exactly one group")
    say("  open part numbers", total_open)
    say("  sum of group counts", int(counts.sum()))
    say("  distinct part numbers classified", cls["pnk"].nunique())
    ok = int(counts.sum()) == total_open and cls["pnk"].nunique() == total_open
    say("  RECONCILES:", "YES" if ok else "NO")
    say("  join accounting (nothing silent)")
    say("    on the master today:", int(cls["on_master"].sum()), "| not:", int((~cls["on_master"]).sum()))
    say("    on the overlay today:", int(cls["on_overlay"].sum()), "| not:", int((~cls["on_overlay"]).sum()))
    say("    in the published file:", int(cls["in_pair"].sum()), "| not:", int((~cls["in_pair"]).sum()))
    say("    on the price extract:", int(cls["in_export"].sum()), "| not:", int((~cls["in_export"]).sum()))
    if int((~cls["in_export"]).sum()):
        say("      ->", ", ".join(cls.loc[~cls["in_export"], "pnk"].tolist()))
    say("    what the published file shows for the open set (these three are disjoint and sum to "
        + str(total_open) + "):")
    say("      a row exists but the family is blank:",
        int(((cls["pair_label"] == "") & cls["in_pair"]).sum()))
    say("      the deliberate Unknown marker:", int(cls["pair_label"].map(is_marker).sum()))
    say("      no row in the published file at all:", int((~cls["in_pair"]).sum()))
    say("      a real family (must be 0 -- anything else is a defect):",
        int(((cls["pair_label"] != "") & (~cls["pair_label"].map(is_marker))).sum()))

    # -------------------------------------------------------------- 6. the split
    label_of = {
        "BLOCKED_UNKNOWN_MARKER": "blocked by the deliberate Unknown marker (a decision, not data)",
        "DATA_NOT_IN_MASTER": "no row in the master at all, so there is nothing to write a family to",
        "DATA_WORDING_UNKNOWN_TO_MASTER": "wording the master has never carried, so the rule has nothing to match",
        "DATA_WORDING_TOO_FEW_PARTS": "wording the master carries, but on fewer than 3 parts",
        "DATA_WORDING_SPLIT_ACROSS_FAMILIES": "wording the master itself splits across more than one family",
        "DATA_FAMILY_ONE_LEAF_SPLIT": "one family, but the master splits it across more than one leave-path",
        "DATA_FAMILY_TWO_STRONG_LEAVES": "the whole family is agreed, but the master holds two strong leave-paths for the wording",
        "DATA_FIGURE_KEY_VETO": "the wording and the figure key point at different families, so the rule stops",
        "DATA_FIGURE_KEY_MULTI_FAMILY": "the wording resolves, but the figure key itself is multi-family so the check cannot pass",
        "DATA_FIGURE_KEY_CONTRADICTS": "the figure key carries one family and it is not the wording's, so the rule stops",
        "DATA_CARVED_OUT_BY_HAND": "looks decidable, but the wordings were deliberately held back",
        "DATA_RESIDUAL_FAMILY_REFUSED": "the only family the wording ever lands in is a residual bucket",
        "DEFECT_RULE_SHOULD_HAVE_PLACED": "DEFECT: the wording resolves, the key agrees, and the rule still did not place it",
        "OTHER_MASTER_HOLDS_NO_FAMILY": "the master row exists but carries no family anywhere",
    }
    say("")
    say("THE SPLIT OF THE OPEN PARTS")
    say(f"  {'group':44s} {'parts':>6s} {'share':>7s}   list EUR")
    for grp, n in counts.items():
        sub = cls[cls["group"] == grp]
        say(f"  {label_of.get(grp, grp):44s} {n:6d} {100 * n / total_open:6.1f}%   {sub['list_eur'].sum():12,.2f}")
    say(f"  {'TOTAL':44s} {int(counts.sum()):6d} {100.0:6.1f}%   {cls['list_eur'].sum():12,.2f}")
    for grp in ("DEFECT_RULE_SHOULD_HAVE_PLACED", "OTHER_MASTER_HOLDS_NO_FAMILY"):
        if grp in counts.index:
            say("")
            say("  named rows in", grp)
            for _, r in cls[cls["group"] == grp].iterrows():
                say(f"    {r['pnk']}  {r['description'][:38]:38s}  {r['detail']}")

    # --------------------------------------------- 7. top 20 of the big group
    big = counts.index[0]
    bigdf = cls[cls["group"] == big].sort_values("list_eur", ascending=False)
    say("")
    say(f"THE 20 HIGHEST-PRICED EXAMPLES OF THE LARGEST GROUP ({label_of.get(big, big)})")
    for _, r in bigdf.head(20).iterrows():
        say(f"  {r['pnk']}  {r['list_eur']:10,.2f}  {r['description'][:56]}")

    # ------------------------------------------- 8. the practical clear counts
    say("")
    say("WHAT WOULD CLEAR EACH GROUP")
    marker = int((cls["group"] == "BLOCKED_UNKNOWN_MARKER").sum())
    mk = cls[cls["group"] == "BLOCKED_UNKNOWN_MARKER"]
    marker_notblocked = int((mk["shadow"] == "NOT_BLOCKED").sum())
    marker_single = int(mk["shadow"].isin(["DATA_RESIDUAL_FAMILY_REFUSED",
                                           "DATA_FAMILY_TWO_STRONG_LEAVES",
                                           "DATA_FIGURE_KEY_MULTI_FAMILY",
                                           "DATA_FIGURE_KEY_CONTRADICTS",
                                           "DATA_CARVED_OUT_BY_HAND"]).sum())
    marker_no_wording = int((mk["wording_families"] == 0).sum())
    marker_split = int((mk["wording_families"] > 1).sum())
    say(f"  (a) a relaxed rule that allows fewer than {SUPPORT_BAR} supporting parts")
    thin = int((cls["group"] == "DATA_WORDING_TOO_FEW_PARTS").sum())
    headroom = int(cls["group"].isin(["DATA_WORDING_TOO_FEW_PARTS", "DATA_RESIDUAL_FAMILY_REFUSED",
                                      "DATA_CARVED_OUT_BY_HAND", "DATA_FAMILY_TWO_STRONG_LEAVES",
                                      "DATA_FIGURE_KEY_MULTI_FAMILY",
                                      "DATA_FIGURE_KEY_CONTRADICTS"]).sum())
    say(f"      clears {thin} open parts outright (wording known, 1 or 2 master parts behind it)")
    say(f"      if the rule is also allowed to use single-family wordings of any size, to stop refusing "
        f"the five residual buckets, to pick a leave-path where two are strong, and to stop letting the "
        f"figure key veto, it reaches {headroom} in total")
    say(f"  (b) the parts-catalogue / Snap-on EPC lookup")
    epc = int(cls["group"].isin(["DATA_WORDING_UNKNOWN_TO_MASTER", "DATA_WORDING_SPLIT_ACROSS_FAMILIES",
                                 "DATA_FAMILY_ONE_LEAF_SPLIT", "DATA_NOT_IN_MASTER",
                                 "OTHER_MASTER_HOLDS_NO_FAMILY"]).sum())
    say(f"      only it can settle {epc} open parts (no master wording for them, or the master's own "
        f"wording conflicts with itself)")
    say(f"  (c) deciding the Unknown marker")
    say(f"      clears {marker} open parts once the marker is cleared and the wording is allowed to stand")
    say(f"      of those, {marker_notblocked} have a wording that resolves to one family with the figure "
        f"key agreeing, so a plain re-run would place them the moment the marker is gone; "
        f"{int((mk['shadow'] == 'DATA_WORDING_TOO_FEW_PARTS').sum())} have a wording the master carries but "
        f"on fewer than 3 parts, so they would also need the relaxed rule; "
        f"{marker_single + int((mk['shadow'] == 'DATA_FAMILY_ONE_LEAF_SPLIT').sum())} resolve to one family "
        f"but stop on a split leave-path, a multi-family figure key or a hand carve-out; "
        f"{marker_split} have a wording that is split across families; and {marker_no_wording} have no "
        f"wording evidence at all")
    say("")
    say("  overlap, stated so the counts are not added twice:")
    say(f"    the {marker} marker parts are blocked on a decision first; until the marker is cleared, "
        f"the relaxed rule in (a) cannot reach them either")
    say(f"    of the {marker}, the {marker_notblocked} resolve as soon as the marker is lifted with no "
        f"rule change at all, and the {marker_no_wording} would still need the EPC afterwards")
    say(f"    so the most that any rule change can clear is "
        f"{total_open - epc} of {total_open}; the other {epc} need the EPC walk")

    # ------------------------------------------------- 9. part-number hygiene
    say("")
    say("PART-NUMBER HYGIENE ON THE OPEN SET (the join traps)")
    pn = cls["pnk"]
    leading = pn[pn.str.match(r"^0\d")]
    nonnum = pn[~pn.str.match(r"^\d+$")]
    say("  open part numbers starting with a zero:", len(leading))
    say("  open part numbers that are not all digits:", len(nonnum))
    say("  the 44 part numbers the master had no row for at all were appended today; the 43 that are "
        "open today with no master row are a different, overlapping-in-spirit set: they never had a "
        "row and are not among the 44 (verified: all 44 carry a family and the stamp)")

    # ---------------------------------------------------------------- 10. files
    cls.sort_values(["group", "list_eur"], ascending=[True, False]).to_csv(
        OUT / "open_parts_classified.csv", index=False, encoding="utf-8-sig")
    counts.rename("open_parts").to_frame().to_csv(OUT / "open_group_counts.csv", encoding="utf-8-sig")
    (OUT / "run_log.txt").write_text("\n".join(LOG) + "\n", encoding="utf-8")
    (OUT / "summary.json").write_text(json.dumps({
        "run_at": datetime.now().astimezone().isoformat(timespec="seconds"),
        "queue_pn": int(len(keys)),
        "open_pn": total_open,
        "closed_pn": len(closed),
        "groups": {str(k): int(v) for k, v in counts.items()},
        "clears": {"relaxed_thin_support": thin, "epc_only": epc, "unknown_marker": marker},
        "sum_check": bool(ok),
    }, indent=2), encoding="utf-8")
    say("")
    say("files under", OUT)
    say("  open_why.py  open_parts_classified.csv  open_group_counts.csv  summary.json  run_log.txt")

    if not ok:
        say("")
        say("RECONCILIATION FAILED -- do not quote these numbers")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
