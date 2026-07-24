/* Record body for build-with-notes: the resolved STOP gate, the session
   timeline that led to it, checks at close, and what stayed open — Acta
   notarial identity, generated from accepted canonical state only. */

const TYPE_LABELS = {
  "plan-confirmed": "Plan",
  deviation: "Deviation",
  check: "Check",
  discovery: "Discovery",
  stop: "STOP",
};

export function renderRecord(data, accepted, { esc }) {
  const decision = accepted.decisions[0];
  const resolution = data.gate.options.find((option) => option.id === decision.selection);

  const timelineRows = (data.entries ?? [])
    .map((entry) => {
      const typeLabel = TYPE_LABELS[entry.type] || entry.type;
      const flags = [];
      if (entry.type === "check" && entry.state) flags.push(entry.state);
      if (entry.needsHuman) flags.push("needed a human");
      const flagText = flags.length ? ` (${flags.join(", ")})` : "";
      return `<tr><td>${esc(entry.time)}</td><td>${esc(typeLabel)}</td><td><strong>${esc(entry.title)}</strong>${esc(flagText)}<br>${esc(entry.body)}</td></tr>`;
    })
    .join("\n");

  const checkRows = (data.checks ?? [])
    .map(
      (check) =>
        `<tr><th scope="row">${esc(check.label)}</th><td>${esc(check.state)}</td><td>${esc(check.detail)}</td></tr>`,
    )
    .join("\n");

  return `
<section class="acta-section" aria-labelledby="gate-title">
<h2 id="gate-title" class="acta-h2"><span class="sn">01</span>Resolved STOP gate</h2>
<div class="acta-call is-positive"><span class="c-k">${esc(decision.id)} — ${esc(data.gate.title)}</span>
<p><strong>Resolution: ${esc(resolution ? resolution.label : decision.selection)}</strong>${esc(resolution ? ` — ${resolution.consequence}` : "")}</p>
<p>Rationale: ${esc(decision.rationale ?? "none volunteered")}. Accepted via ${esc(decision.acceptedVia)}.</p>
</div>
<p>Why work stopped: ${esc(data.gate.reason)}</p>
<p>Next authorized action at acceptance: ${esc(data.nextAction)}</p>
</section>
<section class="acta-section" aria-labelledby="timeline-title">
<h2 id="timeline-title" class="acta-h2"><span class="sn">02</span>Session timeline</h2>
<div class="tablewrap"><table class="acta-table">
<caption>Every session entry that preceded the resolution, in order</caption>
<thead><tr><th scope="col">Time</th><th scope="col">Type</th><th scope="col">Entry</th></tr></thead>
<tbody>
${timelineRows}
</tbody>
</table></div>
</section>
<section class="acta-section" aria-labelledby="checks-title">
<h2 id="checks-title" class="acta-h2"><span class="sn">03</span>Checks at close</h2>
<div class="tablewrap"><table class="acta-table">
<caption>Progress was ${esc(data.slices.done)} of ${esc(data.slices.total)} slices green, paused before ${esc(data.slices.current)}</caption>
<thead><tr><th scope="col">Check</th><th scope="col">State</th><th scope="col">Detail</th></tr></thead>
<tbody>
${checkRows}
</tbody>
</table></div>
</section>
<section class="acta-section" aria-labelledby="files-title">
<h2 id="files-title" class="acta-h2"><span class="sn">04</span>Changed files</h2>
<ul>${(data.files ?? []).map((file) => `<li>${esc(file)}</li>`).join("") || "<li>none recorded</li>"}</ul>
</section>
<section class="acta-section" aria-labelledby="unresolved-title">
<h2 id="unresolved-title" class="acta-h2"><span class="sn">05</span>Unresolved at acceptance</h2>
<ul>${(data.unresolved ?? []).map((item) => `<li>${esc(item)}</li>`).join("") || "<li>nothing recorded</li>"}</ul>
</section>`;
}
