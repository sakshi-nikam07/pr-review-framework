# Explainable Hybrid Multi-Agent AI Framework for GitHub Pull Request Code Review

Reviews the Python code in a Pull Request with **(1) a static-analysis layer, (2) four specialised agents,
(3) a Coordinator that fuses everything with calibrated confidence, and (4) an Explainability layer** that says
*what / why / where / how to fix / how confident / who agreed*.  Core code = **Python standard library only**.

## Quick start (any laptop, Python 3.9+)
```bash
cd pr_review_framework
python main.py generate-data      # (re)build dataset/pr_dataset.jsonl  (300 labelled PRs)
python main.py evaluate           # calibrate on DEV, measure accuracy on TEST -> results/
python main.py demo               # review the demo PR (Rahul's discount code)
python main.py demo --lang mr     # same, explanation in Marathi
python main.py review myfile.py   # review any python file  (or a .diff file)
python -m unittest discover -s tests
pip install matplotlib            # optional: needed only for results/comparison.png
```

## Architecture
```
GitHub PR --> diff parser --> Static layer (AST rules)  --\
                        \-->  Security | Bug | Performance | Style agents --> Coordinator (noisy-OR fusion,
                              (+ optional real LLM agent, + optional Bandit)    calibrated confidence, threshold)
                                                                                   --> Explainer --> PR comment
```
| File | Role |
|---|---|
| `static_tools/analyzer.py` | Deterministic AST checks (12 categories) |
| `agents/*.py` | Security, Bug, Performance, Style agents (text/heuristic reasoners, with light taint tracking) |
| `agents/llm_agent.py` | OPTIONAL real LLM agent (Anthropic API) - same interface |
| `coordinator.py` | Merge duplicates, noisy-OR confidence, threshold, severity ordering |
| `explainer.py`, `knowledge.py` | Explanations (English + Marathi), OWASP/CWE references, fixes |
| `github_client.py`, `main.py review-pr` | GitHub integration (posts the review comment) |
| `.github/workflows/review.yml` | GitHub Actions trigger |
| `dataset/generate_dataset.py` | Builds the labelled dataset |
| `evaluate.py` | Calibration + metrics + chart |

## Dataset (what it is - please read)
`dataset/pr_dataset.jsonl`: **300 synthetic PRs** (each = unified diff + ground-truth labels), built with the
*seeded-bug* method from 70+ templates: **bug** templates (easy / medium / hard), **safe** templates (look similar
but are correct) and **tricky-safe** templates (easy to mistake for a bug). 20% of PRs are clean.
Split: **30% DEV (90)** used only to calibrate confidences, **70% TEST (210)** used only for reporting.
12 categories: SQL injection, hard-coded secret, command injection, eval/exec, insecure deserialization, weak hash,
division by zero, mutable default, bare except, resource leak, nested loop, unused variable.

**Why not CodeReviewer / Big-Vul / BugsInPy?** The build environment had no internet, so they could not be
downloaded, and their labels (C vulnerabilities, bug-fix commits, human comments) do not map 1:1 to these 12
categories. `scripts/fetch_prs.py` (needs internet + a GitHub token) downloads real PRs and runs the reviewer
so you can compare with human reviewers qualitatively.

## Results (TEST split, 210 PRs) - see `results/report.md`, `results/comparison.png`
| System | Label acc. | Exact-match acc. | Detection acc. | Precision | Recall | F1 |
|---|---|---|---|---|---|---|
| Static only | 96.4% | 60.5% | 74.3% | 93.6% | 64.5% | 76.4% |
| Agents only | 97.1% | 68.1% | 81.0% | 85.6% | 81.1% | 83.3% |
| **Hybrid** | **97.5%** | **72.9%** | **85.2%** | 86.3% | **86.0%** | **86.2%** |

Honest reading of the numbers:
* Hybrid has the best **recall, F1 and exact-match**; Static alone has the best **precision** (93.6%).
* The big win is on **medium** PRs (exact-match 29% static, 66% agents, **94% hybrid**): cases where the bug is spread over several lines.
* **Hard** PRs (disguised bugs such as `getattr(os, "system")`, joined strings) are missed by everything (3%).
  These are exactly where a real LLM agent should help (`--use-llm`).
* Hybrid still raises false alarms on tricky-safe code (`token_type = "Bearer"`, `md5(..., usedforsecurity=False)`,
  grid loops): see `results/error_analysis.json`.
* *Label accuracy* is high mostly because most (sample x category) decisions are "no problem"; use F1 / exact-match.

## IMPORTANT limitations (say these in your viva/report)
1. The dataset and the detectors were written by the same author, so the numbers show the **framework's behaviour on a controlled
   benchmark**, NOT real-world accuracy. Real-world accuracy must be measured with real PRs / real LLMs.
2. The four "agents" here are rule/heuristic agents (offline, free, reproducible). The real LLM agent is included but
   **was not tested in the build environment** (no internet / API key).
3. Only Python files; no cross-file context; business-logic bugs (e.g. missing discount validation) need an LLM agent.
4. Explainability here = rule-based reasons + confidence + which sources agreed (no SHAP/LIME).

## Run on GitHub
1. Push this folder as repo `pr-review-framework`.
2. In the repo to be reviewed (e.g. `demo-shop-app`) add `.github/workflows/review.yml` (edit `YOUR_USER`).
3. Open a PR from a branch with buggy code -> **Actions** tab -> the bot comments on the PR.
4. Optional LLM agent: repo *Settings -> Secrets -> ANTHROPIC_API_KEY*, then add `--use-llm` in the workflow.
PRs from forks do not receive secrets (GitHub rule) - test using branches of the same repo.
