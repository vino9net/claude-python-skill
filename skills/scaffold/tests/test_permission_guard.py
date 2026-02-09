#!/usr/bin/env python3
"""Tests for permission_guard.py hook.

Runs the hook as a subprocess, feeding JSON payloads via stdin and asserting
on stdout output and exit code. No third-party dependencies required.
"""

import json
import os
import subprocess
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


def _make_payload(command: str) -> str:
    return json.dumps({"tool_input": {"command": command}})


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

    def test_git_commit(self):
        r = _run_hook(_make_payload("git commit -m 'fix'"))
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


if __name__ == "__main__":
    unittest.main()
