### 🤖 AI Pull Request Review
**5 issue(s)** — 🔴 2 critical, 🟠 1 major, 🟡 2 minor

**🔴 Critical | `demo_pr/rahul_discount.py` line 3 | विश्वास: 80%**
- **समस्या:** कोडमध्ये लिहिलेला पासवर्ड/की  _OWASP A07 / CWE-798_
- **कारण:** पासवर्ड/API key कोडमध्ये ठेवल्यास repository द्वारे लीक होऊ शकते.
- **उपाय:** Environment variable किंवा Secrets manager वापरा: os.environ.get("DB_PASSWORD")
- **स्रोत:** security, static (अनेक स्रोत सहमत)

**🔴 Critical | `demo_pr/rahul_discount.py` line 8 | विश्वास: 78%**
- **समस्या:** SQL Injection चा धोका  _OWASP A03 / CWE-89_
- **कारण:** User input थेट SQL query मध्ये जोडला आहे, त्यामुळे हल्लेखोर query बदलू शकतो (उदा. ' OR '1'='1).
- **उपाय:** Parameterized query वापरा: cur.execute("... WHERE name = ?", (name,))
- **स्रोत:** security 

**🟠 Major | `demo_pr/rahul_discount.py` line 7 | विश्वास: 94%**
- **समस्या:** Resource बंद केलेला नाही  _CWE-772_
- **कारण:** File/DB connection उघडला पण बंद केला नाही; handles लीक होतात.
- **उपाय:** `with` statement वापरा.
- **स्रोत:** static, style (अनेक स्रोत सहमत)

**🟡 Minor | `demo_pr/rahul_discount.py` line 9 | विश्वास: 99%**
- **समस्या:** न वापरलेला variable  _Code quality_
- **कारण:** Variable assign केला पण वापरला नाही; यामुळे कोड गोंधळात टाकतो.
- **उपाय:** तो काढून टाका (किंवा मुद्दाम असल्यास `_` नाव द्या).
- **स्रोत:** static, style (अनेक स्रोत सहमत)

**🟡 Minor | `demo_pr/rahul_discount.py` line 17 | विश्वास: 96%**
- **समस्या:** O(n²) nested loop  _Performance_
- **कारण:** एकाच डेटावर दोन nested loops असल्याने वेळ n² ने वाढतो.
- **उपाय:** set/dict/Counter किंवा built-in functions वापरून O(n) करा.
- **स्रोत:** performance, static (अनेक स्रोत सहमत)

