import re


def split_functions(lines):
    """Very small def-block splitter based on indentation."""
    funcs, pat = [], re.compile(r"^(\s*)def\s+(\w+)\s*\((.*)\)\s*(?:->.*)?:\s*$")
    for i, line in enumerate(lines):
        m = pat.match(line)
        if not m:
            continue
        indent = len(m.group(1))
        end = len(lines)
        for j in range(i + 1, len(lines)):
            if lines[j].strip() and (len(lines[j]) - len(lines[j].lstrip())) <= indent:
                end = j
                break
        params = [p.split("=")[0].split(":")[0].strip().lstrip("*") for p in m.group(3).split(",") if p.strip()]
        funcs.append(dict(name=m.group(2), start=i, end=end, params=params))
    return funcs


def strip_strings_and_comments(line):
    line = re.sub(r"""(["'])(?:\\.|(?!\1).)*\1""", '""', line)
    return line.split("#")[0]
