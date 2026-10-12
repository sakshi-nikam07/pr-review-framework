"""EVALUATION: calibrates on the DEV split, then measures accuracy on the unseen TEST split.
Compares three systems:  Static-only,  Agents-only,  Hybrid (static + agents + coordinator)."""
import json, os, sys
from collections import defaultdict
from knowledge import CATEGORY_LIST
from diffparse import parse_diff, source_from_added
from static_tools.analyzer import analyze
from review_engine import AGENTS
from coordinator import fuse, CAL_PATH

ROOT = os.path.dirname(__file__)
DATA = os.path.join(ROOT, "dataset", "pr_dataset.jsonl")
RESULTS = os.path.join(ROOT, "results")


def load(path=DATA):
    return [json.loads(l) for l in open(path, encoding="utf-8")]


def run_sample(s):
    (path, added), = parse_diff(s["diff"]).items()
    src = source_from_added(added)
    static = analyze(src, path)
    agents = []
    for a in AGENTS:
        agents += a.run(path, src)
    return static, agents


def calibrate(dev):
    """precision of every (source, category) on DEV, Laplace smoothed: (tp+1)/(predicted+2)."""
    tp, pred = defaultdict(int), defaultdict(int)
    for s in dev:
        static, agents = run_sample(s)
        truth = set(s["labels"])
        seen = {(f.source, f.category) for f in static + agents}
        for src, cat in seen:
            pred[(src, cat)] += 1
            tp[(src, cat)] += cat in truth
    cal = defaultdict(dict)
    for (src, cat), n in pred.items():
        cal[src][cat] = round((tp[(src, cat)] + 1) / (n + 2), 3)
    return dict(cal)


def predict(samples, cal):
    recs = []
    for s in samples:
        static, agents = run_sample(s)
        recs.append(dict(id=s["id"], truth=set(s["labels"]), difficulty=s["difficulty"], templates=s["templates"],
                         pred={"Static only": {f.category for f in static},
                               "Agents only": {f.category for f in agents},
                               "Hybrid (proposed)": {f.category for f in fuse(static + agents, cal)}}))
    return recs


def prf(tp, fp, fn):
    p = tp / (tp + fp) if tp + fp else 0.0
    r = tp / (tp + fn) if tp + fn else 0.0
    f = 2 * p * r / (p + r) if p + r else 0.0
    return p, r, f


def metrics(recs, system):
    tp = fp = fn = tn = exact = det_ok = 0
    per = {c: [0, 0, 0] for c in CATEGORY_LIST}
    for r in recs:
        truth, pred = r["truth"], r["pred"][system]
        exact += truth == pred
        det_ok += bool(truth) == bool(pred)
        for c in CATEGORY_LIST:
            t, p = c in truth, c in pred
            tp += t and p; fp += (not t) and p; fn += t and (not p); tn += (not t) and (not p)
            per[c][0] += t and p; per[c][1] += (not t) and p; per[c][2] += t and (not p)
    n = len(recs)
    p, r_, f = prf(tp, fp, fn)
    return dict(samples=n, label_accuracy=(tp + tn) / (n * len(CATEGORY_LIST)), exact_match_accuracy=exact / n,
                detection_accuracy=det_ok / n, precision=p, recall=r_, f1=f, tp=tp, fp=fp, fn=fn, tn=tn,
                per_category={c: dict(zip(("precision", "recall", "f1"), prf(*v)), support=v[0] + v[2])
                              for c, v in per.items()})


def by_difficulty(recs, system):
    out = {}
    for d, name in ((0, "clean (no bug)"), (1, "easy"), (2, "medium"), (3, "hard")):
        sub = [r for r in recs if r["difficulty"] == d]
        if sub:
            m = metrics(sub, system)
            out[name] = dict(samples=len(sub), exact_match=m["exact_match_accuracy"], recall=m["recall"], precision=m["precision"])
    return out


def main():
    data = load()
    dev = [s for s in data if s["split"] == "dev"]
    test = [s for s in data if s["split"] == "test"]
    cal = calibrate(dev)
    os.makedirs(os.path.dirname(CAL_PATH), exist_ok=True)
    json.dump(cal, open(CAL_PATH, "w", encoding="utf-8"), indent=2, sort_keys=True)
    recs = predict(test, cal)
    systems = ["Static only", "Agents only", "Hybrid (proposed)"]
    res = {s: metrics(recs, s) for s in systems}
    diff = {s: by_difficulty(recs, s) for s in systems}

    # --- print + save report
    L = [f"# Evaluation report\n", f"Dataset: {len(data)} synthetic PRs (seeded bugs). Calibration on DEV={len(dev)}, "
         f"results on unseen TEST={len(test)}.\n",
         "## Overall (TEST split)\n",
         "| System | Label accuracy | Exact-match accuracy | Detection accuracy | Precision | Recall | F1 |",
         "|---|---|---|---|---|---|---|"]
    for s in systems:
        m = res[s]
        L.append(f"| {s} | {m['label_accuracy']:.1%} | {m['exact_match_accuracy']:.1%} | {m['detection_accuracy']:.1%} | "
                 f"{m['precision']:.1%} | {m['recall']:.1%} | {m['f1']:.1%} |")
    L += ["", "*Label accuracy* = correct yes/no decisions over (sample x 12 categories) - inflated by many true negatives, "
          "so trust F1 more. *Exact-match* = predicted category set equals the truth set. "
          "*Detection accuracy* = correctly said 'has a problem' vs 'clean'.", "",
          "## By difficulty (exact-match accuracy)\n", "| Difficulty | #PRs | Static | Agents | Hybrid |", "|---|---|---|---|---|"]
    for d in diff["Hybrid (proposed)"]:
        row = [f"{diff[s][d]['exact_match']:.0%}" for s in systems]
        L.append(f"| {d} | {diff['Hybrid (proposed)'][d]['samples']} | " + " | ".join(row) + " |")
    L += ["", "## Per-category F1 (Hybrid) \n", "| Category | Precision | Recall | F1 | Support |", "|---|---|---|---|---|"]
    for c, v in res["Hybrid (proposed)"]["per_category"].items():
        L.append(f"| {c} | {v['precision']:.0%} | {v['recall']:.0%} | {v['f1']:.0%} | {v['support']} |")
    text = "\n".join(L)
    os.makedirs(RESULTS, exist_ok=True)
    open(os.path.join(RESULTS, "report.md"), "w", encoding="utf-8").write(text)
    json.dump(dict(overall=res, by_difficulty=diff), open(os.path.join(RESULTS, "metrics.json"), "w"), indent=2)

    # --- error analysis: which templates are really responsible for Hybrid's mistakes
    from dataset.generate_dataset import TEMPLATES
    meta = {t[0]: (t[1], t[2]) for t in TEMPLATES}
    errs = defaultdict(lambda: {"missed_bug": 0, "false_alarm": 0})
    for r in recs:
        pred = r["pred"]["Hybrid (proposed)"]
        for t in r["templates"]:
            cat, kind = meta[t]
            if kind == "pos" and cat not in pred:
                errs[t]["missed_bug"] += 1
            elif kind != "pos" and cat in pred and cat not in r["truth"]:
                errs[t]["false_alarm"] += 1
    errs = {k: v for k, v in sorted(errs.items(), key=lambda x: -(x[1]["missed_bug"] + x[1]["false_alarm"]))}
    json.dump(errs, open(os.path.join(RESULTS, "error_analysis.json"), "w"), indent=2)

    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
        names = ["precision", "recall", "f1", "exact_match_accuracy"]
        labels = ["Precision", "Recall", "F1", "Exact-match acc."]
        fig, ax = plt.subplots(figsize=(8, 4.5))
        w = 0.26
        for i, s in enumerate(systems):
            vals = [res[s][k] for k in names]
            bars = ax.bar([x + i * w for x in range(len(names))], vals, w, label=s)
            for b, v in zip(bars, vals):
                ax.text(b.get_x() + b.get_width() / 2, v + 0.01, f"{v:.2f}", ha="center", fontsize=7)
        ax.set_xticks([x + w for x in range(len(names))]); ax.set_xticklabels(labels)
        ax.set_ylim(0, 1.1); ax.set_title("Static vs Agents vs Hybrid (TEST split)"); ax.legend()
        plt.tight_layout(); plt.savefig(os.path.join(RESULTS, "comparison.png"), dpi=150)
    except Exception as e:
        print("chart skipped:", e)
    print(text)
    return res


if __name__ == "__main__":
    main()
