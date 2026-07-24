#!/usr/bin/env node

/* Acta v2 suite materializer.
 *
 * Single-source, data-driven materialization for every HTML skill in the
 * suite manifest (design/acta2/lib/suite.mjs). All HTML assembly lives in
 * design/acta2/lib/assemble.mjs; this script (publisher side) and the bundled
 * generators installed with each skill (references/acta2/) use that same
 * implementation, so an independently installed skill regenerates artifacts
 * from scenario/canonical JSON with byte-identical logic and no hand-editing
 * of static HTML.
 *
 * Per skill (role-dependent, see the manifest) it emits deterministically:
 *   skills/<skill>/references/acta2-protocol.md
 *   skills/<skill>/references/acta2/            (generator bundle)
 *   skills/<skill>/references/instrument[-variant].html (scaffold)
 *   skills/<skill>/references/record.html               (scaffold)
 *   tests/fixtures/acta2/<skill>/scenario[-variant].json
 *   tests/fixtures/acta2/<skill>/instrument[-variant].html
 *   tests/fixtures/acta2/<skill>/canonical.json|md · record.html
 *   tests/fixtures/acta2/<skill>/candidate.md|json
 */

import { mkdir, readFile, writeFile } from "node:fs/promises";
import path from "node:path";
import { pathToFileURL } from "node:url";

const args = process.argv.slice(2);
const checkOnly = args.includes("--check");
const rootIndex = args.indexOf("--root");
const rootArgument = rootIndex >= 0 ? args[rootIndex + 1] : undefined;
if (rootIndex >= 0 && rootArgument === undefined) {
  throw new Error("--root requires a directory argument.");
}
const root = path.resolve(rootArgument ?? process.cwd());
const sourceRoot = path.join(root, "design", "acta2");

const assemble = await import(
  pathToFileURL(path.join(sourceRoot, "lib", "assemble.mjs")).href
);
const { digest, renderInstrumentHtml, renderRecordHtml, renderCanonicalMarkdown, renderCandidate } =
  assemble;
const { SUITE, variantSuffix } = await import(
  pathToFileURL(path.join(sourceRoot, "lib", "suite.mjs")).href
);

async function read(relative) {
  const content = await readFile(path.join(sourceRoot, relative), "utf8");
  if (content.includes("\r")) {
    throw new Error(`${relative} must be LF-only.`);
  }
  return content;
}

async function readOptional(relative) {
  try {
    return await read(relative);
  } catch (error) {
    if (error.code === "ENOENT") return null;
    throw error;
  }
}

const version = (await read("VERSION")).trim();
if (version !== "0.2.0") {
  throw new Error(`Unsupported Acta v2 version ${version}.`);
}
const protocol = await read("protocol.md");
const baseCss = await read("base.css");
const recordV2Css = await read("record.css");
const runtimeJs = await read("runtime.js");
const suiteSource = await read("lib/suite.mjs");
const assembleSource = await read("lib/assemble.mjs");
const generateInstrumentSource = await read("lib/generate-instrument.mjs");
const generateRecordSource = await read("lib/generate-record.mjs");
const exportCoreSource = await read("lib/export-core.mjs");
const highlightSource = await read("lib/highlight.mjs");
const flowSource = await read("lib/flow.mjs");
const figureSource = await read("lib/figure.mjs");
const inlineCore = exportCoreSource.replace(
  /\/\* ACTA2-ESM-START[\s\S]*ACTA2-ESM-END \*\//,
  "/* ESM exports stripped for inline use */",
);
if (inlineCore.includes("export {")) {
  throw new Error("export-core ESM block was not stripped for inlining.");
}
const actaV1Css = await readFile(path.join(root, "design", "acta", "acta.css"), "utf8");

/* Bundle copies must resolve their sibling lib modules, wherever they live. */
function rewriteBundleImports(source) {
  return source
    .replaceAll('from "../../lib/', 'from "./')
    .replaceAll('from "../lib/', 'from "./')
    .replace(/from "\.\.\/instruments\/[a-z-]+\//g, 'from "./');
}

async function syncFile(target, content) {
  if (content.includes("\r")) {
    throw new Error(`${path.relative(root, target)} would contain CR characters.`);
  }
  if (checkOnly) {
    let existing;
    try {
      existing = await readFile(target, "utf8");
    } catch (error) {
      if (error.code === "ENOENT") {
        throw new Error(`${path.relative(root, target)} is missing. Run npm run acta2.`);
      }
      throw error;
    }
    if (existing !== content) {
      throw new Error(`${path.relative(root, target)} is stale. Run npm run acta2.`);
    }
    return;
  }
  await mkdir(path.dirname(target), { recursive: true });
  await writeFile(target, content);
}

const protocolOutput = `<!-- acta2-materialized: v${version} protocol sha256=${digest([version, protocol])}; do not edit by hand -->\n${protocol}`;

let instrumentCount = 0;
let recordCount = 0;

for (const skill of SUITE) {
  const name = skill.name;
  const hasInstrument = skill.instruments.length > 0;
  const referencesRoot = path.join(root, "skills", name, "references");
  await syncFile(path.join(referencesRoot, "acta2-protocol.md"), protocolOutput);

  const recordCss =
    skill.record === "v1"
      ? actaV1Css
      : skill.record === "v2"
        ? `${recordV2Css}\n/* ---- ${name} record topology ---- */\n${(await readOptional(`records/${name}.css`)) ?? ""}${
            (await readOptional(`instruments/${name}/shared.css`)) ? `\n/* ---- ${name} shared surface ---- */\n${await readOptional(`instruments/${name}/shared.css`)}` : ""
          }`
        : null;

  /* ---- role-dependent assets ---- */
  const meta = JSON.parse(await read(`instruments/${name}/meta.json`));
  if (meta.skill !== name) {
    throw new Error(`${name}: meta.json skill mismatch.`);
  }
  const sharedCss = hasInstrument ? await readOptional(`instruments/${name}/shared.css`) : null;
  const topologyCss = hasInstrument
    ? `${await read(`instruments/${name}/topology.css`)}${sharedCss ? `\n/* ---- ${name} shared surface ---- */\n${sharedCss}` : ""}`
    : null;
  const instrumentJs = hasInstrument ? await read(`instruments/${name}/instrument.js`) : null;
  const bodySource = hasInstrument ? await read(`instruments/${name}/body.mjs`) : null;
  const renderBody = hasInstrument
    ? (await import(pathToFileURL(path.join(sourceRoot, `instruments/${name}/body.mjs`)).href)).renderBody
    : null;
  const recordSource = skill.record ? await read(`records/${name}.mjs`) : null;
  const renderRecord = skill.record
    ? (await import(pathToFileURL(path.join(sourceRoot, "records", `${name}.mjs`)).href)).renderRecord
    : null;

  /* ---- self-contained generator bundle ---- */
  const bundleRoot = path.join(referencesRoot, "acta2");
  const bundleMeta = `${JSON.stringify(
    {
      skill: name,
      kind: meta.kind,
      role: hasInstrument ? (skill.record ? "instrument+record" : "instrument-only") : "record-only",
      version,
      materializer: "scripts/materialize-acta2.mjs",
    },
    null,
    2,
  )}\n`;
  await syncFile(path.join(bundleRoot, "bundle.json"), bundleMeta);
  await syncFile(path.join(bundleRoot, "export-core.mjs"), exportCoreSource);
  await syncFile(path.join(bundleRoot, "highlight.mjs"), highlightSource);
  await syncFile(path.join(bundleRoot, "flow.mjs"), flowSource);
  await syncFile(path.join(bundleRoot, "figure.mjs"), figureSource);
  await syncFile(path.join(bundleRoot, "assemble.mjs"), assembleSource);
  await syncFile(path.join(bundleRoot, "base.css"), baseCss);
  await syncFile(path.join(bundleRoot, "runtime.js"), runtimeJs);
  if (hasInstrument) {
    await syncFile(path.join(bundleRoot, "body.mjs"), rewriteBundleImports(bodySource));
    await syncFile(path.join(bundleRoot, "topology.css"), topologyCss);
    await syncFile(path.join(bundleRoot, "instrument.js"), instrumentJs);
    await syncFile(path.join(bundleRoot, "generate-instrument.mjs"), generateInstrumentSource);
  }
  if (skill.record) {
    await syncFile(path.join(bundleRoot, "record-body.mjs"), rewriteBundleImports(recordSource));
    await syncFile(path.join(bundleRoot, "acta-record.css"), recordCss);
    await syncFile(path.join(bundleRoot, "generate-record.mjs"), generateRecordSource);
  }

  const renderOptions = hasInstrument
    ? {
        name,
        version,
        baseCss,
        topologyCss,
        runtimeJs,
        inlineCore,
        instrumentJs,
        renderBody,
      }
    : null;

  /* ---- installed scaffolds ---- */
  for (const variant of skill.instruments) {
    const suffix = variantSuffix(variant);
    const scaffoldData = JSON.parse(await read(`instruments/${name}/scaffold-data${suffix}.json`));
    await syncFile(
      path.join(referencesRoot, `instrument${suffix}.html`),
      renderInstrumentHtml({ ...renderOptions, data: scaffoldData }),
    );
  }
  if (skill.record) {
    const scaffoldVariant = skill.candidateVariant ?? "default";
    const scaffoldData = JSON.parse(
      await read(`instruments/${name}/scaffold-data${variantSuffix(hasInstrument ? scaffoldVariant : "default")}.json`),
    );
    const scaffoldAccepted = JSON.parse(await read(`records/${name}-scaffold-accepted.json`));
    await syncFile(
      path.join(referencesRoot, "record.html"),
      renderRecordHtml({
        name,
        version,
        canonical: { scenario: scaffoldData, accepted: scaffoldAccepted },
        actaCss: recordCss,
        renderRecord,
      }),
    );
  }

  /* ---- realistic fixtures ---- */
  const fixtureRoot = path.join(root, "tests", "fixtures", "acta2", name);
  let candidateScenario = null;
  for (const variant of skill.instruments) {
    const suffix = variantSuffix(variant);
    const scenarioSource = await read(`fixtures/${name}/scenario${suffix}.json`);
    const scenario = JSON.parse(scenarioSource);
    await syncFile(path.join(fixtureRoot, `scenario${suffix}.json`), scenarioSource);
    await syncFile(
      path.join(fixtureRoot, `instrument${suffix}.html`),
      renderInstrumentHtml({ ...renderOptions, data: scenario }),
    );
    instrumentCount += 1;
    if (variant === (skill.candidateVariant ?? "default")) candidateScenario = scenario;
  }
  if (!hasInstrument) {
    const scenarioSource = await read(`fixtures/${name}/scenario.json`);
    await syncFile(path.join(fixtureRoot, "scenario.json"), scenarioSource);
    candidateScenario = JSON.parse(scenarioSource);
  }

  if (skill.record) {
    const accepted = JSON.parse(await read(`fixtures/${name}/accepted.json`));
    const canonical = { scenario: candidateScenario, accepted };
    await syncFile(path.join(fixtureRoot, "canonical.json"), `${JSON.stringify(canonical, null, 2)}\n`);
    await syncFile(
      path.join(fixtureRoot, "record.html"),
      renderRecordHtml({ name, version, canonical, actaCss: recordCss, renderRecord }),
    );
    recordCount += 1;
    await syncFile(path.join(fixtureRoot, "canonical.md"), renderCanonicalMarkdown(canonical));
    if (hasInstrument) {
      const candidate = renderCandidate(candidateScenario, accepted.exampleWorking);
      await syncFile(path.join(fixtureRoot, "candidate.md"), candidate.markdown);
      await syncFile(path.join(fixtureRoot, "candidate.json"), `${JSON.stringify(candidate.json, null, 2)}\n`);
    }
  } else if (skill.workingFixture) {
    const working = JSON.parse(await read(`fixtures/${name}/working.json`));
    const candidate = renderCandidate(candidateScenario, working);
    await syncFile(path.join(fixtureRoot, "candidate.md"), candidate.markdown);
    await syncFile(path.join(fixtureRoot, "candidate.json"), `${JSON.stringify(candidate.json, null, 2)}\n`);
  }
}

/* suite.mjs itself ships in every bundle-independent context via tests; it is
   not copied into bundles (bundles are single-skill by design). */
void suiteSource;

console.log(
  checkOnly
    ? "Acta v2 suite materialized files are current."
    : `Materialized Acta v${version}: ${SUITE.length} skills, ${instrumentCount} instruments, ${recordCount} records.`,
);
