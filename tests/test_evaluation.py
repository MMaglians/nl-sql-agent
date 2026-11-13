import pytest

from nl_sql_agent.evaluation import rows_match, summarize, values_match, wilson


def test_wilson_known_values():
    low, high = wilson(20, 20)
    assert high == 1.0 and low == pytest.approx(0.839, abs=1e-3)
    assert wilson(0, 0) == (0.0, 1.0)


def test_numbers_match_up_to_rounding():
    assert values_match(8852.7812, 8852.78)
    assert values_match(68.1534, 68.2)
    assert not values_match(62, 49)
    assert values_match("Middlesex County", " middlesex county")


def test_rows_in_any_order_and_with_extra_columns():
    gold = [["F", 62], ["M", 49]]
    assert rows_match(gold, [["M", 49], ["F", 62]])
    assert rows_match(gold, [["Female", "F", 62], ["Male", "M", 49]])


def test_wrong_or_missing_rows_do_not_match():
    gold = [["F", 62], ["M", 49]]
    assert not rows_match(gold, None)
    assert not rows_match(gold, [["F", 62]])
    assert not rows_match(gold, [["F", 62], ["M", 50]])
    assert not rows_match([[5]], [[5], [6]])


def test_summarize_separates_the_two_kinds_of_question():
    results = [
        {"gold_sql": "x", "correct": True, "steps": 3},
        {"gold_sql": "x", "correct": False, "steps": 5},
        {"gold_sql": None, "abstained": True, "steps": 1},
    ]
    summary = summarize(results)
    assert summary["execution_accuracy"][:2] == (1, 2)
    assert summary["abstention"][:2] == (1, 1)
    assert summary["median_steps"] == 3