from __future__ import annotations

import base64
import json
import urllib.error
import urllib.request
from typing import Iterable, List, Optional

from jira_utils.config import JiraConfig


MAX_RESULTS = 100


class JiraClient:
    def __init__(self, config: JiraConfig) -> None:
        auth = f"{config.email}:{config.api_token}".encode("utf-8")
        self._auth_header = "Basic " + base64.b64encode(auth).decode("ascii")
        self._base_url = config.base_url
        self._timeout = config.timeout

    def check_connection(self) -> dict:
        """Call GET /myself and return the user profile dict."""
        return self._request_json("GET", "/myself", None)

    def search(self, jql: str, fields: Iterable[str]) -> List[dict]:
        issues: List[dict] = []
        next_page_token: Optional[str] = None

        while True:
            payload: dict = {
                "jql": jql,
                "fields": list(fields),
                "maxResults": MAX_RESULTS,
            }
            if next_page_token is not None:
                payload["nextPageToken"] = next_page_token

            data = self._request_json("POST", "/search/jql", payload)
            batch = data.get("issues", [])
            issues.extend(batch)

            if data.get("isLast", True) or not batch:
                return issues

            next_page_token = data.get("nextPageToken")

    def _request_json(self, method: str, path: str, payload: Optional[dict]) -> dict:
        data = None
        headers = {
            "Accept": "application/json",
            "Authorization": self._auth_header,
            "User-Agent": "jira-initiative-progress/1.0",
        }

        if payload is not None:
            data = json.dumps(payload).encode("utf-8")
            headers["Content-Type"] = "application/json"

        request = urllib.request.Request(
            url=f"{self._base_url}{path}",
            data=data,
            headers=headers,
            method=method,
        )

        try:
            with urllib.request.urlopen(request, timeout=self._timeout) as response:
                body = response.read().decode("utf-8")
        except urllib.error.HTTPError as exc:
            message = exc.read().decode("utf-8", errors="replace")
            raise RuntimeError(f"Jira API request failed ({exc.code}): {message}") from exc
        except urllib.error.URLError as exc:
            raise RuntimeError(f"Jira API request failed: {exc}") from exc

        return json.loads(body)
