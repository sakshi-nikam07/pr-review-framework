"""OPTIONAL real-LLM agent (Anthropic API, standard library only).
Enable with:  export ANTHROPIC_API_KEY=...   and run with --use-llm
NOTE: this file could not be tested in the offline build environment."""
import json, os, re, urllib.request
from .base import Agent
from knowledge import CATEGORY_LIST

PROMPT = """You are a senior code reviewer. Review the Python file below.
Report ONLY real problems from this fixed list of categories: {cats}.
Return ONLY a JSON array like [{{"line": 12, "category": "SQL_INJECTION", "reason": "..."}}].
Return [] if there are no problems.

File {path}:
{code}
"""


class LLMAgent(Agent):
    name = "llm"

    def run(self, path, source):
        key = os.environ.get("ANTHROPIC_API_KEY")
        if not key:
            return []
        numbered = "\n".join(f"{i}: {l}" for i, l in enumerate(source.splitlines(), 1))
        body = {"model": os.environ.get("LLM_MODEL", "claude-sonnet-5-5"), "max_tokens": 1500,
                "messages": [{"role": "user", "content": PROMPT.format(cats=", ".join(CATEGORY_LIST), path=path, code=numbered)}]}
        req = urllib.request.Request("https://api.anthropic.com/v1/messages", data=json.dumps(body).encode(),
                                     headers={"x-api-key": key, "anthropic-version": "2023-06-01",
                                              "content-type": "application/json"})
        try:
            with urllib.request.urlopen(req, timeout=90) as r:
                text = json.loads(r.read())["content"][0]["text"]
            items = json.loads(re.search(r"\[.*\]", text, re.S).group(0))
        except Exception:
            return []
        return [self.f(path, int(i.get("line", 1)), i["category"], i.get("reason", ""))
                for i in items if i.get("category") in CATEGORY_LIST]
