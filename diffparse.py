"""Tiny unified-diff parser: which lines were ADDED in each file."""
import re

HUNK = re.compile(r"^@@ -(\d+)(?:,(\d+))? \+(\d+)(?:,(\d+))? @@")


def parse_patch(patch):
    """Parse the hunks of ONE file. Returns {new_line_number: text}."""
    added, new_line, in_hunk = {}, 0, False
    for raw in patch.splitlines():
        m = HUNK.match(raw)
        if m:
            new_line, in_hunk = int(m.group(3)), True
            continue
        if not in_hunk:
            continue
        if raw.startswith("+"):
            added[new_line] = raw[1:]
            new_line += 1
        elif raw.startswith("-") or raw.startswith("\\"):
            continue
        else:
            new_line += 1
    return added


def parse_diff(diff_text):
    """Parse a multi-file diff. Returns {path: {line_no: text}}."""
    files, current, buf = {}, None, []

    def flush():
        if current is not None:
            files[current] = parse_patch("\n".join(buf))

    for raw in diff_text.splitlines():
        if raw.startswith("diff --git"):
            flush()
            current, buf = None, []
        elif raw.startswith("+++ ") and not buf:
            path = raw[4:].strip()
            current = path[2:] if path.startswith("b/") else path
        elif current is not None or raw.startswith("@@"):
            buf.append(raw)
    flush()
    return files


def source_from_added(added):
    """Rebuild a file from its added lines (exact for NEW files)."""
    if not added:
        return ""
    n = max(added)
    return "\n".join(added.get(i, "") for i in range(1, n + 1)) + "\n"
