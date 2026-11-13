"""Run the eval questions through the real agent and save one result per question.

Queries are approved automatically, so the score measures the model alone.
Results are saved after every question: if the quota runs out, run again to resume.
"""
import asyncio
import json
import time
from pathlib import Path

from google import genai
from mcp import Client

from nl_sql_agent.agent import run_turn
from nl_sql_agent.client import DB_PATH, server_parameters
from nl_sql_agent.config import get_api_key, get_model_name
from nl_sql_agent.evaluation import rows_match
from nl_sql_agent.read_only import run_select
from nl_sql_agent.tool_policy import load_pins, verify_tools
from nl_sql_agent.tracing import TraceLog

QUESTIONS = Path("eval/questions.json")
RESULTS = Path("eval/results_v0.json")
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


async def main() -> None:
    questions = json.loads(QUESTIONS.read_text(encoding="utf-8"))
    results = json.loads(RESULTS.read_text(encoding="utf-8")) if RESULTS.exists() else []
    done = {r["id"] for r in results}
    llm, model = genai.Client(api_key=get_api_key()), get_model_name()

    async with Client(server_parameters()) as mcp_client:
        tools = (await mcp_client.list_tools()).tools
        verify_tools(tools, load_pins())
        for item in questions:
            if item["id"] in done:
                continue
            trace, started = TraceLog(), time.perf_counter()
            try:
                answer, result = await run_turn(llm, model, mcp_client, tools, [],
                                                item["question"], lambda sql: True, trace=trace)
            except Exception as exc:  # quota or network: keep what is done, resume later
                print(f"Stopped at {item['id']}: {type(exc).__name__}: {exc}")
                break
            results.append(score(item, answer, result, trace, time.perf_counter() - started))
            RESULTS.write_text(json.dumps(results, indent=2, ensure_ascii=False) + "\n",
                               encoding="utf-8")
            last = results[-1]
            print(f"{item['id']}: correct={last.get('correct')} abstained={last.get('abstained')}")
            await asyncio.sleep(PAUSE_SECONDS)
    print(f"{len(results)} of {len(questions)} questions in {RESULTS} (model {model})")


if __name__ == "__main__":
    asyncio.run(main())