"""Generates the labelled PR dataset (seeded-bug method).

Every sample is a small Python file added by a fake pull request, stored as a unified diff
together with GROUND-TRUTH labels (which problem categories really exist in it).
Snippets come from templates that are 'positive' (contain a bug), 'safe' (correct code that
looks similar) or 'tricky' (safe, but easy to mistake for a bug). Positive templates have a
difficulty: easy (obvious), medium (needs data-flow across lines), hard (disguised)."""
import json, os, random, sys

HEADER = ("import ast\nimport builtins\nimport hashlib\nimport io\nimport os\nimport pickle\n"
          "import sqlite3\nimport subprocess\nimport yaml\n\n\n")
TABLES = ["users", "orders", "products", "customers", "payments", "employees"]
COLS = ["name", "email", "username", "city", "status"]
ARGS = ["name", "email", "username", "city", "term"]
NOUNS = ["record", "account", "item", "report", "profile", "entry", "order", "invoice"]
VERBS = ["get", "fetch", "find", "load", "lookup", "process", "check"]
SECRET_NAMES = ["DB_PASSWORD", "API_KEY", "SECRET_KEY", "AUTH_TOKEN"]
SECRET_VALUES = ["admin123", "sk-live-9fA3kLm2Qp7Xz", "s3cr3t!pass", "ghp_a1B2c3D4e5F6g7H8"]

TEMPLATES = []   # (id, category|None, kind, difficulty, code)


def tpl(tid, cat, kind, diff, code):
    TEMPLATES.append((tid, cat, kind, diff, code.strip("\n") + "\n"))


DB = '''    conn = sqlite3.connect("app.db")
    cur = conn.cursor()
'''
END = '''    rows = cur.fetchall()
    conn.close()
    return rows
'''
def sql(tid, kind, diff, body):
    tpl(tid, "SQL_INJECTION", kind, diff, "def <<fn>>(<<a>>):\n" + DB + body + END)

# ---- SQL injection
sql("sql_concat", "pos", "easy", '''    cur.execute("SELECT * FROM <<t>> WHERE <<c>> = '" + <<a>> + "'")\n''')
sql("sql_fstring", "pos", "easy", '''    cur.execute(f"SELECT * FROM <<t>> WHERE <<c>> = '{<<a>>}'")\n''')
sql("sql_var_concat", "pos", "medium", '''    query = "SELECT * FROM <<t>> WHERE <<c>> = '" + <<a>> + "'"\n    cur.execute(query)\n''')
sql("sql_var_format", "pos", "medium", '''    query = "SELECT * FROM <<t>> WHERE <<c>> = '{}'".format(<<a>>)\n    cur.execute(query)\n''')
sql("sql_var_percent", "pos", "medium", '''    query = "DELETE FROM <<t>> WHERE <<c>> = '%s'" % <<a>>\n    cur.execute(query)\n''')
sql("sql_join", "pos", "hard", '''    query = "".join(["SELECT * FROM <<t>> WHERE <<c>> = '", <<a>>, "'"])\n    cur.execute(query)\n''')
sql("sql_param_qmark", "safe", None, '''    cur.execute("SELECT * FROM <<t>> WHERE <<c>> = ?", (<<a>>,))\n''')
sql("sql_param_named", "safe", None, '''    cur.execute("SELECT * FROM <<t>> WHERE <<c>> = :v", {"v": <<a>>})\n''')
tpl("sql_log_message", "SQL_INJECTION", "tricky", None, '''
def <<fn>>(<<a>>, logger):
    logger.info("DELETE FROM " + <<a>> + " finished")
    return True
''')

# ---- Hard-coded secrets
tpl("secret_const", "HARDCODED_SECRET", "pos", "easy", '''
<<SN>> = "<<SV>>"


def <<fn>>():
    headers = {"Authorization": "Bearer " + <<SN>>}
    return headers
''')
tpl("secret_dict", "HARDCODED_SECRET", "pos", "medium", '''
def <<fn>>():
    config = {"host": "localhost", "password": "<<SV>>"}
    return config
''')
tpl("secret_join", "HARDCODED_SECRET", "pos", "hard", '''
<<SN>> = "".join(["ab12", "cd34", "ef56"])


def <<fn>>():
    headers = {"Authorization": "Bearer " + <<SN>>}
    return headers
''')
tpl("secret_env", "HARDCODED_SECRET", "safe", None, '''
<<SN>> = os.environ.get("<<SN>>")


def <<fn>>():
    headers = {"Authorization": "Bearer " + str(<<SN>>)}
    return headers
''')
tpl("secret_token_type", "HARDCODED_SECRET", "tricky", None, '''
def <<fn>>(<<a>>):
    token_type = "Bearer"
    return token_type + " " + <<a>>
''')

# ---- Command injection
tpl("cmd_concat", "COMMAND_INJECTION", "pos", "easy", '''
def <<fn>>(<<a>>):
    os.system("ping -c 1 " + <<a>>)
    return True
''')
tpl("cmd_shell_fstring", "COMMAND_INJECTION", "pos", "easy", '''
def <<fn>>(<<a>>):
    subprocess.call(f"ls -l {<<a>>}", shell=True)
    return True
''')
tpl("cmd_popen_percent", "COMMAND_INJECTION", "pos", "easy", '''
def <<fn>>(<<a>>):
    out = os.popen("nslookup %s" % <<a>>).read()
    return out
''')
tpl("cmd_var", "COMMAND_INJECTION", "pos", "medium", '''
def <<fn>>(<<a>>):
    cmd = "ping -c 1 " + <<a>>
    os.system(cmd)
    return True
''')
tpl("cmd_getattr", "COMMAND_INJECTION", "pos", "hard", '''
def <<fn>>(<<a>>):
    runner = getattr(os, "system")
    runner("ping -c 1 " + <<a>>)
    return True
''')
tpl("cmd_list", "COMMAND_INJECTION", "safe", None, '''
def <<fn>>(<<a>>):
    subprocess.run(["ping", "-c", "1", <<a>>], check=True)
    return True
''')
tpl("cmd_constant", "COMMAND_INJECTION", "safe", None, '''
def <<fn>>():
    os.system("clear")
    return True
''')

# ---- eval / exec
tpl("eval_direct", "UNSAFE_EVAL", "pos", "easy", '''
def <<fn>>(<<a>>):
    result = eval(<<a>>)
    return result
''')
tpl("exec_direct", "UNSAFE_EVAL", "pos", "easy", '''
def <<fn>>(<<a>>):
    exec(<<a>>)
    return True
''')
tpl("eval_builtins", "UNSAFE_EVAL", "pos", "medium", '''
def <<fn>>(<<a>>):
    return builtins.eval(<<a>>)
''')
tpl("eval_getattr", "UNSAFE_EVAL", "pos", "hard", '''
def <<fn>>(<<a>>):
    fn = getattr(builtins, "ev" + "al")
    return fn(<<a>>)
''')
tpl("eval_literal", "UNSAFE_EVAL", "safe", None, '''
def <<fn>>(<<a>>):
    return ast.literal_eval(<<a>>)
''')
tpl("eval_comment", "UNSAFE_EVAL", "tricky", None, '''
def <<fn>>(<<a>>):
    # never call eval(<<a>>) on untrusted input
    return str(<<a>>).strip()
''')

# ---- Insecure deserialization
tpl("pickle_loads", "INSECURE_DESERIALIZATION", "pos", "easy", '''
def <<fn>>(<<a>>):
    return pickle.loads(<<a>>)
''')
tpl("yaml_load", "INSECURE_DESERIALIZATION", "pos", "easy", '''
def <<fn>>(<<a>>):
    return yaml.load(<<a>>)
''')
tpl("yaml_unsafe_loader", "INSECURE_DESERIALIZATION", "pos", "easy", '''
def <<fn>>(path):
    with open(path) as f:
        return yaml.load(f, Loader=yaml.Loader)
''')
tpl("pickle_alias", "INSECURE_DESERIALIZATION", "pos", "hard", '''
def <<fn>>(<<a>>):
    loader = pickle.loads
    return loader(<<a>>)
''')
tpl("yaml_safe", "INSECURE_DESERIALIZATION", "safe", None, '''
def <<fn>>(<<a>>):
    return yaml.safe_load(<<a>>)
''')
tpl("yaml_safeloader", "INSECURE_DESERIALIZATION", "safe", None, '''
def <<fn>>(path):
    with open(path) as f:
        return yaml.load(f, Loader=yaml.SafeLoader)
''')

# ---- Weak hash
tpl("md5_direct", "WEAK_HASH", "pos", "easy", '''
def <<fn>>(<<a>>):
    return hashlib.md5(<<a>>.encode()).hexdigest()
''')
tpl("sha1_direct", "WEAK_HASH", "pos", "easy", '''
def <<fn>>(<<a>>):
    return hashlib.sha1(<<a>>.encode()).hexdigest()
''')
tpl("md5_new", "WEAK_HASH", "pos", "medium", '''
def <<fn>>(<<a>>):
    h = hashlib.new("md5")
    h.update(<<a>>.encode())
    return h.hexdigest()
''')
tpl("sha256_ok", "WEAK_HASH", "safe", None, '''
def <<fn>>(<<a>>):
    return hashlib.sha256(<<a>>.encode()).hexdigest()
''')
tpl("md5_checksum", "WEAK_HASH", "tricky", None, '''
def <<fn>>(<<a>>):
    return hashlib.md5(<<a>>.encode(), usedforsecurity=False).hexdigest()
''')

# ---- Division by zero
tpl("div_len", "DIV_BY_ZERO", "pos", "easy", '''
def <<fn>>(values):
    return sum(values) / len(values)
''')
tpl("div_param", "DIV_BY_ZERO", "pos", "easy", '''
def <<fn>>(a, b):
    return a / b
''')
tpl("div_floor", "DIV_BY_ZERO", "pos", "easy", '''
def <<fn>>(total, count):
    return total // count
''')
tpl("div_local", "DIV_BY_ZERO", "pos", "hard", '''
def <<fn>>(values):
    total = sum(values)
    count = len(values) - 1
    return total / count
''')
tpl("div_guard_if", "DIV_BY_ZERO", "safe", None, '''
def <<fn>>(values):
    if not values:
        return 0.0
    return sum(values) / len(values)
''')
tpl("div_guard_eq", "DIV_BY_ZERO", "safe", None, '''
def <<fn>>(a, b):
    if b == 0:
        raise ValueError("b must not be zero")
    return a / b
''')
tpl("div_guard_try", "DIV_BY_ZERO", "safe", None, '''
def <<fn>>(a, b):
    try:
        return a / b
    except ZeroDivisionError:
        return 0.0
''')
tpl("div_const", "DIV_BY_ZERO", "safe", None, '''
def <<fn>>(total):
    return total / 100
''')

# ---- Mutable default / bare except
tpl("mut_list", "MUTABLE_DEFAULT", "pos", "easy", '''
def <<fn>>(item, items=[]):
    items.append(item)
    return items
''')
tpl("mut_dict", "MUTABLE_DEFAULT", "pos", "easy", '''
def <<fn>>(key, cache={}):
    cache[key] = True
    return cache
''')
tpl("mut_none", "MUTABLE_DEFAULT", "safe", None, '''
def <<fn>>(item, items=None):
    if items is None:
        items = []
    items.append(item)
    return items
''')
tpl("bare_except", "BARE_EXCEPT", "pos", "easy", '''
def <<fn>>(value):
    try:
        return int(value)
    except:
        return None
''')
tpl("bare_except_pass", "BARE_EXCEPT", "pos", "easy", '''
def <<fn>>(path):
    try:
        os.remove(path)
    except:
        pass
    return True
''')
tpl("specific_except", "BARE_EXCEPT", "safe", None, '''
def <<fn>>(value):
    try:
        return int(value)
    except ValueError:
        return None
''')

# ---- Resource leaks
tpl("leak_open", "RESOURCE_LEAK", "pos", "easy", '''
def <<fn>>(path):
    f = open(path)
    data = f.read()
    return data
''')
tpl("leak_chain", "RESOURCE_LEAK", "pos", "easy", '''
def <<fn>>(path):
    data = open(path).read()
    return data
''')
tpl("leak_sqlite", "RESOURCE_LEAK", "pos", "easy", '''
def <<fn>>(db):
    conn = sqlite3.connect(db)
    cur = conn.cursor()
    cur.execute("SELECT COUNT(*) FROM <<t>>")
    return cur.fetchone()
''')
tpl("leak_io_open", "RESOURCE_LEAK", "pos", "hard", '''
def <<fn>>(path):
    f = io.open(path)
    data = f.read()
    return data
''')
tpl("with_open", "RESOURCE_LEAK", "safe", None, '''
def <<fn>>(path):
    with open(path) as f:
        data = f.read()
    return data
''')
tpl("explicit_close", "RESOURCE_LEAK", "safe", None, '''
def <<fn>>(path):
    f = open(path)
    data = f.read()
    f.close()
    return data
''')
tpl("return_handle", "RESOURCE_LEAK", "safe", None, '''
def <<fn>>(path):
    f = open(path)
    return f
''')

# ---- Nested loops / unused variables
tpl("nested_range", "NESTED_LOOP", "pos", "easy", '''
def <<fn>>(items):
    pairs = 0
    for i in range(len(items)):
        for j in range(len(items)):
            if items[i] == items[j] and i != j:
                pairs += 1
    return pairs
''')
tpl("nested_same_iter", "NESTED_LOOP", "pos", "medium", '''
def <<fn>>(items):
    dup = []
    for a in items:
        for b in items:
            if a is not b and a == b:
                dup.append(a)
    return dup
''')
tpl("single_loop", "NESTED_LOOP", "safe", None, '''
def <<fn>>(items):
    total = 0
    for x in items:
        total += x
    return total
''')
tpl("grid_loop", "NESTED_LOOP", "tricky", None, '''
def <<fn>>(grid):
    total = 0
    for r in range(len(grid)):
        for c in range(len(grid[r])):
            total += grid[r][c]
    return total
''')
tpl("unused_temp", "UNUSED_VARIABLE", "pos", "easy", '''
def <<fn>>(x):
    temp = x * 2
    return x + 1
''')
tpl("unused_backup", "UNUSED_VARIABLE", "pos", "easy", '''
def <<fn>>(x):
    backup = list(x)
    x.sort()
    return x
''')
tpl("used_var", "UNUSED_VARIABLE", "safe", None, '''
def <<fn>>(x):
    doubled = x * 2
    return doubled + 1
''')
tpl("underscore_var", "UNUSED_VARIABLE", "tricky", None, '''
def <<fn>>(x):
    _ = x * 2
    return x + 1
''')


def render(code, r, u):
    s = r.choice(range(len(SECRET_NAMES)))
    rep = {"fn": f"{r.choice(VERBS)}_{r.choice(NOUNS)}_{u}", "a": r.choice(ARGS), "t": r.choice(TABLES),
           "c": r.choice(COLS), "SN": SECRET_NAMES[s], "SV": SECRET_VALUES[s]}
    for k, v in rep.items():
        code = code.replace(f"<<{k}>>", v)
    return code


def make_diff(path, code):
    lines = code.splitlines()
    body = "\n".join("+" + l for l in lines)
    return (f"diff --git a/{path} b/{path}\nnew file mode 100644\n--- /dev/null\n+++ b/{path}\n"
            f"@@ -0,0 +1,{len(lines)} @@\n{body}\n")


def generate(n=300, seed=42, dev_fraction=0.3):
    r = random.Random(seed)
    cats = sorted({t[1] for t in TEMPLATES})
    by = {}
    for t in TEMPLATES:
        by.setdefault((t[1], "pos" if t[2] == "pos" else "safe"), []).append(t)
    samples, rank = [], {"easy": 1, "medium": 2, "hard": 3}
    uid = 0
    for i in range(n):
        clean = r.random() < 0.2
        k = r.choice([1, 2, 3])
        parts, labels, used, diffs = [], set(), [], []
        for j in range(k):
            want_pos = (not clean) and (j == 0 or r.random() < 0.4)
            cat = r.choice(cats)
            if want_pos:
                t = r.choice(by[(cat, "pos")])
            else:
                t = r.choice(by[(cat, "safe")])
            uid += 1
            parts.append(render(t[4], r, uid))
            used.append(t[0])
            if t[2] == "pos":
                labels.add(t[1])
                diffs.append(t[3])
        path = f"src/module_{i:03d}.py"
        code = HEADER + "\n\n".join(parts)
        samples.append(dict(id=f"pr_{i:03d}", filename=path, diff=make_diff(path, code),
                            labels=sorted(labels), templates=used,
                            difficulty=max((rank[d] for d in diffs), default=0)))
    idx = list(range(n))
    r.shuffle(idx)
    dev = set(idx[: int(n * dev_fraction)])
    for i, s in enumerate(samples):
        s["split"] = "dev" if i in dev else "test"
    return samples


def main(out=None):
    out = out or os.path.join(os.path.dirname(__file__), "pr_dataset.jsonl")
    data = generate()
    with open(out, "w", encoding="utf-8") as f:
        for s in data:
            f.write(json.dumps(s) + "\n")
    print(f"wrote {len(data)} samples -> {out}  (dev={sum(s['split']=='dev' for s in data)}, "
          f"test={sum(s['split']=='test' for s in data)}, clean={sum(not s['labels'] for s in data)})")


if __name__ == "__main__":
    main()
