"""Print the metrics of a results file and the cases to read by hand.

Usage: uv run python eval/report.py eval/results_v1.json   (default eval/results_v0.json)
"""
import json
import sys
from pathlib import Path

from nl_sql_agent.evaluation import summarize

path = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("eval/results_v0.json")
results = json.loads(path.read_text(encoding="utf-8"))
summary = summarize(results)

for name in ("execution_accuracy", "abstention"):
    k, n, (low, high) = summary[name]
    print(f"{name}: {k}/{n}  (95% Wilson CI {low:.2f}-{high:.2f})")
for name in ("median_steps", "median_input_tokens", "median_output_tokens", "median_seconds"):
    print(f"{name}: {summary[name]}")

print("\nTo read by hand:")
for r in results:
    if r.get("correct") is False or r.get("abstained") is False:
        print(f"\n[{r['id']}] {r['question']}\n  SQL: {r['proposed_sql']}\n  Answer: {r['answer'][:300]}")