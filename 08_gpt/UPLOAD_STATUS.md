# GPT Enterprise — upload status

**Pack root:** `08_gpt/`
**Sensitivity rule:** Never upload `01_data/raw/sales/*` or line-level billing (AGENTS.md)

## Last upload

| Field | Value |
|-------|-------|
| Upload date | 2026-05-12 (v1.0 context pack) |
| Uploaded by | Jerome |
| FACTS.md reconciled | No — Active_Projects flagged stale May 2026 |
| Pack changelog | 08_gpt/CHANGELOG.md v1.0 |

**Next upload due:** First working Monday of month

## Pre-upload checklist

- Green 01_data/derived/_verification_report.json (0 fail)
- FACTS.md reconciled
- No 01_data/raw/sales/* in selection
- 08_gpt/CHANGELOG.md entry written
- Update this file after upload

## Drift watch

FACTS.md vs Pricing_Logic.md and Active_Projects — not compared since 2026-06-10.
01_data/gpt_safe/ may carry pre-fix figures — re-export after green verify.

Full protocol: 00_docs/agent/AI_STACK.md