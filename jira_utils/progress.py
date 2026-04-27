from __future__ import annotations

import sys
from collections import Counter
from dataclasses import dataclass
from typing import Dict, List, Optional

from jira_utils.client import JiraClient

# Canonical status buckets used for classification and counting.
STATUS_NOT_STARTED = "not_started"
STATUS_IN_PROGRESS = "in_progress"
STATUS_IN_REVIEW = "in_review"
STATUS_DONE = "done"

STATUSES = (STATUS_NOT_STARTED, STATUS_IN_PROGRESS, STATUS_IN_REVIEW, STATUS_DONE)


@dataclass
class EpicProgress:
    summary: str
    counts: Dict[str, int]

    @property
    def total(self) -> int:
        return sum(self.counts.values())


def fetch_epics(client: JiraClient, initiative_key: str) -> List[dict]:
    jql = f'parent = "{initiative_key}" ORDER BY Rank ASC'
    return client.search(jql, fields=["summary", "status"])


def fetch_epic_children(client: JiraClient, epic_key: str) -> List[dict]:
    candidate_queries = [
        f'"parentEpic" = "{epic_key}" ORDER BY Rank ASC',
        f'"Epic Link" = "{epic_key}" ORDER BY Rank ASC',
    ]

    last_error: Optional[Exception] = None
    for jql in candidate_queries:
        try:
            return client.search(jql, fields=["summary", "status"])
        except RuntimeError as exc:
            last_error = exc

    raise RuntimeError(f"Unable to load children for epic {epic_key}: {last_error}")


def classify_issue(issue: dict) -> str:
    """Map a Jira issue to one of the canonical status buckets."""
    status = issue["fields"]["status"]
    name = status["name"].strip().lower()
    category = status["statusCategory"]["key"]

    if category == "done":
        return STATUS_DONE
    if "review" in name:
        return STATUS_IN_REVIEW
    if category == "new":
        return STATUS_NOT_STARTED
    return STATUS_IN_PROGRESS


def build_progress(epics: List[dict], client: JiraClient) -> List[EpicProgress]:
    rows: List[EpicProgress] = []
    n = len(epics)
    for i, epic in enumerate(epics, 1):
        key = epic["key"]
        summary = epic["fields"]["summary"]
        print(f"  [{i}/{n}] Fetching children for {key}: {summary}", file=sys.stderr)

        children = fetch_epic_children(client, key)
        children = [c for c in children if c["key"] != key]
        classified = Counter(classify_issue(child) for child in children)
        counts = {s: classified.get(s, 0) for s in STATUSES}

        rows.append(EpicProgress(summary=summary, counts=counts))
    return rows
