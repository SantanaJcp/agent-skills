---
name: draw-it-in-svg
description: "Create accessible standalone SVG illustrations and an Acta figure sheet with copyable source. Use when reusable vector figures communicate the idea better than prose; do not use for process-flow analysis or raster image generation."
license: Apache-2.0
metadata:
  tags: "svg, illustration, visualization"
---

# Draw It In SVG

## Purpose

Produce vector figures that work both inside an Acta sheet and as independent SVG files.

Read [the Acta artifact protocol](references/acta-protocol.md) and use [the Explore scaffold](references/acta-scaffold.html).

## Process

1. Clarify the communication goal, audience, figure set, dimensions, color constraints, labels, and reuse context.
2. Write `figure-sheet.md` with one purpose statement and interpretation per figure.
3. Create each file under `figures/` as standalone SVG: own viewBox, title, description, definitions, styles, and no external resources. Use semantic grouping and keep text legible in monochrome.
4. Generate `view.html` with one Acta figure block per SVG, dimensions/palette metadata, caption, textual equivalent, and a safe copy-source control backed by the complete source.
5. Validate each SVG by opening or parsing it outside the sheet. Completion: every figure remains understandable and functional when copied alone.

## Guardrails

- Do not share definitions across SVG files or rely on the sheet's CSS/JavaScript.
- Do not embed scripts, remote images, webfonts, or secret data.
- Use draw-the-flow when node/edge sequence is the primary problem; use an image generator when raster art is required.
