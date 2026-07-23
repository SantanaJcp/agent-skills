/* Static renderer for the build-with-notes instrument (Node-side).
   Renders the complete no-JS session board from the same data island the
   runtime parses, so static DOM and live state can never start diverged. */

const TYPE_LABELS = {
  "plan-confirmed": "plan",
  deviation: "deviation",
  check: "check",
  discovery: "discovery",
  stop: "stop",
};

export function renderBody(data, { esc }) {
  const entries = data.entries ?? [];

  /* Counts derived the same way as export-core deriveCounts/filterEntries. */
  let deviations = 0;
  let needsHuman = 0;
  let checkEntries = 0;
  for (const entry of entries) {
    if (entry.type === "deviation") deviations += 1;
    if (entry.needsHuman) needsHuman += 1;
    if (entry.type === "check") checkEntries += 1;
  }
  const checksPassing = (data.checks ?? []).filter((c) => c.state === "pass").length;
  const checksTotal = (data.checks ?? []).length;
  const checksTone = checksPassing === checksTotal ? "pass" : "fail";

  const tiles = [
    {
      tone: "paused",
      value: `${esc(data.slices.done)} / ${esc(data.slices.total)}`,
      label: "slices green",
      sub: `paused before ${esc(data.slices.current)}`,
    },
    {
      tone: checksTone,
      value: `${esc(checksPassing)} / ${esc(checksTotal)}`,
      label: checksTone === "pass" ? "checks passing" : "checks — failure present",
    },
    {
      tone: deviations > 0 ? "warn" : "pass",
      value: `${esc(deviations)}`,
      label: deviations === 1 ? "deviation logged" : "deviations logged",
    },
    {
      tone: needsHuman > 0 ? "fail" : "pass",
      value: `${esc(needsHuman)}`,
      label: needsHuman === 1 ? "needs your attention" : "need your attention",
    },
  ]
    .map(
      (tile) =>
        `<div class="bwn-tile" data-tone="${esc(tile.tone)}"><b>${tile.value}</b><span>${tile.label}</span>${tile.sub ? `<small>${tile.sub}</small>` : ""}</div>`,
    )
    .join("\n");

  const choices = data.gate.options
    .map(
      (option) => `
<label class="a2-choice"><input type="radio" name="acta2-resolution" value="${esc(option.id)}">
<span class="c-label">${esc(option.label)}</span>
<span class="c-consequence">${esc(option.consequence)}</span></label>`,
    )
    .join("\n");

  const filters = [
    { id: "all", label: "All", count: entries.length },
    { id: "deviations", label: "Deviations", count: deviations },
    { id: "needs-human", label: "Needs you", count: needsHuman },
    { id: "checks", label: "Checks", count: checkEntries },
  ]
    .map(
      (chip) =>
        `<button type="button" class="a2-btn" data-filter="${esc(chip.id)}" aria-pressed="${chip.id === "all" ? "true" : "false"}">${esc(chip.label)} (${esc(chip.count)})</button>`,
    )
    .join("\n");

  const checksStrip = (data.checks ?? [])
    .map(
      (check) =>
        `<li data-state="${esc(check.state)}">${esc(check.label)}: ${esc(check.state)} — ${esc(check.detail)}</li>`,
    )
    .join("\n");

  const log = entries
    .map((entry) => {
      const typeLabel = TYPE_LABELS[entry.type] || entry.type;
      const stateBadge =
        entry.type === "check" && entry.state
          ? `<span class="e-type">${esc(entry.state)}</span>`
          : "";
      const needsBadge = entry.needsHuman
        ? `<span class="e-needs">needs you</span>`
        : "";
      return `
<li class="bwn-entry" data-entry="${esc(entry.id)}" data-type="${esc(entry.type)}">
<div class="e-top"><span class="e-time">${esc(entry.time)}</span><span class="e-type">${esc(typeLabel)}</span>${stateBadge}${needsBadge}</div>
<p class="e-title">${esc(entry.title)}</p>
<p class="e-body">${esc(entry.body)}</p>
</li>`;
    })
    .join("\n");

  return `
<div class="bwn-head">
<h1 class="bwn-title">${esc(data.title)} — session board</h1>
<p class="bwn-question">${esc(data.question)}</p>
</div>
<div class="bwn-tiles" aria-label="Session status at a glance">
${tiles}
</div>
<section class="bwn-gate" aria-labelledby="bwn-gate-title">
<div class="g-head">
<p class="g-id">${esc(data.gate.id)} — STOP gate open</p>
<p class="g-title" id="bwn-gate-title">${esc(data.gate.title)}</p>
</div>
<div class="g-body">
<p class="g-reason">${esc(data.gate.reason)}</p>
<div class="bwn-choices" role="group" aria-label="Gate resolution options">
${choices}
</div>
<label class="a2-field"><span>Rationale (optional)</span><textarea rows="2" data-working="rationale" placeholder="Why this resolution, in your words"></textarea></label>
<div class="x-actions">
<button type="button" class="a2-btn" data-acta2-reset>Reset resolution</button>
<p class="a2-jsnote">JavaScript is off, so resolution controls are disabled. Decide in chat instead — for example: “resolve STOP-01: reject the addition and continue the plan”.</p>
</div>
<p class="a2-status" data-bind="status-label">STOP gate open — work is paused for your decision</p>
<p class="g-resolution" data-bind="resolution-line">No resolution proposed yet.</p>
<p class="g-silence">Work resumes only after explicit acceptance in chat; silence never approves.</p>
</div>
</section>
<div class="bwn-next"><b>Next authorized action</b>${esc(data.nextAction)}</div>
<section class="bwn-timeline" aria-labelledby="bwn-timeline-title">
<h2 id="bwn-timeline-title">Session timeline</h2>
<ul class="bwn-checks" aria-label="Checks at this point">
${checksStrip}
</ul>
<div class="bwn-filters" role="group" aria-label="Filter timeline entries">
${filters}
</div>
<p class="bwn-showing" data-bind="showing-line">Showing all ${esc(entries.length)} entries.</p>
<ul class="bwn-log">
${log}
</ul>
</section>
<details class="a2-more"><summary>Changed files this session</summary><div>
<ul>${(data.files ?? []).map((file) => `<li>${esc(file)}</li>`).join("")}</ul>
</div></details>`;
}
