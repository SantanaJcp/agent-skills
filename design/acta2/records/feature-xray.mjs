/* Record body for feature-xray: a source-grounded explanation dossier —
   TL;DR, system map, the operational path step by step, a usage example,
   gotchas, and FAQ. Every claim carries its evidence location. Record-only:
   nothing here changes with human action, so nothing pretends to. */

import { highlightJs } from "../lib/highlight.mjs";
import { renderFlow } from "../lib/flow.mjs";

export function renderRecord(data, accepted, { esc }) {
  const map = renderFlow(data.map, esc, { ariaLabel: "System map for the feature" });

  const steps = data.steps
    .map(
      (step, index) => `
<article class="fx-step">
<p class="fx-step-head"><span class="fx-n">${String(index + 1).padStart(2, "0")}</span><span class="fx-step-title">${esc(step.title)}</span><span class="r-loc">${esc(step.where)}</span></p>
<p class="fx-step-body">${esc(step.what)}</p>
</article>`,
    )
    .join("\n");

  return `
<section class="acta-section" aria-labelledby="tldr-title">
<h2 id="tldr-title" class="acta-h2">TL;DR</h2>
<div class="r-aside"><span class="r-k">Verified against source</span>
<p>${esc(data.tldr)}</p>
</div>
</section>
<section class="acta-section" aria-labelledby="map-title">
<h2 id="map-title" class="acta-h2">System map</h2>
<p>${esc(data.map.lede)}</p>
<div class="plotwrap">${map.svg}</div>
<p class="flowd-caption">${esc(data.map.caption)}</p>
</section>
<section class="acta-section" aria-labelledby="path-title">
<h2 id="path-title" class="acta-h2">The operational path, step by step</h2>
${steps}
</section>
<section class="acta-section" aria-labelledby="usage-title">
<h2 id="usage-title" class="acta-h2">Using it</h2>
<p>${esc(data.usage.lede)}</p>
<div class="a2-code"><div class="c-path">${esc(data.usage.path)}</div><div class="codewrap"><pre><code>${highlightJs(data.usage.snippet, esc)}</code></pre></div></div>
</section>
<section class="acta-section" aria-labelledby="gotchas-title">
<h2 id="gotchas-title" class="acta-h2">Gotchas worth knowing</h2>
<ul class="fx-gotchas">
${data.gotchas
    .map((gotcha) => `<li><strong>${esc(gotcha.lead)}</strong> ${esc(gotcha.body)}</li>`)
    .join("\n")}
</ul>
</section>
<section class="acta-section" aria-labelledby="faq-title">
<h2 id="faq-title" class="acta-h2">FAQ</h2>
${data.faq
    .map(
      (item) => `
<h3 class="acta-h3">${esc(item.q)}</h3>
<p>${esc(item.a)}</p>`,
    )
    .join("\n")}
</section>`;
}
