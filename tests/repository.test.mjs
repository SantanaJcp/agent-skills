import assert from "node:assert/strict";
import path from "node:path";
import { spawnSync } from "node:child_process";
import test from "node:test";

const repositoryRoot = path.resolve(import.meta.dirname, "..");
const repositoryValidator = path.join(
  repositoryRoot,
  "scripts",
  "validate-repository.mjs",
);

test("maintainer can validate the complete repository foundation", () => {
  const result = spawnSync(process.execPath, [repositoryValidator], {
    cwd: repositoryRoot,
    encoding: "utf8",
  });

  assert.equal(result.status, 0, result.stderr);
  assert.match(result.stdout, /Validated repository foundation/);
});
