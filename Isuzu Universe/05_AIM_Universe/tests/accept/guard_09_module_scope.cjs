#!/usr/bin/env node
'use strict';
/* ===========================================================================
   GUARD-09 - the acceptance suite must not quietly load a module the product
   does not ship.

   WHY THIS EXISTS
   ---------------
   This project built several modules twice for one concern, and then pointed
   tests at the copy that is not assembled. tools/build.py lists those copies in
   UNWIRED_MODULES and refuses to assemble anything that reads one - but that
   guard only protects the ARTIFACT. It says nothing about the tests, and a test
   addressed to an unshipped copy is worse than no test: it reports on a module
   nobody receives, while looking exactly like evidence about the product.

   The measured instance that produced this guard (2026-09-22):
     SAFE-05 S09b and S10c asserted against src/output/recipients.js, which
     tools/build.py lists as a "duplicate export builder". The module that
     decides what a distributor receives is src/data/export.js. Both checks now
     ask the shipped module; see accept_05_08_safety.cjs S09b and S10c.

   WHAT IT ASSERTS
   ---------------
   G1  An acceptance check may not load a module that appears in UNWIRED_MODULES
       unless that check carries an explicit declaration for it, in the file,
       naming the module and saying why it is being asked:

           // RETIRED-MODULE-USE: src/output/recipients.js - <reason>

       The declaration is the point. A retired module may still be worth asking
       about - the permission table and the identity stand-in have no shipped
       counterpart - but the reason has to be written down where the next
       reviewer reads it, instead of the misdirection happening silently.

   G2  Every declaration must name a module the check actually loads, and must
       carry a reason. A declaration that outlives the load it described is a
       stale claim, and a claim is not evidence.

   HOW IT MEASURES "LOAD"
   ----------------------
   Not by searching the file for a module name. A name appears in comments, in
   prose and in the recorded comparisons, so a text search reports misdirection
   that is not there and would be tuned until it stopped reporting the
   misdirection that is. Instead it reads `H.PATHS` from the harness the checks
   actually use, then looks at which of those entries each check names. The
   harness is the one door source modules are loaded through, so a name in that
   map that a check uses is a real load.

   The module lists are read from tools/build.py rather than typed here, so this
   guard cannot fall out of step with the build. It reads them the same way
   tools/orphan_audit.py does.

   WHAT IT DOES NOT CLAIM
   ----------------------
   This is a statement about which files the acceptance suite reads. It is not a
   statement that any behaviour is safe, and it confers nothing. It does not
   read or judge the product.
   =========================================================================== */
const H = require('./lib/harness.cjs');
const fs = require('node:fs');
const path = require('node:path');

const ACCEPT = path.join(H.ROOT, 'tests', 'accept');
const BUILD_PY = path.join(H.ROOT, 'tools', 'build.py');

/* ---------------------------------------------------- the build's two lists -- */

/* Read from build.py, not hardcoded. The ASSEMBLED list is the block before
   UNWIRED_MODULES; the retired list is the block that follows. Reading the
   whole file with one pattern puts every module in both lists, which makes the
   guard say nothing - tools/orphan_audit.py reads it that way, and that is fine
   for finding orphans because the union is what it wants, but it is not fine
   for a check that has to tell the two apart. */
function readBuildLists() {
  if (!fs.existsSync(BUILD_PY)) {
    throw new Error('tools/build.py is missing, so the shipped and retired lists cannot be read: ' + BUILD_PY);
  }
  const text = fs.readFileSync(BUILD_PY, 'utf8');
  const unwiredAt = text.indexOf('UNWIRED_MODULES');
  const bannedAt = text.indexOf('BANNED_IN_OUTPUT', unwiredAt);
  if (unwiredAt < 0) throw new Error('tools/build.py has no UNWIRED_MODULES block to read');

  const pair = /\("(src\/[^"]+)",\s*"[^"]+"\)/g;
  const collect = (slice) => [...slice.matchAll(pair)].map(m => m[1]);

  const assembled = collect(text.slice(0, unwiredAt));
  const retired = collect(text.slice(unwiredAt, bannedAt < 0 ? text.length : bannedAt));
  return { assembled, retired, block: text.slice(unwiredAt, bannedAt < 0 ? text.length : bannedAt) };
}

let lists;
try {
  lists = readBuildLists();
} catch (e) {
  const failed = H.makeRun('GUARD-09', 'The acceptance suite only loads modules the build assembles');
  H.test(failed, 'G00', 'The build module lists are readable', () => { throw e; });
  const s = H.write(failed, 'guard_09_module_scope.json');
  process.exit(s.fail ? 1 : 0);
}

const RETIRED = new Set(lists.retired);
const ASSEMBLED = new Set(lists.assembled);

const run = H.makeRun('GUARD-09',
  'The acceptance suite only loads source modules the build assembles',
  ['Reads the module lists from tools/build.py rather than hardcoding them.',
   'Measures loads through the harness PATHS map, not by searching file text.',
   'A retired module may be loaded only with an explicit declaration in the file.']);
run.tested_files = H.pin([BUILD_PY, path.join(ACCEPT, 'lib', 'harness.cjs')]);
run.build_lists = {
  source: 'tools/build.py',
  assembled_count: lists.assembled.length,
  retired_count: lists.retired.length,
  assembled: lists.assembled,
  retired: lists.retired,
  note: 'read as two separate blocks: the assembled list precedes UNWIRED_MODULES, the retired list follows it'
};

/* ------------------------------------------------------- what each check loads -- */

/* Harness PATHS entries that point into src/. These are the loadable source
   modules; the frozen file, the dist artifact and the fixtures are not source. */
const SRC_PATHS = Object.entries(H.PATHS)
  .map(([key, abs]) => ({ key, abs, rel: path.relative(H.ROOT, abs).replace(/\\/g, '/') }))
  .filter(p => p.rel.startsWith('src/'));

const CHECKS = fs.readdirSync(ACCEPT)
  .filter(f => /^accept_\d+.*\.cjs$/.test(f))
  .sort();

const DECLARATION = /^\s*\/\/\s*RETIRED-MODULE-USE:\s*(src\/\S+?)\s*(?:[-:–]\s*(.*))?$/gm;

const loaded = [];          /* every retired load, and whether it was declared  */
const undeclared = [];
const declarations = [];    /* every declaration, and whether it describes a load */
const declaredButNotLoaded = [];
const missingReason = [];

for (const file of CHECKS) {
  const text = fs.readFileSync(path.join(ACCEPT, file), 'utf8');

  /* Which harness paths does this check name? */
  const usedKeys = new Set();
  for (const p of SRC_PATHS) {
    if (new RegExp(`H\\.PATHS\\.${p.key}\\b`).test(text)) usedKeys.add(p.key);
  }
  const usedRetired = SRC_PATHS.filter(p => usedKeys.has(p.key) && RETIRED.has(p.rel));
  const usedAssembled = SRC_PATHS.filter(p => usedKeys.has(p.key) && ASSEMBLED.has(p.rel));

  /* Its declarations. */
  const declared = {};
  for (const m of text.matchAll(DECLARATION)) {
    const rel = m[1].trim();
    const reason = (m[2] || '').trim();
    declared[rel] = reason;
    declarations.push({ file, module: rel, reason });
    if (!reason) missingReason.push({ file, module: rel });
    if (!usedRetired.some(p => p.rel === rel)) {
      declaredButNotLoaded.push({ file, module: rel, used_retired: usedRetired.map(p => p.rel) });
    }
  }

  for (const p of usedRetired) {
    const entry = {
      file, module: p.rel, harness_key: p.key,
      build_reason: (lists.block.match(new RegExp(`\\("${p.rel.replace(/[/.]/g, m => '\\' + m)}",\\s*"([^"]+)"\\)`)) || [])[1] || null,
      declared: Object.prototype.hasOwnProperty.call(declared, p.rel),
      declared_reason: declared[p.rel] || null,
      also_loads_assembled: usedAssembled.map(a => a.rel)
    };
    loaded.push(entry);
    if (!entry.declared) undeclared.push(entry);
  }
}

run.loads = {
  checks_scanned: CHECKS,
  harness_src_paths: SRC_PATHS.map(p => ({ key: p.key, module: p.rel,
    status: RETIRED.has(p.rel) ? 'RETIRED (UNWIRED_MODULES)'
      : ASSEMBLED.has(p.rel) ? 'assembled' : 'neither list' })),
  retired_loads: loaded,
  declarations
};

/* --------------------------------------------------------- which paths are which */

H.test(run, 'G01', 'Every harness path into src/ is classified by the build, so no module is unaccounted for',
  () => {
    /* The harness map is what the checks load through. If it names a module the
       build's two lists do not mention, nothing states whether that module ships,
       which is the orphan case tools/orphan_audit.py reports for the tree as a
       whole. Recorded here so a new harness path cannot appear silently. */
    const unclassified = SRC_PATHS.filter(p => !RETIRED.has(p.rel) && !ASSEMBLED.has(p.rel));
    run.unclassified_harness_paths = unclassified.map(p => p.rel);
    H.eq(unclassified.length, 0,
      'the harness loads source modules that appear in neither the assembled nor the retired list in '
      + 'tools/build.py, so nothing states whether they ship: ' + JSON.stringify(unclassified.map(p => p.rel))
      + '. Run `python tools/orphan_audit.py` for the same question about the whole tree.');
    return `${SRC_PATHS.length} harness source path(s), all classified: `
      + `${SRC_PATHS.filter(p => ASSEMBLED.has(p.rel)).length} assembled, `
      + `${SRC_PATHS.filter(p => RETIRED.has(p.rel)).length} retired`;
  });

H.test(run, 'G02', 'No acceptance check loads an unshipped module without declaring it in the file',
  () => {
    H.eq(undeclared.length, 0,
      'these acceptance checks load a module that tools/build.py does NOT assemble, and say nothing about '
      + 'it: ' + JSON.stringify(undeclared.map(u => ({
        check: u.file, module: u.module,
        build_says: u.build_reason, also_loads: u.also_loads_assembled })))
      + '. A check addressed to an unshipped copy reports on code nobody receives. Either point the check '
      + 'at the assembled module, or declare the use in the check file: '
      + '"// RETIRED-MODULE-USE: ' + (undeclared[0] ? undeclared[0].module : 'src/...')
      + ' - <why this check asks the retired copy>".');
    return loaded.length
      ? `${loaded.length} retired load(s) across ${new Set(loaded.map(l => l.file)).size} check(s), `
        + 'every one declared'
      : 'no acceptance check loads an unshipped module at all';
  });

H.test(run, 'G03', 'Every declaration naming a retired module carries a reason and describes a load that exists',
  () => {
    H.eq(missingReason.length, 0,
      'these declarations name a retired module but give no reason, so the reader cannot tell whether the '
      + 'use is deliberate: ' + JSON.stringify(missingReason));
    H.eq(declaredButNotLoaded.length, 0,
      'these declarations claim a retired module that the check does not actually load through the harness, '
      + 'so the declaration outlived the load it described: ' + JSON.stringify(declaredButNotLoaded)
      + '. A claim left behind after the code moved is not evidence.');
    return declarations.length
      ? `${declarations.length} declaration(s), each naming a module that is loaded and carrying a reason`
      : 'no declarations are present, which is correct if no retired module is loaded';
  });

H.test(run, 'G04', 'The guard can see a retired module when one is named, so G02 is not vacuous',
  () => {
    /* A check that only ever reports zero is not evidence. This asserts the
       detector's own reach: give it the names of retired modules and of
       assembled ones, and it must sort them correctly. */
    const probeNames = ['src/data/export.js', 'src/output/recipients.js',
      'src/engine/pricing.js', 'src/engine/engine.js', 'src/data/costbasis.js'];
    const sorted = probeNames.map(rel => ({ module: rel,
      classified: RETIRED.has(rel) ? 'RETIRED' : ASSEMBLED.has(rel) ? 'assembled' : 'neither' }));
    run.g04_probe = sorted;
    const expected = ['assembled', 'RETIRED', 'RETIRED', 'assembled', 'RETIRED'];
    const observed = sorted.map(s => s.classified);
    H.eq(JSON.stringify(observed), JSON.stringify(expected),
      'the guard misclassifies a module it was given by name: ' + JSON.stringify(sorted));
    return `classifies ${probeNames.length} named modules correctly `
      + `(${observed.filter(o => o === 'RETIRED').length} retired, ${observed.filter(o => o === 'assembled').length} assembled)`;
  });

/* ------------------------------------------- how the shipped concern is asked -- */

H.test(run, 'G05', 'The export builder that decides what a distributor receives is the assembled one, and it is asked',
  () => {
    /* The specific instance this guard exists for. Asserted positively so the
       guard reports the right thing rather than only the absence of a mistake:
       the assembled export module must be in the build's list, and the checks
       that judge participant output must load it. */
    const shippedExport = 'src/data/export.js';
    H.isTrue(ASSEMBLED.has(shippedExport),
      'tools/build.py no longer assembles ' + shippedExport + ', so this guard is asserting about the wrong '
      + 'module. The build list is: ' + JSON.stringify(lists.assembled));
    H.isTrue(RETIRED.has('src/output/recipients.js'),
      'src/output/recipients.js is no longer listed as retired in tools/build.py. If it has been wired in, '
      + 'this guard and the SAFE-05 checks must be revisited rather than left claiming otherwise.');

    const judges = ['accept_04_participant.cjs', 'accept_05_08_safety.cjs'];
    const notAsking = judges.filter(f => {
      const text = fs.readFileSync(path.join(ACCEPT, f), 'utf8');
      return !/H\.PATHS\.exportData\b/.test(text);
    });
    H.eq(notAsking.length, 0,
      'these checks judge the participant-facing export but never load the module the build assembles '
      + '(src/data/export.js, reached as H.PATHS.exportData): ' + JSON.stringify(notAsking));
    return `the build assembles ${shippedExport} and retires src/output/recipients.js; `
      + `${judges.length} export-judging check(s) load the assembled builder`;
  });

const s = H.write(run, 'guard_09_module_scope.json');
process.exitCode = s.fail ? 1 : 0;
