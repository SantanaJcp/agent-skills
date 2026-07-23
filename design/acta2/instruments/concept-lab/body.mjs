/* Static renderer for the concept-lab instrument (Node-side).
   Renders the DEFAULT model state as the no-JS baseline from the same data
   island the runtime parses. The backoff math is imported from the shared
   export-core so static geometry, live geometry, and exports can never
   diverge (single source of truth; contract §4.1). */

import { backoffPlotSpec, deriveBackoff } from "../../lib/export-core.mjs";

/* --- default working state from the data island --- */
function defaultWorking(data) {
  const params = {};
  for (const param of data.params) params[param.id] = param.default;
  const toggles = {};
  for (const toggle of data.toggles ?? []) toggles[toggle.id] = toggle.default;
  return { params, toggles };
}

/* --- shared formatting (mirrored in instrument.js) --- */
function fmtParam(value, unit) {
  if (!unit) return String(value);
  if (unit === "×") return `${value}×`;
  return `${value} ${unit}`;
}
function fmtMs(value) {
  return `${value} ms`;
}
function fmtRange(range) {
  return `${range[0]}–${range[1]} ms`;
}
function totalsText(totals) {
  return `Worst-case total across ${totals.attempts} attempts: ${totals.worstCaseTotalMs} ms · expected ≈ ${totals.expectedTotalMs} ms`;
}

/* --- SVG rendering from the shared plot spec (export-core.backoffPlotSpec).
   Every coordinate, size, dash state, and label comes from the spec; this
   function only maps item types to SVG markup. instrument.js performs the
   identical mapping with DOM nodes. --- */
function renderPlot(spec) {
  return spec.items
    .map((it) => {
      switch (it.el) {
        case "axis-line":
          return `<line x1="${it.x1}" y1="${it.y1}" x2="${it.x2}" y2="${it.y2}" stroke="var(--acta-rule-strong)" stroke-width="1"></line>`;
        case "axis-tick":
          return `<line x1="${it.x}" y1="${it.y1}" x2="${it.x}" y2="${it.y2}" stroke="var(--acta-rule-strong)" stroke-width="1"></line>`;
        case "zero-label":
          return `<text x="${it.x}" y="${it.y}" font-size="11" fill="var(--acta-ink-muted)" text-anchor="middle">${it.text}</text>`;
        case "caption":
          return `<text x="${it.x}" y="${it.y}" font-size="11" fill="var(--acta-ink-muted)" text-anchor="start">${it.text}</text>`;
        case "band": {
          const stroke = it.capped ? "var(--acta-warning)" : "var(--acta-action)";
          const dash = it.capped ? ` stroke-dasharray="3 2"` : "";
          return `<rect x="${it.x}" y="${it.y}" width="${it.width}" height="${it.height}" fill="var(--acta-action-tint)" stroke="${stroke}" stroke-width="1.5"${dash}></rect>`;
        }
        case "tick":
          return `<line x1="${it.x}" y1="${it.y1}" x2="${it.x}" y2="${it.y2}" stroke="var(--acta-ink)" stroke-width="1.5"></line>`;
        case "cap-label":
          return `<text x="${it.x}" y="${it.y}" font-size="10" fill="var(--acta-warning)" text-anchor="middle">${it.text}</text>`;
        case "attempt-label":
          return `<text x="${it.x}" y="${it.y}" font-size="11" font-weight="600" fill="var(--acta-ink)" text-anchor="middle">${it.text}</text>`;
        case "expected-mark":
          return `<line x1="${it.x}" y1="${it.y1}" x2="${it.x}" y2="${it.y2}" stroke="var(--acta-ink-muted)" stroke-width="1.5" stroke-dasharray="2 3"></line>`;
        case "expected-label":
          return `<text x="${it.x}" y="${it.y}" font-size="11" fill="var(--acta-ink-muted)" text-anchor="middle">${it.text}</text>`;
        case "endmark":
          return `<line x1="${it.x1}" y1="${it.y1}" x2="${it.x2}" y2="${it.y2}" stroke="var(--acta-rule-strong)" stroke-width="1"></line>`;
        case "total-label":
          return `<text x="${it.x}" y="${it.y}" font-size="12" font-weight="600" fill="var(--acta-ink)" text-anchor="end">${it.text}</text>`;
        default:
          return "";
      }
    })
    .join("\n");
}

export function renderBody(data, { esc }) {
  const working = defaultWorking(data);
  const spec = backoffPlotSpec(working.params, working.toggles);
  const backoff = spec.backoff;
  const unitById = {};
  for (const param of data.params) unitById[param.id] = param.unit;

  const controls = data.params
    .map(
      (param) => `
<div class="clab-row">
<label for="clab-p-${esc(param.id)}">${esc(param.label)}</label>
<output id="clab-o-${esc(param.id)}" for="clab-p-${esc(param.id)}">${esc(fmtParam(working.params[param.id], param.unit))}</output>
<input type="range" id="clab-p-${esc(param.id)}" data-param="${esc(param.id)}" min="${esc(param.min)}" max="${esc(param.max)}" step="${esc(param.step)}" value="${esc(param.default)}">
</div>`,
    )
    .join("\n");

  const toggles = (data.toggles ?? [])
    .map(
      (toggle) => `
<label class="a2-choice clab-toggle"><input type="checkbox" data-toggle="${esc(toggle.id)}"${toggle.default ? " checked" : ""}><span>${esc(toggle.label)}</span></label>`,
    )
    .join("\n");

  const tableRows = backoff.rows
    .map(
      (row) => `<tr>
<td class="num">${esc(row.attempt)}</td>
<td class="num">${esc(fmtMs(row.delayMs))}${row.cappedAtLimit ? `<span class="clab-cap">capped</span>` : ""}</td>
<td>${esc(fmtRange(row.rangeMs))}</td>
<td class="num">${esc(fmtMs(row.cumulativeWorstMs))}</td>
</tr>`,
    )
    .join("\n");

  const facts = (data.facts ?? [])
    .map(
      (fact) => {
        const index = Number(String(fact.source).replace(/[^0-9]/g, "")) - 1;
        const cite = data.inputs?.[index];
        return `<li><span class="clab-tag is-src">${esc(fact.source)}</span>${esc(fact.text)}${cite ? ` <em class="clab-cite">— ${esc(cite)}</em>` : ""}</li>`;
      },
    )
    .join("\n");

  const simplifications = (data.simplifications ?? [])
    .map(
      (item) => `<li><span class="clab-tag is-simpl">Simplification</span>${esc(item)}</li>`,
    )
    .join("\n");

  return `
<h1 class="clab-question">${esc(data.question)}</h1>
<p class="clab-lede">Adjust the parameters to feel how exponential backoff shapes the total wait a client accumulates across retries. Nothing here changes files.</p>
<div class="clab-bench">
<section class="clab-model" aria-label="Backoff timeline model">
<div class="plotwrap"><svg viewBox="0 0 ${spec.view.w} ${spec.view.h}" role="img" aria-labelledby="clab-svg-title clab-svg-desc" class="clab-svg">
<title id="clab-svg-title">Retry backoff timeline for the current parameters</title>
<desc id="clab-svg-desc">A horizontal cumulative-wait axis showing, for each retry attempt, a band spanning its jitter range placed on the worst-case timeline, with a solid tick at the deterministic delay, a dashed mark at the expected total, and an end mark labelled with the worst-case total. The consequence table below is the full textual equivalent.</desc>
<g data-clab-plot>
${renderPlot(spec)}
</g>
</svg></div>
<ul class="clab-legend" aria-label="How to read the timeline">
<li><span class="lg-band" aria-hidden="true"></span>band = jitter range for one attempt</li>
<li><span class="lg-tick" aria-hidden="true"></span>tick = deterministic delay (no jitter)</li>
<li><span class="lg-expected" aria-hidden="true"></span>dashed mark = expected total</li>
<li><span class="lg-capped" aria-hidden="true"></span>dashed + “capped” = delay cap reached</li>
</ul>
</section>
<section class="clab-controls" aria-label="Parameter controls">
<h2>Parameters</h2>
${controls}
${toggles}
<div class="clab-actions">
<button type="button" class="a2-btn" data-acta2-reset>Reset model</button>
<p class="a2-jsnote">JavaScript is off, so the sliders are disabled; the model shows its default state below. Ask in chat for any other parameter set — for example: “show base 500 ms, factor 3, full jitter”.</p>
</div>
</section>
<section class="clab-readout" aria-label="Derived consequence">
<h2>Derived consequence</h2>
<div class="tablewrap"><table class="clab-table">
<caption class="visually-hidden">Per-attempt delay, jitter range, and cumulative worst-case wait</caption>
<thead><tr><th scope="col">Attempt</th><th scope="col">Delay</th><th scope="col">Jitter range</th><th scope="col">Cumulative worst-case</th></tr></thead>
<tbody id="clab-consequences">
${tableRows}
</tbody>
</table></div>
<p class="clab-totals" data-bind="totals-line">${esc(totalsText(backoff.totals))}</p>
</section>
</div>
<section class="clab-conclude" aria-label="Status and conclusion">
<p class="a2-status" data-bind="status-label">Exploring — adjust the model, then record a conclusion</p>
<label class="a2-field"><span>Observed conclusion (exported with your parameters)</span><textarea rows="3" data-working="conclusion" placeholder="What did the model show you? e.g. the cap dominates once the raw delay exceeds it."></textarea></label>
<p class="a2-hint">Recording a conclusion flips the working status to candidate-ready and readies the export; it stays a candidate until you confirm it in chat.</p>
</section>
<div class="clab-evidence">
<section class="clab-facts" aria-label="Sourced facts">
<h2>Facts (sourced)</h2>
<ul>
${facts}
</ul>
</section>
<section class="clab-simpl" aria-label="Declared simplifications">
<h2>Declared simplifications</h2>
<ul>
${simplifications}
</ul>
</section>
</div>
<details class="a2-more"><summary>Why jitter matters</summary><div>
<p>Without jitter, clients that failed together retry together, re-synchronising into waves that hammer a recovering service. Jitter spreads each client's next attempt across a random window, so load smooths out. Full jitter (0 to the delay) spreads more aggressively than equal jitter (half the delay to the delay): expected per-attempt delay falls from 75% to 50% of the capped exponential delay — one third less — while the worst case stays unchanged.</p>
</div></details>`;
}
