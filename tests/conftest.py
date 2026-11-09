import sqlite3

import pytest

from nl_sql_agent.schema import SCHEMA, create_table_sql


@pytest.fixture
def db_path(tmp_path):
    """A small database with the real schema: the tests never need the CSV files."""
    path = tmp_path / "test.db"
    conn = sqlite3.connect(path)
    for table in SCHEMA:
        conn.execute(create_table_sql(table))
    conn.executemany(
        "INSERT INTO patients (id, gender, birth_date) VALUES (?, ?, ?)",
        [(f"p{i}", "F" if i % 2 else "M", "1980-01-01") for i in range(10)],
    )
    conn.commit()
    conn.close()
    return path