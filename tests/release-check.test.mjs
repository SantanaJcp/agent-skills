import assert from "node:assert/strict";
import { mkdir, mkdtemp, writeFile } from "node:fs/promises";
import { tmpdir } from "node:os";
import path from "node:path";
import { spawnSync } from "node:child_process";
import test from "node:test";

const repositoryRoot = path.resolve(import.meta.dirname, "..");
const releaseCheck = path.join(repositoryRoot, "scripts", "release-check.mjs");

function run(command, args, cwd) {
  return spawnSync(command, args, { cwd, encoding: "utf8" });
}

async function createReleaseCandidate(version = "1.0.0") {
  const root = await mkdtemp(path.join(tmpdir(), "agent-skills-release-"));
  await mkdir(path.join(root, "docs"), { recursive: true });
  await writeFile(
    path.join(root, "package.json"),
    `${JSON.stringify({ name: "agent-skills", version, private: true }, null, 2)}\n`,
  );
  await writeFile(
    path.join(root, "CHANGELOG.md"),
    `# Changelog\n\n## [${version}] - 2026-07-21\n\n### Added\n\n- Initial release.\n`,
  );
  await writeFile(
    path.join(root, "docs", "compatibility.md"),
    `# Compatibility\n\n## Tested versions\n\n| Client | Version |\n| --- | --- |\n| Codex | 1.2.3 |\n| Claude Code | 4.5.6 |\n| skills CLI | 1.5.19 |\n`,
  );
  assert.equal(run("git", ["init", "-q"], root).status, 0);
  assert.equal(run("git", ["config", "user.email", "test@example.com"], root).status, 0);
  assert.equal(run("git", ["config", "user.name", "Test"], root).status, 0);
  assert.equal(run("git", ["add", "."], root).status, 0);
  assert.equal(run("git", ["commit", "-qm", "release candidate"], root).status, 0);
  return root;
}

test("release manager can verify a complete semantic release candidate", async () => {
  const root = await createReleaseCandidate();

  const result = run(process.execPath, [releaseCheck, "1.0.0"], root);

  assert.equal(result.status, 0, result.stderr);
  assert.match(result.stdout, /Release v1\.0\.0 is ready/);
});

test("release manager receives all actionable release failures", async () => {
  const root = await createReleaseCandidate();
  assert.equal(run("git", ["tag", "v2.0.0"], root).status, 0);
  await writeFile(
    path.join(root, "docs", "compatibility.md"),
    "# Compatibility\n\n| Client | Version |\n| --- | --- |\n| Codex | Not yet recorded; pre-release |\n",
  );

  const result = run(process.execPath, [releaseCheck, "2.0.0"], root);

  assert.equal(result.status, 1);
  assert.match(result.stderr, /package\.json version 1\.0\.0 does not match 2\.0\.0/);
  assert.match(result.stderr, /CHANGELOG\.md has no dated 2\.0\.0 release section/);
  assert.match(result.stderr, /concrete Codex version/);
  assert.match(result.stderr, /concrete Claude Code version/);
  assert.match(result.stderr, /concrete skills CLI version/);
  assert.match(result.stderr, /clean working tree/);
  assert.match(result.stderr, /Tag v2\.0\.0 already exists/);
});

test("release manager cannot publish a prerelease foundation", async () => {
  const root = await createReleaseCandidate("0.1.0");

  const result = run(process.execPath, [releaseCheck, "0.1.0"], root);

  assert.equal(result.status, 1);
  assert.match(result.stderr, /Public releases must begin at v1\.0\.0 or later/);
});

test("release manager must publish v1.0.0 before a later major version", async () => {
  const root = await createReleaseCandidate("2.0.0");

  const result = run(process.execPath, [releaseCheck, "2.0.0"], root);

  assert.equal(result.status, 1);
  assert.match(result.stderr, /First public release must be v1\.0\.0/);
});

test("release manager can publish a later version after v1.0.0 exists", async () => {
  const root = await createReleaseCandidate("2.0.0");
  assert.equal(run("git", ["tag", "v1.0.0"], root).status, 0);

  const result = run(process.execPath, [releaseCheck, "2.0.0"], root);

  assert.equal(result.status, 0, result.stderr);
  assert.match(result.stdout, /Release v2\.0\.0 is ready/);
});
