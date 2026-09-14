# Spain PLACSP — LIVE this runner (2026-09-14)

**Mode B.** No Mode A tender HTML / `tender_data.json` publish this pass.

## Diagnose vs hub

Hub §1 item 4 still said “wire ES PLACSP, IT PNCP, DE oeffentlichevergabe.” Country map and `_source_health.json` already had **IT PNCP OK 32** and **DE OV OK 545**. ES was **CODE_READY / WAF**.

## Retry (this runner)

| Probe | HTTP | WAF | Size |
|---|---:|---|---:|
| `contrataciondelsectorpublico.gob.es` …Completo3.atom | 200 | no | ~772 KB |
| `contrataciondelestado.es` …Completo3.atom | 200 | no | ~772 KB (same feed) |
| PlataformasAgregadasSinMenores.atom | 200 | no | ~797 KB but no `<entry>` in the validate window |
| Estonia RHR opendata | 500 | no | still ministry 500 — not a next wire |
| Lithuania CVP | unchanged | — | still needs VPT apiKey — **do not ask Jerome** |

Evidence: `_probe_es_next_2026-09-14.json` · `_phase1_es_fetch_stats_20260914.json` · `_source_health.json` Spain PLACSP.

## Fetch result

- **Status: OK / LIVE**
- Rolling Atom keyword matches: **2** (lookback filter cannot apply — Published empty on RSS parse)
- Isuzu gate: **0** (laundry service + local-police hybrid passenger — correctly dropped)
- Atom is a **recent-notice window**, not a 30-day API dump. Thin CV yield on this snapshot is honest, not a dashboard bug.

Fetcher already existed (`fetch_spain_placsp`). Change this pass: union Atom URLs instead of stopping at the first hit; focused runner `scrape_es_side.py`. WAF detector kept for other egress.

## What is not done

- Did not publish `tender_data.json` / GitHub Pages (needs **rebuild**).
- Did not invent a Spain API key.
- Did not re-open Nordics keys.
- Next national without a human key is still **blocked**: HU EKR login, IE eTenders RSS 404, SK recaptcha, EE RHR HTTP 500, GR login shell.
