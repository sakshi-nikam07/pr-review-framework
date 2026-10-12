import os, sys, unittest
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from review_engine import review_file, review_diff
from diffparse import parse_diff, source_from_added
from coordinator import fuse
from models import Finding


def cats(code):
    return {f.category for f in review_file("t.py", code)}


class Tests(unittest.TestCase):
    def test_sql_injection_detected(self):
        self.assertIn("SQL_INJECTION", cats('def f(n):\n    cur.execute("SELECT * FROM u WHERE n = \'" + n + "\'")\n'))

    def test_parameterized_sql_is_safe(self):
        self.assertNotIn("SQL_INJECTION", cats('def f(n):\n    cur.execute("SELECT * FROM u WHERE n = ?", (n,))\n'))

    def test_division_guard(self):
        self.assertIn("DIV_BY_ZERO", cats("def f(a, b):\n    return a / b\n"))
        self.assertNotIn("DIV_BY_ZERO", cats("def f(a, b):\n    if b == 0:\n        return 0\n    return a / b\n"))

    def test_fusion_noisy_or(self):
        fs = [Finding("a.py", 3, "WEAK_HASH", "static"), Finding("a.py", 3, "WEAK_HASH", "security")]
        out = fuse(fs, {"static": {"WEAK_HASH": 0.5}, "security": {"WEAK_HASH": 0.5}}, threshold=0.7)
        self.assertEqual(len(out), 1)
        self.assertAlmostEqual(out[0].confidence, 0.75)
        one = fuse(fs[:1], {"static": {"WEAK_HASH": 0.5}}, threshold=0.7)
        self.assertEqual(one, [])          # single weak source is rejected

    def test_diff_parsing_and_added_lines_only(self):
        diff = ("diff --git a/x.py b/x.py\n--- a/x.py\n+++ b/x.py\n@@ -1,2 +1,3 @@\n import os\n+PASSWORD = \"abc123\"\n x = 1\n")
        files = parse_diff(diff)
        self.assertEqual(list(files["x.py"].keys()), [2])
        self.assertTrue(any(f.category == "HARDCODED_SECRET" for f in review_diff(diff, cal={})))

    def test_clean_code(self):
        self.assertEqual(cats("def add(a, b):\n    return a + b\n"), set())


if __name__ == "__main__":
    unittest.main()
