"""Print the metrics of eval/results_v0.json and the cases to read by hand."""
import json
from pathlib import Path

from nl_sql_agent.evaluation import summarize

results = json.loads(Path("eval/results_v0.json").read_text(encoding="utf-8"))
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