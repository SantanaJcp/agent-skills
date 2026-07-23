/* Static renderer for the feel-the-flow instrument (Node-side).
   A disposable behavior prototype: the playground on the left is a real
   type-and-watch surface driven by the parameter rail on the right. The
   prototype itself is throwaway by design — only the parameters and the
   felt conclusion export. No durable record exists for this skill. */

export function renderBody(data, { esc }) {
  const rows = (data.dataset.skills ?? [])
    .map(
      (skill) => `<div class="ftf-row" data-row-name="${esc(skill.name.toLowerCase())}"><span class="ftf-name">${esc(skill.name)}</span><span class="ftf-tags">${(skill.tags ?? [])
        .map((tag) => `<i>${esc(tag)}</i>`)
        .join("")}</span></div>`,
    )
    .join("\n");

  const controls = data.params
    .map(
      (param) => `
<div class="ftf-prow">
<label for="ftf-p-${esc(param.id)}">${esc(param.label)}</label>
<output id="ftf-o-${esc(param.id)}" for="ftf-p-${esc(param.id)}">${esc(param.default)}${esc(param.unit)}</output>
<input type="range" id="ftf-p-${esc(param.id)}" data-param="${esc(param.id)}" min="${esc(param.min)}" max="${esc(param.max)}" step="${esc(param.step)}" value="${esc(param.default)}">
</div>`,
    )
    .join("\n");

  const toggles = (data.toggles ?? [])
    .map(
      (toggle) => `
<label class="a2-choice ftf-toggle"><input type="checkbox" data-toggle="${esc(toggle.id)}"${toggle.default ? " checked" : ""}><span>${esc(toggle.label)}</span></label>`,
    )
    .join("\n");

  return `
<h1 class="ftf-question">${esc(data.question)}</h1>
<p class="ftf-lede">${esc(data.lede)}</p>
<div class="ftf-bench">
<section class="ftf-stage" aria-label="Typing playground">
<p class="s-hint"><span class="a2-k">Playground</span>Type below — the list reacts with exactly the configured behavior. Nothing you type is exported.</p>
<div class="ftf-inputwrap">
<input type="text" class="ftf-input" data-ftf-input placeholder="${esc(data.playground.placeholder)}" aria-label="Prototype filter input">
<span class="ftf-pending" data-ftf-pending aria-live="polite"></span>
</div>
<div class="ftf-list" data-ftf-list aria-live="polite">
${rows}
</div>
<p class="ftf-empty" data-ftf-empty hidden>${esc(data.playground.emptyText)}</p>
<p class="a2-jsnote">JavaScript is off, so the playground is inert and the sliders are disabled. The full list stays readable above; describe the feel you want in chat instead — for example: “try 150 ms debounce with instant first keystroke”.</p>
</section>
<section class="ftf-controls" aria-label="Feel parameters">
<h2>Parameters</h2>
${controls}
${toggles}
<div class="ftf-actions">
<button type="button" class="a2-btn" data-acta2-reset>Reset feel</button>
</div>
<p class="ftf-note">${esc(data.playground.note)}</p>
</section>
</div>
<section class="ftf-conclude" aria-label="Felt conclusion">
<p class="a2-status" data-bind="status-label">Exploring — feel the prototype, then record your conclusion</p>
<label class="a2-field"><span>Felt conclusion (exported with your parameters)</span><textarea rows="3" data-working="conclusion" placeholder="${esc(data.playground.conclusionPlaceholder)}"></textarea></label>
<p class="ftf-hint">The prototype is disposable; only these parameters and this conclusion carry forward. There is deliberately no durable record.</p>
</section>`;
}
