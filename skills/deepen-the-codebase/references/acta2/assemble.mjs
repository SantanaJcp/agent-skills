/* Acta v2 shared assembly — the ONLY implementation that turns scenario /
 * canonical JSON into instrument and record HTML. The publisher materializer
 * imports it from design/acta2/lib/; every installed pilot skill ships a
 * verbatim copy in references/acta2/ next to export-core.mjs, so installed
 * skills generate artifacts from data with the exact same code (no
 * hand-editing of static HTML, no publisher dependency).
 *
 * Node built-ins only; no I/O here — callers read assets and pass strings.
 */

import { createHash } from "node:crypto";
import {
  buildCandidate,
  deriveStatus,
  initialWorking,
  validateCanonicalForRecord,
} from "./export-core.mjs";

/** @param {Array<string>} parts */
export function digest(parts) {
  const hash = createHash("sha256");
  for (const part of parts) hash.update(part).update("\0");
  return hash.digest("hex");
}

/** @param {unknown} value */
export function esc(value) {
  return String(value)
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;");
}

/** @param {unknown} data */
export function islandJson(data) {
  return JSON.stringify(data, null, 1).replaceAll("<", "\\u003c");
}

/** @param {string | null | undefined} revision */
function shortRevision(revision) {
  if (!revision) return "no source revision";
  return `rev ${String(revision).slice(0, 7)}`;
}

/** @param {any} data @param {string} roleLine */
function trustStrip(data, roleLine) {
  const inputs = (data.inputs ?? [])
    .map((/** @type {unknown} */ input) => `<span>${esc(input)}</span>`)
    .join("<br>");
  return `<details class="a2-trust">
<summary><span>${esc(data.skill)}</span><span class="t-sep">·</span><span>${esc(data.initiative)}</span><span class="t-sep">·</span><span>${esc(shortRevision(data.sourceRevision))}</span><span class="t-sep">·</span><span>${esc(roleLine)}</span></summary>
<dl>
<dt>Artifact</dt><dd>${esc(data.title)} — ${esc(roleLine)}</dd>
<dt>Producer skill</dt><dd>${esc(data.skill)}</dd>
<dt>Initiative</dt><dd>${esc(data.initiative)}</dd>
<dt>Source revision</dt><dd>${esc(data.sourceRevision ?? "not available")}</dd>
<dt>Inputs</dt><dd>${inputs || "none recorded"}</dd>
<dt>Acta</dt><dd>v{{VERSION}} · generated from structured scenario data · regenerate when inputs change</dd>
<dt>Authority</dt><dd>Working surface only. Canonical state lives in Markdown/JSON and changes solely after explicit acceptance in chat.</dd>
</dl>
</details>`;
}

/* Honest no-JS controls: every interactive control ships disabled and is
   enabled only after the runtime initializes successfully. Applied as a
   post-process over the assembled static markup (never over scripts or the
   data island, which are appended afterwards), so no renderer can forget it. */
/** @param {string} markup */
function disableControls(markup) {
  return markup.replace(/<(input|textarea|button)(?=[\s>])/g, "<$1 disabled data-a2-enable");
}

/**
 * @param {{
 *   name: string, version: string, data: any,
 *   baseCss: string, topologyCss: string, runtimeJs: string,
 *   inlineCore: string, instrumentJs: string,
 *   renderBody: (data: any, helpers: { esc: typeof esc }) => string,
 * }} options
 */
export function renderInstrumentHtml(options) {
  const { name, version, data } = options;
  if (data.skill !== name) {
    throw new Error(`Scenario skill ${data.skill} does not match ${name}.`);
  }
  const working = initialWorking(data);
  const status = deriveStatus(data, working);
  if (/approved|accepted|resolved|completed/.test(status.code)) {
    throw new Error(`${name}: instruments must never start in an accepted state.`);
  }
  const body = options.renderBody(data, { esc });
  const island = islandJson(data);
  const sha = digest([
    version,
    options.baseCss,
    options.topologyCss,
    options.runtimeJs,
    options.inlineCore,
    options.instrumentJs,
    island,
  ]);
  const staticMarkup = disableControls(`<a class="skip" href="#a2-main">Skip to content</a>
<div class="a2-integrity" role="alert">Integrity check failed: a displayed export no longer matches working state. Do not paste either export.</div>
<p class="a2-printnote">Working snapshot for reference only — the durable print artifact is the Acta record generated after acceptance.</p>
<header>
${trustStrip(data, "Acta v2 instrument — working state, candidate only").replaceAll("{{VERSION}}", esc(version))}
</header>
<main id="a2-main">
${body}
</main>
<section class="a2-export" aria-label="Candidate export">
<h2>Candidate export</h2>
<p class="x-note">Derived live from your working state above. Copy it, paste it in chat, and confirm — this page never updates files by itself.</p>
<div class="x-actions">
<button type="button" class="a2-btn is-primary" data-copy-from="a2-export-md" data-copy-label="Candidate Markdown">Copy candidate Markdown</button>
<button type="button" class="a2-btn" data-copy-from="a2-export-json" data-copy-label="Candidate JSON">Copy candidate JSON</button>
<span class="a2-live" data-a2-live aria-live="polite"></span>
</div>
<p class="a2-jsnote">JavaScript is off, so these copy controls stay disabled. State your decision in chat instead; the agent records it only after your explicit confirmation.</p>
<details class="a2-more" open><summary>Markdown payload (derived, never pre-authored)</summary><div><pre id="a2-export-md" data-derived-export="markdown">(The candidate appears here while JavaScript runs. Without JavaScript, state your choice in chat instead.)</pre></div></details>
<details class="a2-more"><summary>JSON payload</summary><div><pre id="a2-export-json" data-derived-export="json">(derived from working state)</pre></div></details>
<p class="visually-hidden" data-selftest></p>
</section>
<noscript><div class="a2-noscript">JavaScript is off. Everything above remains readable and every control is disabled — nothing here only pretends to work. Decide by replying in chat (for example, “choose Path A — rationale: …”); the agent records it only after your explicit confirmation.</div></noscript>`);

  return `<!-- acta2-materialized: v${version} instrument=${name} sha256=${sha}; do not edit by hand — regenerate from scenario JSON -->
<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>${esc(data.title)} — instrument · Acta v2</title>
<style>
${options.baseCss}
/* ---- ${name} topology ---- */
${options.topologyCss}</style>
</head>
<body data-acta2-status="${esc(status.code)}" data-acta2-integrity="ok">
${staticMarkup}
<script type="application/json" id="acta2-data">${island}</script>
<script>
${options.inlineCore}
${options.runtimeJs}
${options.instrumentJs}</script>
</body>
</html>
`;
}

/**
 * Records are generated from accepted canonical state ONLY: callers pass the
 * parsed canonical document ({ scenario, accepted }) and nothing else.
 * @param {{
 *   name: string, version: string,
 *   canonical: { scenario: any, accepted: any },
 *   actaCss: string,
 *   renderRecord: (scenario: any, accepted: any, helpers: { esc: typeof esc }) => string,
 * }} options
 */
export function renderRecordHtml(options) {
  const { name, version, canonical } = options;
  /* Shared boundary: only genuinely accepted canonical state may become a
     record — same gate for the publisher and every installed bundle. */
  validateCanonicalForRecord(canonical);
  const scenario = canonical.scenario;
  const accepted = canonical.accepted;
  if (scenario.skill !== name) {
    throw new Error(`Canonical scenario skill ${scenario.skill} does not match ${name}.`);
  }
  const body = options.renderRecord(scenario, accepted, { esc });
  const sha = digest([version, options.actaCss, JSON.stringify(canonical)]);
  const inputs = (scenario.inputs ?? [])
    .map((/** @type {unknown} */ input, /** @type {number} */ index) => `<li>[E${index + 1}] ${esc(input)}</li>`)
    .join("\n");
  return `<!-- acta2-materialized: v${version} record=${name} sha256=${sha}; do not edit by hand — regenerate from canonical JSON -->
<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>${esc(scenario.title)} — record · Acta</title>
<style>
${options.actaCss}</style>
</head>
<body>
<a class="skip" href="#acta-content">Skip to content</a>
<div class="acta-shell">
<header>
<dl class="acta-prov">
<div><dt>Artifact</dt><dd>${esc(scenario.title)} — accepted record</dd></div>
<div><dt>Skill</dt><dd>${esc(scenario.skill)}</dd></div>
<div><dt>Initiative</dt><dd>${esc(scenario.initiative)}</dd></div>
<div><dt>Status</dt><dd>${esc(accepted.status)}</dd></div>
<div><dt>Source revision</dt><dd>${esc(scenario.sourceRevision ?? "not available")}</dd></div>
</dl>
<p class="acta-prov-note">Acta v${esc(version)} record · Generated from accepted canonical state (${esc(accepted.canonicalPath)}) after explicit acceptance${esc(accepted.acceptedVia ? ` (${accepted.acceptedVia})` : "")} · Never generated from browser state.</p>
<div class="acta-context">
<p class="acta-eyebrow">${esc(scenario.kind)} record · <span class="acta-stamp is-approved">${esc(accepted.stamp)}</span></p>
<h1 class="acta-title">${esc(accepted.recordTitle)}</h1>
<p class="acta-lede">${esc(accepted.summary)}</p>
</div>
</header>
<main id="acta-content">
${body}
</main>
<section id="acta-sources" class="acta-section"><h2 class="acta-h2">Sources</h2><ol class="acta-sources">
${inputs}
</ol></section>
<footer class="acta-colophon"><p>Acta is a print-first engineering record. Fact = directly supported; Inference = reasoned from evidence; Simplification = deliberately reduced model. This record renders accepted canonical state only; open decisions live in the companion instrument.</p></footer>
</div>
</body>
</html>
`;
}

/** @param {{ scenario: any, accepted: any }} canonical */
export function renderCanonicalMarkdown(canonical) {
  const scenario = canonical.scenario;
  const accepted = canonical.accepted;
  const decisions = (accepted.decisions ?? [])
    .map(
      (/** @type {any} */ decision) =>
        `  - id: ${JSON.stringify(decision.id)}\n    selection: ${JSON.stringify(decision.selection)}\n    rationale: ${JSON.stringify(decision.rationale ?? null)}\n    accepted_via: ${JSON.stringify(decision.acceptedVia)}`,
    )
    .join("\n");
  return `---
acta_protocol: "0.2"
artifact_kind: ${JSON.stringify(scenario.artifactKind)}
producer_skill: ${JSON.stringify(scenario.skill)}
initiative: ${JSON.stringify(scenario.initiative)}
status: ${JSON.stringify(accepted.status)}
phase: "accepted"
language: "en"
source_revision: ${scenario.sourceRevision ? JSON.stringify(scenario.sourceRevision) : "null"}
inputs:
${(scenario.inputs ?? []).map((/** @type {unknown} */ input) => `  - ${JSON.stringify(input)}`).join("\n")}
decisions:
${decisions}
supersedes: null
---

${accepted.canonicalBody}
${modelStateSection(accepted)}`;
}

/** Model-kind canonical state must be regenerable from canonical files alone:
 * serialize the accepted parameters, toggles, and conclusion when present.
 * @param {any} accepted */
function modelStateSection(accepted) {
  const working = accepted.exampleWorking;
  if (!working || !working.params) return "";
  const lines = ["", "## Accepted model state", ""];
  for (const [key, value] of Object.entries(working.params)) {
    lines.push(`- param ${key}: ${value}`);
  }
  for (const [key, value] of Object.entries(working.toggles ?? {})) {
    lines.push(`- toggle ${key}: ${value}`);
  }
  if (working.conclusion) lines.push(`- conclusion: ${working.conclusion}`);
  lines.push("");
  return lines.join("\n");
}

/** Example candidate payloads for fixtures/documentation.
 * @param {any} scenario @param {any} working */
export function renderCandidate(scenario, working) {
  return buildCandidate(scenario, working);
}
