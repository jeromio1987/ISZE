#!/usr/bin/env node
/**
 * afterShellExecution: when db_sales_review build_* runs, remind agent to run QA gate
 * before claiming the deck done. Writes a marker for the stop hook.
 */
import fs from 'node:fs'
import path from 'node:path'
import { fileURLToPath } from 'node:url'

const __dirname = path.dirname(fileURLToPath(import.meta.url))
const MARKER = path.join(__dirname, '.db-sales-review-pending-qa.json')

function readStdin() {
  try {
    return fs.readFileSync(0, 'utf8')
  } catch {
    return '{}'
  }
}

function emit(obj) {
  process.stdout.write(JSON.stringify(obj))
}

const raw = readStdin()
let payload = {}
try {
  payload = JSON.parse(raw || '{}')
} catch {
  payload = {}
}

const cmd = String(payload.command || payload.cmd || '')
const hit =
  /db_sales_review|build_full_deck\.py|build_deck\.py|build_parts_analysis\.py/i.test(cmd)

if (!hit) {
  emit({})
  process.exit(0)
}

const dbMatch = cmd.match(/--db\s+(\w+)/i)
const db = dbMatch ? dbMatch[1].toUpperCase() : null
const isFullDeck = /build_full_deck\.py|build_deck\.py/i.test(cmd)
const isParts = /build_parts_analysis\.py/i.test(cmd)

try {
  fs.writeFileSync(
    MARKER,
    JSON.stringify(
      {
        at: new Date().toISOString(),
        command: cmd.slice(0, 500),
        db,
        needs_qa: true,
        after_parts: isParts,
        after_deck: isFullDeck,
      },
      null,
      2,
    ),
    'utf8',
  )
} catch {
  /* ignore */
}

let followup =
  'DB Sales Review build detected. Before claiming done: run ' +
  '`python .cursor/skills/isze-db-sales-review/scripts/qa_deck_gate.py --db <KEY>` ' +
  'and follow `.cursor/skills/isze-db-sales-review/SKILL.md` (sold_to, PBI align, SaTy Mode A, no Best>100%).'

if (isFullDeck && db) {
  followup =
    `Deck build for ${db} finished. You MUST run qa_deck_gate.py --db ${db} now. ` +
    'If gate fails, do not tell Jerome the pack is ready. Re-run build_parts_analysis after any loader fix before rebuild.'
} else if (isParts && db) {
  followup =
    `Parts analysis for ${db} finished. Run qa_deck_gate.py --db ${db} before build_full_deck. ` +
    'Never rebuild PPTX on a failing gate.'
}

emit({ followup_message: followup })
process.exit(0)
