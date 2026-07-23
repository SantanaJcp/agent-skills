#!/usr/bin/env node

import { spawnSync } from "node:child_process";
import {
  access,
  cp,
  lstat,
  mkdir,
  mkdtemp,
  readdir,
  readFile,
  rename,
  rm,
  writeFile,
} from "node:fs/promises";
import path from "node:path";

const defaultSourceRoot = path.resolve(import.meta.dirname, "..");
let sourceRoot = defaultSourceRoot;
const expectedSkills = [
  "build-with-notes",
  "change-blueprint",
  "concept-lab",
  "deepen-the-codebase",
  "do-i-understand-this",
  "draw-it-in-svg",
  "draw-the-flow",
  "feature-xray",
  "feel-the-flow",
  "find-the-cause",
  "interface-directions",
  "learning-workbench",
  "make-me-realize",
  "three-code-paths",
  "what-just-happened",
];
const variants = ["with-sidecars", "without-sidecars"];

function fail(message) {
  console.error(`ERROR: ${message}`);
  process.exit(1);
}

function parseArguments(args) {
  const values = new Map();
  for (let index = 0; index < args.length; index += 2) {
    const flag = args[index];
    const value = args[index + 1];
    if (!["--destination", "--source-root"].includes(flag) || value === undefined) {
      fail("Usage: npm run qa:prepare -- --destination <directory> [--source-root <clean-repository>]");
    }
    if (values.has(flag)) fail(`duplicate argument ${flag}.`);
    values.set(flag, value);
  }
  return values;
}

function git(args) {
  return spawnSync("git", args, {
    cwd: sourceRoot,
    encoding: "utf8",
  });
}

function resolveRevision() {
  const status = git(["status", "--porcelain"]);
  if (status.status !== 0) fail(`cannot inspect the source worktree (${status.stderr.trim()}).`);
  if (status.stdout.trim().length > 0) {
    fail("source worktree must be clean so the QA manifest identifies the exact tested content.");
  }
  const head = git(["rev-parse", "HEAD"]);
  if (head.status !== 0) fail(`cannot resolve source revision (${head.stderr.trim()}).`);
  const revision = head.stdout.trim().toLowerCase();
  if (!/^[a-f0-9]{40}$/.test(revision)) fail("git returned an invalid source revision.");
  return revision;
}

async function exists(target) {
  try {
    await lstat(target);
    return true;
  } catch (error) {
    if (error.code === "ENOENT") return false;
    throw error;
  }
}

async function requireEntry(relative) {
  try {
    await access(path.join(sourceRoot, relative));
  } catch (error) {
    if (error.code === "ENOENT") fail(`required QA source ${relative} is missing.`);
    throw error;
  }
}

async function copyDirectoryContents(source, destination) {
  await mkdir(destination, { recursive: true });
  for (const entry of await readdir(source, { withFileTypes: true })) {
    await cp(path.join(source, entry.name), path.join(destination, entry.name), {
      recursive: true,
    });
  }
}

async function prepareVariant(
  stagingRoot,
  variant,
  revision,
  actaVersion,
  acta2Version,
) {
  const harness = path.join(stagingRoot, variant);
  await mkdir(harness, { recursive: true });
  await copyDirectoryContents(
    path.join(sourceRoot, "tests", "fixtures", "core-cycle-project"),
    harness,
  );
  await cp(
    path.join(sourceRoot, "tests", "fixtures", "acta2"),
    path.join(harness, "acta-fixtures"),
    { recursive: true },
  );
  await cp(
    path.join(sourceRoot, "tests", "smoke"),
    path.join(harness, "smoke-cases"),
    { recursive: true },
  );
  await cp(
    path.join(sourceRoot, "docs", "qa", "evaluator-runbook.md"),
    path.join(harness, "EVALUATOR-RUNBOOK.md"),
  );
  await cp(
    path.join(sourceRoot, "docs", "qa", "evidence", "template.md"),
    path.join(harness, "EVIDENCE-TEMPLATE.md"),
  );

  for (const clientRoot of [".agents", ".claude"]) {
    const skillRoot = path.join(harness, clientRoot, "skills");
    await mkdir(skillRoot, { recursive: true });
    for (const skill of expectedSkills) {
      const target = path.join(skillRoot, skill);
      await cp(path.join(sourceRoot, "incubator", skill), target, { recursive: true });
      if (variant === "without-sidecars") {
        await rm(path.join(target, "agents"), { recursive: true, force: true });
      }
    }
  }

  await writeFile(
    path.join(harness, "QA-MANIFEST.json"),
    `${JSON.stringify({
      schema_version: 2,
      suite: "acta-development-skill-suite",
      acta_version: actaVersion,
      acta2_version: acta2Version,
      active_artifact_system: "acta2",
      source_revision: revision,
      variant,
      skills: expectedSkills,
    }, null, 2)}\n`,
  );
}

const parsed = parseArguments(process.argv.slice(2));
const sourceRootArgument = parsed.get("--source-root");
sourceRoot = sourceRootArgument === undefined
  ? defaultSourceRoot
  : path.resolve(sourceRootArgument);
const destinationArgument = parsed.get("--destination");
if (destinationArgument === undefined) {
  fail("Usage: npm run qa:prepare -- --destination <directory> [--source-root <clean-repository>]");
}
const destination = path.resolve(destinationArgument);
const relativeToSource = path.relative(sourceRoot, destination);
if (relativeToSource === "" || (!relativeToSource.startsWith(`..${path.sep}`) && relativeToSource !== ".." && !path.isAbsolute(relativeToSource))) {
  fail("destination must be outside the source repository.");
}
if (await exists(destination)) fail(`destination already exists: ${destination}.`);

for (const relative of [
  "design/acta/VERSION",
  "design/acta2/VERSION",
  "docs/qa/evaluator-runbook.md",
  "docs/qa/evidence/template.md",
  "tests/fixtures/acta2",
  "tests/fixtures/core-cycle-project",
  "tests/smoke/collisions.yaml",
]) await requireEntry(relative);
for (const skill of expectedSkills) await requireEntry(`incubator/${skill}/SKILL.md`);

const revision = resolveRevision();
const actaVersion = (await readFile(path.join(sourceRoot, "design", "acta", "VERSION"), "utf8")).trim();
if (actaVersion !== "0.1.0") fail(`unsupported Acta version ${actaVersion}.`);
const acta2Version = (await readFile(path.join(sourceRoot, "design", "acta2", "VERSION"), "utf8")).trim();
if (!/^0\.2\.0(?:-pilot)?$/.test(acta2Version)) {
  fail(`unsupported Acta v2 version ${acta2Version}.`);
}

const parent = path.dirname(destination);
await mkdir(parent, { recursive: true });
const stagingRoot = await mkdtemp(path.join(parent, `.${path.basename(destination)}-`));
try {
  for (const variant of variants) {
    await prepareVariant(
      stagingRoot,
      variant,
      revision,
      actaVersion,
      acta2Version,
    );
  }
  await writeFile(
    path.join(stagingRoot, "QA-START-HERE.md"),
    `# Acta v2 manual QA harnesses\n\nSource revision: \`${revision}\`\n\nActive artifact system: Acta v2 \`${acta2Version}\` (legacy rollback: Acta \`${actaVersion}\`).\n\nOpen either \`with-sidecars/\` or \`without-sidecars/\` as the project root in Codex or Claude Code. Read \`EVALUATOR-RUNBOOK.md\` inside the selected variant before testing.\n`,
  );
  await rename(stagingRoot, destination);
} catch (error) {
  await rm(stagingRoot, { recursive: true, force: true });
  throw error;
}

console.log(`Prepared manual QA harnesses at ${destination} for ${revision}.`);
