"""Connect to the MCP server as a separate process and try its tools."""
import asyncio
import os
import sys
from pathlib import Path

from mcp import Client, StdioServerParameters

from nl_sql_agent.tool_policy import ALLOWED_TOOLS, ToolPolicyError, load_pins, save_pins, verify_tools

DB_PATH = Path("data/healthcare.db").resolve()


def server_parameters() -> StdioServerParameters:
    return StdioServerParameters(
        command=sys.executable,
        args=["-m", "nl_sql_agent.server"],
        env={"NL_SQL_DB": str(DB_PATH)},
    )


async def call(client: Client, name: str, arguments: dict):
    if name not in ALLOWED_TOOLS:
        raise ToolPolicyError(f"Tool not allowed: {name}")
    result = await client.call_tool(name, arguments)
    if result.is_error:
        return f"REFUSED: {result.content[0].text}"
    return result.structured_content


async def pin() -> None:
    async with Client(server_parameters()) as client:
        tools = (await client.list_tools()).tools
        for tool in tools:
            print(f"--- {tool.name}\n{tool.description}\n{tool.input_schema}")
        save_pins(tools)
        print("Pins written to tool_pins.json")


async def demo() -> None:
    async with Client(server_parameters()) as client:
        tools = (await client.list_tools()).tools
        verify_tools(tools, load_pins())
        print("Tools verified:", [tool.name for tool in tools])
        print(await call(client, "list_tables", {}))
        count = "SELECT gender, COUNT(*) AS n FROM patients GROUP BY gender"
        print(await call(client, "run_select", {"sql": count}))
        print(await call(client, "run_select", {"sql": "DELETE FROM patients"}))


if __name__ == "__main__":
    asyncio.run(pin() if "--pin" in sys.argv else demo())