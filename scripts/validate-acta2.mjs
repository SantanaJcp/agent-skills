#!/usr/bin/env node

/* Acta v2 pilot static validator.
 *
 * Technical-integrity gates (criteria-v2 Part I, automatable subset) plus the
 * v2-specific state/export invariants that the a8b0837 audit found violated:
 *   - instruments must never claim acceptance or preselect a decision;
 *   - instruments must never embed a static export payload;
 *   - records must be control-free and script-free;
 *   - realistic fixtures must be genuinely open and non-degenerate.
 */

import { access, readFile } from "node:fs/promises";
import path from "node:path";
import { fileURLToPath, pathToFileURL } from "node:url";
import { parse } from "parse5";

/* export-core is loaded from THIS script's repo (not --root) so temp-tree
   validation runs do not need a design/ copy. */
const scriptRepoRoot = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");
const { deriveBackoff, deriveQuizScore } = await import(
  pathToFileURL(path.join(scriptRepoRoot, "design", "acta2", "lib", "export-core.mjs")).href
);
const { SUITE, variantSuffix } = await import(
  pathToFileURL(path.join(scriptRepoRoot, "design", "acta2", "lib", "suite.mjs")).href
);

const args = process.argv.slice(2);
const rootIndex = args.indexOf("--root");
const rootArgument = rootIndex >= 0 ? args[rootIndex + 1] : undefined;
if (rootIndex >= 0 && rootArgument === undefined) {
  throw new Error("--root requires a directory argument.");
}
const root = path.resolve(rootArgument ?? process.cwd());
const kinds = Object.fromEntries(SUITE.map((skill) => [skill.name, skill.kind]));
/** @type {string[]} */
const errors = [];

/** @param {any} node @param {(node: any) => void} visit */
function walk(node, visit) {
  visit(node);
  for (const child of node.childNodes ?? []) walk(child, visit);
  if (node.content) walk(node.content, visit);
}

/** @param {any} node */
function textOf(node) {
  let text = "";
  walk(node, (candidate) => {
    if (candidate.nodeName === "#text") text += candidate.value;
  });
  return text;
}

/** @param {any} node @param {string} name */
function attr(node, name) {
  for (const attribute of node.attrs ?? []) {
    if (attribute.name === name) return attribute.value;
  }
  return null;
}

/** @param {string} hex */
function relativeLuminance(hex) {
  const normalized = hex.trim().replace(/^#/, "");
  if (!/^(?:[a-f0-9]{3}|[a-f0-9]{6})$/i.test(normalized)) return null;
  const expanded = normalized.length === 3 ? [...normalized].map((c) => c + c).join("") : normalized;
  const linear = [0, 2, 4].map((offset) => {
    const value = Number.parseInt(expanded.slice(offset, offset + 2), 16) / 255;
    return value <= 0.04045 ? value / 12.92 : ((value + 0.055) / 1.055) ** 2.4;
  });
  const [red = 0, green = 0, blue = 0] = linear;
  return 0.2126 * red + 0.7152 * green + 0.0722 * blue;
}

/** @param {string} source @param {string} location */
function validateTokens(source, location) {
  const tokens = new Map();
  for (const match of source.matchAll(/(--acta-[a-z0-9-]+)\s*:\s*([^;}]+)/g)) {
    const key = match[1];
    const value = match[2];
    if (key && value && !tokens.has(key)) tokens.set(key, value.trim());
  }
  /** @type {Array<[string, string, number]>} */
  const pairs = [
    ["--acta-ink", "--acta-paper", 4.5],
    ["--acta-ink-muted", "--acta-paper", 4.5],
    ["--acta-rule-strong", "--acta-paper", 3],
    ["--acta-action", "--acta-paper", 4.5],
    ["--acta-positive", "--acta-paper", 4.5],
    ["--acta-warning", "--acta-paper", 4.5],
    ["--acta-danger", "--acta-paper", 4.5],
    ["--acta-action", "--acta-action-tint", 4.5],
    ["--acta-positive", "--acta-positive-tint", 4.5],
    ["--acta-warning", "--acta-warning-tint", 4.5],
    ["--acta-danger", "--acta-danger-tint", 4.5],
  ];
  for (const [foregroundName, backgroundName, minimum] of pairs) {
    const foreground = tokens.get(foregroundName);
    const background = tokens.get(backgroundName);
    const fl = foreground ? relativeLuminance(foreground) : null;
    const bl = background ? relativeLuminance(background) : null;
    const ratio = fl !== null && bl !== null ? (Math.max(fl, bl) + 0.05) / (Math.min(fl, bl) + 0.05) : null;
    if (ratio === null || ratio < minimum) {
      errors.push(`${location}: contrast ${foregroundName} on ${backgroundName} is ${ratio === null ? "unavailable" : ratio.toFixed(2) + ":1"}; expected at least ${minimum}:1.`);
    }
  }
  for (const match of source.matchAll(/border-radius\s*:\s*([^;}]+)/gi)) {
    const value = (match[1] ?? "").trim();
    /* --mk-* radii belong to the fictional product mockups rendered INSIDE
       stages (interface-directions); Acta chrome itself stays on the two
       sanctioned tokens. */
    if (!["var(--acta-radius)", "var(--acta-radius-lg)", "50%", "var(--mk-radius)", "var(--mk-pill)"].includes(value)) {
      errors.push(`${location}: unsupported radius declaration ${value}.`);
    }
  }
}

/** Shared technical gates for any v2 HTML file.
 * @param {string} source @param {string} location */
function validateHtmlSafety(source, location) {
  const document = parse(source, { sourceCodeLocationInfo: true });
  const ids = new Set();
  /** @type {string[]} */
  const references = [];
  let doctype = false;
  walk(document, (node) => {
    if (node.nodeName === "#documentType") doctype = true;
    for (const attribute of node.attrs ?? []) {
      if (/^on/i.test(attribute.name)) errors.push(`${location}: inline event handler ${attribute.name} is forbidden.`);
      if (attribute.name === "id") {
        if (ids.has(attribute.value)) errors.push(`${location}: duplicate id ${attribute.value}.`);
        ids.add(attribute.value);
      }
      if (["href", "src"].includes(attribute.name) && /^https?:/i.test(attribute.value)) {
        errors.push(`${location}: network resource ${attribute.value} is forbidden.`);
      }
      if (["for", "aria-labelledby", "aria-describedby"].includes(attribute.name)) {
        references.push(...attribute.value.split(/\s+/));
      }
    }
  });
  for (const target of references) {
    if (target && !ids.has(target)) errors.push(`${location}: reference to missing id ${target}.`);
  }
  if (!doctype) errors.push(`${location}: missing HTML doctype.`);
  const forbidden = [
    { expression: /\b(?:innerHTML|outerHTML|insertAdjacentHTML|document\.write|eval)\b/, label: "unsafe DOM or evaluation sink" },
    { expression: /\b(?:localStorage|sessionStorage|indexedDB)\b/, label: "browser storage" },
    { expression: /@import\b|url\(\s*["']?https?:/i, label: "network CSS" },
    { expression: /\bfetch\s*\(|XMLHttpRequest|WebSocket|navigator\.sendBeacon/, label: "network API" },
    { expression: /box-shadow\s*:/i, label: "shadow declaration" },
    { expression: /\bMath\.random\b|\bDate\.now\b|new Date\(\)/, label: "nondeterministic source" },
  ];
  for (const { expression, label } of forbidden) {
    if (expression.test(source)) errors.push(`${location}: contains forbidden ${label}.`);
  }
  return document;
}

/** @param {string} source @param {string} location @param {string} name
 * @param {{ fixture: boolean }} options */
function validateInstrument(source, location, name, options) {
  if (!new RegExp(`^<!-- acta2-materialized: v0\\.2\\.0 instrument=${name} sha256=[a-f0-9]{64}; do not edit by hand[^>]*-->`).test(source)) {
    errors.push(`${location}: invalid materialization marker.`);
  }
  const document = validateHtmlSafety(source, location);
  validateTokens(source, location);
  for (const required of [
    "@media print",
    "prefers-reduced-motion",
    ".codewrap,.tablewrap,.flowwrap{overflow-x:auto}",
    "@media (max-width:719px)",
    'aria-live="polite"',
    "data-acta2-reset",
    'data-derived-export="markdown"',
    'data-derived-export="json"',
    "data-a2-live",
    "data-selftest",
    'class="a2-trust"',
    'id="acta2-data"',
    'class="a2-jsnote"',
    'class="a2-printnote"',
  ]) {
    if (!source.includes(required)) errors.push(`${location}: missing required Acta v2 contract ${required}.`);
  }
  let noscript = false;
  /** @type {string | null} */
  let island = null;
  /** @type {any[]} */
  const exportNodes = [];
  /** @type {any[]} */
  const checkedDecisionRadios = [];
  /** @type {any[]} */
  const optionArticles = [];
  let dataEntries = 0;
  let svgCount = 0;
  let paramInputs = 0;
  let enabledControls = 0;
  walk(document, (node) => {
    if (node.tagName === "noscript") noscript = true;
    if (node.tagName === "svg") svgCount += 1;
    if (node.tagName === "script" && attr(node, "id") === "acta2-data") island = textOf(node);
    if (attr(node, "data-derived-export")) exportNodes.push(node);
    if (["input", "button", "textarea", "select"].includes(node.tagName ?? "")) {
      // Honest no-JS: every control ships disabled and runtime-enabled.
      if (attr(node, "disabled") === null || attr(node, "data-a2-enable") === null) {
        enabledControls += 1;
      }
    }
    if (node.tagName === "input") {
      const inputName = attr(node, "name");
      if ((inputName === "acta2-option" || inputName === "acta2-resolution") && attr(node, "checked") !== null) {
        checkedDecisionRadios.push(node);
      }
      if (attr(node, "data-param") !== null) paramInputs += 1;
    }
    if (attr(node, "data-option")) optionArticles.push(node);
    if (attr(node, "data-entry")) dataEntries += 1;
  });
  if (enabledControls > 0) {
    errors.push(`${location}: ${enabledControls} control(s) ship enabled; static controls must be disabled with data-a2-enable until the runtime initializes.`);
  }
  if (!noscript) errors.push(`${location}: missing no-script fallback.`);
  if (island === null) {
    errors.push(`${location}: missing acta2-data island.`);
    return;
  }
  let data;
  try {
    data = JSON.parse(island);
  } catch {
    errors.push(`${location}: acta2-data island is not valid JSON.`);
    return;
  }
  if (data.kind !== kinds[name]) errors.push(`${location}: island kind ${data.kind} does not match ${kinds[name]}.`);
  if (data.skill !== name) errors.push(`${location}: island skill ${data.skill} does not match ${name}.`);

  for (const exportNode of exportNodes) {
    const content = textOf(exportNode);
    if (/payload|acta_protocol|status:/.test(content)) {
      errors.push(`${location}: static export payload detected — exports must be derived from working state only.`);
    }
  }
  if (/acta2-status="(?:approved|accepted|resolved|completed)"/.test(source) || /class="[^"]*is-approved/.test(source)) {
    errors.push(`${location}: instrument claims an accepted state; instruments carry working state only.`);
  }
  if (checkedDecisionRadios.length > 0) {
    errors.push(`${location}: a decision control is preselected; gates must open undecided.`);
  }
  const bodyStatus = source.match(/<body[^>]*data-acta2-status="([^"]+)"/);
  if (!bodyStatus || !["open-unselected", "stopped", "exploring"].includes(bodyStatus[1] ?? "")) {
    errors.push(`${location}: instrument must start in an open working status.`);
  }

  if (options.fixture) {
    if (/\[[a-z][a-z0-9 -]*(?:slug|placeholder|insert|structural|confirmed)[a-z0-9 -]*\]/i.test(island)) {
      errors.push(`${location}: realistic fixture still contains scaffold placeholders.`);
    }
    if (name === "three-code-paths") {
      if (optionArticles.length !== 3) {
        errors.push(`${location}: expected exactly three option columns.`);
      } else {
        const texts = optionArticles.map((node) => textOf(node).replace(/\s+/g, " ").trim());
        if (new Set(texts).size !== 3) {
          errors.push(`${location}: comparison options are duplicated — equal fidelity requires distinct content.`);
        }
      }
    }
    if (name === "build-with-notes") {
      if (dataEntries < 5) errors.push(`${location}: monitoring fixture needs a realistic timeline (found ${dataEntries} entries).`);
      for (const filter of ["deviations", "needs-human"]) {
        if (!source.includes(`data-filter="${filter}"`)) errors.push(`${location}: missing attention filter ${filter}.`);
      }
    }
    if (name === "concept-lab") {
      if (svgCount < 1) errors.push(`${location}: model fixture must render its spatial visualization.`);
      if (paramInputs < 3) errors.push(`${location}: model fixture must expose real parameter controls.`);
    }
  }
}

/** @param {string} source @param {string} location @param {string} name */
function validateRecord(source, location, name) {
  if (!new RegExp(`^<!-- acta2-materialized: v0\\.2\\.0 record=${name} sha256=[a-f0-9]{64}; do not edit by hand[^>]*-->`).test(source)) {
    errors.push(`${location}: invalid materialization marker.`);
  }
  const document = validateHtmlSafety(source, location);
  let scripts = 0;
  let controls = 0;
  walk(document, (node) => {
    if (node.tagName === "script") scripts += 1;
    if (["button", "input", "select", "textarea"].includes(node.tagName ?? "")) controls += 1;
  });
  if (scripts > 0) errors.push(`${location}: records are static; no scripts allowed.`);
  if (controls > 0) errors.push(`${location}: records must not carry interactive controls.`);
  if (source.includes('payload: "candidate"')) errors.push(`${location}: record contains candidate payload language.`);
  if (!source.includes('class="acta-prov"')) errors.push(`${location}: record must keep the full Acta provenance header.`);
  if (!source.includes("accepted canonical state")) errors.push(`${location}: record must declare its accepted-state basis.`);
}

const SHARED_BUNDLE_FILES = [
  "bundle.json",
  "export-core.mjs",
  "highlight.mjs",
  "flow.mjs",
  "figure.mjs",
  "assemble.mjs",
  "base.css",
  "runtime.js",
];
const INSTRUMENT_BUNDLE_FILES = ["body.mjs", "topology.css", "instrument.js", "generate-instrument.mjs"];
const RECORD_BUNDLE_FILES = ["record-body.mjs", "acta-record.css", "generate-record.mjs"];

for (const skill of SUITE) {
  const name = skill.name;
  const hasInstrument = skill.instruments.length > 0;
  const BUNDLE_FILES = [
    ...SHARED_BUNDLE_FILES,
    ...(hasInstrument ? INSTRUMENT_BUNDLE_FILES : []),
    ...(skill.record ? RECORD_BUNDLE_FILES : []),
  ];
  const referencesRoot = `skills/${name}/references`;
  const protocol = await readFile(path.join(root, referencesRoot, "acta2-protocol.md"), "utf8");
  if (!/^<!-- acta2-materialized: v0\.2\.0 protocol sha256=[a-f0-9]{64}; do not edit by hand -->/.test(protocol)) {
    errors.push(`${referencesRoot}/acta2-protocol.md: invalid materialization marker.`);
  }

  /* Self-contained generator bundle: present, offline, and standalone. */
  for (const file of BUNDLE_FILES) {
    const bundlePath = path.join(root, referencesRoot, "acta2", file);
    try {
      await access(bundlePath);
    } catch {
      errors.push(`${referencesRoot}/acta2/${file}: missing generator-bundle file.`);
      continue;
    }
    if (file.endsWith(".mjs") || file.endsWith(".js")) {
      const source = await readFile(bundlePath, "utf8");
      if (/node:(?:http|https|net|tls|dgram|dns|child_process)/.test(source)) {
        errors.push(`${referencesRoot}/acta2/${file}: bundle modules must not use network or process modules.`);
      }
      if (/from "\.\.\//.test(source)) {
        errors.push(`${referencesRoot}/acta2/${file}: bundle modules must only import bundled siblings.`);
      }
    }
  }
  const bundleMeta = JSON.parse(await readFile(path.join(root, referencesRoot, "acta2", "bundle.json"), "utf8"));
  if (bundleMeta.skill !== name || bundleMeta.kind !== kinds[name]) {
    errors.push(`${referencesRoot}/acta2/bundle.json: skill/kind mismatch.`);
  }
  for (const variant of skill.instruments) {
    const suffix = variantSuffix(variant);
    validateInstrument(
      await readFile(path.join(root, referencesRoot, `instrument${suffix}.html`), "utf8"),
      `${referencesRoot}/instrument${suffix}.html`,
      name,
      { fixture: false },
    );
  }
  if (skill.record) {
    validateRecord(
      await readFile(path.join(root, referencesRoot, "record.html"), "utf8"),
      `${referencesRoot}/record.html`,
      name,
    );
  }

  const fixtureRoot = `tests/fixtures/acta2/${name}`;
  for (const variant of skill.instruments) {
    const suffix = variantSuffix(variant);
    validateInstrument(
      await readFile(path.join(root, fixtureRoot, `instrument${suffix}.html`), "utf8"),
      `${fixtureRoot}/instrument${suffix}.html`,
      name,
      { fixture: true },
    );
  }
  if (skill.record) {
    validateRecord(
      await readFile(path.join(root, fixtureRoot, "record.html"), "utf8"),
      `${fixtureRoot}/record.html`,
      name,
    );
  }
  if (hasInstrument && (skill.record || skill.workingFixture)) {
    const candidate = await readFile(path.join(root, fixtureRoot, "candidate.md"), "utf8");
    if (!candidate.includes('payload: "candidate"')) {
      errors.push(`${fixtureRoot}/candidate.md: candidate export must be marked candidate.`);
    }
    if (/^status: "(?:approved|completed)"/m.test(candidate)) {
      errors.push(`${fixtureRoot}/candidate.md: candidates must not claim canonical statuses.`);
    }
    const candidateJson = JSON.parse(await readFile(path.join(root, fixtureRoot, "candidate.json"), "utf8"));
    if (candidateJson.payload !== "candidate") {
      errors.push(`${fixtureRoot}/candidate.json: payload must be "candidate".`);
    }
  }
  if (!skill.record) continue;
  const canonical = await readFile(path.join(root, fixtureRoot, "canonical.md"), "utf8");
  if (!/^phase: "accepted"/m.test(canonical)) {
    errors.push(`${fixtureRoot}/canonical.md: accepted canonical state must carry phase "accepted".`);
  }
  if (!/accepted_via:/.test(canonical)) {
    errors.push(`${fixtureRoot}/canonical.md: decisions must record how they were accepted.`);
  }

  /* Structured canonical state: complete, coherent, and record-sufficient. */
  const candidateVariantSuffix = variantSuffix(hasInstrument ? (skill.candidateVariant ?? "default") : "default");
  const scenarioJson = JSON.parse(
    await readFile(path.join(root, fixtureRoot, `scenario${candidateVariantSuffix}.json`), "utf8"),
  );
  const canonicalJson = JSON.parse(await readFile(path.join(root, fixtureRoot, "canonical.json"), "utf8"));
  if (!canonicalJson.scenario || !canonicalJson.accepted) {
    errors.push(`${fixtureRoot}/canonical.json: must contain scenario and accepted blocks.`);
  } else {
    if (JSON.stringify(canonicalJson.scenario) !== JSON.stringify(scenarioJson)) {
      errors.push(`${fixtureRoot}/canonical.json: scenario block drifted from scenario.json.`);
    }
    if (!Array.isArray(canonicalJson.accepted.decisions) || canonicalJson.accepted.decisions.length === 0) {
      errors.push(`${fixtureRoot}/canonical.json: accepted state must record at least one decision.`);
    }
    /* Epistemic consistency: quiz-kind scores must equal the recompute. */
    if (canonicalJson.scenario.kind === "quiz") {
      const working = canonicalJson.accepted.exampleWorking;
      const derived = canonicalJson.accepted.derived;
      if (!working || !derived) {
        errors.push(`${fixtureRoot}/canonical.json: quiz canonical state needs exampleWorking and derived blocks.`);
      } else {
        const recomputed = deriveQuizScore(canonicalJson.scenario, working);
        if (derived.correct !== recomputed.correct || derived.total !== recomputed.total) {
          errors.push(`${fixtureRoot}/canonical.json: derived score disagrees with the answer key recompute.`);
        }
      }
    }
    /* Epistemic consistency: model-kind derived claims must equal deriveBackoff. */
    if (canonicalJson.scenario.kind === "model") {
      const working = canonicalJson.accepted.exampleWorking;
      const derived = canonicalJson.accepted.derived;
      if (!working || !derived) {
        errors.push(`${fixtureRoot}/canonical.json: model canonical state needs exampleWorking and derived blocks.`);
      } else {
        const recomputed = deriveBackoff(working.params, working.toggles);
        const firstCapped = recomputed.rows.find((row) => row.cappedAtLimit);
        if (
          derived.worstCaseTotalMs !== recomputed.totals.worstCaseTotalMs ||
          derived.expectedTotalMs !== recomputed.totals.expectedTotalMs ||
          derived.attempts !== recomputed.totals.attempts ||
          (derived.firstCappedAttempt ?? null) !== (firstCapped ? firstCapped.attempt : null)
        ) {
          errors.push(`${fixtureRoot}/canonical.json: derived block disagrees with deriveBackoff — the recorded conclusion is not supported by the model.`);
        }
        const conclusion = String(working.conclusion ?? "");
        // The comparison jitter mode is a legitimate derived quantity too.
        const flipped = deriveBackoff(working.params, { ...working.toggles, fullJitter: !working.toggles.fullJitter });
        for (const claim of conclusion.matchAll(/(\d[\d,]*)\s*ms/g)) {
          const value = Number((claim[1] ?? "").replaceAll(",", ""));
          const known = [
            recomputed.totals.worstCaseTotalMs,
            recomputed.totals.expectedTotalMs,
            flipped.totals.worstCaseTotalMs,
            flipped.totals.expectedTotalMs,
            working.params.cap,
            working.params.base,
          ];
          const approximate = known.map((quantity) => Math.round(quantity / 100) * 100);
          if (!known.includes(value) && !approximate.includes(value)) {
            errors.push(`${fixtureRoot}/canonical.json: conclusion cites ${value} ms, which matches no derived quantity.`);
          }
        }
      }
    }
  }
}

if (errors.length) {
  console.error(errors.map((error) => `ERROR: ${error}`).join("\n"));
  process.exit(1);
}
console.log(`Validated ${SUITE.length} Acta v2 skill bundles (instrument, record, candidate, canonical).`);
