import pytest

from nl_sql_agent.read_only import QueryRejected, run_select


def test_select_returns_rows(db_path):
    result = run_select(db_path, "SELECT COUNT(*) AS n FROM patients")
    assert result == {"columns": ["n"], "rows": [[10]], "truncated": False}


def test_like_cte_and_subquery_are_allowed(db_path):
    sql = """
    WITH women AS (SELECT id FROM patients WHERE gender LIKE 'f')
    SELECT COUNT(*) FROM (SELECT id FROM women)
    """
    assert run_select(db_path, sql)["rows"] == [[5]]


def test_rows_are_truncated(db_path):
    result = run_select(db_path, "SELECT id FROM patients", max_rows=3)
    assert len(result["rows"]) == 3
    assert result["truncated"] is True


@pytest.mark.parametrize(
    "sql",
    [
        "",
        "EXPLAIN SELECT 1",
        "DELETE FROM patients",
        "DROP TABLE patients",
        "UPDATE patients SET gender = 'X'",
        "INSERT INTO patients (id) VALUES ('new')",
        "CREATE TABLE stolen (x)",
        "PRAGMA table_info(patients)",
        "ATTACH DATABASE 'other.db' AS other",
        "SELECT * FROM sqlite_master",
        "SELECT load_extension('evil')",
        "SELECT randomblob(1000000000)",
        "SELECT 1; DROP TABLE patients",
        "WITH RECURSIVE c(x) AS (SELECT 1 UNION ALL SELECT x + 1 FROM c) SELECT COUNT(*) FROM c",
    ],
)
def test_dangerous_queries_are_refused(db_path, sql):
    with pytest.raises(QueryRejected):
        run_select(db_path, sql)


def test_database_is_unchanged_after_attacks(db_path):
    with pytest.raises(QueryRejected):
        run_select(db_path, "DELETE FROM patients")
    assert run_select(db_path, "SELECT COUNT(*) FROM patients")["rows"] == [[10]]


def test_slow_query_is_stopped(db_path):
    sql = "SELECT COUNT(*) FROM patients a, patients b, patients c, patients d, patients e"
    with pytest.raises(QueryRejected):
        run_select(db_path, sql, timeout_seconds=-1)


def test_too_long_query_is_refused(db_path):
    with pytest.raises(QueryRejected):
        run_select(db_path, "SELECT 1 " + " " * 5000)