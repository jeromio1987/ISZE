#!/usr/bin/env node
/**
 * Cursor week digest -> ISZE\05_memory\briefs\
 *
 * Cursor keeps chat transcripts locally per workspace under
 *   %USERPROFILE%\.cursor\projects\<projectId>\agent-transcripts\<uuid>\<uuid>.jsonl
 * Claude Desktop's scheduled jobs read ISZE\05_memory\briefs\, so without this
 * bridge a week of Cursor work is invisible to the weekly review.
 *
 * Usage:
 *   node cursor_week_digest.mjs [--days 7] [--out <path>] [--stdout]
 */

import fs from 'node:fs'
import os from 'node:os'
import path from 'node:path'

const DEFAULT_DAYS = 7
const BRIEFS_DIR = path.join(
  os.homedir(),
  'Desktop',
  'claude',
  'ISZE',
  '05_memory',
  'briefs',
)
const PROJECTS_DIR = path.join(os.homedir(), '.cursor', 'projects')
const MAX_TOPIC_CHARS = 220

function parseArgs(argv) {
  const args = { days: DEFAULT_DAYS, out: null, stdout: false }
  for (let i = 0; i < argv.length; i++) {
    if (argv[i] === '--days') args.days = Number(argv[++i])
    else if (argv[i] === '--out') args.out = argv[++i]
    else if (argv[i] === '--stdout') args.stdout = true
  }
  if (!Number.isFinite(args.days) || args.days <= 0) args.days = DEFAULT_DAYS
  return args
}

function isoWeek(date) {
  const d = new Date(Date.UTC(date.getFullYear(), date.getMonth(), date.getDate()))
  const day = d.getUTCDay() || 7
  d.setUTCDate(d.getUTCDate() + 4 - day)
  const yearStart = new Date(Date.UTC(d.getUTCFullYear(), 0, 1))
  const week = Math.ceil(((d - yearStart) / 86400000 + 1) / 7)
  return { year: d.getUTCFullYear(), week }
}

/**
 * Workspace slugs lose the distinction between a path separator and a literal
 * hyphen (mypens-mobile becomes ...-mypens-mypens-mobile), so rebuild the path
 * by extending each segment with hyphens until it exists on disk.
 */
function resolveWorkspace(slug) {
  const m = /^([a-zA-Z])-(.+)$/.exec(slug)
  if (!m) return null
  let current = `${m[1].toUpperCase()}:\\`
  const parts = m[2].split('-')
  let i = 0
  while (i < parts.length) {
    let acc = parts[i]
    let candidate = path.join(current, acc)
    let j = i + 1
    while (!fs.existsSync(candidate) && j < parts.length) {
      acc = `${acc}-${parts[j]}`
      candidate = path.join(current, acc)
      j++
    }
    if (!fs.existsSync(candidate)) return null
    current = candidate
    i = j
  }
  return current
}

function extractText(entry) {
  const content = entry?.message?.content
  if (typeof content === 'string') return content
  if (!Array.isArray(content)) return ''
  return content
    .filter((c) => c?.type === 'text' && typeof c.text === 'string')
    .map((c) => c.text)
    .join('\n')
}

function firstUserQuery(text) {
  const tagged = /<user_query>\s*([\s\S]*?)\s*<\/user_query>/.exec(text)
  const raw = (tagged ? tagged[1] : text)
    .replace(/<[^>]+>/g, ' ')
    .replace(/\s+/g, ' ')
    .trim()
  if (!raw) return null
  return raw.length > MAX_TOPIC_CHARS ? `${raw.slice(0, MAX_TOPIC_CHARS - 1)}…` : raw
}

function readSession(file) {
  let lines
  try {
    lines = fs.readFileSync(file, 'utf8').split(/\r?\n/)
  } catch {
    return null
  }

  let topic = null
  let userTurns = 0
  let assistantTurns = 0

  for (const line of lines) {
    if (!line.trim()) continue
    let entry
    try {
      entry = JSON.parse(line)
    } catch {
      continue
    }
    if (entry.role === 'user') {
      userTurns++
      if (!topic) topic = firstUserQuery(extractText(entry))
    } else if (entry.role === 'assistant') {
      assistantTurns++
    }
  }

  if (!topic && userTurns === 0) return null
  return { topic: topic ?? '(geen leesbare openingsvraag)', userTurns, assistantTurns }
}

function collectSessions(cutoff) {
  if (!fs.existsSync(PROJECTS_DIR)) return []
  const sessions = []

  for (const projectId of fs.readdirSync(PROJECTS_DIR)) {
    const transcripts = path.join(PROJECTS_DIR, projectId, 'agent-transcripts')
    if (!fs.existsSync(transcripts)) continue

    for (const sessionId of fs.readdirSync(transcripts)) {
      const file = path.join(transcripts, sessionId, `${sessionId}.jsonl`)
      let stat
      try {
        stat = fs.statSync(file)
      } catch {
        continue
      }
      if (stat.mtime < cutoff) continue

      const parsed = readSession(file)
      if (!parsed) continue
      sessions.push({ projectId, sessionId, modified: stat.mtime, ...parsed })
    }
  }

  return sessions.sort((a, b) => b.modified - a.modified)
}

function groupByProject(sessions) {
  const groups = new Map()
  for (const s of sessions) {
    if (!groups.has(s.projectId)) groups.set(s.projectId, [])
    groups.get(s.projectId).push(s)
  }
  return [...groups.entries()].sort((a, b) => b[1].length - a[1].length)
}

function plural(n, one, many) {
  return `${n} ${n === 1 ? one : many}`
}

function render(sessions, days, generatedAt) {
  const { year, week } = isoWeek(generatedAt)
  const groups = groupByProject(sessions)
  const totalTurns = sessions.reduce((n, s) => n + s.userTurns, 0)
  const dateOnly = (d) => d.toISOString().slice(0, 10)

  const lines = [
    `# Cursor-week digest — ${year}-W${String(week).padStart(2, '0')}`,
    '',
    `Gegenereerd: ${generatedAt.toISOString()}`,
    `Venster: laatste ${days} dagen · ${plural(sessions.length, 'sessie', 'sessies')} · ${plural(totalTurns, 'gebruikersvraag', 'gebruikersvragen')}`,
    '',
    'Bron: lokale Cursor-transcripts (`~/.cursor/projects/*/agent-transcripts/`).',
    'Dit bestand bestaat zodat de wekelijkse Claude-review het Cursor-werk meeneemt.',
    '',
  ]

  if (sessions.length === 0) {
    lines.push(`Geen Cursor-sessies in de laatste ${days} dagen.`, '')
    return lines.join('\n')
  }

  for (const [projectId, group] of groups) {
    const resolved = resolveWorkspace(projectId)
    const heading = resolved ?? `onbekende workspace (${projectId})`
    lines.push(`## ${heading}`, '')
    lines.push(`${plural(group.length, 'sessie', 'sessies')}.`, '')
    for (const s of group) {
      lines.push(
        `- **${dateOnly(s.modified)}** (${plural(s.userTurns, 'vraag', 'vragen')}) — ${s.topic}`,
      )
    }
    lines.push('')
  }

  lines.push(
    '## Volgende stap',
    '',
    'Lees dit naast de deterministische briefs voordat je conclusies trekt over de week.',
    'Onderwerpen zijn de openingsvraag per sessie, niet de uitkomst — die staat in de projectmemory.',
    '',
  )

  return lines.join('\n')
}

function main() {
  const args = parseArgs(process.argv.slice(2))
  const generatedAt = new Date()
  const cutoff = new Date(generatedAt.getTime() - args.days * 86400000)
  const sessions = collectSessions(cutoff)
  const markdown = render(sessions, args.days, generatedAt)

  if (args.stdout) {
    process.stdout.write(markdown)
    return
  }

  const { year, week } = isoWeek(generatedAt)
  const out =
    args.out ??
    path.join(BRIEFS_DIR, `cursor_week_${year}-W${String(week).padStart(2, '0')}.md`)

  fs.mkdirSync(path.dirname(out), { recursive: true })
  fs.writeFileSync(out, markdown, 'utf8')
  console.log(`Wrote ${out}`)
  console.log(`Sessions: ${sessions.length} (last ${args.days} days)`)
}

main()
