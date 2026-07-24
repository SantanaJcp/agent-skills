#!/usr/bin/env node

/* Bundled Acta v2 record generator (installed with each pilot skill).
 *
 * Usage, only AFTER explicit acceptance in chat:
 *   node <skill>/references/acta2/generate-record.mjs \
 *     --canonical .agent-work/<initiative>/<skill>/canonical.json \
 *     --out .agent-work/<initiative>/<skill>/record.html
 *
 * The canonical JSON ({ scenario, accepted }) is the ONLY input: records are
 * never generated from browser state or from an instrument file. Node
 * built-ins only.
 */

import { readFile, writeFile } from "node:fs/promises";
import path from "node:path";
import { fileURLToPath } from "node:url";

import { renderRecordHtml } from "./assemble.mjs";
import { renderRecord } from "./record-body.mjs";

const here = path.dirname(fileURLToPath(import.meta.url));

function argValue(name) {
  const index = process.argv.indexOf(name);
  if (index === -1 || process.argv[index + 1] === undefined) {
    throw new Error(`${name} <value> is required.`);
  }
  return process.argv[index + 1];
}

const canonicalPath = argValue("--canonical");
const outPath = argValue("--out");

const bundle = JSON.parse(await readFile(path.join(here, "bundle.json"), "utf8"));
const canonical = JSON.parse(await readFile(canonicalPath, "utf8"));

const html = renderRecordHtml({
  name: bundle.skill,
  version: bundle.version,
  canonical,
  actaCss: await readFile(path.join(here, "acta-record.css"), "utf8"),
  renderRecord,
});

await writeFile(outPath, html);
console.log(`Generated ${outPath} from ${canonicalPath} (Acta v${bundle.version}, ${bundle.skill}).`);
