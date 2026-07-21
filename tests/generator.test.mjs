import assert from "node:assert/strict";
import { mkdir, mkdtemp, readFile, writeFile } from "node:fs/promises";
import { tmpdir } from "node:os";
import path from "node:path";
import { spawnSync } from "node:child_process";
import test from "node:test";

const repositoryRoot = path.resolve(import.meta.dirname, "..");
const generator = path.join(repositoryRoot, "scripts", "new-skill.mjs");

test("author can scaffold a new incubator skill", async () => {
  const root = await mkdtemp(path.join(tmpdir(), "agent-skills-generator-"));

  const result = spawnSync(process.execPath, [generator, "research-notes"], {
    cwd: root,
    encoding: "utf8",
  });

  assert.equal(result.status, 0, result.stderr);
  assert.match(result.stdout, /Created incubator skill research-notes/);

  const skill = await readFile(
    path.join(root, "incubator", "research-notes", "SKILL.md"),
    "utf8",
  );
  assert.match(skill, /^name: research-notes$/m);
  assert.match(skill, /^# Research Notes$/m);

  const smoke = await readFile(
    path.join(root, "tests", "smoke", "research-notes.yaml"),
    "utf8",
  );
  assert.match(smoke, /^skill: research-notes$/m);
  assert.match(smoke, /^  - kind: trigger$/m);
  assert.match(smoke, /^  - kind: non-trigger$/m);
});

test("author receives a useful error for an invalid skill name", async () => {
  const root = await mkdtemp(path.join(tmpdir(), "agent-skills-generator-"));

  const result = spawnSync(process.execPath, [generator, "Not Valid"], {
    cwd: root,
    encoding: "utf8",
  });

  assert.equal(result.status, 1);
  assert.match(
    result.stderr,
    /lowercase letters, numbers, and single hyphens/,
  );
});

test("author cannot scaffold a name that already exists", async () => {
  const root = await mkdtemp(path.join(tmpdir(), "agent-skills-generator-"));
  const existing = path.join(root, "skills", "research-notes");
  await mkdir(existing, { recursive: true });
  await writeFile(path.join(existing, "SKILL.md"), "existing skill");

  const result = spawnSync(process.execPath, [generator, "research-notes"], {
    cwd: root,
    encoding: "utf8",
  });

  assert.equal(result.status, 1);
  assert.match(result.stderr, /already exists/);
  assert.equal(await readFile(path.join(existing, "SKILL.md"), "utf8"), "existing skill");
});
