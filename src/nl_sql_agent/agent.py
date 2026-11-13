"""NL→SQL agent: the model writes the SQL, a human approves it, the MCP server runs it."""
import asyncio
import time

from google.genai import types

from nl_sql_agent.bridge import to_declarations, to_response
from nl_sql_agent.retry import generate_with_retry
from nl_sql_agent.tool_policy import ALLOWED_TOOLS
from nl_sql_agent.tracing import TraceLog

NEEDS_APPROVAL = {"run_select"}

SYSTEM_PROMPT = (
    "Sei un analista di dati sanitari. Rispondi in italiano, in modo breve. "
    "Il database SQLite contiene dati SINTETICI generati con Synthea: dillo se "
    "l'utente sembra crederli reali. Prima di scrivere SQL usa list_tables e "
    "describe_table: non inventare tabelle o colonne. Poi usa run_select con una "
    "sola SELECT in sintassi SQLite. Ogni numero della risposta deve venire dal "
    "risultato di run_select, mai dalla tua memoria. Se l'utente rifiuta una "
    "query, non riproporla uguale: chiedi cosa cambiare. Se la domanda non si può "
    "risolvere con questi dati, dillo. Alla fine indica la query usata."
)


def make_config(declarations) -> types.GenerateContentConfig:
    return types.GenerateContentConfig(
        system_instruction=SYSTEM_PROMPT,
        tools=[types.Tool(function_declarations=declarations)],
        automatic_function_calling=types.AutomaticFunctionCallingConfig(disable=True),
        temperature=0,
    )


def _usage(response) -> dict:
    meta = response.usage_metadata
    if meta is None:
        return {}
    return {
        "input_tokens": meta.prompt_token_count,
        "output_tokens": meta.candidates_token_count,
        "thinking_tokens": meta.thoughts_token_count,  # billed as output
    }


def _close(history: list, text: str) -> str:
    """End the turn with a model message, so roles keep alternating."""
    history.append(types.Content(role="model", parts=[types.Part(text=text)]))
    return text


async def execute(mcp_client, name: str, args: dict, confirm, trace: TraceLog) -> dict:
    """Policy first, then human approval, then the MCP server."""
    if name not in ALLOWED_TOOLS:
        return {"error": f"tool not allowed: {name}"}
    if name in NEEDS_APPROVAL:
        approved = await asyncio.to_thread(confirm, args.get("sql", ""))
        trace.event("approval", name=name, args=args, approved=approved)
        if not approved:
            return {"error": "The user rejected this query. Ask what to change."}
    result = await mcp_client.call_tool(name, args)
    return to_response(result)


async def run_turn(llm, model: str, mcp_client, mcp_tools: list, history: list,
                   user_text: str, confirm, *, max_steps: int = 6,
                   trace: TraceLog | None = None) -> tuple[str, dict | None]:
    """One turn. Returns the answer and the last successful query result."""
    trace = trace or TraceLog()
    config = make_config(to_declarations(mcp_tools))
    history.append(types.Content(role="user", parts=[types.Part(text=user_text)]))
    trace.event("user", text=user_text)
    last_result = None

    for step in range(1, max_steps + 1):
        started = time.perf_counter()
        response = await asyncio.to_thread(
            generate_with_retry, llm, model=model, contents=history, config=config
        )
        trace.event("model", step=step, seconds=round(time.perf_counter() - started, 2),
                    **_usage(response))

        if not response.candidates or response.candidates[0].content is None:
            trace.event("error", step=step, text="empty response")
            return _close(history, "Il modello non ha prodotto una risposta. Riprova."), last_result

        history.append(response.candidates[0].content)  # intact, thought signatures included
        calls = response.function_calls or []
        if not calls:
            answer = response.text or ""
            trace.event("final", step=step, text=answer)
            return answer, last_result

        parts = []
        for call in calls:
            args = dict(call.args or {})
            result = await execute(mcp_client, call.name, args, confirm, trace)
            trace.event("tool", step=step, name=call.name, args=args, result=result)
            if call.name == "run_select" and "result" in result:
                last_result = result["result"]
            parts.append(types.Part.from_function_response(name=call.name, response=result))
        history.append(types.Content(role="user", parts=parts))

    trace.event("limit", max_steps=max_steps)
    return _close(history, f"Mi fermo: ho raggiunto il limite di {max_steps} passi."), last_result