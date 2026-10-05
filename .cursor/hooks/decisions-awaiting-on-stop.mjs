#!/usr/bin/env node
/**
 * stop hook: surface the decisions that are waiting on Jerome.
 *
 * Why this exists. Decisions raised in an agent chat die with the chat. The
 * workspace already solves that for one class of item - open source-data gaps,
 * in 01_data/00_derived/_data_integrity_open_issues.md, read by
 * 04_tools/data_gap_ping/Get-DataGapPing.ps1 - but nothing surfaces a decision
 * that is waiting on Jerome. This hook does.
 *
 * Design, and why each part is the way it is:
 *
 *   - It READS the register; it does not carry a copy of the decisions. The
 *     register is 01_data/90_INBOX/DECISIONS_AWAITING_JEROME_<date>.json, newest
 *     dated file wins, so a new register is picked up with no edit here.
 *   - It prints the BLOCKING items in full (id, question, what they block) and
 *     everything else as a count. A wall of twenty-three paragraphs would be
 *     ignored; three questions would not.
 *   - It is QUIET when nothing is open, and QUIET when the register cannot be
 *     read. A reminder that fires on a missing file is noise, and noise is what
 *     makes a reminder get ignored.
 *   - It fires ONCE per chat per register revision, not on every turn. The three
 *     existing stop hooks (db-sales-review, exec-aftersales, mypens) are all
 *     marker-gated so they stay silent on an ordinary turn; a fourth hook that
 *     spoke every turn would be the one that trains Jerome to ignore the other
 *     three. Re-announcement happens when the answer changes the register.
 *   - It never blocks, never writes to the register, and always exits 0.
 *   - loop_count is respected: a follow-up this hook caused must not cause
 *     another one.
 *
 * Output: {} (say nothing) or { followup_message }.
 */

import fs from 'node:fs'
import path from 'node:path'
import { fileURLToPath } from 'node:url'

const __dirname = path.dirname(fileURLToPath(import.meta.url))
const ROOT = path.resolve(__dirname, '..', '..')
const INBOX = path.join(ROOT, '01_data', '90_INBOX')
const STATE = path.join(__dirname, '.decisions-awaiting-announced.json')

const FILE_PREFIX = 'DECISIONS_AWAITING_JEROME_'
const STATUS_OPEN = 'open'

/** Blocking first, then high, then everything else. */
const URGENCY_RANK = { blocking: 0, high: 1, normal: 2 }

function readStdin() {
  try {
    return fs.readFileSync(0, 'utf8')
  } catch {
    return '{}'
  }
}

function emit(obj) {
  try {
    process.stdout.write(JSON.stringify(obj))
  } catch {
    /* ignore */
  }
}

/**
 * Newest dated register in the inbox. Returns null when there is none.
 * The date is in the filename, so a descending name sort is a date sort.
 * ISZE_DECISIONS_REGISTER overrides the file - used by the standalone test.
 */
function findRegister() {
  const override = process.env.ISZE_DECISIONS_REGISTER
  if (override) {
    try {
      const stat = fs.statSync(override)
      if (!stat.isFile()) return null
      return { path: override, name: path.basename(override), mtimeMs: stat.mtimeMs }
    } catch {
      return null
    }
  }
  let names = []
  try {
    names = fs.readdirSync(INBOX)
  } catch {
    return null
  }
  const candidates = names
    .filter((n) => n.startsWith(FILE_PREFIX) && n.endsWith('.json'))
    .sort()
    .reverse()
  if (candidates.length === 0) return null
  const full = path.join(INBOX, candidates[0])
  try {
    const stat = fs.statSync(full)
    if (!stat.isFile()) return null
    return { path: full, name: candidates[0], mtimeMs: stat.mtimeMs }
  } catch {
    return null
  }
}

function loadRegister(file) {
  try {
    let text = fs.readFileSync(file.path, 'utf8')
    // A register written by PowerShell Set-Content -Encoding UTF8 starts with a
    // byte-order mark, which JSON.parse rejects. Strip it rather than reporting
    // "unreadable" and going quiet on a register that is perfectly valid.
    if (text.charCodeAt(0) === 0xfeff) text = text.slice(1)
    const doc = JSON.parse(text)
    if (!doc || !Array.isArray(doc.decisions)) return null
    return doc
  } catch {
    return null
  }
}

function openDecisions(doc) {
  return doc.decisions
    .filter((d) => d && d.status === STATUS_OPEN && typeof d.id === 'string')
    .sort((a, b) => {
      const ra = URGENCY_RANK[a.urgency] ?? 3
      const rb = URGENCY_RANK[b.urgency] ?? 3
      if (ra !== rb) return ra - rb
      return a.id.localeCompare(b.id)
    })
}

/** One line, no trailing punctuation, safe length. */
function oneLine(text, max = 240) {
  if (typeof text !== 'string') return ''
  const t = text.replace(/\s+/g, ' ').trim()
  if (t.length <= max) return t
  const cut = t.slice(0, max)
  const sp = cut.lastIndexOf(' ')
  return (sp > 60 ? cut.slice(0, sp) : cut).replace(/[.,;:]$/, '') + '...'
}

function countBy(list, key) {
  const out = {}
  for (const d of list) {
    const k = d[key] || 'normal'
    out[k] = (out[k] || 0) + 1
  }
  return out
}

/** Signature of what is currently open, for the once-per-chat gate. */
function signatureOf(list, generated) {
  const ids = list.map((d) => `${d.id}:${d.urgency}`).sort().join(',')
  return `${generated || ''}|${ids}`
}

function buildMessage(doc, list, registerName) {
  const blocking = list.filter((d) => d.urgency === 'blocking')
  const high = list.filter((d) => d.urgency === 'high')
  const normal = list.filter((d) => d.urgency === 'normal')
  const safeTier = Array.isArray(doc.safe_tier) ? doc.safe_tier : []

  const total = list.length
  const lines = []

  lines.push(
    `STOP - ${total} decision${total === 1 ? '' : 's'} are waiting on Jerome and have not been answered.`,
  )
  lines.push(
    `Do not treat any of them as settled, and do not claim work in the areas they block. Put the ` +
      `blocking one${blocking.length === 1 ? '' : 's'} in front of him in this reply, in plain English, ` +
      `as a question he can answer yes or no.`,
  )
  lines.push('')

  if (blocking.length > 0) {
    lines.push(`BLOCKING (${blocking.length}) - work is stopped:`)
    for (const d of blocking) {
      lines.push(`  ${d.id} - ${oneLine(d.title, 120)}`)
      lines.push(`      Question: ${oneLine(d.question)}`)
      if (d.recommendation) lines.push(`      View: ${oneLine(d.recommendation)}`)
      if (d.blocks) lines.push(`      Blocks: ${oneLine(d.blocks, 200)}`)
      lines.push('')
    }
  } else {
    lines.push('Nothing is marked blocking, so nothing is stopped - but these are unanswered.')
    lines.push('')
  }

  const rest = []
  if (high.length > 0) rest.push(`${high.length} high (${high.map((d) => d.id).join(', ')})`)
  if (normal.length > 0) rest.push(`${normal.length} normal`)
  if (rest.length > 0) {
    // With no blocking items the headline already said "unanswered", so do not
    // repeat the same count twice in a row.
    lines.push(
      blocking.length > 0
        ? `Also open, not blocking: ${rest.join('; ')}.`
        : `Open: ${rest.join('; ')}.`,
    )
  }
  if (safeTier.length > 0) {
    lines.push(
      `Ready with no decision: ${safeTier.length} safe-tier repairs (${safeTier
        .map((s) => s.id)
        .join(', ')}) - wording and pointers only, no number changes.`,
    )
  }

  lines.push('')
  lines.push(`Register (read-only, the single source): ${path.join(INBOX, registerName)}`)
  lines.push(
    `Readable version for Jerome: ${path.join(INBOX, registerName.replace(/\.json$/, '.md'))}`,
  )
  lines.push(
    'A decision only counts once it is in 00_docs\\ISZE_ROADMAP.md, in DECISIONS.md as a new dated ' +
      'entry, and as status: decided in the file that was waiting.',
  )

  return lines.join('\n')
}

// --- main ------------------------------------------------------------------

const raw = readStdin()
let input = {}
try {
  input = JSON.parse(raw || '{}')
} catch {
  input = {}
}

// A follow-up this hook caused must not cause another one. Cursor reports the
// count as loop_count; the Codex/Claude dialect reports a boolean instead.
if (Number(input.loop_count ?? 0) >= 1 || input.stop_hook_active === true) {
  emit({})
  process.exit(0)
}
if (input.status && input.status !== 'completed') {
  emit({})
  process.exit(0)
}

const file = findRegister()
if (!file) {
  emit({})
  process.exit(0)
}

const doc = loadRegister(file)
if (!doc) {
  emit({})
  process.exit(0)
}

const list = openDecisions(doc)
if (list.length === 0) {
  emit({})
  process.exit(0)
}

const signature = signatureOf(list, doc.generated)

// Already announced this exact set in this chat - stay quiet.
try {
  const prior = JSON.parse(fs.readFileSync(STATE, 'utf8'))
  if (prior && prior.signature === signature) {
    emit({})
    process.exit(0)
  }
} catch {
  /* no state yet - first announcement */
}

try {
  fs.writeFileSync(
    STATE,
    JSON.stringify({ signature, announced_at: new Date().toISOString(), register: file.name }, null, 2),
    'utf8',
  )
} catch {
  // If the state cannot be written we would nag every turn, which is the one
  // failure mode this hook is meant to avoid. Stay silent instead.
  emit({})
  process.exit(0)
}

emit({ followup_message: buildMessage(doc, list, file.name) })
process.exit(0)
