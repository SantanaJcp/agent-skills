<!-- acta-materialized: v0.1.0 protocol sha256=c1aeaf525fe9caa48fd87460434042203b8fb2541feef316d62c983118a59115; do not edit by hand -->
# Acta artifact protocol

Use this protocol for every artifact produced by this skill. The HTML scaffold is a human interface; Markdown and genuinely structured JSON are authoritative.

## Workspace

1. Infer an initiative slug from the issue, branch, or task and confirm it once.
2. Store this skill's work under `.agent-work/<initiative>/<skill>/`. In a Git repository, add `.agent-work/` idempotently to `.git/info/exclude`; do not edit the versioned ignore file.
3. Use stable canonical filenames. Before replacing an approved Markdown or JSON revision, copy it to `history/rNNNN.<ext>`. Do not archive HTML.
4. Learning workspaces are the exception: use the durable directory chosen by the learner.

## Canonical frontmatter

Every canonical Markdown artifact starts with these fields:

```yaml
acta_protocol: "0.1"
artifact_kind: "<kind>"
producer_skill: "<skill>"
initiative: "<slug>"
status: "draft"
language: "<BCP-47 tag>"
source_revision: "<full Git SHA or null>"
inputs: []
decisions: []
supersedes: null
```

Shared statuses are `draft`, `awaiting-decision`, `approved`, `completed`, `blocked`, and `superseded`. Add a separate phase field when a skill needs more detail. Time fields are optional and only belong to real temporal facts such as incidents, implementation sessions, quiz attempts, and review dates.

## Decisions and supersession

- A DecisionGate requires an explicit selection, not a rationale. Preserve a rationale when the user volunteers one.
- Accept an unambiguous natural-language selection or the Markdown/JSON exported by the HTML view; normalize both into the same decision record.
- Never infer approval from silence, fold an open gate, auto-approve, or invoke the next skill automatically.
- A new explicit instruction may supersede an approved decision. Record what changed. During implementation, architecture, API, data, security, or scope changes open a STOP gate before work continues.

## HTML views

- Generate a single self-contained, offline HTML file from the same canonical state exposed by exports.
- Treat the installed scaffold as the structural contract. Keep all essential content in the static DOM and make JavaScript progressive enhancement.
- Do not use network resources, webfonts, inline event handlers, unsafe dynamic markup sinks, browser storage, or direct file writes.
- Preserve native controls, keyboard focus, a no-script explanation, print rules, reduced motion, provenance, epistemic labels, and clipboard fallback.
- Browser state is ephemeral. Persist only through deliberate Markdown/JSON export.
- Try to open the view with a client capability when available; otherwise return its absolute path without failing the skill.

## Publication

Approval inside `.agent-work` does not publish. Publish only after a separate explicit request, follow the consuming project's documented tracker or durable-document rules, and ask for a destination when none is discoverable. A failed publication leaves the approved private artifact intact.
