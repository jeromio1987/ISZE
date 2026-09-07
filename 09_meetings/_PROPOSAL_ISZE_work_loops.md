# ISZE work loops — proposal + build status

**Saved:** 2026-08-31  
**Constraint:** Draft by default. **Send** only when Jerome’s **current** message says send/verstuur — then **verify Sent Items** (or report Outbox stuck).

---

## Verdict

Agents *produce*. Loops *close*. Outbox stuck mail was the smoking gun.

---

## Loop pattern

`TRIGGER → ACT → VERIFY (machine) → HAND OFF / FIX → MEMORY`  
Verify fail → **HOLD**, never claim done.

---

## Five loops

### 1. Mail delivery loop — **BUILT 2026-08-31**
- Skill: `.cursor/skills/isze-mail-delivery/`
- Rules: `isze-mail-delivery-loop.mdc` + updated `isze-no-ship-without-ok.mdc` §1
- Script: `scripts/outlook_delivery.py` (`draft` / `send` / `verify` / `outbox` / `status`)
- Ledger: `09_meetings/_mail_delivery_ledger.jsonl`

### 2. Truth gate loop — not built
### 3. Story compiler (A-lite) — not built
### 4. Cadence loop — not built
### 5. Learning loop — not built

---

## When Jerome says “send”

1. Treat as authorization for **that** mail only.  
2. `outlook_delivery.py send --i-was-told-to-send ...`  
3. `verify` → paste STATUS=SENT proof (or OUTBOX_STUCK).  
4. Never claim delivered without STATUS=SENT.

---

## Related

- Aftermarket BI tick: `02_dashboards/_build/LOOP_AFTERMARKET_BI.md`  
- Dive-deeper: `C:\Users\jerom\.cursor\rules\dive-deeper-by-default.mdc`
