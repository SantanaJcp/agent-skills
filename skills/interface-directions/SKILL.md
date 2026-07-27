---
name: interface-directions
description: "Explore three genuinely different product interface directions using the same scenario, then compare tradeoffs and make a clear choice. Use when layout, density, hierarchy, tone, or behavior needs a decision; do not use for backend or code-architecture choices."
license: Apache-2.0
metadata:
  tags: "design, interface, comparison"
---

# Interface Directions

## Purpose

Resolve a product-interface direction before implementation planning. A shared report frame must not make the candidate interfaces look alike.

Read [the interactive artifact protocol](references/acta2-protocol.md). Artifacts are **generated from structured JSON, never hand-edited**: write `scenario.json` (shared dataset, three direction mockups, tradeoffs, matrix, recommendation) and run [the bundled generator](references/acta2/generate-instrument.mjs); after acceptance, write `canonical.json` and run [the record generator](references/acta2/generate-record.mjs). [instrument.html](references/instrument.html) and [record.html](references/record.html) are rendered examples.

## Process

1. **Verify applicability.** Identify the unresolved user-facing decision and read product constraints, current UI, design tokens, accessibility rules, and prior code-path choice. Completion: the decision materially concerns layout, density, hierarchy, tone, or behavior. If not, stop without manufacturing UI work.
2. **Choose comparison axes.** State the audience, task, device/context, information priority, interaction model, and success criteria. Completion: axes can distinguish directions through behavior, not decoration alone.
3. **Create distinct directions as data.** Author three direction mockups in `scenario.json` — every direction renders the IDENTICAL dataset through a different philosophy (thesis line, mockup fields, tradeoffs). Shared report styling stays in the surrounding chrome; the mockup world carries its own neutral product styling. Completion: removing colors still leaves distinct hierarchy or behavior, and deleting any direction removes a real choice.
4. **Compare honestly.** For each direction record the task flow, responsive behavior, accessibility implications, implementation consequences, risks, strengths, and change conditions. Completion: every candidate has the same evidence shape.
5. **Open the decision gate.** Generate the instrument (`node <skill>/references/acta2/generate-instrument.mjs --scenario scenario.json --out instrument.html`), let the human react to the rendered directions and select one; the pasted candidate export (or an unambiguous chat selection) is the only path to acceptance. Completion: one direction is explicitly accepted in chat, then `canonical.json` + `node <skill>/references/acta2/generate-record.mjs --canonical canonical.json --out record.html` emit the durable record.
6. **Handoff.** Export target behavior, hierarchy, responsive rules, reusable tokens/components, rejected directions, and unresolved details as blueprint input. Never implement or invoke the next skill automatically.

## Guardrails

- Do not apply report-shell tokens to product candidates unless the product itself uses them.
- Do not present three cosmetic themes over the same structure.
- Keep candidate controls demonstrative; do not connect them to production data or services.
