# Acta v2 pilot — historical architecture and implementation contract

Status: superseded for current operations by
[ADR 0004](../adr/0004-acta-v2-suite-generalization.md) and
[ADR 0005](../adr/0005-promote-acta-v2-suite.md). This document preserves the
three-skill pilot contract and is not the published suite's current status;
Acta v2 is now authoritative and Acta 0.1 is retained for compatibility.
Basis: the durable [HTML-effectiveness audit basis](acta2-html-effectiveness-basis.md)
and [effectiveness criteria v2](acta2-effectiveness-criteria-v2.md). This
document translates that audit into an implementable contract; it does not
restate it.

## 1. Roles and definitions

| Term | Definition |
|---|---|
| **Instrument** | A self-contained, offline HTML working surface generated while a task or decision is **open**. Its topology serves one declared cognitive action (compare, monitor, simulate). It renders working state, accepts human input, and produces a candidate export. It is disposable and never authoritative. |
| **Working state** | In-browser state = agent-authored instrument data (a JSON data island) + the human's live inputs (selection, resolution, parameters, rationale, filters). Ephemeral; lost on reload by design. |
| **Candidate export** | A Markdown payload (with YAML frontmatter, plus a JSON equivalent) derived **only** from working state, marked `payload: "candidate"`. It is a proposal carried back to the agent by the human (clipboard/paste or restated in chat). It never updates files by itself. |
| **Acceptance** | A conversational handshake: the agent (1) receives the candidate, (2) restates exactly what will change, (3) waits for explicit confirmation, (4) only then updates canonical files. Silence, gate-folding, or inferred approval are protocol violations. |
| **Canonical state** | The durable state under `.agent-work/<initiative>/<skill>/`: `scenario.json` (the complete structured scenario), `canonical.json` (`{ scenario, accepted }` — everything a record needs: comparison evidence, timeline/checks, facts, simplifications, accepted working state, provenance), and the canonical Markdown per the Acta 0.1 protocol with `acta_protocol: "0.2"` and `phase: "accepted"`. Records regenerate from `canonical.json` alone. |
| **Record** | The durable, printable Acta view (`record.html`) generated **from accepted canonical state only**, after acceptance. Full notarial identity (Acta 0.1 tokens, complete provenance, epistemic labels, evidence register). No decision controls; it may preserve rejected alternatives and evidence. |

## 2. State transitions

```
ground → instrument brief → topology → instrument.html (OPEN)
   → human inspects/manipulates → candidate export
   → agent restates → explicit "yes" in chat        [D2: silence ≠ approval]
   → canonical .md/.json updated (status: approved/completed)
   → record.html regenerated from canonical state   [never from browser state]
```

Rejection or revision loops back to the instrument (regenerate with new data if inputs changed). An instrument whose gate has been accepted is stale; the skill regenerates or removes it and the record becomes the durable artifact.

## 3. Trust boundaries

- **Browser → files: forbidden.** The instrument has no persistence channel (no storage, no network, no file writes). The only exit is human-carried text.
- **Candidate → canonical: agent-mediated only**, behind explicit conversational acceptance (D2).
- **Instrument data**: everything rendered from the data island is treated as untrusted text — `textContent`/`createElement`/`createElementNS`/attribute setters only; no `innerHTML`-class sinks, no inline handlers. The Node-side static renderer HTML-escapes every interpolated value.
- **Record**: generated from canonical state by the agent; carries the same safety rules.

## 4. State/export invariants (mechanically enforced)

1. **Single source:** static no-JS DOM, live DOM updates, candidate Markdown, and candidate JSON all derive from one data structure. The materializer renders the static DOM from the same data island the runtime parses; the runtime derives exports with the same pure functions tests import in Node (`design/acta2/lib/export-core.mjs`).
2. **No static payload:** instruments contain no pre-authored export content. The export node is populated (and re-populated) from working state on every change. The scaffold placeholder text is a marker, never a plausible payload.
3. **Candidate marking:** every export contains `acta_protocol: "0.2"`, `payload: "candidate"`, producer skill, initiative, instrument kind, working status, selections/parameters, unresolved items, and provenance inputs.
4. **Detectable mismatch:** after every render the runtime recomputes the candidate from working state and compares it with the displayed export text; a divergence flips a visible integrity banner and `data-acta2-integrity="mismatch"`. A built-in self-test (`?acta2selftest=1`) simulates the primary interactions and reports `ACTA2-SELFTEST-PASS/FAIL` in the DOM for headless assertion.
5. **Status honesty:** the visible status label and the exported status come from one `deriveStatus()` function. The five audit mismatch classes (approved-vs-awaiting, selection-vs-empty-decisions, resolved-vs-blocked, completed-vs-draft, static stale payload) each have a failing test in `tests/acta2.test.mjs`.
6. **Record honesty:** records are generated from `canonical.json` only, never from instrument working state; instruments never render an accepted/approved stamp.
7. **Honest degradation:** every control ships `disabled` + `data-a2-enable` and is enabled only after the runtime initializes and the first verify passes; inline `.a2-jsnote` chat fallbacks sit beside the controls. Without JavaScript nothing appears operational.
8. **Ephemeral view state:** `build-with-notes`' timeline `filter` changes what the human looks at, never what they decide — it is deliberately excluded from candidate exports and canonical state (tested).
9. **Print policy:** `record.html` is the only durable print artifact. Instruments print as working snapshots: controls are hidden, textual state (status, selection line, parameter outputs) prints, and a visible print banner says so.

## 5. Naming and materialization

```
design/acta2/                      # publisher-side v2 sources (never a runtime dependency)
  VERSION                          # historical 0.2.0-pilot
  protocol.md                      # v2 protocol installed into pilot skills at the time
  base.css                         # shared technical primitives only (tokens, focus, print, reduced motion, reflow, disclosure, trust strip)
  runtime.js                       # shared store/render/export/verify/copy/self-test runtime
  lib/export-core.mjs              # pure logic; Node-importable; inlined into instruments at materialization
  instruments/<skill>/meta.json    # instrument brief (human question, cognitive action, first-viewport contract)
  instruments/<skill>/topology.css # task-specific layout — deliberately NOT shared
  instruments/<skill>/body.mjs     # Node static renderer: data → main topology HTML
  instruments/<skill>/instrument.js# browser wiring for this topology
  instruments/<skill>/scaffold-data.json   # example data island for the installed scaffold
  records/<skill>.mjs              # Node renderer: canonical/accepted data → record body (Acta 0.1 identity)
  fixtures/<skill>/scenario.json           # realistic open-scenario data
  fixtures/<skill>/accepted.json           # realistic accepted-state data (composed into canonical.json)

  lib/assemble.mjs                 # THE single HTML assembly implementation (publisher + bundles)
  lib/generate-instrument.mjs      # bundled CLI: scenario.json → instrument.html
  lib/generate-record.mjs          # bundled CLI: canonical.json → record.html

scripts/materialize-acta2.mjs      # assembles installed references + generator bundles + test fixtures; --check mode
scripts/validate-acta2.mjs         # v2 static gates
tests/acta2.test.mjs               # invariant, determinism, safety, fixture-realism tests

incubator/<pilot>/references/
  acta2-protocol.md                # materialized, sha-marked
  acta2/                           # self-contained generator bundle (Node built-ins only):
                                   #   assemble.mjs · export-core.mjs · body.mjs · record-body.mjs
                                   #   base.css · topology.css · runtime.js · instrument.js
                                   #   acta-record.css · bundle.json
                                   #   generate-instrument.mjs · generate-record.mjs
  instrument.html                  # rendered scaffold example (never hand-edited; regenerate from scenario JSON)
  record.html                      # rendered record example (regenerate from canonical JSON)
```

Materialization was required to be deterministic (byte-stable, LF-only,
sha-256 markers identifying Acta version, recipe, and source digest). The pilot
bundles were self-contained: no runtime reference to `design/acta2/`, sibling
skills, npm packages, or the network. Those properties remain current suite
requirements through the later ADRs.

## 6. Historical backward compatibility and rollback plan

- Acta 0.1 materialization, validation, tests, recipes, and the 11 non-pilot skills are untouched. Pilot skills **keep** their v1 `references/acta-scaffold.html` (still materialized and validated) so `npm run check` stays green and rollback is trivial.
- Rollback = revert the three SKILL.md files (they are the only pointers to v2 references) and delete `design/acta2/`, the two scripts, the test file, and materialized v2 references. No other artifact depends on v2.
- `scripts/check.mjs` gains two commands (`materialize-acta2 --check`, `validate-acta2`); removing them restores the previous pipeline byte-for-byte.

## 7. Historical pilot scope

Only `three-code-paths` (Compare/decide), `build-with-notes` (Monitor/intervene), `concept-lab` (Explore/simulate). Their topologies are intentionally not a shared template; only technical primitives (`base.css`, `runtime.js`, `export-core.mjs`) are shared. Migration of the other eleven HTML skills, routing changes, and record-identity redesign are out of scope.

## 8. Test seams

1. **Pure core:** `export-core.mjs` unit-tested in Node (status derivation, candidate building, per-kind derives: decision, stop-gate, model).
2. **Materializer:** run twice → byte-identical; `--check` detects staleness; unknown pilot rejected; markers present.
3. **Static gates:** `validate-acta2.mjs` — safety sinks, no network, unique ids, resolved refs, noscript, aria-live, print, reduced motion, reflow, no static export payload, instruments never claim acceptance, fixture realism (distinct options, open gate, no preselection).
4. **Behavioral:** in-page self-test driven by headless Chromium (`--dump-dom` + `ACTA2-SELFTEST-PASS`), skipped automatically when no Chromium binary is available.
5. **Manual/cognitive:** criteria-v2 C-gates prepared as an evaluation pack; never auto-claimed.

## 9. Out of scope (explicit)

Migration of the other 11 HTML skills; activation-routing redesign; Acta record visual redesign; npm runtime dependencies; browser-initiated file writes; auto-acceptance; any commit/publication; declaring cognitive gates passed.

---

# Implementation plan (vertical slices)

1. **Core state/export (TDD):** tests for deriveStatus/buildCandidate/per-kind derives + the five stale-export patterns → implement `export-core.mjs`.
2. **Materializer + shared runtime:** `base.css`, `runtime.js`, `materialize-acta2.mjs` (+ npm scripts, check.mjs wiring); determinism tests.
3. **Instrument A (reference): three-code-paths** — topology, body renderer, wiring, scaffold + realistic fixture data; validator v2 first cut; self-test green.
4. **Instrument B: build-with-notes** — board topology, open STOP fixture.
5. **Instrument C: concept-lab** — model topology (deterministic backoff model), SVG timeline, consequence table.
6. **Records:** record renderers + accepted fixtures for all three.
7. **SKILL.md updates** (three pilots) with the v2 loop and instrument brief.
8. **QA:** validator completion, fixture-realism tests, full `npm run check`, headless renders (desktop/mobile/print/no-JS).
9. **Evaluation pack** produced outside the repository (not a release artifact)
   + final two-axis review.
