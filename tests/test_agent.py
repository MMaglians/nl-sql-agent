import asyncio

from google.genai import types
from mcp import Client

from nl_sql_agent.agent import run_turn
from nl_sql_agent.server import create_server
from nl_sql_agent.tracing import TraceLog


def text_response(text):
    content = types.Content(role="model", parts=[types.Part(text=text)])
    return types.GenerateContentResponse(candidates=[types.Candidate(content=content)])


def call_response(name, args):
    part = types.Part(function_call=types.FunctionCall(name=name, args=args))
    content = types.Content(role="model", parts=[part])
    return types.GenerateContentResponse(candidates=[types.Candidate(content=content)])


class FakeModels:
    def __init__(self, responses=None, always=None):
        self.responses, self.always, self.calls = list(responses or []), always, 0
        self.last_config = None

    def generate_content(self, model, contents, config):
        self.calls += 1
        self.last_config = config
        return self.always if self.always is not None else self.responses.pop(0)


class FakeLLM:
    def __init__(self, **kw):
        self.models = FakeModels(**kw)


def run(db_path, llm, confirm, max_steps=6):
    """Real MCP server in memory, fake model, scripted human."""
    async def go():
        async with Client(create_server(db_path)) as mcp_client:
            tools = (await mcp_client.list_tools()).tools
            history, trace = [], TraceLog()
            answer, result = await run_turn(llm, "m", mcp_client, tools, history, "domanda",
                                            confirm, max_steps=max_steps, trace=trace)
            return answer, result, history, trace
    return asyncio.run(go())


def tool_results(history):
    return [p.function_response.response for c in history for p in c.parts if p.function_response]


COUNT = "SELECT gender, COUNT(*) AS n FROM patients GROUP BY gender"


def test_approved_query_is_executed(db_path):
    llm = FakeLLM(responses=[call_response("run_select", {"sql": COUNT}), text_response("5 e 5")])
    seen = []
    answer, result, history, trace = run(db_path, llm, lambda sql: seen.append(sql) or True)
    assert answer == "5 e 5"
    assert seen == [COUNT]
    assert result["rows"] == [["F", 5], ["M", 5]]
    assert [c.role for c in history] == ["user", "model", "user", "model"]


def test_rejected_query_never_reaches_the_server(db_path):
    llm = FakeLLM(responses=[call_response("run_select", {"sql": COUNT}), text_response("ok")])
    answer, result, history, trace = run(db_path, llm, lambda sql: False)
    assert result is None
    assert "rejected" in tool_results(history)[0]["error"]
    assert [e["approved"] for e in trace.events if e["kind"] == "approval"] == [False]


def test_metadata_tools_need_no_approval(db_path):
    llm = FakeLLM(responses=[call_response("describe_table", {"table": "patients"}),
                             text_response("fatto")])
    def never(sql):
        raise AssertionError("confirm must not be called")
    answer, result, history, trace = run(db_path, llm, never)
    columns = tool_results(history)[0]["result"]
    assert answer == "fatto" and isinstance(columns, (list, dict))


def test_unknown_tool_is_refused(db_path):
    llm = FakeLLM(responses=[call_response("drop_database", {}), text_response("ok")])
    answer, result, history, trace = run(db_path, llm, lambda sql: True)
    assert "not allowed" in tool_results(history)[0]["error"]


def test_server_refusal_goes_back_to_the_model(db_path):
    llm = FakeLLM(responses=[call_response("run_select", {"sql": "DELETE FROM patients"}),
                             text_response("non posso")])
    answer, result, history, trace = run(db_path, llm, lambda sql: True)
    assert "Query refused" in tool_results(history)[0]["error"]
    assert answer == "non posso"


def test_step_limit_stops_the_agent(db_path):
    llm = FakeLLM(always=call_response("list_tables", {}))
    answer, result, history, trace = run(db_path, llm, lambda sql: True, max_steps=3)
    assert "limite di 3 passi" in answer and llm.models.calls == 3
    assert history[-1].role == "model"


def test_model_sees_the_server_declarations(db_path):
    llm = FakeLLM(responses=[text_response("ciao")])
    run(db_path, llm, lambda sql: True)
    names = [d.name for d in llm.models.last_config.tools[0].function_declarations]
    assert names == ["list_tables", "describe_table", "run_select"]