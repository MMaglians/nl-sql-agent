"""Legge un file di tracce .jsonl e lo divide per domanda: funzioni pure, testabili."""
import json
from pathlib import Path


def load_events(path: Path) -> list[dict]:
    lines = Path(path).read_text(encoding="utf-8").splitlines()
    return [json.loads(line) for line in lines if line.strip()]


def split_by_question(events: list[dict]) -> dict[str, list[dict]]:
    """Un evento 'question' apre un blocco; se una domanda è stata ripetuta, vale l'ultimo."""
    runs, current = {}, None
    for event in events:
        if event["kind"] == "question":
            current = event["id"]
            runs[current] = []
        if current is not None:
            runs[current].append(event)
    return runs


def summarize_run(events: list[dict]) -> dict:
    """Passi, tool chiamati, query rifiutate dal server, token e tempo del modello."""
    tools = [e for e in events if e["kind"] == "tool"]
    models = [e for e in events if e["kind"] == "model"]
    return {
        "steps": len(models),
        "tools": [e["name"] for e in tools],
        "refused": [e["args"].get("sql") for e in tools if "error" in e["result"]],
        "input_tokens": sum(e.get("input_tokens") or 0 for e in models),
        "model_seconds": round(float(sum(e.get("seconds") or 0 for e in models)), 1),
        "hit_limit": any(e["kind"] == "limit" for e in events),
    }