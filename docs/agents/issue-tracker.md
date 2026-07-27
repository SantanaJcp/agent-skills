# Issue tracker: GitHub Issues

GitHub Issues is the canonical public tracker for repository work, including
deferred validation, defects, and proposed skills. Accepted architecture and
policy decisions live in `docs/adr/`; an issue links those durable documents
rather than replacing them.

## Publishing

- Search existing open and closed issues before creating one.
- Use a specific title, observable acceptance criteria, and repository-relative
  file references.
- Apply one of the canonical triage labels from
  [triage-labels.md](triage-labels.md); do not invent an equivalent label.
- Link blocking or superseding issues explicitly.
- Keep credentials, private repository details, raw model logs, captures, and
  machine-local paths out of issue bodies and comments.

When a skill says “publish to the issue tracker,” create or update the relevant
GitHub Issue and return its URL.

## Local drafts

`.scratch/` may be used for disposable private notes while preparing an issue.
It is ignored and must never be committed, linked as durable evidence, or
treated as the source of truth. Delete local drafts after publishing or move
long-lived private notes to a user-owned location outside this repository.

## Resolution

Close an issue only when its acceptance criteria are met or a maintainer records
an explicit `wontfix` decision. Mergeable implementation details belong in the
pull request; stable decisions and contracts belong in repository documentation.
