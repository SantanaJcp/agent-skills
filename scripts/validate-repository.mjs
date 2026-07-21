#!/usr/bin/env node

import { access, readdir, readFile } from "node:fs/promises";
import path from "node:path";
import { parse } from "yaml";

const root = process.cwd();
const errors = [];
const requiredFiles = [
  ".editorconfig",
  ".gitignore",
  ".npmrc",
  ".github/PULL_REQUEST_TEMPLATE.md",
  ".github/ISSUE_TEMPLATE/bug.yml",
  ".github/ISSUE_TEMPLATE/skill-proposal.yml",
  ".github/ISSUE_TEMPLATE/config.yml",
  ".github/dependabot.yml",
  ".github/workflows/ci.yml",
  ".github/workflows/release.yml",
  "AGENTS.md",
  "CATALOG.md",
  "CHANGELOG.md",
  "CODE_OF_CONDUCT.md",
  "CONTRIBUTING.md",
  "INCUBATOR.md",
  "LICENSE",
  "README.md",
  "SECURITY.md",
  "docs/architecture.md",
  "docs/authoring.md",
  "docs/compatibility.md",
  "docs/releasing.md",
  "docs/testing.md",
  "package-lock.json",
  "package.json",
  "templates/skill/SKILL.md.tmpl",
];
const requiredDirectories = ["skills", "incubator", "tests/smoke"];
const yamlFiles = [
  ".github/ISSUE_TEMPLATE/bug.yml",
  ".github/ISSUE_TEMPLATE/skill-proposal.yml",
  ".github/ISSUE_TEMPLATE/config.yml",
  ".github/dependabot.yml",
  ".github/workflows/ci.yml",
  ".github/workflows/release.yml",
];

async function exists(relative) {
  try {
    await access(path.join(root, relative));
    return true;
  } catch (error) {
    if (error.code === "ENOENT") {
      return false;
    }
    throw error;
  }
}

for (const required of [...requiredFiles, ...requiredDirectories]) {
  if (!(await exists(required))) {
    errors.push(`missing required repository entry ${required}.`);
  }
}

for (const relative of yamlFiles) {
  if (!(await exists(relative))) {
    continue;
  }
  try {
    parse(await readFile(path.join(root, relative), "utf8"));
  } catch (error) {
    errors.push(`${relative} contains invalid YAML (${error.message}).`);
  }
}

try {
  const packageMetadata = JSON.parse(
    await readFile(path.join(root, "package.json"), "utf8"),
  );
  if (packageMetadata.private !== true) {
    errors.push("package.json must remain private.");
  }
  for (const script of [
    "catalog",
    "catalog:check",
    "check",
    "new:skill",
    "release:check",
    "release:notes",
    "test",
    "test:install",
    "typecheck",
    "validate",
    "validate:repository",
  ]) {
    if (typeof packageMetadata.scripts?.[script] !== "string") {
      errors.push(`package.json is missing the ${script} script.`);
    }
  }
  for (const [name, version] of Object.entries(
    packageMetadata.devDependencies ?? {},
  )) {
    if (typeof version !== "string" || /^[~^*]|\s|[<>=]/.test(version)) {
      errors.push(`development dependency ${name} must use an exact version.`);
    }
  }
} catch (error) {
  errors.push(`Cannot validate package.json (${error.message}).`);
}

async function markdownFiles(directory) {
  const files = [];
  for (const entry of await readdir(directory, { withFileTypes: true })) {
    if ([".git", "node_modules"].includes(entry.name)) {
      continue;
    }
    const target = path.join(directory, entry.name);
    if (entry.isDirectory()) {
      files.push(...(await markdownFiles(target)));
    } else if (entry.isFile() && entry.name.endsWith(".md")) {
      files.push(target);
    }
  }
  return files;
}

for (const file of await markdownFiles(root)) {
  const source = await readFile(file, "utf8");
  for (const match of source.matchAll(
    /!?\[[^\]]*\]\(([^)\s]+)(?:\s+"[^"]*")?\)/g,
  )) {
    const capturedLink = match[1];
    if (capturedLink === undefined) {
      continue;
    }
    const link = capturedLink.replace(/^<|>$/g, "");
    if (/^(?:[a-z]+:|#)/i.test(link)) {
      continue;
    }
    const target = decodeURIComponent(link.split("#", 1)[0] ?? "");
    if (target.length === 0) {
      continue;
    }
    const relativeTarget = path.relative(
      root,
      path.resolve(path.dirname(file), target),
    );
    if (!(await exists(relativeTarget))) {
      errors.push(
        `${path.relative(root, file)} contains a broken local link to ${link}.`,
      );
    }
  }
}

for (const forbidden of [
  "skills-lock.json",
  ".codex-plugin/plugin.json",
  ".claude-plugin/plugin.json",
]) {
  if (await exists(forbidden)) {
    errors.push(`${forbidden} is outside the v1 publisher contract.`);
  }
}

try {
  const license = await readFile(path.join(root, "LICENSE"), "utf8");
  if (!/^\s*Apache License\s+Version 2\.0, January 2004/m.test(license)) {
    errors.push("LICENSE must contain the canonical Apache-2.0 text.");
  }
} catch (error) {
  if (error.code !== "ENOENT") {
    throw error;
  }
}

if (errors.length > 0) {
  console.error(errors.map((error) => `ERROR: ${error}`).join("\n"));
  process.exit(1);
}

console.log("Validated repository foundation.");
