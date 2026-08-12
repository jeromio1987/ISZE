# AI sales intelligence — roadmap

**Last updated:** 2026-08-12
**Hub:** [`ISZE_ROADMAP.md`](../ISZE_ROADMAP.md) · **Registry:** [`MAP_REGISTRY.yaml`](../MAP_REGISTRY.yaml)
**Scope:** joining the existing structured sales spine (billing, UIO, pricing, sell-out) to the unstructured corpus (email) to improve wallet share, cycle time, forecast accuracy and admin efficiency.
**Status:** **ACTIVE — Track A (P1) progressing; Track B waits on G0a (local) / G0b (egress+shared).**

> **Numbers:** `../../FACTS.md` wins over any deck, memory or GPT file. Pipeline: green `01_data/00_derived/_verification_report.json` → `metrics_snapshot.json`.
> **Estimates:** every effort figure below is engineering estimate, not measurement. Every business figure is cited with source + date or left as a named input slot. Do not quote an unfilled slot.

---

## 0. Dual track (2026-08-12) — what can run now

Graph/OAuth is closed (tenant admin consent). Local MAPI is open (§1.3). Governance still gates mail code.

| Track | Phases | Gate | Status now |
|---|---|---|---|
| **A — Structured spine** | P1 → then P5 | G1 before P5 go-live | **In progress.** P1.1 done; P1.2 starter map written; catalogue PR00 coverage **98.2%** (coverage bar met; 1.4 + 1.5 + EPC validation still open) |
| **B — Email / interaction** | P0 → P2a → (P2b/P3/P6) | **G0a** then **G0b** | **G0a COMPLETE.** P2a: all 3 tables live, 24-month full run (9,490 interactions, 926 commitments, 203 stakeholders). P2b waits on B1b (Cowork clearance + G0b) |

**Kill rule:** if no approved LLM route (B1b), P2b/P3/P6 die; programme still runs P1 + P2a + P4 + P5.

**Do now:** finish P1 (1.4/1.5), name Cowork status (B1b), spec P4 (account-health KPIs from signal→order latency).  
**Do not start without G0b:** shared Sales/Parts, any LLM on mail text, drafts/digest.

---

## 1. Premise — read this before the phases

### 1.1 The funnel framing does not apply

ISZE sells to distributors (DB), who sell to dealers, who sell to fleets. There is no lead funnel. The retail-funnel objectives translate as follows, and this translation is what orders the roadmap:

| Retail framing | ISZE equivalent | Instrumented today? |
|---|---|---|
| Conversion rate | PMS capture % (share of expected service demand sold) | ✅ `pms_capture_by_db_year.csv` |
| Deal size | GPS spend-per-unit | ✅ `gps_spu_by_distributor.csv` |
| Product mix quality | BVP mix | ✅ `mix_genuine_bvp_pms.csv` |
| Churn | defection / leakage | ✅ `defection_alerts.csv`, `dealer_leakage_ituk.csv` |
| **Sales-cycle length** | signal → DB action latency | ❌ **does not exist** |
| **Pipeline forecast** | order-rate forecast × parc | ❌ **does not exist** |
| **Stakeholder model** | who decides what, at which DB | ❌ **does not exist** |

The three missing rows are the entire subject of this roadmap. The seven existing capabilities are not rebuilt.

### 1.2 Asset inventory — what actually exists

| Asset | State | Location |
|---|---|---|
| Billing / sales fact | ✅ live, **net-only** (gross/SPA/condition closed 2026-08-11 — do not re-ask) | `01_data/04_sales/`, PRISM loaders |
| Dealer sell-out | ✅ partial coverage (ITUK, Greece, UTI/UMI) | `01_data/05_Dealer_sellout/` |
| Dated price lists PR00/ZPR1 2023–2025 + 2026 | ✅ landed 2026-08-11, **joins not yet validated** | `01_data/01_Pricing/history/` |
| UIO / parc | ✅ V19 DVLA-based, 2025 wired | `06_uio/_CURRENT/` |
| Warranty, tender, distributor master | ✅ | `01_data/06_`, `10_`, `08_` |
| Derived layer | ✅ 204 files | `01_data/00_derived/` |
| Scheduled automation pattern | ✅ 9 active skills | `../AUTOMATION_REGISTER.md` |
| **CRM** | ❌ none in workspace | — |
| **Lead log** | ❌ none | — |
| **Call transcripts** | ❌ none | — |
| **Live ERP integration** | ❌ none (SAP arrives as periodic extract) | — |
| **Email corpus** | ✅ **reachable locally via MAPI** — see §1.3. Graph/OAuth route is closed (tenant admin consent), local route is open | `01_data/17_interactions/` (to create) |

**Consequence:** this roadmap is built on email + the existing spine. It does not assume a CRM rollout, transcript capture, or ERP write-back. Each of those is a 6–12 month organisational programme and none is on the critical path.

### 1.3 Mail access — Graph is closed, MAPI is open

**Graph / OAuth route: closed.** The Anthropic M365 MCP client requires **tenant admin consent** at `isuzu-e.com` ("Beheerdersgoedkeuring vereist", 2026-08-12). Not self-serviceable. Same outcome for any other cloud connector (Composio et al.) — they all land on the same tenant consent policy.

**Local MAPI route: open.** Probed on this machine 2026-08-12:

| Check | Result |
|---|---|
| Classic Outlook | `C:\Program Files\Microsoft Office\Root\Office16\OUTLOOK.EXE` |
| `Outlook.Application` COM | ✅ OK, version 16.0.0.20228 |
| Python + pywin32 | ✅ `C:\Python314\python.exe`, `win32com.client` imports |
| MAPI stores | own mailbox + shared **Sales** + shared **Parts** (Exchange) |
| Volume | Inbox 23,343 items · Sent 4,075 · local cache **29.67 GB** OST |

The entire corpus is already on local disk, already authenticated, under permissions already granted. Nothing is circumvented: MAPI runs **as you**, inside your existing Exchange rights.

**Three consequences that change the plan:**

1. **No admin consent needed to start.** The technical blocker is gone. The *governance* gate is not — see §5.
2. **The shared `Sales` and `Parts` mailboxes are the highest-value corpus** (DB-facing, multi-year) **and the highest privacy load** — they contain colleagues' correspondence, not only yours. Own mailbox first, shared mailboxes only after the works-council step.
3. **COM has a shelf life.** New Outlook (`Microsoft.OutlookForWindows 1.2026.728.100`) is also installed and **does not support COM**. When IT forces migration, the collector dies. Therefore: COM is only the *collector*, feeding a local store the rest of the stack reads. Swappable component, isolated behind one interface.

### 1.4 What this roadmap deliberately excludes

- CRM selection or rollout
- Call recording / transcription (legal load far exceeds value at this account count)
- Any auto-sending of outbound mail — architecturally excluded, see P3
- Psychometric profiling of named individuals — replaced by account/role behaviour, see P6
- Re-derivation of GPS / PMS / BVP definitions — they are settled in `metric_dictionary.md`

---

## 2. The logic chain

Why the order is the order. Each arrow is a hard dependency, not a preference.

```
  P0 GOVERNANCE ────────────────────────────────┐
   G0a local-only  /  G0b egress + shared mbx   │ G0a gates P2a; G0b gates the rest
                                                │
  P1 DATA FOUNDATION                            │
   (was 15.1% blind → catalogue 98.2% 2026-08-12)│
        │                                       │
        │  any pricing/realization/forecast      │
        │  needs G1 signed                       │
        ▼                                       ▼
        │                     P2a INTERACTION LAYER  [G0a]
        │                      local MAPI · deterministic · zero egress
        │                       └─► P2b LLM enrichment  [G0b]
        │                                       │
        │                        ┌──────────────┼──────────────┐
        │                        ▼              ▼              ▼
        │                  P3 EMAIL→ACTION  P4 ACCOUNT     P6 ENGAGEMENT
        │                   (efficiency)     HEALTH         PLAYBOOKS
        │                        │          (needs P1+P2a)  (needs G0b+P2b)
        ▼                        │              │              │
  P5 FORECASTING ◄───────────────┘              │              │
   (needs clean PN coverage +                   │              │
    demand signal)                              │              │
        └────────────────┬───────────────────────┴──────────────┘
                         ▼
                  P7 OPERATIONALISE
              (register, own, monitor, retire)
```

**Three rules encoded in that graph:**

1. **P1 before P5.** A forecast built while a large share of CY2025 parts revenue sits on part numbers absent from the price list inherits that blind spot. (Was 15.1% at 2026-08-01; catalogue coverage now 98.2% — see §6.0.)
2. **P0 before P2.** Email ingestion without a closed legal basis is not a risk, it is a breach. No local-collector code merges before **G0a**; nothing leaves the device before **G0b**.
3. **P2 before P3/P4/P6.** All three consume the same three tables. Build the substrate once.

---

## 3. Phase summary

| Phase | Name | Weeks (from kickoff) | Effort (eng. days) | Gate to enter | Primary output |
|---|---|---|---|---|---|
| **P0** | Governance & access | 0–2 | 3–5 + legal/IT | — | Signed DPIA/LIA (split G0a / G0b) |
| **P1** | Data foundation | 1–4 | 8–12 | — | PN coverage ≥ 97% |
| **P2a** | Interaction layer — **local, deterministic, zero LLM** | 2–6 | 10–13 | **G0a** | 3 tables from MAPI, no data leaves the machine |
| **P2b** | Interaction layer — LLM enrichment | 6–9 | 6–8 | **G0b** | intent / sentiment / prose commitments |
| **P3** | Email → action | 6–10 | 12–18 | **G2** | Triage + drafts + digest |
| **P4** | Account health | 8–14 | 10–15 | **G1 + G2** | Scored portfolio + cockpit |
| **P5** | Forecasting | 10–16 | 15–20 | **G1** | Reconciled DB × category forecast |
| **P6** | Engagement playbooks | 14–20 | 8–12 | **G0b + G2** | Account playbooks + wedge trial |
| **P7** | Operationalise | continuous | 2–3 | per-phase | Register entries, owners, monitors |

**Total ~75–105 engineering days ≈ 1.5 FTE over ~5 months**, front-loaded on governance.

---

## 4. Gates

No phase starts until its gate is signed. Gate owner listed; gate is binary.

| Gate | Closes when | Owner | Blocks |
|---|---|---|---|
| **G0a** | *Local processing only, nothing leaves the device.* Internal note filed: purpose, scope, retention · own mailbox only (shared `Sales`/`Parts` excluded until G0b) · derived fields only, no bodies persisted · results not shared beyond you | You + DPO (light) | P2a |
| **G0b** | *Anything leaving the device, or touching shared mailboxes.* DPIA approved · LIA written · Art. 13/14 notice · works-council step done · LLM DPA + zero-retention + EU residency in writing · approved LLM route named (Cowork or other) | DPO + IT | P2b, P3, P6 |
| **G1** | PN price-list coverage ≥ 97% of billed revenue · `_verification_report.json` green · lineage documented | Data eng | P4, P5 |
| **G2** | 3 tables live · extraction precision ≥ 0.85 / recall ≥ 0.80 on the 150-message gold set · retention job proven by test delete · zero message bodies persisted (audited) | Data eng + you | P3, P4, P6 |
| **G3** | 4 weeks shadow mode complete · draft acceptance measured · false-P1 rate < 5% | You | P3 go-live |
| **G4** | Backtest WAPE beats current baseline (or establishes the first one) · override policy agreed | You + commercial | P5 go-live |
| **G5** | Stepped-wedge design pre-registered · endpoints fixed before wave 1 | You | P6 measurement claims |

---

## 5. P0 — Governance & access

**Objective:** make everything downstream legal and technically possible. This phase produces no code.

| # | Task | Effort | Owner |
|---|---|---|---|
| 0.1 | Scope memo: mailboxes, senders, fields derived, never-stored — ✅ **DONE, authorized 2026-08-12** → [`../G0A_LOCAL_MAIL_SCOPE.md`](../G0A_LOCAL_MAIL_SCOPE.md) | 0.5 d | You |
| 0.2 | DPIA (Art. 35 — systematic processing of personal data at scale) | 3–5 d | DPO |
| 0.3 | Legitimate-interest assessment (Art. 6(1)(f)) written and filed | 1 d | Legal |
| 0.4 | Art. 13/14 transparency notice + DB contract annex text | 1 d | Legal |
| 0.5 | Works-council / employee-rep consultation where own-staff mail is processed | var. | HR |
| 0.6 | **Parallel, non-blocking:** file the tenant admin-consent request with IT for the Anthropic M365 app (delegated `Mail.Read` only, never `Mail.Send`). Cheap to ask, slow to land — do not wait on it, P2a does not need it | 0.5 d | You + IT |
| 0.6b | Name the **approved LLM route** for company text (Cowork? other?). Everything in P2b/P3/P6 depends on this having a written answer | 1 d | You + IT |
| 0.7 | LLM vendor: DPA, SCCs, zero-retention / no-training, EU region — in writing | 1 d | Procurement |
| 0.8 | Retention policy: derived rows 24 months, hashes 24 months, bodies never | 0.5 d | DPO |
| 0.9 | Competition-law rule: correspondence revealing **other OEMs'** pricing intent is dropped at extraction, not stored | 0.5 d | Legal |

**Exit criteria:** G0a signed (week 1) → P2a starts. G0b signed (week 2–8) → P2b/P3/P6 unlock.
**Kill criteria:** ~~IT refuses Graph app registration~~ — **no longer a kill criterion.** Graph is already refused at tenant level and P2a routes around it via local MAPI. The remaining kill criterion is narrower: if no approved LLM route for company text exists (0.6b), then P2b/P3/P6 die and the roadmap runs P1 + **P2a** + P4 + P5 — which is still most of the analytical value, because P2a's outputs are deterministic (§7).

---

## 6. P1 — Data foundation

**Objective:** remove the known blind spot before anything is built on top of it.

### 6.0 Measured progress (2026-08-12)

| Checkpoint | Value | Source |
|---|---|---|
| Original published gap (2026-08-01) | 522 PN / €4.96M / **15.1%** | hub roadmap |
| Spec C4 remeasure (numeric, pre-pull) | 251 PN / €4.96M / 15.1% of catalogue parts | `no_pr00_gap_cy2025_ranked.meta.json` |
| Closed by SAP PR00 pull | **220 PN / €4.36M** | `no_pr00_gap_cy2025_closed_20260812.csv` |
| Catalogue-parts PR00 coverage now | **98.2%** (G1 ≥97% bar) | `pn_coverage_classification.meta.json` |
| All-billing coverage (incl. REBATE/TRANSPORT/interest) | 95.7% | same |
| Open residual (all classified) | €1.44M → **€1.38M non-catalogue** (admin + parked Shell) + **€67k / 24 PN** active ZPR1-path hardware | `pn_coverage_classification.csv` |
| Billed under superseded list number | **925 PN / €2.48M** (IE40 `newest_pn`; **not EPC-validated**) | `pn_supersession_map.csv` |

**Rebuild:** `python 01_data/01_Pricing/_build_pn_coverage_p1.py`

**G1 status:** coverage bar **met** on catalogue parts. Still open before signing G1: task **1.4** (year-matched joins), **1.5** (verify rule), EPC validation of the supersession map (finish **1.2**).

**At programme start** (source: `../ISZE_ROADMAP.md`, measured 2026-08-01): **522 part numbers, €4.96M, 15.1%**. Largest then: `7552348290` STEERING UNIT, €718,864 — **now closed** via SAP pull. Supersession billing is larger than the old €1.82M / 800 PN estimate (see map).

| # | Task | Effort | Output | Status 2026-08-12 |
|---|---|---|---|---|
| 1.1 | Classify the gap: superseded · new-not-yet-listed · non-catalogue · data error · closed | 3 d | `pn_coverage_classification.csv` | **Done** (254 rows: 220 closed + 34 open) |
| 1.2 | Build supersession chain resolver (old PN → current PN), validate against EPC | 3 d | `pn_supersession_map.csv` | **Starter done** (IE40 `newest_pn`); EPC validation open |
| 1.3 | Re-run realization / leakage with the resolved map; quantify the delta vs the 85% view | 2 d | delta report | **Next** |
| 1.4 | Validate year-matched list-to-pocket joins on PR00/ZPR1 2023–2025 | 3 d | join validation note | Open (B5) |
| 1.5 | Add coverage % as a standing check in `_verification_report.json` | 1 d | verify rule | Open |

**Exit criteria:** G1. Coverage ≥ 97% of billed revenue, or the residual is classified and explained line by line.
**Risk:** supersession data may not be complete enough to resolve all chains. Mitigation: classify-and-exclude beats silent inclusion.
**Note:** this phase is pure data quality, not AI. It gates credibility of P4 and P5.

---

## 7. P2 — Interaction layer

**Objective:** create the missing clock and the missing stakeholder model. Additive only — no existing table is modified.

### 7.1 Schema

Three new tables hanging off `distributor_dim`:

- **`interaction_fact`** — one row per message. Derived fields only: `intent`, `topic[]`, `entities` (JSONB), `sentiment`, `urgency`, `requires_action`, `extraction_conf`, `model_version`, `body_sha256`, `retention_expires`. **No body text.**
- **`stakeholder_dim`** — pseudonymous `stakeholder_id` (salted hash), `db_code`, **`role`** (`parts_manager` / `md` / `finance` / `workshop`), `decision_authority` (`economic` / `technical` / `user` / `gate`). **Roles, never personality.**
- **`commitment_fact`** — who promised what, by when, met or missed, with `evidence_ref` to the interaction that closed it.

Full DDL: see §7.2 of the design note (to be written as task 2.1).

### 7.2 Three non-negotiable design rules

1. **Bodies are never persisted.** Hash + derived fields only. Converts a DSAR nightmare into a manageable derived dataset.
2. **`model_version` is mandatory and append-only.** Re-extraction inserts new rows, never mutates old ones. Without this, Q1 figures silently change in Q3 — the exact failure the "DO NOT QUOTE" section of `metric_dictionary.md` exists to prevent.
3. **The LLM never emits a number that lands in a table.** It classifies and locates; regex + catalogue joins produce values. Part numbers are accepted only if present in `parts_catalog_dimension`. Amounts come from regex, not the model.

### 7.3 The split that unblocks everything: what actually needs an LLM

Most of the leading KPIs in §13 are **deterministic**. They need timestamps, thread structure, regex and a catalogue join — not a model. That means they can be produced **entirely on this machine, with nothing transmitted anywhere**, under G0a only.

| Signal | Method | LLM? | Phase |
|---|---|---|---|
| Thread structure, direction, timestamps | MAPI properties | ❌ | P2a |
| ISZE response latency p50/p90 | timestamp arithmetic | ❌ | P2a |
| Signal→order latency | thread ts + PN regex + `sales_fact` join | ❌ | P2a |
| Part / order / invoice numbers | regex, validated against `parts_catalog_dimension` | ❌ | P2a |
| Amounts, dates, deadlines | regex | ❌ | P2a |
| Topic tags (pricing / stock / warranty / tender / logistics) | keyword lexicon | ❌ | P2a |
| Stakeholder map, role inference, `stakeholder_churn_flag` | address frequency + thread position + signature block | ❌ | P2a |
| Volume, cadence, escalation count (CC-depth spikes) | counting | ❌ | P2a |
| Commitment detection — explicit ("we will ship by 14/09") | date+modal regex | ❌ | P2a |
| **Intent classification (11 classes)** | model | ✅ | P2b |
| **Sentiment / tone slope** | model | ✅ | P2b |
| **Commitment detection — implicit, in prose** | model | ✅ | P2b |
| **Engagement posture (P6)** | model + aggregation | ✅ | P2b |

**~70% of the analytical value of the interaction layer is in the ❌ rows.** That is the workaround: build those first, with zero external transfer and zero consent dependency.

### 7.4 P2a — local collector (G0a only)

```
Outlook (classic, MAPI/COM)
        │  read-only, runs AS YOU, in your interactive session
        ▼
 collector.py  ── swappable interface (COM today; New Outlook kills COM someday)
        │  own mailbox first; shared Sales/Parts only after G0b
        ▼
 DB-domain allow-list ──► drop everything else at the door
        │
        ▼
 deterministic extract (regex + lexicon + MAPI props) — NO network calls
        │
        ▼
 parquet in 01_data/17_interactions/   ← derived fields + body_sha256 only
        │                                 NO bodies, NO subjects in shared output
        ▼
 PRISM / derived layer
```

| # | Task | Effort | Status 2026-08-12 |
|---|---|---|---|
| 2a.0 | Allow-list generated from the DB master → `04_tools/interactions/db_domains.yaml` | 0.5 d | ✅ **Done** — 24 unambiguous DB domains. UMI `umi.co.il` / UTI `uti.co.il` added 2026-08-12. Still no contact: ARMENIA, KAZAKHSTAN, PALESTINE. `suggest_db_domains.py` proposes matches (manual review required) |
| 2a.1 | Design note + schema + `01_data/17_interactions/` + DATA_MANIFEST entry | 2 d | ✅ **Done** — folder + README + `.gitignore`, manifest row 17. Governance memo `G0A_LOCAL_MAIL_SCOPE.md` live |
| 2a.2 | `collect_mapi.py` — MAPI read-only, own-store guard, DB-domain filter, `--since` / `--limit` / `--dry-run` | 3 d | ✅ **Done** — 24-month run: **9,490** interactions / **926** commitments. Windowing (30-day per-window checkpoints). **Subfolder recurse**: inbox root + IE30 (25 extra) + Inbox_2 + Outlook_Customer_Manager + Sent (1,377). Total examined 31,532; kept 9,490; unmatched 21,667; non-mail 375; errors 0 |
| 2a.3 | Deterministic extractor: PN/amount/date regex, topic lexicon, explicit-commitment flag | 3 d | ✅ **Done** — 9 topics; PN validated against `parts_catalog_dimension`. **det-v2**: commitment hit-rate **9.8%** (926 / 9,490); typed mix (`delivery` / `meeting` / `order_volume` / `stock_confirm` / `price_quote` / `data_delivery`); cross-sentence date matching; relative date parsing |
| 2a.4 | Resolver: validate PN / DB-code against existing dimensions | 2 d | ✅ **Done** for PN + DB. Order-no resolver **open** (not required for signal-latency metric) |
| 2a.5 | `stakeholder_dim` builder (pseudonymous hash, salt outside repo) | 1 d | ✅ **Done** — **203 rows**, 93 above 10-interaction evidence bar. Roles: **`parts_manager`** (81) / **`workshop`** (11) with evidence. **`decision_authority`** (economic/technical/gate). **Churn-flagged:** 49. `db_response_latency.parquet`: **8 DBs above bar**, IUK fastest (0.9h p50), UKRAINE slowest (13.9h) |
| 2a.6 | Retention + hard-delete job + DSAR lookup runbook | 2 d | ✅ **Skeleton done** — `retention_expires` at write; `purge_expired.py` dry-run default / `--apply` / `--stakeholder-id` / `--lookup`; DSAR runbook `00_docs/DSAR_ERASURE_RUNBOOK.md`. Dry-run proof: **0 expired** (first deletion due 2027-08…2028-08). `--apply` not run. No scheduled job |
| 2a.7 | `commitment_fact` + open/met/missed state machine | 2 d | ✅ **Done** — `build_commitment_status.py`: **926 commitments**, status breakdown: **met 579** (62.6%) / **missed 335** (36.2%) / **open 12** (1.3%) / **unknown 0**. State: met = thread activity at/after `due_date` (deterministic proxy, not LLM). Keep-rate: DB 63.9% / ISZE 60% |
| 2a.8 | Recover DBs with no contact on file | 0.5 d | 🟡 **Partial** — UMI/UTI in `db_domains.yaml`. `suggest_db_domains.py` ready for ARMENIA / KAZAKHSTAN / PALESTINE (proposes only, manual review required) |

**Exit criteria:** three tables populated from own mailbox; signal→order latency and response latency computable; zero bodies persisted (audited); zero remote egress (verified). **✅ ALL MET.**
**Status 2026-08-12 (EOD):** **P2a COMPLETE.** Full 24-month run finished with 0 errors.
- `interaction_fact.parquet`: **9,001 rows** (17 distributors; 9,490 matched messages)
- `commitment_fact.parquet`: **926 rows** (typed, due-dated, status-classified; implicit prose deferred to P2b)
- `stakeholder_dim.parquet`: **203 rows** (pseudonymous, role + churn + consensus width)
- `db_response_latency.parquet`: **16 rows** (p50/p90 per DB; 8 above evidence bar)
- **No bodies/subjects/plain addresses** stored. Pseudonymous salt outside repo.

**What is now possible:** signal→order latency per DB, response latency SLA tracking, commitment fulfilment rate (62.6% met), stakeholder role/churn mapping. **What still blocks G2:** implicit-commitment detection (P2b), intent classification (P2b), LLM route (B1b / Cowork clearance).
**Backstop if COM dies:** manual PST export → same extractor. The collector is one file behind one interface, deliberately.

### 7.5 P2b — LLM enrichment (G0b required)

| # | Task | Effort |
|---|---|---|
| 2b.1 | **Gold set: 150 hand-labelled messages**, stratified by intent | 3 d (you: 1 d) |
| 2b.2 | PII redaction + prefilter (drops newsletters/auto-replies before any model call) | 2 d |
| 2b.3 | Extraction prompt v1 + structured schema, temp=0, versioned + hashed into `model_version` | 3 d |
| 2b.4 | Implicit-commitment detector + open/met/missed state machine | 2 d |

**Exit criteria:** G2.
**Risk:** task 2b.1 is the one people skip. Without a gold set you cannot distinguish a prompt improvement from a regression, and the layer becomes unfalsifiable. Not optional.
**Route:** whichever LLM path IT names in task 0.6b. If that is Cowork, P2b runs there and the API question never arises.

---

## 8. P3 — Email → action

**Objective:** efficiency. The self-funding phase, lowest model risk.

### 8.1 Architecture

```
 M365 ──Graph delta──► Ingest+gate ──► Redact ──► Prefilter ──► LLM extract
                        (allow-list)                              (temp=0)
                                                                     │
                                          resolve + join dimensions ◄┘
                                                     │
                                              Action router
                                    ┌────────────────┼────────────────┐
                                    ▼                ▼                ▼
                            daily digest      DRAFT in Outlook    task + commitment
                            (fyi / admin)     (never auto-send)   + dashboard alert
                                    └────────────────┴────────────────┘
                                                     ▼
                                       interaction_fact / commitment_fact
                                                     ▼
                                              PRISM + HTML
```

### 8.2 Routing rules (deterministic layer overrides the model)

```yaml
rules:
  - id: tender_deadline
    when: {topic: tender, entities.due_date_within_days: 14}
    then: {priority: P1, notify: immediate, create_commitment: true}
  - id: pricing_escalation
    when: {intent: complaint, topic: pricing, sentiment: "< -0.4"}
    then: {priority: P1, draft: false, brief: pricing_context_pack}
  - id: stock_enquiry
    when: {intent: availability, entities.part_no: "not empty"}
    then: {priority: P2, draft: true, template: availability_reply}
  - id: routine_order_ack
    when: {intent: order, extraction_conf: "> 0.85"}
    then: {priority: P3, draft: true, template: order_ack}
  - id: default
    then: {priority: P4, digest: daily}
```

### 8.3 Tasks

| # | Task | Effort |
|---|---|---|
| 3.1 | Rules engine + YAML config (thresholds live in config, never in code) | 2 d |
| 3.2 | Draft generator → Outlook **Drafts** folder, source thread linked | 3 d |
| 3.3 | Daily digest (the first shippable value — ship before drafts) | 2 d |
| 3.4 | Dashboard alert feed → `01_data/14_dashboards/` | 2 d |
| 3.5 | **Shadow mode:** pipeline runs, nothing user-facing, weekly grading | 4 wk elapsed, 0.5 d/wk |
| 3.6 | Tune on shadow results; re-measure against gold set | 3 d |
| 3.7 | Go-live + register as CHEAP-tier scheduled skill | 1 d |

### 8.4 Hard rules

- **No auto-send, ever.** `Mail.Send` is not requested from Graph at all — the capability does not exist in the app registration. This inherits `.cursor/rules/isze-no-ship-without-ok.mdc`.
- **Precision over recall on `requires_action`.** A missed FYI costs nothing. A false "urgent" trains you to ignore the system, and then it is dead.
- **Value order: digest → commitment tracking → drafting.** Drafting is the least valuable and most risky; it ships last.

### 8.5 ROI model — formula, inputs to be filled

```
Annual hours saved
  = V × 52 × [ (t_triage × r_auto) + (t_draft × r_draft × p_accept) ]
    + C × h_recovered

V           DB-related emails per week                    → MEASURE (one week)
t_triage    minutes to read/classify/file one email       → MEASURE
r_auto      share auto-classified above threshold         → pipeline output
t_draft     minutes to compose a routine reply            → MEASURE
r_draft     share of replies that are routine             → MEASURE
p_accept    share of drafts sent with ≤ minor edits       → shadow mode (3.5)
C           commitments/yr that currently slip unnoticed  → unknown until P2 runs
h_recovered hours of chase/rework per slipped commitment  → MEASURE
```

**Do not populate this with illustrative numbers in any shared document.** The `C × h_recovered` term is usually the larger one and is unknowable before P2. Running cost is dominated by LLM calls on the post-prefilter volume, which is typically 40–60% of raw.

**Exit criteria:** G3.

---

## 8.6 P3 dependencies on P2b (implicit commitments)

Tasks 3.1–3.7 all require intent classification + implicit-commitment detection (P2b tasks 2b.3–2b.4). Until B1b (Cowork clearance) lands, P3 is blocked. P2a output can support daily digest *stubs* (volume count, routine acknowledgements of known-PN orders) but no intent-based routing.

---

## 9. P4 — Deterministic operational signals

**Objective:** convert P2a tables (interaction_fact, commitment_fact, stakeholder_dim) into account-ops signals — response SLA, commitment tracking, churn risk — deployable immediately, with no model.

**Output:** account_health.parquet (one row per DB + month). 8 deterministic metrics + alert routing.

| Signal | Data source | Method | Ready now? |
|---|---|---|---|
| Response latency p50/p90 | interaction_fact | timestamp arithmetic, rolling 30d | ✅ yes |
| Commitment met-rate | commitment_fact | status='met' / (met + missed), rolling 90d | ✅ yes |
| Signal→order latency | interaction_fact + sales_fact | PN regex ts(mail) → order_date, rolling 90d | ✅ yes (join exists) |
| Stakeholder churn % | stakeholder_dim | churn_flag aggregated per DB, rolling 90d | ✅ yes |
| Escalation cadence | interaction_fact | threads with CC-depth ≥3, rolling 30d | ⚠️ cc_depth not extracted yet |
| Topic entropy | interaction_fact | Shannon entropy of topic[], rolling 90d | ✅ yes |
| Activity volume | interaction_fact | count per day, rolling 30d | ✅ yes |
| Overdue commitments | commitment_fact | count(status='open' AND due_date < today) | ✅ yes |

**Schema, methods, alert thresholds, build task list:** [`P4_DETERMINISTIC_SIGNALS.md`](P4_DETERMINISTIC_SIGNALS.md)

**Blockers:** CC-depth extraction (P2a.9, trivial collector extension).

**Effort:** 1.5 weeks (6–7 d dev + 1 d you: calibration).

**When:** immediately after P2a, before B1b lands. Gives ops team a working baseline while waiting for model.

| # | Task | Effort |
|---|---|---|
| 4.0 | Extract cc_depth from interaction_fact (collector P2a.9) | 0.5 d |
| 4.1–4.8 | Implement signal calculators + alert router (see P4_DETERMINISTIC_SIGNALS.md) | 5 d |
| 4.9 | Manual calibration on 6mo backfill (you: threshold tuning) | 1 d |
| 4.10 | Dashboard / ops runbook integration | 1 d |

**Exit criteria:** account_health.parquet shipping monthly, no false alerts from malformed data, top-3 accounts flagged monthly.

---

## 10. P4 — Account health scoring (predictive model)

**Objective:** rank accounts for attention. Replaces "lead scoring", which has no referent here.

**Label definition (yours to set, and it defines the whole model):** DB revenue in category *c* declines more than **X%** over the next 2 quarters vs the trailing 4-quarter mean.

**Features** — structured (existing) + interaction (new):

```
structured : gps_spu_trend_4q, pms_capture_delta_yoy, bvp_mix_shift,
             order_frequency_cv, days_since_last_order, category_breadth,
             pn_count_active_delta, warranty_claim_rate
interaction: inbound_volume_delta_qoq, pricing_complaint_rate, sentiment_slope_2q,
             db_commitment_keep_rate, our_response_latency_p50,
             escalation_count_2q, stakeholder_churn_flag
```

**Model:** gradient-boosted trees (LGBM, depth 4, balanced). Not deep learning — you need explanations more than the last two points of AUC.
**Validation:** `TimeSeriesSplit` only. Random CV leaks the future and will lie to you.
**Output contract:** every score ships with its top-3 SHAP drivers and `evidence_refs`. No score reaches a human naked.

| # | Task | Effort |
|---|---|---|
| 4.1 | Label definition workshop; fix X | 0.5 d |
| 4.2 | Feature pipeline from existing derived files + P2 tables | 4 d |
| 4.3 | Train / temporal backtest / calibration | 3 d |
| 4.4 | SHAP + output contract + JSON schema | 2 d |
| 4.5 | PRISM page: Account Cockpit + Portfolio Triage (§13) | 4 d |
| 4.6 | Band thresholds set by **capacity**, not by the model | 0.5 d |

**Risk:** scores get treated as truth in a meeting. Mitigation: drivers + evidence mandatory on every display; band = "how many accounts can you actually work this month", not a probability cut-off.

---

## 11. P5 — Forecasting

**Objective:** a reconciled, auditable demand forecast. First honest one, if no baseline exists.

**P5.1 finding (2026-08-12, workspace search):** no operational forecast process, WAPE baseline, or forecast artefact lives in this workspace (only incidental mail-pull PN demand-forecast confirmation snippets under inbox archives). Treat P5 as **creating the first measured baseline**, not improving an existing one — unless Jerome points at an external commercial process (B3).

```
base      : per (db_code, category) monthly demand
method    : ETS / auto-ARIMA per series, UIO (parc) as exogenous regressor
reconcile : MinT across DB → region → ISZE total
override  : commercial adjustments logged as a SIGNED DELTA ROW,
            never edited into the base
KPI       : WAPE + bias, rolling-origin backtest, reported per horizon (1/3/6 mo)
```

| # | Task | Effort | Status |
|---|---|---|---|
| 5.1 | Establish the current baseline error — or record that none exists | 2 d | **Provisional:** none in workspace (confirm B3) |
| 5.2 | Series construction + intermittency handling (many DB × category pairs are sparse) | 4 d | Blocked on G1 sign-off |
| 5.3 | Base models + parc regressor | 4 d | — |
| 5.4 | MinT reconciliation across the hierarchy | 3 d | — |
| 5.5 | Override mechanism (signed delta rows + audit) | 2 d | — |
| 5.6 | Rolling-origin backtest harness + WAPE/bias reporting | 3 d | — |
| 5.7 | PRISM page + monthly refresh hook | 2 d | — |

**Exit criteria:** G4 — beats baseline, or establishes the first measured one.
**Risk:** rejection by the commercial team. The override-as-logged-delta design is the mitigation: judgement is welcome, *silent* judgement is not. Override magnitude (`Σ|delta| ÷ Σ base`) becomes a monitored KPI in its own right.

---

## 12. P6 — Engagement playbooks

**Objective:** systematise how each account is worked. **Renamed from "personality-driven" deliberately — the rename is the risk control.**

### 11.1 Why not personality

Inferring psychological traits about identifiable people, at scale, by automated means, to influence commercial outcomes, is a mandatory-DPIA / Art. 22-adjacent exposure and a relationship-ending leak if it ever surfaces ("the OEM keeps psychological files on our staff"). Nearly all the commercial value survives a version that profiles **observable engagement behaviour at account and role level**. You do not change your approach because someone is "high-C"; you change it because that account always wants the data before the meeting.

### 11.2 Four observable dimensions

| Dimension | Measured from | Separates |
|---|---|---|
| Evidence appetite | data requests per thread, attachments, prep asks | data-first vs relationship-first |
| Decision latency & path | signal→commit days, distinct stakeholders per decision thread | fast-single vs slow-consensus |
| Channel & cadence | reply latency distribution, message length, meeting:mail ratio | verbal vs written |
| Negotiation posture | pricing-topic share, counter-offer frequency, keep-rate | price-led vs availability-led vs partnership-led |

```python
profile[db_code] = {
  "evidence_appetite":  pct_threads_with_data_request,
  "decision_latency_d": median_signal_to_commit_days,
  "consensus_width":    median_distinct_stakeholders_per_decision_thread,
  "posture":            argmax(topic_share),
  "preferred_channel":  argmax(channel_mix),
  "evidence_refs":      [...],          # mandatory, non-empty
  "computed_at": date, "model_version": v, "n_interactions": n,
}
assert n_interactions >= 30   # below threshold: NO profile, not a weak one
```

**No score without receipts.** Every field carries the interactions that produced it.

### 11.3 Execution

| # | Task | Effort |
|---|---|---|
| 6.1 | Compute profiles for DBs above the evidence threshold | 2 d |
| 6.2 | Map profile → playbook (pre-read vs walkthrough; single vs consensus sequence; GPS-gap vs availability vs total-cost framing) | 2 d |
| 6.3 | **Show the profile to the DB** — "this is how we've observed we work best together, is this right?" | — |
| 6.4 | Attach playbook section to the existing `09_meetings/` deck generator | 3 d |
| 6.5 | Quarterly recompute + `stakeholder_churn_flag` trigger | 1 d |

Task 6.3 is the design's keystone: it converts a compliance liability into a relationship asset, and it yields better data than inference ever will.

### 11.4 Measuring uplift

**Not before/after.** Before/after will show an uplift regardless, because playbooks get deployed where you were already leaning in.

**Stepped-wedge:** rank DBs, block into matched pairs on GPS spend-per-unit and PMS capture, release playbooks to one arm per quarter.
- Primary endpoint: Δ GPS spend-per-unit vs matched control
- Secondary: signal→order median days, commitment keep-rate, meeting→action conversion
- **Pre-register endpoints and analysis before wave 1** (G5)

**Honest expectation:** with roughly 20 distributors, power is low and any single-quarter result is noise. Treat Q1 as directional; expect 3–4 quarters before the estimate means anything. Anyone promising a specific % uplift on 20 accounts in one quarter is selling something.

---

## 12. Dashboard targets

Two views. Resist a third.

**A — Account Cockpit** (one DB, one screen, pre-call):

```
┌────────────────────────────────────────────────────────────────────┐
│ DB: <name>            Health: ●RISK 0.68 ▲    Last contact: 4d ago │
├───────────────────────┬────────────────────────────────────────────┤
│ GPS spend/unit  ▁▃▅▄▂ │  Top drivers (SHAP)                        │
│ PMS capture     ▁▂▄▅▅ │  ▸ pricing_complaint_rate    +0.21         │
│ BVP mix         ▅▅▄▃▂ │  ▸ order_frequency_cv        +0.14         │
│ vs peer group   ──●── │  ▸ gps_spu_trend_4q          −0.11         │
├───────────────────────┴────────────────────────────────────────────┤
│ OPEN COMMITMENTS                        │ ENGAGEMENT PROFILE       │
│ ⚠ ISZE  price list Q4      due -6d      │ evidence-first, consensus│
│ ○ DB    volume forecast    due +9d      │ written, price-led       │
│ ✓ ISZE  stock confirm      met          │ [30 interactions · Q3]   │
├─────────────────────────────────────────┴──────────────────────────┤
│ NEXT BEST ACTION  ▸ <action>            [evidence: 3 threads →]    │
└────────────────────────────────────────────────────────────────────┘
```

**B — Portfolio Triage** (Monday morning): sortable table — DB · health band · Δ health 4w · GPS SPU vs peer · capture % · overdue commitments · days since contact · one-line NBA. Filters: region, band, category. No pie charts, no gauges.

**Build order:** PRISM page first (`03_analytics/Isuzu/prism/pages/`); static HTML twin in `02_dashboards/` only once numbers are stable → `sync_to_deploys.ps1`. This is the existing pattern; do not invent a second one.

---

## 13. KPI ledger

Every KPI below must be added to `03_analytics/Isuzu/prism/docs/metric_dictionary.md` **with its formula before it appears anywhere.** That discipline lapsed once already — see the "DO NOT QUOTE" section there.

| Layer | KPI | Definition | Cadence | Phase |
|---|---|---|---|---|
| Lagging | GPS spend-per-unit | existing: actual ÷ target wallet | Quarterly | — |
| Lagging | PMS capture % | existing, `line_type='total'`, uncapped in CSV | Quarterly | — |
| Lagging | **PN price-list coverage %** | billed revenue on PNs present in PR00 ÷ total | Monthly | P1 |
| Leading | **Signal→order median days** | first inbound action-required → next order line, same category, ≤90 d | Monthly | P2 |
| Leading | **DB commitment keep-rate** | met ÷ (met+missed), `owner_side='db'` | Monthly | P2 |
| Leading | **ISZE response latency p50/p90** | first outbound after inbound action-required | Weekly | P3 |
| Leading | **Sentiment slope** | 2-quarter regression per DB | Quarterly | P2 |
| Pipeline | **Forecast WAPE + bias** | rolling-origin, per horizon | Monthly | P5 |
| Pipeline | **Override magnitude** | Σ\|manual delta\| ÷ Σ base | Monthly | P5 |
| System | **Extraction precision/recall** | vs 150-msg gold set, re-run each prompt change | Per release | P2 |
| System | **Draft acceptance rate** | sent with ≤ minor edits ÷ drafts generated | Weekly | P3 |
| System | **Auto-classification rate** | above-threshold confidence ÷ total | Weekly | P3 |

**Small-n rule:** suppress any DB × topic cell with fewer than 10 signals. Do not display, do not quote.

---

## 14. Compliance checklist

| # | Item | Owner | Gate |
|---|---|---|---|
| 1 | DPIA (Art. 35) | DPO | G0b |
| 2 | Legal basis + written LIA (Art. 6(1)(f)) | Legal | G0b |
| 3 | Art. 13/14 notice + DB contract annex | Legal | G0b |
| 4 | Data minimisation — bodies never persisted | Eng | design |
| 5 | Pseudonymisation — salted hash, salt in secret store **not the repo** | Eng | design |
| 6 | Special categories hard-blocked at extraction (health, union, political, religious) | Eng | design |
| 7 | Art. 22 — no automated decision with legal/significant effect; scores rank, humans decide | You | policy |
| 8 | Retention: `retention_expires` set at write; monthly hard-delete job, audited | Eng | G2 |
| 9 | DSAR / erasure runbook — locate + delete by `stakeholder_id` within 30 days | DPO | G2 |
| 10 | Works council / employee reps consulted — **required before shared `Sales`/`Parts` mailboxes enter scope** | HR | G0b |
| 11 | EU residency; LLM under DPA + SCCs + zero-retention, in writing — **n/a for P2a (no egress)** | Legal + IT | G0b |
| 12 | Role-based access to profiles; audit log on every read | IT | G2 |
| 13 | **No personal names in Mode A output** — existing external-language rule applies to every artefact here | You | every release |
| 14 | **Competition law** — never store or model another OEM's pricing intent from DB correspondence; flag and drop | Legal | design |
| 15 | Vendor review through procurement | Procurement | G0b |

Item 14 is the one that gets forgotten and has the largest downside.

---

## 15. Resourcing

| Role | FTE | Weeks | Skills gap risk |
|---|---|---|---|
| Data engineer (Python, SQL, Graph API) | 0.6 | 1–20 | M365 Graph — likely new |
| Analytics engineer (parquet, PRISM) | 0.4 | 4–20 | none — pattern exists |
| ML engineer | 0.3 | 8–16 | hierarchical reconciliation — likely new |
| Product owner (you) | 0.2 | throughout | thresholds, gold-set labelling, override policy |
| DPO / Legal | ~10 d total | 0–6 | front-loaded |
| IT security | ~5 d | 0–4 | Graph registration, DPA review |

**Skills to acquire or hire:** M365 Graph API · LLM structured extraction with evals · hierarchical forecasting with MinT reconciliation. Everything else is inside what the workspace already demonstrates.

---

## 16. Risk register

| Risk | L | I | Mitigation | Phase |
|---|---|---|---|---|
| Email work starts before DPIA closes | High | Severe | G0a/G0b are hard merge gates; P2a is egress-free by construction | P0 |
| Extraction quality drifts silently | High | High | Gold set + `model_version` + per-release metrics | P2 |
| Analytics built on the 15.1% blind spot | Was certain at start; **catalogue coverage now 98.2%** | High | Finish 1.4/1.5 + sign G1 before P5 | P1 |
| Scores treated as truth in a meeting | Medium | High | SHAP + `evidence_refs` mandatory on display | P4 |
| Auto-send incident with a distributor | Low | Severe | `Mail.Send` never requested — architecturally impossible | P3 |
| Profiling read as surveillance by DBs | Medium | Severe | Account/role level only; show them the profile (6.3) | P6 |
| Forecast rejected by commercial team | Medium | Medium | Override-as-logged-delta | P5 |
| Another orphan pipeline in a 204-file derived folder | Medium | Medium | P7: register or it doesn't ship | P7 |
| Low statistical power on ~20 accounts | High | Medium | Stepped wedge + pre-registration + state it upfront | P6 |

---

## 17. P7 — Operationalise

Nothing ships without all four:

1. Entry in `../AUTOMATION_REGISTER.md` — status, cadence, model tier, inputs, outputs, path preflight, owner review
2. Named owner (default: you)
3. A monitor that fails loudly (extraction metrics, retention job, freshness)
4. A retirement condition — what makes this job obsolete, so it doesn't rot in place

Model tier: all of these are **CHEAP** except P6 profile generation, which is **FRONTIER**.

---

## 18. Blockers — open, dated 2026-08-12

| # | Blocker | Impact if unresolved | Owner | Status |
|---|---|---|---|---|
| **B1** | ~~M365 connector unauthorized~~ — Graph needs tenant admin consent; superseded by local MAPI (§1.3). Task 0.6 still parallel | none — P2a routes around it | — | Resolved-by-route |
| **B1b** | **Approved LLM route for company text not named** (Cowork or other?) | P2b, P3, P6 blocked; P1+P2a+P4+P5 still run | You + IT | Open |
| **B1c** | Shared `Sales`/`Parts` mailboxes = colleagues' mail — works-council before scope | Halves corpus until closed | You + HR | Open |
| **B1d** | New Outlook installed; COM dies if IT forces migration | Collector rewrite (one file) | You + IT | Watch |
| **B2** | CRM elsewhere in ISZE/IML not visible here? | Changes §7 schema | You | Open |
| **B3** | Current forecast process with measurable error? | P5 improves vs creates baseline | You | **Workspace: none** (P5.1) — confirm external |
| **B4** | DPO for ISZE, or via IML legal? | P0 is 2 weeks or 8 | You | Open |
| **B5** | Year-matched PR00/ZPR1 list-to-pocket joins not validated | Do not quote leakage; task 1.4 | Data eng | Open — **next Track A** |

---

## 19. Decisions required (log to `../../DECISIONS.md` when taken)

| # | Decision | Needed by |
|---|---|---|
| D1 | Go / no-go on local collector (G0a) — own mailbox only | Week 1 |
| D1b | Approved LLM route named, or P2b/P3/P6 shelved | Week 4 |
| D2 | Label threshold X for "at risk" in P4 | Week 8 |
| D3 | Band thresholds by capacity — how many accounts worked per month | Week 12 |
| D4 | Override policy: who may adjust the forecast, and does it require a reason string | Week 14 |
| D5 | Do DB engagement profiles get shown to the DB (recommended yes) | Week 16 |
| **D6** | Sign G1 on catalogue-parts 98.2% + classified residual, or wait for 1.4/1.5? | **This week** |

---

## Changelog

| Date | Change |
|---|---|
| 2026-08-12 | Created. Proposed, not approved. No code written. |
| 2026-08-12 | **Mail route revised.** Graph/OAuth closed (tenant admin consent required). Local MAPI probed and confirmed open (§1.3). P0 gate split G0a/G0b; P2 split P2a (local, deterministic, zero LLM, zero egress) / P2b (LLM enrichment). B1 superseded; B1b–B1d opened. Still no code written. |
| 2026-08-12 | **Track A executed.** Dual-track §0. P1.1 `pn_coverage_classification.csv` + P1.2 starter `pn_supersession_map.csv`. Spec C4 pull close reflected. Catalogue PR00 coverage **98.2%**. P5.1: no in-workspace forecast baseline. G0a still required before any MAPI ingest merge. |
| 2026-08-12 | **P2a collector live.** Jerome authorized G0a. `04_tools/interactions/collect_mapi.py` + `db_domains.yaml`; first write `01_data/17_interactions/interaction_fact.parquet` (100-row smoke). Socket guard softened so Outlook COM/RPC works. DB email master filed under `01_data/08_Distributor/`. |
| 2026-08-12 | **P2a task ledger + full pull.** §7.4 rewritten with per-task status (2a.0–2a.7). Duplicate G0a memo reconciled. UMI/UTI allow-list gap logged then fixed. |
| 2026-08-12 | **UMI/UTI allow-list fixed.** Own-mailbox probe (domains only): `umi.co.il` / `uti.co.il`. Master xlsx + `db_domains.yaml` updated; Armenia/Kazakhstan/Palestine still no contact. Kept as separate DBs (never blend). |
| 2026-08-12 | **3 tables on partial collect.** `--since 2024-08-01` killed mid-run (exit 4294967295); checkpoint ~7k interactions kept. `stakeholder_dim` + `commitment_fact` (with met/missed/open) built. G2 still blocked on 2a.6 + full Sent pass. |
| 2026-08-12 | **UMI/UTI allow-list fixed.** Own-mailbox probe (domains only): `umi.co.il` / `uti.co.il`. Master xlsx + `db_domains.yaml` updated; Armenia/Kazakhstan/Palestine still no contact. Kept as separate DBs (never blend). |
| 2026-08-12 | **2a.5 + 2a.7 built.** `build_stakeholder_dim.py` → `stakeholder_dim.parquet` (functional role from topic mix, `consensus_width`, `stakeholder_churn_flag`, 10-interaction evidence bar) + `db_response_latency.parquet` (p50/p90 inbound→reply per DB). Commitment extraction moved into the collector: type, `due_date`, `owner_side`, `has_amount`, `sentence_sha256` — **explicit dated promises only, no met/missed status**. `suggest_db_domains.py` added for the three DBs still without contacts (proposes, never writes). 24-month collect re-run so both fact tables come from one pass. **G2 still not claimable** — 2a.6 (delete job) and the 2a.7 state machine remain open. |
| 2026-08-12 | **2a.6 closed.** DSAR runbook `00_docs/DSAR_ERASURE_RUNBOOK.md`; `purge_expired.py` hardened (dry-run default, `--apply`, `--stakeholder-id`, `--lookup`; retention cascade only deletes rows tied to expired ids — never re-syncs dim to a partial fact). Retention dry-run: **0** expired across interaction/commitment/stakeholder. `--apply` not run. **G2 still blocked on P2b gold set** (not on 2a.6). |
