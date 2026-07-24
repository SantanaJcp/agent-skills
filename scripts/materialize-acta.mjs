#!/usr/bin/env node

import { createHash } from "node:crypto";
import { access, mkdir, readFile, unlink, writeFile } from "node:fs/promises";
import path from "node:path";

const args = process.argv.slice(2);
const checkOnly = args.includes("--check");
const rootIndex = args.indexOf("--root");
const rootArgument = rootIndex >= 0 ? args[rootIndex + 1] : undefined;
if (rootIndex >= 0 && rootArgument === undefined) {
  throw new Error("--root requires a directory argument.");
}
const root = path.resolve(rootArgument ?? process.cwd());
const sourceRoot = path.join(root, "design", "acta");
const collectionRoot = path.join(root, "skills");
const textOnlySkill = "make-me-realize";
const expectedRecipes = [
  "three-code-paths",
  "interface-directions",
  "change-blueprint",
  "build-with-notes",
  "do-i-understand-this",
  "feel-the-flow",
  "feature-xray",
  "concept-lab",
  "what-just-happened",
  "draw-the-flow",
  "draw-it-in-svg",
  "deepen-the-codebase",
  "find-the-cause",
  "learning-workbench",
];

function digest(parts) {
  const hash = createHash("sha256");
  for (const part of parts) hash.update(part).update("\0");
  return hash.digest("hex");
}

function escapeHtml(value) {
  return String(value)
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;");
}

async function read(relative) {
  return readFile(path.join(sourceRoot, relative), "utf8");
}

const version = (await read("VERSION")).trim();
if (version !== "0.1.0") throw new Error(`Unsupported Acta version ${version}.`);
const protocol = await read("protocol.md");
const components = await read("components.md");
const css = await read("acta.css");
const javascript = await read("acta.js");
const recipes = JSON.parse(await read("recipes.json"));
const recipeNames = Object.keys(recipes).sort();
assertSameNames(recipeNames, [...expectedRecipes].sort());

function assertSameNames(actual, expected) {
  if (actual.length !== expected.length || actual.some((name, index) => name !== expected[index])) {
    throw new Error(`Acta recipes must be exactly: ${expected.join(", ")}.`);
  }
}

function renderProtocol() {
  const sha = digest([version, protocol]);
  return `<!-- acta-materialized: v${version} protocol sha256=${sha}; do not edit by hand -->\n${protocol}`;
}

function renderHtml(name, recipe, instrument) {
  const sha = digest([version, components, css, javascript, JSON.stringify(recipe), instrument]);
  const title = escapeHtml(recipe.title);
  const family = escapeHtml(recipe.family);
  const lede = escapeHtml(recipe.lede);
  return `<!-- acta-materialized: v${version} recipe=${name} sha256=${sha}; do not edit by hand -->
<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>${title} · Acta</title>
<style>
${css}</style>
</head>
<body>
<a class="skip" href="#acta-content">Skip to content</a>
<div class="acta-shell">
<header>
<dl class="acta-prov">
<div><dt>Artifact</dt><dd>${title}</dd></div>
<div><dt>Skill</dt><dd>${name}</dd></div>
<div><dt>Family</dt><dd>${family}</dd></div>
<div><dt>Source revision</dt><dd>[full Git SHA or not available]</dd></div>
</dl>
<p class="acta-prov-note">Acta v${version} · Generated from canonical Markdown/JSON state · Regenerate when inputs or source revision change.</p>
<div class="acta-context">
<p class="acta-eyebrow">${family} artifact · <span class="acta-stamp is-draft">Draft</span></p>
<h1 class="acta-title">${title}</h1>
<p class="acta-lede">${lede}</p>
</div>
<div class="acta-source"><span class="sp-k">Source prompt</span><blockquote>[Insert the user's request or a concise faithful restatement.]</blockquote></div>
<div class="acta-summary"><p class="sm-k">Summary</p><p>[State the decision-relevant overview before detail.]</p></div>
<nav class="acta-toc" aria-label="Artifact sections"><ol><li><a href="#acta-content"><span class="n">01</span>Instrument</a></li><li><a href="#acta-sources"><span class="n">02</span>Sources</a></li></ol></nav>
</header>
<main id="acta-content">
<section class="acta-section" aria-labelledby="instrument-title">
<h2 id="instrument-title" class="visually-hidden">${title} instrument</h2>
${instrument}</section>
</main>
<section class="acta-export" aria-labelledby="export-title">
<div><h2 id="export-title">Export the current state</h2><p>Persist deliberate state in Markdown and, when structured, JSON.</p></div>
<div><button class="acta-btn" type="button" data-copy-block="canonical-export" data-copy-label="Markdown export">Copy Markdown</button></div>
<pre id="canonical-export" class="visually-hidden">---
acta_protocol: "0.1"
artifact_kind: "${name}"
producer_skill: "${name}"
initiative: "[confirmed-slug]"
status: "draft"
language: "en"
source_revision: null
inputs: []
decisions: []
supersedes: null
---

[Canonical artifact content.]</pre>
<p class="acta-status" data-status aria-live="polite"></p>
</section>
<section id="acta-sources" class="acta-section"><h2 class="acta-h2">Sources</h2><ol><li>[E1] [repo-relative location or trusted source]</li></ol></section>
<footer class="acta-colophon"><p>Acta is a print-first engineering record. Fact = directly supported; Inference = reasoned from evidence; Simplification = deliberately reduced model.</p></footer>
<noscript><div class="acta-noscript">JavaScript is unavailable. All essential content remains readable; copy the canonical text manually to persist a decision.</div></noscript>
</div>
<script>
${javascript}</script>
</body>
</html>
`;
}

async function syncFile(target, content) {
  if (checkOnly) {
    let existing;
    try { existing = await readFile(target, "utf8"); }
    catch (error) {
      if (error.code === "ENOENT") throw new Error(`${path.relative(root, target)} is missing. Run npm run acta.`);
      throw error;
    }
    if (existing !== content) throw new Error(`${path.relative(root, target)} is stale. Run npm run acta.`);
    return;
  }
  await mkdir(path.dirname(target), { recursive: true });
  await writeFile(target, content);
}

const protocolOutput = renderProtocol();
for (const name of [textOnlySkill, ...expectedRecipes]) {
  const skillRoot = path.join(collectionRoot, name);
  await access(path.join(skillRoot, "SKILL.md"));
  await syncFile(path.join(skillRoot, "references", "acta-protocol.md"), protocolOutput);
  const scaffold = path.join(skillRoot, "references", "acta-scaffold.html");
  if (name === textOnlySkill) {
    try {
      await access(scaffold);
      if (checkOnly) throw new Error(`${path.relative(root, scaffold)} must not exist for the text-only skill.`);
      await unlink(scaffold);
    } catch (error) {
      if (error.code !== "ENOENT") throw error;
    }
    continue;
  }
  const instrument = await read(`recipes/${name}.html`);
  await syncFile(scaffold, renderHtml(name, recipes[name], instrument));
}

console.log(checkOnly ? "Acta materialized files are current." : "Materialized Acta 0.1.0 into 15 skill bundles.");
