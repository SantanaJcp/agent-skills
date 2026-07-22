---
name: three-code-paths
description: "Compare exactly three structurally distinct code approaches at equal fidelity and record an explicit choice. Use when a change has a real implementation-shape decision; do not use for cosmetic variants, interface styling, or direct implementation."
license: Apache-2.0
metadata:
  tags: "architecture, comparison, planning"
---

# Three Code Paths

## Purpose

Answer an implementation-shape question with three genuinely different code paths before planning the chosen path.

Read [the Acta artifact protocol](references/acta-protocol.md) and use [the Compare scaffold](references/acta-scaffold.html).

## Process

1. **Ground the decision.** Read project instructions, domain context, ADRs, the relevant code, tests, and any prior realization. Write `code-paths.md` with the decision, constraints, evidence, and evaluation dimensions. Completion: the one load-bearing structural question is explicit.
2. **Construct exactly three paths.** Each path must change a consequential seam, interface, state model, dependency direction, or delivery shape and state the distinct question it answers. Cosmetic or renamed versions do not count. Completion: deleting any path would remove a real choice.
3. **Make paths concrete at equal fidelity.** For every path include the same dimensions: shape, decision-rich interface/snippet/diff, data flow, affected modules, test seam, migration/rollout, benefits, costs, failure modes, and change conditions. Completion: no path is favored by detail level.
4. **Prototype only when evidence cannot decide.** Put disposable work under this skill's workspace, never production paths. Test the narrow uncertainty, record the result, and remove or clearly mark the prototype. Completion: the prototype answers one named question.
5. **Recommend after comparison.** Build the matrix first, then state the recommended path and why it wins under the declared dimensions. Completion: recommendation follows evidence rather than framing it.
6. **Open DecisionGate D-01.** Generate `view.html`, accept an explicit choice in chat or export, and normalize it into the Markdown record and `decision.json`. A rationale is optional. Completion: the chosen path is `approved`; otherwise remain `awaiting-decision`.
7. **Handoff.** Export the chosen path, rejected alternatives, change conditions, and evidence as planning input. Recommend interface exploration when the change has a visual interaction decision; otherwise recommend blueprinting. Never invoke the next skill automatically.

## Guardrails

- Do not modify production code or turn the preferred path into an implementation.
- Do not force minimal/balanced/ambitious archetypes when the context has better structural axes.
- Keep the essential comparison readable without JavaScript and printable in sequence.
