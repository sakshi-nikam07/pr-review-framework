import re
from .base import Agent
from .common import split_functions, strip_strings_and_comments

DIV_RE = re.compile(r"(?<![/\*])/{1,2}(?![/=\*])\s*(len\(\s*([A-Za-z_]\w*)\s*\)|[A-Za-z_]\w*)")


class BugAgent(Agent):
    name = "bug"

    def run(self, path, source):
        out, lines = [], source.splitlines()
        for i, line in enumerate(lines, 1):
            if re.match(r"\s*except\s*:", line):
                out.append(self.f(path, i, "BARE_EXCEPT"))
            if re.search(r"def\s+\w+\(.*\b\w+\s*(?::[^=,)]+)?=\s*(\[\]|\{\}|set\(\)|list\(\)|dict\(\))", line):
                out.append(self.f(path, i, "MUTABLE_DEFAULT"))
        # division by zero without a guard
        for fn in split_functions(lines):
            body = lines[fn["start"] + 1: fn["end"]]
            text = "\n".join(body)
            if "ZeroDivisionError" in text:
                continue
            for k, line in enumerate(body):
                for m in DIV_RE.finditer(strip_strings_and_comments(line)):
                    den = m.group(2) if m.group(2) else m.group(1)
                    if not m.group(2) and den not in fn["params"]:
                        continue
                    guard = re.compile(rf"\bif\b.*\b{re.escape(den)}\b|\b{re.escape(den)}\b\s*(==|!=|<=|>=|<|>)\s*0|assert\s+.*\b{re.escape(den)}\b")
                    if not guard.search(text):
                        out.append(self.f(path, fn["start"] + 2 + k, "DIV_BY_ZERO", f"divisor '{den}' unchecked"))
        return out
