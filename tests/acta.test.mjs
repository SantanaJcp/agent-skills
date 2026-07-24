import assert from "node:assert/strict";
import { cp, mkdtemp, readFile, writeFile } from "node:fs/promises";
import path from "node:path";
import { spawnSync } from "node:child_process";
import test from "node:test";
import { tmpdir } from "node:os";
import { parse } from "yaml";

const root = path.resolve(import.meta.dirname, "..");
const skills = [
  "make-me-realize",
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
const htmlSkills = skills.filter((name) => name !== "make-me-realize");

function runScript(script, args = []) {
  return spawnSync(process.execPath, [path.join(root, "scripts", script), ...args], {
    cwd: root,
    encoding: "utf8",
  });
}

test("publisher materializes the complete Acta bundle deterministically", async () => {
  const result = runScript("materialize-acta.mjs", ["--check"]);
  assert.equal(result.status, 0, `${result.stdout}\n${result.stderr}`);

  assert.equal((await readFile(path.join(root, "design/acta/VERSION"), "utf8")).trim(), "0.1.0");
  const protocols = [];
  for (const name of skills) {
    const skillRoot = path.join(root, "skills", name);
    const protocol = await readFile(path.join(skillRoot, "references", "acta-protocol.md"), "utf8");
    protocols.push(protocol);
    assert.match(protocol, /^<!-- acta-materialized: v0\.1\.0 protocol sha256=[a-f0-9]{64}; do not edit by hand -->/);

    const sidecar = parse(await readFile(path.join(skillRoot, "agents", "openai.yaml"), "utf8"));
    assert.equal(typeof sidecar.interface?.display_name, "string");
    assert.match(sidecar.interface.short_description, /^.{25,64}$/s);
    assert.match(sidecar.interface.default_prompt, new RegExp(`\\$${name}(?:\\s|[.,;:!?]|$)`));
    assert.deepEqual(Object.keys(sidecar).sort(), ["interface"]);
  }
  assert.equal(new Set(protocols).size, 1, "all installed protocol copies must be identical");

  for (const name of htmlSkills) {
    const html = await readFile(path.join(root, "skills", name, "references", "acta-scaffold.html"), "utf8");
    assert.match(html, new RegExp(`^<!-- acta-materialized: v0\\.1\\.0 recipe=${name} sha256=[a-f0-9]{64}; do not edit by hand -->`));
    assert.match(html, /<!doctype html>/i);
    assert.match(html, /class="acta-shell"/);
    assert.match(html, /class="acta-prov"/);
    assert.match(html, /class="acta-context"/);
    assert.match(html, /class="acta-summary"/);
    assert.match(html, /class="acta-export"/);
    assert.match(html, /<noscript>/);
    assert.match(html, /aria-live="polite"/);
    assert.match(html, /@media print/);
    assert.match(html, /prefers-reduced-motion/);
    assert.doesNotMatch(html, /(?:src|href)=["']https?:/i);
    assert.doesNotMatch(html, /\son[a-z]+\s*=/i);
    assert.doesNotMatch(html, /\b(?:innerHTML|outerHTML|insertAdjacentHTML|document\.write|eval)\b/);
    assert.doesNotMatch(html, /localStorage|sessionStorage/);
  }

  await assert.rejects(
    readFile(path.join(root, "skills", "make-me-realize", "references", "acta-scaffold.html"), "utf8"),
    { code: "ENOENT" },
  );
});

test("Acta static validation accepts every materialized recipe", () => {
  const result = runScript("validate-acta.mjs");
  assert.equal(result.status, 0, `${result.stdout}\n${result.stderr}`);
  assert.match(result.stdout, /Validated 14 Acta HTML recipes and 15 protocol copies\./);
});

test("Claude design deliverables are preserved as immutable provenance", async () => {
  const expected = new Map([
    ["research-findings.md", "23f62970f962c971c08a56fe5689fe3a83faf6aadf9824f71ba3c032b8cf7bac"],
    ["direcciones-comparador.html", "09347c45604b9e4924f73e0e499c930de869f7c23d4c571b0f7970fbf2f76199"],
    ["component-sheet.html", "906025cd3e70845f31bfde7684780927b1bf2150d90aa23023aa302de10ad6cf"],
    ["design-system-spec.md", "3b3bad4008a0137608ed0e915c2dbb66fa17f25dc267661a92d59c207e9db0aa"],
    ["qa-report.md", "b6b8faee1410b0371c2ec0808b7a8abfd0c0180d30d0d10493b634c9434b061f"],
  ]);
  const { createHash } = await import("node:crypto");
  for (const [name, digest] of expected) {
    const source = await readFile(path.join(root, "docs", "design", "acta", "provenance", name));
    assert.equal(createHash("sha256").update(source).digest("hex"), digest, name);
  }
});

test("cross-skill collision cases cover every load-bearing boundary", async () => {
  const matrix = parse(
    await readFile(path.join(root, "tests", "smoke", "collisions.yaml"), "utf8"),
  );
  const expectedPairs = new Set([
    "change-blueprint|make-me-realize",
    "interface-directions|three-code-paths",
    "build-with-notes|feel-the-flow",
    "concept-lab|feature-xray",
    "find-the-cause|what-just-happened",
    "build-with-notes|deepen-the-codebase",
    "draw-it-in-svg|draw-the-flow",
  ]);
  assert.equal(matrix.version, 1);
  assert.equal(matrix.cases.length, expectedPairs.size);
  const actualPairs = new Set();
  for (const collision of matrix.cases) {
    const pair = [collision.left, collision.right].sort().join("|");
    actualPairs.add(pair);
    assert.equal(typeof collision.prompt, "string");
    assert.ok(collision.prompt.length > 20);
    assert.equal(typeof collision.expected, "string");
    assert.ok(collision.expected.includes("$"));
  }
  assert.deepEqual(actualPairs, expectedPairs);
});

test("realistic filled Acta artifacts exercise all HTML recipes outside skill bundles", async () => {
  for (const name of htmlSkills) {
    const fixture = await readFile(
      path.join(root, "tests", "fixtures", "acta", `${name}.html`),
      "utf8",
    );
    assert.match(fixture, new RegExp(`^<!-- acta-fixture: recipe=${name}; non-production QA evidence -->`));
    assert.match(fixture, /<!doctype html>/i);
    assert.match(fixture, /class="acta-shell"/);
    assert.doesNotMatch(
      fixture,
      /\[(?:full Git SHA or not available|Insert the user's request|State the decision-relevant overview before detail|Canonical artifact content|repo-relative location or trusted source|confirmed-slug)\]/,
    );
  }
});


test("Acta validation rejects broken visual and interaction contracts", async () => {
  const fixtureRoot = await mkdtemp(path.join(tmpdir(), "acta-contracts-"));
  await cp(path.join(root, "skills"), path.join(fixtureRoot, "skills"), {
    recursive: true,
  });
  const target = path.join(
    fixtureRoot,
    "skills",
    "three-code-paths",
    "references",
    "acta-scaffold.html",
  );
  const broken = (await readFile(target, "utf8"))
    .replace("--acta-action:#2B4C7E", "--acta-action:#FDFDFB")
    .replace("--acta-radius:2px", "--acta-radius:8px")
    .replace("@media (max-width:719px)", "@media (max-width:718px)")
    .replace('document.execCommand("copy")', "false");
  await writeFile(target, broken);

  const result = runScript("validate-acta.mjs", ["--root", fixtureRoot]);

  assert.equal(result.status, 1);
  assert.match(result.stderr, /contrast/i);
  assert.match(result.stderr, /radius/i);
  assert.match(result.stderr, /720px responsive breakpoint/i);
  assert.match(result.stderr, /clipboard fallback/i);
});

test("Acta materialization is repeatable, LF-only, and rejects unknown recipes", async () => {
  const fixtureRoot = await mkdtemp(path.join(tmpdir(), "acta-materializer-"));
  await cp(path.join(root, "design"), path.join(fixtureRoot, "design"), {
    recursive: true,
  });
  await cp(path.join(root, "skills"), path.join(fixtureRoot, "skills"), {
    recursive: true,
  });
  const firstRun = runScript("materialize-acta.mjs", ["--root", fixtureRoot]);
  assert.equal(firstRun.status, 0, `${firstRun.stdout}\n${firstRun.stderr}`);

  const snapshots = new Map();
  for (const name of skills) {
    const protocolPath = path.join(
      fixtureRoot,
      "skills",
      name,
      "references",
      "acta-protocol.md",
    );
    snapshots.set(protocolPath, await readFile(protocolPath, "utf8"));
    if (name !== "make-me-realize") {
      const scaffoldPath = path.join(
        fixtureRoot,
        "skills",
        name,
        "references",
        "acta-scaffold.html",
      );
      snapshots.set(scaffoldPath, await readFile(scaffoldPath, "utf8"));
    }
  }
  const secondRun = runScript("materialize-acta.mjs", ["--root", fixtureRoot]);
  assert.equal(secondRun.status, 0, `${secondRun.stdout}\n${secondRun.stderr}`);
  for (const [file, firstContent] of snapshots) {
    const secondContent = await readFile(file, "utf8");
    assert.equal(secondContent, firstContent, path.relative(fixtureRoot, file));
    assert.doesNotMatch(secondContent, /\r/, path.relative(fixtureRoot, file));
  }

  const recipesPath = path.join(fixtureRoot, "design", "acta", "recipes.json");
  const recipes = JSON.parse(await readFile(recipesPath, "utf8"));
  recipes["unknown-recipe"] = {
    title: "Unknown",
    family: "Document",
    lede: "This recipe must be rejected.",
  };
  await writeFile(recipesPath, JSON.stringify(recipes, null, 2));
  const rejectedRun = runScript("materialize-acta.mjs", ["--root", fixtureRoot]);
  assert.equal(rejectedRun.status, 1);
  assert.match(rejectedRun.stderr, /Acta recipes must be exactly/);
});
