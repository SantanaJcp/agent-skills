/* find-the-cause topology wiring: verdict tints on hypothesis cards and the
   judged-count line. Verdict routing is the shared runtime's data-mark-item
   handler; nothing is ever auto-eliminated. */
(function () {
  "use strict";
  if (!window.Acta2) return;

  window.Acta2.onRender(function (data, working) {
    var judged = 0;
    data.items.forEach(function (item) {
      var mark = working.marks[item.id];
      if (mark) judged += 1;
      var card = document.querySelector("[data-item='" + item.id + "']");
      if (card) card.setAttribute("data-state", mark || "unjudged");
    });
    var line = document.querySelector("[data-bind='marks-line']");
    if (line) line.textContent = judged + " of " + data.items.length + " hypotheses judged";
  });

  window.Acta2.refresh();
})();
