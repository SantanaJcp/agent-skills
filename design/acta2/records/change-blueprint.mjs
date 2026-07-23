/* Record body for change-blueprint: the accepted blueprint — spec contract,
   slice plan, data flow, risks, and both gate decisions — rendered from the
   accepted plan scenario (which embeds the Gate A spec context). */

import { highlightJs } from "../lib/highlight.mjs";
import { renderFlow } from "../lib/flow.mjs";

export function renderRecord(data, accepted, { esc }) {
  const gateB = accepted.decisions.find((decision) => decision.id === "gate-b-plan") ?? accepted.decisions[0];
  const gateA = accepted.decisions.find((decision) => decision.id === "gate-a-spec");
  const flow = renderFlow(data.flow, esc, { ariaLabel: "Accepted data flow for the change" });

  return `
<section class="acta-section" aria-labelledby="gates-title">
<h2 id="gates-title" class="acta-h2">Accepted gates</h2>
${gateA ? `<div class="r-aside"><span class="r-k">Gate A — specification</span>
<p>${esc(data.specContext.summary)}</p>
<p>Rationale: ${esc(gateA.rationale ?? "none volunteered")}. Accepted via ${esc(gateA.acceptedVia)}.</p>
</div>` : ""}
<div class="r-aside"><span class="r-k">Gate B — implementation plan</span>
<p><strong>${esc(gateB.selection)}</strong> — ${esc(data.gateQuestion)}</p>
<p>Rationale: ${esc(gateB.rationale ?? "none volunteered")}. Accepted via ${esc(gateB.acceptedVia)}.</p>
</div>
<div class="r-facts">
${data.facts.map((fact) => `<div class="r-fact"><b>${esc(fact.value)}</b><span>${esc(fact.label)}</span>${fact.sub ? `<small>${esc(fact.sub)}</small>` : ""}</div>`).join("\n")}
</div>
</section>
<section class="acta-section" aria-labelledby="slices-title">
<h2 id="slices-title" class="acta-h2">Slice plan</h2>
<p>${esc(data.slicesLede)}</p>
<div class="tablewrap"><table class="r-table">
<thead><tr><th scope="col">Slice</th><th scope="col">Delivers</th><th scope="col">Touches</th></tr></thead>
<tbody>
${data.slices
    .map(
      (slice) => `<tr><th scope="row">${esc(slice.window)}</th><td><strong>${esc(slice.title)}</strong><br>${esc(slice.detail)}</td><td>${slice.touches
        .map((chip) => `<span class="r-loc">${esc(chip)}</span>`)
        .join("")}</td></tr>`,
    )
    .join("\n")}
</tbody>
</table></div>
</section>
<section class="acta-section" aria-labelledby="flow-title">
<h2 id="flow-title" class="acta-h2">Data flow</h2>
<p>${esc(data.flow.lede)}</p>
<div class="plotwrap">${flow.svg}</div>
<p class="flowd-caption">${esc(data.flow.caption)}</p>
</section>
<section class="acta-section" aria-labelledby="risky-title">
<h2 id="risky-title" class="acta-h2">Riskiest code surface</h2>
<p>${esc(data.riskyCode.lede)}</p>
<div class="a2-code"><div class="c-path">${esc(data.riskyCode.path)}</div><div class="codewrap"><pre><code>${highlightJs(data.riskyCode.snippet, esc)}</code></pre></div></div>
</section>
<section class="acta-section" aria-labelledby="risks-title">
<h2 id="risks-title" class="acta-h2">Risks, tests, rollback</h2>
<div class="tablewrap"><table class="r-table">
<thead><tr><th scope="col">Risk</th><th scope="col">Likelihood</th><th scope="col">Mitigation</th></tr></thead>
<tbody>
${data.risks
    .map((risk) => `<tr><td>${esc(risk.risk)}</td><td>${esc(risk.likelihood)}</td><td>${esc(risk.mitigation)}</td></tr>`)
    .join("\n")}
</tbody>
</table></div>
<h3 class="acta-h3">Proof</h3>
<ul>${data.tests.map((item) => `<li>${esc(item)}</li>`).join("")}</ul>
<h3 class="acta-h3">Rollout, then rollback</h3>
<ul>${data.rollout.map((item) => `<li>${esc(item)}</li>`).join("")}</ul>
<div class="r-warn"><span class="r-k">Rollback</span>
<ul>${data.rollback.map((item) => `<li>${esc(item)}</li>`).join("")}</ul>
</div>
</section>
<section class="acta-section" aria-labelledby="unresolved-title">
<h2 id="unresolved-title" class="acta-h2">Unresolved at acceptance</h2>
<ul>${(data.unresolved ?? []).map((item) => `<li>${esc(item)}</li>`).join("") || "<li>nothing recorded</li>"}</ul>
</section>`;
}
