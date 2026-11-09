"""Client-side policy: which tools may be used, and with which exact definition."""
import hashlib
import json
from pathlib import Path

ALLOWED_TOOLS = ("list_tables", "describe_table", "run_select")
PINS_PATH = Path("tool_pins.json")


class ToolPolicyError(Exception):
    """The server does not match what was reviewed and approved."""


def fingerprint(tool) -> str:
    """Hash everything the model would read about a tool."""
    payload = json.dumps(
        {
            "name": tool.name,
            "description": tool.description,
            "input_schema": tool.input_schema,
        },
        sort_keys=True,
    )
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def verify_tools(tools: list, pins: dict[str, str]) -> None:
    """Fail closed unless the tools are exactly the approved ones."""
    names = {tool.name for tool in tools}
    if names != set(ALLOWED_TOOLS):
        raise ToolPolicyError(f"Unexpected tool set: {sorted(names)}")
    for tool in tools:
        if pins.get(tool.name) != fingerprint(tool):
            raise ToolPolicyError(f"Definition changed for tool: {tool.name}")


def load_pins() -> dict[str, str]:
    return json.loads(PINS_PATH.read_text(encoding="utf-8"))


def save_pins(tools: list) -> None:
    pins = {tool.name: fingerprint(tool) for tool in tools}
    PINS_PATH.write_text(json.dumps(pins, indent=2, sort_keys=True) + "\n", encoding="utf-8")