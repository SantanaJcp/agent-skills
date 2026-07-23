/* Record body for draw-it-in-svg: the accepted figure sheet — each figure
   re-rendered from the same authored vector data, its verdict, and its
   standalone source behind a disclosure (records carry no controls; print
   opens disclosures). */

import { renderFigure } from "./figure.mjs";

export function renderRecord(data, accepted, { esc }) {
  const marks = accepted.exampleWorking.marks;
  const verdictById = Object.create(null);
  for (const verdict of data.verdicts) verdictById[verdict.id] = verdict;

  const figures = data.items
    .map((item, index) => {
      const rendered = renderFigure(item.figure, esc);
      const mark = marks[item.id];
      const verdict = verdictById[mark];
      return `
<article class="dis-r-figure" data-verdict="${esc(mark)}">
<h3 class="acta-h3"><span class="dis-r-n">${String(index + 1).padStart(2, "0")}</span>${esc(item.label)} <span class="dis-r-verdict is-${esc(verdict?.tone ?? "plain")}">${esc(verdict?.label ?? mark)}</span></h3>
<p>${esc(item.figure.desc)}</p>
<div class="dis-r-stage">${rendered.svg}</div>
<p class="flowd-caption">${esc(item.figure.caption ?? "")}</p>
<details><summary>SVG source</summary>
<div class="codewrap"><pre><code>${esc(rendered.source)}</code></pre></div>
</details>
</article>`;
    })
    .join("\n");

  return `
<section class="acta-section" aria-labelledby="verdicts-title">
<h2 id="verdicts-title" class="acta-h2">Sheet verdicts</h2>
<div class="r-aside"><span class="r-k">Decision ${esc(accepted.decisions[0].id)}</span>
<p>${esc(accepted.summary)}</p>
<p>Rationale: ${esc(accepted.decisions[0].rationale ?? "none volunteered")}. Accepted via ${esc(accepted.decisions[0].acceptedVia)}.</p>
</div>
${accepted.exampleWorking.conclusion ? `<div class="r-warn"><span class="r-k">Revision notes</span><p>${esc(accepted.exampleWorking.conclusion)}</p></div>` : ""}
</section>
<section class="acta-section" aria-labelledby="figures-title">
<h2 id="figures-title" class="acta-h2">Figures</h2>
${figures}
</section>`;
}
