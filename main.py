#!/usr/bin/env python3
"""Explainable Hybrid Multi-Agent PR Review Framework - command line.

  python main.py generate-data           build the labelled dataset
  python main.py evaluate                calibrate on DEV, measure accuracy on TEST
  python main.py demo [--lang mr]        review the bundled demo PR (Rahul's discount code)
  python main.py review FILE.py|DIFF     review a python file or a unified diff
  python main.py review-pr               GitHub Actions mode (posts a PR comment)
"""
import argparse, os, sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
ROOT = os.path.dirname(os.path.abspath(__file__))


def cmd_review(args):
    from review_engine import review_diff, review_file
    from explainer import summary
    text = open(args.target, encoding="utf-8").read()
    kw = dict(use_llm=args.use_llm, use_bandit=args.use_bandit)
    if args.target.endswith((".diff", ".patch")):
        findings = review_diff(text, **kw)
    else:
        findings = review_file(args.target, text, **kw)
    print(summary(findings, args.lang))


def cmd_demo(args):
    args.target = os.path.join(ROOT, "demo_pr", "rahul_discount.diff")
    cmd_review(args)


def cmd_review_pr(args):
    from review_engine import review_file
    from diffparse import parse_patch
    from explainer import summary
    import github_client as gh
    repo, number = os.environ["REPO"], os.environ["PR_NUMBER"]
    findings = []
    for f in gh.pr_files(repo, number):
        if not f["filename"].endswith(".py") or f["status"] == "removed" or "patch" not in f:
            continue
        added = parse_patch(f["patch"])
        if os.path.exists(f["filename"]):               # PR code is checked out by the workflow
            source = open(f["filename"], encoding="utf-8").read()
            findings += review_file(f["filename"], source, set(added), use_llm=args.use_llm, use_bandit=args.use_bandit)
    gh.post_comment(repo, number, summary(findings, args.lang))
    print(f"posted review with {len(findings)} finding(s)")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    for name in ("review", "demo", "review-pr"):
        p = sub.add_parser(name)
        if name == "review":
            p.add_argument("target")
        p.add_argument("--lang", choices=["en", "mr"], default=os.environ.get("REVIEW_LANG", "en"))
        p.add_argument("--use-llm", action="store_true", help="add the optional real-LLM agent (needs ANTHROPIC_API_KEY)")
        p.add_argument("--use-bandit", action="store_true", help="add real Bandit results (pip install bandit)")
    sub.add_parser("generate-data")
    sub.add_parser("evaluate")
    args = ap.parse_args()
    if args.cmd == "generate-data":
        from dataset.generate_dataset import main as g; g()
    elif args.cmd == "evaluate":
        from evaluate import main as e; e()
    elif args.cmd == "review":
        cmd_review(args)
    elif args.cmd == "demo":
        cmd_demo(args)
    elif args.cmd == "review-pr":
        cmd_review_pr(args)


if __name__ == "__main__":
    main()
