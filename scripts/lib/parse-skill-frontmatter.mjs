import { parse } from "yaml";

const frontmatterPattern = /^---\r?\n([\s\S]*?)\r?\n---(?:\r?\n|$)/;

export function parseSkillFrontmatter(source, location) {
  const match = source.match(frontmatterPattern);
  if (match?.[1] === undefined) {
    throw new Error(`${location}: SKILL.md must begin with YAML frontmatter.`);
  }

  try {
    return parse(match[1]);
  } catch (error) {
    throw new Error(`${location}: invalid YAML frontmatter (${error.message}).`);
  }
}
