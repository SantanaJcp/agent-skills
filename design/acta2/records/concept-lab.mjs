/* Record body for concept-lab: the accepted model state, the derived
   consequence at the accepted parameters, declared simplifications, sourced
   facts, and unresolved items — Acta notarial identity. The backoff math is
   imported from the shared export-core so the record always agrees with the
   instrument and the export (contract §4.1/§6). */

import { deriveBackoff } from "../lib/export-core.mjs";

function fmtParam(value, unit) {
  if (!unit) return String(value);
  if (unit === "×") return `${value}×`;
  return `${value} ${unit}`;
}

export function renderRecord(data, accepted, { esc }) {
  const decision = accepted.decisions[0];
  const working = accepted.exampleWorking;
  const backoff = deriveBackoff(working.params, working.toggles);

  const paramItems = data.params
    .map(
      (param) =>
        `<li>${esc(param.label)}: <strong>${esc(fmtParam(working.params[param.id], param.unit))}</strong></li>`,
    )
    .join("");
  const toggleItems = (data.toggles ?? [])
    .map(
      (toggle) =>
        `<li>${esc(toggle.label)}: <strong>${working.toggles[toggle.id] ? "on" : "off"}</strong></li>`,
    )
    .join("");

  const tableRows = backoff.rows
    .map(
      (row) => `<tr>
<td class="num">${esc(row.attempt)}</td>
<td class="num">${esc(row.delayMs)} ms${row.cappedAtLimit ? " (capped)" : ""}</td>
<td>${esc(row.rangeMs[0])}–${esc(row.rangeMs[1])} ms</td>
<td class="num">${esc(row.cumulativeWorstMs)} ms</td>
</tr>`,
    )
    .join("\n");

  const facts = (data.facts ?? [])
    .map((fact) => {
      const idx = Number(String(fact.source).replace(/[^0-9]/g, "")) - 1;
      const cite = (data.inputs ?? [])[idx];
      return `<li><span class="acta-label is-fact">Fact</span> ${esc(fact.text)} <em>[${esc(fact.source)}${cite ? ` — ${esc(cite)}` : ""}]</em></li>`;
    })
    .join("\n");

  const simplifications = (data.simplifications ?? [])
    .map(
      (item) => `<li><span class="acta-label is-simplification">Simplification</span> ${esc(item)}</li>`,
    )
    .join("\n");

  const unresolved =
    (data.unresolved ?? []).map((item) => `<li>${esc(item)}</li>`).join("") ||
    "<li>nothing recorded</li>";

  return `
<section class="acta-section" aria-labelledby="model-title">
<h2 id="model-title" class="acta-h2"><span class="sn">01</span>Accepted model state</h2>
<div class="acta-call is-positive"><span class="c-k">Decision ${esc(decision.id)}</span>
<p><strong>Model accepted.</strong> ${esc(decision.rationale ?? "no rationale volunteered")}</p>
<p>Accepted via ${esc(decision.acceptedVia)}.</p>
</div>
<p>Question explored: ${esc(data.question)}</p>
<h3 class="acta-h3">Accepted parameters</h3>
<ul>${paramItems}${toggleItems}</ul>
<h3 class="acta-h3">Observed conclusion</h3>
<p>${esc(working.conclusion)}</p>
</section>
<section class="acta-section" aria-labelledby="consequence-title">
<h2 id="consequence-title" class="acta-h2"><span class="sn">02</span>Derived consequence at the accepted parameters</h2>
<div class="tablewrap"><table class="acta-table">
<caption>Per-attempt delay, jitter range, and cumulative worst-case wait</caption>
<thead><tr><th scope="col">Attempt</th><th scope="col">Delay</th><th scope="col">Jitter range</th><th scope="col">Cumulative worst-case</th></tr></thead>
<tbody>
${tableRows}
</tbody>
</table></div>
<p>Worst-case total across ${esc(backoff.totals.attempts)} attempts: <strong>${esc(backoff.totals.worstCaseTotalMs)} ms</strong> · expected ≈ <strong>${esc(backoff.totals.expectedTotalMs)} ms</strong>.</p>
</section>
<section class="acta-section" aria-labelledby="simpl-title">
<h2 id="simpl-title" class="acta-h2"><span class="sn">03</span>Declared simplifications</h2>
<ul>
${simplifications}
</ul>
</section>
<section class="acta-section" aria-labelledby="facts-title">
<h2 id="facts-title" class="acta-h2"><span class="sn">04</span>Facts (sourced)</h2>
<ul>
${facts}
</ul>
</section>
<section class="acta-section" aria-labelledby="unresolved-title">
<h2 id="unresolved-title" class="acta-h2"><span class="sn">05</span>Unresolved at acceptance</h2>
<ul>${unresolved}</ul>
</section>`;
}
