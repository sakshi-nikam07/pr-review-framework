"""Pipeline: source -> static layer + agents -> coordinator -> explainer."""
from static_tools.analyzer import analyze
from agents.security_agent import SecurityAgent
from agents.bug_agent import BugAgent
from agents.performance_agent import PerformanceAgent
from agents.style_agent import StyleAgent
from coordinator import fuse, load_calibration
from diffparse import parse_diff, source_from_added

AGENTS = [SecurityAgent(), BugAgent(), PerformanceAgent(), StyleAgent()]


def collect(path, source, use_llm=False, use_bandit=False):
    static = analyze(source, path)
    if use_bandit:
        from static_tools.bandit_runner import run_bandit
        static += run_bandit(path, source)
    agents = []
    for a in AGENTS:
        agents += a.run(path, source)
    if use_llm:
        from agents.llm_agent import LLMAgent
        agents += LLMAgent().run(path, source)
    return static, agents


def review_file(path, source, added_lines=None, cal=None, use_llm=False, use_bandit=False):
    cal = load_calibration() if cal is None else cal
    static, agents = collect(path, source, use_llm, use_bandit)
    allf = static + agents
    if added_lines is not None:                       # only comment on lines changed in the PR
        allf = [f for f in allf if f.line in added_lines]
    return fuse(allf, cal)


def review_diff(diff_text, cal=None, **kw):
    out = []
    for path, added in parse_diff(diff_text).items():
        if path.endswith(".py"):
            out += review_file(path, source_from_added(added), set(added), cal, **kw)
    return out
