/* Static renderer for the learning-workbench instrument (Node-side).
   A durable learning workspace: mission, waypoint navigation, source-grounded
   lessons (each with its own model figure and cited facts), then retrieval
   practice (quiz kind) whose score and gaps export into the learning record.
   Multi-session by design — the record carries what to review next. */

import { renderFlow } from "../../lib/flow.mjs";

export function renderBody(data, { esc }) {
  const waypoints = data.lessons
    .map(
      (lesson, index) =>
        `<li><a href="#lwb-l-${esc(lesson.id)}"><span class="w-n">${String(index + 1).padStart(2, "0")}</span>${esc(lesson.title)}</a></li>`,
    )
    .join("\n");

  const lessons = data.lessons
    .map((lesson, index) => {
      const flow = lesson.flow
        ? renderFlow(lesson.flow, esc, { ariaLabel: `Model for ${lesson.title}` })
        : null;
      return `
<section class="lwb-lesson" id="lwb-l-${esc(lesson.id)}" aria-labelledby="lwb-t-${esc(lesson.id)}">
<h2 id="lwb-t-${esc(lesson.id)}"><span class="l-n">${String(index + 1).padStart(2, "0")}</span>${esc(lesson.title)}</h2>
${lesson.body.map((paragraph) => `<p class="l-body">${esc(paragraph)}</p>`).join("\n")}
${flow ? `<div class="lwb-model"><div class="plotwrap">${flow.svg}</div>
<p class="flowd-caption">${esc(lesson.flowCaption)}</p></div>` : ""}
<ul class="lwb-facts">
${lesson.facts
        .map(
          (fact) => `<li><span class="lwb-tag">${esc(fact.source)}</span>${esc(fact.text)}</li>`,
        )
        .join("\n")}
</ul>
</section>`;
    })
    .join("\n");

  const questions = data.questions
    .map(
      (question, index) => `
<article class="lwb-q" data-question="${esc(question.id)}">
<p class="q-prompt"><span class="q-n">${String(index + 1).padStart(2, "0")}</span>${esc(question.prompt)}</p>
<div class="q-options" role="group" aria-label="Answers for practice question ${index + 1}">
${question.options
        .map(
          (option) => `<label class="a2-choice q-opt"><input type="radio" name="acta2-q-${esc(question.id)}" value="${esc(option.id)}" data-quiz-answer="${esc(question.id)}"><span>${esc(option.label)}</span></label>`,
        )
        .join("\n")}
</div>
<details class="a2-more q-reveal"><summary>Reveal the answer and why</summary><div>
<p class="q-answer">Answer: <strong>${esc(question.options.find((option) => option.id === question.answer)?.label ?? question.answer)}</strong></p>
<p>${esc(question.explanation)}</p>
<p class="q-gapline">Review waypoint if missed: <span class="lwb-gaptag">${esc(question.gap)}</span></p>
</div></details>
</article>`,
    )
    .join("\n");

  return `
<h1 class="lwb-question">${esc(data.question)}</h1>
<p class="lwb-mission"><span class="a2-k">Mission</span>${esc(data.mission)}</p>
<nav class="lwb-waypoints" aria-label="Waypoints">
<ol>
${waypoints}
<li class="is-practice"><a href="#lwb-practice"><span class="w-n">◆</span>Retrieval practice</a></li>
</ol>
</nav>
${lessons}
<section class="lwb-practice" id="lwb-practice" aria-label="Retrieval practice">
<h2>Retrieval practice</h2>
<p class="lwb-practicelede">${esc(data.practiceLede)}</p>
<p class="lwb-scoreline"><span class="a2-status" data-bind="status-label">In progress — answer every question</span><span class="lwb-score" data-bind="quiz-score">0 answered · score appears as you go</span></p>
${questions}
<p class="a2-jsnote">JavaScript is off, so answer controls are disabled. Every question keeps its “Reveal” disclosure — practice honestly in your head, or answer in chat and ask for the key.</p>
</section>
<section class="lwb-close" aria-label="Session close">
<h2>Close the session</h2>
<p class="lwb-gapsline" data-bind="gaps-line">Answer the practice questions; missed waypoints collect here for the next session.</p>
<label class="a2-field"><span>Session reflection (optional, exported)</span><textarea rows="2" data-working="reflection" placeholder="What clicked this session? What still feels loose?"></textarea></label>
<p class="lwb-hint">The export carries your answers, score, and review waypoints; after you confirm it in chat, the workbench's canonical learning state is updated for the next session.</p>
</section>`;
}
