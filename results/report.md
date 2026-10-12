# Evaluation report

Dataset: 300 synthetic PRs (seeded bugs). Calibration on DEV=90, results on unseen TEST=210.

## Overall (TEST split)

| System | Label accuracy | Exact-match accuracy | Detection accuracy | Precision | Recall | F1 |
|---|---|---|---|---|---|---|
| Static only | 96.4% | 60.5% | 74.3% | 93.6% | 64.5% | 76.4% |
| Agents only | 97.1% | 68.1% | 81.0% | 85.6% | 81.1% | 83.3% |
| Hybrid (proposed) | 97.5% | 72.9% | 85.2% | 86.3% | 86.0% | 86.2% |

*Label accuracy* = correct yes/no decisions over (sample x 12 categories) - inflated by many true negatives, so trust F1 more. *Exact-match* = predicted category set equals the truth set. *Detection accuracy* = correctly said 'has a problem' vs 'clean'.

## By difficulty (exact-match accuracy)

| Difficulty | #PRs | Static | Agents | Hybrid |
|---|---|---|---|---|
| clean (no bug) | 40 | 85% | 60% | 60% |
| easy | 103 | 80% | 92% | 92% |
| medium | 35 | 29% | 66% | 94% |
| hard | 32 | 3% | 3% | 3% |

## Per-category F1 (Hybrid) 

| Category | Precision | Recall | F1 | Support |
|---|---|---|---|---|
| BARE_EXCEPT | 100% | 100% | 100% | 11 |
| COMMAND_INJECTION | 100% | 76% | 87% | 17 |
| DIV_BY_ZERO | 100% | 77% | 87% | 26 |
| HARDCODED_SECRET | 64% | 69% | 67% | 26 |
| INSECURE_DESERIALIZATION | 100% | 74% | 85% | 19 |
| MUTABLE_DEFAULT | 100% | 100% | 100% | 16 |
| NESTED_LOOP | 71% | 100% | 83% | 22 |
| RESOURCE_LEAK | 100% | 84% | 91% | 19 |
| SQL_INJECTION | 95% | 95% | 95% | 22 |
| UNSAFE_EVAL | 82% | 64% | 72% | 14 |
| UNUSED_VARIABLE | 100% | 100% | 100% | 25 |
| WEAK_HASH | 55% | 100% | 71% | 11 |