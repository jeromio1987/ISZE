# R01 — Independent review (use in a fresh chat after any prompt)

You did not write this code. Review the work done for prompt **<PXX>** against `TECH_SPEC_Partner_Intake_Phase0_2026-10-09.md` and `00_START_HERE.md`. Be a sceptic, not a helper.

1. Run the new tests and the PRISM suite. Report the exact output.
2. For each acceptance test of the prompt: find the test, read it, and say whether it would fail if the behaviour were wrong. A test that cannot fail is not a test.
3. Search for violations: raw billing read; real data in the repository; hard-coded paths; a second loader or duplicate calculation; any send, ship, sync or publish; edits to `.cursor/rules/`, `07_deploy/`, existing adapters or the existing loader; shared-document wording with internal nicknames or personal names; piece counts as a headline; UTI/UMI or IUK/ITUK blended.
4. Re-derive two numbers from the source files by hand (not through the new code) and compare.
5. Open one real output, read it as the distributor or as Jerome would, and say what is confusing or unfair.
6. List what is missing against the spec, what is over-built, and what you would break first.
Return: verdict (accept / accept with changes / reject), a numbered list of findings with file and line, and the smallest set of changes that would make it acceptable. Do not fix anything yourself.
