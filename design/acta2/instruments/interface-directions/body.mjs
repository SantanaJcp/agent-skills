/* Static renderer for the interface-directions instrument (Node-side).
   Every direction renders the IDENTICAL scenario dataset through a different
   visual philosophy, at equal fidelity, inside an identical stage frame —
   the only variable on screen is the design. The record body re-renders the
   chosen mockup through the same exported function, so instrument and record
   can never disagree about what a direction looked like. */

/** Render one direction's mini-mockup from structured scenario data.
 * @param {any} data full scenario @param {any} option direction
 * @param {(value: unknown) => string} esc */
export function renderMockup(data, option, esc) {
  const mock = option.mockup;
  const dataset = data.dataset;
  const catalogRows = (dataset.skills ?? [])
    .map(
      (skill) => `<div class="mk-row"><span class="mk-name">${esc(skill.name)}</span><span class="mk-tags">${(skill.tags ?? [])
        .map((tag) => `<i>${esc(tag)}</i>`)
        .join("")}</span></div>`,
    )
    .join("\n");

  if (mock.kind === "quiet") {
    return `<div class="mk mk-quiet">
<p class="mk-headline">${esc(mock.headline)}</p>
<p class="mk-body">${esc(mock.body)}</p>
${mock.action ? `<span class="mk-action">${esc(mock.action)}</span>` : ""}
</div>`;
  }
  if (mock.kind === "suggest") {
    return `<div class="mk mk-suggest">
<p class="mk-headline">${esc(mock.headline)}</p>
<p class="mk-body">${esc(mock.body)}</p>
<div class="mk-chips">${(mock.suggestions ?? [])
      .map((tag) => `<span class="mk-chip">${esc(tag)}</span>`)
      .join("")}</div>
${mock.action ? `<span class="mk-action">${esc(mock.action)}</span>` : ""}
</div>`;
  }
  if (mock.kind === "dimmed") {
    return `<div class="mk mk-dimmed">
<p class="mk-notice">${esc(mock.notice)}${mock.action ? ` <span class="mk-action mk-inline">${esc(mock.action)}</span>` : ""}</p>
<div class="mk-catalog" aria-hidden="false">
${catalogRows}
</div>
</div>`;
  }
  return `<div class="mk"><p class="mk-headline">${esc(mock.headline ?? "")}</p></div>`;
}

export function renderBody(data, { esc }) {
  const dataset = data.dataset;
  const datasetLine = `${dataset.skills.length} skills · tags: ${[...new Set(dataset.skills.flatMap((skill) => skill.tags))].join(" / ")} · query: ?tag=${dataset.queryTag} → 0 matches`;

  const directions = data.options
    .map(
      (option) => `
<section class="ifd-direction" data-option="${esc(option.id)}" aria-labelledby="ifd-t-${esc(option.id)}">
<div class="d-head">
<span class="d-id" aria-label="Direction ${esc(option.id.toUpperCase())}">${esc(option.id.toUpperCase())}</span>
<h2 id="ifd-t-${esc(option.id)}">${esc(option.label)}</h2>
</div>
<p class="d-thesis">${esc(option.claim)}</p>
<figure class="ifd-stage">
<figcaption class="s-chrome"><span class="s-dots" aria-hidden="true"><i></i><i></i><i></i></span><span class="s-url">${esc(data.stageLabel)}</span></figcaption>
<div class="s-canvas">
${renderMockup(data, option, esc)}
</div>
</figure>
<div class="ifd-notes">
<table class="ifd-procon">
<thead><tr><th scope="col">Holds up because</th><th scope="col">Costs</th></tr></thead>
<tbody>${(() => {
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
        return rows.join("\n");
      })()}</tbody>
</table>
<label class="a2-choice ifd-select"><input type="radio" name="acta2-option" value="${esc(option.id)}"><span>Choose ${esc(option.label)}</span></label>
</div>
</section>`,
    )
    .join("\n");

  const matrixRows = data.matrix
    .map((row) => {
      const cells = data.options
        .map((option) => {
          const verdict = row.verdicts[option.id];
          const mark = verdict.mark === "yes" ? "✓" : verdict.mark === "no" ? "✗" : "◐";
          const word = verdict.mark === "yes" ? "yes" : verdict.mark === "no" ? "no" : "partly";
          return `<td><span class="m-${esc(verdict.mark)}" aria-hidden="true">${mark}</span><span class="visually-hidden">${word}</span> <span class="m-note">${esc(verdict.note)}</span></td>`;
        })
        .join("");
      return `<tr><th scope="row">${esc(row.dimension)}</th>${cells}</tr>`;
    })
    .join("\n");

  const recommended = data.options.find((option) => option.id === data.recommendation.option);

  return `
<h1 class="ifd-question">${esc(data.question)}</h1>
<p class="ifd-lede">Each direction below renders the identical dataset — the only variable is the design. React to real renders, then choose one.</p>
<p class="ifd-dataset"><span class="a2-k">Shared dataset</span>${esc(datasetLine)}</p>
${directions}
<section class="ifd-matrix" aria-label="Comparison matrix">
<h2>Same dimensions, all three directions</h2>
<div class="tablewrap"><table>
<thead><tr><th scope="col">Dimension</th>${data.options.map((option) => `<th scope="col">${esc(option.label)}</th>`).join("")}</tr></thead>
<tbody>
${matrixRows}
</tbody>
</table></div>
</section>
<aside class="ifd-reco"><span class="r-k">Recommendation — after the comparison</span>${esc(
    recommended ? `${recommended.label}: ` : "",
  )}${esc(data.recommendation.reason)}</aside>
<section class="ifd-decide" aria-label="Decision gate">
<h2>DecisionGate — open</h2>
<p class="d-selection" data-bind="selection-line">No direction selected yet.</p>
<p class="a2-status" data-bind="status-label">Open — no direction selected yet</p>
<label class="a2-field"><span>Rationale (optional)</span><textarea rows="2" data-working="rationale" placeholder="Why this direction, in your words"></textarea></label>
<div class="x-actions">
<button type="button" class="a2-btn" data-acta2-reset>Reset selection</button>
</div>
<p class="a2-jsnote">JavaScript is off, so selection controls are disabled. Decide in chat instead — for example: “choose direction B — rationale: …”.</p>
<p>Selecting here only prepares a candidate. The gate is resolved when you confirm the pasted candidate in chat — silence never approves.</p>
</section>`;
}
