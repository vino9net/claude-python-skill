---
name: permission-review
description: >
  Review the permission_guard.py hook log (path from $CLAUDE_HOOK_LOG)
  to find Bash commands that triggered permission prompts over a time
  window, then recommend updates to .claude/settings.json,
  .claude/settings.local.json, and .claude/scripts/permission_guard.py
  that would reduce future prompts. Triggers: "review permissions",
  "permission audit", "which commands keep prompting me",
  "/permission-review".
allowed-tools: Bash(python3:*), Bash(uv run python:*), Read, Grep
---

# Permission Review

Analyze the permission_guard.py log to find which Bash commands
triggered user prompts over a time window, then recommend changes
that eliminate recurring prompts without loosening real guards.

## Usage

```
/permission-review [days]
```

- `days` — lookback window in days. **Default: 2.**

## Preconditions

1. `CLAUDE_HOOK_LOG` must be set for entries to exist. Resolve it
   the same way `permission_guard.py` does:
   - absolute path → use as-is
   - starts with `~` → expand
   - relative → join against `$CLAUDE_PROJECT_DIR`, falling back to
     `$PWD`

2. If the log file does not exist or has no `permission_guard`
   entries in the window, stop and tell the user what to set (and
   that logging only started from whenever the env var was first
   defined).

## Workflow

### Step 1 — Load and filter

Read the log as JSONL and keep entries where **both**:

- `hook == "permission_guard"` (the log also contains
  `format_on_save` entries — skip those)
- `timestamp >= now - days` (ISO 8601 UTC; use
  `datetime.fromisoformat`)

Bucket each kept entry by the `decision` string's prefix:

| Decision prefix | Meaning |
|---|---|
| `allow:*` | Hook auto-granted. No prompt shown. |
| `deny:*` | Hook blocked. No prompt shown. |
| `passthrough` | **User was prompted** (unless a settings.json `allow` entry matched). This is the review target. |
| `passthrough:commit-on-<branch>` | Intentional safety prompt for commits on protected branches. Do **not** recommend auto-allowing these. |

### Step 2 — Summarize

Report totals:

```
Window: last 2 days (2026-04-18 → 2026-04-20)
Entries: 342 permission_guard decisions
  allow:        298
  deny:           4
  passthrough:   40  ← focus
```

For the passthrough bucket, group commands by a **normalized
prefix** and show the top ~15:

- Normalize: take the first token, or the first two if the first is
  in `{uv, git, gh, npm, npx, docker, kubectl, gcloud, aws, cargo, go}`.
- For each group, print count + up to 3 representative full commands
  so the user can see actual usage.

Call out separately:
- `passthrough:commit-on-<branch>` entries (safety-by-design — show
  count, no recommendation).
- Any passthrough whose command the current project's settings.json
  `allow` list would already match — those indicate a logging lag,
  not a missing allow rule.

### Step 3 — Cross-check settings.json

Read `$CLAUDE_PROJECT_DIR/.claude/settings.json` and
`.claude/settings.local.json` (if present). Parse the
`permissions.allow` array from each.

For each top passthrough group:

- Test whether any existing `Bash(<prefix>:*)` entry covers the
  command's prefix (best-effort prefix match; don't reimplement the
  harness's full matcher — flag ambiguous cases).
- If **not covered**, recommend a new entry.

Split recommendations into two lists:

- **`.claude/settings.json`** — team-safe patterns (e.g. `gh pr:*`,
  `make:*`, `docker build:*`).
- **`.claude/settings.local.json`** — user/machine-specific patterns
  (absolute paths, secrets-adjacent commands, anything with `$HOME`
  or usernames).

Present as a diff-style block; do NOT edit the files:

```
.claude/settings.json — proposed additions to permissions.allow:
  + "Bash(gh pr:*)"          # 12 prompts
  + "Bash(make:*)"           #  6 prompts

.claude/settings.local.json — proposed additions:
  + "Bash(/Users/.../mytool:*)"   # 4 prompts
```

### Step 4 — Recommend permission_guard.py changes

Read `.claude/scripts/permission_guard.py` and inspect
`SAFE_COMMAND_PATTERNS`. For each top passthrough group, decide:

- **Add a safe pattern** when the command is broadly safe (read-only
  or idempotent tooling), and a single regex covers many variants
  better than listing them one-by-one in settings.json.
- **Do NOT add a pattern** when the command has a dangerous mode
  (e.g. `terraform apply`, `kubectl delete`, `rm -rf`). Instead,
  suggest a narrower regex that excludes the dangerous subcommand,
  or leave it as a prompt.
- **Propose a new guard** (similar to the existing push/commit
  guards) when a command is usually safe but has specific unsafe
  invocations worth blocking — e.g. `kubectl delete` on prod
  contexts.

Present the recommendation as a code block showing exactly which
lines to add:

```python
# Add to SAFE_COMMAND_PATTERNS in permission_guard.py:
r"^make\b",
r"^terraform (plan|validate|fmt|show|output)\b",  # 'apply/destroy' excluded
```

### Step 5 — Bottom line

One short paragraph:

- Total prompts in window.
- How many would be eliminated if all recommendations are accepted.
- Any passthroughs that should **stay** as prompts and why.

## Notes

- **Do not edit files.** Only recommend. The user decides what to
  apply.
- Log entries may span multiple projects (each record's
  `request.cwd` tells you which). If more than one project appears,
  note it — the settings.json you're reading applies only to the
  current project. Offer to filter by `cwd == $CLAUDE_PROJECT_DIR`
  if the user wants project-scoped analysis.
- For large logs, stream line-by-line rather than loading the whole
  file into memory.
- `passthrough:commit-on-main` / `commit-on-master` are intentional
  — flag them so the user can see the count, but never recommend
  auto-allowing commits on protected branches.
