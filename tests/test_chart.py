from nl_sql_agent.chart import can_plot, save_bar_chart


def test_two_columns_with_numbers_can_be_plotted(tmp_path):
    result = {"columns": ["gender", "n"], "rows": [["F", 62], ["M", 49]], "truncated": False}
    assert can_plot(result)
    path = save_bar_chart(result, tmp_path / "c.png")
    assert path.stat().st_size > 0


def test_other_shapes_are_not_plotted():
    assert not can_plot(None)
    assert not can_plot({"columns": ["a", "b", "c"], "rows": [[1, 2, 3]], "truncated": False})
    assert not can_plot({"columns": ["a", "b"], "rows": [["x", "y"]], "truncated": False})
    assert not can_plot({"columns": ["a", "b"], "rows": [], "truncated": False})