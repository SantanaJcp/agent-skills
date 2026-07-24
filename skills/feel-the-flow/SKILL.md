---
name: feel-the-flow
description: "Build a disposable interaction prototype to answer a focused experience question and export its parameters and conclusions. Use when behavior must be felt before production design; do not use to implement production UI or compare static visual directions."
license: Apache-2.0
metadata:
  tags: "prototype, interaction, design"
---

# Feel The Flow

## Purpose

Create the smallest disposable prototype that lets the user feel a behavior and decide. The output is evidence, not production code.

Read [the Acta v2 protocol](references/acta2-protocol.md). The prototype is **instrument-only and disposable by design** — no durable record exists. Write `scenario.json` (playground dataset, feel parameters, toggles) and run [the bundled generator](references/acta2/generate-instrument.mjs); only the parameters and the felt conclusion export, via the candidate the human confirms in chat. The Acta 0.1 recipe ([acta-protocol.md](references/acta-protocol.md), [acta-scaffold.html](references/acta-scaffold.html)) remains bundled as the published compatibility fallback; Acta v2 is authoritative.

## Process

1. State the one interaction question, audience, context, variables, and observable decision. If there is no behavior to feel, stop and recommend a more appropriate comparison or diagram.
2. Create the skill workspace and write `prototype-decision.md`. Build a self-contained offline `view.html` first, with controls, live region, parameter readout, and static no-script states.
3. Use a disposable copy of the real product stack only when HTML cannot answer a named fidelity risk. Keep it under the workspace, mark it nonproduction, avoid real credentials/data, and state what must not be reused.
4. Ask the user to exercise the prototype. Record observations separately from inferences and update `parameters.json` from the same state represented in Markdown.
5. Export selected parameters, rejected settings, behavioral conclusions, unanswered fidelity risks, and the next decision. Mark complete when the focused question is answered.

## Guardrails

- Do not edit production code, connect production services, or smuggle prototype code into implementation.
- Every interactive variable must have a textual value and export.
- Prefer one tight question over a broad product demo.
