import argparse
import os
from dataclasses import dataclass


DEFAULT_TIMEOUT = 30


@dataclass(frozen=True)
class JiraConfig:
    email: str
    api_token: str
    site: str
    timeout: int

    @property
    def base_url(self) -> str:
        return f"https://{self.site}/rest/api/3"


def build_config(args: argparse.Namespace) -> JiraConfig:
    email = os.environ.get("JIRA_EMAIL")
    api_token = os.environ.get("JIRA_API_TOKEN")

    if not email or not api_token:
        raise SystemExit(
            "Missing Jira credentials. Set JIRA_EMAIL and JIRA_API_TOKEN environment variables.\n\n"
            "Create a personal API token at: https://id.atlassian.com/manage-profile/security/api-tokens\n"
            "Use your Atlassian account email as the username, even when logging in via Google SSO."
        )

    return JiraConfig(
        email=email,
        api_token=api_token,
        site=args.site,
        timeout=args.timeout,
    )
