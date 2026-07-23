/* Static renderer for the find-the-cause instrument (Node-side).
   A falsifiable-hypothesis board: the symptom leads, a causal map shows
   where each hypothesis attacks, and every hypothesis card carries its
   probe, its observation, and an explicit verdict — validated, falsified,
   or still open. The diagnosis conclusion is required before export;
   elimination is never automatic. */

import { renderFlow } from "./flow.mjs";

export function renderBody(data, { esc }) {
  const map = renderFlow(data.causalMap.flow, esc, { ariaLabel: "Causal map for the symptom" });

  const facts = data.facts
    .map(
      (fact) =>
        `<div class="ftc-fact"><b>${esc(fact.value)}</b><span>${esc(fact.label)}</span></div>`,
    )
    .join("\n");

  const hypotheses = data.items
    .map((item, index) => {
      const verdicts = data.verdicts
        .map(
          (verdict) =>
            `<label class="a2-choice ftc-verdict is-${esc(verdict.tone)}"><input type="radio" name="acta2-mark-${esc(item.id)}" value="${esc(verdict.id)}" data-mark-item="${esc(item.id)}"><span>${esc(verdict.label)}</span></label>`,
        )
        .join("\n");
      return `
<article class="ftc-hypothesis" data-item="${esc(item.id)}" aria-labelledby="ftc-t-${esc(item.id)}">
<p class="h-head"><span class="h-n">H${index + 1}</span><span class="h-title" id="ftc-t-${esc(item.id)}">${esc(item.label)}</span></p>
<div class="h-rows">
<div class="h-row"><span class="h-k">Predicts</span><p>${esc(item.predicts)}</p></div>
<div class="h-row"><span class="h-k">Probe</span><p>${esc(item.probe)}</p></div>
<div class="h-row"><span class="h-k">Observed</span><p>${esc(item.observed)}</p></div>
<div class="h-row"><span class="h-k">Evidence</span><p>${item.evidence.map((location) => `<span class="ftc-loc">${esc(location)}</span>`).join("")}</p></div>
</div>
<div class="h-verdicts" role="group" aria-label="Verdict for hypothesis ${index + 1}">
${verdicts}
</div>
</article>`;
    })
    .join("\n");

  return `
<h1 class="ftc-question">${esc(data.question)}</h1>
<p class="ftc-lede">${esc(data.lede)}</p>
<div class="ftc-facts" aria-label="Symptom at a glance">
${facts}
</div>
<section class="ftc-map" aria-label="Causal map">
<h2>Where each hypothesis attacks</h2>
<div class="ftc-mapcard">
<div class="plotwrap">${map.svg}</div>
<p class="flowd-caption">${esc(data.causalMap.caption)}</p>
</div>
</section>
<section class="ftc-board" aria-label="Hypothesis board">
<h2>Hypotheses</h2>
<p class="ftc-boardline"><span class="a2-status" data-bind="status-label">In review — give every hypothesis a verdict</span><span class="ftc-count" data-bind="marks-line">0 of ${data.items.length} hypotheses judged</span></p>
${hypotheses}
</section>
<section class="ftc-conclude" aria-label="Diagnosis">
<h2>Diagnosis</h2>
<p class="ftc-concludenote">${esc(data.conclusionNote)}</p>
<label class="a2-field"><span>Diagnosis (required for export)</span><textarea rows="3" data-working="conclusion" placeholder="${esc(data.conclusionPlaceholder)}"></textarea></label>
<div class="x-actions">
<button type="button" class="a2-btn" data-acta2-reset>Reset board</button>
</div>
<p class="a2-jsnote">JavaScript is off, so verdict controls are disabled. Every hypothesis, probe, and observation stays readable above; judge them in chat instead — for example: “H2 validated, H1 and H3 falsified — diagnosis: …”.</p>
<p class="ftc-silence">Judging here only prepares a candidate. The diagnosis becomes canonical when you confirm the pasted candidate in chat — silence never approves, and no hypothesis is ever auto-eliminated.</p>
</section>`;
}
