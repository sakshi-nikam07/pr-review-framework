"""STATIC ANALYSIS LAYER (rule-based, deterministic).
Uses Python's AST, so it ignores comments/strings and has very few false alarms,
but it only sees what is written *directly* (no data-flow across variables)."""
import ast
from models import Finding

SECRET_WORDS = ("password", "passwd", "pwd", "secret", "api_key", "apikey", "token", "private_key")
SUBPROC = {"run", "call", "Popen", "check_output", "check_call"}


def dotted(n):
    if isinstance(n, ast.Name):
        return n.id
    if isinstance(n, ast.Attribute):
        base = dotted(n.value)
        return f"{base}.{n.attr}" if base else None
    return None


def _is_str(n):
    return isinstance(n, ast.Constant) and isinstance(n.value, str)


def is_dynamic_string(n):
    """True for "..." + x, f"...{x}", "..." % x, "...".format(x)."""
    if isinstance(n, ast.JoinedStr):
        return any(isinstance(v, ast.FormattedValue) for v in n.values)
    if isinstance(n, ast.BinOp) and isinstance(n.op, (ast.Add, ast.Mod)):
        has_str = any(_is_str(x) for x in ast.walk(n))
        has_var = any(isinstance(x, (ast.Name, ast.Call, ast.Attribute, ast.Subscript)) for x in ast.walk(n))
        return has_str and has_var
    if (isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute) and n.func.attr == "format"
            and _is_str(n.func.value) and (n.args or n.keywords)):
        return True
    return False


def _kw(call, name):
    for k in call.keywords:
        if k.arg == name:
            return k.value
    return None


def _iter_key(it):
    if (isinstance(it, ast.Call) and dotted(it.func) == "range" and it.args
            and isinstance(it.args[0], ast.Call) and dotted(it.args[0].func) == "len" and it.args[0].args):
        return ast.dump(it.args[0].args[0])
    if isinstance(it, ast.Name):
        return ast.dump(it)
    return None


def analyze(source, filename):
    try:
        tree = ast.parse(source)
    except SyntaxError:
        return []
    out = []

    def add(node, cat, detail=""):
        out.append(Finding(filename, getattr(node, "lineno", 1), cat, "static", detail))

    parents = {c: p for p in ast.walk(tree) for c in ast.iter_child_nodes(p)}
    with_exprs = {id(it.context_expr) for n in ast.walk(tree)
                  if isinstance(n, (ast.With, ast.AsyncWith)) for it in n.items}

    def enclosing_func(node):
        while node in parents:
            node = parents[node]
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                return node
        return tree

    for n in ast.walk(tree):
        # ---------- calls ----------
        if isinstance(n, ast.Call):
            name = dotted(n.func) or ""
            last = name.split(".")[-1]
            if (isinstance(n.func, ast.Attribute) and n.func.attr in ("execute", "executemany", "executescript")
                    and n.args and is_dynamic_string(n.args[0])):
                add(n, "SQL_INJECTION")
            if name in ("os.system", "os.popen") and n.args and is_dynamic_string(n.args[0]):
                add(n, "COMMAND_INJECTION")
            if name.startswith("subprocess.") and last in SUBPROC and n.args and is_dynamic_string(n.args[0]):
                sh = _kw(n, "shell")
                if isinstance(sh, ast.Constant) and sh.value is True:
                    add(n, "COMMAND_INJECTION")
            if name in ("eval", "exec"):
                add(n, "UNSAFE_EVAL")
            if name in ("pickle.load", "pickle.loads", "cPickle.loads", "marshal.loads"):
                add(n, "INSECURE_DESERIALIZATION")
            if name == "yaml.load":
                loader = _kw(n, "Loader")
                if loader is None or "Safe" not in (dotted(loader) or ""):
                    add(n, "INSECURE_DESERIALIZATION")
            if name in ("hashlib.md5", "hashlib.sha1"):
                ufs = _kw(n, "usedforsecurity")
                if not (isinstance(ufs, ast.Constant) and ufs.value is False):
                    add(n, "WEAK_HASH")
            # resource leaks (open / sqlite3.connect outside `with`)
            if name in ("open", "sqlite3.connect") and id(n) not in with_exprs:
                p = parents.get(n)
                scope = enclosing_func(n)
                if isinstance(p, ast.Assign) and len(p.targets) == 1 and isinstance(p.targets[0], ast.Name):
                    var = p.targets[0].id
                    closed = any(isinstance(c, ast.Call) and isinstance(c.func, ast.Attribute)
                                 and c.func.attr == "close" and isinstance(c.func.value, ast.Name)
                                 and c.func.value.id == var for c in ast.walk(scope))
                    returned = any(isinstance(r, ast.Return) and isinstance(r.value, ast.Name)
                                   and r.value.id == var for r in ast.walk(scope))
                    if not closed and not returned:
                        add(n, "RESOURCE_LEAK")
                elif isinstance(p, ast.Attribute):          # open(...).read()
                    add(n, "RESOURCE_LEAK")

        # ---------- hard-coded secrets ----------
        if isinstance(n, ast.Assign) and _is_str(n.value) and len(n.value.value) >= 3:
            for t in n.targets:
                if isinstance(t, ast.Name) and any(w in t.id.lower() for w in SECRET_WORDS):
                    add(n, "HARDCODED_SECRET")

        # ---------- function level checks ----------
        if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef)):
            defaults = list(n.args.defaults) + [d for d in n.args.kw_defaults if d is not None]
            for d in defaults:
                if isinstance(d, (ast.List, ast.Dict, ast.Set)) or (
                        isinstance(d, ast.Call) and dotted(d.func) in ("list", "dict", "set")):
                    add(n, "MUTABLE_DEFAULT")
                    break
            stores, loads = {}, set()
            uses_locals = False
            for x in ast.walk(n):
                if isinstance(x, ast.Name):
                    p = parents.get(x)
                    if isinstance(x.ctx, ast.Store) and isinstance(p, ast.Assign) and x in p.targets:
                        stores.setdefault(x.id, x)
                    elif isinstance(x.ctx, ast.Load):
                        loads.add(x.id)
                        if x.id == "locals":
                            uses_locals = True
                elif isinstance(x, ast.AugAssign) and isinstance(x.target, ast.Name):
                    loads.add(x.target.id)
            if not uses_locals:
                for var, node in stores.items():
                    if var not in loads and not var.startswith("_"):
                        add(node, "UNUSED_VARIABLE")

        if isinstance(n, ast.ExceptHandler) and n.type is None:
            add(n, "BARE_EXCEPT")

        # ---------- nested loops over the same data ----------
        if isinstance(n, ast.For):
            k = _iter_key(n.iter)
            if k:
                hit = any(isinstance(i, ast.For) and _iter_key(i.iter) == k
                          for stmt in n.body for i in ast.walk(stmt))
                if hit:
                    add(n, "NESTED_LOOP")
    return out
