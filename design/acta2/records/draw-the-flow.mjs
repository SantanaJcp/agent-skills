/* Record body for draw-the-flow: the verified flow drawing, its complete
   textual equivalent, and the verification decision. Path emphasis was
   ephemeral view state and is deliberately absent here. */

import { renderFlow } from "../lib/flow.mjs";

export function renderRecord(data, accepted, { esc }) {
  const flow = renderFlow(data.flow, esc, { ariaLabel: data.flow.ariaLabel });
  const decision = accepted.decisions[0];

  return `
<section class="acta-section" aria-labelledby="verdict-title">
<h2 id="verdict-title" class="acta-h2">Verification</h2>
<div class="r-aside"><span class="r-k">Decision ${esc(decision.id)}</span>
<p><strong>${esc(decision.selection)}</strong> — ${esc(data.question)}</p>
<p>Rationale: ${esc(decision.rationale ?? "none volunteered")}. Accepted via ${esc(decision.acceptedVia)}.</p>
</div>
</section>
<section class="acta-section" aria-labelledby="flow-title">
<h2 id="flow-title" class="acta-h2">The flow</h2>
<div class="plotwrap">${flow.svg}</div>
<p class="flowd-caption">${esc(data.flow.caption)}</p>
</section>
<section class="acta-section" aria-labelledby="paths-title">
<h2 id="paths-title" class="acta-h2">The same flow, in words</h2>
${data.pathViews
    .filter((view) => view.id !== "all")
    .map(
      (view) => `
<h3 class="acta-h3">${esc(view.label)}</h3>
<ol>
${view.steps.map((step) => `<li>${esc(step)}</li>`).join("\n")}
</ol>`,
    )
    .join("\n")}
</section>
<section class="acta-section" aria-labelledby="unresolved-title">
<h2 id="unresolved-title" class="acta-h2">Unresolved at acceptance</h2>
<ul>${(data.unresolved ?? []).map((item) => `<li>${esc(item)}</li>`).join("") || "<li>nothing recorded</li>"}</ul>
</section>`;
}
