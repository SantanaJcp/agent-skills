/* Record body for what-just-happened: an evidence-backed incident record.
   Every timeline entry is epistemically typed — fact, hypothesis (kept even
   when falsified), mitigation, recovery — and follow-ups are a static list:
   no fake active-incident controls, no invented owners. */

import { highlightJs } from "./highlight.mjs";

const TYPE_LABELS = {
  fact: "fact",
  hypothesis: "hypothesis",
  mitigation: "mitigation",
  recovery: "recovery",
};

export function renderRecord(data, accepted, { esc }) {
  const chips = [
    { text: data.severity, tone: "danger" },
    { text: data.state, tone: "positive" },
    { text: `duration ${data.duration}`, tone: "plain" },
    { text: `detected ${data.detected}`, tone: "plain" },
  ]
    .map((chip) => `<span class="wjh-chip is-${esc(chip.tone)}">${esc(chip.text)}</span>`)
    .join("");

  const timeline = data.timeline
    .map(
      (entry) => `
<li class="wjh-entry" data-type="${esc(entry.type)}"${entry.marker ? ` data-marker="${esc(entry.marker)}"` : ""}>
<span class="wjh-dot" aria-hidden="true"></span>
<div class="wjh-entry-body">
<p class="wjh-entry-head"><span class="wjh-time">${esc(entry.time)}</span><span class="wjh-type">${esc(TYPE_LABELS[entry.type] ?? entry.type)}</span></p>
<p class="wjh-entry-title">${esc(entry.title)}</p>
<p class="wjh-entry-text">${esc(entry.body)}</p>
</div>
</li>`,
    )
    .join("\n");

  return `
<p class="wjh-chips">${chips}</p>
<section class="acta-section" aria-labelledby="tldr-title">
<h2 id="tldr-title" class="acta-h2">TL;DR</h2>
<div class="wjh-tldr"><span class="r-k">What happened</span>
<p>${esc(data.tldr)}</p>
</div>
<div class="r-facts">
${data.impact
    .map((item) => `<div class="r-fact"><b>${esc(item.value)}</b><span>${esc(item.label)}</span></div>`)
    .join("\n")}
</div>
</section>
<section class="acta-section" aria-labelledby="timeline-title">
<h2 id="timeline-title" class="acta-h2">Timeline</h2>
<p class="wjh-legend">Entries are typed: <strong>fact</strong> (directly supported), <strong>hypothesis</strong> (kept even when falsified), <strong>mitigation</strong>, <strong>recovery</strong>.</p>
<ol class="wjh-timeline">
${timeline}
</ol>
</section>
<section class="acta-section" aria-labelledby="cause-title">
<h2 id="cause-title" class="acta-h2">Root cause</h2>
<p>${esc(data.rootCause)}</p>
<div class="a2-code"><div class="c-path">${esc(data.evidence.path)}</div><div class="codewrap"><pre><code>${highlightJs(data.evidence.snippet, esc)}</code></pre></div></div>
</section>
<section class="acta-section" aria-labelledby="conditions-title">
<h2 id="conditions-title" class="acta-h2">Contributing conditions</h2>
<ul class="wjh-conditions">
${data.conditions.map((item) => `<li>${esc(item)}</li>`).join("\n")}
</ul>
</section>
<section class="acta-section" aria-labelledby="followups-title">
<h2 id="followups-title" class="acta-h2">Follow-ups</h2>
<ul class="wjh-followups">
${data.followUps
    .map(
      (item) =>
        `<li data-state="${esc(item.state)}"><span class="wjh-state" aria-hidden="true">${item.state === "done" ? "✓" : "○"}</span><span class="visually-hidden">${esc(item.state)}:</span> ${esc(item.text)}</li>`,
    )
    .join("\n")}
</ul>
</section>`;
}
