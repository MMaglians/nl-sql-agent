"""Turn MCP tools into Gemini declarations, and MCP results into Gemini responses."""
from google.genai import types


def to_declarations(mcp_tools: list) -> list[types.FunctionDeclaration]:
    """The model sees exactly what the server declares: the definitions verified by the pins."""
    return [
        types.FunctionDeclaration(
            name=tool.name,
            description=tool.description,
            parameters_json_schema=tool.input_schema,
        )
        for tool in mcp_tools
    ]


def to_response(result) -> dict:
    """Gemini wants a dict: the data under "result", or the error under "error"."""
    if result.is_error:
        return {"error": result.content[0].text if result.content else "unknown error"}
    return {"result": result.structured_content}