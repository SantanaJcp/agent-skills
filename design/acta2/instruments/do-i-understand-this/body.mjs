/* Static renderer for the do-i-understand-this instrument (Node-side).
   Composition order is the instrument's argument: the mental model renders
   BEFORE any question, evidence cards ground every claim in file locations,
   and only then does the quiz ask you to prove it to yourself. Explanations
   ship inside per-question disclosures so the no-JS page stays complete and
   honest; the runtime opens them automatically once a question is answered.
   This check is diagnostic — never a merge gate. */

import { renderFlow } from "../../lib/flow.mjs";

export function renderBody(data, { esc }) {
  const facts = data.facts
    .map(
      (fact) =>
        `<div class="diu-fact" data-tone="${esc(fact.tone ?? "plain")}"><b>${esc(fact.value)}</b><span>${esc(fact.label)}</span></div>`,
    )
    .join("\n");

  const before = renderFlow(data.model.before.flow, esc, { ariaLabel: `Before: ${data.model.before.label}` });
  const after = renderFlow(data.model.after.flow, esc, { ariaLabel: `After: ${data.model.after.label}` });

  const behaviors = data.behaviors
    .map(
      (behavior, index) => `
<article class="diu-behavior">
<p class="b-title"><span class="b-n">${String(index + 1).padStart(2, "0")}</span>${esc(behavior.title)}</p>
<div class="b-rows">
<div class="b-row"><span class="b-k">What</span><p>${esc(behavior.what)}</p></div>
<div class="b-row"><span class="b-k">Why</span><p>${esc(behavior.why)}</p></div>
<div class="b-row"><span class="b-k">Where</span><p>${behavior.where.map((location) => `<span class="diu-loc">${esc(location)}</span>`).join("")}</p></div>
</div>
</article>`,
    )
    .join("\n");

  const questions = data.questions
    .map(
      (question, index) => `
<article class="diu-q" data-question="${esc(question.id)}">
<p class="q-prompt"><span class="q-n">${String(index + 1).padStart(2, "0")}</span>${esc(question.prompt)}</p>
<div class="q-options" role="group" aria-label="Answers for question ${index + 1}">
${question.options
        .map(
          (option) => `<label class="a2-choice q-opt"><input type="radio" name="acta2-q-${esc(question.id)}" value="${esc(option.id)}" data-quiz-answer="${esc(question.id)}"><span>${esc(option.label)}</span></label>`,
        )
        .join("\n")}
</div>
<details class="a2-more q-reveal"><summary>Reveal the answer and why</summary><div>
<p class="q-answer">Answer: <strong>${esc(question.options.find((option) => option.id === question.answer)?.label ?? question.answer)}</strong></p>
<p>${esc(question.explanation)}</p>
<p class="q-gapline">Gap if missed: <span class="diu-gaptag">${esc(question.gap)}</span></p>
</div></details>
</article>`,
    )
    .join("\n");

  return `
<h1 class="diu-question">${esc(data.question)}</h1>
<p class="diu-lede">${esc(data.lede)} This check is diagnostic — it is never a merge gate.</p>
<div class="diu-facts" aria-label="Change at a glance">
${facts}
</div>
<section class="diu-model" aria-label="The mental model">
<h2>The mental model</h2>
<p class="diu-sectionlede">${esc(data.model.lede)}</p>
<div class="diu-flows">
<figure class="diu-flowcard" data-side="before">
<figcaption><span class="f-tag">Before</span>${esc(data.model.before.label)}</figcaption>
<div class="plotwrap">${before.svg}</div>
</figure>
<figure class="diu-flowcard" data-side="after">
<figcaption><span class="f-tag is-after">After</span>${esc(data.model.after.label)}</figcaption>
<div class="plotwrap">${after.svg}</div>
</figure>
</div>
</section>
<section class="diu-behaviors" aria-label="Non-obvious behaviors">
<h2>${esc(data.behaviorsTitle)}</h2>
<p class="diu-sectionlede">${esc(data.behaviorsLede)}</p>
${behaviors}
</section>
<section class="diu-quiz" aria-label="Self-check questions">
<h2>Prove it to yourself</h2>
<p class="diu-scoreline"><span class="a2-status" data-bind="status-label">In progress — answer every question</span><span class="diu-score" data-bind="quiz-score">0 answered · score appears as you go</span></p>
${questions}
<p class="a2-jsnote">JavaScript is off, so the answer controls are disabled. Each question still carries its “Reveal” disclosure — answer honestly in your head first, or answer in chat and ask for the key.</p>
</section>
<section class="diu-close" aria-label="Gaps and reflection">
<h2>Gaps to close</h2>
<p class="diu-gapsline" data-bind="gaps-line">Answer the questions above; any misses collect here as named gaps.</p>
<label class="a2-field"><span>Reflection (optional, exported)</span><textarea rows="2" data-working="reflection" placeholder="What surprised you about this change?"></textarea></label>
</section>`;
}
