"""Unit tests for the shared standard-library hook utilities."""

from contextlib import redirect_stderr
import io
from pathlib import Path
import sys
import tempfile
import unittest

LIB_DIR = Path(__file__).resolve().parents[1] / "hooks" / "lib"
sys.path.insert(0, str(LIB_DIR))

import common  # noqa: E402


class CommonHookTests(unittest.TestCase):
    def test_project_root_and_config(self):
        self.assertEqual(common.find_project_root(__file__), LIB_DIR.parents[2])
        self.assertEqual(common.load_project_config()["max_candidates"], 25)

    def test_glob_matches_repository_relative_path(self):
        self.assertTrue(
            common.match_any_glob("src/models/retrieval/matcher.py", ["src/models/**"])
        )
        self.assertFalse(common.match_any_glob("docs/plan.md", ["src/models/**"]))

    def test_read_stdin_payload_accepts_json_object(self):
        original_stdin = sys.stdin
        try:
            sys.stdin = io.StringIO('{"command": "git status"}')
            self.assertEqual(common.read_stdin_payload(), {"command": "git status"})
        finally:
            sys.stdin = original_stdin

    def test_block_exits_with_code_two_and_diagnostic(self):
        stderr = io.StringIO()
        with redirect_stderr(stderr), self.assertRaises(SystemExit) as raised:
            common.block("blocked action", hook_id="TEST")
        self.assertEqual(raised.exception.code, 2)
        self.assertIn("blocked action", stderr.getvalue())

    def test_state_directory_is_created_under_given_root(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            expected = Path(temp_dir) / ".agents" / "state"
            self.assertEqual(common.ensure_state_dir(temp_dir), expected)
            self.assertTrue(expected.is_dir())


if __name__ == "__main__":
    unittest.main()
