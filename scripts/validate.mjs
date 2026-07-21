#!/usr/bin/env node

import { access, readdir, readFile } from "node:fs/promises";
import path from "node:path";
import { parse } from "yaml";

const root = process.cwd();
const collections = ["skills", "incubator"];
const stableFields = new Set([
  "name",
  "description",
  "license",
  "compatibility",
  "metadata",
]);
const incubatorFields = new Set([
  ...stableFields,
  "allowed-tools",
  "when_to_use",
  "argument-hint",
  "arguments",
  "disable-model-invocation",
  "user-invocable",
  "disallowed-tools",
  "model",
  "effort",
  "context",
  "agent",
  "hooks",
  "paths",
  "shell",
]);
const forbiddenExecutableExtensions = new Set([
  ".app",
  ".bin",
  ".com",
  ".dll",
  ".dylib",
  ".exe",
  ".jar",
  ".msi",
  ".so",
  ".wasm",
]);
const forbiddenOpaqueExtensions = new Set([
  ".7z",
  ".gz",
  ".rar",
  ".tar",
  ".tgz",
  ".zip",
]);
const textExtensions = new Set([
  "",
  ".css",
  ".csv",
  ".html",
  ".js",
  ".json",
  ".md",
  ".mjs",
  ".svg",
  ".txt",
  ".yaml",
  ".yml",
]);
const networkModules = new Set([
  "node:dgram",
  "node:dns",
  "node:http",
  "node:http2",
  "node:https",
  "node:net",
  "node:tls",
]);
const secretPatterns = [
  {
    label: "private key",
    pattern: /-----BEGIN (?:[A-Z ]+ )?PRIVATE KEY-----/,
  },
  { label: "GitHub token", pattern: /\bgh[pousr]_[A-Za-z0-9]{36,}\b/ },
  { label: "GitHub token", pattern: /\bgithub_pat_[A-Za-z0-9_]{20,}\b/ },
  { label: "AWS access key", pattern: /\bAKIA[0-9A-Z]{16}\b/ },
  { label: "API token", pattern: /\bsk-[A-Za-z0-9_-]{20,}\b/ },
];
/** @type {string[]} */
const errors = [];
/** @type {string[]} */
const warnings = [];
const seenNames = new Map();
let skillCount = 0;

function parseSkillDocument(source, location) {
  const match = source.match(/^---\r?\n([\s\S]*?)\r?\n---(?:\r?\n|$)/);
  if (!match) {
    errors.push(`${location}: SKILL.md must begin with YAML frontmatter.`);
    return null;
  }

  try {
    return parse(match[1]);
  } catch (error) {
    errors.push(`${location}: invalid YAML frontmatter (${error.message}).`);
    return null;
  }
}

function validateFrontmatter(frontmatter, collection, directoryName, location) {
  if (
    frontmatter === null ||
    typeof frontmatter !== "object" ||
    Array.isArray(frontmatter)
  ) {
    errors.push(`${location}: frontmatter must be a YAML mapping.`);
    return;
  }

  if (frontmatter.name !== directoryName) {
    errors.push(`${location}: name must match directory ${directoryName}.`);
  }
  if (
    typeof frontmatter.name !== "string" ||
    frontmatter.name.length > 64 ||
    !/^[a-z0-9]+(?:-[a-z0-9]+)*$/.test(frontmatter.name)
  ) {
    errors.push(
      `${location}: name must be 1-64 lowercase letters, numbers, and single hyphens.`,
    );
  }
  if (
    typeof frontmatter.description !== "string" ||
    frontmatter.description.length === 0
  ) {
    errors.push(`${location}: description must be a non-empty string.`);
  } else if (frontmatter.description.length > 1024) {
    errors.push(`${location}: description must be at most 1024 characters.`);
  }
  if (frontmatter.license !== "Apache-2.0") {
    errors.push(`${location}: license must be Apache-2.0.`);
  }
  if (
    frontmatter.compatibility !== undefined &&
    (typeof frontmatter.compatibility !== "string" ||
      frontmatter.compatibility.length > 500)
  ) {
    errors.push(
      `${location}: compatibility must be a string of at most 500 characters.`,
    );
  }

  if (
    frontmatter.metadata === null ||
    typeof frontmatter.metadata !== "object" ||
    Array.isArray(frontmatter.metadata)
  ) {
    errors.push(`${location}: metadata must be a mapping of string values.`);
  } else {
    for (const [key, value] of Object.entries(frontmatter.metadata)) {
      if (typeof value !== "string") {
        errors.push(`${location}: metadata.${key} must be a string.`);
      }
    }
    if (
      typeof frontmatter.metadata.tags !== "string" ||
      frontmatter.metadata.tags.trim().length === 0
    ) {
      errors.push(`${location}: metadata.tags must be a string.`);
    } else {
      const tags = frontmatter.metadata.tags
        .split(",")
        .map((tag) => tag.trim());
      const normalized = tags.map((tag) => tag.toLowerCase());
      if (
        tags.some(
          (tag) => !/^[a-z0-9]+(?:-[a-z0-9]+)*$/.test(tag),
        ) ||
        new Set(normalized).size !== tags.length
      ) {
        errors.push(
          `${location}: metadata.tags must contain unique lowercase kebab-case tags.`,
        );
      }
    }
  }

  const allowedFields = collection === "skills" ? stableFields : incubatorFields;
  for (const field of Object.keys(frontmatter)) {
    if (!allowedFields.has(field)) {
      const maturity = collection === "skills" ? "stable" : "incubator";
      errors.push(
        `${location}: unsupported ${maturity} frontmatter field ${field}.`,
      );
    }
  }
}

function validateSmoke(smoke, collection, directoryName, location) {
  if (smoke === null || typeof smoke !== "object" || Array.isArray(smoke)) {
    errors.push(`${location}: smoke cases must be a YAML mapping.`);
    return;
  }
  if (smoke.skill !== directoryName) {
    errors.push(`${location}: smoke skill must equal ${directoryName}.`);
  }
  if (!Array.isArray(smoke.cases)) {
    errors.push(`${location}: smoke cases must be an array.`);
    return;
  }

  const kinds = new Set();
  for (const [index, smokeCase] of smoke.cases.entries()) {
    if (
      smokeCase === null ||
      typeof smokeCase !== "object" ||
      Array.isArray(smokeCase)
    ) {
      errors.push(`${location}: smoke case ${index + 1} must be a mapping.`);
      continue;
    }
    if (!["trigger", "non-trigger"].includes(smokeCase.kind)) {
      errors.push(
        `${location}: smoke case ${index + 1} kind must be trigger or non-trigger.`,
      );
    } else {
      kinds.add(smokeCase.kind);
    }
    for (const field of ["prompt", "expected"]) {
      if (
        typeof smokeCase[field] !== "string" ||
        smokeCase[field].trim().length === 0
      ) {
        errors.push(
          `${location}: smoke case ${index + 1} ${field} must be a non-empty string.`,
        );
      }
    }
  }

  for (const requiredKind of ["trigger", "non-trigger"]) {
    if (!kinds.has(requiredKind)) {
      errors.push(
        `${location}: smoke cases must include a ${requiredKind} case.`,
      );
    }
  }
  if (
    collection === "skills" &&
    JSON.stringify(smoke).toLowerCase().includes("todo")
  ) {
    errors.push(`${location}: smoke cases must not contain TODO placeholders.`);
  }
}

async function validateLinks(
  source,
  sourceDirectory,
  skillDirectory,
  location,
) {
  const links = source.matchAll(/!?\[[^\]]*\]\(([^)\s]+)(?:\s+"[^"]*")?\)/g);
  for (const match of links) {
    const capturedTarget = match[1];
    if (capturedTarget === undefined) {
      continue;
    }
    const target = capturedTarget.replace(/^<|>$/g, "");
    if (/^(?:[a-z]+:|#)/i.test(target)) {
      continue;
    }

    const fileTarget = target.split("#", 1)[0] ?? "";
    let decodedTarget;
    try {
      decodedTarget = decodeURIComponent(fileTarget);
    } catch {
      errors.push(`${location}: reference is not valid URI syntax: ${target}.`);
      continue;
    }
    const resolved = path.resolve(sourceDirectory, decodedTarget);
    const relative = path.relative(skillDirectory, resolved);
    if (relative.startsWith("..") || path.isAbsolute(relative)) {
      errors.push(`${location}: reference escapes the skill bundle: ${target}.`);
      continue;
    }

    try {
      await access(resolved);
    } catch (error) {
      if (error.code === "ENOENT") {
        errors.push(`${location}: reference does not exist: ${target}.`);
      } else {
        throw error;
      }
    }
  }
}

async function validateScript(source, filePath, skillDirectory, location) {
  const imports = source.matchAll(
    /(?:import\s+(?:[^'"]*?\s+from\s+)?|export\s+[^'"]*?\s+from\s+|import\s*\()\s*["']([^"']+)["']/g,
  );
  for (const match of imports) {
    const specifier = match[1];
    if (specifier === "node:child_process") {
      errors.push(
        `${location}: external process module node:child_process is forbidden.`,
      );
      continue;
    }
    if (networkModules.has(specifier)) {
      warnings.push(
        `${location}: network module ${specifier} requires manual review.`,
      );
      continue;
    }
    if (specifier.startsWith("node:")) {
      continue;
    }
    if (specifier.startsWith(".") || specifier.startsWith("/")) {
      const resolved = path.resolve(path.dirname(filePath), specifier);
      const relative = path.relative(skillDirectory, resolved);
      if (relative.startsWith("..") || path.isAbsolute(relative)) {
        errors.push(
          `${location}: script import escapes the skill bundle: ${specifier}.`,
        );
      } else {
        try {
          await access(resolved);
        } catch (error) {
          if (error.code === "ENOENT") {
            errors.push(
              `${location}: script import does not exist: ${specifier}.`,
            );
          } else {
            throw error;
          }
        }
      }
      continue;
    }
    errors.push(`${location}: runtime package import ${specifier} is forbidden.`);
  }
}

async function validateBundle(skillDirectory, location) {
  const pending = [skillDirectory];

  while (pending.length > 0) {
    const directory = pending.pop();
    const entries = await readdir(directory, { withFileTypes: true });
    for (const entry of entries) {
      const filePath = path.join(directory, entry.name);
      const relative = path.relative(skillDirectory, filePath);
      const itemLocation = `${location}/${relative}`;

      if (entry.isSymbolicLink()) {
        errors.push(`${itemLocation}: symlinks are forbidden.`);
        continue;
      }
      if (entry.isDirectory()) {
        pending.push(filePath);
        continue;
      }
      if (!entry.isFile()) {
        errors.push(`${itemLocation}: unsupported filesystem entry.`);
        continue;
      }

      const extension = path.extname(entry.name).toLowerCase();
      if (forbiddenExecutableExtensions.has(extension)) {
        errors.push(
          `${itemLocation}: opaque executable file type ${extension} is forbidden.`,
        );
      }
      if (forbiddenOpaqueExtensions.has(extension)) {
        errors.push(
          `${itemLocation}: opaque bundled file type ${extension} is forbidden.`,
        );
      }
      if (!textExtensions.has(extension)) {
        continue;
      }

      const source = await readFile(filePath, "utf8");
      for (const secret of secretPatterns) {
        if (secret.pattern.test(source)) {
          errors.push(`${itemLocation}: possible ${secret.label}.`);
        }
      }
      if (relative.startsWith(`scripts${path.sep}`)) {
        if (extension !== ".mjs") {
          errors.push(`${itemLocation}: skill scripts must use the .mjs extension.`);
        } else {
          await validateScript(source, filePath, skillDirectory, itemLocation);
        }
      }
      if (extension === ".md") {
        await validateLinks(
          source,
          path.dirname(filePath),
          skillDirectory,
          itemLocation,
        );
      }
    }
  }
}

async function directoriesAt(directory) {
  try {
    const entries = await readdir(directory, { withFileTypes: true });
    return entries.filter((entry) => entry.isDirectory() && !entry.name.startsWith("."));
  } catch (error) {
    if (error.code === "ENOENT") {
      return [];
    }
    throw error;
  }
}

for (const collection of collections) {
  const collectionDirectory = path.join(root, collection);
  for (const entry of await directoriesAt(collectionDirectory)) {
    const relative = `${collection}/${entry.name}`;
    let source;
    try {
      source = await readFile(
        path.join(collectionDirectory, entry.name, "SKILL.md"),
        "utf8",
      );
    } catch (error) {
      errors.push(
        `${relative}: ${error.code === "ENOENT" ? "missing SKILL.md" : error.message}.`,
      );
      continue;
    }

    const frontmatter = parseSkillDocument(source, relative);
    if (!frontmatter) {
      continue;
    }

    skillCount += 1;
    if (source.split(/\r?\n/).length > 500) {
      errors.push(`${relative}: SKILL.md must not exceed 500 lines.`);
    }
    validateFrontmatter(frontmatter, collection, entry.name, relative);
    await validateBundle(
      path.join(collectionDirectory, entry.name),
      relative,
    );
    if (typeof frontmatter.name === "string") {
      const previous = seenNames.get(frontmatter.name);
      if (previous) {
        errors.push(
          `${relative}: duplicate skill name ${frontmatter.name} in ${previous} and ${relative}.`,
        );
      } else {
        seenNames.set(frontmatter.name, relative);
      }
    }

    try {
      const smoke = parse(
        await readFile(
          path.join(root, "tests", "smoke", `${entry.name}.yaml`),
          "utf8",
        ),
      );
      validateSmoke(smoke, collection, entry.name, relative);
    } catch (error) {
      errors.push(`${relative}: missing or invalid smoke cases (${error.message}).`);
    }
  }
}

if (warnings.length > 0) {
  console.error(warnings.map((warning) => `WARNING: ${warning}`).join("\n"));
}

if (errors.length > 0) {
  console.error(errors.map((error) => `ERROR: ${error}`).join("\n"));
  process.exit(1);
}

console.log(`Validated ${skillCount} skill${skillCount === 1 ? "" : "s"}.`);
