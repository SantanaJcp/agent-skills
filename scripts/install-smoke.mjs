#!/usr/bin/env node

import assert from "node:assert/strict";
import { access, mkdir, mkdtemp, writeFile } from "node:fs/promises";
import { tmpdir } from "node:os";
import path from "node:path";
import { spawnSync } from "node:child_process";

const repositoryRoot = path.resolve(import.meta.dirname, "..");
const cli = path.join(repositoryRoot, "node_modules", "skills", "bin", "cli.mjs");
const sandbox = await mkdtemp(path.join(tmpdir(), "agent-skills-install-"));
const source = path.join(sandbox, "publisher");
const project = path.join(sandbox, "consumer-project");
const wholeProject = path.join(sandbox, "whole-collection-project");
const projectHome = path.join(sandbox, "project-home");
const wholeHome = path.join(sandbox, "whole-home");
const globalHome = path.join(sandbox, "global-home");

function isolatedEnvironment(home) {
  return {
    ...process.env,
    CI: "1",
    DISABLE_TELEMETRY: "1",
    HOME: home,
    USERPROFILE: home,
    XDG_CONFIG_HOME: path.join(home, ".config"),
    XDG_DATA_HOME: path.join(home, ".local", "share"),
    XDG_STATE_HOME: path.join(home, ".local", "state"),
  };
}

function runCli(args, cwd, home) {
  const result = spawnSync(process.execPath, [cli, ...args], {
    cwd,
    encoding: "utf8",
    env: isolatedEnvironment(home),
    timeout: 30_000,
  });
  if (result.status !== 0) {
    throw new Error(
      `skills ${args.join(" ")} failed\n${result.stdout}\n${result.stderr}`,
    );
  }
  return result;
}

async function mustExist(filePath) {
  await access(filePath);
}

await mkdir(path.join(source, "skills", "portable-example"), {
  recursive: true,
});
await mkdir(path.join(source, "skills", "second-example"), {
  recursive: true,
});
await mkdir(project, { recursive: true });
await mkdir(wholeProject, { recursive: true });
await mkdir(projectHome, { recursive: true });
await mkdir(wholeHome, { recursive: true });
await mkdir(globalHome, { recursive: true });
await writeFile(
  path.join(source, "skills", "portable-example", "SKILL.md"),
  `---
name: portable-example
description: Demonstrate portable installation when repository tooling verifies client destinations.
license: Apache-2.0
metadata:
  tags: "testing"
---

# Portable Example
`,
);
await writeFile(
  path.join(source, "skills", "second-example", "SKILL.md"),
  `---
name: second-example
description: Verify whole collection installation when repository tooling exercises CLI selection.
license: Apache-2.0
metadata:
  tags: "testing"
---

# Second Example
`,
);

const listed = runCli(["add", source, "--list"], project, projectHome);
assert.match(`${listed.stdout}\n${listed.stderr}`, /portable-example/);

const selection = [
  "--skill",
  "portable-example",
  "--agent",
  "codex",
  "claude-code",
  "--yes",
  "--copy",
];
runCli(["add", source, ...selection], project, projectHome);

await mustExist(
  path.join(project, ".agents", "skills", "portable-example", "SKILL.md"),
);
await mustExist(
  path.join(project, ".claude", "skills", "portable-example", "SKILL.md"),
);
await mustExist(path.join(project, "skills-lock.json"));

runCli(
  [
    "add",
    source,
    "--skill",
    "*",
    "--agent",
    "codex",
    "claude-code",
    "--yes",
    "--copy",
  ],
  wholeProject,
  wholeHome,
);
for (const agentDirectory of [".agents", ".claude"]) {
  for (const name of ["portable-example", "second-example"]) {
    await mustExist(
      path.join(wholeProject, agentDirectory, "skills", name, "SKILL.md"),
    );
  }
}

runCli(["add", source, "--global", ...selection], globalHome, globalHome);
await mustExist(
  path.join(globalHome, ".agents", "skills", "portable-example", "SKILL.md"),
);
await mustExist(
  path.join(globalHome, ".claude", "skills", "portable-example", "SKILL.md"),
);

let publisherLockExists = true;
try {
  await access(path.join(source, "skills-lock.json"));
} catch (error) {
  if (error.code === "ENOENT") {
    publisherLockExists = false;
  } else {
    throw error;
  }
}
assert.equal(publisherLockExists, false, "publisher must not receive consumer lock state");

console.log(
  "Discovery, direct install, whole collection install, and global install passed.",
);
