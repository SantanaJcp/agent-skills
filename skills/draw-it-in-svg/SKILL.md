---
name: draw-it-in-svg
description: "Create accessible standalone SVG illustrations and an Acta figure sheet with copyable source. Use for requests such as turn this explanation into a labeled vector diagram that works outside the report, even when the source explanation still needs to be requested; activate first, then ask for missing content. Do not use for process-flow analysis or raster image generation."
license: Apache-2.0
metadata:
  tags: "svg, illustration, visualization"
---

# Draw It In SVG

## Purpose

Produce vector figures that work both inside an Acta sheet and as independent SVG files.

Read [the Acta v2 protocol](references/acta2-protocol.md). Artifacts are **generated from structured JSON, never hand-edited**: author every figure as constrained vector data in `scenario.json` (whitelisted elements only — real drawing, no markup sink; each figure carries its own title, description, and caption) and run [the bundled generator](references/acta2/generate-instrument.mjs); the sheet takes an explicit per-figure verdict, and after acceptance `canonical.json` + [the record generator](references/acta2/generate-record.mjs) emit the accepted figure sheet. The Acta 0.1 recipe ([acta-protocol.md](references/acta-protocol.md), [acta-scaffold.html](references/acta-scaffold.html)) remains only as rollback until the v2 migration is approved.

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
