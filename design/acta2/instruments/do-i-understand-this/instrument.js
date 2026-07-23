/* do-i-understand-this topology wiring: verdict tints, auto-revealed
   explanations, live score, and the named-gaps line. The answer key lives in
   the data island by design — this is a self-diagnostic, not an exam. */
(function () {
  "use strict";
  if (!window.Acta2) return;

  window.Acta2.onRender(function (data, working) {
    var answered = 0;
    var correct = 0;
    var gaps = [];
    data.questions.forEach(function (question) {
      var chosen = working.answers[question.id];
      var article = document.querySelector("[data-question='" + question.id + "']");
      if (!article) return;
      if (!chosen) {
        article.setAttribute("data-state", "unanswered");
        return;
      }
      answered += 1;
      var isCorrect = chosen === question.answer;
      if (isCorrect) correct += 1;
      else gaps.push(question.gap);
      article.setAttribute("data-state", isCorrect ? "correct" : "incorrect");
      var reveal = article.querySelector(".q-reveal");
      if (reveal) reveal.open = true;
    });
    var score = document.querySelector("[data-bind='quiz-score']");
    if (score) {
      score.textContent =
        answered === 0
          ? "0 answered · score appears as you go"
          : "Score: " + correct + " / " + data.questions.length + " · " + answered + " answered";
    }
    var gapsLine = document.querySelector("[data-bind='gaps-line']");
    if (gapsLine) {
      if (answered === 0) {
        gapsLine.textContent = "Answer the questions above; any misses collect here as named gaps.";
      } else if (gaps.length === 0) {
        gapsLine.textContent =
          answered === data.questions.length
            ? "No gaps — every answer matched the evidence."
            : "No gaps so far — " + (data.questions.length - answered) + " question(s) left.";
      } else {
        gapsLine.textContent = "Gaps to close: " + gaps.join(" · ");
      }
    }
  });

  window.Acta2.refresh();
})();
