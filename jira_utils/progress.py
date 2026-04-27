from __future__ import annotations

import sys
from dataclasses import dataclass
from typing import Dict, List, Optional

from jira_utils.client import JiraClient


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
    status = issue["fields"]["status"]
    name = status["name"].strip().lower()
    category = status["statusCategory"]["key"]

    if category == "done":
        return "done"
    if "review" in name:
        return "in_review"
    if category == "new":
        return "not_started"
    return "in_progress"


def build_progress(epics: List[dict], client: JiraClient) -> List[EpicProgress]:
    rows: List[EpicProgress] = []
    n = len(epics)
    for i, epic in enumerate(epics, 1):
        key = epic["key"]
        summary = epic["fields"]["summary"]
        print(f"  [{i}/{n}] Fetching children for {key}: {summary}", file=sys.stderr)
        counts = {
            "not_started": 0,
            "in_progress": 0,
            "in_review": 0,
            "done": 0,
        }
        children = fetch_epic_children(client, epic["key"])
        for child in children:
            counts[classify_issue(child)] += 1
        rows.append(EpicProgress(summary=summary, counts=counts))
    return rows
