#!/usr/bin/env node

import { readFile } from "node:fs/promises";
import path from "node:path";
import { spawnSync } from "node:child_process";

const version = process.argv[2];
const root = process.cwd();
const errors = [];

if (!version) {
  console.error("Usage: npm run release:check -- <version>");
  process.exit(1);
}

const semantic = version.match(/^(\d+)\.(\d+)\.(\d+)$/);
if (!semantic) {
  errors.push(`${version} is not a semantic version.`);
} else if (Number(semantic[1]) < 1) {
  errors.push("Public releases must begin at v1.0.0 or later.");
}

let packageMetadata;
try {
  packageMetadata = JSON.parse(
    await readFile(path.join(root, "package.json"), "utf8"),
  );
  if (packageMetadata.version !== version) {
    errors.push(
      `package.json version ${packageMetadata.version} does not match ${version}.`,
    );
  }
} catch (error) {
  errors.push(`Cannot read package.json (${error.message}).`);
}

try {
  const changelog = await readFile(path.join(root, "CHANGELOG.md"), "utf8");
  if (!new RegExp(`^## \\[${version.replaceAll(".", "\\.")}\\] - \\d{4}-\\d{2}-\\d{2}$`, "m").test(changelog)) {
    errors.push(`CHANGELOG.md has no dated ${version} release section.`);
  }
} catch (error) {
  errors.push(`Cannot read CHANGELOG.md (${error.message}).`);
}

try {
  const compatibility = await readFile(
    path.join(root, "docs", "compatibility.md"),
    "utf8",
  );
  for (const client of ["Codex", "Claude Code", "skills CLI"]) {
    const row = new RegExp(
      `^\\|\\s*${client.replace(" ", "\\s+")}\\s*\\|\\s*(?!TBD|TODO|latest|Not\\s+yet|pre-release|N\\/?A)[^|\\s][^|]*\\|$`,
      "im",
    );
    if (!row.test(compatibility)) {
      errors.push(`Compatibility guide must record a concrete ${client} version.`);
    }
  }
} catch (error) {
  errors.push(`Cannot read compatibility guide (${error.message}).`);
}

const status = spawnSync("git", ["status", "--porcelain"], {
  cwd: root,
  encoding: "utf8",
});
if (status.status !== 0) {
  errors.push(`Cannot inspect Git status (${status.stderr.trim()}).`);
} else if (status.stdout.trim().length > 0) {
  errors.push("Release candidate must have a clean working tree.");
}

const tag = spawnSync(
  "git",
  ["rev-parse", "--quiet", "--verify", `refs/tags/v${version}`],
  { cwd: root, encoding: "utf8" },
);
if (tag.status === 0) {
  errors.push(`Tag v${version} already exists.`);
}

if (errors.length > 0) {
  console.error(errors.map((error) => `ERROR: ${error}`).join("\n"));
  process.exit(1);
}

console.log(`Release v${version} is ready.`);
