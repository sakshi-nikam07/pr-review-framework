"""Knowledge base: what each category means, why it matters and how to fix it.
This powers the Explainability layer (English + Marathi)."""

CATEGORIES = {
    "SQL_INJECTION": dict(
        severity="critical", ref="OWASP A03 / CWE-89",
        title="SQL Injection risk", title_mr="SQL Injection चा धोका",
        why="User input is concatenated/formatted into an SQL string, so an attacker can change the query (e.g. ' OR '1'='1).",
        why_mr="User input थेट SQL query मध्ये जोडला आहे, त्यामुळे हल्लेखोर query बदलू शकतो (उदा. ' OR '1'='1).",
        fix='cur.execute("SELECT * FROM users WHERE name = ?", (name,))',
        fix_mr="Parameterized query वापरा: cur.execute(\"... WHERE name = ?\", (name,))"),
    "HARDCODED_SECRET": dict(
        severity="critical", ref="OWASP A07 / CWE-798",
        title="Hard-coded secret", title_mr="कोडमध्ये लिहिलेला पासवर्ड/की",
        why="Passwords/API keys stored in source code leak through the repository history.",
        why_mr="पासवर्ड/API key कोडमध्ये ठेवल्यास repository द्वारे लीक होऊ शकते.",
        fix='DB_PASSWORD = os.environ.get("DB_PASSWORD")',
        fix_mr="Environment variable किंवा Secrets manager वापरा: os.environ.get(\"DB_PASSWORD\")"),
    "COMMAND_INJECTION": dict(
        severity="critical", ref="OWASP A03 / CWE-78",
        title="OS command injection risk", title_mr="OS Command Injection चा धोका",
        why="User-controlled text is passed to a shell, so extra commands can be injected (e.g. '; rm -rf /').",
        why_mr="User input shell कडे पाठवला जातो, त्यामुळे अतिरिक्त commands चालवल्या जाऊ शकतात.",
        fix='subprocess.run(["ping", "-c", "1", host], check=True)',
        fix_mr="Shell टाळा आणि list स्वरूपात arguments द्या: subprocess.run([...], check=True)"),
    "UNSAFE_EVAL": dict(
        severity="critical", ref="CWE-95",
        title="Use of eval/exec", title_mr="eval/exec चा वापर",
        why="eval/exec run arbitrary Python code, so untrusted input leads to remote code execution.",
        why_mr="eval/exec कोणताही Python कोड चालवतात, त्यामुळे अविश्वसनीय input धोकादायक आहे.",
        fix="value = ast.literal_eval(text)",
        fix_mr="ast.literal_eval वापरा किंवा input चे स्पष्ट parsing करा."),
    "INSECURE_DESERIALIZATION": dict(
        severity="critical", ref="OWASP A08 / CWE-502",
        title="Insecure deserialization", title_mr="असुरक्षित Deserialization",
        why="pickle / yaml.load can execute code while loading untrusted data.",
        why_mr="pickle / yaml.load डेटा लोड करताना कोड चालवू शकतात.",
        fix="yaml.safe_load(stream)  # or json.loads(data)",
        fix_mr="yaml.safe_load किंवा json.loads वापरा."),
    "WEAK_HASH": dict(
        severity="major", ref="CWE-327",
        title="Weak hash algorithm (MD5/SHA1)", title_mr="कमकुवत Hash (MD5/SHA1)",
        why="MD5 and SHA1 are broken for security purposes (collisions, fast brute-force).",
        why_mr="MD5/SHA1 सुरक्षेसाठी कमकुवत आहेत.",
        fix="hashlib.sha256(data).hexdigest()  # passwords: bcrypt/argon2",
        fix_mr="SHA-256 वापरा; पासवर्डसाठी bcrypt/argon2."),
    "DIV_BY_ZERO": dict(
        severity="major", ref="CWE-369",
        title="Possible division by zero", title_mr="शून्याने भागाकाराची शक्यता",
        why="The divisor can be 0 (or an empty list) and there is no guard, so the code can crash.",
        why_mr="भाजक 0 (किंवा रिकामी list) असू शकतो आणि तपासणी नाही, त्यामुळे कोड crash होऊ शकतो.",
        fix="if not values:\n    return 0.0\nreturn sum(values) / len(values)",
        fix_mr="भागाकाराआधी भाजक 0 नाही हे तपासा."),
    "MUTABLE_DEFAULT": dict(
        severity="major", ref="Python gotcha",
        title="Mutable default argument", title_mr="Mutable default argument",
        why="A list/dict default is created once and shared between calls, causing hidden state bugs.",
        why_mr="List/dict default एकदाच तयार होतो आणि सर्व calls मध्ये शेअर होतो; त्यामुळे लपलेले bugs येतात.",
        fix="def f(item, items=None):\n    if items is None:\n        items = []",
        fix_mr="Default None ठेवा आणि function मध्ये नवीन list बनवा."),
    "BARE_EXCEPT": dict(
        severity="major", ref="PEP 8 / CWE-396",
        title="Bare except", title_mr="Bare except",
        why="`except:` swallows every error including KeyboardInterrupt, hiding real bugs.",
        why_mr="`except:` सर्व errors गिळतो, त्यामुळे खरे bugs लपतात.",
        fix="except ValueError:",
        fix_mr="विशिष्ट exception पकडा, उदा. except ValueError:"),
    "RESOURCE_LEAK": dict(
        severity="major", ref="CWE-772",
        title="Resource not closed", title_mr="Resource बंद केलेला नाही",
        why="A file/DB connection is opened but never closed, which leaks handles.",
        why_mr="File/DB connection उघडला पण बंद केला नाही; handles लीक होतात.",
        fix="with open(path) as f:\n    data = f.read()",
        fix_mr="`with` statement वापरा."),
    "NESTED_LOOP": dict(
        severity="minor", ref="Performance",
        title="Quadratic nested loop", title_mr="O(n²) nested loop",
        why="Two nested loops over the same data make the work grow with n squared.",
        why_mr="एकाच डेटावर दोन nested loops असल्याने वेळ n² ने वाढतो.",
        fix="Use a set/dict/Counter or built-ins (sum, any) to get O(n).",
        fix_mr="set/dict/Counter किंवा built-in functions वापरून O(n) करा."),
    "UNUSED_VARIABLE": dict(
        severity="minor", ref="Code quality",
        title="Unused variable", title_mr="न वापरलेला variable",
        why="The variable is assigned but never used; dead code hurts readability.",
        why_mr="Variable assign केला पण वापरला नाही; यामुळे कोड गोंधळात टाकतो.",
        fix="Remove it (or rename to `_` if intentional).",
        fix_mr="तो काढून टाका (किंवा मुद्दाम असल्यास `_` नाव द्या)."),
}

CATEGORY_LIST = sorted(CATEGORIES)
SEVERITY_RANK = {"critical": 0, "major": 1, "minor": 2}
