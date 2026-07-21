import assert from "node:assert/strict";
import { mkdir, mkdtemp, symlink, writeFile } from "node:fs/promises";
import { tmpdir } from "node:os";
import path from "node:path";
import { spawnSync } from "node:child_process";
import test from "node:test";

const repositoryRoot = path.resolve(import.meta.dirname, "..");
const validator = path.join(repositoryRoot, "scripts", "validate.mjs");

async function writeSkill(root, collection, name, skill, smoke) {
  const directory = path.join(root, collection, name);
  await mkdir(directory, { recursive: true });
  await mkdir(path.join(root, "tests", "smoke"), { recursive: true });
  await writeFile(path.join(directory, "SKILL.md"), skill);
  await writeFile(path.join(root, "tests", "smoke", `${name}.yaml`), smoke);
}

function runValidator(root) {
  return spawnSync(process.execPath, [validator], {
    cwd: root,
    encoding: "utf8",
  });
}

test("maintainer can validate a portable stable skill", async () => {
  const root = await mkdtemp(path.join(tmpdir(), "agent-skills-validator-"));
  await writeSkill(
    root,
    "skills",
    "research-notes",
    `---
name: research-notes
description: Organize research notes when an agent must synthesize multiple sources.
license: Apache-2.0
metadata:
  tags: "research,documentation"
---

# Research Notes

Use the supplied sources to organize the research notes.
`,
    `skill: research-notes
cases:
  - kind: trigger
    prompt: Organize these five sources into research notes.
    expected: The skill activates and organizes the supplied sources.
  - kind: non-trigger
    prompt: What time is it?
    expected: The skill remains inactive.
`,
  );

  const result = runValidator(root);

  assert.equal(result.status, 0, result.stderr);
  assert.match(result.stdout, /Validated 1 skill/);
});

test("maintainer sees every portable contract violation", async () => {
  const root = await mkdtemp(path.join(tmpdir(), "agent-skills-validator-"));
  await writeSkill(
    root,
    "skills",
    "research-notes",
    `---
name: different-name
description: ""
license: MIT
metadata:
  tags:
    - research
client-only: true
---

# Research Notes
`,
    `skill: research-notes
cases:
  - kind: trigger
    prompt: Organize these notes.
    expected: The skill activates.
  - kind: non-trigger
    prompt: What time is it?
    expected: The skill remains inactive.
`,
  );

  const result = runValidator(root);

  assert.equal(result.status, 1);
  assert.match(result.stderr, /name must match directory research-notes/);
  assert.match(result.stderr, /description must be a non-empty string/);
  assert.match(result.stderr, /license must be Apache-2.0/);
  assert.match(result.stderr, /metadata\.tags must be a string/);
  assert.match(result.stderr, /unsupported stable frontmatter field client-only/);
});

test("description activation context can use clear phrasing without literal when", async () => {
  const root = await mkdtemp(path.join(tmpdir(), "agent-skills-validator-"));
  await writeSkill(
    root,
    "incubator",
    "research-notes",
    `---
name: research-notes
description: Convert CSV to JSON for data-format transformation requests.
license: Apache-2.0
metadata:
  tags: "research"
---

# Research Notes
`,
    `skill: research-notes
cases:
  - kind: trigger
    prompt: Organize these research notes.
    expected: The skill activates.
  - kind: non-trigger
    prompt: What time is it?
    expected: The skill remains inactive.
`,
  );

  const result = runValidator(root);

  assert.equal(result.status, 0, result.stderr);
});

test("maintainer cannot publish duplicate names across maturity collections", async () => {
  const root = await mkdtemp(path.join(tmpdir(), "agent-skills-validator-"));
  const skill = `---
name: research-notes
description: Organize research notes when an agent must synthesize multiple sources.
license: Apache-2.0
metadata:
  tags: "research"
---

# Research Notes
`;
  const smoke = `skill: research-notes
cases:
  - kind: trigger
    prompt: Organize these research notes.
    expected: The skill activates.
  - kind: non-trigger
    prompt: What time is it?
    expected: The skill remains inactive.
`;
  await writeSkill(root, "skills", "research-notes", skill, smoke);
  await writeSkill(root, "incubator", "research-notes", skill, smoke);

  const result = runValidator(root);

  assert.equal(result.status, 1);
  assert.match(
    result.stderr,
    /duplicate skill name research-notes in skills\/research-notes and incubator\/research-notes/,
  );
});

test("stable skill requires complete trigger and non-trigger smoke cases", async () => {
  const root = await mkdtemp(path.join(tmpdir(), "agent-skills-validator-"));
  await writeSkill(
    root,
    "skills",
    "research-notes",
    `---
name: research-notes
description: Organize research notes when an agent must synthesize multiple sources.
license: Apache-2.0
metadata:
  tags: "research"
---

# Research Notes
`,
    `skill: wrong-name
cases:
  - kind: trigger
    prompt: "TODO: Add a prompt."
    expected: The skill activates.
`,
  );

  const result = runValidator(root);

  assert.equal(result.status, 1);
  assert.match(result.stderr, /smoke skill must equal research-notes/);
  assert.match(result.stderr, /smoke cases must include a non-trigger case/);
  assert.match(result.stderr, /smoke cases must not contain TODO placeholders/);
});

test("skill references must stay inside the bundle and resolve", async () => {
  const root = await mkdtemp(path.join(tmpdir(), "agent-skills-validator-"));
  await writeSkill(
    root,
    "incubator",
    "research-notes",
    `---
name: research-notes
description: Organize research notes when an agent must synthesize multiple sources.
license: Apache-2.0
metadata:
  tags: "research"
---

# Research Notes

Read [outside](../shared.md) and [missing](references/missing.md).
`,
    `skill: research-notes
cases:
  - kind: trigger
    prompt: "TODO: Add a prompt."
    expected: "TODO: Add expected behavior."
  - kind: non-trigger
    prompt: "TODO: Add a prompt."
    expected: "TODO: Add expected behavior."
`,
  );

  const result = runValidator(root);

  assert.equal(result.status, 1);
  assert.match(result.stderr, /reference escapes the skill bundle: \.\.\/shared\.md/);
  assert.match(result.stderr, /reference does not exist: references\/missing\.md/);
});

test("skill references may include an anchor in an existing bundled file", async () => {
  const root = await mkdtemp(path.join(tmpdir(), "agent-skills-validator-"));
  await writeSkill(
    root,
    "incubator",
    "research-notes",
    `---
name: research-notes
description: Organize research notes when an agent must synthesize multiple sources.
license: Apache-2.0
metadata:
  tags: "research"
---

# Research Notes

Read [the workflow](references/guide.md#workflow).
`,
    `skill: research-notes
cases:
  - kind: trigger
    prompt: "TODO: Add a prompt."
    expected: "TODO: Add expected behavior."
  - kind: non-trigger
    prompt: "TODO: Add a prompt."
    expected: "TODO: Add expected behavior."
`,
  );
  const references = path.join(
    root,
    "incubator",
    "research-notes",
    "references",
  );
  await mkdir(references);
  await writeFile(path.join(references, "guide.md"), "# Workflow\n");

  const result = runValidator(root);

  assert.equal(result.status, 0, result.stderr);
});

test("supporting documents cannot create deep reference chains", async () => {
  const root = await mkdtemp(path.join(tmpdir(), "agent-skills-validator-"));
  await writeSkill(
    root,
    "incubator",
    "research-notes",
    `---
name: research-notes
description: Organize research notes when an agent must synthesize multiple sources.
license: Apache-2.0
metadata:
  tags: "research"
---

# Research Notes

Read [the workflow](references/workflow.md).
`,
    `skill: research-notes
cases:
  - kind: trigger
    prompt: "TODO: Add a prompt."
    expected: "TODO: Add expected behavior."
  - kind: non-trigger
    prompt: "TODO: Add a prompt."
    expected: "TODO: Add expected behavior."
`,
  );
  const references = path.join(
    root,
    "incubator",
    "research-notes",
    "references",
  );
  await mkdir(references);
  await writeFile(
    path.join(references, "workflow.md"),
    "Continue to [details](details.md).\n",
  );
  await writeFile(path.join(references, "details.md"), "# Details\n");

  const result = runValidator(root);

  assert.equal(result.status, 1);
  assert.match(result.stderr, /Markdown references must stay one hop from SKILL\.md/);
});

test("unsafe or nonportable bundled files are rejected with review signals", async () => {
  const root = await mkdtemp(path.join(tmpdir(), "agent-skills-validator-"));
  await writeSkill(
    root,
    "incubator",
    "research-notes",
    `---
name: research-notes
description: Organize research notes when an agent must synthesize multiple sources.
license: Apache-2.0
metadata:
  tags: "research"
---

# Research Notes
`,
    `skill: research-notes
cases:
  - kind: trigger
    prompt: "TODO: Add a prompt."
    expected: "TODO: Add expected behavior."
  - kind: non-trigger
    prompt: "TODO: Add a prompt."
    expected: "TODO: Add expected behavior."
`,
  );
  const skillRoot = path.join(root, "incubator", "research-notes");
  await mkdir(path.join(skillRoot, "scripts"));
  await mkdir(path.join(skillRoot, "references"));
  await mkdir(path.join(skillRoot, "assets"));
  await writeFile(
    path.join(skillRoot, "scripts", "unsafe.mjs"),
    `import leftPad from "left-pad";
import { spawn } from "node:child_process";
import { createRequire } from "node:module";
import https from "node:https";
import dns from "node:dns/promises";
import "../../outside.mjs";
import ${JSON.stringify(path.join(skillRoot, "scripts", "local.mjs"))};
fetch("https://example.com");
createRequire(import.meta.url)("left-pad");
const packageName = "left-pad";
import(packageName);
`,
  );
  await writeFile(path.join(skillRoot, "scripts", "local.mjs"), "export {};\n");
  await writeFile(path.join(skillRoot, "assets", "tool.exe"), "MZ");
  await writeFile(
    path.join(skillRoot, "assets", "secret.pem"),
    "-----BEGIN PRIVATE KEY-----\nsecret\n-----END PRIVATE KEY-----\n",
  );
  await writeFile(
    path.join(skillRoot, "references", "secret.txt"),
    "-----BEGIN PRIVATE KEY-----\nsecret\n-----END PRIVATE KEY-----\nghp_abcdefghijklmnopqrstuvwxyzABCDEFGHIJ\n",
  );
  if (process.platform !== "win32") {
    await symlink(
      path.join(root, "outside"),
      path.join(skillRoot, "references", "linked"),
    );
  }

  const result = runValidator(root);

  assert.equal(result.status, 1);
  assert.match(result.stderr, /runtime package import left-pad is forbidden/);
  assert.match(result.stderr, /external process module node:child_process is forbidden/);
  assert.match(result.stderr, /dependency-loading module node:module is forbidden/);
  assert.match(result.stderr, /dynamic imports must use one literal specifier/);
  assert.match(result.stderr, /network module node:https requires manual review/);
  assert.match(result.stderr, /network module node:dns\/promises requires manual review/);
  assert.match(result.stderr, /global fetch requires manual network review/);
  assert.match(result.stderr, /script import escapes the skill bundle: \.\.\/\.\.\/outside\.mjs/);
  assert.match(result.stderr, /absolute script import .* is forbidden/);
  assert.match(result.stderr, /opaque executable file type \.exe is forbidden/);
  assert.match(result.stderr, /possible private key/);
  assert.match(result.stderr, /possible GitHub token/);
  if (process.platform !== "win32") {
    assert.match(result.stderr, /symlinks are forbidden/);
  }
});

test("publisher contract rejects ambiguous metadata and opaque resources", async () => {
  const root = await mkdtemp(path.join(tmpdir(), "agent-skills-validator-"));
  const longBody = Array.from({ length: 495 }, () => "instruction").join("\n");
  await writeSkill(
    root,
    "incubator",
    "research-notes",
    `---
name: research-notes
description: Organize research notes when an agent must synthesize multiple sources.
license: Apache-2.0
metadata:
  tags: "Research, research, bad tag!"
---

# Research Notes

${longBody}
`,
    `skill: research-notes
cases:
  - kind: trigger
    prompt: "TODO: Add a prompt."
    expected: "TODO: Add expected behavior."
  - kind: non-trigger
    prompt: "TODO: Add a prompt."
    expected: "TODO: Add expected behavior."
`,
  );
  const skillRoot = path.join(root, "incubator", "research-notes");
  await mkdir(path.join(skillRoot, "scripts"));
  await mkdir(path.join(skillRoot, "assets"));
  await writeFile(
    path.join(skillRoot, "scripts", "main.mjs"),
    `import "./missing.mjs";\n`,
  );
  await writeFile(path.join(skillRoot, "assets", "bundle.zip"), "opaque");
  await writeFile(path.join(skillRoot, "assets", "third-party-logo.png"), "media");

  const result = runValidator(root);

  assert.equal(result.status, 1);
  assert.match(result.stderr, /metadata\.tags must contain unique lowercase kebab-case tags/);
  assert.match(result.stderr, /SKILL\.md must not exceed 500 lines/);
  assert.match(result.stderr, /script import does not exist: \.\/missing\.mjs/);
  assert.match(result.stderr, /opaque bundled file type \.zip is forbidden/);
  assert.match(result.stderr, /assets require THIRD_PARTY_NOTICES\.md/);
});

test("asset notices require per-file provenance and compatible licenses", async () => {
  const root = await mkdtemp(path.join(tmpdir(), "agent-skills-validator-"));
  await writeSkill(
    root,
    "incubator",
    "research-notes",
    `---
name: research-notes
description: Organize research notes when an agent must synthesize multiple sources.
license: Apache-2.0
metadata:
  tags: "research"
---

# Research Notes
`,
    `skill: research-notes
cases:
  - kind: trigger
    prompt: "TODO: Add a prompt."
    expected: "TODO: Add expected behavior."
  - kind: non-trigger
    prompt: "TODO: Add a prompt."
    expected: "TODO: Add expected behavior."
`,
  );
  const skillRoot = path.join(root, "incubator", "research-notes");
  await mkdir(path.join(skillRoot, "assets"));
  await writeFile(path.join(skillRoot, "assets", "logo.png"), "media");
  await writeFile(
    path.join(skillRoot, "THIRD_PARTY_NOTICES.md"),
    "This file intentionally omits structured provenance.\n",
  );

  const result = runValidator(root);

  assert.equal(result.status, 1);
  assert.match(result.stderr, /missing a notice section for assets\/logo\.png/);
});

test("hidden assets cannot bypass provenance validation", async () => {
  const root = await mkdtemp(path.join(tmpdir(), "agent-skills-validator-"));
  await writeSkill(
    root,
    "incubator",
    "research-notes",
    `---
name: research-notes
description: Organize research notes when an agent must synthesize multiple sources.
license: Apache-2.0
metadata:
  tags: "research"
---

# Research Notes
`,
    `skill: research-notes
cases:
  - kind: trigger
    prompt: "TODO: Add a prompt."
    expected: "TODO: Add expected behavior."
  - kind: non-trigger
    prompt: "TODO: Add a prompt."
    expected: "TODO: Add expected behavior."
`,
  );
  const skillRoot = path.join(root, "incubator", "research-notes");
  await mkdir(path.join(skillRoot, "assets"));
  await writeFile(path.join(skillRoot, "assets", ".hidden-logo.png"), "media");

  const result = runValidator(root);

  assert.equal(result.status, 1);
  assert.match(result.stderr, /assets require THIRD_PARTY_NOTICES\.md/);
});

test("asset notices accept documented compatible provenance", async () => {
  const root = await mkdtemp(path.join(tmpdir(), "agent-skills-validator-"));
  await writeSkill(
    root,
    "incubator",
    "research-notes",
    `---
name: research-notes
description: Organize research notes when an agent must synthesize multiple sources.
license: Apache-2.0
metadata:
  tags: "research"
---

# Research Notes
`,
    `skill: research-notes
cases:
  - kind: trigger
    prompt: "TODO: Add a prompt."
    expected: "TODO: Add expected behavior."
  - kind: non-trigger
    prompt: "TODO: Add a prompt."
    expected: "TODO: Add expected behavior."
`,
  );
  const skillRoot = path.join(root, "incubator", "research-notes");
  await mkdir(path.join(skillRoot, "assets"));
  await writeFile(path.join(skillRoot, "assets", "logo.png"), "media");
  await writeFile(
    path.join(skillRoot, "THIRD_PARTY_NOTICES.md"),
    `# Asset notices

## assets/logo.png

- Source: Created for this project.
- Copyright: The agent-skills contributors.
- License: Apache-2.0
`,
  );

  const result = runValidator(root);

  assert.equal(result.status, 0, result.stderr);
});

test("secret detection scans auditable files with unknown extensions", async () => {
  const root = await mkdtemp(path.join(tmpdir(), "agent-skills-validator-"));
  await writeSkill(
    root,
    "incubator",
    "research-notes",
    `---
name: research-notes
description: Organize research notes when an agent must synthesize multiple sources.
license: Apache-2.0
metadata:
  tags: "research"
---

# Research Notes
`,
    `skill: research-notes
cases:
  - kind: trigger
    prompt: "TODO: Add a prompt."
    expected: "TODO: Add expected behavior."
  - kind: non-trigger
    prompt: "TODO: Add a prompt."
    expected: "TODO: Add expected behavior."
`,
  );
  await writeFile(
    path.join(root, "incubator", "research-notes", "credentials.toml"),
    "token = 'github_pat_1234567890_abcdefghijklmnopqrstuvwxyz'\n",
  );

  const result = runValidator(root);

  assert.equal(result.status, 1);
  assert.match(result.stderr, /credentials\.toml: possible GitHub token/);
});

test(
  "top-level skill symlinks are rejected",
  { skip: process.platform === "win32" },
  async () => {
    const root = await mkdtemp(path.join(tmpdir(), "agent-skills-validator-"));
    const outside = path.join(root, "outside-skill");
    await mkdir(outside);
    await mkdir(path.join(root, "skills"));
    await symlink(outside, path.join(root, "skills", "linked-skill"));

    const result = runValidator(root);

    assert.equal(result.status, 1);
    assert.match(result.stderr, /skills\/linked-skill: symlinks are forbidden/);
  },
);

test("supporting Markdown references cannot escape the skill", async () => {
  const root = await mkdtemp(path.join(tmpdir(), "agent-skills-validator-"));
  await writeSkill(
    root,
    "incubator",
    "research-notes",
    `---
name: research-notes
description: Organize research notes when an agent must synthesize multiple sources.
license: Apache-2.0
metadata:
  tags: "research"
---

# Research Notes

Read [the guide](references/guide.md).
`,
    `skill: research-notes
cases:
  - kind: trigger
    prompt: "TODO: Add a prompt."
    expected: "TODO: Add expected behavior."
  - kind: non-trigger
    prompt: "TODO: Add a prompt."
    expected: "TODO: Add expected behavior."
`,
  );
  const references = path.join(
    root,
    "incubator",
    "research-notes",
    "references",
  );
  await mkdir(references);
  await writeFile(
    path.join(references, "guide.md"),
    "Read [outside](../../outside.md).\n",
  );

  const result = runValidator(root);

  assert.equal(result.status, 1);
  assert.match(result.stderr, /reference escapes the skill bundle: \.\.\/\.\.\/outside\.md/);
});
