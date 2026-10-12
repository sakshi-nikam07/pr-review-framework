"""OPTIONAL (needs internet): download real closed PRs of a public repo and run our reviewer on them,
so you can compare with the HUMAN review comments. Usage:
    export GITHUB_TOKEN=...   (a personal access token)
    python scripts/fetch_prs.py owner/repo 30
Output: results/real_prs.json  (our findings + number of human review comments per PR)."""
import json, os, sys, urllib.request
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from review_engine import review_diff

repo, n = sys.argv[1], int(sys.argv[2]) if len(sys.argv) > 2 else 20
H = {"Authorization": f"Bearer {os.environ['GITHUB_TOKEN']}", "User-Agent": "pr-review-framework"}


def get(url, accept="application/vnd.github+json"):
    with urllib.request.urlopen(urllib.request.Request(url, headers={**H, "Accept": accept}), timeout=60) as r:
        return r.read().decode()


prs = json.loads(get(f"https://api.github.com/repos/{repo}/pulls?state=closed&per_page={n}"))
rows = []
for pr in prs:
    diff = get(pr["url"], "application/vnd.github.v3.diff")
    human = json.loads(get(f"https://api.github.com/repos/{repo}/pulls/{pr['number']}/comments"))
    found = review_diff(diff)
    rows.append(dict(pr=pr["number"], title=pr["title"], human_comments=len(human),
                     ai_findings=[(f.file, f.line, f.category, f.confidence) for f in found]))
os.makedirs("results", exist_ok=True)
json.dump(rows, open("results/real_prs.json", "w"), indent=2)
print(f"saved {len(rows)} PRs -> results/real_prs.json")
