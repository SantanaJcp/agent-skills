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
    "docs/qa/evaluator-runbook.md",
    "docs/qa/evidence/template.md",
    "incubator",
    "tests/fixtures/acta",
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
      schema_version: 1,
      suite: "acta-development-skill-suite",
      acta_version: "0.1.0",
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
    assert.equal(await exists(path.join(harness, "EVIDENCE-TEMPLATE.md")), true);
    assert.deepEqual(
      (await readdir(path.join(harness, "smoke-cases")))
        .filter((name) => name.endsWith(".yaml"))
        .sort(),
      ["collisions.yaml", ...expectedSkills.map((name) => `${name}.yaml`)].sort(),
    );
    assert.deepEqual(
      (await readdir(path.join(harness, "acta-fixtures")))
        .filter((name) => name.endsWith(".html"))
        .sort(),
      expectedSkills.filter((name) => name !== "make-me-realize").sort().map((name) => `${name}.html`),
    );

    const baseline = spawnSync("npm", ["test"], {
      cwd: harness,
      encoding: "utf8",
    });
    assert.equal(baseline.status, 0, baseline.stderr);

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
