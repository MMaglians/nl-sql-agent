from nl_sql_agent.trace_view import load_events, split_by_question, summarize_run
from nl_sql_agent.tracing import TraceLog


def test_traces_are_split_and_summarized(tmp_path):
    path = tmp_path / "t.jsonl"
    for qid in ("q01", "x01", "q01"):              # q01 ripetuta: vale l'ultima
        trace = TraceLog(path)
        trace.event("question", id=qid)
        trace.event("model", step=1, seconds=0.5, input_tokens=100)
        trace.event("tool", step=1, name="run_select", args={"sql": "PRAGMA x"},
                    result={"error": "Query refused"})
        trace.event("model", step=2, seconds=0.25, input_tokens=120)
    runs = split_by_question(load_events(path))
    assert list(runs) == ["q01", "x01"] and len(runs["q01"]) == 4
    s = summarize_run(runs["x01"])
    assert s["steps"] == 2 and s["refused"] == ["PRAGMA x"]
    assert s["input_tokens"] == 220 and s["model_seconds"] == 0.8 and not s["hit_limit"]