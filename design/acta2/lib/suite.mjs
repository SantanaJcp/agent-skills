/* Acta v2 suite manifest — the single source of truth for which skills ship
 * which artifacts. The materializer, the static validator, and the test
 * suite all iterate this list; nothing else may hardcode skill rosters.
 *
 * Fields:
 *   name        skill directory under incubator/
 *   kind        export-core state-machine kind (null only for text-only)
 *   instruments variant ids; "default" maps to unsuffixed filenames
 *               (scenario.json / instrument.html), any other id maps to
 *               scenario-<id>.json / instrument-<id>.html
 *   record      "v1" (Acta 0.1 record css — approved pilots), "v2"
 *               (design/acta2/record.css + records/<name>.css), or null
 *   candidateVariant which variant's scenario feeds the candidate fixture
 *   workingFixture   fixtures/<name>/working.json feeds the candidate when
 *                    the skill has no accepted state (instrument-only)
 */

export const SUITE = [
  { name: "three-code-paths", kind: "decision", instruments: ["default"], record: "v1", candidateVariant: "default" },
  { name: "build-with-notes", kind: "stop-gate", instruments: ["default"], record: "v1", candidateVariant: "default" },
  { name: "concept-lab", kind: "model", instruments: ["default"], record: "v1", candidateVariant: "default" },
  /* Cohort A — core development cycle */
  { name: "interface-directions", kind: "decision", instruments: ["default"], record: "v2", candidateVariant: "default" },
  { name: "change-blueprint", kind: "decision", instruments: ["spec", "plan"], record: "v2", candidateVariant: "plan" },
  { name: "do-i-understand-this", kind: "quiz", instruments: ["default"], record: "v2", candidateVariant: "default" },
  /* Cohort B — explanation and visual modeling */
  { name: "feature-xray", kind: "dossier", instruments: [], record: "v2" },
  { name: "what-just-happened", kind: "dossier", instruments: [], record: "v2" },
  { name: "draw-the-flow", kind: "decision", instruments: ["default"], record: "v2", candidateVariant: "default" },
  { name: "draw-it-in-svg", kind: "checklist", instruments: ["default"], record: "v2", candidateVariant: "default" },
  /* Cohort C — exploration, architecture, and learning */
  { name: "feel-the-flow", kind: "prototype", instruments: ["default"], record: null, candidateVariant: "default", workingFixture: true },
  { name: "deepen-the-codebase", kind: "decision", instruments: ["default"], record: "v2", candidateVariant: "default" },
  { name: "find-the-cause", kind: "checklist", instruments: ["default"], record: "v2", candidateVariant: "default" },
  { name: "learning-workbench", kind: "quiz", instruments: ["default"], record: "v2", candidateVariant: "default" },
];

/** Skills that deliberately produce no HTML artifact. */
export const TEXT_ONLY = ["make-me-realize"];

/** @param {string} variant */
export function variantSuffix(variant) {
  return variant === "default" ? "" : `-${variant}`;
}

/** The approved three-skill pilot cohort (byte-stability guarantees). */
export const PILOTS = ["three-code-paths", "build-with-notes", "concept-lab"];
