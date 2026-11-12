import io
import os
import unittest
from contextlib import redirect_stderr, redirect_stdout

from oci_ootb_full_stack_dr_plan_check.cli import main

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


class TestCli(unittest.TestCase):
    def test_missing_file_exits_1(self):
        with redirect_stderr(io.StringIO()):
            self.assertEqual(main(["/nonexistent/plan.json"]), 1)

    def test_invalid_json_exits_1(self):
        with redirect_stderr(io.StringIO()):
            self.assertEqual(main([os.path.join(ROOT, "pyproject.toml")]), 1)

    def test_gappy_sample_exits_2(self):
        out = io.StringIO()
        with redirect_stdout(out):
            code = main([os.path.join(ROOT, "samples", "gappy-plan.json")])
        self.assertEqual(code, 2)
        text = out.getvalue()
        self.assertIn("DRP001", text)   # bucket-replica has no step
        self.assertIn("DRP002", text)   # s4 duplicates s3's name? no - duplicate id check; s4 has own id
        self.assertIn("DRP003", text)   # depends on unknown s9
        self.assertIn("summary:", text)

    def test_complete_sample_exits_0(self):
        out = io.StringIO()
        with redirect_stdout(out):
            code = main([os.path.join(ROOT, "samples", "complete-plan.json")])
        self.assertEqual(code, 0)
        self.assertIn("0 high", out.getvalue())


if __name__ == "__main__":
    unittest.main()
