---
name: second-opinion
description: "Cross-model review of a diff before merge: reviewers run on the other model's CLI, on two separate axes (standards and the request), and the lead triages every finding into act on, consider, noted or dismissed. Use before merging or opening a PR, when I ask for a review, and always when a change touches auth, tenant scope, sync, data or migrations."
---

# second-opinion

The value is a second model looking at the final diff. The lead's job is to filter that review, not to forward it.

## 1. Pin it

- Resolve the base ref and head SHA with `git rev-parse`; run `git diff --stat <base>...<head>`. A bad ref or an empty diff fails here.
- State the intent in two lines and name the originating request: issue, my message, or spec.

## 2. Size the panel

| Diff | Reviewers |
|---|---|
| Under 50 lines, 1–2 files | Skeptic |
| Up to 200 lines, up to 5 files | Skeptic, Architect |
| Larger | Skeptic, Architect, Minimalist |

Auth, tenant scope, sync, data and migrations always get the Skeptic at high effort, whatever the size.

## 3. Run on the other model

Never use a same-model subagent as a reviewer; that defeats the purpose.

- From Claude: `codex exec --skip-git-repo-check -s read-only -o "$DIR/<lens>.md" "<prompt>"`
- From Codex: `claude -p "<prompt>" > "$DIR/<lens>.md"`

Build each prompt from [reviewer-prompt.md](reviewer-prompt.md). Before reading, confirm every output file exists and is not empty. A missing review is a gap, not a pass.

## 4. Lead judgment

You hold the full context; the reviewers saw a diff. For every finding, trace the code: a hypothetical input the callers can never pass is not a finding. Then place it in exactly one bucket:

- **Act on**: real, concrete, worth fixing before merge. More than 5 means you are not filtering hard enough.
- **Consider**: real but optional, or a judgment call for me.
- **Noted**: true, not worth action now.
- **Dismissed**: with the reason. This list is a trust mechanism: it lets me overrule you.

If every finding is a nit, the code is probably fine; say so. Be slow to dismiss security and correctness findings, especially when two reviewers agree.

Keep the two axes separate. Do not merge or rerank Standards findings against Request findings.

## 5. Merge danger

One line each: two-way or one-way door; blast radius; the one fact the change is safe because of, and how far it is proven (said, pointed at the line, walked the failure, ran it, reproduced it in the app).

## Reply

Verdict in one line; Act on; Consider; Noted; Dismissed; Merge danger; reviewers run (CLI, model, output files). Change no code during the review unless I asked you to resolve the findings.
