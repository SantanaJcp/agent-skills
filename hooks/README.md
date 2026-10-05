# Agent hooks

One script per guard. Claude Code and Codex run each one before every Bash command (`PreToolUse`): the script reads the tool call as JSON on stdin, exits 0 to allow it, or exits 2 with a message on stderr that tells the agent what to do instead.

`bin/kitchen install` adds them to `~/.claude/settings.json` and `~/.codex/hooks.json`, keeping the hooks already there. `bin/kitchen doctor` proves each one is installed and blocks a probe command.

`shellparse.py` is shared: it turns the command string into the commands it would run. Every guard has positive, negative, bypass and known-limit cases in `tests/corpus/hooks/cases.json`; a new guard or a newly found evasion starts there.

Try one by hand:

```bash
echo '{"tool_name":"Bash","cwd":"/srv","tool_input":{"command":"git push origin dev"}}' | hooks/deny-shared-push; echo "exit $?"
```
