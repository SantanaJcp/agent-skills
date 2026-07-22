---
name: draw-the-flow
description: "Explain a system or process as an overview-first flow with normal, decision, failure, and recovery paths plus a full textual equivalent. Use when relationships and sequence are the main question; do not use for general-purpose illustration or implementation planning."
license: Apache-2.0
metadata:
  tags: "diagram, flow, visualization"
---

# Draw The Flow

## Purpose

Create an accessible process or system flow that orients the reader before showing stage detail.

Read [the Acta artifact protocol](references/acta-protocol.md) and use [the Explore scaffold](references/acta-scaffold.html).

## Process

1. Define the audience, scope boundary, start/end, actors, evidence, and the question the flow must answer.
2. Write `flow.md` with an ordered textual model first: normal path, decisions, failure paths, retries/recovery, terminal states, and timings when known. Never invent missing transitions.
3. Build the overview figure before detail figures. Use the Acta SVG grammar, labels that survive monochrome, a legend, and timings on edges only when evidenced.
4. Give every figure a title, description, numbered caption, and complete textual equivalent. A click-to-inspect rail may enhance the view but cannot contain unique information.
5. Generate `view.html`; optionally export a standalone `flow.svg`. Verify that the Markdown alone communicates every node and edge. Completion: normal, decision, failure, and recovery paths are accounted for.

## Guardrails

- Do not use Mermaid/CDNs or require JavaScript to understand the graph.
- Do not create decorative SVG unrelated to flow; use draw-it-in-svg.
- Do not use the diagram as a substitute for an implementation plan.
