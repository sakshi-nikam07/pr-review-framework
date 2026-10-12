import re
from .base import Agent
from .common import split_functions


class StyleAgent(Agent):
    name = "style"

    def run(self, path, source):
        out, lines = [], source.splitlines()
        for fn in split_functions(lines):
            body = lines[fn["start"] + 1: fn["end"]]
            text = "\n".join(body)
            for k, line in enumerate(body):
                line_no = fn["start"] + 2 + k
                m = re.match(r"\s*([A-Za-z_]\w*)\s*=(?!=)", line)
                if m and not m.group(1).startswith("_"):
                    var = m.group(1)
                    if len(re.findall(rf"\b{re.escape(var)}\b", text)) == 1:
                        out.append(self.f(path, line_no, "UNUSED_VARIABLE", var))
                m = re.match(r"\s*(\w+)\s*=\s*(open|sqlite3\.connect)\(", line)
                if m:
                    var = m.group(1)
                    if f"{var}.close()" not in text and not re.search(rf"return\s+{var}\s*$", text, re.M):
                        out.append(self.f(path, line_no, "RESOURCE_LEAK", var))
                if re.search(r"(?<!with )(?<![\w.])open\([^)]*\)\.(read|readlines|write)", line) and not line.strip().startswith("with"):
                    out.append(self.f(path, line_no, "RESOURCE_LEAK", "chained open()"))
        return out
