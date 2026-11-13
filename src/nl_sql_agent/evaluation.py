"""Scoring for the NL→SQL eval: compare the agent's last query result with a gold query."""
import math
from statistics import median


def wilson(successes: int, n: int, z: float = 1.96) -> tuple[float, float]:
    """95% Wilson interval for a proportion."""
    if n == 0:
        return (0.0, 1.0)
    p = successes / n
    centre = (p + z * z / (2 * n)) / (1 + z * z / n)
    half = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / (1 + z * z / n)
    return (max(0.0, centre - half), min(1.0, centre + half))


def values_match(gold, got) -> bool:
    """Numbers match up to rounding; text matches ignoring case and spaces."""
    numbers = (int, float)
    if isinstance(gold, numbers) and isinstance(got, numbers):
        return math.isclose(gold, got, rel_tol=1e-3, abs_tol=0.05)
    if gold is None or got is None:
        return gold is got
    return str(gold).strip().lower() == str(got).strip().lower()


def row_matches(gold_row: list, got_row: list) -> bool:
    """Every gold value appears in the agent's row; extra columns are allowed."""
    unused = list(got_row)
    for value in gold_row:
        hit = next((i for i, other in enumerate(unused) if values_match(value, other)), None)
        if hit is None:
            return False
        unused.pop(hit)
    return True


def rows_match(gold_rows: list, got_rows: list | None) -> bool:
    """Same number of rows, in any order, each gold row matched by a different agent row."""
    if got_rows is None or len(gold_rows) != len(got_rows):
        return False
    unused = list(got_rows)
    for gold_row in gold_rows:
        hit = next((i for i, row in enumerate(unused) if row_matches(gold_row, row)), None)
        if hit is None:
            return False
        unused.pop(hit)
    return True


def summarize(results: list[dict]) -> dict:
    """Metrics for the report: accuracy with intervals, abstention, steps, tokens, time."""
    answerable = [r for r in results if r["gold_sql"]]
    impossible = [r for r in results if not r["gold_sql"]]
    correct = sum(r["correct"] for r in answerable)
    abstained = sum(r["abstained"] for r in impossible)

    def med(key):
        values = [r[key] for r in results if r.get(key) is not None]
        return median(values) if values else None

    return {
        "execution_accuracy": (correct, len(answerable), wilson(correct, len(answerable))),
        "abstention": (abstained, len(impossible), wilson(abstained, len(impossible))),
        "median_steps": med("steps"),
        "median_input_tokens": med("input_tokens"),
        "median_output_tokens": med("output_tokens"),
        "median_seconds": med("seconds"),
    }