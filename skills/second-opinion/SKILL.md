---
name: second-opinion
description: "Cross-model review of a diff before merge, or of a whole setup in design-review mode: reviewers run on the other model's CLI, on two separate axes (standards and the request), and the lead triages every finding into act on, consider, noted or dismissed. Use before merging or opening a PR, when I ask for a review, and always when a change touches auth, tenant scope, sync, data or migrations."
---

# second-opinion

The value is a model other than the author looking at the final work. The lead's job is to filter that review, not to forward it.

## 0. Who wrote it

Identify the authoring model before anything else: `Co-Authored-By` trailers in `git log <base>..<head>`, the brief that produced the work, or the delegator's message. Say it in one line.

- You are a different model from the author: review directly yourself, on the same axes. Never send it back to the author's model, and do not recurse into another reviewer.
- You are the author's model: run the reviewers on the other model's CLI (step 3).
- Author unknown: say so and treat it as written by your own model.

## 1. Pin it

Pick the mode:

- **Diff review** (default): resolve the base ref and head SHA with `git rev-parse`; run `git diff --stat <base>...<head>`. A bad ref or an empty diff fails here.
- **Design review**: the whole setup, not a diff (rules, skills, automation, architecture). Pin the commit SHA and the exact list of files or folders in scope.

State the intent in two lines and name the originating request: issue, my message, or spec.

## 2. Size the panel

| Work under review | Reviewers |
|---|---|
| Under 50 lines, 1–2 files | Skeptic |
| Up to 200 lines, up to 5 files | Skeptic, Architect |
| Larger, or any design review | Skeptic, Architect, Minimalist |

Auth, tenant scope, sync, data and migrations always get the Skeptic at high effort, whatever the size.

## 3. Run on the other model

Never use a same-model subagent as a reviewer; that defeats the purpose.

- From Claude: `codex exec --skip-git-repo-check -s read-only -o "$DIR/<lens>.md" "<prompt>"`
- From Codex: `claude -p "<prompt>" > "$DIR/<lens>.md"`

Build each prompt from [reviewer-prompt.md](reviewer-prompt.md). Before reading, confirm every output file exists and is not empty. A missing review is a gap, not a pass.

## 4. Lead judgment

You hold the full context; the reviewers saw a diff or a file list. For every finding, trace the code: a hypothetical input the callers can never pass is not a finding. Every finding you keep carries:

- its **axis**: Standards, Request or (design review) Design;
- its **evidence**: measured (the command you ran and what came out) or inferred (the `file:line` you read).

Then place it in exactly one bucket:

- **Act on**: real, concrete, worth fixing before merge. Every blocker goes here, however many there are. Aim for 5 or fewer otherwise: past that, you are not filtering the nits hard enough. The cap filters nits; it never hides a blocker.
- **Consider**: real but optional, or a judgment call for me.
- **Noted**: true, not worth action now.
- **Dismissed**: with the reason. This list is a trust mechanism: it lets me overrule you.

If every finding is a nit, the work is probably fine; say so. Be slow to dismiss security and correctness findings, especially when two reviewers agree.

Keep the axes separate. Do not merge or rerank Standards findings against Request findings.

## 5. Merge danger

One line each: two-way or one-way door; blast radius; the one fact the change is safe because of, and how far it is proven (said, pointed at the line, walked the failure, ran it, reproduced it in the app).

## Reply

Verdict in one line; author model and review route (direct, or reviewers on which CLI); Act on; Consider; Noted; Dismissed; Merge danger; reviewers run (CLI, model, output files). Change no code during the review unless I asked you to resolve the findings.
