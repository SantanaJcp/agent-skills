/* draw-it-in-svg topology wiring: per-figure verdict tints and the
   marked-count line. Verdict routing itself is the shared runtime's
   data-mark-item handler. */
(function () {
  "use strict";
  if (!window.Acta2) return;

  window.Acta2.onRender(function (data, working) {
    var marked = 0;
    data.items.forEach(function (item) {
      var mark = working.marks[item.id];
      if (mark) marked += 1;
      var card = document.querySelector("[data-item='" + item.id + "']");
      if (card) card.setAttribute("data-state", mark || "unmarked");
    });
    var line = document.querySelector("[data-bind='marks-line']");
    if (line) line.textContent = marked + " of " + data.items.length + " figures marked";
  });

  window.Acta2.refresh();
})();
