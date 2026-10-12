### 🤖 AI Pull Request Review
**5 issue(s)** — 🔴 2 critical, 🟠 1 major, 🟡 2 minor

**🔴 Critical | `demo_pr/rahul_discount.py` line 3 | Confidence: 80%**
- **Problem:** Hard-coded secret  _OWASP A07 / CWE-798_
- **Why:** Passwords/API keys stored in source code leak through the repository history.
- **Fix:**
```python
DB_PASSWORD = os.environ.get("DB_PASSWORD")
```
- **Detected by:** security, static (multiple sources agree)

**🔴 Critical | `demo_pr/rahul_discount.py` line 8 | Confidence: 78%**
- **Problem:** SQL Injection risk  _OWASP A03 / CWE-89_
- **Why:** User input is concatenated/formatted into an SQL string, so an attacker can change the query (e.g. ' OR '1'='1).
- **Fix:**
```python
cur.execute("SELECT * FROM users WHERE name = ?", (name,))
```
- **Detected by:** security 

**🟠 Major | `demo_pr/rahul_discount.py` line 7 | Confidence: 94%**
- **Problem:** Resource not closed  _CWE-772_
- **Why:** A file/DB connection is opened but never closed, which leaks handles.
- **Fix:**
```python
with open(path) as f:
    data = f.read()
```
- **Detected by:** static, style (multiple sources agree)

**🟡 Minor | `demo_pr/rahul_discount.py` line 9 | Confidence: 99%**
- **Problem:** Unused variable  _Code quality_
- **Why:** The variable is assigned but never used; dead code hurts readability.
- **Fix:** Remove it (or rename to `_` if intentional).
- **Detected by:** static, style (multiple sources agree)

**🟡 Minor | `demo_pr/rahul_discount.py` line 17 | Confidence: 96%**
- **Problem:** Quadratic nested loop  _Performance_
- **Why:** Two nested loops over the same data make the work grow with n squared.
- **Fix:** Use a set/dict/Counter or built-ins (sum, any) to get O(n).
- **Detected by:** performance, static (multiple sources agree)

