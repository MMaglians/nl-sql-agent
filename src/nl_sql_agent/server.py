"""Read-only MCP server over the healthcare database."""
import os
import sys
from pathlib import Path

from mcp.server.mcpserver import MCPServer
from mcp.server.mcpserver.exceptions import ToolError
from mcp.types import ToolAnnotations
from pydantic import BaseModel

from nl_sql_agent import read_only
from nl_sql_agent.schema import SCHEMA, TABLE_DESCRIPTIONS

READ_ONLY_TOOL = ToolAnnotations(
    read_only_hint=True,
    destructive_hint=False,
    idempotent_hint=True,
    open_world_hint=False,
)


class QueryResult(BaseModel):
    columns: list[str]
    rows: list[list[str | int | float | None]]
    truncated: bool


def create_server(db_path: Path) -> MCPServer:
    server = MCPServer("healthcare-sql")

    @server.tool(annotations=READ_ONLY_TOOL)
    def list_tables() -> dict[str, str]:
        """List the tables of the database with a short description."""
        return TABLE_DESCRIPTIONS

    @server.tool(annotations=READ_ONLY_TOOL)
    def describe_table(table: str) -> list[dict[str, str]]:
        """Return name, SQL type and meaning of each column of a table."""
        if table not in SCHEMA:
            raise ToolError(f"Unknown table: {table}")
        return [
            {"name": c.name, "type": c.sql_type, "description": c.description}
            for c in SCHEMA[table]
        ]

    @server.tool(annotations=READ_ONLY_TOOL)
    def run_select(sql: str) -> QueryResult:
        """Run one read-only SELECT in SQLite syntax and return at most 200 rows."""
        try:
            return QueryResult(**read_only.run_select(db_path, sql))
        except read_only.QueryRejected as exc:
            raise ToolError(f"Query refused: {exc}") from exc

    return server


def main() -> None:
    db_path = Path(os.environ.get("NL_SQL_DB", "data/healthcare.db"))
    if not db_path.is_file():
        sys.exit(f"Database not found: {db_path}")
    create_server(db_path).run()


if __name__ == "__main__":
    main()