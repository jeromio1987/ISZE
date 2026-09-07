# IUK — SMMT / DVLA LCV data ask (Mode B chase sheet)

**Status:** Monday-ready ask sheet · draft only · **do not send** this weekend  
**Written:** 2026-09-05  
**Audience:** Jerome (chase Aaron / John at IUK, or route via Koen)  
**Not:** Mode A email copy · not Outlook send · independent of EQ-HIT browser work

---

## 1. Purpose

Unlock **GPS/PMS V2 Opt2** for **IUK** (generation-weighted LCV demand) and lift IUK UIO accuracy to **rank A**.

| Need | Why |
|------|-----|
| Subtype counts: **Trooper / D-Max RT / D-Max RG** | Opt2 = generation split; without counts Opt2 stays **off** (do not invent) |
| Authority / SMMT-backed car park | Rank **A** = gov/authority regs **+** subtype counts ([`GPS_PMS_V2_CONCEPT.md`](GPS_PMS_V2_CONCEPT.md)) |
| Vintage × model stock | Also feeds Opt3 / 10y cohort work later |

**Already locked (do not re-ask):** IUK LCV headcount CY2026F = **44,926** (row 25, V20 Decision 30 Jul 2026). This chase is for **generation / model cut**, not the headline parc.

**V20 Still open (source of need):** [`06_uio/_CURRENT/V20_SPEC.md`](../../06_uio/_CURRENT/V20_SPEC.md) § Still open — *IUK LCV generation / authority car park (chase for V20 + GPS/PMS V2 Opt2)*. Until this lands, IUK stays **Opt1-only** (flat LCV + mileage).

**SSOT map:** [`GPS_PMS_V2_LCV_SUBTYPE_SSOT.md`](GPS_PMS_V2_LCV_SUBTYPE_SSOT.md) — IUK row = need / Opt2 off.

---

## 2. What to ask IUK for

Prefer one extract they already pull from **SMMT** (or DVLA car-park feed). Ideal grain = **stock / car park by vintage + model**, not only annual new regs. If they can give **both**, take both.

### Minimum usable file (fields)

| Field | Notes |
|-------|--------|
| **Registration year** (or first-reg year) | Vintage for survival / Opt3 later |
| **Model / description** | As SMMT labels it (D-Max, Trooper, Pickup, etc.) |
| **Generation or chassis cues** (if available) | RT / RG / UBS / chassis code / model-year band — whatever they have |
| **Unit count** | Vehicles in stock (preferred) **or** new regs that year |
| **As-of date** | Snapshot date for car park; for new regs: calendar year covered |
| **Scope note** | Confirm LCV / pickup only (not ITUK CV mix) |

### Nice-to-have

- Separate columns: **car park stock** vs **new registrations** for the same year
- Engine / body if trivial to include (not required for Opt2 enable)
- Any internal IUK mapping table Trooper vs RT vs RG they already use

### Generation labels we will map to (Jerome SSOT)

| Jerome label | Cues (working) |
|--------------|----------------|
| Trooper | UBS / TROOPER |
| D-Max RT | RT56 / RT88 / TFS87-class |
| D-Max RG | RG / RG21 / TFR86-class |

They do **not** need to ship our labels. Raw SMMT model + year (or chassis) is enough; we map.

### Formats

Excel / CSV fine. One sheet or two (stock vs new regs). No need for Mode A packaging.

---

## 3. Ease (how hard for IUK)

**Verdict: medium-easy** if IUK already sits on an SMMT subscription / feed — same family of data **ITUK CV already uses via Duncan** (UIO Sheet 4 Section A: SMMT actuals for trucks).

| Friction | Reality |
|----------|---------|
| Owner / subscription | SMMT is paid / member data — someone at IUK (or ITUK) must own the pull |
| LCV vs CV cut | ITUK path is **CV**; this ask is **IUK LCV / pickup**. Wrong cut = useless for Opt2 |
| Generation coding | SMMT may give model + year, not “RT/RG”; we accept that and code generation ourselves |
| Precedent | Ireland SIMI / Portugal Matriculas already prove national extracts work; UK is the gap |

**Not hard:** inventing a new survey. **Hard if:** no SMMT LCV licence, or only a one-line “UK pickup total” with no vintage/model.

---

## 4. Accuracy

| Claim | Caveat |
|-------|--------|
| **UK SMMT ≈ gov-grade for registration counts** | Good enough for authority rank when paired with subtype (or mappable model/year) |
| Counts ≠ Jerome labels | Must **map** SMMT descriptions → Trooper / RT / RG; ambiguity years need a documented rule |
| Surviving UIO still needs scrap / survival | New regs alone do not equal car park; stock-by-vintage is stronger. V20 already uses pickup survival (~12.3 %) on row 25 |
| Timing lag | SMMT / DVLA snapshots lag; always keep **as-of date** on the file |
| Rank A bar | Gov/authority regs **+** subtype counts — total LCV only = rank **B**, Opt2 still off |

---

## 5. Acceptance

### Good enough for Opt2 (enable)

- [ ] Counts (or clear shares) that resolve to **Trooper + D-Max RT + D-Max RG** for IUK LCV  
- [ ] Either stock-by-vintage+model **or** new regs by year+model with enough history that we can apply survival consistently with V20  
- [ ] **As-of date** + LCV/pickup scope confirmed  
- [ ] Sum of subtypes reconciles to ~IUK LCV total within a stated tolerance (or unexplained remainder labelled **unknown**, not forced into a generation)

→ Then: Opt2 **on** for IUK; UIO accuracy can move toward **rank A**.

### Still Opt1 only (not enough)

- Single **total LCV / pickup** number (even if SMMT) → rank **B** at best; Opt2 **off**
- Model mix without vintage and no stock → usable as a weak share guess only if Jerome explicitly allows; default = **do not invent** Opt2
- CV-only SMMT dump (ITUK path) → wrong DB

### Out of scope for this ask

- Re-locking CY2026F 44,926  
- EQ-HIT PN fitment (parallel track; does not replace subtype UIO)  
- Mode A client narrative

---

## 6. Do not (this weekend)

- **Do not send** chase mail Saturday/Sunday — this file is the Monday-ready sheet only  
- **Do not** draft/send Outlook from this thread unless Jerome explicitly asks later  
- **Do not** wait on EQ-HIT before using this ask  
- **Do not** invent Trooper/RT/RG shares from IMIT aggregate while waiting  

**When Jerome is ready:** contact **Aaron / John** (IUK) or ask **Koen** to route — paste §2 fields + §5 acceptance. Tone = short internal ask, not a formal ISZE letter.

---

## Pointers

| Doc | Role |
|-----|------|
| [`V20_SPEC.md`](../../06_uio/_CURRENT/V20_SPEC.md) § Still open | Locked need statement |
| [`GPS_PMS_V2_LCV_SUBTYPE_SSOT.md`](GPS_PMS_V2_LCV_SUBTYPE_SSOT.md) | IUK row / network map |
| [`GPS_PMS_V2_CONCEPT.md`](GPS_PMS_V2_CONCEPT.md) | Opt1/2/3 + rank A–D |
| UIO Sheet 4 (ITUK) | Precedent: SMMT already in UK CV model via Duncan |
