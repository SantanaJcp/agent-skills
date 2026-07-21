import assert from "node:assert/strict";
import { mkdtemp, readFile, writeFile } from "node:fs/promises";
import { tmpdir } from "node:os";
import path from "node:path";
import { spawnSync } from "node:child_process";
import test from "node:test";

const repositoryRoot = path.resolve(import.meta.dirname, "..");
const releaseNotes = path.join(repositoryRoot, "scripts", "release-notes.mjs");

test("release manager publishes the matching changelog section", async () => {
  const root = await mkdtemp(path.join(tmpdir(), "agent-skills-notes-"));
  await writeFile(
    path.join(root, "CHANGELOG.md"),
    `# Changelog

## [Unreleased]

- Future work.

## [1.2.0] - 2026-07-21

### Added

- Portable skill.

## [1.1.0] - 2026-06-01

- Previous work.
`,
  );

  const output = path.join(root, "release-notes.md");
  const result = spawnSync(process.execPath, [releaseNotes, "1.2.0", output], {
    cwd: root,
    encoding: "utf8",
  });

  assert.equal(result.status, 0, result.stderr);
  const notes = await readFile(output, "utf8");
  assert.match(notes, /^### Added$/m);
  assert.match(notes, /Portable skill/);
  assert.doesNotMatch(notes, /Previous work|Future work/);
});
