# ADR 0004 — Generalizing Acta v2 from the three-skill pilot to the complete suite

Date: 2026-07-23 · Status: proposed (suite candidate — nothing committed, promoted, or released) · Extends: [ADR 0003](0003-acta-v2-instrument-record-pilot.md) (preserved unchanged as the historical pilot decision)

## Context

ADR 0003 piloted the Acta v2 instrument/record architecture on three skills
(`three-code-paths`, `build-with-notes`, `concept-lab`), validating the
compare/decide, monitor/intervene, and explore/simulate topologies plus the
loop: scenario JSON → generated open instrument → live working state →
candidate export → explicit conversational acceptance → accepted canonical
JSON/Markdown → generated durable record. The pilots subsequently received an
approved visual identity (warm canvas, white working surfaces, dark code
islands, v2 type scale) and are the visual-quality floor for the suite.

The remaining eleven HTML skills still shipped Acta 0.1 hand-authored
recipes. This ADR records their migration.

## Decision

1. **One manifest.** `design/acta2/lib/suite.mjs` is the single source of
   truth for the suite roster and each skill's artifact role. The
   materializer, the static validator, and the test suite all iterate it;
   nothing else hardcodes skill lists.
2. **Roles are explicit, not uniform.** Instrument + record:
   `three-code-paths`, `build-with-notes`, `concept-lab`,
   `interface-directions`, `change-blueprint` (two instruments: Gate A
   specification, Gate B implementation plan), `do-i-understand-this`,
   `draw-the-flow`, `draw-it-in-svg`, `deepen-the-codebase`,
   `find-the-cause`, `learning-workbench`. Record-only (no meaningful human
   action inside the page, so no controls): `feature-xray`,
   `what-just-happened`. Instrument-only (deliberately no durable record):
   `feel-the-flow`. Text-only (no HTML at all): `make-me-realize`.
3. **Kinds, not clones.** The state/export core gained three instrument
   kinds — `quiz` (answers → score → named gaps), `checklist` (per-item
   verdicts, optional required conclusion), `prototype` (felt parameters +
   conclusion, no derived model) — plus record-only `dossier` scenarios.
   Existing kinds (`decision`, `stop-gate`, `model`) are reused where the
   state machine genuinely matches; every candidate export and canonical
   record boundary check extends to the new kinds.
4. **Shared renderers, distinct topologies.** Node-side, dependency-free
   modules ship in every bundle: `highlight.mjs` (build-time syntax color),
   `flow.mjs` (grid node/edge diagrams with named-path tagging), and
   `figure.mjs` (constrained vector-figure vocabulary — authored drawings
   with no markup sink). Each skill keeps its own body renderer and
   topology CSS; a blind screenshot distinguishes every topology.
5. **Records got a v2 foundation.** New-skill records render through
   `design/acta2/record.css` (paper identity, print-first) while the three
   pilot records remain byte-compatible on the Acta 0.1 record CSS.
6. **Honesty boundaries hold.** Instruments never ship accepted state;
   candidates never claim canonical status; records generate only from
   accepted canonical state; ephemeral view state (timeline filters, flow
   path emphasis) never enters exports; quizzes and understanding checks are
   never merge gates; no owners or metrics are invented. Multi-gate records
   also validate their prerequisite decision chain: Gate B cannot produce a
   `change-blueprint` record unless the exact accepted Gate A artifact revision
   is present once with an approving selection.

## Rollback

Every migrated skill retains its Acta 0.1 references
(`references/acta-protocol.md`, `references/acta-scaffold.html`) untouched.
Rolling back a skill means deleting its `references/acta2/` bundle and
`references/instrument*.html` / `references/record.html` scaffolds and
reverting its SKILL.md paragraph — the 0.1 recipe resumes working without
further changes. Do not delete the 0.1 references until the full migration
receives human approval.

## Status and evaluation honesty

The suite is a **generated suite candidate**: 76/76 automated checks pass
(state/export invariants, canonical→record boundaries, installed-bundle
byte round-trips, no-JS honesty, 320 px reflow, in-page self-tests, static
validation of all 14 bundles). The formal C2/C3 human-evaluation methodology
in the evaluation pack applies to the three pilots only; none of the eleven
new artifacts has passed human evaluation, and this ADR does not claim
otherwise.
