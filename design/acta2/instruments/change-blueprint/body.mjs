/* Static renderer for the change-blueprint instruments (Node-side).
   One renderer serves both gate moments, driven by scenario data:
     gatePhase "spec" — Gate A: does the specification say what we will
       build and what we will not?
     gatePhase "plan" — Gate B: will this plan build the accepted spec
       safely? (slices timeline, data-flow diagram, risky code island,
       risks, tests, rollout/rollback)
   Both end in the same deliberate resolution gate; acceptance stays in chat. */

import { highlightJs } from "../../lib/highlight.mjs";
import { renderFlow } from "../../lib/flow.mjs";

function factStrip(facts, esc) {
  return `<div class="cb-facts" aria-label="Plan facts">
${facts
    .map(
      (fact) =>
        `<div class="cb-fact"><b>${esc(fact.value)}</b><span>${esc(fact.label)}</span>${
          fact.sub ? `<small>${esc(fact.sub)}</small>` : ""
        }</div>`,
    )
    .join("\n")}
</div>`;
}

function gateSection(data, esc) {
  const choices = data.options
    .map(
      (option) => `
<label class="a2-choice"><input type="radio" name="acta2-option" value="${esc(option.id)}">
<span class="c-label">${esc(option.label)}</span>
<span class="c-consequence">${esc(option.consequence)}</span></label>`,
    )
    .join("\n");
  return `<section class="cb-gate" aria-labelledby="cb-gate-title">
<div class="g-head">
<p class="g-id">${esc(data.gateLabel)} — open</p>
<p class="g-title" id="cb-gate-title">${esc(data.gateQuestion)}</p>
</div>
<div class="g-body">
<div class="cb-choices" role="group" aria-label="Gate resolutions">
${choices}
</div>
<p class="d-selection" data-bind="selection-line">No resolution proposed yet.</p>
<p class="a2-status" data-bind="status-label">${esc(data.openStatusLabel)}</p>
<label class="a2-field"><span>Rationale (optional)</span><textarea rows="2" data-working="rationale" placeholder="Why this resolution, in your words"></textarea></label>
<div class="x-actions">
<button type="button" class="a2-btn" data-acta2-reset>Reset resolution</button>
</div>
<p class="a2-jsnote">JavaScript is off, so resolution controls are disabled. Decide in chat instead — for example: “${esc(data.gateLabel)}: approve — rationale: …”.</p>
<p class="g-silence">Resolving here only prepares a candidate. The gate closes when you confirm the pasted candidate in chat — silence never approves.</p>
</div>
</section>`;
}

function specSections(data, esc) {
  return `
<section class="cb-scope" aria-label="Scope and non-goals">
<div class="cb-cols">
<div class="cb-col is-in">
<h2><span class="col-mark" aria-hidden="true">✓</span>In scope</h2>
<ul>${data.scope.map((item) => `<li>${esc(item)}</li>`).join("\n")}</ul>
</div>
<div class="cb-col is-out">
<h2><span class="col-mark" aria-hidden="true">✗</span>Non-goals</h2>
<ul>${data.nonGoals.map((item) => `<li>${esc(item)}</li>`).join("\n")}</ul>
</div>
</div>
</section>
<section class="cb-criteria" aria-label="Acceptance criteria">
<h2>Acceptance criteria</h2>
<ol class="cb-crit">
${data.acceptanceCriteria.map((item, index) => `<li><span class="crit-n">${String(index + 1).padStart(2, "0")}</span><span class="crit-t">${esc(item)}</span></li>`).join("\n")}
</ol>
</section>
<section class="cb-assumptions" aria-label="Open assumptions">
<h2>Assumptions this spec leans on</h2>
<ul class="cb-assume">${data.assumptions.map((item) => `<li>${esc(item)}</li>`).join("\n")}</ul>
</section>`;
}

function planSections(data, esc) {
  const slices = data.slices
    .map(
      (slice, index) => `
<li class="cb-slice">
<span class="sl-window">${esc(slice.window)}</span>
<span class="sl-dot${index === 0 ? " is-first" : ""}" aria-hidden="true"></span>
<div class="sl-body">
<p class="sl-title">${esc(slice.title)}</p>
<p class="sl-detail">${esc(slice.detail)}</p>
<p class="sl-touches">${slice.touches.map((chip) => `<span class="cb-chip">${esc(chip)}</span>`).join("")}</p>
</div>
</li>`,
    )
    .join("\n");

  const flow = renderFlow(data.flow, esc, { ariaLabel: "Data flow for the planned change" });

  const risks = data.risks
    .map(
      (risk) => `<tr>
<td>${esc(risk.risk)}</td>
<td><span class="cb-sev is-${esc(risk.likelihood)}">${esc(risk.likelihood)}</span></td>
<td>${esc(risk.mitigation)}</td>
</tr>`,
    )
    .join("\n");

  return `
<section class="cb-context" aria-label="Accepted specification context">
<p class="ctx-seal"><span class="cb-sealed">Gate A · accepted</span>${esc(data.specContext.acceptedVia)}</p>
<p class="ctx-summary">${esc(data.specContext.summary)}</p>
</section>
<section class="cb-slices" aria-label="Slices">
<h2><span class="sn">01</span>Slices</h2>
<p class="cb-sectionlede">${esc(data.slicesLede)}</p>
<ol class="cb-timeline">
${slices}
</ol>
</section>
<section class="cb-flowsec" aria-label="Data flow">
<h2><span class="sn">02</span>Data flow</h2>
<p class="cb-sectionlede">${esc(data.flow.lede)}</p>
<div class="cb-flowcard"><div class="plotwrap">${flow.svg}</div>
<p class="flowd-caption">${esc(data.flow.caption)}</p></div>
</section>
<section class="cb-risky" aria-label="Riskiest code surface">
<h2><span class="sn">03</span>Riskiest code surface</h2>
<p class="cb-sectionlede">${esc(data.riskyCode.lede)}</p>
<div class="a2-code"><div class="c-path">${esc(data.riskyCode.path)}</div><div class="codewrap"><pre><code>${highlightJs(data.riskyCode.snippet, esc)}</code></pre></div></div>
</section>
<section class="cb-risks" aria-label="Risks">
<h2><span class="sn">04</span>Risks and mitigations</h2>
<div class="tablewrap"><table class="cb-risktable">
<thead><tr><th scope="col">Risk</th><th scope="col">Likelihood</th><th scope="col">Mitigation</th></tr></thead>
<tbody>
${risks}
</tbody>
</table></div>
</section>
<section class="cb-tests" aria-label="Test plan and rollout">
<h2><span class="sn">05</span>Tests, rollout, rollback</h2>
<div class="cb-cols">
<div class="cb-col">
<h3>Proves it works</h3>
<ul>${data.tests.map((item) => `<li>${esc(item)}</li>`).join("\n")}</ul>
</div>
<div class="cb-col">
<h3>Rollout → rollback</h3>
<ul>${data.rollout.map((item) => `<li>${esc(item)}</li>`).join("\n")}</ul>
<ul class="cb-rollback">${data.rollback.map((item) => `<li>${esc(item)}</li>`).join("\n")}</ul>
</div>
</div>
</section>`;
}

export function renderBody(data, { esc }) {
  const phase = data.gatePhase;
  return `
<h1 class="cb-question">${esc(data.question)}</h1>
<p class="cb-lede">${esc(data.lede)}</p>
${factStrip(data.facts, esc)}
${phase === "spec" ? specSections(data, esc) : planSections(data, esc)}
${gateSection(data, esc)}`;
}
