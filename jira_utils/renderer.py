from __future__ import annotations

import math
import unicodedata
from typing import Dict, List

from jira_utils.progress import EpicProgress


def percent(count: int, total: int) -> float:
    if total == 0:
        return 0.0
    return (count / total) * 100


def format_metric(count: int, total: int) -> str:
    return f"{percent(count, total):.1f}% ({count})"


def build_progress_bar(done_count: int, total: int, blocks: int) -> str:
    if blocks <= 0:
        return ""
    done_percent = percent(done_count, total)
    filled = min(blocks, math.floor((done_percent / 100.0) * blocks + 0.5))
    return ("🟩" * filled) + ("⬜" * (blocks - filled))


def escape_markdown(text: str) -> str:
    return text.replace("|", "\\|")


def display_width(text: str) -> int:
    """Return the number of terminal columns needed to display text.

    Emoji and other wide characters occupy two columns each.
    """
    width = 0
    for ch in text:
        eaw = unicodedata.east_asian_width(ch)
        width += 2 if eaw in ("W", "F") else 1
    return width


def render_markdown_table(rows: List[EpicProgress], blocks: int, include_total: bool) -> str:
    HEADERS = ["Epic", "Progress", "⬜ Not started", "🟧 In progress", "🟪 In review", "🟩 Done"]
    RIGHT   = [False,  False,      True,             True,             True,           True]

    def build_data_row(summary: str, done: int, total: int, counts: Dict[str, int]) -> List[str]:
        progress = f"{build_progress_bar(done, total, blocks)} {format_metric(done, total)}".strip()
        return [
            escape_markdown(summary),
            progress,
            format_metric(counts["not_started"], total),
            format_metric(counts["in_progress"], total),
            format_metric(counts["in_review"], total),
            format_metric(done, total),
        ]

    data_rows: List[List[str]] = [
        build_data_row(row.summary, row.counts["done"], row.total, row.counts)
        for row in rows
    ]

    if include_total:
        totals: Dict[str, int] = {"not_started": 0, "in_progress": 0, "in_review": 0, "done": 0}
        for row in rows:
            for key, value in row.counts.items():
                totals[key] += value
        grand_total = sum(totals.values())
        total_row = build_data_row("Total", totals["done"], grand_total, totals)
        total_row = list(total_row)
        data_rows.append(total_row)

    # Compute the display width of the widest value in each column.
    col_widths = [display_width(h) for h in HEADERS]
    for data_row in data_rows:
        for col, cell in enumerate(data_row):
            col_widths[col] = max(col_widths[col], display_width(cell))

    def pad(text: str, col: int) -> str:
        padding = " " * max(0, col_widths[col] - display_width(text))
        return (padding + text) if RIGHT[col] else (text + padding)

    def sep(col: int) -> str:
        w = col_widths[col]
        return ("-" * (w - 1) + ":") if RIGHT[col] else ("-" * w)

    lines = [
        "| " + " | ".join(pad(h, i) for i, h in enumerate(HEADERS)) + " |",
        "| " + " | ".join(sep(i) for i in range(len(HEADERS))) + " |",
    ]
    for data_row in data_rows:
        lines.append("| " + " | ".join(pad(cell, i) for i, cell in enumerate(data_row)) + " |")

    return "\n".join(lines)
