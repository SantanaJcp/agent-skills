/* Record body for deepen-the-codebase: the accepted direction with its
   dependency diagram and blueprint seed, plus preserved alternatives.
   Analysis record only — nothing was implemented. */

import { renderFlow } from "../lib/flow.mjs";

export function renderRecord(data, accepted, { esc }) {
  const decision = accepted.decisions[0];
  const chosen = data.options.find((option) => option.id === decision.selection);
  const rejected = data.options.filter((option) => option.id !== decision.selection);
  const current = renderFlow(data.currentMap.flow, esc, { ariaLabel: "Module map before deepening" });
  const chosenFlow = chosen ? renderFlow(chosen.flow, esc, { ariaLabel: `Accepted direction: ${chosen.label}` }) : null;

  return `
<section class="acta-section" aria-labelledby="decision-title">
<h2 id="decision-title" class="acta-h2">Accepted direction</h2>
<div class="r-aside"><span class="r-k">Decision ${esc(decision.id)}</span>
<p><strong>${esc(chosen ? chosen.label : decision.selection)}</strong> — ${esc(chosen ? chosen.claim : "")}</p>
<p>Rationale: ${esc(decision.rationale ?? "none volunteered")}. Accepted via ${esc(decision.acceptedVia)}.</p>
</div>
${chosenFlow ? `<div class="plotwrap">${chosenFlow.svg}</div>
<p class="flowd-caption">${esc(chosen.flowCaption)}</p>` : ""}
<div class="r-warn"><span class="r-k">Blueprint seed — handed to change-blueprint</span>
<p>${esc(chosen ? chosen.blueprintSeed : "")}</p>
</div>
</section>
<section class="acta-section" aria-labelledby="current-title">
<h2 id="current-title" class="acta-h2">The map this analysis started from</h2>
<div class="plotwrap">${current.svg}</div>
<p class="flowd-caption">${esc(data.currentMap.caption)}</p>
</section>
<section class="acta-section" aria-labelledby="rejected-title">
<h2 id="rejected-title" class="acta-h2">Rejected directions — preserved</h2>
${rejected
    .map(
      (option) => `
<article>
<h3 class="acta-h3">${esc(option.label)}</h3>
<p>${esc(option.claim)}</p>
<p><strong>Would win when:</strong></p>
<ul>${option.pros.map((item) => `<li>${esc(item)}</li>`).join("")}</ul>
<p><strong>Cost that lost the comparison:</strong></p>
<ul>${option.cons.map((item) => `<li>${esc(item)}</li>`).join("")}</ul>
</article>`,
    )
    .join("\n")}
</section>
<section class="acta-section" aria-labelledby="unresolved-title">
<h2 id="unresolved-title" class="acta-h2">Unresolved at acceptance</h2>
<ul>${(data.unresolved ?? []).map((item) => `<li>${esc(item)}</li>`).join("") || "<li>nothing recorded</li>"}</ul>
</section>`;
}
