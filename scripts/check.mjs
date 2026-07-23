#!/usr/bin/env node

import path from "node:path";
import { spawnSync } from "node:child_process";

const root = path.resolve(import.meta.dirname, "..");
/** @type {Array<[string, string[]]>} */
const commands = [
  [process.execPath, ["--test", "tests/*.test.mjs"]],
  [
    process.execPath,
    [
      path.join(root, "node_modules", "typescript", "bin", "tsc"),
      "-p",
      "jsconfig.json",
    ],
  ],
  ["node", ["scripts/validate-repository.mjs"]],
  ["node", ["scripts/materialize-acta.mjs", "--check"]],
  ["node", ["scripts/validate-acta.mjs"]],
  ["node", ["scripts/materialize-acta2.mjs", "--check"]],
  ["node", ["scripts/validate-acta2.mjs"]],
  ["node", ["scripts/validate.mjs"]],
  ["node", ["scripts/generate-catalog.mjs", "--check"]],
];

for (const [command, args] of commands) {
  const result = spawnSync(command, args, {
    cwd: root,
    encoding: "utf8",
    stdio: "inherit",
  });
  if (result.status !== 0) {
    process.exit(result.status ?? 1);
  }
}

console.log("All repository checks passed.");
