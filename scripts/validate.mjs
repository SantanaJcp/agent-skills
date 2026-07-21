#!/usr/bin/env node

import { access, readdir, readFile } from "node:fs/promises";
import path from "node:path";
import { parse as parseJavaScript } from "acorn";
import { parse } from "yaml";
import { parseSkillFrontmatter } from "./lib/parse-skill-frontmatter.mjs";

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
  ".key",
  ".md",
  ".mjs",
  ".pem",
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
const compatibleAssetLicenses = new Set([
  "Apache-2.0",
  "BSD-2-Clause",
  "BSD-3-Clause",
  "CC-BY-4.0",
  "CC0-1.0",
  "MIT",
]);
const networkGlobals = new Set(["fetch", "WebSocket", "EventSource"]);
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
  try {
    return parseSkillFrontmatter(source, location);
  } catch (error) {
    errors.push(error.message);
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
  sourceFile,
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
    if (
      path.basename(sourceFile) !== "SKILL.md" &&
      path.extname(resolved).toLowerCase() === ".md"
    ) {
      errors.push(
        `${location}: Markdown references must stay one hop from SKILL.md: ${target}.`,
      );
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
  let program;
  try {
    program = parseJavaScript(source, {
      allowHashBang: true,
      ecmaVersion: "latest",
      sourceType: "module",
    });
  } catch (error) {
    errors.push(`${location}: invalid JavaScript (${error.message}).`);
    return;
  }

  const specifiers = [];
  const usedNetworkGlobals = new Set();
  /** @param {any} node */
  function visit(node) {
    if (
      ["ImportDeclaration", "ExportNamedDeclaration", "ExportAllDeclaration"].includes(
        node.type,
      ) &&
      typeof node.source?.value === "string"
    ) {
      specifiers.push(node.source.value);
    } else if (node.type === "ImportExpression") {
      if (node.source?.type === "Literal" && typeof node.source.value === "string") {
        specifiers.push(node.source.value);
      } else {
        errors.push(`${location}: dynamic imports must use one literal specifier.`);
      }
    }

    if (["CallExpression", "NewExpression"].includes(node.type)) {
      let calledName;
      if (node.callee?.type === "Identifier") {
        calledName = node.callee.name;
      } else if (node.callee?.type === "MemberExpression") {
        if (!node.callee.computed && node.callee.property?.type === "Identifier") {
          calledName = node.callee.property.name;
        } else if (
          node.callee.computed &&
          node.callee.property?.type === "Literal" &&
          typeof node.callee.property.value === "string"
        ) {
          calledName = node.callee.property.value;
        }
      }
      if (networkGlobals.has(calledName)) {
        usedNetworkGlobals.add(calledName);
      }
      if (calledName === "getBuiltinModule") {
        errors.push(
          `${location}: process.getBuiltinModule is forbidden because it can bypass dependency checks.`,
        );
      }
      if (calledName === "require") {
        errors.push(`${location}: CommonJS require calls are forbidden.`);
      }
    }

    for (const value of Object.values(node)) {
      if (Array.isArray(value)) {
        for (const child of value) {
          if (child?.type !== undefined) {
            visit(child);
          }
        }
      } else if (value?.type !== undefined) {
        visit(value);
      }
    }
  }
  visit(program);

  for (const specifier of specifiers) {
    if (specifier === "node:child_process") {
      errors.push(
        `${location}: external process module node:child_process is forbidden.`,
      );
      continue;
    }
    if (specifier === "node:module") {
      errors.push(
        `${location}: dependency-loading module node:module is forbidden.`,
      );
      continue;
    }
    if (
      [...networkModules].some(
        (networkModule) =>
          specifier === networkModule || specifier.startsWith(`${networkModule}/`),
      )
    ) {
      warnings.push(
        `${location}: network module ${specifier} requires manual review.`,
      );
      continue;
    }
    if (specifier.startsWith("node:")) {
      continue;
    }
    if (path.posix.isAbsolute(specifier) || path.win32.isAbsolute(specifier)) {
      errors.push(`${location}: absolute script import ${specifier} is forbidden.`);
      continue;
    }
    if (specifier.startsWith(".")) {
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

  for (const name of usedNetworkGlobals) {
    warnings.push(`${location}: global ${name} requires manual network review.`);
  }
}

function parseNoticeSections(source) {
  const sections = new Map();
  let current = null;
  for (const line of source.split(/\r?\n/)) {
    const heading = line.match(/^##\s+`?(.+?)`?\s*$/);
    if (heading?.[1] !== undefined) {
      current = heading[1];
      sections.set(current, []);
    } else if (current !== null) {
      sections.get(current).push(line);
    }
  }
  return new Map(
    [...sections].map(([heading, lines]) => [heading, lines.join("\n")]),
  );
}

async function validateBundle(skillDirectory, location) {
  const pending = [skillDirectory];
  const assetPaths = [];

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
      if (relative.split(path.sep)[0] === "assets") {
        assetPaths.push(relative.split(path.sep).join("/"));
      }
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
      const source = await readFile(filePath, "utf8");
      for (const secret of secretPatterns) {
        if (secret.pattern.test(source)) {
          errors.push(`${itemLocation}: possible ${secret.label}.`);
        }
      }
      if (!textExtensions.has(extension)) {
        continue;
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
          filePath,
          path.dirname(filePath),
          skillDirectory,
          itemLocation,
        );
      }
    }
  }

  if (assetPaths.length > 0) {
    const notices = path.join(skillDirectory, "THIRD_PARTY_NOTICES.md");
    try {
      const noticeSource = await readFile(notices, "utf8");
      if (noticeSource.trim().length === 0) {
        errors.push(`${location}: THIRD_PARTY_NOTICES.md must not be empty.`);
      } else {
        const sections = parseNoticeSections(noticeSource);
        for (const assetPath of assetPaths.sort()) {
          const section = sections.get(assetPath);
          if (section === undefined) {
            errors.push(
              `${location}: THIRD_PARTY_NOTICES.md is missing a notice section for ${assetPath}.`,
            );
            continue;
          }
          const source = section.match(/^- Source:\s*(\S.*)$/m)?.[1];
          const copyright = section.match(/^- Copyright:\s*(\S.*)$/m)?.[1];
          const license = section.match(/^- License:\s*(\S.*)$/m)?.[1];
          if (
            source === undefined ||
            copyright === undefined ||
            license === undefined ||
            /\bTODO\b/i.test(`${source} ${copyright} ${license}`)
          ) {
            errors.push(
              `${location}: notice for ${assetPath} must include concrete Source, Copyright, and License fields.`,
            );
          } else if (!compatibleAssetLicenses.has(license)) {
            errors.push(
              `${location}: notice for ${assetPath} uses unsupported license ${license}.`,
            );
          }
        }
      }
    } catch (error) {
      if (error.code === "ENOENT") {
        errors.push(`${location}: assets require THIRD_PARTY_NOTICES.md.`);
      } else {
        throw error;
      }
    }
  }
}

async function directoriesAt(directory, collection) {
  try {
    const entries = await readdir(directory, { withFileTypes: true });
    const directories = [];
    for (const entry of entries) {
      if (entry.name.startsWith(".")) {
        continue;
      }
      const location = `${collection}/${entry.name}`;
      if (entry.isSymbolicLink()) {
        errors.push(`${location}: symlinks are forbidden.`);
      } else if (entry.isDirectory()) {
        directories.push(entry);
      } else {
        errors.push(`${location}: collection entries must be skill directories.`);
      }
    }
    return directories;
  } catch (error) {
    if (error.code === "ENOENT") {
      return [];
    }
    throw error;
  }
}

for (const collection of collections) {
  const collectionDirectory = path.join(root, collection);
  for (const entry of await directoriesAt(collectionDirectory, collection)) {
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
