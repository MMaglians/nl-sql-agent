"""Run one SELECT on the database, with limits enforced by SQLite itself."""
import sqlite3
import time
from pathlib import Path

from nl_sql_agent.schema import SCHEMA

MAX_ROWS = 200
MAX_SQL_CHARS = 4000
TIMEOUT_SECONDS = 3.0

ALLOWED_FUNCTIONS = {
    "abs", "avg", "coalesce", "count", "date", "ifnull", "julianday", "length",
    "like", "lower", "max", "min", "nullif", "round", "strftime", "substr",
    "sum", "total", "upper",
}


class QueryRejected(Exception):
    """The query was refused or could not be completed."""


def _authorizer(action, arg1, arg2, _db_name, _trigger):
    """Default deny: SQLite asks this function before each operation."""
    if action == sqlite3.SQLITE_SELECT:
        return sqlite3.SQLITE_OK
    if action == sqlite3.SQLITE_READ and arg1 in SCHEMA:
        return sqlite3.SQLITE_OK
    if action == sqlite3.SQLITE_FUNCTION and arg2.lower() in ALLOWED_FUNCTIONS:
        return sqlite3.SQLITE_OK
    return sqlite3.SQLITE_DENY

def open_read_only(db_path: Path) -> sqlite3.Connection:
    """Open the file so that this connection can never write to it."""
    uri = f"{Path(db_path).resolve().as_uri()}?mode=ro" #mode=ro indicates that the db is open in read-only mode
    return sqlite3.connect(uri, uri=True)


def run_select(
    db_path: Path,
    sql: str,
    max_rows: int = MAX_ROWS,
    timeout_seconds: float = TIMEOUT_SECONDS,
) -> dict:
    if len(sql) > MAX_SQL_CHARS:
        raise QueryRejected(f"Query longer than {MAX_SQL_CHARS} characters")
    if not sql.strip().upper().startswith(("SELECT", "WITH")):
        raise QueryRejected("Only SELECT queries are allowed")

    conn = open_read_only(db_path)
    try:
        conn.set_authorizer(_authorizer) #record the function that SQLite queries before each operation.
        deadline = time.monotonic() + timeout_seconds
        conn.set_progress_handler(lambda: time.monotonic() > deadline, 10_000) #stops too long queries.
        cursor = conn.execute(sql)
        columns = [item[0] for item in cursor.description or []]
        rows = cursor.fetchmany(max_rows + 1)
    except (sqlite3.Error, sqlite3.Warning) as exc:
        raise QueryRejected(str(exc)) from exc
    finally:
        conn.close()

    return {
        "columns": columns,
        "rows": [list(row) for row in rows[:max_rows]],
        "truncated": len(rows) > max_rows,
    }