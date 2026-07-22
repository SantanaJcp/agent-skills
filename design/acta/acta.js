(function(){
  "use strict";
  function statusFor(button){
    return button.closest("section")?.querySelector("[data-status]") || document.querySelector("[data-status]");
  }
  function announce(button, message, isError = false){
    const region = statusFor(button);
    if (!region) return;
    region.classList.toggle("is-error", isError);
    region.textContent = message;
  }
  async function copyText(button, text, label){
    try {
      if (!navigator.clipboard?.writeText) throw new Error("clipboard unavailable");
      await navigator.clipboard.writeText(text);
      announce(button, label + " copied to clipboard.");
      return;
    } catch {}
    const area = document.createElement("textarea");
    area.value = text;
    document.body.appendChild(area);
    area.select();
    let copied = false;
    try { copied = document.execCommand("copy"); } catch {}
    area.remove();
    announce(button, copied ? label + " copied to clipboard." : "Copy failed — select the text manually.", !copied);
  }
  document.addEventListener("click", function(event){
    const button = event.target.closest("button");
    if (!button) return;
    const targetId = button.getAttribute("data-copy-block");
    if (targetId){
      const target = document.getElementById(targetId);
      if (target) copyText(button, target.textContent, button.getAttribute("data-copy-label") || "Content");
      return;
    }
    if (button.hasAttribute("data-seg")){
      button.parentElement.querySelectorAll("button").forEach(function(candidate){
        candidate.setAttribute("aria-pressed", String(candidate === button));
      });
      announce(button, "View changed to " + button.textContent + ".");
      return;
    }
    if (button.hasAttribute("data-quiz-check")){
      const quiz = button.closest("[data-quiz]");
      const selected = quiz?.querySelector("input[type=radio]:checked");
      if (!selected){ announce(button, "Select an answer first.", true); return; }
      const correct = selected.value === quiz.getAttribute("data-answer");
      quiz.querySelectorAll("[data-feedback]").forEach(function(feedback){
        feedback.hidden = feedback.getAttribute("data-feedback") !== (correct ? "correct" : "incorrect");
      });
      announce(button, correct ? "Correct answer." : "Review the linked evidence and try again.");
    }
  });
  window.addEventListener("beforeprint", function(){
    document.querySelectorAll("details").forEach(function(detail){ detail.open = true; });
  });
})();
