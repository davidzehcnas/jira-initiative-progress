from __future__ import annotations

import math
import unicodedata
from typing import Dict, List

from jira_utils.progress import (
    EpicProgress,
    STATUS_DONE,
    STATUS_IN_PROGRESS,
    STATUS_IN_REVIEW,
    STATUS_NOT_STARTED,
)

_WIDE_CATEGORIES = frozenset({"W", "F"})

_BLOCKS = 10

_COLUMNS = [
    ("Epic",            False),
    ("Progress",        False),
    ("⬜ Not started",  True),
    ("🟧 In progress",  True),
    ("🟪 In review",    True),
    ("🟩 Done",         True),
]


def percent(count: int, total: int) -> float:
    if total == 0:
        return 0.0
    return (count / total) * 100


def format_metric(count: int, total: int) -> str:
    return f"{percent(count, total):.1f}% ({count})"


def build_progress_bar(done_count: int, total: int) -> str:
    done_percent = percent(done_count, total)
    filled = min(_BLOCKS, math.floor((done_percent / 100.0) * _BLOCKS + 0.5))
    return ("🟩" * filled) + ("⬜" * (_BLOCKS - filled))


def escape_markdown(text: str) -> str:
    return text.replace("|", "\\|")


def display_width(text: str) -> int:
    return sum(
        2 if unicodedata.east_asian_width(ch) in _WIDE_CATEGORIES else 1
        for ch in text
    )


def _build_data_row(summary: str, counts: Dict[str, int]) -> List[str]:
    total = sum(counts.values())
    done = counts[STATUS_DONE]
    epic_label = escape_markdown(summary)
    if total > 0 and done == total:
        epic_label = "* " + epic_label
    return [
        epic_label,
        build_progress_bar(done, total),
        format_metric(counts[STATUS_NOT_STARTED], total),
        format_metric(counts[STATUS_IN_PROGRESS], total),
        format_metric(counts[STATUS_IN_REVIEW], total),
        format_metric(done, total),
    ]


def render_markdown_table(rows: List[EpicProgress]) -> str:
    headers = [name for name, _ in _COLUMNS]
    right = [r for _, r in _COLUMNS]

    data_rows: List[List[str]] = [
        _build_data_row(row.summary, row.counts)
        for row in rows
    ]

    totals: Dict[str, int] = {}
    for row in rows:
        for key, value in row.counts.items():
            totals[key] = totals.get(key, 0) + value
    data_rows.append(_build_data_row("Total", totals))

    col_widths = [display_width(h) for h in headers]
    for data_row in data_rows:
        for col, cell in enumerate(data_row):
            col_widths[col] = max(col_widths[col], display_width(cell))

    def pad(text: str, col: int) -> str:
        padding = " " * max(0, col_widths[col] - display_width(text))
        return (padding + text) if right[col] else (text + padding)

    def sep(col: int) -> str:
        w = col_widths[col]
        return ("-" * (w - 1) + ":") if right[col] else ("-" * w)

    lines = [
        "| " + " | ".join(pad(h, i) for i, h in enumerate(headers)) + " |",
        "| " + " | ".join(sep(i) for i in range(len(headers))) + " |",
    ]
    for data_row in data_rows:
        lines.append("| " + " | ".join(pad(cell, i) for i, cell in enumerate(data_row)) + " |")

    return "\n".join(lines)
