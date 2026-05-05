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

_BLOCKS = 20

_COLUMNS = [
    "Epic",
    "Progress",
    "⬜ Not started",
    "🟧 In progress",
    "🟪 In review",
    "🟩 Done",
]


def percent(count: int, total: int) -> float:
    if total == 0:
        return 0.0
    return (count / total) * 100


def format_metric(count: int, total: int) -> str:
    return f"{percent(count, total):.1f}% ({count})"


def build_progress_bar(counts: Dict[str, int], total: int) -> str:
    if total == 0:
        return "⬜" * _BLOCKS

    done_blocks = math.floor((counts[STATUS_DONE] / total) * _BLOCKS + 0.5)
    review_blocks = math.floor((counts[STATUS_IN_REVIEW] / total) * _BLOCKS + 0.5)
    progress_blocks = math.floor((counts[STATUS_IN_PROGRESS] / total) * _BLOCKS + 0.5)

    # Clamp total assigned blocks to _BLOCKS
    assigned = done_blocks + review_blocks + progress_blocks
    not_started_blocks = _BLOCKS - min(assigned, _BLOCKS)

    # If rounding caused overflow, trim from the right (not_started first, then progress)
    if assigned > _BLOCKS:
        overflow = assigned - _BLOCKS
        progress_blocks = max(0, progress_blocks - overflow)
        overflow = assigned - (done_blocks + review_blocks + progress_blocks + not_started_blocks)
        if overflow > 0:
            review_blocks = max(0, review_blocks - overflow)

    return (
        "🟩" * done_blocks
        + "🟪" * review_blocks
        + "🟧" * progress_blocks
        + "⬜" * not_started_blocks
    )


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
        build_progress_bar(counts, total),
        format_metric(counts[STATUS_NOT_STARTED], total),
        format_metric(counts[STATUS_IN_PROGRESS], total),
        format_metric(counts[STATUS_IN_REVIEW], total),
        format_metric(done, total),
    ]


def render_markdown_table(rows: List[EpicProgress]) -> str:
    headers = _COLUMNS

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

    def pad_center(text: str, col: int) -> str:
        total = col_widths[col]
        w = display_width(text)
        left = (total - w) // 2
        return " " * left + text + " " * (total - w - left)

    def pad_left(text: str, col: int) -> str:
        return text + " " * (col_widths[col] - display_width(text))

    def pad_right(text: str, col: int) -> str:
        return " " * (col_widths[col] - display_width(text)) + text

    def pad_data(text: str, col: int) -> str:
        return pad_left(text, col) if col == 0 else pad_right(text, col)

    def sep(col: int) -> str:
        return ":" + "-" * max(1, col_widths[col] - 2) + ":"

    lines = [
        "| " + " | ".join(pad_center(h, i) for i, h in enumerate(headers)) + " |",
        "| " + " | ".join(sep(i) for i in range(len(headers))) + " |",
    ]
    for data_row in data_rows:
        lines.append("| " + " | ".join(pad_data(cell, i) for i, cell in enumerate(data_row)) + " |")

    return "\n".join(lines)
