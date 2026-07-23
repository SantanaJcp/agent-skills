---
name: three-code-paths
description: "Compare exactly three structurally distinct code approaches at equal fidelity and record an explicit choice. Use when a change has a real implementation-shape decision; do not use for cosmetic variants, interface styling, or direct implementation."
license: Apache-2.0
metadata:
  tags: "architecture, comparison, planning"
---

# Three Code Paths

## Purpose

Answer an implementation-shape question with three genuinely different code paths, decided by the human inside a comparison instrument.

Read [the Acta v2 protocol](references/acta2-protocol.md). Artifacts are **generated from structured JSON, never hand-edited**: write `scenario.json` and run [the bundled generator](references/acta2/generate-instrument.mjs); after acceptance, write `canonical.json` and run [the record generator](references/acta2/generate-record.mjs). [instrument.html](references/instrument.html) and [record.html](references/record.html) are rendered examples of the outputs.

HTML earns its place here because the decision is perceptual: three alternatives must be visible **simultaneously** so the human can scan one criterion across all of them and point at one. If the question collapses to one feasible shape, skip the instrument and record the reasoning in Markdown — a fake comparison wastes attention.

## Process

1. **Ground the decision.** Read project instructions, domain context, ADRs, the relevant code, tests, and any prior realization. Start `code-paths.md` with the decision, constraints, evidence, and evaluation dimensions. Completion: the one load-bearing structural question is explicit.
2. **Write the instrument brief** into `code-paths.md` before any option prose: human question; cognitive action (compare); representation (three equal columns + criterion-major verdict matrix); what the human changes (selects a path, adds a rationale); what changes in response (column highlight, status, candidate export); first-viewport job (question + constraints + all three alternatives); export payload; no-JS equivalent (columns readable, decide in chat). Completion: the brief would let a reviewer reject the representation before long prose exists.
3. **Construct exactly three paths.** Each path must change a consequential seam, interface, state model, dependency direction, or delivery shape and state the distinct question it answers. Completion: deleting any path would remove a real choice.
4. **Fill the scenario, not an essay.** Write the comparison as data — `.agent-work/<initiative>/three-code-paths/scenario.json` (claim, decision-rich snippet, data flow, pros/costs, seams per option; failure modes and change conditions; verdict matrix; recommendation **after** the matrix) — then generate the instrument: `node <skill>/references/acta2/generate-instrument.mjs --scenario scenario.json --out instrument.html`. Never edit the HTML by hand; change the JSON and regenerate. Equal fidelity means the same fields per column, not ten paragraphs per path. Completion: the generator ran clean, all three columns fit a desktop viewport side by side, no option is preselected, and the matrix has a verdict per dimension per path.
5. **Prototype only when evidence cannot decide.** Disposable work under this skill's workspace answers one named uncertainty; record the result and remove or mark the prototype.
6. **Open DecisionGate D-01 in the instrument.** The human selects a path (and optionally a rationale) in the page and pastes the candidate export — or states the choice in chat. The browser never updates files. Completion: you hold a candidate (or an unambiguous chat selection).
7. **Accept explicitly.** Restate what will change (chosen path, rejected alternatives, their change conditions), wait for explicit confirmation, then update `code-paths.md` (+ `decision.json`) with the accepted decision. Silence keeps the gate open. Completion: canonical state carries the decision and how it was accepted.
8. **Emit the record and hand off.** Write `canonical.json` (`{ "scenario": …, "accepted": … }` — the scenario plus the accepted decision, rationale, and how it was accepted) and generate the record from it alone: `node <skill>/references/acta2/generate-record.mjs --canonical canonical.json --out record.html`. The record carries full provenance, the decision, the comparison evidence, and rejected alternatives with change conditions. Recommend interface exploration when the change has a visual interaction decision; otherwise recommend blueprinting. Never invoke the next skill automatically.

## Guardrails

- Do not modify production code or turn the preferred path into an implementation.
- Do not force minimal/balanced/ambitious archetypes when the context has better structural axes.
- The instrument shows working state only: never an approved stamp, never a pre-authored export payload.
- Keep the comparison readable without JavaScript (columns, matrix, and recommendation stay in the static DOM; the human can always decide in chat).
