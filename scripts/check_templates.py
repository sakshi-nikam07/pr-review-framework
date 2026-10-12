"""Runs every template ALONE and shows what Static / Agents / Hybrid say vs the truth.
Used to verify that the ground-truth labels are sensible (not a bug in the dataset)."""
import os, random, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from dataset.generate_dataset import TEMPLATES, HEADER, render
from static_tools.analyzer import analyze
from review_engine import AGENTS
from coordinator import fuse, load_calibration

cal = load_calibration()
r = random.Random(1)
bad = 0
for tid, cat, kind, diff, code in TEMPLATES:
    src = HEADER + render(code, r, 1)
    st = analyze(src, "t.py")
    ag = []
    for a in AGENTS:
        ag += a.run("t.py", src)
    hy = fuse(st + ag, cal)
    truth = {cat} if kind == "pos" else set()
    S, A, H = ({f.category for f in x} for x in (st, ag, hy))
    flag = "" if H == truth else "   <-- hybrid differs"
    print(f"{tid:20s} {kind:6s} {str(diff):6s} truth={sorted(truth)}  static={sorted(S)} agents={sorted(A)} hybrid={sorted(H)}{flag}")
