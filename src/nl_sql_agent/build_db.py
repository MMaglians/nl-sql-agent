"""Build data/healthcare.db from the Synthea CSV files in data/raw."""
import csv
import sqlite3
from pathlib import Path

from nl_sql_agent.schema import SCHEMA, create_table_sql

RAW_DIR = Path("data/raw")
DB_PATH = Path("data/healthcare.db")


def load_table(conn: sqlite3.Connection, table: str, csv_path: Path) -> int:
    columns = SCHEMA[table]
    placeholders = ", ".join("?" for _ in columns)
    conn.execute(create_table_sql(table))
    with csv_path.open(encoding="utf-8", newline="") as handle:
        # Only the columns listed in SCHEMA are read: the others never enter the database.
        rows = [
            [row[c.csv_name] or None for c in columns]
            for row in csv.DictReader(handle)
        ]
    conn.executemany(f"INSERT INTO {table} VALUES ({placeholders})", rows)
    return len(rows)


def main() -> None:
    DB_PATH.unlink(missing_ok=True)
    conn = sqlite3.connect(DB_PATH)
    try:
        for table in SCHEMA:
            count = load_table(conn, table, RAW_DIR / f"{table}.csv")
            print(f"{table}: {count} rows")
        conn.commit()
    finally:
        conn.close()
    print(f"Database written to {DB_PATH}")


if __name__ == "__main__":
    main()