/* Static renderer for the three-code-paths instrument (Node-side).
   Renders the complete no-JS baseline from the same data island the runtime
   parses, so static DOM and live state can never start diverged. Code is
   syntax-highlighted at build time (lib/highlight.mjs) — the browser never
   tokenizes anything. */

import { highlightJs } from "../../lib/highlight.mjs";

function proConTable(option, esc) {
  const rows = [];
  const count = Math.max(option.pros.length, option.cons.length);
  for (let index = 0; index < count; index += 1) {
    const pro = option.pros[index];
    const con = option.cons[index];
    rows.push(
      `<tr>${pro === undefined ? '<td class="pc-empty"></td>' : `<td class="pc-pro">${esc(pro)}</td>`}${
        con === undefined ? '<td class="pc-empty"></td>' : `<td class="pc-con">${esc(con)}</td>`
      }</tr>`,
    );
  }
  return `<table class="tcp-procon">
<thead><tr><th scope="col">Pro</th><th scope="col">Con</th></tr></thead>
<tbody>${rows.join("\n")}</tbody>
</table>`;
}

export function renderBody(data, { esc }) {
  const options = data.options
    .map(
      (option) => `
<article class="tcp-card" data-option="${esc(option.id)}">
<div class="c-head"><span class="c-id" aria-label="Path ${esc(option.id.toUpperCase())}">${esc(option.id.toUpperCase())}</span><h2>${esc(option.label)}</h2></div>
<p class="c-claim">${esc(option.claim)}</p>
<div class="a2-code c-code"><div class="c-path">${esc(option.code.path)}</div><div class="codewrap"><pre><code>${highlightJs(option.code.snippet, esc)}</code></pre></div></div>
<ol class="c-flow" aria-label="Data flow for ${esc(option.label)}">
${option.flow.map((step) => `<li>${esc(step)}</li>`).join("\n")}
</ol>
${proConTable(option, esc)}
<div class="tcp-seams">
<p class="s-row"><span class="s-k">Test seam</span><span class="s-v">${esc(option.seams.test)}</span></p>
<p class="s-row"><span class="s-k">Migration</span><span class="s-v">${esc(option.seams.migration)}</span></p>
</div>
<details class="a2-more"><summary>Failure modes &amp; change conditions</summary><div>
<p><b>Failure modes:</b></p>
<ul>${option.failureModes.map((item) => `<li>${esc(item)}</li>`).join("")}</ul>
<p><b>Reconsider this path when:</b></p>
<ul>${option.changeConditions.map((item) => `<li>${esc(item)}</li>`).join("")}</ul>
</div></details>
<label class="a2-choice tcp-select"><input type="radio" name="acta2-option" value="${esc(option.id)}"><span>Select ${esc(option.label)}</span></label>
</article>`,
    )
    .join("\n");

  const matrixRows = data.matrix
    .map((row) => {
      const cells = data.options
        .map((option) => {
          const verdict = row.verdicts[option.id];
          const mark =
            verdict.mark === "yes" ? "✓" : verdict.mark === "no" ? "✗" : "◐";
          const word =
            verdict.mark === "yes" ? "yes" : verdict.mark === "no" ? "no" : "partly";
          return `<td><span class="m-${esc(verdict.mark)}" aria-hidden="true">${mark}</span><span class="visually-hidden">${word}</span> <span class="m-note">${esc(verdict.note)}</span></td>`;
        })
        .join("");
      return `<tr><th scope="row">${esc(row.dimension)}</th>${cells}</tr>`;
    })
    .join("\n");

  const recommended = data.options.find(
    (option) => option.id === data.recommendation.option,
  );

  return `
<h1 class="tcp-question">${esc(data.question)}</h1>
<div class="tcp-context" aria-label="Constraints and evaluation dimensions">
${data.constraints.map((constraint) => `<span class="tcp-chip">${esc(constraint)}</span>`).join("\n")}
</div>
<div class="tcp-grid">
${options}
</div>
<section class="tcp-matrix" aria-label="Comparison matrix">
<h2>Same dimensions, all three paths</h2>
<div class="tablewrap"><table>
<thead><tr><th scope="col">Dimension</th>${data.options.map((option) => `<th scope="col">${esc(option.label)}</th>`).join("")}</tr></thead>
<tbody>
${matrixRows}
</tbody>
</table></div>
</section>
<aside class="tcp-reco"><span class="r-k">Recommendation — after the comparison</span>${esc(
    recommended ? `${recommended.label}: ` : "",
  )}${esc(data.recommendation.reason)}</aside>
<section class="tcp-decide" aria-label="Decision gate">
<h2>DecisionGate — open</h2>
<p class="d-selection" data-bind="selection-line">No path selected yet.</p>
<p class="a2-status" data-bind="status-label">Open — no path selected yet</p>
<label class="a2-field"><span>Rationale (optional)</span><textarea rows="2" data-working="rationale" placeholder="Why this path, in your words"></textarea></label>
<div class="x-actions">
<button type="button" class="a2-btn" data-acta2-reset>Reset selection</button>
</div>
<p class="a2-jsnote">JavaScript is off, so selection controls are disabled. Decide in chat instead — for example: “choose Path B — rationale: …”.</p>
<p>Selecting here only prepares a candidate. The gate is resolved when you confirm the pasted candidate in chat — silence never approves.</p>
</section>`;
}
