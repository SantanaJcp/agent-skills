import assert from "node:assert/strict";
import { access, cp, mkdir, mkdtemp, readFile, readdir, writeFile } from "node:fs/promises";
import { tmpdir } from "node:os";
import path from "node:path";
import { spawnSync } from "node:child_process";
import test from "node:test";

const repositoryRoot = path.resolve(import.meta.dirname, "..");
const preparer = path.join(repositoryRoot, "scripts", "prepare-manual-qa.mjs");
const expectedSkills = [
  "build-with-notes",
  "change-blueprint",
  "concept-lab",
  "deepen-the-codebase",
  "do-i-understand-this",
  "draw-it-in-svg",
  "draw-the-flow",
  "feature-xray",
  "feel-the-flow",
  "find-the-cause",
  "interface-directions",
  "learning-workbench",
  "make-me-realize",
  "three-code-paths",
  "what-just-happened",
];
const expectedActa2Html = [
  "build-with-notes/instrument.html",
  "build-with-notes/record.html",
  "change-blueprint/instrument-plan.html",
  "change-blueprint/instrument-spec.html",
  "change-blueprint/record.html",
  "concept-lab/instrument.html",
  "concept-lab/record.html",
  "deepen-the-codebase/instrument.html",
  "deepen-the-codebase/record.html",
  "do-i-understand-this/instrument.html",
  "do-i-understand-this/record.html",
  "draw-it-in-svg/instrument.html",
  "draw-it-in-svg/record.html",
  "draw-the-flow/instrument.html",
  "draw-the-flow/record.html",
  "feature-xray/record.html",
  "feel-the-flow/instrument.html",
  "find-the-cause/instrument.html",
  "find-the-cause/record.html",
  "interface-directions/instrument.html",
  "interface-directions/record.html",
  "learning-workbench/instrument.html",
  "learning-workbench/record.html",
  "three-code-paths/instrument.html",
  "three-code-paths/record.html",
  "what-just-happened/record.html",
];

function runPreparer(args) {
  return spawnSync(process.execPath, [preparer, ...args], {
    cwd: repositoryRoot,
    encoding: "utf8",
  });
}

function git(args, cwd) {
  const result = spawnSync("git", args, { cwd, encoding: "utf8" });
  assert.equal(result.status, 0, result.stderr);
  return result.stdout.trim();
}

async function createCommittedSource(parent) {
  const source = path.join(parent, "source");
  const entries = [
    "design/acta/VERSION",
    "design/acta2/VERSION",
    "docs/qa/evaluator-runbook.md",
    "docs/qa/evidence/template.md",
    "incubator",
    "tests/fixtures/acta2",
    "tests/fixtures/core-cycle-project",
    "tests/smoke",
  ];
  for (const relative of entries) {
    const target = path.join(source, relative);
    await mkdir(path.dirname(target), { recursive: true });
    await cp(path.join(repositoryRoot, relative), target, { recursive: true });
  }
  git(["init", "--quiet"], source);
  git(["config", "user.name", "QA Test"], source);
  git(["config", "user.email", "qa@example.invalid"], source);
  git(["add", "."], source);
  git(["commit", "--quiet", "-m", "test fixture"], source);
  return {
    source,
    revision: git(["rev-parse", "HEAD"], source),
  };
}

async function exists(target) {
  try {
    await access(target);
    return true;
  } catch (error) {
    if (error.code === "ENOENT") return false;
    throw error;
  }
}

test("evaluator can prepare isolated manual-QA harnesses for both clients", async () => {
  const parent = await mkdtemp(path.join(tmpdir(), "agent-skills-manual-qa-"));
  const destination = path.join(parent, "harnesses");
  const { source, revision } = await createCommittedSource(parent);

  const result = runPreparer([
    "--destination",
    destination,
    "--source-root",
    source,
  ]);

  assert.equal(result.status, 0, result.stderr);
  assert.match(result.stdout, /Prepared manual QA harnesses/);

  for (const variant of ["with-sidecars", "without-sidecars"]) {
    const harness = path.join(destination, variant);
    const manifest = JSON.parse(
      await readFile(path.join(harness, "QA-MANIFEST.json"), "utf8"),
    );
    assert.deepEqual(manifest, {
      schema_version: 2,
      suite: "acta-development-skill-suite",
      acta_version: "0.1.0",
      acta2_version: "0.2.0-pilot",
      active_artifact_system: "acta2",
      source_revision: revision,
      variant,
      skills: expectedSkills,
    });
    assert.equal(
      (await readFile(path.join(harness, "SCENARIO.md"), "utf8")).includes(
        "Add a keyboard-accessible tag filter",
      ),
      true,
    );
    assert.equal(await exists(path.join(harness, "EVALUATOR-RUNBOOK.md")), true);
    const runbook = await readFile(path.join(harness, "EVALUATOR-RUNBOOK.md"), "utf8");
    assert.match(runbook, /--ignore-user-config/);
    assert.match(runbook, /--setting-sources project/);
    assert.match(runbook, /fresh disposable copy/i);
    assert.equal(await exists(path.join(harness, "EVIDENCE-TEMPLATE.md")), true);
    assert.deepEqual(
      (await readdir(path.join(harness, "smoke-cases")))
        .filter((name) => name.endsWith(".yaml"))
        .sort(),
      ["collisions.yaml", ...expectedSkills.map((name) => `${name}.yaml`)].sort(),
    );
    const acta2Html = [];
    for (const skill of await readdir(path.join(harness, "acta-fixtures"))) {
      const skillRoot = path.join(harness, "acta-fixtures", skill);
      for (const name of await readdir(skillRoot)) {
        if (name.endsWith(".html")) acta2Html.push(`${skill}/${name}`);
      }
    }
    assert.deepEqual(acta2Html.sort(), expectedActa2Html.sort());

    const baseline = spawnSync(process.execPath, ["--test", "test/*.test.mjs"], {
      cwd: harness,
      encoding: "utf8",
    });
    assert.equal(baseline.status, 0, baseline.stderr || baseline.error?.message);

    for (const clientRoot of [".agents", ".claude"]) {
      const installed = path.join(harness, clientRoot, "skills");
      assert.deepEqual((await readdir(installed)).sort(), expectedSkills);
      for (const skill of expectedSkills) {
        const bundle = path.join(installed, skill);
        assert.equal(await exists(path.join(bundle, "SKILL.md")), true);
        assert.equal(
          await exists(path.join(bundle, "agents", "openai.yaml")),
          variant === "with-sidecars",
        );
      }
    }
  }
});

test("manual-QA preparation refuses to overwrite an existing destination", async () => {
  const parent = await mkdtemp(path.join(tmpdir(), "agent-skills-manual-qa-"));
  const destination = path.join(parent, "harnesses");
  await mkdir(destination);
  const sentinel = path.join(destination, "keep.txt");
  await writeFile(sentinel, "preserve me\n");

  const result = runPreparer(["--destination", destination]);

  assert.equal(result.status, 1);
  assert.match(result.stderr, /destination already exists/i);
  assert.equal(await readFile(sentinel, "utf8"), "preserve me\n");
});


test("manual-QA preparation refuses a dirty source revision", async () => {
  const parent = await mkdtemp(path.join(tmpdir(), "agent-skills-manual-qa-"));
  const destination = path.join(parent, "harnesses");
  const { source } = await createCommittedSource(parent);
  await writeFile(path.join(source, "dirty.txt"), "not committed\n");

  const result = runPreparer([
    "--destination",
    destination,
    "--source-root",
    source,
  ]);

  assert.equal(result.status, 1);
  assert.match(result.stderr, /source worktree must be clean/i);
  assert.equal(await exists(destination), false);
});
