"""Minimal GitHub REST client using only the standard library."""
import json, os, urllib.request

API = "https://api.github.com"


def _req(url, method="GET", data=None, accept="application/vnd.github+json"):
    headers = {"Authorization": f"Bearer {os.environ['GITHUB_TOKEN']}", "Accept": accept,
               "X-GitHub-Api-Version": "2022-11-28", "User-Agent": "pr-review-framework"}
    body = json.dumps(data).encode() if data is not None else None
    if body:
        headers["Content-Type"] = "application/json"
    with urllib.request.urlopen(urllib.request.Request(url, data=body, headers=headers, method=method), timeout=60) as r:
        return json.loads(r.read() or b"null")


def pr_files(repo, number):
    """List of changed files (with their 'patch'), handles pagination."""
    out, page = [], 1
    while True:
        batch = _req(f"{API}/repos/{repo}/pulls/{number}/files?per_page=100&page={page}")
        out += batch
        if len(batch) < 100:
            return out
        page += 1


def post_comment(repo, number, body):
    return _req(f"{API}/repos/{repo}/issues/{number}/comments", "POST", {"body": body})


def post_inline(repo, number, commit_sha, path, line, body):
    return _req(f"{API}/repos/{repo}/pulls/{number}/comments", "POST",
                {"body": body, "commit_id": commit_sha, "path": path, "line": line, "side": "RIGHT"})
