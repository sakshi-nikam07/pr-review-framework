import re
from .base import Agent

SQL_KW = r"(SELECT\s.+\sFROM|INSERT\s+INTO|UPDATE\s.+\sSET|DELETE\s+FROM)"
SECRET_RE = re.compile(r"""(password|passwd|pwd|secret|api_?key|token|private_key)\w*["']?\s*[:=]\s*["'][^"']{3,}["']""", re.I)
TOKEN_PREFIX = re.compile(r"""["'](sk-[A-Za-z0-9_\-]{8,}|AKIA[0-9A-Z]{12,}|ghp_[A-Za-z0-9]{10,})["']""")
LITERAL_ARG = re.compile(r"""\s*(["'])[^"'+%{]*\1\s*""")


def looks_like_dynamic_sql(line):
    if not re.search(SQL_KW, line, re.I):
        return False
    return bool(re.search(r"""\bf["'].*\{""", line) or re.search(r"""["']\s*\+|\+\s*["']""", line)
                or ".format(" in line or re.search(r"""["']\s*%\s*[\(\w]""", line))


class SecurityAgent(Agent):
    name = "security"

    def run(self, path, source):
        out, tainted = [], set()
        lines = source.splitlines()
        for i, line in enumerate(lines, 1):
            # --- SQL injection (with light taint tracking through variables) ---
            if looks_like_dynamic_sql(line):
                out.append(self.f(path, i, "SQL_INJECTION", "dynamic SQL string"))
                m = re.match(r"\s*(\w+)\s*=", line)
                if m:
                    tainted.add(m.group(1))
            m = re.search(r"\.execute(?:many|script)?\(\s*(\w+)\s*[,)]", line)
            if m and m.group(1) in tainted:
                out.append(self.f(path, i, "SQL_INJECTION", "tainted query variable executed"))
            # --- secrets ---
            if "environ" not in line and "getenv" not in line and (SECRET_RE.search(line) or TOKEN_PREFIX.search(line)):
                out.append(self.f(path, i, "HARDCODED_SECRET"))
            # --- command injection ---
            m = re.search(r"os\.(?:system|popen)\((.*)\)", line)
            if m and not LITERAL_ARG.fullmatch(m.group(1)):
                out.append(self.f(path, i, "COMMAND_INJECTION"))
            if re.search(r"subprocess\.\w+\(", line) and re.search(r"shell\s*=\s*True", line):
                if (re.search(r"""\+|\bf["']|%|\.format\(""", line)
                        or re.search(r"subprocess\.\w+\(\s*[A-Za-z_]\w*\s*[,)]", line)):
                    out.append(self.f(path, i, "COMMAND_INJECTION"))
            # --- eval / exec ---
            if re.search(r"\b(eval|exec)\s*\(", line):
                out.append(self.f(path, i, "UNSAFE_EVAL"))
            # --- deserialization ---
            if re.search(r"\b(pickle|cPickle|marshal)\.loads?\(", line):
                out.append(self.f(path, i, "INSECURE_DESERIALIZATION"))
            if re.search(r"\byaml\.load\(", line) and "Safe" not in line:
                out.append(self.f(path, i, "INSECURE_DESERIALIZATION"))
            # --- weak hashes ---
            if re.search(r"hashlib\.(md5|sha1)\(", line) or re.search(r"""hashlib\.new\(\s*["'](md5|sha1)""", line):
                out.append(self.f(path, i, "WEAK_HASH"))
        return out
