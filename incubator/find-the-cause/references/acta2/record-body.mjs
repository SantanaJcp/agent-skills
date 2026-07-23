/* Record body for find-the-cause: the accepted diagnosis — the validated
   cause, the causal map, and every hypothesis with its probe, observation,
   and verdict. Falsified hypotheses are preserved, not deleted. */

import { renderFlow } from "./flow.mjs";

export function renderRecord(data, accepted, { esc }) {
  const marks = accepted.exampleWorking.marks;
  const map = renderFlow(data.causalMap.flow, esc, { ariaLabel: "Causal map for the symptom" });
  const verdictById = Object.create(null);
  for (const verdict of data.verdicts) verdictById[verdict.id] = verdict;

  return `
<section class="acta-section" aria-labelledby="diagnosis-title">
<h2 id="diagnosis-title" class="acta-h2">Diagnosis</h2>
<div class="r-aside"><span class="r-k">Validated cause</span>
<p>${esc(accepted.exampleWorking.conclusion)}</p>
<p>Accepted via ${esc(accepted.decisions[0].acceptedVia)}.</p>
</div>
<div class="r-facts">
${data.facts.map((fact) => `<div class="r-fact"><b>${esc(fact.value)}</b><span>${esc(fact.label)}</span></div>`).join("\n")}
</div>
</section>
<section class="acta-section" aria-labelledby="map-title">
<h2 id="map-title" class="acta-h2">Causal map</h2>
<div class="plotwrap">${map.svg}</div>
<p class="flowd-caption">${esc(data.causalMap.caption)}</p>
</section>
<section class="acta-section" aria-labelledby="board-title">
<h2 id="board-title" class="acta-h2">Hypotheses, as judged</h2>
${data.items
    .map((item, index) => {
      const mark = marks[item.id];
      const verdict = verdictById[mark];
      return `
<article class="ftc-r-hypothesis" data-verdict="${esc(mark)}">
<h3 class="acta-h3"><span class="ftc-r-n">H${index + 1}</span>${esc(item.label)} <span class="ftc-r-verdict is-${esc(verdict?.tone ?? "plain")}">${esc(verdict?.label ?? mark)}</span></h3>
<div class="r-tagrow"><span class="r-tag">Predicts</span><span class="r-val">${esc(item.predicts)}</span></div>
<div class="r-tagrow"><span class="r-tag">Probe</span><span class="r-val">${esc(item.probe)}</span></div>
<div class="r-tagrow"><span class="r-tag">Observed</span><span class="r-val">${esc(item.observed)}</span></div>
<p>${item.evidence.map((location) => `<span class="r-loc">${esc(location)}</span>`).join("")}</p>
</article>`;
    })
    .join("\n")}
</section>
<section class="acta-section" aria-labelledby="unresolved-title">
<h2 id="unresolved-title" class="acta-h2">Deliberately out of scope</h2>
<ul>${(data.unresolved ?? []).map((item) => `<li>${esc(item)}</li>`).join("") || "<li>nothing recorded</li>"}</ul>
</section>`;
}
