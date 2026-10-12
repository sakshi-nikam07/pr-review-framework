"""OPTIONAL: run the real Bandit tool (pip install bandit) and map its test ids to our categories."""
import json, os, subprocess, tempfile
from models import Finding

MAP = {"B608": "SQL_INJECTION", "B105": "HARDCODED_SECRET", "B106": "HARDCODED_SECRET",
       "B107": "HARDCODED_SECRET", "B602": "COMMAND_INJECTION", "B605": "COMMAND_INJECTION",
       "B307": "UNSAFE_EVAL", "B102": "UNSAFE_EVAL", "B301": "INSECURE_DESERIALIZATION",
       "B506": "INSECURE_DESERIALIZATION", "B324": "WEAK_HASH", "B110": "BARE_EXCEPT"}


def run_bandit(filename, source):
    try:
        with tempfile.TemporaryDirectory() as d:
            p = os.path.join(d, "f.py")
            open(p, "w", encoding="utf-8").write(source)
            r = subprocess.run(["bandit", "-f", "json", "-q", p], capture_output=True, text=True, timeout=60)
            data = json.loads(r.stdout or "{}")
    except Exception:
        return []
    return [Finding(filename, x["line_number"], MAP[x["test_id"]], "bandit", x["issue_text"])
            for x in data.get("results", []) if x["test_id"] in MAP]
