/* Acta v2 — shared instrument runtime.
   Inlined after export-core; expects the core functions in scope
   (initialWorking, deriveStatus, buildCandidate, deriveBackoff,
   deriveCounts, filterEntries).

   Responsibilities:
   - parse the #acta2-data island into `data`;
   - own `working` state and route all input events into it;
   - re-derive status + candidate export on every change and write them
     into the DOM via textContent (never markup sinks);
   - verify displayed export === recomputed export (integrity contract);
   - clipboard copy with honest fallback;
   - optional in-page self-test (?acta2selftest=1) for headless assertion.

   The browser NEVER persists anything: no storage, no network, no file
   writes. The only exit is human-carried text. */

(function () {
  "use strict";

  var dataNode = document.getElementById("acta2-data");
  if (!dataNode) return;
  var data;
  try {
    data = JSON.parse(dataNode.textContent);
  } catch (error) {
    document.body.setAttribute("data-acta2-integrity", "mismatch");
    return;
  }

  var working = initialWorking(data);
  var renderHooks = [];
  var currentExport = { markdown: "", json: null };

  function text(selector, value) {
    document.querySelectorAll(selector).forEach(function (node) {
      node.textContent = value;
    });
  }

  function announce(message, isError) {
    var region = document.querySelector("[data-a2-live]");
    if (!region) return;
    region.classList.toggle("is-error", Boolean(isError));
    region.textContent = message;
  }

  function expectedExportText(format) {
    var fresh = buildCandidate(data, working);
    return format === "json" ? JSON.stringify(fresh.json, null, 2) : fresh.markdown;
  }

  /* Both displayed payloads must equal a fresh recompute from working state.
     A single stale format is a full integrity failure. */
  function verifyIntegrity() {
    var ok = true;
    ["markdown", "json"].forEach(function (format) {
      var displayed = document.querySelector('[data-derived-export="' + format + '"]');
      if (!displayed || displayed.textContent !== expectedExportText(format)) ok = false;
    });
    document.body.setAttribute("data-acta2-integrity", ok ? "ok" : "mismatch");
    return ok;
  }

  function render() {
    var status = deriveStatus(data, working);
    document.body.setAttribute("data-acta2-status", status.code);
    text("[data-bind='status-label']", status.label);
    currentExport = buildCandidate(data, working);
    text("[data-derived-export='markdown']", currentExport.markdown);
    text("[data-derived-export='json']", JSON.stringify(currentExport.json, null, 2));
    renderHooks.forEach(function (hook) {
      hook(data, working, status);
    });
    verifyIntegrity();
  }

  /* ---------- generic input routing ---------- */

  document.addEventListener("change", function (event) {
    var node = event.target;
    if (!(node instanceof HTMLElement)) return;
    if (node.matches("input[name='acta2-option']")) {
      working.selected = node.value;
      render();
    } else if (node.matches("input[name='acta2-resolution']")) {
      working.resolution = node.value;
      render();
    } else if (node.matches("[data-toggle]")) {
      working.toggles[node.getAttribute("data-toggle")] = node.checked;
      render();
    } else if (node.matches("[data-quiz-answer]")) {
      working.answers[node.getAttribute("data-quiz-answer")] = node.value;
      render();
    } else if (node.matches("[data-mark-item]")) {
      working.marks[node.getAttribute("data-mark-item")] = node.value;
      render();
    }
  });

  document.addEventListener("input", function (event) {
    var node = event.target;
    if (!(node instanceof HTMLElement)) return;
    if (node.matches("[data-param]")) {
      working.params[node.getAttribute("data-param")] = Number(node.value);
      render();
    } else if (node.matches("[data-working]")) {
      working[node.getAttribute("data-working")] = node.value;
      render();
    }
  });

  document.addEventListener("click", function (event) {
    var button = event.target instanceof Element ? event.target.closest("button") : null;
    if (!button) return;
    if (button.hasAttribute("data-acta2-reset")) {
      working = initialWorking(data);
      document.querySelectorAll(
        "input[name='acta2-option'],input[name='acta2-resolution'],[data-quiz-answer],[data-mark-item]"
      ).forEach(function (radio) {
        radio.checked = false;
      });
      document.querySelectorAll("[data-param]").forEach(function (input) {
        var id = input.getAttribute("data-param");
        input.value = String(working.params[id]);
      });
      document.querySelectorAll("[data-toggle]").forEach(function (input) {
        input.checked = Boolean(working.toggles[input.getAttribute("data-toggle")]);
      });
      document.querySelectorAll("[data-working]").forEach(function (input) {
        input.value = "";
      });
      if (working.filter !== undefined) {
        working.filter = "all";
        document.querySelectorAll("[data-filter]").forEach(function (candidate) {
          candidate.setAttribute("aria-pressed", String(candidate.getAttribute("data-filter") === "all"));
        });
      }
      render();
      announce("Working state reset.");
      return;
    }
    if (button.hasAttribute("data-filter")) {
      if (working.filter !== undefined) {
        working.filter = button.getAttribute("data-filter");
        document.querySelectorAll("[data-filter]").forEach(function (candidate) {
          candidate.setAttribute("aria-pressed", String(candidate === button));
        });
        render();
      }
      return;
    }
    var plainCopyId = button.getAttribute("data-copy-text-from");
    if (plainCopyId) {
      var plainSource = document.getElementById(plainCopyId);
      if (plainSource) {
        copyText(plainSource.textContent, button.getAttribute("data-copy-label") || "Source");
      }
      return;
    }
    var copyId = button.getAttribute("data-copy-from");
    if (copyId) {
      var source = document.getElementById(copyId);
      if (!source) return;
      // Verify the EXACT format this button copies, plus overall integrity.
      var format = source.getAttribute("data-derived-export") || "markdown";
      var formatFresh = source.textContent === expectedExportText(format);
      if (!verifyIntegrity() || !formatFresh) {
        announce("Integrity check failed — do not paste this export.", true);
        return;
      }
      copyText(source.textContent, button.getAttribute("data-copy-label") || "Export");
    }
  });

  function copyText(value, label) {
    function fallback() {
      var area = document.createElement("textarea");
      area.value = value;
      document.body.appendChild(area);
      area.select();
      var copied = false;
      try {
        copied = document.execCommand("copy");
      } catch (error) {
        copied = false;
      }
      area.remove();
      announce(
        copied
          ? label + " copied. Paste it in chat; it stays a candidate until you confirm."
          : "Copy failed — select the export text manually.",
        !copied,
      );
    }
    if (navigator.clipboard && navigator.clipboard.writeText) {
      navigator.clipboard.writeText(value).then(function () {
        announce(label + " copied. Paste it in chat; it stays a candidate until you confirm.");
      }, fallback);
    } else {
      fallback();
    }
  }

  window.addEventListener("beforeprint", function () {
    document.querySelectorAll("details").forEach(function (detail) {
      detail.open = true;
    });
  });

  /* ---------- instrument hook API (topology-specific wiring) ---------- */

  window.Acta2 = {
    data: data,
    getWorking: function () {
      return working;
    },
    getExport: function () {
      return currentExport;
    },
    onRender: function (hook) {
      renderHooks.push(hook);
    },
    refresh: render,
  };

  /* ---------- self-test (headless assertion hook) ---------- */

  function selfTest() {
    var failures = [];
    function expect(condition, message) {
      if (!condition) failures.push(message);
    }
    function setInput(node, value) {
      node.value = value;
      node.dispatchEvent(new Event("input", { bubbles: true }));
    }
    try {
      expect(
        document.body.getAttribute("data-acta2-ready") === "true",
        "runtime initialization marks the instrument ready",
      );
      expect(
        document.querySelectorAll("[data-a2-enable][disabled]").length === 0,
        "all controls are enabled after successful initialization",
      );
      var jsnote = document.querySelector(".a2-jsnote");
      expect(
        !jsnote || getComputedStyle(jsnote).display === "none",
        "no-JS fallback notes are hidden once the runtime is live",
      );
      if (data.kind === "decision") {
        var radios = document.querySelectorAll("input[name='acta2-option']");
        expect(radios.length >= 3, "decision instrument exposes option radios");
        expect(
          !document.querySelector("input[name='acta2-option'][checked]"),
          "no option is preselected",
        );
        var second = radios[1];
        second.checked = true;
        second.dispatchEvent(new Event("change", { bubbles: true }));
        expect(working.selected === second.value, "selection reaches working state");
        expect(currentExport.json.selection.option === second.value, "selection reaches export");
        var rationale = document.querySelector("[data-working='rationale']");
        if (rationale) {
          setInput(rationale, "selftest rationale");
          expect(currentExport.markdown.indexOf("selftest rationale") !== -1, "rationale reaches export");
        }
        expect(currentExport.json.status === "candidate-ready", "status follows selection");
        var first = radios[0];
        first.checked = true;
        first.dispatchEvent(new Event("change", { bubbles: true }));
        expect(currentExport.json.selection.option === first.value, "selection can change before export");
      } else if (data.kind === "stop-gate") {
        expect(currentExport.json.gate.state === "open", "gate starts open");
        var resolutions = document.querySelectorAll("input[name='acta2-resolution']");
        expect(resolutions.length >= 2, "gate exposes resolution options");
        resolutions[0].checked = true;
        resolutions[0].dispatchEvent(new Event("change", { bubbles: true }));
        expect(currentExport.json.resolution.option === resolutions[0].value, "resolution reaches export");
        expect(currentExport.json.status === "candidate-ready", "status follows resolution");
        var chip = document.querySelector("button[data-filter='deviations']");
        if (chip) {
          chip.click();
          var expected = filterEntries(data.entries, "deviations").length;
          var visible = document.querySelectorAll("[data-entry]:not([hidden])").length;
          expect(visible === expected, "filter shows exactly the derived entries");
          var resetForFilter = document.querySelector("[data-acta2-reset]");
          if (resetForFilter) {
            resetForFilter.click();
            expect(
              document.querySelectorAll("[data-entry]:not([hidden])").length === data.entries.length,
              "reset restores the unfiltered timeline",
            );
            var allChip = document.querySelector("button[data-filter='all']");
            expect(
              !allChip || allChip.getAttribute("aria-pressed") === "true",
              "reset restores the filter chips' pressed state",
            );
          }
        }
      } else if (data.kind === "model") {
        var slider = document.querySelector("[data-param]");
        expect(Boolean(slider), "model exposes parameter controls");
        var id = slider.getAttribute("data-param");
        setInput(slider, slider.max);
        expect(currentExport.json.parameters[id] === Number(slider.max), "parameter reaches export");
        var toggle = document.querySelector("[data-toggle]");
        if (toggle) {
          toggle.checked = !toggle.checked;
          toggle.dispatchEvent(new Event("change", { bubbles: true }));
          expect(
            currentExport.json.toggles[toggle.getAttribute("data-toggle")] === toggle.checked,
            "toggle reaches export",
          );
        }
        var conclusion = document.querySelector("[data-working='conclusion']");
        if (conclusion) {
          setInput(conclusion, "selftest conclusion");
          expect(currentExport.json.conclusion === "selftest conclusion", "conclusion reaches export");
          expect(currentExport.json.status === "candidate-ready", "status follows conclusion");
        }
        /* Live plot equals the shared spec at these NON-default parameters:
           every item, attribute, label, and capped state. */
        var livePlot = document.querySelector("[data-clab-plot]");
        if (livePlot && typeof backoffPlotSpec === "function") {
          var liveSpec = backoffPlotSpec(working.params, working.toggles);
          expect(
            livePlot.children.length === liveSpec.items.length,
            "live SVG has one node per spec item (" + livePlot.children.length + "/" + liveSpec.items.length + ")",
          );
          liveSpec.items.forEach(function (item, index) {
            var node = livePlot.children[index];
            if (!node) return;
            var tag = node.tagName.toLowerCase();
            if (item.el === "band") {
              expect(tag === "rect", "spec item " + index + " renders a rect");
              expect(node.getAttribute("x") === String(item.x), "band " + index + " x");
              expect(node.getAttribute("y") === String(item.y), "band " + index + " y");
              expect(node.getAttribute("width") === String(item.width), "band " + index + " width");
              expect(node.getAttribute("height") === String(item.height), "band " + index + " height");
              expect(
                Boolean(node.getAttribute("stroke-dasharray")) === Boolean(item.capped),
                "band " + index + " capped dash state",
              );
            } else if (item.el === "tick" || item.el === "axis-line" || item.el === "endmark") {
              expect(tag === "line", "spec item " + index + " renders a line");
              var x1 = item.el === "tick" ? item.x : item.x1;
              var x2 = item.el === "tick" ? item.x : item.x2;
              expect(node.getAttribute("x1") === String(x1), item.el + " " + index + " x1");
              expect(node.getAttribute("x2") === String(x2), item.el + " " + index + " x2");
              expect(node.getAttribute("y1") === String(item.y1), item.el + " " + index + " y1");
              expect(node.getAttribute("y2") === String(item.y2), item.el + " " + index + " y2");
            } else {
              expect(tag === "text", "spec item " + index + " renders a text");
              expect(node.textContent === item.text, item.el + " " + index + " label text");
              expect(node.getAttribute("x") === String(item.x), item.el + " " + index + " x");
              expect(node.getAttribute("y") === String(item.y), item.el + " " + index + " y");
            }
          });
        }
      }
      if (data.kind === "quiz") {
        var firstQuizRadio = document.querySelector("[data-quiz-answer]");
        expect(Boolean(firstQuizRadio), "quiz exposes answer radios");
        expect(
          !document.querySelector("[data-quiz-answer][checked]"),
          "no quiz answer is preselected",
        );
        firstQuizRadio.checked = true;
        firstQuizRadio.dispatchEvent(new Event("change", { bubbles: true }));
        var qid = firstQuizRadio.getAttribute("data-quiz-answer");
        expect(working.answers[qid] === firstQuizRadio.value, "answer reaches working state");
        expect(currentExport.json.answers[qid] === firstQuizRadio.value, "answer reaches export");
      } else if (data.kind === "checklist") {
        var firstMark = document.querySelector("[data-mark-item]");
        expect(Boolean(firstMark), "checklist exposes verdict radios");
        firstMark.checked = true;
        firstMark.dispatchEvent(new Event("change", { bubbles: true }));
        var itemId = firstMark.getAttribute("data-mark-item");
        expect(working.marks[itemId] === firstMark.value, "verdict reaches working state");
        expect(currentExport.json.marks[itemId] === firstMark.value, "verdict reaches export");
      } else if (data.kind === "prototype") {
        var protoSlider = document.querySelector("[data-param]");
        expect(Boolean(protoSlider), "prototype exposes parameter controls");
        setInput(protoSlider, protoSlider.max);
        expect(
          currentExport.json.parameters[protoSlider.getAttribute("data-param")] === Number(protoSlider.max),
          "prototype parameter reaches export",
        );
        var feltConclusion = document.querySelector("[data-working='conclusion']");
        if (feltConclusion) {
          setInput(feltConclusion, "selftest felt conclusion");
          expect(currentExport.json.conclusion === "selftest felt conclusion", "felt conclusion reaches export");
          expect(currentExport.json.status === "candidate-ready", "status follows felt conclusion");
        }
      }
      var displayed = document.querySelector('[data-derived-export="markdown"]');
      expect(displayed && displayed.textContent === buildCandidate(data, working).markdown, "displayed export equals recomputed export");
      expect(currentExport.markdown.indexOf('payload: "candidate"') !== -1, "export is marked candidate");

      /* Tamper tests: each displayed format is independently guarded. */
      var jsonNode = document.querySelector('[data-derived-export="json"]');
      var liveRegion = document.querySelector("[data-a2-live]");
      [
        { node: displayed, label: "markdown" },
        { node: jsonNode, label: "json" },
      ].forEach(function (target) {
        if (!target.node) {
          expect(false, "missing " + target.label + " export node");
          return;
        }
        var original = target.node.textContent;
        target.node.textContent = original + "\ntampered";
        expect(!verifyIntegrity(), "tampered " + target.label + " is detected");
        expect(
          document.body.getAttribute("data-acta2-integrity") === "mismatch",
          "tampered " + target.label + " raises the integrity banner",
        );
        var copyButton = document.querySelector("[data-copy-from]");
        if (copyButton && liveRegion) {
          liveRegion.textContent = "";
          copyButton.click();
          expect(
            liveRegion.textContent.indexOf("Integrity check failed") !== -1,
            "copy refuses a stale " + target.label + " export",
          );
        }
        target.node.textContent = original;
        expect(verifyIntegrity(), "restoring " + target.label + " restores integrity");
      });
      var resetButton = document.querySelector("[data-acta2-reset]");
      if (resetButton) {
        resetButton.click();
        var fresh = buildCandidate(data, initialWorking(data)).markdown;
        expect(
          document.querySelector('[data-derived-export="markdown"]').textContent === fresh,
          "reset returns export to the initial state",
        );
      }
    } catch (error) {
      failures.push("exception: " + error.message);
    }
    var verdict = failures.length === 0 ? "ACTA2-SELFTEST-PASS" : "ACTA2-SELFTEST-FAIL: " + failures.join("; ");
    document.title = verdict;
    var report = document.querySelector("[data-selftest]");
    if (report) report.textContent = verdict;
  }

  render();

  /* Honest no-JS: controls ship disabled and only become operational once
     the runtime has initialized and the first render+verify succeeded. */
  if (verifyIntegrity()) {
    document.querySelectorAll("[data-a2-enable]").forEach(function (control) {
      control.removeAttribute("disabled");
    });
    document.body.setAttribute("data-acta2-ready", "true");
  }

  if (window.location.search.indexOf("acta2selftest=1") !== -1) {
    selfTest();
  }
})();
