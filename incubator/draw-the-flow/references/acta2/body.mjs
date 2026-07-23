/* Static renderer for the draw-the-flow instrument (Node-side).
   One semantic flow, overview first: every node and edge carries the named
   paths it belongs to (normal / decision / failure / recovery), the focus
   buttons only change what is EMPHASIZED (ephemeral view state, never
   exported), and the full textual equivalent ships beside the drawing so
   the no-JS page carries identical meaning. The gate is a real decision:
   is this flow an accurate shared understanding? */

import { renderFlow } from "./flow.mjs";

export function renderBody(data, { esc }) {
  const flow = renderFlow(data.flow, esc, { ariaLabel: data.flow.ariaLabel });

  const focusButtons = data.pathViews
    .map(
      (view) =>
        `<button type="button" class="a2-btn" data-flow-focus="${esc(view.id)}" aria-pressed="${view.id === "all" ? "true" : "false"}">${esc(view.label)}</button>`,
    )
    .join("\n");

  const pathCards = data.pathViews
    .filter((view) => view.id !== "all")
    .map(
      (view) => `
<section class="dtf-path" data-path-card="${esc(view.id)}" aria-labelledby="dtf-p-${esc(view.id)}">
<h3 id="dtf-p-${esc(view.id)}"><span class="p-swatch is-${esc(view.id)}" aria-hidden="true"></span>${esc(view.label)}</h3>
<ol>
${view.steps.map((step) => `<li>${esc(step)}</li>`).join("\n")}
</ol>
</section>`,
    )
    .join("\n");

  const choices = data.options
    .map(
      (option) => `
<label class="a2-choice"><input type="radio" name="acta2-option" value="${esc(option.id)}">
<span class="c-label">${esc(option.label)}</span>
<span class="c-consequence">${esc(option.consequence)}</span></label>`,
    )
    .join("\n");

  return `
<h1 class="dtf-question">${esc(data.question)}</h1>
<p class="dtf-lede">${esc(data.lede)}</p>
<section class="dtf-stage" aria-label="Flow diagram">
<div class="dtf-focus" role="group" aria-label="Emphasize one path (view only — never exported)">
${focusButtons}
</div>
<div class="dtf-plot" data-focus="all"><div class="plotwrap">${flow.svg}</div>
<p class="flowd-caption">${esc(data.flow.caption)}</p></div>
</section>
<section class="dtf-paths" aria-label="Textual equivalent, path by path">
<h2>The same flow, in words</h2>
<div class="dtf-pathgrid">
${pathCards}
</div>
</section>
<section class="dtf-decide" aria-label="Accuracy gate">
<h2>Is this flow the shared understanding?</h2>
<div class="dtf-choices" role="group" aria-label="Verification options">
${choices}
</div>
<p class="d-selection" data-bind="selection-line">No verdict proposed yet.</p>
<p class="a2-status" data-bind="status-label">${esc(data.openStatusLabel)}</p>
<label class="a2-field"><span>Corrections or rationale (optional)</span><textarea rows="2" data-working="rationale" placeholder="What is wrong or missing, in your words"></textarea></label>
<div class="x-actions">
<button type="button" class="a2-btn" data-acta2-reset>Reset verdict</button>
</div>
<p class="a2-jsnote">JavaScript is off, so the verdict controls are disabled and path emphasis stays on the whole flow. The textual equivalent above is complete; decide in chat instead — for example: “the flow is accurate” or “missing: retry path”.</p>
<p>Confirming here only prepares a candidate. The flow becomes the recorded understanding when you confirm the pasted candidate in chat — silence never approves.</p>
</section>`;
}
