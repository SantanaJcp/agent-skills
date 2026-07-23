# ADR 0003: Pilot the Acta v2 instrument/record split on three skills

- **Status:** Piloting (not promoted; Acta 0.1 remains authoritative for all other skills)
- **Date:** 2026-07-22

## Context

The [HTML-effectiveness audit basis](../design/acta2-html-effectiveness-basis.md)
of revision `a8b0837`, evaluated with the durable
[criteria v2](../design/acta2-effectiveness-criteria-v2.md), found that Acta 0.1
artifacts preserved HTML's technical properties but lost its cognitive and
participatory ones: every DecisionGate rendered pre-approved, exports were
pre-authored constants that diverged from visible state, the shell dominated
the first viewport, and all four artifact families converged into one prose
document. The root causes were architectural (one-way Markdown→HTML flow,
prose-shaped skill contracts, cognition-blind QA), not cosmetic.

## Decision

Pilot a record/instrument split on exactly three skills — `three-code-paths`
(compare/decide), `build-with-notes` (monitor/intervene), and `concept-lab`
(explore/simulate):

1. **Instrument** — a task-specific HTML working surface generated while the
   decision is open. Its static no-JS DOM, live DOM, candidate Markdown, and
   candidate JSON all derive from one structured scenario JSON through one
   shared implementation (`design/acta2/lib/`). Controls ship disabled and are
   enabled only after successful runtime initialization; displayed exports are
   re-verified against a fresh recompute on every change and before copying.
2. **Candidate export → explicit acceptance** — the browser never updates
   files; interaction produces a `payload: "candidate"` export the human
   carries into chat; the agent restates the change and updates canonical
   state only after explicit confirmation. Silence is never approval.
3. **Record** — the durable, printable Acta view generated from canonical
   JSON (`{ scenario, accepted }`) only, after acceptance. The record is the
   only durable print artifact; instruments print as working snapshots.
4. **Operational single source** — each pilot skill bundles the generators
   (`references/acta2/`: assemble, export-core, renderers, CSS/JS assets,
   `generate-instrument.mjs`, `generate-record.mjs`), so independently
   installed skills regenerate artifacts from JSON with byte-identical logic
   using Node built-ins only. Agents never hand-edit the HTML.

Materialization stays deterministic and `--check`-guarded
(`npm run acta2`, `npm run acta2:check`); static gates live in
`npm run validate:acta2`; state/export invariants, hostile-identifier
rejection, canonical→record round-trips, and no-JS honesty are covered by
`tests/acta2.test.mjs`.

## Consequences

- The three pilot skills carry both Acta 0.1 references (rollback) and the
  v2 bundle; the other eleven HTML skills are untouched.
- Rollback is confined to reverting three SKILL.md files and deleting the v2
  sources, scripts, tests, and materialized references.
- Cognitive-effectiveness acceptance (criteria-v2 C-gates) is a human
  evaluation, deliberately not claimed by automation; the evaluation pack is
  produced outside the repository.
- Generalizing beyond the pilot requires a separate decision after that
  evaluation.
