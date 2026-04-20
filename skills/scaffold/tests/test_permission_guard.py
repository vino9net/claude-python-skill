"""Tests for permission_guard.py hook.

Runs the hook as a subprocess, feeding JSON payloads via stdin and
asserting on stdout output and exit code.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

SCRIPT = str(
    Path(__file__).resolve().parent.parent
    / "assets"
    / "templates"
    / "permission_guard.py"
)
FIXTURES_DIR = Path(__file__).resolve().parent / "fixtures"


def _make_payload(command: str, cwd: str = "") -> str:
    payload: dict = {"tool_input": {"command": command}}
    if cwd:
        payload["cwd"] = cwd
    return json.dumps(payload)


def _load_fixture(name: str) -> str:
    return (FIXTURES_DIR / name).read_text()


def _run_hook(
    stdin_text: str, extra_env: dict[str, str] | None = None
) -> subprocess.CompletedProcess[str]:
    env = {k: v for k, v in os.environ.items() if k != "CLAUDE_HOOK_LOG"}
    if extra_env:
        env.update(extra_env)
    return subprocess.run(
        [sys.executable, SCRIPT],
        input=stdin_text,
        capture_output=True,
        text=True,
        timeout=10,
        env=env,
    )


def _decision(stdout: str) -> dict:
    return json.loads(stdout)["hookSpecificOutput"]["decision"]


# --- Fixtures ---------------------------------------------------------------


def _init_repo(path: Path, branch: str = "main") -> None:
    """Create a minimal git repo on the given branch."""
    path.mkdir(parents=True, exist_ok=True)
    subprocess.run(
        ["git", "init", "-b", branch], cwd=path, capture_output=True
    )
    subprocess.run(
        ["git", "config", "user.email", "test@test.com"],
        cwd=path,
        capture_output=True,
    )
    subprocess.run(
        ["git", "config", "user.name", "Test"],
        cwd=path,
        capture_output=True,
    )
    subprocess.run(
        ["git", "commit", "--allow-empty", "-m", "init"],
        cwd=path,
        capture_output=True,
    )


@pytest.fixture(scope="module")
def feature_repo(tmp_path_factory: pytest.TempPathFactory) -> str:
    repo = tmp_path_factory.mktemp("feat")
    _init_repo(repo, branch="main")
    subprocess.run(
        ["git", "checkout", "-b", "feature-x"],
        cwd=repo,
        capture_output=True,
    )
    return str(repo)


@pytest.fixture(scope="module")
def main_repo(tmp_path_factory: pytest.TempPathFactory) -> str:
    repo = tmp_path_factory.mktemp("mainrepo")
    _init_repo(repo, branch="main")
    return str(repo)


@pytest.fixture(scope="module")
def master_repo(tmp_path_factory: pytest.TempPathFactory) -> str:
    repo = tmp_path_factory.mktemp("masterrepo")
    _init_repo(repo, branch="master")
    return str(repo)


@pytest.fixture(scope="module")
def cwd_dir(tmp_path_factory: pytest.TempPathFactory) -> str:
    """Plain temp dir (not a git repo) for git -C passthrough tests."""
    return str(tmp_path_factory.mktemp("ccwd").resolve())


# --- Heredoc / python -c auto-allow ----------------------------------------


@pytest.mark.parametrize(
    "command",
    [
        "python <<< 'print(1)'",
        "python3 <<< 'print(1)'",
        "uv run python <<< 'print(1)'",
        "uv run python3 <<< 'import sys'",
        "python << 'EOF'\nprint(1)\nEOF",
        "python3 << 'PYEOF'\nprint(1)\nPYEOF",
        "uv run python3 << 'EOF'\nimport sys\nEOF",
        "   python3 << 'PYEOF'\nprint(1)\nPYEOF",
    ],
)
def test_heredoc_allowed(command: str) -> None:
    r = _run_hook(_make_payload(command))
    assert r.returncode == 0
    assert _decision(r.stdout)["behavior"] == "allow"


def test_heredoc_fixture_allowed() -> None:
    r = _run_hook(_load_fixture("heredoc_allow.json"))
    assert _decision(r.stdout)["behavior"] == "allow"


# --- git push to protected branches → deny ---------------------------------


@pytest.mark.parametrize(
    ("command", "expected_branch"),
    [
        ("git push origin main", "main"),
        ("git push origin master", "master"),
        ("git push origin feature:main", "main"),
        ("git push origin dev:master", "master"),
        ("git push --force origin main", "main"),
        ("git push -u origin main", "main"),
        ("git -C /tmp/repo push origin main", "main"),
        ("git add . && git push origin main", "main"),
        ("git push -o ci.skip origin main", "main"),
        ("git push --no-verify origin main", "main"),
    ],
)
def test_push_to_protected_denied(command: str, expected_branch: str) -> None:
    d = _decision(_run_hook(_make_payload(command)).stdout)
    assert d["behavior"] == "deny"
    assert expected_branch in d["message"]


def test_push_fixture_denied() -> None:
    d = _decision(_run_hook(_load_fixture("push_main_deny.json")).stdout)
    assert d["behavior"] == "deny"


# --- git push to non-protected branches → allow (via safe git pattern) -----


@pytest.mark.parametrize(
    "command",
    [
        "git push origin feature-branch",
        "git push -u origin feature-branch",
        "git push origin main:staging",
    ],
)
def test_push_to_feature_allowed(command: str) -> None:
    assert _decision(_run_hook(_make_payload(command)).stdout)["behavior"] == "allow"


def test_push_feature_fixture_allowed() -> None:
    r = _run_hook(_load_fixture("push_feature_pass.json"))
    assert _decision(r.stdout)["behavior"] == "allow"


# --- Safe commands → allow --------------------------------------------------


@pytest.mark.parametrize("command", ["ls -la", "ruff format ."])
def test_safe_command_allowed(command: str) -> None:
    r = _run_hook(_make_payload(command))
    assert r.returncode == 0
    assert _decision(r.stdout)["behavior"] == "allow"


def test_ls_fixture_allowed() -> None:
    r = _run_hook(_load_fixture("ls_passthrough.json"))
    assert _decision(r.stdout)["behavior"] == "allow"


# --- Malformed input → passthrough (no output) -----------------------------


@pytest.mark.parametrize("stdin_text", ["not json at all", ""])
def test_malformed_input_passthrough(stdin_text: str) -> None:
    r = _run_hook(stdin_text)
    assert r.returncode == 0
    assert r.stdout == ""


# --- SKIP_CLAUDE_HOOKS=1 bypasses everything -------------------------------


@pytest.mark.parametrize(
    "command",
    [
        "python3 <<< 'print(1)'",
        "git push origin main",
        "git commit -m 'fix'",
    ],
)
def test_skip_claude_hooks_bypasses_all(command: str) -> None:
    r = _run_hook(_make_payload(command), extra_env={"SKIP_CLAUDE_HOOKS": "1"})
    assert r.returncode == 0
    assert r.stdout == ""


# --- git commit branch-aware guard -----------------------------------------


def test_commit_on_feature_allowed(feature_repo: str) -> None:
    r = _run_hook(_make_payload("git commit -m 'fix bug'", cwd=feature_repo))
    assert r.returncode == 0
    assert _decision(r.stdout)["behavior"] == "allow"


def test_commit_amend_on_feature_allowed(feature_repo: str) -> None:
    r = _run_hook(
        _make_payload("git commit --amend --no-edit", cwd=feature_repo)
    )
    assert _decision(r.stdout)["behavior"] == "allow"


def test_commit_on_main_passthrough(main_repo: str) -> None:
    r = _run_hook(_make_payload("git commit -m 'fix'", cwd=main_repo))
    assert r.returncode == 0
    assert r.stdout == ""


def test_commit_on_master_passthrough(master_repo: str) -> None:
    r = _run_hook(_make_payload("git commit -m 'fix'", cwd=master_repo))
    assert r.returncode == 0
    assert r.stdout == ""


def test_commit_with_C_flag_feature_allowed(feature_repo: str) -> None:
    r = _run_hook(_make_payload(f"git -C {feature_repo} commit -m 'fix'"))
    assert _decision(r.stdout)["behavior"] == "allow"


def test_commit_with_C_flag_main_passthrough(main_repo: str) -> None:
    r = _run_hook(_make_payload(f"git -C {main_repo} commit -m 'fix'"))
    assert r.stdout == ""


# --- Any git subcommand is auto-allowed (push/commit guards take priority) -


@pytest.mark.parametrize(
    "subcommand",
    [
        "status",
        "add .",
        "diff",
        "log --oneline",
        "show HEAD",
        "branch -a",
        "checkout main",
    ],
)
def test_git_subcommand_allowed(cwd_dir: str, subcommand: str) -> None:
    r = _run_hook(_make_payload(f"git -C {cwd_dir} {subcommand}", cwd=cwd_dir))
    assert _decision(r.stdout)["behavior"] == "allow"


def test_chained_safe_commands_allowed(cwd_dir: str) -> None:
    r = _run_hook(
        _make_payload(
            f"git -C {cwd_dir} add . && git -C {cwd_dir} status",
            cwd=cwd_dir,
        )
    )
    assert _decision(r.stdout)["behavior"] == "allow"


def test_different_dir_allowed(
    cwd_dir: str, tmp_path: Path
) -> None:
    other = str(tmp_path.resolve())
    r = _run_hook(_make_payload(f"git -C {other} status", cwd=cwd_dir))
    assert _decision(r.stdout)["behavior"] == "allow"


def test_no_cwd_in_payload_allowed(cwd_dir: str) -> None:
    r = _run_hook(_make_payload(f"git -C {cwd_dir} status"))
    assert _decision(r.stdout)["behavior"] == "allow"


def test_plain_git_status_allowed(cwd_dir: str) -> None:
    r = _run_hook(_make_payload("git status", cwd=cwd_dir))
    assert _decision(r.stdout)["behavior"] == "allow"
