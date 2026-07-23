/* Record body for three-code-paths: accepted decision, preserved
   alternatives, and the comparison evidence — Acta notarial identity. */

export function renderRecord(data, accepted, { esc }) {
  const chosen = data.options.find((option) => option.id === accepted.decisions[0].selection);
  const rejected = data.options.filter((option) => option.id !== accepted.decisions[0].selection);

  const matrixRows = data.matrix
    .map((row) => {
      const cells = data.options
        .map((option) => {
          const verdict = row.verdicts[option.id];
          const word = verdict.mark === "yes" ? "Yes" : verdict.mark === "no" ? "No" : "Partly";
          return `<td>${esc(word)} — ${esc(verdict.note)}</td>`;
        })
        .join("");
      return `<tr><th scope="row">${esc(row.dimension)}</th>${cells}</tr>`;
    })
    .join("\n");

  return `
<section class="acta-section" aria-labelledby="decision-title">
<h2 id="decision-title" class="acta-h2"><span class="sn">01</span>Accepted decision</h2>
<div class="acta-call is-positive"><span class="c-k">Decision ${esc(accepted.decisions[0].id)}</span>
<p><strong>${esc(chosen ? chosen.label : accepted.decisions[0].selection)}</strong> — ${esc(chosen ? chosen.claim : "")}</p>
<p>Rationale: ${esc(accepted.decisions[0].rationale ?? "none volunteered")}. Accepted via ${esc(accepted.decisions[0].acceptedVia)}.</p>
</div>
<p>Question decided: ${esc(data.question)}</p>
</section>
<section class="acta-section" aria-labelledby="matrix-title">
<h2 id="matrix-title" class="acta-h2"><span class="sn">02</span>Comparison evidence</h2>
<div class="tablewrap"><table class="acta-table">
<caption>Same dimensions, all three paths (as compared before acceptance)</caption>
<thead><tr><th scope="col">Dimension</th>${data.options
    .map((option) => `<th scope="col">${esc(option.label)}</th>`)
    .join("")}</tr></thead>
<tbody>
${matrixRows}
</tbody>
</table></div>
</section>
<section class="acta-section" aria-labelledby="rejected-title">
<h2 id="rejected-title" class="acta-h2"><span class="sn">03</span>Rejected alternatives — preserved with change conditions</h2>
${rejected
    .map(
      (option) => `
<article>
<h3 class="acta-h3">${esc(option.label)}</h3>
<p>${esc(option.claim)}</p>
<p><strong>Reconsider when:</strong></p>
<ul>${option.changeConditions.map((item) => `<li>${esc(item)}</li>`).join("")}</ul>
<p><strong>Known failure modes:</strong></p>
<ul>${option.failureModes.map((item) => `<li>${esc(item)}</li>`).join("")}</ul>
</article>`,
    )
    .join("\n")}
</section>
<section class="acta-section" aria-labelledby="unresolved-title">
<h2 id="unresolved-title" class="acta-h2"><span class="sn">04</span>Unresolved at acceptance</h2>
<ul>${(data.unresolved ?? []).map((item) => `<li>${esc(item)}</li>`).join("") || "<li>nothing recorded</li>"}</ul>
</section>`;
}
