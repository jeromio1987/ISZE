"""Entry point.

  python -m isze_pricing.cli launch  --model dmax_22
  python -m isze_pricing.cli alloc   --target 0.03
  python -m isze_pricing.cli sweep

Every invocation writes a logged run under runs/. Override any config value
inline with --set dotted.key=value, e.g.

  python -m isze_pricing.cli launch --model dmax_22 --set launch.discount_rate=0.10
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import pandas as pd

from . import audit, counterfactual, engine, launch_book, planes, theta
from .runlog import Run, load_config

ROOT = Path(__file__).resolve().parent
REPO_ROOT = ROOT.parents[1]        # <repo>/03_analytics/isze_pricing -> <repo>

# Category x distributor evidence built by the existing dashboard pipeline.
# Override with --set paths.action_map=... to point at PN-level input instead.
DEFAULT_ACTION_MAP = Path(
    r"C:\Users\jerome1\Desktop\claude\Dashboards\ISZE\pricing\_build"
    r"\pricing_action_map.json")


def _parse_sets(pairs: list[str]) -> dict:
    """Parse --set dotted.key=value. JSON first, then a bare-list fallback.

    The fallback exists because shells eat quotes. PowerShell strips the inner
    double quotes from --set theta.require_basis=["a","b"], JSON parsing then
    fails, and the old behaviour handed the consumer the raw string '[a,b]'.
    set() of a string is a set of characters, so every membership test failed
    and a whole config layer silently held flat -- no error, just a wrong run.
    Bare [a, b, c] is now parsed as a list, and consumers reject a string where
    they need a list rather than degrading quietly.
    """
    out = {}
    for p in pairs or []:
        k, _, v = p.partition("=")
        try:
            out[k] = json.loads(v)
            continue
        except json.JSONDecodeError:
            pass
        s = v.strip()
        if s.startswith("[") and s.endswith("]"):
            items = [i.strip().strip("\"'") for i in s[1:-1].split(",")]
            out[k] = [i for i in items if i]
        else:
            out[k] = v
    return out


def _carpark_path(cfg: dict) -> Path:
    """Resolve theta.carpark. Repo-relative by default so the reference stays
    the canonical 01_data copy; absolute paths pass through for a one-off.

    Note 01_data/00_derived sits outside the default sparse checkout. If the
    file is absent, theta.attach() degrades to flat and records MISSING -- it
    does not fail the run. To pull it in:
        git sparse-checkout add 01_data/00_derived
    """
    p = Path(cfg.get("theta", {}).get("carpark", ""))
    return p if p.is_absolute() else REPO_ROOT / p


def cmd_launch(args) -> None:
    cfg = load_config(ROOT / "config.yaml", _parse_sets(args.set))
    run = Run(ROOT, cfg, kind="launch",
              scenario=f"{args.model}_{args.fork}", note=args.note)
    parts_path = run.input("launch_parts", ROOT / "launch_parts.csv")
    parts = pd.read_csv(parts_path)

    det, summ = launch_book.run_scenarios(parts, cfg, args.model, args.fork)
    run.table("launch_detail", det)
    run.table("launch_scenarios", summ)

    best = summ.iloc[0]
    run.headline(f"{args.model}: best tactic '{best.scenario}' "
                 f"NPV GP EUR {best.gp_npv:,.0f}")

    m = cfg["launch"]["models"][args.model]
    md = [f"## {m['label']}\n",
          f"Spec confirmed: **{m['spec_confirmed']}** — {m['source']}\n",
          f"Services/vehicle/yr: {m['annual_km']/m['oil_interval_km']:.2f} "
          f"({m['annual_km']:,} km / {m['oil_interval_km']:,} km interval)\n",
          "\n### Scenario comparison (10y discounted GP)\n",
          summ.to_markdown(index=False),
          "\n\n### Price book — recommended scenario\n",
          det[det.scenario == best.scenario][
              ["pn", "description", "role", "part_class", "sp_class_implied",
               "sp_launch", "price_y10", "gp_pct_launch", "index_launch",
               "index_y10", "revenue_warranty_10y", "gp_npv"]
          ].to_markdown(index=False)]
    out = run.close("\n".join(md))

    print(summ.to_string(index=False))
    print(f"\nrun -> {out}")


def cmd_alloc(args) -> None:
    """Allocation run. Works on the action map today; same call takes a
    PN-level frame once L12M volume and net-to-DB price are available."""
    cfg = load_config(ROOT / "config.yaml", _parse_sets(args.set))
    src = Path(args.source) if args.source else DEFAULT_ACTION_MAP
    run = Run(ROOT, cfg, kind="alloc",
              scenario=f"t{cfg['allocation']['target']*100:g}pct", note=args.note)
    run.input("action_map", src)

    df = engine.from_action_map(src)
    df, theta_report = theta.attach(df, cfg, _carpark_path(cfg))
    run.input("uio_carpark", _carpark_path(cfg))

    out, s = engine.run(df, engine.params_from_config(cfg))
    run.table("alloc_detail", out)

    blind = out[out.evidence_tier == "T5_none"]
    run.headline(
        f"target {s['weighted_increase']*100:.4f}% | base {s['delta_base']*100:+.2f}% "
        f"| EUR {blind.weight.sum():,.0f} unbenchmarked takes "
        f"{blind.delta.mean()*100:+.2f}% "
        f"| theta moves {s.get('n_theta_moving', 0)} cells")

    by_reason = out.groupby("reason_code").agg(
        cells=("weight", "size"), base_eur=("weight", "sum"),
        mean_delta=("delta", "mean"), rev_delta=("revenue_delta_eur", "sum"))
    by_theta = out.groupby(["theta_bucket", "theta_basis"]).agg(
        cells=("weight", "size"), base_eur=("weight", "sum"),
        theta=("theta_parc", "mean"), d_theta=("d_theta", "mean"),
        mean_delta=("delta", "mean"))
    md = ["## Allocation run\n", f"```\n{json.dumps(s, indent=2)}\n```\n",
          "### By reason code\n", by_reason.round(4).to_markdown(),
          "\n\n### Momentum (theta_parc)\n",
          f"```\n{json.dumps(theta_report, indent=2)}\n```\n",
          by_theta.round(4).to_markdown()]
    run.close("\n".join(md))

    print(json.dumps(s, indent=2))
    print("\n" + by_reason.round(4).to_string())
    print("\n" + by_theta.round(4).to_string())


def cmd_audit(args) -> None:
    """Audit the current allocation, and optionally reproduce a logged run."""
    cfg = load_config(ROOT / "config.yaml", _parse_sets(args.set))
    src = DEFAULT_ACTION_MAP
    run = Run(ROOT, cfg, kind="audit", scenario=args.run or "current",
              note=args.note)
    run.input("action_map", src)

    df = engine.from_action_map(src)
    df, _ = theta.attach(df, cfg, _carpark_path(cfg))
    params = engine.params_from_config(cfg)
    out, s = engine.run(df, params)

    table, verdict = audit.run_all(out, df, cfg, params,
                                   cfg["allocation"]["target"])
    run.table("audit_checks", table)
    mat = audit.materiality(out)
    run.table("materiality", mat)

    if args.run:
        rd = ROOT / cfg["runlog"]["dir"] / args.run
        def rerun(c):
            d = engine.from_action_map(src)
            d, _ = theta.attach(d, c, _carpark_path(c))
            o, _ = engine.run(d, engine.params_from_config(c))
            return {"alloc_detail": o}
        rep = pd.DataFrame(audit.reproduce(rd, rerun))
        run.table("reproduce", rep)
        table = pd.concat([table, rep], ignore_index=True)
        if (rep.status == audit.FAIL).any():
            verdict = audit.FAIL

    run.headline(f"audit {verdict} - "
                 f"{int((table.status=='PASS').sum())} pass / "
                 f"{int((table.status=='WARN').sum())} warn / "
                 f"{int((table.status=='FAIL').sum())} fail")
    md = [f"## Audit\n\n**Verdict: {verdict}**\n",
          table.to_markdown(index=False),
          "\n\n### Lines carrying most of the impact\n",
          mat.head(15).round(4).to_markdown(index=False)]
    run.close("\n".join(md))
    print(table.to_string(index=False))
    print(f"\nVERDICT: {verdict}")


def cmd_counterfactual(args) -> None:
    """Turnover and margin under each pricing policy, plus the price bridge."""
    cfg = load_config(ROOT / "config.yaml", _parse_sets(args.set))
    run = Run(ROOT, cfg, kind="counterfactual",
              scenario=f"t{cfg['allocation']['target']*100:g}pct", note=args.note)

    src = Path(args.parts) if args.parts else ROOT / "counterfactual_parts.csv"
    if not Path(src).exists():
        print(f"No cost/price history at {src}.")
        print("Needs per part: bp_jpy_prior/new, fx_prior/new, disc_prior/new,")
        print("class_factor_prior/new, sp_actual_prior/new, units_prior, rev_prior.")
        run.headline("skipped - no cost/price history available")
        run.close("## Counterfactual\n\nBlocked: no dated cost/price history.")
        return
    run.input("counterfactual_parts", Path(src))
    d = pd.read_csv(src)

    br = counterfactual.bridge(d)
    bs = counterfactual.bridge_summary(br)
    ev = counterfactual.evaluate(
        d, cfg, ["frozen", "cost_plus_strict", "uniform_target"])
    run.table("bridge", br); run.table("policies", ev)
    run.headline(f"ISZE decision component {bs.isze_decision*100:+.2f}pp of "
                 f"{bs.total_change*100:+.2f}pp total")
    md = ["## Price bridge\n", bs.to_frame("share").round(5).to_markdown(),
          "\n\n## Policies\n", ev.round(4).to_markdown(index=False)]
    run.close("\n".join(md))
    print(bs.round(5).to_string()); print(); print(ev.round(4).to_string(index=False))


def cmd_sweep(args) -> None:
    """Sensitivity across the three dimensions that carry real judgement.

    Reported so the dimensions can be compared against each other. The point of
    this command is that replacement mileage dominates -- if a sweep only varied
    the tactic it would imply the tactic is what matters, which is false.
    """
    parts = pd.read_csv(ROOT / "launch_parts.csv")
    rows = []
    for model in ["dmax_22", "p700"]:
        for fork in ["short", "base", "long"]:
            for iam_entry in [3, 4, 6]:
                for floor_sens in [0.30, 0.45, 0.60]:
                    cfg = load_config(ROOT / "config.yaml", {
                        "launch.iam_entry_year.wear": iam_entry,
                        "launch.erosion.floor_sensitivity": floor_sens,
                    })
                    _, summ = launch_book.run_scenarios(parts, cfg, model, fork)
                    s = summ.set_index("scenario")
                    best = s.gp_npv.idxmax()
                    rows.append({
                        "model": model, "fork": fork, "iam_entry": iam_entry,
                        "floor_sens": floor_sens, "best_tactic": best,
                        "best_npv": int(s.gp_npv.max()),
                        "worst_npv": int(s.gp_npv.min()),
                        # spread between the best and second-best TACTIC
                        "tactic_spread_pct": round(
                            (s.gp_npv.max() / s.gp_npv.nlargest(2).iloc[-1] - 1) * 100, 3),
                    })
    df = pd.DataFrame(rows)

    # how much does each dimension move the answer, holding the others?
    infl = []
    for dim in ["fork", "iam_entry", "floor_sens"]:
        g = df.groupby(["model", dim]).best_npv.mean().unstack()
        infl.append({"dimension": dim,
                     "swing_pct": round(float(
                         ((g.max(axis=1) / g.min(axis=1)) - 1).mean() * 100), 1)})
    infl.append({"dimension": "tactic choice",
                 "swing_pct": round(float(df.tactic_spread_pct.mean()), 3)})
    inf = pd.DataFrame(infl).sort_values("swing_pct", ascending=False)

    cfg = load_config(ROOT / "config.yaml")
    run = Run(ROOT, cfg, kind="sweep", scenario="launch_sensitivity", note=args.note)
    run.input("launch_parts", ROOT / "launch_parts.csv")
    run.table("sweep", df)
    run.table("influence", inf)
    top = inf.iloc[0]
    run.headline(f"'{top.dimension}' swings the answer {top.swing_pct}% — "
                 f"vs {inf.iloc[-1].swing_pct}% for tactic choice "
                 f"({len(df)} combinations)")
    run.close("## Launch sensitivity\n\n### Which assumption actually moves the answer\n\n"
              + inf.to_markdown(index=False)
              + "\n\n### Full grid\n\n" + df.to_markdown(index=False))
    print(inf.to_string(index=False))
    print(f"\n{len(df)} combinations. Best tactic by model/fork:")
    print(df.groupby(["model", "fork"]).best_tactic.agg(
        lambda x: x.value_counts().index[0]).to_string())


def main() -> None:
    ap = argparse.ArgumentParser(prog="isze_pricing")
    ap.add_argument("--set", action="append", default=[],
                    help="config override, dotted.key=value")
    ap.add_argument("--note", default="")
    sub = ap.add_subparsers(dest="cmd", required=True)

    p = sub.add_parser("launch"); p.add_argument("--model", default="dmax_22")
    p.add_argument("--fork", default="base", choices=["short", "base", "long"],
                   help="replacement-mileage assumption fork")
    p.set_defaults(func=cmd_launch)
    p = sub.add_parser("alloc"); p.add_argument("--source", default=None)
    p.set_defaults(func=cmd_alloc)
    p = sub.add_parser("sweep"); p.set_defaults(func=cmd_sweep)
    p = sub.add_parser("audit")
    p.add_argument("--run", default=None, help="run id to reproduce")
    p.set_defaults(func=cmd_audit)
    p = sub.add_parser("counterfactual")
    p.add_argument("--parts", default=None, help="CSV with prior/new cost inputs")
    p.set_defaults(func=cmd_counterfactual)

    args = ap.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
