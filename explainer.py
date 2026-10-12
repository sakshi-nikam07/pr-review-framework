"""EXPLAINABILITY LAYER: turns a fused finding into a human readable review comment:
WHAT is wrong, WHY, WHERE, HOW to fix, how CONFIDENT we are, and WHO agreed."""
from knowledge import CATEGORIES

EMOJI = {"critical": "🔴 Critical", "major": "🟠 Major", "minor": "🟡 Minor"}


def explain(f, lang="en"):
    k = CATEGORIES[f.category]
    mr = lang == "mr"
    title = k["title_mr"] if mr else k["title"]
    why = k["why_mr"] if mr else k["why"]
    fix = k["fix_mr"] if mr else k["fix"]
    L = ("समस्या", "कारण", "उपाय", "विश्वास", "स्रोत") if mr else ("Problem", "Why", "Fix", "Confidence", "Detected by")
    agree = ("(अनेक स्रोत सहमत)" if mr else "(multiple sources agree)") if len(f.sources) > 1 else ""
    is_code = (not mr) and not fix.startswith(("Use", "Remove"))
    fix_txt = f"\n```python\n{fix}\n```" if is_code else f" {fix}"
    return (f"**{EMOJI[k['severity']]} | `{f.file}` line {f.line} | {L[3]}: {f.confidence:.0%}**\n"
            f"- **{L[0]}:** {title}  _{k['ref']}_\n"
            f"- **{L[1]}:** {why}\n"
            f"- **{L[2]}:**{fix_txt}\n"
            f"- **{L[4]}:** {', '.join(f.sources)} {agree}\n")


def summary(findings, lang="en"):
    if not findings:
        return "### ✅ AI Review: no issues found\n" if lang == "en" else "### ✅ AI Review: कोणतीही समस्या आढळली नाही\n"
    c = {"critical": 0, "major": 0, "minor": 0}
    for f in findings:
        c[CATEGORIES[f.category]["severity"]] += 1
    head = (f"### 🤖 AI Pull Request Review\n**{len(findings)} issue(s)** — "
            f"🔴 {c['critical']} critical, 🟠 {c['major']} major, 🟡 {c['minor']} minor\n\n")
    return head + "\n".join(explain(f, lang) for f in findings)
