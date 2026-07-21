# Testing

## Highest acceptance seam

```bash
npm run check
```

This command runs behavior-focused tests, JavaScript typechecking, strict repository validation, catalog freshness checks, and isolated skills CLI discovery/install tests. CI invokes the same command on Linux and Windows.

Good tests exercise public commands and observable files rather than private helpers. Expected results must come from the repository contract and worked examples, not by reproducing implementation logic inside assertions.

## Smoke definitions

Each skill has a YAML smoke definition containing at least one `trigger` and one `non-trigger` case. Each case records a prompt and expected behavior. Stable cases cannot contain placeholders.

## Promotion evidence

Public CI does not call paid models or receive model credentials. A promotion pull request records manual execution of the committed smoke cases in current stable Codex and Claude Code, including:

- exact client versions;
- whether each trigger activated the skill;
- whether each non-trigger remained inactive;
- observed result compared with the expected behavior;
- confirmation that optional sidecars were not required.

## Focused commands

```bash
npm test
npm run typecheck
npm run validate
npm run catalog:check
npm run test:install
```

Run focused tests while developing and the full acceptance seam once at the end.
