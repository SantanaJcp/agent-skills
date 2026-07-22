#!/usr/bin/env node

import { access, readdir, readFile } from "node:fs/promises";
import path from "node:path";
import { parse } from "yaml";

const root = process.cwd();
const errors = [];
const requiredFiles = [
  ".editorconfig",
  ".gitattributes",
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
  "CONTEXT.md",
  "CONTRIBUTING.md",
  "INCUBATOR.md",
  "LICENSE",
  "README.md",
  "SECURITY.md",
  "docs/architecture.md",
  "docs/adr/0001-portable-skill-publisher.md",
  "docs/adr/0002-acta-development-suite.md",
  "docs/design/acta/provenance/README.md",
  "docs/qa/acta-suite-0.1.0.md",
  "docs/authoring.md",
  "docs/compatibility.md",
  "docs/releasing.md",
  "docs/testing.md",
  "package-lock.json",
  "package.json",
  "design/acta/VERSION",
  "design/acta/README.md",
  "design/acta/acta.css",
  "design/acta/acta.js",
  "design/acta/components.md",
  "design/acta/protocol.md",
  "design/acta/recipes.json",
  "scripts/materialize-acta.mjs",
  "scripts/validate-acta.mjs",
  "templates/skill/SKILL.md.tmpl",
];
const requiredDirectories = ["docs/adr", "skills", "incubator", "tests/smoke"];
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
    "acta",
    "acta:check",
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
    "validate:acta",
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

try {
  const readme = await readFile(path.join(root, "README.md"), "utf8");
  if (!/npx skills add .*--skill ["']\*["'].* -g .*--agent codex claude-code/.test(readme)) {
    errors.push(
      "README.md must document a global whole-collection install for Codex and Claude Code.",
    );
  }
} catch (error) {
  if (error.code !== "ENOENT") {
    errors.push(`Cannot validate README.md (${error.message}).`);
  }
}

try {
  const attributes = await readFile(path.join(root, ".gitattributes"), "utf8");
  if (!/^\*\s+text=auto\s+eol=lf$/m.test(attributes)) {
    errors.push(".gitattributes must enforce LF for cross-platform text files.");
  }
} catch (error) {
  if (error.code !== "ENOENT") {
    errors.push(`Cannot validate .gitattributes (${error.message}).`);
  }
}

try {
  const releaseWorkflow = await readFile(
    path.join(root, ".github", "workflows", "release.yml"),
    "utf8",
  );
  if (/run:\s*[^\n]*\$\{\{\s*inputs\./.test(releaseWorkflow)) {
    errors.push(
      "Release workflow inputs must pass through environment variables before shell use.",
    );
  }
} catch (error) {
  if (error.code !== "ENOENT") {
    errors.push(`Cannot validate release workflow safety (${error.message}).`);
  }
}

async function markdownFiles(directory) {
  const files = [];
  for (const entry of await readdir(directory, { withFileTypes: true })) {
    if ([".git", "node_modules"].includes(entry.name)) {
      continue;
    }
    const target = path.join(directory, entry.name);
    if (entry.isSymbolicLink()) {
      errors.push(`${path.relative(root, target)}: symlinks are forbidden.`);
    } else if (entry.isDirectory()) {
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
    let target;
    try {
      target = decodeURIComponent(link.split("#", 1)[0] ?? "");
    } catch {
      errors.push(
        `${path.relative(root, file)} contains invalid URI syntax in ${link}.`,
      );
      continue;
    }
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
