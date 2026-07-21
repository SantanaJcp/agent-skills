#!/usr/bin/env node

import { readFile, writeFile } from "node:fs/promises";
import path from "node:path";

const [version, output] = process.argv.slice(2);

if (!version || !output) {
  console.error("Usage: npm run release:notes -- <version> <output-file>");
  process.exit(1);
}

const changelog = await readFile(path.join(process.cwd(), "CHANGELOG.md"), "utf8");
const lines = changelog.split(/\r?\n/);
const heading = new RegExp(
  `^## \\[${version.replace(/[.*+?^${}()|[\]\\]/g, "\\$&")}\\] - \\d{4}-\\d{2}-\\d{2}$`,
);
const start = lines.findIndex((line) => heading.test(line));
const end = lines.findIndex(
  (line, index) => index > start && /^## \[/.test(line),
);

if (start === -1) {
  console.error(`CHANGELOG.md has no dated ${version} release section.`);
  process.exit(1);
}

const notes = lines.slice(start + 1, end === -1 ? undefined : end).join("\n").trim();
await writeFile(path.resolve(process.cwd(), output), `${notes}\n`);
console.log(`Wrote release notes for v${version} to ${output}.`);
