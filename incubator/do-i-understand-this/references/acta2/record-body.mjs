/* Record body for do-i-understand-this: the score, every question with the
   chosen and correct answers, and the named gaps with their evidence
   locations. Diagnostic record — never a merge gate. */

export function renderRecord(data, accepted, { esc }) {
  const answers = accepted.exampleWorking.answers;
  let correct = 0;
  const gaps = [];
  for (const question of data.questions) {
    if (answers[question.id] === question.answer) correct += 1;
    else gaps.push(question);
  }

  const rows = data.questions
    .map((question, index) => {
      const chosen = answers[question.id];
      const isCorrect = chosen === question.answer;
      const chosenLabel = question.options.find((option) => option.id === chosen)?.label ?? chosen;
      const answerLabel = question.options.find((option) => option.id === question.answer)?.label ?? question.answer;
      return `<tr>
<th scope="row">${String(index + 1).padStart(2, "0")}</th>
<td>${esc(question.prompt)}</td>
<td>${esc(chosenLabel)}${isCorrect ? "" : `<br><em>correct: ${esc(answerLabel)}</em>`}</td>
<td>${isCorrect ? "✓" : "✗"}</td>
</tr>`;
    })
    .join("\n");

  return `
<section class="acta-section" aria-labelledby="score-title">
<h2 id="score-title" class="acta-h2">Result</h2>
<div class="r-facts">
<div class="r-fact"><b>${correct} / ${data.questions.length}</b><span>score</span></div>
<div class="r-fact"><b>${gaps.length}</b><span>named gaps</span></div>
<div class="r-fact"><b>diagnostic</b><span>never a merge gate</span></div>
</div>
<p>${esc(accepted.summary)}</p>
${accepted.exampleWorking.reflection ? `<div class="r-aside"><span class="r-k">Reflection</span><p>${esc(accepted.exampleWorking.reflection)}</p></div>` : ""}
</section>
<section class="acta-section" aria-labelledby="answers-title">
<h2 id="answers-title" class="acta-h2">Answers</h2>
<div class="tablewrap"><table class="r-table">
<thead><tr><th scope="col">#</th><th scope="col">Question</th><th scope="col">Answered</th><th scope="col"></th></tr></thead>
<tbody>
${rows}
</tbody>
</table></div>
</section>
<section class="acta-section" aria-labelledby="gaps-title">
<h2 id="gaps-title" class="acta-h2">Gaps to close</h2>
${gaps.length === 0 ? "<p>No gaps — every answer matched the evidence.</p>" : gaps
    .map(
      (question) => `
<div class="r-warn"><span class="r-k">${esc(question.gap)}</span>
<p>${esc(question.prompt)}</p>
<p>${esc(question.explanation)}</p>
</div>`,
    )
    .join("\n")}
</section>`;
}
