# -*- coding: utf-8 -*-
"""U26 / agent E -- the gaps table: for every number still empty after the harvest,
which sources were tried and what each returned.

Inputs are the agents' own `tried.csv` files (their first-hand record of what they
attempted), the 2026-10-07 empty-number list this build produced, and the merged
Spareto cross-reference state. Nothing is inferred:

  * a per-number outcome is used only where an agent kept one row per number, and it
    is matched on the exact queried number (never on a substring);
  * a source that recorded only host-level results is written as a one-line summary
    of that record, not as a per-number verdict;
  * a source an agent did not attempt is written `not_attempted`.

Output: `01_data/00_derived/u26_gaps_table_20261007.csv`.
"""
from __future__ import annotations

import csv
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

for _s in (sys.stdout, sys.stderr):
    if _s is not None and hasattr(_s, "reconfigure"):
        try:
            _s.reconfigure(encoding="utf-8", errors="replace")
        except Exception:
            pass

ROOT = Path(__file__).resolve().parents[2]
U26 = ROOT / "01_data" / "90_INBOX" / "scrape_targets" / "_probe" / "_u26"
OUT_DERIVED = ROOT / "01_data" / "00_derived"
EMPTY = OUT_DERIVED / "market_data_gap_empty_pns_20261007.csv"
Q_RE = re.compile(r"[?&](?:q|s|search)=([0-9A-Za-z\-_]+)")


def read_csv(path: Path) -> list[dict]:
    if not path.exists():
        return []
    with path.open(encoding="utf-8", errors="replace", newline="") as fh:
        try:
            return list(csv.DictReader(fh))
        except csv.Error:
            return []


def ks_outcomes() -> dict[str, str]:
    """A1: one row per search URL; the queried number is the exact `q=` value."""
    out: dict[str, str] = {}
    for fname in ("tried.csv", "tried_competitor.csv"):
        for r in read_csv(U26 / "A1" / fname):
            m = Q_RE.search(r.get("url_pattern") or "")
            if not m:
                continue
            q = m.group(1)
            if re.fullmatch(r"\d{10}", q):
                out.setdefault(q, (r.get("outcome") or "").strip())
    return out


def omega_outcomes() -> dict[str, str]:
    """A3: one row per (host, number)."""
    out: dict[str, str] = {}
    for r in read_csv(U26 / "A3" / "tried.csv"):
        pn = (r.get("pn") or "").strip()
        if re.fullmatch(r"\d{10}", pn):
            n = (r.get("rows") or "0").strip()
            out.setdefault(pn, f"{(r.get('outcome') or '').strip()}; rows={n}")
    return out


def pt_second_sweep() -> dict[str, str]:
    """B2: one row per (host, number) across six hosts; summarised per number."""
    per: dict[str, list[str]] = {}
    for r in read_csv(U26 / "B2" / "tried_queries.csv"):
        m = re.search(r"(\d{10})", r.get("url") or "")
        if not m:
            continue
        per.setdefault(m.group(1), []).append((r.get("outcome") or "").strip())
    out = {}
    for pn, ocs in per.items():
        counts: dict[str, int] = {}
        for o in ocs:
            counts[o] = counts.get(o, 0) + 1
        out[pn] = "; ".join(f"{k} x{v}" for k, v in sorted(counts.items()))
    return out


def kr_outcomes(fname: str, pn_col: str, outcome_col: str,
                extra: dict | None = None) -> dict[str, str]:
    """A KR-style file: one row per number, the outcome for that number."""
    out: dict[str, str] = {}
    for r in read_csv(U26 / "A2" / fname):
        pn = (r.get(pn_col) or "").strip()
        if not re.fullmatch(r"\d{10}", pn):
            continue
        o = (r.get(outcome_col) or "").strip()
        if extra:
            bits = [o]
            for col, label in extra.items():
                v = (r.get(col) or "").strip()
                if v:
                    bits.append(f"{label}={v}")
            o = "; ".join(bits)
        out.setdefault(pn, o)
    return out


def host_summary(agent: str, fname: str, hcol: str, ocol: str) -> dict:
    rows = read_csv(U26 / agent / fname)
    hosts = {((r.get(hcol) or "").strip()): (r.get(ocol) or "").strip() for r in rows
             if (r.get(hcol) or "").strip()}
    blocked = [h for h, o in hosts.items()
               if any(t in o.lower() for t in ("robots", "unreachable", "403", "disallow",
                                               "turnstile", "bot-check", "dead"))]
    allowed = [h for h in hosts if h not in blocked]
    return {"hosts_checked": len(hosts), "hosts_blocked_or_unknown": len(blocked),
            "hosts_allowed": len(allowed)}


def main() -> int:
    empty = read_csv(EMPTY)
    ks, omega, pt2 = ks_outcomes(), omega_outcomes(), pt_second_sweep()
    fr = U26 / "A2"
    files = sorted(p.name for p in fr.glob("*.csv"))
    tranzparts_outcome, tmc_outcome = {}, {}
    for fname in files:
        head = read_csv(fr / fname)
        if not head:
            continue
        cols = set(head[0].keys())
        if "host" not in cols:
            continue
        # an A2 per-number file has a row per (host, url, outcome) but no pn column,
        # so the queried number comes from the URL; only rows for that host count.
        for r in head:
            host = (r.get("host") or "").strip().lower()
            if host not in ("tranzparts.co.uk", "www.tranzparts.co.uk",
                            "www.tmcgroup.co.uk", "tmcgroup.co.uk"):
                continue
            m = Q_RE.search(r.get("url_pattern") or "")
            q = m.group(1) if m else ""
            if not re.fullmatch(r"\d{10}", q):
                continue
            o = (r.get("outcome") or "").strip()
            if "tranzparts" in host:
                tranzparts_outcome.setdefault(q, o)
            else:
                tmc_outcome.setdefault(q, o)

    spareto: dict[str, str] = {}
    spareto_hits: dict[str, str] = {}
    sp = ROOT / "04_tools" / "aftermarket_intelligence" / "state" / "spareto_crossref.csv"
    for r in read_csv(sp):
        pn = (r.get("part_no") or "").strip()
        b = (r.get("competitor_brand") or "").strip()
        if pn and b and "ISUZU" not in b.upper():
            spareto_hits.setdefault(pn, set()).add(b)
    spareto_hits = {p: "; ".join(sorted(v)) for p, v in spareto_hits.items()}
    for r in read_csv(U26 / "C1" / "spareto_crossref_per_part.csv"):
        pn = (r.get("part_no") or "").strip()
        if not pn:
            continue
        if pn in spareto_hits:
            spareto[pn] = (f"listed: {spareto_hits[pn]} "
                           f"(Spareto cards; cross-reference only, not a usable price)")
        else:
            spareto[pn] = ((r.get("page_result") or "").strip()
                           or "no match (Spareto: Nothing Matches)")

    a2_sum = host_summary("A2", "tried.csv", "host", "outcome")
    b1_sum = host_summary("B1", "tried_raw.csv", "host", "outcome")
    b2_sum = host_summary("B2", "tried.csv", "host", "outcome")

    out_rows = []
    n_new_prices = 0
    for r in empty:
        pn = r["part_number"]
        ks_o = ks.get(pn, "not_attempted")
        tr_o = tranzparts_outcome.get(pn, "not_attempted")
        tmc_o = tmc_outcome.get(pn, "not_attempted")
        om_o = omega.get(pn, "not_attempted")
        row = {
            "part_number": pn,
            "market": r["market"],
            "distributor": r["distributor"],
            "pms_category": r["pms_category"],
            "eur_all_billed_all_markets": r["eur_all_billed_all_markets"],
            "tried_KS_International_UK": ks_o,
            "tried_Omega_UK": om_o,
            "tried_Tranzparts_UK": tr_o,
            "tried_TM_Commercials_UK": tmc_o,
            "tried_PT_first_sweep": (
                f"{b1_sum['hosts_checked']} Portuguese hosts robots-checked; "
                f"{b1_sum['hosts_allowed']} allowed, {b1_sum['hosts_blocked_or_unknown']} "
                f"blocked or unreachable. No allowed host served a part price in raw HTML, "
                f"so no number was queried to a conclusion."),
            "tried_PT_second_sweep": pt2.get(pn, "not_attempted"),
            "tried_Spareto_crossref": spareto.get(pn, "no match (Spareto: Nothing Matches)"),
        }
        out_rows.append(row)

    cols = list(out_rows[0].keys()) if out_rows else ["part_number"]
    out = OUT_DERIVED / "u26_gaps_table_20261007.csv"
    with out.open("w", encoding="utf-8", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=cols, extrasaction="ignore")
        w.writeheader()
        for r in out_rows:
            w.writerow(r)

    summary = {
        "built_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "rule": ("for every number still empty, which sources were tried and what each "
                 "returned. A per-number column is filled only from an agent's own per-number "
                 "record and matched on the exact number; a source recorded only by host gets "
                 "one honest summary line; a source not attempted is written not_attempted."),
        "rows": len(out_rows),
        "empty_by_market": {m: sum(1 for r in out_rows if r["market"] == m)
                            for m in ("UK", "PT")},
        "per_number_channels": {
            "KS International (UK)": len(ks),
            "Omega (UK)": len(omega),
            "PT hosts, second sweep (B2)": len(pt2),
            "Spareto (crossref)": len(spareto),
        },
        "host_level_sources": {"Tranzparts/T&M (A2)": a2_sum,
                               "PT first sweep (B1)": b1_sum,
                               "PT host records (B2)": b2_sum},
        "columns": cols,
    }
    (OUT_DERIVED / "u26_gaps_table_20261007.meta.json").write_text(
        json.dumps(summary, indent=2), encoding="utf-8")
    print(json.dumps(summary, indent=2))
    print("WROTE", out)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
