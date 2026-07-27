# QA evidence policy

This directory contains concise, reviewable, versioned summaries that support a
published compatibility or promotion claim.

Commit only final evidence that:

- identifies the tested source revision, surface, versions, date, and verdict;
- distinguishes passed, failed, blocked, deferred, and not-applicable rows;
- contains enough observations to audit the verdict without reproducing a raw
  model transcript;
- uses repository-relative or portable placeholder paths;
- excludes credentials, private data, monetary usage details, machine-local
  absolute paths, raw JSONL, HAR files, captures, disposable worktrees, and
  generated command logs.

Raw evaluator output is ephemeral or belongs in a reviewer-controlled location
outside this repository. A release tag preserves the exact summaries published
with that release; later evidence may supersede a result prospectively but must
not rewrite a historical deferral into a pass.
