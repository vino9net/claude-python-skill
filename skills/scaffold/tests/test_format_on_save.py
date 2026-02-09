#!/usr/bin/env python3
"""Tests for format_on_save.py hook.

Uses unittest.mock to patch subprocess.run and shutil.which so that
ruff is never actually executed.
"""

import importlib.util
import io
import json
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


if __name__ == "__main__":
    unittest.main()
