# Scraper redo — delegation file (Claude orchestrates, DeepSeek works, GPT reviews)

**Written:** 2026-09-24 · internal · status **Phase 0 + 5 built 2026-09-24 (no scraping). Windows-side work: `00_docs/agent/CURSOR_BRIEF_SCRAPER_REDO_20260924.md`**
**Parent plan:** the "match numbers first, then price" redesign (chat 2026-09-23/24). Phases 0–4 below follow it.
**Existing plumbing reused:** `04_tools/deepseek_utils.py` (`DeepSeekClient`, `MODEL_FLASH`, `MODEL_PRO`), `04_tools/autodoc_scraper/check_scrape_consent.py`, `00_docs/agent/DELEGATOR_BOARD.md`, `00_docs/agent/AI_STACK.md`.
**Still open from Jerome (does not block Phase 0):** (1) main purpose — ITUK defence, next price revision, or maintenance-parts campaigns; (2) budget for a TecAlliance / wider Eucon licence.
**Resolved 2026-09-24 (chat, this session):** (3) explicit go for live scrape — **given**, all six Phase 1 platforms in parallel. **Also given the same turn:** Eucon-sourced competitor numbers (93% of the match index) may be used to drive the scrape now, before legal has answered the four open questions in `00_docs/EUCON_LICENCE_BRIEF_2026-09-24.md` — Jerome's explicit choice, risk flagged and accepted. See `DECISIONS.md` 2026-09-24 entry. **Not changed:** Eucon-sourced rows still never go to DeepSeek or any outside-EU service (§3 below) — that boundary was not addressed in the go and stays as the standing rule until Jerome says otherwise.

> **RECONSTRUCTION NOTE, 2026-09-24 16:55.** This file was destroyed at 16:51 by an editing mistake — a
> script opened it for writing and then failed on an encoding error, leaving it at 0 bytes. It was
> never committed to git, so no committed copy exists and nothing on disk survived. **This is a
> rewritten version, reconstructed from a full read of the original earlier in the same session, with
> today's status changes folded in.** It is faithful in substance and structure. It is not the
> original bytes, and any wording I have not reproduced exactly is mine rather than the original
> author's. Cite it with that in mind. The five status claims updated today are marked ✅ / 🟨 with a
> date; everything else is as the original stood.

---

## 1. Who does what

| Role | Worker | Strength | Weakness to design around |
|---|---|---|---|
| **Orchestrator** | Claude (Cowork) | Reads the whole workspace, writes and tests code, judges, verifies | Expensive per token — do not spend it on volume |
| **Workhorse** | DeepSeek via API (`deepseek-v4-flash` default, `deepseek-v4-pro` for judgement) | Cheap bulk: extraction, classification, first-pass matching | Makes things up under pressure; no workspace context; data leaves the EU (see §3) |
| **Reviewer** | GPT (chat only, no API) | Independent second opinion, good at challenge and wording | Manual copy-paste by Jerome → small packs only, never a pipeline step |
| **Fetcher** | Plain Python (no LLM) | Downloads pages, respects robots, rate-limits | — an LLM is never needed to *fetch* |
| **Decider** | Jerome | Go/no-go on scraping, spend, external mail | Time — keep asks to one line |

**Routing rule in one line:** if it is repeated more than ~50 times and the output can be checked mechanically → DeepSeek. If being wrong is expensive or it needs more than one workspace file → Claude. If it needs an outside opinion → GPT pack.

**What does NOT go to DeepSeek even though it is cheap:** writing the core pipeline code (ledger schema, loaders, verifiers). It is small, and reviewing DeepSeek-drafted code costs Claude nearly as much as writing it. DeepSeek drafts code only for per-site parsers that are throwaway by nature.

---

## 2. The key trick — selectors first, DeepSeek as self-healing fallback

Sending every page to an LLM is slow and adds cost for no gain. Instead:

1. Per site, Claude writes a deterministic parser (CSS selector / JSON-LD / sitemap field).
2. When the parser returns nothing or fails its checks, the page text goes to **DeepSeek flash** with the fixed extraction prompt (§6.1).
3. If DeepSeek succeeds on the same site ≥ 3 times in a row where the parser failed, the site layout has changed → the healthcheck proposes a new selector (existing allowlist rules apply).

Result: DeepSeek volume stays small, and scrapers repair themselves instead of silently returning `no_results`.

---

## 3. Data boundary — what may go where

DeepSeek is a Chinese provider; assume anything sent is stored outside the EU. GPT follows the existing `AI_STACK.md` governance.

| Data | DeepSeek | GPT chat | Why |
|---|---|---|---|
| Public web page text, public product titles, public prices | ✅ | ✅ | Already public |
| Isuzu part numbers + descriptions alone | ✅ | ✅ | Public in every catalogue |
| Competitor/IAM numbers and crossref rows | ✅ | ✅ | Public or licensed-for-analysis (check Eucon terms before sending Eucon rows — **open**) |
| **The price list (our list/dealer prices)** | ❌ | ❌ | Never — AI_STACK governance |
| Billed revenue, quantities, sales to dealer, distributor names tied to numbers | ❌ | ❌ | Commercial |
| Special-price / "don't lose the deal" case details | ❌ | Summary only, anonymised | Dealer-confidential |
| Kosha, ITUK dispute, IML correspondence | ❌ | ❌ | Claude local only |
| API keys, `.env`, credentials | ❌ | ❌ | Never |

**Enforcement:** every DeepSeek batch script builds its payload from an explicit column allowlist (`ALLOWED_COLS`), never from `df.to_dict()` of a full file. Claude checks the allowlist before a script is first run.

---

## 4. Handoff mechanics

```
04_tools/delegation/
  deepseek/
    queue/     <task_id>.jsonl      one JSON object per item, allowlisted fields only
    out/       <task_id>.jsonl      DeepSeek answers, one per input line, same item_id
    rejects/   <task_id>.jsonl      rows that failed mechanical checks
    run_log.csv                     task_id, model, items, tokens_in, tokens_out, fails, started, ended
  gpt/
    <date>_<topic>_PACK.md          what Jerome pastes into GPT (≤ ~4 pages)
    <date>_<topic>_REPLY.md         Jerome pastes GPT's answer back here
```

- **DeepSeek runs on Jerome's Windows machine** (the key is in the local `.env`). Claude writes the batch script; a Windows scheduled task or Jerome runs it; Claude reads `out/` and verifies. Whether the Cowork sandbox can reach `api.deepseek.com` is **unverified** — do not assume it.
- **Never use `deepseek_agent.py --yolo`** for this programme. DeepSeek gets text in and JSON out, no shell and no file writes.
- **Every finished task** → one row on `DELEGATOR_BOARD.md`.

---

## 5. Acceptance rules (Claude never accepts DeepSeek output unchecked)

Mechanical checks, run by script on every row (cheap, catches most hallucinations):

1. **Verbatim check** — every extracted price string and every part number must appear as a substring of the source text sent. Fail → `rejects/`.
2. **Schema check** — valid JSON, required keys present, currency ∈ {GBP, EUR, NOK, SEK, DKK, ILS, PLN}, price > 0.
3. **Placeholder check** — reject known junk values (e.g. the 2.34 EUR / £2 "no result" placeholder).
4. **Plausibility** — price outside 0.05×–20× the median for that category → flag, not reject.

Then Claude samples: **5% of rows, minimum 20**, against the raw page. Acceptance bar: ≥ 95% correct on the sample. Below that → fix the prompt or parser, rerun; do not patch rows by hand.

GPT output is **advice**, never data. Nothing from a GPT reply enters a CSV without Claude verifying it against a source.

---

## 6. Standard prompts

### 6.1 DeepSeek flash — product page extraction
```
System: You extract structured data from one product web page. Output JSON only.
If a field is not stated on the page, use null. Never guess. Never convert currency.
Copy numbers exactly as written on the page.

Schema:
{"item_id": str, "title": str|null, "brand": str|null, "brand_part_no": str|null,
 "oem_refs": [str], "price_text": str|null, "price": float|null, "currency": str|null,
 "vat": "incl"|"excl"|"unknown", "stock": "in"|"out"|"unknown",
 "is_genuine": true|false|null, "pack_qty": int|null}

User: item_id=<id>  site=<domain>
<page text, HTML stripped, max ~6k tokens>
```

### 6.2 DeepSeek pro — crossref plausibility
```
System: You judge whether an aftermarket part can replace an Isuzu part, using only
the text given. Output JSON only: {"item_id", "verdict": "match"|"likely"|"doubt"|"no",
"reason": <one sentence quoting the evidence>}. If the evidence is thin, say "doubt".

User: Isuzu <part_no> "<description>" | Candidate <brand> <brand_part_no> "<title>" |
Source: <site>, listed OEM refs: <refs>
```
Give `max_tokens ≥ 2000` (pro reasons before answering; see `deepseek_readme.md`).

### 6.3 GPT pack header (every pack)
```
You are a second reviewer. Challenge, do not agree by default.
Context: <3 lines>. Question: <1 line>. Evidence: <table/excerpt>.
Answer: verdict first, then the 3 weakest points, then what you would check.
```

---

## 7. Task cards by phase

Status key: ⬜ not started · 🟨 in progress · ✅ accepted · ⛔ blocked on Jerome

### Phase 0 — no scraping (can start now)

| ID | Task | Worker | Input → Output | Accept when | Status |
|---|---|---|---|---|---|
| 0.1 | Design the price-observation ledger (one schema: part no, source, date, currency, price type, match method, vintage) | Claude | → `01_data/00_derived/price_observations.parquet` + schema doc | Loads all existing sources without loss | ✅ 2026-09-24 — `04_tools/price_ledger/build_price_ledger.py` |
| 0.2 | Load existing data into the ledger: KS, TMC, Eucon crossref (822 rows), Eucon 2023 survey (labelled 2023), Omega/Amayama probes if any | Claude (script) | existing CSV/XLSX → ledger | Row counts reconcile with sources | ✅ 2026-09-24 — 1,081 rows, 113 Isuzu nos (Eucon 821 of 822: 1 row had no price) |
| 0.3 | Parse KS `KS_AllProducts` strings into separate products (genuine vs aftermarket, OOS, kits) | DeepSeek flash | 300 rows → structured JSON | §5 checks + 20-row sample | 🟨 regex parses KS exactly (DeepSeek not needed here); used as DeepSeek golden test → Cursor C1, **PASS 2026-09-24: 63 of 64, one row lost to a token limit** |
| 0.4 | Retire Mekonomen, Auto365, Tranzparts from the weekly run and the healthcheck | Claude proposes, Jerome approves | change note | Jerome yes | ✅ 2026-09-24 — removed from the weekly run; the seven false Mekonomen prices blocked at source in both builders |
| 0.5 | GPT challenge of the whole redesign (is anything missing, what fails first) | GPT | `gpt/…_REDESIGN_PACK.md` → REPLY | Claude logs which points change the plan | 🟨 pack ready: `04_tools/delegation/gpt/2026-09-24_scraper_redesign_PACK.md`; **a second pack answering it now exists: `00_docs/agent/OPUS55_PROMPT2_AFTERMARKET_20260924.md`** |

### Phase 1 — catalogue reading (scrape go given 2026-09-24 — see header)

| ID | Task | Worker | Input → Output | Accept when | Status |
|---|---|---|---|---|---|
| 1.1 | KS sitemap → list of 6,453 Isuzu URLs, robots check | Python fetcher | sitemap → URL list | `check_scrape_consent.py` exit 0 | 🟨 unblocked 2026-09-24 — Cursor to run `check_scrape_consent.py` first |
| 1.2 | KS product pages at ≥ 2 s spacing; selector parser; failures → 6.1 | Python + DeepSeek flash (fallback) | pages → ledger rows with OEM refs | §5 + sample; OEM refs present on ≥ 50% of rows (**estimate**, revise after first 100) | 🟨 unblocked 2026-09-24 |
| 1.3 | Same pattern for Amayama, Omega, geparden.no, mekster.no | Claude writes parser; DeepSeek fallback | pages → ledger | §5 per site | 🟨 unblocked 2026-09-24 — **all six sites now in parallel (Jerome, chat, 2026-09-24), not sequenced.** Amayama parser already written and proven against a saved page; Omega/geparden/mekster.no are stubs that throw rather than return empty and need real parsers before any fetch |
| 1.4 | GPT review of each new site's terms of use (Jerome pastes terms text) | GPT | terms → verdict | Claude cross-checks against `legal_and_access.md` | ⬜ — **should run alongside 1.3/1.5, not after**, since fetching starts on the same go |
| 1.5 | tungen-bil.no (Isuzu dealer price list, searchable by part no, ex. mva) and autoline.dk (part and reference numbers with EUR prices) | Claude writes parser; DeepSeek fallback | pages → ledger | §5 per site; tungen-bil tagged `price_type = dealer`, autoline tagged `marketplace` — never mixed with aftermarket | 🟨 unblocked 2026-09-24 — in the same parallel batch as 1.3 |

### Phase 2 — price the aftermarket numbers

| ID | Task | Worker | Input → Output | Accept when | Status |
|---|---|---|---|---|---|
| 2.1 | Build crossref graph Isuzu no ↔ IAM no from 0.2 + 1.x | Claude (script) | ledger → `crossref_graph.parquet` | Every edge has a source and date | ✅ 2026-09-24 — `04_tools/aftermarket_intelligence/build_crossref_graph.py`. **7,443 edges, 647 Isuzu numbers, 3,023 competitor numbers, 0 refused for a missing source or date.** Outputs `crossref_edges.parquet`, `crossref_edges.csv`, `evidence_seed.csv`, `CROSSREF_GRAPH_REPORT.md`. **Caution recorded: `n_sources` counts distinct FILES, not independent verifications.** |
| 2.2 | Judge doubtful crossref edges (only those not confirmed by ≥ 2 sources) | DeepSeek pro (6.2) | edges → verdicts | Claude audits all "match" on top-100 revenue parts, sample on the rest | ⬜ — **now scoped: 2,446 competitor numbers rest on one source only; 463 have two or more; 168 have three or more** |
| 2.3 | Search allowed sources by IAM number; extract | Python + DeepSeek flash fallback | IAM nos → ledger | §5 | ⛔ — **seed now built: `evidence_seed.csv`, ranked by independent confirmation, not by our billing** |

### Phase 3 — non-scraping sources

| ID | Task | Worker | Input → Output | Accept when | Status |
|---|---|---|---|---|---|
| 3.1 | "Don't lose the deal" / special-price intake: one-line form (part no, competitor brand, quoted price, date, country) | Claude designs; GPT challenges wording | form + ledger feed | Jerome approves before anything goes to ITUK | ⛔ |
| 3.2 | Quote requests: TecAlliance (OE Parts Data + price layer), Eucon wider run | Claude drafts; Jerome sends | 2 draft mails | Jerome sends — Claude never sends | 🟨 drafted: `04_tools/delegation/drafts/OUTBOUND_DRAFTS_20260924.md` |
| 3.3 | eBay Browse API (official key) search by IAM and Isuzu numbers. **Priority: low, after 1.x and 2.x.** Main value = genuine Isuzu parts sold below our reference dealer price by parallel/grey sellers (leakage evidence), plus D-Max consumable street prices in UK/DE. Jerome creates the developer account (Claude may not); eBay API licence terms on storing data **to be checked** before building | Claude writes client; DeepSeek flash classifies listings (new/used/genuine/IAM) | API JSON → ledger | §5; used/grey never mixed with new | ⛔ |
| 3.4 | Tender award notices → unit or lot prices where published | DeepSeek flash extraction on tender text already collected | `tender_data.json` results → candidate rows | Claude sample; most will have no unit price — record that honestly | ⬜ |
| 3.5 | Ireland quote basket: quarterly request on ~30 parts **via Harris Group = our Irish distributor (sold-to 76, corrected 2026-09-24)**, benchmarking the independents (Colm Burns, D. Dennehy, H&I Parts, North Dublin Commercials — phone/form only). **Iceland excluded (Jerome 2026-09-24).** | Claude picks the basket and drafts the request; Jerome (or the Irish distributor) sends; Claude loads answers | basket list + draft → ledger rows `price_type = quote` | Jerome approves basket and wording; no request sent by Claude | 🟨 basket (30 parts, 13.8% of Ireland billed) + draft ready |
| 3.6 | Truck makers' own value lines (MAN LINE360, Mercedes-Benz TruckParts and the others in `all_makes_programmes.md`): for the ~30 highest-revenue maintenance/wear categories, where does each maker price its cheaper range against its own genuine and against aftermarket | Claude scopes; DeepSeek flash extracts from allowed catalogue pages; GPT challenges the read-out | pages/PDFs → ledger `price_type = oem_value_line` + one-page positioning note | Every price traced to a dated source; programmes with no public prices recorded as such, not guessed | ⬜ |

### Phase 5 — staying current (refresh by value + automatic triggers)

Refresh tiers are set by billed value, re-ranked monthly from sales data. The ranking stays local; only part numbers go into fetch queues.

| Tier | Parts | Refresh | Source of truth |
|---|---|---|---|
| **A** | Top ~300 by billed € + all maintenance-programme parts | Weekly | Observed prices |
| **B** | Next ~2,000 | Monthly (sitemap `lastmod` weekly: re-read only changed pages) | Observed prices |
| **C** | The rest | No scheduled scrape | Phase 4 estimate, re-fitted monthly |

| ID | Task | Worker | Input → Output | Accept when | Status |
|---|---|---|---|---|---|
| 5.1 | Tier builder: rank parts by billed € monthly, write `refresh_tiers.csv` (part no + tier only) | Claude (script) | sales data → tier list | Tier A covers ≥ the share of billed € stated in the file (measure, don't assume) | ✅ A 491 parts 61.6% · B 1,809 28.3% · C 14,211 10.1% |
| 5.2 | Scheduler: weekly/monthly queues per tier, sitemap `lastmod` diff for tier B, per-site rate limits | Claude (script) + Windows scheduled task | tier list → fetch queues | Dry run lists what would be fetched; no fetch without scrape go | ⛔ |
| 5.3 | Trigger — **new or superseded part number in the price list**: diff each new price-list file against the previous; new numbers and supersession pairs go to the next queue; old number's observations linked to the new one | Claude (script) | price list old vs new → trigger rows | Diff reconciles with price-list row counts | ✅ baseline stored; flood guard >2,000 new |
| 5.4 | Trigger — **new "don't lose the deal" / special-price case**: each intake row (3.1) queues a check on that part and its crossref family within 48 h | Claude (script) | intake → queue | Depends on 3.1 | ⛔ |
| 5.5 | Trigger — **price revision**: when a revision file lands, queue every revised part in tiers A+B for a fresh observation before/after, so the revision can be read against the market | Claude (script) | revision file → queue | Before/after pairs dated in the ledger | ✅ in `price_list_triggers.py` (A+B only) |
| 5.6 | Trigger log: every trigger writes one row (time, type, part no, queued for) to `04_tools/delegation/trigger_log.csv`; healthcheck reports triggers not served within their window | Claude | → log + healthcheck line | Healthcheck shows the count | 🟨 log live; healthcheck line → Cursor C4 |
| 5.7 | Weekly runner: tiers → triggers → ledger rebuild, as one bat, ordered after the Monday 07:00 refresh | Claude (script) + Windows scheduled task | → `run_price_ledger_weekly.bat` | Runs end to end, exits non-zero on any step failing | ✅ 2026-09-24 — registered `ISZE_PriceLedger_Weekly`, Mondays 09:00 |

### Phase 4 — estimates for the long tail

| ID | Task | Worker | Input → Output | Accept when | Status |
|---|---|---|---|---|---|
| 4.1 | Competitor-to-list ratio model by category × price class, with confidence band | Claude | ledger → estimate table | Back-test on held-out observed parts; report the error, do not hide it | 🟨 2026-09-24 — built and back-tested, `04_tools/aftermarket_intelligence/build_ratio_model.py`. **The back-test FAILS the card's intent: typical out-of-sample error is 11% on one price type and 29–36% on the other three; only 19% of predictions come from a category × price-class cell and 49% fall back to the whole price-type average.** Do not publish a category estimate from this. What it does support: the ratio between our list and a competitor's recommended retail is the only stable relationship in the data — ~11% typical error, 31% at the 9-in-10 line. |
| 4.2 | Adversarial review of the method | DeepSeek pro, then GPT | method note → critique | Claude records accepted/rejected points | ⬜ — **now has something to attack: the 4.1 back-test above** |
| 4.3 | Dashboard: observed vs estimated shown separately; KPI = % of billed € with an observation < 90 days | Claude | → existing dashboard | No estimate displayed as observed | ⬜ — **the reach table in `seed_reach_tierA.csv` is the first honest version of this: observed, rival-number-only, inside-our-own-brand, and nothing-to-search-with, kept apart** |

---

## 8. Cost and throughput (estimates — verify before scaling)

- DeepSeek pricing: **not stated here** — check the current rate on the DeepSeek platform page before any run above 1,000 items, and log actual tokens in `run_log.csv`.
- Size guide (**estimate**): a stripped product page ≈ 1.5–4k input tokens. With selectors first, DeepSeek should see only the failures — plan for 10–20% of pages, not 100%.
- Throughput is limited by polite fetching (≥ 2 s per request per site), not by DeepSeek. KS at 6,453 pages ≈ 3.5–4 h per full pass. Refresh follows the tiers in Phase 5: tier A weekly, tier B monthly plus changed pages weekly, tier C estimated only.
- Claude's cost is kept low by reading `run_log.csv`, `rejects/` counts and samples — never whole `out/` files.

**Measured 2026-09-24, first real DeepSeek run:** the KS golden task cost **15,171 input + 28,506 output tokens over about 3 minutes** for 64 items. That is the first real data point on this section.

---

## 9. Failure modes to watch

| Risk | Guard |
|---|---|
| DeepSeek invents a price or part number | §5 verbatim check — non-negotiable |
| Silent drift: DeepSeek model alias changes behaviour | Pin model name in `run_log.csv`; rerun a 20-item golden set monthly, compare |
| Internal data leaks into a payload | `ALLOWED_COLS` allowlist per script, Claude reviews before first run |
| GPT advice pasted in as fact | GPT replies live only in `gpt/*_REPLY.md`, never in data folders |
| Scraping a site that asks crawlers away | `check_scrape_consent.py` before every run; no bypassing Cloudflare/logins |
| Mixing price types (retail, trade, grey genuine, 2023 survey, used) | Ledger `price_type` + `vintage` are required fields; loaders refuse rows without them |
| Scope creep toward 15,000 parts | KPI is billed-€ coverage, not part count |

**Two additional failure modes learned on 2026-09-24, both worth a row because both happened:**

| Risk | Guard |
|---|---|
| **A column whose name says "price" is not a price.** The July file's `OE RRP` holds a price for our own part number that is neither our list nor an aftermarket price. Loading it as a competitor price would publish a wrong number with a clean audit trail. | Every loaded price column must be **named in the loader, with what it is**, and a column whose meaning is unknown is loaded as a match row with no price. |
| **One competitor number written two ways looks like two sources.** 174 numbers in the index have more than one spelling (`F 026 402 115` / `F026402115`). Counting confirmation on the written form understates agreement; counting on the loose form overstates it. | Keep both keys and state which one each count uses. `build_crossref_graph.py` does. |

---

## 10. Next step

Phase 0 and 5 are complete, and task 2.1 is now complete. The next work in order is **2.2** — judge the crossref edges that rest on a single source, which is 2,446 numbers and the largest block in the graph. **4.2** (adversarial review) has a real target: the failing 4.1 back-test. **3.4** needs no scrape and no licence.

Phases 1, 2.3, 3.1, 3.3 and 5.2 wait for the three open answers at the top. Nothing in this programme fetches anything until Jerome gives an explicit scrape go.
