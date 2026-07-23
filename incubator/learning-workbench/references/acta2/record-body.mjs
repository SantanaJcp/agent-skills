/* Record body for learning-workbench: the durable learning state a session
   leaves behind — score, per-question outcomes, waypoints to review next,
   and the session reflection. Diagnostic learning state, never a gate. */

export function renderRecord(data, accepted, { esc }) {
  const answers = accepted.exampleWorking.answers;
  let correct = 0;
  const review = [];
  for (const question of data.questions) {
    if (answers[question.id] === question.answer) correct += 1;
    else review.push(question);
  }

  return `
<section class="acta-section" aria-labelledby="session-title">
<h2 id="session-title" class="acta-h2">Session result</h2>
<div class="r-facts">
<div class="r-fact"><b>${correct} / ${data.questions.length}</b><span>retrieval score</span></div>
<div class="r-fact"><b>${data.lessons.length}</b><span>waypoints covered</span></div>
<div class="r-fact"><b>${review.length}</b><span>to review next session</span></div>
</div>
<p>${esc(accepted.summary)}</p>
${accepted.exampleWorking.reflection ? `<div class="r-aside"><span class="r-k">Reflection</span><p>${esc(accepted.exampleWorking.reflection)}</p></div>` : ""}
</section>
<section class="acta-section" aria-labelledby="review-title">
<h2 id="review-title" class="acta-h2">Review next session</h2>
${review.length === 0 ? "<p>Nothing queued — every retrieval held this session.</p>" : review
    .map(
      (question) => `
<div class="r-warn"><span class="r-k">${esc(question.gap)}</span>
<p>${esc(question.prompt)}</p>
<p>${esc(question.explanation)}</p>
</div>`,
    )
    .join("\n")}
</section>
<section class="acta-section" aria-labelledby="waypoints-title">
<h2 id="waypoints-title" class="acta-h2">Waypoints this session</h2>
<div class="tablewrap"><table class="r-table">
<thead><tr><th scope="col">#</th><th scope="col">Waypoint</th><th scope="col">Grounding</th></tr></thead>
<tbody>
${data.lessons
    .map(
      (lesson, index) => `<tr><th scope="row">${String(index + 1).padStart(2, "0")}</th><td>${esc(lesson.title)}</td><td>${lesson.facts
        .map((fact) => `<span class="r-loc">${esc(fact.source)}</span>`)
        .join("")}</td></tr>`,
    )
    .join("\n")}
</tbody>
</table></div>
</section>`;
}
