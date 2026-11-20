"""Riepilogo delle tracce di una valutazione, o la cronologia di una domanda.

uv run python eval/show_trace.py v1          tabella di tutte le domande
uv run python eval/show_trace.py v1 x02      eventi di una domanda, in ordine
"""
import json
import sys
from pathlib import Path

from nl_sql_agent.trace_view import load_events, split_by_question, summarize_run

version = sys.argv[1]
runs = split_by_question(load_events(Path(f"logs/traces_{version}.jsonl")))

if len(sys.argv) > 2:
    for event in runs[sys.argv[2]]:
        detail = {k: v for k, v in event.items() if k not in ("time", "kind")}
        print(f"{event['time'][11:]}  {event['kind']:<9} {json.dumps(detail, ensure_ascii=False)[:160]}")
else:
    print(f"{'id':<5} {'passi':>5} {'rifiuti':>7} {'token':>6} {'s':>5}  tool")
    for qid, events in runs.items():
        s = summarize_run(events)
        print(f"{qid:<5} {s['steps']:>5} {len(s['refused']):>7} {s['input_tokens']:>6} "
              f"{s['model_seconds']:>5}  {' '.join(s['tools'])}{'  LIMITE' if s['hit_limit'] else ''}")