#!/usr/bin/env -S uv run
# /// script
# requires-python = ">=3.10"
# dependencies = [
#     "bashlex",
# ]
# ///
"""PermissionRequest hook: auto-grant safe commands, block pushes to protected branches.

This is a PEP 723 inline-script that depends on ``bashlex``. It is invoked
via ``uv run`` so the dependency is resolved automatically.

Claude Code calls this script on every Bash tool permission request.
It reads a JSON payload from stdin and prints a JSON decision to stdout:

    allow       — skip the permission prompt
    deny        — block the call (with a message)
    (no output) — fall through to normal permission flow (passthrough)

Decision flow
-------------
1. Python heredoc / ``python -c``?  → **allow**
2. ``git push`` to main/master?     → **deny**
3. ``git commit`` on main/master?   → **passthrough** (prompt the user)
4. Parse the command with bashlex and walk the AST. If *every* simple
   command matches a safe-command pattern → **allow**
5. Otherwise → **passthrough**

Safe command matching
---------------------
The SAFE_COMMAND_PATTERNS list (regex) near the top of this file defines
which commands are auto-allowed. Patterns are matched against the command
text starting from the first word of each simple-command node in the AST,
so multi-word prefixes like ``uv run`` work naturally.

Bash constructs (pipelines, ``&&``/``||`` chains, ``for``/``while`` loops,
if/case, subshells) are handled by recursively walking the bashlex AST —
the hook only auto-allows if **all** commands within the construct are safe.

Commands intentionally kept as passthrough (prompt the user):
    rm, rmdir, pkill, kill

Preprocessing
-------------
Before parsing, the script strips ``#!/bin/bash`` shebangs and replaces
heredoc bodies (``<< 'EOF' ... EOF``) with a placeholder so that bashlex
can parse the surrounding command structure.

Logging
-------
Set ``CLAUDE_HOOK_LOG`` to a file path to log every decision as JSONL.
Set ``SKIP_CLAUDE_HOOKS=1`` to disable the hook entirely.
"""

from __future__ import annotations

import json
import os
import re
import shlex
import shutil
import subprocess
import sys
from datetime import UTC, datetime

import bashlex

GIT_BIN = shutil.which("git") or "git"

# ---------------------------------------------------------------------------
# Safe command patterns (regex matched against command text from first word)
# ---------------------------------------------------------------------------
# Each pattern is matched against the command text starting from the first
# non-assignment word in a simple command. Use ^ to anchor.
#
# NOTE: "uv run" and "uv pip" are safe, but not "uv" by itself.
# Git commands are handled separately by the push/commit guards,
# so we allow all git subcommands here — guards take priority.
SAFE_COMMAND_PATTERNS: list[re.Pattern[str]] = [
    re.compile(p)
    for p in [
        # Python / project tooling
        r"^(\S+/)?python3?\b",  # python3, .venv/bin/python3, /usr/bin/python, etc.
        r"^uv (run|pip|sync|add|remove|tree|lock|venv|--version)\b",
        r"^pytest\b",
        r"^ruff\b",
        r"^ty\b",
        # File operations (read-oriented)
        r"^ls\b",
        r"^find\b",
        r"^cat\b",
        r"^head\b",
        r"^tail\b",
        r"^wc\b",
        r"^sort\b",
        r"^uniq\b",
        r"^diff\b",
        r"^grep\b",
        r"^rg\b",
        r"^sed\b",
        r"^awk\b",
        r"^jq\b",
        r"^cut\b",
        r"^tr\b",
        r"^tee\b",
        r"^xargs\b",
        # File operations (write)
        r"^mkdir\b",
        r"^touch\b",
        r"^cp\b",
        r"^mv\b",
        r"^chmod\b",
        r"^tar\b",
        r"^zip\b",
        r"^unzip\b",
        r"^gunzip\b",
        # Shell builtins / control
        r"^echo\b",
        r"^printf\b",
        r"^cd\b",
        r"^pwd\b",
        r"^export\b",
        r"^source\b",
        r"^\.\s",  # . script.sh (source shorthand)
        r"^set\b",
        r"^true$",
        r"^false$",
        r"^test\b",
        r"^\[$",  # [ test expression ]
        r"^sleep\b",
        r"^date\b",
        r"^read\b",
        # Git (push/commit handled by dedicated guards before this)
        r"^git\b",
        # Cloud / dev tools
        r"^gcloud\b",
        r"^gsutil\b",
        r"^gh\b",
        r"^docker\b",
        r"^ssh\b",
        r"^scp\b",
        r"^rsync\b",
        r"^curl\b",
        r"^wget\b",
        r"^aws\b",
        r"^npm\b",
        r"^npx\b",
        r"^pip\b",
        # System / process inspection
        r"^ps\b",
        r"^du\b",
        r"^which\b",
        r"^lsof\b",
        r"^seq\b",
        r"^wait\b",
        r"^paste\b",
        r"^comm\b",
        r"^pstree\b",
        r"^sqlite3\b",
        r"^bash\b",
        r"^sh\b",
        # rm is intentionally NOT here — keep prompting for deletes
    ]
]

HEREDOC_PATTERN = re.compile(r"^(uv run )?(python3?)\s+<<<?")
PYTHON_INLINE_PATTERN = re.compile(r"^(uv run )?(python3?)\s+-c\s+")

GIT_PUSH_PATTERN = re.compile(r"\bgit\b.*\bpush\b")
GIT_COMMIT_PATTERN = re.compile(r"\bgit\b.*\bcommit\b")
PROTECTED_BRANCH_RE = re.compile(r"^(main|master)$")

GIT_PUSH_FLAGS_WITH_VALUE = {
    "--push-option",
    "--repo",
    "--receive-pack",
    "--exec",
    "-o",
    "--recurse-submodules",
}

GIT_PUSH_FLAGS_STANDALONE = {
    "-u",
    "--set-upstream",
    "-f",
    "--force",
    "--force-with-lease",
    "--no-verify",
    "--tags",
    "--all",
    "--mirror",
    "--delete",
    "--dry-run",
    "-n",
    "--verbose",
    "-v",
    "--quiet",
    "-q",
    "--prune",
    "--porcelain",
    "--no-thin",
    "--thin",
    "--follow-tags",
    "--signed",
    "--no-signed",
    "--atomic",
    "--progress",
    "--no-progress",
    "--force-if-includes",
}


def _resolve_log_path() -> str | None:
    path = os.environ.get("CLAUDE_HOOK_LOG")
    if not path:
        return None
    if path.startswith("~"):
        return os.path.expanduser(path)
    if not os.path.isabs(path):
        root = os.environ.get("CLAUDE_PROJECT_DIR", os.getcwd())
        return os.path.join(root, path)
    return path


def log(payload: dict, decision: str) -> None:
    log_file = _resolve_log_path()
    if not log_file:
        return
    os.makedirs(os.path.dirname(log_file), exist_ok=True)
    timestamp = datetime.now(UTC).isoformat()
    entry = {
        "timestamp": timestamp,
        "hook": "permission_guard",
        "request": payload,
        "decision": decision,
    }
    with open(log_file, "a") as f:
        f.write(json.dumps(entry) + "\n")


def _emit(behavior: str, message: str = "") -> None:
    decision: dict = {"behavior": behavior}
    if message:
        decision["message"] = message
    json.dump(
        {
            "hookSpecificOutput": {
                "hookEventName": "PermissionRequest",
                "decision": decision,
            }
        },
        sys.stdout,
    )


def _git_current_branch(cwd: str | None) -> str | None:
    """Return the current git branch via ``git rev-parse``."""
    try:
        # All argv entries are static constants; only `cwd` is variable
        # and is not interpreted by a shell. Safe by construction.
        result = subprocess.run(  # noqa: S603
            [GIT_BIN, "rev-parse", "--abbrev-ref", "HEAD"],
            capture_output=True,
            text=True,
            cwd=cwd,
            timeout=5,
        )
        if result.returncode == 0:
            return result.stdout.strip()
    except (OSError, subprocess.TimeoutExpired):
        pass
    return None


def _find_git_push(tokens: list[str]) -> tuple[int, str | None] | None:
    """Locate ``push`` after ``git``, returning (push_idx, cwd-from-``-C``)."""
    try:
        git_idx = tokens.index("git")
    except ValueError:
        return None

    cwd: str | None = None
    j = git_idx + 1
    while j < len(tokens):
        if tokens[j] == "-C" and j + 1 < len(tokens):
            cwd = tokens[j + 1]
            j += 2
            continue
        if tokens[j] == "push":
            return j, cwd
        j += 1
    return None


def _parse_push_positionals(tokens: list[str], push_idx: int) -> list[str]:
    """Return positional arguments after ``git push``, skipping flags."""
    positional: list[str] = []
    k = push_idx + 1
    while k < len(tokens):
        tok = tokens[k]
        if tok in GIT_PUSH_FLAGS_WITH_VALUE:
            k += 2
            continue
        if tok in GIT_PUSH_FLAGS_STANDALONE or (tok.startswith("-") and "=" in tok):
            k += 1
            continue
        if tok in ("&&", "||", ";", "|"):
            break
        positional.append(tok)
        k += 1
    return positional


def _resolve_push_branch(command: str) -> str | None:
    """Parse a git push command and return the target branch name."""
    try:
        tokens = shlex.split(command)
    except ValueError:
        return None

    found = _find_git_push(tokens)
    if found is None:
        return None
    push_idx, cwd = found

    positional = _parse_push_positionals(tokens, push_idx)
    if len(positional) >= 2:
        refspec = positional[1]
        if ":" in refspec:
            return refspec.rsplit(":", 1)[1]
        return refspec

    return _git_current_branch(cwd)


def _current_branch(command: str, cwd: str) -> str | None:
    """Resolve the current git branch for a command."""
    work_dir = cwd or None
    try:
        tokens = shlex.split(command)
    except ValueError:
        tokens = []
    for i, tok in enumerate(tokens):
        if tok == "-C" and i + 1 < len(tokens):
            work_dir = tokens[i + 1]
            break
    return _git_current_branch(work_dir)


# ---------------------------------------------------------------------------
# bashlex-based safe command checker
# ---------------------------------------------------------------------------


def _is_safe_command(cmd_text: str) -> bool:
    """Check if command text matches any safe command pattern."""
    for pattern in SAFE_COMMAND_PATTERNS:
        if pattern.search(cmd_text):
            return True
    return False


def _check_node_safe(node: object, command: str) -> bool:
    """Recursively check if a node and all its children are safe."""
    kind = node.kind  # type: ignore[attr-defined]

    if kind == "command":
        parts = node.parts  # type: ignore[attr-defined]
        # Find the first non-assignment word — that's the command name
        for part in parts:
            if part.kind == "word":  # type: ignore[attr-defined]
                word_val = part.word  # type: ignore[attr-defined]
                if "=" in word_val and not word_val.startswith("-"):
                    continue  # skip VAR=val
                # Get command text from original string starting at this
                # word's position for multi-word pattern matching
                pos = part.pos  # type: ignore[attr-defined]
                start = pos[0] if isinstance(pos, tuple) else pos
                cmd_text = command[start:]
                return _is_safe_command(cmd_text)
        # Pure assignments only (e.g. FOO=bar) — safe
        return True

    if kind == "pipeline":
        return all(
            _check_node_safe(p, command)
            for p in node.parts  # type: ignore[attr-defined]
        )

    if kind == "list":
        return all(
            _check_node_safe(p, command)
            for p in node.parts  # type: ignore[attr-defined]
            if hasattr(p, "kind")
        )

    if kind == "compound":
        # for/while/until/if/case — check body and clauses
        # Also recurse into parts for nested structures
        for attr in ("list", "clauses", "parts"):
            body = getattr(node, attr, None)
            if body:
                for part in body:
                    if hasattr(part, "kind"):
                        if not _check_node_safe(part, command):
                            return False
        return True

    # Structural/leaf nodes that are not commands themselves:
    # operator (&&, ||, ;), pipe (|), word, assignment, redirect,
    # reservedword (for/do/done/if/then/fi), for, while, until,
    # if, commandsubstitution, parameter, processsubstitution
    if kind in (
        "operator",
        "pipe",
        "word",
        "assignment",
        "redirect",
        "reservedword",
        "for",
        "while",
        "until",
        "if",
        "commandsubstitution",
        "processsubstitution",
        "parameter",
        "tilde",
        "heredoc",
    ):
        return True

    # Unknown node kind — passthrough
    return False


HEREDOC_STRIP_RE = re.compile(
    r"<<-?\s*['\"]?(\w+)['\"]?\n.*?\n\1",
    re.DOTALL,
)
SHEBANG_RE = re.compile(r"^#![^\n]*\n")


def _preprocess_for_parsing(command: str) -> str:
    """Preprocess command to work around bashlex limitations.

    - Strip shebang lines (#!/bin/bash)
    - Replace heredoc bodies with a placeholder so bashlex doesn't
      choke on the content. The command before the heredoc is what
      we actually need to check.
    """
    result = command
    # Strip shebang
    result = SHEBANG_RE.sub("", result)
    # Replace heredoc bodies: keep the command part, replace the body
    # with a simple string so the command structure is preserved
    result = HEREDOC_STRIP_RE.sub("'HEREDOC_PLACEHOLDER'", result)
    return result


def _all_commands_safe(command: str) -> bool:
    """Parse command with bashlex and check if all commands are safe.

    Returns True only if every simple command in the parsed AST matches
    a safe command pattern. Returns False on parse errors or
    unrecognized constructs.
    """
    preprocessed = _preprocess_for_parsing(command)
    try:
        parts = bashlex.parse(preprocessed)
    except (bashlex.errors.ParsingError, NotImplementedError):
        return False

    # Use preprocessed for AST but original-length-aware matching
    return all(_check_node_safe(node, preprocessed) for node in parts)


def main() -> None:
    if os.environ.get("SKIP_CLAUDE_HOOKS") == "1":
        return

    try:
        payload = json.load(sys.stdin)
    except (json.JSONDecodeError, EOFError):
        return

    tool_input = payload.get("tool_input", {})
    command = tool_input.get("command", "")
    cwd = payload.get("cwd", "")

    # 1. Auto-grant python heredocs and inline scripts
    stripped = command.strip()
    if HEREDOC_PATTERN.match(stripped) or PYTHON_INLINE_PATTERN.match(stripped):
        _emit("allow")
        log(payload, "allow:heredoc")
        return

    # 2. Guard git push to protected branches
    if GIT_PUSH_PATTERN.search(command):
        branch = _resolve_push_branch(command)
        if branch and PROTECTED_BRANCH_RE.match(branch):
            _emit(
                "deny",
                f"Push to protected branch '{branch}' is blocked. "
                "Merge via pull request instead.",
            )
            log(payload, f"deny:push-to-{branch}")
            return

    # 3. Guard git commit on protected branches
    if GIT_COMMIT_PATTERN.search(command):
        branch = _current_branch(command, cwd)
        if branch and PROTECTED_BRANCH_RE.match(branch):
            log(payload, f"passthrough:commit-on-{branch}")
            return  # ask the user
        _emit("allow")
        log(payload, "allow:commit")
        return

    # 4. Parse with bashlex — if all commands are safe, auto-allow
    if _all_commands_safe(command):
        _emit("allow")
        log(payload, "allow:safe-commands")
        return

    # 5. Everything else: passthrough
    log(payload, "passthrough")


if __name__ == "__main__":
    main()
