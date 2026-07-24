#!/usr/bin/env node

import { readFile } from "node:fs/promises";
import path from "node:path";
import { parse } from "parse5";

const args = process.argv.slice(2);
const rootIndex = args.indexOf("--root");
const rootArgument = rootIndex >= 0 ? args[rootIndex + 1] : undefined;
if (rootIndex >= 0 && rootArgument === undefined) {
  throw new Error("--root requires a directory argument.");
}
const root = path.resolve(rootArgument ?? process.cwd());
const skills = [
  "make-me-realize", "three-code-paths", "interface-directions", "change-blueprint",
  "build-with-notes", "do-i-understand-this", "feel-the-flow", "feature-xray",
  "concept-lab", "what-just-happened", "draw-the-flow", "draw-it-in-svg",
  "deepen-the-codebase", "find-the-cause", "learning-workbench",
];
const htmlSkills = skills.filter((name) => name !== "make-me-realize");
const errors = [];

function walk(node, visit) {
  visit(node);
  for (const child of node.childNodes ?? []) walk(child, visit);
  if (node.content) walk(node.content, visit);
}

function actaTokens(source) {
  const tokens = new Map();
  for (const match of source.matchAll(/(--acta-[a-z0-9-]+)\s*:\s*([^;}]+)/g)) {
    tokens.set(match[1], match[2].trim());
  }
  return tokens;
}

function rgb(hex) {
  const normalized = hex.trim().replace(/^#/, "");
  if (!/^(?:[a-f0-9]{3}|[a-f0-9]{6})$/i.test(normalized)) return null;
  const expanded = normalized.length === 3
    ? [...normalized].map((character) => character + character).join("")
    : normalized;
  return [0, 2, 4].map((offset) => Number.parseInt(expanded.slice(offset, offset + 2), 16));
}

function relativeLuminance(hex) {
  const channels = rgb(hex);
  if (channels === null) return null;
  const linear = channels.map((channel) => {
    const value = channel / 255;
    return value <= 0.04045 ? value / 12.92 : ((value + 0.055) / 1.055) ** 2.4;
  });
  const [red = 0, green = 0, blue = 0] = linear;
  return 0.2126 * red + 0.7152 * green + 0.0722 * blue;
}

function contrastRatio(foreground, background) {
  const foregroundLuminance = relativeLuminance(foreground);
  const backgroundLuminance = relativeLuminance(background);
  if (foregroundLuminance === null || backgroundLuminance === null) return null;
  const lighter = Math.max(foregroundLuminance, backgroundLuminance);
  const darker = Math.min(foregroundLuminance, backgroundLuminance);
  return (lighter + 0.05) / (darker + 0.05);
}

function validateVisualContracts(source, location) {
  const tokens = actaTokens(source);
  /** @type {Array<[string, string, number]>} */
  const pairs = [
    ["--acta-ink", "--acta-paper", 4.5],
    ["--acta-ink-muted", "--acta-paper", 4.5],
    ["--acta-ink-inverse", "--acta-inverse", 4.5],
    ["--acta-ink-inverse-muted", "--acta-inverse", 4.5],
    ["--acta-rule-strong", "--acta-paper", 3],
    ["--acta-action", "--acta-paper", 4.5],
    ["--acta-positive", "--acta-paper", 4.5],
    ["--acta-warning", "--acta-paper", 4.5],
    ["--acta-danger", "--acta-paper", 4.5],
    ["--acta-action", "--acta-action-tint", 4.5],
    ["--acta-positive", "--acta-positive-tint", 4.5],
    ["--acta-warning", "--acta-warning-tint", 4.5],
    ["--acta-danger", "--acta-danger-tint", 4.5],
    ["--acta-code-add", "--acta-inverse", 4.5],
    ["--acta-code-del", "--acta-inverse", 4.5],
    ["--acta-code-dim", "--acta-inverse", 4.5],
  ];
  for (const [foregroundName, backgroundName, minimum] of pairs) {
    const foreground = tokens.get(foregroundName);
    const background = tokens.get(backgroundName);
    const ratio = foreground && background ? contrastRatio(foreground, background) : null;
    if (ratio === null || ratio < minimum) {
      const rendered = ratio === null ? "unavailable" : ratio.toFixed(2) + ":1";
      errors.push(`${location}: contrast ${foregroundName} on ${backgroundName} is ${rendered}; expected at least ${minimum}:1.`);
    }
  }
  if (tokens.get("--acta-radius") !== "2px") {
    errors.push(`${location}: Acta radius token must remain 2px.`);
  }
  if (tokens.get("--acta-quick") !== "90ms linear") {
    errors.push(`${location}: Acta motion token must remain 90ms linear.`);
  }
  for (const match of source.matchAll(/border-radius\s*:\s*([^;}]+)/gi)) {
    const value = match[1].trim();
    if (!["var(--acta-radius)", "50%"].includes(value)) {
      errors.push(`${location}: unsupported radius declaration ${value}.`);
    }
  }
  if (!source.includes("@media (max-width:959px)")) {
    errors.push(`${location}: missing 960px responsive breakpoint contract.`);
  }
  if (!source.includes("@media (max-width:719px)")) {
    errors.push(`${location}: missing 720px responsive breakpoint contract.`);
  }
  if (!source.includes(".codewrap,.tablewrap,.flowwrap{overflow-x:auto}")) {
    errors.push(`${location}: missing 320px reflow wrapper contract.`);
  }
  if (!/prefers-reduced-motion[\s\S]*transition:none!important;animation:none!important;scroll-behavior:auto!important/.test(source)) {
    errors.push(`${location}: incomplete reduced-motion override.`);
  }
  for (const match of source.matchAll(/transition\s*:\s*([^;}]+)/gi)) {
    const value = match[1].replaceAll(" ", "");
    const allowedTransition = /^(?:background|color|border(?:-color)?)(?:[^,]*var\(--acta-quick\))(?:,(?:background|color|border(?:-color)?)[^,]*var\(--acta-quick\))*$/.test(value);
    if (value !== "none!important" && !allowedTransition) {
      errors.push(`${location}: motion may transition only color or border properties through --acta-quick.`);
    }
  }
}

for (const name of htmlSkills) {
  const location = `skills/${name}/references/acta-scaffold.html`;
  const source = await readFile(path.join(root, location), "utf8");
  const document = parse(source, { sourceCodeLocationInfo: true });
  validateVisualContracts(source, location);
  const ids = new Set();
  const references = [];
  let doctype = false;
  let noscript = false;
  let polite = false;
  walk(document, (node) => {
    if (node.nodeName === "#documentType") doctype = true;
    if (node.tagName === "noscript") noscript = true;
    for (const attr of node.attrs ?? []) {
      if (/^on/i.test(attr.name)) errors.push(`${location}: inline event handler ${attr.name} is forbidden.`);
      if (attr.name === "id") {
        if (ids.has(attr.value)) errors.push(`${location}: duplicate id ${attr.value}.`);
        ids.add(attr.value);
      }
      if (["href", "src"].includes(attr.name) && /^https?:/i.test(attr.value)) errors.push(`${location}: network resource ${attr.value} is forbidden.`);
      if (attr.name === "aria-live" && attr.value === "polite") polite = true;
      if (["for", "aria-labelledby", "aria-describedby"].includes(attr.name)) references.push(...attr.value.split(/\s+/));
    }
  });
  for (const target of references) if (target && !ids.has(target)) errors.push(`${location}: reference to missing id ${target}.`);
  if (!doctype) errors.push(`${location}: missing HTML doctype.`);
  if (!noscript) errors.push(`${location}: missing no-script fallback.`);
  if (!polite) errors.push(`${location}: missing polite status region.`);
  if (!source.includes('document.execCommand("copy")')) errors.push(`${location}: missing clipboard fallback.`);
  const forbiddenPatterns = [
    { expression: /\b(?:innerHTML|outerHTML|insertAdjacentHTML|document\.write|eval)\b/, label: "unsafe DOM or evaluation sink" },
    { expression: /\b(?:localStorage|sessionStorage)\b/, label: "browser storage" },
    { expression: /@import\b|url\(\s*["']?https?:/i, label: "network CSS" },
    { expression: /box-shadow\s*:/i, label: "shadow declaration" },
  ];
  for (const { expression, label } of forbiddenPatterns) {
    if (expression.test(source)) errors.push(`${location}: contains forbidden ${label}.`);
  }
  for (const required of [
    "--acta-paper", "--acta-ink", "--acta-action", "--acta-radius", "--acta-quick",
    "class=\"acta-shell\"", "class=\"acta-prov\"", "class=\"acta-context\"",
    "class=\"acta-summary\"", "class=\"acta-export\"", "@media print",
    "prefers-reduced-motion", ".codewrap,.tablewrap,.flowwrap",
  ]) if (!source.includes(required)) errors.push(`${location}: missing required Acta contract ${required}.`);
}

const protocolCopies = [];
for (const name of skills) {
  const location = `skills/${name}/references/acta-protocol.md`;
  const source = await readFile(path.join(root, location), "utf8");
  protocolCopies.push(source);
  if (!/^<!-- acta-materialized: v0\.1\.0 protocol sha256=[a-f0-9]{64}; do not edit by hand -->/.test(source)) errors.push(`${location}: invalid materialization marker.`);
}
if (new Set(protocolCopies).size !== 1) errors.push("Acta protocol copies differ across installed skills.");

if (errors.length) {
  console.error(errors.map((error) => `ERROR: ${error}`).join("\n"));
  process.exit(1);
}
console.log("Validated 14 Acta HTML recipes and 15 protocol copies.");
