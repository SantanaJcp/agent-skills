#!/usr/bin/env node

/* Bundled Acta v2 instrument generator (installed with each applicable skill).
 *
 * Usage, from anywhere:
 *   node <skill>/references/acta2/generate-instrument.mjs \
 *     --scenario .agent-work/<initiative>/<skill>/scenario.json \
 *     --out .agent-work/<initiative>/<skill>/instrument.html
 *
 * Reads the structured scenario JSON, renders the complete self-contained
 * instrument (static no-JS DOM, data island, and runtime all derived from
 * that one input), and writes it to --out. Never hand-edit the output;
 * change the scenario JSON and regenerate. Node built-ins only.
 */

import { readFile, writeFile } from "node:fs/promises";
import path from "node:path";
import { fileURLToPath } from "node:url";

import { renderInstrumentHtml } from "./assemble.mjs";
import { renderBody } from "./body.mjs";

const here = path.dirname(fileURLToPath(import.meta.url));

function argValue(name) {
  const index = process.argv.indexOf(name);
  if (index === -1 || process.argv[index + 1] === undefined) {
    throw new Error(`${name} <value> is required.`);
  }
  return process.argv[index + 1];
}

const scenarioPath = argValue("--scenario");
const outPath = argValue("--out");

const bundle = JSON.parse(await readFile(path.join(here, "bundle.json"), "utf8"));
const data = JSON.parse(await readFile(scenarioPath, "utf8"));
if (data.skill !== bundle.skill || data.kind !== bundle.kind) {
  throw new Error(
    `Scenario is for ${data.skill}/${data.kind}; this bundle generates ${bundle.skill}/${bundle.kind}.`,
  );
}

const exportCoreSource = await readFile(path.join(here, "export-core.mjs"), "utf8");
const inlineCore = exportCoreSource.replace(
  /\/\* ACTA2-ESM-START[\s\S]*ACTA2-ESM-END \*\//,
  "/* ESM exports stripped for inline use */",
);

const html = renderInstrumentHtml({
  name: bundle.skill,
  version: bundle.version,
  data,
  baseCss: await readFile(path.join(here, "base.css"), "utf8"),
  topologyCss: await readFile(path.join(here, "topology.css"), "utf8"),
  runtimeJs: await readFile(path.join(here, "runtime.js"), "utf8"),
  inlineCore,
  instrumentJs: await readFile(path.join(here, "instrument.js"), "utf8"),
  renderBody,
});

await writeFile(outPath, html);
console.log(`Generated ${outPath} from ${scenarioPath} (Acta v${bundle.version}, ${bundle.skill}).`);
