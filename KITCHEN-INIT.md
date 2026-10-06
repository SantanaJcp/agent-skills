# kitchen init proposal

Written by `kitchen init` from base 82486e3. The owner reviews and pushes this branch; kitchen never pushes, opens a pull request or changes GitHub settings.

## Measured by --check at 82486e3 (that commit's tree; uncommitted changes are not part of the proposal)

- FAIL     check contract                     no bin/check and no .kitchen/checks.toml
- PASS     pre-commit hook active             .githooks/pre-commit is executable (core.hooksPath=.githooks)
- FAIL     AGENTS.md                          AGENTS.md has 22 lines but names no verify command (a verify-<repo> skill, bin/check or bin/verify)
- FAIL     verify skill + map guard           no .agents/skills/verify-*/SKILL.md
- PASS     decisions.md                       decisions.md
- FAIL     secret scan in hook                no secret scanner in the active hook or the files it references (.githooks/pre-commit, bin/kitchen)
- FAIL     baseline ratchet                   no baseline file (*baseline*/*ratchet* data file, eslint-suppressions.json, .betterer.results)
- FAIL     skills in .claude/skills           no project skills under .agents/skills to link
- FAIL     required status on shared branch   main: no required status in gh api repos/SantanaJcp/agent-skills/branches/main (classic) or repos/SantanaJcp/agent-skills/rules/branches/main (rules: none)
- FAIL     agent guards travel with the repo  no .kitchen/hooks/: teammates and cloud sessions run agents without the kitchen's guards
- FAIL     principles travel with the repo    no .kitchen/PRINCIPLES.md: an agent with only this repo never sees the principles

## Files on kitchen/init

- written          bin/check
   does: The one check contract: tiers commit, integrate, nightly and verify-tree, filled from the manifests; `--list` prints them.
   would block today: every commit that is not docs-only, today: bin/check commit exit 1 at 32e7dfd
- written          .agents/skills/verify-agent-skills/SKILL.md
- written          .agents/skills/verify-agent-skills/features/README.md
   does: Skeleton of the project's verify skill from templates/verify: placeholders to fill, no bin/verify yet.
   would block today: nothing: a skeleton
- written          .kitchen/baseline.json
   does: What --check measured, in measure-only mode: no gate reads it yet.
   would block today: nothing: measure-only
- written          .kitchen/hooks/deny-no-verify
- written          .kitchen/hooks/deny-recursive-rm
- written          .kitchen/hooks/deny-shared-push
- written          .kitchen/hooks/shellparse.py
- written          .claude/settings.json
   does: The kitchen's agent guards, copied into the repo so teammates and cloud sessions run them without installing the kitchen; .claude/settings.json runs each one before every Bash command in Claude Code.
   would block today: agent commands that push to a shared branch, skip the repo's hooks, or rm -r outside the temp dir, in Claude Code sessions started at the repo root
- written          .kitchen/PRINCIPLES.md
   does: The kitchen's PRINCIPLES.md, so an agent with only this repo (a teammate, a cloud session) knows what we do and why.
   would block today: nothing: agents read it once AGENTS.md or CLAUDE.md names it

## Proposals (not written: yours to apply)

1. secret-scan: add `gitleaks git --pre-commit --staged` to .githooks/pre-commit, failing when gitleaks is missing
2. agents-md: AGENTS.md has 22 lines but names no verify command (a verify-<repo> skill, bin/check or bin/verify). Name the verify command in AGENTS.md (the verify-<repo> skill or bin/check).
3. skills-linked: link the project skills in each clone: mkdir -p .claude/skills && ln -s ../../.agents/skills/verify-agent-skills .claude/skills/verify-agent-skills
4. principles: add this line to AGENTS.md (kitchen writes no prose there): Principles: `.kitchen/PRINCIPLES.md` says what we do and why. When no rule here settles a decision, read it and decide the way it points.

## Unverified

- bin/check integrate, nightly and verify-tree: never run by kitchen init
- verify-agent-skills is a skeleton: placeholders, no bin/verify, no feature mapped; it proves nothing yet
- .kitchen/hooks: Claude Code loads .claude/settings.json only in a session started at the repo root (measured)
- Codex gets no project hooks from this branch: project hooks did not load in Codex 0.160 when measured; a Codex session has the guards only where `kitchen install` ran
- .kitchen/baseline.json is measure-only: no gate compares against it
- --check only reads lint configs and manifests; it never ran a linter, a build or a test

## Readiness

- files proposed              yes: 10 files on kitchen/init
- checks run green            no: bin/check commit exit 1 at 32e7dfd
- negative control went red   not run: bin/check commit is not green and stable before the control, so a red control would prove nothing
- unattended-ready            not assessed: kitchen init does not assess unattended runs (sandbox, schedule, credentials)

## Trust per piece

- untrusted    bin/check: bin/check commit exit 1 at 32e7dfd
- untrusted    .agents/skills/verify-agent-skills/SKILL.md: a skeleton: nothing to run until bin/verify exists and its own negative control goes red
- measure-only .kitchen/baseline.json: not a gate, so there is nothing to prove

## One-way doors: owner decisions, printed and never executed

1. Ruleset on the default branch: block deletion and force-push, require a pull request. Recommended: yes.

   ```sh
   gh api -X POST repos/SantanaJcp/agent-skills/rulesets --input - <<'JSON'
   {"name": "default branch", "target": "branch", "enforcement": "active", "conditions": {"ref_name": {"include": ["~DEFAULT_BRANCH"], "exclude": []}}, "rules": [{"type": "deletion"}, {"type": "non_fast_forward"}, {"type": "pull_request", "parameters": {"required_approving_review_count": 0, "dismiss_stale_reviews_on_push": false, "require_code_owner_review": false, "require_last_push_approval": false, "required_review_thread_resolution": false}}]}
   JSON
   ```

2. Required status check on that ruleset: a CI job named `check` that runs `bin/check integrate`. Recommended: yes, once that CI job has run green, so the rule never blocks every merge.

   ```sh
   gh api repos/SantanaJcp/agent-skills/rulesets   # the id of the ruleset from the decision above
   gh api -X PUT repos/SantanaJcp/agent-skills/rulesets/RULESET_ID --input - <<'JSON'
   {"name": "default branch", "target": "branch", "enforcement": "active", "conditions": {"ref_name": {"include": ["~DEFAULT_BRANCH"], "exclude": []}}, "rules": [{"type": "deletion"}, {"type": "non_fast_forward"}, {"type": "pull_request", "parameters": {"required_approving_review_count": 0, "dismiss_stale_reviews_on_push": false, "require_code_owner_review": false, "require_last_push_approval": false, "required_review_thread_resolution": false}}, {"type": "required_status_checks", "parameters": {"strict_required_status_checks_policy": false, "required_status_checks": [{"context": "check"}]}}]}
   JSON
   ```

3. Schedule the nightly tier on a host with the kitchen's automation. Recommended: yes, once `bin/check nightly` is green by hand.

   ```sh
   # in ~/.config/kitchen/automation/agent-skills.env: GUARD_STEPS=("check|bin/check nightly")
   automation/bin/install-schedule agent-skills   # from the kitchen checkout
   ```

4. Credentials for unattended pushes (the gardener): a fine-grained token limited to this repo. Recommended: not yet: unattended-ready is not assessed.

   ```sh
   # create it at https://github.com/settings/personal-access-tokens/new: repository SantanaJcp/agent-skills, Contents and Pull requests read and write; keep it on the host, never in the repo
   ```


## Next (two-way, yours)

- review the branch (`git diff HEAD...kitchen/init`), then push it yourself: `git push -u origin kitchen/init`
