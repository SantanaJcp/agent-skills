"""`kitchen retro`: my own prompts from Claude Code and Codex transcripts, for the retro skill to read."""
from __future__ import annotations

import json
import re
from pathlib import Path

from .common import home, parse_ts

SECRET = re.compile(
    r"(sk-[A-Za-z0-9_-]{16,}|gh[pousr]_[A-Za-z0-9]{20,}|xox[abp]-[A-Za-z0-9-]{10,}|AKIA[0-9A-Z]{16}"
    r"|eyJ[A-Za-z0-9_-]{20,}\.[A-Za-z0-9_-]{10,}|(?i:(password|passwd|token|secret|api[_-]?key)\s*[=:]\s*)\S+)"
)
T3_CONTEXT = re.compile(r"<t3_context.*?</t3_context>", re.S)
NOT_HUMAN = (
    "<task-notification", "<command-name", "<local-command", "<system-reminder",
    "This session is being continued", "[Request interrupted",
    "Context handoff (",  # T3 Code injects these when it moves context between threads
)
DELEGATED = re.compile(r"^Act as the [\w -]+ sub-agent for this task\.")  # T3 Code wraps delegated tasks this way
CODEX_REQUEST = re.compile(r"## My request(?: for Codex)?:\s*\n(.*)", re.S)


def scrub(text: str) -> str:
    return SECRET.sub("[REDACTED]", text)


def claude_prompts(since) -> list[dict]:
    root = home() / ".claude" / "projects"
    prompts = []
    for transcript in sorted(root.glob("*/*.jsonl")):  # main sessions only; subagent transcripts live deeper
        if transcript.stat().st_mtime < since.timestamp():
            continue
        for line in transcript.open(encoding="utf-8", errors="replace"):
            try:
                event = json.loads(line)
            except json.JSONDecodeError:
                continue
            if event.get("type") != "user" or event.get("isMeta"):
                continue
            ts = parse_ts(event.get("timestamp") or "")
            if ts is None or ts < since:
                continue
            content = event.get("message", {}).get("content")
            if isinstance(content, list):
                if any(part.get("type") == "tool_result" for part in content):
                    continue
                texts = [part.get("text", "") for part in content if part.get("type") == "text"]
            else:
                texts = [content or ""]
            for raw in texts:
                text = T3_CONTEXT.sub("", raw).strip()
                if text and not text.startswith(NOT_HUMAN) and not DELEGATED.match(text):
                    prompts.append({"ts": ts.isoformat(timespec="seconds"), "tool": "claude", "project": event.get("cwd") or transcript.parent.name, "session": transcript.stem, "text": scrub(text)})
    return prompts


def codex_prompts(since) -> list[dict]:
    root = home() / ".codex"
    files = list((root / "sessions").glob("*/*/*/rollout-*.jsonl")) + list((root / "archived_sessions").glob("rollout-*.jsonl"))
    automation_prompts = []
    for manifest in (root / "automations").glob("*/automation.toml"):
        match = re.search(r'^prompt\s*=\s*"(.{20,80})', manifest.read_text(encoding="utf-8"), re.MULTILINE)
        if match:
            automation_prompts.append(match.group(1)[:60])
    prompts = []
    for rollout in sorted(files):
        if rollout.stat().st_mtime < since.timestamp():
            continue
        cwd = session = None
        human_session = True
        with rollout.open("rb") as handle:
            for raw in handle:
                head = raw[:300]
                if b'"type":"session_meta"' in head and session is None:
                    meta = json.loads(raw)["payload"]
                    cwd, session = meta.get("cwd"), meta.get("id")
                    human_session = isinstance(meta.get("source"), str)  # guardian and subagent sessions carry an object
                elif human_session and b'"item_completed"' in head and b'"UserMessage"' in raw[:700]:
                    event = json.loads(raw)
                    ts = parse_ts(event.get("timestamp") or "")
                    if ts is None or ts < since:
                        continue
                    item = event["payload"]["item"]
                    text = "\n".join(part.get("text", "") for part in item.get("content", []) if part.get("type") == "text")
                    request = CODEX_REQUEST.search(text)
                    text = (request.group(1) if request else text).strip()
                    if text and not DELEGATED.match(text) and not any(prompt in text for prompt in automation_prompts):
                        prompts.append({"ts": ts.isoformat(timespec="seconds"), "tool": "codex", "project": cwd, "session": session, "text": scrub(text)})
    return prompts


def collect(since, tool: str, pattern: str | None) -> list[dict]:
    found = []
    if tool in ("all", "claude"):
        found += claude_prompts(since)
    if tool in ("all", "codex"):
        found += codex_prompts(since)
    if pattern:
        regex = re.compile(pattern, re.IGNORECASE)
        found = [p for p in found if regex.search(p["text"])]
    return sorted(found, key=lambda p: p["ts"])


def render(prompts: list[dict], full: bool) -> str:
    lines = []
    for p in prompts:
        text = p["text"] if full else p["text"].replace("\n", " ⏎ ")[:300]
        project = Path(p["project"]).name if p["project"] else "?"
        lines.append(f"{p['ts'][:16]}  {p['tool']:<6} {project:<24} {text}")
    lines.append(f"{len(prompts)} prompts")
    return "\n".join(lines)
