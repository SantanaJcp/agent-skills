/* Static renderer for the draw-it-in-svg instrument (Node-side).
   A figure sheet under review: every figure is authored vector data rendered
   through the constrained lib/figure.mjs vocabulary (real drawing, no markup
   sink), carries its own title/desc, shows its copyable source, and takes an
   explicit per-figure verdict. The sheet is accepted figure by figure, not
   with one global nod. */

import { renderFigure } from "./figure.mjs";

export function renderBody(data, { esc }) {
  const figures = data.items
    .map((item, index) => {
      const rendered = renderFigure(item.figure, esc);
      const verdicts = data.verdicts
        .map(
          (verdict) =>
            `<label class="a2-choice dis-verdict"><input type="radio" name="acta2-mark-${esc(item.id)}" value="${esc(verdict.id)}" data-mark-item="${esc(item.id)}"><span>${esc(verdict.label)}</span></label>`,
        )
        .join("\n");
      return `
<article class="dis-figure" data-item="${esc(item.id)}" aria-labelledby="dis-t-${esc(item.id)}">
<div class="f-head">
<span class="f-n">${String(index + 1).padStart(2, "0")}</span>
<div class="f-titles">
<h2 id="dis-t-${esc(item.id)}">${esc(item.label)}</h2>
<p class="f-desc">${esc(item.figure.desc)}</p>
</div>
</div>
<div class="f-stage">
${rendered.svg}
</div>
<p class="f-caption">${esc(item.figure.caption ?? "")}</p>
<div class="f-actions">
<div class="f-verdicts" role="group" aria-label="Verdict for ${esc(item.label)}">
${verdicts}
</div>
<button type="button" class="a2-btn" data-copy-text-from="dis-src-${esc(item.id)}" data-copy-label="SVG source for ${esc(item.label)}">Copy SVG source</button>
</div>
<details class="a2-more"><summary>SVG source (standalone, self-describing)</summary><div>
<div class="codewrap"><pre id="dis-src-${esc(item.id)}"><code>${esc(rendered.source)}</code></pre></div>
</div></details>
</article>`;
    })
    .join("\n");

  return `
<h1 class="dis-question">${esc(data.question)}</h1>
<p class="dis-lede">${esc(data.lede)}</p>
<p class="dis-progress"><span class="a2-status" data-bind="status-label">In review — give every figure a verdict</span><span class="dis-count" data-bind="marks-line">0 of ${data.items.length} figures marked</span></p>
${figures}
<section class="dis-close" aria-label="Sheet conclusion">
<h2>Sheet verdict</h2>
<p class="dis-closenote">Every figure needs a verdict before the sheet can export. Figures marked “needs revision” return to the drawing board with your notes.</p>
<label class="a2-field"><span>Notes (optional, exported)</span><textarea rows="2" data-working="conclusion" placeholder="Revision notes or acceptance context, in your words"></textarea></label>
<div class="x-actions">
<button type="button" class="a2-btn" data-acta2-reset>Reset verdicts</button>
</div>
<p class="a2-jsnote">JavaScript is off, so verdict and copy controls are disabled. Every figure and its SVG source remain readable above; give verdicts in chat instead — for example: “fig-dataflow: approve; fig-seams: revise — arrowheads too heavy”.</p>
</section>`;
}
