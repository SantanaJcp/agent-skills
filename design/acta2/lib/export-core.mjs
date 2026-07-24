/*
 * Acta v2 — pure state/export core.
 *
 * One source of truth for: status derivation, per-kind derived consequences,
 * and candidate export building (Markdown + JSON). This file runs in two
 * places from the same bytes:
 *   - imported by Node tests and the materializer (ESM exports below);
 *   - inlined into every instrument by scripts/materialize-acta2.mjs, which
 *     strips the block between the ACTA2-ESM markers.
 *
 * Rules: no imports, no I/O, no randomness, no clock reads, no DOM access.
 * Everything here must be deterministic for identical inputs.
 */

const ACTA2_PROTOCOL = "0.2";

/* Identifiers coming from instrument data (param/toggle/option/gate-option
   ids) are untrusted: they become YAML frontmatter keys, DOM attribute
   values, and state-map keys. Only a conservative shape is accepted — this
   blocks newline/colon YAML injection, duplicate-key smuggling, and
   prototype-shaped keys ("__proto__" fails the leading-letter rule). */
const SAFE_ID = /^[a-zA-Z][a-zA-Z0-9_-]{0,40}$/;
const RESERVED_IDS = new Set(["__proto__", "prototype", "constructor"]);

function assertSafeIdList(ids, kindLabel) {
  const seen = new Set();
  for (const id of ids) {
    if (typeof id !== "string" || !SAFE_ID.test(id) || RESERVED_IDS.has(id)) {
      throw new Error(
        `Unsafe ${kindLabel} identifier ${JSON.stringify(id)}: identifiers must match ${SAFE_ID}.`,
      );
    }
    if (seen.has(id)) {
      throw new Error(`Duplicate ${kindLabel} identifier ${JSON.stringify(id)}.`);
    }
    seen.add(id);
  }
}

function assertSafeInstrumentData(data) {
  switch (data.kind) {
    case "decision":
      assertSafeIdList([data.decisionId], "decision");
      assertSafeIdList((data.options ?? []).map((option) => option.id), "option");
      if (data.requiredPriorDecisions !== undefined) {
        if (!Array.isArray(data.requiredPriorDecisions)) {
          throw new Error("requiredPriorDecisions must be an array when present.");
        }
        assertSafeIdList(
          data.requiredPriorDecisions.map((decision) => decision.id),
          "required prior decision",
        );
        for (const prior of data.requiredPriorDecisions) {
          if (prior.id === data.decisionId) {
            throw new Error(`Required prior decision ${JSON.stringify(prior.id)} cannot be the current decision.`);
          }
          if (!Array.isArray(prior.allowedSelections) || prior.allowedSelections.length === 0) {
            throw new Error(
              `Required prior decision ${JSON.stringify(prior.id)} must declare at least one allowed selection.`,
            );
          }
          assertSafeIdList(prior.allowedSelections, `required prior decision ${prior.id} selection`);
          if (typeof prior.artifactPath !== "string" || prior.artifactPath.trim() === "") {
            throw new Error(`Required prior decision ${JSON.stringify(prior.id)} must identify its artifact path.`);
          }
          if (typeof prior.acceptedRevision !== "string" || prior.acceptedRevision.trim() === "") {
            throw new Error(`Required prior decision ${JSON.stringify(prior.id)} must identify its accepted revision.`);
          }
        }
      }
      break;
    case "stop-gate":
      assertSafeIdList([data.gate?.id], "STOP gate");
      assertSafeIdList((data.gate?.options ?? []).map((option) => option.id), "gate option");
      assertSafeIdList((data.entries ?? []).map((entry) => entry.id), "entry");
      break;
    case "model":
      assertSafeIdList([data.decisionId], "decision");
      assertSafeIdList([data.acceptanceToken], "model acceptance");
      assertSafeIdList((data.params ?? []).map((param) => param.id), "parameter");
      assertSafeIdList((data.toggles ?? []).map((toggle) => toggle.id), "toggle");
      break;
    case "prototype":
      assertSafeIdList([data.decisionId], "decision");
      assertSafeIdList([data.acceptanceToken], "prototype acceptance");
      assertSafeIdList((data.params ?? []).map((param) => param.id), "parameter");
      assertSafeIdList((data.toggles ?? []).map((toggle) => toggle.id), "toggle");
      break;
    case "quiz":
      assertSafeIdList([data.decisionId], "decision");
      assertSafeIdList([data.acceptanceToken], "quiz acceptance");
      assertSafeIdList((data.questions ?? []).map((question) => question.id), "question");
      for (const question of data.questions ?? []) {
        assertSafeIdList((question.options ?? []).map((option) => option.id), `question ${question.id} option`);
        assertSafeIdList([question.answer], `question ${question.id} answer`);
      }
      break;
    case "checklist":
      assertSafeIdList([data.decisionId], "decision");
      assertSafeIdList([data.acceptanceToken], "checklist acceptance");
      assertSafeIdList((data.items ?? []).map((item) => item.id), "item");
      assertSafeIdList((data.verdicts ?? []).map((verdict) => verdict.id), "verdict");
      break;
    case "dossier":
      /* Record-only evidence dossiers: no instrument working state exists.
         The only decision is publishing the record after acceptance in chat. */
      assertSafeIdList([data.decisionId], "decision");
      assertSafeIdList([data.acceptanceToken], "dossier acceptance");
      break;
    default:
      throw new Error(`Unknown instrument kind: ${data.kind}`);
  }
  return data;
}

const INSTRUMENT_STATUSES = {
  "open-unselected": {
    code: "open-unselected",
    label: "Open — no path selected yet",
  },
  stopped: {
    code: "stopped",
    label: "STOP gate open — work is paused for your decision",
  },
  exploring: {
    code: "exploring",
    label: "Exploring — adjust the model, then record a conclusion",
  },
  "candidate-ready": {
    code: "candidate-ready",
    label: "Candidate ready — copy the export and confirm in chat",
  },
};

function initialWorking(data) {
  assertSafeInstrumentData(data);
  switch (data.kind) {
    case "decision":
      return { selected: null, rationale: "" };
    case "stop-gate":
      /* `filter` is deliberately EPHEMERAL view state: it changes what the
         human is looking at, never what they decided. It is excluded from
         candidate exports and canonical state by contract. */
      return { resolution: null, rationale: "", filter: "all" };
    case "model":
    case "prototype": {
      const params = Object.create(null);
      for (const param of data.params) params[param.id] = param.default;
      const toggles = Object.create(null);
      for (const toggle of data.toggles ?? []) toggles[toggle.id] = toggle.default;
      return { params, toggles, conclusion: "" };
    }
    case "quiz": {
      const answers = Object.create(null);
      for (const question of data.questions) answers[question.id] = null;
      return { answers, reflection: "" };
    }
    case "checklist": {
      const marks = Object.create(null);
      for (const item of data.items) marks[item.id] = null;
      return { marks, conclusion: "" };
    }
    case "dossier":
      throw new Error("dossier scenarios are record-only; no instrument working state exists.");
    default:
      throw new Error(`Unknown instrument kind: ${data.kind}`);
  }
}

function deriveStatus(data, working) {
  switch (data.kind) {
    case "decision":
      if (working.selected) return INSTRUMENT_STATUSES["candidate-ready"];
      /* Scenario-provided open label keeps gate/direction/flow decisions
         honest without changing the original scenario wording. */
      return data.openStatusLabel
        ? { code: "open-unselected", label: data.openStatusLabel }
        : INSTRUMENT_STATUSES["open-unselected"];
    case "stop-gate":
      return working.resolution
        ? INSTRUMENT_STATUSES["candidate-ready"]
        : INSTRUMENT_STATUSES.stopped;
    case "model":
      return working.conclusion.trim()
        ? INSTRUMENT_STATUSES["candidate-ready"]
        : INSTRUMENT_STATUSES.exploring;
    case "prototype":
      return working.conclusion.trim()
        ? INSTRUMENT_STATUSES["candidate-ready"]
        : { code: "exploring", label: "Exploring — feel the prototype, then record your conclusion" };
    case "quiz": {
      const unanswered = data.questions.filter((question) => !working.answers[question.id]);
      return unanswered.length === 0
        ? INSTRUMENT_STATUSES["candidate-ready"]
        : { code: "exploring", label: `In progress — ${unanswered.length} of ${data.questions.length} questions unanswered` };
    }
    case "checklist": {
      const unmarked = data.items.filter((item) => !working.marks[item.id]);
      const needsConclusion = Boolean(data.conclusionRequired) && !working.conclusion.trim();
      return unmarked.length === 0 && !needsConclusion
        ? INSTRUMENT_STATUSES["candidate-ready"]
        : { code: "exploring", label: unmarked.length > 0
            ? `In review — ${unmarked.length} of ${data.items.length} items still need a verdict`
            : "In review — record the conclusion to ready the export" };
    }
    default:
      throw new Error(`Unknown instrument kind: ${data.kind}`);
  }
}

function optionById(options, id) {
  for (const option of options ?? []) if (option.id === id) return option;
  return null;
}

/* ---------- model kind: deterministic exponential backoff ---------- */

function deriveBackoff(params, toggles) {
  const rows = [];
  let worstCaseTotalMs = 0;
  let expectedTotalMs = 0;
  for (let attempt = 0; attempt < params.retries; attempt += 1) {
    const raw = params.base * params.factor ** attempt;
    const delayMs = Math.min(params.cap, Math.round(raw));
    const rangeLowMs = toggles.fullJitter ? 0 : Math.round(delayMs / 2);
    const rangeMs = [rangeLowMs, delayMs];
    worstCaseTotalMs += delayMs;
    expectedTotalMs += Math.round((rangeLowMs + delayMs) / 2);
    rows.push({
      attempt: attempt + 1,
      delayMs,
      rangeMs,
      cappedAtLimit: raw > params.cap,
      cumulativeWorstMs: worstCaseTotalMs,
    });
  }
  return {
    rows,
    totals: {
      attempts: params.retries,
      worstCaseTotalMs,
      expectedTotalMs,
    },
  };
}

/* ---------- quiz kind: score and gaps derived from the answer key ---------- */

function deriveQuizScore(data, working) {
  let correct = 0;
  const gaps = [];
  for (const question of data.questions) {
    const chosen = working.answers[question.id] ?? null;
    if (chosen === question.answer) {
      correct += 1;
    } else {
      gaps.push({
        question: question.id,
        prompt: question.prompt,
        gap: question.gap,
        chosen,
        answer: question.answer,
      });
    }
  }
  return { correct, total: data.questions.length, gaps };
}

/* ---------- checklist kind: verdict tallies ---------- */

function deriveChecklistSummary(data, working) {
  const byVerdict = Object.create(null);
  for (const verdict of data.verdicts) byVerdict[verdict.id] = 0;
  let marked = 0;
  for (const item of data.items) {
    const mark = working.marks[item.id];
    if (mark) {
      marked += 1;
      if (mark in byVerdict) byVerdict[mark] += 1;
    }
  }
  return { marked, total: data.items.length, byVerdict };
}

/* Shared plot geometry for the backoff model. One implementation feeds the
   Node static renderer, the browser redraw, and tests — every attribute a
   renderer writes (positions, sizes, dash state, label text) comes from
   these items, so static and live SVG cannot diverge semantically.

   Composition (720×240 viewBox, near-1:1 pixels in the instrument column):
     y  50  worst-case total label (anchored to the end mark)
     y  88  attempt labels, above their bands (thinned when bands crowd)
     y  96–180  jitter bands sitting on the axis; deterministic-delay ticks
     y 180  cumulative axis with minor boundary ticks; expected-total mark
     y 198  origin "0"
     y 220  axis caption (left) and expected-total label (at its mark)
   Label-collision rules are deterministic and part of the spec: attempt
   labels are skipped when their centers come closer than attemptLabelMinGap,
   the inline "capped" tag is skipped on bands narrower than capTagMinWidth,
   and the expected-total label is clamped inside the drawable width. */
const PLOT = {
  viewW: 720,
  viewH: 240,
  marginL: 46,
  marginR: 26,
  axisY: 180,
  bandTop: 96,
  bandH: 84,
  attemptLabelY: 88,
  attemptLabelMinGap: 20,
  capTagMinWidth: 46,
  totalLabelY: 50,
  endmarkTop: 60,
  axisTickLen: 6,
  zeroLabelY: 198,
  footnoteY: 220,
  footnoteHalfWidth: 62,
};

function plotRound(value) {
  return Math.round(value * 100) / 100;
}

function backoffPlotSpec(params, toggles) {
  const backoff = deriveBackoff(params, toggles);
  const worst = backoff.totals.worstCaseTotalMs || 1;
  const drawW = PLOT.viewW - PLOT.marginL - PLOT.marginR;
  const scale = drawW / worst;
  const xOf = (t) => plotRound(PLOT.marginL + t * scale);
  const bandBottom = PLOT.bandTop + PLOT.bandH;
  const items = [];

  items.push({ el: "axis-line", x1: xOf(0), y1: PLOT.axisY, x2: xOf(worst), y2: PLOT.axisY });
  items.push({ el: "zero-label", x: xOf(0), y: PLOT.zeroLabelY, text: "0" });
  items.push({
    el: "caption",
    x: PLOT.marginL,
    y: PLOT.footnoteY,
    text: "cumulative worst-case wait (ms) →",
  });

  let prev = 0;
  /** @type {number | null} */
  let lastAttemptLabelX = null;
  for (const row of backoff.rows) {
    const x1 = xOf(prev + row.rangeMs[0]);
    const x2 = xOf(prev + row.rangeMs[1]);
    const width = plotRound(Math.max(x2 - x1, 2));
    const tickX = xOf(prev + row.delayMs);
    const center = plotRound((x1 + x2) / 2);
    items.push({ el: "axis-tick", x: xOf(prev), y1: PLOT.axisY, y2: PLOT.axisY + PLOT.axisTickLen });
    items.push({ el: "band", x: x1, y: PLOT.bandTop, width, height: PLOT.bandH, capped: row.cappedAtLimit });
    items.push({ el: "tick", x: tickX, y1: PLOT.bandTop - 6, y2: bandBottom + 6 });
    if (row.cappedAtLimit && width >= PLOT.capTagMinWidth) {
      items.push({ el: "cap-label", x: center, y: PLOT.bandTop + PLOT.bandH / 2 + 3.5, text: "capped" });
    }
    if (lastAttemptLabelX === null || center - lastAttemptLabelX >= PLOT.attemptLabelMinGap) {
      items.push({ el: "attempt-label", x: center, y: PLOT.attemptLabelY, text: `#${row.attempt}` });
      lastAttemptLabelX = center;
    }
    prev = row.cumulativeWorstMs;
  }

  const expectedX = xOf(backoff.totals.expectedTotalMs);
  const expectedLabelX = plotRound(
    Math.min(
      Math.max(expectedX, PLOT.marginL + PLOT.footnoteHalfWidth),
      PLOT.viewW - PLOT.marginR - PLOT.footnoteHalfWidth,
    ),
  );
  items.push({ el: "expected-mark", x: expectedX, y1: PLOT.axisY - 6, y2: PLOT.axisY + 12 });
  items.push({
    el: "expected-label",
    x: expectedLabelX,
    y: PLOT.footnoteY,
    text: `expected ≈ ${backoff.totals.expectedTotalMs} ms`,
  });
  items.push({ el: "endmark", x1: xOf(worst), y1: PLOT.endmarkTop, x2: xOf(worst), y2: PLOT.axisY });
  items.push({ el: "total-label", x: xOf(worst), y: PLOT.totalLabelY, text: `worst case ${worst} ms` });

  return { view: { w: PLOT.viewW, h: PLOT.viewH }, backoff, items };
}

/* ---------- stop-gate kind: typed session entries ---------- */

function deriveCounts(entries) {
  let deviations = 0;
  let needsHuman = 0;
  let checksFailed = 0;
  for (const entry of entries) {
    if (entry.type === "deviation") deviations += 1;
    if (entry.needsHuman) needsHuman += 1;
    if (entry.type === "check" && entry.state !== "pass") checksFailed += 1;
  }
  return { all: entries.length, deviations, needsHuman, checksFailed };
}

function filterEntries(entries, filter) {
  switch (filter) {
    case "deviations":
      return entries.filter((entry) => entry.type === "deviation");
    case "needs-human":
      return entries.filter((entry) => Boolean(entry.needsHuman));
    case "checks":
      return entries.filter((entry) => entry.type === "check");
    default:
      return entries.slice();
  }
}

/* ---------- record boundary ---------- */

/* The ONLY statuses that may produce a durable record. Working/candidate
   statuses are structurally incapable of reaching record generation. */
const ACCEPTED_RECORD_STATUSES = ["approved", "completed"];

/** Shared gate between canonical state and record generation, used by the
 * publisher materializer and every installed bundle. Throws on any canonical
 * document that is not genuinely accepted. */
function validateCanonicalForRecord(canonical) {
  if (!canonical || typeof canonical !== "object") {
    throw new Error("Record generation requires a canonical document.");
  }
  const scenario = canonical.scenario;
  const accepted = canonical.accepted;
  if (!scenario || !accepted) {
    throw new Error("Canonical state must contain scenario and accepted blocks.");
  }
  assertSafeInstrumentData(scenario);

  const status = String(accepted.status ?? "");
  if (!ACCEPTED_RECORD_STATUSES.includes(status)) {
    throw new Error(
      `Records require an accepted terminal status (${ACCEPTED_RECORD_STATUSES.join("|")}); ` +
        `got ${JSON.stringify(status)}. Candidate or open state never produces a record.`,
    );
  }
  if (typeof accepted.acceptedVia !== "string" || accepted.acceptedVia.trim() === "") {
    throw new Error("Canonical state must record acceptedVia — how acceptance happened in chat.");
  }
  if (!Array.isArray(accepted.decisions) || accepted.decisions.length === 0) {
    throw new Error("Canonical state must record at least one accepted decision.");
  }
  for (const decision of accepted.decisions) {
    if (typeof decision.acceptedVia !== "string" || decision.acceptedVia.trim() === "") {
      throw new Error(
        `Decision ${JSON.stringify(decision.id ?? "?")} is missing acceptedVia evidence.`,
      );
    }
  }

  const working = accepted.exampleWorking;
  const primary = accepted.decisions[0];
  for (const required of scenario.requiredPriorDecisions ?? []) {
    const matches = accepted.decisions.filter((decision) => decision.id === required.id);
    if (matches.length !== 1) {
      throw new Error(
        `Required prior decision ${JSON.stringify(required.id)} must appear exactly once in accepted canonical state.`,
      );
    }
    const prior = matches[0];
    if (!required.allowedSelections.includes(prior.selection)) {
      throw new Error(
        `Prior decision ${JSON.stringify(required.id)} selection ${JSON.stringify(prior.selection)} is not accepted; ` +
          `expected one of ${required.allowedSelections.map((selection) => JSON.stringify(selection)).join(", ")}.`,
      );
    }
    if (prior.artifactPath !== required.artifactPath) {
      throw new Error(
        `Prior decision ${JSON.stringify(required.id)} artifact path does not match the accepted prerequisite.`,
      );
    }
    if (prior.acceptedRevision !== required.acceptedRevision) {
      throw new Error(
        `Prior decision ${JSON.stringify(required.id)} revision does not match the accepted prerequisite.`,
      );
    }
  }
  if (scenario.kind === "decision") {
    if (primary.id !== scenario.decisionId) {
      throw new Error(
        `Accepted decision id ${JSON.stringify(primary.id)} does not match scenario decision id ${JSON.stringify(scenario.decisionId)}.`,
      );
    }
    const optionIds = (scenario.options ?? []).map((option) => option.id);
    if (!optionIds.includes(primary.selection)) {
      throw new Error(
        `Accepted selection ${JSON.stringify(primary.selection)} is not an option in the scenario.`,
      );
    }
    if (!working || working.selected !== primary.selection) {
      throw new Error(
        "Accepted working state disagrees with the recorded decision (selected option mismatch).",
      );
    }
    if (working.rationale !== primary.rationale) {
      throw new Error(
        "Accepted working rationale disagrees with the recorded decision rationale.",
      );
    }
  } else if (scenario.kind === "stop-gate") {
    if (primary.id !== scenario.gate.id) {
      throw new Error(
        `Accepted decision id ${JSON.stringify(primary.id)} does not match STOP gate id ${JSON.stringify(scenario.gate.id)}.`,
      );
    }
    const optionIds = (scenario.gate?.options ?? []).map((option) => option.id);
    if (!optionIds.includes(primary.selection)) {
      throw new Error(
        `Accepted resolution ${JSON.stringify(primary.selection)} is not a gate option in the scenario.`,
      );
    }
    if (!working || working.resolution !== primary.selection) {
      throw new Error(
        "Accepted working state disagrees with the recorded decision (resolution mismatch).",
      );
    }
    if (Object.hasOwn(working, "filter")) {
      throw new Error(
        "STOP-board filter is ephemeral view state and must not enter accepted canonical state.",
      );
    }
    if (working.rationale !== primary.rationale) {
      throw new Error(
        "Accepted working rationale disagrees with the recorded decision rationale.",
      );
    }
  } else if (scenario.kind === "model") {
    if (primary.id !== scenario.decisionId) {
      throw new Error(
        `Accepted decision id ${JSON.stringify(primary.id)} does not match scenario decision id ${JSON.stringify(scenario.decisionId)}.`,
      );
    }
    if (primary.selection !== scenario.acceptanceToken) {
      throw new Error(
        `Accepted model acceptance ${JSON.stringify(primary.selection)} does not match scenario acceptance token ${JSON.stringify(scenario.acceptanceToken)}.`,
      );
    }
    if (!working || !working.params || !working.toggles) {
      throw new Error("Model canonical state must carry the accepted working parameters.");
    }
    const derived = accepted.derived;
    if (!derived) {
      throw new Error("Model canonical state must carry the derived block recorded at acceptance.");
    }
    const recomputed = deriveBackoff(working.params, working.toggles);
    const firstCapped = recomputed.rows.find((row) => row.cappedAtLimit);
    const consistent =
      derived.attempts === recomputed.totals.attempts &&
      derived.worstCaseTotalMs === recomputed.totals.worstCaseTotalMs &&
      derived.expectedTotalMs === recomputed.totals.expectedTotalMs &&
      (derived.firstCappedAttempt ?? null) === (firstCapped ? firstCapped.attempt : null);
    if (!consistent) {
      throw new Error(
        "Model canonical derived values disagree with the shared core calculation — the record would misstate the model.",
      );
    }
  } else if (
    scenario.kind === "prototype" ||
    scenario.kind === "quiz" ||
    scenario.kind === "checklist" ||
    scenario.kind === "dossier"
  ) {
    if (primary.id !== scenario.decisionId) {
      throw new Error(
        `Accepted decision id ${JSON.stringify(primary.id)} does not match scenario decision id ${JSON.stringify(scenario.decisionId)}.`,
      );
    }
    if (primary.selection !== scenario.acceptanceToken) {
      throw new Error(
        `Accepted selection ${JSON.stringify(primary.selection)} does not match the scenario acceptance token ${JSON.stringify(scenario.acceptanceToken)}.`,
      );
    }
    if (scenario.kind === "prototype") {
      if (!working || !working.params || !working.toggles) {
        throw new Error("Prototype canonical state must carry the accepted felt parameters.");
      }
    } else if (scenario.kind === "quiz") {
      if (!working || !working.answers) {
        throw new Error("Quiz canonical state must carry the accepted answers.");
      }
      for (const question of scenario.questions) {
        const chosen = working.answers[question.id];
        if (!chosen) {
          throw new Error(`Quiz canonical state is missing an answer for ${JSON.stringify(question.id)}.`);
        }
        if (!(question.options ?? []).some((option) => option.id === chosen)) {
          throw new Error(`Quiz canonical answer ${JSON.stringify(chosen)} is not an option of ${JSON.stringify(question.id)}.`);
        }
      }
      const recomputed = deriveQuizScore(scenario, working);
      const derived = accepted.derived;
      if (!derived || derived.correct !== recomputed.correct || derived.total !== recomputed.total) {
        throw new Error(
          "Quiz canonical score disagrees with the recomputed score — the record would misstate the result.",
        );
      }
    } else if (scenario.kind === "checklist") {
      if (!working || !working.marks) {
        throw new Error("Checklist canonical state must carry the accepted item verdicts.");
      }
      const verdictIds = (scenario.verdicts ?? []).map((verdict) => verdict.id);
      for (const item of scenario.items) {
        const mark = working.marks[item.id];
        if (!mark) {
          throw new Error(`Checklist canonical state is missing a verdict for ${JSON.stringify(item.id)}.`);
        }
        if (!verdictIds.includes(mark)) {
          throw new Error(`Checklist canonical verdict ${JSON.stringify(mark)} is not a declared verdict.`);
        }
      }
      if (scenario.conclusionRequired && !(working.conclusion ?? "").trim()) {
        throw new Error("Checklist canonical state requires a conclusion before a record exists.");
      }
    }
    /* dossier: acceptance-token match above is the whole working-state contract. */
  }
  return canonical;
}

/* ---------- candidate export ---------- */

function yamlValue(value) {
  if (value === null || value === undefined) return "null";
  if (typeof value === "number" || typeof value === "boolean") return String(value);
  return JSON.stringify(String(value));
}

function yamlLines(pairs) {
  return pairs.map(([key, value]) => `${key}: ${yamlValue(value)}`).join("\n");
}

function markdownList(items, empty) {
  if (!items || items.length === 0) return `- ${empty}`;
  return items.map((item) => `- ${item}`).join("\n");
}

function buildCandidate(data, working) {
  assertSafeInstrumentData(data);
  const status = deriveStatus(data, working);
  const commonFront = [
    ["acta_protocol", ACTA2_PROTOCOL],
    ["payload", "candidate"],
    ["artifact_kind", data.artifactKind],
    ["producer_skill", data.skill],
    ["initiative", data.initiative],
    ["instrument", data.kind],
    ["status", status.code],
    ["source_revision", data.sourceRevision],
  ];
  const json = {
    acta_protocol: ACTA2_PROTOCOL,
    payload: "candidate",
    artifact_kind: data.artifactKind,
    producer_skill: data.skill,
    initiative: data.initiative,
    instrument: data.kind,
    status: status.code,
    source_revision: data.sourceRevision,
    inputs: (data.inputs ?? []).slice(),
    unresolved: (data.unresolved ?? []).slice(),
  };

  const preamble = [
    `# Candidate — ${data.title}`,
    "",
    "This payload is a candidate, not canonical state. Apply it only after",
    "explicit acceptance in chat; silence is never approval.",
    "",
    `Question: ${data.question}`,
    `Working status: ${status.label}`,
  ];

  let kindFront = [];
  let body = [];

  if (data.kind === "decision") {
    const selected = optionById(data.options, working.selected);
    kindFront = [["selected_option", working.selected]];
    json.selection = {
      option: working.selected,
      label: selected ? selected.label : null,
      rationale: working.rationale || null,
    };
    body = [
      "## Working selection",
      "",
      selected
        ? `Selected: **${selected.label}** (\`${selected.id}\`)`
        : "No option selected yet.",
      working.rationale ? `Rationale: ${working.rationale}` : "Rationale: (none volunteered)",
      "",
      "## Alternatives on the table",
      "",
      markdownList(
        data.options.map((option) =>
          option.id === working.selected ? `${option.label} ← selected` : option.label,
        ),
        "none",
      ),
    ];
  } else if (data.kind === "stop-gate") {
    const resolution = optionById(data.gate.options, working.resolution);
    kindFront = [
      ["stop_gate", data.gate.id],
      ["stop_resolution", working.resolution],
    ];
    json.gate = {
      id: data.gate.id,
      title: data.gate.title,
      state: working.resolution ? "resolution-proposed" : "open",
    };
    json.resolution = {
      option: working.resolution,
      label: resolution ? resolution.label : null,
      rationale: working.rationale || null,
    };
    body = [
      `## ${data.gate.id} — ${data.gate.title}`,
      "",
      resolution
        ? `Proposed resolution: **${resolution.label}** (\`${resolution.id}\`)`
        : "The gate is open. No resolution proposed yet; work stays paused.",
      working.rationale ? `Rationale: ${working.rationale}` : "Rationale: (none volunteered)",
      "",
      "Work resumes only after explicit acceptance in chat records this resolution",
      "in canonical state.",
    ];
  } else if (data.kind === "model") {
    const derived = deriveBackoff(working.params, working.toggles);
    kindFront = [
      ...Object.entries(working.params).map(([id, value]) => [`param_${id}`, value]),
      ...Object.entries(working.toggles).map(([id, value]) => [`toggle_${id}`, value]),
    ];
    json.parameters = { ...working.params };
    json.toggles = { ...working.toggles };
    json.conclusion = working.conclusion.trim() || null;
    json.derived = {
      attempts: derived.totals.attempts,
      worstCaseTotalMs: derived.totals.worstCaseTotalMs,
      expectedTotalMs: derived.totals.expectedTotalMs,
    };
    body = [
      "## Chosen parameters",
      "",
      markdownList(
        data.params.map(
          (param) => `${param.label}: ${working.params[param.id]}${param.unit}`,
        ),
        "defaults",
      ),
      markdownList(
        (data.toggles ?? []).map(
          (toggle) => `${toggle.label}: ${working.toggles[toggle.id] ? "on" : "off"}`,
        ),
        "no toggles",
      ),
      "",
      "## Derived consequence",
      "",
      `Worst-case total wait across ${derived.totals.attempts} attempts: ${derived.totals.worstCaseTotalMs}ms` +
        ` (expected ≈ ${derived.totals.expectedTotalMs}ms).`,
      "",
      "## Observed conclusion",
      "",
      working.conclusion.trim() || "(record what the model showed you before exporting)",
      "",
      "## Declared simplifications",
      "",
      markdownList(data.simplifications, "none declared"),
    ];
  } else if (data.kind === "prototype") {
    kindFront = [
      ...Object.entries(working.params).map(([id, value]) => [`param_${id}`, value]),
      ...Object.entries(working.toggles).map(([id, value]) => [`toggle_${id}`, value]),
    ];
    json.parameters = { ...working.params };
    json.toggles = { ...working.toggles };
    json.conclusion = working.conclusion.trim() || null;
    body = [
      "## Felt parameters",
      "",
      markdownList(
        data.params.map(
          (param) => `${param.label}: ${working.params[param.id]}${param.unit}`,
        ),
        "defaults",
      ),
      markdownList(
        (data.toggles ?? []).map(
          (toggle) => `${toggle.label}: ${working.toggles[toggle.id] ? "on" : "off"}`,
        ),
        "no toggles",
      ),
      "",
      "## Felt conclusion",
      "",
      working.conclusion.trim() || "(record how the prototype felt before exporting)",
      "",
      "The prototype itself is disposable; only these parameters and this",
      "conclusion carry forward.",
    ];
  } else if (data.kind === "quiz") {
    const score = deriveQuizScore(data, working);
    kindFront = [
      ["score_correct", score.correct],
      ["score_total", score.total],
      ["gaps", score.gaps.length],
    ];
    json.answers = { ...working.answers };
    json.score = { correct: score.correct, total: score.total };
    json.gaps = score.gaps.map((gap) => ({ question: gap.question, gap: gap.gap ?? null }));
    json.reflection = (working.reflection ?? "").trim() || null;
    body = [
      "## Self-check result",
      "",
      `Score: ${score.correct} / ${score.total}. This check is diagnostic — never a merge gate.`,
      "",
      "## Answers",
      "",
      markdownList(
        data.questions.map((question) => {
          const chosen = working.answers[question.id];
          const mark = chosen === question.answer ? "✓" : chosen ? "✗" : "—";
          return `${mark} ${question.prompt} (chose: ${chosen ?? "unanswered"})`;
        }),
        "no questions",
      ),
      "",
      "## Gaps to close",
      "",
      markdownList(
        score.gaps.map((gap) => `${gap.gap ?? gap.prompt}`),
        "none — every answer matched the evidence",
      ),
    ];
  } else if (data.kind === "checklist") {
    const summary = deriveChecklistSummary(data, working);
    const verdictById = Object.create(null);
    for (const verdict of data.verdicts) verdictById[verdict.id] = verdict;
    kindFront = data.items.map((item) => [`mark_${item.id}`, working.marks[item.id]]);
    json.marks = { ...working.marks };
    json.counts = { ...summary.byVerdict };
    json.conclusion = (working.conclusion ?? "").trim() || null;
    body = [
      "## Item verdicts",
      "",
      markdownList(
        data.items.map((item) => {
          const mark = working.marks[item.id];
          const verdict = mark ? verdictById[mark] : null;
          return `${item.label}: ${verdict ? verdict.label : "(no verdict yet)"}`;
        }),
        "no items",
      ),
      "",
      "## Conclusion",
      "",
      (working.conclusion ?? "").trim() || "(none recorded)",
    ];
  } else {
    throw new Error(`Unknown instrument kind: ${data.kind}`);
  }

  const closing = [
    "## Unresolved",
    "",
    markdownList(data.unresolved, "nothing recorded"),
    "",
    "## Provenance inputs",
    "",
    markdownList(data.inputs, "none recorded"),
  ];

  const markdown = [
    "---",
    yamlLines([...commonFront, ...kindFront]),
    "---",
    "",
    ...preamble,
    "",
    ...body,
    "",
    ...closing,
    "",
  ].join("\n");

  return { markdown, json };
}

/* ACTA2-ESM-START (stripped when inlined into instruments) */
export {
  ACTA2_PROTOCOL,
  ACCEPTED_RECORD_STATUSES,
  INSTRUMENT_STATUSES,
  assertSafeInstrumentData,
  backoffPlotSpec,
  initialWorking,
  deriveStatus,
  deriveBackoff,
  deriveCounts,
  deriveQuizScore,
  deriveChecklistSummary,
  filterEntries,
  buildCandidate,
  validateCanonicalForRecord,
};
/* ACTA2-ESM-END */
