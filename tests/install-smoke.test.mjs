import assert from "node:assert/strict";
import path from "node:path";
import { spawnSync } from "node:child_process";
import test from "node:test";

const repositoryRoot = path.resolve(import.meta.dirname, "..");
const installerSmoke = path.join(repositoryRoot, "scripts", "install-smoke.mjs");

test("consumer can discover and install a portable skill for both clients", () => {
  const result = spawnSync(process.execPath, [installerSmoke], {
    cwd: repositoryRoot,
    encoding: "utf8",
    env: {
      ...process.env,
      CI: "1",
      DISABLE_TELEMETRY: "1",
    },
  });

  assert.equal(result.status, 0, result.stderr);
  assert.match(
    result.stdout,
    /real full-suite install, all isolated skill installs, and installed Acta v2 generators passed/,
  );
});
