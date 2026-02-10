#!/usr/bin/env python3
"""Tests for format_on_save.py hook.

Uses unittest.mock to patch subprocess.run and shutil.which so that
ruff is never actually executed.
"""

import importlib.util
import io
import json
import os
import sys
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

# Load the hook module from the template path (not installed as a package)
_SCRIPT = (
    Path(__file__).resolve().parent.parent
    / "assets"
    / "templates"
    / "format_on_save.py"
)
_spec = importlib.util.spec_from_file_location("format_on_save", _SCRIPT)
_mod = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_mod)
sys.modules["format_on_save"] = _mod
main = _mod.main
_resolve_log_path = _mod._resolve_log_path
log = _mod.log

FIXTURES_DIR = Path(__file__).resolve().parent / "fixtures"


def _load_fixture(name: str) -> str:
    return (FIXTURES_DIR / name).read_text()


def _make_payload(file_path: str) -> str:
    return json.dumps({"tool_input": {"file_path": file_path}})


def _run_main(stdin_text: str) -> None:
    """Run main() with the given string on sys.stdin."""
    with patch("format_on_save.sys.stdin", io.StringIO(stdin_text)):
        main()


class TestPyFileWithRuffOnPath(unittest.TestCase):
    """When ruff is on PATH and the file is .py, format with ruff directly."""

    @patch("format_on_save.subprocess.run")
    @patch("format_on_save.shutil.which", return_value="/usr/bin/ruff")
    def test_calls_ruff_format(self, mock_which, mock_run):
        mock_run.return_value = MagicMock(returncode=0)
        _run_main(_make_payload("/tmp/project/app.py"))

        mock_which.assert_called_once_with("ruff")
        mock_run.assert_called_once_with(
            ["/usr/bin/ruff", "format", "/tmp/project/app.py"],
            capture_output=True,
            timeout=10,
        )

    @patch("format_on_save.subprocess.run")
    @patch("format_on_save.shutil.which", return_value="/usr/bin/ruff")
    def test_no_stdout_output(self, _mock_which, mock_run):
        mock_run.return_value = MagicMock(returncode=0)
        # Capture stdout to verify the hook produces no output
        with patch("format_on_save.sys.stdout", new_callable=io.StringIO) as out:
            _run_main(_make_payload("/tmp/project/app.py"))
        self.assertEqual(out.getvalue(), "")

    @patch("format_on_save.subprocess.run")
    @patch("format_on_save.shutil.which", return_value="/usr/bin/ruff")
    def test_fixture_edit_py(self, _mock_which, mock_run):
        mock_run.return_value = MagicMock(returncode=0)
        _run_main(_load_fixture("edit_py_file.json"))

        args = mock_run.call_args[0][0]
        self.assertEqual(args[0], "/usr/bin/ruff")
        self.assertEqual(args[1], "format")
        self.assertTrue(args[2].endswith(".py"))


class TestPyFileWithoutRuff(unittest.TestCase):
    """When ruff is not on PATH, fall back to uv run ruff."""

    @patch("format_on_save.subprocess.run")
    @patch("format_on_save.shutil.which", return_value=None)
    def test_falls_back_to_uv_run(self, _mock_which, mock_run):
        mock_run.return_value = MagicMock(returncode=0)
        _run_main(_make_payload("/tmp/project/app.py"))

        mock_run.assert_called_once_with(
            ["uv", "run", "ruff", "format", "/tmp/project/app.py"],
            capture_output=True,
            timeout=10,
        )


class TestRuffFailure(unittest.TestCase):
    """When ruff fails (returncode=1), the hook should not crash."""

    @patch("format_on_save.subprocess.run")
    @patch("format_on_save.shutil.which", return_value="/usr/bin/ruff")
    def test_no_crash_on_failure(self, _mock_which, mock_run):
        mock_run.return_value = MagicMock(returncode=1)
        # Should not raise
        _run_main(_make_payload("/tmp/project/app.py"))
        mock_run.assert_called_once()

    @patch("format_on_save.subprocess.run")
    @patch("format_on_save.shutil.which", return_value="/usr/bin/ruff")
    def test_no_stdout_on_failure(self, _mock_which, mock_run):
        mock_run.return_value = MagicMock(returncode=1)
        with patch("format_on_save.sys.stdout", new_callable=io.StringIO) as out:
            _run_main(_make_payload("/tmp/project/app.py"))
        self.assertEqual(out.getvalue(), "")


class TestNonPyFile(unittest.TestCase):
    """Non-.py files should be skipped entirely (no subprocess call)."""

    @patch("format_on_save.subprocess.run")
    @patch("format_on_save.shutil.which")
    def test_json_file_skipped(self, mock_which, mock_run):
        _run_main(_make_payload("/tmp/project/config.json"))
        mock_which.assert_not_called()
        mock_run.assert_not_called()

    @patch("format_on_save.subprocess.run")
    @patch("format_on_save.shutil.which")
    def test_fixture_edit_json(self, mock_which, mock_run):
        _run_main(_load_fixture("edit_json_file.json"))
        mock_which.assert_not_called()
        mock_run.assert_not_called()

    @patch("format_on_save.subprocess.run")
    @patch("format_on_save.shutil.which")
    def test_md_file_skipped(self, mock_which, mock_run):
        _run_main(_make_payload("/tmp/project/README.md"))
        mock_run.assert_not_called()


class TestInvalidInput(unittest.TestCase):
    """Invalid or empty stdin should exit cleanly without crashing."""

    @patch("format_on_save.subprocess.run")
    def test_invalid_json(self, mock_run):
        _run_main("not json at all")
        mock_run.assert_not_called()

    @patch("format_on_save.subprocess.run")
    def test_empty_stdin(self, mock_run):
        _run_main("")
        mock_run.assert_not_called()

    @patch("format_on_save.subprocess.run")
    def test_missing_file_path(self, mock_run):
        _run_main(json.dumps({"tool_input": {}}))
        mock_run.assert_not_called()


class TestSkipClaudeHooks(unittest.TestCase):
    """SKIP_CLAUDE_HOOKS=1 should bypass all hook logic."""

    @patch("format_on_save.subprocess.run")
    @patch("format_on_save.shutil.which", return_value="/usr/bin/ruff")
    def test_py_file_skipped_when_env_set(self, mock_which, mock_run):
        with patch.dict("os.environ", {"SKIP_CLAUDE_HOOKS": "1"}):
            _run_main(_make_payload("/tmp/project/app.py"))
        mock_which.assert_not_called()
        mock_run.assert_not_called()

    @patch("format_on_save.subprocess.run")
    @patch("format_on_save.shutil.which", return_value="/usr/bin/ruff")
    def test_not_skipped_when_env_unset(self, _mock_which, mock_run):
        mock_run.return_value = MagicMock(returncode=0)
        with patch.dict("os.environ", {}, clear=False):
            env = dict(**os.environ)
            env.pop("SKIP_CLAUDE_HOOKS", None)
            with patch.dict("os.environ", env, clear=True):
                _run_main(_make_payload("/tmp/project/app.py"))
        mock_run.assert_called_once()


class TestLogging(unittest.TestCase):
    """CLAUDE_HOOK_LOG env var controls log path resolution."""

    def test_unset_returns_none(self):
        with patch.dict("os.environ", {}, clear=True):
            self.assertIsNone(_resolve_log_path())

    def test_empty_returns_none(self):
        with patch.dict("os.environ", {"CLAUDE_HOOK_LOG": ""}):
            self.assertIsNone(_resolve_log_path())

    def test_tilde_expands(self):
        with patch.dict("os.environ", {"CLAUDE_HOOK_LOG": "~/tmp/hooks.log"}):
            result = _resolve_log_path()
            self.assertFalse(result.startswith("~"))
            self.assertTrue(result.endswith("/tmp/hooks.log"))

    def test_relative_uses_project_dir(self):
        env = {"CLAUDE_HOOK_LOG": "logs/hook.log", "CLAUDE_PROJECT_DIR": "/proj"}
        with patch.dict("os.environ", env, clear=True):
            self.assertEqual(_resolve_log_path(), "/proj/logs/hook.log")

    def test_relative_uses_cwd_without_project_dir(self):
        env = {"CLAUDE_HOOK_LOG": "logs/hook.log"}
        with patch.dict("os.environ", env, clear=True), patch(
            "format_on_save.os.getcwd", return_value="/fallback"
        ):
            self.assertEqual(_resolve_log_path(), "/fallback/logs/hook.log")

    def test_absolute_used_as_is(self):
        with patch.dict(
            "os.environ", {"CLAUDE_HOOK_LOG": "/absolute/path.log"}
        ):
            self.assertEqual(_resolve_log_path(), "/absolute/path.log")

    def test_log_noop_when_unset(self):
        """log() should not write anything when CLAUDE_HOOK_LOG is unset."""
        with patch.dict("os.environ", {}, clear=True), patch(
            "builtins.open"
        ) as mock_open:
            log({"tool_input": {}}, "skip")
            mock_open.assert_not_called()


if __name__ == "__main__":
    unittest.main()
