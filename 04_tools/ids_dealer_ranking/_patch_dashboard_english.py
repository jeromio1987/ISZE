#!/usr/bin/env python3
"""Patch IDS dealer-compare template: English bands, max-point good/bad, changelog."""

from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parent
TPL = ROOT / "ids_dashboard_template.html"


def main() -> None:
    t = TPL.read_text(encoding="utf-8")

    repls = [
        (
            "<p>Offline · sections A–E + questions · goed / medium / slecht · built __BUILT_AT__</p>",
            "<p>Offline · sections A–E + questions · good / medium / bad · built __BUILT_AT__</p>",
        ),
        ("<h3>Strengths (goed)</h3>", "<h3>Strengths (good)</h3>"),
        ("<h3>Weak points (slecht)</h3>", "<h3>Weak points (bad)</h3>"),
        (
            '<option value="band">traffic light (goed/medium/slecht)</option>',
            '<option value="band">traffic light (good/medium/bad)</option>',
        ),
        (
            "<p class=\"hint\">Compare each checklist item to country and network average. Band = goed / medium / slecht.</p>",
            "<p class=\"hint\">Compare each checklist item to country and network average. Band = good / medium / bad. Strengths = full score on max-point items; weak = zero score — one pick per section A–E.</p>",
        ),
        ('<option value="good">Goed</option>', '<option value="good">Good</option>'),
        ('<option value="bad">Slecht</option>', '<option value="bad">Bad</option>'),
        (
            'return b === "good" ? "Goed" : b === "bad" ? "Slecht" : b === "medium" ? "Medium" : "—";',
            'return b === "good" ? "Good" : b === "bad" ? "Bad" : b === "medium" ? "Medium" : "—";',
        ),
        (
            '<span><i style="background:var(--good)"></i>Goed ${counts.good}</span>',
            '<span><i style="background:var(--good)"></i>Good ${counts.good}</span>',
        ),
        (
            '<span><i style="background:var(--bad)"></i>Slecht ${counts.bad}</span>',
            '<span><i style="background:var(--bad)"></i>Bad ${counts.bad}</span>',
        ),
        (
            'legend.innerHTML = `<span><i style="background:#2d8a5e"></i> Goed</span><span><i style="background:#c48a1a"></i> Medium</span><span><i style="background:#c45c3e"></i> Slecht</span>`;',
            'legend.innerHTML = `<span><i style="background:#2d8a5e"></i> Good</span><span><i style="background:#c48a1a"></i> Medium</span><span><i style="background:#c45c3e"></i> Bad</span>`;',
        ),
    ]
    for old, new in repls:
        if old not in t:
            print("WARN missing:", old[:70])
        else:
            t = t.replace(old, new)

    # Add changelog tab if missing
    if 'data-tab="changelog"' not in t:
        t = t.replace(
            '<button class="tab" data-tab="country" type="button">By country</button>\n  </nav>',
            '<button class="tab" data-tab="country" type="button">By country</button>\n'
            '    <button class="tab" data-tab="changelog" type="button">Changelog</button>\n  </nav>',
        )

    changelog_panel = '''
    <section id="panel-changelog" class="panel">
      <div class="card">
        <h2>Changelog — 2026-07-28</h2>
        <ul>
          <li>All UI labels in English (good / medium / bad — no Dutch goed/slecht).</li>
          <li>Country names in English: Switzerland / France / Italy / Spain (not MIDI_CH etc.).</li>
          <li>UK LCV (IUK), UK CV (ITUK), Israel LCV (UMI IDS pack — never blended with UTI), Norway (RSA).</li>
          <li>Benelux kept; Belgium, Netherlands and Luxembourg also shown as separate countries.</li>
          <li>Overview strengths / weak points: per section A–E, based on max-point items (full score = good, zero = bad) — not “first question in section”.</li>
          <li>Dealer total score shown as percentage (Score % of 280); GPS context on feedback packs prefers capture % where available.</li>
        </ul>
        <p class="hint">Built __BUILT_AT__</p>
      </div>
    </section>
'''
    if 'id="panel-changelog"' not in t:
        # Insert before closing </main>
        t = t.replace("  </main>", changelog_panel + "\n  </main>")

    # Replace overview strengths/weak block with max-point logic
    old_block = """      const ranked = [...rows].filter((r) => r.gapC != null).sort((a, b) => b.gapC - a.gapC);
      const strengths = ranked.filter((r) => r.gapC > 0).slice(0, 5);
      const weak = [...ranked].filter((r) => r.gapC < 0).sort((a, b) => a.gapC - b.gapC).slice(0, 5);
      $("#ov-strengths").innerHTML = strengths.length
        ? strengths.map((r) => `<li><button type="button" class="linkish" data-jump-sec="${r.id}"><strong>${r.id}</strong></button> ${pctGap(r.gapC)} vs country · ${bandHtml(r.band)}</li>`).join("")
        : "<li>No section above country average.</li>";
      $("#ov-weak").innerHTML = weak.length
        ? weak.map((r) => `<li><button type="button" class="linkish" data-jump-sec="${r.id}"><strong>${r.id}</strong></button> ${pctGap(r.gapC)} vs country · ${bandHtml(r.band)}</li>`).join("")
        : "<li>No section below country average.</li>";
      [...$("#ov-strengths").querySelectorAll("[data-jump-sec]"), ...$("#ov-weak").querySelectorAll("[data-jump-sec]")].forEach((btn) => {
        btn.addEventListener("click", () => jumpToQuestions(dealer.id, btn.getAttribute("data-jump-sec")));
      });
    }"""

    new_block = """      const hl = pickMaxPointHighlights(dealer);
      $("#ov-strengths").innerHTML = hl.strengths.length
        ? hl.strengths.map((r) => `<li><button type="button" class="linkish" data-jump-sec="${r.section}" data-jump-q="${r.id}"><strong>${r.id}</strong></button> ${r.score}/${r.max} (full) · ${esc(shortText(r.text))}</li>`).join("")
        : "<li>No full-score max-point items in sections A–E.</li>";
      $("#ov-weak").innerHTML = hl.weak.length
        ? hl.weak.map((r) => `<li><button type="button" class="linkish" data-jump-sec="${r.section}" data-jump-q="${r.id}"><strong>${r.id}</strong></button> 0/${r.max} · ${esc(shortText(r.text))}</li>`).join("")
        : "<li>No zero-score max-point items in sections A–E.</li>";
      [...$("#ov-strengths").querySelectorAll("[data-jump-sec]"), ...$("#ov-weak").querySelectorAll("[data-jump-sec]")].forEach((btn) => {
        btn.addEventListener("click", () => jumpToQuestions(dealer.id, btn.getAttribute("data-jump-sec")));
      });
    }

    function shortText(s) {
      const t = (s || "").replace(/\\s+/g, " ").trim();
      return t.length > 72 ? t.slice(0, 70) + "…" : t;
    }
    function esc(s) {
      return String(s || "").replace(/&/g,"&amp;").replace(/</g,"&lt;").replace(/>/g,"&gt;");
    }
    /** Per section A–E: good = full score on an item; bad = zero. Prefer higher max points (not first row). */
    function pickMaxPointHighlights(dealer) {
      const qs = questions();
      const strengths = [];
      const weak = [];
      if (!dealer || !Array.isArray(dealer.q) || !qs.length) return { strengths, weak };
      const bySec = {};
      qs.forEach((q, i) => {
        const dPct = dealer.q[i];
        const maxPts = Number(q.max) || 0;
        if (dPct == null || maxPts <= 0) return;
        const score = dPct * maxPts;
        const sec = q.section || (q.id || "").charAt(0);
        if (!secIds().includes(sec)) return;
        if (!bySec[sec]) bySec[sec] = { good: [], bad: [] };
        const item = { id: q.id, section: sec, text: q.text || "", score: Math.round(score * 1000) / 1000, max: maxPts, pct: dPct };
        if (Math.abs(score - maxPts) < 0.05) bySec[sec].good.push(item);
        if (score < 0.05) bySec[sec].bad.push(item);
      });
      secIds().forEach((sec) => {
        const g = (bySec[sec] && bySec[sec].good || []).slice().sort((a, b) => b.max - a.max || a.id.localeCompare(b.id));
        const b = (bySec[sec] && bySec[sec].bad || []).slice().sort((a, b) => b.max - a.max || a.id.localeCompare(b.id));
        if (g[0]) strengths.push(g[0]);
        if (b[0]) weak.push(b[0]);
      });
      return { strengths, weak };
    }"""

    if old_block in t:
        t = t.replace(old_block, new_block)
        print("overview highlights replaced")
    elif "pickMaxPointHighlights" in t:
        print("overview highlights already patched")
    else:
        print("WARN: overview block not found")

    # Overview hint
    t = t.replace(
        "plus strengths and weak points. Click a section to open question drill.",
        "plus strengths/weak points (full vs zero on max-point checklist items, one per section A–E). Click a section to open question drill.",
    )

    # Changelog tab activation
    if 'if (btn.dataset.tab === "vs-network") renderVsNetwork();' in t and "changelog" not in t.split("btn.dataset.tab ===")[-1][:200]:
        pass  # no render needed for static changelog

    TPL.write_text(t, encoding="utf-8")
    print("template written", TPL)
    print("goed left:", t.lower().count("goed"), "slecht left:", t.lower().count("slecht"))


if __name__ == "__main__":
    main()
