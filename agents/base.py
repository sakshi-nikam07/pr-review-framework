from models import Finding


class Agent:
    """Every agent has a name and a run(path, source) -> list[Finding] method.
    Agents here are fast pattern/heuristic reasoners that work on the TEXT of the code
    (different from the AST-based static layer). A real LLM agent can be plugged in
    through agents/llm_agent.py using the same interface."""
    name = "agent"

    def run(self, path, source):
        raise NotImplementedError

    def f(self, path, line, category, detail=""):
        return Finding(path, line, category, self.name, detail)
