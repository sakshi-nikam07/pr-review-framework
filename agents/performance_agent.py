import re
from .base import Agent


class PerformanceAgent(Agent):
    name = "performance"

    def run(self, path, source):
        out, stack = [], []
        for i, line in enumerate(source.splitlines(), 1):
            if not line.strip():
                continue
            ind = len(line) - len(line.lstrip())
            while stack and ind <= stack[-1][0]:
                stack.pop()
            if re.match(r"\s*for\s+.+\s+in\s+range\(\s*len\(", line):
                if stack:
                    out.append(self.f(path, stack[-1][1], "NESTED_LOOP", "nested range(len()) loops"))
                stack.append((ind, i))
        return out
