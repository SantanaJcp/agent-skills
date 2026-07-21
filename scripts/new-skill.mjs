#!/usr/bin/env node

import { access, mkdir, readFile, writeFile } from "node:fs/promises";
import path from "node:path";

const name = process.argv[2];

if (!name) {
  console.error("Usage: npm run new:skill -- <skill-name>");
  process.exit(1);
}

const validName =
  name.length <= 64 && /^[a-z0-9]+(?:-[a-z0-9]+)*$/.test(name);

if (!validName) {
  console.error(
    "Skill names must be 1-64 lowercase letters, numbers, and single hyphens, with no leading or trailing hyphen.",
  );
  process.exit(1);
}

const title = name
  .split("-")
  .map((word) => word.charAt(0).toUpperCase() + word.slice(1))
  .join(" ");
const root = process.cwd();
const templatePath = path.resolve(
  import.meta.dirname,
  "..",
  "templates",
  "skill",
  "SKILL.md.tmpl",
);
const skillDirectory = path.join(root, "incubator", name);
const smokeDirectory = path.join(root, "tests", "smoke");
const conflicts = [
  path.join(root, "skills", name),
  skillDirectory,
  path.join(smokeDirectory, `${name}.yaml`),
];

for (const conflict of conflicts) {
  try {
    await access(conflict);
    console.error(`Skill ${name} already exists.`);
    process.exit(1);
  } catch (error) {
    if (error.code !== "ENOENT") {
      throw error;
    }
  }
}

const template = await readFile(templatePath, "utf8");
const skill = template
  .replaceAll("{{name}}", name)
  .replaceAll("{{title}}", title);
const smoke = `skill: ${name}
cases:
  - kind: trigger
    prompt: "TODO: Add a prompt that should activate ${name}."
    expected: "TODO: Describe the expected skill-assisted behavior."
  - kind: non-trigger
    prompt: "TODO: Add a related prompt that should not activate ${name}."
    expected: "TODO: Describe why the skill should remain inactive."
`;

await mkdir(skillDirectory, { recursive: true });
await mkdir(smokeDirectory, { recursive: true });
await writeFile(path.join(skillDirectory, "SKILL.md"), skill, { flag: "wx" });
await writeFile(path.join(smokeDirectory, `${name}.yaml`), smoke, { flag: "wx" });

console.log(`Created incubator skill ${name}.`);
