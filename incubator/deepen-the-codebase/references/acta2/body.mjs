/* Static renderer for the deepen-the-codebase instrument (Node-side).
   Architecture comparison without refactoring: the CURRENT module map leads,
   then each candidate direction shows its own dependency-direction diagram,
   evidence locations, and cost/benefit at equal fidelity. The chosen
   direction carries a change-blueprint seed into the record — analysis here,
   implementation never. */

import { renderFlow } from "./flow.mjs";

export function renderBody(data, { esc }) {
  const current = renderFlow(data.currentMap.flow, esc, { ariaLabel: "Current module map" });

  const directions = data.options
    .map((option) => {
      const flow = renderFlow(option.flow, esc, { ariaLabel: `Dependency direction for ${option.label}` });
      return `
<section class="dcb-direction" data-option="${esc(option.id)}" aria-labelledby="dcb-t-${esc(option.id)}">
<div class="d-head">
<span class="d-id" aria-label="Direction ${esc(option.id.toUpperCase())}">${esc(option.id.toUpperCase())}</span>
<h2 id="dcb-t-${esc(option.id)}">${esc(option.label)}</h2>
</div>
<p class="d-claim">${esc(option.claim)}</p>
<div class="dcb-cols">
<div class="dcb-flowside">
<div class="plotwrap">${flow.svg}</div>
<p class="flowd-caption">${esc(option.flowCaption)}</p>
</div>
<div class="dcb-notes">
<p class="dcb-k">Evidence</p>
<p class="dcb-evidence">${option.evidence.map((location) => `<span class="dcb-loc">${esc(location)}</span>`).join("")}</p>
<p class="dcb-k">Wins</p>
<ul class="dcb-list is-pro">${option.pros.map((item) => `<li>${esc(item)}</li>`).join("")}</ul>
<p class="dcb-k">Costs</p>
<ul class="dcb-list is-con">${option.cons.map((item) => `<li>${esc(item)}</li>`).join("")}</ul>
<p class="dcb-k">Blueprint seed if chosen</p>
<p class="dcb-seed">${esc(option.blueprintSeed)}</p>
<label class="a2-choice dcb-select"><input type="radio" name="acta2-option" value="${esc(option.id)}"><span>Choose ${esc(option.label)}</span></label>
</div>
</div>
</section>`;
    })
    .join("\n");

  const recommended = data.options.find((option) => option.id === data.recommendation.option);

  return `
<h1 class="dcb-question">${esc(data.question)}</h1>
<p class="dcb-lede">${esc(data.lede)}</p>
<section class="dcb-current" aria-label="Current module map">
<h2>The codebase as it stands</h2>
<div class="dcb-currentcard">
<div class="plotwrap">${current.svg}</div>
<p class="flowd-caption">${esc(data.currentMap.caption)}</p>
</div>
</section>
${directions}
<aside class="dcb-reco"><span class="r-k">Recommendation — after the comparison</span>${esc(
    recommended ? `${recommended.label}: ` : "",
  )}${esc(data.recommendation.reason)}</aside>
<section class="dcb-decide" aria-label="Decision gate">
<h2>DecisionGate — open</h2>
<p class="d-selection" data-bind="selection-line">No direction selected yet.</p>
<p class="a2-status" data-bind="status-label">${esc(data.openStatusLabel)}</p>
<label class="a2-field"><span>Rationale (optional)</span><textarea rows="2" data-working="rationale" placeholder="Why this deepening direction, in your words"></textarea></label>
<div class="x-actions">
<button type="button" class="a2-btn" data-acta2-reset>Reset selection</button>
</div>
<p class="a2-jsnote">JavaScript is off, so selection controls are disabled. Decide in chat instead — for example: “deepen along direction B — rationale: …”.</p>
<p>Choosing here only prepares a candidate — analysis, never implementation. The accepted direction exports a change-blueprint seed; nothing is refactored by this instrument.</p>
</section>`;
}
