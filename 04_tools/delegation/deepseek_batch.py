# -*- coding: utf-8 -*-
"""
DeepSeek batch runner — the workhorse side of 00_docs/agent/SCRAPER_REDO_DELEGATION.md

Text in, JSON out. DeepSeek gets no shell, no files, no workspace. Claude writes the
queue and the task spec, this script runs on Jerome's Windows machine (key in ISZE/.env),
Claude reads run_log.csv + rejects/ + a sample of out/.

Folders (created on first run):
  04_tools/delegation/deepseek/queue/<task>.jsonl    one item per line: {"item_id":..., "text":..., <allowed fields>}
  04_tools/delegation/deepseek/out/<task>.jsonl      accepted answers
  04_tools/delegation/deepseek/rejects/<task>.jsonl  answers that failed a mechanical check (with reason)
  04_tools/delegation/deepseek/run_log.csv           one row per run
Task specs:
  04_tools/delegation/tasks/<task>.json               system prompt, model, allowed fields, checks

Mechanical checks on every answer (SCRAPER_REDO_DELEGATION.md §5):
  1. valid JSON, every required key present
  2. verbatim: each value in `verbatim_fields` must appear literally in the item text
  3. placeholder: numeric fields in `price_fields` must be > placeholder_max
  4. item_id echoed back unchanged
Data boundary (§3): queue items may only carry keys listed in the spec's `allowed_fields`.
The runner refuses the whole queue if any item carries anything else.

Usage (from the ISZE root, PowerShell):
  python 04_tools/delegation/deepseek_batch.py ks_products_golden --dry-run     # sizes only, no API call
  python 04_tools/delegation/deepseek_batch.py ks_products_golden --limit 20    # first 20 items
  python 04_tools/delegation/deepseek_batch.py ks_products_golden --golden      # also score vs expected answers
"""
import argparse
import csv
import json
import re
import sys
import time
from datetime import datetime
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
BASE = HERE / "deepseek"
TASKS = HERE / "tasks"
sys.path.insert(0, str(ROOT / "04_tools"))


def _norm(s):
    return re.sub(r"\s+", " ", str(s)).strip().lower()


def load_spec(task):
    spec = json.loads((TASKS / f"{task}.json").read_text(encoding="utf-8"))
    for k in ("system_prompt", "model", "allowed_fields", "required_keys"):
        if k not in spec:
            raise SystemExit(f"task spec {task}.json missing '{k}'")
    spec.setdefault("verbatim_fields", [])
    spec.setdefault("price_fields", [])
    spec.setdefault("placeholder_max", 2.34)
    spec.setdefault("max_tokens", 1500)
    spec.setdefault("temperature", 0.0)
    return spec


def load_queue(task, spec, limit=None):
    items = []
    allowed = set(spec["allowed_fields"]) | {"item_id", "text"}
    with open(BASE / "queue" / f"{task}.jsonl", encoding="utf-8") as fh:
        for n, line in enumerate(fh, 1):
            if not line.strip():
                continue
            it = json.loads(line)
            extra = set(it) - allowed
            if extra:
                raise SystemExit(f"REFUSED — queue line {n} carries fields outside the allowlist: {sorted(extra)}")
            items.append(it)
            if limit and len(items) >= limit:
                break
    return items


def build_prompt(it, spec):
    head = " ".join(f"{k}={it[k]}" for k in spec["allowed_fields"] if k in it and k != "text")
    return f"item_id={it['item_id']} {head}\n\n{it['text']}"


def parse_json(reply):
    s = reply.strip()
    s = re.sub(r"^```(?:json)?\s*|\s*```$", "", s)
    return json.loads(s)


def check(ans, it, spec):
    if not isinstance(ans, dict):
        return "answer is not a JSON object"
    missing = [k for k in spec["required_keys"] if k not in ans]
    if missing:
        return f"missing keys {missing}"
    if str(ans.get("item_id")) != str(it["item_id"]):
        return "item_id changed"
    text = _norm(it["text"])
    for f in spec["verbatim_fields"]:
        vals = ans.get(f)
        vals = vals if isinstance(vals, list) else [vals]
        for v in vals:
            if v in (None, ""):
                continue
            if _norm(v) not in text:
                return f"verbatim fail: {f}={v!r} not in source text"
    for f in spec["price_fields"]:
        vals = ans.get(f)
        vals = vals if isinstance(vals, list) else [vals]
        for v in vals:
            if v is None:
                continue
            try:
                if float(v) <= spec["placeholder_max"]:
                    return f"placeholder-level {f}={v}"
            except (TypeError, ValueError):
                return f"non-numeric {f}={v!r}"
    return None


def score_golden(task, accepted):
    gpath = BASE / "golden" / f"{task}.expected.jsonl"
    if not gpath.exists():
        return None
    exp = {}
    for line in gpath.open(encoding="utf-8"):
        if line.strip():
            e = json.loads(line)
            exp[str(e["item_id"])] = e
    hit = tot = 0
    for a in accepted:
        e = exp.get(str(a["item_id"]))
        if e is None:
            continue
        tot += 1
        if json.dumps(e.get("expect"), sort_keys=True) == json.dumps(a.get(e.get("compare_key", "products")), sort_keys=True):
            hit += 1
    return hit, tot


def run(task, limit=None, dry_run=False, golden=False, client=None):
    spec = load_spec(task)
    items = load_queue(task, spec, limit)
    for d in ("out", "rejects"):
        (BASE / d).mkdir(parents=True, exist_ok=True)
    chars = sum(len(build_prompt(i, spec)) for i in items)
    print(f"{task}: {len(items)} items, ~{chars // 4:,} input tokens (chars/4 estimate), model {spec['model']}")
    if dry_run:
        return
    if client is None:
        from deepseek_utils import DeepSeekClient
        client = DeepSeekClient(model=spec["model"])

    started = datetime.now().isoformat(timespec="seconds")
    tok_in = tok_out = 0
    accepted, rejected = [], []
    for n, it in enumerate(items, 1):
        reason, ans, reply = None, None, ""
        try:
            reply = client.chat(build_prompt(it, spec), system_prompt=spec["system_prompt"],
                                temperature=spec["temperature"], max_tokens=spec["max_tokens"],
                                model=spec["model"])
            u = getattr(client, "last_usage", {}) or {}
            tok_in += u.get("prompt_tokens", 0)
            tok_out += u.get("completion_tokens", 0)
            ans = parse_json(reply)
            reason = check(ans, it, spec)
        except json.JSONDecodeError:
            reason = "invalid JSON"
        except Exception as e:                      # API error: record and continue
            reason = f"api error: {str(e)[:200]}"
        if reason:
            rejected.append({"item_id": it["item_id"], "reason": reason, "reply": reply[:2000]})
        else:
            accepted.append(ans)
        if n % 25 == 0:
            print(f"  {n}/{len(items)}  accepted {len(accepted)}  rejected {len(rejected)}")
        time.sleep(spec.get("sleep_s", 0.2))

    with open(BASE / "out" / f"{task}.jsonl", "w", encoding="utf-8") as fh:
        for a in accepted:
            fh.write(json.dumps(a, ensure_ascii=False) + "\n")
    with open(BASE / "rejects" / f"{task}.jsonl", "w", encoding="utf-8") as fh:
        for r in rejected:
            fh.write(json.dumps(r, ensure_ascii=False) + "\n")

    g = score_golden(task, accepted) if golden else None
    log = BASE / "run_log.csv"
    new = not log.exists()
    with open(log, "a", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh)
        if new:
            w.writerow(["task", "model", "items", "accepted", "rejected", "tokens_in", "tokens_out",
                        "golden_hit", "golden_total", "started", "ended"])
        w.writerow([task, spec["model"], len(items), len(accepted), len(rejected), tok_in, tok_out,
                    g[0] if g else "", g[1] if g else "", started, datetime.now().isoformat(timespec="seconds")])
    print(f"done: accepted {len(accepted)}, rejected {len(rejected)}, tokens {tok_in}+{tok_out}"
          + (f", golden {g[0]}/{g[1]}" if g else ""))
    return accepted, rejected


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("task")
    ap.add_argument("--limit", type=int)
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--golden", action="store_true")
    a = ap.parse_args()
    run(a.task, a.limit, a.dry_run, a.golden)
