import assert from "node:assert/strict";
import { mkdir, mkdtemp, readFile, writeFile } from "node:fs/promises";
import { tmpdir } from "node:os";
import path from "node:path";
import { spawnSync } from "node:child_process";
import test from "node:test";

const repositoryRoot = path.resolve(import.meta.dirname, "..");
const generator = path.join(repositoryRoot, "scripts", "generate-catalog.mjs");

async function writeCatalogSkill(root, collection, name, description, tags) {
  const directory = path.join(root, collection, name);
  await mkdir(directory, { recursive: true });
  await writeFile(
    path.join(directory, "SKILL.md"),
    `---
name: ${name}
description: ${description}
license: Apache-2.0
metadata:
  tags: "${tags}"
---

# ${name}
`,
  );
}

function runGenerator(root, ...args) {
  return spawnSync(process.execPath, [generator, ...args], {
    cwd: root,
    encoding: "utf8",
  });
}

test("visitor receives deterministic stable and incubator catalogs", async () => {
  const root = await mkdtemp(path.join(tmpdir(), "agent-skills-catalog-"));
  await writeCatalogSkill(
    root,
    "skills",
    "research-notes",
    "Organize research notes when an agent must synthesize multiple sources.",
    "research, documentation",
  );
  await writeCatalogSkill(
    root,
    "incubator",
    "draft-review",
    "Review a draft when an author needs experimental editorial guidance.",
    "documentation, writing",
  );

  const result = runGenerator(root);

  assert.equal(result.status, 0, result.stderr);
  assert.match(result.stdout, /Generated CATALOG\.md and INCUBATOR\.md/);

  const stable = await readFile(path.join(root, "CATALOG.md"), "utf8");
  assert.match(stable, /\[research-notes\]\(skills\/research-notes\/SKILL\.md\)/);
  assert.match(stable, /<github-user>\/agent-skills@research-notes/);
  assert.match(stable, /## Topics[\s\S]*### documentation[\s\S]*### research/);

  const incubator = await readFile(path.join(root, "INCUBATOR.md"), "utf8");
  assert.match(incubator, /not covered by the stable compatibility promise/i);
  assert.match(incubator, /\[draft-review\]\(incubator\/draft-review\/SKILL\.md\)/);
});

test("contributor is told when committed catalogs are stale", async () => {
  const root = await mkdtemp(path.join(tmpdir(), "agent-skills-catalog-"));
  assert.equal(runGenerator(root).status, 0);
  for (const catalog of ["CATALOG.md", "INCUBATOR.md"]) {
    const content = await readFile(path.join(root, catalog), "utf8");
    assert.equal(content.endsWith("\n\n"), false, `${catalog} has a blank line at EOF`);
  }
  await writeFile(path.join(root, "CATALOG.md"), "stale catalog\n");

  const stale = runGenerator(root, "--check");
  assert.equal(stale.status, 1);
  assert.match(stale.stderr, /CATALOG\.md is stale/);

  assert.equal(runGenerator(root).status, 0);
  const current = runGenerator(root, "--check");
  assert.equal(current.status, 0, current.stderr);
  assert.match(current.stdout, /Catalogs are current/);
});
