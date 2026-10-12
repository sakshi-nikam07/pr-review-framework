"""COORDINATOR: merges findings from the static layer and all agents (Hybrid Fusion).

Idea:  every source has a *calibrated precision* per category (measured on a DEV split).
When several sources report the same problem we combine them with a noisy-OR:
        confidence = 1 - Π (1 - precision_source)
A finding is kept only if confidence >= threshold. So a weak, agent-only guess is dropped,
but two independent sources agreeing is accepted. This is how hallucination/false alarms are reduced."""
import json, os
from models import FusedFinding
from knowledge import CATEGORIES, SEVERITY_RANK

CAL_PATH = os.path.join(os.path.dirname(__file__), "config", "calibration.json")
DEFAULT_PRECISION = {"static": 0.85, "bandit": 0.85}
DEFAULT_AGENT_PRECISION = 0.55
THRESHOLD = 0.6
CLUSTER_GAP = 3   # lines


def load_calibration(path=CAL_PATH):
    try:
        return json.load(open(path, encoding="utf-8"))
    except Exception:
        return {}


def precision(cal, source, category):
    p = cal.get(source, {}).get(category)
    if p is not None:
        return p
    return DEFAULT_PRECISION.get(source, DEFAULT_AGENT_PRECISION)


def fuse(findings, cal=None, threshold=THRESHOLD):
    cal = cal or {}
    groups = {}
    for f in findings:
        groups.setdefault((f.file, f.category), []).append(f)
    fused = []
    for (file, cat), fs in groups.items():
        fs.sort(key=lambda x: x.line)
        clusters, cur = [], [fs[0]]
        for f in fs[1:]:
            if f.line - cur[-1].line <= CLUSTER_GAP:
                cur.append(f)
            else:
                clusters.append(cur)
                cur = [f]
        clusters.append(cur)
        for cl in clusters:
            sources = sorted({x.source for x in cl})
            miss = 1.0
            for s in sources:
                miss *= (1 - precision(cal, s, cat))
            conf = round(1 - miss, 3)
            if conf >= threshold:
                static_lines = [x.line for x in cl if x.source in ("static", "bandit")]
                line = min(static_lines) if static_lines else min(x.line for x in cl)
                fused.append(FusedFinding(file, line, cat, sources, conf))
    fused.sort(key=lambda x: (SEVERITY_RANK[CATEGORIES[x.category]["severity"]], x.file, x.line))
    return fused
