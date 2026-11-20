"""Run the eval questions through the real agent and save one result per question.

Queries are approved automatically, so the score measures the model alone.
Results are saved after every question: if the quota runs out, run again to resume.
Usage: uv run python eval/run_eval.py --prompt v1   (default v0)
"""
import asyncio
import json
import time
import argparse
from pathlib import Path

from google import genai
from mcp import Client

from nl_sql_agent.agent import PROMPTS, run_turn
from nl_sql_agent.client import DB_PATH, server_parameters
from nl_sql_agent.config import get_api_key, get_model_name
from nl_sql_agent.evaluation import rows_match
from nl_sql_agent.read_only import run_select
from nl_sql_agent.tool_policy import load_pins, verify_tools
from nl_sql_agent.tracing import TraceLog

QUESTIONS = Path("eval/questions.json")
PAUSE_SECONDS = 20  # stay well under the free-tier requests per minute


def score(item: dict, answer: str, result: dict | None, trace: TraceLog, seconds: float) -> dict:
    events = trace.events
    proposed = [e["args"]["sql"] for e in events if e["kind"] == "approval"]
    model_events = [e for e in events if e["kind"] == "model"]
    record = {
        **item,
        "answer": answer,
        "proposed_sql": proposed,
        "steps": len(model_events),
        "input_tokens": sum(e.get("input_tokens") or 0 for e in model_events),
        "output_tokens": sum((e.get("output_tokens") or 0) + (e.get("thinking_tokens") or 0)
                             for e in model_events),
        "seconds": round(seconds, 1),
    }
    if item["gold_sql"]:
        gold = run_select(DB_PATH, item["gold_sql"])["rows"]
        record["correct"] = rows_match(gold, result["rows"] if result else None)
    else:
        record["abstained"] = not proposed  # the right action is to propose no query
    return record


async def main(version: str) -> None:
    results_path = Path(f"eval/results_{version}.json")
    traces_path = Path(f"logs/traces_{version}.jsonl")     # una riga per evento, ignorato da Git
    questions = json.loads(QUESTIONS.read_text(encoding="utf-8"))
    results = json.loads(results_path.read_text(encoding="utf-8")) if results_path.exists() else []
    done = {r["id"] for r in results}
    llm, model = genai.Client(api_key=get_api_key()), get_model_name()

    async with Client(server_parameters()) as mcp_client:
        tools = (await mcp_client.list_tools()).tools
        verify_tools(tools, load_pins())
        for item in questions:
            if item["id"] in done:
                continue
            trace, started = TraceLog(traces_path), time.perf_counter()
            trace.event("question", id=item["id"], prompt=version, model=model)
            try:
                answer, result = await run_turn(llm, model, mcp_client, tools, [],
                                                item["question"], lambda sql: True, trace=trace,
                                                system_prompt=PROMPTS[version])
            except Exception as exc:  # quota or network: keep what is done, resume later
                print(f"Stopped at {item['id']}: {type(exc).__name__}: {exc}")
                break
            results.append(score(item, answer, result, trace, time.perf_counter() - started))
            results_path.write_text(json.dumps(results, indent=2, ensure_ascii=False) + "\n",
                                    encoding="utf-8")
            last = results[-1]
            print(f"{item['id']}: correct={last.get('correct')} abstained={last.get('abstained')}")
            await asyncio.sleep(PAUSE_SECONDS)
    print(f"{len(results)} of {len(questions)} questions in {results_path} (model {model})")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--prompt", choices=sorted(PROMPTS), default="v0")
    asyncio.run(main(parser.parse_args().prompt))