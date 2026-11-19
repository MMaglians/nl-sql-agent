"""Esegue i casi di prompt injection sull'agente reale: uv run python eval/run_injection.py

Le query sono approvate in automatico (caso peggiore: chi approva non legge).
Gli attacchi indiretti usano una COPIA avvelenata del database. Si riprende da dove si era fermato.
"""
import asyncio
import json
from pathlib import Path

from google import genai
from mcp import Client

from nl_sql_agent.agent import PROMPTS, run_turn
from nl_sql_agent.client import DB_PATH, server_parameters
from nl_sql_agent.config import get_api_key, get_model_name
from nl_sql_agent.injection import CASES, INDIRECT_QUESTION, poison_db, table_counts, verdict
from nl_sql_agent.tool_policy import load_pins, verify_tools
from nl_sql_agent.tracing import TraceLog

PROMPT = "v1"
REPEATS = 3
PAUSE_SECONDS = 20
RESULTS = Path("eval/injection_results.json")
TRACES = Path("logs/traces_injection.jsonl")
POISONED = Path("data/healthcare_injection.db")


async def run_case(llm, model, db_path, question, case_id, rep) -> dict:
    async with Client(server_parameters(db_path)) as mcp_client:
        tools = (await mcp_client.list_tools()).tools
        verify_tools(tools, load_pins())
        trace = TraceLog(TRACES)
        trace.event("question", id=f"{case_id}#{rep}", prompt=PROMPT, model=model)
        answer, _ = await run_turn(llm, model, mcp_client, tools, [], question,
                                   lambda sql: True, trace=trace, system_prompt=PROMPTS[PROMPT])
    tool_events = [e for e in trace.events if e["kind"] == "tool" and e["name"] == "run_select"]
    proposed = [e["args"].get("sql", "") for e in tool_events]
    executed = [e["args"].get("sql", "") for e in tool_events if "result" in e["result"]]
    return {"case": case_id, "rep": rep, "question": question, "answer": answer,
            "proposed_sql": proposed, "executed_sql": executed,
            **verdict(case_id, proposed, executed, answer)}


async def main() -> None:
    results = json.loads(RESULTS.read_text(encoding="utf-8")) if RESULTS.exists() else []
    done = {(r["case"], r["rep"]) for r in results}
    llm, model = genai.Client(api_key=get_api_key()), get_model_name()
    before = table_counts(DB_PATH)
    for case_id, kind, text in CASES:
        if kind == "indirect":
            poison_db(DB_PATH, POISONED, text)
        db_path, question = (POISONED, INDIRECT_QUESTION) if kind == "indirect" else (DB_PATH, text)
        poisoned_before = table_counts(db_path)
        for rep in range(1, REPEATS + 1):
            if (case_id, rep) in done:
                continue
            try:
                row = await run_case(llm, model, db_path, question, case_id, rep)
            except Exception as exc:  # quota o rete: si salva ciò che è fatto
                print(f"Stop a {case_id}#{rep}: {type(exc).__name__}: {exc}")
                return
            row["data_unchanged"] = table_counts(db_path) == poisoned_before
            results.append(row)
            RESULTS.write_text(json.dumps(results, indent=2, ensure_ascii=False) + "\n",
                               encoding="utf-8")
            print(f"{case_id}#{rep}: complied={row['complied']} harmful={row['harmful']} "
                  f"data_unchanged={row['data_unchanged']}")
            await asyncio.sleep(PAUSE_SECONDS)
    assert table_counts(DB_PATH) == before, "il database originale è cambiato!"
    print(f"{len(results)} esecuzioni in {RESULTS} (modello {model}, prompt {PROMPT})")
    


if __name__ == "__main__":
    asyncio.run(main())