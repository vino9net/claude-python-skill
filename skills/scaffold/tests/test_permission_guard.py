#!/usr/bin/env python3
"""Tests for permission_guard.py hook.

Runs the hook as a subprocess, feeding JSON payloads via stdin and asserting
on stdout output and exit code. No third-party dependencies required.
"""

import json
import os
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

SCRIPT = str(
    Path(__file__).resolve().parent.parent
    / "assets"
    / "templates"
    / "permission_guard.py"
)

# Prebuilt test fixtures --------------------------------------------------

FIXTURES_DIR = Path(__file__).resolve().parent / "fixtures"


def _make_payload(command: str, cwd: str = "") -> str:
    payload: dict = {"tool_input": {"command": command}}
    if cwd:
        payload["cwd"] = cwd
    return json.dumps(payload)


def _load_fixture(name: str) -> str:
    return (FIXTURES_DIR / name).read_text()


def _run_hook(stdin_text: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["python3", SCRIPT],
        input=stdin_text,
        capture_output=True,
        text=True,
        timeout=10,
        env={k: v for k, v in os.environ.items() if k != "CLAUDE_HOOK_LOG"},
    )


def _parse_decision(stdout: str) -> dict:
    data = json.loads(stdout)
    return data["hookSpecificOutput"]["decision"]


# -------------------------------------------------------------------------


class TestHeredocAllow(unittest.TestCase):
    """Python heredoc commands should be auto-allowed."""

    def test_python_heredoc(self):
        r = _run_hook(_make_payload("python <<< 'print(1)'"))
        self.assertEqual(r.returncode, 0)
        self.assertEqual(_parse_decision(r.stdout)["behavior"], "allow")

    def test_python3_heredoc(self):
        r = _run_hook(_make_payload("python3 <<< 'print(1)'"))
        self.assertEqual(_parse_decision(r.stdout)["behavior"], "allow")

    def test_uv_run_python_heredoc(self):
        r = _run_hook(_make_payload("uv run python <<< 'print(1)'"))
        self.assertEqual(_parse_decision(r.stdout)["behavior"], "allow")

    def test_uv_run_python3_heredoc(self):
        r = _run_hook(_make_payload("uv run python3 <<< 'import sys'"))
        self.assertEqual(_parse_decision(r.stdout)["behavior"], "allow")

    def test_python_heredoc_double_angle(self):
        r = _run_hook(_make_payload("python << 'EOF'\nprint(1)\nEOF"))
        self.assertEqual(_parse_decision(r.stdout)["behavior"], "allow")

    def test_python3_heredoc_double_angle(self):
        r = _run_hook(_make_payload("python3 << 'PYEOF'\nprint(1)\nPYEOF"))
        self.assertEqual(_parse_decision(r.stdout)["behavior"], "allow")

    def test_uv_run_python3_heredoc_double_angle(self):
        r = _run_hook(_make_payload("uv run python3 << 'EOF'\nimport sys\nEOF"))
        self.assertEqual(_parse_decision(r.stdout)["behavior"], "allow")

    def test_python3_heredoc_double_angle_leading_spaces(self):
        r = _run_hook(_make_payload("   python3 << 'PYEOF'\nprint(1)\nPYEOF"))
        self.assertEqual(_parse_decision(r.stdout)["behavior"], "allow")

    def test_fixture_heredoc(self):
        r = _run_hook(_load_fixture("heredoc_allow.json"))
        self.assertEqual(_parse_decision(r.stdout)["behavior"], "allow")


class TestGitPushDeny(unittest.TestCase):
    """Pushes to main/master should be denied."""

    def test_push_origin_main(self):
        r = _run_hook(_make_payload("git push origin main"))
        d = _parse_decision(r.stdout)
        self.assertEqual(d["behavior"], "deny")
        self.assertIn("main", d["message"])

    def test_push_origin_master(self):
        r = _run_hook(_make_payload("git push origin master"))
        d = _parse_decision(r.stdout)
        self.assertEqual(d["behavior"], "deny")
        self.assertIn("master", d["message"])

    def test_push_refspec_to_main(self):
        r = _run_hook(_make_payload("git push origin feature:main"))
        d = _parse_decision(r.stdout)
        self.assertEqual(d["behavior"], "deny")
        self.assertIn("main", d["message"])

    def test_push_refspec_to_master(self):
        r = _run_hook(_make_payload("git push origin dev:master"))
        d = _parse_decision(r.stdout)
        self.assertEqual(d["behavior"], "deny")

    def test_force_push_main(self):
        r = _run_hook(_make_payload("git push --force origin main"))
        d = _parse_decision(r.stdout)
        self.assertEqual(d["behavior"], "deny")

    def test_push_with_set_upstream_main(self):
        r = _run_hook(_make_payload("git push -u origin main"))
        d = _parse_decision(r.stdout)
        self.assertEqual(d["behavior"], "deny")

    def test_push_with_C_flag_main(self):
        r = _run_hook(_make_payload("git -C /tmp/repo push origin main"))
        d = _parse_decision(r.stdout)
        self.assertEqual(d["behavior"], "deny")

    def test_fixture_push_main(self):
        r = _run_hook(_load_fixture("push_main_deny.json"))
        d = _parse_decision(r.stdout)
        self.assertEqual(d["behavior"], "deny")


class TestGitPushPassthrough(unittest.TestCase):
    """Pushes to non-protected branches should passthrough (no output)."""

    def test_push_feature_branch(self):
        r = _run_hook(_make_payload("git push origin feature-branch"))
        self.assertEqual(r.returncode, 0)
        self.assertEqual(r.stdout, "")

    def test_push_with_set_upstream_feature(self):
        r = _run_hook(_make_payload("git push -u origin feature-branch"))
        self.assertEqual(r.stdout, "")

    def test_push_refspec_to_feature(self):
        r = _run_hook(_make_payload("git push origin main:staging"))
        self.assertEqual(r.stdout, "")

    def test_fixture_push_feature(self):
        r = _run_hook(_load_fixture("push_feature_pass.json"))
        self.assertEqual(r.stdout, "")


class TestPassthrough(unittest.TestCase):
    """Non-matching commands should passthrough (no output)."""

    def test_ls(self):
        r = _run_hook(_make_payload("ls -la"))
        self.assertEqual(r.returncode, 0)
        self.assertEqual(r.stdout, "")

    def test_ruff_format(self):
        r = _run_hook(_make_payload("ruff format ."))
        self.assertEqual(r.stdout, "")

    def test_invalid_json(self):
        r = _run_hook("not json at all")
        self.assertEqual(r.returncode, 0)
        self.assertEqual(r.stdout, "")

    def test_empty_stdin(self):
        r = _run_hook("")
        self.assertEqual(r.returncode, 0)
        self.assertEqual(r.stdout, "")

    def test_fixture_ls(self):
        r = _run_hook(_load_fixture("ls_passthrough.json"))
        self.assertEqual(r.stdout, "")


class TestSkipClaudeHooks(unittest.TestCase):
    """SKIP_CLAUDE_HOOKS=1 should bypass all hook logic."""

    def _run_hook_with_skip(self, stdin_text: str):
        env = {
            k: v for k, v in os.environ.items() if k != "CLAUDE_HOOK_LOG"
        }
        env["SKIP_CLAUDE_HOOKS"] = "1"
        return subprocess.run(
            ["python3", SCRIPT],
            input=stdin_text,
            capture_output=True,
            text=True,
            timeout=10,
            env=env,
        )

    def test_heredoc_skipped(self):
        r = self._run_hook_with_skip(
            _make_payload("python3 <<< 'print(1)'")
        )
        self.assertEqual(r.returncode, 0)
        self.assertEqual(r.stdout, "")

    def test_push_main_skipped(self):
        r = self._run_hook_with_skip(
            _make_payload("git push origin main")
        )
        self.assertEqual(r.returncode, 0)
        self.assertEqual(r.stdout, "")

    def test_commit_skipped(self):
        r = self._run_hook_with_skip(
            _make_payload("git commit -m 'fix'")
        )
        self.assertEqual(r.returncode, 0)
        self.assertEqual(r.stdout, "")


class TestBranchParsing(unittest.TestCase):
    """Edge cases in _resolve_push_branch."""

    def test_chained_command_push_main(self):
        """git push in a chained command should still be caught."""
        r = _run_hook(_make_payload("git add . && git push origin main"))
        d = _parse_decision(r.stdout)
        self.assertEqual(d["behavior"], "deny")

    def test_push_with_push_option(self):
        r = _run_hook(
            _make_payload("git push -o ci.skip origin main")
        )
        d = _parse_decision(r.stdout)
        self.assertEqual(d["behavior"], "deny")

    def test_push_no_verify_main(self):
        r = _run_hook(_make_payload("git push --no-verify origin main"))
        d = _parse_decision(r.stdout)
        self.assertEqual(d["behavior"], "deny")


def _init_repo(path: str, branch: str = "main") -> None:
    """Create a minimal git repo on the given branch."""
    os.makedirs(path, exist_ok=True)
    subprocess.run(
        ["git", "init", "-b", branch],
        cwd=path,
        capture_output=True,
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


class TestGitCommitGuard(unittest.TestCase):
    """Git commit branch-aware guard (rule 3)."""

    @classmethod
    def setUpClass(cls):
        cls._tmpdir = tempfile.mkdtemp()
        cls._feature_repo = os.path.join(cls._tmpdir, "feat")
        _init_repo(cls._feature_repo, branch="main")
        subprocess.run(
            ["git", "checkout", "-b", "feature-x"],
            cwd=cls._feature_repo,
            capture_output=True,
        )
        cls._main_repo = os.path.join(cls._tmpdir, "mainrepo")
        _init_repo(cls._main_repo, branch="main")
        cls._master_repo = os.path.join(cls._tmpdir, "masterrepo")
        _init_repo(cls._master_repo, branch="master")

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(cls._tmpdir, ignore_errors=True)

    def test_commit_on_feature_branch_allowed(self):
        r = _run_hook(_make_payload(
            "git commit -m 'fix bug'", cwd=self._feature_repo
        ))
        self.assertEqual(r.returncode, 0)
        self.assertEqual(_parse_decision(r.stdout)["behavior"], "allow")

    def test_commit_amend_on_feature_allowed(self):
        r = _run_hook(_make_payload(
            "git commit --amend --no-edit", cwd=self._feature_repo
        ))
        self.assertEqual(_parse_decision(r.stdout)["behavior"], "allow")

    def test_commit_on_main_passthrough(self):
        r = _run_hook(_make_payload(
            "git commit -m 'fix'", cwd=self._main_repo
        ))
        self.assertEqual(r.returncode, 0)
        self.assertEqual(r.stdout, "")

    def test_commit_on_master_passthrough(self):
        r = _run_hook(_make_payload(
            "git commit -m 'fix'", cwd=self._master_repo
        ))
        self.assertEqual(r.returncode, 0)
        self.assertEqual(r.stdout, "")

    def test_commit_with_C_flag_feature(self):
        r = _run_hook(_make_payload(
            f"git -C {self._feature_repo} commit -m 'fix'"
        ))
        self.assertEqual(_parse_decision(r.stdout)["behavior"], "allow")

    def test_commit_with_C_flag_main(self):
        r = _run_hook(_make_payload(
            f"git -C {self._main_repo} commit -m 'fix'"
        ))
        self.assertEqual(r.stdout, "")


class TestGitCCwd(unittest.TestCase):
    """Auto-allow git -C <cwd> <safe_subcommand> (rule 4)."""

    @classmethod
    def setUpClass(cls):
        cls._tmpdir = os.path.realpath(tempfile.mkdtemp())

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(cls._tmpdir, ignore_errors=True)

    def test_status_allowed(self):
        r = _run_hook(_make_payload(
            f"git -C {self._tmpdir} status", cwd=self._tmpdir
        ))
        self.assertEqual(_parse_decision(r.stdout)["behavior"], "allow")

    def test_add_allowed(self):
        r = _run_hook(_make_payload(
            f"git -C {self._tmpdir} add .", cwd=self._tmpdir
        ))
        self.assertEqual(_parse_decision(r.stdout)["behavior"], "allow")

    def test_diff_allowed(self):
        r = _run_hook(_make_payload(
            f"git -C {self._tmpdir} diff", cwd=self._tmpdir
        ))
        self.assertEqual(_parse_decision(r.stdout)["behavior"], "allow")

    def test_log_allowed(self):
        r = _run_hook(_make_payload(
            f"git -C {self._tmpdir} log --oneline", cwd=self._tmpdir
        ))
        self.assertEqual(_parse_decision(r.stdout)["behavior"], "allow")

    def test_show_allowed(self):
        r = _run_hook(_make_payload(
            f"git -C {self._tmpdir} show HEAD", cwd=self._tmpdir
        ))
        self.assertEqual(_parse_decision(r.stdout)["behavior"], "allow")

    def test_branch_allowed(self):
        r = _run_hook(_make_payload(
            f"git -C {self._tmpdir} branch -a", cwd=self._tmpdir
        ))
        self.assertEqual(_parse_decision(r.stdout)["behavior"], "allow")

    def test_chained_safe_commands_allowed(self):
        r = _run_hook(_make_payload(
            f"git -C {self._tmpdir} add . && git -C {self._tmpdir} status",
            cwd=self._tmpdir,
        ))
        self.assertEqual(_parse_decision(r.stdout)["behavior"], "allow")

    def test_different_dir_passthrough(self):
        other = os.path.realpath(tempfile.mkdtemp())
        try:
            r = _run_hook(_make_payload(
                f"git -C {other} status", cwd=self._tmpdir
            ))
            self.assertEqual(r.stdout, "")
        finally:
            shutil.rmtree(other, ignore_errors=True)

    def test_unsafe_subcommand_passthrough(self):
        """checkout is not in GIT_SAFE_SUBCOMMANDS."""
        r = _run_hook(_make_payload(
            f"git -C {self._tmpdir} checkout main", cwd=self._tmpdir
        ))
        self.assertEqual(r.stdout, "")

    def test_no_cwd_in_payload_passthrough(self):
        r = _run_hook(_make_payload(
            f"git -C {self._tmpdir} status"
        ))
        self.assertEqual(r.stdout, "")

    def test_plain_git_not_matched(self):
        """Plain git status (no -C) should not be handled by rule 4."""
        r = _run_hook(_make_payload(
            "git status", cwd=self._tmpdir
        ))
        self.assertEqual(r.stdout, "")


if __name__ == "__main__":
    unittest.main()
