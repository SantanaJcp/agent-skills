import assert from "node:assert/strict";
import { access, cp, mkdtemp, readFile, writeFile } from "node:fs/promises";
import path from "node:path";
import { spawnSync } from "node:child_process";
import test from "node:test";
import { tmpdir } from "node:os";
import { parse as parseYaml, parseDocument } from "yaml";

import {
  assertSafeInstrumentData,
  backoffPlotSpec,
  buildCandidate,
  deriveBackoff,
  deriveCounts,
  deriveStatus,
  filterEntries,
  initialWorking,
  INSTRUMENT_STATUSES,
} from "../design/acta2/lib/export-core.mjs";

import { SUITE, variantSuffix } from "../design/acta2/lib/suite.mjs";

const root = path.resolve(import.meta.dirname, "..");
/* Every generated instrument fixture across the suite (variant-aware). */
const instrumentTargets = SUITE.flatMap((skill) =>
  skill.instruments.map((variant) => ({
    name: skill.name,
    file: `instrument${variantSuffix(variant)}.html`,
  })),
);
const recordSkills = SUITE.filter((skill) => skill.record);

function skipBrowserProbes(t) {
  if (process.env.ACTA2_SKIP_BROWSER_PROBES === "1") {
    t.skip(
      "browser probes explicitly skipped; manual browser/AT evidence remains tracked in GitHub Issue #8",
    );
    return true;
  }
  return false;
}

function frontmatterOf(markdown) {
  const match = markdown.match(/^---\n([\s\S]*?)\n---\n/);
  assert.ok(match, "candidate markdown must start with YAML frontmatter");
  return parseYaml(match[1]);
}

const decisionData = {
  acta2: "0.2.0",
  kind: "decision",
  decisionId: "D-01",
  skill: "three-code-paths",
  artifactKind: "code-path-decision",
  initiative: "tag-filter",
  title: "Three code paths",
  question: "Where should tag filtering and URL-state logic live?",
  sourceRevision: "a8b083705553550eda289ddf9cf1d028df907682",
  inputs: ["src/catalog.mjs", "index.html"],
  options: [
    { id: "a", label: "Path A — functional core" },
    { id: "b", label: "Path B — custom element" },
    { id: "c", label: "Path C — pub/sub store" },
  ],
  recommendation: { option: "a", reason: "only shape without test-constraint tension" },
  unresolved: ["empty-state copy is owned by interface-directions"],
};

const stopGateData = {
  acta2: "0.2.0",
  kind: "stop-gate",
  skill: "build-with-notes",
  artifactKind: "implementation-session",
  initiative: "tag-filter",
  title: "Build with notes",
  question: "Remote-API scope addition conflicts with the approved spec — how do we proceed?",
  sourceRevision: "a8b083705553550eda289ddf9cf1d028df907682",
  inputs: ["spec.md", "implementation-plan.md"],
  gate: {
    id: "STOP-01",
    title: "Remote tag-suggestion API conflicts with approved non-goals",
    options: [
      { id: "reject-addition", label: "Reject the addition; continue the approved plan" },
      { id: "revise-blueprint", label: "Accept the addition; reopen change-blueprint first" },
      { id: "pause-session", label: "Pause the session entirely" },
    ],
  },
  entries: [
    { id: "e1", type: "plan-confirmed", title: "Slice 1 green", needsHuman: false },
    { id: "e2", type: "deviation", title: "URLSearchParams quirk", needsHuman: false },
    { id: "e3", type: "check", title: "node --test 12 pass", state: "pass", needsHuman: false },
    { id: "e4", type: "stop", title: "STOP-01 opened", needsHuman: true },
    { id: "e5", type: "discovery", title: "catalog.mjs already pure", needsHuman: false },
    { id: "e6", type: "deviation", title: "membership check for unknown tags", needsHuman: true },
  ],
  unresolved: ["commit authorization pending after STOP resolution"],
};

const modelData = {
  acta2: "0.2.0",
  kind: "model",
  decisionId: "D-01",
  acceptanceToken: "model-accepted",
  skill: "concept-lab",
  artifactKind: "concept-model",
  initiative: "retry-backoff",
  title: "Concept lab",
  question: "How do base delay, factor, and jitter shape total retry wait?",
  sourceRevision: null,
  inputs: ["https://aws.amazon.com/blogs/architecture/exponential-backoff-and-jitter/"],
  params: [
    { id: "base", label: "Base delay", min: 50, max: 1000, step: 50, default: 100, unit: "ms" },
    { id: "factor", label: "Growth factor", min: 1, max: 4, step: 0.5, default: 2, unit: "×" },
    { id: "retries", label: "Max retries", min: 1, max: 8, step: 1, default: 5, unit: "" },
    { id: "cap", label: "Delay cap", min: 500, max: 30000, step: 500, default: 10000, unit: "ms" },
  ],
  toggles: [{ id: "fullJitter", label: "Full jitter", default: false }],
  simplifications: ["assumes an ideal clock", "ignores network transfer time"],
  unresolved: [],
};

test("acta2 core: instruments can never claim acceptance", () => {
  for (const status of Object.values(INSTRUMENT_STATUSES)) {
    assert.doesNotMatch(status.code, /approved|accepted|completed|resolved/);
  }
  const selected = { ...initialWorking(decisionData), selected: "b" };
  assert.notEqual(deriveStatus(decisionData, selected).code, "approved");
});

test("acta2 core: decision status and export always agree (stale pattern 1)", () => {
  const open = initialWorking(decisionData);
  assert.equal(open.selected, null, "no option may be preselected");
  const openStatus = deriveStatus(decisionData, open);
  assert.equal(openStatus.code, "open-unselected");
  const openExport = buildCandidate(decisionData, open);
  assert.equal(frontmatterOf(openExport.markdown).status, "open-unselected");
  assert.equal(openExport.json.status, "open-unselected");

  const chosen = { ...open, selected: "b", rationale: "encapsulation matters here" };
  const chosenStatus = deriveStatus(decisionData, chosen);
  assert.equal(chosenStatus.code, "candidate-ready");
  const chosenExport = buildCandidate(decisionData, chosen);
  assert.equal(frontmatterOf(chosenExport.markdown).status, "candidate-ready");
  assert.equal(chosenExport.json.status, "candidate-ready");
  assert.notEqual(chosenExport.markdown, openExport.markdown, "changing selection must change the export");
});

test("acta2 core: a visible selection can never export empty decisions (stale pattern 2)", () => {
  const chosen = { ...initialWorking(decisionData), selected: "c" };
  const { markdown, json } = buildCandidate(decisionData, chosen);
  assert.equal(json.selection.option, "c");
  assert.equal(frontmatterOf(markdown).selected_option, "c");
  assert.match(markdown, /Path C — pub\/sub store/);
  const reset = buildCandidate(decisionData, initialWorking(decisionData));
  assert.equal(reset.json.selection.option, null);
});

test("acta2 core: resolving a STOP gate flips both status and export (stale pattern 3)", () => {
  const stopped = initialWorking(stopGateData);
  assert.equal(stopped.resolution, null);
  assert.equal(deriveStatus(stopGateData, stopped).code, "stopped");
  const stoppedExport = buildCandidate(stopGateData, stopped);
  assert.equal(stoppedExport.json.status, "stopped");
  assert.equal(stoppedExport.json.gate.state, "open");

  const resolved = { ...stopped, resolution: "reject-addition", rationale: "spec non-goals win" };
  assert.equal(deriveStatus(stopGateData, resolved).code, "candidate-ready");
  const resolvedExport = buildCandidate(stopGateData, resolved);
  assert.equal(resolvedExport.json.status, "candidate-ready");
  assert.equal(resolvedExport.json.gate.state, "resolution-proposed");
  assert.equal(resolvedExport.json.resolution.option, "reject-addition");
  assert.equal(frontmatterOf(resolvedExport.markdown).stop_resolution, "reject-addition");
  assert.match(resolvedExport.markdown, /explicit acceptance in chat/i, "export must state acceptance is still pending");
});

test("acta2 core: model export reflects the exact working parameters (stale pattern 4)", () => {
  const working = initialWorking(modelData);
  assert.deepEqual({ ...working.params }, { base: 100, factor: 2, retries: 5, cap: 10000 });
  const tuned = {
    ...working,
    params: { ...working.params, base: 200, retries: 3 },
    toggles: { fullJitter: true },
    conclusion: "with full jitter, worst case halves on average",
  };
  const { markdown, json } = buildCandidate(modelData, tuned);
  assert.deepEqual({ ...json.parameters }, { ...tuned.params });
  assert.equal(json.toggles.fullJitter, true);
  assert.equal(json.conclusion, tuned.conclusion);
  const front = frontmatterOf(markdown);
  assert.equal(front.param_base, 200);
  assert.equal(front.param_retries, 3);
  const derived = deriveBackoff(tuned.params, tuned.toggles);
  assert.equal(json.derived.worstCaseTotalMs, derived.totals.worstCaseTotalMs);
});

test("acta2 core: every candidate is marked candidate and carries provenance", () => {
  for (const data of [decisionData, stopGateData, modelData]) {
    const { markdown, json } = buildCandidate(data, initialWorking(data));
    const front = frontmatterOf(markdown);
    assert.equal(front.acta_protocol, "0.2");
    assert.equal(front.payload, "candidate");
    assert.equal(front.producer_skill, data.skill);
    assert.equal(front.initiative, data.initiative);
    assert.equal(front.artifact_kind, data.artifactKind);
    assert.equal(front.instrument, data.kind);
    assert.equal(json.payload, "candidate");
    assert.deepEqual(json.inputs, data.inputs);
    assert.equal(json.source_revision, data.sourceRevision);
    assert.deepEqual(json.unresolved, data.unresolved);
    assert.match(markdown, /candidate, not canonical/i);
  }
});

test("acta2 core: backoff model is deterministic and honest about jitter", () => {
  const equal = deriveBackoff({ base: 100, factor: 2, retries: 4, cap: 10000 }, { fullJitter: false });
  assert.equal(equal.rows.length, 4);
  assert.deepEqual(equal.rows.map((row) => row.delayMs), [100, 200, 400, 800]);
  assert.deepEqual(equal.rows[3].rangeMs, [400, 800]);
  assert.equal(equal.totals.worstCaseTotalMs, 1500);
  const capped = deriveBackoff({ base: 1000, factor: 4, retries: 5, cap: 5000 }, { fullJitter: false });
  assert.ok(capped.rows.every((row) => row.delayMs <= 5000));
  const full = deriveBackoff({ base: 100, factor: 2, retries: 4, cap: 10000 }, { fullJitter: true });
  assert.deepEqual(full.rows[3].rangeMs, [0, 800]);
  assert.equal(full.totals.worstCaseTotalMs, equal.totals.worstCaseTotalMs);
});

test("acta2 core: monitoring counts and filters derive from the same entries", () => {
  const counts = deriveCounts(stopGateData.entries);
  assert.equal(counts.all, 6);
  assert.equal(counts.deviations, 2);
  assert.equal(counts.needsHuman, 2);
  const deviations = filterEntries(stopGateData.entries, "deviations");
  assert.deepEqual(deviations.map((entry) => entry.id), ["e2", "e6"]);
  const needsHuman = filterEntries(stopGateData.entries, "needs-human");
  assert.deepEqual(needsHuman.map((entry) => entry.id), ["e4", "e6"]);
  assert.equal(filterEntries(stopGateData.entries, "all").length, 6);
});

test("acta2 core: candidate markdown and JSON are semantically equivalent", () => {
  const working = { ...initialWorking(decisionData), selected: "a", rationale: "matches repo idiom" };
  const { markdown, json } = buildCandidate(decisionData, working);
  const front = frontmatterOf(markdown);
  assert.equal(front.selected_option, json.selection.option);
  assert.equal(front.status, json.status);
  assert.match(markdown, /matches repo idiom/);
  assert.equal(json.selection.rationale, "matches repo idiom");
  const document = parseDocument(markdown.match(/^---\n([\s\S]*?)\n---\n/)?.[1] ?? "");
  assert.equal(document.errors.length, 0, "frontmatter must be valid YAML");
});

test("acta2 core: hostile identifiers are rejected before they reach YAML or state", () => {
  const hostileIds = [
    "a\nstatus: approved",
    "a: b",
    "__proto__",
    "constructor",
    "1leading-digit",
    "spaced id",
    "quote\"id",
    "",
  ];
  for (const hostile of hostileIds) {
    const data = {
      ...modelData,
      params: [{ id: hostile, label: "X", min: 0, max: 10, step: 1, default: 1, unit: "" }],
    };
    assert.throws(
      () => assertSafeInstrumentData(data),
      /identifier/i,
      `param id ${JSON.stringify(hostile)} must be rejected`,
    );
    assert.throws(() => initialWorking(data), /identifier/i);
  }
  const hostileToggle = {
    ...modelData,
    toggles: [{ id: "bad\ntoggle", label: "X", default: false }],
  };
  assert.throws(() => buildCandidate(hostileToggle, { params: {}, toggles: {}, conclusion: "" }), /identifier/i);

  const duplicated = {
    ...modelData,
    params: [
      { id: "base", label: "A", min: 0, max: 10, step: 1, default: 1, unit: "" },
      { id: "base", label: "B", min: 0, max: 10, step: 1, default: 2, unit: "" },
    ],
  };
  assert.throws(() => assertSafeInstrumentData(duplicated), /duplicate/i);

  const hostileOption = {
    ...decisionData,
    options: [
      { id: "ok", label: "fine" },
      { id: "evil\nid", label: "bad" },
    ],
  };
  assert.throws(() => initialWorking(hostileOption), /identifier/i);

  // prototype safety: state maps must not have Object.prototype chains
  const working = initialWorking(modelData);
  assert.equal(Object.getPrototypeOf(working.params), null);
  assert.equal(Object.getPrototypeOf(working.toggles), null);

  // valid ids with dashes/underscores still parse to equivalent YAML/JSON
  const dashed = {
    ...modelData,
    params: [{ id: "base_delay-ms", label: "Base", min: 0, max: 10, step: 1, default: 3, unit: "ms" }],
    toggles: [],
  };
  const dashedWorking = initialWorking(dashed);
  const { markdown, json } = buildCandidate(dashed, dashedWorking);
  const front = frontmatterOf(markdown);
  assert.equal(front["param_base_delay-ms"], 3);
  assert.equal(json.parameters["base_delay-ms"], 3);
});

test("acta2 core: build-with-notes filter is ephemeral view state, never exported", () => {
  const base = initialWorking(stopGateData);
  const filtered = { ...base, resolution: "reject-addition", filter: "needs-human" };
  const unfiltered = { ...base, resolution: "reject-addition", filter: "all" };
  const exportA = buildCandidate(stopGateData, filtered);
  const exportB = buildCandidate(stopGateData, unfiltered);
  assert.equal(exportA.markdown, exportB.markdown, "filter must not affect the candidate");
  assert.deepEqual(exportA.json, exportB.json);
  assert.equal("filter" in exportA.json, false, "filter is view state, not exported state");
  assert.doesNotMatch(exportA.markdown, /^filter:/m);
});

/* ------------------------------------------------------------------ */
/* Materialization, validation, and fixture integrity                  */
/* ------------------------------------------------------------------ */

function runScript(script, scriptArgs = []) {
  return spawnSync(process.execPath, [path.join(root, "scripts", script), ...scriptArgs], {
    cwd: root,
    encoding: "utf8",
  });
}

test("acta2 materializer output is current, marked, and self-contained", async () => {
  const check = runScript("materialize-acta2.mjs", ["--check"]);
  assert.equal(check.status, 0, `${check.stdout}\n${check.stderr}`);

  for (const skill of SUITE) {
    const name = skill.name;
    const protocol = await readFile(
      path.join(root, "skills", name, "references", "acta2-protocol.md"),
      "utf8",
    );
    assert.match(protocol, /^<!-- acta2-materialized: v0\.2\.0 protocol sha256=[a-f0-9]{64}; do not edit by hand -->/);

    const artifacts = /** @type {Array<[string, string]>} */ ([
      ...skill.instruments.map((variant) => [
        `instrument${variantSuffix(variant)}.html`,
        `instrument=${name}`,
      ]),
      ...(skill.record ? [["record.html", `record=${name}`]] : []),
    ]);
    for (const [file, marker] of artifacts) {
      for (const location of [
        path.join(root, "skills", name, "references", file),
        path.join(root, "tests", "fixtures", "acta2", name, file),
      ]) {
        const html = await readFile(location, "utf8");
        assert.match(
          html,
          new RegExp(`^<!-- acta2-materialized: v0\\.2\\.0 ${marker} sha256=[a-f0-9]{64}; do not edit by hand[^>]*-->`),
          location,
        );
        assert.doesNotMatch(html, /(?:src|href)=["']https?:/i, location);
        assert.doesNotMatch(html, /<link\b/i, `${location} must not reference external resources`);
        assert.doesNotMatch(html, /\bsrc=/i, `${location} must be fully inlined`);
        assert.doesNotMatch(html, /\son[a-z]+\s*=/i, location);
        assert.doesNotMatch(html, /\b(?:innerHTML|outerHTML|insertAdjacentHTML|document\.write|eval)\b/, location);
        assert.doesNotMatch(html, /localStorage|sessionStorage/, location);
        assert.doesNotMatch(html, /\r/, `${location} must be LF-only`);
      }
    }
    // Compatibility safety: Acta 0.1 references stay in place for every v2 skill.
    await access(path.join(root, "skills", name, "references", "acta-scaffold.html"));
    await access(path.join(root, "skills", name, "references", "acta-protocol.md"));
  }
});

test("acta2 instruments never ship resolved gates or static payloads", async () => {
  for (const { name, file } of instrumentTargets) {
    for (const location of [
      path.join(root, "skills", name, "references", file),
      path.join(root, "tests", "fixtures", "acta2", name, file),
    ]) {
      const html = await readFile(location, "utf8");
      assert.doesNotMatch(html, /is-approved/, `${location}: instruments must not claim acceptance`);
      assert.doesNotMatch(
        html,
        /name="acta2-(?:option|resolution)"[^>]*\bchecked\b/,
        `${location}: no decision control may be preselected`,
      );
      const exportBlock = html.match(/<pre id="a2-export-md"[^>]*>([\s\S]*?)<\/pre>/);
      assert.ok(exportBlock, `${location}: derived export node missing`);
      assert.doesNotMatch(
        exportBlock?.[1] ?? "",
        /payload|acta_protocol|status:/,
        `${location}: export node must not carry a static payload`,
      );
      assert.match(
        html,
        /<body[^>]*data-acta2-status="(?:open-unselected|stopped|exploring)"/,
        `${location}: instrument must start open`,
      );
    }
  }
});

test("acta2 realistic fixtures are open, distinct, and candidate-marked", async () => {
  const tcp = await readFile(
    path.join(root, "tests", "fixtures", "acta2", "three-code-paths", "instrument.html"),
    "utf8",
  );
  const articles = [...tcp.matchAll(/<article class="tcp-card" data-option="([a-z])">([\s\S]*?)<\/article>/g)];
  assert.equal(articles.length, 3, "three option columns");
  const bodies = new Set(articles.map((match) => (match[2] ?? "").replace(/\s+/g, " ")));
  assert.equal(bodies.size, 3, "comparison options must not duplicate content");

  const bwn = await readFile(
    path.join(root, "tests", "fixtures", "acta2", "build-with-notes", "instrument.html"),
    "utf8",
  );
  assert.match(bwn, /data-filter="deviations"/);
  assert.match(bwn, /data-filter="needs-human"/);
  assert.ok((bwn.match(/data-entry=/g) ?? []).length >= 5, "realistic timeline");

  const clab = await readFile(
    path.join(root, "tests", "fixtures", "acta2", "concept-lab", "instrument.html"),
    "utf8",
  );
  assert.match(clab, /<svg[^>]*role="img"/);
  assert.ok((clab.match(/data-param=/g) ?? []).length >= 3, "real parameter controls");

  for (const skill of SUITE) {
    const fixtureRoot = path.join(root, "tests", "fixtures", "acta2", skill.name);
    if (skill.instruments.length > 0 && (skill.record || skill.workingFixture)) {
      const candidate = await readFile(path.join(fixtureRoot, "candidate.md"), "utf8");
      assert.match(candidate, /payload: "candidate"/);
      const candidateJson = JSON.parse(await readFile(path.join(fixtureRoot, "candidate.json"), "utf8"));
      assert.equal(candidateJson.payload, "candidate");
    }
    if (skill.record) {
      const canonical = await readFile(path.join(fixtureRoot, "canonical.md"), "utf8");
      assert.match(canonical, /^phase: "accepted"/m);
      const record = await readFile(path.join(fixtureRoot, "record.html"), "utf8");
      assert.doesNotMatch(record, /<script/, "records are static");
      assert.doesNotMatch(record, /<(?:button|input|select|textarea)\b/, "records carry no controls");
      assert.match(record, /accepted canonical state/);
    }
  }
});

test("acta2 static validation accepts the tree and rejects violated invariants", async () => {
  const accepted = runScript("validate-acta2.mjs");
  assert.equal(accepted.status, 0, `${accepted.stdout}\n${accepted.stderr}`);

  const fixtureRoot = await mkdtemp(path.join(tmpdir(), "acta2-validate-"));
  await cp(path.join(root, "skills"), path.join(fixtureRoot, "skills"), { recursive: true });
  await cp(path.join(root, "tests", "fixtures", "acta2"), path.join(fixtureRoot, "tests", "fixtures", "acta2"), {
    recursive: true,
  });
  const target = path.join(fixtureRoot, "tests", "fixtures", "acta2", "three-code-paths", "instrument.html");
  const broken = (await readFile(target, "utf8"))
    .replace('name="acta2-option" value="a"', 'name="acta2-option" value="a" checked')
    .replace(
      /<pre id="a2-export-md"[^>]*>[\s\S]*?<\/pre>/,
      '<pre id="a2-export-md" data-derived-export="markdown">payload: "candidate"\nstatus: "approved"</pre>',
    );
  await writeFile(target, broken);

  const rejected = runScript("validate-acta2.mjs", ["--root", fixtureRoot]);
  assert.equal(rejected.status, 1);
  assert.match(rejected.stderr, /preselected/i);
  assert.match(rejected.stderr, /static export payload/i);
});

test("acta2 materialization is deterministic, repeatable, and version-locked", async () => {
  const fixtureRoot = await mkdtemp(path.join(tmpdir(), "acta2-materializer-"));
  await cp(path.join(root, "design"), path.join(fixtureRoot, "design"), { recursive: true });
  await cp(path.join(root, "skills"), path.join(fixtureRoot, "skills"), { recursive: true });

  const firstRun = runScript("materialize-acta2.mjs", ["--root", fixtureRoot]);
  assert.equal(firstRun.status, 0, `${firstRun.stdout}\n${firstRun.stderr}`);

  const snapshots = new Map();
  for (const skill of SUITE) {
    const name = skill.name;
    const files = [
      path.join("skills", name, "references", "acta2-protocol.md"),
      path.join("skills", name, "references", "acta2", "bundle.json"),
      path.join("skills", name, "references", "acta2", "assemble.mjs"),
      path.join("skills", name, "references", "acta2", "export-core.mjs"),
    ];
    for (const variant of skill.instruments) {
      const suffix = variantSuffix(variant);
      files.push(
        path.join("skills", name, "references", `instrument${suffix}.html`),
        path.join("tests", "fixtures", "acta2", name, `instrument${suffix}.html`),
        path.join("tests", "fixtures", "acta2", name, `scenario${suffix}.json`),
      );
    }
    if (skill.instruments.length > 0) {
      files.push(path.join("skills", name, "references", "acta2", "body.mjs"));
      files.push(path.join("skills", name, "references", "acta2", "generate-instrument.mjs"));
    }
    if (skill.instruments.length > 0 && (skill.record || skill.workingFixture)) {
      files.push(
        path.join("tests", "fixtures", "acta2", name, "candidate.md"),
        path.join("tests", "fixtures", "acta2", name, "candidate.json"),
      );
    }
    if (skill.record) {
      files.push(
        path.join("skills", name, "references", "record.html"),
        path.join("tests", "fixtures", "acta2", name, "record.html"),
        path.join("tests", "fixtures", "acta2", name, "canonical.md"),
        path.join("tests", "fixtures", "acta2", name, "canonical.json"),
      );
    }
    for (const relative of files) {
      snapshots.set(relative, await readFile(path.join(fixtureRoot, relative), "utf8"));
    }
  }
  const secondRun = runScript("materialize-acta2.mjs", ["--root", fixtureRoot]);
  assert.equal(secondRun.status, 0, `${secondRun.stdout}\n${secondRun.stderr}`);
  for (const [relative, firstContent] of snapshots) {
    const secondContent = await readFile(path.join(fixtureRoot, relative), "utf8");
    assert.equal(secondContent, firstContent, `${relative} must be byte-stable`);
    assert.doesNotMatch(secondContent, /\r/, `${relative} must be LF-only`);
  }

  await writeFile(path.join(fixtureRoot, "design", "acta2", "VERSION"), "9.9.9\n");
  const rejectedRun = runScript("materialize-acta2.mjs", ["--root", fixtureRoot]);
  assert.equal(rejectedRun.status, 1);
  assert.match(rejectedRun.stderr, /Unsupported Acta v2 version/);
});

test("acta2 instruments reflow without document-level horizontal scroll at 320px", async (t) => {
  if (skipBrowserProbes(t)) return;
  for (const { name, file } of instrumentTargets) {
    const fixture = path.join(root, "tests", "fixtures", "acta2", name, file);
    const result = runScript("acta2-render-probe.mjs", [
      "--url",
      `file://${fixture}`,
      "--width",
      "320",
      "--height",
      "700",
    ]);
    if (result.status === 2) {
      t.skip("no Chromium binary available for the reflow probe");
      return;
    }
    assert.equal(result.status, 0, `${name}: ${result.stdout}\n${result.stderr}`);
    assert.match(result.stdout, /overflow=none/, `${name}: ${result.stdout}`);
  }
});

test("acta2 instruments pass their in-page state/export self-test", async (t) => {
  if (skipBrowserProbes(t)) return;
  const chromeCandidates = /** @type {string[]} */ ([
    process.env.CHROME_BIN,
    "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
    "/usr/bin/google-chrome",
    "/usr/bin/chromium-browser",
  ].filter(Boolean));
  /** @type {string | null} */
  let chrome = null;
  for (const candidate of chromeCandidates) {
    try {
      await access(candidate);
      chrome = candidate;
      break;
    } catch {}
  }
  if (!chrome) {
    t.skip("no Chromium binary available for the behavioral self-test");
    return;
  }
  for (const { name, file } of instrumentTargets) {
    const fixture = path.join(root, "tests", "fixtures", "acta2", name, file);
    const result = spawnSync(
      chrome,
      [
        "--headless=new",
        "--disable-gpu",
        "--no-sandbox",
        "--virtual-time-budget=4000",
        "--dump-dom",
        `file://${fixture}?acta2selftest=1`,
      ],
      { encoding: "utf8", timeout: 60000 },
    );
    assert.equal(result.status, 0, `${name}: chrome exited ${result.status}\n${result.stderr}`);
    assert.match(
      result.stdout,
      /ACTA2-SELFTEST-PASS/,
      `${name}: self-test failed:\n${(result.stdout.match(/ACTA2-SELFTEST-FAIL[^<]*/) ?? ["no verdict found"])[0]}`,
    );
  }
});

/* ------------------------------------------------------------------ */
/* Bundled generators: standalone, data-driven, reproducible           */
/* ------------------------------------------------------------------ */

const freshScenario = {
  acta2: "0.2.0",
  kind: "decision",
  decisionId: "D-01",
  skill: "three-code-paths",
  artifactKind: "code-path-decision",
  initiative: "retry-queue",
  title: "Three code paths",
  question: "Where should retry orchestration live for the outbound webhook queue?",
  sourceRevision: null,
  inputs: ["src/webhooks/queue.mjs"],
  unresolved: ["alerting thresholds belong to a later stage"],
  constraints: ["no new runtime dependency", "worker restarts must be safe"],
  options: [
    {
      id: "x",
      label: "Inline retry in the worker loop",
      claim: "Retry stays where the failure happens.",
      code: { path: "src/webhooks/queue.mjs", snippet: "await deliver(job); // retry inline" },
      flow: ["job", "deliver", "retry inline"],
      pros: ["smallest change"],
      cons: ["blocks the loop"],
      seams: { test: "unit test on the loop", migration: "in place" },
      failureModes: ["head-of-line blocking"],
      changeConditions: ["throughput requirements grow"],
    },
    {
      id: "y",
      label: "Scheduled redelivery table",
      claim: "Failures are rows; a sweeper redelivers.",
      code: { path: "src/webhooks/redelivery.mjs", snippet: "insert into redelivery(next_at)" },
      flow: ["job", "fail", "row", "sweeper"],
      pros: ["restart safe"],
      cons: ["new table"],
      seams: { test: "sweeper unit tests", migration: "one migration" },
      failureModes: ["sweeper lag"],
      changeConditions: ["delivery volume shrinks"],
    },
    {
      id: "z",
      label: "Dedicated retry queue",
      claim: "A second queue owns all retry policy.",
      code: { path: "src/webhooks/retry-queue.mjs", snippet: "retryQueue.push(job, backoff)" },
      flow: ["job", "fail", "retry queue", "worker"],
      pros: ["isolates policy"],
      cons: ["more moving parts"],
      seams: { test: "queue contract tests", migration: "additive" },
      failureModes: ["queue divergence"],
      changeConditions: ["a shared queue library lands"],
    },
  ],
  matrix: [
    {
      dimension: "Restart safety",
      verdicts: {
        x: { mark: "no", note: "in-memory only" },
        y: { mark: "yes", note: "durable rows" },
        z: { mark: "part", note: "depends on queue backing" },
      },
    },
  ],
  recommendation: { option: "y", reason: "durability is the binding constraint" },
};

test("acta2 bundled generator creates a brand-new instrument from scenario JSON, standalone", async () => {
  const install = await mkdtemp(path.join(tmpdir(), "acta2-install-"));
  await cp(
    path.join(root, "skills", "three-code-paths", "references", "acta2"),
    path.join(install, "acta2"),
    { recursive: true },
  );
  const scenarioPath = path.join(install, "scenario.json");
  const outPath = path.join(install, "instrument.html");
  await writeFile(scenarioPath, JSON.stringify(freshScenario, null, 2));

  const run = spawnSync(
    process.execPath,
    [path.join(install, "acta2", "generate-instrument.mjs"), "--scenario", scenarioPath, "--out", outPath],
    { cwd: install, encoding: "utf8" },
  );
  assert.equal(run.status, 0, `${run.stdout}\n${run.stderr}`);
  const html = await readFile(outPath, "utf8");

  // static no-JS DOM derives from the input scenario
  for (const option of freshScenario.options) {
    assert.ok(html.includes(option.label), `static DOM must render ${option.label}`);
  }
  assert.ok(html.includes("Where should retry orchestration live"), "question rendered statically");
  assert.ok(!html.includes("Functional core, thin shell"), "no content from any other scenario");

  // live DOM starts semantically equal: island === input, initial status matches
  const island = html.match(/<script type="application\/json" id="acta2-data">([\s\S]*?)<\/script>/);
  assert.ok(island, "data island present");
  assert.deepEqual(JSON.parse(island?.[1] ?? "{}"), JSON.parse(JSON.stringify(freshScenario)));
  const status = deriveStatus(freshScenario, initialWorking(freshScenario));
  assert.ok(html.includes(status.label), "static status label equals derived initial status");
  assert.match(html, /<body[^>]*data-acta2-status="open-unselected"/);

  // candidate Markdown and JSON derive from the same state
  const candidate = buildCandidate(freshScenario, initialWorking(freshScenario));
  assert.equal(frontmatterOf(candidate.markdown).status, candidate.json.status);
  assert.equal(candidate.json.payload, "candidate");

  // honest no-JS: every control ships disabled until the runtime enables it
  for (const tag of ["<input", "<textarea", "<button"]) {
    const total = html.split(tag).length - 1;
    const guarded = html.split(`${tag} disabled data-a2-enable`).length - 1;
    assert.equal(guarded, total, `${tag} controls must ship disabled (${guarded}/${total})`);
  }

  // changing source data and rematerializing cannot retain stale content
  const renamed = JSON.parse(JSON.stringify(freshScenario));
  renamed.options[1].label = "Outbox pattern with relay";
  await writeFile(scenarioPath, JSON.stringify(renamed, null, 2));
  const rerun = spawnSync(
    process.execPath,
    [path.join(install, "acta2", "generate-instrument.mjs"), "--scenario", scenarioPath, "--out", outPath],
    { cwd: install, encoding: "utf8" },
  );
  assert.equal(rerun.status, 0, `${rerun.stdout}\n${rerun.stderr}`);
  const regenerated = await readFile(outPath, "utf8");
  assert.ok(regenerated.includes("Outbox pattern with relay"), "new content present");
  assert.ok(!regenerated.includes("Scheduled redelivery table"), "stale content cannot survive rematerialization");
});

test("acta2 canonical/scenario JSON reproduce the fixtures byte-for-byte via installed bundles", async () => {
  for (const skill of SUITE) {
    const name = skill.name;
    const install = await mkdtemp(path.join(tmpdir(), `acta2-roundtrip-${name}-`));
    await cp(
      path.join(root, "skills", name, "references", "acta2"),
      path.join(install, "acta2"),
      { recursive: true },
    );
    const fixtureRoot = path.join(root, "tests", "fixtures", "acta2", name);

    for (const variant of skill.instruments) {
      const suffix = variantSuffix(variant);
      const instrumentOut = path.join(install, `instrument${suffix}.html`);
      const genInstrument = spawnSync(
        process.execPath,
        [
          path.join(install, "acta2", "generate-instrument.mjs"),
          "--scenario",
          path.join(fixtureRoot, `scenario${suffix}.json`),
          "--out",
          instrumentOut,
        ],
        { cwd: install, encoding: "utf8" },
      );
      assert.equal(genInstrument.status, 0, `${name}${suffix}: ${genInstrument.stdout}\n${genInstrument.stderr}`);
      assert.equal(
        await readFile(instrumentOut, "utf8"),
        await readFile(path.join(fixtureRoot, `instrument${suffix}.html`), "utf8"),
        `${name}${suffix}: bundled generator must reproduce the fixture instrument exactly`,
      );
    }

    if (skill.record) {
      const recordOut = path.join(install, "record.html");
      const genRecord = spawnSync(
        process.execPath,
        [
          path.join(install, "acta2", "generate-record.mjs"),
          "--canonical",
          path.join(fixtureRoot, "canonical.json"),
          "--out",
          recordOut,
        ],
        { cwd: install, encoding: "utf8" },
      );
      assert.equal(genRecord.status, 0, `${name}: ${genRecord.stdout}\n${genRecord.stderr}`);
      assert.equal(
        await readFile(recordOut, "utf8"),
        await readFile(path.join(fixtureRoot, "record.html"), "utf8"),
        `${name}: record must regenerate from canonical JSON alone, byte-for-byte`,
      );
    }
  }
});

test("acta2 concept-lab static SVG equals the shared plot spec (no static/live drift)", async () => {
  const scenario = JSON.parse(
    await readFile(path.join(root, "tests", "fixtures", "acta2", "concept-lab", "scenario.json"), "utf8"),
  );
  const working = initialWorking(scenario);
  const spec = backoffPlotSpec(working.params, working.toggles);
  const html = await readFile(
    path.join(root, "tests", "fixtures", "acta2", "concept-lab", "instrument.html"),
    "utf8",
  );
  const svg = html.match(/<svg[\s\S]*?<\/svg>/)?.[0] ?? "";

  const specBands = spec.items.filter((item) => item.el === "band");
  const renderedBands = [...svg.matchAll(/<rect x="([\d.]+)" y="(\d+)" width="([\d.]+)" height="(\d+)"/g)];
  assert.equal(renderedBands.length, specBands.length, "one rendered band per spec band");
  specBands.forEach((band, index) => {
    assert.equal(Number(renderedBands[index]?.[1]), band.x, `band ${index} x`);
    assert.equal(Number(renderedBands[index]?.[3]), band.width, `band ${index} width`);
  });
  const totalLabel = spec.items.find((item) => item.el === "total-label");
  assert.ok(svg.includes(`>${totalLabel.text}</text>`), "worst-case total label matches spec");
  assert.ok(html.includes("clab-legend"), "legend present beside the plot");
});

test("acta2 instruments stay honestly inert without JavaScript", async (t) => {
  /* Static half (deterministic, no browser): the shipped HTML must not claim
     readiness, must ship every control disabled, and must carry the inline
     chat fallback beside the controls. */
  for (const { name, file } of instrumentTargets) {
    const fixture = path.join(root, "tests", "fixtures", "acta2", name, file);
    const html = await readFile(fixture, "utf8");
    assert.doesNotMatch(html, /<body[^>]*data-acta2-ready/, `${name}: static HTML must not claim runtime readiness`);
    assert.match(html, /class="a2-jsnote"/, `${name}: inline chat fallback present beside controls`);
    for (const tag of ["<input", "<textarea", "<button"]) {
      const total = html.split(tag).length - 1;
      const guarded = html.split(`${tag} disabled data-a2-enable`).length - 1;
      assert.equal(guarded, total, `${name}: ${tag} controls must ship disabled (${guarded}/${total})`);
    }
  }

  /* Browser half: load a script-stripped copy (exactly the DOM a no-JS
     browser renders) and confirm the live document stays inert. */
  if (skipBrowserProbes(t)) return;
  const stripDir = await mkdtemp(path.join(tmpdir(), "acta2-nojs-"));
  for (const { name, file } of instrumentTargets) {
    const fixture = path.join(root, "tests", "fixtures", "acta2", name, file);
    const html = await readFile(fixture, "utf8");
    const stripped = html.replace(/<script>[\s\S]*?<\/script>/g, "<!-- scripts unavailable -->");
    const target = path.join(stripDir, `${name}-${file}`);
    await writeFile(target, stripped);
    const result = runScript("acta2-render-probe.mjs", [
      "--url",
      `file://${target}`,
      "--width",
      "1280",
      "--height",
      "900",
      "--dump",
    ]);
    if (result.status === 2) {
      t.skip("no Chromium binary available");
      return;
    }
    assert.equal(result.status, 0, `${name}: probe exited ${result.status}\n${result.stderr}`);
    assert.ok(result.stdout.length > 1000, `${name}: probe returned the rendered DOM`);
    assert.doesNotMatch(result.stdout, /<body[^>]*data-acta2-ready/, `${name}: no readiness without JS`);
    assert.match(result.stdout, /class="a2-jsnote"/, `${name}: fallback visible without JS`);
    const enabled = [...result.stdout.matchAll(/<(?:input|textarea|button)(?![^>]*disabled)[^>]*>/g)];
    assert.equal(enabled.length, 0, `${name}: no control may appear operational without JS: ${enabled[0]?.[0] ?? ""}`);
  }
});

/* ------------------------------------------------------------------ */
/* Closure-pass findings: protocol language, record boundary, styles   */
/* ------------------------------------------------------------------ */

test("acta2 protocol and skill workflows carry no manual-HTML path", async () => {
  const forbidden = [
    /Fill the `acta2-data`/i,
    /keep the rendered static DOM consistent/i,
    /replacing the `acta2-data` island/i,
    /regenerating the static topology/i,
    /from the installed scaffold/i,
  ];
  const workflowDocs = [
    { doc: path.join(root, "design", "acta2", "protocol.md"), generator: /generate-instrument\.mjs/ },
  ];
  for (const skill of SUITE) {
    const generator =
      skill.instruments.length > 0 ? /generate-instrument\.mjs/ : /generate-record\.mjs/;
    workflowDocs.push({
      doc: path.join(root, "skills", skill.name, "references", "acta2-protocol.md"),
      generator: /generate-instrument\.mjs/,
    });
    workflowDocs.push({ doc: path.join(root, "skills", skill.name, "SKILL.md"), generator });
  }
  for (const { doc, generator } of workflowDocs) {
    const content = await readFile(doc, "utf8");
    for (const pattern of forbidden) {
      assert.doesNotMatch(content, pattern, `${path.relative(root, doc)} still contains manual-sync language`);
    }
    assert.match(content, generator, `${path.relative(root, doc)} must require the bundled generator`);
  }
  const protocol = await readFile(path.join(root, "design", "acta2", "protocol.md"), "utf8");
  assert.match(protocol, /Never edit the `acta2-data` island, the static DOM,\s+or any generated HTML by hand/);
});

test("acta2 record boundary rejects unaccepted canonical state (installed bundle)", async () => {
  const install = await mkdtemp(path.join(tmpdir(), "acta2-record-boundary-"));
  await cp(
    path.join(root, "skills", "three-code-paths", "references", "acta2"),
    path.join(install, "acta2"),
    { recursive: true },
  );
  const good = JSON.parse(
    await readFile(path.join(root, "tests", "fixtures", "acta2", "three-code-paths", "canonical.json"), "utf8"),
  );
  const attempt = async (mutate, expectedMessage, label) => {
    const canonical = JSON.parse(JSON.stringify(good));
    mutate(canonical);
    const canonicalPath = path.join(install, `${label}.json`);
    await writeFile(canonicalPath, JSON.stringify(canonical, null, 2));
    const run = spawnSync(
      process.execPath,
      [
        path.join(install, "acta2", "generate-record.mjs"),
        "--canonical",
        canonicalPath,
        "--out",
        path.join(install, `${label}.html`),
      ],
      { cwd: install, encoding: "utf8" },
    );
    assert.notEqual(run.status, 0, `${label}: unaccepted canonical must not produce a record`);
    assert.match(run.stderr, expectedMessage, `${label}: rejection reason`);
    await assert.rejects(readFile(path.join(install, `${label}.html`), "utf8"), { code: "ENOENT" });
  };

  await attempt((c) => { c.accepted.status = "candidate-ready"; }, /accepted terminal status/, "candidate-ready");
  await attempt((c) => { c.accepted.status = "draft"; }, /accepted terminal status/, "draft");
  await attempt((c) => { c.accepted.status = "stopped"; }, /accepted terminal status/, "stopped");
  await attempt((c) => { c.accepted.acceptedVia = "  "; }, /acceptedVia/, "no-acceptance-evidence");
  await attempt((c) => { c.accepted.decisions = []; }, /at least one accepted decision/, "empty-decisions");
  await attempt((c) => { delete c.accepted.decisions[0].acceptedVia; }, /missing acceptedVia/, "decision-no-evidence");
  await attempt((c) => { c.accepted.decisions[0].selection = "not-an-option"; }, /not an option/, "unknown-selection");
  await attempt((c) => { c.accepted.exampleWorking.selected = "b"; }, /disagrees with the recorded decision/, "working-mismatch");

  // model-kind: derived values must agree with the shared core
  const clab = JSON.parse(
    await readFile(path.join(root, "tests", "fixtures", "acta2", "concept-lab", "canonical.json"), "utf8"),
  );
  const clabInstall = await mkdtemp(path.join(tmpdir(), "acta2-record-boundary-clab-"));
  await cp(
    path.join(root, "skills", "concept-lab", "references", "acta2"),
    path.join(clabInstall, "acta2"),
    { recursive: true },
  );
  clab.accepted.derived.worstCaseTotalMs = 9999;
  const clabPath = path.join(clabInstall, "bad-derived.json");
  await writeFile(clabPath, JSON.stringify(clab, null, 2));
  const clabRun = spawnSync(
    process.execPath,
    [
      path.join(clabInstall, "acta2", "generate-record.mjs"),
      "--canonical",
      clabPath,
      "--out",
      path.join(clabInstall, "bad-derived.html"),
    ],
    { cwd: clabInstall, encoding: "utf8" },
  );
  assert.notEqual(clabRun.status, 0);
  assert.match(clabRun.stderr, /disagree with the shared core calculation/);
});

test("acta2 record boundary rejects contradictory accepted decisions (installed bundles)", async () => {
  const cases = [
    {
      pilot: "three-code-paths",
      mutations: [
        {
          label: "wrong-decision-id",
          apply: (canonical) => { canonical.accepted.decisions[0].id = "WRONG-GATE"; },
          message: /decision id/i,
        },
        {
          label: "working-rationale-mismatch",
          apply: (canonical) => {
            canonical.accepted.exampleWorking.rationale = "the exact opposite rationale";
          },
          message: /rationale/i,
        },
      ],
    },
    {
      pilot: "build-with-notes",
      mutations: [
        {
          label: "wrong-stop-id",
          apply: (canonical) => { canonical.accepted.decisions[0].id = "WRONG-STOP"; },
          message: /decision id/i,
        },
        {
          label: "working-rationale-mismatch",
          apply: (canonical) => {
            canonical.accepted.exampleWorking.rationale = "the exact opposite rationale";
          },
          message: /rationale/i,
        },
        {
          label: "ephemeral-filter-in-canonical",
          apply: (canonical) => { canonical.accepted.exampleWorking.filter = "needs-human"; },
          message: /ephemeral view state/i,
        },
      ],
    },
    {
      pilot: "concept-lab",
      mutations: [
        {
          label: "wrong-model-decision-id",
          apply: (canonical) => { canonical.accepted.decisions[0].id = "WRONG-GATE"; },
          message: /decision id/i,
        },
        {
          label: "unknown-model-acceptance",
          apply: (canonical) => {
            canonical.accepted.decisions[0].selection = "not-a-model-acceptance";
          },
          message: /model acceptance/i,
        },
      ],
    },
  ];

  for (const { pilot, mutations } of cases) {
    const install = await mkdtemp(path.join(tmpdir(), `acta2-record-consistency-${pilot}-`));
    await cp(
      path.join(root, "skills", pilot, "references", "acta2"),
      path.join(install, "acta2"),
      { recursive: true },
    );
    const good = JSON.parse(
      await readFile(path.join(root, "tests", "fixtures", "acta2", pilot, "canonical.json"), "utf8"),
    );

    for (const mutation of mutations) {
      const canonical = JSON.parse(JSON.stringify(good));
      mutation.apply(canonical);
      const canonicalPath = path.join(install, `${mutation.label}.json`);
      const recordPath = path.join(install, `${mutation.label}.html`);
      await writeFile(canonicalPath, JSON.stringify(canonical, null, 2));
      const run = spawnSync(
        process.execPath,
        [
          path.join(install, "acta2", "generate-record.mjs"),
          "--canonical",
          canonicalPath,
          "--out",
          recordPath,
        ],
        { cwd: install, encoding: "utf8" },
      );
      assert.notEqual(run.status, 0, `${pilot}/${mutation.label}: contradictory canonical must fail`);
      assert.match(run.stderr, mutation.message, `${pilot}/${mutation.label}: rejection reason`);
      await assert.rejects(readFile(recordPath, "utf8"), { code: "ENOENT" });
    }
  }
});

test("acta2 change-blueprint record requires the accepted Gate A prerequisite (installed bundle)", async () => {
  const install = await mkdtemp(path.join(tmpdir(), "acta2-change-blueprint-prerequisite-"));
  await cp(
    path.join(root, "skills", "change-blueprint", "references", "acta2"),
    path.join(install, "acta2"),
    { recursive: true },
  );
  const good = JSON.parse(
    await readFile(path.join(root, "tests", "fixtures", "acta2", "change-blueprint", "canonical.json"), "utf8"),
  );
  const mutations = [
    {
      label: "missing-gate-a",
      apply: (canonical) => {
        canonical.accepted.decisions = canonical.accepted.decisions.filter(
          (decision) => decision.id !== "gate-a-spec",
        );
      },
      message: /required prior decision.*gate-a-spec/i,
    },
    {
      label: "unaccepted-gate-a-selection",
      apply: (canonical) => {
        canonical.accepted.decisions.find((decision) => decision.id === "gate-a-spec").selection =
          "request-changes";
      },
      message: /prior decision.*gate-a-spec.*selection/i,
    },
    {
      label: "wrong-gate-a-revision",
      apply: (canonical) => {
        canonical.accepted.decisions.find((decision) => decision.id === "gate-a-spec").acceptedRevision =
          "spec-revision-that-was-never-approved";
      },
      message: /prior decision.*gate-a-spec.*revision/i,
    },
    {
      label: "wrong-gate-a-artifact",
      apply: (canonical) => {
        canonical.accepted.decisions.find((decision) => decision.id === "gate-a-spec").artifactPath =
          "different-spec.md";
      },
      message: /prior decision.*gate-a-spec.*artifact path/i,
    },
    {
      label: "duplicate-gate-a",
      apply: (canonical) => {
        const gateA = canonical.accepted.decisions.find((decision) => decision.id === "gate-a-spec");
        canonical.accepted.decisions.push({ ...gateA });
      },
      message: /required prior decision.*gate-a-spec.*exactly once/i,
    },
  ];

  for (const mutation of mutations) {
    const canonical = JSON.parse(JSON.stringify(good));
    mutation.apply(canonical);
    const canonicalPath = path.join(install, `${mutation.label}.json`);
    const recordPath = path.join(install, `${mutation.label}.html`);
    await writeFile(canonicalPath, JSON.stringify(canonical, null, 2));
    const run = spawnSync(
      process.execPath,
      [
        path.join(install, "acta2", "generate-record.mjs"),
        "--canonical",
        canonicalPath,
        "--out",
        recordPath,
      ],
      { cwd: install, encoding: "utf8" },
    );
    assert.notEqual(run.status, 0, `${mutation.label}: Gate B must not erase or rewrite Gate A`);
    assert.match(run.stderr, mutation.message, `${mutation.label}: rejection reason`);
    await assert.rejects(readFile(recordPath, "utf8"), { code: "ENOENT" });
  }
});

test("acta2 disabled controls are visually disabled (computed styles)", async (t) => {
  if (skipBrowserProbes(t)) return;
  const stripDir = await mkdtemp(path.join(tmpdir(), "acta2-disabled-styles-"));
  const fixture = path.join(root, "tests", "fixtures", "acta2", "concept-lab", "instrument.html");
  const html = await readFile(fixture, "utf8");
  const stripped = html.replace(/<script>[\s\S]*?<\/script>/g, "<!-- scripts unavailable -->");
  const target = path.join(stripDir, "concept-lab.html");
  await writeFile(target, stripped);
  const result = runScript("acta2-render-probe.mjs", [
    "--url",
    `file://${target}`,
    "--width",
    "1280",
    "--height",
    "900",
    "--probe-disabled",
  ]);
  if (result.status === 2) {
    t.skip("no Chromium binary available");
    return;
  }
  assert.equal(result.status, 0, `${result.stdout}\n${result.stderr}`);
  const payload = result.stdout.match(/DISABLED-STYLES (.+)/);
  assert.ok(payload, "probe reported computed styles");
  const styles = JSON.parse(payload?.[1] ?? "{}");
  for (const [control, expected] of Object.entries({ button: true, slider: true, textarea: true })) {
    assert.ok(styles[control], `${control} found in disabled state`);
    assert.equal(styles[control].cursor, "not-allowed", `${control} cursor must not invite interaction`);
    assert.ok(styles[control].opacity < 1, `${control} must be visibly dimmed`);
    assert.ok(expected);
  }
  assert.ok(styles.choiceLabel, "choice label found");
  assert.equal(styles.choiceLabel.cursor, "not-allowed", "choice labels must not retain pointer cursors");
  assert.ok(styles.choiceLabel.opacity < 1, "choice labels must be visibly dimmed");
});

test("acta2 concept-lab static SVG matches the full plot spec item-by-item", async () => {
  const scenario = JSON.parse(
    await readFile(path.join(root, "tests", "fixtures", "acta2", "concept-lab", "scenario.json"), "utf8"),
  );
  const working = initialWorking(scenario);
  const spec = backoffPlotSpec(working.params, working.toggles);
  const html = await readFile(
    path.join(root, "tests", "fixtures", "acta2", "concept-lab", "instrument.html"),
    "utf8",
  );
  const plot = html.match(/<g data-clab-plot>([\s\S]*?)<\/g>/)?.[1] ?? "";
  const nodes = [...plot.matchAll(/<(rect|line|text)\b([^>]*)>(?:([^<]*)<\/text>)?/g)];
  assert.equal(nodes.length, spec.items.length, "one rendered element per spec item");
  const attrOf = (raw, name) => (raw ?? "").match(new RegExp(`${name}="([^"]*)"`))?.[1];
  spec.items.forEach((item, index) => {
    const [, tag, raw, text] = nodes[index] ?? [];
    if (item.el === "band") {
      assert.equal(tag, "rect", `item ${index} tag`);
      assert.equal(attrOf(raw, "x"), String(item.x), `band ${index} x`);
      assert.equal(attrOf(raw, "y"), String(item.y), `band ${index} y`);
      assert.equal(attrOf(raw, "width"), String(item.width), `band ${index} width`);
      assert.equal(attrOf(raw, "height"), String(item.height), `band ${index} height`);
      assert.equal((raw ?? "").includes("stroke-dasharray"), Boolean(item.capped), `band ${index} capped dash`);
    } else if (
      item.el === "tick" ||
      item.el === "axis-tick" ||
      item.el === "expected-mark" ||
      item.el === "axis-line" ||
      item.el === "endmark"
    ) {
      assert.equal(tag, "line", `item ${index} tag`);
      const x1 = item.x1 ?? item.x;
      assert.equal(attrOf(raw, "x1"), String(x1), `${item.el} ${index} x1`);
      assert.equal(attrOf(raw, "y1"), String(item.y1), `${item.el} ${index} y1`);
      assert.equal(attrOf(raw, "y2"), String(item.y2), `${item.el} ${index} y2`);
    } else {
      assert.equal(tag, "text", `item ${index} tag`);
      assert.equal(text, item.text, `${item.el} ${index} label`);
      assert.equal(attrOf(raw, "x"), String(item.x), `${item.el} ${index} x`);
      assert.equal(attrOf(raw, "y"), String(item.y), `${item.el} ${index} y`);
    }
  });
});

/* ------------------------------------------------------------------ */
/* Suite generalization: quiz / checklist / prototype / dossier kinds  */
/* ------------------------------------------------------------------ */

import { validateCanonicalForRecord, deriveQuizScore } from "../design/acta2/lib/export-core.mjs";

const quizData = {
  acta2: "0.2.0",
  kind: "quiz",
  decisionId: "understanding-check",
  acceptanceToken: "record-gaps",
  skill: "do-i-understand-this",
  artifactKind: "understanding-check",
  initiative: "tag-filter",
  title: "Do I understand this",
  question: "Do you understand what the tag-filter change actually did?",
  sourceRevision: null,
  inputs: ["src/catalog.mjs"],
  questions: [
    {
      id: "q1",
      prompt: "Where does filterByTag run?",
      options: [
        { id: "a", label: "In the browser only" },
        { id: "b", label: "In Node tests and the browser" },
      ],
      answer: "b",
      explanation: "The pure function is imported by both.",
      gap: "shared pure-function seam",
    },
    {
      id: "q2",
      prompt: "What does an unknown ?tag= render?",
      options: [
        { id: "a", label: "The full catalog" },
        { id: "b", label: "An empty list" },
      ],
      answer: "b",
      explanation: "Spec keeps unknown tags empty until STOP-01 said otherwise.",
      gap: "unknown-tag fallback",
    },
  ],
  unresolved: [],
};

const checklistData = {
  acta2: "0.2.0",
  kind: "checklist",
  decisionId: "figure-review",
  acceptanceToken: "accept-figures",
  skill: "draw-it-in-svg",
  artifactKind: "figure-sheet",
  initiative: "tag-filter",
  title: "Draw it in SVG",
  question: "Which figures are approved for reuse?",
  sourceRevision: null,
  inputs: ["docs/architecture.md"],
  items: [
    { id: "fig-flow", label: "Tag-filter data flow" },
    { id: "fig-seams", label: "Module seams" },
  ],
  verdicts: [
    { id: "approve", label: "Approve", tone: "positive" },
    { id: "revise", label: "Needs revision", tone: "warning" },
  ],
  conclusionRequired: false,
  unresolved: [],
};

const prototypeData = {
  acta2: "0.2.0",
  kind: "prototype",
  decisionId: "feel-check",
  acceptanceToken: "record-feel",
  skill: "feel-the-flow",
  artifactKind: "interaction-prototype",
  initiative: "tag-filter",
  title: "Feel the flow",
  question: "How should tag filtering feel while typing?",
  sourceRevision: null,
  inputs: [],
  params: [
    { id: "debounce", label: "Debounce", min: 0, max: 600, step: 50, default: 150, unit: "ms" },
  ],
  toggles: [{ id: "instant", label: "Instant first keystroke", default: false }],
  unresolved: [],
};

test("acta2 quiz kind: answers drive score, gaps, and candidate status", () => {
  const working = initialWorking(quizData);
  assert.deepEqual({ ...working.answers }, { q1: null, q2: null });
  assert.equal(deriveStatus(quizData, working).code, "exploring");

  working.answers.q1 = "b";
  assert.equal(deriveStatus(quizData, working).code, "exploring", "half-answered stays open");
  working.answers.q2 = "a";
  assert.equal(deriveStatus(quizData, working).code, "candidate-ready");

  const score = deriveQuizScore(quizData, working);
  assert.equal(score.correct, 1);
  assert.equal(score.total, 2);
  assert.deepEqual(score.gaps.map((gap) => gap.question), ["q2"]);

  const candidate = buildCandidate(quizData, working);
  const front = frontmatterOf(candidate.markdown);
  assert.equal(front.score_correct, 1);
  assert.equal(front.score_total, 2);
  assert.equal(candidate.json.score.correct, 1);
  assert.deepEqual(candidate.json.answers, { q1: "b", q2: "a" });
  assert.equal(candidate.json.gaps.length, 1);
  assert.match(candidate.markdown, /unknown-tag fallback/);
  assert.match(candidate.markdown, /never a merge gate/i);
});

test("acta2 checklist kind: every item needs a verdict before candidate-ready", () => {
  const working = initialWorking(checklistData);
  assert.deepEqual({ ...working.marks }, { "fig-flow": null, "fig-seams": null });
  assert.equal(deriveStatus(checklistData, working).code, "exploring");
  working.marks["fig-flow"] = "approve";
  assert.equal(deriveStatus(checklistData, working).code, "exploring");
  working.marks["fig-seams"] = "revise";
  assert.equal(deriveStatus(checklistData, working).code, "candidate-ready");

  const candidate = buildCandidate(checklistData, working);
  assert.equal(candidate.json.marks["fig-seams"], "revise");
  const front = frontmatterOf(candidate.markdown);
  assert.equal(front["mark_fig-seams"], "revise");
  assert.match(candidate.markdown, /Needs revision/);
});

test("acta2 checklist kind: conclusionRequired holds candidate-ready until conclusion", () => {
  const data = { ...checklistData, conclusionRequired: true };
  const working = initialWorking(data);
  working.marks["fig-flow"] = "approve";
  working.marks["fig-seams"] = "approve";
  assert.equal(deriveStatus(data, working).code, "exploring");
  working.conclusion = "both figures match the shipped architecture";
  assert.equal(deriveStatus(data, working).code, "candidate-ready");
});

test("acta2 prototype kind: parameters and felt conclusion export without a fake model", () => {
  const working = initialWorking(prototypeData);
  assert.equal(working.params.debounce, 150);
  assert.equal(deriveStatus(prototypeData, working).code, "exploring");
  working.conclusion = "150ms feels laggy; 50ms with instant first keystroke feels right";
  assert.equal(deriveStatus(prototypeData, working).code, "candidate-ready");
  const candidate = buildCandidate(prototypeData, working);
  assert.equal(candidate.json.parameters.debounce, 150);
  assert.equal(candidate.json.derived, undefined, "prototype exports no derived model block");
  const front = frontmatterOf(candidate.markdown);
  assert.equal(front.param_debounce, 150);
});

test("acta2 new kinds reject hostile identifiers", () => {
  assert.throws(
    () => initialWorking({ ...quizData, questions: [{ ...quizData.questions[0], id: "__proto__" }] }),
    /Unsafe|identifier/i,
  );
  assert.throws(
    () => initialWorking({ ...checklistData, items: [{ id: "a:b", label: "x" }] }),
    /Unsafe|identifier/i,
  );
});

test("acta2 dossier kind: record-only canonical validates, instruments are refused", () => {
  const scenario = {
    acta2: "0.2.0",
    kind: "dossier",
    decisionId: "publish-xray",
    acceptanceToken: "publish-record",
    skill: "feature-xray",
    artifactKind: "feature-explanation",
    initiative: "tag-filter",
    title: "Feature X-ray",
    question: "How does tag filtering actually work?",
    sourceRevision: null,
    inputs: ["src/catalog.mjs"],
    unresolved: [],
  };
  assert.throws(() => initialWorking(scenario), /dossier|instrument/i, "dossier never yields instrument working state");
  const canonical = {
    scenario,
    accepted: {
      status: "approved",
      acceptedVia: "chat 2026-07-23 — explanation verified against source",
      decisions: [
        { id: "publish-xray", selection: "publish-record", rationale: "verified", acceptedVia: "chat" },
      ],
    },
  };
  assert.equal(validateCanonicalForRecord(canonical), canonical);
  assert.throws(
    () =>
      validateCanonicalForRecord({
        scenario,
        accepted: { ...canonical.accepted, decisions: [{ ...canonical.accepted.decisions[0], selection: "other" }] },
      }),
    /acceptance token|acceptance/i,
  );
});

test("acta2 quiz canonical must carry answers consistent with the recomputed score", () => {
  const working = { answers: { q1: "b", q2: "b" }, reflection: "" };
  const canonical = {
    scenario: quizData,
    accepted: {
      status: "approved",
      acceptedVia: "chat",
      decisions: [{ id: "understanding-check", selection: "record-gaps", rationale: null, acceptedVia: "chat" }],
      exampleWorking: working,
      derived: { correct: 2, total: 2 },
    },
  };
  assert.equal(validateCanonicalForRecord(canonical), canonical);
  assert.throws(
    () =>
      validateCanonicalForRecord({
        ...canonical,
        accepted: { ...canonical.accepted, derived: { correct: 1, total: 2 } },
      }),
    /score|disagree/i,
  );
});
