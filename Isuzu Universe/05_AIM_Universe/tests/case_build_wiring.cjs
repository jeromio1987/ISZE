#!/usr/bin/env node
/* ===========================================================================
   The assembled artifact must define every global its modules read.

   WHY THIS FILE EXISTS
   --------------------
   This is a FAILING check, deliberately. It is the reproduction of a defect
   found while doing CASE-01..05, in a file this developer does not own, so the
   test is written and reported here rather than patched.

   WHAT IS WRONG
   -------------
   `src/data/cases.js` is now a facade over `src/case/schema.js` and
   `src/case/store.js` - one implementation instead of two. `tools/build.py`
   assembles `src/data/cases.js` but retires the two modules it depends on, so
   the artifact contains a module that reads two globals nothing defines.

   In a browser, `src/data/cases.js` resolves its dependency from `root`
   (there is no `require`), so `AIMCaseStore` is `undefined` and:

     $ node -e "... run the assembled modules in a vm context without the base ..."
     makeRepository() THREW: TypeError: Cannot read properties of undefined (reading 'describeStorage')

   `src/ui/app.js` calls `AIMCases.makeRepository({...})` at its module scope, so
   the throw happens before any view paints. The SYNTHETIC artifact built on
   2026-09-22 after the facade landed is a blank page with a console error.

   WHY THE EXISTING GUARD DID NOT CATCH IT
   ---------------------------------------
   `tools/build.py` has a check for exactly this class of fault: a shipped module
   must not read an unwired one. It computes the global to look for like this:

     stem   = os.path.splitext(os.path.basename(unwired))[0]
     holder = "root.AIM" + stem[0].upper() + stem[1:]

   That gives `root.AIMStore` for `src/case/store.js` and `root.AIMSchema` for
   `src/case/schema.js`. Those names do not exist. The files publish
   `root.AIMCaseStore` and `root.AIMCaseSchema`, so the guard searched the
   shipped source for two strings that never occur, found nothing, and reported
   the build clean. `src/data/cases.js` is assembled with a dependency nothing
   provides and `labels : clean` is printed.

   The guard works by coincidence for the other retired modules, whose globals
   happen to match their file names (`src/ui/views.js` -> `root.AIMViews`). This
   is the first pair where it does not, which is why the fault arrived now.

   HOW TO FIX IT - two changes, and they belong together
   -----------------------------------------------------
   1. `tools/build.py`: compute `holder` from the name each file actually
      publishes rather than from its file name. The declaration is already in
      every module, on its last lines - `root.AIMCaseStore = API;` in
      `src/case/store.js`, `root.AIMCaseSchema = API;` in `src/case/schema.js`,
      and `root.AIMUI = root.AIMUI || {}` in `src/ui/views.js`, which publishes
      into a namespace rather than on a bare name of its own.

      Reading that line is what makes the check measure the thing it claims to.
      The `src/ui/views.js` case also needs handling, because it publishes into a
      namespace rather than on its own name.

   2. `tools/build.py`: decide whether `src/case/schema.js` and
      `src/case/store.js` are assembled. They are the lifecycle the plan's
      CASE-02..05 require, and CASE-01's durable store. Either
        (a) add both to `MODULES`, before `src/data/cases.js`, so the facade has
            something to resolve - this is a wiring decision, and
            docs/DEDUP_and_VAT.md already records it as the integration owner's
            to make; or
        (b) keep them retired and delete the dependency from `src/data/cases.js`,
            which means putting the logic back in that file - which is the
            duplicate the CASE work exists to remove.
      (a) is the honest one. Until it is made, the artifact must not be rebuilt.

   WHAT THIS FILE DOES NOT DO
   --------------------------
   It does not patch `tools/build.py`, and it does not rebuild `dist/`. It
   measures the artifact, if one is present, and reports.
   =========================================================================== */
'use strict';

const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');

const ROOT = path.join(__dirname, '..');
const BUILD = path.join(ROOT, 'tools', 'build.py');

const checks = [];
function check(id, name, fn) {
  try {
    const evidence = fn();
    checks.push({ id, name, status: 'PASS', evidence: evidence === undefined ? '' : String(evidence) });
  } catch (e) {
    checks.push({ id, name, status: 'FAIL', evidence: e.message });
  }
}

/* ---------------------------------------------------------------- helpers -- */

/* The modules the build assembles, and the modules it retires. Read from
   tools/build.py the same way tests/accept/guard_09_module_scope.cjs reads them,
   so this file cannot fall out of step with the build. */
function buildLists() {
    const text = fs.readFileSync(BUILD, 'utf8');
    /* Anchor on the declarations, not on the top of the file. The build carries
       explanatory prose above MODULES and a helper below it, and a slice from
       offset zero picks up quoted paths inside that prose. Measured 2026-09-22:
       that made `assembled` start with a path from a docstring and W04 report
       that cases.js was no longer assembled while it plainly was. */
    const modsAt = text.indexOf('MODULES = [');
    const unwiredAt = text.indexOf('UNWIRED_MODULES = [');
    const bannedAt = text.indexOf('BANNED_IN_OUTPUT', unwiredAt);
    const pair = /\("(src\/[^"]+)",\s*"[^"]+"\)/g;
    const collect = slice => [...slice.matchAll(pair)].map(m => m[1]);
    return {
      assembled: collect(text.slice(modsAt, unwiredAt)),
      retired: collect(text.slice(unwiredAt, bannedAt < 0 ? text.length : bannedAt))
    };
  }

  /* The globals a module publishes, read from the file rather than derived from
     its name. `root.AIMX = ...` and `root.AIMUI = root.AIMUI || {}` both count. */
  function globalsPublishedBy(source) {
    const out = [];
    for (const m of source.matchAll(/root\.(AIM[A-Za-z0-9_]*)\s*=/g)) {
      if (out.indexOf(m[1]) < 0) out.push(m[1]);
    }
    return out;
  }

  /* PUBLISHED_BY as the build declares it: path -> the global that file publishes.
     Added 2026-09-22 with the fix; W01 reads it instead of reproducing a
     derivation the build no longer uses. */
  function publishedByTable() {
    const text = fs.readFileSync(BUILD, 'utf8');
    const at = text.indexOf('PUBLISHED_BY');
    if (at < 0) return {};
    const body = text.slice(text.indexOf('{', at), text.indexOf('\n}', at));
    const out = {};
    for (const m of body.matchAll(/"([^"]+)"\s*:\s*(?:"([^"]+)"|(None))/g)) {
      out[m[1]] = m[3] ? null : m[2];
    }
    return out;
  }

/* The globals a module reads off `root`, excluding its own assignment line. */
function globalsReadBy(source) {
  const out = [];
  for (const m of source.matchAll(/root\.(AIM[A-Za-z0-9_]*)/g)) {
    const line = source.slice(source.lastIndexOf('\n', m.index) + 1, m.index);
    if (/root\.AIM[A-Za-z0-9_]*\s*=\s*$/.test(line.trim())) continue;
    if (out.indexOf(m[1]) < 0) out.push(m[1]);
  }
  return out;
}

/* ============================================================ the checks == */

check('W01', 'The build guard looks for the global each retired module actually publishes',
  () => {
    /* UPDATED 2026-09-22 by the integration owner, after the fix this file asked
       for. It used to assert the build's FILE-NAME derivation and fail while that
       derivation was wrong. The build now carries PUBLISHED_BY, a table read from
       each module's own assignment line, so the original assertion no longer
       describes the mechanism. The original wording and expectation are kept in
       this comment so the two states can be compared.

       What it checks now: every retired module that still exists on disk has an
       entry in PUBLISHED_BY, and that entry names a global the file really
       publishes. A missing or stale entry is what would make the guard vacuous
       again. */
    const lists = buildLists();
    const table = publishedByTable();
    const problems = [];
    for (const rel of lists.retired) {
      const file = path.join(ROOT, rel);
      if (!fs.existsSync(file)) continue;              /* tombstone for a deleted file */
      const published = globalsPublishedBy(fs.readFileSync(file, 'utf8'));
      const declared = table[rel];
      if (declared === undefined) {
        problems.push({ module: rel, problem: 'no PUBLISHED_BY entry, so the guard cannot see it',
          file_publishes: published });
      } else if (published.indexOf(declared) < 0 && published.length) {
        problems.push({ module: rel, problem: 'PUBLISHED_BY names a global the file does not publish',
          declared: declared, file_publishes: published });
      }
    }
    if (problems.length) {
      throw new Error('tools/build.py PUBLISHED_BY is missing or stale for these retired modules, so '
        + 'the "a shipped module must not read an unwired one" check cannot see them: '
        + JSON.stringify(problems));
    }
    const checked = lists.retired.filter((r) => fs.existsSync(path.join(ROOT, r))).length;
    return checked + ' retired module(s) on disk, each declared in PUBLISHED_BY with the global it '
      + 'actually publishes';
  });

check('W02', 'A module the build assembles does not read a global the build retires',
  () => {
    /* The property the guard is supposed to enforce, measured directly instead of
       through the guard. This is the check that fails today. */
    const lists = buildLists();
    const retiredGlobals = {};
    for (const rel of lists.retired) {
      const file = path.join(ROOT, rel);
      if (!fs.existsSync(file)) continue;
      globalsPublishedBy(fs.readFileSync(file, 'utf8')).forEach(g => { retiredGlobals[g] = rel; });
    }
    const offenders = [];
    for (const rel of lists.assembled) {
      const file = path.join(ROOT, rel);
      if (!fs.existsSync(file)) continue;
      const source = fs.readFileSync(file, 'utf8');
      const own = globalsPublishedBy(source);
      globalsReadBy(source).forEach(g => {
        if (own.indexOf(g) >= 0) return;
        if (retiredGlobals[g]) offenders.push({ module: rel, reads: 'root.' + g, provided_by: retiredGlobals[g] });
      });
    }
    if (offenders.length) {
      throw new Error('these assembled modules read a global that only a RETIRED module publishes, so in a '
        + 'browser the read is undefined and the failure is at runtime: ' + JSON.stringify(offenders)
        + '. Either assemble the module that provides it (add it to MODULES in tools/build.py, before the '
        + 'module that reads it), or remove the dependency. Until then the artifact must not be rebuilt.');
    }
    return lists.assembled.length + ' assembled module(s), none reading a retired global';
  });

check('W03', 'Each assembled artifact is self-consistent: it defines every global its own code reads',
  () => {
    /* The end-to-end question, asked of the BUILT FILE's own code rather than of
       today's source. That distinction matters: an artifact built before a source
       change is not broken, it is older. Measuring the artifact's own scripts is
       what tells the two apart. */
    const distDir = path.join(ROOT, 'dist');
    if (!fs.existsSync(distDir)) throw new Error('no dist/ folder, so this check proved nothing');
    const artifacts = fs.readdirSync(distDir).filter(f => f.endsWith('.html'));
    if (!artifacts.length) throw new Error('no artifact in dist/ to measure, so this check proved nothing');

    const report = [];
    for (const name of artifacts) {
      const html = fs.readFileSync(path.join(distDir, name), 'utf8');
      /* The artifact's own assembled code: every <script> body, minus the JSON
         payload block. */
      const scripts = [];
      for (const m of html.matchAll(/<script(?![^>]*type="application\/json")[^>]*>([\s\S]*?)<\/script>/g)) {
        scripts.push(m[1]);
      }
      const code = scripts.join('\n');

      const defined = globalsPublishedBy(code);
      const missing = [];
      for (const g of globalsReadBy(code)) {
        if (defined.indexOf(g) >= 0) continue;
        /* A read that is not an assignment, of a name the artifact never
           defines. */
        if (!new RegExp('root\\.' + g + '\\s*=\\s*[^=]').test(code)) missing.push('root.' + g);
      }
      const stale = missing.length && !/RETIRED_AS_IMPLEMENTATION/.test(code)
        ? ' (this artifact predates the current source, so a REBUILD would fail; this file is not itself broken)'
        : '';
      report.push(name + (missing.length ? ' MISSING ' + JSON.stringify(missing) + stale : ' complete')
        + ' [' + scripts.length + ' script block(s)]');
      if (missing.length && !stale) {
        throw new Error('the artifact ' + name + ' reads globals nothing in it defines, so it fails at '
          + 'runtime: ' + JSON.stringify(missing));
      }
    }
    return report.join(' | ');
  });

check('W04', 'A browser has no require, so the facade must not depend on one',
  () => {
    /* The mechanism that makes W02 fatal rather than merely untidy: in the
       artifact there is no `require`, so a module's dependency resolves from
       `root` or not at all. Demonstrated by running the assembled modules in a
       vm context that has no require, exactly as a browser does. */
    const lists = buildLists();
    if (!lists.assembled.some(r => r.endsWith('src/data/cases.js'))) {
      throw new Error('src/data/cases.js is no longer assembled, so this check is measuring the wrong tree');
    }
    const sandbox = {
      localStorage: { getItem: () => null, setItem() {}, removeItem() {} },
      console, Intl, JSON, Math, Date, URLSearchParams
    };
    sandbox.window = sandbox;
    sandbox.globalThis = sandbox;
    vm.createContext(sandbox);

    /* Everything the build assembles before the module under test, in build order,
       exactly as the artifact loads them. This used to load contracts.js and
       cases.js only, which was the tree when the facade needed one global. The
       facade now needs the case pair as well, so the check loads whatever the
       build actually puts before it rather than a hardcoded pair that can drift. */
    const all = lists.assembled;
    const idx = all.indexOf('src/data/cases.js');
    if (idx < 0) {
      throw new Error('src/data/cases.js is not in the build\'s module list, so this check is '
        + 'measuring the wrong tree');
    }
    const loaded = [];
    for (const rel of all.slice(0, idx)) {
      vm.runInContext(fs.readFileSync(path.join(ROOT, rel), 'utf8'), sandbox);
      loaded.push(rel);
    }
    const casesPath = path.join(ROOT, 'src/data/cases.js');
    vm.runInContext(fs.readFileSync(casesPath, 'utf8'), sandbox);

    if (typeof sandbox.AIMCases !== 'object' || !sandbox.AIMCases) {
      throw new Error('src/data/cases.js did not publish AIMCases in a browser-like context');
    }
    try {
      sandbox.AIMCases.makeRepository({ forceMemory: true });
    } catch (e) {
      throw new Error('src/data/cases.js could not build a repository in a browser-like context, so the '
        + 'assembled page cannot start: ' + e.constructor.name + ': ' + e.message
        + '. The facade resolves its implementation from a global the artifact does not define.');
    }
    return 'the facade builds a repository with only the globals the artifact defines, loading '
      + loaded.length + ' module(s) first: ' + loaded.join(', ');
  });

/* ---------------------------------------------------------------- report -- */

const width = Math.max(...checks.map(c => c.id.length + c.name.length)) + 4;
console.log('');
console.log('AIM build wiring - ' + checks.length + ' checks');
console.log('='.repeat(Math.min(width + 20, 100)));
let failures = 0;
for (const c of checks) {
  if (c.status === 'FAIL') failures++;
  console.log(`${c.status}  ${c.id}  ${c.name}`);
  if (c.evidence) console.log('      -> ' + c.evidence);
}
console.log('-'.repeat(Math.min(width + 20, 100)));
console.log(`${checks.length - failures} passed, ${failures} failed, of ${checks.length}`);
console.log('');
if (failures) {
  console.log('A failing check here means the assembled artifact would throw before any view paints, or');
  console.log('that a guard it relies on cannot see the thing it is supposed to guard. Fix the build,');
  console.log('not this file.');
  console.log('');
}
process.exit(failures === 0 ? 0 : 1);
