"""Bar chart of a query result with one label column and one numeric column."""
from pathlib import Path

import matplotlib

matplotlib.use("Agg")  # write to file, no window
import matplotlib.pyplot as plt  # noqa: E402


def can_plot(result: dict | None) -> bool:
    if not result or len(result["columns"]) != 2 or not result["rows"]:
        return False
    return all(isinstance(row[1], (int, float)) for row in result["rows"])


def save_bar_chart(result: dict, path: Path, max_bars: int = 20) -> Path:
    rows = result["rows"][:max_bars]
    labels = [str(row[0]) for row in rows]
    values = [row[1] for row in rows]
    fig, ax = plt.subplots(figsize=(8, max(3, 0.4 * len(rows))))
    ax.barh(labels[::-1], values[::-1])
    ax.set_xlabel(result["columns"][1])
    ax.set_ylabel(result["columns"][0])
    fig.tight_layout()
    path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(path, dpi=120)
    plt.close(fig)
    return path